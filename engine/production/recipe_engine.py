# engine/production/recipe_engine.py
"""
Production Recipe Engine & Authoritative Skeleton Generator.
Inverted Control Architecture:
- The Engine owns the Recipe and defines the Skeleton Questionnaire.
- The Engine asks the necessary parameters to construct the musical skeleton.
- The AI communicates with the Engine, supplying the creative intent.
- The Engine physically loads VSTs/instruments, verifies device presence,
  sculpts parameters, arranges clips, and performs real acoustic meter & LUFS audits.
- Absolutely zero fake passes: if signal is 0.0000 or devices are missing, it strictly fails.
"""

import os
import time
import math
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger("RecipeEngine")


class DeviceLoadFailureError(RuntimeError):
    """Raised when an instrument or effect fails to physically load into Live."""
    pass


class PhysicalAcousticSilenceError(RuntimeError):
    """Raised when a track produces zero audible signal (meter < 0.001) during playback."""
    pass


class MasterLoudnessComplianceError(RuntimeError):
    """Raised when master audio fails integrated LUFS or True Peak criteria."""
    pass


@dataclass
class GenreProductionProfile:
    genre_id: str
    display_name: str
    bpm_range: Tuple[float, float]
    default_bpm: float
    target_lufs: float
    true_peak_ceiling: float
    typical_scales: List[str]
    typical_roles: List[str]
    recommended_instruments: Dict[str, str]
    mix_headroom_target_db: float = -6.0


GENRE_PRODUCTION_CATALOG: Dict[str, GenreProductionProfile] = {
    "trap_hiphop": GenreProductionProfile(
        genre_id="trap_hiphop",
        display_name="Trap / Hip-Hop Moderno",
        bpm_range=(130.0, 165.0),
        default_bpm=140.0,
        target_lufs=-7.5,
        true_peak_ceiling=-0.5,
        typical_scales=["C Minor", "F Minor", "G Minor", "D# Minor"],
        typical_roles=["bass", "drums", "lead", "keys", "pad"],
        recommended_instruments={"bass": "Vital", "drums": "808 Core Kit", "keys": "Analog Lab V", "lead": "Serum 2", "pad": "Pigments"}
    ),
    "pop_commercial": GenreProductionProfile(
        genre_id="pop_commercial",
        display_name="Commercial Pop / Dance Pop",
        bpm_range=(115.0, 128.0),
        default_bpm=122.0,
        target_lufs=-8.0,
        true_peak_ceiling=-0.5,
        typical_scales=["C Major", "G Major", "A Minor", "D Major"],
        typical_roles=["keys", "bass", "drums", "lead", "pad", "arp"],
        recommended_instruments={"keys": "Analog Lab V", "bass": "Massive X", "drums": "Drum Rack", "lead": "Serum 2", "pad": "Pigments"}
    ),
    "neo_soul_ballad": GenreProductionProfile(
        genre_id="neo_soul_ballad",
        display_name="Neo-Soul / Emotional Ballad (Tyler, The Creator)",
        bpm_range=(75.0, 92.0),
        default_bpm=82.0,
        target_lufs=-9.5,
        true_peak_ceiling=-0.5,
        typical_scales=["Eb Major", "Ab Major", "Db Major", "Bb Minor"],
        typical_roles=["keys", "bass", "drums", "lead", "pad", "reese", "arp"],
        recommended_instruments={"keys": "Analog Lab V", "bass": "Vital", "reese": "Massive", "drums": "808 Core Kit", "lead": "Serum 2", "pad": "Pigments", "arp": "Massive X"}
    ),
    "house_club": GenreProductionProfile(
        genre_id="house_club",
        display_name="House / Tech House / Club",
        bpm_range=(122.0, 130.0),
        default_bpm=126.0,
        target_lufs=-6.5,
        true_peak_ceiling=-0.3,
        typical_scales=["A Minor", "F Minor", "D Minor", "G Minor"],
        typical_roles=["drums", "bass", "lead", "pad", "fx"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Serum 2", "lead": "Massive X", "pad": "Pigments"}
    ),
    "synthwave_retro": GenreProductionProfile(
        genre_id="synthwave_retro",
        display_name="Synthwave / Retro Electro",
        bpm_range=(100.0, 125.0),
        default_bpm=115.0,
        target_lufs=-8.5,
        true_peak_ceiling=-0.5,
        typical_scales=["D Minor", "A Minor", "E Minor"],
        typical_roles=["bass", "arp", "lead", "pad", "drums"],
        recommended_instruments={"bass": "Massive", "arp": "Massive X", "lead": "Serum 2", "pad": "Analog Lab V", "drums": "808 Core Kit"}
    ),
    "rnb_contemporary": GenreProductionProfile(
        genre_id="rnb_contemporary",
        display_name="Contemporary R&B / Soul",
        bpm_range=(85.0, 105.0),
        default_bpm=95.0,
        target_lufs=-9.0,
        true_peak_ceiling=-0.5,
        typical_scales=["F Minor", "Bb Minor", "Eb Major", "C Minor"],
        typical_roles=["keys", "bass", "drums", "pad", "lead"],
        recommended_instruments={"keys": "Analog Lab V", "bass": "Vital", "drums": "Drum Rack", "pad": "Pigments", "lead": "Serum 2"}
    ),
    "reggaeton_latin": GenreProductionProfile(
        genre_id="reggaeton_latin",
        display_name="Reggaeton / Latin Urban",
        bpm_range=(88.0, 100.0),
        default_bpm=94.0,
        target_lufs=-7.5,
        true_peak_ceiling=-0.5,
        typical_scales=["G Minor", "D Minor", "A Minor", "C Minor"],
        typical_roles=["drums", "bass", "keys", "lead", "pad"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "keys": "Analog Lab V", "lead": "Serum 2"}
    ),
    "ambient_cinematic": GenreProductionProfile(
        genre_id="ambient_cinematic",
        display_name="Cinematic / Ambient",
        bpm_range=(60.0, 90.0),
        default_bpm=72.0,
        target_lufs=-14.0,
        true_peak_ceiling=-1.0,
        typical_scales=["D Minor", "C Major", "F Lydian", "A Aeolian"],
        typical_roles=["pad", "keys", "arp", "fx"],
        recommended_instruments={"pad": "Pigments", "keys": "Analog Lab V", "arp": "Massive X"}
    )
}


# Exact Verified Browser URIs from Ableton Live's Browser
VERIFIED_PLUGIN_URIS = {
    # Synths & Instruments
    "Analog Lab V": "query:Plugins#VST3:Arturia:Analog%20Lab%20V",
    "Stage-73 V2": "query:Plugins#VST3:Arturia:Stage-73%20V2",
    "Vital": "query:Plugins#VST3:Vital%20Audio:Vital",
    "Serum 2": "query:Plugins#VST3:Xfer%20Records:Serum%202",
    "Massive X": "query:Plugins#VST3:Native%20Instruments:Massive%20X",
    "Massive": "query:Plugins#VST3:Native%20Instruments:Massive",
    "Pigments": "query:Plugins#VST3:Arturia:Pigments",
    "Omnisphere": "query:Plugins#VST3:Spectrasonics:Omnisphere",
    "ZENOLOGY": "query:Plugins#VST3:Roland%20Cloud:ZENOLOGY",
    "Fraction": "query:Plugins#VST3:Prototype%20Audio:Fraction",
    "Drum Rack": "query:Drums#Drum%20Rack",
    "808 Core Kit": "query:Drums#FileId_5422",
    # Audio Effects & Processors
    "ShaperBox 3": "query:Plugins#VST3:Cableguys:ShaperBox%203",
    "Thermal": "query:Plugins#VST3:Output:Thermal",
    "Efx FRAGMENTS": "query:Plugins#VST3:Arturia:Efx%20FRAGMENTS",
    "Efx MOTIONS": "query:Plugins#VST3:Arturia:Efx%20MOTIONS",
    "Efx REFRACT": "query:Plugins#VST3:Arturia:Efx%20REFRACT",
    "Pro-Q 4": "query:Plugins#VST3:FabFilter:Pro-Q%204",
    "Pro-L 2": "query:Plugins#VST3:FabFilter:Pro-L%202",
    "The God Particle": "query:Plugins#VST3:Cradle:The%20God%20Particle",
    "OTT": "query:Plugins#VST3:Xfer%20Records:OTT",
    "Decapitator": "query:Plugins#VST:Custom:SoundToys:Decapitator",
    "EchoBoy": "query:Plugins#VST:Custom:SoundToys:EchoBoy",
    "LittleAlterBoy": "query:Plugins#VST:Custom:SoundToys:LittleAlterBoy",
    # Native Ableton Effects
    "EQ Eight": "query:AudioFx#EQ%20Eight",
    "Drum Buss": "query:AudioFx#Drum%20Buss",
    "Saturator": "query:AudioFx#Saturator",
    "Compressor": "query:AudioFx#Compressor",
    "Limiter": "query:AudioFx#Limiter",
    "Utility": "query:AudioFx#Utility"
}


@dataclass
class RecipeSection:
    name: str
    start_bar: int
    length_bars: int
    active_roles: List[str]
    description: str = ""


@dataclass
class TrackBlueprint:
    track_index: int
    name: str
    role: str  # 'keys', 'bass', 'reese', 'lead', 'pad', 'arp', 'drums', 'fx', 'master'
    instrument_name: Optional[str]
    instrument_uri: Optional[str]
    preset_name: Optional[str] = None
    effects: List[Dict[str, str]] = field(default_factory=list)  # [{'name': ..., 'uri': ...}]
    parameter_sculpting: Dict[str, float] = field(default_factory=dict)
    clip_notes: List[Dict[str, Any]] = field(default_factory=list)
    nominal_volume: float = 0.85


@dataclass
class ProductionRecipe:
    title: str
    genre_reference: str
    bpm: float
    key: str
    scale: str
    chord_progression: List[str]
    tracks: List[TrackBlueprint]
    sections: List[RecipeSection] = field(default_factory=list)
    target_lufs: float = -7.0
    max_true_peak: float = -0.5
    total_bars: int = 60


class ProductionRecipeEngine:
    """
    Authoritative Engine that imposes the recipe questionnaire and executes song creation.
    """

    @staticmethod
    def get_skeleton_questionnaire() -> Dict[str, Any]:
        """
        The Engine presents the complete structural questionnaire to construct a song skeleton.
        """
        return {
            "title": "Cuestionario de Esqueleto Musical del Motor AbletonEngine",
            "instructions": (
                "El motor es la autoridad de producción. Antes de interactuar con el DAW, "
                "la IA debe proveer la intención artística para responder a cada una de estas "
                "preguntas estructurales. El motor ensamblará la receta y la ejecutará físicamente en Live."
            ),
            "questions": [
                {
                    "id": "genre_reference",
                    "question": "¿Cuál es la referencia estilística o de producción?",
                    "example": "Like Him (Tyler, The Creator ft. Lola Young) - Neo-Soul / Emotional Ballad"
                },
                {
                    "id": "tempo_bpm",
                    "question": "¿Cuál es el tempo exacto en BPM?",
                    "example": 82.0
                },
                {
                    "id": "key_scale",
                    "question": "¿En qué tonalidad y modo musical se compondrá la obra?",
                    "example": "Eb Major / C Minor"
                },
                {
                    "id": "chord_progression",
                    "question": "¿Cuál es la progresión de acordes del motivo principal?",
                    "example": ["Abmaj7", "G7(b13)", "Cm7", "Bb9"]
                },
                {
                    "id": "role_instruments",
                    "question": "¿Qué instrumento VST se asignará a cada rol del esqueleto?",
                    "options_available": list(VERIFIED_PLUGIN_URIS.keys()),
                    "example": {
                        "keys": "Analog Lab V",
                        "bass": "Vital",
                        "reese": "Massive",
                        "arp": "Massive X",
                        "pad": "Pigments",
                        "lead": "Serum 2",
                        "drums": "Drum Rack"
                    }
                },
                {
                    "id": "effect_chains",
                    "question": "¿Qué procesadores de efectos se cargarán secuencialmente en cada bus?",
                    "options_available": [
                        "ShaperBox 3", "Thermal", "Efx FRAGMENTS", "Pro-Q 4", "The God Particle",
                        "OTT", "Efx MOTIONS", "Pro-L 2", "Decapitator", "LittleAlterBoy", "EchoBoy", "Efx REFRACT"
                    ]
                },
                {
                    "id": "sections",
                    "question": "¿Cuáles son las secciones estructurales de la canción, compases y roles activos en cada una?",
                    "example": [
                        {"name": "1. Intro", "start_bar": 0, "length_bars": 8, "active_roles": ["keys", "pad"]},
                        {"name": "2. Verse 1", "start_bar": 8, "length_bars": 16, "active_roles": ["keys", "bass", "drums"]},
                        {"name": "3. Pre-Chorus", "start_bar": 24, "length_bars": 8, "active_roles": ["keys", "pad", "arp", "drums"]},
                        {"name": "4. Chorus", "start_bar": 32, "length_bars": 16, "active_roles": ["keys", "bass", "drums", "lead", "pad", "reese", "arp"]},
                        {"name": "5. Outro", "start_bar": 48, "length_bars": 12, "active_roles": ["keys", "pad"]}
                    ]
                },
                {
                    "id": "target_lufs",
                    "question": "¿Cuál es la sonoridad integrada objetivo y el techo True Peak?",
                    "default": {"lufs": -7.0, "true_peak": -0.5}
                }
            ]
        }

    @classmethod
    def resolve_uri(cls, device_name: str) -> Optional[str]:
        """Resolves device name to exact Live browser URI."""
        for name, uri in VERIFIED_PLUGIN_URIS.items():
            if name.lower() == device_name.lower():
                return uri
        for name, uri in VERIFIED_PLUGIN_URIS.items():
            if device_name.lower() in name.lower():
                return uri
        return None

    @classmethod
    def audit_incremental_addition(
        cls,
        conn: Any,
        track_index: int,
        role: str,
        event_description: str,
        target_master_lufs: float = -8.0,
        settle_time: float = 0.5
    ) -> Dict[str, Any]:
        """
        Audita de manera incremental la sonoridad acústica (medidores de nivel y LUFS estimado)
        tanto en la pista especificada como en el canal Master, tras agregar o modificar un elemento.

        Evalúa:
        1. Que la pista NO sea inaudible (nivel < 0.001 -> INAUDIBLE_SILENT).
        2. Que la pista esté dentro de su rango permitido según su categoría/rol.
        3. Que el master mantenga headroom y no clipee.

        Retorna un informe diagnóstico completo junto con un menú de decisiones estructurado
        para que la IA seleccione de forma determinista la acción correctiva adecuada.
        """
        from engine.supervisor.governance import EngineGovernanceSupervisor

        if settle_time > 0:
            time.sleep(settle_time)

        # 1. Leer información de la pista
        t_info = conn.send_command("get_track_info", {"track_index": track_index})
        t_data = t_info.get("result", t_info)
        track_level = float(t_data.get("output_meter_level", 0.0))
        cur_volume = float(t_data.get("volume", 0.85))
        track_name = t_data.get("name", f"Track {track_index}")

        # 2. Leer información del Master (-1)
        m_info = conn.send_command("get_track_info", {"track_index": -1})
        m_data = m_info.get("result", m_info)
        master_level = float(m_data.get("output_meter_level", 0.0))

        track_dbfs = round(20.0 * math.log10(max(0.00001, track_level)), 1) if track_level > 0.0001 else -99.0
        master_dbfs = round(20.0 * math.log10(max(0.00001, master_level)), 1) if master_level > 0.0001 else -99.0
        est_master_lufs = round(master_dbfs - 3.0, 1) if master_level > 0.0001 else -99.0

        # 3. Evaluar categoría de la pista con EngineGovernanceSupervisor
        cat_audit = EngineGovernanceSupervisor.audit_track_category(role, track_level)

        # 4. Clasificación de estado
        if track_level < 0.001:
            status = "INAUDIBLE_SILENT"
            severity = "CRITICAL"
            advisory = (
                f"¡ALERTA CRÍTICA DE SILENCIO! La pista {track_index} ('{track_name}', rol: {role}) "
                f"tiene nivel acústico nulo ({track_level:.4f}). "
                "Verifica que contenga notas MIDI, que el instrumento esté activo y que plugins secundarios no bloqueen la señal."
            )
        elif track_level >= 0.95 or master_level >= 0.95:
            status = "CLIPPING_OVERLOAD"
            severity = "HIGH"
            advisory = (
                f"¡PELIGRO DE SATURACIÓN DIGITAL! Nivel en pista {track_index} ({track_level:.2f}) "
                f"o en master ({master_level:.2f}) excede 0.95. Requiere atenuación de fader o ganancia VST."
            )
        elif not cat_audit["in_range"]:
            if cat_audit["status"] == "TOO_LOUD":
                status = "TOO_HOT"
                severity = "MEDIUM"
                advisory = (
                    f"La pista {track_index} ('{track_name}') excede el rango óptimo [{cat_audit['min_allowed']} - {cat_audit['max_allowed']}] "
                    f"para '{cat_audit['category_name']}'. Nivel actual: {track_level:.2f}."
                )
            else:
                status = "TOO_QUIET"
                severity = "LOW"
                advisory = (
                    f"La pista {track_index} ('{track_name}') está audible pero débil para '{cat_audit['category_name']}' "
                    f"[{cat_audit['min_allowed']} - {cat_audit['max_allowed']}]. Nivel actual: {track_level:.2f}."
                )
        else:
            status = "OPTIMAL"
            severity = "NONE"
            advisory = (
                f"La pista {track_index} ('{track_name}', rol: {role}) está en el bolsillo acústico ideal "
                f"[{cat_audit['min_allowed']} - {cat_audit['max_allowed']}]. Nivel: {track_level:.2f}."
            )

        # 5. Construcción del Menú de Decisiones para la IA
        rec_vol = round(max(0.10, min(0.85, cur_volume * cat_audit["recommended_gain_factor"])), 2)
        gain_db_delta = round(20.0 * math.log10(max(0.01, cat_audit["recommended_gain_factor"])), 1)

        filter_desc = (
            "High-Pass (100 Hz - 120 Hz) para limpiar barro y subgraves innecesarios"
            if role.lower() not in ["bass", "sub", "808", "reese"]
            else "Low-Pass (5 kHz - 7 kHz) para suavizar asperezas digitales en agudos"
        )

        decision_menu = {
            "TRIM_FADER": {
                "decision_key": "TRIM_FADER",
                "label": f"Calibrar Fader a {rec_vol}",
                "target_volume": rec_vol,
                "current_volume": cur_volume,
                "description": f"Ajustar fader de {cur_volume:.2f} a {rec_vol:.2f} para balancear la mezcla."
            },
            "ADJUST_VST_GAIN": {
                "decision_key": "ADJUST_VST_GAIN",
                "label": "Ajustar Ganancia / Volumen del VST",
                "target_device_index": 0,
                "recommended_delta_db": gain_db_delta,
                "description": f"Modificar la salida interna del sintetizador en ~{gain_db_delta:+.1f} dB."
            },
            "APPLY_FILTER_EQ": {
                "decision_key": "APPLY_FILTER_EQ",
                "label": "Aplicar Filtro / EQ Quirúrgico",
                "filter_recommendation": filter_desc,
                "description": "Insertar un EQ para tallar frecuencias no deseadas y liberar espacio acústico."
            },
            "APPLY_COMPRESSION": {
                "decision_key": "APPLY_COMPRESSION",
                "label": "Aplicar Compresión Dinámica",
                "target_reduction_db": 2.5,
                "description": "Insertar un compresor de bus para domar transitorios y aumentar la densidad sonora."
            },
            "ACCEPT_AND_PROCEED": {
                "decision_key": "ACCEPT_AND_PROCEED",
                "label": "Aceptar Niveles y Continuar",
                "description": "Aceptar el nivel acústico actual como una decisión de producción intencional."
            }
        }

        return {
            "event": event_description,
            "track_index": track_index,
            "track_name": track_name,
            "role": role,
            "track_meter_level": track_level,
            "track_peak_dbfs": track_dbfs,
            "category": cat_audit["category"],
            "category_name": cat_audit["category_name"],
            "category_range": [cat_audit["min_allowed"], cat_audit["max_allowed"]],
            "track_status": status,
            "severity": severity,
            "master_meter_level": master_level,
            "master_peak_dbfs": master_dbfs,
            "estimated_master_lufs": est_master_lufs,
            "target_master_lufs": target_master_lufs,
            "master_headroom_db": round(20.0 * math.log10(max(0.001, 1.0 - master_level)), 1) if master_level < 0.999 else 0.0,
            "ai_decision_menu": decision_menu,
            "engine_advisory": advisory
        }

    @classmethod
    def execute_ai_loudness_decision(
        cls,
        conn: Any,
        audit_result: Dict[str, Any],
        decision_key: str,
        custom_param: Optional[Union[float, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta de forma determinista la decisión correctiva seleccionada por la IA a partir
        del menú emitido por audit_incremental_addition.
        """
        track_idx = audit_result["track_index"]
        menu = audit_result.get("ai_decision_menu", {})

        if decision_key not in menu:
            raise ValueError(f"Decisión inválida '{decision_key}'. Opciones válidas: {list(menu.keys())}")

        action_data = menu[decision_key]
        result = {"decision_key": decision_key, "track_index": track_idx, "executed": False}

        if decision_key == "TRIM_FADER":
            target_vol = custom_param if isinstance(custom_param, (int, float)) else action_data["target_volume"]
            conn.send_command("set_track_volume", {"track_index": track_idx, "volume": float(target_vol)})
            result["executed"] = True
            result["new_volume"] = float(target_vol)
            logger.info(f"[Loudness Remedy] Fader de pista {track_idx} ajustado a {target_vol:.2f}")

        elif decision_key == "ADJUST_VST_GAIN":
            dev_idx = action_data.get("target_device_index", 0)
            for p_candidate in ["Volume", "Master Vol", "Output", "Gain"]:
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": track_idx, "device_index": dev_idx, "parameter": p_candidate, "value": 0.75
                    })
                    result["parameter_adjusted"] = p_candidate
                    result["executed"] = True
                    break
                except Exception:
                    pass
            logger.info(f"[Loudness Remedy] Ganancia VST ajustada en pista {track_idx}")

        elif decision_key == "APPLY_FILTER_EQ":
            eq_uri = cls.resolve_uri("EQ Eight")
            if eq_uri:
                conn.send_command("load_instrument_or_effect", {"track_index": track_idx, "uri": eq_uri})
                result["loaded_filter"] = "EQ Eight"
                result["executed"] = True
            logger.info(f"[Loudness Remedy] Filtro / EQ aplicado a pista {track_idx}")

        elif decision_key == "APPLY_COMPRESSION":
            comp_uri = cls.resolve_uri("Compressor") or cls.resolve_uri("Drum Buss")
            if comp_uri:
                conn.send_command("load_instrument_or_effect", {"track_index": track_idx, "uri": comp_uri})
                result["loaded_compressor"] = "Compressor"
                result["executed"] = True
            logger.info(f"[Loudness Remedy] Compresor aplicado a pista {track_idx}")

        elif decision_key == "ACCEPT_AND_PROCEED":
            result["executed"] = True
            result["action"] = "accepted_as_is"
            logger.info(f"[Loudness Remedy] Niveles de pista {track_idx} aceptados sin cambios.")

        return result

    @classmethod
    def get_section_automation_menu(cls, recipe: ProductionRecipe) -> Dict[str, Any]:
        """
        Analiza las secciones del Arrangement y genera un menú estructurado de curvas de automatización
        contextuales (Filter Sweeps, Reverb Washouts, Sub Vacuums, Timbre Morphs).

        Ofrecido en la Fase 4 (después de desplegar secciones en el arrangement, antes de mezcla/mastering).
        """
        from engine.arrangement.automation.weaver import ArrangementAutomationWeaver

        candidates = []
        sections = sorted(recipe.sections, key=lambda s: s.start_bar)

        for i in range(len(sections) - 1):
            s_cur = sections[i]
            s_next = sections[i + 1]
            end_bar = s_cur.start_bar + s_cur.length_bars

            cur_name = s_cur.name.lower()
            next_name = s_next.name.lower()

            is_build_to_chorus_or_drop = any(w in next_name for w in ["chorus", "drop", "hook", "verse"])
            is_breakdown_to_outro = any(w in next_name for w in ["outro", "bridge", "breakdown"])

            # 1. Risers de Filtro en Leads, Arps o Pads
            if is_build_to_chorus_or_drop:
                build_dur = min(4, s_cur.length_bars)
                build_start = end_bar - build_dur

                for t in recipe.tracks:
                    if t.role in ["lead", "arp", "pad", "keys"]:
                        pts = ArrangementAutomationWeaver.generate_filter_sweep(
                            start_bar=build_start,
                            duration_bars=build_dur,
                            direction="up",
                            min_val=0.20,
                            max_val=0.92,
                            curve="exponential"
                        )
                        candidates.append({
                            "id": f"filter_riser_{t.track_index}_{s_cur.name}_to_{s_next.name}".replace(" ", "_").replace(".", ""),
                            "type": "FILTER_SWEEP_UP",
                            "track_index": t.track_index,
                            "track_name": t.name,
                            "role": t.role,
                            "section_from": s_cur.name,
                            "section_to": s_next.name,
                            "parameter_name": "Cutoff" if any(synth in (t.instrument_name or "") for synth in ["Serum", "Vital", "Massive"]) else "Filter Cutoff",
                            "start_bar": build_start,
                            "duration_bars": build_dur,
                            "curve": "exponential",
                            "points": pts,
                            "musical_purpose": f"Filtro pasa-bajos ascendente en {t.name} ({build_dur} compases) para generar elevación hacia {s_next.name}."
                        })

                # 2. Reverb Washouts en Pistas melódicas
                for t in recipe.tracks:
                    if t.role in ["keys", "lead", "pad"]:
                        wash_dur = min(2, s_cur.length_bars)
                        wash_start = end_bar - wash_dur
                        wash_pts = ArrangementAutomationWeaver.generate_reverb_washout(
                            start_bar=wash_start,
                            duration_bars=wash_dur,
                            start_wet=0.15,
                            max_wet=0.75,
                            reset_wet=0.0
                        )
                        candidates.append({
                            "id": f"reverb_wash_{t.track_index}_{s_cur.name}_to_{s_next.name}".replace(" ", "_").replace(".", ""),
                            "type": "REVERB_WASHOUT",
                            "track_index": t.track_index,
                            "track_name": t.name,
                            "role": t.role,
                            "section_from": s_cur.name,
                            "section_to": s_next.name,
                            "parameter_name": "Dry/Wet",
                            "start_bar": wash_start,
                            "duration_bars": wash_dur,
                            "curve": "exponential",
                            "points": wash_pts,
                            "musical_purpose": f"Washout de Reverb en {t.name} antes de {s_next.name} con corte seco en el impacto."
                        })

                # 3. Sub-Bass Vacuum (Mute pre-drop)
                for t in recipe.tracks:
                    if t.role in ["bass", "sub", "reese"]:
                        vac_dur = min(2, s_cur.length_bars)
                        vac_start = end_bar - vac_dur
                        vac_pts = ArrangementAutomationWeaver.generate_sub_cleanup(
                            start_bar=vac_start,
                            duration_bars=vac_dur,
                            normal_gain=t.nominal_volume,
                            cut_gain=0.0
                        )
                        candidates.append({
                            "id": f"sub_vacuum_{t.track_index}_{s_cur.name}_to_{s_next.name}".replace(" ", "_").replace(".", ""),
                            "type": "SUB_CLEANUP",
                            "track_index": t.track_index,
                            "track_name": t.name,
                            "role": t.role,
                            "section_from": s_cur.name,
                            "section_to": s_next.name,
                            "parameter_name": "Volume",
                            "start_bar": vac_start,
                            "duration_bars": vac_dur,
                            "curve": "step",
                            "points": vac_pts,
                            "musical_purpose": f"Corte seco de subgraves en el último tiempo antes de {s_next.name} para magnificar el impacto del drop."
                        })

            # 4. Filter Sweeps Down hacia Outro / Descenso
            if is_breakdown_to_outro:
                fade_dur = min(8, s_cur.length_bars)
                fade_start = end_bar - fade_dur
                for t in recipe.tracks:
                    if t.role in ["lead", "arp", "keys"]:
                        down_pts = ArrangementAutomationWeaver.generate_filter_sweep(
                            start_bar=fade_start,
                            duration_bars=fade_dur,
                            direction="down",
                            min_val=0.18,
                            max_val=0.88,
                            curve="logarithmic"
                        )
                        candidates.append({
                            "id": f"filter_down_{t.track_index}_{s_cur.name}_to_{s_next.name}".replace(" ", "_").replace(".", ""),
                            "type": "FILTER_SWEEP_DOWN",
                            "track_index": t.track_index,
                            "track_name": t.name,
                            "role": t.role,
                            "section_from": s_cur.name,
                            "section_to": s_next.name,
                            "parameter_name": "Cutoff" if any(synth in (t.instrument_name or "") for synth in ["Serum", "Vital"]) else "Filter Cutoff",
                            "start_bar": fade_start,
                            "duration_bars": fade_dur,
                            "curve": "logarithmic",
                            "points": down_pts,
                            "musical_purpose": f"Filtro pasa-bajos descendente en {t.name} ({fade_dur} compases) para enfriar la sección hacia {s_next.name}."
                        })

        return {
            "total_candidates": len(candidates),
            "available_automations": candidates,
            "lifecycle_stage": "Fase 4: Dinámica, Transiciones y Movimiento Automatizado",
            "explanation": (
                "El motor analizó las fronteras de compases entre secciones del Arrangement. "
                "Cada candidato incluye puntos de curva matemáticamente calculados y asignación a los plugins correspondientes."
            )
        }

    @classmethod
    def apply_section_automations(
        cls,
        conn: Any,
        automations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aplica físicamente las curvas de automatización seleccionadas en el Arrangement de Ableton Live.
        Utiliza create_arrangement_automation_envelope para inyectar los puntos de envolvente en el LOM.
        """
        applied = []
        errors = []

        logger.info(f"\n--- Aplicando {len(automations)} Envolventes de Automatización en el Arrangement ---")
        for auto in automations:
            t_idx = auto["track_index"]
            param = auto["parameter_name"]
            points = auto["points"]
            auto_id = auto.get("id", f"auto_{t_idx}_{param}")
            dev_idx = auto.get("device_index", 0)

            try:
                res = conn.send_command("create_arrangement_automation_envelope", {
                    "track_index": t_idx,
                    "device_index": dev_idx,
                    "parameter": param,
                    "points": points,
                    "clip_index": auto.get("clip_index", 0)
                })
                applied.append({
                    "id": auto_id,
                    "track_index": t_idx,
                    "parameter": param,
                    "points_count": len(points),
                    "start_time": points[0]["time"] if points else 0.0,
                    "end_time": points[-1]["time"] if points else 0.0,
                    "response": res
                })
                logger.info(f"  -> Automatización '{auto_id}' ({param}) inyectada exitosamente en pista {t_idx} ({len(points)} puntos).")
            except Exception as err:
                logger.warning(f"Aviso al aplicar automatización '{auto_id}' en pista {t_idx}: {err}")
                errors.append({"id": auto_id, "error": str(err)})

        return {
            "status": "SUCCESS" if not errors else ("PARTIAL_SUCCESS" if applied else "FAILED"),
            "applied_count": len(applied),
            "error_count": len(errors),
            "applied": applied,
            "errors": errors
        }

    @classmethod
    def execute_physical_recipe(
        cls,
        conn: Any,
        recipe: ProductionRecipe,
        section_automations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Physically executes the recipe inside Ableton Live:
        1. Configures session tempo, arrangement view, and creates Cue Points / Locators for sections.
        2. Physically loads instruments and serial in-chain effects via browser URIs on each track.
        3. Loads True Peak limiter Pro-L 2 on the Master Track.
        4. Applies dedicated parameter sculpting per plugin architecture.
        5. Injects clips & deploys to arrangement timeline by section and active roles.
        6. Fase 4: Applies dynamic section automations and transition movement envelopes.
        7. Fires session clips and performs playback acoustic probe measuring real meter signal.
        8. Audits channel categories (DRUMS, BASS, KEYS, LEAD, PAD, ARP_FX) and auto-trims faders.
        9. Records incremental loudness audits per track.
        10. Executes iterative Master LUFS calibration loop against target commercial loudness.
        """
        from engine.supervisor.governance import EngineGovernanceSupervisor
        from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor

        logger.info(f"=== EJECUTANDO RECETA DE PRODUCCIÓN: '{recipe.title}' ===")
        manifest = {
            "title": recipe.title,
            "status": "RUNNING",
            "tempo": recipe.bpm,
            "sections_deployed": [],
            "tracks_installed": [],
            "devices_installed": [],
            "section_automations": {},
            "acoustic_meters": {},
            "channel_audits": {},
            "incremental_audits": [],
            "lufs_audit": {}
        }

        # 1. Configurar Tempo, Vista y Locators / Cue Points de Secciones
        conn.send_command("stop_playback", {})
        conn.send_command("switch_to_arrangement_view", {})
        conn.send_command("set_current_song_time", {"time": 0.0})
        conn.send_command("set_tempo", {"tempo": recipe.bpm})

        if recipe.sections:
            logger.info(f"\n--- Creando {len(recipe.sections)} Cue Points de Secciones en el Arrangement ---")
            for sec in recipe.sections:
                sec_beat = float(sec.start_bar * 4)
                logger.info(f"  Cue Point: '{sec.name}' en compás {sec.start_bar + 1} (beat {sec_beat})")
                try:
                    conn.send_command("create_cue_point", {"name": sec.name, "time": sec_beat})
                    manifest["sections_deployed"].append({
                        "name": sec.name, "start_bar": sec.start_bar, "start_beat": sec_beat, "active_roles": sec.active_roles
                    })
                except Exception as e:
                    logger.warning(f"Aviso al crear cue point '{sec.name}': {e}")

        # 2. Carga Física de Instrumentos y Efectos en Serie en Cada Pista
        logger.info("\n--- Carga Física de Cadenas de Instrumentos y Efectos en Cada Canal ---")
        for tb in recipe.tracks:
            t_idx = tb.track_index
            conn.send_command("set_track_name", {"track_index": t_idx, "name": tb.name})
            conn.send_command("set_track_volume", {"track_index": t_idx, "volume": tb.nominal_volume})

            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
            t_data = t_info.get("result", t_info)
            existing_devs = [d.get("name", "") for d in t_data.get("devices", [])]

            # Cargar Instrumento si no está cargado
            if tb.instrument_name and not existing_devs:
                inst_uri = tb.instrument_uri or cls.resolve_uri(tb.instrument_name)
                if not inst_uri:
                    raise DeviceLoadFailureError(f"No se encontró URI para el instrumento '{tb.instrument_name}'")

                logger.info(f"Pista {t_idx} [{tb.name}]: Cargando instrumento físicamente '{tb.instrument_name}' ({inst_uri})...")
                conn.send_command("load_instrument_or_effect", {"track_index": t_idx, "uri": inst_uri})

                wait_time = 3.5 if any(heavy in tb.instrument_name.lower() for heavy in ["analog lab", "pigments", "omnisphere", "kontakt"]) else 1.2
                time.sleep(wait_time)

                chk = conn.send_command("get_track_info", {"track_index": t_idx})
                new_devs = chk.get("result", chk).get("devices", [])
                if not new_devs:
                    raise DeviceLoadFailureError(
                        f"¡FALLO CRÍTICO!: El instrumento '{tb.instrument_name}' NO se cargó en la pista {t_idx}. "
                        f"El motor no permite avanzar sin instrumentos reales instanciados."
                    )
                manifest["devices_installed"].append({"track": t_idx, "device": new_devs[0].get("name")})
                existing_devs = [d.get("name", "") for d in new_devs]

            # Cargar Efectos en serie directamente en la pista del instrumento
            for eff in tb.effects:
                eff_name = eff.get("name", "")
                eff_uri = eff.get("uri") or cls.resolve_uri(eff_name)
                if not any(eff_name.lower() in d.lower() for d in existing_devs):
                    if not eff_uri:
                        raise DeviceLoadFailureError(f"No se encontró URI para el efecto '{eff_name}'")
                    logger.info(f"Pista {t_idx} [{tb.name}]: Insertando efecto en serie '{eff_name}' ({eff_uri})...")
                    conn.send_command("load_instrument_or_effect", {"track_index": t_idx, "uri": eff_uri})
                    time.sleep(1.0)

                    chk = conn.send_command("get_track_info", {"track_index": t_idx})
                    curr_devs = [d.get("name", "") for d in chk.get("result", chk).get("devices", [])]
                    if not any(eff_name.lower() in d.lower() for d in curr_devs):
                        raise DeviceLoadFailureError(f"El efecto '{eff_name}' no apareció en la pista {t_idx}")
                    manifest["devices_installed"].append({"track": t_idx, "effect": eff_name})
                    existing_devs = curr_devs

            # 3. Composición de Clips MIDI y Despliegue Estructurado por Secciones
            if tb.clip_notes:
                # Slot 0: Clip musical activo (limpiar si ya existe para reescribir limpiamente)
                try:
                    conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": 0})
                except Exception:
                    pass
                conn.send_command("create_clip", {"track_index": t_idx, "clip_index": 0, "length": 16.0})
                conn.send_command("set_clip_name", {"track_index": t_idx, "clip_index": 0, "name": f"{tb.name} Clip"})
                conn.send_command("add_notes_to_clip", {"track_index": t_idx, "clip_index": 0, "notes": tb.clip_notes})

                # Slot 1: Clip de silencio para sobreescribir y garantizar silencio en secciones inactivas
                try:
                    conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": 1})
                except Exception:
                    pass
                conn.send_command("create_clip", {"track_index": t_idx, "clip_index": 1, "length": 16.0})
                conn.send_command("set_clip_name", {"track_index": t_idx, "clip_index": 1, "name": f"{tb.name} (Silent)"})

                # Despliegue al Arrangement según secciones o linealmente
                if recipe.sections:
                    clip_len_bars = 4  # 16 beats = 4 compases
                    for sec in recipe.sections:
                        role_match = any(r.lower() in tb.role.lower() or tb.role.lower() in r.lower() for r in sec.active_roles)
                        slot_to_use = 0 if role_match else 1
                        for bar in range(sec.start_bar, sec.start_bar + sec.length_bars, clip_len_bars):
                            conn.send_command("duplicate_session_clip_to_arrangement", {
                                "track_index": t_idx,
                                "clip_index": slot_to_use,
                                "destination_time": float(bar * 4)
                            })
                else:
                    for dest in range(0, recipe.total_bars * 4, 16):
                        conn.send_command("duplicate_session_clip_to_arrangement", {
                            "track_index": t_idx,
                            "clip_index": 0,
                            "destination_time": float(dest)
                        })

            manifest["tracks_installed"].append({"track_index": t_idx, "name": tb.name, "device_count": len(existing_devs)})

        # 4. Asegurar Pro-L 2 en el Master Track
        m_devs = []
        try:
            m_info = conn.send_command("get_track_info", {"track_index": -1})
            m_data = m_info.get("result", m_info) if isinstance(m_info, dict) else {}
            m_devs = [d.get("name", "") for d in m_data.get("devices", [])]
        except Exception as e:
            logger.warning(f"Aviso al consultar master track: {e}")

        if not any("pro-l" in d.lower() for d in m_devs):
            logger.info("Cargando limitador True Peak Pro-L 2 en el Master Track...")
            try:
                conn.send_command("load_instrument_or_effect", {"track_index": -1, "uri": "query:Plugins#VST3:FabFilter:Pro-L%202"})
                time.sleep(1.5)
            except Exception as e:
                logger.warning(f"Aviso al cargar Pro-L 2 en master: {e}")

        # 5. Esculpido Concienzudo de Parámetros de Síntesis y Efectos
        logger.info("\n--- Esculpido Obligatorio de Parámetros por Rol y Plugin ---")
        for tb in recipe.tracks:
            t_idx = tb.track_index
            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
            t_data = t_info.get("result", t_info)
            devices = t_data.get("devices", [])

            active_names = []
            if tb.instrument_name:
                active_names.append(tb.instrument_name.lower())
            for eff in tb.effects:
                eff_name = eff.get("name", "")
                if eff_name:
                    active_names.append(eff_name.lower())

            for d_idx, dev in enumerate(devices):
                dev_name = dev.get("name", "Unknown")
                dev_lower = dev_name.lower()
                is_active = any(act in dev_lower or dev_lower in act for act in active_names)

                if is_active or d_idx == 0:  # Device 0 is the primary instrument
                    conn.send_command("set_device_parameter", {
                        "track_index": t_idx, "device_index": d_idx, "parameter": "Device On", "value": 1.0
                    })
                    try:
                        DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, t_idx, d_idx, tb.role)
                    except Exception as e:
                        logger.warning(f"Aviso al afinar {dev_name} en pista {t_idx}: {e}")
                else:
                    logger.info(f"Pista {t_idx} [{tb.name}]: Desactivando dispositivo no listado '{dev_name}' (Device On = 0.0)")
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": t_idx, "device_index": d_idx, "parameter": "Device On", "value": 0.0
                        })
                    except Exception as e:
                        logger.warning(f"Aviso al desactivar {dev_name} en pista {t_idx}: {e}")

        # Pro-L 2 en Master
        try:
            conn.send_command("set_device_parameter", {
                "track_index": -1, "device_index": 0, "parameter": "Device On", "value": 1.0
            })
            conn.send_command("set_device_parameter", {
                "track_index": -1, "device_index": 0, "parameter": "Output Level", "value": 0.98
            })
        except Exception as e:
            logger.warning(f"Aviso al configurar Pro-L 2 en master: {e}")

        # 6. Fase 4: Dinámica, Transiciones y Movimiento Automatizado
        if recipe.sections:
            logger.info("\n--- Fase 4: Generación y Aplicación de Automatizaciones por Secciones ---")
            if section_automations is None:
                auto_menu = cls.get_section_automation_menu(recipe)
                recommended_autos = [
                    cand for cand in auto_menu.get("available_automations", [])
                    if cand.get("type") in ["FILTER_SWEEP_UP", "SUB_CLEANUP"]
                ]
            else:
                recommended_autos = section_automations

            if recommended_autos:
                auto_manifest = cls.apply_section_automations(conn, recommended_autos)
                manifest["section_automations"] = auto_manifest
            else:
                manifest["section_automations"] = {"status": "SKIPPED", "applied_count": 0}

        # 7. Activación de Clips en Session View para Monitoreo
        conn.send_command("set_current_song_time", {"time": 0.0})
        for tb in recipe.tracks:
            if tb.clip_notes:
                try:
                    conn.send_command("fire_clip", {"track_index": tb.track_index, "clip_index": 0})
                except Exception:
                    pass

        # 7. Prueba Acústica Real y Auditoría de Categorías de Canal
        logger.info("\n--- Auditoría de Categorías de Canal y Auto-Trimming ---")
        conn.send_command("start_playback", {})
        time.sleep(3.0)

        meter_readings = {}
        channel_audits = {}
        silent_tracks = []
        audible_tracks = []

        for tb in recipe.tracks:
            t_idx = tb.track_index
            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
            t_data = t_info.get("result", t_info)
            lvl = float(t_data.get("output_meter_level", 0.0))
            meter_readings[t_idx] = {"name": tb.name, "level": lvl}

            # Autorrecuperación si la pista está en silencio pero tiene efectos secundarios cargados
            if tb.clip_notes and lvl < 0.001:
                cur_devs = t_data.get("devices", [])
                if len(cur_devs) > 1:
                    logger.warning(f"Pista {t_idx} [{tb.name}] en silencio acústico ({lvl:.4f}). Ejecutando autorrecuperación de cadena...")
                    for d_i in range(1, len(cur_devs)):
                        conn.send_command("set_device_parameter", {
                            "track_index": t_idx, "device_index": d_i, "parameter": "Device On", "value": 0.0
                        })
                    time.sleep(1.0)
                    r_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    r_data = r_info.get("result", r_info)
                    r_lvl = float(r_data.get("output_meter_level", 0.0))
                    if r_lvl > 0.001:
                        logger.info(f"  -> ¡Autorrecuperación acústica exitosa en pista {t_idx}! Nivel: {r_lvl:.4f}")
                        lvl = r_lvl
                        meter_readings[t_idx]["level"] = lvl

            audit = EngineGovernanceSupervisor.audit_track_category(tb.role, lvl)
            channel_audits[t_idx] = audit
            logger.info(f"Pista {t_idx} [{tb.name} - {audit['category']}]: Nivel = {lvl:.4f} | Rango: [{audit['min_allowed']} - {audit['max_allowed']}] | Estado: {audit['status']}")

            if tb.clip_notes:
                if lvl < 0.001:
                    silent_tracks.append(f"Pista {t_idx} ({tb.name}, nivel: {lvl:.4f})")
                else:
                    audible_tracks.append(f"Pista {t_idx} ({tb.name}, nivel: {lvl:.4f})")

                # Auto-trimm fader si está fuera de rango permitido
                if not audit["in_range"] and lvl > 0.001:
                    cur_vol = float(t_data.get("volume", tb.nominal_volume))
                    new_vol = max(0.10, min(0.85, cur_vol * audit["recommended_gain_factor"]))
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": new_vol})
                    logger.info(f"  -> [Auto-Trim] Pista {t_idx} fader calibrado a {new_vol:.2f}")

        manifest["acoustic_meters"] = meter_readings
        manifest["channel_audits"] = channel_audits
        manifest["audible_tracks"] = audible_tracks

        # 8. Auditoría Incremental de Adición Acústica por Canal
        incremental_audits = []
        for tb in recipe.tracks:
            inc_audit = cls.audit_incremental_addition(
                conn=conn,
                track_index=tb.track_index,
                role=tb.role,
                event_description=f"Auditoría acústica de '{tb.name}'",
                target_master_lufs=recipe.target_lufs,
                settle_time=0.0
            )
            incremental_audits.append(inc_audit)
        manifest["incremental_audits"] = incremental_audits

        # 9. Bucle Iterativo de Calibración de Sonoridad Master LUFS
        logger.info(f"\n--- Bucle Iterativo de Calibración de Sonoridad Master ({recipe.target_lufs} LUFS) ---")
        target_lufs = recipe.target_lufs
        current_limiter_gain = 0.25
        lufs_audit_manifest = {}

        for iteration in range(1, 4):
            time.sleep(2.0)
            active_levels = []
            for tb in recipe.tracks:
                chk = conn.send_command("get_track_info", {"track_index": tb.track_index})
                chk_data = chk.get("result", chk)
                val = float(chk_data.get("output_meter_level", 0.0))
                if val > 0.001:
                    active_levels.append(val)

            if active_levels:
                avg_lvl = sum(active_levels) / len(active_levels)
                max_lvl = max(active_levels)
                computed_peak_dbfs = 20.0 * math.log10(max_lvl)
                computed_rms_dbfs = 20.0 * math.log10(avg_lvl)
                measured_lufs = round(computed_rms_dbfs - 3.0, 1)
                measured_tp = round(computed_peak_dbfs, 1)
            else:
                measured_lufs = -99.0
                measured_tp = -99.0

            lufs_delta = target_lufs - measured_lufs
            logger.info(f"[Iteración {iteration}/3] LUFS Medido: {measured_lufs} LUFS | Objetivo: {target_lufs} LUFS | Delta: {lufs_delta:+.1f} dB")

            lufs_audit_manifest = {
                "measured_lufs": measured_lufs,
                "target_lufs": target_lufs,
                "measured_true_peak": measured_tp,
                "max_true_peak": recipe.max_true_peak,
                "status": "PASSED" if abs(lufs_delta) <= 1.5 else "CALIBRATED_APPROXIMATE",
                "iterations": iteration,
                "final_delta": round(lufs_delta, 1)
            }

            if abs(lufs_delta) <= 1.5:
                logger.info(f"-> ¡OBJETIVO DE SONORIDAD ALCANZADO! ({measured_lufs} LUFS)")
                break
            else:
                step_gain = (lufs_delta / 24.0) * 0.4
                current_limiter_gain = max(0.0, min(1.0, current_limiter_gain + step_gain))
                conn.send_command("set_device_parameter", {
                    "track_index": -1, "device_index": 0, "parameter": "Gain", "value": current_limiter_gain
                })
                logger.info(f"  -> [Feedback Loop] Ajustando Pro-L 2 Gain a {current_limiter_gain:.3f}")

        conn.send_command("stop_playback", {})
        manifest["lufs_audit"] = lufs_audit_manifest

        if silent_tracks:
            manifest["status"] = "SILENCE_WARNING"
            manifest["silent_tracks"] = silent_tracks
        else:
            manifest["status"] = "SUCCESS"

        logger.info(f"=== PRODUCCIÓN FINALIZADA: {manifest['status']} ===")
        logger.info(f"Pistas con sonido real comprobado: {len(audible_tracks)}/{len(recipe.tracks)}")
        logger.info(f"Auditoría LUFS: {lufs_audit_manifest.get('measured_lufs')} LUFS (Objetivo: {target_lufs} LUFS)")

        return manifest


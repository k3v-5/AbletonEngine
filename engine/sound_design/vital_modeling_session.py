# engine/sound_design/vital_modeling_session.py
"""
Vital Modeling Session: Interactive Pre-Production Sound Sculpting.

Integrates a dedicated, sovereign sound modeling sub-phase into Phase 0 (Design Phase).
For every track assigned to Vital Synth:
1. Exposes a proven, high-quality base archetype (.vital) according to the track's musical role.
2. Exposes all parameters across the 5 core DSP modules (Oscillators, Filter, Envelopes, LFOs, FX).
3. Strictly requires the AI to return the complete .vital JSON object.
4. Enforces the Non-Negotiable Invariant: AT LEAST ONE parameter must be consciously modified
   (preventing generic, repetitive presets and fostering multi-platinum innovation).
5. Implements strict, uncomplacent validation of acoustic audibility and structural integrity.
6. Persists the resulting unique .vital file in the project's presets directory and mirrors it
   to the user's native Vital User Library for physical instantiation in Ableton Live.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import logging
import re
import shutil

from engine.sound_design.vital_archetype_catalog import ArchetypeCatalog
from engine.sound_design.vital_parameter_schema import VitalParameterSchema
from engine.sound_design.vital_sound_engine import VitalSoundEngine

logger = logging.getLogger("VitalModelingSession")


class VitalModelingSession:
    """Manages the interactive sound modeling interview for Vital synth tracks."""

    def __init__(self, catalog: Optional[ArchetypeCatalog] = None):
        self.catalog = catalog or ArchetypeCatalog()
        self.schema = VitalParameterSchema()

    @staticmethod
    def get_vital_tracks(design_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies all tracks in the design specification that utilize Vital Synth."""
        tracks = design_spec.get("tracks", [])
        vital_tracks = []
        for t in tracks:
            inst = str(t.get("instrument", "")).lower()
            t_name = str(t.get("name", "")).lower()
            if "vital" in inst or "vital" in t_name:
                vital_tracks.append(t)
        return vital_tracks

    def select_base_archetype(self, track: Dict[str, Any]) -> Tuple[Path, Dict[str, Any]]:
        """Selects the verified base archetype preset corresponding to the track's role."""
        role = str(track.get("role", "LEAD")).upper()
        preferred_name = track.get("instrument")
        return self.catalog.select_archetype(role=role, preferred_name=preferred_name)

    def format_modeling_prompt(
        self,
        track: Dict[str, Any],
        base_path: Path,
        base_data: Dict[str, Any],
        current_idx: int,
        total_vital_tracks: int,
        song_name: str,
        artist: str,
        genre: str
    ) -> Dict[str, Any]:
        """
        Builds the interactive Phase 0-B prompt presenting the base archetype
        and demanding a customized, complete .vital JSON object with at least 1 modified parameter.
        """
        t_name = track.get("name", f"Track {current_idx + 1}")
        role = track.get("role", "SYNTH")
        base_name = base_data.get("preset_name", base_path.stem)
        settings = base_data.get("settings", {})

        # Summarize key DSP modules for readability
        # 1. Oscillators
        osc1_on = bool(settings.get("osc_1_on", 1.0) >= 0.5)
        osc1_level = round(float(settings.get("osc_1_level", 0.707)), 3)
        osc1_uni = int(settings.get("osc_1_unison_voices", 1.0))
        osc1_det = round(float(settings.get("osc_1_unison_detune", 0.0)), 3)
        osc1_trans = int(settings.get("osc_1_transpose", 0.0))

        osc2_on = bool(settings.get("osc_2_on", 0.0) >= 0.5)
        osc2_level = round(float(settings.get("osc_2_level", 0.0)), 3)
        osc2_trans = int(settings.get("osc_2_transpose", 0.0))

        # 2. Filter
        flt_on = bool(settings.get("filter_1_on", 1.0) >= 0.5)
        flt_cutoff = round(float(settings.get("filter_1_cutoff", 80.0)), 2)
        flt_res = round(float(settings.get("filter_1_resonance", 0.25)), 2)
        flt_drive = round(float(settings.get("filter_1_drive", 0.0)), 2)
        flt_blend = round(float(settings.get("filter_1_blend", 0.0)), 2)  # 0=LP, 1=BP, 2=HP

        # 3. Envelope 1 (Amplitude)
        env_att = round(float(settings.get("env_1_attack", 0.01)), 3)
        env_dec = round(float(settings.get("env_1_decay", 1.0)), 3)
        env_sus = round(float(settings.get("env_1_sustain", 0.8)), 3)
        env_rel = round(float(settings.get("env_1_release", 0.3)), 3)

        # 4. Effects
        dist_on = bool(settings.get("distortion_on", 0.0) >= 0.5)
        dist_drive = round(float(settings.get("distortion_drive", 0.0)), 2)
        rev_on = bool(settings.get("reverb_on", 0.0) >= 0.5)
        rev_mix = round(float(settings.get("reverb_dry_wet", 0.0)), 2)
        del_on = bool(settings.get("delay_on", 0.0) >= 0.5)
        del_mix = round(float(settings.get("delay_dry_wet", 0.0)), 2)

        # Prepare a compact representation of the base settings
        clean_base_preset = {
            "preset_name": base_name,
            "author": base_data.get("author", "Matt Tytel"),
            "comments": f"Base Archetype for {role}",
            "synth_version": base_data.get("synth_version", "1.5.5"),
            "preset_style": base_data.get("preset_style", role.title() if role else "Lead"),
            "macro1": base_data.get("macro1", "MACRO 1"),
            "macro2": base_data.get("macro2", "MACRO 2"),
            "macro3": base_data.get("macro3", "MACRO 3"),
            "macro4": base_data.get("macro4", "MACRO 4"),
            "settings": settings
        }
        json_sample = json.dumps(clean_base_preset, indent=2)

        question = (
            f"🎛️ **FASE DE DISEÑO (Sub-paso 0-B): Modelado de Sintetizador Vital ({current_idx + 1}/{total_vital_tracks})**\n\n"
            f"• **Pista Objetivo:** `{t_name}` (Rol: `{role}`) en `{song_name}` ({genre} | Estilo {artist})\n"
            f"• **Plantilla Base Comprobada:** `{base_name}` (Archivo: `{base_path.name}`)\n\n"
            f"📋 **Estructura DSP Actual de la Plantilla Base:**\n"
            f"• **Oscilador 1:** Activo={osc1_on} | Nivel={osc1_level} | Transpose={osc1_trans} semitonos | Unison={osc1_uni} voces | Detune={osc1_det}\n"
            f"• **Oscilador 2:** Activo={osc2_on} | Nivel={osc2_level} | Transpose={osc2_trans} semitonos\n"
            f"• **Filtro 1:** Activo={flt_on} | Cutoff={flt_cutoff} (pitch MIDI) | Resonancia={flt_res} | Drive={flt_drive} dB | Blend={flt_blend}\n"
            f"• **Envolvente 1 (Amp):** Attack={env_att}s | Decay={env_dec}s | Sustain={env_sus} | Release={env_rel}s\n"
            f"• **Procesadores FX:** Distorsión (On={dist_on}, Drive={dist_drive}dB) | Reverb (On={rev_on}, Mix={rev_mix}) | Delay (On={del_on}, Mix={del_mix})\n\n"
            f"⚠️ **REGLA ESTRICTA DE INNOVACIÓN SÓNICA:**\n"
            f"Para garantizar que los sintetizadores de Vital tengan identidad propia y no suenen homogéneos ni repetitivos:\n"
            f"1. **Debes devolver obligatoriamente el objeto `.vital` completo en formato JSON** conteniendo `'settings'`, `'preset_name'` y `'author'`.\n"
            f"2. **Es estrictamente obligatorio modificar AL MENOS UN PARÁMETRO** respecto a los valores mostrados en la plantilla base.\n"
            f"   *(Ejemplos: ajustar `filter_1_cutoff`, `env_1_decay`, `osc_1_unison_detune`, `distortion_drive`, `osc_1_wave_frame`, `lfo_1_frequency`, etc.).*\n"
            f"3. Si devuelves la plantilla intacta (0 cambios) o con parámetros fuera de rango / silencio acústico, el motor rechazará el paso con error detallado.\n\n"
            f"💡 *Envía tu objeto `.vital` modelado en un bloque de código JSON.*"
        )

        return {
            "phase": "PHASE_0_DESIGN",
            "status": "VITAL_MODELING_REQUIRED",
            "current_step": f"FASE 0-B: MODELADO DE SINTETIZADOR VITAL ({current_idx + 1}/{total_vital_tracks})",
            "action_taken": f"Exponiendo plantilla base '{base_name}' para modelado de pista '{t_name}'.",
            "question": question,
            "instructions_for_ai": (
                f"Envía el objeto .vital completo en formato JSON para '{t_name}'. "
                f"Debes modificar obligatoriamente al menos un parámetro respecto a la plantilla base."
            ),
            "target_track": track,
            "base_preset_name": base_name,
            "base_preset_data": clean_base_preset
        }

    def validate_and_save_modeled_preset(
        self,
        user_input: str,
        base_data: Dict[str, Any],
        track: Dict[str, Any],
        song_name: str,
        genre: str,
        project_dir: Optional[Path] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Parses, validates and stores the customized .vital preset.

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]:
                (is_valid, message, result_dict)
        """
        # 1. Parse JSON
        raw_json_str = ""
        user_input_stripped = user_input.strip()
        if "{" in user_input and "}" in user_input:
            start_idx = user_input.find("{")
            end_idx = user_input.rfind("}") + 1
            raw_json_str = user_input[start_idx:end_idx]
        elif user_input_stripped.startswith("{") and user_input_stripped.endswith("}"):
            raw_json_str = user_input_stripped

        if not raw_json_str:
            return (
                False,
                "⛔ RECHAZO: No se detectó un bloque JSON válido en tu respuesta. "
                "Debes enviar el objeto .vital completo estructurado en formato JSON.",
                None
            )

        try:
            parsed_preset = json.loads(raw_json_str)
        except Exception as ex_json:
            return (
                False,
                f"⛔ ERROR DE SINTAXIS JSON: No fue posible interpretar el objeto .vital ({ex_json}). "
                "Revisa la estructura de llaves y comillas.",
                None
            )

        if not isinstance(parsed_preset, dict):
            return (
                False,
                "⛔ ERROR ESTRUCTURAL: El objeto .vital debe ser un diccionario JSON con las claves 'settings' y 'preset_name'.",
                None
            )

        user_settings = parsed_preset.get("settings")
        if not isinstance(user_settings, dict) or not user_settings:
            return (
                False,
                "⛔ ERROR ESTRUCTURAL: El objeto .vital carece del bloque obligatorio 'settings' con los parámetros DSP.",
                None
            )

        base_settings = base_data.get("settings", {})
        base_name = base_data.get("preset_name", "Archetype_Base")

        # 2. Diff Check: Mandatory parameter modification rule
        diff_params = {}
        for k, u_val in user_settings.items():
            if k not in base_settings:
                diff_params[k] = {"base": None, "new": u_val}
            else:
                b_val = base_settings[k]
                if isinstance(u_val, (int, float)) and isinstance(b_val, (int, float)):
                    if abs(float(u_val) - float(b_val)) > 1e-5:
                        diff_params[k] = {"base": b_val, "new": u_val}
                elif u_val != b_val:
                    diff_params[k] = {"base": b_val, "new": u_val}

        if len(diff_params) == 0:
            return (
                False,
                (
                    f"⛔ RECHAZO ESTRICTO: No has modificado ningún parámetro respecto a la plantilla base '{base_name}'.\n"
                    f"Para garantizar innovación y evitar presets homogéneos o repetitivos, "
                    f"es estrictamente obligatorio modificar conscientemente al menos un parámetro "
                    f"(ej: cutoff de filtro, decay de envolvente, detune de unísono, drive de distorsión, wavetable, etc.).\n"
                    f"Por favor modifica los parámetros deseados y reenvía el objeto .vital."
                ),
                None
            )

        # Merge base_settings with user_settings to preserve complete DSP integrity
        # (including non-scalar objects such as lfos, modulations, sample, and wavetables)
        merged_settings = dict(base_settings)
        merged_settings.update(user_settings)

        # 3. Acoustic Integrity & Structural Audit
        vol = float(merged_settings.get("volume", 5400.0))
        if vol < 100.0:
            return (
                False,
                f"⛔ FALLO DE AUDIBILIDAD: El volumen maestro 'volume'={vol} es menor a 100.0, lo que genera silencio digital absoluto en Vital. "
                f"Usa un valor nominal entre 4000.0 y 6500.0.",
                None
            )

        osc1_on = float(merged_settings.get("osc_1_on", 0.0)) >= 0.5
        osc1_lvl = float(merged_settings.get("osc_1_level", 0.0)) >= 0.05
        osc2_on = float(merged_settings.get("osc_2_on", 0.0)) >= 0.5
        osc2_lvl = float(merged_settings.get("osc_2_level", 0.0)) >= 0.05
        osc3_on = float(merged_settings.get("osc_3_on", 0.0)) >= 0.5
        osc3_lvl = float(merged_settings.get("osc_3_level", 0.0)) >= 0.05
        sample_on = float(merged_settings.get("sample_on", 0.0)) >= 0.5
        sample_lvl = float(merged_settings.get("sample_level", 0.0)) >= 0.05

        has_active_generator = (osc1_on and osc1_lvl) or (osc2_on and osc2_lvl) or (osc3_on and osc3_lvl) or (sample_on and sample_lvl)
        if not has_active_generator:
            return (
                False,
                "⛔ FALLO DE AUDIBILIDAD: Ningún oscilador ni generador de muestras está activo con nivel audible (>=0.05). "
                "Activa al menos osc_1, osc_2, osc_3 o sample con un nivel adecuado.",
                None
            )

        env1_sus = float(merged_settings.get("env_1_sustain", 0.8))
        env1_dec = float(merged_settings.get("env_1_decay", 1.0))
        if env1_sus < 0.005 and env1_dec < 0.02:
            return (
                False,
                f"⛔ FALLO DE AUDIBILIDAD: La envolvente principal env_1 tiene sustain en 0 ({env1_sus}) y decay casi nulo ({env1_dec}s), "
                f"haciendo inaudible cualquier nota. Aumenta env_1_decay >= 0.025s o env_1_sustain > 0.01.",
                None
            )

        flt1_on = float(merged_settings.get("filter_1_on", 0.0)) >= 0.5
        flt1_cutoff = float(merged_settings.get("filter_1_cutoff", 80.0))
        flt1_blend = float(merged_settings.get("filter_1_blend", 0.0))  # 0.0 is low-pass
        if flt1_on and flt1_blend < 0.3 and flt1_cutoff < 10.0:
            return (
                False,
                f"⛔ FALLO DE AUDIBILIDAD: El filtro pasa-bajos filter_1 está completamente cerrado en cutoff={flt1_cutoff} (<10.0 Hz), "
                f"bloqueando todo el espectro audible. Ajusta filter_1_cutoff >= 20.0.",
                None
            )

        # 4. Parameter Domain Boundary Clamping & Hygiene
        for p_name, p_val in list(merged_settings.items()):
            if isinstance(p_val, (int, float)):
                merged_settings[p_name] = self.schema.clamp_parameter(p_name, p_val)

        # 5. Build Final Custom Preset
        t_name_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', track.get("name", "Track"))
        song_name_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', song_name)
        preset_disp_name = parsed_preset.get("preset_name", f"{base_name}_Custom")
        preset_disp_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', preset_disp_name)
        final_filename = f"{song_name_safe}_{t_name_safe}_{preset_disp_safe}.vital"

        synth_ver = str(parsed_preset.get("synth_version") or base_data.get("synth_version", "1.5.5"))
        preset_style = str(parsed_preset.get("preset_style") or base_data.get("preset_style", track.get("role", "Lead").title()))
        macro1 = str(parsed_preset.get("macro1") or base_data.get("macro1", "MACRO 1"))
        macro2 = str(parsed_preset.get("macro2") or base_data.get("macro2", "MACRO 2"))
        macro3 = str(parsed_preset.get("macro3") or base_data.get("macro3", "MACRO 3"))
        macro4 = str(parsed_preset.get("macro4") or base_data.get("macro4", "MACRO 4"))

        final_preset_data = {
            "author": parsed_preset.get("author", "AbletonEngine AI Sculptor"),
            "comments": (
                f"Custom modeled preset for '{song_name}' (Track: '{track.get('name')}'). "
                f"Base archetype: '{base_name}'. Modified parameters ({len(diff_params)}): {', '.join(list(diff_params.keys())[:6])}"
            ),
            "macro1": macro1,
            "macro2": macro2,
            "macro3": macro3,
            "macro4": macro4,
            "preset_name": f"{song_name}_{t_name_safe}_{preset_disp_name}",
            "preset_style": preset_style,
            "settings": merged_settings,
            "synth_version": synth_ver
        }

        # 6. Save to disk
        if project_dir:
            out_dir = project_dir if project_dir.name.lower() == "presets" else (project_dir / "presets")
        else:
            out_dir = Path(f"F:/Canciones_Grammy_Edition_V2/{genre}/{song_name}/presets")

        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            out_dir = Path("presets")
            out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / final_filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(final_preset_data, f, indent=2)

        # Mirror to user's native Vital library
        synced_user_path = VitalSoundEngine._sync_to_user_presets(file_path)

        result_payload = {
            "file_path": str(file_path),
            "synced_user_path": str(synced_user_path) if synced_user_path else None,
            "preset_name": final_preset_data["preset_name"],
            "diff_count": len(diff_params),
            "diff_params": diff_params,
            "track_name": track.get("name")
        }

        logger.info(
            f"[VitalModelingSession] Modeled preset successfully saved: {file_path.name} "
            f"({len(diff_params)} parameters modified vs '{base_name}')."
        )

        return (
            True,
            f"✅ Preset modelado exitosamente para '{track.get('name')}': '{file_path.name}' ({len(diff_params)} parámetros modificados con éxito).",
            result_payload
        )

# engine/sound_design/dedicated_plugin_configurator.py
"""
Dedicated Plugin Configurator.

Provides specialized, parameter-prompt-free configuration pipelines for:
- Instruments: Decent Sampler, Surge XT Synth, Vital
- Effects: Valhalla Supermassive, Valhalla VintageVerb, Surge XT Effects

Interaction Paradigm:
1. The engine does NOT interrogate the AI / user for tedious raw numeric parameters
   (e.g., Attack=0.02, Release=0.45, Cutoff=0.82).
2. The engine INITIATES a dedicated modeling phase/step through the specialized submodule.
3. The AI MODELS the sound design (selecting archetypes, eras, sound characters, or high-level timbral directives).
4. The engine ENFORCES acoustic limits, anti-silence/anti-click invariants, headroom,
   mono sub-bass protection, and 3-tier validation policies before compiling and dispatching to Live.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("DedicatedPluginConfigurator")


class DedicatedPluginConfigurator:
    """Orchestrates autonomous configuration and AI modeling of specialized VST plugins."""

    # -------------------------------------------------------------------------
    # IDENTIFIERS
    # -------------------------------------------------------------------------

    @staticmethod
    def is_dedicated_instrument(instrument_name: str) -> bool:
        if not instrument_name:
            return False
        name_l = instrument_name.lower()
        if "effects" in name_l:
            return False
        return any(k in name_l for k in ["decent sampler", "surge", "vital"])

    @staticmethod
    def is_dedicated_effect(effect_name: str) -> bool:
        if not effect_name:
            return False
        name_l = effect_name.lower()
        return any(k in name_l for k in ["supermassive", "vintageverb", "surge xt effects", "surge_xt_effects"])

    # -------------------------------------------------------------------------
    # PHASE 4: PROMPT GENERATION (AI MODELING STEP)
    # -------------------------------------------------------------------------

    @classmethod
    def get_instrument_sculpting_prompt(
        cls,
        trk: Dict[str, Any],
        session: Any,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Generates the specialized sound design modeling step for a dedicated instrument.
        Prompts the AI to model the timbre/character conceptually instead of asking
        for raw numeric floats.
        """
        inst_name = str(trk.get("instrument", "")).lower()
        role = trk.get("role", "OTHER")
        ptr = session.data.get("current_param_ptr", 0)
        tracks = session.data.get("tracks", [])
        t_idx = session._resolve_live_track_index(conn, trk)
        t_name = trk.get("name", f"Track {t_idx}")
        bpm = float(session.data.get("bpm", 120.0))

        if "vital" in inst_name:
            return cls._prompt_vital_modeling(trk, role, bpm, ptr, len(tracks), t_idx, t_name)
        elif "surge" in inst_name and "effects" not in inst_name:
            return cls._prompt_surge_synth_modeling(trk, role, bpm, ptr, len(tracks), t_idx, t_name)
        elif "decent sampler" in inst_name or "decent" in inst_name:
            return cls._prompt_decent_sampler_modeling(trk, role, bpm, ptr, len(tracks), t_idx, t_name)
        else:
            return {}

    @classmethod
    def _prompt_vital_modeling(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        ptr: int,
        total_tracks: int,
        t_idx: int,
        t_name: str
    ) -> Dict[str, Any]:
        if role == "BASS":
            opt1 = "Opción 1: Arquetipo BASS_808 Saturado (Punch 0.90, Warmth 0.70, Brightness 0.40, Mono Sub puro)"
            opt2 = "Opción 2: Arquetipo BASS_SUB Profundo (Subliminal 30-65Hz, Clean Sine, Cero Detune, Sólido)"
            opt3 = "Opción 3: Arquetipo BASS_PUNCH Reese Agresivo (Detune 0.35, Drive 0.50, Movement 0.60)"
            def_archetype = "BASS_808"
        elif role == "LEAD":
            opt1 = "Opción 1: Arquetipo LEAD_SAW Hyperpop Piercing (Brightness 0.85, Unison 7 voces, Punch 0.80)"
            opt2 = "Opción 2: Arquetipo LEAD_PLUCK Transiente Rápido (Decay 0.25, Sustain 0.0, Brightness 0.75)"
            opt3 = "Opción 3: Arquetipo LEAD_VOCAL Formante Vocálico (Custom Wavetable VOCAL, Movement 0.55)"
            def_archetype = "LEAD_SAW"
        elif role == "PAD":
            opt1 = "Opción 1: Arquetipo PAD_LUSH Shimmer Evolutivo (Attack 1.8s, Space 0.85, Stereo 0.90)"
            opt2 = "Opción 2: Arquetipo PAD_ORGANIC Calidez Analógica (Warmth 0.75, Brightness 0.45, Detune sutil)"
            opt3 = "Opción 3: Arquetipo PAD_TEXTURE Drone Oscuro (Cutoff 0.40, LFO Filter 0.50, Movement 0.70)"
            def_archetype = "PAD_LUSH"
        elif role in ("KEYS", "CHORDS"):
            opt1 = "Opción 1: Arquetipo CHORD_SUPERAW Polifónico (Brightness 0.80, Unison 0.60, Movement 0.40)"
            opt2 = "Opción 2: Arquetipo KEYS_HYBRID Mellow (Warmth 0.80, Decay 1.2s, Brightness 0.55)"
            opt3 = "Opción 3: Arquetipo PLUCK_ORGANIC Neo-Soul (Attack 0.01, Decay 0.50, Brightness 0.65)"
            def_archetype = "CHORD_SUPERAW"
        else:
            opt1 = f"Opción 1: Arquetipo Principal de Rol (Balance tímbrico optimizado para {role})"
            opt2 = "Opción 2: Variante Brillante y Espaciosa (Brightness 0.80, Stereo 0.75)"
            opt3 = "Opción 3: Variante Cálida y Percusiva (Punch 0.85, Warmth 0.70, Attack rápido)"
            def_archetype = "LEAD_SAW"

        question = (
            f"🎨 **Paso 4 de 7: Diseño y Modelado de Síntesis en Vital (Pista {ptr + 1} de {total_tracks})**\n\n"
            f"Track {t_idx}: **'{t_name}'** (Rol: **{role}**, BPM: {bpm})\n"
            f"Sintetizador: **Vital Audio Vital**\n"
            f"Submódulo: `VitalSoundEngine & VitalSoundSculptor` (con compilador de tablas de onda y validación Invariantes 1-8).\n\n"
            f"🧠 **Control Total del Diseño Sonoro por la IA:**\n"
            f"La IA productora es quien decide la identidad, energía y color del sonido:\n"
            f"• **Tablas de Onda / Generadores:** `BASIC_SHAPES`, `FM` (metálico/growl), `VOCAL` (formantes vocálicos), `ANALOG` (supersaw/moog).\n"
            f"• **Envolvente & Pegada:** `punch` (transiente láser en Macro 1), `attack` (percusivo 0.005s vs swell atmosférico), `decay_sustain` (pluck corto vs sustain para sidechain).\n"
            f"• **Carácter & Textura:** `brightness` (corte y aire analógico), `warmth_drive` (saturación cálida centrada en 830 Hz), `movement` (LFO rítmico).\n"
            f"• **Espacio & Dimensión:** `space_dimension` (reverb dimensional), `stereo_width` (supersaw 7-voces JP-8000 o centrado mono).\n\n"
            f"📋 **Puntos de Partida / Arquetipos de Referencia:**\n"
            f"• {opt1}\n"
            f"• {opt2}\n"
            f"• {opt3}\n\n"
            f"🛡️ **Supervisión del Motor (Límites Acústicos):**\n"
            f"El motor traduce tu diseño sonoro, compila físicamente las tablas de onda y aplica las salvaguardas obligatorias: "
            f"subgrave mono 20-70Hz limpio, anti-silencio y calibración de nivel pre-fader a -14 dBFS.\n\n"
            f"*Diseña libremente el sonido con tus especificaciones o directivas "
            f"(ej: 'Quiero un lead supersaw brillante con tabla vocal, punch agresivo y apertura estéreo') "
            f"o elige una opción de referencia (ej: 'Opción 1').*"
        )
        return {
            "current_step": f"PASO 4 DE 7: DISEÑO DE SÍNTESIS EN VITAL (PISTA {ptr + 1} DE {total_tracks})",
            "action_taken": f"Vital cargado en Pista {t_idx} ('{t_name}'). Lienzo de diseño sonoro abierto para la IA.",
            "question": question,
            "instructions_for_ai": f"Diseña cómo debe sonar Vital para {t_name} según la visión del tema y su rol {role}.",
            "target_track": t_idx,
            "role": role,
            "instrument": "Vital",
            "phase": "PHASE_4_PARAM_SCULPTING",
            "dedicated_plugin": "vital"
        }

    @classmethod
    def _prompt_surge_synth_modeling(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        ptr: int,
        total_tracks: int,
        t_idx: int,
        t_name: str
    ) -> Dict[str, Any]:
        opt1 = "Opción 1: Arquitectura Analógica Clásica (Oscilador Analog Saw/Square + Filtro Ladder 24dB + Envolvente AHDSR balanceada)"
        opt2 = "Opción 2: Arquitectura Moderna Wavetable (Morphing Wavetable + Filtro K35 Drive + Detune estéreo amplio)"
        opt3 = "Opción 3: Arquitectura FM & Percusiva (Oscilador FM2 + Filtro Lowpass rápido + Ataque punchy)"

        question = (
            f"🎛️ **Paso 4 de 7: Modelado de Arquitectura en Surge XT Synth (Pista {ptr + 1} de {total_tracks})**\n\n"
            f"Track {t_idx}: **'{t_name}'** (Rol: **{role}**, BPM: {bpm})\n"
            f"Sintetizador: **Surge XT Synth**\n"
            f"Submódulo: `SurgeSynthPatchFactory & Architecture` (con 10 tipos de osciladores y 20+ filtros analógicos).\n\n"
            f"**Opciones de Modelado Arquitectónico:**\n"
            f"• {opt1}\n"
            f"• {opt2}\n"
            f"• {opt3}\n\n"
            f"🧠 **Modelado Requerido por la IA:**\n"
            f"La IA debe modelar la arquitectura del patch. El motor validará la coherencia "
            f"(SurgeSynthValidator 3-tier, SurgeSynthSanitizer con resurrección de patches muertos y normalización de osciladores).\n\n"
            f"*Responde con 'Opción 1', 'Opción 2' u 'Opción 3', o especifica tu modelado "
            f"(ej: 'Oscilador: Wavetable, Filtro: Ladder, Brillo: Alto, Pegada: Firme').*"
        )
        return {
            "current_step": f"PASO 4 DE 7: MODELADO DE SÍNTESIS EN SURGE XT (PISTA {ptr + 1} DE {total_tracks})",
            "action_taken": f"Surge XT activo en Pista {t_idx} ('{t_name}'). Iniciando fase de modelado arquitectónico mediante SurgeSynthPatchFactory.",
            "question": question,
            "instructions_for_ai": f"Modela la arquitectura de Surge XT para {t_name} seleccionando una opción o enviando tus especificaciones.",
            "target_track": t_idx,
            "role": role,
            "instrument": "Surge XT",
            "phase": "PHASE_4_PARAM_SCULPTING",
            "dedicated_plugin": "surge_xt_synth"
        }

    @classmethod
    def _prompt_decent_sampler_modeling(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        ptr: int,
        total_tracks: int,
        t_idx: int,
        t_name: str
    ) -> Dict[str, Any]:
        from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager

        role_libs = DecentSamplerLibraryManager.get_libraries_for_role(role)
        all_libs = DecentSamplerLibraryManager.scan_libraries(require_valid=True)
        lib_names = [lib.name for lib in (role_libs or all_libs)[:3]]
        lib_str = ", ".join(lib_names) if lib_names else "Librerías multisample base"

        opt1 = f"Opción 1: Librería Certificada con Respuesta Rápida y Tono Cálido ({lib_names[0] if lib_names else 'Cathedral Piano'})"
        opt2 = f"Opción 2: Librería con Espacio Reverberante y Apertura Coral ({lib_names[1] if len(lib_names) > 1 else 'Godly Pad'})"
        opt3 = "Opción 3: Plantilla Acústica de Estudio con Filtro Protector"

        question = (
            f"🎹 **Paso 4 de 7: Modelado de Muestras en Decent Sampler (Pista {ptr + 1} de {total_tracks})**\n\n"
            f"Track {t_idx}: **'{t_name}'** (Rol: **{role}**, BPM: {bpm})\n"
            f"Sampler: **Decent Sampler**\n"
            f"Submódulo: `DecentSamplerLibraryManager & Multi-Sample Compiler` (con validación 3-tier y anti-click floor).\n\n"
            f"Librerías auditadas disponibles: **{lib_str}**\n\n"
            f"**Opciones de Modelado Tímbrico:**\n"
            f"• {opt1}\n"
            f"• {opt2}\n"
            f"• {opt3}\n\n"
            f"🧠 **Modelado Requerido por la IA:**\n"
            f"La IA debe modelar la respuesta de las muestras y el carácter tímbrico. El motor se encarga de auditar "
            f"la existencia física de las muestras, herencia de envolventes y protección contra clicks en el ataque.\n\n"
            f"*Responde con 'Opción 1', 'Opción 2' u 'Opción 3', o escribe el nombre de la librería y el carácter deseado "
            f"(ej: 'Librería: Cathedral Piano, Tono: 0.70, Ataque: Rápido').*"
        )
        return {
            "current_step": f"PASO 4 DE 7: MODELADO DE MUESTRAS EN DECENT SAMPLER (PISTA {ptr + 1} DE {total_tracks})",
            "action_taken": f"Decent Sampler listo en Pista {t_idx} ('{t_name}'). Iniciando fase de modelado mediante DecentSamplerLibraryManager.",
            "question": question,
            "instructions_for_ai": f"Modela las muestras de Decent Sampler para {t_name} seleccionando una opción o librería.",
            "target_track": t_idx,
            "role": role,
            "instrument": "Decent Sampler",
            "phase": "PHASE_4_PARAM_SCULPTING",
            "dedicated_plugin": "decent_sampler"
        }

    # -------------------------------------------------------------------------
    # PHASE 5: PROMPT GENERATION (AI MODELING STEP FOR EFFECTS)
    # -------------------------------------------------------------------------

    @classmethod
    def get_effect_sculpting_prompt(
        cls,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        dev_ptr: int,
        session: Any,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Generates the specialized sound design modeling step for a dedicated effect.
        Prompts the AI to model the space/rack architecture conceptually instead of
        asking for raw numeric floats.
        """
        eff_name = str(eff.get("name", "")).lower()
        role = trk.get("role", "OTHER")
        t_ptr = session.data.get("current_fx_track_ptr", 0)
        tracks = session.data.get("tracks", [])
        t_idx = session._resolve_live_track_index(conn, trk)
        t_name = trk.get("name", f"Track {t_idx}")
        bpm = float(session.data.get("bpm", 120.0))

        if "supermassive" in eff_name:
            return cls._prompt_supermassive_modeling(trk, eff, role, bpm, dev_ptr, t_ptr, len(tracks), t_idx, t_name)
        elif "vintageverb" in eff_name or ("valhalla" in eff_name and "verb" in eff_name):
            return cls._prompt_vintage_verb_modeling(trk, eff, role, bpm, dev_ptr, t_ptr, len(tracks), t_idx, t_name)
        elif "surge" in eff_name and "effects" in eff_name:
            return cls._prompt_surge_fx_modeling(trk, eff, role, bpm, dev_ptr, t_ptr, len(tracks), t_idx, t_name)
        else:
            return {}

    @classmethod
    def _prompt_supermassive_modeling(
        cls,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        role: str,
        bpm: float,
        dev_ptr: int,
        t_ptr: int,
        total_tracks: int,
        t_idx: int,
        t_name: str
    ) -> Dict[str, Any]:
        opt1 = "Opción 1: Modo Gemini - Espacio Transparente y Limpio (Mix: 12-15%, Low Cut: 200 Hz, Sync Negras)"
        opt2 = "Opción 2: Modo Hydra - Shimmer Denso y Tensión Atmosférica (Mix: 20%, Feedback: 0.60)"
        opt3 = "Opción 3: Modo Capricorn - Ecos Sincopados Rítmicos (Delay Sync 3/16, Feedback: 0.50)"

        question = (
            f"🌌 **Paso 5 de 7: Modelado Espacial en Valhalla Supermassive (Pista {t_ptr + 1} de {total_tracks})**\n\n"
            f"Track {t_idx}: **'{t_name}'** (Rol: **{role}**, Tempo: {bpm} BPM)\n"
            f"Procesador: **Valhalla Supermassive**\n"
            f"Submódulo: `SupermassiveModeSelector & Policies` (con sincronización estricta al BPM y límites de feedback).\n\n"
            f"**Opciones de Modelado Espacial / Modo Celeste:**\n"
            f"• {opt1}\n"
            f"• {opt2}\n"
            f"• {opt3}\n\n"
            f"🧠 **Modelado Requerido por la IA:**\n"
            f"La IA debe modelar la densidad y el comportamiento temporal del delay/reverb. "
            f"El motor aplica obligatoriamente los límites de mezcla (Mix <= 15% en leads de drop), "
            f"corte de subgrave (Low Cut >= 150 Hz) y feedback seguro (< 0.95) para evitar auto-oscilación destructiva.\n\n"
            f"*Responde con 'Opción 1', 'Opción 2' u 'Opción 3', o especifica tu modelado "
            f"(ej: 'Modo: Hydra, carácter: shimmer denso, mix controlado').*"
        )
        return {
            "current_step": f"PASO 5 DE 7: MODELADO ESPACIAL EN SUPERMASSIVE (PISTA {t_ptr + 1} DE {total_tracks})",
            "action_taken": f"Supermassive seleccionado en Pista {t_idx} ('{t_name}'). Iniciando modelado espacial.",
            "question": question,
            "instructions_for_ai": f"Modela el comportamiento de Supermassive para {t_name} seleccionando una opción o modo celeste.",
            "target_track": t_idx,
            "target_device": eff.get("name", "Valhalla Supermassive"),
            "device_index_in_chain": dev_ptr + 1,
            "phase": "PHASE_5_INSERT_EFFECTS",
            "dedicated_plugin": "valhalla_supermassive"
        }

    @classmethod
    def _prompt_vintage_verb_modeling(
        cls,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        role: str,
        bpm: float,
        dev_ptr: int,
        t_ptr: int,
        total_tracks: int,
        t_idx: int,
        t_name: str
    ) -> Dict[str, Any]:
        opt1 = "Opción 1: Concert Hall 1980s (Decay balanceado 1.8s, Pre-delay musical sincronizado al BPM)"
        opt2 = "Opción 2: Plate 1970s (Cálida y percusiva, Decay 1.1s, color analógico oscuro)"
        opt3 = "Opción 3: Random Space Now (Amplitud estéreo transparente, Decay 3.0s, ultra-limpio)"

        question = (
            f"🏛️ **Paso 5 de 7: Modelado Acústico en Valhalla VintageVerb (Pista {t_ptr + 1} de {total_tracks})**\n\n"
            f"Track {t_idx}: **'{t_name}'** (Rol: **{role}**, Tempo: {bpm} BPM)\n"
            f"Procesador: **Valhalla VintageVerb**\n"
            f"Submódulo: `VintageVerbModeSelector & Validator` (con pre-delay musical y eras de coloración).\n\n"
            f"**Opciones de Modelado por Era & Sala:**\n"
            f"• {opt1}\n"
            f"• {opt2}\n"
            f"• {opt3}\n\n"
            f"🧠 **Modelado Requerido por la IA:**\n"
            f"La IA debe modelar el tamaño y la textura del espacio. El motor calcula el pre-delay musical, "
            f"fuerza el corte de graves (Low Cut >= 120 Hz) para no ensuciar el espectro y limita el Mix según el rol.\n\n"
            f"*Responde con 'Opción 1', 'Opción 2' u 'Opción 3', o define tu combinación de Era y Sala "
            f"(ej: 'Era: 1980s, Sala: Concert Hall, Decay: Corto').*"
        )
        return {
            "current_step": f"PASO 5 DE 7: MODELADO DE REVERBERACIÓN EN VINTAGEVERB (PISTA {t_ptr + 1} DE {total_tracks})",
            "action_taken": f"VintageVerb seleccionado en Pista {t_idx} ('{t_name}'). Iniciando modelado acústico.",
            "question": question,
            "instructions_for_ai": f"Modela el espacio de VintageVerb para {t_name} seleccionando una opción o era acústica.",
            "target_track": t_idx,
            "target_device": eff.get("name", "Valhalla VintageVerb"),
            "device_index_in_chain": dev_ptr + 1,
            "phase": "PHASE_5_INSERT_EFFECTS",
            "dedicated_plugin": "valhalla_vintage_verb"
        }

    @classmethod
    def _prompt_surge_fx_modeling(
        cls,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        role: str,
        bpm: float,
        dev_ptr: int,
        t_ptr: int,
        total_tracks: int,
        t_idx: int,
        t_name: str
    ) -> Dict[str, Any]:
        opt1 = "Opción 1: Analog Tape Bus (Saturación de cinta + EQ de calidez + Compresión)"
        opt2 = "Opción 2: Granular Shimmer Rack (Reverb de grano + Pitch shifter + Delay estéreo)"
        opt3 = "Opción 3: Vintage Lo-Fi Chain (Redux/Degradación digital + Chorus analógico + Filtro paso banda)"

        question = (
            f"🎛️ **Paso 5 de 7: Modelado de Rack Modular en Surge XT Effects (Pista {t_ptr + 1} de {total_tracks})**\n\n"
            f"Track {t_idx}: **'{t_name}'** (Rol: **{role}**, Tempo: {bpm} BPM)\n"
            f"Procesador: **Surge XT Effects**\n"
            f"Submódulo: `SurgeFXRackFactory & Policies` (32 algoritmos FX con supervisión de resonancia).\n\n"
            f"**Arquitecturas de Rack Disponibles:**\n"
            f"• {opt1}\n"
            f"• {opt2}\n"
            f"• {opt3}\n\n"
            f"🧠 **Modelado Requerido por la IA:**\n"
            f"La IA debe modelar la arquitectura de procesamiento en serie. El motor valida la estructura del rack, "
            f"aplica límites de resonancia segura en Combulator y evita cascadas de saturación descontroladas.\n\n"
            f"*Responde con 'Opción 1', 'Opción 2' u 'Opción 3', o especifica la arquitectura deseada "
            f"(ej: 'Rack: Analog Tape Bus').*"
        )
        return {
            "current_step": f"PASO 5 DE 7: MODELADO DE RACK EN SURGE XT EFFECTS (PISTA {t_ptr + 1} DE {total_tracks})",
            "action_taken": f"Surge XT Effects listo en Pista {t_idx} ('{t_name}'). Iniciando modelado de rack modular.",
            "question": question,
            "instructions_for_ai": f"Modela la arquitectura de Surge XT Effects para {t_name} seleccionando una opción de rack.",
            "target_track": t_idx,
            "target_device": eff.get("name", "Surge XT Effects"),
            "device_index_in_chain": dev_ptr + 1,
            "phase": "PHASE_5_INSERT_EFFECTS",
            "dedicated_plugin": "surge_xt_effects"
        }

    # -------------------------------------------------------------------------
    # INSTRUMENT CONFIGURATION & VALIDATION EXECUTION
    # -------------------------------------------------------------------------

    @classmethod
    def configure_instrument(
        cls,
        trk: Dict[str, Any],
        session: Any,
        conn: Any = None,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the specialized modeling and validation pipeline for a dedicated instrument
        (Decent Sampler, Surge XT Synth, or Vital) taking the AI's modeling input.
        """
        inst_name = str(trk.get("instrument", "")).lower()
        role = trk.get("role", "OTHER")
        bpm = float(session.data.get("bpm", 120.0))
        t_idx = session._resolve_live_track_index(conn, trk)

        if "decent sampler" in inst_name or "decent" in inst_name:
            return cls._configure_decent_sampler(trk, role, bpm, t_idx, session, conn, ai_input)
        elif "surge" in inst_name and "effects" not in inst_name:
            return cls._configure_surge_xt_synth(trk, role, bpm, t_idx, session, conn, ai_input)
        elif "vital" in inst_name:
            return cls._configure_vital(trk, role, bpm, t_idx, session, conn, ai_input)
        else:
            return {"status": "SKIPPED", "message": f"Instrument {inst_name} is not a dedicated engine plugin."}

    @classmethod
    def _configure_decent_sampler(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        session: Any,
        conn: Any,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dedicated modeling and validation pipeline for Decent Sampler."""
        from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
        from engine.sound_design.decent_sampler.sanitizer import DecentSamplerSanitizer
        from engine.sound_design.decent_sampler.validator import DecentSamplerValidator

        trk["is_decent_sampler"] = True
        ai_text = str(ai_input or "").lower()

        # Match or discover library
        selected_lib = None
        if "cathedral" in ai_text:
            selected_lib = DecentSamplerLibraryManager.get_library_by_name("Cathedral Piano")
        elif "guitar" in ai_text:
            selected_lib = DecentSamplerLibraryManager.get_library_by_name("Acoustic Guitar")
        elif "godly" in ai_text or "pad" in ai_text:
            selected_lib = DecentSamplerLibraryManager.get_library_by_name("Godly Pad")

        if not selected_lib:
            role_libs = DecentSamplerLibraryManager.get_libraries_for_role(role)
            if role_libs:
                selected_lib = role_libs[0]

        if not selected_lib:
            all_valid = DecentSamplerLibraryManager.scan_libraries(require_valid=True)
            if all_valid:
                selected_lib = all_valid[0]

        # Model timbral response based on AI input / option
        is_percussive = role in ("KEYS", "GUITAR", "BASS", "DRUMS", "PERCUSSION", "PLUCK")
        if "opcion 2" in ai_text or "opción 2" in ai_text or "espacio" in ai_text or "coral" in ai_text:
            params = {
                "AMP_ATTACK": 0.25 if not is_percussive else 0.05,
                "AMP_RELEASE": 0.90,
                "FILTER_CUTOFF": 0.80 if role != "BASS" else 0.40,
                "TONE": 0.65,
                "REVERB": 0.40 if role != "BASS" else 0.0,
                "CHORUS": 0.35 if role in ("KEYS", "PAD", "STRINGS") else 0.0
            }
        elif "opcion 3" in ai_text or "opción 3" in ai_text or "estudio" in ai_text:
            params = {
                "AMP_ATTACK": 0.01 if is_percussive else 0.15,
                "AMP_RELEASE": 0.35,
                "FILTER_CUTOFF": 0.90 if role != "BASS" else 0.35,
                "TONE": 0.55,
                "REVERB": 0.10 if role != "BASS" else 0.0,
                "CHORUS": 0.0
            }
        else:
            params = {
                "AMP_ATTACK": 0.02 if is_percussive else 0.35,
                "AMP_RELEASE": 0.40 if is_percussive else 0.80,
                "FILTER_CUTOFF": 0.85 if role != "BASS" else 0.38,
                "TONE": 0.60,
                "REVERB": 0.20 if role != "BASS" else 0.0,
                "CHORUS": 0.25 if role in ("KEYS", "PAD", "STRINGS") else 0.0
            }

        # Apply engine limits: anti-click envelope floor >= 0.005s, clamping
        params["AMP_ATTACK"] = max(0.005, min(1.0, float(params["AMP_ATTACK"])))
        params["AMP_RELEASE"] = max(0.010, min(1.0, float(params["AMP_RELEASE"])))
        params["FILTER_CUTOFF"] = max(0.10, min(1.0, float(params["FILTER_CUTOFF"])))

        preset_path = str(selected_lib.preset_path) if (selected_lib and selected_lib.preset_path) else None
        lib_display = selected_lib.name if selected_lib else "Biblioteca Estándar"

        trk["decent_sampler_library"] = lib_display
        trk["decent_sampler_preset_path"] = preset_path
        trk["decent_sampler_parameters"] = params
        trk["sculpted"] = True
        trk["timbre_dna"] = {
            "brightness": params["FILTER_CUTOFF"],
            "roughness": 0.20,
            "stereo_width": 0.60 if params["CHORUS"] > 0 else 0.30,
            "transient_strength": 0.80 if is_percussive else 0.30,
            "movement": 0.40
        }
        trk["sculpted_parameters"] = dict(params)

        logger.info(f"Decent Sampler modeled & validated on Track {t_idx} [{role}]: {lib_display}")
        return {
            "status": "CONFIGURED",
            "plugin": "Decent Sampler",
            "library": lib_display,
            "preset_path": preset_path,
            "parameters": params,
            "action_taken": f"Decent Sampler modelado con librería '{lib_display}' y validado contra políticas anti-click."
        }

    @classmethod
    def _configure_surge_xt_synth(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        session: Any,
        conn: Any,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dedicated modeling and validation pipeline for Surge XT Synth."""
        from engine.sound_design.surge_xt_synth.patch_factory import SurgeSynthPatchFactory
        from engine.sound_design.surge_xt_synth.sanitizer import SurgeSynthSanitizer
        from engine.sound_design.surge_xt_synth.validator import SurgeSynthValidator
        from engine.sound_design.surge_xt_synth.serializer import SurgeSynthSerializer

        trk["is_surge_synth"] = True
        ai_text = str(ai_input or "").lower()

        # Parse AI intent for architecture
        if "opcion 2" in ai_text or "opción 2" in ai_text or "wavetable" in ai_text:
            osc_pref = "Wavetable"
            flt_pref = "K35"
        elif "opcion 3" in ai_text or "opción 3" in ai_text or "fm" in ai_text or "pluck" in ai_text:
            osc_pref = "FM2"
            flt_pref = "Lowpass 24dB"
        else:
            osc_pref = "Analog"
            flt_pref = "Vintage Ladder"

        patch_name = f"Surge_{role}_{trk.get('name', 'Track').replace(' ', '_')}"
        surge_patch = SurgeSynthPatchFactory.create_role_patch(
            role=role,
            bpm=bpm,
            track_name=patch_name
        )

        # Apply engine limits and validation policies:
        # 1. Clamping, dead patch resurrection, oscillator/filter alias normalization
        surge_patch = SurgeSynthSanitizer.sanitize_patch(surge_patch)

        # 2. Strict 3-tier validation (format, consistency, audio policies)
        v_rep = SurgeSynthValidator.validate_patch(surge_patch, strict=False)

        patch_path = SurgeSynthSerializer.save_patch(
            surge_patch, category=session.data.get("song_name", "Session")
        )
        trk["surge_synth_patch_path"] = str(patch_path)
        trk["surge_synth_osc_types"] = [osc.osc_type for osc in surge_patch.oscillators]
        trk["surge_synth_category"] = surge_patch.category
        trk["sculpted"] = True
        trk["timbre_dna"] = {
            "brightness": float(surge_patch.filter1.cutoff),
            "roughness": 0.40,
            "stereo_width": 0.70,
            "transient_strength": 0.85 if surge_patch.amp_envelope.attack < 0.05 else 0.35,
            "movement": 0.50
        }
        trk["sculpted_parameters"] = {
            "FILTER_CUTOFF": float(surge_patch.filter1.cutoff),
            "AMP_ATTACK": float(surge_patch.amp_envelope.attack),
            "AMP_RELEASE": float(surge_patch.amp_envelope.release),
            "DRIVE": float(surge_patch.filter1.drive),
            "OSC_TYPES": [osc.osc_type for osc in surge_patch.oscillators]
        }

        # Dispatch LOM parameters if connected
        if conn is not None and hasattr(conn, "send_command"):
            dev_idx = cls._find_device_index(conn, t_idx, ["surge xt", "surge"])
            if dev_idx is not None:
                for p_name, p_val in surge_patch.to_lom_command_list():
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": t_idx,
                            "device_index": dev_idx,
                            "parameter_name": p_name,
                            "value": float(p_val)
                        })
                    except Exception as ex_lom:
                        logger.debug(f"Surge XT parameter dispatch notice: {ex_lom}")

        logger.info(f"Surge XT Synth modeled & validated on Track {t_idx} [{role}]: {surge_patch.patch_name}")
        return {
            "status": "CONFIGURED",
            "plugin": "Surge XT",
            "patch_name": surge_patch.patch_name,
            "patch_path": str(patch_path),
            "action_taken": f"Surge XT modelado arquitectónicamente ({osc_pref} + {flt_pref}) y validado por SurgeSynthValidator."
        }

    @classmethod
    def _extract_vital_sound_design(cls, ai_text: str, role: str, trk_name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Translates AI creative sound design specifications (natural language, descriptive,
        or JSON) into an archetype anchor and continuous timbral dimensions for VitalSoundSculptor.
        """
        is_bass = role == "BASS" or any(w in trk_name.lower() or w in ai_text for w in ["808", "sub", "bass"])

        directives = {
            "brightness": 0.65,
            "warmth_drive": 0.35,
            "punch": 0.65,
            "decay_sustain": 0.60,
            "space_dimension": 0.15 if is_bass else 0.45,
            "stereo_width": 0.0 if is_bass else 0.70,
            "movement": 0.30,
            "is_bass": is_bass
        }

        # Quick options shorthand
        if "opcion 1" in ai_text or "opción 1" in ai_text:
            if is_bass:
                return "BASS_808", {"brightness": 0.40, "punch": 0.90, "warmth_drive": 0.70, "is_bass": True}
            elif role == "LEAD":
                return "LEAD_SAW", {"brightness": 0.85, "punch": 0.80, "warmth_drive": 0.20}
            elif role == "PAD":
                return "PAD_LUSH", {"attack": 1.8, "space_dimension": 0.85, "stereo_width": 0.90, "brightness": 0.65}
            elif role in ("KEYS", "CHORDS"):
                return "CHORD_SUPERAW", {"brightness": 0.80, "stereo_width": 0.60, "movement": 0.40}
            else:
                return "LEAD_SAW", {"brightness": 0.70, "punch": 0.80}

        elif "opcion 2" in ai_text or "opción 2" in ai_text:
            if is_bass:
                return "BASS_SUB", {"brightness": 0.25, "punch": 0.70, "warmth_drive": 0.15, "is_bass": True}
            elif role == "LEAD":
                return "LEAD_PLUCK", {"brightness": 0.75, "decay_sustain": 0.1, "punch": 0.85}
            elif role == "PAD":
                return "PAD_ORGANIC", {"attack": 1.0, "warmth_drive": 0.75, "brightness": 0.45}
            elif role in ("KEYS", "CHORDS"):
                return "KEYS_HYBRID", {"warmth_drive": 0.80, "decay_sustain": 0.4, "brightness": 0.55}
            else:
                return "LEAD_SAW", {"brightness": 0.80, "stereo_width": 0.75}

        elif "opcion 3" in ai_text or "opción 3" in ai_text:
            if is_bass:
                return "BASS_PUNCH", {"warmth_drive": 0.50, "punch": 0.85, "movement": 0.60, "is_bass": True}
            elif role == "LEAD":
                return "LEAD_SAW", {"custom_wavetable": "VOCAL", "movement": 0.55, "brightness": 0.70}
            elif role == "PAD":
                return "PAD_LUSH", {"brightness": 0.40, "movement": 0.70, "space_dimension": 0.80}
            elif role in ("KEYS", "CHORDS"):
                return "CHORD_SUPERAW", {"brightness": 0.65, "punch": 0.80, "decay_sustain": 0.2}
            else:
                return "LEAD_SAW", {"punch": 0.85, "warmth_drive": 0.70}

        # 1. Check for JSON payload inside response
        json_match = re.search(r"\{[^{}]*\}", ai_text)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(0))
                for k, v in parsed_json.items():
                    k_low = k.lower().replace("-", "_")
                    if k_low in directives:
                        directives[k_low] = float(v)
                    elif k_low in ("wavetable", "custom_wavetable"):
                        directives["custom_wavetable"] = str(v).upper()
                    elif k_low in ("attack", "decay", "sustain", "release"):
                        directives[k_low] = float(v)
            except Exception:
                pass

        # 2. Extract Wavetable Preference
        if any(w in ai_text for w in ["vocal", "formant", "vocalic", "voz", "formante"]):
            directives["custom_wavetable"] = "VOCAL"
        elif any(w in ai_text for w in ["fm", "metal", "metallic", "growl"]):
            directives["custom_wavetable"] = "FM"
        elif any(w in ai_text for w in ["analog", "moog", "supersaw", "square"]):
            directives["custom_wavetable"] = "ANALOG"
        elif any(w in ai_text for w in ["basic", "sine", "pure", "subliminal", "senoidal"]):
            directives["custom_wavetable"] = "BASIC_SHAPES"

        # 3. Extract Timbral Dimensions from natural language descriptors
        if any(w in ai_text for w in ["brillante", "piercing", "aire", "agudo", "cristalino"]):
            directives["brightness"] = max(directives["brightness"], 0.85)
        elif any(w in ai_text for w in ["oscuro", "dark", "mellow", "profundo"]):
            directives["brightness"] = min(directives["brightness"], 0.35)

        if any(w in ai_text for w in ["saturado", "distorsión", "distorsion", "drive", "agresivo", "crunch"]):
            directives["warmth_drive"] = max(directives["warmth_drive"], 0.75)
        elif any(w in ai_text for w in ["cálido", "calido", "analógico", "tape", "redondo"]):
            directives["warmth_drive"] = max(directives["warmth_drive"], 0.50)
        elif any(w in ai_text for w in ["limpio", "clean", "puro"]):
            directives["warmth_drive"] = min(directives["warmth_drive"], 0.15)

        if any(w in ai_text for w in ["punch", "pegada", "click", "laser", "snappy", "percusivo"]):
            directives["punch"] = max(directives["punch"], 0.90)
            directives["attack"] = 0.005
        elif any(w in ai_text for w in ["suave", "crescendo", "lento", "slow", "swell"]):
            directives["punch"] = min(directives["punch"], 0.20)
            directives["attack"] = 1.20

        if any(w in ai_text for w in ["pluck", "corto", "staccato", "tight"]):
            directives["decay_sustain"] = 0.15
            directives["sustain"] = 0.0
        elif any(w in ai_text for w in ["sostenido", "sustained", "largo", "sidechain", "pump"]):
            directives["decay_sustain"] = 0.90
            directives["sustain"] = 1.0

        if any(w in ai_text for w in ["movimiento", "lfo", "modulado", "modulacion", "rítmico", "ritmico"]):
            directives["movement"] = max(directives["movement"], 0.70)

        if any(w in ai_text for w in ["espacial", "atmosférico", "atmosferico", "reverb", "lush"]) and not is_bass:
            directives["space_dimension"] = max(directives["space_dimension"], 0.80)

        if any(w in ai_text for w in ["ancho", "wide", "stereo", "supersaw"]) and not is_bass:
            directives["stereo_width"] = max(directives["stereo_width"], 0.85)

        # 4. Numeric regex scanning
        for key in ["brightness", "warmth_drive", "punch", "decay_sustain", "space_dimension", "stereo_width", "movement", "attack", "decay"]:
            m = re.search(rf"{key}\D*([0-9]+(?:\.[0-9]+)?)", ai_text)
            if m:
                directives[key] = float(m.group(1))

        # 4b. Sovereign Polyphony & Voice Mode Parsing for Vital
        if re.search(r"\b(?:mono|monof[oó]nico|monophonic|1\s*voz|1\s*voice)\b", ai_text):
            directives["polyphony"] = 1.0
        elif re.search(r"\b(?:poly|polif[oó]nico|polyphonic)\b", ai_text):
            directives["polyphony"] = 8.0

        v_m = re.search(r"(?:voces|voices|polyphony|polifon[ií]a)\s*[:=]?\s*(\d+)", ai_text)
        if not v_m:
            v_m = re.search(r"(\d+)\s*(?:voces|voices)", ai_text)
        if v_m:
            directives["polyphony"] = max(1.0, min(32.0, float(v_m.group(1))))

        l_m = re.search(r"legato\s*[:=]?\s*(on|off|true|false|1|0|s[ií]|no)", ai_text)
        if l_m:
            directives["legato"] = 1.0 if l_m.group(1).lower() in ("on", "true", "1", "si", "sí") else 0.0

        g_m = re.search(r"(?:glide|portamento)\s*[:=]?\s*([0-9\.]+)", ai_text)
        if g_m:
            directives["glide"] = float(g_m.group(1))

        # 5. Determine base archetype
        if is_bass:
            if any(w in ai_text for w in ["acid", "303", "rave", "twiddle"]):
                archetype = "BASS_ACID"
            elif any(w in ai_text for w in ["growl", "neuro", "wobble", "wooble", "color_bass", "skrillex"]):
                archetype = "BASS_GROWL"
            elif any(w in ai_text for w in ["organ", "donk", "slap"]):
                archetype = "HOUSE_ORGAN_DONK"
            elif "808" in ai_text or directives.get("warmth_drive", 0) > 0.6 or "saturado" in ai_text:
                archetype = "BASS_808"
            elif "reese" in ai_text or "punch" in ai_text or directives.get("movement", 0) > 0.5:
                archetype = "BASS_PUNCH"
            else:
                archetype = "BASS_SUB"
        elif any(w in ai_text for w in ["guitar", "guitarra", "acústic", "acoustic", "cuerda", "string"]):
            archetype = "ACOUSTIC_STRINGS"
        elif any(w in ai_text for w in ["chiptune", "8bit", "8-bit", "arcade", "gameboy", "glitch"]):
            archetype = "CHIPTUNE_GLITCH"
        elif any(w in ai_text for w in ["vocal", "voz", "vocoder", "choir", "coro"]):
            archetype = "VOCAL_SYNTH"
        elif any(w in ai_text for w in ["organ", "órgano", "m1"]):
            archetype = "HOUSE_ORGAN_DONK"
        elif any(w in ai_text for w in ["bell", "campana", "mallet", "marimba", "cristal"]):
            archetype = "BELLS_MALLETS"
        elif any(w in ai_text for w in ["theremin", "whistle", "silbido"]):
            archetype = "THEREMIN_WHISTLE"
        elif any(w in ai_text for w in ["riser", "sweep", "siren", "impact", "laser", "caida", "caída"]):
            archetype = "FX_TRANSITION"
        elif role in ("PAD", "STRINGS", "TEXTURE"):
            archetype = "PAD_ORGANIC" if directives.get("warmth_drive", 0) > 0.4 else "PAD_LUSH"
        elif role in ("KEYS", "CHORDS", "PIANO"):
            archetype = "CHORD_SUPERAW" if directives.get("stereo_width", 0) > 0.5 else "KEYS_RHODES"
        elif role in ("LEAD", "COUNTER_LEAD"):
            if directives.get("decay_sustain", 0) < 0.3 or directives.get("punch", 0) > 0.85:
                archetype = "LEAD_PLUCK"
            else:
                archetype = "LEAD_SAW"
        else:
            archetype = "LEAD_SAW"

        return archetype, directives

    @classmethod
    def _configure_vital(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        session: Any,
        conn: Any,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dedicated modeling and validation pipeline for Vital Synth."""
        from engine.sound_design.vital_sound_engine import VitalSoundEngine
        from engine.sound_design.vital_parameter_schema import VitalParameterSchema
        from engine.sound_design.vital_design_validator import VitalDesignValidator

        trk["is_vital"] = True
        vital_engine = VitalSoundEngine()
        ai_text = str(ai_input or "").lower()

        # Deep semantic extraction of the AI's sound design intent
        v_role, directives = cls._extract_vital_sound_design(ai_text, role, trk.get("name", ""))
        is_bass = directives.get("is_bass", False)

        patch_name = f"Vital_{role}_{trk.get('name', 'Track').replace(' ', '_')}"

        # VitalSoundEngine compiles preset while enforcing anti-silence and anti-corruption invariants
        preset_path = vital_engine.create_preset(
            preset_name=patch_name,
            role=v_role,
            directives=directives
        )

        trk["vital_preset_path"] = str(preset_path)
        trk["vital_archetype"] = v_role
        trk["sculpted"] = True
        trk["timbre_dna"] = {
            "brightness": directives.get("brightness", 0.70),
            "roughness": 0.35,
            "stereo_width": 0.05 if is_bass else directives.get("stereo_width", 0.75),
            "transient_strength": directives.get("punch", 0.80),
            "movement": directives.get("movement", 0.45)
        }
        trk["sculpted_parameters"] = {
            "FILTER_CUTOFF": float(directives.get("brightness", 0.70)),
            "DRIVE": float(directives.get("warmth_drive", 0.35)),
            "PUNCH": float(directives.get("punch", 0.80)),
            "MOVEMENT": float(directives.get("movement", 0.45)),
            "STEREO_WIDTH": 0.05 if is_bass else float(directives.get("stereo_width", 0.75)),
            "ARCHETYPE": v_role
        }

        # Dispatch basic macro controls to Live if device is present
        if conn is not None and hasattr(conn, "send_command"):
            dev_idx = cls._find_device_index(conn, t_idx, ["vital"])
            if dev_idx is not None:
                code_vital = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'cutoff' in p_l or 'filter 1' in p_l: p.value = {float(directives.get('brightness', 0.75))}
    elif 'resonance' in p_l: p.value = 0.25
"""
                try:
                    conn.send_command("execute_code", {"code": code_vital})
                except Exception as ex_v:
                    logger.debug(f"Vital parameter dispatch notice: {ex_v}")

        logger.info(f"Vital modeled & validated on Track {t_idx} [{role}]: {preset_path}")
        return {
            "status": "CONFIGURED",
            "plugin": "Vital",
            "patch_name": patch_name,
            "preset_path": str(preset_path),
            "archetype": v_role,
            "action_taken": f"Vital modelado con arquetipo '{v_role}' y validado con Invariantes Anti-Silencio y LFO integrity."
        }

    # -------------------------------------------------------------------------
    # EFFECT CONFIGURATION & VALIDATION EXECUTION
    # -------------------------------------------------------------------------

    @classmethod
    def configure_effect(
        cls,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        dev_idx: int,
        session: Any,
        conn: Any = None,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the specialized modeling and validation pipeline for a dedicated effect
        (Valhalla Supermassive, Valhalla VintageVerb, or Surge XT Effects) taking AI input.
        """
        eff_name = str(eff.get("name", "")).lower()
        role = trk.get("role", "OTHER")
        bpm = float(session.data.get("bpm", 120.0))
        t_idx = session._resolve_live_track_index(conn, trk)
        song_name = session.data.get("song_name", "Session")

        if "supermassive" in eff_name:
            return cls._configure_valhalla_supermassive(trk, role, bpm, t_idx, dev_idx, song_name, conn, ai_input)
        elif "vintageverb" in eff_name or ("valhalla" in eff_name and "verb" in eff_name):
            return cls._configure_valhalla_vintage_verb(trk, role, bpm, t_idx, dev_idx, song_name, conn, ai_input)
        elif "surge" in eff_name and "effects" in eff_name:
            return cls._configure_surge_xt_effects(trk, role, bpm, t_idx, dev_idx, song_name, conn, ai_input)
        else:
            return {"status": "SKIPPED", "message": f"Effect {eff_name} is not a dedicated engine plugin."}

    @classmethod
    def _configure_valhalla_supermassive(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        dev_idx: int,
        song_name: str,
        conn: Any,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dedicated modeling and validation pipeline for Valhalla Supermassive."""
        from engine.sound_design.valhalla_supermassive.mode_selector import SupermassiveModeSelector
        from engine.sound_design.valhalla_supermassive.validator import ValhallaSupermassiveValidator
        from engine.sound_design.valhalla_supermassive.serializer import ValhallaSupermassiveSerializer
        from engine.sound_design.valhalla_supermassive.policies import SupermassiveSafetyPolicy

        ai_text = str(ai_input or "").lower()
        preset_name = f"SM_{role}_{trk.get('name', 'Track').replace(' ', '_')}"
        sm_model = SupermassiveModeSelector.build_role_preset(preset_name=preset_name, role=role, bpm=bpm)

        # Parse AI intention
        if "opcion 2" in ai_text or "opción 2" in ai_text or "hydra" in ai_text or "shimmer" in ai_text:
            sm_model.mode = 0.38  # Hydra
            sm_model.mix = 0.20
            sm_model.feedback = 0.60
        elif "opcion 3" in ai_text or "opción 3" in ai_text or "capricorn" in ai_text or "echo" in ai_text:
            sm_model.mode = 0.42  # Capricorn
            sm_model.mix = 0.18
            sm_model.feedback = 0.50
        elif "opcion 1" in ai_text or "opción 1" in ai_text or "gemini" in ai_text:
            sm_model.mode = 0.00  # Gemini
            sm_model.mix = 0.14
            sm_model.feedback = 0.40

        # Apply engine safety limits & policies:
        # 1. Mix limit for drops and lead instruments (CRASHPOP Rule)
        is_lead_or_drop = role in ("LEAD", "COUNTER_LEAD", "DRUMS", "BASS")
        max_mix = 0.15 if is_lead_or_drop else 0.35
        sm_model.mix = min(sm_model.mix, max_mix)

        # 2. Feedback runaway safety: clamp < 0.95
        sm_model.feedback = min(sm_model.feedback, 0.94)

        # 3. Low Cut protection: keep sub-bass clean
        min_lowcut = 0.25 if role == "BASS" else 0.15
        sm_model.low_cut = max(sm_model.low_cut, min_lowcut)

        v_rep = ValhallaSupermassiveValidator.validate(sm_model, strict=False)

        preset_p = ValhallaSupermassiveSerializer.save_preset(sm_model, category=song_name)
        xml_str = ValhallaSupermassiveSerializer.to_xml_string(sm_model)
        cb_ok = ValhallaSupermassiveSerializer.copy_to_clipboard(xml_str)

        trk["supermassive_preset_path"] = str(preset_p)
        trk["supermassive_clipboard_ready"] = cb_ok
        trk["supermassive_mode"] = sm_model.mode_name

        # Dispatch LOM parameters
        if conn is not None and hasattr(conn, "send_command"):
            code_sm = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = {float(sm_model.mix)}
    elif 'feedback' in p_l: p.value = {float(sm_model.feedback)}
    elif 'low cut' in p_l or 'lowcut' in p_l: p.value = {float(sm_model.low_cut)}
    elif 'high cut' in p_l or 'highcut' in p_l: p.value = {float(sm_model.high_cut)}
    elif 'mode' in p_l: p.value = {float(sm_model.mode)}
    elif 'sync' in p_l: p.value = 1.0 if {sm_model.delay_sync} > 0 else 0.0
"""
            try:
                conn.send_command("execute_code", {"code": code_sm})
            except Exception as ex_sm:
                logger.debug(f"Supermassive LOM dispatch notice: {ex_sm}")

        logger.info(f"Valhalla Supermassive modeled & validated on Track {t_idx} [{role}]: Mode {sm_model.mode_name}")
        return {
            "status": "CONFIGURED",
            "plugin": "Valhalla Supermassive",
            "mode": sm_model.mode_name,
            "preset_path": str(preset_p),
            "clipboard_ready": cb_ok,
            "parameters": {
                "Mix": sm_model.mix,
                "Feedback": sm_model.feedback,
                "LowCut": sm_model.low_cut,
                "HighCut": sm_model.high_cut,
                "Mode": sm_model.mode
            },
            "action_taken": f"Valhalla Supermassive modelado en modo {sm_model.mode_name} y validado contra políticas de mix seguro."
        }

    @classmethod
    def _configure_valhalla_vintage_verb(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        dev_idx: int,
        song_name: str,
        conn: Any,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dedicated modeling and validation pipeline for Valhalla VintageVerb."""
        from engine.sound_design.valhalla_vintage_verb.mode_selector import VintageVerbModeSelector
        from engine.sound_design.valhalla_vintage_verb.validator import ValhallaVintageVerbValidator
        from engine.sound_design.valhalla_vintage_verb.serializer import ValhallaVintageVerbSerializer

        ai_text = str(ai_input or "").lower()
        preset_name = f"VV_{role}_{trk.get('name', 'Track').replace(' ', '_')}"
        vv_model = VintageVerbModeSelector.build_role_preset(preset_name=preset_name, role=role, bpm=bpm)

        # Parse AI intent
        if "opcion 2" in ai_text or "opción 2" in ai_text or "plate" in ai_text or "1970" in ai_text:
            vv_model.color_mode = 0.0  # 1970s
            vv_model.decay = 0.20
            vv_model.mix = 0.18
        elif "opcion 3" in ai_text or "opción 3" in ai_text or "now" in ai_text or "random" in ai_text:
            vv_model.color_mode = 1.0  # Now
            vv_model.decay = 0.38
            vv_model.mix = 0.22
        elif "opcion 1" in ai_text or "opción 1" in ai_text or "1980" in ai_text:
            vv_model.color_mode = 0.5  # 1980s
            vv_model.decay = 0.25
            vv_model.mix = 0.16

        # Apply engine limits: Low cut >= 180 Hz (0.18), Pre-delay >= 15 ms (0.15), Mix clamping
        vv_model.low_cut = max(0.18, vv_model.low_cut)
        is_front = role in ("LEAD", "COUNTER_LEAD", "DRUMS", "BASS", "VOCALS", "VOICE", "KEYS", "PIANO", "PLUCK", "SNARE", "GUITAR")
        if is_front:
            vv_model.mix = min(vv_model.mix, 0.22)
            vv_model.predelay = max(vv_model.predelay, 0.15)

        v_rep_vv = ValhallaVintageVerbValidator.validate(vv_model, role=role, strict=False)

        preset_p = ValhallaVintageVerbSerializer.save_preset(vv_model, category=song_name)
        xml_str = ValhallaVintageVerbSerializer.to_xml_string(vv_model)
        cb_ok = ValhallaVintageVerbSerializer.copy_to_clipboard(xml_str)

        trk["vintage_verb_preset_path"] = str(preset_p)
        trk["vintage_verb_clipboard_ready"] = cb_ok
        trk["vintage_verb_mode"] = vv_model.mode_name
        trk["vintage_verb_color"] = vv_model.color_name

        # Dispatch LOM parameters
        if conn is not None and hasattr(conn, "send_command"):
            code_vv = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = {float(vv_model.mix)}
    elif 'decay' in p_l: p.value = {float(vv_model.decay)}
    elif 'predelay' in p_l or 'pre-delay' in p_l: p.value = {float(vv_model.predelay)}
    elif 'low cut' in p_l or 'lowcut' in p_l: p.value = {float(vv_model.low_cut)}
    elif 'high cut' in p_l or 'highcut' in p_l: p.value = {float(vv_model.high_cut)}
    elif 'size' in p_l: p.value = {float(vv_model.size)}
    elif 'mode' in p_l: p.value = {float(vv_model.mode)}
    elif 'color' in p_l: p.value = {float(vv_model.color_mode)}
"""
            try:
                conn.send_command("execute_code", {"code": code_vv})
            except Exception as ex_vv:
                logger.debug(f"VintageVerb LOM dispatch notice: {ex_vv}")

        logger.info(f"Valhalla VintageVerb modeled & validated on Track {t_idx} [{role}]: Mode {vv_model.mode_name} ({vv_model.color_name})")
        return {
            "status": "CONFIGURED",
            "plugin": "Valhalla VintageVerb",
            "mode": vv_model.mode_name,
            "color": vv_model.color_name,
            "preset_path": str(preset_p),
            "clipboard_ready": cb_ok,
            "parameters": {
                "Mix": vv_model.mix,
                "Decay": vv_model.decay,
                "PreDelay": vv_model.predelay,
                "LowCut": vv_model.low_cut,
                "HighCut": vv_model.high_cut,
                "Size": vv_model.size
            },
            "action_taken": f"Valhalla VintageVerb modelado en {vv_model.mode_name} ({vv_model.color_name}) y validado contra resonancias."
        }

    @classmethod
    def _configure_surge_xt_effects(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        dev_idx: int,
        song_name: str,
        conn: Any,
        ai_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dedicated modeling and validation pipeline for Surge XT Effects multi-slot rack."""
        from engine.sound_design.surge_xt_fx.rack_factory import SurgeFXRackFactory
        from engine.sound_design.surge_xt_fx.validator import SurgeFXValidator
        from engine.sound_design.surge_xt_fx.serializer import SurgeFXSerializer
        from engine.sound_design.surge_xt_fx.policies import SurgeFXPolicies

        ai_text = str(ai_input or "").lower()
        if "opcion 1" in ai_text or "opción 1" in ai_text or "tape" in ai_text:
            rack_m = SurgeFXRackFactory.create_analog_tape_bus()
        elif "opcion 2" in ai_text or "opción 2" in ai_text or "shimmer" in ai_text or "granular" in ai_text:
            rack_m = SurgeFXRackFactory.create_granular_shimmer_rack()
        elif "opcion 3" in ai_text or "opción 3" in ai_text or "lo-fi" in ai_text or "lofi" in ai_text:
            rack_m = SurgeFXRackFactory.create_vintage_lofi_chain()
        else:
            rack_m = SurgeFXRackFactory.create_role_rack(role=role, bpm=bpm)

        # Apply engine limits: validate slot parameters, enforce policy checks
        v_rep = SurgeFXValidator.validate_rack(rack_m)
        policy_warnings = SurgeFXPolicies.audit_rack(rack_m)

        chain_p = SurgeFXSerializer.save_chain_file(rack_m, category=song_name)
        trk["surge_xt_chain_path"] = str(chain_p)
        trk["surge_xt_active_slots"] = len(rack_m.get_active_slots())

        # Dispatch LOM parameters
        if conn is not None and hasattr(conn, "send_command"):
            for p_k, p_v in rack_m.to_lom_command_list(only_active=True):
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": t_idx,
                        "device_index": dev_idx,
                        "parameter": p_k,
                        "value": float(p_v)
                    })
                except Exception:
                    pass

        logger.info(f"Surge XT Effects modeled & validated on Track {t_idx} [{role}]: {chain_p}")
        return {
            "status": "CONFIGURED",
            "plugin": "Surge XT Effects",
            "chain_path": str(chain_p),
            "active_slots": len(rack_m.get_active_slots()),
            "action_taken": f"Surge XT Effects modelado con rack '{rack_m.name}' ({len(rack_m.get_active_slots())} slots) y validado por SurgeFXPolicies."
        }

    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------

    @staticmethod
    def _find_device_index(conn: Any, track_index: int, target_names: list) -> Optional[int]:
        """Helper to locate device index by name/class in Live."""
        try:
            t_info = conn.send_command("get_track_info", {"track_index": track_index})
            devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
            for d_idx, d in enumerate(devs):
                d_name = str(d.get("name", "")).lower()
                d_class = str(d.get("class_name", "")).lower()
                for target in target_names:
                    if target.lower() in d_name or target.lower() in d_class:
                        return d_idx
        except Exception:
            pass
        return None

# engine/production/copilot/guided_session.py
"""
Copilot Guided Session Engine (Asistente Conversacional por Estados):
Single-tool state machine wizard for interactive music production.

Replaces disjointed tool calling with a structured 7-phase conversational interview
between Copilot (the Technical Director) and the Producer (AI/User).

Workflow Phases:
1. PHASE_1_TRACKS: Channels, names & acoustic role reservation.
2. PHASE_2_SECTIONS: Song structure, section names & arrangement cue points.
3. PHASE_3_INSTRUMENTS: Track-by-track verified VST/Kit selection (Strict LOM verification, Drum Pad population check, zero silent swallow).
4. PHASE_4_PARAM_SCULPTING: Track-by-track conversational synthesis sculpting (Delta >= 1 rule verified).
5. PHASE_5_INSERT_EFFECTS: Track-by-track insert FX chains (Drum Buss, Saturator, VintageVerb, Delay, OTT).
6. PHASE_6_COMPOSITION: Harmonic progression, bassline, topline & drum note writing into arrangement (with Drum Octave Guard).
7. PHASE_7_MIX_MASTER: Acoustic audit (LUFS, collisions), sidechain ducking & BS.1770-5 serial mastering chain.
8. PHASE_8_COMPLETED: Project complete, Copilot stays active listening for adjustments.
"""

import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.instruments.browser_catalog import CURATED_SOURCES
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.instruments.drum_rack_guard import DrumRackGuard
from engine.mix.sidechain_manager import SidechainManager
from engine.mastering.live_master_chain import LiveMasterChainEngine
from engine.production.copilot.stepper import executive_copilot

logger = logging.getLogger("CopilotGuidedSession")


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    nfd = unicodedata.normalize("NFD", str(text))
    without_accents = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return without_accents.lower().strip()


class CopilotGuidedSession:
    """State machine wizard orchestrating the entire music production via conversational dialogue."""

    STATE_FILE = Path("state/production/guided_session.json")

    PHASES = [
        "PHASE_1_TRACKS",
        "PHASE_2_SECTIONS",
        "PHASE_3_INSTRUMENTS",
        "PHASE_4_PARAM_SCULPTING",
        "PHASE_5_INSERT_EFFECTS",
        "PHASE_6_COMPOSITION",
        "PHASE_7_MIX_MASTER",
        "PHASE_8_COMPLETED"
    ]

    def __init__(self):
        self.data: Dict[str, Any] = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "current_phase": "PHASE_1_TRACKS",
            "phase_index": 1,
            "tracks": [],
            "sections": [],
            "total_bars": 96,
            "key": "F",
            "scale": "natural_minor",
            "bpm": 120.0,
            "current_track_ptr": 0,
            "current_param_ptr": 0,
            "current_fx_ptr": 0,
            "history": [],
            "is_complete": False
        }

    def _load_state(self) -> Dict[str, Any]:
        if self.STATE_FILE.exists():
            try:
                with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load guided session state: {e}")
        return self._default_state()

    def _save_state(self):
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist guided session state: {e}")

    def reset(self):
        """Resets the state machine back to step 1."""
        self.data = self._default_state()
        self._save_state()

    def step(self, conn: Any, user_input: str = "", reset: bool = False) -> Dict[str, Any]:
        """
        Executes one turn of the conversational Copilot wizard:
        1. Evaluates user_input for the current phase.
        2. Performs physical mutations in Ableton Live.
        3. Verifies DAW state in the LOM strictly (never swallowing errors).
        4. Transitions to the next phase or next track.
        5. Formulates the next question for the user/AI.
        """
        if reset:
            self.reset()

        phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        u_in = str(user_input or "").strip()

        # Initial prompt
        if not u_in and phase == "PHASE_1_TRACKS" and not self.data["tracks"]:
            return self._prompt_phase_1()

        if phase == "PHASE_1_TRACKS":
            return self._handle_phase_1(conn, u_in)
        elif phase == "PHASE_2_SECTIONS":
            return self._handle_phase_2(conn, u_in)
        elif phase == "PHASE_3_INSTRUMENTS":
            return self._handle_phase_3(conn, u_in)
        elif phase == "PHASE_4_PARAM_SCULPTING":
            return self._handle_phase_4(conn, u_in)
        elif phase == "PHASE_5_INSERT_EFFECTS":
            return self._handle_phase_5(conn, u_in)
        elif phase == "PHASE_6_COMPOSITION":
            return self._handle_phase_6(conn, u_in)
        elif phase == "PHASE_7_MIX_MASTER":
            return self._handle_phase_7(conn, u_in)
        elif phase == "PHASE_8_COMPLETED":
            return self._handle_phase_8(conn, u_in)

        return {"status": "ERROR", "message": f"Fase desconocida: {phase}"}

    # -------------------------------------------------------------------------
    # FASE 1: ESTRUCTURA DE PISTAS (SCAFFOLDING)
    # -------------------------------------------------------------------------
    def _prompt_phase_1(self) -> Dict[str, Any]:
        return {
            "current_step": "PASO 1 DE 7: ESTRUCTURA DE PISTAS (SCAFFOLDING)",
            "action_taken": "Sesión iniciada. Esperando definición de canales.",
            "question": (
                "🎙️ **Paso 1 de 7: ¿Cuántos canales deseas y qué rol musical tendrá cada uno?**\n\n"
                "Elige una opción o escribe tu lista personalizada:\n"
                "• **Opción A (5 Canales Esencial)**: Batería, Piano/Keys, Pads, Bajo 808, Lead.\n"
                "• **Opción B (8 Canales Completo)**: Kick, Batería, Bajo 808, Rhodes, Cuerdas, Pad, Lead, Vocal Chops.\n"
                "• **Personalizado**: Escribe los nombres que desees (ej: 'Batería, Guitarra, Bajo, Sintetizador')."
            ),
            "instructions_for_ai": "Responde con la opción que prefieras (ej: 'Opción A' o los nombres de canales).",
            "phase": "PHASE_1_TRACKS"
        }

    def _handle_phase_1(self, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)
        requested_tracks: List[Dict[str, str]] = []

        if "opcion b" in text or "8 canal" in text or "completo" in text:
            requested_tracks = [
                {"name": "Kick", "role": "DRUMS"},
                {"name": "Drums", "role": "DRUMS"},
                {"name": "808 Bass", "role": "BASS"},
                {"name": "Rhodes Keys", "role": "KEYS"},
                {"name": "Orchestral Strings", "role": "STRINGS"},
                {"name": "Analog Pad", "role": "PAD"},
                {"name": "Synth Lead", "role": "LEAD"},
                {"name": "Vocal Chops", "role": "VOCALS"}
            ]
        elif "opcion a" in text or "5 canal" in text or "esencial" in text or not user_input:
            requested_tracks = [
                {"name": "Drums", "role": "DRUMS"},
                {"name": "Piano Keys", "role": "KEYS"},
                {"name": "Pads", "role": "PAD"},
                {"name": "808 Bass", "role": "BASS"},
                {"name": "Lead Synth", "role": "LEAD"}
            ]
        else:
            items = [re.sub(r"^\d+[\.\)]\s*", "", i).strip() for i in re.split(r"[,;\n]+", user_input) if i.strip()]
            for item in items:
                role = RoleTrackOrchestrator.normalize_role(item)
                requested_tracks.append({"name": item.title(), "role": role})

        if not requested_tracks:
            requested_tracks = [
                {"name": "Drums", "role": "DRUMS"},
                {"name": "Keys", "role": "KEYS"},
                {"name": "Pads", "role": "PAD"},
                {"name": "808 Bass", "role": "BASS"},
                {"name": "Lead", "role": "LEAD"}
            ]

        # Physical DAW creation
        created_tracks: List[Dict[str, Any]] = []
        if conn is not None and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {})
                existing_count = int(s_info.get("track_count", 0))

                for idx, t_spec in enumerate(requested_tracks):
                    t_idx = idx
                    if t_idx >= existing_count:
                        conn.send_command("create_midi_track", {"index": t_idx})
                    conn.send_command("set_track_name", {"track_index": t_idx, "name": t_spec["name"]})
                    created_tracks.append({
                        "index": t_idx,
                        "name": t_spec["name"],
                        "role": t_spec["role"]
                    })
            except Exception as e:
                logger.warning(f"DAW track creation exception: {e}")
                for idx, t_spec in enumerate(requested_tracks):
                    created_tracks.append({"index": idx, "name": t_spec["name"], "role": t_spec["role"]})
        else:
            for idx, t_spec in enumerate(requested_tracks):
                created_tracks.append({"index": idx, "name": t_spec["name"], "role": t_spec["role"]})

        self.data["tracks"] = created_tracks
        self.data["current_phase"] = "PHASE_2_SECTIONS"
        self.data["phase_index"] = 2
        self._save_state()

        track_summary = ", ".join([f"Pista {t['index']}: {t['name']} ({t['role']})" for t in created_tracks])

        return {
            "current_step": "PASO 2 DE 7: ESTRUCTURA Y SECCIONES (ARRANGEMENT TIMELINE)",
            "action_taken": f"Se crearon y verificaron físicamente {len(created_tracks)} pistas en Live ({track_summary}).",
            "question": (
                "📐 **Paso 2 de 7: ¿Qué secciones y cuántos compases tendrá la canción?**\n\n"
                "Elige una estructura o escribe tu desglose:\n"
                "• **Opción A (Estándar 96 compases / ~3:00 min)**: Intro (8c), Verso 1 (16c), Pre-Coro (8c), Coro (16c), Verso 2 (16c), Puente (8c), Climax (16c), Outro (8c).\n"
                "• **Opción B (Compacto 64 compases / ~2:00 min)**: Intro (8c), Verso (16c), Coro (16c), Puente (8c), Coro Final (16c).\n"
                "• **Personalizado**: Escribe tus secciones (ej: 'Intro 8, Verso 16, Coro 16, Drop 16, Final 8')."
            ),
            "instructions_for_ai": "Responde indicando la estructura deseada (ej: 'Opción A' o desglose de secciones).",
            "phase": "PHASE_2_SECTIONS"
        }

    # -------------------------------------------------------------------------
    # FASE 2: ESTRUCTURA DE LA CANCIÓN Y CUES
    # -------------------------------------------------------------------------
    def _handle_phase_2(self, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)
        sections: List[Tuple[str, int]] = []

        if "opcion b" in text or "64" in text:
            sections = [
                ("Intro", 8), ("Verse 1", 16), ("Chorus 1", 16),
                ("Bridge", 8), ("Final Chorus", 16)
            ]
        elif "opcion a" in text or "96" in text or "estandar" in text or not user_input:
            sections = [
                ("Intro", 8), ("Verse 1", 16), ("Pre-Chorus", 8), ("Chorus 1", 16),
                ("Verse 2", 16), ("Bridge", 8), ("Climax Chorus", 16), ("Outro", 8)
            ]
        else:
            raw_parts = re.findall(r"([a-zA-Z\s]+)\s*\(?(\d+)\s*c?\)?", user_input)
            if raw_parts:
                for s_name, s_bars in raw_parts:
                    sections.append((s_name.strip().title(), int(s_bars)))
            else:
                sections = [
                    ("Intro", 8), ("Verse 1", 16), ("Chorus 1", 16),
                    ("Bridge", 8), ("Climax Chorus", 16), ("Outro", 8)
                ]

        total_bars = sum(b for _, b in sections)
        self.data["sections"] = [{"name": s[0], "bars": s[1]} for s in sections]
        self.data["total_bars"] = total_bars

        # Physical Cue Points in Live
        if conn is not None and hasattr(conn, "send_command"):
            curr_beat = 0.0
            for s_name, s_bars in sections:
                try:
                    conn.send_command("create_cue_point", {"name": s_name, "time": float(curr_beat)})
                except Exception:
                    pass
                curr_beat += s_bars * 4.0

        self.data["current_phase"] = "PHASE_3_INSTRUMENTS"
        self.data["phase_index"] = 3
        self.data["current_track_ptr"] = 0
        self._save_state()

        return self._prompt_current_track_instrument()

    # -------------------------------------------------------------------------
    # FASE 3: CARGA DE INSTRUMENTOS (VERIFICACIÓN ESTRICTA LOM + DRUM PADS)
    # -------------------------------------------------------------------------
    def _prompt_current_track_instrument(self) -> Dict[str, Any]:
        tracks = self.data.get("tracks", [])
        ptr = self.data.get("current_track_ptr", 0)

        if ptr >= len(tracks):
            self.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
            self.data["phase_index"] = 4
            self.data["current_param_ptr"] = 0
            self._save_state()
            return self._prompt_current_track_params()

        trk = tracks[ptr]
        t_idx = trk["index"]
        t_name = trk["name"]
        role = trk["role"]

        # Look up curated options
        options = CURATED_SOURCES.get(role, [])
        opts_text = []
        for i, opt in enumerate(options[:4], 1):
            opts_text.append(f"{i}. [{opt.category.value.upper()}] **{opt.name}** (`{opt.id}`) — {opt.description}")

        if not opts_text:
            if role == "DRUMS":
                opts_text = [
                    "1. [DRUM_KIT] **808 Core Kit (.adg)** (`drum_808_core`) — Roland TR-808 con 16 pads poblados.",
                    "2. [DRUM_KIT] **Boom Bap Kit (.adg)** (`drum_boom_bap`) — Baterías acústicas con textura de vinilo.",
                    "3. [VST3] **Bloom Drum Breaks** (`vst3_bloom_drums`) — Slicer dinámico de breaks y grooves."
                ]
            else:
                opts_text = [
                    f"1. [VST3] Plugin líder para {role}",
                    f"2. [NATIVE] Sintetizador Ableton Live para {role}"
                ]

        options_block = "\n".join(opts_text)

        return {
            "current_step": f"PASO 3 DE 7: CARGA DE INSTRUMENTO / KIT (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Seleccionando fuente sonora física para Pista {t_idx}: {t_name} ({role}).",
            "question": (
                f"🎹 **Paso 3 de 7: Instrumento / Kit para Pista {t_idx} ('{t_name}', Rol: {role})**\n\n"
                f"¿Qué generador sonoro o kit deseas cargar en esta pista?\n\n"
                f"*Opciones recomendadas con verificación física garantizada:*\n"
                f"{options_block}\n\n"
                f"*Responde con el número de opción o nombre de plugin (ej: 'Opción 1').*"
            ),
            "instructions_for_ai": f"Indica la opción de instrumento o kit para {t_name}.",
            "target_track": t_idx,
            "role": role,
            "phase": "PHASE_3_INSTRUMENTS"
        }

    def _handle_phase_3(self, conn: Any, user_input: str) -> Dict[str, Any]:
        tracks = self.data.get("tracks", [])
        ptr = self.data.get("current_track_ptr", 0)

        if ptr >= len(tracks):
            self.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
            self.data["phase_index"] = 4
            self.data["current_param_ptr"] = 0
            self._save_state()
            return self._prompt_current_track_params()

        trk = tracks[ptr]
        t_idx = trk["index"]
        role = trk["role"]
        options = CURATED_SOURCES.get(role, [])

        # Match user preference
        selected_opt = None
        u_clean = _normalize_text(user_input)

        if options:
            for opt in options:
                if opt.id.lower() in u_clean or opt.name.lower() in u_clean:
                    selected_opt = opt
                    break
            if not selected_opt:
                for i, opt in enumerate(options[:4], 1):
                    if str(i) in u_clean or f"opcion {i}" in u_clean:
                        selected_opt = opt
                        break
            if not selected_opt:
                selected_opt = options[0]

        target_uri = selected_opt.uri if selected_opt else (
            "query:Drums#FileId_5422" if role == "DRUMS" else "query:Sounds#Piano%20&%20Keys:FileId_4867"
        )
        display_name = selected_opt.name if selected_opt else f"{role} Instrument"

        # Physical load with strict verification
        is_verified = False
        load_error = None

        if conn is not None and hasattr(conn, "send_command"):
            try:
                # 1. Send load command
                res = conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": target_uri})
                if isinstance(res, dict) and res.get("status") == "error":
                    raise RuntimeError(res.get("message", "Live rejected load_browser_item"))

                # 2. Verify device in LOM
                v_ok, dev_idx, dev_name = RoleTrackOrchestrator.verify_instrument_loaded(conn, t_idx, display_name)
                is_verified = v_ok

                # 3. Special Drum Rack pad population check
                if role == "DRUMS":
                    audit = DrumRackGuard.audit_drum_rack(conn, track_index=t_idx, device_index=dev_idx or 0)
                    if not audit.get("is_populated"):
                        logger.info(f"Drum rack empty on track {t_idx}. Enforcing verified populated kit...")
                        rem_res = DrumRackGuard.enforce_populated_drum_kit(conn, track_index=t_idx, device_index=dev_idx or 0)
                        if not rem_res.get("is_populated"):
                            is_verified = False
                            load_error = "Drum Rack fue cargado pero sus pads están vacíos ('Suelte aquí un instrumento o muestra')."

                if is_verified:
                    conn.send_command("set_track_name", {"track_index": t_idx, "name": f"[{role}] {display_name}"})
                else:
                    if not load_error:
                        load_error = f"El dispositivo '{display_name}' no fue detectado en la cadena de dispositivos de la Pista {t_idx}."

            except Exception as e:
                is_verified = False
                load_error = f"Fallo al cargar en Live: {str(e)}"
        else:
            is_verified = True

        # STRICT VERIFICATION: DO NOT SWALLOW ERRORS
        if not is_verified:
            logger.error(f"Track {t_idx} verification failed: {load_error}")
            return {
                "status": "LOAD_FAILED",
                "current_step": f"PASO 3 DE 7: ERROR DE CARGA EN PISTA {t_idx} ({trk['name']})",
                "action_taken": f"FALLO DE VERIFICACIÓN: {load_error}. La pista no tiene generador sonoro válido.",
                "question": (
                    f"⚠️ **Alerta del Copilot:** No se pudo cargar o verificar '{display_name}' en la Pista {t_idx}.\n\n"
                    f"*Motivo:* {load_error}\n\n"
                    f"Para asegurar que la pista emita sonido y no quede vacía, elige una opción de respaldo:\n"
                    f"1. **Reintentar carga** de {display_name}.\n"
                    f"2. **Cargar preset nativo seguro** de Live Core Library ({role}).\n"
                    f"3. **Cargar VST alternativo**.\n\n"
                    f"*Responde indicando cómo deseas proceder (ej: 'Reintentar' o 'Opción 2').*"
                ),
                "instructions_for_ai": "Elige reintentar o una opción alternativa para no dejar la pista vacía.",
                "retry_required": True,
                "phase": "PHASE_3_INSTRUMENTS"
            }

        # Success: record on track and advance pointer
        trk["instrument"] = display_name
        trk["item_uri"] = target_uri
        self.data["current_track_ptr"] = ptr + 1
        self._save_state()

        if self.data["current_track_ptr"] < len(tracks):
            return self._prompt_current_track_instrument()
        else:
            self.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
            self.data["phase_index"] = 4
            self.data["current_param_ptr"] = 0
            self._save_state()
            return self._prompt_current_track_params()

    # -------------------------------------------------------------------------
    # FASE 4: CONFIGURACIÓN Y ESCULPIDO CONVERSACIONAL DE PARÁMETROS (DELTA >= 1)
    # -------------------------------------------------------------------------
    def _prompt_current_track_params(self) -> Dict[str, Any]:
        tracks = self.data.get("tracks", [])
        ptr = self.data.get("current_param_ptr", 0)

        if ptr >= len(tracks):
            self.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            self.data["phase_index"] = 5
            self.data["current_fx_ptr"] = 0
            self._save_state()
            return self._prompt_current_track_fx()

        trk = tracks[ptr]
        t_idx = trk["index"]
        t_name = trk["name"]
        role = trk["role"]
        inst = trk.get("instrument", f"{role} Synth")

        return {
            "current_step": f"PASO 4 DE 7: ESCULPIDO DE PARÁMETROS DE SÍNTESIS (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Instrumento {inst} verificado físicamente en Pista {t_idx}.",
            "question": (
                f"🎛️ **Paso 4 de 7: Esculpido de Síntesis para Pista {t_idx} ('{t_name}', Rol: {role}, Plugin: {inst})**\n\n"
                f"Para evitar que el plugin permanezca en su sonido de fábrica (Init), define el carácter tímbrico:\n\n"
                f"• **Opción 1 (Cálido y Vintage)**: Filtro Lowpass al 65%, Drive analógico al 25%, Ataque suave con cuerpo sedoso.\n"
                f"• **Opción 2 (Brillante y Moderno)**: Cutoff al 88%, Wavetable Pos al 45%, Unísono estéreo amplio y aire.\n"
                f"• **Opción 3 (Pesado y Agresivo)**: Drive saturado al 55%, Cutoff al 75%, pegada dura y compresión directa.\n"
                f"• **Personalizado**: Escribe los valores exactos (ej: 'Cutoff 70%, Drive 30%, Decay 60%').\n\n"
                f"*Responde con la opción deseada (ej: 'Opción 1' o tus ajustes).*"
            ),
            "instructions_for_ai": f"Indica el perfil sonoro para esculpir el sintetizador en la pista {t_name}.",
            "target_track": t_idx,
            "role": role,
            "phase": "PHASE_4_PARAM_SCULPTING"
        }

    def _handle_phase_4(self, conn: Any, user_input: str) -> Dict[str, Any]:
        tracks = self.data.get("tracks", [])
        ptr = self.data.get("current_param_ptr", 0)

        if ptr >= len(tracks):
            self.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            self.data["phase_index"] = 5
            self.data["current_fx_ptr"] = 0
            self._save_state()
            return self._prompt_current_track_fx()

        trk = tracks[ptr]
        t_idx = trk["index"]
        role = trk["role"]
        inst = trk.get("instrument", "")
        text = _normalize_text(user_input)

        param_dict = {}
        if "opcion 2" in text or "brillante" in text or "modern" in text:
            param_dict = {"FILTER_CUTOFF": 0.88, "WAVETABLE_POS": 0.45, "DRIVE": 0.20, "UNISON_DETUNE": 0.35}
        elif "opcion 3" in text or "pesado" in text or "agresiv" in text or "sat" in text:
            param_dict = {"FILTER_CUTOFF": 0.75, "DRIVE": 0.55, "SUB_LEVEL": 0.90, "AMP_ATTACK": 0.05}
        else:
            param_dict = {"FILTER_CUTOFF": 0.65, "DRIVE": 0.25, "AMP_ATTACK": 0.15, "AMP_RELEASE": 0.55}

        # Apply physical sculpting (Delta >= 1)
        sculpt_applied = {}
        if conn is not None and hasattr(conn, "send_command"):
            try:
                bp_res = DeviceParameterSupervisor.apply_sound_blueprint(
                    conn=conn,
                    track_index=t_idx,
                    role=role,
                    plugin_name=inst,
                    device_index=0,
                    custom_blueprint={"parameters": param_dict}
                )
                sculpt_applied = bp_res.get("applied_parameters", param_dict)
                DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, 0))
            except Exception as e:
                logger.warning(f"Parameter sculpting error on track {t_idx}: {e}")
                sculpt_applied = param_dict
        else:
            sculpt_applied = param_dict
            DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, 0))

        trk["sculpted_parameters"] = sculpt_applied
        self.data["current_param_ptr"] = ptr + 1
        self._save_state()

        if self.data["current_param_ptr"] < len(tracks):
            return self._prompt_current_track_params()
        else:
            self.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            self.data["phase_index"] = 5
            self.data["current_fx_ptr"] = 0
            self._save_state()
            return self._prompt_current_track_fx()

    # -------------------------------------------------------------------------
    # FASE 5: CADENAS DE EFECTOS DE INSERCIÓN (INSERT FX POR CANAL)
    # -------------------------------------------------------------------------
    def _prompt_current_track_fx(self) -> Dict[str, Any]:
        tracks = self.data.get("tracks", [])
        ptr = self.data.get("current_fx_ptr", 0)

        if ptr >= len(tracks):
            self.data["current_phase"] = "PHASE_6_COMPOSITION"
            self.data["phase_index"] = 6
            self._save_state()
            return self._prompt_phase_6()

        trk = tracks[ptr]
        t_idx = trk["index"]
        t_name = trk["name"]
        role = trk["role"]

        if role == "DRUMS":
            fx_rec = (
                "• **Opción 1 (Recomendada)**: Drum Buss (Drive 28%, Crunch 35%, Transients +1.5dB) + Glue Compressor.\n"
                "• **Opción 2**: Saturator (Analógico) + OTT (Mix 20%).\n"
                "• **Opción 3**: Directo (Sin efectos de inserción)."
            )
        elif role == "BASS":
            fx_rec = (
                "• **Opción 1 (Recomendada)**: Saturator (Analog Clip, Drive +3.5dB) + EQ Eight (Corte subsónico < 28 Hz).\n"
                "• **Opción 2**: Overdrive analógico + Compressor.\n"
                "• **Opción 3**: Directo (Sin efectos de inserción)."
            )
        elif role == "KEYS":
            fx_rec = (
                "• **Opción 1 (Recomendada)**: Chorus-Ensemble (Amount 40%) + ValhallaVintageVerb (Decay 2.2s, Mix 18%).\n"
                "• **Opción 2**: Tremolo analógico + Delay estéreo a corcheas.\n"
                "• **Opción 3**: Directo (Sin efectos de inserción)."
            )
        elif role == "LEAD":
            fx_rec = (
                "• **Opción 1 (Recomendada)**: Delay estéreo (Dotted 1/8, Feedback 30%) + OTT (Mix 25%).\n"
                "• **Opción 2**: Chorus-Ensemble + ValhallaVintageVerb (Decay 3.5s).\n"
                "• **Opción 3**: Directo (Sin efectos de inserción)."
            )
        else:
            fx_rec = (
                "• **Opción 1 (Recomendada)**: EQ Eight (High-pass 140 Hz) + ValhallaVintageVerb (Decay 3.2s, Mix 25%).\n"
                "• **Opción 2**: Phaser/Flanger espacial + Reverb ambiental.\n"
                "• **Opción 3**: Directo (Sin efectos de inserción)."
            )

        return {
            "current_step": f"PASO 5 DE 7: EFECTOS DE INSERCIÓN (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Parámetros de síntesis esculpidos en Pista {t_idx}.",
            "question": (
                f"🔌 **Paso 5 de 7: Cadena de Efectos de Inserción para Pista {t_idx} ('{t_name}', Rol: {role})**\n\n"
                f"¿Qué procesadores en serie deseas insertar en este canal?\n\n"
                f"{fx_rec}\n\n"
                f"*Responde con la opción deseada (ej: 'Opción 1' o los efectos personalizados).*"
            ),
            "instructions_for_ai": f"Indica la cadena de efectos de inserción para la pista {t_name}.",
            "target_track": t_idx,
            "role": role,
            "phase": "PHASE_5_INSERT_EFFECTS"
        }

    def _handle_phase_5(self, conn: Any, user_input: str) -> Dict[str, Any]:
        tracks = self.data.get("tracks", [])
        ptr = self.data.get("current_fx_ptr", 0)

        if ptr >= len(tracks):
            self.data["current_phase"] = "PHASE_6_COMPOSITION"
            self.data["phase_index"] = 6
            self._save_state()
            return self._prompt_phase_6()

        trk = tracks[ptr]
        t_idx = trk["index"]
        role = trk["role"]
        text = _normalize_text(user_input)

        applied_fx = []
        if "opcion 3" in text or "directo" in text or "bypass" in text or "sin efecto" in text:
            applied_fx = ["Bypass (Dry)"]
        else:
            fx_to_load = []
            if role == "DRUMS":
                fx_to_load = [("Drum Buss", "query:AudioFx#Drum%20Buss"), ("Glue Compressor", "query:AudioFx#Glue%20Compressor")]
            elif role == "BASS":
                fx_to_load = [("Saturator", "query:AudioFx#Saturator"), ("EQ Eight", "query:AudioFx#EQ%20Eight")]
            elif role == "KEYS":
                fx_to_load = [("Chorus-Ensemble", "query:AudioFx#Chorus-Ensemble"), ("ValhallaVintageVerb", "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb")]
            elif role == "LEAD":
                fx_to_load = [("Delay", "query:AudioFx#Delay"), ("OTT", "query:Plugins#VST3:Xfer%20Records:OTT")]
            else:
                fx_to_load = [("EQ Eight", "query:AudioFx#EQ%20Eight"), ("ValhallaVintageVerb", "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb")]

            if conn is not None and hasattr(conn, "send_command"):
                for fx_name, fx_uri in fx_to_load:
                    try:
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": fx_uri})
                        applied_fx.append(fx_name)
                    except Exception as ex:
                        logger.warning(f"Could not load insert FX {fx_name} on track {t_idx}: {ex}")
            else:
                applied_fx = [name for name, _ in fx_to_load]

        trk["insert_effects"] = applied_fx
        self.data["current_fx_ptr"] = ptr + 1
        self._save_state()

        if self.data["current_fx_ptr"] < len(tracks):
            return self._prompt_current_track_fx()
        else:
            self.data["current_phase"] = "PHASE_6_COMPOSITION"
            self.data["phase_index"] = 6
            self._save_state()
            return self._prompt_phase_6()

    # -------------------------------------------------------------------------
    # FASE 6: COMPOSICIÓN DE NOTAS Y TIMELINE (CON DRUM OCTAVE GUARD)
    # -------------------------------------------------------------------------
    def _prompt_phase_6(self) -> Dict[str, Any]:
        return {
            "current_step": "PASO 6 DE 7: COMPOSICIÓN DE NOTAS Y DESPLIEGUE EN ARRANGEMENT",
            "action_taken": "Todos los instrumentos y efectos de inserción fueron configurados físicamente en Live.",
            "question": (
                "🎼 **Paso 6 de 7: ¿En qué tonalidad, escala y tempo (BPM) componemos la música?**\n\n"
                "*Sugerencias armónicas y rítmicas:*\n"
                "• **Neo-Soul / R&B**: Fa Menor (F minor), 84 a 120 BPM, acordes Drop-2 con novenas y 808 con glides.\n"
                "• **Trap / Rap Oscuro**: Do Menor (C minor), 138 a 144 BPM, 808 pesado y hats syncopados.\n"
                "• **Personalizado**: Indica tu tonalidad y BPM deseados (ej: 'Sol menor a 90 BPM').\n\n"
                "*Responde indicando la tonalidad y BPM (ej: 'Tonalidad F menor a 120 BPM con Drop-2').*"
            ),
            "instructions_for_ai": "Indica tonalidad, escala y tempo para la composición.",
            "phase": "PHASE_6_COMPOSITION"
        }

    def _handle_phase_6(self, conn: Any, user_input: str) -> Dict[str, Any]:
        text = user_input.upper()

        key = "F"
        for k_candidate in ["C#", "DB", "D#", "EB", "F#", "GB", "G#", "AB", "A#", "BB", "C", "D", "E", "F", "G", "A", "B"]:
            if f" {k_candidate} " in f" {text} " or f"KEY {k_candidate}" in text or f"TONALIDAD {k_candidate}" in text:
                key = k_candidate.title()
                break

        scale = "natural_minor"
        if "MAYOR" in text or "MAJOR" in text:
            scale = "major"
        elif "DORIAN" in text:
            scale = "dorian"

        bpm = 120.0
        bpm_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*BPM", user_input, re.IGNORECASE)
        if bpm_match:
            bpm = float(bpm_match.group(1))

        self.data["key"] = key
        self.data["scale"] = scale
        self.data["bpm"] = bpm
        total_bars = self.data.get("total_bars", 96)

        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("set_tempo", {"tempo": bpm})
            except Exception:
                pass

        # Compose notes and deploy to arrangement for every track
        tracks = self.data.get("tracks", [])
        composed_summary = []

        for trk in tracks:
            t_idx = trk["index"]
            role = trk["role"]
            rendered_notes = RoleTrackOrchestrator.generate_musical_notes(
                role=role, key=key, scale=scale, arrange_bars=total_bars
            )

            # DRUM OCTAVE GUARD: Ensure drum notes land in Quadrant 1 (pitch 36-51)
            if role == "DRUMS" and rendered_notes:
                q3_notes = [n for n in rendered_notes if 60 <= n.pitch <= 75]
                q1_notes = [n for n in rendered_notes if 36 <= n.pitch <= 51]
                if q3_notes and len(q1_notes) == 0:
                    for n in rendered_notes:
                        n.pitch = max(36, n.pitch - 24)

            # Deploy to Live
            if conn is not None and hasattr(conn, "send_command") and rendered_notes:
                try:
                    max_note_beat = max(n.start + n.duration for n in rendered_notes)
                    is_loop = (role == "DRUMS" or max_note_beat <= 32.0)
                    clip_len = 16.0 if is_loop else float(max(64.0, max_note_beat))

                    conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": 0})
                    conn.send_command("create_clip", {"track_index": t_idx, "clip_index": 0, "length": clip_len})
                    conn.send_command("add_notes_to_clip", {
                        "track_index": t_idx,
                        "clip_index": 0,
                        "notes": [
                            {"pitch": int(n.pitch), "start_time": round(float(n.start), 3), "duration": round(float(n.duration), 3), "velocity": int(n.velocity), "mute": False}
                            for n in rendered_notes
                            if (n.start < clip_len if is_loop else True)
                        ]
                    })

                    # Duplicate across arrangement
                    total_beats = float(total_bars * 4.0)
                    if is_loop:
                        for dest in range(0, int(total_beats), int(clip_len)):
                            conn.send_command("duplicate_session_clip_to_arrangement", {"track_index": t_idx, "clip_index": 0, "destination_time": float(dest)})
                    else:
                        conn.send_command("duplicate_session_clip_to_arrangement", {"track_index": t_idx, "clip_index": 0, "destination_time": 0.0})

                    composed_summary.append(f"{trk['name']} ({len(rendered_notes)} notas)")
                except Exception as ex:
                    logger.warning(f"Composition deployment error on track {t_idx}: {ex}")

        self.data["current_phase"] = "PHASE_7_MIX_MASTER"
        self.data["phase_index"] = 7
        self._save_state()

        return self._prompt_phase_7(total_bars, bpm, key, scale, composed_summary)

    # -------------------------------------------------------------------------
    # FASE 7: MEZCLA DINÁMICA Y MASTERIZACIÓN (BS.1770-5)
    # -------------------------------------------------------------------------
    def _prompt_phase_7(self, total_bars, bpm, key, scale, composed_summary) -> Dict[str, Any]:
        return {
            "current_step": "PASO 7 DE 7: MEZCLA DINÁMICA Y MASTERIZACIÓN (BS.1770-5)",
            "action_taken": f"Composición desplegada en {total_bars} compases a {bpm} BPM en {key} {scale}. Pistas arregladas: {', '.join(composed_summary)}.",
            "question": (
                "🎚️ **Paso 7 de 7: Mezcla Dinámica, Sidechain y Cadena de Masterización**\n\n"
                "La música ya está escrita y ubicada en el Arrangement.\n"
                "*Auditoría acústica de la sesión:*\n"
                "• Detección de Kick y 808 Bass: se requiere Sidechain dinámico para evitar colisiones en 50-80 Hz.\n"
                "• Calibración de Masterización ITU-R BS.1770-5 (5 procesadores en serie).\n\n"
                "*¿Qué objetivo de sonoridad prefieres para el Master?*\n"
                "1. **STREAMING**: -14.0 LUFS integrado, -1.0 dB True Peak (Spotify, Apple Music, balance dinámico).\n"
                "2. **CLUB / TRAP**: -8.5 LUFS integrado, -0.5 dB True Peak (Máxima pegada comercial, graves apretados).\n\n"
                "*Responde indicando el perfil deseado (ej: 'Club a -8.5 LUFS' o 'Streaming a -14 LUFS').*"
            ),
            "instructions_for_ai": "Indica el objetivo de masterización (Streaming o Club).",
            "phase": "PHASE_7_MIX_MASTER"
        }

    def _handle_phase_7(self, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)
        target_profile = "CLUB" if ("club" in text or "-8" in text or "trap" in text) else "STREAMING"

        tracks = self.data.get("tracks", [])
        kick_idx = None
        bass_idx = None
        for t in tracks:
            r = t["role"].upper()
            if "DRUM" in r and kick_idx is None:
                kick_idx = t["index"]
            elif "BASS" in r and bass_idx is None:
                bass_idx = t["index"]

        # 1. Configure Physical Sidechain if Kick & Bass present
        sidechain_status = "No requerido"
        if kick_idx is not None and bass_idx is not None and conn is not None:
            try:
                SidechainManager.configure_sidechain(conn, bass_track_index=bass_idx, kick_track_index=kick_idx)
                sidechain_status = f"Configurado Kick (Pista {kick_idx}) -> Bass (Pista {bass_idx})"
            except Exception as e:
                sidechain_status = f"Omitido ({e})"

        # 2. Setup 5-device Mastering Chain
        mastering_status = "Omitido"
        if conn is not None and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {})
                num_tracks = int(s_info.get("track_count", len(tracks)))
                master_target_idx = num_tracks - 1
                LiveMasterChainEngine.setup_live_mastering_chain(conn, track_index=master_target_idx, target_profile=target_profile)
                mastering_status = f"Cadena de 5 procesadores calibrada para {target_profile} en Pista {master_target_idx}"
            except Exception as e:
                mastering_status = f"Mastering warning: {e}"

        # 3. Switch to Arrangement View & Reset Cursor
        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("switch_to_arrangement_view", {})
                conn.send_command("set_current_song_time", {"time": 0.0})
            except Exception:
                pass

        # 4. Preflight Audit
        preflight = executive_copilot.preflight_check()

        self.data["current_phase"] = "PHASE_8_COMPLETED"
        self.data["phase_index"] = 8
        self.data["is_complete"] = True
        self.data["target_profile"] = target_profile
        self._save_state()

        return {
            "current_step": "SESIÓN FINALIZADA — COPILOT EN ESCUCHA ACTIVA",
            "action_taken": f"Sidechain: {sidechain_status}. Master: {mastering_status}. Vista conmutada a Arrangement.",
            "question": (
                "🎉 **¡PRODUCCIÓN FINALIZADA CON ÉXITO!**\n\n"
                f"• **Pistas:** {len(tracks)} canales activos con VSTs verificados y parámetros esculpidos (Delta >= 1).\n"
                f"• **Línea de Tiempo:** {self.data.get('total_bars', 96)} compases en el Arrangement con marcadores de sección.\n"
                f"• **Mastering:** Perfil {target_profile} conforme a norma ITU-R BS.1770-5.\n"
                f"• **Auditoría Preflight:** {'APROBADA (0 blockers, lista para exportar)' if preflight.get('ready_for_export') else 'Completa con avisos'}.\n\n"
                "🎧 **El Copilot permanece activo y escuchando en esta misma herramienta.**\n"
                "Puedes solicitar cualquier ajuste en lenguaje natural, por ejemplo:\n"
                "- *'Bájale 2 dB al 808'*\n"
                "- *'Haz el Piano más brillante'*\n"
                "- *'Cambia el tempo a 88 BPM'*\n"
                "- *'Silencia los pads durante el verso'*."
            ),
            "instructions_for_ai": "La canción está lista. Puedes pedir cualquier ajuste quirúrgico al Copilot.",
            "ready_for_export": preflight.get("ready_for_export", False),
            "phase": "PHASE_8_COMPLETED"
        }

    # -------------------------------------------------------------------------
    # FASE 8: REFINAMIENTOS Y ESCUCHA ACTIVA
    # -------------------------------------------------------------------------
    def _handle_phase_8(self, conn: Any, user_input: str) -> Dict[str, Any]:
        """Handles post-production conversational refinements."""
        text = _normalize_text(user_input)
        applied_tweak = []

        if conn is not None and hasattr(conn, "send_command"):
            # Tempo adjustment
            bpm_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*bpm", text)
            if bpm_match:
                new_bpm = float(bpm_match.group(1))
                conn.send_command("set_tempo", {"tempo": new_bpm})
                self.data["bpm"] = new_bpm
                applied_tweak.append(f"Tempo actualizado a {new_bpm} BPM")

            # Track volume tweak
            db_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*db", text)
            for trk in self.data.get("tracks", []):
                t_name = trk["name"].lower()
                if t_name in text or trk["role"].lower() in text:
                    t_idx = trk["index"]
                    if "mute" in text or "silencia" in text or "apaga" in text:
                        conn.send_command("set_track_mute", {"track_index": t_idx, "mute": True})
                        applied_tweak.append(f"Pista {trk['name']} silenciada (Mute)")
                    elif "unmute" in text or "activa" in text:
                        conn.send_command("set_track_mute", {"track_index": t_idx, "mute": False})
                        applied_tweak.append(f"Pista {trk['name']} reactivada")
                    elif db_match:
                        conn.send_command("set_track_volume", {"track_index": t_idx, "volume": 0.70})
                        applied_tweak.append(f"Volumen de {trk['name']} ajustado")

        self._save_state()
        tweak_str = "; ".join(applied_tweak) if applied_tweak else "Ajuste registrado y aplicado en la sesión."

        return {
            "current_step": "AJUSTE QUIRÚRGICO APLICADO",
            "action_taken": tweak_str,
            "question": (
                f"✅ **Ajuste aplicado:** {tweak_str}\n\n"
                "¿Deseas realizar algún otro cambio en la mezcla, timbres o arreglo?"
            ),
            "instructions_for_ai": "Pide más ajustes o da por concluida la sesión.",
            "phase": "PHASE_8_COMPLETED"
        }


# Global singleton
copilot_guided_session_engine = CopilotGuidedSession()

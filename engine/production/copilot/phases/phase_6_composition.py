# engine/production/copilot/phases/phase_6_composition.py
"""
Phase 6: Multi-section harmonic, rhythmic, and melodic composition in arrangement timeline.
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.music.modular_generator import resolve_genre_style, generate_modular_section_notes
from engine.production.recipe_engine import ProductionRecipe, RecipeSection, TrackBlueprint
from engine.arrangement.batch_composer import BatchComposer
from engine.arrangement.top_tail_guard import TopTailGuard
from engine.arrangement.collision_guard import ArrangementCollisionGuard
from engine.supervisor.governance import GovernanceViolationError
from engine.memory.user_learning import get_user_preferences
from engine.session.transaction_guard import TransactionGuard
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.vocal.vocal_chain_processor import VocalChainProcessor

logger = logging.getLogger("Phase6Composition")

class Phase6CompositionHandler(BasePhaseHandler):
    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_phase_6(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_6(session, conn, user_input)

    def enforce_pre_drop_vacuum(self, session: Any, conn: Any) -> None:
        """Enforces physical pre-drop vacuum across all arrangement clips in Live."""
        if conn is not None and hasattr(conn, "send_command"):
            try:
                code_phys_vac = """
for t in song.tracks:
    try:
        clips = list(t.arrangement_clips)
    except Exception:
        continue
    for c in clips:
        if getattr(c, 'is_midi_clip', False):
            for cp in getattr(song, 'cue_points', []):
                cp_nm = str(getattr(cp, 'name', '')).lower()
                cp_t = float(getattr(cp, 'time', 0.0))
                if any(w in cp_nm for w in ['drop', 'switch', 'climax', 'caida', 'caída', 'corte']):
                    v_start = max(0.0, cp_t - 2.0)
                    if c.start_time < cp_t and c.end_time > v_start:
                        c.remove_notes_extended(from_time=max(0.0, v_start - c.start_time), from_pitch=0, time_span=max(0.1, cp_t - max(v_start, c.start_time)), pitch_span=128)
"""
                conn.send_command("execute_code", {"code": code_phys_vac})
            except Exception as ex_vac:
                logger.debug(f"Physical vacuum sweep notice: {ex_vac}")
    
    def deploy_clip_with_governance_retry(
        self,
        session_or_conn: Any,
        conn: Any = None,
        t_idx: int = 0,
        s_idx: int = 0,
        s_beats: float = 32.0,
        s_notes_dicts: Optional[List[Dict[str, Any]]] = None,
        current_beat: float = 0.0,
        trk: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Deploys a clip to session and arrangement with automatic governance healing.
        If an un-sculpted synth error (INIT_SYNTH_DETECTED) occurs:
        1. Attempts automatic character sculpting on the instrument via DeviceParameterSupervisor.
        2. Retries clip creation and deployment.
        3. If retry fails, raises GovernanceViolationError so the caller halts and prompts
           for an instrument change or manual parameter sculpting.
        """
        conn = conn if conn is not None else session_or_conn
        if s_notes_dicts is None:
            s_notes_dicts = []
        if trk is None:
            trk = {}
        if conn is None or not hasattr(conn, "send_command"):
            return True
    
        notes_payload = [
            {
                "pitch": int(d["pitch"]),
                "start_time": round(float(d.get("start_time", d.get("start", 0.0))), 3),
                "duration": round(float(d.get("duration", 1.0)), 3),
                "velocity": int(d.get("velocity", 100)),
                "mute": bool(d.get("mute", False))
            }
            for d in s_notes_dicts
        ]
    
        def _do_deploy():
            conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": s_idx})
            if s_notes_dicts:
                conn.send_command("create_clip", {"track_index": t_idx, "clip_index": s_idx, "length": s_beats})
                conn.send_command("add_notes_to_clip", {
                    "track_index": t_idx,
                    "clip_index": s_idx,
                    "notes": notes_payload
                })
                conn.send_command("duplicate_session_clip_to_arrangement", {
                    "track_index": t_idx,
                    "clip_index": s_idx,
                    "destination_time": float(current_beat)
                })
            elif s_idx == 0:
                conn.send_command("create_clip", {"track_index": t_idx, "clip_index": 0, "length": s_beats})
    
        try:
            _do_deploy()
            return True
        except Exception as ex:
            err_msg = str(ex)
            is_governance = (
                "INIT_SYNTH" in err_msg
                or "Delta = 0" in err_msg
                or "sinte sin esculpir" in err_msg
                or "GovernanceViolation" in type(ex).__name__
            )
            if is_governance:
                logger.warning(
                    f"Clip deployment blocked by governance on track {t_idx} ('{trk.get('name')}'): {ex}. "
                    "Attempting automatic synthesis sculpting & retry..."
                )
                role = trk.get("role", "SYNTH")
                try:
                    DeviceParameterSupervisor.enforce_mandatory_sculpting(
                        conn, track_index=t_idx, device_index=0, role=role
                    )
                    _do_deploy()
                    logger.info(f"Auto-sculpting retry succeeded on track {t_idx} ('{trk.get('name')}'). Clip deployed.")
                    return True
                except Exception as ex_retry:
                    logger.error(
                        f"Governance auto-sculpt retry failed on track {t_idx} ('{trk.get('name')}'): {ex_retry}."
                    )
                    raise ex_retry
            else:
                logger.error(f"Clip deployment error on track {t_idx} section {s_idx}: {ex}")
                raise ex

    _deploy_clip_with_governance_retry = deploy_clip_with_governance_retry

    def deploy_single_track_composition(
        self,
        session: Any,
        conn: Any,
        trk: Dict[str, Any],
        custom_notes_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        sections: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Deploys MIDI notes or audio clips for a single track across all arrangement sections.
        Returns the total number of notes/clips deployed.
        """
        if sections is None:
            sections = session.data.get("sections", [])
        if not sections:
            sections = [
                {"name": "Intro", "bars": 8, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 8},
                {"name": "Buildup", "bars": 8, "start_bar": 24},
                {"name": "Drop 1", "bars": 16, "start_bar": 32},
                {"name": "Puente (Calma)", "bars": 8, "start_bar": 48},
                {"name": "Drop 2 (Climax)", "bars": 16, "start_bar": 56},
                {"name": "Outro", "bars": 8, "start_bar": 72}
            ]
    
        t_idx = session._resolve_live_track_index(conn, trk)
        role = trk.get("role", "OTHER")
        current_beat = 0.0
        total_notes_trk = 0
        tracks = session.data.get("tracks", [])
    
        # --- VOCAL / AUDIO TRACK HANDLING ---
        if (role == "VOCALS" or trk.get("is_audio")) and not trk.get("chopping_mode"):
            if trk.get("live_recording_mode") or not trk.get("sample_path"):
                if conn is not None and hasattr(conn, "send_command"):
                    try:
                        code_clean_live = f"""
t = song.tracks[{t_idx}]
arr_clips = list(getattr(t, 'arrangement_clips', []))
if len(arr_clips) == 0:
    for slot in t.clip_slots:
        if slot.has_clip:
            try:
                slot.delete_clip()
            except:
                pass
"""
                        conn.send_command("execute_code", {"code": code_clean_live})
                    except Exception as ex_clean_live:
                        logger.debug(f"Live vocal track clean notice: {ex_clean_live}")
                return 1
    
            v_path = trk.get("sample_path")
            alt_v_path = trk.get("alt_sample_path")
            if conn is not None and hasattr(conn, "send_command") and v_path and os.path.exists(v_path):
                try:
                    conn.send_command("create_audio_clip", {
                        "track_index": t_idx,
                        "clip_index": 0,
                        "path": v_path
                    })
                except Exception as e_c0:
                    logger.debug(f"Audio clip slot 0 load notice: {e_c0}")
                if alt_v_path and os.path.exists(alt_v_path):
                    try:
                        conn.send_command("create_audio_clip", {
                            "track_index": t_idx,
                            "clip_index": 1,
                            "path": alt_v_path
                        })
                    except Exception as e_c1:
                        logger.debug(f"Audio clip slot 1 load notice: {e_c1}")
    
            vocal_sections_count = 0
            for s_idx, sec in enumerate(sections):
                s_name = str(sec.get("name", f"Section {s_idx + 1}")).lower()
                s_bars = int(sec.get("bars", 8))
                s_beats = float(s_bars * 4.0)
    
                is_vocal_section = False
                if any(w in s_name for w in ["verse", "verso", "drop", "hook", "coro", "climax", "chorus"]):
                    is_vocal_section = True
                if any(w in s_name for w in ["intro", "buildup", "build", "puente", "calma", "break", "outro", "silence"]):
                    is_vocal_section = False
    
                if is_vocal_section:
                    vocal_sections_count += 1
                    slot_to_deploy = 1 if ("drop" in s_name or "climax" in s_name or "hook" in s_name) and trk.get("alt_sample_path") else 0
                    if conn is not None and hasattr(conn, "send_command"):
                        try:
                            conn.send_command("duplicate_session_clip_to_arrangement", {
                                "track_index": t_idx,
                                "clip_index": slot_to_deploy,
                                "destination_time": float(current_beat)
                            })
                        except Exception as ex_arr:
                            logger.warning(f"Vocal deployment notice on track {t_idx} section {s_idx}: {ex_arr}")
    
                current_beat += s_beats
    
            return vocal_sections_count
    
        # --- MIDI TRACK HANDLING ---
        for s_idx, sec in enumerate(sections):
            s_name = sec.get("name", f"Section {s_idx + 1}")
            s_bars = int(sec.get("bars", 8))
            s_beats = float(s_bars * 4.0)
    
            has_kick_track = any(
                (t.get("role") == "KICK" or "kick" in str(t.get("name", "")).lower())
                for t in tracks if t != trk
            )
    
            raw_notes = self.find_custom_notes_for_track_section(session, 
                custom_map=custom_notes_map,
                trk=trk,
                s_idx=s_idx,
                s_name=s_name,
                s_beats=s_beats
            )
            s_notes_dicts = raw_notes if raw_notes is not None else []
    
            # Fallback to ("current", s_idx) or ("current", "all") only if no section-specific notes were provided
            if raw_notes is None and not s_notes_dicts:
                cur_keys = [
                    ("current", s_idx),
                    ("current", str(s_idx)),
                    ("current", str(s_name).lower()),
                    ("current", "all")
                ]
                for ck in cur_keys:
                    if ck in custom_notes_map:
                        base_notes = custom_notes_map[ck]
                        if ck[1] == "all" and base_notes:
                            # Filter out notes that are outside this section's timeline window if global timeline notes were provided
                            sec_st = float(sec.get("start_bar", 0)) * 4.0
                            sec_end = sec_st + s_beats
                            in_window = [n for n in base_notes if sec_st <= n.get("start_time", 0.0) < sec_end]
                            if in_window:
                                shifted = []
                                for n in in_window:
                                    n_c = dict(n)
                                    n_c["start_time"] = round(n["start_time"] - sec_st, 4)
                                    shifted.append(n_c)
                                s_notes_dicts = shifted
                                break
                            max_reach = max(n["start_time"] + n["duration"] for n in base_notes)
                            if max_reach > 0 and s_beats > max_reach:
                                pattern_len = 16.0 if max_reach <= 16.0 else max_reach
                                tiled = []
                                offset = 0.0
                                while offset < s_beats:
                                    for n in base_notes:
                                        n_st = n["start_time"] + offset
                                        if n_st < s_beats:
                                            n_copy = dict(n)
                                            n_copy["start_time"] = round(n_st, 4)
                                            n_dur = min(n["duration"], s_beats - n_st)
                                            n_copy["duration"] = round(n_dur, 4)
                                            tiled.append(n_copy)
                                    offset += pattern_len
                                s_notes_dicts = tiled
                            else:
                                s_notes_dicts = list(base_notes)
                        else:
                            s_notes_dicts = list(base_notes)
    
            if not s_notes_dicts and not custom_notes_map:
                key = session.data.get("key", "F")
                scale = session.data.get("scale", "natural_minor")
                bpm = session.data.get("bpm", 120.0)
                genre = session.data.get("genre", "trap")
                role = trk.get("role", "OTHER")
                raw_gen = generate_modular_section_notes(
                    role=role,
                    section_index=s_idx,
                    section_name=s_name,
                    section_bars=s_bars,
                    key=key,
                    scale=scale,
                    bpm=bpm,
                    genre=genre
                )
                s_notes_dicts = []
                for n in raw_gen:
                    if hasattr(n, "start") and hasattr(n, "pitch"):
                        s_notes_dicts.append({
                            "pitch": int(n.pitch),
                            "start_time": float(n.start),
                            "duration": float(n.duration),
                            "velocity": int(n.velocity)
                        })
                    elif isinstance(n, dict):
                        s_notes_dicts.append({
                            "pitch": int(n.get("pitch", 60)),
                            "start_time": float(n.get("start_time", n.get("start", 0.0))),
                            "duration": float(n.get("duration", 1.0)),
                            "velocity": int(n.get("velocity", 100))
                        })

            # Auto-tile section motifs if shorter than section length (e.g. 16-beat motif for a 64-beat section)
            if s_notes_dicts and not any(w in s_name.lower() for w in ["silence", "silencio", "false ending", "falso final"]):
                max_reach = max(n.get("start_time", 0.0) + n.get("duration", 1.0) for n in s_notes_dicts)
                if 0 < max_reach < s_beats and max_reach <= 16.0:
                    pattern_len = 16.0
                    tiled = []
                    offset = 0.0
                    while offset < s_beats:
                        for n in s_notes_dicts:
                            n_st = n.get("start_time", 0.0) + offset
                            if n_st < s_beats:
                                n_copy = dict(n)
                                n_copy["start_time"] = round(n_st, 4)
                                n_dur = min(n.get("duration", 1.0), s_beats - n_st)
                                n_copy["duration"] = round(n_dur, 4)
                                tiled.append(n_copy)
                        offset += pattern_len
                    s_notes_dicts = tiled
    
            if any(w in s_name.lower() for w in ["silence", "silencio", "false ending", "falso final"]):
                s_notes_dicts = []
    
            if role == "KICK":
                if s_notes_dicts:
                    k_hits = [d for d in s_notes_dicts if d.get("pitch") in (35, 36)]
                    if k_hits:
                        s_notes_dicts = k_hits
                    else:
                        for d in s_notes_dicts:
                            d["pitch"] = 36
                else:
                    drum_custom = self.find_custom_notes_for_track_section(session, 
                        custom_map=custom_notes_map,
                        trk={"name": "Drums", "role": "DRUMS"},
                        s_idx=s_idx,
                        s_name=s_name,
                        s_beats=s_beats
                    )
                    if drum_custom:
                        s_notes_dicts = [dict(d) for d in drum_custom if d.get("pitch") in (35, 36)]
    
            if role == "DRUMS" and s_notes_dicts:
                # Timbre-aware sanitization: only transpose if ALL notes are uniformly in octave C3 (60..75)
                # and zero notes exist in standard C1 (36..51) or C2 (52..59).
                # Preserves multi-octave percussion, auxiliary percs, and intentional high notes.
                q3_notes = [d for d in s_notes_dicts if 60 <= d.get("pitch", 0) <= 75]
                q1_notes = [d for d in s_notes_dicts if 36 <= d.get("pitch", 0) <= 51]
                q2_notes = [d for d in s_notes_dicts if 52 <= d.get("pitch", 0) <= 59]
                if len(q3_notes) == len(s_notes_dicts) and len(q1_notes) == 0 and len(q2_notes) == 0:
                    for d in s_notes_dicts:
                        d["pitch"] = max(36, d["pitch"] - 24)
    
            if (trk.get("chopping_mode") or "chop" in str(trk.get("name", "")).lower() or trk.get("slice_mode") == "Slicing") and s_notes_dicts:
                slices_cnt = int(trk.get("slices_count", 64))
                if slices_cnt <= 0:
                    slices_cnt = 64
                for d in s_notes_dicts:
                    p = int(d.get("pitch", 36))
                    if p < 36 or p >= (36 + slices_cnt):
                        d["pitch"] = 36 + ((p - 36) % slices_cnt)
    
            if role == "DRUMS" and has_kick_track and s_notes_dicts:
                s_notes_dicts = [d for d in s_notes_dicts if d.get("pitch") not in (35, 36)]
    
            is_pre_drop_transition = False
            if s_idx + 1 < len(sections):
                next_s_name = str(sections[s_idx + 1].get("name", "")).lower()
                curr_s_name = str(sec.get("name", "")).lower()
                if any(w in next_s_name for w in ["drop", "switch", "climax", "caida", "caída", "corte"]):
                    is_pre_drop_transition = True
                elif any(w in curr_s_name for w in ["build", "subida", "pre-drop", "pre drop", "pre-chorus", "pre chorus"]) and any(w in next_s_name for w in ["chorus", "coro", "hook"]):
                    is_pre_drop_transition = True
    
            if is_pre_drop_transition and s_notes_dicts:
                cutoff_beat = max(0.0, s_beats - 2.0)
                vacuumed_notes = []
                for d in s_notes_dicts:
                    st = float(d.get("start_time", d.get("start", 0.0)))
                    dur = float(d.get("duration", 1.0))
                    if st >= cutoff_beat:
                        continue
                    elif (st + dur) > cutoff_beat:
                        d_c = dict(d)
                        d_c["duration"] = max(0.05, round(cutoff_beat - st, 4))
                        vacuumed_notes.append(d_c)
                    else:
                        vacuumed_notes.append(d)
                s_notes_dicts = vacuumed_notes
    
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    self.deploy_clip_with_governance_retry(session, 
                        conn=conn,
                        t_idx=t_idx,
                        s_idx=s_idx,
                        s_beats=s_beats,
                        s_notes_dicts=s_notes_dicts,
                        current_beat=current_beat,
                        trk=trk
                    )
                    total_notes_trk += len(s_notes_dicts)
                except Exception as ex:
                    trk["deployment_failed"] = True
                    trk["deployment_error"] = str(ex)
                    logger.error(
                        f"Deployment failed permanently on track {t_idx} ('{trk.get('name')}') section {s_idx}: {ex}. "
                        "Note count NOT incremented."
                    )
            else:
                total_notes_trk += len(s_notes_dicts)
    
            current_beat += s_beats
    
        trk["notes_count"] = total_notes_trk
        return total_notes_trk

    _deploy_single_track_composition = deploy_single_track_composition
    
    def prompt_by_track_step(self, session: Any, trk_idx: int) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        if trk_idx >= len(tracks):
            return session._prompt_phase_7()
    
        cur_trk = tracks[trk_idx]
        cur_trk_is_aud = bool(cur_trk.get("is_audio", False) or str(cur_trk.get("role", "")).upper() == "VOCALS" or cur_trk.get("live_recording_mode", False))
        sec_names = [s.get("name", f"Sección {i+1}") for i, s in enumerate(sections)]
        sec_str = ", ".join(sec_names) if sec_names else "Todas las secciones"
    
        if cur_trk_is_aud:
            return {
                "status": "AWAITING_AUDIO_TRACK_CONFIRMATION",
                "current_step": f"PASO 6 (POR PISTA {trk_idx + 1}/{len(tracks)}): PREPARACIÓN DE CANAL AUDIO '{cur_trk.get('name')}'",
                "action_taken": f"Modo interactivo pista por pista activo. Pista de Audio/Grabación/FX: {cur_trk.get('name')} (Rol: {cur_trk.get('role')}).",
                "question": (
                    f"🎙️ **Canal de Audio / Grabación / Ruteo FX {trk_idx + 1} de {len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                    f"• **Instrumento / Ruteo:** {cur_trk.get('instrument', cur_trk.get('name'))}\n"
                    f"• **Tipo de Pista:** Canal de Audio (Sin notas MIDI requeridas).\n\n"
                    f"Envía 'confirmar' o 'siguiente' para validar el ruteo y armar el canal en el Arrangement."
                ),
                "instructions_for_ai": f"Envía 'confirmar' para preparar el canal de audio '{cur_trk.get('name')}'.",
                "phase": "PHASE_6_COMPOSITION",
                "track_index": trk_idx,
                "track_name": cur_trk.get("name"),
                "track_role": cur_trk.get("role")
            }
    
        drum_spec_block = ""
        role_upper = str(cur_trk.get("role", "")).upper()
        inst_lower = str(cur_trk.get("instrument", "")).lower()
        trk_name_lower = str(cur_trk.get("name", "")).lower()
        if role_upper in ("DRUMS", "KICK") or any(w in inst_lower for w in ["drum", "bater", "kit", "rack"]) or any(w in trk_name_lower for w in ["drum", "bater", "perc"]):
            drum_spec_block = (
                "\n\n🥁 **Especificación Física de Drum Rack (Ableton Live):**\n"
                "• **Octava Inicial Obligatoria:** C1 (MIDI pitch 36).\n"
                "• **Mapa de Pads Estándar:**\n"
                "  - 36 (C1): Bombo / Kick\n"
                "  - 37 (C#1): Aro / Rimshot / Sidestick\n"
                "  - 38 (D1): Caja / Snare acústico\n"
                "  - 39 (D#1): Aplauso / Hand Clap\n"
                "  - 42 (F#1): Hi-Hat cerrado / Shaker\n"
                "  - 46 (A#1): Hi-Hat abierto\n"
                "  - 49 (C#2): Platillo Crash\n"
                "  - 51 (D#2): Platillo Ride\n"
                "⚠️ *Para evitar pads silenciosos en Ableton Live, mapea tus notas a partir de C1 (pitch 36 a 51).*"
            )
    
        return {
            "status": "AWAITING_TRACK_COMPOSITION",
            "current_step": f"PASO 6 (POR PISTA {trk_idx + 1}/{len(tracks)}): COMPOSICIÓN PARA '{cur_trk.get('name')}'",
            "action_taken": f"Modo interactivo pista por pista activo. Pista actual: {cur_trk.get('name')} (Rol: {cur_trk.get('role')}).",
            "question": (
                f"🎼 **Paso 6: Componiendo Pista {trk_idx + 1} de {len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                f"• **Secciones del Arreglo:** {sec_str}\n"
                f"• **Rol Musical:** `{cur_trk.get('role')}`\n"
                f"• **Instrumento:** {cur_trk.get('instrument', cur_trk.get('name'))}\n\n"
                f"⚠️ **Regla de Oro (Cero Relleno Procedural):**\n"
                f"Define las notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) **únicamente para esta pista** en todas sus secciones activas.\n\n"
                f"Puedes enviar un JSON con `notes` (para todo el arreglo o sección) o `sections` detallando las notas por sección."
                f"{drum_spec_block}"
            ),
            "instructions_for_ai": f"Define y envía las notas MIDI explícitas para la pista '{cur_trk.get('name')}' ({cur_trk.get('role')}). El motor no autocompletará notas.",
            "phase": "PHASE_6_COMPOSITION",
            "track_index": trk_idx,
            "track_name": cur_trk.get("name"),
            "track_role": cur_trk.get("role")
        }
    
    def prompt_by_clip_step(self, session: Any, trk_idx: int, sec_idx: int) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        if trk_idx >= len(tracks):
            return session._prompt_phase_7()
    
        cur_trk = tracks[trk_idx]
        cur_trk_is_aud = bool(cur_trk.get("is_audio", False) or str(cur_trk.get("role", "")).upper() == "VOCALS" or cur_trk.get("live_recording_mode", False))
    
        if cur_trk_is_aud:
            return {
                "status": "AWAITING_AUDIO_TRACK_CONFIRMATION",
                "current_step": f"PASO 6 (PISTA {trk_idx + 1}/{len(tracks)}): CANAL AUDIO '{cur_trk.get('name')}'",
                "action_taken": f"Modo Clip por Clip. Canal de Audio/Grabación/FX: {cur_trk.get('name')} (Rol: {cur_trk.get('role')}).",
                "question": (
                    f"🎙️ **Canal de Audio / Grabación / Ruteo FX {trk_idx + 1} de {len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                    f"• **Instrumento / Ruteo:** {cur_trk.get('instrument', cur_trk.get('name'))}\n"
                    f"• **Tipo de Pista:** Canal de Audio (Sin clips MIDI requeridos).\n\n"
                    f"Envía 'confirmar' o 'siguiente' para validar el ruteo y avanzar a la siguiente pista."
                ),
                "instructions_for_ai": f"Envía 'confirmar' para validar el canal de audio '{cur_trk.get('name')}'.",
                "phase": "PHASE_6_COMPOSITION",
                "track_index": trk_idx,
                "section_index": sec_idx,
                "track_name": cur_trk.get("name"),
                "track_role": cur_trk.get("role")
            }
    
        cur_sec = sections[sec_idx] if sec_idx < len(sections) else sections[0]
        s_bars = int(cur_sec.get("bars", 8))
        s_beats = float(s_bars * 4.0)
    
        drum_spec_block = ""
        role_upper = str(cur_trk.get("role", "")).upper()
        inst_lower = str(cur_trk.get("instrument", "")).lower()
        trk_name_lower = str(cur_trk.get("name", "")).lower()
        if role_upper in ("DRUMS", "KICK") or any(w in inst_lower for w in ["drum", "bater", "kit", "rack"]) or any(w in trk_name_lower for w in ["drum", "bater", "perc"]):
            drum_spec_block = (
                "\n\n🥁 **Especificación Física de Drum Rack (Ableton Live):**\n"
                "• **Octava Inicial Obligatoria:** C1 (MIDI pitch 36).\n"
                "• **Mapa de Pads Estándar:**\n"
                "  - 36 (C1): Bombo / Kick\n"
                "  - 37 (C#1): Aro / Rimshot / Sidestick\n"
                "  - 38 (D1): Caja / Snare acústico\n"
                "  - 39 (D#1): Aplauso / Hand Clap\n"
                "  - 42 (F#1): Hi-Hat cerrado / Shaker\n"
                "  - 46 (A#1): Hi-Hat abierto\n"
                "  - 49 (C#2): Platillo Crash\n"
                "  - 51 (D#2): Platillo Ride\n"
                "⚠️ *Para evitar pads silenciosos en Ableton Live, mapea tus notas a partir de C1 (pitch 36 a 51).*"
            )
    
        return {
            "status": "AWAITING_CLIP_COMPOSITION",
            "current_step": f"PASO 6 (CLIP {sec_idx + 1}/{len(sections)}): '{cur_trk.get('name')}' EN '{cur_sec.get('name')}' ({s_bars} COMPASES)",
            "action_taken": f"Modo Clip por Clip activo. Solicitando notas para {s_bars} compases ({cur_sec.get('name')}).",
            "question": (
                f"🎼 **Componiendo Clip {sec_idx + 1} de {len(sections)} — Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                f"• **Sección / Clip:** **'{cur_sec.get('name')}'** ({s_bars} compases / {s_beats} tiempos métricos)\n"
                f"• **Instrumento:** {cur_trk.get('instrument', cur_trk.get('name'))}\n"
                f"• **Ventana Temporal del Clip:** `start_time` relativo de `0.0` a `{s_beats}` (o motivo de 16 tiempos con auto-tiling)\n\n"
                f"⚠️ **Regla de Oro (Cero Relleno Procedural):**\n"
                f"Define las notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) **únicamente para este bloque de {s_bars} compases**.\n\n"
                "Puedes enviar una lista JSON `[{\"pitch\": X, \"start_time\": Y, ...}]` o un objeto `{\"notes\": [...]}`.\n"
                "Si este canal debe permanecer en silencio durante esta sección, envía `[]` o escribe 'Silencio'."
                f"{drum_spec_block}"
            ),
            "instructions_for_ai": f"Define y envía las notas MIDI explícitas para el clip '{cur_sec.get('name')}' ({s_bars} compases) de '{cur_trk.get('name')}'.",
            "phase": "PHASE_6_COMPOSITION",
            "track_index": trk_idx,
            "section_index": sec_idx,
            "track_name": cur_trk.get("name"),
            "track_role": cur_trk.get("role"),
            "section_name": cur_sec.get("name"),
            "clip_bars": s_bars,
            "clip_beats": s_beats
        }
    
    # -------------------------------------------------------------------------
    # FASE 6: COMPOSICIÓN MODULAR DE NOTAS (DIRECTA POR IA / ASISTIDA)
    # -------------------------------------------------------------------------
    def _prompt_phase_6(self, session: Any) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        total_bars = session.data.get("total_bars", 96)
    
        # Check user preference for composition mode:
        pref_mode = "monolithic"
        try:
            from engine.memory.user_learning import get_user_preferences
            prefs = get_user_preferences()
            pref_mode = prefs.get("composition", {}).get("mode", "by_clip")
        except Exception:
            pass
    
        if pref_mode in ("by_clip", "clip_by_clip", "clip"):
            session.data["composition_session"] = {
                "active": True,
                "mode": "BY_CLIP",
                "track_index": 0,
                "section_index": 0
            }
            session._save_state()
            return self.prompt_by_clip_step(session, 0, 0)
    
        if pref_mode == "track_by_track":
            session.data["composition_session"] = {
                "active": True,
                "mode": "BY_TRACK",
                "interactive": True,
                "track_index": 0,
                "section_index": 0
            }
            session._save_state()
            return self.prompt_by_track_step(session, 0)
    
        track_lines = [f"• Pista {t.get('index')}: **{t.get('name')}** (Rol: `{t.get('role')}`)" for t in tracks]
        sec_lines = [f"• Sección {i}: **{s.get('name')}** ({s.get('bars')} compases, inicio: c.{s.get('start_bar', i*8)})" for i, s in enumerate(sections)]
    
        return {
            "current_step": "PASO 6 DE 7: COMPOSICIÓN MODULAR DE NOTAS Y DESPLIEGUE EN ARRANGEMENT",
            "action_taken": "Todos los instrumentos y efectos de inserción fueron configurados y afinados físicamente en Live.",
            "question": (
                "🎼 **Paso 6 de 7: Composición de Notas MIDI y Despliegue en Arrangement**\n\n"
                "**Dotación Instrumental en Live:**\n"
                + "\n".join(track_lines) + "\n\n"
                f"**Estructura del Arreglo ({total_bars} compases totales):**\n"
                + "\n".join(sec_lines) + "\n\n"
                "🧠 **Decisión Técnica Requerida:**\n"
                "⚠️ **Regla de Oro del Motor (Cero Auto-Relleno Procedural):**\n"
                "El motor prohíbe terminantemente autocompletar con notas genéricas o sugerir 'Siguiente' para inventar patrones.\n"
                "La IA debe definir explícitamente las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para cada instrumento y sección.\n\n"
                "🧠 **Modalidades de Envío de Notas:**\n"
                "• **Inyección Estructurada Completa (Recomendada)**: Envía un payload JSON con la clave `composition` o `tracks` detallando notas por pista y sección.\n"
                "• **Composición Modular Por Sección**: Escribe 'Por Sección' para definir notas bloque a bloque.\n"
                "• **Composición Modular Por Pista**: Escribe 'Por Pista' para definir notas pista por pista.\n"
                "• **Composición Combinada**: Escribe 'Combinado' para pista y sección específica.\n\n"
                "*Envía el JSON con la tonalidad, escala y notas de tu composición o indica tu modalidad modular para comenzar.*"
            ),
            "instructions_for_ai": "Genera y envía las notas MIDI explícitas para cada pista y sección activa. El motor no autocompletará notas.",
            "phase": "PHASE_6_COMPOSITION"
        }
    
    def handle_modular_composition_step(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Handles stepping through modular composition (by section, by track, or combined)."""
        session_state = session.data.get("composition_session", {})
        mode = session_state.get("mode", "BY_SECTION")
        sections = session.data.get("sections", [])
        tracks = session.data.get("tracks", [])

        sec_idx = session_state.get("section_index", 0)
        trk_idx = session_state.get("track_index", 0)

        text_norm = _normalize_text(user_input)
        ai_meta, custom_notes_map, has_notes = self.parse_ai_composition(session, user_input)

        is_explicit_key_directive = bool(re.search(r'\bKEY\s+[A-G][#b]?\b', user_input, re.IGNORECASE))
        if is_explicit_key_directive or any(w in text_norm for w in ["key ", "tonalidad", "dorian", "bpm", "natural_minor", "phrygian"]):
            session.data["composition_session"] = {"active": False}
            return self._handle_phase_6(session, conn, user_input)

        # Record step completion
        if mode == "BY_SECTION":
            if has_notes and sec_idx < len(sections):
                for trk in tracks:
                    self.deploy_single_track_composition(session, conn, trk, custom_notes_map, [sections[sec_idx]])
                    if trk.get("deployment_failed"):
                        session.data["pending_instrument_swap_track"] = trk.get("index")
                        session._save_state()
                        return {
                            "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                            "phase": "PHASE_6_COMPOSITION",
                            "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{trk.get('name')}')",
                            "action_taken": f"Error de gobernanza al desplegar clips en '{trk.get('name')}': {trk.get('deployment_error')}. Reintento de auto-esculpido fallido.",
                            "question": (
                                f"⚠️ **Error de Gobernanza en Pista '{trk.get('name')}' (Rol: `{trk.get('role')}`):**\n\n"
                                f"El instrumento `{trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                                f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                                f"**Opciones:**\n"
                                f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                                f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                                f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                            ),
                            "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                            "track_name": trk.get("name"),
                            "track_index": trk.get("index")
                        }
            sec_idx += 1
            session_state["section_index"] = sec_idx
            if sec_idx >= len(sections):
                session.data["composition_session"] = {"active": False}
                session.data["current_phase"] = "PHASE_7_AUTOMATION"
                session.data["phase_index"] = 7
                session._save_state()
                return session._prompt_phase_7()

            cur_sec = sections[sec_idx]
            session._save_state()
            return {
                "status": "MODULAR_COMPOSITION_STEP",
                "current_step": f"COMPOSICIÓN POR SECCIÓN ({sec_idx + 1}/{len(sections)}): {cur_sec.get('name')}",
                "action_taken": f"Sección {sec_idx} completada e inyectada en Live.",
                "question": f"🎼 **Componiendo Sección {sec_idx + 1} de {len(sections)}: '{cur_sec.get('name')}' ({cur_sec.get('bars')} compases):**\n\nDefine las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para los instrumentos de esta sección.",
                "instructions_for_ai": f"Envía las notas explícitas para la sección {cur_sec.get('name')}. El motor no autocompleta notas.",
                "phase": "PHASE_6_COMPOSITION"
            }

        elif mode == "BY_TRACK":
            trk_idx = session_state.get("track_index", 0)
            is_stepping = any(w in text_norm for w in ["siguiente", "next", "skip", "continuar", "avanzar"])

            # Interactive mode (strict prompt per track, blocks next without notes)
            is_interactive = session_state.get("interactive", False)
            if is_interactive:
                cur_trk = tracks[trk_idx] if trk_idx < len(tracks) else {}
                if is_stepping and not has_notes:
                    return {
                        "status": "MODULAR_COMPOSITION_BLOCKED",
                        "phase": "PHASE_6_COMPOSITION",
                        "current_step": f"COMPOSICIÓN POR PISTA BLOQUEADA ({trk_idx + 1}/{len(tracks)}): {cur_trk.get('name')}",
                        "action_taken": "Bloqueo: Se requieren notas explícitas para esta pista en modo interactivo.",
                        "question": f"⚠️ **Composición Bloqueada para '{cur_trk.get('name')}':**\n\nEl modo interactivo requiere notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) antes de continuar.",
                        "instructions_for_ai": f"Genera y envía notas MIDI explícitas en JSON para {cur_trk.get('name')}.",
                        "track_index": trk_idx
                    }

                if has_notes and trk_idx < len(tracks):
                    self.deploy_single_track_composition(session, conn, cur_trk, custom_notes_map)
                    cur_trk["notes_count"] = len(custom_notes_map) or sum(len(v) for v in custom_notes_map.values())
                    if cur_trk.get("deployment_failed"):
                        session.data["pending_instrument_swap_track"] = cur_trk.get("index")
                        session._save_state()
                        return {
                            "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                            "phase": "PHASE_6_COMPOSITION",
                            "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{cur_trk.get('name')}')",
                            "action_taken": f"Error de gobernanza al desplegar clips en '{cur_trk.get('name')}': {cur_trk.get('deployment_error')}. Reintento de auto-esculpido fallido.",
                            "question": (
                                f"⚠️ **Error de Gobernanza en Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                                f"El instrumento `{cur_trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                                f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                                f"**Opciones:**\n"
                                f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                                f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                                f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                            ),
                            "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                            "track_name": cur_trk.get("name"),
                            "track_index": cur_trk.get("index")
                        }

                trk_idx += 1
                session_state["track_index"] = trk_idx
                session._save_state()

                if trk_idx < len(tracks):
                    return self.prompt_by_track_step(session, trk_idx)
                else:
                    self.enforce_pre_drop_vacuum(session, conn)
                    session.data["composition_session"] = {"active": False}
                    session.data["current_phase"] = "PHASE_7_AUTOMATION"
                    session.data["phase_index"] = 7
                    session._save_state()
                    return session._prompt_phase_7()

            if is_stepping or has_notes:
                if has_notes and trk_idx < len(tracks):
                    cur_trk = tracks[trk_idx]
                    self.deploy_single_track_composition(session, conn, cur_trk, custom_notes_map)
                    if cur_trk.get("deployment_failed"):
                        session.data["pending_instrument_swap_track"] = cur_trk.get("index")
                        session._save_state()
                        return {
                            "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                            "phase": "PHASE_6_COMPOSITION",
                            "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{cur_trk.get('name')}')",
                            "action_taken": f"Error de gobernanza al desplegar clips en '{cur_trk.get('name')}': {cur_trk.get('deployment_error')}. Reintento de auto-esculpido fallido.",
                            "question": (
                                f"⚠️ **Error de Gobernanza en Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                                f"El instrumento `{cur_trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                                f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                                f"**Opciones:**\n"
                                f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                                f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                                f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                            ),
                            "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                            "track_name": cur_trk.get("name"),
                            "track_index": cur_trk.get("index")
                        }
                trk_idx += 1
                session_state["track_index"] = trk_idx
                if trk_idx >= len(tracks):
                    session.data["composition_session"] = {"active": False}
                    session.data["current_phase"] = "PHASE_7_AUTOMATION"
                    session.data["phase_index"] = 7
                    session._save_state()
                    return session._prompt_phase_7()

                next_trk = tracks[trk_idx]
                session._save_state()
                return {
                    "status": "MODULAR_COMPOSITION_STEP",
                    "current_step": f"COMPOSICIÓN POR PISTA ({trk_idx + 1}/{len(tracks)}): {next_trk.get('name')}",
                    "action_taken": f"Pista {trk_idx} completada.",
                    "question": f"🎼 **Componiendo Pista {trk_idx + 1} de {len(tracks)}: '{next_trk.get('name')}' (Rol: `{next_trk.get('role')}`):**\n\nDefine las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para esta pista.",
                    "instructions_for_ai": f"Envía las notas explícitas para {next_trk.get('name')}.",
                    "phase": "PHASE_6_COMPOSITION"
                }
    
            # All tracks completed
            unpopulated = []
            for t in tracks:
                r = str(t.get("role", "")).upper()
                is_aud = bool(t.get("is_audio", False) or r == "VOCALS" or t.get("live_recording_mode", False))
                if not is_aud and t.get("notes_count", 0) == 0:
                    unpopulated.append(t["name"])
    
            if unpopulated:
                return {
                    "status": "PHASE_6_GATEKEEPER_BLOCKED",
                    "phase": "PHASE_6_COMPOSITION",
                    "current_step": "FASE 6: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER)",
                    "action_taken": f"Gatekeeper de Completitud activado: {len(unpopulated)} pista(s) sin notas ({', '.join(unpopulated)}).",
                    "question": f"⚠️ Las siguientes pistas de instrumento carecen de notas MIDI: **{', '.join(unpopulated)}**.\nPor favor provee las notas MIDI para continuar.",
                    "instructions_for_ai": "Genera y envía las notas explícitas para las pistas vacías.",
                    "unpopulated_tracks": unpopulated
                }
    
            self.enforce_pre_drop_vacuum(session, conn)
    
            session.data["composition_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_7_AUTOMATION"
            session.data["phase_index"] = 7
            session._save_state()
            return session._prompt_phase_7()
    
        elif mode in ("BY_CLIP", "COMBINED"):
            trk_idx = session_state.get("track_index", 0)
            sec_idx = session_state.get("section_index", 0)
            if trk_idx >= len(tracks):
                session.data["composition_session"] = {"active": False}
                session.data["current_phase"] = "PHASE_7_AUTOMATION"
                session.data["phase_index"] = 7
                session._save_state()
                return session._prompt_phase_7()
    
            cur_trk = tracks[trk_idx]
            cur_sec = sections[sec_idx] if sec_idx < len(sections) else sections[0]
            cur_trk_is_aud = bool(cur_trk.get("is_audio", False) or str(cur_trk.get("role", "")).upper() == "VOCALS" or cur_trk.get("live_recording_mode", False))
    
            if cur_trk_is_aud:
                # Advance audio track to next track directly
                trk_idx += 1
                sec_idx = 0
                session_state["track_index"] = trk_idx
                session_state["section_index"] = sec_idx
                session._save_state()
                if trk_idx < len(tracks):
                    return self.prompt_by_clip_step(session, trk_idx, sec_idx)
                else:
                    self.enforce_pre_drop_vacuum(session, conn)
                    session.data["composition_session"] = {"active": False}
                    session.data["current_phase"] = "PHASE_7_AUTOMATION"
                    session.data["phase_index"] = 7
                    session._save_state()
                    return session._prompt_phase_7()
    
            s_bars = int(cur_sec.get("bars", 8))
            s_beats = float(s_bars * 4.0)
    
            # Check if user input indicates intentional silence or empty notes
            is_silence = any(w in text_norm for w in ["silencio", "silence", "mutear", "mute", "vacio", "vacío"]) or user_input.strip() in ("[]", "{}")
    
            clip_notes = []
            if not is_silence:
                for k, v in custom_notes_map.items():
                    if v:
                        clip_notes = list(v)
                        break
                if not clip_notes and not has_notes and not is_silence:
                    return {
                        "status": "AWAITING_CLIP_NOTES",
                        "phase": "PHASE_6_COMPOSITION",
                        "current_step": f"NOTAS REQUERIDAS: '{cur_trk.get('name')}' EN '{cur_sec.get('name')}'",
                        "action_taken": "Bloqueo: Notas requeridas para este clip.",
                        "question": f"⚠️ Por favor envía las notas MIDI explícitas para el clip de '{cur_trk.get('name')}' en '{cur_sec.get('name')}' ({s_bars} compases), o indica 'Silencio'.",
                        "instructions_for_ai": "Envía el JSON con las notas del clip o escribe 'Silencio'."
                    }
    
            # Deploy directly to Ableton Live
            t_idx = session._resolve_live_track_index(conn, cur_trk)
            current_beat = sum(float(sections[i].get("bars", 8)) * 4.0 for i in range(sec_idx))
    
            # Auto-tile motif if shorter than s_beats (e.g. 16-beat motif for a 64-beat clip)
            if clip_notes:
                max_reach = max(n.get("start_time", 0.0) + n.get("duration", 1.0) for n in clip_notes)
                if 0 < max_reach < s_beats and max_reach <= 16.0:
                    pattern_len = 16.0
                    tiled = []
                    offset = 0.0
                    while offset < s_beats:
                        for n in clip_notes:
                            n_st = n.get("start_time", 0.0) + offset
                            if n_st < s_beats:
                                n_c = dict(n)
                                n_c["start_time"] = round(n_st, 4)
                                n_c["duration"] = round(min(n.get("duration", 1.0), s_beats - n_st), 4)
                                tiled.append(n_c)
                        offset += pattern_len
                    clip_notes = tiled
    
            # Drum rack C1 octave sanitization
            role_upper = str(cur_trk.get("role", "")).upper()
            if role_upper == "DRUMS" and clip_notes:
                q3_notes = [d for d in clip_notes if 60 <= d.get("pitch", 0) <= 75]
                q1_notes = [d for d in clip_notes if 36 <= d.get("pitch", 0) <= 51]
                q2_notes = [d for d in clip_notes if 52 <= d.get("pitch", 0) <= 59]
                if len(q3_notes) == len(clip_notes) and len(q1_notes) == 0 and len(q2_notes) == 0:
                    for d in clip_notes:
                        d["pitch"] = max(36, d["pitch"] - 24)
    
            # Live LOM clip creation with governance healing & retry
            if conn and hasattr(conn, "send_command"):
                try:
                    self.deploy_clip_with_governance_retry(session, 
                        conn=conn,
                        t_idx=t_idx,
                        s_idx=sec_idx,
                        s_beats=s_beats,
                        s_notes_dicts=clip_notes,
                        current_beat=current_beat,
                        trk=cur_trk
                    )
                    cur_trk["notes_count"] = cur_trk.get("notes_count", 0) + len(clip_notes)
                except Exception as ex_clip:
                    cur_trk["deployment_failed"] = True
                    cur_trk["deployment_error"] = str(ex_clip)
                    logger.error(f"Clip deployment failed on track {t_idx} section {sec_idx}: {ex_clip}")
                    session.data["pending_instrument_swap_track"] = cur_trk.get("index")
                    session._save_state()
                    return {
                        "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                        "phase": "PHASE_6_COMPOSITION",
                        "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{cur_trk.get('name')}')",
                        "action_taken": f"Error de gobernanza en '{cur_trk.get('name')}': {ex_clip}. Reintento de auto-esculpido fallido.",
                        "question": (
                            f"⚠️ **Error de Gobernanza en Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                            f"El instrumento `{cur_trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                            f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                            f"**Opciones:**\n"
                            f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                            f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                            f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                        ),
                        "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                        "track_name": cur_trk.get("name"),
                        "track_index": t_idx
                    }
            else:
                cur_trk["notes_count"] = cur_trk.get("notes_count", 0) + len(clip_notes)
    
            # Advance to next clip
            sec_idx += 1
            if sec_idx >= len(sections):
                sec_idx = 0
                trk_idx += 1
    
            session_state["track_index"] = trk_idx
            session_state["section_index"] = sec_idx
            session._save_state()
    
            if trk_idx < len(tracks):
                return self.prompt_by_clip_step(session, trk_idx, sec_idx)
    
            self.enforce_pre_drop_vacuum(session, conn)
            session.data["composition_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_7_AUTOMATION"
            session.data["phase_index"] = 7
            session._save_state()
            return session._prompt_phase_7()
    
        session.data["current_phase"] = "PHASE_7_AUTOMATION"
        session.data["phase_index"] = 7
        session._save_state()
        return session._prompt_phase_7()
    
    def parse_ai_composition(self, session: Any, user_input: str) -> Tuple[Dict[str, Any], Dict[Tuple[Any, Any], List[Dict[str, Any]]], bool]:
        """
        Parses direct MIDI note composition payloads provided by AI/Producer.
        Supports multiple schemas (composition dict, tracks list/dict, roles dict, clips list).
        """
        meta: Dict[str, Any] = {}
        custom_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]] = {}
    
        def _norm_notes(raw_notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            res = []
            for n in raw_notes:
                if not isinstance(n, dict):
                    continue
                pitch = int(n.get("pitch", 60))
                st = float(n.get("start_time", n.get("start", 0.0)))
                dur = float(n.get("duration", 1.0))
                vel = int(n.get("velocity", 100))
                res.append({
                    "pitch": max(0, min(127, pitch)),
                    "start_time": round(st, 4),
                    "duration": round(dur, 4),
                    "velocity": max(1, min(127, vel)),
                    "mute": bool(n.get("mute", False))
                })
            return res
    
        data = None
        clean_path = str(user_input).strip().strip('"').strip("'")
        if not (os.path.exists(clean_path) and clean_path.endswith(".json")):
            path_m = re.search(r'([A-Za-z]:\\[^"\'\r\n]+\.json|/[^"\'\r\n]+\.json)', user_input)
            if path_m and os.path.exists(path_m.group(1)):
                clean_path = path_m.group(1)

        if os.path.exists(clean_path) and clean_path.endswith(".json"):
            try:
                with open(clean_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None
    
        if not data:
            json_str = None
            fence_m = re.search(r"```(?:json)?\s*([\{\[][\s\S]*?[\}\]])\s*```", user_input, re.DOTALL)
            if fence_m:
                json_str = fence_m.group(1)
            else:
                brace_m = re.search(r"([\{\[][\s\S]*[\}\]])", user_input, re.DOTALL)
                if brace_m:
                    json_str = brace_m.group(1)
    
            if not json_str:
                return meta, custom_map, False
    
            try:
                data = json.loads(json_str)
            except Exception:
                return meta, custom_map, False
    
        if isinstance(data, list):
            custom_map[("current", "all")] = _norm_notes(data)
            return meta, custom_map, len(custom_map) > 0
    
        if not isinstance(data, dict):
            return meta, custom_map, False
    
        for k in ["bpm", "key", "scale", "genre"]:
            if k in data:
                meta[k] = data[k]
    
        # Single track 'notes' list or 'sections' dict
        if "notes" in data and isinstance(data["notes"], list):
            custom_map[("current", "all")] = _norm_notes(data["notes"])
        if "sections" in data and isinstance(data["sections"], dict):
            for s_k, n_list in data["sections"].items():
                if isinstance(n_list, list):
                    try:
                        s_idx = int(s_k)
                    except ValueError:
                        s_idx = str(s_k).lower()
                    custom_map[("current", s_idx)] = _norm_notes(n_list)
    
        # Direct section keys at root level (e.g. {"Intro": [...], "Verse 1": [...]})
        for s_k, n_list in data.items():
            if str(s_k).lower() in ("intro", "verse", "verse 1", "verse 2", "buildup", "build", "drop", "drop 1", "drop 2", "puente", "breakdown", "outro", "all") and isinstance(n_list, list):
                custom_map[("current", str(s_k).lower())] = _norm_notes(n_list)
    
        # 1. 'composition' dict or list: {track_key: {section_key: [notes]}} or list of track items
        comp = data.get("composition")
        if isinstance(comp, dict):
            for t_k, sec_val in comp.items():
                if isinstance(sec_val, dict):
                    for s_k, n_list in sec_val.items():
                        try:
                            s_idx = int(s_k)
                        except ValueError:
                            s_idx = str(s_k).lower()
                        if isinstance(n_list, list):
                            custom_map[(t_k, s_idx)] = _norm_notes(n_list)
                elif isinstance(sec_val, list):
                    custom_map[(t_k, "all")] = _norm_notes(sec_val)
        elif isinstance(comp, list):
            for item in comp:
                if isinstance(item, dict):
                    t_ident = item.get("track", item.get("track_name", item.get("track_index", item.get("role", item.get("name")))))
                    s_idx = item.get("section", item.get("section_index", 0))
                    try:
                        s_idx = int(s_idx)
                    except ValueError:
                        s_idx = str(s_idx).lower()
                    normed = _norm_notes(item.get("notes", []))
                    custom_map[(t_ident, s_idx)] = normed
                    if isinstance(t_ident, str):
                        custom_map[(t_ident.lower(), s_idx)] = normed
                        if not t_ident.isdigit():
                            norm_r = RoleTrackOrchestrator.normalize_role(t_ident)
                            if norm_r:
                                custom_map[(norm_r, s_idx)] = normed
                                custom_map[(norm_r.lower(), s_idx)] = normed
    
        # 2. 'tracks' list or dict
        trks = data.get("tracks")
        if isinstance(trks, dict):
            for t_k, sec_val in trks.items():
                if isinstance(sec_val, dict):
                    for s_k, n_list in sec_val.items():
                        try:
                            s_idx = int(s_k)
                        except ValueError:
                            s_idx = str(s_k).lower()
                        if isinstance(n_list, list):
                            custom_map[(t_k, s_idx)] = _norm_notes(n_list)
                elif isinstance(sec_val, list):
                    custom_map[(t_k, "all")] = _norm_notes(sec_val)
        elif isinstance(trks, list):
            for trk_item in trks:
                if not isinstance(trk_item, dict):
                    continue
                t_ident = trk_item.get("index", trk_item.get("track_index", trk_item.get("name", trk_item.get("role"))))
                if "clips" in trk_item and isinstance(trk_item["clips"], list):
                    for c_idx, clip in enumerate(trk_item["clips"]):
                        if isinstance(clip, dict):
                            s_idx = clip.get("section_index", clip.get("section", c_idx))
                            try:
                                s_idx = int(s_idx)
                            except ValueError:
                                s_idx = str(s_idx).lower()
                            custom_map[(t_ident, s_idx)] = _norm_notes(clip.get("notes", []))
                elif "notes" in trk_item and isinstance(trk_item["notes"], list):
                    custom_map[(t_ident, "all")] = _norm_notes(trk_item["notes"])
    
        # 3. 'roles' dict
        roles = data.get("roles")
        if isinstance(roles, dict):
            for r_k, r_val in roles.items():
                r_upper = str(r_k).upper()
                if isinstance(r_val, dict):
                    for s_k, n_list in r_val.items():
                        try:
                            s_idx = int(s_k)
                        except ValueError:
                            s_idx = str(s_k).lower()
                        if isinstance(n_list, list):
                            custom_map[(r_upper, s_idx)] = _norm_notes(n_list)
                elif isinstance(r_val, list):
                    custom_map[(r_upper, "all")] = _norm_notes(r_val)
    
        # 4. 'clips' list
        clips = data.get("clips")
        if isinstance(clips, list):
            for clip in clips:
                if isinstance(clip, dict):
                    t_ident = clip.get("track", clip.get("track_index", clip.get("role", clip.get("name"))))
                    s_idx = clip.get("section", clip.get("section_index", 0))
                    try:
                        s_idx = int(s_idx)
                    except ValueError:
                        s_idx = str(s_idx).lower()
                    normed = _norm_notes(clip.get("notes", []))
                    custom_map[(t_ident, s_idx)] = normed
                    if isinstance(t_ident, str) and not t_ident.isdigit():
                        norm_r = RoleTrackOrchestrator.normalize_role(t_ident)
                        if norm_r:
                            custom_map[(norm_r, s_idx)] = normed
                            custom_map[(norm_r.lower(), s_idx)] = normed
    
        return meta, custom_map, len(custom_map) > 0
    
    def find_custom_notes_for_track_section(
        self,
        session: Any,
        custom_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        trk: Dict[str, Any],
        s_idx: int,
        s_name: str,
        s_beats: float
    ) -> Optional[List[Dict[str, Any]]]:
        t_idx = trk.get("index")
        t_name = str(trk.get("name", "")).lower()
        t_role = str(trk.get("role", "")).upper()
        s_name_lower = str(s_name).lower()
    
        # Bidirectional role aliases resolution
        role_aliases = RoleTrackOrchestrator.get_role_aliases(t_role)
        norm_name_role = RoleTrackOrchestrator.normalize_role(trk.get("name", ""))
        for r_extra in RoleTrackOrchestrator.get_role_aliases(norm_name_role):
            if r_extra not in role_aliases:
                role_aliases.append(r_extra)
    
        keys_to_check = [
            (t_idx, s_idx),
            (str(t_idx), s_idx),
            (str(t_idx), str(s_idx)),
            (t_name, s_idx),
            (t_name, str(s_idx)),
            (t_idx, s_name_lower),
            (str(t_idx), s_name_lower),
            (t_name, s_name_lower),
        ]
        for alias in role_aliases:
            keys_to_check.extend([
                (alias, s_idx),
                (alias, str(s_idx)),
                (alias, s_name_lower),
                (alias.lower(), s_idx),
                (alias.lower(), str(s_idx)),
                (alias.lower(), s_name_lower),
            ])
    
        for k in keys_to_check:
            if k in custom_map:
                return list(custom_map[k])
    
        # Cross-map lookup across custom_map keys for matching section
        for (map_ident, map_sec), notes_val in custom_map.items():
            if str(map_sec).lower() in [str(s_idx), str(s_name_lower)]:
                map_ident_str = str(map_ident).strip().upper()
                if map_ident_str in role_aliases or map_ident_str.lower() in t_name or t_name in map_ident_str.lower():
                    return list(notes_val)
    
        # Check fallback to "all"
        all_keys = [
            (t_idx, "all"),
            (str(t_idx), "all"),
            (t_name, "all"),
        ]
        for alias in role_aliases:
            all_keys.extend([
                (alias, "all"),
                (alias.lower(), "all"),
            ])
        for k in all_keys:
            if k in custom_map:
                base_notes = custom_map[k]
                if not base_notes:
                    return []
                # If the base pattern is shorter than section beats, tile it to fill section
                max_reach = max(n["start_time"] + n["duration"] for n in base_notes)
                if max_reach > 0 and s_beats > max_reach:
                    pattern_len = 16.0 if max_reach <= 16.0 else max_reach
                    tiled = []
                    offset = 0.0
                    while offset < s_beats:
                        for n in base_notes:
                            n_st = n["start_time"] + offset
                            if n_st < s_beats:
                                n_copy = dict(n)
                                n_copy["start_time"] = round(n_st, 4)
                                n_dur = min(n["duration"], s_beats - n_st)
                                n_copy["duration"] = round(n_dur, 4)
                                tiled.append(n_copy)
                        offset += pattern_len
                    return tiled
                else:
                    return list(base_notes)
    
        # Cross-map fallback for "all"
        for (map_ident, map_sec), notes_val in custom_map.items():
            if str(map_sec).lower() == "all":
                map_ident_str = str(map_ident).strip().upper()
                if map_ident_str in role_aliases or map_ident_str.lower() in t_name or t_name in map_ident_str.lower():
                    base_notes = notes_val
                    if not base_notes:
                        return []
                    max_reach = max(n["start_time"] + n["duration"] for n in base_notes)
                    if max_reach > 0 and s_beats > max_reach:
                        pattern_len = 16.0 if max_reach <= 16.0 else max_reach
                        tiled = []
                        offset = 0.0
                        while offset < s_beats:
                            for n in base_notes:
                                n_st = n["start_time"] + offset
                                if n_st < s_beats:
                                    n_copy = dict(n)
                                    n_copy["start_time"] = round(n_st, 4)
                                    n_dur = min(n["duration"], s_beats - n_st)
                                    n_copy["duration"] = round(n_dur, 4)
                                    tiled.append(n_copy)
                            offset += pattern_len
                        return tiled
                    else:
                        return list(base_notes)
    
        return None

    _find_custom_notes_for_track_section = find_custom_notes_for_track_section

    def _handle_phase_6(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text_norm = _normalize_text(user_input)
    
        # Check if user selects a modular composition mode
        if any(w in text_norm for w in ["por seccion", "seccion por seccion"]) or ("opcion 1" in text_norm and "seccion" in text_norm):
            mode = "BY_SECTION"
        elif any(w in text_norm for w in ["por pista", "pista por pista"]) or ("opcion 2" in text_norm and "pista" in text_norm):
            mode = "BY_TRACK"
        elif any(w in text_norm for w in ["combinado", "seccion y pista", "opcion 3"]):
            mode = "COMBINED"
        elif any(w in text_norm for w in ["por clip", "clip por clip", "clip", "de 16 en 16", "de 8 en 8", "16 en 16", "8 en 8", "opcion 1"]):
            mode = "BY_CLIP"
        elif "opcion 2" in text_norm:
            mode = "BY_TRACK"
        else:
            mode = None

        if mode is not None and not any(w in text_norm for w in ["tonalidad", "bpm", "menor", "mayor", "opcion 4"]):
            session.data["composition_session"] = {
                "active": True,
                "mode": mode,
                "section_index": 0,
                "track_index": 0
            }
            session._save_state()
            sections = session.data.get("sections", [])
            tracks = session.data.get("tracks", [])
            first_sec = sections[0] if sections else {"name": "Intro", "bars": 8}
            first_trk = tracks[0] if tracks else {"name": "Drums", "role": "DRUMS"}
            step_desc = f"Sección 1/{len(sections)}: '{first_sec.get('name')}'" if mode == "BY_SECTION" else (f"Pista 1/{len(tracks)}: '{first_trk.get('name')}'" if mode == "BY_TRACK" else f"Pista '{first_trk.get('name')}' en '{first_sec.get('name')}'")
            return {
                "status": "MODULAR_COMPOSITION_INITIALIZED",
                "mode": mode,
                "current_step": f"COMPOSICIÓN MODULAR INICIADA: {step_desc}",
                "action_taken": f"Modo de composición '{mode}' activado. Esperando notas del primer bloque.",
                "question": f"🎼 **Composición Modular Activada ({step_desc}):**\n\nDefine las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para este bloque.",
                "instructions_for_ai": f"Envía las notas MIDI explícitas para {step_desc}.",
                "phase": "PHASE_6_COMPOSITION"
            }
    
        u_clean = _normalize_text(user_input)
    
        # 0. Direct Instrument Swap Trigger from Phase 6
        is_swap_trigger = any(w in u_clean for w in [
            "cambiar instrumento", "cambiar sonido", "cambio de instrumento", "cambio de sonido",
            "reemplazar instrumento", "reemplazar sonido", "otro instrumento", "swap instrument",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger:
            failed_t_idx = session.data.get("pending_instrument_swap_track")
            if failed_t_idx is not None:
                tracks = session.data.get("tracks", [])
                target_t = next((t for t in tracks if t.get("index") == failed_t_idx), None)
                if target_t:
                    session.data["instrument_swap_state"] = {
                        "active": True,
                        "stage": "SELECT_PRESET",
                        "track_index": target_t.get("index"),
                        "track_name": target_t.get("name"),
                        "track_role": target_t.get("role"),
                        "origin_phase": "PHASE_6_COMPOSITION"
                    }
                    session._save_state()
                    return self._prompt_instrument_swap_preset(target_t)
            return self._initiate_instrument_swap_flow(conn, user_input)
    
        # 0. Retry Trigger for Failed Governance Deployments
        is_retry = any(w in u_clean for w in ["reintentar", "intentar de nuevo", "reintenta", "retry"])
        cached_notes_map = getattr(self, "_last_custom_notes_map", None)
        if is_retry and cached_notes_map:
            tracks = session.data.get("tracks", [])
            for t in tracks:
                t["deployment_failed"] = False
                t["deployment_error"] = None
            sections = session.data.get("sections", [])
            composed_summary = []
            for trk in tracks:
                total_notes_trk = self.deploy_single_track_composition(session, conn, trk, cached_notes_map, sections)
                composed_summary.append(f"{trk['name']} ({total_notes_trk} notas en {len(sections)} secciones)")
    
            failed_governance_tracks = [t for t in tracks if t.get("deployment_failed")]
            if failed_governance_tracks:
                first_failed = failed_governance_tracks[0]
                session.data["pending_instrument_swap_track"] = first_failed.get("index")
                session._save_state()
                return {
                    "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                    "phase": "PHASE_6_COMPOSITION",
                    "current_step": "FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO POR GOBERNANZA)",
                    "action_taken": f"Reintento fallido en {len(failed_governance_tracks)} pista(s). El instrumento '{first_failed.get('instrument')}' continúa rechazado por gobernanza ({first_failed.get('deployment_error')}).",
                    "question": (
                        f"⚠️ **Error Persistente de Gobernanza en Pista '{first_failed.get('name')}':**\n\n"
                        f"El instrumento `{first_failed.get('instrument')}` sigue sin estar esculpido (`INIT_SYNTH_DETECTED`).\n\n"
                        f"Por favor escribe 'cambiar instrumento' para elegir otro instrumento o provee parámetros manuales para esculpirlo."
                    ),
                    "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                    "failed_tracks": [t["name"] for t in failed_governance_tracks],
                    "target_track": first_failed.get("index")
                }
            session.data["pending_instrument_swap_track"] = None
            self.enforce_pre_drop_vacuum(session, conn)
            session.data["current_phase"] = "PHASE_7_AUTOMATION"
            session.data["phase_index"] = 7
            session._save_state()
            return session._prompt_phase_7()
    
        ai_meta, custom_notes_map, has_custom_notes = self.parse_ai_composition(session, user_input)
        if has_custom_notes:
            self._last_custom_notes_map = custom_notes_map
    
        is_explicit_key_directive = bool(re.search(r'\bKEY\s+[A-G][#b]?\b', user_input, re.IGNORECASE))
        is_test_env = (
            "PYTEST_CURRENT_TEST" in os.environ
            or os.environ.get("ABLETON_TEST_MODE") == "1"
            or "Mock" in type(conn).__name__
        )
        if not has_custom_notes and not is_explicit_key_directive:
            return {
                "status": "AWAITING_EXPLICIT_AI_COMPOSITION",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (NOTAS EXPLÍCITAS REQUERIDAS)",
                "action_taken": "Bloqueo estricto del motor: Se prohíbe terminantemente el autocompletado y relleno procedural de notas.",
                "question": (
                    "🚫 **COMPOSICIÓN REQUERIDA (PROHIBIDO AUTO-RELLENO PROCEDURAL):**\n\n"
                    "El motor prohíbe el autocompletado y relleno de notas genéricas procedimentales.\n"
                    "La IA debe definir y suministrar obligatoriamente las notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) para cada instrumento y sección.\n\n"
                    "Por favor, envía la composición en formato JSON con la clave `composition` o `tracks` detallando las notas para cada pista en el arreglo."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas para cada pista y sección activa. El motor no autocompletará notas.",
            }
    
        text = user_input.upper()
    
        key = ai_meta.get("key")
        if not key:
            key = "F"
            for k_candidate in ["C#", "DB", "D#", "EB", "F#", "GB", "G#", "AB", "A#", "BB", "C", "D", "E", "F", "G", "A", "B"]:
                if f" {k_candidate} " in f" {text} " or f"KEY {k_candidate}" in text or f"TONALIDAD {k_candidate}" in text:
                    key = k_candidate.title()
                    break
    
        scale = ai_meta.get("scale")
        if not scale:
            scale = "natural_minor"
            if "ROYAL" in text or "JPOP" in text or "J-POP" in text or "ROYAL_ROAD" in text:
                scale = "royal_road"
            elif "DORIAN" in text or "DORICA" in text:
                scale = "dorian"
            elif "ARMONICA" in text or "HARMONIC" in text:
                scale = "harmonic_minor"
            elif "MAYOR" in text or "MAJOR" in text:
                scale = "major"
            elif "CLASSIC_DARK" in text or "OSCURA" in text or "CLASSIC DARK" in text:
                scale = "classic_dark"
            elif "JAZZ_HIPHOP" in text or "JAZZ HIPHOP" in text or "JAZZ" in text:
                scale = "jazz_hiphop"
            elif "SOUL_FEEL" in text or "SOUL FEEL" in text or "SOUL" in text:
                scale = "soul_feel"
            elif "MELANCHOLIC" in text or "MELANCOLICA" in text:
                scale = "melancholic"
            elif "MINIMAL_JAZZ" in text or "MINIMAL" in text:
                scale = "minimal_jazz"
            elif "PHRYGIAN" in text or "FRIGIA" in text:
                scale = "phrygian_dark"
            elif "NEO_SOUL" in text or "NEOSOUL" in text:
                scale = "neo_soul"
    
        bpm = 120.0
        if "bpm" in ai_meta:
            try:
                bpm = float(ai_meta["bpm"])
            except (ValueError, TypeError):
                bpm = 120.0
        else:
            bpm_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*BPM", user_input, re.IGNORECASE)
            if bpm_match:
                bpm = float(bpm_match.group(1))
    
        # Detect genre from user input, ai_meta or fallback to BPM inference
        detected_genre = ai_meta.get("genre")
        if not detected_genre:
            for g_candidate in ["trap", "house", "neo_soul", "reggaeton", "synthwave", "boom_bap", "techno", "cumbia", "afrobeat", "edm", "drum_and_bass", "pop", "rock", "lofi", "hip_hop", "hip hop", "dnb"]:
                if g_candidate.upper() in text:
                    detected_genre = g_candidate.replace(" ", "_").replace("hip_hop", "trap").replace("lofi", "boom_bap").replace("dnb", "drum_and_bass")
                    break
        if detected_genre:
            session.data["genre"] = detected_genre
        elif "genre" not in session.data:
            session.data["genre"] = resolve_genre_style(None, bpm=bpm).value
    
        session.data["key"] = key
        session.data["scale"] = scale
        session.data["bpm"] = bpm
        session.data["ai_composed"] = bool(has_custom_notes)
        total_bars = session.data.get("total_bars", 96)
    
        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("set_tempo", {"tempo": bpm})
            except Exception:
                pass
            try:
                k_upper = str(key).upper()
                s_upper = "MINOR" if any(w in str(scale).upper() for w in ["MINOR", "MENOR", "DORIAN", "PHRYGIAN", "DARK", "MELANCHOLIC", "SOUL"]) else ("CHROMATIC" if "CHROM" in str(scale).upper() else "MAJOR")
                k_val = VocalChainProcessor.AUTOTUNE_KEY_VALUES.get(k_upper, 0.48)
                s_val = VocalChainProcessor.AUTOTUNE_SCALE_VALUES.get(s_upper, 0.05)
                sync_at_code = f"""
for trk in song.tracks:
    for d in trk.devices:
        d_name = d.name.lower()
        if 'auto-tune' in d_name or 'autotune' in d_name:
            for p in d.parameters:
                p_l = p.name.lower()
                if 'key' in p_l:
                    p.value = {k_val}
                elif 'scale' in p_l:
                    p.value = {s_val}
"""
                conn.send_command("execute_code", {"code": sync_at_code})
            except Exception as ex_sync:
                logger.debug(f"Notice auto-tuning sync in Phase 6: {ex_sync}")
    
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        if not sections:
            sections = [
                {"name": "Intro", "bars": 8, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 8},
                {"name": "Buildup", "bars": 8, "start_bar": 24},
                {"name": "Drop 1", "bars": 16, "start_bar": 32},
                {"name": "Puente (Calma)", "bars": 8, "start_bar": 48},
                {"name": "Drop 2 (Climax)", "bars": 16, "start_bar": 56},
                {"name": "Outro", "bars": 8, "start_bar": 72}
            ]
    
        composed_summary = []
    
        for trk in tracks:
            total_notes_trk = self.deploy_single_track_composition(session, conn, trk, custom_notes_map, sections)
            composed_summary.append(f"{trk['name']} ({total_notes_trk} notas en {len(sections)} secciones)")
    
        failed_governance_tracks = [t for t in tracks if t.get("deployment_failed")]
        if failed_governance_tracks:
            first_failed = failed_governance_tracks[0]
            session.data["pending_instrument_swap_track"] = first_failed.get("index")
            session._save_state()
            failed_desc = ", ".join([f"'{t['name']}' ({t.get('instrument', 'Sin instrumento')})" for t in failed_governance_tracks])
            return {
                "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO POR GOBERNANZA)",
                "action_taken": f"Bloqueo de gobernanza: {len(failed_governance_tracks)} pista(s) no pudieron recibir clips ({failed_desc}). Se intentó auto-esculpido pero el instrumento falló.",
                "question": (
                    f"⚠️ **Error Crítico de Gobernanza en Pista '{first_failed.get('name')}' (Rol: `{first_failed.get('role')}`):**\n\n"
                    f"El instrumento `{first_failed.get('instrument')}` fue bloqueado por el gatekeeper (`INIT_SYNTH_DETECTED`) y el reintento automático no pudo resolverlo.\n"
                    f"Detalle: `{first_failed.get('deployment_error')}`.\n\n"
                    f"El motor prohíbe avanzar con pistas vacías o silenciar errores como advertencias.\n\n"
                    f"**Acciones Disponibles:**\n"
                    f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o 'cargar [preset]' para seleccionar un generador de sonido compatible de la librería.\n"
                    f"2. 🎛️ **Esculpir Parámetros:** Provee valores de macros o síntesis para esculpir este sintetizador (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                    f"3. 🔁 **Reintentar:** Envía 'reintentar' tras inicializar o ajustar el instrumento manualmente en Live."
                ),
                "instructions_for_ai": "Pide al usuario seleccionar un nuevo instrumento o envía parámetros de esculpido explícitos.",
                "failed_tracks": [t["name"] for t in failed_governance_tracks],
                "target_track": first_failed.get("index")
            }
    
        # Enforce Physical Pre-Drop Vacuum across all arrangement clips in Live (Point 3)
        self.enforce_pre_drop_vacuum(session, conn)
    
        # Phase 6 Gatekeeper of Completeness: Guarantee zero unpopulated MIDI tracks
        unpopulated_midi_tracks = []
        for trk in tracks:
            r = str(trk.get("role", "")).upper()
            is_aud = bool(trk.get("is_audio", False) or r == "VOCALS")
            is_live_rec = bool(trk.get("live_recording_mode", False))
            if is_aud or is_live_rec:
                continue
            notes_cnt = trk.get("notes_count", 0)
            if notes_cnt == 0:
                logger.warning(f"Phase 6 Gatekeeper: Track '{trk['name']}' has 0 notes across the arrangement.")
                unpopulated_midi_tracks.append(trk["name"])
    
        if unpopulated_midi_tracks and not is_explicit_key_directive:
            session._save_state()
            return {
                "status": "PHASE_6_GATEKEEPER_BLOCKED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER)",
                "action_taken": f"Gatekeeper de Completitud activado: {len(unpopulated_midi_tracks)} pista(s) sin notas ({', '.join(unpopulated_midi_tracks)}).",
                "question": (
                    f"⚠️ **Gatekeeper de Completitud Activado:**\n\n"
                    f"Las siguientes pistas de instrumento carecen de notas MIDI: **{', '.join(unpopulated_midi_tracks)}**.\n"
                    f"El motor prohíbe el autocompletado y relleno procedural. Bloquea la transición a Fase 7 hasta que la IA defina explícitamente las notas MIDI para estas pistas.\n\n"
                    f"Por favor, provee las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para las pistas vacías para continuar."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas para las pistas vacías indicadas antes de continuar a Fase 7. El motor no autocompletará notas.",
                "unpopulated_tracks": unpopulated_midi_tracks
            }
    
        # Phase 6 Gatekeeper: Synthesizer Outro Non-Silencing Law
        # El sintetizador nunca se debe silenciar en el Outro (debe mantener notas/drones para el colapso armónico)
        outro_sec_idx = next((i for i, s in enumerate(sections) if "outro" in str(s.get("name", "")).lower()), None)
        silenced_synths_in_outro = []
        if outro_sec_idx is not None:
            o_sec = sections[outro_sec_idx]
            o_name = o_sec.get("name", "Outro")
            o_bars = int(o_sec.get("bars", 8))
            o_beats = float(o_bars * 4.0)
            for trk in tracks:
                r = str(trk.get("role", "")).upper()
                nm = str(trk.get("name", "")).lower()
                is_aud = bool(trk.get("is_audio", False) or r == "VOCALS" or "vocal" in nm or trk.get("live_recording_mode", False))
                if is_aud:
                    continue
                is_synth = (r in ("LEAD", "SYNTH") or any(k in nm for k in ["synth", "vital", "serum", "saw", "lead"]))
                if is_synth and has_custom_notes:
                    o_notes = self.find_custom_notes_for_track_section(session, 
                        custom_map=custom_notes_map,
                        trk=trk,
                        s_idx=outro_sec_idx,
                        s_name=o_name,
                        s_beats=o_beats
                    )
                    if not o_notes:
                        silenced_synths_in_outro.append(trk.get("name", f"Pista {trk.get('index')}"))
    
        if silenced_synths_in_outro:
            session._save_state()
            return {
                "status": "PHASE_6_GATEKEEPER_BLOCKED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER - SINTETIZADOR EN OUTRO)",
                "action_taken": f"Gatekeeper de Outro activado: el sintetizador no se debe silenciar en el outro ({', '.join(silenced_synths_in_outro)}).",
                "question": (
                    f"⚠️ **Gatekeeper de Outro Activado (Sintetizador no debe silenciarse):**\n\n"
                    f"Las siguientes pistas de sintetizador carecen de notas en la sección Outro: **{', '.join(silenced_synths_in_outro)}**.\n"
                    f"La regla de producción exige terminantemente que el sintetizador no se silencie en el Outro para mantener drones armónicos sostenidos que alimenten el colapso y la saturación final.\n\n"
                    f"Por favor, provee las notas MIDI para el sintetizador en la sección Outro para continuar a Fase 7."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas (drones armónicos sostenidos) para el sintetizador en el Outro. El motor prohíbe silenciar el sintetizador en el outro.",
                "silenced_synth_tracks": silenced_synths_in_outro
            }
    
        session.data["current_phase"] = "PHASE_7_AUTOMATION"
        session.data["phase_index"] = 7
        session.data["composed_summary"] = composed_summary
        session._save_state()
    
        return session._prompt_phase_7()
    
    # -------------------------------------------------------------------------
    # FASE 7: AUTOMATIZACIONES DINÁMICAS DE PISTAS Y TRANSICIONES EN ARRANGEMENT
    # -------------------------------------------------------------------------
    def build_recipe_from_session(self, session: Any) -> ProductionRecipe:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        key = session.data.get("key", "F")
        scale = session.data.get("scale", "natural_minor")
        bpm = float(session.data.get("bpm", 120.0))
    
        recipe_tracks = []
        for trk in tracks:
            recipe_tracks.append(TrackBlueprint(
                track_index=trk["index"],
                name=trk["name"],
                role=trk["role"].lower(),
                instrument_name=trk.get("instrument", trk["name"])
            ))
    
        recipe_sections = []
        current_bar = 0
        for idx, s in enumerate(sections):
            s_name = s.get("name", f"Section {idx+1}")
            s_bars = int(s.get("bars", 8))
            recipe_sections.append(RecipeSection(
                name=s_name,
                start_bar=current_bar,
                length_bars=s_bars,
                active_roles=[t.role for t in recipe_tracks]
            ))
            current_bar += s_bars
    
        return ProductionRecipe(
            title="Copilot Guided Production",
            genre_reference="Modern Production",
            key=key,
            scale=scale,
            chord_progression=["Fm", "Db", "Ab", "Eb"],
            bpm=bpm,
            tracks=recipe_tracks,
            sections=recipe_sections
        )
    

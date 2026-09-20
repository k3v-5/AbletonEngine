# engine/production/copilot/phases/phase_6/gatekeepers.py
"""
Phase 6 Gatekeepers:
Enforces mandatory explicit composition, unpopulated MIDI track barriers,
synthesizer outro non-silencing laws, and physical pre-drop vacuum.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("Phase6Gatekeepers")


class Phase6Gatekeepers:
    """Acoustic and workflow safety checks for Phase 6."""

    @staticmethod
    def enforce_pre_drop_vacuum(session: Any, conn: Any) -> None:
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

    @staticmethod
    def check_explicit_composition_required(
        session: Any,
        user_input: str,
        has_custom_notes: bool,
        is_explicit_key_directive: bool
    ) -> Optional[Dict[str, Any]]:
        """Blocks advancement if no custom notes or explicit key directive was supplied."""
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
        return None

    @staticmethod
    def check_unpopulated_midi_tracks(
        session: Any,
        tracks: List[Dict[str, Any]],
        is_explicit_key_directive: bool
    ) -> Optional[Dict[str, Any]]:
        """Blocks transition if an active instrumental MIDI track has zero notes."""
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
        return None

    @staticmethod
    def check_silenced_synths_in_outro(
        session: Any,
        tracks: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        has_custom_notes: bool,
        custom_notes_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        parser_fn: Any
    ) -> Optional[Dict[str, Any]]:
        """Enforces that synthesizer tracks sustain notes into the Outro section."""
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
                    o_notes = parser_fn(
                        session,
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
        return None

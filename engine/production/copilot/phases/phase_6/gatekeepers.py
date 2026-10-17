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
        """
        Enforces physical pre-drop vacuum (1.0 beat silence before Drop / Chorus downbeats)
        on low-end and harmonic bed tracks (KICK, BASS, 808, SUB, PAD, KEYS, RHYTHM_GUITAR)
        while preserving DRUMS turnaround fills, FX risers, and Vocal/Lead pickups.
        """
        if conn is not None and hasattr(conn, "send_command"):
            try:
                sec_drop_beats = []
                if session and hasattr(session, "data"):
                    ts = session.data.get("time_signature", (4, 4))
                    sig_num, sig_den = (int(ts[0]), int(ts[1])) if isinstance(ts, (list, tuple)) and len(ts) >= 2 else (4, 4)
                    beats_per_bar = float(sig_num) * (4.0 / max(1, sig_den))
                    cur_bar = 0.0
                    for sec in session.data.get("sections", []):
                        if not isinstance(sec, dict):
                            continue
                        s_nm = str(sec.get("name", "")).lower()
                        raw_sb = sec.get("start_bar")
                        s_start = float(raw_sb) if raw_sb is not None else cur_bar
                        raw_bars = sec.get("bars")
                        s_bars = float(raw_bars) if raw_bars is not None else 8.0
                        is_pre = any(p in s_nm for p in ("pre-", "pre ", "precoro", "prechorus", "predrop", "buildup", "build"))
                        if s_start > 0 and not is_pre and any(w in s_nm for w in ("drop", "chorus", "coro", "estribillo", "climax", "clímax", "switch", "caida", "caída")):
                            sec_drop_beats.append(s_start * beats_per_bar)
                        cur_bar = s_start + s_bars

                code_phys_vac = f"""
drop_beats = set({repr(sec_drop_beats)})
for cp in getattr(song, 'cue_points', []):
    cp_nm = str(getattr(cp, 'name', '')).lower()
    cp_t = float(getattr(cp, 'time', 0.0))
    is_pre_cp = False
    for p in ('pre-', 'pre ', 'precoro', 'prechorus', 'predrop', 'buildup', 'build'):
        if p in cp_nm:
            is_pre_cp = True
            break
    if cp_t > 0.0 and not is_pre_cp:
        for w in ('drop', 'chorus', 'coro', 'estribillo', 'switch', 'climax', 'clímax', 'caida', 'caída', 'corte'):
            if w in cp_nm:
                drop_beats.add(cp_t)
                break

for t in song.tracks:
    t_nm = str(getattr(t, 'name', '')).lower()
    # Preserve drum turnaround fills, FX risers, and vocal/lead pickups
    should_skip = False
    for skip_w in ('[drums]', '[percussion]', '[fx]', '[vocals]', '[lead]', 'riser', 'fill', 'motoric_drums'):
        if skip_w in t_nm:
            should_skip = True
            break
    if should_skip and '[kick]' not in t_nm and 'guitar' not in t_nm:
        continue
    try:
        clips = list(t.arrangement_clips) if not getattr(t, 'is_foldable', False) else []
    except Exception:
        continue
    for c in clips:
        if getattr(c, 'is_midi_clip', False):
            for cp_t in sorted(drop_beats):
                v_start = max(0.0, cp_t - 1.08)
                if c.start_time < cp_t and c.end_time > v_start:
                    rel_from = max(0.0, v_start - c.start_time)
                    rel_span = max(0.1, cp_t - max(v_start, c.start_time))
                    try:
                        c.remove_notes_extended(0, 128, rel_from, rel_span)
                    except Exception:
                        pass
result = sorted(drop_beats)
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
            is_aud = bool(
                trk.get("is_audio", False)
                or trk.get("live_recording_mode", False)
                or (r == "VOCALS" and trk.get("sample_path") and not trk.get("chopping_mode"))
            )
            if is_aud:
                continue
            notes_cnt = trk.get("notes_count", 0)
            if notes_cnt == 0:
                logger.warning(f"Phase 6 Gatekeeper: Track '{trk['name']}' has 0 notes across the arrangement.")
                unpopulated_midi_tracks.append(trk.get("original_name") or trk["name"])

        if unpopulated_midi_tracks and not is_explicit_key_directive:
            session._save_state()
            return {
                "status": "PHASE_6_GATEKEEPER_BLOCKED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "PASO 4: COMPOSICIÓN (BLOQUEADA POR ARNÉS DE COMPLETITUD)",
                "action_taken": f"Gatekeeper de Completitud activado: {len(unpopulated_midi_tracks)} pista(s) MIDI sin notas ({', '.join(unpopulated_midi_tracks)}).",
                "question": (
                    f"⚠️ **Arnés de Completitud Musical Activado (Cero Pistas Huérfanas):**\n\n"
                    f"Las siguientes pistas MIDI carecen de notas en el Arrangement: **{', '.join(unpopulated_midi_tracks)}**.\n"
                    f"El motor prohíbe el autocompletado procedural y bloquea el avance al Paso 5 (Esculpido de Síntesis) hasta que definas explícitamente las notas MIDI para todas las pistas.\n\n"
                    f"Por favor, provee las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para las pistas vacías para continuar."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas para las pistas vacías indicadas antes de continuar al Paso 5 (Esculpido de Síntesis).",
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
        """
        Checks synthesizer activity in the Outro section.
        Genre-agnostic: Only blocks if `enforce_synth_outro_drone` is explicitly enabled in session.data;
        otherwise respects artistic silence in the Outro (e.g., Rock, Jazz, Boom-Bap, Pop, Acoustic endings).
        """
        if not (session and hasattr(session, "data") and session.data.get("enforce_synth_outro_drone", False)):
            return None

        ts = session.data.get("time_signature", (4, 4)) if (session and hasattr(session, "data")) else (4, 4)
        sig_num, sig_den = (int(ts[0]), int(ts[1])) if isinstance(ts, (list, tuple)) and len(ts) >= 2 else (4, 4)
        beats_per_bar = float(sig_num) * (4.0 / max(1, sig_den))

        outro_sec_idx = next((i for i, s in enumerate(sections) if "outro" in str(s.get("name", "")).lower()), None)
        silenced_synths_in_outro = []
        if outro_sec_idx is not None:
            o_sec = sections[outro_sec_idx]
            o_name = o_sec.get("name", "Outro")
            o_bars = int(o_sec.get("bars", 8))
            o_beats = float(o_bars * beats_per_bar)
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
                    if o_notes is not None and len(o_notes) == 0:
                        continue
                    if not o_notes:
                        silenced_synths_in_outro.append(trk.get("name", f"Pista {trk.get('index')}"))

        if silenced_synths_in_outro:
            session._save_state()
            return {
                "status": "PHASE_6_GATEKEEPER_BLOCKED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "PASO 4: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER - SINTETIZADOR EN OUTRO)",
                "action_taken": f"Gatekeeper de Outro activado: el sintetizador no se debe silenciar en el outro ({', '.join(silenced_synths_in_outro)}).",
                "question": (
                    f"⚠️ **Gatekeeper de Outro Activado (Sintetizador no debe silenciarse):**\n\n"
                    f"Las siguientes pistas de sintetizador carecen de notas en la sección Outro: **{', '.join(silenced_synths_in_outro)}**.\n"
                    f"Por favor, provee las notas MIDI para el sintetizador en la sección Outro para continuar al Paso 5 (Esculpido de Síntesis)."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas para el sintetizador en el Outro.",
                "silenced_synth_tracks": silenced_synths_in_outro
            }
        return None

    @staticmethod
    def audit_composition_quality_harness(
        session: Any,
        tracks: List[Dict[str, Any]],
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Non-mutating Composition Quality Harness:
        Audits velocity dynamics, section density contrast, and same-role track differentiation
        without injecting unsolicited procedural notes.
        """
        warnings: List[str] = []
        track_metrics: Dict[str, Any] = {}
        role_fingerprints: Dict[str, List[Tuple[str, Any]]] = {}

        for trk in tracks:
            t_label = trk.get("original_name") or trk.get("name", f"Track {trk.get('index')}")
            role = str(trk.get("role", "OTHER")).upper()
            summary = trk.get("composed_notes_summary", {})
            sec_notes = trk.get("section_notes", {})
            if not summary:
                continue

            track_metrics[t_label] = summary
            vel_span = summary.get("max_velocity", 100) - summary.get("min_velocity", 100)
            if summary.get("notes_count", 0) >= 8 and vel_span == 0:
                warnings.append(f"Velocity plana detectada en '{t_label}' (todas las notas a {summary.get('max_velocity')}).")

            # Check same-role track collisions
            fp = (
                summary.get("notes_count"),
                summary.get("min_pitch"),
                summary.get("max_pitch"),
                summary.get("avg_duration")
            )
            for prev_name, prev_fp in role_fingerprints.get(role, []):
                if prev_fp == fp and summary.get("notes_count", 0) > 0:
                    warnings.append(
                        f"Posible colisión de notas en rol {role}: '{t_label}' y '{prev_name}' comparten idéntico perfil de notas {fp}."
                    )
            role_fingerprints.setdefault(role, []).append((t_label, fp))

            # Check section contrast
            if len(sec_notes) >= 3:
                counts = [len(v) for v in sec_notes.values() if len(v) > 0]
                if len(counts) >= 3 and len(set(counts)) == 1:
                    warnings.append(f"Densidad estática en '{t_label}': todas las secciones activas tienen exactamente {counts[0]} notas.")

        report = {
            "status": "PASSED" if not warnings else "PASSED_WITH_ADVISORIES",
            "warnings": warnings,
            "track_metrics": track_metrics
        }
        session.data["composition_harness_audit"] = report
        return report

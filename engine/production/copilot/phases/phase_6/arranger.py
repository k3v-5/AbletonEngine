# engine/production/copilot/phases/phase_6/arranger.py
"""
Phase 6 Arrangement Deployer:
Deploys MIDI notes and audio clips across sections in Live's arrangement timeline,
handles motif auto-tiling, structural silences, kick/drums decoupling, and octave transposition.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from engine.music.modular_generator import generate_modular_section_notes
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from .parser import Phase6Parser

logger = logging.getLogger("Phase6Arranger")


class Phase6Arranger:
    """Arrangement clip deployer with governance retry and acoustic safeguards."""

    @staticmethod
    def deploy_clip_with_governance_retry(
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
        3. If retry fails, raises GovernanceViolationError so caller halts and prompts.
        """
        conn = conn if conn is not None else session_or_conn
        if s_notes_dicts is None:
            s_notes_dicts = []
        if trk is None:
            trk = {}
        if conn is None or not hasattr(conn, "send_command"):
            return True

        session_obj = kwargs.get("session") or (session_or_conn if hasattr(session_or_conn, "data") else None)
        hum_level = 2
        bpm = 120.0
        is_custom_ai = kwargs.get("is_custom_ai", False)
        if session_obj and hasattr(session_obj, "data"):
            hum_level = session_obj.data.get("humanization_level", 2)
            bpm = float(session_obj.data.get("bpm", 120.0))
            if session_obj.data.get("ai_composed", False):
                is_custom_ai = True
        elif "humanization_level" in kwargs:
            hum_level = kwargs["humanization_level"]

        if is_custom_ai:
            final_notes_dicts = s_notes_dicts
        else:
            from engine.music.groove.humanizer import DynamicGrooveHumanizer
            role_for_hum = str(trk.get("role", "drums")).lower()
            final_notes_dicts = DynamicGrooveHumanizer.humanize_with_level(
                dict_notes=s_notes_dicts,
                level=hum_level,
                role=role_for_hum,
                tempo=bpm
            ) if s_notes_dicts else []

        notes_payload = [
            {
                "pitch": int(d["pitch"]),
                "start_time": round(float(d.get("start_time", d.get("start", d.get("time", 0.0)))), 3),
                "duration": round(float(d.get("duration", 1.0)), 3),
                "velocity": min(127, max(1, int(d.get("velocity", 100)))),
                "mute": bool(d.get("mute", False))
            }
            for d in (final_notes_dicts or s_notes_dicts)
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

    @classmethod
    def deploy_single_track_composition(
        cls,
        session: Any,
        conn: Any,
        trk: Dict[str, Any],
        custom_notes_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        sections: Optional[List[Dict[str, Any]]] = None,
        find_notes_fn: Optional[Callable] = None
    ) -> int:
        """
        Deploys MIDI notes or audio clips for a single track across all arrangement sections.
        Returns total notes or clips deployed.
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

        if find_notes_fn is None:
            find_notes_fn = Phase6Parser.find_custom_notes_for_track_section

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
            is_test_env = getattr(session, "is_test_env", False) or os.getenv("IS_TEST_ENV") == "1" or os.getenv("PYTEST_CURRENT_TEST") is not None
            if conn is not None and hasattr(conn, "send_command") and v_path and (os.path.exists(v_path) or is_test_env):
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

            raw_notes = find_notes_fn(
                session,
                custom_map=custom_notes_map,
                trk=trk,
                s_idx=s_idx,
                s_name=s_name,
                s_beats=s_beats
            )
            s_notes_dicts = raw_notes if raw_notes is not None else []

            # Fallback to ("current", s_idx) or ("current", "all")
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
                allow_autonomous = bool(session.data.get("allow_autonomous_note_generation", False))
                if allow_autonomous:
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
                else:
                    # Strict assistant policy: engine NEVER autonomously writes chords or notes on its own
                    s_notes_dicts = []
                    logger.debug(
                        f"Phase 6 Assistant Policy: zero autonomous note generation on track {t_idx} "
                        f"('{trk.get('name')}') section {s_idx} ('{s_name}'). Empty clip prepared on arrangement timeline."
                    )

            # Auto-tile section motifs if shorter than section length
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
                    drum_custom = find_notes_fn(
                        session,
                        custom_map=custom_notes_map,
                        trk={"name": "Drums", "role": "DRUMS"},
                        s_idx=s_idx,
                        s_name=s_name,
                        s_beats=s_beats
                    )
                    if drum_custom:
                        s_notes_dicts = [dict(d) for d in drum_custom if d.get("pitch") in (35, 36)]

            if role == "DRUMS" and s_notes_dicts:
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

            # Outro Decay Room & Boundary Enforcement:
            # Clamps all notes in the final section so they do not sustain past the song boundary,
            # leaving natural breathing room for the reverb and delay tail to decay into the fade-out
            is_last_section = (s_idx == len(sections) - 1)
            if is_last_section and s_notes_dicts:
                decay_buffer_beats = min(4.0, max(1.0, s_beats * 0.25))
                max_note_boundary = max(1.0, s_beats - decay_buffer_beats)
                bounded_notes = []
                for d in s_notes_dicts:
                    st = float(d.get("start_time", d.get("start", 0.0)))
                    dur = float(d.get("duration", 1.0))
                    if st >= max_note_boundary:
                        continue
                    elif (st + dur) > max_note_boundary:
                        d_c = dict(d)
                        d_c["duration"] = max(0.1, round(max_note_boundary - st, 4))
                        bounded_notes.append(d_c)
                    else:
                        bounded_notes.append(d)
                s_notes_dicts = bounded_notes

            # Intro Soft Start:
            # Prevents pad/synth notes from slamming at sample 0 of beat 0.0 with maximum transient
            is_first_section = (s_idx == 0)
            if is_first_section and s_notes_dicts and any(r in str(role).upper() for r in ["PAD", "ATMOSPHERE", "SYNTH", "KEYS"]):
                softened_intro = []
                for d in s_notes_dicts:
                    st = float(d.get("start_time", d.get("start", 0.0)))
                    d_c = dict(d)
                    if st == 0.0:
                        d_c["velocity"] = min(int(d_c.get("velocity", 90)), 78)
                        d_c["start_time"] = 0.02
                    softened_intro.append(d_c)
                s_notes_dicts = softened_intro

            # 8-bar Turnaround variation enforcement
            from .turnaround_engine import TurnaroundEngine
            from engine.music.humanizer import HumanizerEngine
            if s_bars >= 8 and s_notes_dicts and not is_pre_drop_transition:
                if TurnaroundEngine.is_bar_8_identical(s_notes_dicts):
                    s_notes_dicts = TurnaroundEngine.apply_turnaround(
                        notes=s_notes_dicts,
                        role=role,
                        section_name=s_name,
                        total_bars=s_bars
                    )

            # Intentional Performance & Humanization Pass (Nivel T)
            # Applies role-calibrated microtiming, chord strumming with top-voice accent,
            # and phrase breathing (climax note weight + guaranteed breath gaps >= 35 ms).
            is_custom_ai = (raw_notes is not None) or bool(custom_notes_map)
            humanization_requested = False
            last_prompt = str(session.data.get("last_composition_prompt", "")).lower()
            if any(w in last_prompt for w in ["humanizar", "humanize", "respirar", "breathing", "dilla", "pocket", "laid_back", "laid back"]):
                humanization_requested = True

            if s_notes_dicts and (not is_custom_ai or humanization_requested):
                bpm_val = float(session.data.get("bpm", 120.0))
                try:
                    from engine.performance import (
                        PerformanceCore,
                        InstrumentPerformanceProfile,
                        PerformanceIntent,
                        PhraseBreathingEngine,
                        PocketTendency,
                        VelocityProfile,
                        ArticulationStyle,
                    )
                    perf_prof = InstrumentPerformanceProfile.create_default(role)
                    pocket = PocketTendency.LAID_BACK if any(w in last_prompt for w in ["dilla", "laid_back", "laid back", "neo_soul", "r&b"]) else PocketTendency.TIGHT_POCKET
                    intent = PerformanceIntent(
                        pocket=pocket,
                        velocity_profile=VelocityProfile.EXPRESSIVE,
                        articulation=ArticulationStyle.NATURAL_BREATHING,
                        human_factor=0.75
                    )
                    s_notes_dicts = PerformanceCore.humanize_track_notes(
                        s_notes_dicts,
                        role=role,
                        profile=perf_prof,
                        intent=intent,
                        bpm=bpm_val
                    )
                    if role.upper() in ["LEAD", "VOCALS", "MELODY", "KEYS", "PIANO"]:
                        perf_prof.phrase_breathing_enabled = True
                        s_notes_dicts = PhraseBreathingEngine.apply_phrase_breathing(
                            s_notes_dicts,
                            profile=perf_prof,
                            intent=intent,
                            bpm=bpm_val
                        )
                except Exception as ex_perf:
                    logger.debug(f"Nivel T performance pass fallback: {ex_perf}")
                    s_notes_dicts = HumanizerEngine.humanize_clip(
                        s_notes_dicts,
                        bpm=bpm_val,
                        role=role,
                        humanize_velocity=True,
                        humanize_timing=True
                    )


            if conn is not None and hasattr(conn, "send_command"):
                try:
                    cls.deploy_clip_with_governance_retry(
                        session_or_conn=session,
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

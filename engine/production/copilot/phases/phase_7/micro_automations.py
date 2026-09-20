"""
Micro-Automations Pass (Phase 7):
Injects subtle, humanized micro-automations that elevate arrangement production:
1. Delay Throws: 100% send wet on the final note of a vocal/lead phrase before a section transition.
2. Dynamic Auto-Pan: Stereo motion sweeps across transitions and builds.
3. 808 Pitch Bends: Glides and pitch slides at the end of drop turnaround bars.
"""

import logging
from typing import List, Dict, Any, Optional
from engine.arrangement.automation.weaver import ArrangementAutomationWeaver

logger = logging.getLogger("MicroAutomations")


class MicroAutomationsPass:
    """
    Coordinates and executes surgical micro-automation passes in Ableton Live arrangement.
    """

    @classmethod
    def inject_delay_throw(
        cls,
        conn: Any,
        track_index: int,
        throw_start_beat: float,
        duration_beats: float = 1.0,
        send_index: int = 0
    ) -> bool:
        """
        Injects a delay throw: spikes Send A or B to 100% for the duration of a final note,
        then snaps back to 0.0 to prevent muddying the next section.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return False

        try:
            # We construct a 3-point automation envelope:
            # (start - 0.05: 0.0) -> (start: 1.0) -> (start + dur: 1.0) -> (start + dur + 0.1: 0.0)
            points = [
                {"time": max(0.0, throw_start_beat - 0.05), "value": 0.0},
                {"time": throw_start_beat, "value": 1.0},
                {"time": throw_start_beat + duration_beats, "value": 1.0},
                {"time": throw_start_beat + duration_beats + 0.1, "value": 0.0}
            ]
            code = f"""
t = song.tracks[{track_index}]
# Automate Send {send_index}
if len(t.mixer_device.sends) > {send_index}:
    send_param = t.mixer_device.sends[{send_index}]
    clip = song.arrangement_clips[0] if len(song.arrangement_clips) > 0 else None
"""
            # Use ArrangementAutomationWeaver or socket send_command
            res = conn.send_command("add_automation_points", {
                "track_index": track_index,
                "parameter_name": f"Send {chr(65 + send_index)}",
                "points": points
            })
            return True
        except Exception as e:
            logger.debug(f"Delay throw injection notice: {e}")
            return False

    @classmethod
    def inject_dynamic_auto_pan(
        cls,
        conn: Any,
        track_index: int,
        start_beat: float,
        end_beat: float,
        pan_swing: float = 0.35
    ) -> bool:
        """
        Automates subtle stereo panning motion during builds or transitions.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return False

        try:
            points = [
                {"time": start_beat, "value": 0.0},
                {"time": start_beat + (end_beat - start_beat) * 0.25, "value": -pan_swing},
                {"time": start_beat + (end_beat - start_beat) * 0.75, "value": pan_swing},
                {"time": end_beat, "value": 0.0}
            ]
            conn.send_command("add_automation_points", {
                "track_index": track_index,
                "parameter_name": "Panning",
                "points": points
            })
            return True
        except Exception as e:
            logger.debug(f"Dynamic auto-pan injection notice: {e}")
            return False

    @classmethod
    def inject_808_pitch_bend(
        cls,
        conn: Any,
        track_index: int,
        bend_start_beat: float,
        semitones: int = 2
    ) -> bool:
        """
        Injects a pitch bend / slide on an 808 bass line before a turnaround downbeat.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return False

        try:
            # Pitch bend: 0.0 is center, +1.0 is max pitch bend
            bend_val = min(1.0, semitones / 12.0)
            points = [
                {"time": bend_start_beat, "value": 0.0},
                {"time": bend_start_beat + 0.75, "value": bend_val},
                {"time": bend_start_beat + 1.0, "value": 0.0}
            ]
            conn.send_command("add_automation_points", {
                "track_index": track_index,
                "parameter_name": "Pitch Bend",
                "points": points
            })
            return True
        except Exception as e:
            logger.debug(f"808 pitch bend injection notice: {e}")
            return False

    @classmethod
    def execute_micro_automation_pass(
        cls,
        session: Any,
        conn: Any
    ) -> Dict[str, Any]:
        """
        Automatically analyzes the session tracks and sections and applies
        appropriate micro-automations (delay throws, dynamic auto-pan, 808 bends).
        """
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        applied_events = []

        cur_beat = 0.0
        for s_idx, sec in enumerate(sections):
            s_bars = int(sec.get("bars", 8))
            s_beats = float(s_bars * 4.0)
            s_name = str(sec.get("name", "")).lower()

            # 1. Delay Throw on Lead/Vocal before Drops and Breaks
            is_transition_sec = any(w in s_name for w in ["verse", "build", "puente", "break"])
            if is_transition_sec and (s_idx + 1 < len(sections)):
                throw_time = cur_beat + s_beats - 1.0
                for trk in tracks:
                    r = str(trk.get("role", "")).upper()
                    if r in ("LEAD", "VOCALS", "COUNTER_LEAD"):
                        t_idx = session._resolve_live_track_index(conn, trk)
                        cls.inject_delay_throw(conn, t_idx, throw_time, duration_beats=1.0)
                        applied_events.append({
                            "type": "delay_throw",
                            "track": trk.get("name"),
                            "time_beat": throw_time
                        })

            # 2. Dynamic Auto-Pan in Buildup sections
            if "build" in s_name:
                for trk in tracks:
                    r = str(trk.get("role", "")).upper()
                    if r in ("PAD", "KEYS", "COUNTER_LEAD", "EAR_CANDY"):
                        t_idx = session._resolve_live_track_index(conn, trk)
                        cls.inject_dynamic_auto_pan(conn, t_idx, cur_beat, cur_beat + s_beats)
                        applied_events.append({
                            "type": "dynamic_auto_pan",
                            "track": trk.get("name"),
                            "start_beat": cur_beat,
                            "end_beat": cur_beat + s_beats
                        })

            # 3. 808 Pitch Bend on Bar 8 of Drops
            if "drop" in s_name and s_bars >= 8:
                bend_time = cur_beat + (7 * 4.0) + 3.0  # Beat 4 of Bar 8
                for trk in tracks:
                    r = str(trk.get("role", "")).upper()
                    if r in ("BASS", "SUB") or "808" in str(trk.get("name", "")).lower():
                        t_idx = session._resolve_live_track_index(conn, trk)
                        cls.inject_808_pitch_bend(conn, t_idx, bend_time, semitones=2)
                        applied_events.append({
                            "type": "808_pitch_bend",
                            "track": trk.get("name"),
                            "time_beat": bend_time
                        })

            cur_beat += s_beats

        return {
            "status": "MICRO_AUTOMATION_PASS_COMPLETED",
            "applied_count": len(applied_events),
            "events": applied_events
        }

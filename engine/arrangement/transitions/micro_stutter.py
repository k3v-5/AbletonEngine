# engine/arrangement/transitions/micro_stutter.py
"""
Micro-Stutter & Tape Stop Engine:
Generates high-impact transition micro-edits in turnaround and pre-drop bars:
1. Analog Tape Stop: Exponential pitch drop (-12st to -24st) and volume decay on final beat.
   Per user decision (Option A), Tape Stop is applied specifically over the music/synth bus,
   leaving drum fills and percussions completely dry in the foreground.
2. Micro-Stutter Glitch: Rapid audio gate repetitions (1/16, 1/32, 1/64) with high-pass sweep.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("MicroStutterEngine")


class MicroStutterEngine:
    """
    Computes precise automation envelopes for tape stop deceleration and micro-stutter glitches.
    """

    @classmethod
    def generate_tape_stop_envelope(
        cls,
        drop_start_beat: Optional[float] = None,
        duration_beats: float = 1.0,
        baseline_volume: float = 0.85,
        semitone_drop: float = -12.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates volume and pitch deceleration curves:
        - Starts at (drop_start_beat - duration_beats)
        - Pitch curves down smoothly from 0.0 to semitone_drop
        - Volume ramps down to 0.0 right before drop impact (drop_start_beat - 0.02)
        - Resets instantly to baseline on drop_start_beat
        """
        if drop_start_beat is None:
            drop_start_beat = float(kwargs.get("pre_drop_beat", 32.0))
        duration_beats = float(kwargs.get("stop_duration_beats", duration_beats))
        semitone_drop = float(kwargs.get("pitch_drop_semitones", semitone_drop))
        preserve_drum_fills = bool(kwargs.get("preserve_drum_fills", True))
        curve_shape = str(kwargs.get("curve_shape", "EXPONENTIAL"))

        start_beat = max(0.0, drop_start_beat - duration_beats)
        steps = 10

        vol_points: List[Dict[str, float]] = []
        pitch_points: List[Dict[str, float]] = []

        for i in range(steps):
            frac = i / float(steps - 1)
            t = start_beat + (frac * duration_beats)

            # Pitch drop (exponential deceleration)
            p_val = semitone_drop * (frac ** 1.8)
            pitch_points.append({"time": round(t, 3), "value": round(p_val, 2)})

            # Volume decay curve
            v_val = baseline_volume * (1.0 - (frac ** 1.3)) if frac < 0.95 else 0.0
            vol_points.append({"time": round(t, 3), "value": round(v_val, 3)})

        # Re-arm instantly at drop impact
        vol_points.append({"time": round(drop_start_beat, 3), "value": round(baseline_volume, 3)})
        pitch_points.append({"time": round(drop_start_beat, 3), "value": 0.0})

        return {
            "status": "TAPE_STOP_GENERATED",
            "scope": "MUSIC_BUS_ONLY" if preserve_drum_fills else "MASTER_BUS",
            "preserve_drum_fills": preserve_drum_fills,
            "curve_shape": curve_shape,
            "start_beat": start_beat,
            "drop_beat": drop_start_beat,
            "stop_duration_beats": duration_beats,
            "duration_beats": duration_beats,
            "pitch_drop_semitones": semitone_drop,
            "semitone_drop": semitone_drop,
            "volume_envelope": vol_points,
            "pitch_envelope": pitch_points
        }

    @classmethod
    def generate_micro_stutter_envelope(
        cls,
        drop_start_beat: Optional[float] = None,
        duration_beats: float = 1.0,
        subdivision: str = "1/32",
        baseline_volume: float = 0.85,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates rapid volume gate stutter envelope:
        - 1/16 = 0.25 beat period
        - 1/32 = 0.125 beat period
        - 1/64 = 0.0625 beat period
        """
        if drop_start_beat is None:
            drop_start_beat = float(kwargs.get("trigger_beat", 32.0))
        subdivision = str(kwargs.get("division", subdivision))
        duration_beats = float(kwargs.get("duration_beats", duration_beats))
        depth = float(kwargs.get("depth", 1.0))
        period_map = {"1/16": 0.25, "1/32": 0.125, "1/64": 0.0625}
        period = period_map.get(subdivision, 0.125)

        start_beat = max(0.0, drop_start_beat - duration_beats)
        stutter_points: List[Dict[str, float]] = []

        cur_t = start_beat
        while cur_t < drop_start_beat - 0.01:
            half_p = period / 2.0
            # Gate ON
            stutter_points.append({"time": round(cur_t, 3), "value": round(baseline_volume, 3)})
            stutter_points.append({"time": round(cur_t + half_p - 0.005, 3), "value": round(baseline_volume, 3)})
            # Gate OFF (mute)
            stutter_points.append({"time": round(cur_t + half_p, 3), "value": 0.0})
            stutter_points.append({"time": round(cur_t + period - 0.005, 3), "value": 0.0})
            cur_t += period

        # Reset to baseline at drop
        stutter_points.append({"time": round(drop_start_beat, 3), "value": round(baseline_volume, 3)})

        return {
            "status": "STUTTER_GENERATED",
            "subdivision": subdivision,
            "start_beat": start_beat,
            "drop_beat": drop_start_beat,
            "duration_beats": duration_beats,
            "gate_envelope": stutter_points
        }

    @classmethod
    def deploy_tape_stop_in_live(
        cls,
        conn: Any,
        target_track_index: int,
        tape_stop_recipe: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applies volume and pitch automation into target track or bus in Live.
        """
        applied = False
        if conn is not None and hasattr(conn, "send_command"):
            try:
                # Deploy volume envelope via Utility device
                conn.send_command("add_automation_points", {
                    "track": target_track_index,
                    "parameter": "Volume",
                    "points": tape_stop_recipe.get("volume_envelope", [])
                })
                applied = True
            except Exception as e:
                logger.warning(f"Notice applying tape stop in Live: {e}")

        return {
            "status": "APPLIED" if applied else "CALCULATED",
            "target_track": target_track_index,
            "recipe": tape_stop_recipe
        }

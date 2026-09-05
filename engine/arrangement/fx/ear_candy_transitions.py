# engine/arrangement/fx/ear_candy_transitions.py
"""
Ear Candy Transition Engine:
Unifies analog tape stops, reverse vocal swells, and freeze wash FX across transition boundaries.
"""

from typing import List, Dict, Any, Tuple, Optional
from engine.arrangement.fx.ear_candy import EarCandyEngine, EarCandyType


class EarCandyTransitionEngine:
    """Generates micro-transitional FX and automation curves across 96 bars."""

    @classmethod
    def generate_tape_stop_transition(cls, target_bar: int = 33, duration_beats: float = 1.0) -> Dict[str, Any]:
        """
        Generates analog tape slowdown curve preceding target_bar (default bar 33 -> Drop 1).
        Slowdown occurs in the duration_beats right before the drop hits.
        """
        res = EarCandyEngine.generate_tape_stop(
            target_bar=float(target_bar),
            duration_beats=duration_beats,
            curve_exp=2.8
        )
        return {
            "status": "SUCCESS",
            "target_bar": target_bar,
            "duration_beats": duration_beats,
            "pitch_bend_points": res.get("pitch_bend_points", res.get("pitch_bend_envelope", [])),
            "volume_points": res.get("volume_points", res.get("volume_envelope", []))
        }

    @classmethod
    def generate_reverse_vocal_swell(cls, drop_bar: int = 32, duration_beats: float = 2.0) -> Dict[str, Any]:
        """
        Calculates coordinates and parameters for a reverse vocal sweep leading into the drop.
        At drop_bar 32 (beat 128.0), the swell starts at beat 126.0 and crests at 128.0.
        """
        end_beat = float((drop_bar - 1) * 4)
        start_beat = max(0.0, end_beat - duration_beats)
        return {
            "status": "SUCCESS",
            "effect": "reverse_vocal_swell",
            "start_beat": start_beat,
            "end_beat": end_beat,
            "duration_beats": duration_beats,
            "volume_ramp": [(start_beat, 0.05), (start_beat + duration_beats * 0.7, 0.45), (end_beat, 1.0)],
            "high_pass_filter_hz": [(start_beat, 350.0), (end_beat, 120.0)]
        }

    @classmethod
    def generate_reverb_freeze_wash(cls, bar: int = 24, duration_beats: float = 4.0) -> Dict[str, Any]:
        """
        Freezes the reverb decay tail at the end of the verse / pre-chorus boundary.
        """
        start_beat = float((bar - 1) * 4)
        return {
            "status": "SUCCESS",
            "effect": "reverb_freeze_wash",
            "start_beat": start_beat,
            "duration_beats": duration_beats,
            "reverb_decay_time_sec": 12.0,
            "send_a_level": 0.85,
            "dry_wet": [(start_beat, 0.20), (start_beat + duration_beats, 1.0)]
        }

    @classmethod
    def get_full_ear_candy_manifest(cls) -> Dict[str, Any]:
        """Returns the complete micro-production FX transition roadmap."""
        tape_stop_drop1 = cls.generate_tape_stop_transition(target_bar=33, duration_beats=1.0)
        vocal_swell_drop1 = cls.generate_reverse_vocal_swell(drop_bar=33, duration_beats=2.0)
        reverb_wash_v1 = cls.generate_reverb_freeze_wash(bar=24, duration_beats=4.0)
        tape_stop_climax = cls.generate_tape_stop_transition(target_bar=73, duration_beats=1.0)
        vocal_swell_climax = cls.generate_reverse_vocal_swell(drop_bar=73, duration_beats=2.0)

        return {
            "status": "SUCCESS",
            "total_micro_fx": 5,
            "items": [
                {"name": "Tape Stop (Pre-Drop 1)", "data": tape_stop_drop1},
                {"name": "Reverse Vocal Swell (Drop 1)", "data": vocal_swell_drop1},
                {"name": "Reverb Freeze Wash (Pre-Chorus)", "data": reverb_wash_v1},
                {"name": "Tape Stop (Pre-Final Chorus)", "data": tape_stop_climax},
                {"name": "Reverse Vocal Swell (Final Chorus)", "data": vocal_swell_climax},
            ]
        }

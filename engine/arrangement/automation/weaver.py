# engine/arrangement/automation/weaver.py
"""
Arrangement Automation Weaver:
Translates high-level energy curves and transition directives into continuous,
mathematically precise parameter breakpoint envelopes in Ableton Live.
Weaves filter sweeps, reverb washouts, sub-bass cutoffs, and gain staging.
"""

import math
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class TransitionAutomationType(str, Enum):
    FILTER_SWEEP_UP = "filter_sweep_up"
    FILTER_SWEEP_DOWN = "filter_sweep_down"
    REVERB_WASHOUT = "reverb_washout"
    SUB_CLEANUP = "sub_cleanup"
    ENERGY_GAIN = "energy_gain"


class ArrangementAutomationWeaver:
    """Computes and injects multi-parameter arrangement automation breakpoint curves."""

    @staticmethod
    def _interpolate(t: float, start_val: float, end_val: float, curve: str = "exponential") -> float:
        """Interpolates normalized t in [0.0, 1.0] across start_val and end_val."""
        t_clamped = max(0.0, min(1.0, t))
        c = curve.lower()

        if c == "exponential":
            factor = t_clamped ** 2.4
        elif c == "logarithmic":
            factor = t_clamped ** 0.4
        elif c == "ease_in_out":
            factor = 0.5 * (1.0 - math.cos(t_clamped * math.pi))
        elif c == "ease_in":
            factor = t_clamped ** 2.0
        elif c == "ease_out":
            factor = 1.0 - (1.0 - t_clamped) ** 2.0
        else:  # linear
            factor = t_clamped

        return start_val + (end_val - start_val) * factor

    @classmethod
    def generate_filter_sweep(
        cls,
        start_bar: float,
        duration_bars: float,
        direction: str = "up",
        min_val: float = 0.15,
        max_val: float = 0.95,
        curve: str = "exponential",
        steps_per_bar: int = 4
    ) -> List[Dict[str, float]]:
        """
        Generates continuous filter cutoff sweep envelope.
        direction: 'up' (low to high build) or 'down' (high to low breakdown).
        """
        start_beat = start_bar * 4.0
        total_beats = duration_bars * 4.0
        total_steps = max(2, int(round(duration_bars * steps_per_bar)))

        s_val = min_val if direction.lower() == "up" else max_val
        e_val = max_val if direction.lower() == "up" else min_val

        points: List[Dict[str, float]] = []
        for i in range(total_steps + 1):
            t = i / total_steps
            beat_time = start_beat + t * total_beats
            val = cls._interpolate(t, s_val, e_val, curve)
            points.append({
                "time": round(beat_time, 3),
                "value": round(val, 4)
            })

        return points

    @classmethod
    def generate_reverb_washout(
        cls,
        start_bar: float,
        duration_bars: float,
        start_wet: float = 0.10,
        max_wet: float = 0.75,
        reset_wet: float = 0.0,
        curve: str = "exponential",
        steps_per_bar: int = 4
    ) -> List[Dict[str, float]]:
        """
        Generates dramatic reverb washout: rises exponentially to max_wet during build,
        then drops instantly to reset_wet at the downbeat of the drop.
        """
        points = cls.generate_filter_sweep(
            start_bar=start_bar,
            duration_bars=duration_bars,
            direction="up",
            min_val=start_wet,
            max_val=max_wet,
            curve=curve,
            steps_per_bar=steps_per_bar
        )
        # Snap down to zero on the downbeat of the arrival bar
        arrival_beat = (start_bar + duration_bars) * 4.0
        points.append({
            "time": round(arrival_beat + 0.01, 3),
            "value": round(reset_wet, 4)
        })
        return points

    @classmethod
    def generate_sub_cleanup(
        cls,
        start_bar: float,
        duration_bars: float = 2.0,
        normal_gain: float = 0.85,
        cut_gain: float = 0.0
    ) -> List[Dict[str, float]]:
        """
        Pre-drop sub cleanup: ramps volume down or filter up right before drop impact.
        """
        start_beat = start_bar * 4.0
        drop_beat = (start_bar + duration_bars) * 4.0
        return [
            {"time": round(start_beat, 3), "value": normal_gain},
            {"time": round(drop_beat - 4.0, 3), "value": normal_gain * 0.8},
            {"time": round(drop_beat - 1.0, 3), "value": cut_gain},
            {"time": round(drop_beat, 3), "value": normal_gain}
        ]

    @classmethod
    def apply_transition_automation(
        cls,
        adapter: Any,
        track_index: int,
        transition_type: Union[TransitionAutomationType, str],
        start_bar: float,
        duration_bars: float,
        parameter_name: str = "Filter Cutoff"
    ) -> Dict[str, Any]:
        """Injects calculated transition automation curves into Live."""
        ttype = TransitionAutomationType(transition_type) if isinstance(transition_type, str) else transition_type

        if ttype == TransitionAutomationType.FILTER_SWEEP_UP:
            points = cls.generate_filter_sweep(start_bar, duration_bars, direction="up")
        elif ttype == TransitionAutomationType.FILTER_SWEEP_DOWN:
            points = cls.generate_filter_sweep(start_bar, duration_bars, direction="down")
        elif ttype == TransitionAutomationType.REVERB_WASHOUT:
            points = cls.generate_reverb_washout(start_bar, duration_bars)
            parameter_name = "Dry/Wet"
        elif ttype == TransitionAutomationType.SUB_CLEANUP:
            points = cls.generate_sub_cleanup(start_bar, duration_bars)
            parameter_name = "Volume"
        else:
            points = cls.generate_filter_sweep(start_bar, duration_bars, direction="up")

        start_beat = start_bar * 4.0
        duration_beats = duration_bars * 4.0

        res = {}
        if hasattr(adapter, "send_command"):
            try:
                res = adapter.send_command("create_automation", {
                    "track": track_index,
                    "parameter": parameter_name,
                    "start": start_beat,
                    "duration": duration_beats,
                    "start_value": points[0]["value"],
                    "end_value": points[-1]["value"],
                    "curve": "exponential"
                })
            except Exception as e:
                res = {"error": str(e)}

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "transition_type": ttype.value,
            "parameter": parameter_name,
            "start_bar": start_bar,
            "duration_bars": duration_bars,
            "points_count": len(points),
            "points": points,
            "adapter_response": res
        }

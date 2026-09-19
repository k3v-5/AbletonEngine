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
    def _cubic_bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
        """Cubic Bézier formula: B(t) = (1-t)^3*p0 + 3(1-t)^2*t*p1 + 3(1-t)*t^2*p2 + t^3*p3."""
        u = 1.0 - t
        return (u ** 3) * p0 + 3 * (u ** 2) * t * p1 + 3 * u * (t ** 2) * p2 + (t ** 3) * p3

    @classmethod
    def _interpolate(cls, t: float, start_val: float, end_val: float, curve: str = "exponential") -> float:
        """Interpolates normalized t in [0.0, 1.0] across start_val and end_val."""
        t_clamped = max(0.0, min(1.0, t))
        c = curve.lower()

        if c == "exponential":
            factor = t_clamped ** 2.4
        elif c == "bezier":
            factor = cls._cubic_bezier(t_clamped, 0.0, 0.15, 0.85, 1.0)
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
    def generate_bezier_curve(
        cls,
        start_beat: float,
        duration_beats: float,
        start_val: float,
        end_val: float,
        control_y1: float = 0.15,
        control_y2: float = 0.85,
        num_micro_points: int = 32
    ) -> List[Dict[str, float]]:
        """
        Punto 21: Visible Multi-Point Bézier Curve in Live 12.
        Renders 16 to 32 micro-points along a cubic Bézier curve so that the
        envelope displays visually contoured and editable in Live 12's arrangement view.
        """
        points: List[Dict[str, float]] = []
        n_points = max(16, min(64, num_micro_points))
        p0 = start_val
        p3 = end_val
        p1 = start_val + (end_val - start_val) * control_y1
        p2 = start_val + (end_val - start_val) * control_y2

        for i in range(n_points + 1):
            t = i / float(n_points)
            beat_time = start_beat + t * duration_beats
            val = cls._cubic_bezier(t, p0, p1, p2, p3)
            points.append({
                "time": round(beat_time, 3),
                "value": round(max(0.0, min(1.0, val)), 4)
            })
        return points


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
    def generate_pre_drop_vacuum(
        cls,
        start_bar: float,
        duration_bars: float = 1.0,
        normal_gain: float = 0.85,
        vacuum_beats: float = 2.0
    ) -> List[Dict[str, float]]:
        """
        Creates an aggressive pre-drop silence vacuum:
        Maintains normal gain until the last beat(s) of the transition bar, then drops
        instantly to 0.0 gain, recovering to 0.85 at the exact downbeat of the drop.
        """
        start_beat = start_bar * 4.0
        arrival_beat = (start_bar + duration_bars) * 4.0
        cut_beat = max(start_beat, arrival_beat - vacuum_beats)

        return [
            {"time": round(start_beat, 3), "value": normal_gain},
            {"time": round(cut_beat - 0.05, 3), "value": normal_gain},
            {"time": round(cut_beat, 3), "value": 0.0},
            {"time": round(arrival_beat - 0.01, 3), "value": 0.0},
            {"time": round(arrival_beat, 3), "value": normal_gain}
        ]

    @classmethod
    def generate_pumping_sidechain(
        cls,
        start_bar: float,
        duration_bars: float = 4.0,
        duck_depth: float = 0.15,
        normal_gain: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Generates continuous 4-on-the-floor EDM volume pumping (pseudo-sidechain ducking).
        """
        points: List[Dict[str, float]] = []
        total_bars = int(round(duration_bars))
        for b in range(total_bars):
            bar_start = (start_bar + b) * 4.0
            for beat in range(4):
                t_beat = bar_start + beat
                # Duck on the beat, recover by the offbeat
                points.append({"time": round(t_beat, 3), "value": round(duck_depth, 3)})
                points.append({"time": round(t_beat + 0.25, 3), "value": round(normal_gain * 0.7, 3)})
                points.append({"time": round(t_beat + 0.5, 3), "value": round(normal_gain, 3)})
        return points

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
        ttype_str = transition_type.value if hasattr(transition_type, "value") else str(transition_type).lower()

        if "sweep_up" in ttype_str or "filter_up" in ttype_str:
            points = cls.generate_filter_sweep(start_bar, duration_bars, direction="up")
        elif "sweep_down" in ttype_str or "filter_down" in ttype_str:
            points = cls.generate_filter_sweep(start_bar, duration_bars, direction="down")
        elif "washout" in ttype_str or "reverb" in ttype_str:
            points = cls.generate_reverb_washout(start_bar, duration_bars)
            parameter_name = "Dry/Wet"
        elif "vacuum" in ttype_str or "pre_drop" in ttype_str:
            points = cls.generate_pre_drop_vacuum(start_bar, duration_bars)
            parameter_name = "Volume"
        elif "pump" in ttype_str or "sidechain" in ttype_str:
            points = cls.generate_pumping_sidechain(start_bar, duration_bars)
            parameter_name = "Volume"
        elif "sub" in ttype_str or "cleanup" in ttype_str:
            points = cls.generate_sub_cleanup(start_bar, duration_bars)
            parameter_name = "Volume"
        else:
            points = cls.generate_filter_sweep(start_bar, duration_bars, direction="up")

        start_beat = start_bar * 4.0
        duration_beats = duration_bars * 4.0

        res = {}
        if hasattr(adapter, "send_command"):
            try:
                # Direct arrangement envelope injection
                res = adapter.send_command("record_arrangement_automation", {
                    "track_index": track_index,
                    "parameter_name": parameter_name,
                    "points": points
                })
            except Exception:
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
            "transition_type": ttype_str,
            "parameter": parameter_name,
            "start_bar": start_bar,
            "duration_bars": duration_bars,
            "points_count": len(points),
            "points": points,
            "adapter_response": res
        }

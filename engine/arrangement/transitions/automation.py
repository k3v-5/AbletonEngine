# engine/arrangement/transitions/automation.py
"""
Transition & Energy Automation Engine:
Generates continuous, mathematically precise automation breakpoint curves for
filter sweeps, reverb washouts, volume swells, sidechain simulation, and arrangement energy.
"""

import math
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum

class AutomationCurveType(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"

class TransitionAutomationEngine:
    """Computes exact automation breakpoint envelopes for musical arrangement transitions."""

    @staticmethod
    def _interpolate(t: float, start_val: float, end_val: float, curve: str) -> float:
        """Interpolate normalized t in [0.0, 1.0] to [start_val, end_val] according to curve."""
        t_clamped = max(0.0, min(1.0, t))
        c = curve.lower()

        if c == "linear":
            factor = t_clamped
        elif c == "exponential":
            factor = t_clamped ** 2.5
        elif c == "logarithmic":
            factor = t_clamped ** 0.4
        elif c == "ease_in":
            factor = t_clamped ** 2.0
        elif c == "ease_out":
            factor = 1.0 - (1.0 - t_clamped) ** 2.0
        elif c == "ease_in_out":
            factor = 0.5 * (1.0 - math.cos(t_clamped * math.pi))
        else:
            factor = t_clamped

        return start_val + (end_val - start_val) * factor

    @classmethod
    def generate_filter_sweep(
        cls,
        start_bar: float,
        duration_bars: float,
        direction: str = "up",
        min_freq: float = 200.0,
        max_freq: float = 20000.0,
        curve: str = "exponential",
        resolution_beats: float = 0.25
    ) -> List[Dict[str, float]]:
        """
        Generate filter frequency sweep envelope.
        direction: 'up' (low to high, tension build) or 'down' (high to low, breakdown/outro).
        Frequency scaling follows logarithmic perception of pitch/cutoff.
        """
        start_beat = start_bar * 4.0
        total_beats = duration_bars * 4.0
        steps = max(2, int(round(total_beats / resolution_beats)))

        start_f = min_freq if direction.lower() == "up" else max_freq
        end_f = max_freq if direction.lower() == "up" else min_freq

        # Convert to log2 space for musical frequency perception
        log_start = math.log2(max(20.0, start_f))
        log_end = math.log2(max(20.0, end_f))

        points: List[Dict[str, float]] = []
        for i in range(steps + 1):
            t = i / steps
            beat_time = start_beat + t * total_beats
            log_val = cls._interpolate(t, log_start, log_end, curve)
            freq_val = 2.0 ** log_val
            points.append({
                "time": round(beat_time, 3),
                "value": round(freq_val, 2)
            })

        return points

    @classmethod
    def generate_reverb_washout(
        cls,
        start_bar: float,
        duration_bars: float,
        start_wet: float = 0.15,
        max_wet: float = 0.85,
        reset_wet: float = 0.0,
        curve: str = "exponential",
        resolution_beats: float = 0.25
    ) -> List[Dict[str, float]]:
        """
        Generate classic washout reverb automation:
        Dry/Wet rises from start_wet up to max_wet during the transition,
        and instantly snaps back to reset_wet at the downbeat of the new section.
        """
        start_beat = start_bar * 4.0
        total_beats = duration_bars * 4.0
        steps = max(2, int(round(total_beats / resolution_beats)))

        points: List[Dict[str, float]] = []
        for i in range(steps):
            t = i / steps
            beat_time = start_beat + t * total_beats
            val = cls._interpolate(t, start_wet, max_wet, curve)
            points.append({
                "time": round(beat_time, 3),
                "value": round(val, 3)
            })

        # Peak at the final edge before the section boundary
        boundary_beat = start_beat + total_beats
        points.append({
            "time": round(boundary_beat - 0.01, 3),
            "value": round(max_wet, 3)
        })
        # Instant snap reset on downbeat
        points.append({
            "time": round(boundary_beat, 3),
            "value": round(reset_wet, 3)
        })

        return points

    @classmethod
    def generate_volume_swell(
        cls,
        start_bar: float,
        duration_bars: float,
        start_vol: float = 0.2,
        end_vol: float = 0.85,
        pre_drop_silence_beats: float = 0.0,
        curve: str = "linear",
        resolution_beats: float = 0.25
    ) -> List[Dict[str, float]]:
        """
        Generate volume swell / riser automation.
        If pre_drop_silence_beats > 0, mutes to 0.0 during the final beats before the drop.
        """
        start_beat = start_bar * 4.0
        total_beats = duration_bars * 4.0
        swell_beats = total_beats - pre_drop_silence_beats

        if swell_beats <= 0:
            swell_beats = total_beats
            pre_drop_silence_beats = 0.0

        steps = max(2, int(round(swell_beats / resolution_beats)))
        points: List[Dict[str, float]] = []

        for i in range(steps + 1):
            t = i / steps
            beat_time = start_beat + t * swell_beats
            val = cls._interpolate(t, start_vol, end_vol, curve)
            points.append({
                "time": round(beat_time, 3),
                "value": round(val, 3)
            })

        # Pre-drop silence gap
        if pre_drop_silence_beats > 0:
            silence_start = start_beat + swell_beats
            points.append({
                "time": round(silence_start, 3),
                "value": 0.0
            })
            boundary_beat = start_beat + total_beats
            points.append({
                "time": round(boundary_beat - 0.01, 3),
                "value": 0.0
            })
            # Restore to end_vol at drop downbeat
            points.append({
                "time": round(boundary_beat, 3),
                "value": round(end_vol, 3)
            })

        return points

    @classmethod
    def generate_sidechain_pump(
        cls,
        start_bar: float,
        duration_bars: float,
        duck_depth: float = 0.8,
        baseline_vol: float = 0.85,
        rate_beats: float = 1.0,
        curve: str = "ease_in_out"
    ) -> List[Dict[str, float]]:
        """
        Simulate 4-on-the-floor / 8th-note sidechain pumping automation.
        Ducks volume down to (baseline_vol * (1 - duck_depth)) on downbeats and recovers.
        """
        start_beat = start_bar * 4.0
        total_beats = duration_bars * 4.0
        cycles = int(round(total_beats / rate_beats))

        min_vol = baseline_vol * max(0.0, (1.0 - duck_depth))
        points: List[Dict[str, float]] = []

        sub_steps = 4  # 4 breakpoints per pump cycle
        for c in range(cycles):
            cycle_start = start_beat + c * rate_beats
            for s in range(sub_steps):
                t = s / sub_steps
                beat_time = cycle_start + t * rate_beats
                # Duck lowest at start (t=0), recovers smoothly back to baseline
                val = cls._interpolate(t, min_vol, baseline_vol, curve)
                points.append({
                    "time": round(beat_time, 3),
                    "value": round(val, 3)
                })

        # Final anchor
        points.append({
            "time": round(start_beat + total_beats, 3),
            "value": round(baseline_vol, 3)
        })

        return points

    @classmethod
    def generate_energy_curve_automation(
        cls,
        sections: List[Dict[str, Any]],
        target_parameter: str = "volume",
        min_val: float = 0.2,
        max_val: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Generate continuous macro automation envelope mapping arrangement section
        energies to parameter values (e.g. Master volume, Filter cutoff, or Send level).
        """
        if not sections:
            return []

        points: List[Dict[str, float]] = []
        for i, sec in enumerate(sections):
            start_bar = sec.get("start_bar", 0)
            bars = sec.get("bars", 8)
            energy = sec.get("energy", 0.5)

            # Map energy [0.0, 1.0] to [min_val, max_val]
            target_val = min_val + (max_val - min_val) * energy

            start_beat = start_bar * 4.0
            mid_beat = start_beat + (bars * 2.0)
            end_beat = start_beat + (bars * 4.0)

            if i == 0:
                points.append({"time": round(start_beat, 3), "value": round(target_val, 3)})

            points.append({"time": round(mid_beat, 3), "value": round(target_val, 3)})
            points.append({"time": round(end_beat - 0.01, 3), "value": round(target_val, 3)})

        return points

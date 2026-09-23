# engine/arrangement/transitions/tension_dynamics.py
"""
Macro & Micro Tension Dynamics Engine:
Implements high-impact commercial transition contrast techniques:
1. Dead Air (Pre-Drop Micro-Silence): Cuts audio signal and reverb/delay tails on the final
   beat (e.g., beat 3.0 to 4.0 or beat 3.5 to 4.0) before the drop impact.
2. Stereo Width Narrowing: Progressively collapses stereo field from 100% down to 60%
   during the buildup, followed by an instantaneous 100% explosion on drop impact.
3. Pre-Drop Gain Dip: Subtly lowers gain by -1.2 dB over the final 2 bars of tension,
   accentuating the perceptual loudness surge of the chorus/drop.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("TensionDynamicsEngine")


class TensionDynamicsEngine:
    """Computes exact tension contrast automation breakpoints and dead-air schedules."""

    @classmethod
    def generate_dead_air_silence(
        cls,
        drop_start_beat: float,
        silence_duration_beats: float = 1.0,
        baseline_volume: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Generates volume automation breakpoints to produce a razor-sharp dead air silence
        right before the drop impact:
        - Maintains baseline_volume until (drop_start_beat - silence_duration_beats)
        - Drops instantly to 0.0 at (drop_start_beat - silence_duration_beats + 0.01)
        - Holds at 0.0 throughout the dead air gap
        - Snaps back to baseline_volume at drop_start_beat
        """
        silence_start = max(0.0, drop_start_beat - silence_duration_beats)
        return [
            {"time": round(silence_start, 3), "value": round(baseline_volume, 3)},
            {"time": round(silence_start + 0.01, 3), "value": 0.0},
            {"time": round(drop_start_beat - 0.01, 3), "value": 0.0},
            {"time": round(drop_start_beat, 3), "value": round(baseline_volume, 3)}
        ]

    @classmethod
    def generate_stereo_narrowing_buildup(
        cls,
        buildup_start_beat: float,
        drop_start_beat: float,
        min_width: float = 0.60,
        max_width: float = 1.00
    ) -> List[Dict[str, float]]:
        """
        Generates stereo width automation (Utility Width: 0.0 = Mono, 1.0 = 100%, 2.0 = 200%):
        - Starts at 100% (max_width) at buildup_start_beat
        - Progressively collapses linearly/exponentially to 60% (min_width) at the end of the build
        - Explodes back to 100% on drop_start_beat
        """
        duration = max(1.0, drop_start_beat - buildup_start_beat)
        points: List[Dict[str, float]] = []

        sub_steps = 8
        for i in range(sub_steps):
            t = i / float(sub_steps)
            b_time = buildup_start_beat + (t * duration)
            # Quadratic collapse curve
            w_val = max_width - ((max_width - min_width) * (t ** 1.5))
            points.append({"time": round(b_time, 3), "value": round(w_val, 3)})

        # Lowest width right before drop
        points.append({"time": round(drop_start_beat - 0.01, 3), "value": round(min_width, 3)})
        # Instantaneous stereo expansion on drop impact
        points.append({"time": round(drop_start_beat, 3), "value": round(max_width, 3)})

        return points

    @classmethod
    def generate_pre_drop_gain_dip(
        cls,
        drop_start_beat: float,
        dip_duration_beats: float = 8.0,
        dip_amount_db: float = -1.2,
        baseline_gain: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Generates a subtle gain dip (-1.2 dB) over the final 1-2 bars of the buildup,
        recovering to baseline on the drop to amplify the psychoacoustic punch.
        """
        dip_linear = baseline_gain * (10.0 ** (dip_amount_db / 20.0))
        start_time = max(0.0, drop_start_beat - dip_duration_beats)
        mid_time = start_time + (dip_duration_beats * 0.5)

        return [
            {"time": round(start_time, 3), "value": round(baseline_gain, 3)},
            {"time": round(mid_time, 3), "value": round(dip_linear, 3)},
            {"time": round(drop_start_beat - 0.01, 3), "value": round(dip_linear, 3)},
            {"time": round(drop_start_beat, 3), "value": round(baseline_gain, 3)}
        ]

    @classmethod
    def compile_full_drop_tension_package(
        cls,
        buildup_start_beat: float,
        drop_start_beat: float,
        baseline_volume: float = 0.85
    ) -> Dict[str, Any]:
        """Assembles the complete synchronized tension dynamics package for a drop."""
        return {
            "dead_air_curve": cls.generate_dead_air_silence(drop_start_beat, silence_duration_beats=1.0, baseline_volume=baseline_volume),
            "stereo_narrowing_curve": cls.generate_stereo_narrowing_buildup(buildup_start_beat, drop_start_beat),
            "gain_dip_curve": cls.generate_pre_drop_gain_dip(drop_start_beat, dip_duration_beats=8.0, baseline_gain=baseline_volume),
            "description": "Paquete completo de contraste psicoacústico: Dead Air (1 beat), Estrechamiento estéreo (60%) y Dip de ganancia (-1.2 dB)."
        }

    @classmethod
    def calculate_dead_air_window(
        cls,
        drop_start_beat: float,
        duration_beats: float = 1.0,
        baseline_volume: float = 0.85
    ) -> Dict[str, Any]:
        """Calculates dead air pre-drop silence parameters and automation points."""
        silence_start = max(0.0, drop_start_beat - duration_beats)
        points = cls.generate_dead_air_silence(drop_start_beat, silence_duration_beats=duration_beats, baseline_volume=baseline_volume)
        return {
            "silence_start_beat": silence_start,
            "silence_end_beat": drop_start_beat,
            "duration_beats": duration_beats,
            "cut_reverb_decay": True,
            "points": points
        }

    @classmethod
    def calculate_stereo_narrowing_automation(
        cls,
        build_start_beat: float,
        drop_start_beat: float,
        collapsed_width_percent: float = 60.0
    ) -> List[Dict[str, float]]:
        """Calculates stereo narrowing automation curve."""
        min_w = collapsed_width_percent / 100.0
        return cls.generate_stereo_narrowing_buildup(
            buildup_start_beat=build_start_beat,
            drop_start_beat=drop_start_beat,
            min_width=min_w,
            max_width=1.0
        )

    @classmethod
    def calculate_predrop_gain_dip(
        cls,
        drop_start_beat: float,
        dip_duration_beats: float = 8.0,
        dip_db: float = -1.2,
        baseline_gain: float = 0.85
    ) -> List[Dict[str, float]]:
        """Calculates pre-drop gain dip automation curve."""
        pts = cls.generate_pre_drop_gain_dip(
            drop_start_beat=drop_start_beat,
            dip_duration_beats=dip_duration_beats,
            dip_amount_db=dip_db,
            baseline_gain=baseline_gain
        )
        for p in pts:
            val = p.get("value", baseline_gain)
            ratio = max(0.0001, val / baseline_gain)
            p["gain_db"] = round(20.0 * math.log10(ratio), 2)
        return pts

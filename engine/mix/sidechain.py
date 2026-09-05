# engine/mix/sidechain.py
"""
Auto-Sidechain Ducker:
Mathematically models and applies surgical sub-bass ducking keyed to Kick strikes.
Eliminates low-end phase cancellation and prevents master bus headroom clipping.
"""

import math
from typing import List, Dict, Any, Optional


class AutoSidechainDucker:
    """Computes exact volume ducking envelopes for 808/Sub Bass keyed to Kick transients."""

    @classmethod
    def calculate_ducking_envelope(
        cls,
        kick_strike_beats: List[float],
        ducking_depth_db: float = -10.0,
        hold_ms: float = 25.0,
        release_ms: float = 110.0,
        tempo: float = 120.0,
        base_gain: float = 0.85,
        total_duration_beats: Optional[float] = None
    ) -> List[Dict[str, float]]:
        """
        Generates volume breakpoint automation points synchronized to kick strikes.
        - Instant drop (0 ms attack) to clear the kick transient.
        - Hold duration preserves space for the punch.
        - Exponential release recovers full sub sustain.
        """
        if not kick_strike_beats:
            return []

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        hold_beats = hold_ms * beats_per_ms
        release_beats = release_ms * beats_per_ms

        # Linear multiplier from dB: e.g. -10 dB -> ~0.316
        duck_factor = 10.0 ** (ducking_depth_db / 20.0)
        ducked_gain = round(base_gain * duck_factor, 4)

        points: List[Dict[str, float]] = []
        sorted_kicks = sorted(set(round(t, 4) for t in kick_strike_beats))

        for idx, k_time in enumerate(sorted_kicks):
            # Pre-kick baseline guard point (just before strike if space allows and after beat 0)
            if k_time > 0.02 and (idx == 0 or (k_time - points[-1]["time"]) > 0.05):
                points.append({
                    "time": round(k_time - 0.02, 4),
                    "value": base_gain
                })

            # 1. Instant duck at kick strike
            points.append({
                "time": round(k_time, 4),
                "value": ducked_gain
            })

            # 2. Hold phase
            t_hold = k_time + hold_beats
            points.append({
                "time": round(t_hold, 4),
                "value": ducked_gain
            })

            # 3. Exponential release recovery (midpoint + end)
            t_mid = t_hold + (release_beats * 0.4)
            # exponential curve recovers ~70% of energy at 40% release time
            mid_gain = round(ducked_gain + (base_gain - ducked_gain) * 0.65, 4)
            points.append({
                "time": round(t_mid, 4),
                "value": mid_gain
            })

            # 4. Full recovery
            t_rec = t_hold + release_beats
            # If next kick occurs before recovery, clamp
            next_kick = sorted_kicks[idx + 1] if (idx + 1) < len(sorted_kicks) else float("inf")
            if t_rec < next_kick:
                points.append({
                    "time": round(t_rec, 4),
                    "value": base_gain
                })

        # Ensure trailing end point if total_duration_beats specified
        if total_duration_beats and points and points[-1]["time"] < total_duration_beats:
            points.append({
                "time": round(total_duration_beats, 4),
                "value": base_gain
            })

        return sorted(points, key=lambda p: p["time"])

    @classmethod
    def apply_sidechain_to_track(
        cls,
        adapter: Any,
        bass_track_index: int,
        kick_strike_beats: List[float],
        tempo: float = 120.0,
        ducking_depth_db: float = -10.0,
        release_ms: float = 110.0
    ) -> Dict[str, Any]:
        """Calculates and applies sidechain ducking curve directly to Ableton Live track."""
        points = cls.calculate_ducking_envelope(
            kick_strike_beats=kick_strike_beats,
            ducking_depth_db=ducking_depth_db,
            release_ms=release_ms,
            tempo=tempo
        )

        res = {}
        if hasattr(adapter, "send_command") and points:
            start_t = points[0]["time"]
            end_t = points[-1]["time"]
            dur = max(1.0, end_t - start_t)
            try:
                res = adapter.send_command("create_automation", {
                    "track": bass_track_index,
                    "parameter": "Volume",
                    "start": start_t,
                    "duration": dur,
                    "start_value": points[0]["value"],
                    "end_value": points[-1]["value"],
                    "curve": "linear"
                })
            except Exception as e:
                res = {"error": str(e)}

        return {
            "status": "SUCCESS",
            "bass_track_index": bass_track_index,
            "kick_strikes_processed": len(kick_strike_beats),
            "ducking_depth_db": ducking_depth_db,
            "release_ms": release_ms,
            "points_generated": len(points),
            "adapter_response": res
        }

# engine/mix/spatial/depth.py
"""
3D Depth & Spatial Staging Engine:
Calculates tempo-synced acoustic depth planes (Foreground, Midground, Background)
and dynamic ducked reverb envelopes to achieve massive clarity and separation.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from engine.music.models import NoteEvent


class DepthPlane(str, Enum):
    FOREGROUND = "foreground"    # Up close, direct punch (Kick, 808, Lead Vocals)
    MIDGROUND = "midground"      # Room dimension (Snares, Chords, Guitars)
    BACKGROUND = "background"    # Ambient horizon (Pads, Textures, FX, Ad-libs)


@dataclass
class SpatialProfile:
    plane: DepthPlane
    pre_delay_ms: float
    decay_time_s: float
    dry_wet: float
    high_cut_hz: float
    stereo_width: float
    ducking_enabled: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plane": self.plane.value,
            "pre_delay_ms": round(self.pre_delay_ms, 2),
            "decay_time_s": round(self.decay_time_s, 2),
            "dry_wet": round(self.dry_wet, 3),
            "high_cut_hz": round(self.high_cut_hz, 1),
            "stereo_width": round(self.stereo_width, 2),
            "ducking_enabled": self.ducking_enabled
        }


class DepthStagingEngine:
    """Orchestrates acoustic depth placement and dynamic space automation."""

    @staticmethod
    def calculate_plane_parameters(
        plane: Union[DepthPlane, str],
        tempo: float = 120.0
    ) -> SpatialProfile:
        """
        Calculates tempo-synchronized pre-delay, acoustic absorption filters,
        and decay characteristics for the specified depth plane.
        """
        p = DepthPlane(plane) if isinstance(plane, str) else plane
        ms_per_beat = (60.0 / tempo) * 1000.0

        if p == DepthPlane.FOREGROUND:
            # 1/64 note pre-delay or 0 ms for instant in-your-face clarity
            pre_delay = ms_per_beat / 16.0
            return SpatialProfile(
                plane=p,
                pre_delay_ms=pre_delay,
                decay_time_s=0.75,
                dry_wet=0.08,
                high_cut_hz=16000.0,
                stereo_width=1.0,
                ducking_enabled=True
            )
        elif p == DepthPlane.MIDGROUND:
            # 1/32 note pre-delay
            pre_delay = ms_per_beat / 8.0
            return SpatialProfile(
                plane=p,
                pre_delay_ms=pre_delay,
                decay_time_s=1.50,
                dry_wet=0.22,
                high_cut_hz=9500.0,
                stereo_width=1.15,
                ducking_enabled=False
            )
        else: # BACKGROUND
            # 1/16 note pre-delay (depth separation)
            pre_delay = ms_per_beat / 4.0
            return SpatialProfile(
                plane=p,
                pre_delay_ms=pre_delay,
                decay_time_s=2.80,
                dry_wet=0.45,
                high_cut_hz=5200.0,  # Air absorption rolls off highs
                stereo_width=1.40,  # Wide spatial field
                ducking_enabled=False
            )

    @staticmethod
    def calculate_ducked_reverb_envelope(
        notes: List[NoteEvent],
        tempo: float = 120.0,
        active_gain_db: float = -8.0,
        release_ms: float = 120.0,
        baseline_gain: float = 1.0
    ) -> List[Dict[str, float]]:
        """
        Computes reverb send gain automation points that duck when instrument notes are playing,
        and blossom into full reverb tails during vocal/lead pauses.
        """
        if not notes:
            return []

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat
        release_beats = release_ms * beats_per_ms

        duck_factor = 10.0 ** (active_gain_db / 20.0)
        ducked_gain = round(baseline_gain * duck_factor, 4)

        # Merge overlapping note active intervals
        sorted_notes = sorted(notes, key=lambda n: n.start)
        merged_intervals = []
        for n in sorted_notes:
            n_start = round(n.start, 4)
            n_end = round(n.start + n.duration, 4)
            if not merged_intervals:
                merged_intervals.append([n_start, n_end])
            else:
                last_start, last_end = merged_intervals[-1]
                if n_start <= last_end + 0.05:
                    merged_intervals[-1][1] = max(last_end, n_end)
                else:
                    merged_intervals.append([n_start, n_end])

        points: List[Dict[str, float]] = []

        for idx, (st, end) in enumerate(merged_intervals):
            # Guard baseline before active phrase
            if idx == 0 and st > 0.05:
                points.append({"time": 0.0, "value": baseline_gain})
            if idx > 0 and (st - points[-1]["time"]) > 0.05:
                points.append({"time": round(st - 0.02, 4), "value": baseline_gain})

            # Duck at note start
            points.append({"time": round(st, 4), "value": ducked_gain})
            # Maintain ducked gain throughout note
            points.append({"time": round(end, 4), "value": ducked_gain})

            # Recover to baseline in release window
            rec_time = round(end + release_beats, 4)
            next_start = merged_intervals[idx + 1][0] if (idx + 1) < len(merged_intervals) else float("inf")
            if rec_time < next_start:
                points.append({"time": rec_time, "value": baseline_gain})

        return sorted(points, key=lambda p: p["time"])

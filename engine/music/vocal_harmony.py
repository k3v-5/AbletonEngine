# engine/music/vocal_harmony.py
"""
Vocal Harmony & Stereo Spread Engine:
Generates intelligent diatonic and modal harmony stacks (High Harmony 3rd, Low Harmony 3rd/6th, Octave Doubles).
Applies automatic wide stereo distribution (Pan 60L / 60R) and organic micro-timing humanization
to create lush, commercial stadium-sized chorus vocal stacks without comb-filtering.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import random
import logging

logger = logging.getLogger("VocalHarmonyEngine")


class VocalHarmonyEngine:
    """
    Computes vocal harmony layers and stereo distribution maps from lead vocal melody lines.
    """

    @classmethod
    def generate_vocal_harmony_stack(
        cls,
        lead_notes: List[Dict[str, Any]],
        scale_root_pitch: int = 60,
        scale_intervals: Optional[List[int]] = None,
        include_high_harmony: bool = True,
        include_low_harmony: bool = True,
        include_octave_double: bool = False,
        humanize_timing_ms: float = 8.0,
        bpm: float = 120.0
    ) -> Dict[str, Any]:
        """
        Generates full stereo harmony stack:
        - High Harmony (typically +3 or +4 semitones fitting scale) paneada al 60L.
        - Low Harmony (typically -3 or -4 semitones fitting scale) paneada al 60R.
        - Octave Doubles (opcional) ensanchadas.
        """
        if scale_intervals is None:
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals

        # Beat conversion for microtiming humanization
        ms_per_beat = (60.0 / max(40.0, bpm)) * 1000.0
        human_beat_jitter = (humanize_timing_ms / ms_per_beat)

        # Gamut of scale pitches
        scale_set = set()
        for oct_i in range(1, 9):
            for int_val in scale_intervals:
                scale_set.add(oct_i * 12 + int_val)

        high_notes = []
        low_notes = []
        octave_notes = []

        for n in lead_notes:
            p = int(n.get("pitch", 60))
            st = float(n.get("start_time", n.get("start", 0.0)))
            dur = float(n.get("duration", 1.0))
            vel = int(n.get("velocity", 100))

            # 1. High Harmony (Find nearest scale pitch ~3-4 semitones above)
            if include_high_harmony:
                cand_high = p + 4 if (p + 4) in scale_set else (p + 3 if (p + 3) in scale_set else p + 5)
                jitter_h = random.uniform(-human_beat_jitter, human_beat_jitter)
                high_notes.append({
                    "pitch": cand_high,
                    "start_time": round(max(0.0, st + jitter_h), 3),
                    "duration": round(dur, 3),
                    "velocity": max(1, min(127, vel - 8)),
                    "mute": False,
                    "pan": -0.60,
                    "layer": "HIGH_HARMONY"
                })

            # 2. Low Harmony (Find nearest scale pitch ~3-4 semitones below)
            if include_low_harmony:
                cand_low = p - 3 if (p - 3) in scale_set else (p - 4 if (p - 4) in scale_set else p - 5)
                jitter_l = random.uniform(-human_beat_jitter, human_beat_jitter)
                low_notes.append({
                    "pitch": cand_low,
                    "start_time": round(max(0.0, st + jitter_l), 3),
                    "duration": round(dur, 3),
                    "velocity": max(1, min(127, vel - 12)),
                    "mute": False,
                    "pan": 0.60,
                    "layer": "LOW_HARMONY"
                })

            # 3. Octave Double
            if include_octave_double:
                cand_oct = p + 12 if p < 72 else p - 12
                jitter_o = random.uniform(-human_beat_jitter, human_beat_jitter)
                octave_notes.append({
                    "pitch": cand_oct,
                    "start_time": round(max(0.0, st + jitter_o), 3),
                    "duration": round(dur, 3),
                    "velocity": max(1, min(127, vel - 15)),
                    "mute": False,
                    "pan": 0.0,
                    "layer": "OCTAVE_DOUBLE"
                })

        layers = {
            "lead": lead_notes,
            "high_harmony": high_notes,
            "low_harmony": low_notes
        }
        if include_octave_double:
            layers["octave_double"] = octave_notes

        return {
            "status": "HARMONIES_GENERATED",
            "lead_notes_count": len(lead_notes),
            "layers": layers,
            "high_harmony_notes": high_notes,
            "low_harmony_notes": low_notes,
            "stereo_layout": {
                "lead": "Centro (Pan 0.0)",
                "high_harmony": "Hard Left (Pan -0.60)",
                "low_harmony": "Hard Right (Pan +0.60)",
                "octave_double": "Centro / Amplio (Pan 0.0)"
            },
            "total_harmony_notes": len(high_notes) + len(low_notes) + len(octave_notes)
        }

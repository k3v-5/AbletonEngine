# engine/mix/fader_rider.py
"""
Vocal & Lead Fader Riding Automation Engine:
Computes section-aware dynamic fader riding curves across 96 bars,
maintaining constant vocal intelligibility and emotional climax presence without over-compression.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


class VocalLeadFaderRider:
    """Generates continuous fader rides across 96 bars for vocal hooks and lead melodies."""

    SECTION_FADER_MAP = [
        ("Intro", 0, 8, -2.5, "Atmospheric vocal chops tucked behind Rhodes chords."),
        ("Verse 1", 8, 24, -1.2, "Intimate conversational presence sitting inside the groove."),
        ("Pre-Chorus 1", 24, 32, +0.5, "Gradual volume swell building emotional tension."),
        ("Chorus 1", 32, 48, +2.0, "Commanding upfront vocal hook punching through heavy 808."),
        ("Verse 2", 48, 64, -0.8, "Slightly energetic verse momentum."),
        ("Bridge", 64, 72, 0.0, "Isolated spotlight on the melody over Dorian chords."),
        ("Final Chorus", 72, 88, +2.8, "Maximum energy climax fader boost with dual lead layers."),
        ("Outro", 88, 96, -3.0, "Gentle decompression fade into vinyl atmosphere."),
    ]

    BASE_FADER_VAL = 0.85  # Ableton 0 dB nominal level

    @classmethod
    def db_to_fader_val(cls, db_offset: float) -> float:
        """Converts dB fader adjustment into Ableton Live normalized volume fader value."""
        # 0.85 is Ableton 0.0 dB. +6dB is 1.0 (approx)
        gain_mult = 10.0 ** (db_offset / 20.0)
        norm_val = cls.BASE_FADER_VAL * gain_mult
        return round(max(0.0, min(1.0, norm_val)), 4)

    @classmethod
    def generate_fader_automation_envelope(
        cls,
        role: str = "vocal",
        crossfade_beats: float = 2.0
    ) -> List[Dict[str, float]]:
        """
        Generates continuous volume breakpoint automation points across all 96 bars (384 beats).
        Crossfades smoothly across section boundaries to eliminate sudden volume jumps.
        """
        points: List[Dict[str, float]] = []

        for idx, (sec_name, start_bar, end_bar, db_gain, desc) in enumerate(cls.SECTION_FADER_MAP):
            start_beat = start_bar * 4.0
            end_beat = end_bar * 4.0
            target_val = cls.db_to_fader_val(db_gain)

            if idx == 0:
                # Initial point
                points.append({"time": 0.0, "value": target_val})
            else:
                # Smooth ramp into new section
                ramp_start = max(0.0, start_beat - crossfade_beats)
                prev_val = points[-1]["value"]
                points.append({"time": round(ramp_start, 3), "value": prev_val})
                points.append({"time": round(start_beat, 3), "value": target_val})

            # Section steady point before next ramp
            steady_end = max(start_beat, end_beat - crossfade_beats)
            points.append({"time": round(steady_end, 3), "value": target_val})

        # Final end point
        last_val = cls.db_to_fader_val(cls.SECTION_FADER_MAP[-1][3])
        points.append({"time": 384.0, "value": last_val})
        return points

    @classmethod
    def get_fader_riding_manifest(cls) -> Dict[str, Any]:
        """Returns the complete 96-bar fader riding manifest with section descriptions."""
        envelope = cls.generate_fader_automation_envelope(role="vocal")
        sections_summary = [
            {
                "section": sec,
                "bars": f"{s_bar}-{e_bar}",
                "db_offset": db,
                "fader_value": cls.db_to_fader_val(db),
                "rationale": desc
            }
            for sec, s_bar, e_bar, db, desc in cls.SECTION_FADER_MAP
        ]

        return {
            "status": "SUCCESS",
            "phase": "PHASE_6_MIX_SURGICAL",
            "total_sections": len(sections_summary),
            "total_automation_points": len(envelope),
            "sections": sections_summary,
            "automation_envelope": envelope
        }

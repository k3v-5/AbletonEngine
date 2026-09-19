# engine/music/procedural_fills.py
"""
Procedural Drum Fills & Transition Turnaround Engine:
Generates natural drum fills, tom cascades, snare rolls, and pre-drop vacuums
at section boundaries (bars 8, 16, 24) automatically.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("ProceduralFills")


class ProceduralDrumFillEngine:
    """Injects musical turnaround drum fills and pre-drop vacuum cuts."""

    # General MIDI standard drum pad mappings
    KICK = 36
    SNARE = 38
    RIM = 37
    CLAP = 39
    TOM_HI = 50
    TOM_MID = 47
    TOM_LOW = 43
    CRASH = 49

    @classmethod
    def generate_turnaround_fill(
        cls,
        total_bars: float = 16.0,
        fill_bars: float = 1.0,
        fill_style: str = "SNARE_ROLL_AND_TOMS",
        include_pre_drop_vacuum: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Creates a drum fill leading into the downbeat of the arrival bar.
        """
        fill_start_beat = (total_bars - fill_bars) * 4.0
        notes: List[Dict[str, Any]] = []

        if "SNARE_ROLL" in fill_style.upper():
            # Bar starts with 8th notes, speeds up to 16ths on beat 2 and 3
            # Beat 1: two 8ths
            notes.append({"pitch": cls.SNARE, "start_time": round(fill_start_beat + 0.0, 3), "duration": 0.25, "velocity": 85})
            notes.append({"pitch": cls.SNARE, "start_time": round(fill_start_beat + 0.5, 3), "duration": 0.25, "velocity": 90})

            # Beat 2: four 16ths
            for i in range(4):
                notes.append({"pitch": cls.SNARE, "start_time": round(fill_start_beat + 1.0 + (i * 0.25), 3), "duration": 0.2, "velocity": 95 + (i * 4)})

            # Beat 3: tom cascade
            notes.append({"pitch": cls.TOM_HI, "start_time": round(fill_start_beat + 2.0, 3), "duration": 0.2, "velocity": 110})
            notes.append({"pitch": cls.TOM_HI, "start_time": round(fill_start_beat + 2.25, 3), "duration": 0.2, "velocity": 112})
            notes.append({"pitch": cls.TOM_MID, "start_time": round(fill_start_beat + 2.5, 3), "duration": 0.2, "velocity": 115})
            notes.append({"pitch": cls.TOM_LOW, "start_time": round(fill_start_beat + 2.75, 3), "duration": 0.2, "velocity": 120})

            # Beat 4: If pre_drop_vacuum is True, LEAVE EMPTY (silence gives massive drop punch!)
            if not include_pre_drop_vacuum:
                notes.append({"pitch": cls.SNARE, "start_time": round(fill_start_beat + 3.0, 3), "duration": 0.2, "velocity": 125})
                notes.append({"pitch": cls.SNARE, "start_time": round(fill_start_beat + 3.5, 3), "duration": 0.2, "velocity": 127})

        return notes

    @classmethod
    def inject_fills_into_section(
        cls,
        existing_notes: List[Dict[str, Any]],
        section_bars: float,
        next_section_is_drop: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Replaces the final bar of the section pattern with an energetic fill.
        """
        fill_start_beat = (section_bars - 1.0) * 4.0

        # Keep existing notes that occur before the final turnaround bar
        cleaned_notes = [n for n in existing_notes if float(n.get("start_time", 0.0)) < fill_start_beat]

        fill_notes = cls.generate_turnaround_fill(
            total_bars=section_bars,
            fill_bars=1.0,
            fill_style="SNARE_ROLL_AND_TOMS",
            include_pre_drop_vacuum=next_section_is_drop
        )

        return sorted(cleaned_notes + fill_notes, key=lambda x: x["start_time"])

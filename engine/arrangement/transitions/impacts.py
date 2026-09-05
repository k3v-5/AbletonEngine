# engine/arrangement/transitions/impacts.py
"""
Section Impact & Downlifter Engine:
Deploys sub-booms, crashes, and exponential downlifters at section arrivals across 96 bars.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from engine.music.models import NoteEvent
from engine.arrangement.impacts.downlifters import ImpactEngine, ImpactType


@dataclass
class SectionImpactEvent:
    section_name: str
    bar: int
    beat: float
    impact_type: str
    crash_pitch: int = 49  # C#2
    sub_boom_pitch: int = 36  # C1
    velocity: int = 110
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section_name,
            "bar": self.bar,
            "beat": self.beat,
            "type": self.impact_type,
            "velocity": self.velocity,
            "description": self.description,
        }


class SectionImpactEngine:
    """Orchestrates arrival impacts and downlifters at section boundaries across 96 bars."""

    SECTION_IMPACT_MAP = [
        ("Intro", 0, 0.0, "ambient_crash", 49, 36, 85, "Atmospheric entry crash with lush reverb tail."),
        ("Verse 1", 8, 32.0, "sub_boom_soft", 49, 36, 95, "Soft warm 45Hz sub-boom grounding the groove."),
        ("Chorus 1", 32, 128.0, "sub_boom_heavy", 49, 36, 127, "Heavy 40Hz sub-boom + snappy crash anchoring Drop 1."),
        ("Verse 2", 48, 192.0, "downlifter_filtered", 49, 36, 90, "Filtered downlifter sweep transitioning into Verse 2."),
        ("Bridge", 64, 256.0, "sub_drop_dark", 49, 36, 100, "Dark pitch-dropping sub impact for the Dorian beat switch."),
        ("Final Chorus", 72, 288.0, "climax_impact", 49, 36, 127, "Maximum energy climax impact: dual crash + sub-boom."),
        ("Outro", 88, 352.0, "ambient_boom", 49, 36, 75, "Warm resolving decompression boom fading to silence."),
    ]

    @classmethod
    def get_section_impact_manifest(cls) -> Dict[str, Any]:
        """Returns the complete 8-section impact plan with metadata."""
        events = [
            SectionImpactEvent(
                section_name=sec,
                bar=bar,
                beat=beat,
                impact_type=i_type,
                crash_pitch=c_pitch,
                sub_boom_pitch=s_pitch,
                velocity=vel,
                description=desc
            )
            for sec, bar, beat, i_type, c_pitch, s_pitch, vel, desc in cls.SECTION_IMPACT_MAP
        ]
        return {
            "status": "SUCCESS",
            "total_impacts": len(events),
            "events": [e.to_dict() for e in events]
        }

    @classmethod
    def generate_impact_notes(cls) -> List[NoteEvent]:
        """Generates physical MIDI NoteEvents for crashes and sub-booms on the Foley/FX track."""
        notes: List[NoteEvent] = []

        for sec, bar, beat, i_type, c_pitch, s_pitch, vel, _ in cls.SECTION_IMPACT_MAP:
            # Crash hit on note 49
            notes.append(NoteEvent(
                pitch=c_pitch,
                start=beat,
                duration=4.0 if "heavy" in i_type or "climax" in i_type else 2.0,
                velocity=vel,
                accent=("heavy" in i_type or "climax" in i_type)
            ))
            # Sub-boom layer on note 36 for heavy drops and climax
            if "boom" in i_type or "climax" in i_type or "drop" in i_type:
                notes.append(NoteEvent(
                    pitch=s_pitch,
                    start=beat,
                    duration=2.5,
                    velocity=min(127, vel + 5),
                    accent=True
                ))

        return sorted(notes, key=lambda n: n.start)

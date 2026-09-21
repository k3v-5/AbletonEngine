# engine/sound_design/contrast_engine.py
"""
Contrast Engine (Gen 2):
Tracks, designs, and audits acoustic polarities between arrangement sections:
1. CLEAN ↔ DIRTY
2. WIDE ↔ MONO
3. BRIGHT ↔ DARK
4. DRY ↔ WET
5. SHORT ↔ LONG
6. ACOUSTIC ↔ SYNTHETIC
7. STABLE ↔ UNSTABLE
8. FULL ↔ EMPTY

Guarantees that sonic identity is delivered through dynamic timbral narrative,
preventing static, uniform textures from dulling listener perception.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("ContrastEngine")


class ContrastPolarity(str, Enum):
    CLEAN_DIRTY = "CLEAN_DIRTY"              # -1.0 (Pristine) to +1.0 (Heavy Saturation/Distortion)
    WIDE_MONO = "WIDE_MONO"                  # -1.0 (Mono Center) to +1.0 (Wide 140%+)
    BRIGHT_DARK = "BRIGHT_DARK"              # -1.0 (Dark/Filtered) to +1.0 (Crisp/Open Spectrum)
    DRY_WET = "DRY_WET"                      # -1.0 (Bone Dry) to +1.0 (Wash Reverb/Echo)
    SHORT_LONG = "SHORT_LONG"                # -1.0 (Staccato/Gated) to +1.0 (Endless Sustain)
    ACOUSTIC_SYNTH = "ACOUSTIC_SYNTH"        # -1.0 (Organic Wood/Felt) to +1.0 (Resynthesized Digital)
    STABLE_UNSTABLE = "STABLE_UNSTABLE"      # -1.0 (Rock-solid Tuning) to +1.0 (Tape Wow & Flutter Drift)
    FULL_EMPTY = "FULL_EMPTY"                # -1.0 (Arrangement Valley) to +1.0 (Wall of Sound Climax)


@dataclass
class SectionPolarityState:
    """The polar profile of an instrument or section in a single moment."""
    section_name: str
    track_name: str
    clean_dirty: float = 0.0        # -1.0 to +1.0
    wide_mono: float = 0.0          # -1.0 (Mono) to +1.0 (Wide)
    bright_dark: float = 0.0        # -1.0 (Dark) to +1.0 (Bright)
    dry_wet: float = 0.0            # -1.0 (Dry) to +1.0 (Wet)
    acoustic_synth: float = 0.0     # -1.0 (Acoustic) to +1.0 (Synthetic)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "track_name": self.track_name,
            "clean_dirty": round(self.clean_dirty, 2),
            "wide_mono": round(self.wide_mono, 2),
            "bright_dark": round(self.bright_dark, 2),
            "dry_wet": round(self.dry_wet, 2),
            "acoustic_synth": round(self.acoustic_synth, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SectionPolarityState:
        return cls(
            section_name=data.get("section_name", "Section"),
            track_name=data.get("track_name", "Instrument"),
            clean_dirty=float(data.get("clean_dirty", 0.0)),
            wide_mono=float(data.get("wide_mono", 0.0)),
            bright_dark=float(data.get("bright_dark", 0.0)),
            dry_wet=float(data.get("dry_wet", 0.0)),
            acoustic_synth=float(data.get("acoustic_synth", 0.0)),
        )


class ContrastEngine:
    """
    Evaluates dynamic contrast deltas across sections and plans intentional polar shifts.
    """

    MIN_REQUIRED_DELTA = 0.50  # Must change by at least 50% on at least 2 axes across sections

    @classmethod
    def build_rhodes_contrast_arc(cls, track_name: str = "Stage-73 Rhodes") -> List[SectionPolarityState]:
        """
        Creates the classic four-section Neo-Soul contrast arc:
        - Verse 1: Clean, Dry, Centered, Acoustic (-0.8 clean, -0.6 dry, -0.5 narrow, -0.9 acoustic)
        - Hook 1: Saturated, Wide, Bright (+0.4 dirty, +0.2 wet, +0.6 wide, +0.5 bright)
        - Bridge: Dark, Wet, Mono, Unstable (-0.5 dark, +0.8 wet, -0.8 mono, +0.7 unstable)
        - Hook 3: Climax Payoff (+0.6 dirty, +0.5 wet, +0.9 wide, +0.8 bright)
        """
        return [
            SectionPolarityState(
                section_name="Verse 1",
                track_name=track_name,
                clean_dirty=-0.8,
                wide_mono=-0.4,
                bright_dark=-0.2,
                dry_wet=-0.7,
                acoustic_synth=-0.9
            ),
            SectionPolarityState(
                section_name="Hook 1",
                track_name=track_name,
                clean_dirty=+0.4,
                wide_mono=+0.6,
                bright_dark=+0.5,
                dry_wet=+0.2,
                acoustic_synth=-0.4
            ),
            SectionPolarityState(
                section_name="Bridge",
                track_name=track_name,
                clean_dirty=+0.2,
                wide_mono=-0.8,  # Mono collapse!
                bright_dark=-0.7,  # Dark filtered!
                dry_wet=+0.8,    # Washed in reverb!
                acoustic_synth=+0.6  # High resynthesis
            ),
            SectionPolarityState(
                section_name="Hook 3",
                track_name=track_name,
                clean_dirty=+0.6,
                wide_mono=+0.9,  # Maximum width!
                bright_dark=+0.7,
                dry_wet=+0.4,
                acoustic_synth=+0.3
            ),
        ]

    @classmethod
    def audit_contrast_arc(cls, arc: List[SectionPolarityState]) -> Dict[str, Any]:
        """
        Verifies that the instrument undergoes authentic dramatic transformation across sections.
        """
        if len(arc) < 2:
            return {"is_dynamic": True, "verdict": "MINIMAL_SECTIONS", "max_delta": 0.0}

        # Calculate max delta on each polarity axis
        dirty_delta = max(s.clean_dirty for s in arc) - min(s.clean_dirty for s in arc)
        width_delta = max(s.wide_mono for s in arc) - min(s.wide_mono for s in arc)
        brightness_delta = max(s.bright_dark for s in arc) - min(s.bright_dark for s in arc)
        space_delta = max(s.dry_wet for s in arc) - min(s.dry_wet for s in arc)

        max_delta = max(dirty_delta, width_delta, brightness_delta, space_delta)
        is_dynamic = width_delta >= cls.MIN_REQUIRED_DELTA and (dirty_delta >= cls.MIN_REQUIRED_DELTA or space_delta >= cls.MIN_REQUIRED_DELTA)

        return {
            "is_dynamic": is_dynamic,
            "width_delta": round(width_delta, 2),
            "dirty_delta": round(dirty_delta, 2),
            "brightness_delta": round(brightness_delta, 2),
            "space_delta": round(space_delta, 2),
            "max_delta": round(max_delta, 2),
            "verdict": "VIBRANT_DYNAMIC_CONTRAST" if is_dynamic else "FLAT_UNVARIED_TEXTURE",
        }

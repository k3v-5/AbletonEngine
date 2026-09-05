# engine/sound/macros/semantic_morph.py
"""
Semantic Timbre Morph Engine:
Bridges high-level musical descriptors (Brightness, Warmth, Sub Weight, Space, Attack Snap)
to physical device parameters in Ableton Live 12 and generates dynamic section-by-section
automation envelopes across the 96-bar song timeline.
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TimbreMacroState:
    brightness: float = 0.50    # 0.0 (dark/muffled) to 1.0 (open/airy)
    warmth: float = 0.50        # 0.0 (clean digital) to 1.0 (analog saturation)
    sub_weight: float = 0.50    # 0.0 (light/thin) to 1.0 (heavy 808 sub)
    space: float = 0.30         # 0.0 (dry/mono) to 1.0 (lush reverb/delay wash)
    attack_snap: float = 0.50   # 0.0 (soft/slow) to 1.0 (fast punchy transient)

    def to_dict(self) -> Dict[str, float]:
        return {
            "brightness": round(self.brightness, 3),
            "warmth": round(self.warmth, 3),
            "sub_weight": round(self.sub_weight, 3),
            "space": round(self.space, 3),
            "attack_snap": round(self.attack_snap, 3),
        }


@dataclass
class SectionMorphPoint:
    section_name: str
    start_bar: int
    end_bar: int
    start_beat: float
    end_beat: float
    state: TimbreMacroState


class SemanticTimbreMorphEngine:
    """Calculates dynamic timbre states and generates parameter automation across sections."""

    # Default section morph roadmap for 96-bar urban/neo-soul trap production
    DEFAULT_SECTION_ROADMAP = [
        ("Intro", 0, 8, TimbreMacroState(brightness=0.35, warmth=0.80, sub_weight=0.10, space=0.65, attack_snap=0.30)),
        ("Verse 1", 8, 24, TimbreMacroState(brightness=0.55, warmth=0.70, sub_weight=0.75, space=0.40, attack_snap=0.60)),
        ("Pre-Chorus", 24, 32, TimbreMacroState(brightness=0.80, warmth=0.75, sub_weight=0.40, space=0.70, attack_snap=0.70)),
        ("Chorus 1", 32, 48, TimbreMacroState(brightness=0.95, warmth=0.65, sub_weight=0.95, space=0.50, attack_snap=0.90)),
        ("Verse 2", 48, 64, TimbreMacroState(brightness=0.60, warmth=0.75, sub_weight=0.80, space=0.40, attack_snap=0.65)),
        ("Bridge", 64, 72, TimbreMacroState(brightness=0.45, warmth=0.85, sub_weight=0.60, space=0.75, attack_snap=0.40)),
        ("Final Chorus", 72, 88, TimbreMacroState(brightness=1.00, warmth=0.70, sub_weight=1.00, space=0.55, attack_snap=0.95)),
        ("Outro", 88, 96, TimbreMacroState(brightness=0.30, warmth=0.90, sub_weight=0.20, space=0.80, attack_snap=0.20)),
    ]

    @classmethod
    def get_section_morph_plan(cls) -> List[SectionMorphPoint]:
        """Returns the 8-section timbre roadmap with bar and beat coordinates."""
        plan = []
        for name, start_bar, end_bar, state in cls.DEFAULT_SECTION_ROADMAP:
            plan.append(SectionMorphPoint(
                section_name=name,
                start_bar=start_bar,
                end_bar=end_bar,
                start_beat=float(start_bar * 4),
                end_beat=float(end_bar * 4),
                state=state,
            ))
        return plan

    @classmethod
    def frequency_to_normalized(cls, freq: float, min_f: float = 20.0, max_f: float = 20000.0) -> float:
        """Logarithmic frequency to Live 12 normalized 0.0-1.0 parameter value."""
        clamped = max(min_f, min(max_f, freq))
        return math.log10(clamped / min_f) / math.log10(max_f / min_f)

    @classmethod
    def brightness_to_filter_hz(cls, brightness: float) -> float:
        """Maps brightness 0.0-1.0 to LPF cutoff from 300 Hz to 20000 Hz."""
        # Exponential curve for musical frequency sweep
        return 300.0 * ((20000.0 / 300.0) ** brightness)

    @classmethod
    def warmth_to_saturator_drive(cls, warmth: float) -> float:
        """Maps warmth 0.0-1.0 to Saturator drive in dB (0.0 to 6.0 dB)."""
        return round(warmth * 6.0, 2)

    @classmethod
    def generate_brightness_envelope(cls, track_role: str = "CHORDS") -> List[Tuple[float, float]]:
        """
        Generates a list of (beat, normalized_value) automation breakpoints across 96 bars (384 beats).
        Pre-Chorus includes a rising filter sweep; pre-drop has a micro dip.
        """
        points: List[Tuple[float, float]] = []

        for name, start_bar, end_bar, state in cls.DEFAULT_SECTION_ROADMAP:
            start_beat = float(start_bar * 4)
            end_beat = float(end_bar * 4)
            norm_val = cls.frequency_to_normalized(cls.brightness_to_filter_hz(state.brightness))

            if name == "Pre-Chorus":
                # Filter sweep: starts at verse level, opens fully into chorus
                start_sweep = cls.frequency_to_normalized(cls.brightness_to_filter_hz(0.55))
                end_sweep = cls.frequency_to_normalized(cls.brightness_to_filter_hz(0.95))
                points.append((start_beat, start_sweep))
                points.append((end_beat - 4.0, end_sweep))
                # Pre-drop filter snap down for contrast
                points.append((end_beat - 1.0, cls.frequency_to_normalized(cls.brightness_to_filter_hz(0.40))))
            elif name == "Chorus 1" or name == "Final Chorus":
                points.append((start_beat, norm_val))
                points.append((end_beat - 1.0, norm_val))
            elif name == "Outro":
                # Fade down
                start_val = cls.frequency_to_normalized(cls.brightness_to_filter_hz(0.50))
                end_val = cls.frequency_to_normalized(cls.brightness_to_filter_hz(0.20))
                points.append((start_beat, start_val))
                points.append((end_beat, end_val))
            else:
                points.append((start_beat, norm_val))
                points.append((end_beat, norm_val))

        return points

    @classmethod
    def generate_full_automation_manifest(cls) -> Dict[str, Any]:
        """Returns the complete multi-parameter automation roadmap for the project."""
        return {
            "status": "SUCCESS",
            "total_bars": 96,
            "total_beats": 384.0,
            "sections": [
                {
                    "section": p.section_name,
                    "bars": f"{p.start_bar}-{p.end_bar}",
                    "beats": f"{p.start_beat}-{p.end_beat}",
                    "macros": p.state.to_dict(),
                    "lpf_cutoff_hz": round(cls.brightness_to_filter_hz(p.state.brightness), 1),
                    "saturator_drive_db": cls.warmth_to_saturator_drive(p.state.warmth),
                }
                for p in cls.get_section_morph_plan()
            ],
            "brightness_envelope_points": len(cls.generate_brightness_envelope()),
        }

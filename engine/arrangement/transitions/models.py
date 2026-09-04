"""
Transition Models:
Data classes for transition descriptors, types, and automated FX fills.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class TransitionType(str, Enum):
    CUT = "cut"
    SWEEP_UP = "sweep_up"
    SWEEP_DOWN = "sweep_down"
    SNARE_ROLL = "snare_roll"
    RISER_CRASH = "riser_crash"
    SILENCE_GAP = "silence_gap"
    FILTER_FADE = "filter_fade"
    DRUM_FILL = "drum_fill"
    CROSSFADE = "crossfade"

@dataclass
class TransitionDescriptor:
    """Defines how the song transitions between two adjacent sections."""
    from_section_idx: int
    to_section_idx: int
    start_bar: int
    duration_bars: float  # e.g., 0.25 (1 beat), 0.5 (2 beats), 1.0, 2.0, 4.0
    transition_type: TransitionType
    affected_roles: List[str]
    pre_drop_silence_beats: float = 0.0  # e.g. 1.0 or 2.0 beats before drop
    intensity: float = 1.0  # 0.0 to 1.0
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "from_section": self.from_section_idx,
            "to_section": self.to_section_idx,
            "start_bar": self.start_bar,
            "duration_bars": self.duration_bars,
            "type": self.transition_type.value,
            "affected_roles": self.affected_roles,
            "pre_drop_silence_beats": self.pre_drop_silence_beats,
            "intensity": self.intensity,
            "description": self.description
        }

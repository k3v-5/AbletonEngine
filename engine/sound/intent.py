"""
Sound Intent & Sidechain Intent Models:
High-level musical declarations from the LLM or Creative Director.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class SoundIntent:
    """Declaration of desired sound character without referencing physical plugins."""
    role: str
    character: str = "dark_club"
    weight: float = 0.5
    brightness: float = 0.5
    warmth: float = 0.5
    punch: float = 0.5
    grit: float = 0.2
    movement: float = 0.3
    space: float = 0.2
    width: float = 0.3
    aggression: float = 0.3
    mono_below_hz: Optional[float] = None
    custom_params: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-set mono_below for low register roles
        if self.mono_below_hz is None and self.role.upper() in ["SUB_BASS", "BASS", "KICK"]:
            self.mono_below_hz = 120.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "character": self.character,
            "weight": round(self.weight, 3),
            "brightness": round(self.brightness, 3),
            "warmth": round(self.warmth, 3),
            "punch": round(self.punch, 3),
            "grit": round(self.grit, 3),
            "movement": round(self.movement, 3),
            "space": round(self.space, 3),
            "width": round(self.width, 3),
            "aggression": round(self.aggression, 3),
            "mono_below_hz": self.mono_below_hz,
            "custom_params": self.custom_params
        }

@dataclass
class SidechainIntent:
    """Sidechain ducking relationship between two musical roles."""
    source_role: str = "KICK"
    target_role: str = "BASS"
    amount: float = 0.65       # 0.0 to 1.0
    attack_ms: float = 2.0
    release_ms: float = 120.0
    curve: str = "musical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_role,
            "target": self.target_role,
            "amount": self.amount,
            "attack_ms": self.attack_ms,
            "release_ms": self.release_ms,
            "curve": self.curve
        }

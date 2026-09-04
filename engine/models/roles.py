# engine/models/roles.py
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field

class RoleEnum(str, Enum):
    KICK = "KICK"
    SUB_BASS = "SUB_BASS"
    BASS = "BASS"
    DRUMS = "DRUMS"
    PERCUSSION = "PERCUSSION"
    SNARE = "SNARE"
    HIHAT = "HIHAT"
    CLAP = "CLAP"
    VOCAL = "VOCAL"
    VOCAL_CHOP = "VOCAL_CHOP"
    CHORDS = "CHORDS"
    HARMONY = "HARMONY"
    LEAD = "LEAD"
    COUNTER_LEAD = "COUNTER_LEAD"
    ARPEGGIO = "ARPEGGIO"
    PAD = "PAD"
    TEXTURE = "TEXTURE"
    FX = "FX"
    RISER = "RISER"
    IMPACT = "IMPACT"
    ATMOSPHERE = "ATMOSPHERE"
    REFERENCE = "REFERENCE"
    OTHER = "OTHER"

def validate_role(role_name: Optional[str]) -> Optional[str]:
    """Validate and normalize a role string. Returns normalized name or raises ValueError if invalid."""
    if role_name is None:
        return None
    normalized = role_name.strip().upper()
    try:
        return RoleEnum(normalized).value
    except ValueError:
        valid_roles = [r.value for r in RoleEnum]
        raise ValueError(f"Invalid role '{role_name}'. Allowed roles: {valid_roles} or None")

@dataclass
class TrackMetadata:
    role: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    priority: float = 0.5
    locked: bool = False
    lock_reason: Optional[str] = None
    generated_by_engine: bool = False

    def to_dict(self):
        return {
            "role": self.role,
            "tags": self.tags,
            "priority": self.priority,
            "locked": self.locked,
            "lock_reason": self.lock_reason,
            "generated_by_engine": self.generated_by_engine
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            role=data.get("role"),
            tags=data.get("tags", []),
            priority=data.get("priority", 0.5),
            locked=data.get("locked", False),
            lock_reason=data.get("lock_reason"),
            generated_by_engine=data.get("generated_by_engine", False)
        )

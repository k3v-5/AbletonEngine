# engine/arrangement/models/section.py
from enum import Enum
from typing import Dict, Any, List, Optional

class SectionType(str, Enum):
    INTRO = "INTRO"
    PRE_INTRO = "PRE_INTRO"
    VERSE = "VERSE"
    DEVELOPMENT = "DEVELOPMENT"
    BUILD = "BUILD"
    PRE_DROP = "PRE_DROP"
    DROP = "DROP"
    BREAK = "BREAK"
    BREAKDOWN = "BREAKDOWN"
    BRIDGE = "BRIDGE"
    OUTRO = "OUTRO"
    TRANSITION = "TRANSITION"
    CUSTOM = "CUSTOM"

    @classmethod
    def from_str(cls, val: Any) -> "SectionType":
        if isinstance(val, SectionType):
            return val
        cleaned = str(val).strip().upper().replace(" ", "_").replace("-", "_")
        for member in cls:
            if member.value == cleaned:
                return member
        return cls.CUSTOM

class RoleState(str, Enum):
    OFF = "OFF"
    GHOST = "GHOST"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    FULL = "FULL"
    FEATURED = "FEATURED"

    @classmethod
    def from_str(cls, val: Any) -> "RoleState":
        if isinstance(val, RoleState):
            return val
        cleaned = str(val).strip().upper()
        for member in cls:
            if member.value == cleaned:
                return member
        return cls.OFF

class Section:
    """Represents a discrete musical section within a song arrangement."""
    def __init__(
        self,
        name: str = "Section",
        type: Any = SectionType.CUSTOM,
        id: str = "",
        start_bar: int = 1,
        end_bar: int = 16,
        duration_bars: int = 16,
        energy: float = 0.5,
        density: float = 0.5,
        tension: float = 0.2,
        release: float = 0.5,
        active_roles: Optional[Dict[str, RoleState]] = None,
        inactive_roles: Optional[List[str]] = None,
        variation: float = 0.0,
        transition_in: Optional[Dict[str, Any]] = None,
        transition_out: Optional[Dict[str, Any]] = None,
        humanization: float = 0.3,
        locked: bool = False,
        lock_reason: str = "",
        tags: Optional[List[str]] = None,
        groove: str = "straight",
        variation_type: str = "standard",
        section_type: Optional[Any] = None,
        bars: Optional[int] = None,
        **kwargs
    ):
        self.name = name
        raw_t = section_type if section_type is not None else type
        self.type = SectionType.from_str(raw_t)
        
        self.duration_bars = bars if bars is not None else (duration_bars if duration_bars > 0 else 16)
        self.start_bar = start_bar
        self.end_bar = start_bar + self.duration_bars - 1
        self.id = id if id else f"{self.name.lower().replace(' ', '_')}_{self.start_bar}"
        self.energy = float(energy)
        self.density = float(density)
        self.tension = float(tension)
        self.release = float(release)
        self.active_roles = active_roles or {}
        self.inactive_roles = inactive_roles or []
        self.variation = float(variation)
        self.transition_in = transition_in
        self.transition_out = transition_out
        self.humanization = float(humanization)
        self.locked = bool(locked)
        self.lock_reason = lock_reason
        self.tags = tags or []
        self.groove = groove
        self._variation_type = variation_type

    @property
    def bars(self) -> int:
        return self.duration_bars

    @bars.setter
    def bars(self, val: int):
        self.duration_bars = val
        self.end_bar = self.start_bar + val - 1

    @property
    def section_type(self) -> SectionType:
        return self.type

    @section_type.setter
    def section_type(self, val: Any):
        self.type = SectionType.from_str(val)

    @property
    def variation_type(self) -> str:
        return self._variation_type

    @variation_type.setter
    def variation_type(self, val: str):
        self._variation_type = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, SectionType) else str(self.type),
            "start_bar": self.start_bar,
            "end_bar": self.end_bar,
            "duration_bars": self.duration_bars,
            "energy": round(self.energy, 3),
            "density": round(self.density, 3),
            "tension": round(self.tension, 3),
            "release": round(self.release, 3),
            "active_roles": {r: (s.value if isinstance(s, RoleState) else str(s)) for r, s in self.active_roles.items()},
            "inactive_roles": list(self.inactive_roles),
            "variation": round(self.variation, 3),
            "transition_in": self.transition_in,
            "transition_out": self.transition_out,
            "humanization": round(self.humanization, 3),
            "locked": self.locked,
            "lock_reason": self.lock_reason,
            "tags": list(self.tags),
            "groove": self.groove,
            "variation_type": self._variation_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Section":
        raw_type = data.get("type", data.get("section_type", "CUSTOM"))
        raw_roles = data.get("active_roles", {})
        active_roles = {r: RoleState.from_str(s) for r, s in raw_roles.items()}

        s_bar = int(data.get("start_bar", 1))
        e_bar = int(data.get("end_bar", s_bar + 15))
        dur_bars = int(data.get("duration_bars", data.get("bars", (e_bar - s_bar + 1))))

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Section"),
            type=raw_type,
            start_bar=s_bar,
            end_bar=e_bar,
            duration_bars=dur_bars,
            energy=float(data.get("energy", 0.5)),
            density=float(data.get("density", 0.5)),
            tension=float(data.get("tension", 0.2)),
            release=float(data.get("release", 0.5)),
            active_roles=active_roles,
            inactive_roles=data.get("inactive_roles", []),
            variation=float(data.get("variation", 0.0)),
            transition_in=data.get("transition_in"),
            transition_out=data.get("transition_out"),
            humanization=float(data.get("humanization", 0.3)),
            locked=bool(data.get("locked", False)),
            lock_reason=data.get("lock_reason", ""),
            tags=data.get("tags", []),
            groove=data.get("groove", "straight"),
            variation_type=data.get("variation_type", "standard")
        )

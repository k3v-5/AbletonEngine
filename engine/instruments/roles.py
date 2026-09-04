# engine/instruments/roles.py
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class InstrumentRole(str, Enum):
    # Percussive / Drum roles
    KICK = "KICK"
    KICK_ALT = "KICK_ALT"
    SNARE = "SNARE"
    CLAP = "CLAP"
    CLOSED_HAT = "CLOSED_HAT"
    OPEN_HAT = "OPEN_HAT"
    PERCUSSION = "PERCUSSION"
    PERC_1 = "PERC_1"
    PERC_2 = "PERC_2"
    SHAKER = "SHAKER"
    TOM = "TOM"
    FX = "FX"
    IMPACT = "IMPACT"
    VOCAL_CHOP = "VOCAL_CHOP"

    # Melodic / Harmonic roles
    SUB_BASS = "SUB_BASS"
    BASS = "BASS"
    CHORDS = "CHORDS"
    PAD = "PAD"
    LEAD = "LEAD"
    ARPEGGIO = "ARPEGGIO"
    PLUCK = "PLUCK"
    KEYS = "KEYS"

    @classmethod
    def from_str(cls, val: str) -> "InstrumentRole":
        clean = val.strip().upper()
        for role in cls:
            if role.value == clean:
                return role
        # Common aliases
        if clean in ["KICK1", "BD", "BOMBO"]: return cls.KICK
        if clean in ["SD", "CAJA"]: return cls.SNARE
        if clean in ["CP"]: return cls.CLAP
        if clean in ["CH", "HAT", "HIHAT", "HI_HAT", "CLOSED_HIHAT"]: return cls.CLOSED_HAT
        if clean in ["OH", "OPEN_HIHAT"]: return cls.OPEN_HAT
        if clean in ["PERC", "PERCUSSION_1"]: return cls.PERC_1
        if clean in ["PERCUSSION_2"]: return cls.PERC_2
        if clean in ["SUB"]: return cls.SUB_BASS
        if clean in ["SYNTH"]: return cls.LEAD
        if clean in ["STRINGS", "PIANO", "HARMONY"]: return cls.CHORDS
        return cls.PERCUSSION

@dataclass
class SoundProfile:
    """Sonic profile specification describing how a role should sound"""
    name: str
    role: InstrumentRole
    character: str = ""                # e.g. 'deep', 'punchy', 'tight', 'bright', 'warm', 'analog'
    genre_affinity: List[str] = field(default_factory=lambda: ["melodic_techno", "techno"])
    frequency_bias: str = "balanced"   # 'sub', 'low_mid', 'mid', 'high'
    attack_ms: float = 10.0
    decay_ms: float = 250.0
    sustain_level: float = 0.0
    release_ms: float = 200.0
    preferred_sources: List[str] = field(default_factory=lambda: ["sample", "simpler"])
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role.value if isinstance(self.role, InstrumentRole) else str(self.role),
            "character": self.character,
            "genre_affinity": self.genre_affinity,
            "frequency_bias": self.frequency_bias,
            "attack_ms": self.attack_ms,
            "decay_ms": self.decay_ms,
            "sustain_level": self.sustain_level,
            "release_ms": self.release_ms,
            "preferred_sources": self.preferred_sources,
            "tags": self.tags
        }

# engine/music/intent.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class MusicalIntent:
    """High-level semantic musical intent requested by the LLM / Creative Director"""
    role: str                           # "BASS", "SUB_BASS", "KICK", "DRUMS", "CHORDS", "LEAD", "PAD", "PERCUSSION", etc.
    genre: str = "melodic_techno"       # "techno", "house", "melodic_techno", "trance", "hip_hop", "trap", "drill", "dnb"
    style: str = "rolling"              # "rolling", "four_on_floor", "syncopated", "arpeggiated", "sustained", "staccato"
    key: str = "F"                      # Root key, e.g. "C", "D#", "F", "Ab"
    scale: str = "natural_minor"        # "major", "natural_minor", "harmonic_minor", "dorian", "phrygian", etc.
    tempo: float = 128.0
    meter: str = "4/4"
    bars: int = 16
    energy: float = 0.8                 # Energy level (0.0 to 1.0)
    density: float = 0.7                # Note density (0.0 to 1.0)
    complexity: float = 0.4             # Rhythmic / Harmonic complexity (0.0 to 1.0)
    movement: float = 0.75              # Pitch movement / range traversal (0.0 to 1.0)
    tension: float = 0.55               # Harmonic tension / dissonance allowance (0.0 to 1.0)
    groove: str = "straight"            # "straight", "light_swing", "medium_swing", "heavy_swing", "laid_back", "pushing", "human"
    humanization: float = 0.5           # Humanization intensity (0.0 = strict quantized, 1.0 = heavy pocket jitter)
    seed: Optional[int] = 12345         # Deterministic seed for exact reproducibility
    register_min: Optional[int] = None  # Minimum MIDI note boundary
    register_max: Optional[int] = None  # Maximum MIDI note boundary
    section_type: Optional[str] = None  # "INTRO", "BUILD", "DROP", "BREAK", "OUTRO"
    variation_amount: float = 0.0       # 0.0 = static loop, 1.0 = heavy periodic evolution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "genre": self.genre,
            "style": self.style,
            "key": self.key,
            "scale": self.scale,
            "tempo": self.tempo,
            "meter": self.meter,
            "bars": self.bars,
            "energy": self.energy,
            "density": self.density,
            "complexity": self.complexity,
            "movement": self.movement,
            "tension": self.tension,
            "groove": self.groove,
            "humanization": self.humanization,
            "seed": self.seed,
            "register_min": self.register_min,
            "register_max": self.register_max,
            "section_type": self.section_type,
            "variation_amount": self.variation_amount
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MusicalIntent":
        return cls(
            role=data.get("role", "BASS"),
            genre=data.get("genre", "melodic_techno"),
            style=data.get("style", "rolling"),
            key=data.get("key", "F"),
            scale=data.get("scale", "natural_minor"),
            tempo=float(data.get("tempo", 128.0)),
            meter=data.get("meter", "4/4"),
            bars=int(data.get("bars", 16)),
            energy=float(data.get("energy", 0.8)),
            density=float(data.get("density", 0.7)),
            complexity=float(data.get("complexity", 0.4)),
            movement=float(data.get("movement", 0.75)),
            tension=float(data.get("tension", 0.55)),
            groove=data.get("groove", "straight"),
            humanization=float(data.get("humanization", 0.5)),
            seed=data.get("seed", 12345),
            register_min=data.get("register_min"),
            register_max=data.get("register_max"),
            section_type=data.get("section_type"),
            variation_amount=float(data.get("variation_amount", 0.0))
        )

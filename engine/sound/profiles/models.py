"""
Sound Profile Models:
Normalized [0.0, 1.0] timbre representations defining character, weight, brightness, and space.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class SoundProfile:
    """Comprehensive timbre descriptor for a musical role."""
    id: str
    role: str  # SUB_BASS, BASS, LEAD, PAD, CHORDS, DRUMS, etc.
    genre: str = "melodic_techno"
    character: str = "dark_club"  # clean, warm, dark, aggressive, analog, etc.
    weight: float = 0.5        # Low-end body & sub presence
    brightness: float = 0.5    # High frequency / cutoff opening
    warmth: float = 0.5        # Low-mid saturation & harmonic fullness
    aggression: float = 0.3    # Distortion, bite, resonance
    movement: float = 0.4      # LFO modulation, tremolo, filter sweeps
    space: float = 0.2         # Reverb & delay depth
    width: float = 0.3         # Stereo spread (0.0 = pure mono)
    density: float = 0.5       # Polyphony / harmonic density
    transient: float = 0.5     # Attack sharpness & punch
    distortion: float = 0.2    # Overdrive / tape warmth
    stereo: bool = True
    register_min_hz: float = 20.0
    register_max_hz: float = 20000.0

    def __post_init__(self):
        # Enforce strict normalization [0.0, 1.0]
        self.weight = max(0.0, min(1.0, float(self.weight)))
        self.brightness = max(0.0, min(1.0, float(self.brightness)))
        self.warmth = max(0.0, min(1.0, float(self.warmth)))
        self.aggression = max(0.0, min(1.0, float(self.aggression)))
        self.movement = max(0.0, min(1.0, float(self.movement)))
        self.space = max(0.0, min(1.0, float(self.space)))
        self.width = max(0.0, min(1.0, float(self.width)))
        self.density = max(0.0, min(1.0, float(self.density)))
        self.transient = max(0.0, min(1.0, float(self.transient)))
        self.distortion = max(0.0, min(1.0, float(self.distortion)))

    @property
    def punch(self) -> float:
        return self.transient
        if self.width <= 0.05:
            self.stereo = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "genre": self.genre,
            "character": self.character,
            "weight": round(self.weight, 3),
            "brightness": round(self.brightness, 3),
            "warmth": round(self.warmth, 3),
            "aggression": round(self.aggression, 3),
            "movement": round(self.movement, 3),
            "space": round(self.space, 3),
            "width": round(self.width, 3),
            "density": round(self.density, 3),
            "transient": round(self.transient, 3),
            "distortion": round(self.distortion, 3),
            "stereo": self.stereo,
            "register_min_hz": self.register_min_hz,
            "register_max_hz": self.register_max_hz
        }

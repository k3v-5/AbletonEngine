# engine/arrangement/energy/dimensions.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EnergyDimensions:
    """Multi-dimensional representation of musical energy in an arrangement."""
    energy: float = 0.5               # Global perceived energy (0.0 to 1.0)
    density: float = 0.5              # Active layers & note frequency (0.0 to 1.0)
    tension: float = 0.2              # Harmonic / rhythmic dissonance / suspense (0.0 to 1.0)
    brightness: float = 0.5           # High-frequency presence / register (0.0 to 1.0)
    rhythmic_activity: float = 0.5    # Subdivision speed & syncopation (0.0 to 1.0)
    harmonic_activity: float = 0.5    # Chord change frequency & extensions (0.0 to 1.0)
    spectral_activity: float = 0.5    # Frequency spread from sub to top-end (0.0 to 1.0)

    def to_dict(self) -> Dict[str, float]:
        return {
            "energy": round(self.energy, 3),
            "density": round(self.density, 3),
            "tension": round(self.tension, 3),
            "brightness": round(self.brightness, 3),
            "rhythmic_activity": round(self.rhythmic_activity, 3),
            "harmonic_activity": round(self.harmonic_activity, 3),
            "spectral_activity": round(self.spectral_activity, 3)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnergyDimensions":
        return cls(
            energy=float(data.get("energy", 0.5)),
            density=float(data.get("density", 0.5)),
            tension=float(data.get("tension", 0.2)),
            brightness=float(data.get("brightness", 0.5)),
            rhythmic_activity=float(data.get("rhythmic_activity", 0.5)),
            harmonic_activity=float(data.get("harmonic_activity", 0.5)),
            spectral_activity=float(data.get("spectral_activity", 0.5))
        )

# engine/arrangement/emotional_arc_engine.py
"""
Emotional Arc Engine (Level L - Emotional Arc):
Replaces 1D scalar energy (0.0 to 1.0) with a comprehensive 9-Dimensional Emotional State Tensor:
1. Tension (dissonance, pedal points, rising filters)
2. Release (tonal cadence, drop impact, open cutoff)
3. Density (voice count, event rate per beat)
4. Intimacy (close-mic acoustic isolation, dry signal)
5. Aggressiveness (saturation drive, transient snap, high velocity)
6. Luminosity (spectral air >6kHz, major/lydian inflections)
7. Darkness (sub-bass dominance, low-pass damping, minor/phrygian weight)
8. Movement (syncopation, rhythmic bounce, delay throws)
9. Expectation (vacuum drops, unresolved cadences, risers)

Provides high-resolution emotional tracking across all arrangement sections.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("EmotionalArcEngine")


@dataclass
class EmotionalStateVector:
    """A 9-dimensional psychological point representing the acoustic mood of a section."""
    tension: float = 0.50          # 0.0 (restful) to 1.0 (extreme tension)
    release: float = 0.50          # 0.0 (unresolved) to 1.0 (cathartic resolution)
    density: float = 0.50          # 0.0 (isolated solo) to 1.0 (dense wall of sound)
    intimacy: float = 0.50         # 0.0 (massive/distant) to 1.0 (close-mic whisper)
    aggressiveness: float = 0.50   # 0.0 (gentle/warm) to 1.0 (heavy punch/distortion)
    luminosity: float = 0.50       # 0.0 (veiled) to 1.0 (crystalline/open highs)
    darkness: float = 0.50         # 0.0 (sunlit) to 1.0 (deep sub/gloomy)
    movement: float = 0.50         # 0.0 (static drone) to 1.0 (kinetic syncopation)
    expectation: float = 0.50      # 0.0 (settled) to 1.0 (intense anticipation)

    def to_vector(self) -> List[float]:
        return [
            self.tension,
            self.release,
            self.density,
            self.intimacy,
            self.aggressiveness,
            self.luminosity,
            self.darkness,
            self.movement,
            self.expectation,
        ]

    def distance_to(self, other: EmotionalStateVector) -> float:
        """Calculates normalized Euclidean distance between two emotional states (0.0 to ~3.0)."""
        v1 = self.to_vector()
        v2 = other.to_vector()
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    def cosine_similarity(self, other: EmotionalStateVector) -> float:
        """Calculates cosine similarity between two emotional states (0.0 to 1.0)."""
        v1 = self.to_vector()
        v2 = other.to_vector()
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a ** 2 for a, b in zip(v1, v2)))
        mag2 = math.sqrt(sum(b ** 2 for a, b in zip(v1, v2)))
        if mag1 == 0.0 or mag2 == 0.0:
            return 1.0
        return max(0.0, min(1.0, dot / (mag1 * mag2)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tension": round(self.tension, 2),
            "release": round(self.release, 2),
            "density": round(self.density, 2),
            "intimacy": round(self.intimacy, 2),
            "aggressiveness": round(self.aggressiveness, 2),
            "luminosity": round(self.luminosity, 2),
            "darkness": round(self.darkness, 2),
            "movement": round(self.movement, 2),
            "expectation": round(self.expectation, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EmotionalStateVector:
        return cls(
            tension=float(data.get("tension", 0.5)),
            release=float(data.get("release", 0.5)),
            density=float(data.get("density", 0.5)),
            intimacy=float(data.get("intimacy", 0.5)),
            aggressiveness=float(data.get("aggressiveness", 0.5)),
            luminosity=float(data.get("luminosity", 0.5)),
            darkness=float(data.get("darkness", 0.5)),
            movement=float(data.get("movement", 0.5)),
            expectation=float(data.get("expectation", 0.5)),
        )


@dataclass
class SectionEmotionalProfile:
    """Emotional characterization of an individual arrangement section."""
    section_name: str
    bar_range: Tuple[int, int]
    vector: EmotionalStateVector
    narrative_focus: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "bar_range": list(self.bar_range),
            "vector": self.vector.to_dict(),
            "narrative_focus": self.narrative_focus,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SectionEmotionalProfile:
        br = data.get("bar_range", [1, 8])
        return cls(
            section_name=data.get("section_name", "Section"),
            bar_range=(int(br[0]), int(br[1])),
            vector=EmotionalStateVector.from_dict(data.get("vector", {})),
            narrative_focus=data.get("narrative_focus", ""),
        )


class EmotionalArcEngine:
    """
    Constructs, computes, and audits the master 9D emotional narrative arc of a song.
    """

    DEFAULT_PROFILES = {
        "intro": EmotionalStateVector(
            tension=0.20, release=0.10, density=0.25, intimacy=0.80,
            aggressiveness=0.10, luminosity=0.50, darkness=0.40, movement=0.30, expectation=0.60
        ),
        "verse 1": EmotionalStateVector(
            tension=0.30, release=0.20, density=0.45, intimacy=0.70,
            aggressiveness=0.20, luminosity=0.40, darkness=0.50, movement=0.50, expectation=0.40
        ),
        "hook 1": EmotionalStateVector(
            tension=0.50, release=0.80, density=0.80, intimacy=0.20,
            aggressiveness=0.50, luminosity=0.80, darkness=0.25, movement=0.85, expectation=0.30
        ),
        "verse 2": EmotionalStateVector(
            tension=0.45, release=0.25, density=0.40, intimacy=0.55,
            aggressiveness=0.35, luminosity=0.35, darkness=0.65, movement=0.75, expectation=0.60
        ),
        "hook 2": EmotionalStateVector(
            tension=0.65, release=0.85, density=0.85, intimacy=0.15,
            aggressiveness=0.68, luminosity=0.90, darkness=0.20, movement=0.92, expectation=0.55
        ),
        "bridge": EmotionalStateVector(
            tension=0.90, release=0.10, density=0.30, intimacy=0.85,
            aggressiveness=0.20, luminosity=0.20, darkness=0.85, movement=0.20, expectation=0.95
        ),
        "hook 3": EmotionalStateVector(
            tension=0.75, release=0.95, density=0.95, intimacy=0.10,
            aggressiveness=0.75, luminosity=0.90, darkness=0.20, movement=0.95, expectation=0.20
        ),
        "outro": EmotionalStateVector(
            tension=0.10, release=0.90, density=0.20, intimacy=0.80,
            aggressiveness=0.05, luminosity=0.50, darkness=0.50, movement=0.20, expectation=0.10
        ),
    }

    @classmethod
    def get_standard_profile(cls, section_name: str) -> EmotionalStateVector:
        s_low = section_name.lower().strip()
        for k, v in cls.DEFAULT_PROFILES.items():
            if k in s_low:
                return v
        return EmotionalStateVector()

    @classmethod
    def build_narrative_arc(
        cls,
        sections: List[Dict[str, Any]]
    ) -> List[SectionEmotionalProfile]:
        """
        Builds the 9D emotional timeline across all sections of the arrangement.
        """
        profiles: List[SectionEmotionalProfile] = []
        cur_bar = 1

        for sec in sections:
            s_name = sec.get("name", "Section")
            s_bars = int(sec.get("bars", 8))
            end_bar = cur_bar + s_bars - 1

            vec = cls.get_standard_profile(s_name)
            focus = f"Emotional trajectory for {s_name} with target tension {vec.tension} and expectation {vec.expectation}"

            profiles.append(SectionEmotionalProfile(
                section_name=s_name,
                bar_range=(cur_bar, end_bar),
                vector=vec,
                narrative_focus=focus,
            ))
            cur_bar = end_bar + 1

        return profiles

    @classmethod
    def compute_novelty_distance(
        cls,
        profile_a: SectionEmotionalProfile,
        profile_b: SectionEmotionalProfile
    ) -> float:
        """
        Returns the percentage delta novelty between two sections (0.0 to 1.0).
        High distance means the audience experiences a fresh psychological state.
        """
        # Distance normalized by max theoretical distance sqrt(9) = 3.0
        euc_dist = profile_a.vector.distance_to(profile_b.vector)
        normalized_dist = min(1.0, euc_dist / 1.732)
        return round(normalized_dist, 3)

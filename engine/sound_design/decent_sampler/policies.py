# engine/sound_design/decent_sampler/policies.py
"""
Level 3: Audio Safety Policies, Resource Heuristics, and UX Recommendations.

Encodes engineering guidelines, acoustic safety rules, and CPU protection policies
distinct from the raw Decent Sampler format specification.
"""

from typing import Tuple, Dict, Any, List
from dataclasses import dataclass


@dataclass
class AudioSafetyPolicy:
    """
    Heuristics and safety boundaries to guarantee pristine sound quality
    and protect listener ears and speakers from DC clicks and acoustic blowups.
    """

    # --- ANTI-CLICK TRANSIENT POLICIES ---
    # When sample files do not start on a zero-crossing, an attack of 0.0s can cause
    # a steep voltage jump (DC step), yielding an audible digital click.
    RECOMMENDED_MIN_ATTACK_SEC: float = 0.001  # 1 ms micro-fade
    RECOMMENDED_MIN_RELEASE_SEC: float = 0.005  # 5 ms smooth note-off

    # --- FILTER DSP LIMITS ---
    SAFE_CUTOFF_MIN_HZ: float = 20.0
    SAFE_CUTOFF_MAX_HZ: float = 20000.0
    SAFE_RESONANCE_MAX: float = 4.5  # Prevents self-oscillation howl

    # --- GAIN STAGING ---
    MAX_RECOMMENDED_GAIN_DB: float = 6.0
    MIN_RECOMMENDED_GAIN_DB: float = -60.0

    @classmethod
    def audit_envelope(cls, attack: float, release: float) -> List[str]:
        """Audits envelope parameters against acoustic click policies."""
        issues = []
        if attack < cls.RECOMMENDED_MIN_ATTACK_SEC:
            issues.append(
                f"Attack time ({attack:.6f}s) is below safe threshold ({cls.RECOMMENDED_MIN_ATTACK_SEC}s); "
                "risk of DC transient click on un-aligned sample start."
            )
        if release < cls.RECOMMENDED_MIN_RELEASE_SEC:
            issues.append(
                f"Release time ({release:.6f}s) is below safe threshold ({cls.RECOMMENDED_MIN_RELEASE_SEC}s); "
                "risk of sudden note-off click."
            )
        return issues


@dataclass
class ResourcePolicy:
    """
    CPU and memory heuristics to protect host DAW performance.
    """

    # Effects that create tail buffers and multiply CPU consumption per voice
    # are strongly recommended at the instrument level rather than per-group.
    INSTRUMENT_LEVEL_PREFERRED_EFFECTS: Tuple[str, ...] = ("reverb", "delay", "convolution")

    MAX_SUGGESTED_GROUPS: int = 64
    MAX_SUGGESTED_SAMPLES_PER_GROUP: int = 512

    @classmethod
    def audit_effect_placement(cls, effect_type: str, level: str) -> List[str]:
        """Audits whether heavy time-domain effects are safely placed."""
        warnings = []
        canonical_type = effect_type.lower()
        if level == "group" and canonical_type in cls.INSTRUMENT_LEVEL_PREFERRED_EFFECTS:
            warnings.append(
                f"Effect '{canonical_type}' placed at group level. Time-domain tail processing "
                "in per-voice groups risks voice-destruction truncation and high CPU overhead. "
                "Recommend moving to instrument-level <effects>."
            )
        return warnings


@dataclass
class UXPolicy:
    """
    Ergonomic and visual recommendations for plugin user interfaces.
    """

    DEFAULT_WIDTH: int = 812
    DEFAULT_HEIGHT: int = 375
    MIN_MACRO_KNOBS: int = 2
    MAX_MACRO_KNOBS: int = 8
    KNOB_SPACING_X: int = 100
    KNOB_START_X: int = 40
    KNOB_START_Y: int = 40

    @classmethod
    def calculate_knob_layout(cls, num_knobs: int) -> List[Tuple[int, int]]:
        """Calculates visually balanced (x, y) coordinates for macro controls."""
        coordinates = []
        for i in range(num_knobs):
            x = cls.KNOB_START_X + (i * cls.KNOB_SPACING_X)
            y = cls.KNOB_START_Y
            coordinates.append((x, y))
        return coordinates

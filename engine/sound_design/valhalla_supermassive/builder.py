# engine/sound_design/valhalla_supermassive/builder.py
"""
High-Level Preset Builder & Archetypes for Valhalla Supermassive.

Provides production-ready templates and a fluent builder for AI sound design:
- Ethereal Reverb (cosmic ambient clouds)
- Ping Pong Delay (crisp rhythmic stereo echoes)
- Dimension Chorus (wide multi-voice modulation)
- Infinite Drone Space (evolving endless spatial tail)
- Shimmer Cluster (celestial sparkling diffusion)
- Clean Plate (transparent percussion & vocal space)
"""

from typing import Optional, Union
from .model import SupermassiveModel
from .schema import ValhallaSupermassiveSchema
from .sanitizer import SupermassiveSanitizer


class SupermassiveBuilder:
    """Fluent builder for constructing Supermassive presets programmatically."""

    def __init__(self, preset_name: Optional[str] = None, name: Optional[str] = None):
        p_name = name or preset_name or "New Preset"
        self._model = SupermassiveModel(preset_name=p_name)

    def with_mode(self, mode_name: str) -> "SupermassiveBuilder":
        self._model.set_mode(mode_name)
        return self

    def with_mix(self, mix: float) -> "SupermassiveBuilder":
        self._model.mix = mix
        return self

    def with_synced_delay(self, division: str = "1/8", sync_type: str = "straight") -> "SupermassiveBuilder":
        self._model.set_sync(sync_type)
        self._model.set_delay_note(division)
        return self

    def with_free_delay(self, delay_ms: float) -> "SupermassiveBuilder":
        self._model.set_sync("ms")
        self._model.delay_ms = delay_ms
        return self

    def with_decay(self, feedback: float, density: float = 0.5, warp: float = 0.5) -> "SupermassiveBuilder":
        self._model.feedback = feedback
        self._model.density = density
        self._model.delay_warp = warp
        return self

    def with_tone(self, low_cut: float = 0.05, high_cut: float = 0.85) -> "SupermassiveBuilder":
        self._model.low_cut = low_cut
        self._model.high_cut = high_cut
        return self

    def with_modulation(self, rate: float = 0.5, depth: float = 0.5) -> "SupermassiveBuilder":
        self._model.mod_rate = rate
        self._model.mod_depth = depth
        return self

    def with_width(self, width: float = 1.0) -> "SupermassiveBuilder":
        self._model.width = width
        return self

    # Ergonomic set_* aliases
    def set_mix(self, mix: float) -> "SupermassiveBuilder":
        return self.with_mix(mix)

    def set_mode(self, mode: Union[str, float]) -> "SupermassiveBuilder":
        if isinstance(mode, (int, float)):
            self._model.mode = float(mode)
        else:
            self._model.set_mode(str(mode))
        return self

    def set_delay_sync(self, synced: bool) -> "SupermassiveBuilder":
        self._model.set_sync("synced" if synced else "ms")
        return self

    def set_feedback(self, feedback: float) -> "SupermassiveBuilder":
        self._model.feedback = float(feedback)
        return self

    def set_warp(self, warp: float) -> "SupermassiveBuilder":
        self._model.delay_warp = float(warp)
        return self

    def set_density(self, density: float) -> "SupermassiveBuilder":
        self._model.density = float(density)
        return self

    def set_low_cut(self, low_cut: float) -> "SupermassiveBuilder":
        self._model.low_cut = float(low_cut)
        return self

    def set_high_cut(self, high_cut: float) -> "SupermassiveBuilder":
        self._model.high_cut = float(high_cut)
        return self

    def build(self, sanitize: bool = True) -> SupermassiveModel:
        if sanitize:
            sanitized, _ = SupermassiveSanitizer.sanitize(self._model)
            return sanitized
        return self._model.copy()


ValhallaSupermassiveBuilder = SupermassiveBuilder


class SupermassiveArchetypes:
    """Production-grade archetype presets for AI sound design agents."""

    @staticmethod
    def create_ethereal_reverb(name: str = "Ethereal Ambient Cloud") -> SupermassiveModel:
        """Massive cosmic wash with slow bloom and rich stereo diffusion."""
        return (
            SupermassiveBuilder(name)
            .with_mode("Andromeda")
            .with_mix(0.50)
            .with_synced_delay("1/4", "dotted")
            .with_decay(feedback=0.75, density=0.80, warp=0.60)
            .with_tone(low_cut=0.08, high_cut=0.70)
            .with_modulation(rate=0.35, depth=0.45)
            .with_width(1.0)
            .build()
        )

    @staticmethod
    def create_ping_pong_delay(name: str = "Crisp Ping Pong") -> SupermassiveModel:
        """Crisp rhythmic echoes bouncing across the stereo field."""
        return (
            SupermassiveBuilder(name)
            .with_mode("Lyra")
            .with_mix(0.35)
            .with_synced_delay("1/8", "straight")
            .with_decay(feedback=0.45, density=0.15, warp=0.20)
            .with_tone(low_cut=0.10, high_cut=0.85)
            .with_modulation(rate=0.20, depth=0.15)
            .with_width(1.0)
            .build()
        )

    @staticmethod
    def create_dimension_chorus(name: str = "Dimension Ensemble Chorus") -> SupermassiveModel:
        """Wide dimensional chorus with short delay and zero feedback."""
        return (
            SupermassiveBuilder(name)
            .with_mode("Hydra")
            .with_mix(0.60)
            .with_free_delay(delay_ms=0.08)
            .with_decay(feedback=0.0, density=0.40, warp=0.10)
            .with_tone(low_cut=0.05, high_cut=0.90)
            .with_modulation(rate=0.40, depth=0.65)
            .with_width(1.0)
            .build()
        )

    @staticmethod
    def create_infinite_drone_space(name: str = "Infinite Drone Expanse") -> SupermassiveModel:
        """Vast evolving soundscape with sustained spatial energy."""
        return (
            SupermassiveBuilder(name)
            .with_mode("Great Annihilator")
            .with_mix(0.70)
            .with_synced_delay("1/2", "straight")
            .with_decay(feedback=0.88, density=0.90, warp=0.70)
            .with_tone(low_cut=0.12, high_cut=0.60)
            .with_modulation(rate=0.25, depth=0.50)
            .with_width(1.0)
            .build()
        )

    @staticmethod
    def create_shimmer_cluster(name: str = "Celestial Shimmer Cluster") -> SupermassiveModel:
        """Bright sparkling multi-tap reflections for plucks and leads."""
        return (
            SupermassiveBuilder(name)
            .with_mode("Pleiades")
            .with_mix(0.40)
            .with_synced_delay("1/16", "dotted")
            .with_decay(feedback=0.65, density=0.85, warp=0.45)
            .with_tone(low_cut=0.15, high_cut=0.95)
            .with_modulation(rate=0.50, depth=0.60)
            .with_width(1.0)
            .build()
        )

    @staticmethod
    def create_clean_plate(name: str = "Modern Clean Plate") -> SupermassiveModel:
        """Tight, transparent plate reverberation with zero mud."""
        return (
            SupermassiveBuilder(name)
            .with_mode("Virgo")
            .with_mix(0.30)
            .with_free_delay(delay_ms=0.20)
            .with_decay(feedback=0.50, density=0.70, warp=0.30)
            .with_tone(low_cut=0.10, high_cut=0.80)
            .with_modulation(rate=0.20, depth=0.20)
            .with_width(0.85)
            .build()
        )

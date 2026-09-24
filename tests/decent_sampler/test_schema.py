# tests/decent_sampler/test_schema.py
"""
Unit tests for DecentSamplerSchema (Level 1 Format Specification).
"""

import pytest
from engine.sound_design.decent_sampler.schema import DecentSamplerSchema


class TestDecentSamplerSchema:
    def test_canonical_effect_types_are_all_lowercase(self):
        """Invariant: All canonical effect names must be strictly lowercase."""
        for eff in DecentSamplerSchema.CANONICAL_EFFECT_TYPES:
            assert eff == eff.lower(), f"Effect type '{eff}' must be lowercase"
            assert eff.isalpha() or "_" in eff or "1pl" in eff

    def test_global_only_effects(self):
        """Verifies reverb and delay are recognized as global-only."""
        assert "reverb" in DecentSamplerSchema.GLOBAL_ONLY_EFFECTS
        assert "delay" in DecentSamplerSchema.GLOBAL_ONLY_EFFECTS
        # Filters and chorus should be allowed in groups
        assert "lowpass" in DecentSamplerSchema.GROUP_COMPATIBLE_EFFECTS
        assert "chorus" in DecentSamplerSchema.GROUP_COMPATIBLE_EFFECTS

    def test_physical_boundaries(self):
        """Verifies MIDI notes, velocity, and frequencies bounds."""
        assert DecentSamplerSchema.NOTE_MIN == 0
        assert DecentSamplerSchema.NOTE_MAX == 127
        assert DecentSamplerSchema.VELOCITY_MIN == 0
        assert DecentSamplerSchema.VELOCITY_MAX == 127
        assert DecentSamplerSchema.FREQUENCY_MIN_HZ == 20.0
        assert DecentSamplerSchema.FREQUENCY_MAX_HZ == 22000.0

    def test_binding_parameter_tokens(self):
        """Verifies essential parameter tokens exist."""
        expected_tokens = {
            "AMP_VOLUME", "PAN", "GLOBAL_TUNING",
            "ENV_ATTACK", "ENV_RELEASE", "ENV_SUSTAIN", "ENV_DECAY",
            "FX_FILTER_FREQUENCY", "FX_REVERB_WET_LEVEL", "FX_DELAY_TIME",
            "FX_DRIVE", "FX_BIT_DEPTH", "FX_RATIO", "GLIDE_TIME",
        }
        for token in expected_tokens:
            assert token in DecentSamplerSchema.VALID_BINDING_PARAMETERS

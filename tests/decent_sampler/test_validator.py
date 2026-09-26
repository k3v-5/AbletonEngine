# tests/decent_sampler/test_validator.py
"""
Unit tests for DecentSamplerValidator (3-Tier Validation System).
"""

import pytest
from engine.sound_design.decent_sampler.model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    BindingModel,
    ControlModel,
)
from engine.sound_design.decent_sampler.validator import DecentSamplerValidator, ValidationError


class TestDecentSamplerValidator:
    def test_tier1_format_uppercase_effect_detected(self):
        """Verifies uppercase effect types fail Tier 1 validation."""
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="sample.wav", root_note=60, lo_note=0, hi_note=127))
        inst.add_group(grp)
        inst.add_effect(EffectModel(type="Reverb"))  # Uppercase!

        report = DecentSamplerValidator.validate_model(inst, strict=False)
        assert report.is_valid is False
        assert any("canonical lowercase" in err for err in report.format_errors)

    def test_tier1_invalid_binding_token_detected(self):
        """Verifies unrecognized binding tokens are flagged."""
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="sample.wav", root_note=60))
        inst.add_group(grp)

        ctrl = ControlModel()
        ctrl.bindings.append(BindingModel(parameter="NON_EXISTENT_PARAMETER"))
        inst.add_control(ctrl)

        report = DecentSamplerValidator.validate_model(inst, strict=False)
        assert report.is_valid is False
        assert any("Unrecognized parameter token" in err for err in report.format_errors)

    def test_tier2_consistency_note_inversion_detected(self):
        """Verifies loNote > hiNote is caught as a structural error."""
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="sample.wav", root_note=60, lo_note=80, hi_note=40))
        inst.add_group(grp)

        report = DecentSamplerValidator.validate_model(inst, strict=False)
        assert report.is_valid is False
        assert any("Inverted note bounds" in err for err in report.consistency_errors)

    def test_tier2_consistency_path_backslash_detected(self):
        """Verifies Windows backslashes in paths are flagged."""
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="Samples\\piano_c4.wav", root_note=60, lo_note=0, hi_note=127))
        inst.add_group(grp)

        report = DecentSamplerValidator.validate_model(inst, strict=False)
        assert report.is_valid is False
        assert any("Windows backslashes" in err for err in report.consistency_errors)

    def test_tier3_policy_envelope_click_warning(self):
        """Verifies zero attack triggers an AudioSafetyPolicy warning (not a fatal error)."""
        inst = InstrumentModel()
        grp = GroupModel(attack=0.0)  # Zero attack!
        grp.add_sample(SampleZoneModel(path="sample.wav", root_note=60, lo_note=0, hi_note=127))
        inst.add_group(grp)

        report = DecentSamplerValidator.validate_model(inst, strict=False)
        # Should still be structurally valid, but emit a Tier 3 warning
        assert report.is_valid is True
        assert len(report.policy_warnings) > 0
        assert any("DC transient click" in w for w in report.policy_warnings)

    def test_strict_mode_raises_validation_error(self):
        """Verifies strict=True raises ValidationError on invalid model."""
        inst = InstrumentModel()  # Empty instrument (no groups)
        with pytest.raises(ValidationError):
            DecentSamplerValidator.validate_model(inst, strict=True)

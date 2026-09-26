# tests/test_surge_xt_synth.py
"""
Comprehensive Unit & Integration Test Suite for Surge XT Synthesizer Engine.
Tests oscillator models, 3-tier validation, sanitizer, serializer, and patch factory.
"""

import xml.etree.ElementTree as ET
import pytest
from pathlib import Path

from engine.sound_design.surge_xt_synth import (
    SurgeXTSynthSchema,
    SurgeOscillatorType,
    SurgeFilterType,
    SurgeSynthPatchModel,
    SurgeSynthOscillatorModel,
    SurgeSynthFilterModel,
    SurgeSynthEnvelopeModel,
    SurgeSynthValidator,
    SurgeSynthValidationError,
    SurgeSynthSanitizer,
    SurgeSynthSerializer,
    SurgeSynthPatchFactory,
)


class TestSurgeXTSynthSchema:
    """Verifies schema definitions, oscillator and filter topologies."""

    def test_all_10_oscillator_types_registered(self):
        assert len(SurgeXTSynthSchema.OSCILLATOR_TYPES) == 10
        assert "Classic" in SurgeXTSynthSchema.OSCILLATOR_TYPES
        assert "Modern" in SurgeXTSynthSchema.OSCILLATOR_TYPES
        assert "Wavetable" in SurgeXTSynthSchema.OSCILLATOR_TYPES
        assert "FM2" in SurgeXTSynthSchema.OSCILLATOR_TYPES
        assert "String" in SurgeXTSynthSchema.OSCILLATOR_TYPES
        assert "Twist" in SurgeXTSynthSchema.OSCILLATOR_TYPES

    def test_filters_registered(self):
        assert len(SurgeXTSynthSchema.FILTER_TYPES) >= 15
        assert "Ladder Lowpass" in SurgeXTSynthSchema.FILTER_TYPES
        assert "K35 Lowpass" in SurgeXTSynthSchema.FILTER_TYPES
        assert "Diode Lowpass" in SurgeXTSynthSchema.FILTER_TYPES

    def test_unison_and_pitch_bounds(self):
        assert SurgeXTSynthSchema.UNISON_MIN_VOICES == 1
        assert SurgeXTSynthSchema.UNISON_MAX_VOICES == 16
        assert SurgeXTSynthSchema.OCTAVE_MIN == -3
        assert SurgeXTSynthSchema.OCTAVE_MAX == 3
        assert SurgeXTSynthSchema.MIN_RELEASE_SEC == 0.005


class TestSurgeSynthModel:
    """Tests data models, XML generation, and LOM mapping."""

    def test_patch_initialization_and_to_dict(self):
        patch = SurgeSynthPatchModel(patch_name="TestReese", volume=0.85, unison_count=2)
        d = patch.to_dict()
        assert d["patch_name"] == "TestReese"
        assert d["volume"] == 0.85
        assert d["unison_count"] == 2
        assert len(d["oscillators"]) == 3
        assert "filter1" in d
        assert "amp_envelope" in d

    def test_to_xml_string_is_valid_xml(self):
        patch = SurgeSynthPatchModel(patch_name="ValidXMLPatch")
        xml_str = patch.to_xml_string()

        assert xml_str.startswith("<surge-patch")
        root = ET.fromstring(xml_str)
        assert root.tag == "surge-patch"
        assert root.attrib["name"] == "ValidXMLPatch"

        # Check subelements
        scene = root.find("scene")
        assert scene is not None
        assert len(scene.find("oscillators")) == 3
        assert len(scene.find("filters")) == 2

    def test_to_lom_command_list(self):
        patch = SurgeSynthPatchModel(volume=0.75, unison_count=4)
        cmds = patch.to_lom_command_list()
        cmd_dict = dict(cmds)

        assert cmd_dict["Volume"] == 0.75
        assert cmd_dict["Unison Count"] == 4.0
        assert "Osc 1 Level" in cmd_dict
        assert "Filter 1 Cutoff" in cmd_dict
        assert "Amp Attack" in cmd_dict


class TestSurgeSynthValidator:
    """Tests 3-tier validation rules: bounds, physical consistency, acoustic policy."""

    def test_valid_patch_passes(self):
        patch = SurgeSynthPatchModel()
        rep = SurgeSynthValidator.validate_patch(patch)
        assert rep.is_valid
        assert len(rep.errors) == 0

    def test_tier1_invalid_osc_type_or_bounds(self):
        patch = SurgeSynthPatchModel(volume=1.5, unison_count=25)
        patch.oscillators[0].osc_type = "NonExistentOsc"
        rep = SurgeSynthValidator.validate_patch(patch)

        assert not rep.is_valid
        assert not rep.tier1_passed
        assert any("Volume" in e.lower() or "volume" in e.lower() for e in rep.errors)
        assert any("unison_count" in e for e in rep.errors)
        assert any("invalid type" in e for e in rep.errors)

    def test_tier2_dead_patch_detection(self):
        # Mute all oscillators
        patch = SurgeSynthPatchModel()
        for osc in patch.oscillators:
            osc.mute = True
        rep = SurgeSynthValidator.validate_patch(patch)
        assert not rep.is_valid
        assert not rep.tier2_passed
        assert any("Dead patch" in e for e in rep.errors)

    def test_tier2_anti_click_release_floor(self):
        patch = SurgeSynthPatchModel()
        patch.amp_envelope.release = 0.001  # Below 0.005s floor
        rep = SurgeSynthValidator.validate_patch(patch)
        assert not rep.is_valid
        assert not rep.tier2_passed
        assert any("release" in e.lower() for e in rep.errors)

    def test_tier3_policy_warnings(self):
        patch = SurgeSynthPatchModel()
        patch.filter1.resonance = 0.98  # Dangerously high resonance
        rep = SurgeSynthValidator.validate_patch(patch)
        assert rep.is_valid  # Warnings don't block unless strict
        assert len(rep.warnings) > 0
        assert any("resonance" in w.lower() for w in rep.warnings)

    def test_strict_mode_raises(self):
        patch = SurgeSynthPatchModel()
        patch.amp_envelope.release = 0.0  # Invalid
        with pytest.raises(SurgeSynthValidationError):
            SurgeSynthValidator.validate_patch(patch, strict=True)


class TestSurgeSynthSanitizer:
    """Tests clamping, alias resolution, and dead patch resurrection."""

    def test_sanitizes_out_of_bounds(self):
        patch = SurgeSynthPatchModel(volume=2.0, unison_count=32, unison_detune=1.5)
        SurgeSynthSanitizer.sanitize_patch(patch)
        assert patch.volume == 1.0
        assert patch.unison_count == 16
        assert patch.unison_detune == 1.0

    def test_resolves_oscillator_and_filter_aliases(self):
        assert SurgeSynthSanitizer.resolve_oscillator_type("saw") == "Classic"
        assert SurgeSynthSanitizer.resolve_oscillator_type("plaits") == "Twist"
        assert SurgeSynthSanitizer.resolve_oscillator_type("fm") == "FM2"
        assert SurgeSynthSanitizer.resolve_oscillator_type("chiptune") == "Alias"

        assert SurgeSynthSanitizer.resolve_filter_type("moog") == "Ladder Lowpass"
        assert SurgeSynthSanitizer.resolve_filter_type("k35") == "K35 Lowpass"
        assert SurgeSynthSanitizer.resolve_filter_type("303") == "Diode Lowpass"

    def test_resurrects_dead_patch(self):
        patch = SurgeSynthPatchModel()
        for osc in patch.oscillators:
            osc.mute = True
            osc.level = 0.0
        SurgeSynthSanitizer.sanitize_patch(patch)
        assert not patch.oscillators[0].mute
        assert patch.oscillators[0].level > 0.0


class TestSurgeSynthSerializer:
    """Tests saving .surgepatch XML files."""

    def test_save_patch_and_read_xml(self, tmp_path):
        patch = SurgeSynthPatchModel(patch_name="BassMonster", volume=0.88)
        dest = tmp_path / "BassMonster.surgepatch"
        saved = SurgeSynthSerializer.save_patch(patch, target_path=dest)

        assert saved.exists()
        content = saved.read_text(encoding="utf-8")
        assert "<surge-patch" in content
        root = ET.fromstring(content)
        assert root.attrib["name"] == "BassMonster"


class TestSurgeSynthPatchFactory:
    """Tests factory patch generators across musical roles."""

    def test_all_factory_presets_are_100_percent_valid(self):
        reese = SurgeSynthPatchFactory.build_bass_reese_patch()
        assert SurgeSynthValidator.validate_patch(reese).is_valid

        pluck = SurgeSynthPatchFactory.build_pluck_fm_patch()
        assert SurgeSynthValidator.validate_patch(pluck).is_valid

        lead = SurgeSynthPatchFactory.build_lead_supersaw_patch()
        assert SurgeSynthValidator.validate_patch(lead).is_valid

        pad = SurgeSynthPatchFactory.build_pad_lush_patch()
        assert SurgeSynthValidator.validate_patch(pad).is_valid

        sub808 = SurgeSynthPatchFactory.build_808_sub_patch()
        assert SurgeSynthValidator.validate_patch(sub808).is_valid

    def test_dynamic_create_role_patch(self):
        roles = ["BASS", "KEYS", "LEAD", "PAD", "PLUCK", "SUB_BASS"]
        for r in roles:
            patch = SurgeSynthPatchFactory.create_role_patch(r, bpm=128.0, applied_params={"Volume": 0.82})
            assert isinstance(patch, SurgeSynthPatchModel)
            rep = SurgeSynthValidator.validate_patch(patch, role=r)
            assert rep.is_valid, f"Generated patch for {r} must be valid"
            assert patch.amp_envelope.release >= 0.005

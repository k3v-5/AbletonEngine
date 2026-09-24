# tests/test_valhalla_supermassive.py
"""
Exhaustive Test Suite for Valhalla Supermassive Sound Design & Validation Engine.
"""

import pytest
import tempfile
from pathlib import Path

from engine.sound_design.valhalla_supermassive import (
    ValhallaSupermassiveSchema,
    SupermassiveModel,
    SupermassiveSafetyPolicy,
    ValhallaSupermassiveValidator,
    ValhallaValidationReport,
    ValhallaValidationError,
    SupermassiveSanitizer,
    ValhallaSupermassiveSerializer,
    SupermassiveBuilder,
    SupermassiveArchetypes,
)


class TestValhallaSchema:
    def test_22_modes_count_and_indexing(self):
        assert ValhallaSupermassiveSchema.NUM_MODES == 22
        assert len(ValhallaSupermassiveSchema.MODES) == 22
        assert ValhallaSupermassiveSchema.MODES[0] == "Gemini"
        assert ValhallaSupermassiveSchema.MODES[5] == "Andromeda"
        assert ValhallaSupermassiveSchema.MODES[6] == "Lyra"
        assert ValhallaSupermassiveSchema.MODES[21] == "Sirius"

    def test_mode_float_conversion_roundtrip(self):
        for idx, mode_name in enumerate(ValhallaSupermassiveSchema.MODES):
            expected_float = idx / 21.0
            float_val = ValhallaSupermassiveSchema.mode_to_float(mode_name)
            assert pytest.approx(float_val, abs=1e-5) == expected_float

            recovered_name = ValhallaSupermassiveSchema.float_to_mode(float_val)
            assert recovered_name == mode_name

            recovered_idx = ValhallaSupermassiveSchema.float_to_mode_index(float_val)
            assert recovered_idx == idx

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown Valhalla Supermassive mode"):
            ValhallaSupermassiveSchema.mode_to_float("NebulaDoesNotExist")

    def test_sync_modes(self):
        assert ValhallaSupermassiveSchema.SYNC_MODES["unsynced"] == 0.0
        assert ValhallaSupermassiveSchema.SYNC_MODES["straight"] == 0.25
        assert ValhallaSupermassiveSchema.SYNC_MODES["dotted"] == 0.5
        assert ValhallaSupermassiveSchema.SYNC_MODES["triplet"] == 0.75


class TestValhallaModel:
    def test_default_model(self):
        m = SupermassiveModel()
        assert m.preset_name == "Default"
        assert m.plugin_version == "2.5.0"
        assert m.mode_name == "Gemini"
        assert m.mix == 1.0
        assert m.feedback == 0.5

    def test_set_mode_and_sync(self):
        m = SupermassiveModel()
        m.set_mode("Andromeda")
        assert m.mode_name == "Andromeda"
        assert m.mode_index == 5
        assert pytest.approx(m.mode, abs=1e-4) == 5 / 21.0

        m.set_sync("triplet")
        assert m.delay_sync == 0.75

        m.set_delay_note("1/4")
        assert pytest.approx(m.delay_note, abs=1e-4) == 0.428571433

    def test_to_xml_attribs(self):
        m = SupermassiveModel(preset_name="TestPatch")
        attribs = m.to_xml_attribs()
        assert attribs["presetName"] == "TestPatch"
        assert attribs["pluginVersion"] == "2.5.0"
        assert "Mix" in attribs
        assert "Mode" in attribs
        assert "Feedback" in attribs
        assert len(attribs) == 20  # 18 float params (14 DSP + 4 Reserved) + pluginVersion + presetName


class TestValhallaSanitizer:
    def test_clamp_out_of_bounds_parameters(self):
        bad = SupermassiveModel(
            mix=1.5,
            feedback=-0.2,
            low_cut=2.0,
            high_cut=-1.0,
            clear=0.7,
        )
        repaired, fixes = SupermassiveSanitizer.sanitize(bad)
        assert repaired.mix == 1.0
        assert repaired.feedback == 0.0
        assert repaired.low_cut == 1.0
        assert repaired.high_cut == 0.0
        assert repaired.clear == 1.0
        assert len(fixes) >= 5

    def test_sanitize_empty_preset_name(self):
        bad = SupermassiveModel(preset_name="")
        repaired, fixes = SupermassiveSanitizer.sanitize(bad)
        assert repaired.preset_name == "Untitled"
        assert any("presetName" in f for f in fixes)


class TestValhallaSafetyPolicy:
    def test_runaway_feedback_warning(self):
        m = SupermassiveModel(feedback=0.98, delay_warp=0.85)
        warnings = SupermassiveSafetyPolicy.audit_model(m)
        assert any("Runaway Feedback" in w for w in warnings)

    def test_sub_mud_warning(self):
        m = SupermassiveModel(mix=0.6, low_cut=0.01)
        m.set_mode("Andromeda")
        warnings = SupermassiveSafetyPolicy.audit_model(m)
        assert any("Sub Mud" in w for w in warnings)

    def test_safe_preset_has_no_hazard(self):
        m = SupermassiveModel(mix=0.5, feedback=0.6, delay_warp=0.5, low_cut=0.10)
        m.set_mode("Centaurus")
        warnings = SupermassiveSafetyPolicy.audit_model(m)
        assert len(warnings) == 0


class TestValhallaValidator:
    def test_valid_model(self):
        m = SupermassiveModel()
        report = ValhallaSupermassiveValidator.validate_model(m)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_invalid_model_tier2(self):
        m = SupermassiveModel(feedback=1.5)
        report = ValhallaSupermassiveValidator.validate_model(m)
        assert not report.is_valid
        assert any("feedback" in e for e in report.consistency_errors)

    def test_strict_mode_raises(self):
        m = SupermassiveModel(feedback=1.5)
        with pytest.raises(ValhallaValidationError):
            ValhallaSupermassiveValidator.validate_model(m, strict=True)

    def test_validate_valid_xml_string(self):
        m = SupermassiveModel(preset_name="ValidXml")
        xml_str = ValhallaSupermassiveSerializer.to_xml_string(m)
        report = ValhallaSupermassiveValidator.validate_xml_string(xml_str)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_validate_invalid_xml_string(self):
        bad_xml = "<WrongTag Mix='1.0' />"
        report = ValhallaSupermassiveValidator.validate_xml_string(bad_xml)
        assert not report.is_valid
        assert any("WrongTag" in e for e in report.format_errors)


class TestValhallaSerializer:
    def test_roundtrip_xml(self):
        original = SupermassiveModel(
            preset_name="SpaceOddity",
            mix=0.65,
            feedback=0.72,
            low_cut=0.08,
            high_cut=0.85,
        )
        original.set_mode("Andromeda")

        xml_str = ValhallaSupermassiveSerializer.to_xml_string(original)
        assert xml_str.startswith("<ValhallaSupermassive")
        assert "presetName=\"SpaceOddity\"" in xml_str

        restored = ValhallaSupermassiveSerializer.from_xml_string(xml_str)
        assert restored.preset_name == "SpaceOddity"
        assert pytest.approx(restored.mix, abs=1e-4) == 0.65
        assert pytest.approx(restored.feedback, abs=1e-4) == 0.72
        assert pytest.approx(restored.low_cut, abs=1e-4) == 0.08
        assert restored.mode_name == "Andromeda"

    def test_file_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "MyCustomPreset.vpreset"
            m = SupermassiveModel(preset_name="FileTest", mix=0.42)
            m.set_mode("Lyra")

            saved_path = ValhallaSupermassiveSerializer.save_preset_file(m, destination_path=file_path)
            assert saved_path.exists()
            assert saved_path.suffix == ".vpreset"

            loaded = ValhallaSupermassiveSerializer.load_preset_file(saved_path)
            assert loaded.preset_name == "FileTest"
            assert loaded.mode_name == "Lyra"
            assert pytest.approx(loaded.mix, abs=1e-4) == 0.42


class TestValhallaBuilderAndArchetypes:
    def test_fluent_builder(self):
        m = (
            SupermassiveBuilder("CustomSwell")
            .with_mode("Centaurus")
            .with_mix(0.45)
            .with_synced_delay("1/4", "dotted")
            .with_decay(feedback=0.60, density=0.75, warp=0.40)
            .with_tone(low_cut=0.06, high_cut=0.80)
            .with_modulation(rate=0.30, depth=0.40)
            .with_width(0.90)
            .build()
        )
        assert m.preset_name == "CustomSwell"
        assert m.mode_name == "Centaurus"
        assert m.delay_sync == 0.5  # dotted
        assert m.low_cut == 0.06

        report = ValhallaSupermassiveValidator.validate_model(m)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_all_archetypes_valid(self):
        archetypes = [
            SupermassiveArchetypes.create_ethereal_reverb(),
            SupermassiveArchetypes.create_ping_pong_delay(),
            SupermassiveArchetypes.create_dimension_chorus(),
            SupermassiveArchetypes.create_infinite_drone_space(),
            SupermassiveArchetypes.create_shimmer_cluster(),
            SupermassiveArchetypes.create_clean_plate(),
        ]
        for arc in archetypes:
            report = ValhallaSupermassiveValidator.validate_model(arc)
            assert report.is_valid
            assert len(report.all_errors) == 0

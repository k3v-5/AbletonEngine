# tests/test_valhalla_vintage_verb.py
"""
Comprehensive Unit & Integration Test Suite for Valhalla VintageVerb Engine.
Tests the 22 modes, 3 color eras, 3-tier validation, sanitizer, serializer, and mode selector.
"""

import os
import xml.etree.ElementTree as ET
import pytest
from pathlib import Path

from engine.sound_design.valhalla_vintage_verb import (
    ValhallaVintageVerbSchema,
    VintageVerbColor,
    VintageVerbModel,
    ValhallaVintageVerbValidator,
    VintageVerbValidationError,
    ValhallaVintageVerbSanitizer,
    ValhallaVintageVerbSerializer,
    VintageVerbModeSelector,
)


class TestValhallaVintageVerbSchema:
    """Verifies schema definitions, algorithmic modes, and mathematical conversions."""

    def test_all_22_modes_registered(self):
        assert len(ValhallaVintageVerbSchema.MODES) == 22
        assert ValhallaVintageVerbSchema.NUM_MODES == 22

    def test_mode_bijective_mapping(self):
        for idx, mode_name in enumerate(ValhallaVintageVerbSchema.MODES):
            norm_val = ValhallaVintageVerbSchema.mode_to_float(mode_name)
            assert 0.0 <= norm_val <= 1.0
            reconstructed = ValhallaVintageVerbSchema.float_to_mode(norm_val)
            assert reconstructed == mode_name

    def test_color_modes_mapping(self):
        assert len(ValhallaVintageVerbSchema.COLORS) == 3
        for color_name in ["1970s", "1980s", "Now"]:
            norm_val = ValhallaVintageVerbSchema.color_to_float(color_name)
            assert 0.0 <= norm_val <= 1.0
            reconstructed = ValhallaVintageVerbSchema.float_to_color(norm_val)
            assert reconstructed == color_name

    def test_predelay_conversion(self):
        assert ValhallaVintageVerbSchema.predelay_to_ms(0.0) == 0.0
        assert ValhallaVintageVerbSchema.predelay_to_ms(1.0) == 500.0
        assert ValhallaVintageVerbSchema.predelay_to_ms(0.1) == 50.0

        assert ValhallaVintageVerbSchema.ms_to_predelay(0.0) == 0.0
        assert ValhallaVintageVerbSchema.ms_to_predelay(500.0) == 1.0
        assert ValhallaVintageVerbSchema.ms_to_predelay(50.0) == 0.1

    def test_decay_conversion(self):
        assert ValhallaVintageVerbSchema.decay_to_seconds(0.0) == 0.20
        assert ValhallaVintageVerbSchema.decay_to_seconds(1.0) == 70.00
        # Roundtrip
        for sec in [0.5, 1.5, 3.0, 10.0, 45.0]:
            norm = ValhallaVintageVerbSchema.seconds_to_decay(sec)
            recovered = ValhallaVintageVerbSchema.decay_to_seconds(norm)
            assert abs(recovered - sec) < 0.2


class TestValhallaVintageVerbModel:
    """Tests model representation, dictionary conversion, and XML output."""

    def test_default_model_initialization(self):
        model = VintageVerbModel()
        assert model.plugin_version == "2.2.0"
        assert model.mode_name == "Concert Hall"
        assert model.color_name == "1980s"
        assert model.mix == 0.20

    def test_to_dict_keys_and_values(self):
        model = VintageVerbModel(preset_name="StudioSnare", mix=0.25, decay=0.30)
        d = model.to_dict()
        assert d["preset_name"] == "StudioSnare"
        assert d["Mix"] == 0.25
        assert d["Decay"] == 0.30
        assert "mode_name" in d
        assert "color_name" in d

    def test_to_xml_string_is_valid_xml(self):
        model = VintageVerbModel(preset_name="VocalPlate", mix=0.22, low_cut=0.18)
        model.mode_name = "Smooth Plate"
        xml_str = model.to_xml_string()

        assert xml_str.startswith("<ValhallaVintageVerb")
        assert "presetName=\"VocalPlate\"" in xml_str
        assert "pluginVersion=\"2.2.0\"" in xml_str

        # Parse with ElementTree to verify XML well-formedness
        root = ET.fromstring(xml_str)
        assert root.tag == "ValhallaVintageVerb"
        assert root.attrib["Mix"] == str(round(model.mix, 6))

    def test_from_dict_and_case_insensitivity(self):
        data = {
            "preset_name": "AmbientChamber",
            "mix": 0.35,
            "mode": "Chamber",
            "color_mode": "1970s",
            "predelay": 0.05,
        }
        model = VintageVerbModel.from_dict(data)
        assert model.preset_name == "AmbientChamber"
        assert model.mix == 0.35
        assert model.mode_name == "Chamber"
        assert model.color_name == "1970s"
        assert model.predelay == 0.05


class TestValhallaVintageVerbValidator:
    """Tests 3-tier validation rules: bounds, physical consistency, acoustic policy."""

    def test_valid_model_passes(self):
        model = VintageVerbModel()
        rep = ValhallaVintageVerbValidator.validate(model)
        assert rep.is_valid
        assert len(rep.errors) == 0

    def test_tier1_parameter_out_of_bounds(self):
        model = VintageVerbModel(mix=1.5)  # > 1.0
        rep = ValhallaVintageVerbValidator.validate(model)
        assert not rep.is_valid
        assert not rep.tier1_passed
        assert any("Mix" in e for e in rep.errors)

    def test_tier2_spectral_inversion(self):
        # LowCut higher than HighCut
        model = VintageVerbModel(low_cut=0.80, high_cut=0.20)
        rep = ValhallaVintageVerbValidator.validate(model)
        assert not rep.is_valid
        assert not rep.tier2_passed
        assert any("Spectral inversion" in e for e in rep.errors)

    def test_tier3_policy_warnings(self):
        # LowCut too low for drums
        model = VintageVerbModel(low_cut=0.01)
        rep = ValhallaVintageVerbValidator.validate(model, role="DRUMS")
        assert rep.is_valid  # Warnings don't invalidate unless strict
        assert len(rep.warnings) > 0
        assert any("mud" in w.lower() for w in rep.warnings)

    def test_strict_mode_raises(self):
        model = VintageVerbModel(decay=-0.1)
        with pytest.raises(VintageVerbValidationError):
            ValhallaVintageVerbValidator.validate(model, strict=True)


class TestValhallaVintageVerbSanitizer:
    """Tests automatic clamping, alias resolution, and inversion repair."""

    def test_sanitizes_out_of_bounds(self):
        model = VintageVerbModel(mix=2.5, predelay=-0.5, size=0.01)
        ValhallaVintageVerbSanitizer.sanitize(model)
        assert model.mix == 1.0
        assert model.predelay == 0.0
        assert model.size >= 0.05

    def test_repairs_spectral_inversion(self):
        model = VintageVerbModel(low_cut=0.85, high_cut=0.15)
        ValhallaVintageVerbSanitizer.sanitize(model)
        assert model.low_cut < model.high_cut

    def test_resolves_mode_and_color_aliases(self):
        assert ValhallaVintageVerbSanitizer.resolve_mode("concert") == "Concert Hall"
        assert ValhallaVintageVerbSanitizer.resolve_mode("smooth plate") == "Smooth Plate"
        assert ValhallaVintageVerbSanitizer.resolve_mode("gated") == "Nonlin"
        assert ValhallaVintageVerbSanitizer.resolve_color("80s") == "1980s"
        assert ValhallaVintageVerbSanitizer.resolve_color("modern") == "Now"


class TestValhallaVintageVerbSerializer:
    """Tests saving presets to disk and clipboard copying."""

    def test_save_preset_and_load_xml(self, tmp_path):
        model = VintageVerbModel(preset_name="TestReverb", mix=0.28)
        dest = tmp_path / "TestReverb.vpreset"
        saved_path = ValhallaVintageVerbSerializer.save_preset(model, target_path=dest)

        assert saved_path.exists()
        content = saved_path.read_text(encoding="utf-8")
        assert "<ValhallaVintageVerb" in content
        root = ET.fromstring(content)
        assert root.attrib["presetName"] == "TestReverb"


class TestVintageVerbModeSelector:
    """Tests role-based mode selection and acoustic tailoring."""

    def test_recommend_modes_for_roles(self):
        mode, color = VintageVerbModeSelector.recommend_mode_and_color_for_role("DRUMS")
        assert mode == "Plate"
        assert color == "1980s"

        mode_v, color_v = VintageVerbModeSelector.recommend_mode_and_color_for_role("VOCALS")
        assert mode_v == "Smooth Plate"

        mode_k, _ = VintageVerbModeSelector.recommend_mode_and_color_for_role("KEYS")
        assert mode_k == "Chamber"

        mode_p, _ = VintageVerbModeSelector.recommend_mode_and_color_for_role("PAD")
        assert mode_p == "Cathedral"

    def test_haas_pre_delay_roles(self):
        drum_haas = VintageVerbModeSelector.calculate_haas_pre_delay_ms(120.0, "DRUMS")
        assert drum_haas <= 12.0

        vocal_haas = VintageVerbModeSelector.calculate_haas_pre_delay_ms(120.0, "VOCALS")
        assert vocal_haas >= 25.0

    def test_build_role_preset_validity(self):
        for role in ["DRUMS", "VOCALS", "KEYS", "PAD", "LEAD", "BASS"]:
            preset = VintageVerbModeSelector.build_role_preset(
                preset_name=f"Studio_{role}",
                role=role,
                bpm=124.0,
                applied_params={"Mix": 0.22}
            )
            assert isinstance(preset, VintageVerbModel)
            v_rep = ValhallaVintageVerbValidator.validate(preset, role=role)
            assert v_rep.is_valid, f"Preset for {role} must be valid"
            assert preset.low_cut < preset.high_cut

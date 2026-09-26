# tests/test_surge_xt_fx.py
"""
Exhaustive Test Suite for Surge XT FX Multi-Tier Validation & Sound Design Engine.
"""

import pytest
import tempfile
from pathlib import Path

from engine.sound_design.surge_xt_fx import (
    FXType,
    FXChain,
    FXBypass,
    SurgeFXSchema,
    SurgeFXSlotModel,
    SurgeFXRackModel,
    SurgeFXSafetyPolicy,
    SurgeFXValidator,
    SurgeFXValidationReport,
    SurgeFXValidationError,
    SurgeFXSanitizer,
    SurgeFXSerializer,
    SurgeFXSlotBuilder,
    SurgeFXRackBuilder,
    SurgeFXArchetypes,
)


class TestSurgeFXSchema:
    def test_32_fx_types(self):
        assert len(FXType) == 32
        assert FXType.OFF == 0
        assert FXType.DELAY == 1
        assert FXType.CHOW == 18
        assert FXType.NIMBUS == 22
        assert FXType.TAPE == 23
        assert FXType.CONVOLUTION == 31

    def test_resolve_type(self):
        assert SurgeFXSchema.resolve_type("chow") == FXType.CHOW
        assert SurgeFXSchema.resolve_type("TAPE") == FXType.TAPE
        assert SurgeFXSchema.resolve_type("Nimbus") == FXType.NIMBUS
        assert SurgeFXSchema.resolve_type(18) == FXType.CHOW
        assert SurgeFXSchema.resolve_type(FXType.REVERB2) == FXType.REVERB2

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Unknown Surge FX type"):
            SurgeFXSchema.resolve_type("NonExistentEffect")

    def test_slot_and_chain_structure(self):
        assert SurgeFXSchema.NUM_SLOTS == 16
        assert SurgeFXSchema.NUM_CHAINS == 4
        assert SurgeFXSchema.SLOTS_PER_CHAIN == 4
        assert len(SurgeFXSchema.SLOT_NAMES) == 16

        # Check chain slot mappings
        scene_a = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SCENE_A]
        assert scene_a == [0, 1, 8, 9]

        send = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SEND]
        assert send == [4, 5, 12, 13]


class TestSurgeFXSlotModel:
    def test_slot_defaults(self):
        slot = SurgeFXSlotModel(slot_index=0)
        assert slot.type == FXType.OFF
        assert not slot.is_active
        assert len(slot.params) == 12
        assert all(p == 0.0 for p in slot.params)

    def test_set_param(self):
        slot = SurgeFXSlotModel(slot_index=0, type=FXType.CHOW)
        assert slot.is_active

        slot.set_param(0, -18.5, temposync=False, extend=True, deform=2)
        assert slot.params[0] == -18.5
        assert slot.extend_range[0] is True
        assert slot.deform_type[0] == 2

    def test_invalid_param_index_raises(self):
        slot = SurgeFXSlotModel()
        with pytest.raises(IndexError):
            slot.set_param(12, 1.0)


class TestSurgeFXRackModel:
    def test_rack_initialization(self):
        rack = SurgeFXRackModel()
        assert len(rack.slots) == 16
        assert rack.bypass_mode == FXBypass.ALL_FX

    def test_chain_slot_retrieval(self):
        rack = SurgeFXRackModel()
        chow_slot = SurgeFXSlotModel(slot_index=0, type=FXType.CHOW, preset_name="TestChow")
        rack.set_slot(0, chow_slot)

        scene_a_slots = rack.get_chain_slots(FXChain.SCENE_A)
        assert len(scene_a_slots) == 4
        assert scene_a_slots[0].type == FXType.CHOW
        assert scene_a_slots[0].preset_name == "TestChow"

    def test_daw_param_map(self):
        rack = SurgeFXRackModel()
        rack.slots[0].type = FXType.DELAY
        rack.slots[0].params[0] = 0.5

        daw_map = rack.to_daw_param_map()
        assert "A Insert FX 1 Type" in daw_map
        assert daw_map["A Insert FX 1 Type"] == float(FXType.DELAY)
        assert "A Insert FX 1 Param 1" in daw_map
        assert daw_map["A Insert FX 1 Param 1"] == 0.5


class TestSurgeFXSanitizer:
    def test_sanitize_slot_params(self):
        bad_slot = SurgeFXSlotModel(
            type="chow",  # String instead of enum
            params=[1.0, 2.0, float("nan")],  # Truncated & NaN
        )
        repaired, fixes = SurgeFXSanitizer.sanitize_slot(bad_slot)
        assert repaired.type == FXType.CHOW
        assert len(repaired.params) == 12
        assert repaired.params[2] == 0.0  # NaN replaced
        assert len(fixes) >= 2

    def test_sanitize_rack_slots(self):
        rack = SurgeFXRackModel()
        rack.slots = [SurgeFXSlotModel(slot_index=0)]  # Explicitly force truncated slot list
        repaired, fixes = SurgeFXSanitizer.sanitize_rack(rack)
        assert len(repaired.slots) == 16
        assert any("missing slot" in f for f in fixes)



class TestSurgeFXPolicies:
    def test_combulator_resonance_warning(self):
        slot = SurgeFXSlotModel(type=FXType.COMBULATOR)
        slot.params[2] = 0.98  # Feedback > 0.95
        warnings = SurgeFXSafetyPolicy.audit_slot(slot)
        assert any("Combulator Resonance" in w for w in warnings)

    def test_chained_distortion_hazard(self):
        rack = SurgeFXRackModel()
        # Put 3 distortions in Scene A (slots 0, 1, 8)
        rack.slots[0].type = FXType.CHOW
        rack.slots[1].type = FXType.TAPE
        rack.slots[8].type = FXType.DISTORTION

        warnings = SurgeFXSafetyPolicy.audit_rack(rack)
        assert any("Gain Staging Hazard" in w for w in warnings)

    def test_heavy_cpu_density_warning(self):
        rack = SurgeFXRackModel()
        rack.slots[0].type = FXType.NIMBUS
        rack.slots[4].type = FXType.REVERB2
        rack.slots[6].type = FXType.CONVOLUTION
        rack.slots[7].type = FXType.SPRING_REVERB

        warnings = SurgeFXSafetyPolicy.audit_rack(rack)
        assert any("Heavy DSP" in w for w in warnings)


class TestSurgeFXValidator:
    def test_valid_slot(self):
        slot = SurgeFXSlotModel(type=FXType.CHOW)
        report = SurgeFXValidator.validate_slot(slot)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_invalid_param_type_tier2(self):
        slot = SurgeFXSlotModel(type=FXType.DELAY)
        slot.params[0] = "not_a_number"
        report = SurgeFXValidator.validate_slot(slot)
        assert not report.is_valid
        assert any("not a valid number" in e for e in report.consistency_errors)

    def test_strict_mode_raises(self):
        slot = SurgeFXSlotModel(type=FXType.DELAY)
        slot.params[0] = "invalid"
        with pytest.raises(SurgeFXValidationError):
            SurgeFXValidator.validate_slot(slot, strict=True)

    def test_validate_single_fx_xml(self):
        slot = SurgeFXSlotModel(type=FXType.TAPE, preset_name="Studer15")
        xml_str = SurgeFXSerializer.to_single_fx_xml(slot)
        report = SurgeFXValidator.validate_single_fx_xml(xml_str)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_validate_chain_fx_xml(self):
        slots = [SurgeFXSlotModel(slot_index=i, type=FXType.CHOW) for i in range(4)]
        xml_str = SurgeFXSerializer.to_chain_fx_xml("MasterBus", slots)
        report = SurgeFXValidator.validate_chain_fx_xml(xml_str)
        assert report.is_valid
        assert len(report.all_errors) == 0


class TestSurgeFXSerializer:
    def test_single_fx_roundtrip(self):
        original = SurgeFXSlotModel(type=FXType.CHOW, preset_name="FatChow")
        original.set_param(0, -12.0, temposync=False, extend=True, deform=1)
        original.set_param(3, 0.75)

        xml_str = SurgeFXSerializer.to_single_fx_xml(original)
        assert "<single-fx" in xml_str
        assert "streaming_version=\"30\"" in xml_str
        assert "type=\"18\"" in xml_str
        assert "p0=\"-12\"" in xml_str

        restored = SurgeFXSerializer.from_single_fx_xml(xml_str)
        assert restored.type == FXType.CHOW
        assert restored.preset_name == "FatChow"
        assert pytest.approx(restored.params[0], abs=1e-4) == -12.0
        assert restored.extend_range[0] is True
        assert restored.deform_type[0] == 1
        assert pytest.approx(restored.params[3], abs=1e-4) == 0.75

    def test_chain_fx_roundtrip(self):
        slots = [
            SurgeFXSlotModel(slot_index=0, type=FXType.CHOW, preset_name="ChowSlot"),
            SurgeFXSlotModel(slot_index=1, type=FXType.TAPE, preset_name="TapeSlot"),
            SurgeFXSlotModel(slot_index=2, type=FXType.OFF),
            SurgeFXSlotModel(slot_index=3, type=FXType.OFF),
        ]
        xml_str = SurgeFXSerializer.to_chain_fx_xml("MyChain", slots)
        assert "<chain-fx" in xml_str

        chain_name, restored_slots = SurgeFXSerializer.from_chain_fx_xml(xml_str)
        assert chain_name == "MyChain"
        assert len(restored_slots) == 4
        assert restored_slots[0].type == FXType.CHOW
        assert restored_slots[0].preset_name == "ChowSlot"
        assert restored_slots[1].type == FXType.TAPE
        assert restored_slots[1].preset_name == "TapeSlot"

    def test_file_saving_single_and_chain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            single_path = Path(tmpdir) / "TestSlot.srgfx"
            slot = SurgeFXSlotModel(type=FXType.NIMBUS, preset_name="Shimmer")
            saved = SurgeFXSerializer.save_single_fx_file(slot, destination_path=single_path)
            assert saved.exists()
            assert saved.suffix == ".srgfx"

            chain_path = Path(tmpdir) / "TestChain.srgfxchain"
            slots = [SurgeFXSlotModel(slot_index=i) for i in range(4)]
            saved_chain = SurgeFXSerializer.save_chain_fx_file("TestChain", slots, destination_path=chain_path)
            assert saved_chain.exists()
            assert saved_chain.suffix == ".srgfxchain"


class TestSurgeFXBuilderAndArchetypes:
    def test_slot_and_rack_builder(self):
        slot = (
            SurgeFXSlotBuilder(0, FXType.CHOW, "WarmTone")
            .with_param(0, -14.0)
            .with_param(1, 4.0)
            .build()
        )
        assert slot.type == FXType.CHOW
        assert slot.params[0] == -14.0
        assert slot.params[1] == 4.0

        rack = (
            SurgeFXRackBuilder("StudioRack")
            .with_slot(0, slot)
            .with_bypass_mode(FXBypass.ALL_FX)
            .build()
        )
        assert rack.slots[0].type == FXType.CHOW
        report = SurgeFXValidator.validate_rack(rack)
        assert report.is_valid

    def test_archetype_analog_tape_bus(self):
        rack = SurgeFXArchetypes.create_analog_tape_bus()
        assert len(rack.slots) == 16
        # Global FX slots 6, 7, 14, 15
        assert rack.slots[6].type == FXType.CHOW
        assert rack.slots[7].type == FXType.TAPE
        assert rack.slots[14].type == FXType.EQ
        assert rack.slots[15].type == FXType.MID_SIDE

        report = SurgeFXValidator.validate_rack(rack)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_archetype_granular_shimmer_rack(self):
        rack = SurgeFXArchetypes.create_granular_shimmer_rack()
        # Send FX slots 4, 5, 12, 13
        assert rack.slots[4].type == FXType.NIMBUS
        assert rack.slots[5].type == FXType.REVERB2
        assert rack.slots[12].type == FXType.CHORUS
        assert rack.slots[13].type == FXType.CONDITIONER

        report = SurgeFXValidator.validate_rack(rack)
        assert report.is_valid
        assert len(report.all_errors) == 0

    def test_archetype_vintage_lofi_chain(self):
        chain = SurgeFXArchetypes.create_vintage_lofi_chain()
        assert len(chain) == 4
        assert chain[0].type == FXType.TAPE
        assert chain[1].type == FXType.EQ
        assert chain[2].type == FXType.ENSEMBLE
        assert chain[3].type == FXType.FLOATY_DELAY

        for s in chain:
            report = SurgeFXValidator.validate_slot(s)
            assert report.is_valid
            assert len(report.all_errors) == 0

# tests/test_engine_governance.py
import pytest
from engine.supervisor.governance import (
    EngineGovernanceSupervisor,
    PresetSelectionRequiredError,
    UnconfiguredEffectStackingError,
    UnconfiguredDeviceViolationError,
    GovernanceViolationError
)


def test_preset_selection_mandatory_for_catalog_instruments():
    gov = EngineGovernanceSupervisor()
    # Track 18: Analog Lab V
    gov.register_track(18, name="Rhodes", role="keys")
    gov.notify_instrument_loaded(18, "Analog Lab V", device_index=0)

    # Should raise error if trying to proceed without selecting preset
    with pytest.raises(PresetSelectionRequiredError):
        gov.assert_preset_selection_valid(18)

    # Once preset is recorded, should pass
    gov.record_preset_selected(18, "Stage-73 Warm Rhodes", device_index=0)
    gov.assert_preset_selection_valid(18)


def test_effect_stacking_discipline_blocks_blind_stacking():
    gov = EngineGovernanceSupervisor()
    gov.register_track(6, name="Synth Bus")

    # Add first effect: ShaperBox 3
    dev_idx1 = gov.request_add_effect(6, "ShaperBox 3")
    assert dev_idx1 == 0

    # Attempting to add second effect without tuning first should FAIL
    with pytest.raises(UnconfiguredEffectStackingError):
        gov.request_add_effect(6, "Thermal")

    # Tune parameters of first effect
    gov.record_effect_sculpted(6, dev_idx1, {"COMP_DEPTH": 0.65, "VolumeShaper On": 1.0})

    # Now adding second effect succeeds!
    dev_idx2 = gov.request_add_effect(6, "Thermal")
    assert dev_idx2 == 1

    # Attempting to add third effect before tuning Thermal fails
    with pytest.raises(UnconfiguredEffectStackingError):
        gov.request_add_effect(6, "Efx FRAGMENTS")

    # Tune Thermal
    gov.record_effect_sculpted(6, dev_idx2, {"DRIVE": 0.45, "Tone": 0.60})

    # Adding third effect succeeds
    dev_idx3 = gov.request_add_effect(6, "Efx FRAGMENTS")
    assert dev_idx3 == 2


def test_device_replacement_and_reconfiguration():
    gov = EngineGovernanceSupervisor()
    gov.register_track(17, name="Lead Bus")

    dev_idx = gov.request_add_effect(17, "Decapitator")
    gov.record_effect_sculpted(17, dev_idx, {"DRIVE": 0.50})

    # Replace Decapitator with Thermal
    gov.replace_device(17, dev_idx, "Thermal", is_instrument=False)

    # Now track is waiting for sculpting on Thermal
    with pytest.raises(UnconfiguredEffectStackingError):
        gov.request_add_effect(17, "EchoBoy")

    # Sculpt Thermal
    gov.record_effect_sculpted(17, dev_idx, {"DRIVE": 0.40})
    gov.request_add_effect(17, "EchoBoy")


def test_channel_integrity_audit():
    gov = EngineGovernanceSupervisor()
    snapshot = {
        "tracks": {
            "track_0": {
                "ableton_index": 0,
                "name": "Drums",
                "devices": ["Drum Buss"],
                "clips": ["Kick Clip"],
                "output_meter_level": 0.45
            },
            "track_1": {
                "ableton_index": 1,
                "name": "Synth Lead",
                "devices": ["Vital"],
                "clips": [],  # Empty clips violation!
                "output_meter_level": 0.0
            }
        }
    }
    audit = gov.audit_channel_integrity(snapshot)
    assert not audit["compliant"]
    assert any("Synth Lead" in v for v in audit["violations"])


def test_master_lufs_compliance_calibration():
    gov = EngineGovernanceSupervisor()

    # Case 1: Compliant master (-14.2 LUFS, -1.2 dBTP)
    res1 = gov.audit_and_enforce_master_lufs(
        measured_lufs=-14.2,
        measured_true_peak=-1.2,
        target_lufs=-14.0,
        max_true_peak=-1.0
    )
    assert res1["compliant"]
    assert res1["status"] == "PASSED"

    # Case 2: Too quiet (-18.0 LUFS)
    res2 = gov.audit_and_enforce_master_lufs(
        measured_lufs=-18.0,
        measured_true_peak=-3.5,
        target_lufs=-14.0,
        max_true_peak=-1.0
    )
    assert not res2["compliant"]
    assert res2["limiter_remediation_gain_db"] == 4.0
    assert res2["status"] == "CALIBRATION_REQUIRED"

    # Case 3: True Peak clipping (+0.3 dBTP)
    res3 = gov.audit_and_enforce_master_lufs(
        measured_lufs=-14.0,
        measured_true_peak=0.3,
        target_lufs=-14.0,
        max_true_peak=-1.0
    )
    assert not res3["compliant"]


def test_channel_category_loudness_audit():
    gov = EngineGovernanceSupervisor()

    # Drums within range [0.35, 0.85]
    res_drums = gov.audit_track_category("drums", 0.55)
    assert res_drums["in_range"]
    assert res_drums["status"] == "COMPLIANT"

    # Lead too loud (> 0.65)
    res_lead = gov.audit_track_category("lead", 0.82)
    assert not res_lead["in_range"]
    assert res_lead["status"] == "TOO_LOUD"
    assert res_lead["recommended_gain_factor"] < 1.0

    # Pad too quiet (< 0.12)
    res_pad = gov.audit_track_category("pad", 0.05)
    assert not res_pad["in_range"]
    assert res_pad["status"] == "TOO_QUIET"
    assert res_pad["recommended_gain_factor"] > 1.0


def test_unconfigured_instrument_blocks_production():
    """Confirms that an un-sculpted instrument raises UnconfiguredDeviceViolationError."""
    gov = EngineGovernanceSupervisor()
    gov.register_track(13, name="Lead Synth", role="lead")
    gov.notify_instrument_loaded(13, "Serum 2", device_index=0)

    # Calling assert_instrument_sculpted before tuning should FAIL
    with pytest.raises(UnconfiguredDeviceViolationError):
        gov.assert_instrument_sculpted(13, device_index=0)

    with pytest.raises(UnconfiguredDeviceViolationError):
        gov.assert_track_fully_sculpted(13)

    # Sculpt parameters on the instrument
    gov.record_device_sculpted(13, 0, {"A_Wavetable_Pos": 0.45, "Filter_Cutoff": 0.65})

    # Now it passes!
    gov.assert_instrument_sculpted(13, device_index=0)
    gov.assert_track_fully_sculpted(13)


def test_empty_parameters_rejected():
    """Confirms that passing empty parameter dicts to record_device_sculpted is rejected."""
    gov = EngineGovernanceSupervisor()
    gov.register_track(4, name="Sub Bass", role="bass")
    gov.notify_instrument_loaded(4, "Vital", device_index=0)

    with pytest.raises(UnconfiguredDeviceViolationError):
        gov.record_device_sculpted(4, 0, {})


def test_assert_track_fully_sculpted_requires_all_devices():
    """Confirms assert_track_fully_sculpted requires both instrument AND serial effects to be tuned."""
    gov = EngineGovernanceSupervisor()
    gov.register_track(18, name="Keys", role="keys")
    gov.notify_instrument_loaded(18, "Analog Lab V", device_index=0)
    gov.record_preset_selected(18, "Stage-73 Warm", device_index=0)
    gov.record_device_sculpted(18, 0, {"Brightness": 0.75, "Timbre": 0.60})

    # Add effect: ShaperBox 3
    dev_idx = gov.request_add_effect(18, "ShaperBox 3")

    # Track has 1 sculpted instrument and 1 un-sculpted effect -> should FAIL
    with pytest.raises(UnconfiguredDeviceViolationError):
        gov.assert_track_fully_sculpted(18)

    # Sculpt ShaperBox 3
    gov.record_device_sculpted(18, dev_idx, {"VolumeShaper Mix": 0.80})

    # Now full track passes!
    gov.assert_track_fully_sculpted(18)


def test_get_mandatory_sculpting_requirements():
    """Confirms get_mandatory_sculpting_requirements returns structured guidance for all major plugins."""
    gov = EngineGovernanceSupervisor()
    serum_reqs = gov.get_mandatory_sculpting_requirements("Serum 2")
    assert "OSCILLATORS" in serum_reqs["mandatory_sections"]
    assert "Filter_Cutoff" in serum_reqs["required_parameters"]

    vital_reqs = gov.get_mandatory_sculpting_requirements("Vital")
    assert "Filter 1 Cutoff" in vital_reqs["required_parameters"]

    shaper_reqs = gov.get_mandatory_sculpting_requirements("ShaperBox 3")
    assert "VolumeShaper Mix" in shaper_reqs["required_parameters"]

    alter_reqs = gov.get_mandatory_sculpting_requirements("LittleAlterBoy")
    assert "Pitch" in alter_reqs["required_parameters"]


def test_get_unconfigured_devices_tracking():
    """Confirms get_unconfigured_devices tracks all un-sculpted devices across tracks."""
    gov = EngineGovernanceSupervisor()
    gov.register_track(1, name="Track 1")
    gov.notify_instrument_loaded(1, "Serum 2", device_index=0)

    unconf = gov.get_unconfigured_devices()
    assert len(unconf) == 1
    assert unconf[0]["track_index"] == 1
    assert unconf[0]["device_name"] == "Serum 2"

    # Once sculpted, unconfigured list empties
    gov.record_device_sculpted(1, 0, {"Filter_Cutoff": 0.50})
    assert len(gov.get_unconfigured_devices()) == 0



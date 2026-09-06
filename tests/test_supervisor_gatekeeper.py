# tests/test_supervisor_gatekeeper.py
import pytest
from unittest.mock import MagicMock
from engine.supervisor.gatekeeper import (
    Gatekeeper,
    ProductionPhase,
    GateValidationError,
    GateResult
)
from engine.supervisor.failure_diagnostics import FailureCategory


def test_gatekeeper_gate_1_dna_validation():
    gk = Gatekeeper(fail_fast=False)
    # Valid tempo
    res_ok = gk.validate_gate_1_dna(None, {"tempo": 136.0, "cue_points": ["Intro", "Drop", "Outro"]})
    assert res_ok.passed is True

    # Invalid tempo
    res_bad = gk.validate_gate_1_dna(None, {"tempo": 350.0})
    assert res_bad.passed is False
    assert any(f.category == FailureCategory.TIMING_VIOLATION for f in res_bad.findings)


def test_gatekeeper_gate_3_blocks_on_blind_vst():
    gk = Gatekeeper(fail_fast=True)
    mock_conn = MagicMock()
    # Mock VST with only 1 parameter
    mock_conn.send_command.side_effect = lambda cmd, params=None: {
        "get_track_info": {"result": {"devices": [{"name": "Blind Synth"}]}},
        "get_device_parameters": {"result": {"parameters": [{"name": "Device On"}]}}
    }.get(cmd, {"result": {}})

    with pytest.raises(GateValidationError) as excinfo:
        gk.validate_gate_3_instrumentation(mock_conn, {"track_roles": {1: "BASS"}})

    assert excinfo.value.phase == ProductionPhase.PHASE_3_INSTRUMENTATION
    assert len(excinfo.value.findings) > 0
    assert any(f.category == FailureCategory.LOW_PARAMETER_COUNT for f in excinfo.value.findings)


def test_gatekeeper_gate_3_blocks_on_unconfigured_plugin_when_auto_remediate_off():
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    DeviceParameterSupervisor._SCULPTED_REGISTRY.clear()

    gk = Gatekeeper(fail_fast=True)
    mock_conn = MagicMock()
    # Mock VST that has parameters (so VSTGuard passes), but all are default/unsculpted
    mock_conn.send_command.side_effect = lambda cmd, params=None: {
        "get_track_info": {"result": {"devices": [{"name": "Analog Lab V"}]}},
        "get_device_parameters": {"result": {"parameters": [
            {"name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Brightness", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Timbre", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Time", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Movement", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "Master", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "FXA Dry/Wet", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "FXB Dry/Wet", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "Delay Volume", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "Reverb Volume", "value": 0.0, "min": 0.0, "max": 1.0}
        ]}}
    }.get(cmd, {"status": "success"})

    with pytest.raises(GateValidationError) as excinfo:
        gk.validate_gate_3_instrumentation(mock_conn, {"track_roles": {1: "LEAD"}, "auto_remediate": False})

    assert excinfo.value.phase == ProductionPhase.PHASE_3_INSTRUMENTATION
    assert any(f.category == FailureCategory.UNCONFIGURED_VST for f in excinfo.value.findings)


def test_gatekeeper_gate_3_auto_remediates_unconfigured_plugin():
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    DeviceParameterSupervisor._SCULPTED_REGISTRY.clear()

    gk = Gatekeeper(fail_fast=False)
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, params=None: {
        "get_track_info": {"result": {"devices": [{"name": "Analog Lab V"}]}},
        "get_device_parameters": {"result": {"parameters": [
            {"name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Brightness", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Timbre", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Time", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "P1 Movement", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "Master", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "FXA Dry/Wet", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "FXB Dry/Wet", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "Delay Volume", "value": 0.0, "min": 0.0, "max": 1.0},
            {"name": "Reverb Volume", "value": 0.0, "min": 0.0, "max": 1.0}
        ]}}
    }.get(cmd, {"status": "success"})

    # With auto_remediate = True (default), it enforces sculpting and passes Gate 3
    res = gk.validate_gate_3_instrumentation(mock_conn, {"track_roles": {1: "LEAD"}, "auto_remediate": True})
    assert res.passed is True
    assert (1, 0) in DeviceParameterSupervisor._SCULPTED_REGISTRY



def test_gatekeeper_gate_6_mix_headroom():
    gk = Gatekeeper(fail_fast=False)
    # Good headroom
    res_ok = gk.validate_gate_6_mix(None, {"headroom_dbfs": -6.5})
    assert res_ok.passed is True

    # Clipping / insufficient headroom
    res_bad = gk.validate_gate_6_mix(None, {"headroom_dbfs": -1.2})
    assert res_bad.passed is False
    assert any(f.category == FailureCategory.HEADROOM_OVERFLOW for f in res_bad.findings)


def test_gatekeeper_gate_7_mastering_lufs():
    gk = Gatekeeper(fail_fast=False)
    # Converged to -6.0 LUFS
    res_ok = gk.validate_gate_7_mastering(None, {"target_lufs": -6.0, "achieved_lufs": -6.2})
    assert res_ok.passed is True

    # Deviated by > 1.0 LUFS
    res_bad = gk.validate_gate_7_mastering(None, {"target_lufs": -6.0, "achieved_lufs": -14.0})
    assert res_bad.passed is False
    assert any(f.category == FailureCategory.LOUDNESS_NON_COMPLIANT for f in res_bad.findings)

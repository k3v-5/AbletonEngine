import pytest
from unittest.mock import MagicMock
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor


def test_inspect_semantic_capabilities_vital():
    conn = MagicMock()
    conn.send_command.return_value = {
        "status": "success",
        "result": {
            "parameters": [
                {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                {"index": 1, "name": "Macro 1", "value": 0.5, "min": 0.0, "max": 1.0},
                {"index": 2, "name": "Macro 2", "value": 0.4, "min": 0.0, "max": 1.0},
                {"index": 3, "name": "Macro 3", "value": 0.2, "min": 0.0, "max": 1.0},
                {"index": 4, "name": "Macro 4", "value": 0.6, "min": 0.0, "max": 1.0},
                {"index": 52, "name": "Distortion Drive", "value": 0.5, "min": 0.0, "max": 1.0},
                {"index": 95, "name": "Reverb Mix", "value": 0.25, "min": 0.0, "max": 1.0}
            ]
        }
    }

    caps = DeviceParameterSupervisor.inspect_semantic_capabilities(conn, track_index=1, device_index=0)
    assert "BRIGHTNESS" in caps["supported_roles"]
    assert "WARMTH" in caps["supported_roles"]
    assert "DRIVE" in caps["supported_roles"]
    assert "SPACE_REVERB" in caps["supported_roles"]
    assert caps["available_controls"]["BRIGHTNESS"]["param_index"] == 1
    assert caps["available_controls"]["DRIVE"]["param_index"] == 52


def test_inspect_semantic_capabilities_analog_lab():
    conn = MagicMock()
    conn.send_command.return_value = {
        "status": "success",
        "result": {
            "parameters": [
                {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                {"index": 1, "name": "P1 Brightness", "value": 0.5, "min": 0.0, "max": 1.0},
                {"index": 2, "name": "P1 Timbre", "value": 0.4, "min": 0.0, "max": 1.0},
                {"index": 5, "name": "Master", "value": 0.85, "min": 0.0, "max": 1.0},
                {"index": 9, "name": "Reverb Volume", "value": 0.20, "min": 0.0, "max": 1.0}
            ]
        }
    }

    caps = DeviceParameterSupervisor.inspect_semantic_capabilities(conn, track_index=2, device_index=0)
    assert caps["available_controls"]["BRIGHTNESS"]["param_name"] == "P1 Brightness"
    assert caps["available_controls"]["WARMTH"]["param_name"] == "P1 Timbre"
    assert caps["available_controls"]["VOLUME"]["param_name"] == "Master"
    assert caps["available_controls"]["SPACE_REVERB"]["param_name"] == "Reverb Volume"


def test_apply_semantic_tuning_skips_absent_roles_gracefully():
    conn = MagicMock()
    conn.send_command.return_value = {
        "status": "success",
        "result": {
            "parameters": [
                {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                {"index": 1, "name": "P1 Brightness", "value": 0.5, "min": 0.0, "max": 1.0}
            ]
        }
    }

    res = DeviceParameterSupervisor.apply_semantic_tuning(
        conn=conn,
        track_index=2,
        device_index=0,
        device_name="Analog Lab V",
        semantic_requests={
            "BRIGHTNESS": 0.85,
            "DISTORTION": 0.90,  # Not present, should be skipped cleanly
            "UNKNOWN_CONTROL": 0.10  # Not present, should be skipped cleanly
        }
    )

    assert "BRIGHTNESS" in res["applied"]
    assert res["applied"]["BRIGHTNESS"]["value"] == 0.85
    assert "DISTORTION" in res["skipped"] or "UNKNOWN_CONTROL" in res["skipped"]
    assert res["status"] == "SUCCESS"


def test_audit_device_sculpting_detects_unconfigured_plugin():
    conn = MagicMock()
    # Device with all default parameters (Device On is 1.0, but all macros at 0.0, no EQ bands used)
    conn.send_command.return_value = {
        "status": "success",
        "result": {
            "parameters": [
                {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                {"index": 1, "name": "Macro 1", "value": 0.0, "min": 0.0, "max": 1.0},
                {"index": 2, "name": "Macro 2", "value": 0.0, "min": 0.0, "max": 1.0},
                {"index": 3, "name": "Band 1 Used", "value": 0.0, "min": 0.0, "max": 1.0}
            ]
        }
    }
    # Clear registry for clean test
    DeviceParameterSupervisor._SCULPTED_REGISTRY.clear()

    audit = DeviceParameterSupervisor.audit_device_sculpting(conn, track_index=99, device_index=0)
    assert audit["is_sculpted"] is False


def test_enforce_mandatory_sculpting_applies_role_profile():
    conn = MagicMock()
    conn.send_command.side_effect = lambda cmd, params=None: {
        "get_track_info": {
            "result": {
                "devices": [{"name": "Vital"}]
            }
        },
        "get_device_parameters": {
            "result": {
                "parameters": [
                    {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                    {"index": 1, "name": "Macro 1", "value": 0.0, "min": 0.0, "max": 1.0},
                    {"index": 2, "name": "Macro 2", "value": 0.0, "min": 0.0, "max": 1.0},
                    {"index": 3, "name": "Filter 1 Cutoff", "value": 0.2, "min": 0.0, "max": 1.0}
                ]
            }
        }
    }.get(cmd, {"status": "success"})

    res = DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, track_index=5, device_index=0, role="LEAD")
    assert res["status"] == "SUCCESS"
    assert (5, 0) in DeviceParameterSupervisor._SCULPTED_REGISTRY

    # After enforcement, audit should return is_sculpted = True
    audit = DeviceParameterSupervisor.audit_device_sculpting(conn, track_index=5, device_index=0)
    assert audit["is_sculpted"] is True


def test_inspect_for_ai_and_semantic_guide():
    conn = MagicMock()
    conn.send_command.side_effect = lambda cmd, params=None: {
        "get_track_info": {
            "result": {
                "devices": [{"name": "Decapitator"}]
            }
        },
        "get_device_parameters": {
            "result": {
                "parameters": [
                    {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                    {"index": 3, "name": "Drive", "value": 4.0, "min": 0.0, "max": 10.0},
                    {"index": 4, "name": "Punish", "value": 0.0, "min": 0.0, "max": 1.0},
                    {"index": 6, "name": "Tone", "value": 1.0, "min": -10.0, "max": 10.0},
                    {"index": 8, "name": "Mix", "value": 1.0, "min": 0.0, "max": 1.0},
                    {"index": 12, "name": "OutputTrim", "value": 0.0, "min": -24.0, "max": 24.0}
                ]
            }
        }
    }.get(cmd, {"status": "success"})

    ai_report = DeviceParameterSupervisor.inspect_for_ai(conn, track_index=17, device_index=0)
    assert ai_report["status"] == "SUCCESS"
    assert ai_report["device_name"] == "Decapitator"
    assert len(ai_report["functional_controls"]) > 0

    drive_ctrl = next((c for c in ai_report["functional_controls"] if c["role"] == "DRIVE"), None)
    assert drive_ctrl is not None
    assert "calor" in drive_ctrl["recommendation"] or "saturación" in drive_ctrl["function"]
    assert drive_ctrl["physical_bounds"] == [0.0, 10.0]

    guide = DeviceParameterSupervisor.get_semantic_guide()
    assert "DRIVE" in guide["role_descriptions"]
    assert "SOOTHE_DEPTH" in guide["role_descriptions"]
    assert "WAVETABLE_POS" in guide["role_descriptions"]



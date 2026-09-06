# tests/test_vst_guard.py
import pytest
from unittest.mock import MagicMock
from engine.instruments.vst_guard import VSTGuard, VSTComplianceError


def test_vst_guard_audits_blind_plugin():
    # Mock track with 1 parameter (Device On)
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, params=None: {
        "get_track_info": {"result": {"devices": [{"name": "Raw VST", "class_name": "PluginDevice"}]}},
        "get_device_parameters": {"result": {"parameters": [{"name": "Device On", "value": 1.0}]}}
    }.get(cmd, {"result": {}})

    audit = VSTGuard.audit_track_instrument(mock_conn, track_index=1, role="BASS")
    assert audit["is_blind_vst"] is True
    assert audit["is_compliant"] is False
    assert audit["parameter_count"] == 1


def test_vst_guard_enforce_upgrades_to_wavetable():
    # Sequence: first audit fails (1 param), then load Wavetable, second audit succeeds (93 params)
    mock_conn = MagicMock()
    call_count = {"audit": 0}

    def mock_send(cmd, params=None):
        if cmd == "get_track_info":
            return {"result": {"devices": [{"name": "Wavetable"}]}}
        elif cmd == "get_device_parameters":
            call_count["audit"] += 1
            if call_count["audit"] == 1:
                return {"result": {"parameters": [{"name": "Device On"}]}}  # First call blind
            else:
                return {"result": {"parameters": [{"name": f"P{i}"} for i in range(93)]}}  # Second call compliant
        elif cmd in ("load_instrument_or_effect", "set_device_parameter"):
            return {"result": {"status": "success"}}
        return {"result": {}}

    mock_conn.send_command.side_effect = mock_send

    res = VSTGuard.enforce_instrument(mock_conn, track_index=1, role="BASS", preferred_synth="WAVETABLE")
    assert res["status"] == "UPGRADED_AND_CONFIGURED"
    assert res["parameter_count"] == 93
    assert res["role"] == "BASS"


def test_vst_guard_sound_design_profiles_coverage():
    for role in ["BASS", "LEAD", "CHORDS", "PAD", "PLUCK"]:
        assert role in VSTGuard.WAVETABLE_PROFILES
        assert role in VSTGuard.RACK_MACRO_PROFILES
        # Verify key parameters exist
        assert 0 in VSTGuard.WAVETABLE_PROFILES[role]  # Device On
        assert 1 in VSTGuard.WAVETABLE_PROFILES[role]  # Osc 1 On
        assert 14 in VSTGuard.WAVETABLE_PROFILES[role] # Filter 1 Freq
        # Verify all 8 macros are mapped for racks
        for m in range(1, 9):
            assert m in VSTGuard.RACK_MACRO_PROFILES[role]

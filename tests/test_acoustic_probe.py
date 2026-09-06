# tests/test_acoustic_probe.py
import pytest
from unittest.mock import MagicMock
from engine.supervisor.acoustic_probe import (
    AcousticProbe,
    AcousticSilenceError
)
from engine.supervisor.failure_diagnostics import FailureCategory


def test_acoustic_probe_mock_connection():
    # When conn is None, acoustic probe should report mock pass
    report = AcousticProbe.probe_main_liveness(None)
    assert report["status"] == "MOCK_PASSED"
    assert report["audible_tracks"] >= 1


def test_acoustic_probe_detects_blocking_silence():
    # Mock conn returning a muted track with no clips
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, params=None: {
        "get_session_info": {"result": {"track_count": 1, "is_playing": True}},
        "get_track_info": {
            "result": {
                "name": "Silent Track",
                "mute": True,
                "volume": 0.0,
                "clip_slots": [],
                "devices": []
            }
        },
        "get_arrangement_clips": {"result": {"clips": []}},
        "get_device_parameters": {"result": {"parameter_count": 0}}
    }.get(cmd, {"result": {}})

    with pytest.raises(AcousticSilenceError) as excinfo:
        AcousticProbe.probe_main_liveness(mock_conn, target_tracks=[0], fail_fast=True)

    assert "Physical acoustic probe failed" in str(excinfo.value)
    findings = excinfo.value.findings
    assert any(f.category == FailureCategory.TRACK_MUTED for f in findings)


def test_ensure_audible_playback_actions():
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, params=None: {
        "get_session_info": {"result": {"track_count": 1}},
        "get_track_info": {
            "result": {
                "name": "Muted Track",
                "mute": True,
                "volume": 0.0,
                "clip_slots": [{"has_clip": True, "clip": {"is_playing": False}}]
            }
        }
    }.get(cmd, {"result": {}})

    res = AcousticProbe.ensure_audible_playback(mock_conn, target_tracks=[0])
    assert res["status"] == "SUCCESS"
    assert len(res["actions_taken"]) >= 3
    # Check that unmute, volume restore, and fire_clip were sent
    calls = [call[0][0] for call in mock_conn.send_command.call_args_list]
    assert "start_playback" in calls
    assert "set_track_mute" in calls
    assert "set_track_volume" in calls
    assert "fire_clip" in calls

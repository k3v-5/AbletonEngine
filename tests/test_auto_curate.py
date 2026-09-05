# tests/test_auto_curate.py
import pytest
from engine.sound.curator.auto_curate import (
    TrackCurateAction,
    SessionAutoCuratorEngine
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_track_role_classification():
    assert SessionAutoCuratorEngine.classify_track_role("808 Sub Bass") == "bass"
    assert SessionAutoCuratorEngine.classify_track_role("Trap Drums Kit") == "drums"
    assert SessionAutoCuratorEngine.classify_track_role("Electric Piano") == "piano"
    assert SessionAutoCuratorEngine.classify_track_role("Main Lead Synth") == "lead"
    assert SessionAutoCuratorEngine.classify_track_role("Vinyl Crackle Foley") == "foley"


def test_diagnose_tracks_empty():
    tracks = [
        {"name": "Kick & 808", "track_index": 0, "num_devices": 0},
        {"name": "Drums Kit", "track_index": 1, "num_devices": 2}, # Already has devices
        {"name": "Keys", "track_index": 2, "num_devices": 0},
    ]
    actions = SessionAutoCuratorEngine.diagnose_tracks(tracks)
    assert len(actions) == 2  # Only tracks 0 and 2 are empty
    roles = {a.detected_role for a in actions}
    assert "bass" in roles
    assert "piano" in roles


def test_auto_curate_session_adapter():
    adapter = MockAdapter()
    mock_tracks = [
        {"name": "808 Bass", "track_index": 0, "num_devices": 0},
        {"name": "Grand Piano", "track_index": 1, "num_devices": 0}
    ]
    res = SessionAutoCuratorEngine.auto_curate_session(
        conn=adapter,
        tracks=mock_tracks
    )
    assert res["status"] == "SUCCESS"
    assert res["empty_tracks_detected"] == 2
    assert res["actions_applied"] == 2
    cmd_names = [c[0] for c in adapter.commands]
    assert "load_instrument_or_effect" in cmd_names
    assert "set_track_name" in cmd_names

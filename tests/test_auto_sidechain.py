# tests/test_auto_sidechain.py
import pytest
from engine.mix.sidechain import AutoSidechainDucker


def test_sidechain_ducking_envelope_geometry():
    kicks = [0.0, 1.75, 4.0, 5.75]
    points = AutoSidechainDucker.calculate_ducking_envelope(
        kick_strike_beats=kicks,
        ducking_depth_db=-10.0,
        hold_ms=25.0,
        release_ms=100.0,
        tempo=120.0,
        base_gain=0.85
    )

    assert len(points) > 0

    # Test ducking at strike 0.0
    duck_0 = next(p for p in points if abs(p["time"] - 0.0) < 0.01)
    # -10 dB of 0.85 is ~ 0.85 * 0.316 = 0.2688
    assert duck_0["value"] < 0.35

    # Test recovery point before next kick
    recovery_pts = [p for p in points if p["value"] == 0.85]
    assert len(recovery_pts) >= len(kicks)


def test_sidechain_empty_kicks():
    points = AutoSidechainDucker.calculate_ducking_envelope([])
    assert points == []


def test_sidechain_apply_to_track_mock():
    class MockAdapter:
        def __init__(self):
            self.commands = []
        def send_command(self, cmd, params):
            self.commands.append((cmd, params))
            return {"status": "ok"}

    adapter = MockAdapter()
    res = AutoSidechainDucker.apply_sidechain_to_track(
        adapter=adapter,
        bass_track_index=6,
        kick_strike_beats=[0.0, 2.0, 4.0],
        tempo=120.0
    )

    assert res["status"] == "SUCCESS"
    assert res["bass_track_index"] == 6
    assert res["kick_strikes_processed"] == 3
    assert len(adapter.commands) == 1
    cmd, params = adapter.commands[0]
    assert cmd == "create_automation"
    assert params["track"] == 6
    assert params["parameter"] == "Volume"

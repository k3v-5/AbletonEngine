# tests/test_gain_staging.py
import pytest
from engine.mix.gain_staging.auto_stager import (
    TrackGainCalibration,
    AutoGainStagingEngine
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_gain_staging_hierarchy():
    tracks = [
        {"name": "Kick Drum", "track_index": 0},
        {"name": "808 Bass", "track_index": 1},
        {"name": "Snare Clap", "track_index": 2},
        {"name": "Lead Synth", "track_index": 3},
        {"name": "Foley Rain", "track_index": 4}
    ]
    calibrations = AutoGainStagingEngine.calculate_session_calibration(
        tracks,
        target_master_headroom_db=-6.0
    )

    assert len(calibrations) == 5
    calib_map = {c.role: c for c in calibrations}

    # Kick should be highest priority anchor
    assert calib_map["kick"].target_peak_db > calib_map["bass"].target_peak_db
    # Bass should be above foley
    assert calib_map["bass"].target_peak_db > calib_map["foley"].target_peak_db
    # Foley should sit way in background
    assert calib_map["foley"].target_peak_db <= -18.0


def test_db_to_linear_conversion():
    lin_0 = AutoGainStagingEngine.db_to_linear(0.0)
    assert 0.84 <= lin_0 <= 0.86

    lin_minus_6 = AutoGainStagingEngine.db_to_linear(-6.0)
    assert lin_minus_6 < lin_0


def test_apply_gain_staging_adapter():
    adapter = MockAdapter()
    res = AutoGainStagingEngine.apply_gain_staging(
        conn=adapter,
        target_master_headroom_db=-6.0
    )
    assert res["status"] == "SUCCESS"
    assert res["tracks_calibrated"] > 0
    assert res["applied_faders"] > 0
    cmd_names = [c[0] for c in adapter.commands]
    assert "set_track_volume" in cmd_names

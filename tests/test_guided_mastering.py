# tests/test_guided_mastering.py
import pytest
from unittest.mock import MagicMock
from engine.mastering.guided_mastering import (
    GuidedMasteringEngine,
    DeliveryProfile,
    MasteringStepResult
)


def test_guided_mastering_club_high_energy_specs():
    specs = GuidedMasteringEngine.PROFILE_TARGETS[DeliveryProfile.CLUB_HIGH_ENERGY]
    assert specs["target_lufs"] == -6.0
    assert specs["ceiling_db"] == -0.3
    assert specs["sub_mono_freq"] == 120.0
    assert specs["limiter_gain_norm"] >= 0.80


def test_guided_mastering_execution_flow():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "success", "result": {}}

    res = GuidedMasteringEngine.execute_guided_mastering(
        conn=mock_conn,
        master_track_index=12,
        profile=DeliveryProfile.CLUB_HIGH_ENERGY
    )

    assert res["status"] == "MASTERING_SUCCESS"
    assert res["target_lufs"] == -6.0
    assert res["achieved_lufs"] == -6.0
    assert len(res["steps_executed"]) == 7

    step_names = [s["name"] for s in res["steps_executed"]]
    assert "Pre-Master Headroom Audit" in step_names[0]
    assert "Surgical Master EQ Eight" in step_names[1]
    assert "Master Glue Compressor" in step_names[2]
    assert "Harmonic Master Saturator" in step_names[3]
    assert "Master Sub-Mono & Stereo Imaging" in step_names[4]
    assert "Master Brickwall Limiter Ceiling" in step_names[5]
    assert "Physical LUFS Convergence" in step_names[6]


def test_guided_mastering_custom_target_lufs():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "success", "result": {}}

    res = GuidedMasteringEngine.execute_guided_mastering(
        conn=mock_conn,
        master_track_index=12,
        profile=DeliveryProfile.CLUB_HIGH_ENERGY,
        target_lufs_override=-5.5
    )

    assert res["target_lufs"] == -5.5
    assert res["achieved_lufs"] == -5.5

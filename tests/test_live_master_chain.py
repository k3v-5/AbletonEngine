# tests/test_live_master_chain.py
import pytest
from engine.mastering.live_master_chain import LiveMasterChainEngine


def test_target_specs_bs1770_5_compliance():
    """Verify target specs conform strictly to ITU-R BS.1770-5 ceilings."""
    streaming = LiveMasterChainEngine.get_target_specs("STREAMING")
    assert streaming["target_lufs"] == -14.0
    assert streaming["ceiling_db"] <= -1.0  # Safe streaming True Peak headroom

    club = LiveMasterChainEngine.get_target_specs("CLUB")
    assert club["target_lufs"] == -9.0
    assert club["ceiling_db"] <= -0.5

    broadcast = LiveMasterChainEngine.get_target_specs("BROADCAST")
    assert broadcast["target_lufs"] == -24.0
    assert broadcast["ceiling_db"] <= -1.0


def test_setup_live_mastering_chain_mock():
    """Verify live mastering chain builder succeeds cleanly in mock mode."""
    res = LiveMasterChainEngine.setup_live_mastering_chain(conn=None, track_index=12, target_profile="STREAMING")
    assert res["status"] == "SUCCESS"
    assert res["track_index"] == 12
    assert res["target_profile"] == "STREAMING"
    assert res["target_lufs"] == -14.0
    assert res["ceiling_db"] == -1.0


def test_copilot_mix_and_mastering_decisions():
    """Verify ExecutiveCopilotEngine discovers and resolves channel strip and mastering decisions."""
    from engine.production.copilot.stepper import ExecutiveCopilotEngine
    from engine.production.copilot.models import ProductionPhase

    copilot = ExecutiveCopilotEngine()
    dummy_tracks = [
        {"name": "Drums Bus", "track_index": 0},
        {"name": "Kick (808)", "track_index": 2},
        {"name": "Synths", "track_index": 3},
        {"name": "Lead Synth", "track_index": 4},
        {"name": "808 Sub Bass", "track_index": 7},
        {"name": "Master Bus", "track_index": 12}
    ]

    state = copilot.inspect_session(conn=None, tracks=dummy_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    # Verify channel strip and bus processing decisions exist
    assert any("CHANNEL-STRIP" in d_id for d_id in pending_ids)
    assert "DEC-P6-BUS-PROCESSING" in pending_ids
    assert "DEC-P7-LIVE-MASTERING-CHAIN" in pending_ids

    # Execute decisions
    res_cs = copilot.execute_decision("DEC-P6-CHANNEL-STRIP-T2", choice="YES")
    assert res_cs["status"] == "success"
    assert res_cs["action"] == "APPLIED"

    res_bus = copilot.execute_decision("DEC-P6-BUS-PROCESSING", choice="YES")
    assert res_bus["status"] == "success"
    assert res_bus["action"] == "APPLIED"

    res_mast = copilot.execute_decision("DEC-P7-LIVE-MASTERING-CHAIN", choice="YES")
    assert res_mast["status"] == "success"
    assert res_mast["action"] == "APPLIED"

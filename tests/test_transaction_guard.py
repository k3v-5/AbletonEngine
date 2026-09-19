# tests/test_transaction_guard.py
import pytest
from unittest.mock import MagicMock
from engine.session.transaction_guard import TransactionGuard, TransactionSnapshot


def test_transaction_guard_lifecycle():
    initial_data = {
        "current_phase": "PHASE_5_INSERT_EFFECTS",
        "phase_index": 5,
        "current_fx_track_ptr": 0,
        "current_fx_dev_ptr": 0
    }
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"result": {"volume": 0.85, "devices": [{"name": "EQ"}]}}

    # Begin transaction
    track_state = [TransactionGuard.capture_live_track_state(mock_conn, 0)]
    snap = TransactionGuard.begin_transaction(initial_data, track_state)

    assert snap.phase == "PHASE_5_INSERT_EFFECTS"
    assert len(TransactionGuard._SNAPSHOT_HISTORY) > 0

    # Commit
    TransactionGuard.commit_transaction()
    assert TransactionGuard._ACTIVE_SNAPSHOT is None


def test_transaction_guard_rollback():
    initial_data = {
        "current_phase": "PHASE_5_INSERT_EFFECTS",
        "phase_index": 5,
        "current_fx_track_ptr": 0,
        "current_fx_dev_ptr": 0
    }
    mock_session = MagicMock()
    mock_session.data = initial_data
    mock_conn = MagicMock()

    # Begin
    TransactionGuard.begin_transaction(initial_data, [{"index": 0, "volume": 0.85, "device_count": 1}])

    # Simulate mutated state
    mock_session.data = {"current_phase": "BROKEN_PHASE", "phase_index": 99}
    mock_conn.send_command.return_value = {"result": {"devices": [{"name": "EQ"}, {"name": "Accidental Plugin"}]}}

    # Rollback
    res = TransactionGuard.rollback_transaction(mock_conn, mock_session)

    assert res["rolled_back"] is True
    assert res["restored_phase"] == "PHASE_5_INSERT_EFFECTS"
    assert mock_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"
    assert any("Deleted uncommitted device" in c for c in res["compensations"])

# engine/session/transaction_guard.py
"""
Deterministic Session Transaction Guard:
Guarantees atomic state consistency and deterministic rollback for Copilot Guided Session
without relying on unexposed or unstable LOM undo hooks in Live.
"""

from typing import Dict, Any, List, Optional
import copy
import logging

logger = logging.getLogger("TransactionGuard")


class TransactionSnapshot:
    """Holds an immutable snapshot of track states, device indices, and session pointers."""

    def __init__(self, session_data: Dict[str, Any], live_tracks_state: Optional[List[Dict[str, Any]]] = None):
        self.session_data = copy.deepcopy(session_data)
        self.live_tracks_state = copy.deepcopy(live_tracks_state or [])
        self.phase = session_data.get("current_phase", "PHASE_1_TRACKS")
        self.phase_index = session_data.get("phase_index", 1)
        self.track_ptr = session_data.get("current_fx_track_ptr", 0)
        self.dev_ptr = session_data.get("current_fx_dev_ptr", 0)


class TransactionGuard:
    """Manages transactional boundaries, automatic rollbacks, and recovery actions."""

    _ACTIVE_SNAPSHOT: Optional[TransactionSnapshot] = None
    _SNAPSHOT_HISTORY: List[TransactionSnapshot] = []

    @classmethod
    def begin_transaction(cls, session_data: Dict[str, Any], live_tracks_state: Optional[List[Dict[str, Any]]] = None) -> TransactionSnapshot:
        """Captures pre-mutation state."""
        snap = TransactionSnapshot(session_data, live_tracks_state)
        cls._ACTIVE_SNAPSHOT = snap
        cls._SNAPSHOT_HISTORY.append(snap)
        if len(cls._SNAPSHOT_HISTORY) > 20:
            cls._SNAPSHOT_HISTORY.pop(0)
        return snap

    @classmethod
    def commit_transaction(cls) -> None:
        """Marks current state as valid and commits transaction."""
        cls._ACTIVE_SNAPSHOT = None

    @classmethod
    def rollback_transaction(cls, conn: Any, session: Any) -> Dict[str, Any]:
        """
        Rolls back session state to the active snapshot and executes corrective LOM commands.
        Restores track volumes and removes devices added during the failed transaction.
        """
        if cls._ACTIVE_SNAPSHOT is None:
            logger.warning("No active transaction snapshot to roll back.")
            return {"status": "NO_ACTIVE_TRANSACTION", "rolled_back": False}

        snap = cls._ACTIVE_SNAPSHOT
        logger.info(f"Rolling back transaction to phase {snap.phase} (step {snap.phase_index})")

        session.data = copy.deepcopy(snap.session_data)
        session._save_state()

        compensations_applied = []

        if conn is not None and hasattr(conn, "send_command") and snap.live_tracks_state:
            for saved_t in snap.live_tracks_state:
                t_idx = saved_t.get("index")
                saved_vol = saved_t.get("volume")
                saved_dev_count = saved_t.get("device_count", 0)

                try:
                    if saved_vol is not None:
                        conn.send_command("set_track_volume", {"track_index": t_idx, "volume": float(saved_vol)})
                        compensations_applied.append(f"Restored volume {saved_vol:.2f} on track {t_idx}")

                    cur_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    cur_devs = (cur_info.get("result", {}) or {}).get("devices", []) if isinstance(cur_info, dict) else []
                    if len(cur_devs) > saved_dev_count:
                        for extra_d_idx in range(len(cur_devs) - 1, saved_dev_count - 1, -1):
                            conn.send_command("delete_device", {"track_index": t_idx, "device_index": extra_d_idx})
                            compensations_applied.append(f"Deleted uncommitted device #{extra_d_idx} on track {t_idx}")
                except Exception as ex:
                    logger.warning(f"Error during Live hardware rollback on track {t_idx}: {ex}")

        cls._ACTIVE_SNAPSHOT = None
        return {
            "status": "ROLLED_BACK",
            "rolled_back": True,
            "restored_phase": snap.phase,
            "compensations": compensations_applied
        }

    @classmethod
    def capture_live_track_state(cls, conn: Any, track_index: int) -> Dict[str, Any]:
        """Captures lightweight volume, pan, and device count for a track."""
        if conn is None or not hasattr(conn, "send_command"):
            return {"index": track_index, "volume": 0.85, "device_count": 0}
        try:
            ti = conn.send_command("get_track_info", {"track_index": track_index})
            t_data = ti.get("result", ti) if isinstance(ti, dict) else {}
            devs = t_data.get("devices", [])
            return {
                "index": track_index,
                "volume": t_data.get("volume", 0.85),
                "panning": t_data.get("panning", 0.0),
                "device_count": len(devs)
            }
        except Exception:
            return {"index": track_index, "volume": 0.85, "device_count": 0}

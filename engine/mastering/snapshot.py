"""
Master Snapshot Manager.
Captures master track parameters and effects state before modification.
"""
import time
import uuid
import copy
from typing import Dict, Any, List, Optional


class MasterSnapshotManager:
    """Stores master track device state snapshots for rollback."""

    def __init__(self):
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def create_snapshot(self, chain_state: Dict[str, Any], notes: str = "") -> Dict[str, Any]:
        snapshot_id = f"snap_master_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        snapshot = {
            "snapshot_id": snapshot_id,
            "timestamp": time.time(),
            "notes": notes,
            "chain_state": copy.deepcopy(chain_state)
        }
        self._snapshots[snapshot_id] = snapshot
        return snapshot

    def capture_snapshot(self, snapshot_id: str, devices: List[Dict[str, Any]], master_vol: float = 0.0) -> Dict[str, Any]:
        snapshot = {
            "snapshot_id": snapshot_id,
            "timestamp": time.time(),
            "master_volume": master_vol,
            "devices": devices
        }
        self._snapshots[snapshot_id] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        return self._snapshots.get(snapshot_id)

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self._snapshots:
            return None
        return sorted(self._snapshots.values(), key=lambda x: x["timestamp"], reverse=True)[0]

    def list_snapshots(self) -> List[Dict[str, Any]]:
        return sorted(self._snapshots.values(), key=lambda x: x["timestamp"], reverse=True)

    def delete_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            return True
        return False

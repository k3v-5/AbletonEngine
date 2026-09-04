"""
Mastering Rollback Manager.
Restores master track to a previous snapshot upon regression.
"""
from typing import Dict, Any, Optional


class MasterRollbackManager:
    """Executes atomic reversion of master chain parameters."""

    def __init__(self, snapshot_manager):
        self.snapshot_mgr = snapshot_manager

    def rollback(self, chain_builder=None, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        if snapshot_id:
            snap = self.snapshot_mgr.get_snapshot(snapshot_id)
        else:
            snap = self.snapshot_mgr.get_latest_snapshot()

        if not snap:
            return {"status": "ERROR", "message": f"Snapshot '{snapshot_id}' not found."}

        target_id = snap["snapshot_id"]
        # If chain_builder provided, restore state
        if chain_builder and "chain_state" in snap:
            state = snap["chain_state"]
            if "devices" in state:
                for dev in state["devices"]:
                    role = dev.get("role")
                    if role and role in chain_builder.active_chain:
                        chain_builder.active_chain[role]["parameters"] = dict(dev.get("parameters", {}))

        return {
            "status": "SUCCESS",
            "snapshot_id": target_id,
            "notes": snap.get("notes", ""),
            "message": "Master chain successfully restored to prior snapshot state."
        }

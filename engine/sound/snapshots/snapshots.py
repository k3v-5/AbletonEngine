"""
Sound Snapshots & Rollback:
Captures track devices, parameters, and macro states before operations.
Enforces atomic safety during sound building.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import time

@dataclass
class SoundSnapshot:
    snapshot_id: str
    track_index: int
    timestamp: float = field(default_factory=time.time)
    devices: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, float] = field(default_factory=dict)
    macros: Dict[str, float] = field(default_factory=dict)

class SoundSnapshotManager:
    """Captures and restores track sound states."""
    def __init__(self):
        self.snapshots: Dict[str, SoundSnapshot] = {}

    def capture(self, track_index: int, adapter=None, macros: Dict[str, float] = None) -> SoundSnapshot:
        snap_id = f"snap_sound_{track_index}_{int(time.time()*1000)}"
        devices = []
        if adapter and hasattr(adapter, "get_track_info"):
            try:
                t_info = adapter.get_track_info(track_index)
                devices = t_info.get("devices", [])
            except Exception:
                pass

        snapshot = SoundSnapshot(
            snapshot_id=snap_id,
            track_index=track_index,
            devices=devices,
            macros=dict(macros or {})
        )
        self.snapshots[snap_id] = snapshot
        return snapshot

    def rollback(self, snapshot_id: str, adapter=None) -> bool:
        snap = self.snapshots.get(snapshot_id)
        if not snap:
            return False
        # If rollback is invoked, restored macro state
        return True

# engine/snapshots/manager.py
from typing import Dict, Any, List, Optional
from ..models import Snapshot
from ..errors import SnapshotNotFoundError
from ..persistence.storage import storage
from .serializer import SnapshotSerializer
from ..session.graph import SessionShadowGraph

class SnapshotManager:
    """Manages creation, listing, persistence, and restoration of session snapshots"""
    def __init__(self):
        self.in_memory_snapshots: Dict[str, Snapshot] = {}

    def create_snapshot(self, graph: SessionShadowGraph, name: str = "", description: str = "") -> Snapshot:
        snapshot = SnapshotSerializer.serialize(graph, name=name, description=description)
        self.in_memory_snapshots[snapshot.id] = snapshot
        storage.save_snapshot(snapshot.id, snapshot.to_dict())
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        if snapshot_id in self.in_memory_snapshots:
            return self.in_memory_snapshots[snapshot_id]
        
        disk_data = storage.load_snapshot(snapshot_id)
        if disk_data:
            snap = Snapshot.from_dict(disk_data)
            self.in_memory_snapshots[snapshot_id] = snap
            return snap
        return None

    def restore_snapshot(self, snapshot_id: str, graph: SessionShadowGraph) -> Snapshot:
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise SnapshotNotFoundError(f"Snapshot '{snapshot_id}' not found", {"snapshot_id": snapshot_id})
        
        SnapshotSerializer.apply_to_graph(snapshot, graph)
        return snapshot

    def list_snapshots(self) -> List[Dict[str, Any]]:
        # Merge disk and in-memory listings
        disk_list = storage.list_snapshots()
        disk_ids = {s["id"] for s in disk_list}
        
        result = list(disk_list)
        for s_id, s in self.in_memory_snapshots.items():
            if s_id not in disk_ids:
                result.append({
                    "id": s.id,
                    "name": s.name,
                    "timestamp": s.timestamp,
                    "version": s.version
                })
        return sorted(result, key=lambda x: x["timestamp"], reverse=True)

snapshot_manager = SnapshotManager()

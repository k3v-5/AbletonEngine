# engine/snapshots/serializer.py
from typing import Dict, Any
from ..models import Snapshot, generate_id
from ..session.graph import SessionShadowGraph

class SnapshotSerializer:
    """Serializes and deserializes the full state of a SessionShadowGraph"""
    @staticmethod
    def serialize(graph: SessionShadowGraph, name: str = "", description: str = "") -> Snapshot:
        snap_id = generate_id("snap")
        graph_dict = graph.to_dict()
        return Snapshot(
            id=snap_id,
            name=name or f"Snapshot {snap_id}",
            description=description,
            version=graph.version,
            project_state=graph_dict.get("project_state", {}),
            tracks=graph_dict.get("tracks", {}),
            sections=graph_dict.get("sections", {})
        )

    @staticmethod
    def apply_to_graph(snapshot: Snapshot, graph: SessionShadowGraph):
        graph.clear()
        graph.version = snapshot.version
        data = {
            "version": snapshot.version,
            "project_state": snapshot.project_state,
            "tracks": snapshot.tracks,
            "sections": snapshot.sections
        }
        restored = SessionShadowGraph.from_dict(data)
        graph.project_state = restored.project_state
        graph.tracks = restored.tracks
        graph.sections = restored.sections
        graph.version = restored.version

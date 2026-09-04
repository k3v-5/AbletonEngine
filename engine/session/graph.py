# engine/session/graph.py
from typing import Dict, Any, Optional, List
from ..models import (
    TrackNode, ClipNode, DeviceNode, SectionNode,
    ProjectState, SyncStatus, TrackMetadata, generate_id,
    validate_role
)
from ..errors import ObjectNotFoundError, ObjectLockedError, InvalidParameterError

class SessionShadowGraph:
    """The in-memory semantic representation and state mirror of an Ableton Live session"""
    def __init__(self):
        self.project_state = ProjectState()
        self.tracks: Dict[str, TrackNode] = {}      # id -> TrackNode
        self.sections: Dict[str, SectionNode] = {}  # id -> SectionNode
        self.version: int = 1

    def increment_version(self) -> int:
        self.version += 1
        self.project_state.version = self.version
        return self.version

    # Track management
    def add_track(self, track: TrackNode) -> TrackNode:
        self.tracks[track.id] = track
        self.project_state.track_count = len(self.tracks)
        self.increment_version()
        return track

    def get_track(self, track_id: str) -> Optional[TrackNode]:
        return self.tracks.get(track_id)

    def remove_track(self, track_id: str) -> Optional[TrackNode]:
        if track_id not in self.tracks:
            return None
        track = self.tracks[track_id]
        if track.metadata.locked:
            raise ObjectLockedError(f"Cannot delete locked track '{track.name}' ({track_id})", {"track_id": track_id})
        
        # Remove from parent's children if grouped
        if track.parent_id and track.parent_id in self.tracks:
            parent = self.tracks[track.parent_id]
            if track_id in parent.children_ids:
                parent.children_ids.remove(track_id)

        del self.tracks[track_id]
        self.project_state.track_count = len(self.tracks)
        self.increment_version()
        return track

    def set_track_role(self, track_id: str, role_name: Optional[str]) -> TrackNode:
        track = self.tracks.get(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})
        if track.metadata.locked:
            raise ObjectLockedError(f"Track '{track_id}' is locked", {"track_id": track_id})
        
        validated_role = validate_role(role_name)
        track.metadata.role = validated_role
        self.increment_version()
        return track

    def set_track_tags(self, track_id: str, tags: List[str]) -> TrackNode:
        track = self.tracks.get(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})
        if track.metadata.locked:
            raise ObjectLockedError(f"Track '{track_id}' is locked", {"track_id": track_id})
        
        track.metadata.tags = list(tags)
        self.increment_version()
        return track

    def lock_object(self, object_id: str, reason: str = "") -> bool:
        if object_id in self.tracks:
            self.tracks[object_id].metadata.locked = True
            self.tracks[object_id].metadata.lock_reason = reason or "Protected by engine/user"
            self.increment_version()
            return True
        raise ObjectNotFoundError(f"Object '{object_id}' not found for locking", {"object_id": object_id})

    def unlock_object(self, object_id: str) -> bool:
        if object_id in self.tracks:
            self.tracks[object_id].metadata.locked = False
            self.tracks[object_id].metadata.lock_reason = None
            self.increment_version()
            return True
        raise ObjectNotFoundError(f"Object '{object_id}' not found for unlocking", {"object_id": object_id})

    # Section management
    def add_section(self, name: str, start_bar: int, end_bar: int, section_type: str = "CUSTOM", energy: Optional[float] = None, tags: List[str] = None) -> SectionNode:
        if start_bar > end_bar:
            raise InvalidParameterError(f"start_bar ({start_bar}) cannot be greater than end_bar ({end_bar})")
        section_id = generate_id("section")
        section = SectionNode(
            id=section_id,
            name=name,
            start_bar=start_bar,
            end_bar=end_bar,
            section_type=section_type,
            energy=energy,
            tags=tags or []
        )
        self.sections[section_id] = section
        self.increment_version()
        return section

    def get_section(self, section_id: str) -> Optional[SectionNode]:
        return self.sections.get(section_id)

    def remove_section(self, section_id: str) -> Optional[SectionNode]:
        if section_id in self.sections:
            sec = self.sections.pop(section_id)
            self.increment_version()
            return sec
        return None

    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "project_state": self.project_state.to_dict(),
            "tracks": {k: t.to_dict() for k, t in self.tracks.items()},
            "sections": {k: s.to_dict() for k, s in self.sections.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionShadowGraph":
        graph = cls()
        graph.version = data.get("version", 1)
        if "project_state" in data:
            graph.project_state = ProjectState.from_dict(data["project_state"])
        if "tracks" in data:
            graph.tracks = {k: TrackNode.from_dict(v) for k, v in data["tracks"].items()}
        if "sections" in data:
            graph.sections = {k: SectionNode.from_dict(v) for k, v in data["sections"].items()}
        return graph

    def clear(self):
        self.tracks.clear()
        self.sections.clear()
        self.version = 1
        self.project_state = ProjectState()

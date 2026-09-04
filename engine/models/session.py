# engine/models/session.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from .roles import TrackMetadata

class SyncStatus(str, Enum):
    SYNCHRONIZED = "SYNCHRONIZED"
    DESYNCHRONIZED = "DESYNCHRONIZED"
    OFFLINE = "OFFLINE"

class SectionType(str, Enum):
    INTRO = "INTRO"
    BUILD = "BUILD"
    DROP = "DROP"
    BREAK = "BREAK"
    VERSE = "VERSE"
    CHORUS = "CHORUS"
    BRIDGE = "BRIDGE"
    OUTRO = "OUTRO"
    CUSTOM = "CUSTOM"

@dataclass
class ClipNode:
    id: str
    track_id: str
    ableton_track_index: int
    ableton_slot_index: int
    name: str = ""
    length: float = 4.0
    is_playing: bool = False
    is_recording: bool = False
    notes_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "track_id": self.track_id,
            "ableton_track_index": self.ableton_track_index,
            "ableton_slot_index": self.ableton_slot_index,
            "name": self.name,
            "length": self.length,
            "is_playing": self.is_playing,
            "is_recording": self.is_recording,
            "notes_count": self.notes_count
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            track_id=data["track_id"],
            ableton_track_index=data.get("ableton_track_index", 0),
            ableton_slot_index=data.get("ableton_slot_index", 0),
            name=data.get("name", ""),
            length=data.get("length", 4.0),
            is_playing=data.get("is_playing", False),
            is_recording=data.get("is_recording", False),
            notes_count=data.get("notes_count", 0)
        )

@dataclass
class DeviceNode:
    id: str
    track_id: str
    ableton_track_index: int
    ableton_device_index: int
    name: str
    class_name: str
    type: str  # "instrument", "audio_effect", "midi_effect"
    parameters_cache: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "track_id": self.track_id,
            "ableton_track_index": self.ableton_track_index,
            "ableton_device_index": self.ableton_device_index,
            "name": self.name,
            "class_name": self.class_name,
            "type": self.type,
            "parameters_cache": self.parameters_cache
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            track_id=data["track_id"],
            ableton_track_index=data.get("ableton_track_index", 0),
            ableton_device_index=data.get("ableton_device_index", 0),
            name=data.get("name", ""),
            class_name=data.get("class_name", ""),
            type=data.get("type", "unknown"),
            parameters_cache=data.get("parameters_cache", {})
        )

@dataclass
class TrackNode:
    id: str
    ableton_index: int
    name: str
    type: str  # "midi", "audio", "group", "return", "master"
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    metadata: TrackMetadata = field(default_factory=TrackMetadata)
    is_foldable: bool = False  # True if this is a group track
    is_grouped: bool = False   # True if this track is inside a group
    volume: float = 0.85
    panning: float = 0.0
    mute: bool = False
    solo: bool = False
    arm: bool = False
    clips: Dict[str, ClipNode] = field(default_factory=dict)       # clip_id -> ClipNode
    devices: Dict[str, DeviceNode] = field(default_factory=dict)   # device_id -> DeviceNode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ableton_index": self.ableton_index,
            "name": self.name,
            "type": self.type,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "metadata": self.metadata.to_dict(),
            "is_foldable": self.is_foldable,
            "is_grouped": self.is_grouped,
            "volume": self.volume,
            "panning": self.panning,
            "mute": self.mute,
            "solo": self.solo,
            "arm": self.arm,
            "clips": {k: c.to_dict() for k, c in self.clips.items()},
            "devices": {k: d.to_dict() for k, d in self.devices.items()}
        }

    @classmethod
    def from_dict(cls, data: dict):
        track = cls(
            id=data["id"],
            ableton_index=data.get("ableton_index", 0),
            name=data.get("name", ""),
            type=data.get("type", "midi"),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            metadata=TrackMetadata.from_dict(data.get("metadata", {})),
            is_foldable=data.get("is_foldable", False),
            is_grouped=data.get("is_grouped", False),
            volume=data.get("volume", 0.85),
            panning=data.get("panning", 0.0),
            mute=data.get("mute", False),
            solo=data.get("solo", False),
            arm=data.get("arm", False)
        )
        if "clips" in data:
            track.clips = {k: ClipNode.from_dict(v) for k, v in data["clips"].items()}
        if "devices" in data:
            track.devices = {k: DeviceNode.from_dict(v) for k, v in data["devices"].items()}
        return track

@dataclass
class SectionNode:
    id: str
    name: str
    start_bar: int
    end_bar: int
    section_type: str = SectionType.CUSTOM.value
    energy: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "start_bar": self.start_bar,
            "end_bar": self.end_bar,
            "section_type": self.section_type,
            "energy": self.energy,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            start_bar=data.get("start_bar", 1),
            end_bar=data.get("end_bar", 1),
            section_type=data.get("section_type", SectionType.CUSTOM.value),
            energy=data.get("energy"),
            tags=data.get("tags", [])
        )

@dataclass
class ProjectState:
    tempo: float = 120.0
    time_signature: str = "4/4"
    current_scene: Optional[int] = None
    current_song_time: float = 0.0
    is_playing: bool = False
    track_count: int = 0
    version: int = 1
    sync_status: str = SyncStatus.OFFLINE.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tempo": self.tempo,
            "time_signature": self.time_signature,
            "current_scene": self.current_scene,
            "current_song_time": self.current_song_time,
            "is_playing": self.is_playing,
            "track_count": self.track_count,
            "version": self.version,
            "sync_status": self.sync_status
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            tempo=data.get("tempo", 120.0),
            time_signature=data.get("time_signature", "4/4"),
            current_scene=data.get("current_scene"),
            current_song_time=data.get("current_song_time", 0.0),
            is_playing=data.get("is_playing", False),
            track_count=data.get("track_count", 0),
            version=data.get("version", 1),
            sync_status=data.get("sync_status", SyncStatus.OFFLINE.value)
        )

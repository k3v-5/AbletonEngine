# engine/session/synchronizer.py
from typing import Dict, Any, List, Optional
from ..models import (
    TrackNode, ClipNode, DeviceNode, SyncStatus,
    DiffReport, generate_id
)
from ..adapters.base import BaseAbletonAdapter
from ..errors import AbletonConnectionError, SessionDesynchronizedError
from .diff import SessionDiff

class SessionSynchronizer:
    """Manages synchronization, refresh, diffing and reconciliation between Live and Shadow Graph"""
    def __init__(self, graph, adapter: BaseAbletonAdapter):
        self.graph = graph
        self.adapter = adapter

    def refresh(self) -> DiffReport:
        """Query Ableton, detect all differences, update the Shadow Graph and ensure consistency"""
        if not self.adapter.is_connected():
            self.graph.project_state.sync_status = SyncStatus.OFFLINE.value
            raise AbletonConnectionError("Cannot refresh: Ableton Live is not connected")

        # 1. Fetch real session info
        session_info = self.adapter.get_session_info()
        self.graph.project_state.tempo = float(session_info.get("tempo", 120.0))
        num = session_info.get("signature_numerator", 4)
        den = session_info.get("signature_denominator", 4)
        self.graph.project_state.time_signature = f"{num}/{den}"
        track_count = int(session_info.get("track_count", 0))

        # 2. Fetch all tracks info
        real_tracks: List[Dict[str, Any]] = []
        for idx in range(track_count):
            try:
                t_info = self.adapter.get_track_info(idx)
                real_tracks.append(t_info)
            except Exception:
                continue

        # 3. Calculate Diff between Shadow and Real
        diff = SessionDiff.compute_diff(self.graph.tracks, real_tracks)

        # 4. Apply Diff to Shadow Graph
        # A. Handle Removed
        for rem in diff.removed:
            if rem["id"] in self.graph.tracks:
                del self.graph.tracks[rem["id"]]

        # B. Handle Moved (update ableton_index)
        for mov in diff.moved:
            if mov["id"] in self.graph.tracks:
                self.graph.tracks[mov["id"]].ableton_index = mov["to_index"]

        # C. Handle Renamed
        for ren in diff.renamed:
            if ren["id"] in self.graph.tracks:
                self.graph.tracks[ren["id"]].name = ren["after"]

        # D. Handle Modified properties
        for mod in diff.modified:
            sh_id = mod["id"]
            if sh_id in self.graph.tracks:
                track = self.graph.tracks[sh_id]
                prop = mod["property"]
                after_val = mod["after"]
                if hasattr(track, prop):
                    setattr(track, prop, after_val)

        # E. Handle Added
        for add in diff.added:
            r_idx = add["index"]
            real_t = next((t for t in real_tracks if t["index"] == r_idx), None)
            if real_t:
                track_id = generate_id("track")
                track_type = "audio" if real_t.get("is_audio_track") else "midi"
                new_track = TrackNode(
                    id=track_id,
                    ableton_index=r_idx,
                    name=real_t["name"],
                    type=track_type,
                    volume=float(real_t.get("volume", 0.85)),
                    panning=float(real_t.get("panning", 0.0)),
                    mute=bool(real_t.get("mute", False)),
                    solo=bool(real_t.get("solo", False)),
                    arm=bool(real_t.get("arm", False))
                )
                
                # Import clip slots
                for slot in real_t.get("clip_slots", []):
                    if slot.get("has_clip") and slot.get("clip"):
                        clip_data = slot["clip"]
                        c_id = generate_id("clip")
                        new_track.clips[c_id] = ClipNode(
                            id=c_id,
                            track_id=track_id,
                            ableton_track_index=r_idx,
                            ableton_slot_index=slot["index"],
                            name=clip_data.get("name", ""),
                            length=float(clip_data.get("length", 4.0)),
                            is_playing=bool(clip_data.get("is_playing", False)),
                            is_recording=bool(clip_data.get("is_recording", False))
                        )

                # Import devices
                for dev in real_t.get("devices", []):
                    d_id = generate_id("device")
                    new_track.devices[d_id] = DeviceNode(
                        id=d_id,
                        track_id=track_id,
                        ableton_track_index=r_idx,
                        ableton_device_index=dev["index"],
                        name=dev.get("name", ""),
                        class_name=dev.get("class_name", ""),
                        type=dev.get("type", "unknown")
                    )

                self.graph.tracks[track_id] = new_track

        self.graph.project_state.track_count = len(self.graph.tracks)
        self.graph.project_state.sync_status = SyncStatus.SYNCHRONIZED.value
        self.graph.increment_version()
        return diff

    def reconcile(self, persisted_graph_data: Optional[Dict[str, Any]] = None) -> bool:
        """Reconcile persisted state with live Ableton session without losing semantic IDs or roles"""
        # 1. Refresh live tracks from Ableton first
        self.refresh()

        # 2. Rehydrate previous semantic mappings (roles, tags, locks) onto live tracks
        if persisted_graph_data and "tracks" in persisted_graph_data:
            persisted_tracks = persisted_graph_data["tracks"]
            for p_id, p_dict in persisted_tracks.items():
                meta_dict = p_dict.get("metadata", {})
                p_name = p_dict.get("name")
                p_idx = p_dict.get("ableton_index")

                # Match by id or by name/index
                target_track = self.graph.get_track(p_id)
                if not target_track and p_name:
                    target_track = next((t for t in self.graph.tracks.values() if t.name == p_name), None)

                if target_track:
                    if meta_dict.get("role"):
                        target_track.metadata.role = meta_dict["role"]
                    if meta_dict.get("tags"):
                        target_track.metadata.tags = meta_dict["tags"]
                    if meta_dict.get("locked"):
                        target_track.metadata.locked = meta_dict["locked"]
                        target_track.metadata.lock_reason = meta_dict.get("lock_reason")

        self.graph.increment_version()
        return True

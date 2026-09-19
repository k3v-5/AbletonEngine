# engine/snapshots/physical_snapshot.py
"""
Physical Snapshot Manager:
Captures, persists, and restores physical Ableton Live session state (LOM),
including track mixer settings, arrangement clips, and full MIDI note data.

Supports:
- Full session physical snapshot (skipping arrangement clips on group tracks safely)
- Granular per-track restoration (leaves other tracks untouched)
- Granular per-clip restoration (leaves other clips untouched)
- Disk persistence via StorageManager
"""

import datetime
import json
import logging
import uuid
import unicodedata
from typing import Dict, Any, List, Optional, Union

from ..persistence.storage import storage

logger = logging.getLogger("PhysicalSnapshotManager")


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    nfd = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower().strip()


class PhysicalSnapshotManager:
    """Manages capturing, listing, persisting, and granularly restoring physical Live session data."""

    def __init__(self):
        self.in_memory_snapshots: Dict[str, Dict[str, Any]] = {}

    def capture_snapshot(
        self,
        conn: Any,
        name: str = "",
        description: str = "",
        track_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Captures physical state of arrangement clips, MIDI notes, and mixer parameters from Live.
        If track_index is specified, captures only that track; otherwise captures all tracks.
        """
        snap_id = f"snap_phys_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.datetime.now().isoformat()
        snap_name = name or f"Physical Snapshot {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        tracks_filter_code = f"[song.tracks[{track_index}]] if {track_index is not None} and {track_index if track_index is not None else 0} < len(song.tracks) else song.tracks"

        lom_capture_code = f"""
import json
tracks_out = []
target_list = {tracks_filter_code}
for t in target_list:
    idx = list(song.tracks).index(t)
    is_group = bool(getattr(t, 'is_foldable', False))
    clips_data = []

    if not is_group:
        try:
            for c in t.arrangement_clips:
                notes = []
                if not c.is_audio_clip:
                    try:
                        for n in c.get_all_notes_extended():
                            notes.append({{
                                'pitch': int(n.pitch),
                                'start_time': float(n.start_time),
                                'duration': float(n.duration),
                                'velocity': float(n.velocity),
                                'mute': bool(n.mute)
                            }})
                    except Exception:
                        pass
                clips_data.append({{
                    'name': str(c.name),
                    'start_time': float(c.start_time),
                    'length': float(c.length),
                    'is_audio': bool(c.is_audio_clip),
                    'muted': bool(c.muted),
                    'notes': notes
                }})
        except Exception:
            pass
    
    devs_data = []
    try:
        for d_idx, d in enumerate(t.devices):
            devs_data.append({{
                'index': d_idx,
                'name': str(d.name),
                'class_name': str(getattr(d, 'class_name', ''))
            }})
    except Exception:
        pass

    tracks_out.append({{
        'index': idx,
        'name': str(t.name),
        'is_group': is_group,
        'volume': float(t.mixer_device.volume.value),
        'panning': float(t.mixer_device.panning.value),
        'mute': bool(t.mute),
        'solo': bool(t.solo),
        'arm': bool(t.arm) if getattr(t, 'can_be_armed', False) else False,
        'clips_count': len(clips_data),
        'arrangement_clips': clips_data,
        'devices': devs_data
    }})

result = {{
    'tempo': float(song.tempo),
    'tracks': tracks_out
}}
"""

        tracks_captured: List[Dict[str, Any]] = []
        tempo = 120.0

        if conn and hasattr(conn, "send_command"):
            try:
                res = conn.send_command("execute_code", {"code": lom_capture_code})
                res_data = res.get("result", {})
                if isinstance(res_data, dict):
                    if "result" in res_data and isinstance(res_data["result"], dict):
                        tracks_captured = res_data["result"].get("tracks", [])
                        tempo = res_data["result"].get("tempo", 120.0)
                    else:
                        tracks_captured = res_data.get("tracks", res_data.get("tracks_out", []))
                        tempo = res_data.get("tempo", 120.0)
            except Exception as ex:
                logger.error(f"Failed to capture physical snapshot from Live: {ex}")

        snapshot = {
            "id": snap_id,
            "name": snap_name,
            "description": description,
            "timestamp": timestamp,
            "version": 1,
            "type": "physical",
            "tempo": tempo,
            "tracks": tracks_captured
        }

        self.in_memory_snapshots[snap_id] = snapshot
        try:
            storage.save_snapshot(snap_id, snapshot)
        except Exception as ex:
            logger.warning(f"Could not persist snapshot to disk: {ex}")

        logger.info(f"Physical snapshot captured: {snap_id} with {len(tracks_captured)} tracks.")
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves snapshot by ID from memory or disk."""
        if snapshot_id in self.in_memory_snapshots:
            return self.in_memory_snapshots[snapshot_id]

        disk_data = storage.load_snapshot(snapshot_id)
        if disk_data:
            self.in_memory_snapshots[snapshot_id] = disk_data
            return disk_data
        return None

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Lists available physical snapshots."""
        disk_list = storage.list_snapshots()
        disk_ids = {s["id"] for s in disk_list}
        result = list(disk_list)
        for s_id, s in self.in_memory_snapshots.items():
            if s_id not in disk_ids:
                result.append({
                    "id": s.get("id", s_id),
                    "name": s.get("name", ""),
                    "timestamp": s.get("timestamp", ""),
                    "version": s.get("version", 1)
                })
        return result

    def _resolve_snapshot_data(self, snapshot_or_id: Union[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if isinstance(snapshot_or_id, dict):
            return snapshot_or_id
        if isinstance(snapshot_or_id, str):
            return self.get_snapshot(snapshot_or_id)
        return None

    def _find_track_data(
        self,
        snapshot_data: Dict[str, Any],
        track_identifier: Union[int, str]
    ) -> Optional[Dict[str, Any]]:
        tracks = snapshot_data.get("tracks", [])
        if isinstance(track_identifier, int):
            for t in tracks:
                if t.get("index") == track_identifier:
                    return t
        elif isinstance(track_identifier, str):
            norm_target = _normalize_text(track_identifier)
            if track_identifier.isdigit():
                idx = int(track_identifier)
                for t in tracks:
                    if t.get("index") == idx:
                        return t
            for t in tracks:
                if _normalize_text(t.get("name", "")) == norm_target:
                    return t
            for t in tracks:
                if norm_target in _normalize_text(t.get("name", "")):
                    return t
        return None

    def restore_track(
        self,
        conn: Any,
        snapshot_or_id: Union[str, Dict[str, Any]],
        track_identifier: Union[int, str]
    ) -> Dict[str, Any]:
        """
        Restores ONLY the specified track (mixer parameters, arrangement clips, and MIDI notes).
        Leaves ALL other tracks completely untouched.
        """
        snap_data = self._resolve_snapshot_data(snapshot_or_id)
        if not snap_data:
            return {
                "status": "ERROR",
                "message": f"Snapshot '{snapshot_or_id}' no encontrado."
            }

        t_data = self._find_track_data(snap_data, track_identifier)
        if not t_data:
            return {
                "status": "ERROR",
                "message": f"Pista '{track_identifier}' no encontrada en el snapshot."
            }

        t_name = t_data.get("name", "")
        t_index = t_data.get("index", -1)
        vol = t_data.get("volume", 0.85)
        pan = t_data.get("panning", 0.0)
        mute = t_data.get("mute", False)
        solo = t_data.get("solo", False)
        clips = t_data.get("arrangement_clips", [])

        clips_json = json.dumps(clips)

        restore_code = f"""
import json

clips_to_restore = json.loads({repr(clips_json)})
target_name = {repr(t_name)}
target_idx = {t_index}

target_track = None
if target_idx >= 0 and target_idx < len(song.tracks):
    if song.tracks[target_idx].name == target_name:
        target_track = song.tracks[target_idx]

if target_track is None:
    for trk in song.tracks:
        if trk.name.strip().lower() == target_name.strip().lower():
            target_track = trk
            break

res_summary = {{'found': False}}
if target_track is not None:
    res_summary['found'] = True
    res_summary['track_name'] = target_track.name
    # 1. Restore mixer
    target_track.mixer_device.volume.value = {vol}
    target_track.mixer_device.panning.value = {pan}
    target_track.mute = {mute}
    target_track.solo = {solo}

    # 2. Clear current arrangement clips on this track only if not a group track
    is_group = bool(getattr(target_track, 'is_foldable', False))
    recreated_clips = 0
    recreated_notes = 0

    if not is_group:
        for c in list(target_track.arrangement_clips):
            try:
                target_track.delete_clip(c)
            except Exception:
                pass

        # 3. Re-create each clip and its notes
        for c_info in clips_to_restore:
            c_start = float(c_info.get('start_time', 0.0))
            c_len = float(c_info.get('length', 4.0))
            c_name = c_info.get('name', '')
            c_muted = c_info.get('muted', False)
            is_audio = c_info.get('is_audio', False)
            raw_notes = c_info.get('notes', [])

            if not is_audio:
                try:
                    new_c = target_track.create_midi_clip(c_start, c_len)
                    if c_name:
                        new_c.name = c_name
                    new_c.muted = c_muted

                    if raw_notes:
                        live_tuples = []
                        for n in raw_notes:
                            live_tuples.append((
                                int(n['pitch']),
                                float(n['start_time']),
                                float(n['duration']),
                                float(n['velocity']),
                                bool(n.get('mute', False))
                            ))
                        new_c.set_notes(tuple(live_tuples))
                        recreated_notes += len(live_tuples)
                    recreated_clips += 1
                except Exception as ex:
                    pass

    res_summary['recreated_clips'] = recreated_clips
    res_summary['recreated_notes'] = recreated_notes

result = res_summary
"""

        if conn and hasattr(conn, "send_command"):
            try:
                if t_index >= 0:
                    try:
                        conn.send_command("set_track_volume", {"track_index": t_index, "volume": vol})
                        conn.send_command("set_track_panning", {"track_index": t_index, "panning": pan})
                        conn.send_command("set_track_mute", {"track_index": t_index, "is_muted": mute})
                    except Exception:
                        pass

                cmd_res = conn.send_command("execute_code", {"code": restore_code})
                exec_result = cmd_res.get("result", {})
                if isinstance(exec_result, dict) and "result" in exec_result:
                    exec_result = exec_result["result"]

                is_found = exec_result.get("found", False) if isinstance(exec_result, dict) else False
                if not is_found and (cmd_res.get("status") != "success" or not exec_result):
                    return {
                        "status": "ERROR",
                        "message": f"Pista '{t_name}' (índice {t_index}) no fue encontrada en Live."
                    }

                recreated_clips = exec_result.get("recreated_clips", len(clips)) if isinstance(exec_result, dict) else len(clips)
                recreated_notes = exec_result.get("recreated_notes", sum(len(c.get("notes", [])) for c in clips)) if isinstance(exec_result, dict) else 0

                return {
                    "status": "SUCCESS",
                    "track_name": t_name,
                    "track_index": t_index,
                    "clips_restored": recreated_clips,
                    "notes_restored": recreated_notes,
                    "message": f"Pista '{t_name}' restaurada exitosamente con {recreated_clips} clips y {recreated_notes} notas MIDI."
                }
            except Exception as ex:
                logger.error(f"Error executing restore_track in Live: {ex}")
                return {
                    "status": "ERROR",
                    "message": f"Error restaurando pista en Live: {str(ex)}"
                }


        return {
            "status": "SUCCESS_MOCK",
            "track_name": t_name,
            "clips_restored": len(clips),
            "notes_restored": sum(len(c.get("notes", [])) for c in clips)
        }

    def restore_clip(
        self,
        conn: Any,
        snapshot_or_id: Union[str, Dict[str, Any]],
        track_identifier: Union[int, str],
        clip_identifier: Union[int, str, float]
    ) -> Dict[str, Any]:
        """
        Restores ONLY a single arrangement clip on the specified track.
        Leaves all other clips on that track and all other tracks completely untouched.
        """
        snap_data = self._resolve_snapshot_data(snapshot_or_id)
        if not snap_data:
            return {"status": "ERROR", "message": f"Snapshot '{snapshot_or_id}' no encontrado."}

        t_data = self._find_track_data(snap_data, track_identifier)
        if not t_data:
            return {"status": "ERROR", "message": f"Pista '{track_identifier}' no encontrada en el snapshot."}

        t_name = t_data.get("name", "")
        t_index = t_data.get("index", -1)
        clips = t_data.get("arrangement_clips", [])

        target_clip = None
        if isinstance(clip_identifier, int) and 0 <= clip_identifier < len(clips):
            target_clip = clips[clip_identifier]
        elif isinstance(clip_identifier, float):
            for c in clips:
                if abs(float(c.get("start_time", -999)) - clip_identifier) < 0.1:
                    target_clip = c
                    break
        elif isinstance(clip_identifier, str):
            norm_clip = _normalize_text(clip_identifier)
            try:
                start_val = float(clip_identifier)
                for c in clips:
                    if abs(float(c.get("start_time", -999)) - start_val) < 0.1:
                        target_clip = c
                        break
            except ValueError:
                pass
            if target_clip is None:
                for c in clips:
                    if _normalize_text(c.get("name", "")) == norm_clip:
                        target_clip = c
                        break

        if not target_clip:
            return {
                "status": "ERROR",
                "message": f"Clip '{clip_identifier}' no encontrado en los clips guardados de '{t_name}'."
            }

        clip_json = json.dumps(target_clip)

        restore_clip_code = f"""
import json

c_info = json.loads({repr(clip_json)})
target_name = {repr(t_name)}
target_idx = {t_index}

target_track = None
if target_idx >= 0 and target_idx < len(song.tracks):
    if song.tracks[target_idx].name == target_name:
        target_track = song.tracks[target_idx]

if target_track is None:
    for trk in song.tracks:
        if trk.name.strip().lower() == target_name.strip().lower():
            target_track = trk
            break

res = {{'found_track': False, 'clip_restored': False}}
if target_track is not None:
    res['found_track'] = True
    c_start = float(c_info.get('start_time', 0.0))
    c_len = float(c_info.get('length', 4.0))
    c_end = c_start + c_len
    c_name = c_info.get('name', '')
    raw_notes = c_info.get('notes', [])

    for existing in list(target_track.arrangement_clips):
        e_start = existing.start_time
        e_end = e_start + existing.length
        if not (e_end <= c_start or e_start >= c_end):
            try:
                target_track.delete_clip(existing)
            except Exception:
                pass

    if not c_info.get('is_audio', False):
        new_c = target_track.create_midi_clip(c_start, c_len)
        if c_name:
            new_c.name = c_name
        new_c.muted = c_info.get('muted', False)
        if raw_notes:
            live_tuples = []
            for n in raw_notes:
                live_tuples.append((
                    int(n['pitch']),
                    float(n['start_time']),
                    float(n['duration']),
                    float(n['velocity']),
                    bool(n.get('mute', False))
                ))
            new_c.set_notes(tuple(live_tuples))
            res['notes_count'] = len(live_tuples)
        res['clip_restored'] = True

result = res
"""

        if conn and hasattr(conn, "send_command"):
            try:
                cmd_res = conn.send_command("execute_code", {"code": restore_clip_code})
                exec_result = cmd_res.get("result", {})
                if isinstance(exec_result, dict) and "result" in exec_result:
                    exec_result = exec_result["result"]

                if not exec_result.get("found_track", False):
                    return {"status": "ERROR", "message": f"Pista '{t_name}' no encontrada en Live."}

                return {
                    "status": "SUCCESS",
                    "track_name": t_name,
                    "clip_name": target_clip.get("name", ""),
                    "start_time": target_clip.get("start_time"),
                    "length": target_clip.get("length"),
                    "notes_restored": exec_result.get("notes_count", 0),
                    "message": f"Clip en t={target_clip.get('start_time')} restaurado exitosamente con {exec_result.get('notes_count', 0)} notas."
                }
            except Exception as ex:
                logger.error(f"Error executing restore_clip in Live: {ex}")
                return {"status": "ERROR", "message": str(ex)}

        return {
            "status": "SUCCESS_MOCK",
            "track_name": t_name,
            "clip_name": target_clip.get("name", ""),
            "notes_restored": len(target_clip.get("notes", []))
        }

    def restore_full(
        self,
        conn: Any,
        snapshot_or_id: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Restores all tracks and clips recorded in the snapshot."""
        snap_data = self._resolve_snapshot_data(snapshot_or_id)
        if not snap_data:
            return {"status": "ERROR", "message": f"Snapshot '{snapshot_or_id}' no encontrado."}

        tracks = snap_data.get("tracks", [])
        results = []
        for t in tracks:
            res = self.restore_track(conn, snap_data, t.get("index"))
            results.append(res)

        return {
            "status": "SUCCESS",
            "snapshot_id": snap_data.get("id"),
            "tracks_restored": len(results),
            "details": results
        }


physical_snapshot_manager = PhysicalSnapshotManager()

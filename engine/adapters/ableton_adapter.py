# engine/adapters/ableton_adapter.py
from typing import Dict, Any
from .base import BaseAbletonAdapter
from ..errors import AbletonConnectionError, RemoteScriptError

class LiveAbletonAdapter(BaseAbletonAdapter):
    """Production adapter that communicates with Ableton Live Remote Script via TCP socket"""
    def __init__(self, connection_getter):
        self.connection_getter = connection_getter

    def _get_connection(self):
        try:
            conn = self.connection_getter()
            if not conn.connect():
                raise AbletonConnectionError("Could not connect to Ableton Live Remote Script on port 9877")
            return conn
        except Exception as e:
            raise AbletonConnectionError(f"Connection failure: {str(e)}")

    def is_connected(self) -> bool:
        try:
            conn = self.connection_getter()
            return conn.connect()
        except Exception:
            return False

    def _send(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            return conn.send_command(command_type, params or {})
        except Exception as e:
            raise RemoteScriptError(f"Remote script error executing '{command_type}': {str(e)}")

    def get_session_info(self) -> Dict[str, Any]:
        return self._send("get_session_info")

    def get_track_info(self, track_index: int) -> Dict[str, Any]:
        return self._send("get_track_info", {"track_index": track_index})

    def create_midi_track(self, index: int = -1) -> Dict[str, Any]:
        return self._send("create_midi_track", {"index": index})

    def set_track_name(self, track_index: int, name: str) -> Dict[str, Any]:
        return self._send("set_track_name", {"track_index": track_index, "name": name})

    def delete_track(self, track_index: int) -> Dict[str, Any]:
        return self._send("delete_track", {"track_index": track_index})

    def create_clip(self, track_index: int, clip_index: int, length: float = 4.0) -> Dict[str, Any]:
        return self._send("create_clip", {"track_index": track_index, "clip_index": clip_index, "length": length})

    def delete_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        return self._send("delete_clip", {"track_index": track_index, "clip_index": clip_index})

    def set_track_volume(self, track_index: int, volume: float) -> Dict[str, Any]:
        return self._send("set_track_volume", {"track_index": track_index, "volume": volume})

    def set_track_panning(self, track_index: int, panning: float) -> Dict[str, Any]:
        return self._send("set_track_panning", {"track_index": track_index, "panning": panning})

    def set_track_mute(self, track_index: int, mute: bool) -> Dict[str, Any]:
        return self._send("set_track_mute", {"track_index": track_index, "mute": mute})

    def set_track_solo(self, track_index: int, solo: bool) -> Dict[str, Any]:
        return self._send("set_track_solo", {"track_index": track_index, "solo": solo})

    def set_tempo(self, tempo: float) -> Dict[str, Any]:
        return self._send("set_tempo", {"tempo": tempo})

    def add_notes_to_clip(self, track_index: int, clip_index: int, notes: List[Dict[str, Any]], mode: str = "create") -> Dict[str, Any]:
        if mode in ["create", "replace"]:
            try:
                clip_len = 16.0
                if notes:
                    clip_len = max(16.0, max(float(n.get("start_time", 0.0)) + float(n.get("duration", 0.25)) for n in notes))
                self.create_clip(track_index, clip_index, length=clip_len)
            except Exception:
                pass
        return self._send("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })

    def get_clip_notes(self, track_index: int, clip_index: int) -> List[Dict[str, Any]]:
        try:
            res = self._send("get_clip_notes", {
                "track_index": track_index,
                "clip_index": clip_index
            })
            if isinstance(res, list):
                return res
            return res.get("notes", [])
        except Exception:
            return []

    def fire_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        return self._send("fire_clip", {"track_index": track_index, "clip_index": clip_index})

    def stop_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        return self._send("stop_clip", {"track_index": track_index, "clip_index": clip_index})

    def start_playback(self) -> Dict[str, Any]:
        return self._send("start_playback")

    def stop_playback(self) -> Dict[str, Any]:
        return self._send("stop_playback")

    def load_instrument_or_effect(self, track_index: int, uri: str) -> Dict[str, Any]:
        return self._send("load_browser_item", {"track_index": track_index, "item_uri": uri})

    def load_drum_pad_item(self, track_index: int, pad_note: int, item_uri: str, device_index: int = 0) -> Dict[str, Any]:
        return self._send("load_drum_pad_item", {
            "track_index": track_index,
            "pad_note": pad_note,
            "item_uri": item_uri,
            "device_index": device_index
        })


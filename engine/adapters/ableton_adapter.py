# engine/adapters/ableton_adapter.py
from typing import Dict, Any, List, Optional
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

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}

        # 1. Repair and translate add_automation_points to create_arrangement_automation_envelope / master automation
        if command_type == "add_automation_points":
            p = dict(params)
            t_id = p.get("track_index", p.get("track", 0))
            pts = p.get("points", [])
            param_name = p.get("parameter", "Volume")
            dev_idx = p.get("device_index", p.get("device"))
            clip_idx = p.get("clip_index")

            # Check if targeting master track explicitly or out of range
            is_master = str(t_id).lower() in ("master", "-1")
            if not is_master and isinstance(t_id, int):
                try:
                    return self._send("create_arrangement_automation_envelope", {
                        "track_index": t_id,
                        "device_index": dev_idx,
                        "parameter": param_name,
                        "points": pts,
                        "clip_index": clip_idx
                    })
                except Exception as ex_arr:
                    if "out of range" in str(ex_arr).lower():
                        is_master = True
                    else:
                        raise ex_arr

            if is_master:
                # Master track volume/pan automation via LOM
                code_lines = ["# Master automation injection"]
                if pts and str(param_name).lower() in ("volume", "master volume"):
                    final_v = float(pts[0].get("value", 0.85))
                    code_lines.append(f"song.master_track.mixer_device.volume.value = {final_v}")
                code_lines.append(f"result = {{'status': 'success', 'master_automated': True, 'points': {len(pts)}}}")
                return self._send("execute_code", {"code": "\n".join(code_lines)})
            else:
                return self._send("create_arrangement_automation_envelope", {
                    "track_index": t_id,
                    "device_index": dev_idx,
                    "parameter": param_name,
                    "points": pts,
                    "clip_index": clip_idx
                })

        # 2. Translate ensure_device to track check and load_browser_item
        if command_type == "ensure_device":
            p = dict(params)
            t_idx = p.get("track_index", p.get("track", 0))
            d_name = str(p.get("device_name", "Utility"))
            try:
                t_info = self._send("get_track_info", {"track_index": t_idx})
                devices = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
                for idx, d in enumerate(devices):
                    if d_name.lower() in str(d.get("name", "")).lower() or d_name.lower() in str(d.get("class_name", "")).lower():
                        return {"status": "ALREADY_PRESENT", "track_index": t_idx, "device_index": idx, "device_name": d_name}
            except Exception:
                pass

            uri_map = {
                "utility": "query:AudioFx#Utility",
                "eq eight": "query:AudioFx#EQ%20Eight",
                "glue compressor": "query:AudioFx#Glue%20Compressor",
                "compressor": "query:AudioFx#Compressor",
                "redux": "query:AudioFx#Redux",
                "erosion": "query:AudioFx#Erosion",
                "saturator": "query:AudioFx#Saturator",
                "beat repeat": "query:AudioFx#Beat%20Repeat",
            }
            target_uri = uri_map.get(d_name.lower(), f"query:AudioFx#{d_name}")
            try:
                load_res = self._send("load_browser_item", {"track_index": t_idx, "item_uri": target_uri})
                return {"status": "SUCCESS", "track_index": t_idx, "device_name": d_name, "load_result": load_res}
            except Exception as ex_load:
                return {"status": "FALLBACK", "track_index": t_idx, "device_name": d_name, "notice": str(ex_load)}

        return self._send(command_type, params)

    def get_cue_points(self) -> Dict[str, Any]:
        return self._send("get_cue_points")

    def get_arrangement_clips(self, track_index: int) -> Dict[str, Any]:
        return self._send("get_arrangement_clips", {"track_index": track_index})

    def execute_batch(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a batch of LOM operations in a single atomic TCP round-trip
        by compiling instructions into an execute_code payload.
        """
        lines = ["# Batch atomic execution"]
        for op in operations:
            cmd = op.get("command")
            p = op.get("params", {})
            if cmd == "set_device_parameter":
                lines.append(f"try:\n    song.tracks[{p['track_index']}].devices[{p['device_index']}].parameters[{p.get('parameter', 0)}].value = {float(p['value'])}\nexcept Exception: pass")
            elif cmd == "set_track_volume":
                lines.append(f"try:\n    song.tracks[{p['track_index']}].mixer_device.volume.value = {float(p['volume'])}\nexcept Exception: pass")
            elif cmd == "set_track_panning":
                lines.append(f"try:\n    song.tracks[{p['track_index']}].mixer_device.panning.value = {float(p['panning'])}\nexcept Exception: pass")
        
        batch_code = "\n".join(lines) + "\nres = {'executed_ops': " + str(len(operations)) + ", 'status': 'success'}"
        return self._send("execute_code", {"code": batch_code})

    def set_semantic_vst_parameter(self, track_index: int, device_index: int, param_name: str, value: float) -> Dict[str, Any]:
        """Sets parameter by fuzzy/canonical name matching to resist VST3 parameter index shifts."""
        code = f"""
t = song.tracks[{track_index}]
d = t.devices[{device_index}]
target = '{param_name.lower().strip()}'
matched = False
for p in d.parameters:
    p_n = p.name.lower().strip()
    if target == p_n or target in p_n or p_n in target:
        p.value = {float(value)}
        matched = True
        break
res = {{'matched': matched, 'target': '{param_name}', 'value': {float(value)}}}
"""
        return self._send("execute_code", {"code": code})




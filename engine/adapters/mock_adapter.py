# engine/adapters/mock_adapter.py
from typing import Dict, Any, List, Optional
from .base import BaseAbletonAdapter

class MockAbletonAdapter(BaseAbletonAdapter):
    """In-memory simulation of Ableton Live for offline execution and automated tests"""
    def __init__(self):
        self._connected = True
        self.tempo = 128.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.tracks: List[Dict[str, Any]] = [
            {
                "index": 0,
                "name": "Kick",
                "is_audio_track": False,
                "is_midi_track": True,
                "mute": False,
                "solo": False,
                "arm": False,
                "volume": 0.85,
                "panning": 0.0,
                "clip_slots": [
                    {"index": 0, "has_clip": True, "clip": {"name": "Kick 4x4", "length": 4.0, "is_playing": False, "is_recording": False}},
                    {"index": 1, "has_clip": False, "clip": None}
                ],
                "devices": [
                    {"index": 0, "name": "Drum Buss", "class_name": "DrumBuss", "type": "audio_effect"}
                ]
            },
            {
                "index": 1,
                "name": "Bass",
                "is_audio_track": False,
                "is_midi_track": True,
                "mute": False,
                "solo": False,
                "arm": False,
                "volume": 0.75,
                "panning": 0.0,
                "clip_slots": [
                    {"index": 0, "has_clip": True, "clip": {"name": "Rolling Sub", "length": 8.0, "is_playing": False, "is_recording": False}},
                    {"index": 1, "has_clip": False, "clip": None}
                ],
                "devices": [
                    {"index": 0, "name": "Drift", "class_name": "Drift", "type": "instrument"}
                ]
            }
        ]

    def is_connected(self) -> bool:
        return self._connected

    def set_connected(self, state: bool):
        self._connected = state

    def get_session_info(self) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        return {
            "tempo": self.tempo,
            "signature_numerator": self.signature_numerator,
            "signature_denominator": self.signature_denominator,
            "track_count": len(self.tracks),
            "return_track_count": 0,
            "master_track": {
                "name": "Master",
                "volume": 0.85,
                "panning": 0.0
            }
        }

    def get_track_info(self, track_index: int) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        if track_index < 0 or track_index >= len(self.tracks):
            raise IndexError(f"Track index {track_index} out of range")
        track = dict(self.tracks[track_index])
        track["index"] = track_index
        return track

    def create_midi_track(self, index: int = -1) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        new_track = {
            "index": len(self.tracks) if index == -1 else index,
            "name": f"MIDI Track {len(self.tracks) + 1}",
            "is_audio_track": False,
            "is_midi_track": True,
            "mute": False,
            "solo": False,
            "arm": False,
            "volume": 0.85,
            "panning": 0.0,
            "clip_slots": [{"index": i, "has_clip": False, "clip": None} for i in range(8)],
            "devices": []
        }
        if index == -1 or index >= len(self.tracks):
            self.tracks.append(new_track)
            created_idx = len(self.tracks) - 1
        else:
            self.tracks.insert(index, new_track)
            created_idx = index
        self._reindex_tracks()
        return {"track_index": created_idx, "name": new_track["name"]}

    def set_track_name(self, track_index: int, name: str) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        self.tracks[track_index]["name"] = name
        return {"track_index": track_index, "name": name}

    def delete_track(self, track_index: int) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        if track_index < 0 or track_index >= len(self.tracks):
            raise IndexError("Track index out of range")
        deleted = self.tracks.pop(track_index)
        self._reindex_tracks()
        return {"track_index": track_index, "deleted_name": deleted["name"]}

    def create_clip(self, track_index: int, clip_index: int, length: float = 4.0) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        while len(track["clip_slots"]) <= clip_index:
            track["clip_slots"].append({"index": len(track["clip_slots"]), "has_clip": False, "clip": None})
        track["clip_slots"][clip_index] = {
            "index": clip_index,
            "has_clip": True,
            "clip": {"name": f"Clip {clip_index}", "length": length, "is_playing": False, "is_recording": False}
        }
        return {"track_index": track_index, "clip_index": clip_index, "length": length}

    def delete_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        if clip_index < len(track["clip_slots"]):
            track["clip_slots"][clip_index] = {"index": clip_index, "has_clip": False, "clip": None}
        return {"track_index": track_index, "clip_index": clip_index, "deleted": True}

    def set_track_volume(self, track_index: int, volume: float) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        self.tracks[track_index]["volume"] = float(volume)
        return {"track_index": track_index, "volume": volume}

    def set_track_panning(self, track_index: int, panning: float) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        self.tracks[track_index]["panning"] = float(panning)
        return {"track_index": track_index, "panning": panning}

    def set_track_mute(self, track_index: int, mute: bool) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        self.tracks[track_index]["mute"] = bool(mute)
        return {"track_index": track_index, "mute": mute}

    def set_track_solo(self, track_index: int, solo: bool) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        self.tracks[track_index]["solo"] = bool(solo)
        return {"track_index": track_index, "solo": solo}

    def set_tempo(self, tempo: float) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        self.tempo = float(tempo)
        return {"tempo": tempo}

    def add_notes_to_clip(self, track_index: int, clip_index: int, notes: List[Dict[str, Any]], mode: str = "create") -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        while len(track["clip_slots"]) <= clip_index:
            track["clip_slots"].append({"index": len(track["clip_slots"]), "has_clip": False, "clip": None})
        slot = track["clip_slots"][clip_index]
        if not slot.get("has_clip") or not slot.get("clip"):
            slot["has_clip"] = True
            slot["clip"] = {"name": f"Clip {clip_index}", "length": 16.0, "is_playing": False, "is_recording": False, "notes": []}
        if "notes" not in slot["clip"] or mode == "replace":
            slot["clip"]["notes"] = []
        slot["clip"]["notes"].extend(notes)
        return {"track_index": track_index, "clip_index": clip_index, "notes_added": len(notes)}

    def get_clip_notes(self, track_index: int, clip_index: int) -> List[Dict[str, Any]]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        if clip_index < len(track["clip_slots"]):
            slot = track["clip_slots"][clip_index]
            if slot.get("has_clip") and slot.get("clip"):
                return list(slot["clip"].get("notes", []))
        return []

    def _reindex_tracks(self):
        for i, t in enumerate(self.tracks):
            t["index"] = i

    def load_instrument_or_effect(self, track_index: int, uri: str) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        uri_lower = uri.lower()

        # Check if loading an audio effect
        is_effect = ("audiofx" in uri_lower or "audio_effects" in uri_lower or
                     any(e in uri_lower for e in ("drum%20buss", "glue", "eq%20eight", "saturator", "delay", "ott", "valhalla", "chorus", "compressor", "fragments")))

        if is_effect:
            eff_name = "Audio Effect"
            c_name = "AudioEffectGroupDevice"
            if "drum" in uri_lower and "buss" in uri_lower:
                eff_name = "Drum Buss"
                c_name = "DrumBuss"
            elif "glue" in uri_lower:
                eff_name = "Glue Compressor"
                c_name = "GlueCompressor"
            elif "eq" in uri_lower:
                eff_name = "EQ Eight"
                c_name = "Eq8"
            elif "saturator" in uri_lower:
                eff_name = "Saturator"
                c_name = "Saturator"
            elif "chorus" in uri_lower:
                eff_name = "Chorus-Ensemble"
                c_name = "Chorus"
            elif "valhalla" in uri_lower:
                eff_name = "ValhallaVintageVerb"
                c_name = "PluginDevice"
            elif "delay" in uri_lower:
                eff_name = "Delay"
                c_name = "Delay"
            elif "ott" in uri_lower:
                eff_name = "OTT"
                c_name = "PluginDevice"
            elif "fragments" in uri_lower:
                eff_name = "Efx FRAGMENTS"
                c_name = "PluginDevice"
            elif "compressor" in uri_lower:
                eff_name = "Compressor"
                c_name = "Compressor"
            elif "#" in uri:
                eff_name = uri.split("#")[-1].replace("%20", " ").strip()

            new_dev = {
                "index": len(track["devices"]),
                "name": eff_name,
                "class_name": c_name,
                "type": "audio_effect"
            }
            track["devices"].append(new_dev)
            return {"loaded": True, "track_index": track_index, "uri": uri, "new_devices": [eff_name]}

        # Otherwise, loading an instrument
        is_drum = "drum" in uri_lower or "kit" in uri_lower or "808" in uri_lower
        dev_name = "Drum Rack" if is_drum else "Drift"

        # Check for kit presets that populate pads
        is_kit_preset = is_drum and any(k in uri_lower for k in ("kit", "fileid", "808", "preset", "acoustic"))
        pads = []
        if is_kit_preset:
            pads = [
                {"note": 36, "name": "Kick", "mute": False, "solo": False, "devices": [{"name": "Simpler"}]},
                {"note": 38, "name": "Snare", "mute": False, "solo": False, "devices": [{"name": "Simpler"}]},
                {"note": 42, "name": "Closed HH", "mute": False, "solo": False, "devices": [{"name": "Simpler"}]},
                {"note": 46, "name": "Open HH", "mute": False, "solo": False, "devices": [{"name": "Simpler"}]},
            ]

        # If track already has a Drum Rack and we load a kit preset into it:
        for d in track.get("devices", []):
            if d.get("class_name") == "DrumGroupDevice" or "drum rack" in d.get("name", "").lower():
                if pads:
                    d["drum_pads"] = pads
                return {"loaded": True, "track_index": track_index, "uri": uri, "new_devices": [d["name"]]}

        new_dev = {
            "index": len(track["devices"]),
            "name": dev_name,
            "class_name": "DrumGroupDevice" if is_drum else "InstrumentDevice",
            "type": "drum_machine" if is_drum else "synth",
            "drum_pads": pads
        }
        track["devices"].append(new_dev)
        return {"loaded": True, "track_index": track_index, "uri": uri, "new_devices": [dev_name]}

    def delete_device(self, track_index: int, device_index: int) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        if track_index < 0 or track_index >= len(self.tracks):
            raise IndexError(f"Track index {track_index} out of range")
        track = self.tracks[track_index]
        devices = track.get("devices", [])
        if device_index < 0 or device_index >= len(devices):
            raise IndexError(f"Device index {device_index} out of range")
        deleted = devices.pop(device_index)
        for idx, dev in enumerate(devices):
            dev["index"] = idx
        return {"status": "success", "track_index": track_index, "device_index": device_index, "deleted_device": deleted.get("name", "")}


    def get_drum_rack_pads(self, track_index: int, device_index: int = 0) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        devices = track.get("devices", [])
        drum_dev = None
        if device_index < len(devices) and ("drum rack" in devices[device_index].get("name", "").lower() or devices[device_index].get("class_name") == "DrumGroupDevice"):
            drum_dev = devices[device_index]
        else:
            for d in devices:
                if "drum rack" in d.get("name", "").lower() or d.get("class_name") == "DrumGroupDevice":
                    drum_dev = d
                    break
        if not drum_dev:
            return {"track_index": track_index, "active_pad_count": 0, "pads": [], "result": {"active_pad_count": 0, "pads": []}}
        pads = drum_dev.get("drum_pads", [])
        res = {
            "track_index": track_index,
            "drum_rack_name": drum_dev.get("name", "Drum Rack"),
            "active_pad_count": len(pads),
            "pads": pads
        }
        res["result"] = res
        return res

    def get_drum_pad_devices(self, track_index: int, pad_note: int, device_index: int = 0) -> Dict[str, Any]:
        rack_info = self.get_drum_rack_pads(track_index, device_index)
        for p in rack_info.get("pads", []):
            if p.get("note") == pad_note:
                return p
        return {"pad_note": pad_note, "pad_name": f"Pad {pad_note}", "mute": False, "solo": False, "devices": []}

    def load_drum_pad_item(self, track_index: int, pad_note: int, item_uri: str, device_index: int = 0) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        devices = track.get("devices", [])
        drum_dev = None
        if device_index < len(devices) and ("drum rack" in devices[device_index].get("name", "").lower() or devices[device_index].get("class_name") == "DrumGroupDevice"):
            drum_dev = devices[device_index]
        else:
            for d in devices:
                if "drum rack" in d.get("name", "").lower() or d.get("class_name") == "DrumGroupDevice":
                    drum_dev = d
                    break
        if not drum_dev:
            self.load_instrument_or_effect(track_index, "query:Drums#Drum%20Rack")
            drum_dev = track["devices"][-1]

        dev = drum_dev
        if "drum_pads" not in dev:
            dev["drum_pads"] = []

        
        target_pad = None
        for p in dev["drum_pads"]:
            if p.get("note") == pad_note:
                target_pad = p
                break
        if not target_pad:
            target_pad = {
                "note": pad_note,
                "name": f"Pad {pad_note}",
                "mute": False,
                "solo": False,
                "devices": [{"name": "Simpler", "class_name": "OriginalSimpler", "sample": item_uri}]
            }
            dev["drum_pads"].append(target_pad)
        else:
            target_pad["devices"] = [{"name": "Simpler", "class_name": "OriginalSimpler", "sample": item_uri}]
        return {"loaded": True, "pad_note": pad_note, "uri": item_uri}

    def get_arrangement_clips(self, track_index: int) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        clips = track.get("arrangement_clips", [])
        return {
            "track_index": track_index,
            "track_name": track.get("name", ""),
            "clip_count": len(clips),
            "clips": clips
        }

    def duplicate_to_arrangement(self, track_index: int, clip_index: int, destination_time: float) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectionError("Mock Ableton is disconnected")
        track = self.tracks[track_index]
        if "arrangement_clips" not in track:
            track["arrangement_clips"] = []
        clip_slots = track.get("clip_slots", [])
        c_name = f"Clip_{clip_index}"
        c_len = 16.0
        if clip_index < len(clip_slots) and clip_slots[clip_index].get("has_clip"):
            c = clip_slots[clip_index]["clip"]
            c_name = c.get("name", c_name)
            c_len = c.get("length", 16.0)
        new_arr_clip = {
            "name": c_name,
            "start_time": float(destination_time),
            "end_time": float(destination_time + c_len),
            "length": c_len,
            "is_midi_clip": track.get("is_midi_track", True),
            "is_audio_clip": track.get("is_audio_track", False),
        }
        track["arrangement_clips"].append(new_arr_clip)
        return {"status": "success", "track_index": track_index, "destination_time": destination_time}

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        if command_type == "get_arrangement_clips":
            return self.get_arrangement_clips(params.get("track_index", 0))
        elif command_type in ("duplicate_to_arrangement", "duplicate_session_clip_to_arrangement"):
            return self.duplicate_to_arrangement(
                params.get("track_index", 0),
                params.get("clip_index", 0),
                params.get("destination_time", 0.0)
            )
        elif command_type == "create_cue_point":
            if not hasattr(self, "cue_points"):
                self.cue_points = []
            self.cue_points.append({"name": params.get("name", ""), "time": params.get("time", 0.0)})
            return {"status": "success", "cue_point": params}
        elif command_type == "get_cue_points":
            return {"cue_points": getattr(self, "cue_points", [])}
        elif command_type in ("create_arrangement_automation_envelope", "record_arrangement_automation"):
            if not hasattr(self, "automation_envelopes"):
                self.automation_envelopes = []
            self.automation_envelopes.append(params)
            return {"status": "success", "envelope": params}
        elif command_type == "record_multi_automation_pass":
            if not hasattr(self, "automation_envelopes"):
                self.automation_envelopes = []
            for a in params.get("automations", []):
                self.automation_envelopes.append(a)
            return {"status": "success", "result": {"status": "completed", "automations_recorded": len(params.get("automations", []))}}
        return self._send(command_type, params)

    def _send(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        if command_type == "get_drum_rack_pads":
            return self.get_drum_rack_pads(params.get("track_index", 0), params.get("device_index", 0))
        elif command_type == "get_drum_pad_devices":
            return self.get_drum_pad_devices(params.get("track_index", 0), params.get("pad_note", 36), params.get("device_index", 0))
        elif command_type == "load_drum_pad_item":
            return self.load_drum_pad_item(params.get("track_index", 0), params.get("pad_note", 36), params.get("item_uri", ""), params.get("device_index", 0))
        elif command_type in ("load_browser_item", "load_instrument_or_effect"):
            uri = params.get("item_uri", params.get("uri", ""))
            return self.load_instrument_or_effect(params.get("track_index", 0), uri)
        elif command_type == "get_track_info":
            return self.get_track_info(params.get("track_index", 0))
        elif command_type == "get_session_info":
            return self.get_session_info()
        elif command_type == "create_clip":
            return self.create_clip(params.get("track_index", 0), params.get("clip_index", 0), params.get("length", 4.0))
        elif command_type == "delete_clip":
            return self.delete_clip(params.get("track_index", 0), params.get("clip_index", 0))
        elif command_type == "delete_device":
            return self.delete_device(params.get("track_index", 0), params.get("device_index", 0))
        elif command_type == "add_notes_to_clip":
            return self.add_notes_to_clip(params.get("track_index", 0), params.get("clip_index", 0), params.get("notes", []), params.get("mode", "create"))
        elif command_type == "set_track_name":
            return self.set_track_name(params.get("track_index", 0), params.get("name", ""))
        elif command_type == "create_midi_track":
            return self.create_midi_track(params.get("index", -1))
        elif command_type == "set_track_volume":
            return self.set_track_volume(params.get("track_index", 0), params.get("volume", 0.85))
        elif command_type == "set_track_panning":
            return self.set_track_panning(params.get("track_index", 0), params.get("panning", 0.0))
        elif command_type == "set_track_mute":
            return self.set_track_mute(params.get("track_index", 0), params.get("mute", False))
        elif command_type == "set_track_solo":
            return self.set_track_solo(params.get("track_index", 0), params.get("solo", False))
        elif command_type == "set_tempo":
            return self.set_tempo(params.get("tempo", 120.0))
        elif command_type == "fire_clip":
            return self.fire_clip(params.get("track_index", 0), params.get("clip_index", 0))
        elif command_type == "stop_clip":
            return self.stop_clip(params.get("track_index", 0), params.get("clip_index", 0))
        elif command_type == "start_playback":
            return self.start_playback()
        elif command_type == "stop_playback":
            return self.stop_playback()
        return {}


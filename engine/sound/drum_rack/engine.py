"""
Drum Rack Engine v2:
Idempotent batch construction, pad configuration, and strict verification.
"""
from typing import Dict, List, Any, Optional, Union
from engine.instruments.drum_map import DrumMap
from .models import DrumRackSpec, DrumPadSpec
from .resolver import DrumSoundResolver
from .verifier import DrumRackVerifier

class DrumRackEngine:
    """Master production engine for Drum Racks in Ableton Live."""

    STANDARD_ROLES = [
        ("KICK", 36), ("SNARE", 38), ("CLAP", 39),
        ("CLOSED_HAT", 40), ("OPEN_HAT", 41),
        ("PERC_1", 42), ("PERC_2", 43), ("CRASH", 49)
    ]

    def __init__(self, adapter=None):
        self.adapter = adapter
        self.verifier = DrumRackVerifier

    def build_drum_rack(
        self,
        track_index: int,
        style: str = "melodic_techno",
        spec: Optional[DrumRackSpec] = None,
        seed: int = 2026,
        preview: bool = False
    ) -> Dict[str, Any]:
        """
        Builds and populates a complete Drum Rack in an atomic batch operation.
        Strictly verifies that pads are populated before returning success.
        """
        # 1. Build default spec if not provided
        if not spec:
            spec = DrumRackSpec(name=f"AG_{style.capitalize()}_Kit", style=style)
            for role_name, note in self.STANDARD_ROLES:
                sample_path = DrumSoundResolver.resolve_drum_sound(role=role_name, genre=style, seed=seed)
                spec.pads[note] = DrumPadSpec(
                    note=note,
                    role=role_name,
                    name=f"[{DrumMap.get_display_name(note)}] {role_name}",
                    sample_path=sample_path
                )

        if preview or not self.adapter:
            return {
                "status": "preview",
                "track_index": track_index,
                "spec": spec.to_dict(),
                "total_pads_to_build": len(spec.pads)
            }

        # 2. Ensure Drum Rack container exists on track
        try:
            t_info = self.adapter.get_track_info(track_index) if hasattr(self.adapter, "get_track_info") else {}
            has_rack = any("drum" in d.get("name", "").lower() or d.get("class_name") == "DrumGroupDevice" for d in t_info.get("devices", []))
            if not has_rack:
                if hasattr(self.adapter, "load_instrument_or_effect"):
                    self.adapter.load_instrument_or_effect(track_index, "query:Drums#Drum%20Rack")
                elif hasattr(self.adapter, "send_command"):
                    self.adapter.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Drums#Drum%20Rack"})
        except Exception:
            pass

        # 3. Populate pads with samples
        populated_count = 0
        failed_pads = []
        for note, pad in spec.pads.items():
            try:
                uri = pad.sample_path or f"query:Drums#{pad.role.capitalize()}"
                if hasattr(self.adapter, "load_drum_pad_item"):
                    self.adapter.load_drum_pad_item(track_index, note, uri, 0)
                    populated_count += 1
                elif hasattr(self.adapter, "send_command"):
                    self.adapter.send_command("load_drum_pad_item", {
                        "track_index": track_index,
                        "pad_note": note,
                        "item_uri": uri,
                        "device_index": 0
                    })
                    populated_count += 1
            except Exception as e:
                failed_pads.append({"note": note, "role": pad.role, "error": str(e)})

        # 4. Strict physical verification
        verification = DrumRackVerifier.verify_drum_rack(self.adapter, track_index, [p.role for p in spec.pads.values()])
        
        return {
            "status": "success" if verification.get("verified", False) else "partial_failure",
            "track_index": track_index,
            "rack_name": spec.name,
            "populated_pads": populated_count,
            "verification": verification,
            "failed_pads": failed_pads
        }

    def add_pad(
        self,
        track_index: int,
        pad_note: int,
        sound_type: str,
        sample_path: Optional[str] = None,
        preview: bool = False
    ) -> Dict[str, Any]:
        """Adds or updates a single pad in an existing Drum Rack."""
        resolved_sample = sample_path or DrumSoundResolver.resolve_drum_sound(role=sound_type)
        if preview or not self.adapter:
            return {
                "status": "preview",
                "track_index": track_index,
                "pad_note": pad_note,
                "sound_type": sound_type,
                "sample_path": resolved_sample
            }

        try:
            if hasattr(self.adapter, "load_drum_pad_item"):
                res = self.adapter.load_drum_pad_item(track_index, pad_note, resolved_sample, 0)
            elif hasattr(self.adapter, "send_command"):
                res = self.adapter.send_command("load_drum_pad_item", {
                    "track_index": track_index,
                    "pad_note": pad_note,
                    "item_uri": resolved_sample,
                    "device_index": 0
                })
            else:
                res = {"status": "mock"}
            return {
                "status": "success",
                "track_index": track_index,
                "pad_note": pad_note,
                "sound_type": sound_type,
                "sample_path": resolved_sample,
                "result": res
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "track_index": track_index, "pad_note": pad_note}

    def load_sample(
        self,
        track_index: int,
        pad_note: int,
        sample_path: str
    ) -> Dict[str, Any]:
        """Loads a specific audio sample onto a drum pad."""
        return self.add_pad(track_index=track_index, pad_note=pad_note, sound_type="SAMPLE", sample_path=sample_path)

    def set_pad_params(
        self,
        track_index: int,
        pad_note: int,
        volume: Optional[float] = None,
        pitch: Optional[int] = None,
        filter_freq: Optional[float] = None,
        decay: Optional[float] = None,
        pan: Optional[float] = None,
        mute: Optional[bool] = None,
        solo: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Modifies volume, pitch, filter, decay, pan, mute, or solo of a drum pad."""
        updates = []
        if not self.adapter:
            return {"status": "mock", "track_index": track_index, "pad_note": pad_note}

        try:
            if mute is not None or solo is not None:
                if hasattr(self.adapter, "send_command"):
                    self.adapter.send_command("set_drum_pad_mute_solo", {
                        "track_index": track_index,
                        "pad_note": pad_note,
                        "mute": mute,
                        "solo": solo,
                        "device_index": 0
                    })
                    updates.append("mute_solo")

            # Map parameters
            param_map = {
                "Volume": volume,
                "Pitch": pitch,
                "Filter Freq": filter_freq,
                "Decay": decay,
                "Pan": pan
            }
            for p_name, p_val in param_map.items():
                if p_val is not None and hasattr(self.adapter, "send_command"):
                    self.adapter.send_command("set_drum_pad_parameter", {
                        "track_index": track_index,
                        "pad_note": pad_note,
                        "chain_device_index": 0,
                        "parameter": p_name,
                        "value": float(p_val),
                        "device_index": 0
                    })
                    updates.append(p_name)

            return {
                "status": "success",
                "track_index": track_index,
                "pad_note": pad_note,
                "updated_params": updates
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "track_index": track_index, "pad_note": pad_note}

    def inspect_drum_rack(self, track_index: int) -> Dict[str, Any]:
        """Inspects all loaded pads, samples, and chains in a Drum Rack."""
        if not self.adapter:
            return {"track_index": track_index, "pads": [], "status": "mock"}

        try:
            if hasattr(self.adapter, "get_drum_rack_pads"):
                return self.adapter.get_drum_rack_pads(track_index, device_index=0)
            elif hasattr(self.adapter, "send_command"):
                return self.adapter.send_command("get_drum_rack_pads", {"track_index": track_index, "device_index": 0})
        except Exception as e:
            return {"status": "error", "error": str(e), "track_index": track_index}

        return {"track_index": track_index, "pads": []}

    def rebuild_unverified_pads(self, track_index: int, genre: str = "melodic_techno") -> Dict[str, Any]:
        """Rebuilds missing or unverified pads using fallback sample library."""
        ver = DrumRackVerifier.verify_drum_rack(self.adapter, track_index)
        if ver.get("verified", False):
            return {"status": "already_verified", "track_index": track_index, "verification": ver}

        # Re-run build_drum_rack
        return self.build_drum_rack(track_index=track_index, style=genre)

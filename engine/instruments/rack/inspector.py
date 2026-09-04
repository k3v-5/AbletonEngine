# engine/instruments/rack/inspector.py
from typing import Dict, Any, List, Optional
from ..models import RackInspectionReport
from ..drum_map import DrumMap
from ..roles import InstrumentRole

class DrumRackInspector:
    """Inspects tracks and Drum Racks in Live to detect empty racks and pad population state."""
    def __init__(self, adapter):
        self.adapter = adapter

    def inspect(self, track_index: int, device_index: Optional[int] = None) -> RackInspectionReport:
        if not self.adapter or not self.adapter.is_connected():
            return RackInspectionReport(
                rack_exists=False,
                track_index=track_index,
                track_name=f"Track {track_index}",
                status="OFFLINE"
            )

        # 1. Fetch track info to find Drum Rack device
        try:
            track_info = self.adapter.get_track_info(track_index)
        except Exception:
            return RackInspectionReport(
                rack_exists=False,
                track_index=track_index,
                track_name=f"Track {track_index}",
                status="NOT_FOUND"
            )

        track_name = track_info.get("name", f"Track {track_index}")
        devices = track_info.get("devices", [])

        # Find first Drum Rack device if not specified
        drum_device_idx = device_index
        if drum_device_idx is None:
            for idx, d in enumerate(devices):
                d_name = d.get("name", "").lower()
                c_name = d.get("class_name", "")
                d_type = d.get("type", "")
                if "drum rack" in d_name or c_name == "DrumGroupDevice" or d_type == "drum_machine":
                    drum_device_idx = idx
                    break

        if drum_device_idx is None:
            return RackInspectionReport(
                rack_exists=False,
                track_index=track_index,
                track_name=track_name,
                pads=16,
                populated=0,
                empty=16,
                status="NO_RACK",
                missing_roles=["KICK", "SNARE", "CLAP", "CLOSED_HAT", "OPEN_HAT", "PERC_1", "PERC_2"]
            )

        # 2. Query active drum pads from Ableton Live Remote Script
        try:
            rack_data = self.adapter._send("get_drum_rack_pads", {
                "track_index": track_index,
                "device_index": drum_device_idx
            })
        except Exception:
            rack_data = {"active_pad_count": 0, "pads": []}

        pads_list = rack_data.get("pads", [])
        populated_count = len(pads_list)
        empty_count = max(0, 16 - populated_count)

        if populated_count == 0:
            status = "EMPTY"
        elif populated_count < 6:
            status = "PARTIAL"
        else:
            status = "POPULATED"

        # Determine missing roles
        populated_notes = {p.get("note") for p in pads_list if p.get("note") is not None}
        missing_roles = []
        for note, role in DrumMap.NOTE_TO_ROLE.items():
            if note not in populated_notes:
                missing_roles.append(role.value)

        return RackInspectionReport(
            rack_exists=True,
            track_index=track_index,
            track_name=track_name,
            device_index=drum_device_idx,
            pads=16,
            populated=populated_count,
            empty=empty_count,
            status=status,
            active_pads=pads_list,
            missing_roles=missing_roles
        )

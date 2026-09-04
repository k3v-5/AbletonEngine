# engine/instruments/rack/verifier.py
from typing import Dict, Any, List, Optional
from ..drum_map import DrumMap

class DrumRackVerifier:
    """Verifies that each populated pad in a Drum Rack contains real chains, devices and samples."""
    def __init__(self, adapter):
        self.adapter = adapter

    def verify(self, track_index: int, device_index: int = 0) -> Dict[str, Any]:
        if not self.adapter or not self.adapter.is_connected():
            return {"status": "error", "error": "Ableton Live adapter not connected"}

        try:
            rack_data = self.adapter._send("get_drum_rack_pads", {
                "track_index": track_index,
                "device_index": device_index
            })
        except Exception as e:
            return {"status": "error", "error": str(e)}

        pads = rack_data.get("pads", [])
        verified_pads: List[Dict[str, Any]] = []
        issues: List[Dict[str, Any]] = []

        for p in pads:
            note = p.get("note")
            name = p.get("name", "")
            devices = p.get("devices", [])
            role = DrumMap.get_role_for_note(note)
            role_name = role.value if role else "UNKNOWN"

            if not devices:
                issues.append({
                    "note": note,
                    "role": role_name,
                    "issue": "Pad has chain but no active device/instrument"
                })
            else:
                verified_pads.append({
                    "note": note,
                    "pad_name": name or DrumMap.get_display_name_for_note(note),
                    "role": role_name,
                    "device_name": devices[0].get("name", ""),
                    "class_name": devices[0].get("class_name", "")
                })

        # Core roles required for a functional drum kit
        core_roles = [36, 38, 39, 40, 41]  # Kick, Snare, Clap, Closed Hat, Open Hat
        populated_notes = {p.get("note") for p in pads}
        for cr in core_roles:
            if cr not in populated_notes:
                role = DrumMap.get_role_for_note(cr)
                issues.append({
                    "note": cr,
                    "role": role.value if role else str(cr),
                    "issue": "Core drum pad is not populated"
                })

        is_verified = len(issues) == 0 and len(verified_pads) > 0
        return {
            "status": "verified" if is_verified else "issues_found",
            "track_index": track_index,
            "drum_rack_name": rack_data.get("drum_rack_name", "Drum Rack"),
            "populated": len(verified_pads),
            "missing": len(issues),
            "verified_pads": verified_pads,
            "issues": issues
        }

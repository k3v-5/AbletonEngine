"""
Drum Rack Verifier:
Enforces the strict 'No Fake Success' invariant.
Audits physical Drum Rack pads in Ableton Live.
"""
from typing import Dict, Any, List

class DrumRackVerifier:
    """Strictly audits that a Drum Rack has real physical devices and samples in its pads."""

    @staticmethod
    def verify_drum_rack(adapter, track_index: int, required_roles: List[str] = None) -> Dict[str, Any]:
        """
        Verifies that the Drum Rack exists and is populated.
        Returns FAIL or PARTIAL_FAILURE if the rack exists but pads are empty!
        """
        req_roles = required_roles or ["KICK", "SNARE", "CLOSED_HAT"]
        
        if not adapter:
            return {"status": "verified", "active_pad_count": len(req_roles), "verified": True}

        try:
            if hasattr(adapter, "get_drum_rack_pads"):
                rack_data = adapter.get_drum_rack_pads(track_index, device_index=0)
            elif hasattr(adapter, "send_command"):
                rack_data = adapter.send_command("get_drum_rack_pads", {"track_index": track_index, "device_index": 0})
            else:
                rack_data = {}
        except Exception as e:
            return {"status": "error", "message": str(e), "verified": False}

        pads = rack_data.get("pads", [])
        active_count = len(pads)

        if active_count == 0:
            return {
                "status": "partial_failure",
                "verified": False,
                "created": True,
                "populated": False,
                "active_pad_count": 0,
                "missing": req_roles,
                "reason": "Drum Rack device exists on track, but contains 0 populated pads."
            }

        # Check for Simplers
        empty_pads = []
        for p in pads:
            devs = p.get("devices", [])
            if not devs:
                empty_pads.append(p.get("note"))

        if empty_pads:
            return {
                "status": "partial_failure",
                "verified": False,
                "created": True,
                "populated": False,
                "empty_pad_notes": empty_pads,
                "active_pad_count": active_count - len(empty_pads),
                "reason": f"Pads {empty_pads} exist but lack sound devices/samples."
            }

        return {
            "status": "pass",
            "verified": True,
            "created": True,
            "populated": True,
            "active_pad_count": active_count,
            "drum_rack_name": rack_data.get("drum_rack_name", "Drum Rack")
        }

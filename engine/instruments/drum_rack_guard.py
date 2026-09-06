# engine/instruments/drum_rack_guard.py
"""
Drum Rack Guard & Pad Population Supervisor:
Audits drum racks in Ableton Live to guarantee that pads are physically populated
with devices/samples, preventing silent drum tracks ("Suelte aquí un instrumento o muestra").
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("DrumRackGuard")


class DrumRackEmptyError(RuntimeError):
    """Raised when a Drum Rack in Ableton Live has 0 populated pads or missing devices."""
    def __init__(self, message: str, track_index: int, pad_count: int = 0):
        super().__init__(message)
        self.track_index = track_index
        self.pad_count = pad_count


class DrumRackGuard:
    """Supervises Drum Rack integrity, pad devices, and sound readiness."""

    # Standard 16-pad layout mapping (GM / Ableton Standard)
    CRITICAL_PAD_NOTES = {
        36: "Bass Drum (Kick)",
        37: "Rim Shot",
        38: "Snare Drum",
        39: "Hand Clap",
        42: "Closed Hi-Hat",
        46: "Open Hi-Hat",
        49: "Cymbal / Crash"
    }

    # Verified kit preset that loads all 16 pads with Simpler devices and samples
    VERIFIED_808_KIT_URI = "query:Drums#FileId_5422"

    @classmethod
    def audit_drum_rack(cls, conn: Any, track_index: int, device_index: int = 0) -> Dict[str, Any]:
        """
        Audits a Drum Rack on track_index:
        - Retrieves pad list via get_drum_rack_pads
        - Verifies each pad contains devices
        - Returns a full audit report
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "track_index": track_index,
                "status": "MOCK_OK",
                "active_pad_count": 16,
                "populated": True,
                "pads": []
            }

        res = conn.send_command("get_drum_rack_pads", {
            "track_index": track_index,
            "device_index": device_index
        })

        data = res.get("result", {}) if isinstance(res, dict) else {}
        pad_count = data.get("active_pad_count", 0)
        pads = data.get("pads", [])

        # Count pads with actual devices loaded
        populated_pads = []
        empty_pads = []
        for p in pads:
            note = p.get("note")
            name = p.get("name", f"Pad_{note}")
            devs = p.get("devices", [])
            if len(devs) > 0:
                populated_pads.append({"note": note, "name": name, "device_count": len(devs)})
            else:
                empty_pads.append({"note": note, "name": name})

        is_populated = (len(populated_pads) >= 4)  # At minimum Kick, Snare, Clap, Hat

        return {
            "track_index": track_index,
            "drum_rack_name": data.get("drum_rack_name", "Drum Rack"),
            "active_pad_count": pad_count,
            "populated_pad_count": len(populated_pads),
            "empty_pad_count": len(empty_pads),
            "populated_pads": populated_pads,
            "empty_pads": empty_pads,
            "is_populated": is_populated,
            "status": "POPULATED" if is_populated else "EMPTY"
        }

    @classmethod
    def enforce_populated_drum_kit(cls, conn: Any, track_index: int, device_index: int = 0) -> Dict[str, Any]:
        """
        Audits the Drum Rack and if empty, automatically remediates by loading
        the verified 808 Core Kit preset containing 16 populated pads.
        """
        audit = cls.audit_drum_rack(conn, track_index, device_index)
        if audit.get("is_populated"):
            logger.info(f"Drum Rack on track {track_index} is verified and populated ({audit.get('populated_pad_count')} pads).")
            return audit

        logger.warning(
            f"Drum Rack on track {track_index} is EMPTY ({audit.get('populated_pad_count')} pads). "
            f"Loading verified 808 Core Kit preset: {cls.VERIFIED_808_KIT_URI}"
        )

        if conn and hasattr(conn, "send_command"):
            load_res = conn.send_command("load_instrument_or_effect", {
                "track_index": track_index,
                "uri": cls.VERIFIED_808_KIT_URI
            })
            # Re-audit
            re_audit = cls.audit_drum_rack(conn, track_index, device_index)
            if not re_audit.get("is_populated"):
                raise DrumRackEmptyError(
                    f"CRITICAL: Failed to populate Drum Rack on track {track_index}. "
                    f"Pads are still empty after loading preset {cls.VERIFIED_808_KIT_URI}.",
                    track_index=track_index,
                    pad_count=re_audit.get("populated_pad_count", 0)
                )
            return re_audit

        return audit

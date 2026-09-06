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

    @classmethod
    def audit_drum_clip_octaves(
        cls,
        conn: Any,
        track_index: int,
        clip_index: int = 0
    ) -> Dict[str, Any]:
        """
        Audits MIDI clip notes on a drum track against Drum Rack physical pad quadrant layout.
        Standard Ableton Drum Racks map functional pads to Quadrant 1 (C1-D#2, pitches 36-51).
        If notes are written in Quadrant 3 (C3-D#4, pitches 60-75) or higher, pads remain silent.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "status": "MOCK_OK",
                "notes_count": 0,
                "quadrant_1_count": 0,
                "quadrant_3_count": 0,
                "is_aligned": True,
                "warning": None
            }

        try:
            raw = conn.send_command("get_clip_notes", {
                "track_index": track_index,
                "clip_index": clip_index
            })
        except Exception as e:
            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "status": "EMPTY_SLOT",
                "notes_count": 0,
                "quadrant_1_count": 0,
                "quadrant_3_count": 0,
                "is_aligned": True,
                "warning": f"No clip found in slot {clip_index} on track {track_index}: {e}",
                "needs_remediation": False
            }

        data = raw.get("result", raw) if isinstance(raw, dict) else raw
        notes = data.get("notes", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])

        if not notes:
            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "status": "EMPTY_CLIP",
                "notes_count": 0,
                "quadrant_1_count": 0,
                "quadrant_3_count": 0,
                "is_aligned": True,
                "warning": "No notes found in clip slot."
            }

        total_notes = len(notes)
        q1_notes = []  # 36 - 51 (Quadrant 1: C1 - D#2)
        q3_notes = []  # 60 - 75 (Quadrant 3: C3 - D#4)
        other_notes = []

        for n in notes:
            pitch = int(n.get("pitch", 0))
            if 36 <= pitch <= 51:
                q1_notes.append(n)
            elif 60 <= pitch <= 75:
                q3_notes.append(n)
            else:
                other_notes.append(n)

        # Detect mismatch: if significant notes are in Quadrant 3 (C3+) and none or few in Quadrant 1
        has_quadrant_3_mismatch = (len(q3_notes) > 0 and len(q1_notes) == 0) or (len(q3_notes) >= len(q1_notes) and len(q3_notes) >= 4)

        if has_quadrant_3_mismatch:
            warning_msg = (
                f"CRITICAL: Drum Rack pads on Track {track_index} are in Quadrant 1 (C1-D#2, pitches 36-51), "
                f"but {len(q3_notes)}/{total_notes} notes are in Quadrant 3 (C3-D#4, pitches 60-75). "
                f"Drum pads are empty in Quadrant 3 and will sound completely SILENT! "
                f"Requires -24 semitone shift down to Quadrant 1."
            )
            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "status": "OCTAVE_MISMATCH_QUADRANT_3",
                "is_aligned": False,
                "total_notes": total_notes,
                "quadrant_1_count": len(q1_notes),
                "quadrant_3_count": len(q3_notes),
                "other_notes_count": len(other_notes),
                "suggested_semitone_shift": -24,
                "warning": warning_msg,
                "needs_remediation": True
            }

        return {
            "track_index": track_index,
            "clip_index": clip_index,
            "status": "ALIGNED",
            "is_aligned": True,
            "total_notes": total_notes,
            "quadrant_1_count": len(q1_notes),
            "quadrant_3_count": len(q3_notes),
            "other_notes_count": len(other_notes),
            "suggested_semitone_shift": 0,
            "warning": None,
            "needs_remediation": False
        }

    @classmethod
    def remediate_drum_clip_octaves(
        cls,
        conn: Any,
        track_index: int,
        clip_index: int = 0,
        semitone_shift: int = -24
    ) -> Dict[str, Any]:
        """
        Transposes all notes in the drum clip by semitone_shift (default -24 semitones / 2 octaves)
        so that notes in Quadrant 3 (C3+) land squarely on Quadrant 1 pads (C1-D#2, pitches 36-51).
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "status": "MOCK_REMEDIATED",
                "transposed_count": 0,
                "semitone_shift": semitone_shift
            }

        raw = conn.send_command("get_clip_notes", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        data = raw.get("result", raw) if isinstance(raw, dict) else raw
        notes = data.get("notes", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])

        if not notes:
            return {
                "status": "error",
                "message": f"No notes found on track {track_index} clip {clip_index} to transpose."
            }

        # Calculate clip length from notes or default 16 beats (4 bars)
        max_end_time = max([float(n.get("start_time", n.get("start", 0.0))) + float(n.get("duration", 0.25)) for n in notes])
        clip_length = max(4.0, ((int(max_end_time) // 4) + 1) * 4.0)

        transposed_notes = []
        for n in notes:
            orig_pitch = int(n.get("pitch", 60))
            new_pitch = max(0, min(127, orig_pitch + semitone_shift))
            start = float(n.get("start_time", n.get("start", 0.0)))
            dur = float(n.get("duration", 0.25))
            vel = int(n.get("velocity", 100))
            transposed_notes.append({
                "pitch": new_pitch,
                "start_time": start,
                "duration": dur,
                "velocity": vel,
                "mute": bool(n.get("mute", False))
            })

        # Delete existing clip in slot to prevent 'Clip slot already has a clip' error
        try:
            conn.send_command("delete_clip", {
                "track_index": track_index,
                "clip_index": clip_index
            })
        except Exception:
            pass

        # Re-create clip to clean slot and push transposed notes
        conn.send_command("create_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "length": clip_length
        })

        conn.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": transposed_notes
        })

        logger.info(
            f"[DrumRackGuard] Successfully transposed {len(transposed_notes)} notes "
            f"on Track {track_index} Clip {clip_index} by {semitone_shift} semitones to Quadrant 1."
        )

        return {
            "status": "success",
            "track_index": track_index,
            "clip_index": clip_index,
            "transposed_count": len(transposed_notes),
            "semitone_shift": semitone_shift,
            "target_quadrant": "Quadrant 1 (C1-D#2, pitches 36-51)",
            "clip_length": clip_length
        }

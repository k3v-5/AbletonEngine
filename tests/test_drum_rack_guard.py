# tests/test_drum_rack_guard.py
import pytest
from engine.instruments.drum_rack_guard import DrumRackGuard, DrumRackEmptyError

class MockEmptyDrumRackConn:
    def send_command(self, cmd, params=None):
        if cmd == "get_drum_rack_pads":
            return {
                "status": "success",
                "result": {
                    "drum_rack_name": "Drum Rack",
                    "active_pad_count": 0,
                    "pads": []
                }
            }
        return {"status": "success"}

class MockPopulatedDrumRackConn:
    def send_command(self, cmd, params=None):
        if cmd == "get_drum_rack_pads":
            return {
                "status": "success",
                "result": {
                    "drum_rack_name": "808 Core Kit",
                    "active_pad_count": 16,
                    "pads": [
                        {"note": 36, "name": "Bass Drum", "devices": [{"name": "Bass Drum"}]},
                        {"note": 37, "name": "Rim Shot", "devices": [{"name": "Rim Shot"}]},
                        {"note": 38, "name": "Snare Drum", "devices": [{"name": "Snare Drum"}]},
                        {"note": 39, "name": "Hand Clap", "devices": [{"name": "Hand Clap"}]},
                        {"note": 42, "name": "Closed Hi Hat", "devices": [{"name": "Closed Hi Hat"}]}
                    ]
                }
            }
        return {"status": "success"}

def test_empty_drum_rack_detected():
    conn = MockEmptyDrumRackConn()
    audit = DrumRackGuard.audit_drum_rack(conn, track_index=1)
    assert audit["is_populated"] is False
    assert audit["populated_pad_count"] == 0
    assert audit["status"] == "EMPTY"

def test_populated_drum_rack_detected():
    conn = MockPopulatedDrumRackConn()
    audit = DrumRackGuard.audit_drum_rack(conn, track_index=1)
    assert audit["is_populated"] is True
    assert audit["populated_pad_count"] == 5
    assert audit["status"] == "POPULATED"

def test_enforce_populated_kit_success():
    conn = MockPopulatedDrumRackConn()
    result = DrumRackGuard.enforce_populated_drum_kit(conn, track_index=1)
    assert result["is_populated"] is True


class MockOctaveMismatchDrumConn:
    def __init__(self):
        self.commands = []
        # Notes in C3 (pitches 60, 62, 64) -> Quadrant 3
        self.clip_notes = [
            {"pitch": 60, "start_time": 0.0, "duration": 0.25, "velocity": 110},
            {"pitch": 62, "start_time": 1.0, "duration": 0.25, "velocity": 100},
            {"pitch": 60, "start_time": 2.0, "duration": 0.25, "velocity": 110},
            {"pitch": 62, "start_time": 3.0, "duration": 0.25, "velocity": 100},
        ]

    def send_command(self, cmd, params=None):
        self.commands.append((cmd, params))
        if cmd == "get_clip_notes":
            return {"status": "success", "result": {"notes": self.clip_notes}}
        if cmd == "add_notes_to_clip":
            self.clip_notes = params.get("notes", [])
            return {"status": "success"}
        if cmd == "create_clip":
            return {"status": "success"}
        return {"status": "success"}


def test_drum_clip_octave_mismatch_detected():
    conn = MockOctaveMismatchDrumConn()
    audit = DrumRackGuard.audit_drum_clip_octaves(conn, track_index=2, clip_index=0)

    assert audit["is_aligned"] is False
    assert audit["status"] == "OCTAVE_MISMATCH_QUADRANT_3"
    assert audit["quadrant_3_count"] == 4
    assert audit["quadrant_1_count"] == 0
    assert audit["suggested_semitone_shift"] == -24
    assert "SILENT" in audit["warning"]
    assert audit["needs_remediation"] is True


def test_drum_clip_octave_remediation_success():
    conn = MockOctaveMismatchDrumConn()
    remedy = DrumRackGuard.remediate_drum_clip_octaves(conn, track_index=2, clip_index=0, semitone_shift=-24)

    assert remedy["status"] == "success"
    assert remedy["transposed_count"] == 4
    assert remedy["semitone_shift"] == -24

    # Verify that the transposed notes are in Quadrant 1 (36 and 38)
    pitches = [n["pitch"] for n in conn.clip_notes]
    assert pitches == [36, 38, 36, 38]

    # Re-audit should now be ALIGNED
    re_audit = DrumRackGuard.audit_drum_clip_octaves(conn, track_index=2, clip_index=0)
    assert re_audit["is_aligned"] is True
    assert re_audit["status"] == "ALIGNED"
    assert re_audit["quadrant_1_count"] == 4
    assert re_audit["quadrant_3_count"] == 0
    assert re_audit["needs_remediation"] is False

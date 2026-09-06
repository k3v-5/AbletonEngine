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

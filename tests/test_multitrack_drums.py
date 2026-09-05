# tests/test_multitrack_drums.py
import pytest
from engine.music.drums.multitrack import MultiTrackDrumEngine, DrumLayerConfig


class MockConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "create_midi_track":
            return {"status": "success", "result": {"track_index": len(self.commands)}}
        return {"status": "success", "result": {}}


def test_multitrack_layers_definition():
    layers = MultiTrackDrumEngine.DRUM_LAYERS
    assert len(layers) == 5
    names = [l.name for l in layers]
    assert "Kick" in names
    assert "Snare" in names
    assert "Clap" in names
    assert "Hi-Hats" in names
    assert "Crash" in names


def test_verified_drum_kits():
    kits = MultiTrackDrumEngine.VERIFIED_DRUM_KITS
    assert "808_core" in kits
    assert "boom_bap" in kits
    assert "query:Drums#FileId_5422" in kits["808_core"]["uri"]


def test_scaffold_drum_tracks():
    conn = MockConnection()
    res = MultiTrackDrumEngine.scaffold_drum_tracks(conn, kit_type="808_core")
    assert res["status"] == "SUCCESS"
    assert res["kit_loaded"] == "808 Core Kit"
    assert len(res["scaffolded_layers"]) == 5


def test_distribute_drum_pattern():
    sample_notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 100}, # Kick
        {"pitch": 38, "start_time": 1.0, "duration": 0.25, "velocity": 95},  # Snare
        {"pitch": 39, "start_time": 1.0, "duration": 0.25, "velocity": 90},  # Clap
        {"pitch": 42, "start_time": 0.5, "duration": 0.125, "velocity": 80}, # Closed Hat
        {"pitch": 49, "start_time": 0.0, "duration": 1.0, "velocity": 110},  # Crash
    ]
    distributed = MultiTrackDrumEngine.distribute_drum_pattern(sample_notes)
    assert len(distributed["Kick"]) == 1
    assert len(distributed["Snare"]) == 1
    assert len(distributed["Clap"]) == 1
    assert len(distributed["Hi-Hats"]) == 1
    assert len(distributed["Crash"]) == 1

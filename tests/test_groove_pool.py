# tests/test_groove_pool.py
import pytest
from engine.music.groove.pool import (
    GroovePreset,
    GroovePoolEngine,
)


class MockConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_session_info":
            return {"tempo": 120.0}
        if cmd == "get_clip_notes":
            return {
                "notes": [
                    {"pitch": 36, "start_time": i * 0.25, "duration": 0.2, "velocity": 100}
                    for i in range(16)
                ]
            }
        return {"status": "ok"}


def test_mpc_60_swing_template():
    dna_50 = GroovePoolEngine.get_preset_dna(preset=GroovePreset.MPC_60, swing_percentage=50.0)
    # Straight 50% swing has 0 ms offset on odd 16ths
    assert dna_50.timing_offsets_ms[1] == 0.0

    dna_60 = GroovePoolEngine.get_preset_dna(preset=GroovePreset.MPC_60, swing_percentage=60.0)
    # 60% swing delays odd 16th steps
    assert dna_60.timing_offsets_ms[1] > 0.0
    assert dna_60.timing_offsets_ms[0] == 0.0  # Downbeat remains anchored


def test_groove_dna_extraction():
    # Construct notes with deliberate delayed offbeats (+20 ms at 120 bpm = 0.04 beats)
    notes = [
        {"pitch": 36, "start_time": 0.0, "velocity": 110},
        {"pitch": 36, "start_time": 0.29, "velocity": 90},  # delayed 16th (0.25 + 0.04)
        {"pitch": 36, "start_time": 0.50, "velocity": 105},
        {"pitch": 36, "start_time": 0.79, "velocity": 88},
    ]
    dna = GroovePoolEngine.extract_groove_dna_from_notes(notes, bpm=120.0)
    assert dna.preset == GroovePreset.CUSTOM_EXTRACTED
    assert dna.swing_percentage > 50.0
    assert dna.timing_offsets_ms[1] > 0.0


def test_apply_groove_to_notes():
    dna = GroovePoolEngine.get_preset_dna(preset=GroovePreset.DILLA_DRUNK)
    raw_notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.2, "velocity": 100},
        {"pitch": 38, "start_time": 1.0, "duration": 0.2, "velocity": 100},  # Backbeat snare step 4
    ]
    swung = GroovePoolEngine.apply_groove_to_notes(raw_notes, dna, bpm=120.0, strength=1.0)
    assert len(swung) == 2
    # Step 4 in Dilla has heavy delayed snare
    assert swung[1]["start_time"] > 1.0
    assert swung[1]["velocity"] > 100


def test_apply_groove_live_adapter():
    conn = MockConnection()
    res = GroovePoolEngine.apply_groove_to_live_clip(
        conn=conn,
        track_indices=[0, 1],
        groove_preset=GroovePreset.SP_1200,
        swing_percentage=62.0,
    )
    assert res["status"] == "success"
    assert len(res["applied_tracks"]) == 2
    cmd_names = [c[0] for c in conn.commands]
    assert "add_notes_to_clip" in cmd_names

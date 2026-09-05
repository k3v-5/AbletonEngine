# tests/test_drum_evolver.py
import pytest
from engine.music.models import NoteEvent
from engine.music.drums.evolver import (
    DrumFillType,
    DrumPatternEvolver
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_bar_4_turnaround():
    base = [NoteEvent(pitch=42, start=i * 0.5, duration=0.2, velocity=90) for i in range(32)]
    evolved = DrumPatternEvolver.inject_bar_4_turnaround(base, loop_bars=4.0)

    # Must contain ghost snare (pitch 38)
    snares = [n for n in evolved if n.pitch == 38]
    assert len(snares) == 1
    assert snares[0].velocity == 45


def test_bar_8_fill():
    base = [NoteEvent(pitch=36, start=i * 1.0, duration=0.5, velocity=100) for i in range(32)]
    evolved = DrumPatternEvolver.inject_bar_8_fill(base, loop_bars=8.0)

    # Must contain toms (50, 47, 45)
    toms = [n for n in evolved if n.pitch in (50, 47, 45)]
    assert len(toms) >= 6


def test_evolve_drum_sequence():
    base_4bars = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=120),
        NoteEvent(pitch=38, start=2.0, duration=0.5, velocity=127),
        NoteEvent(pitch=42, start=1.0, duration=0.2, velocity=90)
    ]
    evolved = DrumPatternEvolver.evolve_drum_sequence(base_4bars, total_bars=16.0)

    assert len(evolved) > len(base_4bars) * 4
    # Crashes on beat 0 and beat 32
    crashes = [n for n in evolved if n.pitch == 49]
    assert len(crashes) >= 2


def test_apply_drum_evolution_adapter():
    adapter = MockAdapter()
    res = DrumPatternEvolver.apply_drum_evolution(
        conn=adapter,
        track_index=13,
        total_bars=16.0
    )
    assert res["status"] == "SUCCESS"
    assert res["evolved_notes_count"] > 20
    cmd_names = [c[0] for c in adapter.commands]
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names

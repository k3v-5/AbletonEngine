# tests/test_counter_melody_arp.py
import pytest
from engine.music.models import Chord
from engine.music.melody.counterpoint import (
    ArpMode,
    CounterpointEngine
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_extract_chord_pitches():
    chord_fm = Chord(root="F", quality="minor", duration=4.0)
    pitches = CounterpointEngine.extract_chord_pitches(chord_fm, base_octave=5)
    assert len(pitches) >= 4
    # F5 is 77, Ab5 is 80, C6 is 84, Eb6 is 87
    assert 77 in pitches
    assert 80 in pitches


def test_guide_tone_counter_melody():
    notes = CounterpointEngine.generate_guide_tone_counter_melody()
    assert len(notes) >= 16
    for n in notes:
        assert n.pitch >= 70 # Higher registers
        assert n.duration > 0
        assert 0 < n.velocity <= 127


def test_modal_arpeggios():
    notes_up = CounterpointEngine.generate_modal_arpeggio(mode=ArpMode.UP)
    assert len(notes_up) >= 32

    notes_down = CounterpointEngine.generate_modal_arpeggio(mode=ArpMode.DOWN)
    assert len(notes_down) >= 32

    notes_converge = CounterpointEngine.generate_modal_arpeggio(mode=ArpMode.CONVERGE)
    assert len(notes_converge) >= 32


def test_apply_counterpoint_adapter():
    adapter = MockAdapter()
    res = CounterpointEngine.apply_counterpoint(
        conn=adapter,
        track_index=4,
        style="counter_melody"
    )
    assert res["status"] == "SUCCESS"
    assert res["notes_generated"] > 0
    cmd_names = [c[0] for c in adapter.commands]
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names

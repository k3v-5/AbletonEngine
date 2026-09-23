# tests/test_note_event_mute.py
import pytest
from engine.music.models import NoteEvent
from engine.music.groove.pocket import GroovePocketEngine, PocketStyle

def test_note_event_accepts_mute_flag():
    note = NoteEvent(
        pitch=60,
        start=0.0,
        duration=1.0,
        velocity=100,
        mute=True
    )
    assert note.mute is True
    d = note.to_dict()
    assert "mute" in d
    assert d["mute"] is True

def test_note_event_mute_default_false():
    note = NoteEvent(pitch=60)
    assert note.mute is False
    assert note.to_dict()["mute"] is False

def test_pocket_engine_preserves_mute():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100, mute=False),
        NoteEvent(pitch=38, start=1.0, duration=0.5, velocity=90, mute=True),
    ]
    pocketed = GroovePocketEngine.apply_pocket_to_notes(
        notes=notes,
        role="drums",
        pocket_style=PocketStyle.ATLANTA_TRAP,
        strength=1.0
    )
    assert len(pocketed) == 2
    assert pocketed[0].mute is False
    assert pocketed[1].mute is True

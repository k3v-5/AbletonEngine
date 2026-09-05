# tests/test_groove_pocket.py
import pytest
from engine.music.groove.pocket import GroovePocketEngine, PocketStyle, ROLE_POCKET_BUDGETS
from engine.music.models import NoteEvent


def test_pocket_timing_and_velocity_jitter():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100),
        NoteEvent(pitch=38, start=1.0, duration=0.5, velocity=100),
        NoteEvent(pitch=42, start=1.5, duration=0.2, velocity=90),
    ]

    pocketed = GroovePocketEngine.apply_pocket_to_notes(
        notes=notes,
        role="snare",
        pocket_style=PocketStyle.ATLANTA_TRAP,
        tempo=120.0,
        strength=1.0,
        seed=42
    )

    assert len(pocketed) == len(notes)
    assert pocketed[1].start != notes[1].start
    assert 1 <= pocketed[0].velocity <= 127
    assert 1 <= pocketed[1].velocity <= 127


def test_pocket_zero_strength():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100),
        NoteEvent(pitch=38, start=2.0, duration=0.5, velocity=110),
    ]

    pocketed = GroovePocketEngine.apply_pocket_to_notes(
        notes=notes,
        role="kick",
        pocket_style=PocketStyle.DARK_RAGE,
        tempo=140.0,
        strength=0.0
    )

    for orig, p in zip(notes, pocketed):
        assert p.start == orig.start
        assert p.velocity == orig.velocity
        assert p.duration == orig.duration


def test_pocket_styles_exist():
    for style in [PocketStyle.ATLANTA_TRAP, PocketStyle.NEO_SOUL_DILLA, PocketStyle.BOOM_BAP, PocketStyle.DARK_RAGE, PocketStyle.ORGANIC_HUMAN]:
        assert style in ROLE_POCKET_BUDGETS
        assert "kick" in ROLE_POCKET_BUDGETS[style]
        assert "snare" in ROLE_POCKET_BUDGETS[style]
        assert "hihat" in ROLE_POCKET_BUDGETS[style]


def test_chord_strum_roll():
    chord_notes = [
        NoteEvent(pitch=53, start=0.0, duration=3.8, velocity=80),
        NoteEvent(pitch=56, start=0.0, duration=3.8, velocity=80),
        NoteEvent(pitch=60, start=0.0, duration=3.8, velocity=80),
        NoteEvent(pitch=63, start=0.0, duration=3.8, velocity=80),
        NoteEvent(pitch=67, start=0.0, duration=3.8, velocity=80),
    ]

    strummed = GroovePocketEngine.apply_chord_strum(
        notes=chord_notes,
        tempo=120.0,
        strum_ms=15.0,
        direction="up",
        velocity_tilt=0.2,
        seed=100
    )

    assert len(strummed) == 5
    for i in range(len(strummed) - 1):
        assert strummed[i].start <= strummed[i + 1].start

    assert strummed[0].pitch == 53
    assert strummed[-1].pitch == 67
    assert strummed[-1].start > strummed[0].start
    assert strummed[-1].velocity >= strummed[0].velocity


def test_chord_strum_down_direction():
    chord_notes = [
        NoteEvent(pitch=48, start=4.0, duration=2.0, velocity=85),
        NoteEvent(pitch=52, start=4.0, duration=2.0, velocity=85),
        NoteEvent(pitch=55, start=4.0, duration=2.0, velocity=85),
    ]

    strummed = GroovePocketEngine.apply_chord_strum(
        notes=chord_notes,
        tempo=120.0,
        strum_ms=10.0,
        direction="down",
        seed=42
    )

    assert len(strummed) == 3
    assert strummed[0].pitch == 55
    assert strummed[-1].pitch == 48

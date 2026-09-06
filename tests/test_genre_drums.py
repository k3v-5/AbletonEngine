# tests/test_genre_drums.py
import pytest
from engine.music.drums.genre_grooves import (
    GenreRhythmGrooveEngine,
    GenreDrumStyle
)
from engine.music.models import NoteEvent


def test_supported_genres_list():
    genres = GenreRhythmGrooveEngine.get_supported_genres()
    assert "trap" in genres
    assert "house" in genres
    assert "neo_soul" in genres
    assert "reggaeton" in genres
    assert "synthwave" in genres


def test_generate_trap_rhythm():
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("trap", length_bars=4, tempo=140.0)
    assert len(notes) > 0
    # Claps/snares on beat 2.0 (third beat in 4/4 half-time)
    claps = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.CLAP_PITCH]
    assert len(claps) == 4
    for i, c in enumerate(claps):
        assert abs(c.start - (i * 4.0 + 2.0)) < 0.1

    # Hi-hats present
    hats = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.CLOSED_HAT_PITCH]
    assert len(hats) >= 24


def test_generate_house_four_on_floor():
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("house", length_bars=2, tempo=126.0)
    kicks = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    # 2 bars * 4 kicks = 8 kicks
    assert len(kicks) == 8
    for i, k in enumerate(kicks):
        assert abs(k.start - (i * 1.0)) < 0.05

    # Offbeat open hats (0.5, 1.5, 2.5, etc.)
    open_hats = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.OPEN_HAT_PITCH]
    assert len(open_hats) == 8
    for i, h in enumerate(open_hats):
        assert abs(h.start - (i * 1.0 + 0.5)) < 0.05


def test_generate_reggaeton_dembow():
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("reggaeton", length_bars=2, tempo=95.0)
    kicks = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    snares = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.SNARE_PITCH]
    assert len(kicks) == 8
    # Dembow snares on 0.75, 1.5, 2.75, 3.5 per bar = 8 snares across 2 bars
    assert len(snares) == 8
    first_bar_snares = [s.start for s in snares[:4]]
    expected = [0.75, 1.50, 2.75, 3.50]
    for actual, exp in zip(first_bar_snares, expected):
        assert abs(actual - exp) < 0.05


def test_generate_neo_soul_laid_back_and_ghosts():
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("neo_soul", length_bars=2, tempo=88.0)
    snares = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.SNARE_PITCH]
    # Check for presence of low velocity ghost notes (< 50 velocity)
    ghosts = [s for s in snares if s.velocity < 50]
    assert len(ghosts) >= 2


def test_mpc_swing_application():
    base_notes = [
        NoteEvent(pitch=42, start=0.0, duration=0.1, velocity=80),
        NoteEvent(pitch=42, start=0.25, duration=0.1, velocity=80),
        NoteEvent(pitch=42, start=0.50, duration=0.1, velocity=80),
        NoteEvent(pitch=42, start=0.75, duration=0.1, velocity=80),
    ]
    swung = GenreRhythmGrooveEngine.apply_mpc_swing(base_notes, swing_percent=0.60)
    # Downbeats 0.0 and 0.5 untouched
    assert swung[0].start == 0.0
    assert swung[2].start == 0.5
    # Odd 16ths shifted forward
    assert swung[1].start > 0.25
    assert swung[3].start > 0.75

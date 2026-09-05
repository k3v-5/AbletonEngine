# tests/test_phrase_evolver.py
import pytest
from engine.music.variation.phrase_evolver import PhraseEvolver, PhraseFunction
from engine.music.models import NoteEvent


def test_phrase_evolver_statement_a():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100),
        NoteEvent(pitch=38, start=2.0, duration=0.5, velocity=110),
    ]

    evolved = PhraseEvolver.evolve_phrase(
        notes=notes,
        phrase_index=0,
        role="drums"
    )

    assert len(evolved) == len(notes)
    for orig, ev in zip(notes, evolved):
        assert ev.pitch == orig.pitch
        assert ev.start == orig.start
        assert ev.velocity == orig.velocity


def test_phrase_evolver_a_prime_drums():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100),
        NoteEvent(pitch=42, start=12.0, duration=0.2, velocity=90),
        NoteEvent(pitch=42, start=14.0, duration=0.2, velocity=90),
    ]

    evolved = PhraseEvolver.evolve_phrase(
        notes=notes,
        phrase_index=1,
        role="drums",
        seed=42
    )

    # A' for drums adds ghost snare and/or hat roll
    assert len(evolved) >= len(notes)
    pitches = [n.pitch for n in evolved]
    # Snare (pitch 38) ghost note injected
    assert 38 in pitches


def test_phrase_evolver_departure_b():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=120),  # kick bar 1
        NoteEvent(pitch=36, start=4.0, duration=0.5, velocity=120),  # kick bar 2
        NoteEvent(pitch=38, start=2.0, duration=0.5, velocity=110),
    ]

    evolved = PhraseEvolver.evolve_phrase(
        notes=notes,
        phrase_index=2,
        role="drums",
        seed=42
    )

    # Kick in bar 1 (start < 4.0) should drop out for contrast
    early_kicks = [n for n in evolved if n.pitch == 36 and n.start < 4.0]
    assert len(early_kicks) == 0


def test_phrase_evolver_climax_a_double_prime():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100),
        NoteEvent(pitch=38, start=2.0, duration=0.5, velocity=100),
        NoteEvent(pitch=42, start=15.5, duration=0.5, velocity=100), # Very end of phrase
    ]

    evolved = PhraseEvolver.evolve_phrase(
        notes=notes,
        phrase_index=3,
        role="drums",
        seed=42
    )

    # Pre-drop silence clears notes in the last beat (>= 15.0)
    assert not any(n.start >= 15.0 and n.pitch == 42 for n in evolved)
    # Turnaround snare roll injected
    turnaround_snares = [n for n in evolved if n.pitch == 38 and n.start >= 14.0]
    assert len(turnaround_snares) == 4

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


def test_generate_cumbia_guira_and_tumbao():
    """Validates authentic cumbia continuous güira scrape (16ths), tumbao congas, and timbales."""
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("cumbia", length_bars=4, tempo=92.0)
    assert len(notes) > 0

    # Güira (closed hats) should have 16 hits per bar * 4 bars = 64 hits
    guira_hits = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.CLOSED_HAT_PITCH]
    assert len(guira_hits) == 64

    # The 3rd sixteenth of each beat should be the accented scrape (velocity > 100)
    accents = [n for n in guira_hits if n.velocity >= 110]
    assert len(accents) >= 16

    # Kicks on 1 and 3
    kicks = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    assert len(kicks) >= 8

    # Conga slaps (pitch 37) on beats 2 & 4
    slaps = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.PERC_PITCH]
    assert len(slaps) == 8


def test_generate_rock_driving_backbeat():
    """Validates rock acoustic kit: heavy snare crack on 2 & 4, 8th-note hats, crash on bar 1."""
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("rock", length_bars=4, tempo=128.0)
    assert len(notes) > 0

    # Snares on 2 & 4 with velocity >= 120
    snares = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.SNARE_PITCH]
    assert len(snares) >= 8
    for s in snares[:8]:
        assert s.velocity >= 120

    # Kicks on 1 and 3
    kicks = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    assert len(kicks) >= 8

    # 8th-note hi-hats (8 hits per bar * 4 bars = 32 hits)
    hats = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.CLOSED_HAT_PITCH]
    assert len(hats) == 32

    # Crash on beat 0.0 of bar 0
    crashes = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.OPEN_HAT_PITCH]
    assert len(crashes) >= 1
    assert crashes[0].start == 0.0


def test_generate_afrobeat_cross_rhythm():
    """Validates Afrobeat syncopated kick cross-rhythm and rimshot accents."""
    notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("afrobeat", length_bars=2, tempo=104.0)
    assert len(notes) > 0

    # Kicks on 0.0, 1.75, 2.5 per bar = 6 across 2 bars
    kicks = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    assert len(kicks) == 6

    # Rimshots on 1.5, 2.75, 3.5 per bar = 6 across 2 bars
    rimshots = [n for n in notes if n.pitch == GenreRhythmGrooveEngine.SNARE_PITCH]
    assert len(rimshots) == 6


def test_generate_edm_and_dnb():
    """Validates EDM 4-on-the-floor and DnB 174 BPM 2-step breakbeat."""
    # EDM
    edm_notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("edm", length_bars=2, tempo=128.0)
    edm_kicks = [n for n in edm_notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    assert len(edm_kicks) == 8  # 4-on-the-floor * 2 bars

    # Drum & Bass
    dnb_notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("drum_and_bass", length_bars=2, tempo=174.0)
    dnb_kicks = [n for n in dnb_notes if n.pitch == GenreRhythmGrooveEngine.KICK_PITCH]
    assert len(dnb_kicks) == 4  # 2-step kicks (0.0, 2.75) * 2 bars


def test_generate_pop():
    """Validates commercial pop pattern."""
    pop_notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("pop", length_bars=2, tempo=120.0)
    pop_claps = [n for n in pop_notes if n.pitch == GenreRhythmGrooveEngine.CLAP_PITCH]
    assert len(pop_claps) == 4


def test_offer_genre_options_structure():
    """Validates that offer_genre_options groups genres into required categories and states non-limiting nature."""
    menu = GenreRhythmGrooveEngine.offer_genre_options()
    assert menu["status"] == "success"
    cats = menu["catalog"]
    assert "rap_trap" in cats
    assert "cumbia" in cats
    assert "electro" in cats
    assert "urbano_pop" in cats
    assert "rock" in cats

    # Check non-limiting guarantee
    assert "extra" in menu["notice"].lower()

    # Filter test
    cumbia_filter = GenreRhythmGrooveEngine.offer_genre_options(category="cumbia")
    assert "cumbia" in cumbia_filter["catalog"]


def test_get_genre_descriptor_and_freeform_fallback():
    """Validates specific genre lookup and safe fallback for custom/freeform uncataloged genres."""
    # Existing genre
    trap_desc = GenreRhythmGrooveEngine.get_genre_descriptor("trap")
    assert trap_desc["status"] == "found"
    assert trap_desc["profile"]["bpm_default"] == 140.0

    # Cumbia
    cumbia_desc = GenreRhythmGrooveEngine.get_genre_descriptor("cumbia")
    assert cumbia_desc["status"] == "found"
    assert "güira" in cumbia_desc["profile"]["groove"].lower()

    # Custom / Freeform fallback
    custom_desc = GenreRhythmGrooveEngine.get_genre_descriptor("polka_metal_fusion")
    assert custom_desc["status"] == "custom"
    assert "libre" in custom_desc["profile"]["groove"].lower()


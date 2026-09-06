"""
tests/test_musical_os_and_prosody.py
Unit tests for the Musical OS Layer:
1. SongState & MusicalSection serialization and LLM prompt summary.
2. MusicAnalyzer melodic range, density, contour, and prosodic blueprint extraction.
3. LyricEngine syllabification, stress detection, and closed-loop validation.
"""

import pytest
from engine.music.song_state import SongState, MusicalSection, MelodicState, LyricBlueprint, ProsodicConstraint
from engine.music.analyzer import MusicAnalyzer, pitch_to_name
from engine.vocal.lyric_engine import LyricEngine


def test_pitch_to_name_conversion():
    """Confirms MIDI pitch numbers convert accurately to scientific pitch notation."""
    assert pitch_to_name(60) == "C4"
    assert pitch_to_name(61) == "C#4"
    assert pitch_to_name(69) == "A4"
    assert pitch_to_name(72) == "C5"
    assert pitch_to_name(73) == "C#5"
    assert pitch_to_name(36) == "C2"


def test_song_state_serialization_and_llm_summary():
    """Confirms SongState serializes cleanly and produces a compact LLM prompt summary."""
    sec1 = MusicalSection(
        name="1. Intro",
        bars=(0, 8),
        energy=0.25,
        harmony=["F#m", "D", "A", "E"],
        mood="mysterious",
        narrative_role="establish_atmosphere"
    )
    sec2 = MusicalSection(
        name="2. Chorus",
        bars=(24, 40),
        energy=0.85,
        harmony=["A", "E", "F#m", "D"],
        melody=MelodicState(
            track_name="Lead Vocal",
            pitch_range="E4-C#5",
            lowest_pitch=64,
            highest_pitch=73,
            density=0.70,
            rhythmic_style="syncopated",
            contour="ascending",
            hook=True
        ),
        mood="cathartic",
        narrative_role="central_message",
        lyric_blueprint=LyricBlueprint(
            section_name="Chorus",
            bars=(24, 40),
            rhyme_scheme="AABB",
            phrases_count=4,
            syllables_per_phrase=[7, 8, 7, 9],
            narrative_role="main_hook",
            emotional_theme="defiance"
        )
    )

    song = SongState(
        title="Test Anthem",
        tempo=96.0,
        key="F#",
        scale="minor",
        sections=[sec1, sec2],
        tracks_installed=["Lead Vocal", "Rhodes", "Bass", "Drums"],
        overall_energy_curve=[0.25, 0.85]
    )

    d = song.to_dict()
    assert d["song"]["title"] == "Test Anthem"
    assert d["song"]["tempo"] == 96.0
    assert d["song"]["key"] == "F# minor"
    assert len(d["sections"]) == 2
    assert d["sections"][1]["melody"]["hook"] is True

    summary = song.to_llm_prompt_summary()
    assert "=== SONG STATE: 'Test Anthem' ===" in summary
    assert "F# minor" in summary
    assert "[2. Chorus]" in summary
    assert "Range E4-C#5" in summary
    assert "AABB" in summary


def test_music_analyzer_melodic_features():
    """Confirms MusicAnalyzer computes pitch range, contour, and density from raw MIDI notes."""
    # Ascending scale from C4 (60) to A4 (69)
    notes = [
        {"pitch": 60, "start_time": 0.0, "duration": 0.5},
        {"pitch": 62, "start_time": 0.5, "duration": 0.5},
        {"pitch": 64, "start_time": 1.0, "duration": 0.5},
        {"pitch": 65, "start_time": 1.5, "duration": 0.5},
        {"pitch": 67, "start_time": 2.0, "duration": 0.5},
        {"pitch": 69, "start_time": 2.5, "duration": 1.0}
    ]

    mel = MusicAnalyzer.analyze_melody_clip(notes, track_name="Vocal Topline")
    assert mel.pitch_range == "C4-A4"
    assert mel.lowest_pitch == 60
    assert mel.highest_pitch == 69
    assert mel.contour == "ascending"
    assert mel.notes_count == 6


def test_lyric_engine_syllable_and_stress_analysis():
    """Confirms LyricEngine correctly counts syllables and detects tonic stress."""
    # Spanish: "corazón" -> 3 syllables, stress on 3 (aguda)
    count, tonic, syls = LyricEngine.count_syllables_word("corazón", language="es")
    assert count == 3
    assert tonic == 3

    # Spanish: "cielo" -> 2 syllables, stress on 1 (llana)
    count, tonic, syls = LyricEngine.count_syllables_word("cielo", language="es")
    assert count == 2
    assert tonic == 1

    # Full line analysis
    line_res = LyricEngine.analyze_line("quiero cantar hoy", language="es")
    assert line_res["word_count"] == 3
    assert line_res["syllable_count"] >= 4


def test_lyric_engine_closed_loop_validator_feedback():
    """
    Confirms LyricEngine rejects mismatched syllable lines and generates
    corrective feedback for the LLM.
    """
    # 1. Reject when syllable count is wrong
    res_mismatch = LyricEngine.validate_line_against_constraint(
        text_line="hoy te busco en la noche oscura de abril",
        target_syllables=6, # Melody only has 6 notes, text has ~12
        language="es"
    )
    assert res_mismatch["is_valid"] is False
    assert len(res_mismatch["errors"]) > 0
    assert "Exceso de sílabas" in res_mismatch["errors"][0]
    assert res_mismatch["correction_prompt"] is not None

    # 2. Accept when syllables match target exactly
    res_match = LyricEngine.validate_line_against_constraint(
        text_line="yo te busco amor",  # yo (1), te (1), bus-co (2), a-mor (2) -> 6 syllables
        target_syllables=6,
        language="es"
    )
    assert res_match["is_valid"] is True
    assert res_match["actual_syllables"] == 6

    # 3. Peak vowel resonance check on high note >= A4
    res_vowel = LyricEngine.validate_line_against_constraint(
        text_line="dime si tu",
        target_syllables=4,
        peak_syllable_idx=4, # syllable 4 is 'tu' with closed vowel 'u'
        peak_pitch=73,       # C#5 (high note)
        language="es"
    )
    assert any("Advertencia de resonancia vocal" in adv for adv in res_vowel["advisories"])

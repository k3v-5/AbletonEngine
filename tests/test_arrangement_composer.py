# tests/test_arrangement_composer.py
import pytest
from engine.arrangement.arrangement_composer import ArrangementComposer, ArrangementSection

def test_arrangement_sections_structure():
    assert len(ArrangementComposer.SECTIONS) == 5
    sec_names = [s.name for s in ArrangementComposer.SECTIONS]
    assert "1. INTRO" in sec_names
    assert "2. VERSE" in sec_names
    assert "3. PRE-DROP" in sec_names
    assert "4. DROP" in sec_names
    assert "5. OUTRO" in sec_names

    total_beats = sum(s.length_beats for s in ArrangementComposer.SECTIONS)
    assert total_beats == 128.0

def test_drums_pattern_variation():
    intro_drums = ArrangementComposer._drums_pattern("INTRO", 32.0)
    verse_drums = ArrangementComposer._drums_pattern("VERSE", 32.0)
    predrop_drums = ArrangementComposer._drums_pattern("PRE_DROP", 16.0)
    drop_drums = ArrangementComposer._drums_pattern("DROP", 32.0)
    outro_drums = ArrangementComposer._drums_pattern("OUTRO", 16.0)

    # Intro is quiet/sparse
    assert len(intro_drums) < len(verse_drums)

    # Pre-drop has snare rolls but SILENCE in the last bar (vacuum drop, beats 12-16)
    assert len(predrop_drums) > 0
    predrop_times = [n["start_time"] for n in predrop_drums]
    assert all(t < 12.0 for t in predrop_times), "Bar 4 of Pre-drop must be completely silent!"

    # Drop has maximum density with kicks (pitch 36) and hard snares (pitch 38)
    drop_kicks = [n for n in drop_drums if n["pitch"] == 36]
    assert len(drop_kicks) >= 10, "Drop must contain heavy 808 kick rhythm!"

def test_sub_bass_pattern_variation():
    intro_bass = ArrangementComposer._sub_bass_pattern("INTRO", 32.0)
    assert len(intro_bass) == 0, "Intro must have zero sub bass to maximize drop dynamic contrast!"

    predrop_bass = ArrangementComposer._sub_bass_pattern("PRE_DROP", 16.0)
    predrop_bass_times = [n["start_time"] for n in predrop_bass]
    assert all(t < 12.0 for t in predrop_bass_times), "Sub bass must be 100% silent during the 1-bar vacuum drop!"

    drop_bass = ArrangementComposer._sub_bass_pattern("DROP", 32.0)
    assert len(drop_bass) > 0
    # Verify pitch variation/slides in drop
    pitches = set(n["pitch"] for n in drop_bass)
    assert len(pitches) >= 3, "Drop 808 must feature multiple root notes and slides!"

def test_lead_pattern_variation():
    intro_lead = ArrangementComposer._lead_pattern("INTRO", 32.0)
    assert len(intro_lead) == 0

    drop_lead = ArrangementComposer._lead_pattern("DROP", 32.0)
    assert len(drop_lead) >= 20, "Drop lead must feature the full melodic hook!"

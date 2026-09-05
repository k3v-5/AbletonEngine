# tests/test_beat_switch_reharmonization.py
import pytest
from engine.music.harmony.reharmonizer import ModalReharmonizer, ReharmStyle
from engine.arrangement.structure.beat_switch import BeatSwitchOrchestrator
from engine.music.models import Chord


def test_secondary_dominants():
    chords = [
        Chord(root="F", quality="minor", duration=4.0),
        Chord(root="Db", quality="major", duration=4.0),
    ]

    reharm = ModalReharmonizer.reharmonize_progression(
        chords=chords,
        style=ReharmStyle.SECONDARY_DOMINANTS,
        tension_level=0.7
    )

    # Target is Db -> V7 of Db is Ab
    sec_chord = next(c for c in reharm if "V7/Db" in c.roman_numeral)
    assert sec_chord.root == "Ab"
    assert sec_chord.duration == 1.0


def test_tritone_substitutions():
    chords = [
        Chord(root="F", quality="minor", duration=4.0),
        Chord(root="Db", quality="major", duration=4.0),
    ]

    reharm = ModalReharmonizer.reharmonize_progression(
        chords=chords,
        style=ReharmStyle.TRITONE_SUBSTITUTIONS,
        tension_level=0.7
    )

    # Tritone sub of V7/Db (Ab7) is D7 (half step above Db)
    sub_chord = next(c for c in reharm if "subV7/Db" in c.roman_numeral)
    assert sub_chord.root == "D"


def test_beat_switch_orchestrator():
    plan = BeatSwitchOrchestrator.plan_beat_switch(
        switch_bar=33.0,
        current_bpm=138.0,
        target_bpm=92.0,
        target_genre="lofi_soul",
        transition_mode="instant_cut"
    )

    assert plan["status"] == "SUCCESS"
    assert plan["switch_beat"] == 128.0 # (33 - 1) * 4
    assert len(plan["tempo_points"]) == 2
    # Instant step change on downbeat
    assert plan["tempo_points"][0]["value"] == 138.0
    assert plan["tempo_points"][1]["value"] == 92.0
    assert len(plan["section_markers"]) == 2

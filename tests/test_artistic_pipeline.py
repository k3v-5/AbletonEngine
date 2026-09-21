# tests/test_artistic_pipeline.py
import pytest
from engine.production.contract.artistic_pipeline import (
    ArtisticInterventionPipeline,
    LayeredAuditionPlan,
    AuditionLayer,
    InvariantCheckResult
)
from engine.production.contract.musical_memory import MusicalMemory


def test_layered_audition_plan_solo_states():
    plan = LayeredAuditionPlan(
        target_track_name="Emotional Piano",
        target_track_index=5,
        bass_track_index=4,
        lead_track_index=7,
        section_name="Hook 1"
    )

    # 1. Target solo
    assert plan.get_daw_solo_states(AuditionLayer.TARGET_SOLO) == {5: True}

    # 2. Target + Bass
    assert plan.get_daw_solo_states(AuditionLayer.TARGET_PLUS_BASS) == {5: True, 4: True}

    # 3. Target + Lead
    assert plan.get_daw_solo_states(AuditionLayer.TARGET_PLUS_LEAD) == {5: True, 7: True}

    # 4. Full arrangement (unsolo all)
    assert plan.get_daw_solo_states(AuditionLayer.FULL_ARRANGEMENT) == {}


def test_verify_physical_invariants():
    notes_orig = [
        {"pitch": 42, "start_time": 0.0, "duration": 3.0, "velocity": 90},
        {"pitch": 54, "start_time": 0.0, "duration": 3.0, "velocity": 90},
        {"pitch": 66, "start_time": 0.0, "duration": 3.0, "velocity": 90},
    ]
    notes_intervened = [
        {"pitch": 42, "start_time": 0.0, "duration": 2.9, "velocity": 68},
        {"pitch": 54, "start_time": 0.015, "duration": 2.88, "velocity": 82},
        {"pitch": 66, "start_time": 0.030, "duration": 2.87, "velocity": 96},
    ]

    # Clean invariant check
    res = ArtisticInterventionPipeline.verify_physical_invariants(
        notes_orig, notes_intervened, target_track_name="Piano", collateral_modified_tracks=[]
    )
    assert res.is_valid is True
    assert res.pitches_preserved is True
    assert res.notes_count_before == 3
    assert res.notes_count_after == 3
    assert len(res.collateral_tracks_modified) == 0

    # Failing invariant check (modified pitch)
    corrupted_notes = [
        {"pitch": 43, "start_time": 0.0, "duration": 2.9, "velocity": 68},
        {"pitch": 54, "start_time": 0.015, "duration": 2.88, "velocity": 82},
        {"pitch": 66, "start_time": 0.030, "duration": 2.87, "velocity": 96},
    ]
    res_fail = ArtisticInterventionPipeline.verify_physical_invariants(
        notes_orig, corrupted_notes, target_track_name="Piano", collateral_modified_tracks=["Drums"]
    )
    assert res_fail.is_valid is False
    assert res_fail.pitches_preserved is False
    assert "Drums" in res_fail.collateral_tracks_modified


def test_audit_context_interactions():
    piano_notes = [
        {"pitch": 42, "start_time": 0.0, "duration": 3.0, "velocity": 68},
        {"pitch": 66, "start_time": 0.0, "duration": 3.0, "velocity": 90},
    ]
    lead_notes = [
        {"pitch": 69, "start_time": 2.0, "duration": 1.5, "velocity": 100},
        {"pitch": 73, "start_time": 4.0, "duration": 1.5, "velocity": 100},
    ]
    bass_notes = [
        {"pitch": 30, "start_time": 0.0, "duration": 1.5, "velocity": 110},
        {"pitch": 30, "start_time": 2.5, "duration": 1.5, "velocity": 105},
    ]
    kick_notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 115},
        {"pitch": 36, "start_time": 4.0, "duration": 0.25, "velocity": 115},
    ]

    report = ArtisticInterventionPipeline.audit_context_interactions(
        piano_notes=piano_notes,
        lead_notes=lead_notes,
        bass_notes=bass_notes,
        kick_notes=kick_notes,
        section_name="Hook 1"
    )

    assert "piano_lead_space" in report
    assert "piano_bass_interference" in report
    assert "kick_bass_pocket" in report
    assert report["piano_bass_interference"]["low_piano_notes_count"] == 1


def test_musical_memory_narrative_update():
    memory = MusicalMemory(song_id="test_song")
    milestone = ArtisticInterventionPipeline.update_musical_memory_narrative(
        memory=memory,
        section_name="Hook 1",
        element="Emotional Piano",
        action="PERFORMATIVE_REARTICULATION"
    )
    assert milestone.element == "Emotional Piano"
    assert milestone.section == "Hook 1"
    assert "PERFORMATIVE_REARTICULATION" in milestone.action
    assert len(memory.milestones) == 1


def test_generate_artistic_dilemmas_and_progression():
    dilemmas = ArtisticInterventionPipeline.generate_artistic_dilemmas(
        section_name="Hook 1"
    )
    assert len(dilemmas) == 3
    paths = [d["path"] for d in dilemmas]
    assert any("DRUMS" in p for p in paths)
    assert any("LEAD" in p for p in paths)
    assert any("CONSERVAR" in p for p in paths)

    progression = ArtisticInterventionPipeline.evaluate_section_progression_readiness("Hook 1")
    assert progression["next_target_section"] == "Verse 2"
    assert len(progression["roadmap"]) == 4

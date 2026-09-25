# tests/test_world_class_producer_framework.py
"""
Test Suite for World-Class Producer Framework (WCPF):
1. Verifies Contextual Transition Catalog across Trap, Rap, Reggaeton, Electro, and Cinematic.
2. Verifies that every registered track must have sound in at least one section of the song.
3. Verifies that orchestral Tacet / section rests are permitted when the track plays in at least one section.
4. Verifies role-based genre & BPM automatic calibration (eliminating blind 120.0 fallback).
"""

import pytest
from engine.arrangement.transitions.contextual_catalog import ContextualTransitionCatalog
from engine.production.copilot.phases.phase_6.gatekeepers import Phase6Gatekeepers
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_1_tracks import Phase1TracksHandler


def test_contextual_transition_catalog_genres():
    """Verifies that all 5 genres return specialized, rich transition blueprints."""
    genres = ["TRAP", "RAP", "REGGAETON", "ELECTRO", "CINEMATIC"]
    for g in genres:
        transitions = ContextualTransitionCatalog.get_transitions_for_genre(g)
        assert len(transitions) >= 2, f"Genre {g} must have at least 2 transitions"
        for t in transitions:
            assert t.name
            assert t.description
            assert t.duration_bars > 0
            assert t.pre_drop_vacuum_beats >= 0.0
            assert t.musical_purpose != ""
            d = t.to_dict()
            assert "automation_directives" in d

        # Format menu verification
        menu_text = ContextualTransitionCatalog.format_transition_menu_for_prompt(g)
        assert len(menu_text) > 20
        assert "⚡" in menu_text


def test_check_every_track_has_sound_blocks_totally_silent_track():
    """Verifies that an instrument with zero notes in 100% of the song triggers TRACK_COMPLETELY_SILENT_ERROR."""
    class DummySession:
        def __init__(self):
            self.data = {"custom_notes": {}}
        def _save_state(self):
            pass

    session = DummySession()
    tracks = [
        {"index": 0, "name": "Drums", "role": "DRUMS", "notes_count": 16, "is_audio": False},
        {"index": 1, "name": "Lead Synth", "role": "LEAD", "notes_count": 0, "is_audio": False},
    ]
    sections = [
        {"name": "Intro", "bars": 8},
        {"name": "Verse", "bars": 16},
    ]

    custom_notes_map = {
        (0, 0): [{"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 100}]
    }

    result = Phase6Gatekeepers.check_every_track_has_sound(
        session=session,
        tracks=tracks,
        sections=sections,
        custom_notes_map=custom_notes_map,
        is_test_env=False
    )

    assert result is not None
    assert result["status"] == "TRACK_COMPLETELY_SILENT_ERROR"
    assert "Lead Synth" in result["totally_silent_tracks"]


def test_check_every_track_has_sound_allows_orchestral_tacet():
    """Verifies that Tacet / silence in Intro/Verse is fully respected if the track plays in Chorus."""
    class DummySession:
        def __init__(self):
            self.data = {"custom_notes": {}}
        def _save_state(self):
            pass

    session = DummySession()
    tracks = [
        {"index": 0, "name": "Cello Solo", "role": "STRINGS", "notes_count": 0, "is_audio": False},
        {"index": 1, "name": "Orchestral Brass", "role": "BRASS", "notes_count": 0, "is_audio": False},
    ]
    sections = [
        {"name": "Verse 1", "bars": 16},
        {"name": "Chorus (Climax)", "bars": 16},
    ]

    # Cello plays in Verse 1, Brass rests in Verse 1 (Tacet) but plays in Chorus
    custom_notes_map = {
        (0, 0): [{"pitch": 48, "start_time": 0.0, "duration": 4.0, "velocity": 85}],  # Cello in Verse
        (1, 1): [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 110}]  # Brass in Chorus
    }

    result = Phase6Gatekeepers.check_every_track_has_sound(
        session=session,
        tracks=tracks,
        sections=sections,
        custom_notes_map=custom_notes_map,
        is_test_env=False
    )

    # Both tracks play in at least one section: must pass!
    assert result is None


def test_role_based_genre_and_bpm_inference():
    """Verifies that 808 Bass automatically infers Trap and 140.0 BPM, eliminating 120.0 default."""
    session = CopilotGuidedSession()
    session.data = {"preflight_clean": {}}
    handler = Phase1TracksHandler()

    # Pass roles without mentioning the word 'trap' in text
    user_input = "Kick, 808 Bass, Hi-Hats, Synth Lead"
    res = handler.handle(session, conn=None, user_input=user_input)

    assert session.data.get("genre") == "trap"
    assert session.data.get("bpm") == 140.0

    # Test Reggaeton Dembow inference
    session2 = CopilotGuidedSession()
    session2.data = {"preflight_clean": {}}
    user_input2 = "Dembow, Sub Bass, Sintetizador, Coros"
    res2 = handler.handle(session2, conn=None, user_input=user_input2)

    assert session2.data.get("genre") == "reggaeton"
    assert session2.data.get("bpm") == 94.0

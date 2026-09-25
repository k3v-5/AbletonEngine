"""
Tests for Phase 4: Migration of Gatekeepers to Structural Decision Contracts.
Verifies that Phase 6 Gatekeepers distinguish intentional Tacet / artistic decisions
from lazy omissions and forgotten tracks via StructuralDecisionContract.
"""

import pytest
from engine.production.copilot.phases.phase_6.gatekeepers import Phase6Gatekeepers


class MockSession:
    def __init__(self, structural_contracts=None):
        self.data = {
            "custom_notes": {},
            "structural_contracts": structural_contracts or {},
        }

    def _save_state(self):
        pass


def test_gatekeeper_blocks_forgotten_silent_track_without_contract():
    session = MockSession()
    tracks = [
        {"index": 0, "name": "Drums", "role": "DRUMS", "notes_count": 32, "is_audio": False},
        {"index": 1, "name": "Forgotten Strings", "role": "STRINGS", "notes_count": 0, "is_audio": False},
    ]
    sections = [{"name": "Intro", "bars": 8}, {"name": "Verse", "bars": 16}]

    result = Phase6Gatekeepers.check_every_track_has_sound(
        session=session,
        tracks=tracks,
        sections=sections,
        custom_notes_map={(0, 0): [{"pitch": 36}]},
        is_test_env=False,
    )

    assert result is not None
    assert result["status"] == "TRACK_COMPLETELY_SILENT_ERROR"
    assert "Forgotten Strings" in result["totally_silent_tracks"]


def test_gatekeeper_allows_intentional_silent_track_with_contract():
    """
    Contract specifies 'exception_type': 'intentional_silence'.
    Gatekeeper must authorize the omission and NOT block the session.
    """
    session = MockSession(
        structural_contracts={
            "contract-tacet-01": {
                "contract_id": "contract-tacet-01",
                "target": "Atmospheric Drone",
                "decision": "TACET",
                "exception_type": "intentional_silence",
                "justification": "Aesthetic choice: track is reserved for extended remix, silent in main cut",
            }
        }
    )
    tracks = [
        {"index": 0, "name": "Drums", "role": "DRUMS", "notes_count": 32, "is_audio": False},
        {"index": 1, "name": "Atmospheric Drone", "role": "PAD", "notes_count": 0, "is_audio": False},
    ]
    sections = [{"name": "Intro", "bars": 8}, {"name": "Verse", "bars": 16}]

    result = Phase6Gatekeepers.check_every_track_has_sound(
        session=session,
        tracks=tracks,
        sections=sections,
        custom_notes_map={(0, 0): [{"pitch": 36}]},
        is_test_env=False,
    )

    # Must be approved!
    assert result is None


def test_gatekeeper_unpopulated_midi_track_allows_tacet_contract():
    """
    MIDI track with 0 notes is allowed if covered by intentional silence contract.
    """
    session = MockSession(
        structural_contracts={
            "contract-tacet-02": {
                "target": "Cinematic Horns",
                "decision": "REJECT",
                "exception_type": "intentional_silence",
            }
        }
    )
    tracks = [
        {"index": 0, "name": "Cinematic Horns", "role": "BRASS", "notes_count": 0, "is_audio": False},
    ]

    result = Phase6Gatekeepers.check_unpopulated_midi_tracks(
        session=session,
        tracks=tracks,
        is_explicit_key_directive=False,
    )

    assert result is None


def test_gatekeeper_second_drop_mutation_allows_contracted_identical_drop():
    """
    Identical Drop 2 is authorized if an artistic contract declares REJECTED_BY_ARTIST
    to preserve hypnotic repetition in minimal genres.
    """
    session = MockSession(
        structural_contracts={
            "contract-drop-01": {
                "target": "second_drop",
                "decision": "REJECTED_BY_ARTIST",
                "justification": "Minimal Techno hypnosis: maintain identical drop without variation",
            }
        }
    )
    sections = [
        {"name": "Drop 1", "bars": 16},
        {"name": "Break", "bars": 8},
        {"name": "Drop 2", "bars": 16},
    ]
    # Identical notes in Drop 1 (sec 0) and Drop 2 (sec 2)
    custom_notes_map = {
        (0, 0): [{"pitch": 40, "start_time": 0.0, "duration": 1.0, "velocity": 100}],
        (0, 2): [{"pitch": 40, "start_time": 0.0, "duration": 1.0, "velocity": 100}],
    }

    result = Phase6Gatekeepers.check_second_drop_transformation(
        session=session,
        sections=sections,
        custom_notes_map=custom_notes_map,
        is_test_env=False,
    )

    # Must be authorized by contract without blocking!
    assert result is None

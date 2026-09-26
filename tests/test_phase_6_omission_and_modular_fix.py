"""
Unit tests verifying the Phase 6 Composition fixes:
1. Interception of multi-track score JSONs in modular mode ensuring Track 0 (Drums) is not bypassed.
2. Completeness gatekeeper blocks exit to Phase 7 if any instrumental MIDI track has zero notes.
3. Targeted note resolution in BY_CLIP mode.
"""
import json
import pytest
from unittest.mock import MagicMock
from engine.production.copilot.phases.phase_6.handler import Phase6CompositionHandler
from engine.production.copilot.phases.phase_6.gatekeepers import Phase6Gatekeepers


class MockSession:
    def __init__(self, tracks=None, sections=None):
        self.data = {
            "session_id": "test_session",
            "tracks": tracks or [
                {"name": "Drums", "role": "DRUMS", "index": 0, "notes_count": 0},
                {"name": "808 Bass", "role": "808_BASS", "index": 1, "notes_count": 0},
                {"name": "Keys", "role": "KEYS", "index": 2, "notes_count": 0},
                {"name": "Lead", "role": "LEAD", "index": 3, "notes_count": 0},
                {"name": "Vocal", "role": "VOCALS", "index": 4, "is_audio": True, "notes_count": 0}
            ],
            "sections": sections or [
                {"name": "Intro", "bars": 8, "start_bar": 0},
                {"name": "Verso", "bars": 16, "start_bar": 8},
                {"name": "Coro", "bars": 16, "start_bar": 24},
                {"name": "Outro", "bars": 8, "start_bar": 40}
            ],
            "bpm": 140.0,
            "key": "C",
            "scale": "minor",
            "genre": "trap",
            "current_phase": "PHASE_6_COMPOSITION",
            "phase_index": 6,
            "composition_session": {
                "active": True,
                "mode": "BY_TRACK",
                "track_index": 1,  # Simulating pointer desync where Drums was skipped
                "section_index": 0
            }
        }

    def _save_state(self):
        pass

    def _prompt_phase_7(self):
        return {"status": "PROMPT_PHASE_7", "phase": "PHASE_7_AUTOMATION"}

    def _resolve_live_track_index(self, conn, trk):
        return trk.get("index", 0)


def test_modular_mode_intercepts_multi_track_score():
    handler = Phase6CompositionHandler()
    session = MockSession()
    conn = MagicMock()

    # Multi-track score payload with notes for all tracks
    multi_track_score = {
        "composition": {
            "Drums": {
                "0": [{"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 100}],
                "1": [{"pitch": 38, "start_time": 0.0, "duration": 1.0, "velocity": 100}]
            },
            "808 Bass": {
                "0": [{"pitch": 36, "start_time": 0.0, "duration": 2.0, "velocity": 100}]
            },
            "Keys": {
                "0": [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}]
            },
            "Lead": {
                "0": [{"pitch": 72, "start_time": 0.0, "duration": 1.0, "velocity": 95}]
            }
        }
    }

    # Intercept should route to monolithic handler, deploying all tracks including Track 0 (Drums)
    res = handler.handle_modular_composition_step(session, conn, json.dumps(multi_track_score))

    # All 4 MIDI tracks should have notes deployed
    drums_trk = session.data["tracks"][0]
    bass_trk = session.data["tracks"][1]
    keys_trk = session.data["tracks"][2]
    lead_trk = session.data["tracks"][3]

    assert drums_trk["notes_count"] > 0, "Drums (Track 0) must NOT be skipped when multi-track score is provided!"
    assert bass_trk["notes_count"] > 0
    assert keys_trk["notes_count"] > 0
    assert lead_trk["notes_count"] > 0
    assert session.data["composition_session"]["active"] is False


def test_by_track_interactive_exit_blocked_by_unpopulated_track():
    handler = Phase6CompositionHandler()
    session = MockSession()
    session.data["composition_session"] = {
        "active": True,
        "mode": "BY_TRACK",
        "interactive": True,
        "track_index": 4,  # Reached last track
        "section_index": 0
    }
    # Drums (Track 0) still has 0 notes
    session.data["tracks"][0]["notes_count"] = 0
    session.data["tracks"][1]["notes_count"] = 50
    session.data["tracks"][2]["notes_count"] = 50
    session.data["tracks"][3]["notes_count"] = 50

    conn = MagicMock()
    # Step out of track 4
    res = handler.handle_modular_composition_step(session, conn, "siguiente")

    assert res["status"] == "PHASE_6_GATEKEEPER_BLOCKED"
    assert "Drums" in res["unpopulated_tracks"]


def test_by_clip_exit_blocked_by_unpopulated_track():
    handler = Phase6CompositionHandler()
    session = MockSession()
    session.data["composition_session"] = {
        "active": True,
        "mode": "BY_CLIP",
        "track_index": 4,  # Reached last track
        "section_index": 3
    }
    # Drums has 0 notes
    session.data["tracks"][0]["notes_count"] = 0
    session.data["tracks"][1]["notes_count"] = 50
    session.data["tracks"][2]["notes_count"] = 50
    session.data["tracks"][3]["notes_count"] = 50

    conn = MagicMock()
    # Complete the last clip of track 4 (audio/vocals)
    res = handler.handle_modular_composition_step(session, conn, "[]")

    assert res["status"] == "PHASE_6_GATEKEEPER_BLOCKED"
    assert "Drums" in res["unpopulated_tracks"]

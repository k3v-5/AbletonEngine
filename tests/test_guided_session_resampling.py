# tests/test_guided_session_resampling.py
"""
Integration tests for Phase 11: Audio Reprocessing & Resynthesis Catalog in CopilotGuidedSession.
Validates state machine transitions, Opción A (Existing track), Opción B (New track design),
DSP execution, new audio track deployment, and rollback.
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_11_resampling import Phase11ResamplingHandler


@pytest.fixture
def session():
    sess = CopilotGuidedSession()
    sess.reset()
    sess.data["tracks"] = [
        {"index": 0, "name": "[KEYS] Prolonged Grand Piano", "role": "KEYS"},
        {"index": 1, "name": "[BASS] 808 Sub", "role": "BASS"},
    ]
    sess.data["key"] = "F"
    sess.data["scale"] = "Minor"
    sess.data["bpm"] = 120.0
    return sess


def test_phases_list_contains_phase_11():
    """Validates that PHASE_11_AUDIO_RESAMPLING is officially registered as the 11th phase."""
    phases = CopilotGuidedSession.PHASES
    assert len(phases) == 11
    assert phases[10] == "PHASE_11_AUDIO_RESAMPLING"


def test_phase_11_entry_prompt(session):
    """Validates initial entry prompt for Phase 11."""
    handler = Phase11ResamplingHandler()
    res = handler.prompt(session, conn=None)

    assert res["status"] == "AWAITING_SOURCE_SELECTION"
    assert res["phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert "FASE 11: CATÁLOGO DE REPROCESAMIENTO" in res["question"]
    assert "Opción A" in res["question"]
    assert "Opción B" in res["question"]
    assert session.data["resampling_session"]["active"] is True
    assert session.data["resampling_session"]["stage"] == "SELECT_SOURCE"


def test_phase_11_option_a_existing_track_flow(session):
    """Validates selecting an existing track and choosing a mutation technique."""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, args: (
        {"result": {"index": 18, "name": "[RESAMPLE 02] Tuned Comb Karplus-Strong Chime (F Minor)"}}
        if cmd == "execute_code"
        else {"status": "success"}
    )

    handler = Phase11ResamplingHandler()
    handler.prompt(session, conn=mock_conn)

    # Step 1: User chooses Option A (Existing track: Piano)
    step1_res = handler.handle(session, mock_conn, "Opción A usar pista Piano")
    assert step1_res["status"] == "AWAITING_TECHNIQUE_SELECTION"
    assert session.data["resampling_session"]["stage"] == "SELECT_TECHNIQUE"
    assert "Sonido Fuente" in step1_res["question"] or "Piano" in step1_res["question"]

    # Step 2: User selects Technique #2 (Tuned Comb Chime)
    step2_res = handler.handle(session, mock_conn, "Opción 2 Tuned Comb Chime")
    assert step2_res["status"] == "MUTATION_DEPLOYED_SUCCESSFULLY"
    assert session.data["resampling_session"]["stage"] == "AUDITION_LAYER"
    assert "[RESAMPLE 02]" in step2_res["action_taken"]
    assert len(session.data.get("resampled_tracks", [])) == 1
    assert session.data["resampled_tracks"][0]["technique_index"] == 2


def test_phase_11_option_b_new_track_sound_design_flow(session):
    """Validates guided sound design interview when creating a new source track from scratch."""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, args: (
        {"result": {"index": 19, "name": "[RESAMPLE 05] Sub-Safe Low-End Saturated Growl (F Minor)"}}
        if cmd == "execute_code"
        else {"status": "success"}
    )

    handler = Phase11ResamplingHandler()
    handler.prompt(session, conn=mock_conn)

    # Step 1: User chooses Option B (New track)
    res_b = handler.handle(session, mock_conn, "Opción B crear pista nueva")
    assert res_b["status"] == "AWAITING_DESIGN_ROLE"
    assert session.data["resampling_session"]["stage"] == "DESIGN_ROLE"

    # Step 2: User selects Role (Keys)
    res_role = handler.handle(session, mock_conn, "Keys")
    assert res_role["status"] == "AWAITING_DESIGN_INSTRUMENT"
    assert session.data["resampling_session"]["stage"] == "DESIGN_INSTRUMENT"

    # Step 3: User selects Instrument (Analog Lab V)
    res_inst = handler.handle(session, mock_conn, "Analog Lab V")
    assert res_inst["status"] == "AWAITING_DESIGN_PRESET"
    assert session.data["resampling_session"]["stage"] == "DESIGN_PRESET"

    # Step 4: User confirms Preset
    res_preset = handler.handle(session, mock_conn, "Confirmar")
    assert res_preset["status"] == "AWAITING_DESIGN_FX"
    assert session.data["resampling_session"]["stage"] == "DESIGN_FX"

    # Step 5: User confirms FX and synthesis proceeds
    res_fx = handler.handle(session, mock_conn, "Proceder con reverb y saturator")
    assert res_fx["status"] == "AWAITING_TECHNIQUE_SELECTION"
    assert session.data["resampling_session"]["stage"] == "SELECT_TECHNIQUE"

    # Step 6: User chooses Technique #5 (Sub-Safe Low Growl)
    res_tech = handler.handle(session, mock_conn, "5 Sub Safe Low Growl")
    assert res_tech["status"] == "MUTATION_DEPLOYED_SUCCESSFULLY"
    assert session.data["resampling_session"]["stage"] == "AUDITION_LAYER"
    assert session.data["resampled_tracks"][-1]["technique_index"] == 5


def test_rollback_to_phase_11(session):
    """Validates non-destructive rollback targeting Phase 11."""
    session.data["current_phase"] = "PHASE_10_COMPLETED"
    session.data["phase_index"] = 10

    res = session.step(conn=None, user_input="volver a la fase 11")
    assert res["status"] == "ROLLBACK_SUCCESSFUL"
    assert session.data["current_phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert session.data["phase_index"] == 11
    assert session.data["resampling_session"]["stage"] == "SELECT_SOURCE"


def test_keyword_intercept_enters_phase_11(session):
    """Validates that asking to 'resamplear pista' or 'reprocesar' from Phase 10 enters Phase 11."""
    session.data["current_phase"] = "PHASE_10_COMPLETED"
    session.data["phase_index"] = 10

    res = session.step(conn=None, user_input="quiero resamplear una pista con el catalogo de reprocesamiento")
    assert session.data["current_phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert res["phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert res["status"] == "AWAITING_SOURCE_SELECTION"

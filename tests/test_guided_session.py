# tests/test_guided_session.py
"""
Unit tests for Copilot Guided Session (State Machine Wizard for Interactive Music Production).
Tests the conversational, step-by-step interactive interview flow from Phase 1 to Phase 6.
"""

import pytest
from unittest.mock import MagicMock
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor


@pytest.fixture
def clean_session():
    """Provides a fresh CopilotGuidedSession with reset state."""
    session = CopilotGuidedSession()
    session.reset()
    return session


def test_guided_session_initial_prompt(clean_session):
    adapter = MockAbletonAdapter()
    res = clean_session.step(conn=adapter, user_input="")

    assert res["phase"] == "PHASE_1_TRACKS"
    assert "Paso 1 de 5" in res["question"]
    assert "Opción A" in res["question"]
    assert "Opción B" in res["question"]


def test_guided_session_phase_1_scaffolding(clean_session):
    adapter = MockAbletonAdapter()
    # User selects 5 essential channels
    res = clean_session.step(conn=adapter, user_input="Opción A")

    assert res["phase"] == "PHASE_2_SECTIONS"
    assert clean_session.data["phase_index"] == 2
    assert len(clean_session.data["tracks"]) == 5
    assert clean_session.data["tracks"][0]["role"] == "DRUMS"
    assert clean_session.data["tracks"][1]["role"] == "KEYS"
    assert clean_session.data["tracks"][2]["role"] == "PAD"
    assert clean_session.data["tracks"][3]["role"] == "BASS"
    assert clean_session.data["tracks"][4]["role"] == "LEAD"

    # Verify physical tracks were named in Live
    assert len(adapter.tracks) >= 5
    assert "Paso 2 de 5" in res["question"]


def test_guided_session_phase_2_sections(clean_session):
    adapter = MockAbletonAdapter()
    # Step 1: scaffold
    clean_session.step(conn=adapter, user_input="Opción A")

    # Step 2: sections (Option B: 64 bars)
    res = clean_session.step(conn=adapter, user_input="Opción B")

    assert res["phase"] == "PHASE_3_INSTRUMENTS"
    assert clean_session.data["phase_index"] == 3
    assert clean_session.data["total_bars"] == 64
    assert len(clean_session.data["sections"]) == 5
    assert clean_session.data["current_track_ptr"] == 0

    # Verify cue point command dispatch
    assert hasattr(adapter, "cue_points")
    assert len(adapter.cue_points) == 5

    # Should ask for track 0 (Drums) instrument
    assert "Configuración de Instrumento para Pista 0" in res["question"]


def test_guided_session_phase_3_track_by_track(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")

    # Track 0 (Drums)
    res_t0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 1
    assert "Configuración de Instrumento para Pista 1" in res_t0["question"]

    # Track 1 (Keys)
    res_t1 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 2
    assert "Configuración de Instrumento para Pista 2" in res_t1["question"]

    # Track 2 (Pads)
    res_t2 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 3

    # Track 3 (Bass)
    res_t3 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 4

    # Track 4 (Lead) - Final track in list
    res_t4 = clean_session.step(conn=adapter, user_input="Opción 1")
    
    # Should automatically transition to Phase 4 (Composition)
    assert res_t4["phase"] == "PHASE_4_COMPOSITION"
    assert clean_session.data["phase_index"] == 4
    assert "Paso 4 de 5" in res_t4["question"]
    assert "tonalidad" in res_t4["question"].lower()


def test_guided_session_phase_4_composition(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    # Step 4: composition input
    res = clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    assert res["phase"] == "PHASE_5_MIX_MASTER"
    assert clean_session.data["phase_index"] == 5
    assert clean_session.data["key"] == "F"
    assert clean_session.data["scale"] == "natural_minor"
    assert clean_session.data["bpm"] == 120.0

    # Verify clips and notes written in Live
    for trk in adapter.tracks[:5]:
        assert trk["clip_slots"][0]["has_clip"] is True
        assert len(trk.get("arrangement_clips", [])) > 0

    assert "Paso 5 de 5" in res["question"]
    assert "CLUB" in res["question"]
    assert "STREAMING" in res["question"]


def test_guided_session_phase_5_mix_master_and_phase_6(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    # Step 5: Mix & Master
    res = clean_session.step(conn=adapter, user_input="Club a -8.5 LUFS")

    assert res["phase"] == "PHASE_6_COMPLETED"
    assert clean_session.data["phase_index"] == 6
    assert clean_session.data["is_complete"] is True
    assert clean_session.data["target_profile"] == "CLUB"
    assert "PRODUCCIÓN FINALIZADA" in res["question"]
    assert "El Copilot permanece activo y escuchando" in res["question"]

    # Step 6: Conversational post-production adjustment
    res_tweak = clean_session.step(conn=adapter, user_input="Cambia el tempo a 128 BPM")
    assert res_tweak["phase"] == "PHASE_6_COMPLETED"
    assert clean_session.data["bpm"] == 128.0
    assert "128.0 BPM" in res_tweak["action_taken"]

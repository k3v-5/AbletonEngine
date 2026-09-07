# tests/test_guided_session.py
"""
Unit tests for Copilot Guided Session (State Machine Wizard for Interactive Music Production).
Tests the conversational, step-by-step interactive interview flow across all 7 production phases:
1. PHASE_1_TRACKS (Scaffolding)
2. PHASE_2_SECTIONS (Arrangement cue points)
3. PHASE_3_INSTRUMENTS (Track-by-track verified instrument loading and Drum Pad verification)
4. PHASE_4_PARAM_SCULPTING (Track-by-track synthesis sculpting Delta >= 1)
5. PHASE_5_INSERT_EFFECTS (Track-by-track insert FX chains)
6. PHASE_6_COMPOSITION (Arrangement composition with Drum Octave Guard)
7. PHASE_7_MIX_MASTER (Mixing, Sidechain ducking and LUFS mastering)
8. PHASE_8_COMPLETED (Active listening for ongoing tweaks)
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
    assert "Paso 1 de 7" in res["question"]
    assert "Opción A" in res["question"]
    assert "Opción B" in res["question"]


def test_guided_session_phase_1_scaffolding(clean_session):
    adapter = MockAbletonAdapter()
    res = clean_session.step(conn=adapter, user_input="Opción A")

    assert res["phase"] == "PHASE_2_SECTIONS"
    assert clean_session.data["phase_index"] == 2
    assert len(clean_session.data["tracks"]) == 5
    assert clean_session.data["tracks"][0]["role"] == "DRUMS"
    assert clean_session.data["tracks"][1]["role"] == "KEYS"
    assert clean_session.data["tracks"][2]["role"] == "PAD"
    assert clean_session.data["tracks"][3]["role"] == "BASS"
    assert clean_session.data["tracks"][4]["role"] == "LEAD"

    assert len(adapter.tracks) >= 5
    assert "Paso 2 de 7" in res["question"]


def test_guided_session_phase_2_sections(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    res = clean_session.step(conn=adapter, user_input="Opción B")

    assert res["phase"] == "PHASE_3_INSTRUMENTS"
    assert clean_session.data["phase_index"] == 3
    assert clean_session.data["total_bars"] == 64
    assert len(clean_session.data["sections"]) == 5
    assert clean_session.data["current_track_ptr"] == 0

    assert hasattr(adapter, "cue_points")
    assert len(adapter.cue_points) == 5
    assert "Instrumento / Kit para Pista 0" in res["question"]


def test_guided_session_phase_3_zero_silent_swallow(clean_session):
    """Verifies that an unverified instrument halts progression and flags LOAD_FAILED."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")

    original_send = adapter.send_command
    def fail_load(cmd, params=None):
        if cmd == "load_browser_item":
            raise RuntimeError("Live connection timeout during VST scan")
        return original_send(cmd, params)

    adapter.send_command = fail_load

    res_fail = clean_session.step(conn=adapter, user_input="Opción 1")
    assert res_fail["status"] == "LOAD_FAILED"
    assert res_fail["retry_required"] is True
    assert clean_session.data["current_track_ptr"] == 0
    assert "FALLO DE VERIFICACIÓN" in res_fail["action_taken"]


def test_guided_session_phase_3_track_by_track(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")

    res_t0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 1
    assert "Instrumento / Kit para Pista 1" in res_t0["question"]

    res_t1 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 2
    assert "Instrumento / Kit para Pista 2" in res_t1["question"]

    res_t2 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 3

    res_t3 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 4

    res_t4 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert res_t4["phase"] == "PHASE_4_PARAM_SCULPTING"
    assert clean_session.data["phase_index"] == 4
    assert "Paso 4 de 7" in res_t4["question"]
    assert "Esculpido de Síntesis" in res_t4["question"]


def test_guided_session_phase_4_param_sculpting(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING"

    res_p0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_param_ptr"] == 1

    res_p1 = clean_session.step(conn=adapter, user_input="Opción 2 (Brillante y Moderno)")
    assert clean_session.data["current_param_ptr"] == 2

    clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Opción 3 (Pesado y Agresivo)")
    res_p4 = clean_session.step(conn=adapter, user_input="Opción 2")

    assert res_p4["phase"] == "PHASE_5_INSERT_EFFECTS"
    assert clean_session.data["phase_index"] == 5
    assert "Paso 5 de 7" in res_p4["question"]
    assert "Cadena de Efectos de Inserción" in res_p4["question"]


def test_guided_session_phase_5_insert_effects(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"

    res_fx0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_fx_ptr"] == 1

    res_fx1 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_fx_ptr"] == 2

    clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Opción 1")
    res_fx4 = clean_session.step(conn=adapter, user_input="Opción 1")

    assert res_fx4["phase"] == "PHASE_6_COMPOSITION"
    assert clean_session.data["phase_index"] == 6
    assert "Paso 6 de 7" in res_fx4["question"]
    assert "tonalidad" in res_fx4["question"].lower()


def test_guided_session_phase_6_composition(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    res = clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    assert res["phase"] == "PHASE_7_MIX_MASTER"
    assert clean_session.data["phase_index"] == 7
    assert clean_session.data["key"] == "F"
    assert clean_session.data["scale"] == "natural_minor"
    assert clean_session.data["bpm"] == 120.0

    for trk in adapter.tracks[:5]:
        assert trk["clip_slots"][0]["has_clip"] is True
        assert len(trk.get("arrangement_clips", [])) > 0

    assert "Paso 7 de 7" in res["question"]
    assert "CLUB" in res["question"]
    assert "STREAMING" in res["question"]


def test_guided_session_phase_7_mix_master_and_phase_8(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    res = clean_session.step(conn=adapter, user_input="Club a -8.5 LUFS")

    assert res["phase"] == "PHASE_8_COMPLETED"
    assert clean_session.data["phase_index"] == 8
    assert clean_session.data["is_complete"] is True
    assert clean_session.data["target_profile"] == "CLUB"
    assert "PRODUCCIÓN FINALIZADA" in res["question"]
    assert "El Copilot permanece activo y escuchando" in res["question"]

    res_tweak = clean_session.step(conn=adapter, user_input="Cambia el tempo a 128 BPM")
    assert res_tweak["phase"] == "PHASE_8_COMPLETED"
    assert clean_session.data["bpm"] == 128.0
    assert "128.0 BPM" in res_tweak["action_taken"]

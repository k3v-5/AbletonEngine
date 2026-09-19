# tests/test_guided_session_automation_surgical.py
"""
Unit and integration tests for the Surgical Clip-by-Clip Automation System (Phase 7)
in CopilotGuidedSession (AbletonEngine).

Validates:
1. Surgical mode activation via Option B, keywords, or direct candidate numbers.
2. Complete catalog generation and selective candidate filtering (e.g. "1, 2").
3. Step-by-step clip prompts asking for breakpoint count (2, 3, 4, N points).
4. Accurate point generation (2-point linear ramp, 3-point washout/pre-drop peak, 4-point plateau, N-point curve).
5. Physical injection into Live (mock adapter automation envelopes).
6. Navigation controls: 'saltar' (skip clip), 'express' (batch remaining), and 'regresar' (reversal).
7. Clean progression to Phase 8 Vocal Ducking.
8. User preference persistence ('clip_by_clip' vs 'express').
"""

import pytest
import json
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.memory.user_learning import save_user_preference, get_user_preferences


def _make_composition_input(bpm=120.0, key="F", scale="natural_minor", genre="trap"):
    payload = {
        "bpm": bpm,
        "key": key,
        "scale": scale,
        "genre": genre,
        "composition": {
            "0": {"all": [{"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 127}, {"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 115}]},
            "DRUMS": {"all": [{"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 100}]},
            "KICK": {"all": [{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 127}]},
            "KEYS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "PAD": {"all": [{"pitch": 65, "start_time": 0.0, "duration": 4.0, "velocity": 80}]},
            "BASS": {"all": [{"pitch": 29, "start_time": 0.0, "duration": 0.5, "velocity": 120}, {"pitch": 41, "start_time": 0.75, "duration": 0.25, "velocity": 110}]},
            "LEAD": {"all": [{"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}]},
            "BRASS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 110}]},
            "CHOIR": {"all": [{"pitch": 65, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "GUITAR": {"all": [{"pitch": 57, "start_time": 0.0, "duration": 1.0, "velocity": 90}]},
            "STRINGS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "PERCUSSION": {"all": [{"pitch": 42, "start_time": 0.0, "duration": 0.25, "velocity": 90}]},
        }
    }
    return f"```json\n{json.dumps(payload)}\n```"


def _setup_session_at_phase_7(session, adapter):
    session.reset()
    session.step(conn=adapter, user_input="Opción A")  # Phase 1
    session.step(conn=adapter, user_input="Opción B")  # Phase 2
    for _ in range(5):
        session.step(conn=adapter, user_input="Opción 1")  # Phase 3
    for _ in range(5):
        session.step(conn=adapter, user_input="Opción 1")  # Phase 4
    while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        session.step(conn=adapter, user_input="Opción 1")  # Phase 5
    res6 = session.step(conn=adapter, user_input=_make_composition_input())  # Phase 6
    assert session.data["current_phase"] == "PHASE_7_AUTOMATION"
    return res6


def test_surgical_automation_full_clip_by_clip_flow():
    """Tests selecting candidate curves 1 and 2, defining points for each, and advancing to Phase 8."""
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()
    _setup_session_at_phase_7(session, adapter)

    # 1. Choose Option B (Modo Quirúrgico Clip por Clip)
    res_sel = session.step(conn=adapter, user_input="Opción B")
    assert res_sel["status"] == "AWAITING_AUTOMATION_SELECTION"
    assert "Decisión Técnica Requerida" in res_sel["question"]
    assert res_sel["candidates_count"] >= 2
    assert session.data["automation_session"]["stage"] == "SELECTION"

    # 2. Select candidates 1 and 2
    res_clip1 = session.step(conn=adapter, user_input="1, 2")
    assert res_clip1["status"] == "AWAITING_CLIP_POINTS"
    assert res_clip1["step_index"] == 1
    assert res_clip1["total_steps"] == 2
    assert session.data["automation_session"]["stage"] == "POINT_CONFIG"
    assert "2 puntos" in res_clip1["question"]
    assert "3 puntos" in res_clip1["question"]

    # 3. Clip 1: Request 2 points (linear ramp)
    initial_envelopes_count = len(getattr(adapter, "automation_envelopes", []))
    res_clip2 = session.step(conn=adapter, user_input="2 puntos")
    assert res_clip2["status"] == "AWAITING_CLIP_POINTS"
    assert res_clip2["step_index"] == 2
    assert res_clip2["total_steps"] == 2
    assert "✅ Curva de" in res_clip2["action_taken"]
    assert "2 puntos" in res_clip2["action_taken"]

    # Verify adapter received the first automation envelope with exactly 2 points
    assert len(adapter.automation_envelopes) == initial_envelopes_count + 1
    env1 = adapter.automation_envelopes[-1]
    assert len(env1["points"]) == 2

    # 4. Clip 2: Request 3 points (bell curve / pre-drop / washout)
    res_done = session.step(conn=adapter, user_input="3 puntos")
    assert res_done["phase"] == "PHASE_8_VOCAL_DUCKING"
    assert session.data["phase_index"] == 8
    assert session.data["automation_session"]["active"] is False

    # Verify adapter received the second automation envelope with exactly 3 points
    assert len(adapter.automation_envelopes) == initial_envelopes_count + 2
    env2 = adapter.automation_envelopes[-1]
    assert len(env2["points"]) == 3

    # Verify session automations recorded
    assert len(session.data["automations"]) == 2


def test_surgical_automation_direct_candidate_input():
    """Tests specifying candidate numbers directly from Phase 7 prompt (e.g. '1, 2')."""
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()
    _setup_session_at_phase_7(session, adapter)

    # From Phase 7 initial prompt, directly send candidate numbers
    res_clip1 = session.step(conn=adapter, user_input="1 y 2")
    assert res_clip1["status"] == "AWAITING_CLIP_POINTS"
    assert res_clip1["step_index"] == 1
    assert res_clip1["total_steps"] == 2
    assert session.data["automation_session"]["active"] is True


def test_surgical_automation_custom_n_points_and_skip():
    """Tests configuring custom N points (e.g. 8 points) and using 'saltar' (skip)."""
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()
    _setup_session_at_phase_7(session, adapter)

    session.step(conn=adapter, user_input="Opción B")
    session.step(conn=adapter, user_input="1, 2")

    # Clip 1: Request 8 points
    res_clip2 = session.step(conn=adapter, user_input="8 puntos")
    assert res_clip2["step_index"] == 2
    env1 = adapter.automation_envelopes[-1]
    assert len(env1["points"]) == 8

    # Clip 2: Skip this clip
    res_done = session.step(conn=adapter, user_input="saltar")
    assert res_done["phase"] == "PHASE_8_VOCAL_DUCKING"
    assert session.data["phase_index"] == 8
    # Only 1 automation applied
    assert len(session.data["automations"]) == 1


def test_surgical_automation_preference_command():
    """Tests toggling user preference between clip_by_clip and express."""
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()

    # Test preference saving via session command
    res_pref = session.step(conn=adapter, user_input="configurar automatizacion por clip")
    assert res_pref["status"] == "PREFERENCE_SAVED"
    assert get_user_preferences("automation", "mode") == "clip_by_clip"

    res_pref2 = session.step(conn=adapter, user_input="configurar automatizacion express")
    assert res_pref2["status"] == "PREFERENCE_SAVED"
    assert get_user_preferences("automation", "mode") == "express"


def test_surgical_automation_reversal_to_selection_and_phase_6():
    """Tests navigating backward using 'regresar' from point config to selection, and from selection to Phase 6."""
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()
    _setup_session_at_phase_7(session, adapter)

    session.step(conn=adapter, user_input="Opción B")
    session.step(conn=adapter, user_input="1, 2")

    # Point config -> Regresar to selection
    res_back = session.step(conn=adapter, user_input="regresar")
    assert res_back["status"] == "AWAITING_AUTOMATION_SELECTION"
    assert session.data["automation_session"]["stage"] == "SELECTION"

    # Selection -> Regresar to Phase 6
    res_p6 = session.step(conn=adapter, user_input="regresar")
    assert res_p6["phase"] == "PHASE_6_COMPOSITION"
    assert session.data["phase_index"] == 6
    assert session.data["automation_session"]["active"] is False


def test_surgical_automation_express_midway():
    """Tests choosing 'express' mid-way during clip-by-clip configuration to batch remaining clips."""
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()
    _setup_session_at_phase_7(session, adapter)

    session.step(conn=adapter, user_input="Opción B")
    session.step(conn=adapter, user_input="1, 2, 3")

    # Configure clip 1 with 2 points
    session.step(conn=adapter, user_input="2 puntos")

    # Mid-way: inject remaining via express
    res_done = session.step(conn=adapter, user_input="express")
    assert res_done["phase"] == "PHASE_8_VOCAL_DUCKING"
    assert session.data["phase_index"] == 8
    # All 3 selected automations applied
    assert len(session.data["automations"]) == 3

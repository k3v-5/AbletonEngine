# tests/test_state_flexibility_and_micro_surgery.py
"""
Unit and integration tests for:
1. Backward effect recalibration right after pre-vocal panning / Phase 8 without resetting.
2. Phase 6 modular composition (by section, by track, or combined).
3. Phase 10 post-mastering interactive decision hub and clip micro-surgery (bar 47, velocity tweaks).
"""

import pytest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.session.clip_micro_surgeon import ClipMicroSurgeon


@pytest.fixture
def mock_adapter():
    adapter = MockAbletonAdapter()
    while len(adapter.tracks) < 16:
        idx = len(adapter.tracks)
        adapter.tracks.append({
            "name": f"Track {idx}",
            "volume": 0.85,
            "panning": 0.0,
            "mute": False,
            "solo": False,
            "arm": False,
            "devices": []
        })
    return adapter


@pytest.fixture
def clean_session():
    gs = CopilotGuidedSession()
    gs.reset()
    return gs


def test_backward_effect_adjustment_after_panning(clean_session, mock_adapter):
    """
    Validates that after pre-vocal panning evaluation, the assistant can modify
    previously created Phase 5 insert effects without resetting the session.
    """
    clean_session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
    clean_session.data["phase_index"] = 8
    clean_session.data["tracks"] = [
        {
            "index": 0, "name": "[DRUMS] Core Kit", "role": "DRUMS", "panning": 0.0,
            "insert_effects": [{"name": "Drum Buss", "parameters": {}}]
        },
        {
            "index": 2, "name": "[KEYS] Piano", "role": "KEYS", "panning": -0.24,
            "insert_effects": [{"name": "ValhallaVintageVerb", "parameters": {"Decay": 4.0, "Mix": 40.0}}]
        }
    ]
    clean_session._save_state()

    # 1. Prompt pre-vocal panning
    res_pan = clean_session.step(conn=mock_adapter, user_input="evaluar separacion estereo y paneo")
    assert res_pan["status"] == "AWAITING_PRE_VOCAL_PANNING_DECISION"
    assert "Opción D" in res_pan["question"]

    # 2. Assistant chooses Opción D (Ajustar Efectos Anteriores)
    res_fx_prompt = clean_session.step(conn=mock_adapter, user_input="Opción D ajustar efectos")
    assert res_fx_prompt["status"] == "AWAITING_EFFECT_RECALIBRATION"
    assert clean_session.data.get("awaiting_effect_recalibration") is True
    assert "ValhallaVintageVerb" in res_fx_prompt["question"]

    # 3. Assistant modifies Piano Reverb
    res_tweak = clean_session.step(conn=mock_adapter, user_input="Pista 2 Keys: Reverb Decay 2.0s, Mix 20%")
    assert res_tweak["status"] == "EFFECT_RECALIBRATED"
    assert "Parámetro modificado" in res_tweak["action_taken"]

    # 4. Assistant finishes tweaking and continues
    res_cont = clean_session.step(conn=mock_adapter, user_input="Continuar")
    assert clean_session.data.get("awaiting_effect_recalibration") is False
    assert res_cont["status"] in ("AWAITING_PRE_VOCAL_PANNING_DECISION", "PASO 8 DE 9: VOCAL DUCKING Y SIDECHAIN ARMÓNICO")


def test_phase_6_modular_composition_by_section(clean_session, mock_adapter):
    """
    Validates that Phase 6 allows modular composition section by section
    rather than requiring a monolithic block of all notes.
    """
    clean_session.data["current_phase"] = "PHASE_6_COMPOSITION"
    clean_session.data["phase_index"] = 6
    clean_session.data["sections"] = [
        {"name": "Intro", "bars": 8},
        {"name": "Drop 1", "bars": 16},
        {"name": "Outro", "bars": 8}
    ]
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS"},
        {"index": 1, "name": "Bass", "role": "BASS"}
    ]
    clean_session._save_state()

    # User chooses modular by section
    res1 = clean_session.step(conn=mock_adapter, user_input="Opción 1 por sección")
    assert res1["status"] == "MODULAR_COMPOSITION_INITIALIZED"
    assert res1["mode"] == "BY_SECTION"
    assert clean_session.data.get("composition_session", {}).get("active") is True

    # Step through remaining sections
    res2 = clean_session.step(conn=mock_adapter, user_input="Siguiente")
    assert res2["status"] == "MODULAR_COMPOSITION_STEP"
    assert "Drop 1" in res2["question"]

    res3 = clean_session.step(conn=mock_adapter, user_input="Siguiente")
    assert res3["status"] == "MODULAR_COMPOSITION_STEP"
    assert "Outro" in res3["question"]

    # Final section completion advances to Phase 7
    res_final = clean_session.step(conn=mock_adapter, user_input="Siguiente")
    assert res_final["phase"] == "PHASE_7_AUTOMATION"
    assert clean_session.data.get("current_phase") == "PHASE_7_AUTOMATION"
    assert clean_session.data.get("composition_session", {}).get("active") is False


def test_phase_6_modular_composition_by_track(clean_session, mock_adapter):
    """
    Validates that Phase 6 allows modular composition track by track.
    """
    clean_session.data["current_phase"] = "PHASE_6_COMPOSITION"
    clean_session.data["phase_index"] = 6
    clean_session.data["sections"] = [{"name": "Full", "bars": 32}]
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS"},
        {"index": 1, "name": "Bass", "role": "BASS"}
    ]
    clean_session._save_state()

    res1 = clean_session.step(conn=mock_adapter, user_input="Opción 2 por pista")
    assert res1["status"] == "MODULAR_COMPOSITION_INITIALIZED"
    assert res1["mode"] == "BY_TRACK"

    res2 = clean_session.step(conn=mock_adapter, user_input="Siguiente")
    assert res2["status"] == "MODULAR_COMPOSITION_STEP"
    assert "Bass" in res2["question"]

    res_final = clean_session.step(conn=mock_adapter, user_input="Siguiente")
    assert res_final["phase"] == "PHASE_7_AUTOMATION"
    assert clean_session.data.get("current_phase") == "PHASE_7_AUTOMATION"


def test_clip_micro_surgery_in_phase_10(clean_session, mock_adapter):
    """
    Validates surgical precision note editing in Phase 10 post-mastering:
    moving notes in bar 47 and tuning hi-hat velocities.
    """
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["phase_index"] = 10
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS"},
        {"index": 4, "name": "Hi-Hats", "role": "HI_HATS"}
    ]
    clean_session._save_state()

    # Move notes in bar 47
    res_surg1 = clean_session.step(conn=mock_adapter, user_input="Mover notas de pista 0 compas 47 0.25 beats adelante")
    assert res_surg1["status"] == "CLIP_SURGERY_COMPLETED"
    assert "MICRO-CIRUGÍA EN CLIP" in res_surg1["current_step"]
    assert res_surg1["surgery_result"]["bar"] == 47.0
    assert res_surg1["surgery_result"]["track_index"] == 0

    # Adjust hi-hat velocity in bar 32
    res_surg2 = clean_session.step(conn=mock_adapter, user_input="Cambiar velocidad de pista 4 compas 32 a 115")
    assert res_surg2["status"] == "CLIP_SURGERY_COMPLETED"
    assert res_surg2["surgery_result"]["bar"] == 32.0
    assert res_surg2["surgery_result"]["track_index"] == 4


def test_clip_micro_surgeon_unit_direct():
    """Unit tests on ClipMicroSurgeon helper algorithms."""
    notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 100},
        {"pitch": 38, "start_time": 184.0, "duration": 0.25, "velocity": 90},  # Bar 47 (beat (47-1)*4 = 184)
        {"pitch": 42, "start_time": 185.0, "duration": 0.25, "velocity": 95}
    ]

    # Move notes in bar 47 by 0.5 beats and +2 semitones
    moved, count = ClipMicroSurgeon.move_notes(notes, bar_start=47.0, delta_beats=0.5, delta_pitch=2)
    assert count == 2
    assert moved[1]["start_time"] == 184.5
    assert moved[1]["pitch"] == 40
    assert moved[2]["start_time"] == 185.5

    # Adjust velocities in bar 47 to 125
    vel_notes, v_count = ClipMicroSurgeon.adjust_velocity(moved, bar_start=47.0, target_velocity=125)
    assert v_count == 2
    assert vel_notes[1]["velocity"] == 125
    assert vel_notes[2]["velocity"] == 125
    assert vel_notes[0]["velocity"] == 100  # Bar 1 untouched


def test_phase_10_retroactive_effect_adjustment(clean_session, mock_adapter):
    """Validates that from Phase 10, the user can adjust previously created effects."""
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["tracks"] = [
        {"index": 1, "name": "Bass", "role": "BASS", "insert_effects": [{"name": "Saturator", "parameters": {}}]}
    ]
    clean_session._save_state()

    res = clean_session.step(conn=mock_adapter, user_input="corregir efectos")
    assert res["status"] == "AWAITING_EFFECT_RECALIBRATION"
    assert "Saturator" in res["question"]

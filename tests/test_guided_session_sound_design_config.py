# tests/test_guided_session_sound_design_config.py
import pytest
from unittest.mock import MagicMock
from pathlib import Path

from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession


def create_mock_conn():
    return MockAbletonAdapter()


def setup_session_at_phase_4(session, conn):
    session.reset()
    # Step 1: Tracks
    session.step(conn, "Opción A")
    # Step 2: Sections
    session.step(conn, "Opción B")
    # Step 3: Instruments for 5 tracks
    for _ in range(5):
        session.step(conn, "Opción 1")
    assert session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING"
    assert session.data["current_param_ptr"] == 0


def test_default_sound_design_mode_is_legacy(tmp_path, monkeypatch):
    test_state_file = tmp_path / "gs_legacy_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    conn = create_mock_conn()
    setup_session_at_phase_4(session, conn)

    assert session.get_sound_design_mode() == "LEGACY"

    # Prompt should be legacy
    prompt_res = session._prompt_current_track_params()
    assert "PASO 4 DE 7: ESCULPIDO QUIRÚRGICO DE SÍNTESIS" in prompt_res.get("current_step", "")
    assert "sound_design_mode" not in prompt_res

    # Step with Option 1 in legacy mode advances track pointer normally
    resp = session.step(conn, "Opción 1")
    assert session.data["current_param_ptr"] == 1


def test_conversational_sound_design_mode_toggle(tmp_path, monkeypatch):
    test_state_file = tmp_path / "gs_toggle_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    conn = create_mock_conn()
    session.reset()

    # Toggle to ADVANCED
    resp_adv = session.step(conn, "activar sound design avanzado")
    assert resp_adv["status"] == "SOUND_DESIGN_MODE_UPDATED"
    assert resp_adv["mode"] == "ADVANCED"
    assert session.get_sound_design_mode() == "ADVANCED"

    # Query status
    resp_stat = session.step(conn, "estado sound design")
    assert resp_stat["status"] == "SOUND_DESIGN_CONFIG_STATUS"
    assert resp_stat["mode"] == "ADVANCED"

    # Toggle back to LEGACY
    resp_leg = session.step(conn, "modo sound design clasico")
    assert resp_leg["status"] == "SOUND_DESIGN_MODE_UPDATED"
    assert resp_leg["mode"] == "LEGACY"
    assert session.get_sound_design_mode() == "LEGACY"


def test_advanced_sound_design_outer_shell(tmp_path, monkeypatch):
    test_state_file = tmp_path / "gs_adv_shell_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    conn = create_mock_conn()
    setup_session_at_phase_4(session, conn)

    session.set_sound_design_mode("ADVANCED")
    assert session.get_sound_design_mode() == "ADVANCED"

    # Prompt in ADVANCED mode
    prompt_res = session._prompt_current_track_params()
    assert "SOUND DESIGN AVANZADO" in prompt_res.get("current_step", "")
    assert prompt_res.get("sound_design_mode") == "ADVANCED"
    assert "Outer Sound Design Shell" in prompt_res.get("question", "")

    # Select Option 1: Outer Shell
    resp = session.step(conn, "Opción 1 (Outer Shell)")
    trk_0 = session.data["tracks"][0]
    assert "sound_design" in trk_0
    assert trk_0["sound_design"]["strategy"] == "OUTER_SOUND_DESIGN_SHELL"
    assert trk_0["sound_design"]["applied"] is True
    assert session.data["current_param_ptr"] == 1


def test_advanced_sound_design_uhts_layer(tmp_path, monkeypatch):
    test_state_file = tmp_path / "gs_adv_uhts_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    conn = create_mock_conn()
    setup_session_at_phase_4(session, conn)
    session.set_sound_design_mode("ADVANCED")

    # Select Option 2: Capa UHTS Shimmer
    session.step(conn, "Opción 2: Capa UHTS Shimmer")
    trk_0 = session.data["tracks"][0]
    assert trk_0["sound_design"]["strategy"] == "UHTS_RESAMPLING_LAYER"
    assert trk_0["sound_design"]["technique"] == "Pitch-Shifted Shimmer Diffusion"
    assert session.data["current_param_ptr"] == 1


def test_advanced_sound_design_macro_rack(tmp_path, monkeypatch):
    test_state_file = tmp_path / "gs_adv_macro_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    conn = create_mock_conn()
    setup_session_at_phase_4(session, conn)
    session.set_sound_design_mode("ADVANCED")

    # Select Option 3: Macro Rack
    session.step(conn, "Opción 3 (Macro Rack)")
    trk_0 = session.data["tracks"][0]
    assert trk_0["sound_design"]["strategy"] == "MACRO_RACK_4_CHARS"
    assert "MACRO_1" in trk_0["sound_design"]["macros"]
    assert session.data["current_param_ptr"] == 1


def test_advanced_sound_design_omit_skip(tmp_path, monkeypatch):
    test_state_file = tmp_path / "gs_adv_omit_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    conn = create_mock_conn()
    setup_session_at_phase_4(session, conn)
    session.set_sound_design_mode("ADVANCED")

    # User decides to skip / omit track sound design
    session.step(conn, "Omitir")
    trk_0 = session.data["tracks"][0]
    assert trk_0["sound_design"]["strategy"] == "SKIPPED"
    assert trk_0["sound_design"]["status"] == "PRESERVED"
    assert session.data["current_param_ptr"] == 1

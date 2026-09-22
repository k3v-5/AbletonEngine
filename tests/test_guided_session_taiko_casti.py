# tests/test_guided_session_taiko_casti.py
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from engine.composition.taiko_casti_composer import TaikoCastiComposer
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_11_resampling import Phase11ResamplingHandler


def create_mock_live_conn():
    conn = MagicMock()
    # Mock responses
    def mock_send_command(cmd, args=None):
        args = args or {}
        if cmd == "get_session_info":
            return {"track_count": 23, "scene_count": 20, "tempo": 100.0}
        elif cmd == "get_track_info":
            t_idx = args.get("track_index", 0)
            return {"index": t_idx, "name": f"Track {t_idx}", "is_foldable": False}
        elif cmd == "execute_code":
            return {"result": 20}
        return {"status": "ok"}
    conn.send_command.side_effect = mock_send_command
    return conn


def test_composer_deploy_with_mock_conn():
    conn = create_mock_live_conn()
    res = TaikoCastiComposer.deploy(conn)

    assert res["success"] is True
    assert res["bpm"] == 100.0
    assert res["key"] == "F"
    assert res["scale"] == "Minor"
    assert res["scenes_count"] == 20
    assert res["bars"] == 80
    assert res["total_beats"] == 320.0
    assert len(res["tracks"]) == 5

    # Check track roles
    roles = [t["role"] for t in res["tracks"]]
    assert "DRUMS" in roles
    assert "BASS" in roles
    assert "LEAD" in roles
    assert "KEYS" in roles
    assert "PAD" in roles

    # Verify key commands were sent to Live
    sent_cmds = [call[0][0] for call in conn.send_command.call_args_list]
    assert "execute_code" in sent_cmds
    assert "load_instrument_or_effect" in sent_cmds


def test_guided_session_taiko_casti_step_intercept(tmp_path, monkeypatch):
    conn = create_mock_live_conn()

    test_state_file = tmp_path / "guided_session_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    session.reset()

    user_query = (
        "Bien implementa una cancion fuertemente basada en taiko con su cancion Casti, "
        "y agrega un pad agregando cada una de las 20 escenas o procesamientos que se hicieron a lo largo de la cancion"
    )

    resp = session.step(conn, user_query)

    assert resp["status"] == "TAIKO_CASTI_ORCHESTRATED"
    assert resp["phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert resp["phase_index"] == 11
    assert resp["bpm"] == 100.0
    assert resp["tonality"] == "F Minor Phrygian"
    assert resp["bars"] == 80
    assert resp["scenes_count"] == 20
    assert len(resp["tracks"]) == 5

    # Verify session.data internal state synchronization
    assert session.data["current_phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert session.data["phase_index"] == 11
    assert session.data["bpm"] == 100.0
    assert session.data["key"] == "F"
    assert session.data["scale"] == "Minor"
    assert len(session.data["tracks"]) == 5
    assert len(session.data["sections"]) == 20
    assert session.data["resampling_session"]["active"] is True
    assert session.data["resampling_session"]["mode"] == "FULL_20_SCENE_EVOLUTION"


def test_phase_11_option_c_20_scene_pad(tmp_path, monkeypatch):
    conn = create_mock_live_conn()

    test_state_file = tmp_path / "guided_session_test_p11.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_11_AUDIO_RESAMPLING"
    session.data["phase_index"] = 11
    session.data["key"] = "F"
    session.data["scale"] = "Minor"
    session.data["bpm"] = 100.0

    handler = Phase11ResamplingHandler()

    # User triggers option C
    resp = handler.handle(session, conn, "opcion c: pad evolutivo de 20 escenas")

    assert resp["status"] == "FULL_20_SCENE_PAD_DEPLOYED"
    assert resp["phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert resp["scenes_deployed"] == 20
    assert "pad_track_name" in resp
    assert "[PAD] UHTS 20-Stage Audio" in resp["pad_track_name"]
    assert session.data["resampling_session"]["mode"] == "FULL_20_SCENE_EVOLUTION"

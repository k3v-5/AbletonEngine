# tests/test_taiko_shimmer_single_effect.py
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from engine.composition.taiko_shimmer_composer import TaikoShimmerComposer
from engine.production.copilot.guided_session import CopilotGuidedSession


def create_mock_live_conn():
    conn = MagicMock()

    def mock_send_command(cmd, args=None):
        args = args or {}
        if cmd == "get_session_info":
            return {"track_count": 23, "scene_count": 10, "tempo": 105.0}
        elif cmd == "get_track_info":
            t_idx = args.get("track_index", 0)
            return {"index": t_idx, "name": f"Track {t_idx}", "is_foldable": False}
        elif cmd == "execute_code":
            return {"result": {"success": True, "scenes_deployed": 10}}
        return {"status": "ok"}

    conn.send_command.side_effect = mock_send_command
    return conn


def test_taiko_shimmer_composer_notes_and_scenes():
    assert TaikoShimmerComposer.get_scene_count() == 10
    scenes = TaikoShimmerComposer.SCENES
    assert len(scenes) == 10

    total_bars = sum(4 for _ in scenes)
    assert total_bars == 40
    assert total_bars * 4.0 == 160.0

    # Verify that each scene has notes generated
    for s_idx in range(1, 11):
        taiko_notes = TaikoShimmerComposer.get_taiko_notes_for_scene(s_idx)
        bass_notes = TaikoShimmerComposer.get_bass_notes_for_scene(s_idx)
        lead_notes = TaikoShimmerComposer.get_lead_notes_for_scene(s_idx)
        pad_notes = TaikoShimmerComposer.get_pad_notes_for_scene(s_idx)

        assert isinstance(taiko_notes, list)
        assert isinstance(bass_notes, list)
        assert isinstance(lead_notes, list)
        assert isinstance(pad_notes, list)

        # Intro scene 1 has wooden stick clicks
        if s_idx == 1:
            assert len(taiko_notes) >= 4
            assert any(n["pitch"] == TaikoShimmerComposer.BACHI_CLICK for n in taiko_notes)

        # Pad notes exist across scenes
        assert len(pad_notes) > 0


def test_taiko_shimmer_composer_deploy_mock():
    conn = create_mock_live_conn()
    res = TaikoShimmerComposer.deploy(conn)

    assert res["success"] is True
    assert res["bpm"] == 105.0
    assert res["key"] == "D"
    assert res["scale"] == "Minor"
    assert res["scenes_count"] == 10
    assert res["bars"] == 40
    assert res["total_beats"] == 160.0
    assert len(res["tracks"]) == 5

    # Check track roles and types
    roles = [t["role"] for t in res["tracks"]]
    assert "DRUMS" in roles
    assert "BASS" in roles
    assert "LEAD" in roles
    assert "PAD" in roles

    # Verify audio track for UHTS shimmer is present
    audio_tracks = [t for t in res["tracks"] if t.get("type") == "audio"]
    assert len(audio_tracks) == 1
    assert "Shimmer" in audio_tracks[0]["name"]

    # Verify execute_code was dispatched
    sent_cmds = [call[0][0] for call in conn.send_command.call_args_list]
    assert "execute_code" in sent_cmds


def test_copilot_guided_session_taiko_single_effect_intercept(tmp_path, monkeypatch):
    conn = create_mock_live_conn()

    test_state_file = tmp_path / "guided_session_shimmer_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    session.reset()

    user_query = (
        "Generame una siguiente cancion igual estilo taiko, con un solo efecto de procesamiento, "
        "que sea un pad el sonido ariginal"
    )

    resp = session.step(conn, user_query)

    assert resp["status"] == "TAIKO_SHIMMER_ORCHESTRATED"
    assert resp["phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert resp["phase_index"] == 11
    assert resp["bpm"] == 105.0
    assert resp["tonality"] == "D Minor Insen"
    assert resp["bars"] == 40
    assert resp["scenes_count"] == 10
    assert len(resp["tracks"]) == 5

    # Verify session data state
    assert session.data["current_phase"] == "PHASE_11_AUDIO_RESAMPLING"
    assert session.data["phase_index"] == 11
    assert session.data["bpm"] == 105.0
    assert session.data["key"] == "D"
    assert session.data["scale"] == "Minor"
    assert len(session.data["tracks"]) == 5
    assert len(session.data["sections"]) == 10
    assert session.data["resampling_session"]["active"] is True
    assert session.data["resampling_session"]["mode"] == "SINGLE_TECHNIQUE_PAD"
    assert session.data["resampling_session"]["technique_index"] == 6
    assert session.data["resampling_session"]["technique"] == "Pitch-Shifted Shimmer Diffusion"

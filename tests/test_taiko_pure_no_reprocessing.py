# tests/test_taiko_pure_no_reprocessing.py
import pytest
from unittest.mock import MagicMock
from pathlib import Path

from engine.composition.taiko_pure_composer import TaikoPureComposer
from engine.production.copilot.guided_session import CopilotGuidedSession


def create_mock_live_conn():
    conn = MagicMock()

    def mock_send_command(cmd, args=None):
        args = args or {}
        if cmd == "get_session_info":
            return {"track_count": 23, "scene_count": 8, "tempo": 112.0}
        elif cmd == "get_track_info":
            t_idx = args.get("track_index", 0)
            return {"index": t_idx, "name": f"Track {t_idx}", "is_foldable": False}
        elif cmd == "execute_code":
            return {"result": {"success": True, "scenes_deployed": 8}}
        return {"status": "ok"}

    conn.send_command.side_effect = mock_send_command
    return conn


def test_taiko_pure_composer_notes_and_scenes():
    assert TaikoPureComposer.get_scene_count() == 8
    scenes = TaikoPureComposer.SCENES
    assert len(scenes) == 8

    total_bars = sum(4 for _ in scenes)
    assert total_bars == 32
    assert total_bars * 4.0 == 128.0

    for s_idx in range(1, 9):
        taiko_notes = TaikoPureComposer.get_taiko_notes_for_scene(s_idx)
        bass_notes = TaikoPureComposer.get_bass_notes_for_scene(s_idx)
        lead_notes = TaikoPureComposer.get_lead_notes_for_scene(s_idx)
        koto_notes = TaikoPureComposer.get_koto_notes_for_scene(s_idx)
        pad_notes = TaikoPureComposer.get_pad_notes_for_scene(s_idx)

        assert isinstance(taiko_notes, list)
        assert isinstance(bass_notes, list)
        assert isinstance(lead_notes, list)
        assert isinstance(koto_notes, list)
        assert isinstance(pad_notes, list)

        # Pad chords exist for all scenes
        assert len(pad_notes) > 0

        # Intro scene 1 has ceremonial bell & bachi clicks
        if s_idx == 1:
            assert any(n["pitch"] == TaikoPureComposer.ATARIGANE for n in taiko_notes)
            assert any(n["pitch"] == TaikoPureComposer.BACHI_CLICK for n in taiko_notes)


def test_taiko_pure_composer_deploy_mock():
    conn = create_mock_live_conn()
    res = TaikoPureComposer.deploy(conn)

    assert res["success"] is True
    assert res["bpm"] == 112.0
    assert res["key"] == "A"
    assert res["scale"] == "Minor"
    assert res["scenes_count"] == 8
    assert res["bars"] == 32
    assert res["total_beats"] == 128.0
    assert len(res["tracks"]) == 5

    # Strictly verify that NO track is an audio track (100% pure live MIDI tracks)
    for trk in res["tracks"]:
        assert trk.get("type") != "audio"

    roles = [t["role"] for t in res["tracks"]]
    assert "DRUMS" in roles
    assert "BASS" in roles
    assert "LEAD" in roles
    assert "KEYS" in roles
    assert "PAD" in roles

    # Verify zero audio reprocessing
    assert "NONE" in res["reprocessing"]


def test_guided_session_taiko_pure_intercept(tmp_path, monkeypatch):
    conn = create_mock_live_conn()

    test_state_file = tmp_path / "guided_session_pure_test.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    session = CopilotGuidedSession()
    session.reset()

    user_query = "Bien, generame una cancion estilo taiko, usando guided_session pero no quiero que reproceses ningun sonido"

    resp = session.step(conn, user_query)

    assert resp["status"] == "TAIKO_PURE_ORCHESTRATED"
    assert resp["phase"] == "PHASE_6_COMPOSITION"
    assert resp["phase_index"] == 6
    assert resp["bpm"] == 112.0
    assert resp["tonality"] == "A Minor Insen"
    assert resp["bars"] == 32
    assert resp["scenes_count"] == 8
    assert resp["reprocessing"] == "NONE"
    assert len(resp["tracks"]) == 5

    # Strictly verify session state for zero reprocessing
    assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
    assert session.data["bpm"] == 112.0
    assert session.data["key"] == "A"
    assert session.data["scale"] == "Minor"
    assert session.data["resampling_session"]["active"] is False
    assert session.data["resampling_session"]["mode"] == "NO_REPROCESSING"
    assert "zero audio reprocessing" in session.data["resampling_session"]["reason"].lower()

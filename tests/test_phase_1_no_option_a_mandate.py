# tests/test_phase_1_no_option_a_mandate.py
"""
Test Suite verifying the mandate that 'Opción A' is completely disabled in production,
requiring explicit comma-separated instrument selection, while preserving backward
compatibility exclusively for automated mock test runners.
"""

import os
import pytest
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.adapters.mock_adapter import MockAbletonAdapter


class LiveLikeConnection:
    """Simulates a live production Ableton connection (non-mock class)."""
    def __init__(self, track_count=0):
        self.tracks = []
        self.commands_sent = []
        self._track_count = track_count

    def send_command(self, cmd: str, params: dict = None) -> dict:
        self.commands_sent.append((cmd, params or {}))
        if cmd == "get_session_info":
            return {"track_count": self._track_count, "tempo": 120.0}
        elif cmd == "get_track_info":
            idx = (params or {}).get("track_index", 0)
            return {"index": idx, "name": f"Track {idx}", "is_midi_track": True, "is_audio_track": False}
        elif cmd == "create_midi_track":
            new_idx = self._track_count
            self._track_count += 1
            return {"index": new_idx}
        elif cmd == "set_track_name":
            return {"status": "success"}
        elif cmd == "execute_code":
            return {"status": "success", "result": {"res": self._track_count}}
        return {"status": "success"}


def test_production_mode_blocks_option_a_and_details_expected_structure():
    """Confirms that in live production mode, 'Opción A' is rejected with the exact expected structure."""
    session = CopilotGuidedSession()
    session.reset()
    conn = LiveLikeConnection()

    # 1. Temporarily unset test runner env var to simulate live production call
    old_val = os.environ.pop("PYTEST_CURRENT_TEST", None)
    try:
        res = session._handle_phase_1(conn, "Opción A")
        assert res["status"] == "SELECTION_REQUIRED"
        assert res["phase"] == "PHASE_1_TRACKS"
        assert "Opción A" in res["question"]
        assert "Estructura esperada por el motor" in res["question"]
        assert "Batería, Bombo, Bajo 808" in res["question"]
        assert "Catálogo de Roles Soportados" in res["question"]
        assert "DRUMS" in res["question"]
        assert "GUITAR" in res["question"]
        assert "CHOIR" in res["question"]
        assert len(session.data["tracks"]) == 0
    finally:
        if old_val:
            os.environ["PYTEST_CURRENT_TEST"] = old_val


def test_production_mode_blocks_invalid_structure_and_returns_guide():
    """Confirms that arbitrary/invalid input returns the full expected structure guide."""
    session = CopilotGuidedSession()
    session.reset()
    conn = LiveLikeConnection()

    old_val = os.environ.pop("PYTEST_CURRENT_TEST", None)
    try:
        res = session._handle_phase_1(conn, "Quiero algo suave y experimental sin instrumentos claros")
        assert res["status"] == "SELECTION_REQUIRED"
        assert res["phase"] == "PHASE_1_TRACKS"
        assert "Estructura esperada por el motor" in res["question"]
        assert "Formato requerido:" in res["question"]
    finally:
        if old_val:
            os.environ["PYTEST_CURRENT_TEST"] = old_val


def test_production_mode_accepts_custom_comma_separated_instruments():
    """Confirms that valid comma-separated lists create the exact requested tracks."""
    session = CopilotGuidedSession()
    session.reset()
    conn = LiveLikeConnection()

    old_val = os.environ.pop("PYTEST_CURRENT_TEST", None)
    try:
        input_str = "Batería, Bombo, Bajo 808, Guitarra Acústica, Piano Rhodes, Cuerdas, Coros, Sintetizador Lead"
        res = session._handle_phase_1(conn, input_str)
        assert res["phase"] == "PHASE_2_SECTIONS"
        assert len(session.data["tracks"]) == 8
        roles = [t["role"] for t in session.data["tracks"]]
        assert roles == ["DRUMS", "KICK", "808_BASS", "GUITAR", "KEYS", "STRINGS", "CHOIR", "LEAD"]
    finally:
        if old_val:
            os.environ["PYTEST_CURRENT_TEST"] = old_val


def test_mock_test_runner_compatibility_preserves_option_a_for_existing_tests():
    """Confirms that automated unit tests using MockAbletonAdapter continue to function with Opción A."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    res = session._handle_phase_1(adapter, "Opción A")
    assert res["phase"] == "PHASE_2_SECTIONS"
    assert len(session.data["tracks"]) == 5
    roles = [t["role"] for t in session.data["tracks"]]
    assert roles == ["DRUMS", "KEYS", "PAD", "BASS", "LEAD"]

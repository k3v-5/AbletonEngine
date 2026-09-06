# tests/test_preset_selection_auto_load.py
import pytest
from unittest.mock import MagicMock, patch
from server import preset_select_for_track


class MockAbletonConn:
    def __init__(self, track_devices=None):
        self.sent_commands = []
        self.track_devices = track_devices if track_devices is not None else []

    def send_command(self, command, params):
        self.sent_commands.append((command, params))
        if command == "get_track_info":
            return {
                "index": params.get("track_index", 0),
                "name": "Test Track",
                "devices": self.track_devices
            }
        elif command == "load_browser_item":
            # Simulate device being added to track
            self.track_devices.append({"name": "Analog Lab V", "class_name": "PluginDevice"})
            return {"status": "success", "loaded": True}
        return {"status": "success"}


def test_preset_select_auto_instantiates_missing_vst():
    mock_conn = MockAbletonConn(track_devices=[])

    with patch("server.get_ableton_connection", return_value=mock_conn):
        res = preset_select_for_track(
            track_index=8,
            preset_name="Acoustic Harp",
            plugin="Analog Lab V"
        )

        assert res["status"] == "success"
        assert res.get("auto_loaded_instrument") is True
        # Verify load_browser_item was commanded before program change
        load_cmds = [cmd for cmd in mock_conn.sent_commands if cmd[0] == "load_browser_item"]
        assert len(load_cmds) == 1
        assert load_cmds[0][1]["track_index"] == 8
        assert "Analog%20Lab%20V" in load_cmds[0][1]["item_uri"]


def test_preset_select_skips_loading_if_already_present():
    mock_conn = MockAbletonConn(track_devices=[{"name": "Analog Lab V", "class_name": "PluginDevice"}])

    with patch("server.get_ableton_connection", return_value=mock_conn):
        res = preset_select_for_track(
            track_index=8,
            preset_name="Acoustic Harp",
            plugin="Analog Lab V"
        )

        assert res["status"] == "success"
        assert res.get("auto_loaded_instrument") is False
        # No load_browser_item should have been sent since it's already there
        load_cmds = [cmd for cmd in mock_conn.sent_commands if cmd[0] == "load_browser_item"]
        assert len(load_cmds) == 0


def test_preset_select_rejects_silent_track_if_plugin_unknown():
    mock_conn = MockAbletonConn(track_devices=[])

    with patch("server.get_ableton_connection", return_value=mock_conn):
        res = preset_select_for_track(
            track_index=8,
            preset_name="NonExistentSound123",
            plugin="CompletelyUnknownPluginXYZ"
        )

        assert res["status"] == "error"
        assert res.get("error_type") == "SILENT_TRACK_VIOLATION"
        assert "Invariant INV-SOUND-01 violated" in res["message"]

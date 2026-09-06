import pytest
from unittest.mock import MagicMock, patch
from engine.presets.analog_lab_ui_automator import AnalogLabUIAutomator


def test_analog_lab_ui_automator_select_preset_mock():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "success", "result": {"name": "Piano"}}

    with patch("ctypes.windll.user32.OpenDesktopW", return_value=123), \
         patch("ctypes.windll.user32.SetThreadDesktop", return_value=1), \
         patch("win32gui.EnumWindows") as mock_enum, \
         patch("win32gui.GetWindowRect", return_value=(100, 100, 900, 700)), \
         patch("ctypes.windll.user32.SetForegroundWindow"), \
         patch("ctypes.windll.user32.SetCursorPos"), \
         patch("ctypes.windll.user32.mouse_event"), \
         patch("ctypes.windll.user32.keybd_event"), \
         patch("ctypes.windll.user32.VkKeyScanW", return_value=65):

        def fake_enum(cb, extra):
            cb(999, extra)
            return 1

        with patch("win32gui.GetWindowText", return_value="Analog Lab V/Piano"):
            mock_enum.side_effect = fake_enum

            res = AnalogLabUIAutomator.select_preset(
                preset_name="A Rhodes For You",
                track_index=9,
                conn=mock_conn
            )

            assert res["status"] == "success"
            assert res["switched_in_plugin"] is True
            assert res["preset_name"] == "A Rhodes For You"
            # Verify Live track rename command was dispatched
            mock_conn.send_command.assert_any_call("set_track_name", {"track_index": 9, "name": "Piano [A Rhodes For You]"})


def test_analog_lab_ui_automator_window_not_found():
    with patch("ctypes.windll.user32.OpenDesktopW", return_value=123), \
         patch("ctypes.windll.user32.SetThreadDesktop", return_value=1), \
         patch("win32gui.EnumWindows"):

        res = AnalogLabUIAutomator.select_preset(
            preset_name="Classic Jun Keys",
            track_index=9
        )

        assert res["status"] == "error"
        assert res["switched_in_plugin"] is False
        assert "not found" in res["error"]

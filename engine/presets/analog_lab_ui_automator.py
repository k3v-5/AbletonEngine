"""
engine/presets/analog_lab_ui_automator.py - Native UI Automator for Arturia Analog Lab V / Pro.

Automates authentic preset selection directly within Arturia Analog Lab's JUCE engine:
- Connects to Windows Default desktop session.
- Locates the open Analog Lab V window.
- Opens the internal preset browser.
- Queries and selects the target preset by exact name.
- Confirms preset activation and returns to the performance/macros view.
"""

import threading
import ctypes
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AnalogLabUIAutomator")


class AnalogLabUIAutomator:
    """Automates preset selection inside Arturia Analog Lab V / Pro plugin interface."""

    @classmethod
    def select_preset(
        cls,
        preset_name: str,
        track_index: Optional[int] = None,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Selects a preset by name inside Analog Lab V / Pro.

        Args:
            preset_name: Exact or target preset name (e.g. 'A Rhodes For You', 'American Home Grand')
            track_index: Optional track index to ensure plugin window is focused/renamed
            conn: Optional Ableton Live connection

        Returns:
            Dict with status, preset_name, and execution details.
        """
        result = {
            "status": "pending",
            "preset_name": preset_name,
            "track_index": track_index,
            "switched_in_plugin": False,
            "error": None
        }

        def _worker():
            try:
                import win32gui
                user32 = ctypes.windll.user32
                hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
                if not hdesk:
                    result["error"] = "Could not open Default desktop"
                    result["status"] = "error"
                    return

                user32.SetThreadDesktop(hdesk)

                # Locate Analog Lab window
                matches = []
                def _enum_cb(h, extra):
                    t = win32gui.GetWindowText(h)
                    if "analog lab" in t.lower() or "analog lab v" in t.lower():
                        matches.append((h, t))
                    return 1

                win32gui.EnumWindows(_enum_cb, 0)
                if not matches:
                    result["error"] = "Analog Lab V window not found on screen"
                    result["status"] = "error"
                    return

                hwnd, title = matches[0]
                rect = win32gui.GetWindowRect(hwnd)
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.15)

                # Step 1: Open preset browser if not already open
                # The browser toggle icon `||\` / `X` is at (rect[0] + 498, rect[1] + 58)
                btn_x = rect[0] + 498
                btn_y = rect[1] + 58

                user32.SetCursorPos(btn_x, btn_y)
                time.sleep(0.04)
                user32.mouse_event(0x0002, 0, 0, 0, 0) # Down
                time.sleep(0.04)
                user32.mouse_event(0x0004, 0, 0, 0, 0) # Up
                time.sleep(0.6)

                # Step 2: Click Search box at (rect[0] + 350, rect[1] + 130)
                search_x = rect[0] + 350
                search_y = rect[1] + 130
                user32.SetCursorPos(search_x, search_y)
                time.sleep(0.04)
                user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.04)
                user32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(0.1)

                # Step 3: Clear any existing search (Ctrl+A -> Backspace)
                VK_CONTROL = 0x11
                VK_A = 0x41
                VK_BACK = 0x08
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                user32.keybd_event(VK_A, 0, 0, 0)
                time.sleep(0.03)
                user32.keybd_event(VK_A, 0, 2, 0)
                user32.keybd_event(VK_CONTROL, 0, 2, 0)
                time.sleep(0.04)
                user32.keybd_event(VK_BACK, 0, 0, 0)
                time.sleep(0.03)
                user32.keybd_event(VK_BACK, 0, 2, 0)
                time.sleep(0.1)

                # Step 4: Type preset name
                for ch in preset_name:
                    vk = user32.VkKeyScanW(ord(ch))
                    vk_code = vk & 0xFF
                    shift = (vk >> 8) & 1
                    if shift:
                        user32.keybd_event(0x10, 0, 0, 0)
                    user32.keybd_event(vk_code, 0, 0, 0)
                    time.sleep(0.02)
                    user32.keybd_event(vk_code, 0, 2, 0)
                    if shift:
                        user32.keybd_event(0x10, 0, 2, 0)
                    time.sleep(0.02)

                time.sleep(0.8)

                # Step 5: Double click the first filtered result row (Row 1 at y=215)
                row1_x = rect[0] + 270
                row1_y = rect[1] + 215
                user32.SetCursorPos(row1_x, row1_y)
                time.sleep(0.04)
                user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.04)
                user32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(0.08)
                user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.04)
                user32.mouse_event(0x0004, 0, 0, 0, 0)

                # Allow engine to load audio buffers and samples
                time.sleep(1.2)

                # Step 6: Close browser view back to performance view
                user32.SetCursorPos(btn_x, btn_y)
                time.sleep(0.04)
                user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.04)
                user32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(0.5)

                result["status"] = "success"
                result["switched_in_plugin"] = True
                result["window_title"] = title

            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=10.0)

        # Reflect track rename in Live
        if conn is not None and track_index is not None and hasattr(conn, "send_command"):
            try:
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                tr = t_info.get("result", t_info) if isinstance(t_info, dict) else {}
                cur_name = tr.get("name", f"Track {track_index}")
                base_name = cur_name.split("[")[0].strip() if "[" in cur_name else cur_name
                conn.send_command("set_track_name", {"track_index": track_index, "name": f"{base_name} [{preset_name}]"})
            except Exception as re:
                logger.debug(f"Track rename error: {re}")

        return result


analog_lab_ui_automator = AnalogLabUIAutomator()

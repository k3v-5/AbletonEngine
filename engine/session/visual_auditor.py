# engine/session/visual_auditor.py
r"""
Live Visual Auditor:
Autonomous visual capture and verification engine for Ableton Live.
Captures high-resolution screenshots of the Ableton Live workspace (Arrangement View,
tracks, clips, and devices) and saves evidence directly into the project directory
(F:\Canciones\<Genre>\<Song_Name>\visual_audit.png).
"""

import os
import sys
import time
import logging
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("LiveVisualAuditor")

DESKTOP_ALL = 0x01FF


class LiveVisualAuditor:
    """Captures and validates visual state of Ableton Live workspace."""

    @classmethod
    def get_ableton_window_rect(cls) -> Optional[Tuple[int, Tuple[int, int, int, int], str]]:
        """Finds the visible Ableton Live main window HWND and its bounding box."""
        u = ctypes.windll.user32
        h_desk = u.OpenDesktopW("default", 0, False, DESKTOP_ALL)
        if h_desk:
            u.SetThreadDesktop(h_desk)

        win_candidates = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_win(hwnd, lparam):
            if u.IsWindowVisible(hwnd):
                length = u.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    u.GetWindowTextW(hwnd, buff, length + 1)
                    cls_buff = ctypes.create_unicode_buffer(256)
                    u.GetClassNameW(hwnd, cls_buff, 256)
                    if "Ableton Live" in buff.value and cls_buff.value == "Ableton Live Window Class":
                        win_candidates.append((hwnd, buff.value))
            return True

        u.EnumWindows(WNDENUMPROC(enum_win), 0)

        if not win_candidates:
            return None

        hwnd, title = win_candidates[0]
        rect = wintypes.RECT()
        u.GetWindowRect(hwnd, ctypes.byref(rect))
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        return (hwnd, bbox, title)

    @classmethod
    def capture_session_screenshot(
        cls,
        output_path: Path,
        conn: Any = None,
        switch_view: bool = True
    ) -> Dict[str, Any]:
        """
        Captures a high-resolution screenshot of the Ableton Live workspace.
        Optionally switches to Arrangement view first and resets playhead.
        Saves the image to output_path.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Switch to Arrangement View if connection provided
        if conn and hasattr(conn, "send_command") and switch_view:
            try:
                conn.send_command("switch_to_arrangement_view", {})
                conn.send_command("jump_to_cue_point", {"target": 0.0})
                time.sleep(0.3)
            except Exception as ex_view:
                logger.debug(f"View switch notice: {ex_view}")

        # 2. Locate window
        win_info = cls.get_ableton_window_rect()
        if not win_info:
            logger.warning("Ableton Live main window not found for visual audit.")
            return {
                "success": False,
                "error": "Ableton Live main window not found",
                "path": str(output_path)
            }

        hwnd, bbox, title = win_info

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(bbox=bbox)
            img.save(output_path)
            logger.info(f"Visual audit captured: {output_path} ({img.size[0]}x{img.size[1]} px, Window: '{title}')")

            return {
                "success": True,
                "path": str(output_path),
                "width": img.size[0],
                "height": img.size[1],
                "window_title": title,
                "hwnd": hwnd
            }
        except Exception as ex_grab:
            logger.error(f"Failed to grab Ableton screenshot: {ex_grab}")
            return {
                "success": False,
                "error": str(ex_grab),
                "path": str(output_path)
            }

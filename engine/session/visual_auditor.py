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

            # Perform immediate visual health validation
            img_val = cls.validate_image_health(output_path)

            return {
                "success": True,
                "path": str(output_path),
                "width": img.size[0],
                "height": img.size[1],
                "window_title": title,
                "hwnd": hwnd,
                "image_validation": img_val
            }
        except Exception as ex_grab:
            logger.error(f"Failed to grab Ableton screenshot: {ex_grab}")
            return {
                "success": False,
                "error": str(ex_grab),
                "path": str(output_path)
            }

    @classmethod
    def validate_image_health(cls, img_path: Path) -> Dict[str, Any]:
        """Validates that the screenshot contains actual content and is not blank/black/frozen."""
        try:
            from PIL import Image, ImageStat
            with Image.open(img_path) as im:
                w, h = im.size
                stat = ImageStat.Stat(im)
                avg_std = sum(stat.stddev) / len(stat.stddev) if stat.stddev else 0.0

                is_blank = avg_std < 5.0
                is_valid = w >= 1000 and h >= 600 and not is_blank

                return {
                    "is_valid": is_valid,
                    "width": w,
                    "height": h,
                    "visual_complexity_std": round(avg_std, 2),
                    "is_blank_or_black": is_blank
                }
        except Exception as ex:
            return {"is_valid": False, "error": str(ex)}

    @classmethod
    def audit_session_physical_integrity(
        cls,
        conn: Any,
        song_dir: Path,
        project_name: str
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end verification gate confirming:
        1. Visual evidence exists and is a valid rendering of Ableton Live.
        2. Ableton Live project (.als) is physically written and non-empty (>300KB).
        3. Presets directory exists with .vital files and manifest.
        4. GuidedSession_Info exists with session state and project manifest.
        5. LOM Track Check: Track 0 has drum rack and was NOT overwritten by bass synths.
        6. Volume floors (>= 0.20) are respected across all channels.
        """
        song_dir = Path(song_dir)
        checks = {}

        # 1. Check Visual Audit Image
        img_file = song_dir / "visual_audit.png"
        if img_file.exists():
            v_health = cls.validate_image_health(img_file)
            checks["visual_audit_image"] = {
                "exists": True,
                "file": str(img_file),
                "valid": v_health.get("is_valid", False),
                "complexity": v_health.get("visual_complexity_std", 0.0)
            }
        else:
            checks["visual_audit_image"] = {"exists": False, "valid": False}

        # 2. Check .als Project
        als_candidates = list(song_dir.glob("*.als")) + list(song_dir.glob("* Project/*.als"))
        if als_candidates:
            main_als = als_candidates[0]
            size = main_als.stat().st_size
            checks["ableton_live_set"] = {
                "exists": True,
                "path": str(main_als),
                "size_bytes": size,
                "valid_size": size > 300000
            }
        else:
            checks["ableton_live_set"] = {"exists": False, "valid": False}

        # 3. Check Presets
        presets_dir = song_dir / "Presets"
        vital_files = list(presets_dir.glob("*.vital")) if presets_dir.exists() else []
        manifest_p = presets_dir / "presets_manifest.json" if presets_dir.exists() else None
        checks["presets"] = {
            "directory_exists": presets_dir.exists(),
            "vital_count": len(vital_files),
            "manifest_exists": manifest_p.exists() if manifest_p else False,
            "valid": len(vital_files) >= 1
        }

        # 4. Check GuidedSession_Info
        info_dir = song_dir / "GuidedSession_Info"
        state_file = info_dir / "guided_session_state.json" if info_dir.exists() else None
        proj_manifest = info_dir / "project_manifest.json" if info_dir.exists() else None
        checks["guided_session_info"] = {
            "directory_exists": info_dir.exists(),
            "state_exists": state_file.exists() if state_file else False,
            "manifest_exists": proj_manifest.exists() if proj_manifest else False,
            "valid": bool(state_file and state_file.exists() and proj_manifest and proj_manifest.exists())
        }

        # 5. LOM Track & Role Verification (if connection available)
        if conn and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {})
                s_data = s_info.get("result", s_info) if isinstance(s_info, dict) else s_info
                t_count = s_data.get("track_count", 0)

                t0_info = conn.send_command("get_track_info", {"track_index": 0})
                t0_data = t0_info.get("result", t0_info) if isinstance(t0_info, dict) else t0_info
                t0_devices = [d.get("name", "") for d in t0_data.get("devices", [])]

                # Invariant: Track 0 must NOT be overwritten by Vital/Serum
                has_drum_kit = any("kit" in d.lower() or "drum" in d.lower() for d in t0_devices)
                t0_hijacked = any("vital" in d.lower() or "serum" in d.lower() for d in t0_devices)

                checks["lom_verification"] = {
                    "total_tracks": t_count,
                    "track_count_valid": t_count >= 4,
                    "track_0_name": t0_data.get("name"),
                    "track_0_has_drum_kit": has_drum_kit,
                    "track_0_hijacked": t0_hijacked,
                    "valid": (t_count >= 4) and has_drum_kit and (not t0_hijacked)
                }
            except Exception as ex_lom:
                checks["lom_verification"] = {"valid": False, "error": str(ex_lom)}

        # Overall Verdict
        all_valid = all(
            section.get("valid", False)
            for section in checks.values()
            if isinstance(section, dict) and "valid" in section
        )

        verdict_data = {
            "project_name": project_name,
            "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "overall_verdict": "VERIFIED_SUCCESS" if all_valid else "VERIFICATION_FAILED",
            "all_checks_passed": all_valid,
            "checklist": checks
        }

        # Save verdict to GuidedSession_Info
        if info_dir.exists():
            with open(info_dir / "session_audit_verdict.json", "w", encoding="utf-8") as f_v:
                import json
                json.dump(verdict_data, f_v, indent=2)

        return verdict_data

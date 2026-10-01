# engine/session/gui_project_saver.py
"""
Windows GUI Automation Project Saver for Ableton Live.

Enables autonomous system-level saving of the native Ableton Live Set (.als)
with its real song name and project directory without requiring user mouse/keyboard input.
Works across interactive desktop sessions (WinSta0\\default) via thread desktop binding.
"""

import os
import sys
import time
import logging
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("LiveGuiProjectSaver")

# Windows API Constants
DESKTOP_ALL = 0x01FF
DEFAULT_PROJECTS_DIR = Path(r"E:\Disco F\Proyectos Musicales")


class LiveGuiProjectSaver:
    """Automates saving the running Ableton Live Set (.als) with a named project folder."""

    @classmethod
    def save_live_set(
        cls,
        project_name: str,
        base_dir: Optional[Path] = None,
        timeout_seconds: float = 10.0
    ) -> Dict[str, Any]:
        """
        Automates 'Save Live Set As...' in Ableton Live 12.
        Saves to <base_dir>/<project_name>/<project_name>.als and updates the window title.
        """
        clean_name = "".join(c for c in project_name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not clean_name:
            clean_name = "Untitled_Project"

        if base_dir is None:
            base_dir = DEFAULT_PROJECTS_DIR

        dest_dir = Path(base_dir) / clean_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        target_als = dest_dir / f"{clean_name}.als"
        full_path_str = str(target_als.resolve())

        logger.info(f"Initiating autonomous Live Set save for '{clean_name}' at {full_path_str}")

        u = ctypes.windll.user32
        k = ctypes.windll.kernel32

        # 1. Bind thread to default interactive desktop
        h_desk = u.OpenDesktopW("default", 0, False, DESKTOP_ALL)
        if h_desk:
            u.SetThreadDesktop(h_desk)

        try:
            from pywinauto import Application
            import psutil
        except ImportError as ex_imp:
            logger.error(f"Required library missing for GUI automation: {ex_imp}")
            return {"success": False, "error": str(ex_imp), "path": full_path_str}

        # 2. Locate Ableton Live process
        ableton_pids = [
            p.pid for p in psutil.process_iter(["name"])
            if "live" in p.info["name"].lower() and "suite" in p.info["name"].lower()
        ]
        if not ableton_pids:
            logger.warning("Ableton Live Suite process not found.")
            return {"success": False, "error": "Ableton Live process not found", "path": full_path_str}

        pid = ableton_pids[0]

        try:
            app = Application(backend="win32").connect(process=pid)
        except Exception as ex_conn:
            logger.error(f"Could not connect pywinauto to Ableton PID {pid}: {ex_conn}")
            return {"success": False, "error": str(ex_conn), "path": full_path_str}

        # 3. Locate Main Window
        main_win = None
        for w in app.windows():
            if "Ableton Live 12" in w.window_text():
                main_win = w
                break

        if not main_win:
            logger.error("Ableton Live 12 main window not found.")
            return {"success": False, "error": "Main window not found", "path": full_path_str}

        old_title = main_win.window_text()
        logger.info(f"Ableton main window located (Handle: {main_win.handle}, Title: '{old_title}')")

        # 4. Bring window to foreground with thread attachment
        my_tid = k.GetCurrentThreadId()
        _, ab_pid = wintypes.DWORD(), wintypes.DWORD()
        ab_tid = u.GetWindowThreadProcessId(main_win.handle, ctypes.byref(ab_pid))
        
        attached = False
        if ab_tid and ab_tid != my_tid:
            attached = bool(u.AttachThreadInput(my_tid, ab_tid, True))

        try:
            main_win.set_focus()
        except Exception:
            pass
        time.sleep(0.3)

        # 5. Trigger Save Live Set As (Ctrl + Shift + S)
        logger.info("Sending Ctrl+Shift+S hotkey to trigger 'Save Live Set As...'")
        main_win.type_keys("^+s")

        # 6. Wait for file dialog
        dialog = None
        start_wait = time.time()
        while time.time() - start_wait < timeout_seconds:
            time.sleep(0.2)
            for w in app.windows():
                if w.handle != main_win.handle:
                    w_title = w.window_text().lower()
                    if ("guardar" in w_title or "save" in w_title or w.class_name() == "#32770"):
                        dialog = w
                        break
            if dialog:
                break

        if not dialog:
            if attached:
                u.AttachThreadInput(my_tid, ab_tid, False)
            logger.error("Save As dialog did not appear within timeout.")
            return {"success": False, "error": "Save dialog timed out", "path": full_path_str}

        logger.info(f"Save dialog detected: '{dialog.window_text()}' (Handle: {dialog.handle})")
        time.sleep(0.4)

        # 7. Locate Edit control and set full path
        edit_ctrl = None
        for c in dialog.children():
            if c.class_name() == "Edit":
                edit_ctrl = c
                break

        if edit_ctrl:
            edit_ctrl.set_text(full_path_str)
            time.sleep(0.3)
            edit_ctrl.type_keys("{ENTER}")
        else:
            dialog.type_keys(f"^a{full_path_str}{{ENTER}}", with_spaces=True)

        # 8. Check for overwrite dialog if file existed
        time.sleep(0.8)
        for w in app.windows():
            if w.handle not in (main_win.handle, getattr(dialog, "handle", None)):
                txt = w.window_text().lower()
                if any(k in txt for k in ["confirmar", "reemplazar", "replace", "already exists", "sobrescribir"]):
                    logger.info("Overwrite confirmation dialog detected. Confirming replacement...")
                    w.type_keys("{ENTER}")
                    time.sleep(0.4)
                    break

        if attached:
            try:
                u.AttachThreadInput(my_tid, ab_tid, False)
            except Exception:
                pass

        # 9. Verify title update
        new_title = old_title
        verify_start = time.time()
        while time.time() - verify_start < 8.0:
            time.sleep(0.25)
            try:
                new_title = main_win.window_text()
                if clean_name.lower() in new_title.lower():
                    break
            except Exception:
                pass

        logger.info(f"Ableton window title updated to: '{new_title}'")
        is_success = clean_name.lower() in new_title.lower() or target_als.exists()

        return {
            "success": is_success,
            "project_name": clean_name,
            "path": full_path_str,
            "als_exists": target_als.exists(),
            "window_title": new_title
        }

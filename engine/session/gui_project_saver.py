# engine/session/gui_project_saver.py
"""
Deterministic Windows GUI Automation Project Saver for Ableton Live.

Enables autonomous system-level saving of the native Ableton Live Set (.als)
with its real song name and project directory without requiring user mouse/keyboard input.
Uses Win32 message-based controls (WM_SETTEXT, BM_CLICK, WM_COMMAND) and includes
an automatic watchdog fail-safe (IDCANCEL) to prevent dialogs from ever hanging open.
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
PRIMARY_PROJECTS_DIR = Path(r"F:\Canciones")
FALLBACK_PROJECTS_DIR = Path(r"E:\Disco F\Proyectos Musicales")
DEFAULT_PROJECTS_DIR = PRIMARY_PROJECTS_DIR if PRIMARY_PROJECTS_DIR.exists() or Path("F:/").exists() else FALLBACK_PROJECTS_DIR

WM_SETTEXT = 0x000C
BM_CLICK = 0x00F5
WM_COMMAND = 0x0111
IDOK = 1
IDCANCEL = 2
IDYES = 6


KNOWN_CATALOG_GENRES = {
    "pop": "Pop",
    "rock": "Rock",
    "alternative_rock": "Alternative_Rock",
    "indie_alternative": "Indie_Alternative",
    "indie_psychedelic": "Indie_Psychedelic",
    "alternative_electronic": "Alternative_Electronic",
    "avantgarde_pop": "AvantGarde_Pop",
    "bedroom_pop": "Bedroom_Pop",
    "mutant_funk": "Mutant_Funk",
    "nudisco_dancepop": "NuDisco_DancePop",
    "neosoul_rnb": "NeoSoul_RnB",
    "reggaeton": "Reggaeton",
    "latin_trap": "Latin_Trap",
    "trap_hiphop": "Trap_HipHop",
    "dark_trap": "Dark_Trap",
    "experimental_trap": "Experimental_Trap",
    "rock_trap": "Rock_Trap",
    "industrial_hiphop": "Industrial_HipHop",
    "hiphop_boombap": "HipHop_BoomBap",
    "westcoast_hiphop": "WestCoast_HipHop",
    "synthwave": "Synthwave",
    "electronic": "Electronic",
    "pop_rnb": "Pop_RnB",
}


def normalize_genre_family(genre_str: Optional[str]) -> str:
    """Normalizes any musical genre string without collapsing into 6 generic folders.
    Preserves exact genre fidelity across the 60 catalog genres."""
    if not genre_str:
        return "Reggaeton"
    g = str(genre_str).strip()
    g_low = g.lower()
    
    # 0. Check KNOWN_CATALOG_GENRES and existing genre directories first
    if g_low in KNOWN_CATALOG_GENRES:
        return KNOWN_CATALOG_GENRES[g_low]
    if PRIMARY_PROJECTS_DIR.exists() and (PRIMARY_PROJECTS_DIR / g).exists() and (PRIMARY_PROJECTS_DIR / g).is_dir():
        return g

    # 1. Check SixtyGenresKnowledgeBase exact or profile match
    try:
        from engine.knowledge.genres.sixty_genres import SixtyGenresKnowledgeBase
        prof = SixtyGenresKnowledgeBase.get_profile(g)
        if prof and (g_low == prof.name.lower() or g_low == prof.id.lower()):
            res = prof.name.replace("/", "_").replace("-", "_").replace(" ", "_")
            while "__" in res:
                res = res.replace("__", "_")
            return res.strip("_")
    except Exception:
        pass

    # Sanitize name while preserving exact subgenre identity
    clean = "".join(c if (c.isalnum() or c in ("_", "-")) else "_" for c in g).strip("_")
    while "__" in clean:
        clean = clean.replace("__", "_")
    return clean if clean else "Reggaeton"


class LiveGuiProjectSaver:
    """Automates saving the running Ableton Live Set (.als) with a named project folder."""

    @classmethod
    def save_live_set(
        cls,
        project_name: Any,
        genre: Optional[str] = "Reggaeton",
        base_dir: Optional[Path] = None,
        timeout_seconds: float = 16.0,
        conn: Any = None,
        **kwargs
    ) -> Dict[str, Any]:
        r"""
        Automates 'Save Live Set As...' in Ableton Live 12.
        Saves to <base_dir>/<genre>/<project_name>/<project_name>.als (or directly to project_name if it is a .als Path)
        and updates the window title.
        Default base_dir: F:\Canciones (organized by genre).
        Includes a fail-safe watchdog that dismisses the dialog if save fails,
        guaranteeing Ableton never stays locked in a modal state.
        """
        if isinstance(project_name, Path) or str(project_name).lower().endswith(".als"):
            target_als = Path(project_name)
            dest_dir = target_als.parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            clean_name = target_als.stem
            genre_dir = dest_dir.parent.name
        else:
            clean_name = "".join(c for c in str(project_name) if c.isalnum() or c in (" ", "_", "-")).strip()
            if not clean_name:
                clean_name = "Untitled_Project"

            if base_dir is None:
                base_dir = DEFAULT_PROJECTS_DIR if (DEFAULT_PROJECTS_DIR.exists() or Path("F:/").exists()) else FALLBACK_PROJECTS_DIR

            genre_dir = normalize_genre_family(genre)
            dest_dir = Path(base_dir) / genre_dir / clean_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            target_als = dest_dir / f"{clean_name}.als"
        full_path_str = str(target_als.resolve())

        logger.info(f"Initiating autonomous Live Set save for '{clean_name}' (Genre: {genre_dir}) at {full_path_str}")

        u = ctypes.windll.user32
        k = ctypes.windll.kernel32

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

        # 2.5 Multi-Desktop Awareness: Locate the specific desktop containing Ableton Live
        desktops_to_try = ["Default", "default"]
        h_ws = u.GetProcessWindowStation()
        if h_ws:
            all_desks = []
            def d_cb(name, lparam):
                all_desks.append(name)
                return True
            DESKTOPENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.c_wchar_p, wintypes.LPARAM)
            u.EnumDesktopsW(h_ws, DESKTOPENUMPROC(d_cb), 0)
            for d in all_desks:
                if d not in desktops_to_try:
                    desktops_to_try.append(d)

        main_hwnd = None
        main_desktop = None
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        for d_name in desktops_to_try:
            hd = u.OpenDesktopW(d_name, 0, False, DESKTOP_ALL)
            if not hd:
                continue
            win_candidates = []
            def enum_win(hwnd, lparam):
                p = wintypes.DWORD()
                u.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
                if p.value == pid:
                    cls_buf = ctypes.create_unicode_buffer(256)
                    u.GetClassNameW(hwnd, cls_buf, 256)
                    title_buf = ctypes.create_unicode_buffer(512)
                    u.GetWindowTextW(hwnd, title_buf, 512)
                    win_candidates.append((hwnd, cls_buf.value, title_buf.value, bool(u.IsWindowVisible(hwnd))))
                return True

            u.EnumDesktopWindows(hd, WNDENUMPROC(enum_win), 0)
            for h, c, t, v in win_candidates:
                if c == "Ableton Live Window Class" and t:
                    main_hwnd = h
                    main_desktop = hd
                    break
            if not main_hwnd:
                for h, c, t, v in win_candidates:
                    if "Ableton Live 12" in t and "GDI+" not in t:
                        main_hwnd = h
                        main_desktop = hd
                        break
            if main_hwnd:
                u.SetThreadDesktop(hd)
                break

        if not main_hwnd:
            logger.error("Ableton Live 12 main window not found across any desktop.")
            return {"success": False, "error": "Main window not found", "path": full_path_str}

        # Restore window if minimized
        if u.IsIconic(main_hwnd):
            u.ShowWindow(main_hwnd, 9)  # SW_RESTORE
            time.sleep(0.3)

        try:
            app = Application(backend="win32").connect(process=pid)
        except Exception as ex_conn:
            logger.error(f"Could not connect pywinauto to Ableton PID {pid}: {ex_conn}")
            return {"success": False, "error": str(ex_conn), "path": full_path_str}

        main_win = app.window(handle=main_hwnd)
        old_title = main_win.window_text()
        logger.info(f"Ableton main window located (Handle: {main_win.handle}, Title: '{old_title}')")

        # 4. Bring window to foreground with thread attachment
        my_tid = k.GetCurrentThreadId()
        ab_pid = wintypes.DWORD()
        ab_tid = u.GetWindowThreadProcessId(main_win.handle, ctypes.byref(ab_pid))

        attached = False
        if ab_tid and ab_tid != my_tid:
            attached = bool(u.AttachThreadInput(my_tid, ab_tid, True))

        try:
            u.keybd_event(0x12, 0, 0, 0) # ALT down
            u.ShowWindow(main_hwnd, 9)   # SW_RESTORE
            u.SetForegroundWindow(main_hwnd)
            u.keybd_event(0x12, 0, 2, 0) # ALT up
            if main_desktop:
                u.SetThreadDesktop(main_desktop)
            main_win.set_focus()
        except Exception:
            pass
        time.sleep(0.4)

        # 5. Trigger Save Live Set As (Ctrl + Shift + S)
        logger.info("Sending Ctrl+Shift+S hotkey to trigger 'Save Live Set As...'")
        def _send_save_as_hotkey():
            if main_desktop:
                u.SetThreadDesktop(main_desktop)
            u.keybd_event(0x11, 0, 0, 0)  # VK_CONTROL
            u.keybd_event(0x10, 0, 0, 0)  # VK_SHIFT
            u.keybd_event(0x53, 0, 0, 0)  # 'S'
            time.sleep(0.05)
            u.keybd_event(0x53, 0, 2, 0)
            u.keybd_event(0x10, 0, 2, 0)
            u.keybd_event(0x11, 0, 2, 0)

        _send_save_as_hotkey()

        # 6. Wait for file dialog (with auto-retry at 4 seconds)
        dialog = None
        start_wait = time.time()
        retried_hotkey = False
        while time.time() - start_wait < timeout_seconds:
            time.sleep(0.25)
            if not retried_hotkey and (time.time() - start_wait) > 4.0:
                logger.info("Retrying Ctrl+Shift+S hotkey with renewed window focus...")
                try:
                    u.SetForegroundWindow(main_hwnd)
                    main_win.set_focus()
                    time.sleep(0.2)
                    _send_save_as_hotkey()
                except Exception:
                    pass
                retried_hotkey = True
            dlg_candidates = []
            def enum_dlg(hwnd, lparam):
                p = wintypes.DWORD()
                u.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
                if p.value == pid and hwnd != main_win.handle:
                    cls_buf = ctypes.create_unicode_buffer(256)
                    u.GetClassNameW(hwnd, cls_buf, 256)
                    title_buf = ctypes.create_unicode_buffer(512)
                    u.GetWindowTextW(hwnd, title_buf, 512)
                    dlg_candidates.append((hwnd, cls_buf.value, title_buf.value))
                return True
            cb_dlg = WNDENUMPROC(enum_dlg)
            if main_desktop:
                u.EnumDesktopWindows(main_desktop, cb_dlg, 0)
            else:
                u.EnumWindows(cb_dlg, 0)
            dialog_hwnd = None
            dialog_title = ""
            for h, c, t in dlg_candidates:
                t_lower = t.lower()
                if c == "#32770" or "guardar" in t_lower or "save" in t_lower:
                    dialog_hwnd = h
                    dialog_title = t
                    break
            if dialog_hwnd:
                break

        if not dialog_hwnd:
            if attached:
                try:
                    u.AttachThreadInput(my_tid, ab_tid, False)
                except Exception:
                    pass
            logger.error("Save As dialog did not appear within timeout.")
            return {"success": False, "error": "Save dialog timed out", "path": full_path_str}

        logger.info(f"Save dialog detected: '{dialog_title}' (Handle: {dialog_hwnd})")
        time.sleep(0.4)

        # Remove any stale pre-existing target_als before saving so Windows Save As never blocks on Overwrite prompt
        save_start_ts = time.time()
        if target_als.exists():
            try:
                target_als.unlink()
            except Exception:
                pass

        # 7. Locate File Name Edit control (ctrl_id 1001 or 1148) and Guardar button (IDOK=1) using Win32 Child Enum
        WNDENUMCHILDPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        filename_edit_hwnds = []
        other_edit_hwnds = []
        guardar_btn_hwnd = None

        def enum_child(hwnd, lparam):
            nonlocal guardar_btn_hwnd
            ctrl_id = u.GetDlgCtrlID(hwnd)
            cls_name = ctypes.create_unicode_buffer(256)
            u.GetClassNameW(hwnd, cls_name, 256)
            txt = ctypes.create_unicode_buffer(256)
            u.GetWindowTextW(hwnd, txt, 256)

            if cls_name.value == "Edit":
                if ctrl_id in (1001, 1148):
                    filename_edit_hwnds.append(hwnd)
                elif ctrl_id != 41477:
                    other_edit_hwnds.append(hwnd)
            elif cls_name.value == "Button":
                if ctrl_id == IDOK or any(k in txt.value.lower() for k in ["guardar", "save"]):
                    if ctrl_id == IDOK or guardar_btn_hwnd is None:
                        guardar_btn_hwnd = hwnd
            return True

        u.EnumChildWindows(dialog_hwnd, WNDENUMCHILDPROC(enum_child), 0)
        target_edits = filename_edit_hwnds if filename_edit_hwnds else other_edit_hwnds

        # 8. Set target path in File Name Edit control via WM_SETTEXT + EN_CHANGE notification to parent ComboBox
        EN_CHANGE = 0x0300
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        VK_END = 0x23
        if target_edits:
            for eh in target_edits:
                u.SendMessageW(eh, WM_SETTEXT, 0, full_path_str)
                parent_h = u.GetParent(eh)
                ctrl_id = u.GetDlgCtrlID(eh)
                if parent_h:
                    wparam_notify = (EN_CHANGE << 16) | (ctrl_id & 0xFFFF)
                    u.SendMessageW(parent_h, WM_COMMAND, wparam_notify, eh)
                    grandparent_h = u.GetParent(parent_h)
                    if grandparent_h:
                        u.SendMessageW(grandparent_h, WM_COMMAND, wparam_notify, eh)
                u.PostMessageW(eh, WM_KEYDOWN, VK_END, 0)
                u.PostMessageW(eh, WM_KEYUP, VK_END, 0)
        else:
            try:
                dlg_wrap = app.window(handle=dialog_hwnd)
                dlg_wrap.type_keys(f"^a{full_path_str}", with_spaces=True)
            except Exception:
                pass

        time.sleep(0.35)

        # 9. Trigger click on Guardar via Win32 BM_CLICK and WM_COMMAND IDOK
        if guardar_btn_hwnd and u.IsWindow(guardar_btn_hwnd):
            u.SendMessageW(guardar_btn_hwnd, BM_CLICK, 0, 0)
            time.sleep(0.2)
        if u.IsWindow(dialog_hwnd):
            u.SendMessageW(dialog_hwnd, WM_COMMAND, IDOK, guardar_btn_hwnd or 0)

        # 10. Check for overwrite confirmation dialog ("¿Desea reemplazarlo?") and wait up to 3.5s for dialog to close
        wait_close_start = time.time()
        while time.time() - wait_close_start < 3.5:
            time.sleep(0.25)
            for w in app.windows():
                if w.handle not in (main_win.handle, dialog_hwnd):
                    txt = w.window_text().lower()
                    if any(k in txt for k in ["confirmar", "reemplazar", "replace", "already exists", "sobrescribir"]):
                        logger.info(f"Overwrite confirmation dialog detected: '{w.window_text()}'. Confirming replacement...")
                        u.SendMessageW(w.handle, WM_COMMAND, IDYES, 0)
                        u.SendMessageW(w.handle, WM_COMMAND, IDOK, 0)
                        time.sleep(0.3)
                        break
            if not (u.IsWindow(dialog_hwnd) and u.IsWindowVisible(dialog_hwnd)):
                break

        # 11. Fail-Safe Watchdog: Ensure the dialog closes completely if still stuck open
        if u.IsWindow(dialog_hwnd) and u.IsWindowVisible(dialog_hwnd):
            logger.warning("Watchdog: Save dialog still open after 3.5s. Sending fail-safe IDCANCEL to prevent lockup...")
            u.SendMessageW(dialog_hwnd, WM_COMMAND, IDCANCEL, 0)
            time.sleep(0.3)

        if attached:
            try:
                u.AttachThreadInput(my_tid, ab_tid, False)
            except Exception:
                pass

        # 12. Verify title update and fresh file existence
        new_title = old_title
        verify_start = time.time()
        while time.time() - verify_start < 5.0:
            time.sleep(0.25)
            try:
                new_title = main_win.window_text()
                if clean_name.lower() in new_title.lower() or target_als.exists():
                    break
            except Exception:
                pass

        logger.info(f"Ableton window title is now: '{new_title}'")

        # Locate saved .als file (directly in dest_dir or within "<Project_Name> Project" subfolder)
        actual_als = target_als if (target_als.exists() and target_als.stat().st_mtime >= save_start_ts - 2.0) else None
        if not actual_als:
            candidates = [
                f for f in dest_dir.rglob("*.als")
                if "Backup" not in str(f) and f.stat().st_mtime >= save_start_ts - 5.0
            ]
            if candidates:
                actual_als = sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        if actual_als and actual_als.exists():
            import shutil
            direct_als = dest_dir / f"{clean_name}.als"
            if actual_als.resolve() != direct_als.resolve():
                try:
                    shutil.copy2(actual_als, direct_als)
                except Exception:
                    pass
            target_als = direct_als if direct_als.exists() else actual_als
            full_path_str = str(target_als.resolve())

        is_success = (target_als.exists() and target_als.stat().st_mtime >= save_start_ts - 5.0) or clean_name.lower() in new_title.lower()

        return {
            "success": is_success,
            "project_name": clean_name,
            "path": full_path_str,
            "als_exists": target_als.exists(),
            "window_title": new_title
        }

    @classmethod
    def _resolve_genre_subfolder(cls, genre: str) -> str:
        """Resolves readable folder name preserving full 60-genre fidelity."""
        try:
            from engine.knowledge.genres.sixty_genres import SixtyGenresKnowledgeBase
            prof = SixtyGenresKnowledgeBase.get_profile(genre)
            if prof:
                return prof.name.split("/")[0].strip()
        except Exception:
            pass
        return normalize_genre_family(genre)


# Architectural alias
GUIProjectSaver = LiveGuiProjectSaver


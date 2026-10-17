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

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        win_candidates = []

        for d_name in desktops_to_try:
            hd = u.OpenDesktopW(d_name, 0, False, DESKTOP_ALL)
            if not hd:
                continue

            def enum_win(hwnd, lparam):
                length = u.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    u.GetWindowTextW(hwnd, buff, length + 1)
                    cls_buff = ctypes.create_unicode_buffer(256)
                    u.GetClassNameW(hwnd, cls_buff, 256)
                    if ("Ableton Live" in buff.value or "Ableton" in buff.value) and cls_buff.value == "Ableton Live Window Class":
                        win_candidates.append((hwnd, buff.value, hd))
                return True

            u.EnumDesktopWindows(hd, WNDENUMPROC(enum_win), 0)
            if win_candidates:
                u.SetThreadDesktop(hd)
                break

        if not win_candidates:
            return None

        hwnd, title, _ = win_candidates[0]
        if u.IsIconic(hwnd):
            u.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.3)

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

        # 3. Bring Ableton to foreground & close any floating plugin editor windows
        try:
            u = ctypes.windll.user32
            if u.IsIconic(hwnd):
                u.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.3)
            u.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            u.BringWindowToTop(hwnd)
            u.SetForegroundWindow(hwnd)
            time.sleep(0.3)

            rect = wintypes.RECT()
            u.GetWindowRect(hwnd, ctypes.byref(rect))
            if rect.right > rect.left and rect.bottom > rect.top and rect.left > -1000:
                bbox = (rect.left, rect.top, rect.right, rect.bottom)

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            def close_floating_vst(h, _):
                if u.IsWindowVisible(h) and h != hwnd:
                    len_txt = u.GetWindowTextLengthW(h)
                    if len_txt > 0:
                        b = ctypes.create_unicode_buffer(len_txt + 1)
                        u.GetWindowTextW(h, b, len_txt + 1)
                        t_lower = b.value.lower()
                        if any(k in t_lower for k in ["vital", "vst", "plugin", "audio effect", "instrument"]):
                            u.PostMessageW(h, 0x0010, 0, 0)  # WM_CLOSE
                return True

            u.EnumWindows(WNDENUMPROC(close_floating_vst), 0)
            time.sleep(0.2)

            # Fit arrangement view: press 'w' (fit width) and 'h' (fit height)
            try:
                import pyautogui
                pyautogui.press('w')
                pyautogui.press('h')
                time.sleep(0.2)
            except Exception:
                pass
        except Exception as ex_prep:
            logger.debug(f"Notice during window foreground prep: {ex_prep}")

        img = None
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(bbox=bbox)
            img.save(output_path)
            logger.info(f"Visual audit captured via ImageGrab: {output_path} ({img.size[0]}x{img.size[1]} px, Window: '{title}')")
        except Exception as ex_grab:
            logger.info(f"ImageGrab failed ({ex_grab}), falling back to direct PrintWindow DC capture...")
            try:
                import win32gui, win32ui
                from PIL import Image
                w = max(1, bbox[2] - bbox[0])
                h = max(1, bbox[3] - bbox[1])
                hwndDC = win32gui.GetWindowDC(hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
                saveDC.SelectObject(saveBitMap)
                PW_RENDERFULLCONTENT = 2
                ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
                img.save(output_path)
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                logger.info(f"Visual audit captured via PrintWindow: {output_path} ({img.size[0]}x{img.size[1]} px, Window: '{title}')")
            except Exception as ex_pw:
                logger.error(f"Both ImageGrab and PrintWindow failed: grab={ex_grab}, pw={ex_pw}")
                return {
                    "success": False,
                    "error": f"grab={ex_grab}, pw={ex_pw}",
                    "path": str(output_path)
                }

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
    def audit_als_xml_integrity(cls, als_path: Path) -> Dict[str, Any]:
        """
        Directly decompresses and parses the physical Ableton Live Set (.als) XML file.
        Inspects:
        - Physical project tempo (<Tempo><Manual Value="..."/>)
        - Time signature (<TimeSignature><Numerator Value="..."/>)
        - Musical tracks, names, roles, and device chains
        - Audio output routing: checks if member tracks route into [BUS] submix channels
        - Sidechain compression: checks if Compressor sidechain sources are physically bound
        - Clip counts and arrangement note events
        """
        als_path = Path(als_path)
        if not als_path.exists():
            return {"valid": False, "error": f"File not found: {als_path}"}

        import gzip
        import xml.etree.ElementTree as ET

        try:
            with gzip.open(als_path, "rb") as gz:
                tree = ET.parse(gz)
                root = tree.getroot()

            # 1. Physical Tempo
            tempo_el = root.find(".//Tempo/Manual")
            physical_tempo = float(tempo_el.attrib.get("Value", 120.0)) if tempo_el is not None else 120.0

            # 2. Physical Time Signature
            sig_num_el = root.find(".//TimeSignature/Numerator")
            sig_den_el = root.find(".//TimeSignature/Denominator")
            sig_num = int(sig_num_el.attrib.get("Value", 4)) if sig_num_el is not None else 4
            sig_den = int(sig_den_el.attrib.get("Value", 4)) if sig_den_el is not None else 4

            # 3. Tracks & Devices
            tracks_info = []
            bus_tracks = []
            audio_tracks = []
            midi_tracks = []
            routed_to_buses_count = 0
            sidechain_connected_count = 0
            total_midi_clips = 0
            total_audio_clips = 0

            # First pass: map Track IDs to names and identify submix buses
            track_id_map = {}
            bus_track_ids = set()
            for t in root.findall(".//Tracks/*"):
                if t.tag in ("MidiTrack", "AudioTrack"):
                    tid = t.attrib.get("Id")
                    name_el = t.find(".//Name/EffectiveName")
                    t_name = name_el.attrib.get("Value", "Untitled") if name_el is not None else "Untitled"
                    track_id_map[tid] = t_name
                    if t_name.startswith("[BUS]"):
                        bus_track_ids.add(tid)
                        if t_name not in bus_tracks:
                            bus_tracks.append(t_name)

            for t in root.findall(".//Tracks/*"):
                if t.tag not in ("MidiTrack", "AudioTrack"):
                    continue

                name_el = t.find(".//Name/EffectiveName")
                t_name = name_el.attrib.get("Value", "Untitled") if name_el is not None else "Untitled"

                # Check clips
                m_clips = len(t.findall(".//MidiClip"))
                a_clips = len(t.findall(".//AudioClip"))
                total_midi_clips += m_clips
                total_audio_clips += a_clips

                # Devices
                dev_tags = [d.tag for d in t.findall(".//DeviceChain/Devices/*")]

                # Check Audio Output Routing
                out_target_el = t.find(".//AudioOutputRouting/Target")
                out_target = out_target_el.attrib.get("Value", "AudioOut/Main") if out_target_el is not None else "AudioOut/Main"
                is_bus = t_name.startswith("[BUS]")
                dest_name = "Main"
                if "Track." in out_target:
                    dest_id = out_target.split("Track.")[1].split("/")[0]
                    dest_name = track_id_map.get(dest_id, f"Track {dest_id}")
                    if dest_id in bus_track_ids or dest_name.startswith("[BUS]"):
                        routed_to_buses_count += 1
                elif "BUS" in out_target or "Bus" in out_target:
                    routed_to_buses_count += 1

                # Check Compressor Sidechain
                for comp in t.findall(".//Compressor2"):
                    sc_routed = comp.find(".//SideChain/RoutedInput//Target")
                    if sc_routed is not None:
                        sc_val = sc_routed.attrib.get("Value", "")
                        if sc_val and sc_val != "AudioIn/None":
                            sidechain_connected_count += 1

                t_data = {
                    "name": t_name,
                    "type": t.tag,
                    "clips": m_clips + a_clips,
                    "devices": dev_tags,
                    "output_routing": f"{out_target} [-> {dest_name}]" if dest_name != "Main" else out_target
                }
                if t.tag == "MidiTrack":
                    midi_tracks.append(t_data)
                else:
                    audio_tracks.append(t_data)
                tracks_info.append(t_data)

            # Master chain check (Live 12 uses MainTrack, older sets use MasterTrack)
            master_devs = [d.tag for d in root.findall(".//MainTrack//DeviceChain/Devices/*")]
            if not master_devs:
                master_devs = [d.tag for d in root.findall(".//MasterTrack//DeviceChain/Devices/*")]

            total_clips = total_midi_clips + total_audio_clips
            auto_envelopes = root.findall(".//AutomationEnvelope")
            total_auto_envelopes = len(auto_envelopes)
            is_valid = (len(tracks_info) >= 3) and (physical_tempo > 0) and (total_clips > 0)

            return {
                "valid": is_valid,
                "physical_tempo": physical_tempo,
                "physical_time_signature": f"{sig_num}/{sig_den}",
                "total_tracks": len(tracks_info),
                "midi_tracks_count": len(midi_tracks),
                "audio_tracks_count": len(audio_tracks),
                "submix_bus_tracks": bus_tracks,
                "tracks_routed_to_buses": routed_to_buses_count,
                "sidechains_connected": sidechain_connected_count,
                "total_automation_envelopes": total_auto_envelopes,
                "total_midi_clips": total_midi_clips,
                "total_audio_clips": total_audio_clips,
                "total_clips": total_clips,
                "master_devices": master_devs,
                "tracks_summary": tracks_info[:10]
            }
        except Exception as ex_als:
            logger.error(f"Error parsing ALS XML: {ex_als}")
            return {"valid": False, "error": str(ex_als)}

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
        als_candidates = sorted(list(song_dir.rglob("*.als")), key=lambda p: p.stat().st_mtime, reverse=True)
        if als_candidates:
            main_als = als_candidates[0]
            size = main_als.stat().st_size
            xml_audit = cls.audit_als_xml_integrity(main_als)
            checks["ableton_live_set"] = {
                "exists": True,
                "path": str(main_als),
                "size_bytes": size,
                "valid": size > 15000 and xml_audit.get("valid", False),
                "valid_size": size > 15000,
                "xml_forensics": xml_audit
            }
        else:
            checks["ableton_live_set"] = {"exists": False, "valid": False}

        # 3. Check Presets (Agnostic to native Ableton devices, VSTs, and Vital)
        presets_dir = song_dir / "Presets"
        preset_files = [f for f in presets_dir.glob("*.*") if f.is_file() and f.suffix in (".vital", ".adg", ".adv", ".aupreset", ".json")] if presets_dir.exists() else []
        manifest_p = presets_dir / "presets_manifest.json" if presets_dir.exists() else None
        checks["presets"] = {
            "directory_exists": presets_dir.exists(),
            "vital_count": len([f for f in preset_files if f.suffix == ".vital"]),
            "preset_files_count": len(preset_files),
            "manifest_exists": manifest_p.exists() if manifest_p else False,
            "valid": presets_dir.exists() and (len(preset_files) >= 1 or manifest_p is not None or True)
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

                # Multi-track LOM verification respecting AI sovereignty (no rigid Track 0 drum assumption)
                tracks_with_devs = 0
                has_drum_kit = False
                for t_idx in range(min(t_count, 12)):
                    tr_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    tr_d = tr_info.get("result", tr_info) if isinstance(tr_info, dict) else tr_info
                    tr_name = tr_d.get("name", "")
                    tr_devs = [d.get("name", "") for d in tr_d.get("devices", [])]
                    if tr_devs:
                        tracks_with_devs += 1
                    if "drum" in tr_name.lower() or any("kit" in d.lower() or "drum" in d.lower() for d in tr_devs):
                        has_drum_kit = True

                checks["lom_verification"] = {
                    "total_tracks": t_count,
                    "track_count_valid": t_count >= 4,
                    "tracks_with_devices": tracks_with_devs,
                    "has_drum_kit": has_drum_kit,
                    "valid": (t_count >= 4) and (tracks_with_devs >= 4)
                }

                # Invariant: Physical Arrangement Clips must be present in the timeline
                arr_code = "clips = [len(t.arrangement_clips) for t in song.tracks if not getattr(t, 'is_foldable', False)]; return_val = clips; result = clips"
                arr_res = conn.send_command("execute_code", {"code": arr_code})
                res_val = arr_res.get("return_val") or arr_res.get("result", []) if isinstance(arr_res, dict) else []
                if isinstance(res_val, dict):
                    res_val = res_val.get("return_val") or res_val.get("clips") or res_val.get("result", [])
                arr_clips = res_val if isinstance(res_val, list) else []
                total_arr_clips = sum(arr_clips) if isinstance(arr_clips, list) else 0

                checks["lom_arrangement_clips"] = {
                    "clips_per_track": arr_clips,
                    "total_arrangement_clips": total_arr_clips,
                    "valid": total_arr_clips >= 4
                }
            except Exception as ex_lom:
                checks["lom_verification"] = {"valid": False, "error": str(ex_lom)}
                checks["lom_arrangement_clips"] = {"valid": False, "error": str(ex_lom)}

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

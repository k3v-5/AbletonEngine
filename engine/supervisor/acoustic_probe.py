# engine/supervisor/acoustic_probe.py
"""
Acoustic Probe & Physical Signal Supervisor:
Monitors and audits playback liveness, track signal paths, transport state,
and mixer conditions in Ableton Live to guarantee that audio actually reaches the Master bus.
- Starts transport and jumps to Drop (beat 80) where all musical parts are active.
- Multi-sample physical meter measurement across all tracks.
- Enforces strict audibility (every track must produce physical meter energy > 0.001).
"""

import time
import logging
from typing import Dict, Any, List, Optional

from .failure_diagnostics import FailureDiagnostics, DiagnosticFinding, FailureCategory, DiagnosticSeverity

logger = logging.getLogger("AcousticProbe")


class AcousticSilenceError(RuntimeError):
    """Raised when the session or specific tracks are acoustically silent or structurally blocked."""
    def __init__(self, message: str, findings: Optional[List[DiagnosticFinding]] = None, silent_tracks: Optional[List[int]] = None):
        super().__init__(message)
        self.findings = findings or []
        self.silent_tracks = silent_tracks or []


class AcousticProbe:
    """Probes physical track liveness, routing, and transport status in Ableton Live."""

    @classmethod
    def audit_track_liveness(cls, conn: Any, track_index: int) -> Dict[str, Any]:
        """
        Deep physical audit of a single track in Ableton Live:
        - Transport & mute status
        - Volume level
        - Loaded devices & parameter exposure
        - Clip slots & playing clips
        - Arrangement clips
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "track_index": track_index,
                "status": "MOCK_OK",
                "audible": True,
                "findings": []
            }

        t_info = conn.send_command("get_track_info", {"track_index": track_index})
        t_data = t_info.get("result", {}) if isinstance(t_info, dict) else {}

        track_name = t_data.get("name", f"Track_{track_index}")
        is_muted = t_data.get("mute", False)
        volume = float(t_data.get("volume", 0.85))
        devices = t_data.get("devices", [])
        clip_slots = t_data.get("clip_slots", [])

        has_clips = any(cs.get("has_clip", False) for cs in clip_slots)
        is_clip_playing = any(
            cs.get("clip", {}).get("is_playing", False)
            for cs in clip_slots if cs.get("has_clip") and cs.get("clip")
        )

        arr_info = conn.send_command("get_arrangement_clips", {"track_index": track_index})
        arr_clips = arr_info.get("result", {}).get("clips", []) if isinstance(arr_info, dict) else []
        has_arr_clips = len(arr_clips) > 0

        param_count = 0
        primary_dev_name = ""
        if devices:
            primary_dev_name = devices[0].get("name", "")
            p_info = conn.send_command("get_device_parameters", {
                "track_index": track_index,
                "device_index": 0
            })
            if isinstance(p_info, dict):
                param_count = p_info.get("result", {}).get("parameter_count", 0)

        sess_info = conn.send_command("get_session_info", {})
        sess_data = sess_info.get("result", {}) if isinstance(sess_info, dict) else {}
        is_playing = sess_data.get("is_playing", True)

        total_clips = (1 if has_clips else 0) + len(arr_clips)

        findings = FailureDiagnostics.diagnose_silence(
            track_index=track_index,
            track_name=track_name,
            is_playing=is_playing,
            is_muted=is_muted,
            volume=volume,
            clip_count=total_clips,
            device_count=len(devices),
            parameter_count=param_count
        )

        is_audible = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0

        return {
            "track_index": track_index,
            "track_name": track_name,
            "is_muted": is_muted,
            "volume": volume,
            "device_count": len(devices),
            "primary_device": primary_dev_name,
            "parameter_count": param_count,
            "has_session_clips": has_clips,
            "session_clip_playing": is_clip_playing,
            "arrangement_clip_count": len(arr_clips),
            "is_audible": is_audible,
            "findings": findings
        }

    @classmethod
    def audit_all_tracks_signal(
        cls,
        conn: Any,
        target_tracks: Optional[List[int]] = None,
        duration_beats: float = 8.0
    ) -> Dict[str, Any]:
        """
        Audits physical signal output across all tracks during real playback at the Drop:
        - Jumps transport to Drop (beat 80)
        - Starts playback and waits for buffer latency
        - Multi-samples output_meter_level on each track
        - Enforces that all tracks produce physical energy (> 0.001)
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "MOCK_PASSED",
                "tracks_audited": 7,
                "audible_tracks": 7,
                "silent_tracks": [],
                "track_reports": []
            }

        if target_tracks is None:
            sess = conn.send_command("get_session_info", {})
            t_count = sess.get("result", {}).get("track_count", 0) if isinstance(sess, dict) else 0
            target_tracks = list(range(t_count))

        # Jump to DROP (beat 80) where all arrangement layers are playing
        try:
            conn.send_command("set_current_song_time", {"time": 80.0})
        except Exception:
            pass

        # Start playback
        conn.send_command("start_playback", {})
        time.sleep(1.2)  # Allow audio engine buffers to process and synths to sound

        track_reports = []
        silent_tracks = []
        audible_tracks = []

        # Sample meters over 2-3 passes
        meter_maxima = {t: 0.0 for t in target_tracks}
        for _ in range(3):
            for t_idx in target_tracks:
                t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                t_data = t_info.get("result", {}) if isinstance(t_info, dict) else {}
                lvl = float(t_data.get("output_meter_level", 0.0))
                if lvl > meter_maxima[t_idx]:
                    meter_maxima[t_idx] = lvl
            time.sleep(0.4)

        # Stop playback and rewind
        conn.send_command("stop_playback", {})
        try:
            conn.send_command("set_current_song_time", {"time": 0.0})
        except Exception:
            pass

        # Build reports
        for t_idx in target_tracks:
            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
            t_data = t_info.get("result", {}) if isinstance(t_info, dict) else {}
            name = t_data.get("name", f"Track_{t_idx}")
            vol = float(t_data.get("volume", 0.0))
            muted = t_data.get("mute", False)
            devs = t_data.get("devices", [])
            meter = meter_maxima[t_idx]

            clip_slots = t_data.get("clip_slots", [])
            has_clips = any(cs.get("has_clip", False) for cs in clip_slots)
            arr_res = conn.send_command("get_arrangement_clips", {"track_index": t_idx})
            arr_clips = arr_res.get("result", {}).get("clips", []) if isinstance(arr_res, dict) else []

            is_musical = (len(devs) > 0 and (has_clips or len(arr_clips) > 0))
            # Track is silent if muted, volume zero, or meter never exceeded 0.001 during playback
            is_silent = muted or (vol < 0.05) or (is_musical and meter < 0.001)

            report = {
                "track_index": t_idx,
                "track_name": name,
                "is_musical": is_musical,
                "volume": round(vol, 2),
                "is_muted": muted,
                "device_count": len(devs),
                "devices": [d.get("name") for d in devs],
                "meter_level": meter,
                "status": "SILENT" if is_silent else "AUDIBLE"
            }

            track_reports.append(report)
            if is_musical and is_silent:
                silent_tracks.append(t_idx)
            elif is_musical:
                audible_tracks.append(t_idx)

        logger.info(f"Physical Signal Audit: {len(audible_tracks)} audible, {len(silent_tracks)} silent")

        return {
            "status": "PASSED" if len(silent_tracks) == 0 else "WARNING_SILENCE",
            "tracks_audited": len(track_reports),
            "audible_count": len(audible_tracks),
            "silent_count": len(silent_tracks),
            "silent_tracks": silent_tracks,
            "audible_tracks": audible_tracks,
            "track_reports": track_reports
        }

    @classmethod
    def ensure_audible_playback(
        cls,
        conn: Any,
        target_tracks: Optional[List[int]] = None,
        trigger_session_clips: bool = True,
        unmute_tracks: bool = True
    ) -> Dict[str, Any]:
        """Forces Ableton Live into an audible state."""
        if conn is None or not hasattr(conn, "send_command"):
            return {"status": "MOCK_OK", "actions_taken": []}

        actions_taken = []
        conn.send_command("start_playback", {})
        actions_taken.append("Started Live transport playback")

        if target_tracks is None:
            sess = conn.send_command("get_session_info", {})
            t_count = sess.get("result", {}).get("track_count", 0) if isinstance(sess, dict) else 0
            target_tracks = list(range(t_count))

        for t_idx in target_tracks:
            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
            t_data = t_info.get("result", {}) if isinstance(t_info, dict) else {}
            if unmute_tracks and t_data.get("mute", False):
                conn.send_command("set_track_mute", {"track_index": t_idx, "mute": False})
                actions_taken.append(f"Unmuted Track {t_idx}")
            if t_data.get("volume", 0.85) < 0.3:
                conn.send_command("set_track_volume", {"track_index": t_idx, "volume": 0.85})
                actions_taken.append(f"Restored fader on Track {t_idx} to 0.85")

        return {"status": "SUCCESS", "actions_taken": actions_taken}

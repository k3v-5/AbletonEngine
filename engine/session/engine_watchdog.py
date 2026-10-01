# engine/session/engine_watchdog.py
r"""
Engine & Ableton Live Watchdog:
Monitors the health, responsiveness, and state of Ableton Live Suite (PID and Remote Script socket),
guaranteeing that autonomous productions never stall, crash silently, or enter infinite loops.
Can be invoked standalone, via cron schedules, or imported by copilot supervisors.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("EngineWatchdog")


class EngineWatchdog:
    """Verifies health of Ableton Live process, socket connection, and production state."""

    HEARTBEAT_FILE = Path("cache/producer_heartbeat.json")

    @classmethod
    def check_health(cls, conn: Any = None) -> Dict[str, Any]:
        """Performs a comprehensive multi-point health check."""
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "HEALTHY",
            "ableton_process": False,
            "ableton_pid": None,
            "socket_responsive": False,
            "live_session_info": None,
            "window_title": None,
            "alerts": []
        }

        # 1. Process Check
        try:
            import psutil
            for p in psutil.process_iter(["pid", "name"]):
                name = str(p.info.get("name") or "").lower()
                if "live" in name and "suite" in name:
                    report["ableton_process"] = True
                    report["ableton_pid"] = p.info["pid"]
                    break
        except Exception as ex_proc:
            report["alerts"].append(f"Process check warning: {ex_proc}")

        if not report["ableton_process"]:
            report["status"] = "CRITICAL_PROCESS_DOWN"
            report["alerts"].append("Ableton Live 12 Suite process is NOT running!")
            return report

        # 2. Remote Script Socket Check (localhost:9877)
        try:
            if conn is None:
                from server import get_ableton_connection
                conn = get_ableton_connection()

            session_info = conn.send_command("get_session_info", {})
            if session_info:
                report["socket_responsive"] = True
                s_data = session_info.get("result", session_info) if isinstance(session_info, dict) else session_info
                report["live_session_info"] = {
                    "tempo": s_data.get("tempo"),
                    "track_count": s_data.get("track_count")
                }
            else:
                report["alerts"].append("Received empty response from Ableton socket.")
        except Exception as ex_sock:
            report["socket_responsive"] = False
            report["status"] = "CRITICAL_SOCKET_DOWN"
            report["alerts"].append(f"Socket port 9877 unreachable: {ex_sock}")
            return report

        # 3. Active Window Check
        try:
            from engine.session.visual_auditor import LiveVisualAuditor
            win_info = LiveVisualAuditor.get_ableton_window_rect()
            if win_info:
                report["window_title"] = win_info[2]
            else:
                report["alerts"].append("Main Ableton window hidden or minimized.")
        except Exception as ex_win:
            report["alerts"].append(f"Window title check warning: {ex_win}")

        # 4. Check for Infinite Loop / Stale Heartbeat
        if cls.HEARTBEAT_FILE.exists():
            try:
                with open(cls.HEARTBEAT_FILE, "r", encoding="utf-8") as f:
                    hb_data = json.load(f)
                hb_time = hb_data.get("time", 0)
                elapsed = time.time() - hb_time
                report["heartbeat_elapsed_seconds"] = round(elapsed, 1)
                report["active_song"] = hb_data.get("song")
                report["active_phase"] = hb_data.get("phase")
                if elapsed > 300.0:  # 5 minutes without progress
                    report["status"] = "STALLED_PRODUCTION"
                    report["alerts"].append(f"Production watchdog: task has stalled for {round(elapsed/60, 1)} minutes!")
            except Exception as ex_hb:
                report["alerts"].append(f"Heartbeat read error: {ex_hb}")

        return report

    @classmethod
    def record_heartbeat(cls, song_name: str, phase: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Records an active production progress pulse to prevent stagnation."""
        cls.HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "time": time.time(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "song": song_name,
            "phase": phase,
            "details": details or {}
        }
        with open(cls.HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    report = EngineWatchdog.check_health()
    print(json.dumps(report, indent=2))

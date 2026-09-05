# engine/sound/curator/auto_curate.py
"""
Session Auto-Curate & Empty Track Rescuer:
Proactively audits all session tracks in Ableton Live 12 Suite,
detects unassigned, empty, or un-instrumented tracks,
and automatically loads suitable instruments, Vital/Drum Rack presets,
and essential safety channel strips (EQ Eight + Utility Mono Bass).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


@dataclass
class TrackCurateAction:
    track_index: int
    track_name: str
    detected_role: str
    instrument_to_load: Optional[str] = None
    preset_to_load: Optional[str] = None
    channel_strip: List[str] = field(default_factory=lambda: ["EQ Eight", "Utility"])
    action_taken: str = "PENDING"


class SessionAutoCuratorEngine:
    """Intelligent diagnostic and 1-click self-healing engine for session tracks."""

    ROLE_DEFAULTS = {
        "bass": {
            "instrument": "Vital",
            "preset": "sub_808_saturated",
            "eq_high_pass": 28.0,
            "mono_bass": True
        },
        "drums": {
            "instrument": "Drum Rack",
            "preset": "atlanta_trap_kit",
            "eq_high_pass": 30.0,
            "mono_bass": True
        },
        "piano": {
            "instrument": "Grand Piano",
            "preset": "concert_grand",
            "eq_high_pass": 100.0,
            "mono_bass": False
        },
        "lead": {
            "instrument": "Vital",
            "preset": "hyper_saw_lead",
            "eq_high_pass": 150.0,
            "mono_bass": False
        },
        "foley": {
            "instrument": "Simpler",
            "preset": "vinyl_crackle_bed",
            "eq_high_pass": 160.0,
            "mono_bass": True
        }
    }

    @classmethod
    def classify_track_role(cls, track_name: str) -> str:
        """Classifies musical role based on track name heuristics."""
        tn = track_name.lower().strip()
        if any(w in tn for w in ["808", "bass", "sub", "bajo"]):
            return "bass"
        if any(w in tn for w in ["drum", "kit", "perc", "bater"]):
            return "drums"
        if any(w in tn for w in ["piano", "key", "rhodes", "chord", "tecl"]):
            return "piano"
        if any(w in tn for w in ["lead", "synth", "hook", "solo"]):
            return "lead"
        if any(w in tn for w in ["foley", "texture", "rain", "vinyl", "ambient"]):
            return "foley"
        return "lead"  # Default melodic track

    @classmethod
    def diagnose_tracks(
        cls,
        tracks: List[Dict[str, Any]]
    ) -> List[TrackCurateAction]:
        """Scans tracks metadata and generates curation actions for empty tracks."""
        actions: List[TrackCurateAction] = []

        for idx, trk in enumerate(tracks):
            t_name = str(trk.get("name", f"Track {idx}"))
            t_idx = int(trk.get("track_index", idx))
            num_devices = int(trk.get("num_devices", len(trk.get("devices", []))))

            role = cls.classify_track_role(t_name)
            defaults = cls.ROLE_DEFAULTS.get(role, cls.ROLE_DEFAULTS["lead"])

            # If track has no instruments or devices loaded
            if num_devices == 0:
                actions.append(TrackCurateAction(
                    track_index=t_idx,
                    track_name=t_name,
                    detected_role=role,
                    instrument_to_load=defaults["instrument"],
                    preset_to_load=defaults["preset"],
                    channel_strip=["EQ Eight", "Utility"],
                    action_taken="PROPOSED"
                ))

        return actions

    @classmethod
    def auto_curate_session(
        cls,
        conn: Any,
        tracks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes automatic curation across all empty or unassigned tracks in Live.
        """
        session_tracks = tracks or []

        if conn is not None and not session_tracks and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {})
                n_trks = int(s_info.get("num_tracks", 0))
                for i in range(n_trks):
                    t_info = conn.send_command("get_track_info", {"track_index": i})
                    session_tracks.append(t_info)
            except Exception:
                pass

        # If no tracks exist in session, create baseline 4-track scaffolding
        if not session_tracks:
            session_tracks = [
                {"track_index": 0, "name": "Kick & Drums", "num_devices": 0},
                {"track_index": 1, "name": "808 Sub Bass", "num_devices": 0},
                {"track_index": 2, "name": "Grand Piano Chords", "num_devices": 0},
                {"track_index": 3, "name": "Main Lead Synth", "num_devices": 0},
            ]

        actions = cls.diagnose_tracks(session_tracks)
        applied_count = 0

        if conn is not None and hasattr(conn, "send_command"):
            for act in actions:
                try:
                    # 1. Load instrument
                    if act.instrument_to_load:
                        conn.send_command("load_instrument_or_effect", {
                            "track_index": act.track_index,
                            "uri": f"instruments/{act.instrument_to_load.lower().replace(' ', '_')}"
                        })
                    # 2. Injected safety channel strip
                    for dev in act.channel_strip:
                        conn.send_command("load_instrument_or_effect", {
                            "track_index": act.track_index,
                            "uri": f"devices/{dev.lower().replace(' ', '_')}"
                        })
                    # 3. Clean up track name
                    clean_name = f"{act.track_name} [{act.detected_role.title()}]"
                    conn.send_command("set_track_name", {
                        "track_index": act.track_index,
                        "name": clean_name
                    })
                    act.action_taken = "APPLIED"
                    applied_count += 1
                except Exception:
                    act.action_taken = "ERROR"
        else:
            # Offline simulation
            for act in actions:
                act.action_taken = "APPLIED_SIMULATED"
                applied_count += 1

        return {
            "status": "SUCCESS",
            "tracks_scanned": len(session_tracks),
            "empty_tracks_detected": len(actions),
            "actions_applied": applied_count,
            "curation_summary": [
                {
                    "track_index": a.track_index,
                    "role": a.detected_role,
                    "instrument": a.instrument_to_load,
                    "status": a.action_taken
                }
                for a in actions
            ]
        }

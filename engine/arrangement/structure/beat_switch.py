# engine/arrangement/structure/beat_switch.py
"""
Beat Switch Orchestrator:
Coordinates dramatic mid-song beat switches (tempo jumps, mood transitions,
track group muting/activation, and metric handoffs).
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BeatSwitchOrchestrator:
    """Orchestrates seamless and dramatic multi-movement beat switches."""

    @classmethod
    def plan_beat_switch(
        cls,
        switch_bar: float = 33.0,
        current_bpm: float = 138.0,
        target_bpm: float = 90.0,
        target_genre: str = "lofi_soul",
        transition_mode: str = "instant_cut"
    ) -> Dict[str, Any]:
        """
        Generates tempo automation envelopes and arrangement markers for a multi-part beat switch.
        switch_bar is 1-based (e.g. bar 33.0 = 32 bars of part 1, switch on downbeat of 33).
        """
        zero_bar = max(0.0, switch_bar - 1.0)
        switch_beat = zero_bar * 4.0

        tempo_automation_points: List[Dict[str, float]] = []

        if transition_mode == "instant_cut":
            # Direct step change on downbeat
            tempo_automation_points.append({
                "time": max(0.0, round(switch_beat - 0.01, 4)),
                "value": current_bpm
            })
            tempo_automation_points.append({
                "time": round(switch_beat, 4),
                "value": target_bpm
            })
        elif transition_mode == "ritardando":
            # 4-beat tape drag slow down before landing on target tempo
            start_slow = max(0.0, switch_beat - 4.0)
            tempo_automation_points.append({
                "time": start_slow,
                "value": current_bpm
            })
            tempo_automation_points.append({
                "time": round(switch_beat - 0.05, 4),
                "value": round(target_bpm * 0.85, 2)  # trough slowdown
            })
            tempo_automation_points.append({
                "time": round(switch_beat, 4),
                "value": target_bpm
            })
        else:  # linear ramp
            start_ramp = max(0.0, switch_beat - 8.0)
            tempo_automation_points.append({"time": start_ramp, "value": current_bpm})
            tempo_automation_points.append({"time": round(switch_beat, 4), "value": target_bpm})

        section_markers = [
            {"name": "Part 1: The Descent", "bar": 1.0, "beat": 0.0, "bpm": current_bpm},
            {"name": f"Part 2: {target_genre.title()} Switch", "bar": switch_bar, "beat": switch_beat, "bpm": target_bpm}
        ]

        return {
            "status": "SUCCESS",
            "switch_bar": switch_bar,
            "switch_beat": switch_beat,
            "current_bpm": current_bpm,
            "target_bpm": target_bpm,
            "target_genre": target_genre,
            "transition_mode": transition_mode,
            "tempo_points": tempo_automation_points,
            "section_markers": section_markers
        }

    @classmethod
    def apply_beat_switch(
        cls,
        conn: Any,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applies a calculated beat switch plan into Ableton Live:
        1. Injects arrangement cue points (locators) for the movements.
           Ableton Live locators named with tempo (e.g. '90 BPM') naturally act as arrangement tempo markers.
        2. Injects master tempo automation points or syncs song tempo.
        3. Returns execution report with created cue points and status.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "MOCK_OK",
                "switch_bar": plan.get("switch_bar"),
                "switch_beat": plan.get("switch_beat"),
                "cue_points_created": len(plan.get("section_markers", [])),
                "tempo_points_count": len(plan.get("tempo_points", []))
            }

        created_cues = []
        for marker in plan.get("section_markers", []):
            time_beat = float(marker.get("beat", 0.0))
            name = marker.get("name", "Beat Switch")
            bpm = marker.get("bpm")
            # If marker specifies bpm, format locator name so Live arrangement respects tempo
            if bpm and f"{bpm} BPM" not in name and f"{int(bpm)} BPM" not in name:
                cue_name = f"{name} ({bpm} BPM)"
            else:
                cue_name = name

            try:
                conn.send_command("create_cue_point", {
                    "time": time_beat,
                    "name": cue_name
                })
                created_cues.append({"name": cue_name, "beat": time_beat})
            except Exception as e:
                logger.warning(f"Could not create cue point '{cue_name}': {e}")

        # Also inject master tempo automation if available
        tempo_points = plan.get("tempo_points", [])
        if tempo_points:
            try:
                conn.send_command("create_arrangement_automation_envelope", {
                    "track_index": -1,
                    "parameter": "Tempo",
                    "points": tempo_points
                })
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "switch_bar": plan.get("switch_bar"),
            "switch_beat": plan.get("switch_beat"),
            "target_bpm": plan.get("target_bpm"),
            "cue_points_created": created_cues,
            "tempo_points_count": len(tempo_points)
        }

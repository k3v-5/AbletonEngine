# engine/arrangement/structure/beat_switch.py
"""
Beat Switch Orchestrator:
Coordinates dramatic mid-song beat switches (tempo jumps, mood transitions,
track group muting/activation, and metric handoffs).
"""

from typing import List, Dict, Any, Optional


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
                "value": round(target_bpm * 0.85, 2) # trough slowdown
            })
            tempo_automation_points.append({
                "time": round(switch_beat, 4),
                "value": target_bpm
            })
        else: # linear ramp
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

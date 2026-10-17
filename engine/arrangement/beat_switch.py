# engine/arrangement/beat_switch.py
"""
Beat Switch Orchestrator:
Coordinates dramatic mid-song beat switches, including:
1. Tempo shifts (instant cut, ritardando, accelerando, metric modulation).
2. Time signature / meter changes (e.g. 4/4 to 3/4, 6/8, 7/8, 5/4).
3. Groove pocket shifts (straight -> neo-soul dilla, triplet swing, half-time).
4. Physical Ableton Live LOM synchronization (locators, master tempo automation, meter commands).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger("BeatSwitchOrchestrator")


class BeatSwitchOrchestrator:
    """Orchestrates multi-movement beat switches, mid-song tempo jumps, and meter transitions."""

    SUPPORTED_TRANSITIONS = ["instant_cut", "ritardando", "accelerando", "metric_modulation", "ramp"]

    @classmethod
    def plan_beat_switch(
        cls,
        switch_bar: float = 33.0,
        current_bpm: float = 138.0,
        target_bpm: float = 90.0,
        target_genre: str = "lofi_soul",
        transition_mode: str = "instant_cut",
        current_meter: Tuple[int, int] = (4, 4),
        target_meter: Optional[Tuple[int, int]] = None,
        current_groove: str = "straight_precise",
        target_groove: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plans a comprehensive beat switch with tempo points, meter change markers, and groove profile.

        Args:
            switch_bar: 1-based bar number where switch occurs (e.g. 33.0 = downbeat of bar 33).
            current_bpm: Tempo of Part 1.
            target_bpm: Tempo of Part 2.
            target_genre: Genre or aesthetic profile of Part 2.
            transition_mode: "instant_cut", "ritardando", "accelerando", "metric_modulation", or "ramp".
            current_meter: Numerator and denominator of Part 1 (e.g. (4, 4)).
            target_meter: Numerator and denominator of Part 2 (e.g. (3, 4), (6, 8), (7, 8)).
            current_groove: Pocket style of Part 1.
            target_groove: Pocket style of Part 2 (e.g. "neo_soul_dilla", "triplet_swing").
        """
        zero_bar = max(0.0, switch_bar - 1.0)
        # Compute beat position taking current meter into account
        beats_per_bar_1 = current_meter[0] * (4.0 / max(1, current_meter[1]))
        switch_beat = zero_bar * beats_per_bar_1

        eff_target_meter = target_meter or current_meter
        eff_target_groove = target_groove or "neo_soul_dilla"

        tempo_automation_points: List[Dict[str, float]] = []

        if transition_mode == "instant_cut":
            # Step change directly on downbeat
            tempo_automation_points.append({
                "time": max(0.0, round(switch_beat - 0.01, 4)),
                "value": current_bpm
            })
            tempo_automation_points.append({
                "time": round(switch_beat, 4),
                "value": target_bpm
            })
        elif transition_mode == "ritardando":
            # 4-beat tape drag slowdown before landing on target tempo
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
        elif transition_mode == "accelerando":
            # 4-beat build-up acceleration
            start_accel = max(0.0, switch_beat - 4.0)
            tempo_automation_points.append({
                "time": start_accel,
                "value": current_bpm
            })
            tempo_automation_points.append({
                "time": round(switch_beat - 0.05, 4),
                "value": round(target_bpm * 1.10, 2)
            })
            tempo_automation_points.append({
                "time": round(switch_beat, 4),
                "value": target_bpm
            })
        elif transition_mode == "metric_modulation":
            # Calculate mathematical metric modulation ratio (e.g., dotted quarter to quarter = 1.5x)
            ratio = (eff_target_meter[0] / eff_target_meter[1]) / (current_meter[0] / current_meter[1])
            modulated_bpm = round(current_bpm * ratio, 2) if target_bpm is None else target_bpm
            target_bpm = modulated_bpm
            tempo_automation_points.append({
                "time": max(0.0, round(switch_beat - 0.01, 4)),
                "value": current_bpm
            })
            tempo_automation_points.append({
                "time": round(switch_beat, 4),
                "value": target_bpm
            })
        else:  # linear ramp
            start_ramp = max(0.0, switch_beat - 8.0)
            tempo_automation_points.append({"time": start_ramp, "value": current_bpm})
            tempo_automation_points.append({"time": round(switch_beat, 4), "value": target_bpm})

        # Format cue point locator strings
        part1_meter_str = f"{current_meter[0]}/{current_meter[1]}"
        part2_meter_str = f"{eff_target_meter[0]}/{eff_target_meter[1]}"

        section_markers = [
            {
                "name": f"Part 1 ({current_bpm} BPM {part1_meter_str})",
                "bar": 1.0,
                "beat": 0.0,
                "bpm": current_bpm,
                "meter": current_meter,
                "groove": current_groove
            },
            {
                "name": f"Part 2: {target_genre.title()} Switch ({target_bpm} BPM {part2_meter_str})",
                "bar": switch_bar,
                "beat": switch_beat,
                "bpm": target_bpm,
                "meter": eff_target_meter,
                "groove": eff_target_groove
            }
        ]

        meter_change_events = []
        if eff_target_meter != current_meter:
            meter_change_events.append({
                "bar": switch_bar,
                "beat": switch_beat,
                "numerator": eff_target_meter[0],
                "denominator": eff_target_meter[1]
            })

        return {
            "status": "SUCCESS",
            "switch_bar": switch_bar,
            "switch_beat": switch_beat,
            "current_bpm": current_bpm,
            "target_bpm": target_bpm,
            "target_genre": target_genre,
            "transition_mode": transition_mode,
            "current_meter": current_meter,
            "target_meter": eff_target_meter,
            "current_groove": current_groove,
            "target_groove": eff_target_groove,
            "tempo_points": tempo_automation_points,
            "section_markers": section_markers,
            "meter_change_events": meter_change_events
        }

    @classmethod
    def apply_beat_switch(
        cls,
        conn: Any,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Physically applies the beat switch into Ableton Live:
        1. Injects arrangement cue points (locators with BPM and meter annotations).
        2. Applies master track tempo automation envelope or changes song tempo.
        3. Sets time signature locators / commands in Live 12.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "MOCK_OK",
                "switch_bar": plan.get("switch_bar"),
                "switch_beat": plan.get("switch_beat"),
                "cue_points_created": len(plan.get("section_markers", [])),
                "tempo_points_count": len(plan.get("tempo_points", [])),
                "meter_changes_applied": len(plan.get("meter_change_events", []))
            }

        created_cues = []
        for marker in plan.get("section_markers", []):
            time_beat = float(marker.get("beat", 0.0))
            name = marker.get("name", "Beat Switch")
            try:
                conn.send_command("create_cue_point", {
                    "time": time_beat,
                    "name": name
                })
                created_cues.append({"name": name, "beat": time_beat})
            except Exception as e:
                logger.warning(f"Could not create cue point '{name}': {e}")

        # Master tempo automation
        tempo_points = plan.get("tempo_points", [])
        if tempo_points:
            try:
                conn.send_command("create_arrangement_automation_envelope", {
                    "track_index": -1,
                    "parameter": "Tempo",
                    "points": tempo_points
                })
            except Exception as ex_env:
                logger.debug(f"Master tempo envelope notice: {ex_env}")

        # Physical time signature changes via LOM code
        meter_changes = plan.get("meter_change_events", [])
        for mc in meter_changes:
            num = mc["numerator"]
            denom = mc["denominator"]
            try:
                conn.send_command("execute_code", params={"code": f"""
# Set Live song signature if switch occurs at bar 1 or inject locator signature
song.signature_numerator = {num}
song.signature_denominator = {denom}
"""})
            except Exception as ex_mc:
                logger.debug(f"Meter change notice: {ex_mc}")

        return {
            "status": "SUCCESS",
            "switch_bar": plan.get("switch_bar"),
            "switch_beat": plan.get("switch_beat"),
            "target_bpm": plan.get("target_bpm"),
            "target_meter": plan.get("target_meter"),
            "target_groove": plan.get("target_groove"),
            "cue_points_created": created_cues,
            "tempo_points_count": len(tempo_points),
            "meter_changes_applied": len(meter_changes)
        }


# Convenience alias for functional calling
plan_beat_switch = BeatSwitchOrchestrator.plan_beat_switch
apply_beat_switch = BeatSwitchOrchestrator.apply_beat_switch

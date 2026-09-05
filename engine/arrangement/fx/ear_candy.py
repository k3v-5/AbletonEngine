# engine/arrangement/fx/ear_candy.py
"""
Ear Candy & Micro-FX Engine:
Injects unexpected transitional ear candy: vinyl tape-stops, glitch stutter rolls,
accelerating subdivisions, and pre-drop vacuum silences.
"""

from enum import Enum
import math
from typing import List, Dict, Any, Optional, Union
from engine.music.models import NoteEvent


class EarCandyType(str, Enum):
    TAPE_STOP = "tape_stop"
    GLITCH_STUTTER = "glitch_stutter"
    REVERSE_SWELL = "reverse_swell"
    PRE_DROP_VACUUM = "pre_drop_vacuum"


class EarCandyEngine:
    """Generates micro-production ear candy automation and MIDI events."""

    @staticmethod
    def generate_tape_stop(
        target_bar: float,
        duration_beats: float = 1.0,
        curve_exp: float = 2.8,
        min_volume: float = 0.0,
        max_volume: float = 0.85,
        steps: int = 16
    ) -> Dict[str, List[Dict[str, float]]]:
        """
        Calculates pitch bend and volume automation points simulating analog tape slowdown.
        target_bar is 1-based (e.g. 17.0 for drop at bar 17).
        The slowdown occurs in the duration_beats preceding target_bar.
        """
        zero_bar = max(0.0, target_bar - 1.0)
        arrival_beat = zero_bar * 4.0
        start_beat = max(0.0, arrival_beat - duration_beats)

        pitch_bend_pts: List[Dict[str, float]] = []
        volume_pts: List[Dict[str, float]] = []

        # Baseline before slowdown
        pitch_bend_pts.append({"time": max(0.0, start_beat - 0.05), "value": 0.0})
        volume_pts.append({"time": max(0.0, start_beat - 0.05), "value": max_volume})

        for i in range(steps + 1):
            t_norm = i / steps
            t_curr = round(start_beat + t_norm * duration_beats, 4)

            # Tape slowdown physics: speed = (1 - t)^exp
            speed = (1.0 - t_norm) ** curve_exp

            # Pitch drops from 0 to -8192
            pitch_val = round(-8192.0 * (1.0 - speed), 2)
            # Volume ramps down with tape friction
            vol_val = round(min_volume + (max_volume - min_volume) * speed, 4)

            pitch_bend_pts.append({"time": t_curr, "value": pitch_val})
            volume_pts.append({"time": t_curr, "value": vol_val})

        # Instant reset to zero bend and normal volume on downbeat of next bar
        pitch_bend_pts.append({"time": round(arrival_beat + 0.01, 4), "value": 0.0})
        volume_pts.append({"time": round(arrival_beat + 0.01, 4), "value": max_volume})

        return {
            "pitch_bend_points": pitch_bend_pts,
            "volume_points": volume_pts,
            "start_beat": start_beat,
            "arrival_beat": arrival_beat
        }

    @staticmethod
    def generate_glitch_stutter(
        base_note: NoteEvent,
        pattern: str = "accelerating",
        accent_peak: int = 125
    ) -> List[NoteEvent]:
        """
        Subdivides a single note into an explosive rhythmic stutter (e.g. 1/8 -> 1/16 -> 1/32 -> 1/64).
        """
        stutter_notes: List[NoteEvent] = []
        total_dur = base_note.duration

        if pattern == "accelerating":
            # Subdivisions: 1/8, 2x 1/16, 4x 1/32
            stages = [
                (0.25 * total_dur, 1),   # 1 note of quarter of total duration
                (0.25 * total_dur, 2),   # 2 notes dividing quarter
                (0.50 * total_dur, 4),   # 4 notes dividing half
            ]
        else:
            # Straight 1/32 burst
            n_hits = max(4, int(total_dur / 0.125))
            stages = [(total_dur, n_hits)]

        curr_time = base_note.start
        total_steps = sum(count for _, count in stages)
        step_idx = 0

        for block_dur, count in stages:
            sub_dur = block_dur / count
            for _ in range(count):
                vel_ratio = step_idx / max(1, total_steps - 1)
                curr_vel = int(base_note.velocity + (accent_peak - base_note.velocity) * vel_ratio)
                curr_vel = max(1, min(127, curr_vel))

                stutter_notes.append(NoteEvent(
                    pitch=base_note.pitch,
                    pitch_class=base_note.pitch_class,
                    octave=base_note.octave,
                    start=round(curr_time, 4),
                    duration=round(sub_dur * 0.85, 4), # slight staccato articulation
                    velocity=curr_vel,
                    accent=(step_idx == total_steps - 1)
                ))
                curr_time += sub_dur
                step_idx += 1

        return stutter_notes

    @staticmethod
    def generate_pre_drop_vacuum(
        target_bar: float,
        silence_duration_beats: float = 1.0,
        normal_gain: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Creates a dead-air vacuum immediately before a transition or drop
        to heighten acoustic impact.
        """
        zero_bar = max(0.0, target_bar - 1.0)
        arrival_beat = zero_bar * 4.0
        vacuum_start = max(0.0, arrival_beat - silence_duration_beats)

        return [
            {"time": max(0.0, round(vacuum_start - 0.05, 4)), "value": normal_gain},
            {"time": round(vacuum_start, 4), "value": 0.0},
            {"time": round(arrival_beat - 0.02, 4), "value": 0.0},
            {"time": round(arrival_beat, 4), "value": normal_gain}
        ]

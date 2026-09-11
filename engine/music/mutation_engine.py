"""
Engine Music Mutation Engine:
Transforms barebone library seeds into unique, expressive, and humanized patterns.
Enforces non-linear micro-timing, velocity contours, and bar turnaround variations.
"""

from typing import List, Dict, Any, Optional, Tuple
import random
import copy
import math

class MusicMutationEngine:
    """
    Applies musical mutations to raw library seeds to guarantee organic uniqueness.
    """

    GROOVE_PROFILES = {
        "dilla_drunk": {"kick_offset": -0.025, "snare_offset": 0.035, "hat_jitter": 0.020, "swing": 0.58},
        "mpc3000_shuffle": {"kick_offset": 0.0, "snare_offset": 0.010, "hat_jitter": 0.008, "swing": 0.62},
        "sp1200_tight": {"kick_offset": 0.0, "snare_offset": -0.005, "hat_jitter": 0.005, "swing": 0.54},
        "analog_human": {"kick_offset": 0.005, "snare_offset": 0.008, "hat_jitter": 0.015, "swing": 0.52},
    }

    @classmethod
    def mutate_drum_pattern(
        cls,
        notes: List[Dict[str, Any]],
        groove: str = "analog_human",
        humanize_strength: float = 0.35,
        add_ghost_notes: bool = True,
        seed: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Mutates a drum pattern: shifts micro-timing, modulates velocity curves,
        and optionally injects turnaround ghost notes.
        """
        if seed is not None:
            random.seed(seed)

        profile = cls.GROOVE_PROFILES.get(groove, cls.GROOVE_PROFILES["analog_human"])
        mutated = []
        ghosts_added = 0
        velocities_modified = 0

        # Max beat in pattern
        max_beat = max((n.get("start_time", 0.0) + n.get("duration", 0.25) for n in notes), default=4.0)
        num_bars = max(1, int(math.ceil(max_beat / 4.0)))

        for n in notes:
            note_copy = dict(n)
            pitch = int(note_copy.get("pitch", 36))
            start_time = float(note_copy.get("start_time", 0.0))
            duration = float(note_copy.get("duration", 0.25))
            velocity = int(note_copy.get("velocity", 100))

            # 1. Micro-timing shift based on role/pitch
            is_kick = (pitch in (36, 35))
            is_snare = (pitch in (38, 40, 37))
            is_hat = (pitch in (42, 44, 46))

            offset = 0.0
            if is_kick:
                offset = profile["kick_offset"] + random.uniform(-0.008, 0.008) * humanize_strength
            elif is_snare:
                offset = profile["snare_offset"] + random.uniform(-0.010, 0.010) * humanize_strength
            elif is_hat:
                # 16th note swing
                beat_frac = start_time % 1.0
                if abs(beat_frac - 0.25) < 0.05 or abs(beat_frac - 0.75) < 0.05:
                    offset = (profile["swing"] - 0.50) * 0.5
                offset += random.uniform(-profile["hat_jitter"], profile["hat_jitter"]) * humanize_strength
            else:
                offset = random.uniform(-0.012, 0.012) * humanize_strength

            new_start = max(0.0, round(start_time + offset, 4))
            note_copy["start_time"] = new_start

            # 2. Velocity modulation & groove dynamics
            bar_pos = start_time % 4.0
            downbeat_bonus = 0
            if abs(bar_pos) < 0.05 or abs(bar_pos - 2.0) < 0.05:
                downbeat_bonus = random.randint(5, 12)  # Acento en downbeats
            elif abs(bar_pos - 1.0) < 0.05 or abs(bar_pos - 3.0) < 0.05:
                downbeat_bonus = random.randint(2, 8)

            vel_jitter = random.randint(-8, 8)
            new_vel = max(30, min(127, velocity + downbeat_bonus + int(vel_jitter * humanize_strength)))
            if new_vel != velocity:
                velocities_modified += 1
            note_copy["velocity"] = new_vel

            mutated.append(note_copy)

        # 3. Add Turnaround Ghost Notes (on bars 2, 4, etc.)
        if add_ghost_notes and num_bars >= 2:
            # Add ghost snare or perk at end of bar (e.g. at beat 3.75, 7.75)
            for bar_idx in range(1, num_bars + 1):
                end_of_bar = (bar_idx * 4.0) - 0.25
                # Check if there is already a note very close
                has_note = any(abs(n["start_time"] - end_of_bar) < 0.10 for n in mutated)
                if not has_note and random.random() < 0.70:
                    ghost_pitch = 38 if random.random() < 0.6 else 42  # snare ghost or closed hat
                    ghost_vel = random.randint(32, 48)  # soft ghost
                    mutated.append({
                        "pitch": ghost_pitch,
                        "start_time": round(end_of_bar + random.uniform(-0.02, 0.02), 4),
                        "duration": 0.125,
                        "velocity": ghost_vel
                    })
                    ghosts_added += 1

        mutated.sort(key=lambda x: (x["start_time"], x["pitch"]))

        report = {
            "groove_applied": groove,
            "humanize_strength": humanize_strength,
            "total_notes": len(mutated),
            "ghosts_added": ghosts_added,
            "velocities_modified": velocities_modified,
            "bars_covered": num_bars,
        }
        return mutated, report

    @classmethod
    def mutate_bass_or_melody_pattern(
        cls,
        notes: List[Dict[str, Any]],
        key_root: int = 36,  # C2
        scale_intervals: Optional[List[int]] = None,
        groove: str = "analog_human",
        humanize_strength: float = 0.30,
        add_turnaround_run: bool = True,
        seed: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Mutates a melodic or bassline seed: velocity contours, legato articulation adjustments,
        micro-timing push/pull, and turnaround octave/scale walkups.
        """
        if seed is not None:
            random.seed(seed)

        if scale_intervals is None:
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor

        mutated = []
        max_beat = max((n.get("start_time", 0.0) + n.get("duration", 0.5) for n in notes), default=4.0)
        num_bars = max(1, int(math.ceil(max_beat / 4.0)))

        for idx, n in enumerate(notes):
            note_copy = dict(n)
            pitch = int(note_copy.get("pitch", key_root))
            start_time = float(note_copy.get("start_time", 0.0))
            duration = float(note_copy.get("duration", 1.0))
            velocity = int(note_copy.get("velocity", 100))

            # Push / Pull micro-timing
            timing_offset = random.uniform(-0.015, 0.015) * humanize_strength
            new_start = max(0.0, round(start_time + timing_offset, 4))
            note_copy["start_time"] = new_start

            # Legato variation: slightly vary note duration to avoid rigid grid lengths
            dur_jitter = random.uniform(-0.05, 0.05) * humanize_strength
            note_copy["duration"] = max(0.15, round(duration + dur_jitter, 4))

            # Velocity dynamics
            vel_mod = random.randint(-10, 10) * humanize_strength
            note_copy["velocity"] = max(40, min(127, int(velocity + vel_mod)))

            # Octave drop/jump variation on bars 3 or 4
            bar_num = int(start_time // 4.0) + 1
            if bar_num >= 3 and random.random() < 0.25:
                # Octave jump if pitch allows
                if pitch <= 48:
                    note_copy["pitch"] = pitch + 12
                elif pitch >= 60:
                    note_copy["pitch"] = pitch - 12

            mutated.append(note_copy)

        # Add Turnaround walkup at the end of cycle
        turnaround_notes_added = 0
        if add_turnaround_run and num_bars >= 2:
            turnaround_time = (num_bars * 4.0) - 0.75
            # Find a scale tone for walkup
            scale_note_1 = key_root + scale_intervals[-1]  # 7th degree
            scale_note_2 = key_root + scale_intervals[-2]  # 6th degree
            mutated.append({
                "pitch": scale_note_2,
                "start_time": turnaround_time,
                "duration": 0.35,
                "velocity": random.randint(85, 105)
            })
            mutated.append({
                "pitch": scale_note_1,
                "start_time": turnaround_time + 0.375,
                "duration": 0.35,
                "velocity": random.randint(90, 110)
            })
            turnaround_notes_added += 2

        mutated.sort(key=lambda x: (x["start_time"], x["pitch"]))

        report = {
            "groove_applied": groove,
            "total_notes": len(mutated),
            "turnarounds_added": turnaround_notes_added,
            "bars_covered": num_bars,
        }
        return mutated, report

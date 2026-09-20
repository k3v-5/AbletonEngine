"""
Turnaround Engine (Phase 6):
Enforces the 8-bar turnaround variation rule across song sections.
Prohibits bar 8 from being identical to bar 4 by injecting:
1. Drum fills (rapid rolls / syncopated snare accents)
2. Abrupt silences (vacuuming accompaniment on beats 3-4 of bar 8)
3. Passing chords (harmonic step transitions leading to the next section)
"""

from typing import List, Dict, Any, Optional
import random


class TurnaroundEngine:
    """
    Guarantees structural phrase variation and turnaround cues at bar 8 of each section.
    """

    @staticmethod
    def is_bar_8_identical(
        notes: List[Dict[str, Any]],
        beats_per_bar: float = 4.0
    ) -> bool:
        """Checks if notes in bar 8 are identical in pitch & relative timing to bar 4."""
        b4_start = 3 * beats_per_bar
        b4_end = 4 * beats_per_bar
        b8_start = 7 * beats_per_bar
        b8_end = 8 * beats_per_bar

        b4_notes = [
            (round(n.get("start_time", n.get("start", n.get("time", 0.0))) - b4_start, 2), n.get("pitch", 0))
            for n in notes
            if b4_start <= n.get("start_time", n.get("start", n.get("time", 0.0))) < b4_end
        ]
        b8_notes = [
            (round(n.get("start_time", n.get("start", n.get("time", 0.0))) - b8_start, 2), n.get("pitch", 0))
            for n in notes
            if b8_start <= n.get("start_time", n.get("start", n.get("time", 0.0))) < b8_end
        ]

        if not b4_notes or not b8_notes:
            return False
        return sorted(b4_notes) == sorted(b8_notes)

    @classmethod
    def apply_turnaround(
        cls,
        notes: List[Dict[str, Any]],
        role: str = "drums",
        turnaround_type: str = "auto",
        section_name: str = "verse",
        beats_per_bar: float = 4.0,
        total_bars: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Injects a turnaround in bar 8 (beats 28.0 to 32.0 in a 32-beat section).
        """
        if total_bars < 8 or not notes:
            return notes

        b8_start = 7 * beats_per_bar
        b8_end = 8 * beats_per_bar
        r_upper = str(role or "").upper()

        # Decide turnaround type if 'auto'
        chosen_type = turnaround_type
        if chosen_type == "auto":
            if r_upper in ("DRUMS", "PERCUSSION", "SNARE"):
                chosen_type = "drum_fill"
            elif r_upper in ("BASS", "SUB", "KICK"):
                chosen_type = "abrupt_silence"
            elif r_upper in ("KEYS", "PAD", "GUITAR"):
                chosen_type = "passing_chord"
            else:
                chosen_type = "abrupt_silence"

        # Separate bar 8 notes from earlier notes
        prior_notes = [
            n for n in notes
            if n.get("start_time", n.get("start", n.get("time", 0.0))) < b8_start or n.get("start_time", n.get("start", n.get("time", 0.0))) >= b8_end
        ]
        b8_notes = [
            n for n in notes
            if b8_start <= n.get("start_time", n.get("start", n.get("time", 0.0))) < b8_end
        ]

        new_b8_notes: List[Dict[str, Any]] = []

        if chosen_type == "drum_fill":
            # Keep first 2 beats of bar 8, inject snare/tom 16th-note roll on beats 3 and 4
            for n in b8_notes:
                t = n.get("start_time", n.get("start", n.get("time", 0.0)))
                if t < b8_start + 2.0:
                    new_b8_notes.append(n)
            # Add fill notes on beats 2 and 3 of bar 8 (e.g. snare 38, high tom 50, mid tom 47)
            fill_pitches = [38, 38, 47, 47, 50, 50, 38, 38]
            for idx, p in enumerate(fill_pitches):
                step_t = b8_start + 2.0 + (idx * 0.25)
                vel = 80 + int(idx * 5)  # Rising velocity crescendo
                new_b8_notes.append({
                    "pitch": p,
                    "start_time": step_t,
                    "time": step_t,
                    "duration": 0.20,
                    "velocity": min(127, vel)
                })

        elif chosen_type == "abrupt_silence":
            # Abrupt silence: mute/remove all notes on beats 3 and 4 of bar 8
            for n in b8_notes:
                t = n.get("start_time", n.get("start", n.get("time", 0.0)))
                if t < b8_start + 2.0:
                    new_b8_notes.append(n)

        elif chosen_type == "passing_chord":
            # Keep bar 8 notes up to beat 3, then add passing tension chord on beat 3.5 or 4
            for n in b8_notes:
                t = n.get("start_time", n.get("start", n.get("time", 0.0)))
                if t < b8_start + 3.0:
                    new_b8_notes.append(n)
            # Passing chord (e.g. tritone sub or diminished notes)
            base_pitch = b8_notes[0].get("pitch", 60) if b8_notes else 60
            passing_pitches = [base_pitch + 1, base_pitch + 5, base_pitch + 8]
            for p in passing_pitches:
                new_b8_notes.append({
                    "pitch": p,
                    "start_time": b8_start + 3.0,
                    "time": b8_start + 3.0,
                    "duration": 1.0,
                    "velocity": 95
                })
        else:
            new_b8_notes = b8_notes

        return prior_notes + new_b8_notes

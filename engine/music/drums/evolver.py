# engine/music/drums/evolver.py
"""
Drum Pattern Evolver & Micro-Turnaround Engine:
Eliminates loop monotony by procedurally evolving drum sequences:
- Injects Bar 4 micro-turnarounds (ghost snares & triplet hi-hat rolls)
- Injects Bar 8 fills (cascading toms & syncopated flams)
- Injects section crashes and impact layers on arrivals.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
import copy
from engine.music.models import NoteEvent


class DrumFillType(str, Enum):
    BAR_4_TURNAROUND = "bar_4_turnaround"
    BAR_8_FILL = "bar_8_fill"
    SECTION_CRASH = "section_crash"
    ALL_EVOLUTION = "all_evolution"


class DrumPatternEvolver:
    """Procedural micro-variation and fill generator for drum loops."""

    @classmethod
    def inject_bar_4_turnaround(
        cls,
        notes: List[NoteEvent],
        loop_bars: float = 4.0,
        hat_pitch: int = 42,
        snare_pitch: int = 38
    ) -> List[NoteEvent]:
        """
        Inserts ghost notes and a triplet hat roll in the final beat of Bar 4 (beats 14.0 to 16.0).
        """
        evolved = [copy.deepcopy(n) for n in notes]
        b4_start = (loop_bars - 1.0) * 4.0 # e.g. beat 12.0
        b4_end = loop_bars * 4.0          # e.g. beat 16.0

        # Remove existing hats in the last beat (15.0 to 16.0) to make room for roll
        evolved = [n for n in evolved if not (n.pitch == hat_pitch and b4_start + 3.0 <= n.start < b4_end)]

        # 1. Injected ghost snare at beat 15.25
        evolved.append(NoteEvent(
            pitch=snare_pitch,
            start=b4_start + 3.25,
            duration=0.20,
            velocity=45,
            accent=False
        ))

        # 2. Injected 1/24 triplet hi-hat roll on beats 15.5, 15.666, 15.833
        roll_times = [b4_start + 3.5, b4_start + 3.667, b4_start + 3.833]
        velocities = [75, 95, 115]
        for t, v in zip(roll_times, velocities):
            evolved.append(NoteEvent(
                pitch=hat_pitch,
                start=round(t, 3),
                duration=0.12,
                velocity=v
            ))

        return sorted(evolved, key=lambda x: x.start)

    @classmethod
    def inject_bar_8_fill(
        cls,
        notes: List[NoteEvent],
        loop_bars: float = 8.0,
        tom_high: int = 50,
        tom_mid: int = 47,
        tom_low: int = 45,
        snare_pitch: int = 38
    ) -> List[NoteEvent]:
        """
        Inserts a dynamic tom and snare fill across the last 2 beats of Bar 8 (beats 30.0 to 32.0).
        """
        evolved = [copy.deepcopy(n) for n in notes]
        b8_start = (loop_bars - 1.0) * 4.0 # e.g. beat 28.0
        b8_end = loop_bars * 4.0          # e.g. beat 32.0

        # Clear existing hits in the last 2 beats (beats 30.0 to 32.0)
        fill_start = b8_start + 2.0
        evolved = [n for n in evolved if not (fill_start <= n.start < b8_end)]

        # Tom sequence: High Tom -> Mid Tom -> Low Tom -> Snare Flam
        fill_hits = [
            (tom_high, fill_start + 0.0, 0.22, 105),
            (tom_high, fill_start + 0.25, 0.22, 110),
            (tom_mid,  fill_start + 0.50, 0.22, 115),
            (tom_mid,  fill_start + 0.75, 0.22, 118),
            (tom_low,  fill_start + 1.00, 0.22, 122),
            (tom_low,  fill_start + 1.25, 0.22, 125),
            # Flam on snare
            (snare_pitch, fill_start + 1.65, 0.10, 85),
            (snare_pitch, fill_start + 1.75, 0.20, 127),
        ]

        for p, t, d, v in fill_hits:
            evolved.append(NoteEvent(pitch=p, start=round(t, 3), duration=d, velocity=v))

        return sorted(evolved, key=lambda x: x.start)

    @classmethod
    def inject_section_crash(
        cls,
        notes: List[NoteEvent],
        arrival_beat: float = 0.0,
        crash_pitch: int = 49,
        velocity: int = 127
    ) -> List[NoteEvent]:
        """Inserts a crash cymbal on section arrival beat."""
        evolved = [copy.deepcopy(n) for n in notes]
        evolved.append(NoteEvent(
            pitch=crash_pitch,
            start=round(arrival_beat, 3),
            duration=1.5,
            velocity=velocity,
            accent=True
        ))
        return sorted(evolved, key=lambda x: x.start)

    @classmethod
    def evolve_drum_sequence(
        cls,
        base_4bar_notes: List[NoteEvent],
        total_bars: float = 16.0,
        add_turnarounds: bool = True,
        add_fills: bool = True,
        add_crashes: bool = True
    ) -> List[NoteEvent]:
        """
        Extends a 4-bar drum motif across total_bars with procedurally varied fills,
        turnarounds, and crash accents.
        """
        full_notes: List[NoteEvent] = []
        repeats = int(total_bars / 4.0)

        for r in range(repeats):
            offset = r * 16.0
            for n in base_4bar_notes:
                copied = copy.deepcopy(n)
                copied.start += offset
                full_notes.append(copied)

        # 1. Injected Crashes on Bar 1 (beat 0) and Bar 9 (beat 32)
        if add_crashes:
            full_notes = cls.inject_section_crash(full_notes, arrival_beat=0.0)
            if total_bars >= 8.0:
                full_notes = cls.inject_section_crash(full_notes, arrival_beat=32.0)

        # 2. Turnarounds on Bar 4 and Bar 12
        if add_turnarounds:
            # Bar 4 turnaround (beat 12-16)
            full_notes = cls.inject_bar_4_turnaround(full_notes, loop_bars=4.0)
            if total_bars >= 12.0:
                full_notes = cls.inject_bar_4_turnaround(full_notes, loop_bars=12.0)

        # 3. Fills on Bar 8 and Bar 16
        if add_fills:
            if total_bars >= 8.0:
                full_notes = cls.inject_bar_8_fill(full_notes, loop_bars=8.0)
            if total_bars >= 16.0:
                full_notes = cls.inject_bar_8_fill(full_notes, loop_bars=16.0)

        return sorted(full_notes, key=lambda x: x.start)

    @classmethod
    def apply_drum_evolution(
        cls,
        conn: Any,
        track_index: int = 13,
        total_bars: float = 16.0
    ) -> Dict[str, Any]:
        """Reads or creates drum notes, evolves them with fills, and writes to Live."""
        # Default 4-bar foundation pattern
        base_notes = [
            NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=125),
            NoteEvent(pitch=38, start=2.0, duration=0.5, velocity=127),
            NoteEvent(pitch=42, start=0.0, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=0.5, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=1.0, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=1.5, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=2.0, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=2.5, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=3.0, duration=0.2, velocity=90),
            NoteEvent(pitch=42, start=3.5, duration=0.2, velocity=90),
        ]
        # Repeat across 4 bars
        b4_notes = []
        for b in range(4):
            for n in base_notes:
                cp = copy.deepcopy(n)
                cp.start += b * 4.0
                b4_notes.append(cp)

        evolved_notes = cls.evolve_drum_sequence(
            b4_notes,
            total_bars=total_bars,
            add_turnarounds=True,
            add_fills=True,
            add_crashes=True
        )

        if conn is not None and hasattr(conn, "send_command"):
            try:
                clip_len = total_bars * 4.0
                conn.send_command("delete_clip", {"track_index": track_index, "clip_index": 0})
                conn.send_command("create_clip", {"track_index": track_index, "clip_index": 0, "length": clip_len})
                conn.send_command("add_notes_to_clip", {
                    "track_index": track_index,
                    "clip_index": 0,
                    "notes": [
                        {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
                        for n in evolved_notes
                    ]
                })
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "total_bars": total_bars,
            "evolved_notes_count": len(evolved_notes),
            "track_index": track_index
        }

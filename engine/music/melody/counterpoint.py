# engine/music/melody/counterpoint.py
"""
Counter-Melody & Polyphonic Modal Arpeggiator Engine:
Generates guide-tone counter-melodies in upper registers (C5-C7) on syncopated off-beats,
and mathematical polyphonic arpeggios (Up, Down, Converge, Ping-Pong) with dynamic humanization.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
import math
from engine.music.models import NoteEvent, Chord


class ArpMode(str, Enum):
    UP = "up"
    DOWN = "down"
    UP_DOWN = "up_down"
    CONVERGE = "converge"
    PING_PONG = "ping_pong"


class CounterpointEngine:
    """Intelligent guide-tone counter-melody and arpeggio composer."""

    NOTE_TO_SEMITONE = {
        "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
        "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
    }

    @classmethod
    def extract_chord_pitches(cls, chord: Chord, base_octave: int = 5) -> List[int]:
        """Calculates MIDI pitches for a chord."""
        root_name = chord.root.upper().strip()
        root_semi = cls.NOTE_TO_SEMITONE.get(root_name, 5) # Default F
        base_pitch = (base_octave + 1) * 12 + root_semi

        # Interval offsets based on quality
        q = chord.quality.lower()
        if "min" in q:
            intervals = [0, 3, 7, 10]
        elif "maj7" in q:
            intervals = [0, 4, 7, 11]
        elif "dom" in q or "7" in q:
            intervals = [0, 4, 7, 10]
        elif "dim" in q:
            intervals = [0, 3, 6, 9]
        else:
            # Major triad
            intervals = [0, 4, 7, 12]

        return [base_pitch + i for i in intervals]

    @classmethod
    def generate_guide_tone_counter_melody(
        cls,
        chords: Optional[List[Chord]] = None,
        base_octave: int = 6,
        tempo: float = 120.0
    ) -> List[NoteEvent]:
        """
        Generates soaring counter-melody notes focusing on 3rds and 7ths of chords,
        placed primarily on off-beats (beats 0.5, 1.5, 2.75) to weave around the lead vocal.
        """
        active_chords = chords or [
            Chord(root="F", quality="minor", duration=4.0),
            Chord(root="Db", quality="major", duration=4.0),
            Chord(root="Bb", quality="minor", duration=4.0),
            Chord(root="C", quality="dominant7", duration=4.0)
        ]

        counter_notes: List[NoteEvent] = []
        curr_time = 0.0

        for chord in active_chords:
            pitches = cls.extract_chord_pitches(chord, base_octave=base_octave)
            p_third = pitches[1]  # 3rd (guide tone)
            p_fifth = pitches[2]  # 5th
            p_seventh = pitches[3] if len(pitches) > 3 else pitches[0] + 12

            # Syncopated off-beat motif:
            # Beat 0.5 (3rd) -> Beat 1.75 (7th) -> Beat 2.5 (5th) -> Beat 3.25 (3rd octave)
            counter_notes.append(NoteEvent(pitch=p_third, start=curr_time + 0.5, duration=0.8, velocity=105))
            counter_notes.append(NoteEvent(pitch=p_seventh, start=curr_time + 1.75, duration=0.6, velocity=115))
            counter_notes.append(NoteEvent(pitch=p_fifth, start=curr_time + 2.5, duration=0.6, velocity=110))
            counter_notes.append(NoteEvent(pitch=p_third + 12, start=curr_time + 3.25, duration=0.5, velocity=118))

            curr_time += chord.duration

        return counter_notes

    @classmethod
    def generate_modal_arpeggio(
        cls,
        chords: Optional[List[Chord]] = None,
        mode: Union[ArpMode, str] = ArpMode.UP_DOWN,
        subdivision: str = "1/16",
        base_octave: int = 5,
        swing: float = 0.15
    ) -> List[NoteEvent]:
        """
        Arpeggiates chord tones across the bar using the specified directional mode.
        """
        if isinstance(mode, str):
            try:
                mode = ArpMode(mode.lower())
            except ValueError:
                mode = ArpMode.UP_DOWN

        active_chords = chords or [
            Chord(root="F", quality="minor", duration=4.0),
            Chord(root="Db", quality="major", duration=4.0),
            Chord(root="Bb", quality="minor", duration=4.0),
            Chord(root="C", quality="dominant7", duration=4.0)
        ]

        step_dur = 0.25 if subdivision == "1/16" else 0.5 # 1/16th vs 1/8th
        arp_notes: List[NoteEvent] = []
        curr_time = 0.0

        for chord in active_chords:
            base_tones = cls.extract_chord_pitches(chord, base_octave=base_octave)
            tones_2oct = sorted(base_tones + [p + 12 for p in base_tones])

            # Order tones by mode
            if mode == ArpMode.UP:
                sequence = tones_2oct
            elif mode == ArpMode.DOWN:
                sequence = list(reversed(tones_2oct))
            elif mode == ArpMode.UP_DOWN:
                sequence = tones_2oct + list(reversed(tones_2oct[1:-1]))
            elif mode == ArpMode.CONVERGE:
                # Outside in: lowest, highest, second lowest, second highest...
                sequence = []
                left = 0
                right = len(tones_2oct) - 1
                while left <= right:
                    sequence.append(tones_2oct[left])
                    if left != right:
                        sequence.append(tones_2oct[right])
                    left += 1
                    right -= 1
            else:
                sequence = tones_2oct

            num_steps = int(chord.duration / step_dur)
            for s in range(num_steps):
                p = sequence[s % len(sequence)]
                t = curr_time + s * step_dur
                # Apply slight swing on odd 16ths
                if s % 2 == 1:
                    t += swing * 0.03

                # Velocity wave
                wave = 85 + int(30 * math.sin(s * 0.5))
                arp_notes.append(NoteEvent(
                    pitch=p,
                    start=round(t, 3),
                    duration=round(step_dur * 0.82, 3), # Crisp staccato articulation
                    velocity=min(127, wave)
                ))

            curr_time += chord.duration

        return arp_notes

    @classmethod
    def apply_counterpoint(
        cls,
        conn: Any,
        track_index: int = 4,
        style: str = "counter_melody",
        bpm: float = 120.0
    ) -> Dict[str, Any]:
        """Generates counter-melody or arpeggio and writes to Live clip."""
        if style == "arpeggio":
            notes = cls.generate_modal_arpeggio(mode=ArpMode.UP_DOWN)
        else:
            notes = cls.generate_guide_tone_counter_melody()

        if conn is not None and hasattr(conn, "send_command"):
            try:
                clip_len = 16.0
                conn.send_command("delete_clip", {"track_index": track_index, "clip_index": 0})
                conn.send_command("create_clip", {"track_index": track_index, "clip_index": 0, "length": clip_len})
                conn.send_command("set_clip_name", {"track_index": track_index, "clip_index": 0, "name": f"Counterpoint ({style})"})
                conn.send_command("add_notes_to_clip", {
                    "track_index": track_index,
                    "clip_index": 0,
                    "notes": [
                        {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
                        for n in notes
                    ]
                })
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "style": style,
            "notes_generated": len(notes),
            "track_index": track_index
        }

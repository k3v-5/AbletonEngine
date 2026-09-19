# engine/music/harmony/full_song.py
"""
Full-Song Harmonic Progression Engine:
Composes section-aware, progressive harmony across the full 96-bar arrangement.
Generates Drop-2/4 voicings, modal tension modulation, and smooth voice leading
without static loops.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import random
from engine.music.models import Chord, NoteEvent
from engine.music.theory.notes import normalize_pitch_class, note_to_midi, midi_to_note
from engine.music.theory.scales import get_scale_pitch_classes


class FullSongHarmonyEngine:
    """Composes macro-level harmony and Drop-2 voice-led chords across 96 bars."""

    # Note semitone lookup
    SEMITONES = {
        "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
        "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
    }

    # Relative chord templates per section for Neo-Soul / Jazz-Hop in F Minor
    # Section specifications: (section_name, start_bar, duration_bars, progression_chords)
    SECTION_HARMONY_BLUEPRINTS = {
        "Intro": [
            ("F", "min9", 8.0), ("Bb", "min11", 8.0),
            ("F", "min9", 8.0), ("C", "7sus4", 8.0)
        ],
        "Verse 1": [
            ("F", "min9", 8.0), ("Db", "maj7", 8.0), ("Bb", "min9", 8.0), ("C", "7alt", 8.0),
            ("F", "min9", 8.0), ("Db", "maj9", 8.0), ("Bb", "min11", 8.0), ("C", "7b9", 8.0)
        ],
        "Pre-Chorus": [
            ("Db", "maj9", 8.0), ("Eb", "9", 8.0),
            ("F", "min11", 8.0), ("G", "7#9", 4.0), ("C", "7b9", 4.0)
        ],
        "Chorus": [
            ("F", "min11", 8.0), ("Db", "maj9", 8.0), ("Eb", "13", 8.0), ("C", "min7", 8.0),
            ("F", "min9", 8.0), ("Db", "maj9", 8.0), ("Eb", "9", 8.0), ("C", "7alt", 8.0)
        ],
        "Verse 2": [
            ("F", "min9", 8.0), ("Ab", "maj7", 4.0), ("D", "dim7", 4.0),
            ("Bb", "min9", 8.0), ("C", "7alt", 8.0),
            ("F", "min9", 8.0), ("Db", "maj9", 8.0),
            ("Bb", "min11", 8.0), ("C", "7b9", 8.0)
        ],
        "Bridge": [
            ("F", "min11", 8.0), ("Bb", "13", 8.0),
            ("G", "min7b5", 8.0), ("C", "7#9", 8.0)
        ],
        "Final Chorus": [
            ("F", "min11", 8.0), ("Db", "maj9", 8.0), ("Eb", "13", 8.0), ("C", "min7", 8.0),
            ("F", "min9", 8.0), ("Db", "maj9", 8.0), ("Eb", "13", 8.0), ("C", "7alt", 8.0)
        ],
        "Outro": [
            ("F", "min9", 8.0), ("Bb", "min11", 8.0),
            ("Db", "maj9", 8.0), ("F", "min(add9)", 8.0)
        ]
    }

    @classmethod
    def get_chord_intervals(cls, quality: str) -> List[int]:
        """Returns semitone interval offsets for chord qualities."""
        q = quality.lower().replace(" ", "")
        if "min11" in q:
            return [0, 3, 7, 10, 14, 17]
        elif "min9" in q:
            return [0, 3, 7, 10, 14]
        elif "min(add9)" in q:
            return [0, 3, 7, 14]
        elif "min7b5" in q:
            return [0, 3, 6, 10]
        elif "min7" in q or "min" in q:
            return [0, 3, 7, 10]
        elif "maj9" in q:
            return [0, 4, 7, 11, 14]
        elif "maj7" in q:
            return [0, 4, 7, 11]
        elif "13" in q:
            return [0, 4, 7, 10, 14, 21]
        elif "9" in q and "7" not in q:
            return [0, 4, 7, 10, 14]
        elif "7alt" in q or "7#9" in q:
            return [0, 4, 10, 15] # 3rd, b7, #9
        elif "7b9" in q:
            return [0, 4, 10, 13] # 3rd, b7, b9
        elif "7sus4" in q:
            return [0, 5, 7, 10]
        elif "dim7" in q:
            return [0, 3, 6, 9]
        elif "dom7" in q or "7" in q:
            return [0, 4, 7, 10]
        else:
            return [0, 4, 7] # Major triad

    @classmethod
    def build_drop2_voicing(
        cls,
        root: str,
        quality: str,
        target_center_pitch: int = 60
    ) -> List[int]:
        """
        Creates an open Drop-2 voicing centered around middle C (MIDI 60).
        Drop-2 drops the second highest voice down an octave, creating
        a rich, wide spread that leaves space in the low-midrange.
        """
        root_semi = cls.SEMITONES.get(root.upper().strip(), 5)
        intervals = cls.get_chord_intervals(quality)

        # Build 4-note closed chord around base octave 4 (MIDI 60)
        base_octave = 4
        chord_pitches = [(base_octave * 12 + root_semi + i) for i in intervals[:4]]

        if len(chord_pitches) >= 4:
            # Sort pitches ascending
            chord_pitches.sort()
            # Drop the second voice from the top down an octave (12 semitones)
            second_highest = chord_pitches[-2]
            dropped = second_highest - 12
            voicing = [chord_pitches[0], dropped, chord_pitches[1], chord_pitches[3]]
            voicing.sort()
        else:
            voicing = chord_pitches

        # Shift voicing octave so its centroid aligns with target_center_pitch
        centroid = sum(voicing) / len(voicing)
        while centroid < target_center_pitch - 6:
            voicing = [p + 12 for p in voicing]
            centroid += 12
        while centroid > target_center_pitch + 6:
            voicing = [p - 12 for p in voicing]
            centroid -= 12

        return voicing

    @classmethod
    def optimize_voice_leading(cls, prev_voicing: List[int], next_voicing: List[int]) -> List[int]:
        """
        Inverts and octave-shifts next_voicing so that the sum of distances
        between voices is minimized, ensuring smooth conjunct motion.
        """
        best_voicing = next_voicing
        best_cost = float("inf")

        # Test octave shifts: -1, 0, +1
        for oct_shift in [-12, 0, 12]:
            shifted = [p + oct_shift for p in next_voicing]
            # Calculate distance cost against previous voicing
            cost = sum(abs(s - p) for s, p in zip(sorted(shifted), sorted(prev_voicing)))
            if cost < best_cost:
                best_cost = cost
                best_voicing = shifted

        return sorted(best_voicing)

    @classmethod
    def generate_full_song_progression(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor",
        total_bars: int = 96
    ) -> List[Chord]:
        """
        Generates the continuous list of Chord objects across 96 bars.
        """
        chords: List[Chord] = []
        current_bar = 0

        section_sequence = [
            "Intro", "Verse 1", "Pre-Chorus", "Chorus",
            "Verse 2", "Bridge", "Final Chorus", "Outro"
        ]

        SEMITONE_TO_NAME = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        delta = (cls.SEMITONES.get(key_root.upper().strip(), 5) - cls.SEMITONES["F"]) % 12

        for sec_name in section_sequence:
            sec_spec = cls.SECTION_HARMONY_BLUEPRINTS.get(sec_name, [])
            for root, quality, dur_beats in sec_spec:
                dur_bars = dur_beats / 4.0
                # Transpose root from base F to requested key_root
                if delta != 0:
                    orig_semi = cls.SEMITONES.get(root.upper().strip(), 5)
                    trans_root = SEMITONE_TO_NAME[(orig_semi + delta) % 12]
                else:
                    trans_root = root

                c = Chord(
                    root=trans_root,
                    quality=quality,
                    duration=dur_beats
                )
                chords.append(c)
                current_bar += dur_bars

        return chords

    @classmethod
    def generate_harmony_notes(
        cls,
        chords: Optional[List[Chord]] = None,
        key_root: str = "F",
        scale: str = "natural_minor",
        humanize_velocity: bool = True
    ) -> List[NoteEvent]:
        """
        Generates the full 96-bar sequence of NoteEvents with smooth voice leading,
        gentle velocity humanization, and natural note durations.
        """
        if chords is None:
            chords = cls.generate_full_song_progression(key_root=key_root, scale=scale)

        notes: List[NoteEvent] = []
        current_time = 0.0
        prev_voicing: Optional[List[int]] = None
        rng = random.Random(42)

        for chord in chords:
            raw_voicing = cls.build_drop2_voicing(chord.root, chord.quality)
            if prev_voicing is not None:
                smooth_voicing = cls.optimize_voice_leading(prev_voicing, raw_voicing)
            else:
                smooth_voicing = raw_voicing
            prev_voicing = smooth_voicing

            # Duration: chords sustain for their full length minus a tiny breath (0.1 beat)
            dur = max(0.5, chord.duration - 0.10)

            for voice_idx, pitch in enumerate(smooth_voicing):
                # Velocity weighting: top voice slightly louder, lower voices warmer
                base_vel = 78 + (voice_idx * 4) # 78, 82, 86, 90
                if humanize_velocity:
                    base_vel += rng.randint(-3, 3)
                base_vel = max(40, min(115, base_vel))

                notes.append(NoteEvent(
                    pitch=pitch,
                    start=current_time,
                    duration=dur,
                    velocity=base_vel
                ))

            current_time += chord.duration

        return notes

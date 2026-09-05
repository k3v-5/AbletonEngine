# engine/music/melody/topline.py
"""
Top-Line Melodic Engine:
Composes human-like Call-and-Response melodies with vocal respiration,
emotional melodic contours (arch, climax, cascade), and scale color degree emphasis.
"""

from typing import List, Dict, Any, Optional
import math
import random
from engine.music.models import Chord, NoteEvent
from engine.music.harmony.full_song import FullSongHarmonyEngine


class TopLineMelodyEngine:
    """Composes conversational, singable top-line lead melodies across sections."""

    # F Minor Scale Degrees (MIDI Octave 4 & 5: F4=65, G4=67, Ab4=68, Bb4=70, C5=72, Db5=73, Eb5=75, F5=77)
    F_MINOR_SCALE = [60, 61, 63, 65, 67, 68, 70, 72, 73, 75, 77, 80] # C4 to Ab5

    @classmethod
    def generate_8bar_phrase(
        cls,
        start_beat: float,
        key_root: str = "F",
        scale: str = "natural_minor",
        energy_level: float = 0.85,
        phrase_seed: int = 42
    ) -> List[NoteEvent]:
        """
        Generates an 8-bar (32 beats) structured Call-and-Response melodic statement:
        - Bars 1-2 (Beats 0-8): Question (Call) -> Ends unresolved on scale degree 2 or 5.
        - Bars 3-4 (Beats 8-16): Answer (Response) -> Resolves to tonic or 3rd with breath.
        - Bars 5-6 (Beats 16-24): Climax / Apex -> Higher register, energetic rhythmic activity.
        - Bars 7-8 (Beats 24-32): Cadential resolution -> Graceful descent with trailing breath.
        """
        rng = random.Random(phrase_seed)
        notes: List[NoteEvent] = []

        # 1. QUESTION (Call) - Bars 1-2 (Beats 0 to 7)
        # Starts with pickup on beat 0.5, ascends towards G4 or C5, leaves beat 7.0-8.0 as breath
        call_pitches = [65, 68, 70, 72] if energy_level > 0.6 else [60, 63, 65, 67] # F4, Ab4, Bb4, C5
        notes.append(NoteEvent(pitch=call_pitches[0], start=start_beat + 0.5, duration=0.75, velocity=85))
        notes.append(NoteEvent(pitch=call_pitches[1], start=start_beat + 1.5, duration=1.00, velocity=92))
        notes.append(NoteEvent(pitch=call_pitches[2], start=start_beat + 3.0, duration=0.75, velocity=90))
        notes.append(NoteEvent(pitch=call_pitches[3], start=start_beat + 4.5, duration=2.25, velocity=102))
        # Breath from 6.75 to 8.0 (silence)

        # 2. ANSWER (Response) - Bars 3-4 (Beats 8 to 15)
        # Descends smoothly back to tonic F4 or 3rd Ab4
        resp_pitches = [72, 70, 68, 65] # C5 -> Bb4 -> Ab4 -> F4
        notes.append(NoteEvent(pitch=resp_pitches[0], start=start_beat + 8.5, duration=0.75, velocity=94))
        notes.append(NoteEvent(pitch=resp_pitches[1], start=start_beat + 9.5, duration=1.00, velocity=88))
        notes.append(NoteEvent(pitch=resp_pitches[2], start=start_beat + 11.0, duration=1.25, velocity=86))
        notes.append(NoteEvent(pitch=resp_pitches[3], start=start_beat + 12.5, duration=2.50, velocity=95))
        # Breath from 15.0 to 16.0 (silence)

        # 3. CLIMAX / APEX - Bars 5-6 (Beats 16 to 23)
        # Register leaps to Eb5 or F5 with rhythmic subdivisions
        apex_pitch = 75 if energy_level > 0.7 else 72 # Eb5 or C5
        notes.append(NoteEvent(pitch=70, start=start_beat + 16.5, duration=0.50, velocity=88))
        notes.append(NoteEvent(pitch=72, start=start_beat + 17.0, duration=0.50, velocity=94))
        notes.append(NoteEvent(pitch=apex_pitch, start=start_beat + 18.0, duration=1.75, velocity=112)) # Peak emotional hit
        notes.append(NoteEvent(pitch=apex_pitch - 2, start=start_beat + 20.25, duration=0.75, velocity=98))
        notes.append(NoteEvent(pitch=70, start=start_beat + 21.5, duration=1.75, velocity=95))
        # Breath from 23.25 to 24.0 (silence)

        # 4. RESOLUTION CADENCE - Bars 7-8 (Beats 24 to 31)
        notes.append(NoteEvent(pitch=68, start=start_beat + 24.5, duration=0.75, velocity=88))
        notes.append(NoteEvent(pitch=67, start=start_beat + 25.5, duration=0.75, velocity=84))
        notes.append(NoteEvent(pitch=65, start=start_beat + 26.5, duration=3.50, velocity=96)) # Sustained root F4
        # Breath until end of bar 8

        return notes

    @classmethod
    def generate_full_song_melody(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor"
    ) -> List[NoteEvent]:
        """
        Generates full-song melodic arrangement across active sections:
        - Verse 1 (Bars 16 - 24): 8-bar introspective statement.
        - Chorus 1 (Bars 32 - 48): 16-bar high-energy double statement.
        - Verse 2 (Bars 56 - 64): 8-bar melodic variation.
        - Bridge (Bars 64 - 72): 8-bar modal counter-statement.
        - Final Chorus (Bars 72 - 88): 16-bar maximum climax melody.
        """
        notes: List[NoteEvent] = []

        # Verse 1: Bars 16-24 (start beat = 64.0)
        v1_notes = cls.generate_8bar_phrase(start_beat=64.0, energy_level=0.50, phrase_seed=101)
        notes.extend(v1_notes)

        # Chorus 1: Bars 32-48 (start beats = 128.0 and 160.0)
        ch1_a = cls.generate_8bar_phrase(start_beat=128.0, energy_level=0.90, phrase_seed=202)
        ch1_b = cls.generate_8bar_phrase(start_beat=160.0, energy_level=0.95, phrase_seed=203)
        notes.extend(ch1_a)
        notes.extend(ch1_b)

        # Verse 2: Bars 56-64 (start beat = 224.0)
        v2_notes = cls.generate_8bar_phrase(start_beat=224.0, energy_level=0.55, phrase_seed=303)
        notes.extend(v2_notes)

        # Bridge: Bars 64-72 (start beat = 256.0)
        bridge_notes = cls.generate_8bar_phrase(start_beat=256.0, energy_level=0.70, phrase_seed=404)
        notes.extend(bridge_notes)

        # Final Chorus: Bars 72-88 (start beats = 288.0 and 320.0)
        final_a = cls.generate_8bar_phrase(start_beat=288.0, energy_level=1.00, phrase_seed=505)
        final_b = cls.generate_8bar_phrase(start_beat=320.0, energy_level=1.00, phrase_seed=506)
        notes.extend(final_a)
        notes.extend(final_b)

        return notes

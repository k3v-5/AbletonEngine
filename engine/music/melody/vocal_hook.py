# engine/music/melody/vocal_hook.py
"""
Vocal Hook Chop Engine:
Generates infectious, syncopated vocal chop hook motifs.
Aligned with active harmonic degrees and positioned dynamically across
Intro, Chorus, and Final Climax sections.
"""

from typing import List, Dict, Any, Optional
import random
from engine.music.models import NoteEvent, Chord
from engine.music.harmony.full_song import FullSongHarmonyEngine


class VocalHookChopEngine:
    """Composes rhythmic vocal chop hooks across 96 bars."""

    CHOP_PITCH_POOL = [65, 68, 70, 72, 75] # F4, Ab4, Bb4, C5, Eb5 (Minor Pentatonic)

    @classmethod
    def generate_2bar_hook_motif(
        cls,
        start_beat: float,
        octave_shift: int = 0,
        energy_level: float = 0.90,
        motif_seed: int = 77
    ) -> List[NoteEvent]:
        """
        Generates a 2-bar (8 beats) infectious syncopated vocal chop motif.
        """
        rng = random.Random(motif_seed)
        notes: List[NoteEvent] = []

        # Syncopated rhythm offsets: 0.5 (and of 1), 1.25, 2.75, 4.0, 5.5, 6.75
        rhythm_offsets = [
            (0.5, 0.45, 102),
            (1.25, 0.50, 95),
            (2.5, 0.75, 110),
            (4.0, 0.45, 98),
            (5.25, 0.50, 105),
            (6.5, 1.20, 115) # Held chop ending phrase
        ]

        for offset, dur, vel in rhythm_offsets:
            p = rng.choice(cls.CHOP_PITCH_POOL) + (octave_shift * 12)
            notes.append(NoteEvent(
                pitch=p,
                start=start_beat + offset,
                duration=dur,
                velocity=int(vel * (0.8 + (energy_level * 0.2)))
            ))

        return notes

    @classmethod
    def generate_full_song_vocal_hook(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor"
    ) -> List[NoteEvent]:
        """
        Deploys the vocal chop hook into:
        1. Intro (Bars 4 - 8): Distant, filtered chops (lower octave 4).
        2. Chorus 1 (Bars 32 - 48): Full hook motif repeated every 2 bars (8 times) in high register (octave 5).
        3. Bridge (Bars 68 - 72): Sparse pre-drop teaser chops.
        4. Final Chorus (Bars 72 - 88): Maximum intensity hook with rhythmic variations.
        """
        notes: List[NoteEvent] = []

        # 1. Intro: Bars 4-8 (beats 16.0 to 32.0)
        for b_idx, start_b in enumerate([16.0, 24.0]):
            notes.extend(cls.generate_2bar_hook_motif(
                start_beat=start_b,
                octave_shift=0,
                energy_level=0.40,
                motif_seed=10 + b_idx
            ))

        # 2. Chorus 1: Bars 32-48 (beats 128.0 to 192.0) - 8 repetitions of 2-bar motif
        for rep in range(8):
            start_b = 128.0 + (rep * 8.0)
            notes.extend(cls.generate_2bar_hook_motif(
                start_beat=start_b,
                octave_shift=1, # Octave 5 (bright hook)
                energy_level=0.92,
                motif_seed=100 + (rep % 4)
            ))

        # 3. Bridge: Bars 68-72 (beats 272.0 to 288.0)
        notes.extend(cls.generate_2bar_hook_motif(
            start_beat=272.0,
            octave_shift=0,
            energy_level=0.60,
            motif_seed=301
        ))

        # 4. Final Chorus: Bars 72-88 (beats 288.0 to 352.0)
        for rep in range(8):
            start_b = 288.0 + (rep * 8.0)
            notes.extend(cls.generate_2bar_hook_motif(
                start_beat=start_b,
                octave_shift=1,
                energy_level=1.00,
                motif_seed=400 + (rep % 4)
            ))

        return notes

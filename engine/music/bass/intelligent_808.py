# engine/music/bass/intelligent_808.py
"""
Intelligent 808 Bass Engine:
Composes interlocking, section-dynamic 808 sub-basslines.
Features kick-groove interlocking, chromatic leading-tone approaches,
octave leaps, authentic portamento slide envelopes, and pre-drop vacuums.
"""

from typing import List, Dict, Any, Optional
import math
import random
from engine.music.models import Chord, NoteEvent
from engine.music.harmony.full_song import FullSongHarmonyEngine


class Intelligent808BassEngine:
    """Composes performance-grade 808 basslines across 96 bars."""

    SEMITONES = FullSongHarmonyEngine.SEMITONES

    @classmethod
    def get_bass_pitch_for_root(cls, root: str, target_octave: int = 1) -> int:
        """Calculates root MIDI pitch clamped strictly in sub-bass range (MIDI 24 - 44)."""
        semi = cls.SEMITONES.get(root.upper().strip(), 5) # Default F
        pitch = (target_octave + 1) * 12 + semi
        while pitch < 24: # C1
            pitch += 12
        while pitch > 44: # Ab2
            pitch -= 12
        return pitch

    @classmethod
    def generate_808_bassline(
        cls,
        chords: Optional[List[Chord]] = None,
        key_root: str = "F",
        scale: str = "natural_minor",
        enable_slides: bool = True,
        enable_chromatic_approach: bool = True
    ) -> List[NoteEvent]:
        """
        Generates complete 96-bar 808 bassline aligned with chords and section energy.
        """
        if chords is None:
            chords = FullSongHarmonyEngine.generate_full_song_progression(key_root=key_root, scale=scale)

        notes: List[NoteEvent] = []
        current_beat = 0.0

        for chord_idx, chord in enumerate(chords):
            duration_beats = chord.duration
            bar_start = int(current_beat / 4.0)
            root_pitch = cls.get_bass_pitch_for_root(chord.root)

            # Determine target chord root for chromatic approach
            next_chord = chords[chord_idx + 1] if chord_idx + 1 < len(chords) else None
            next_root_pitch = cls.get_bass_pitch_for_root(next_chord.root) if next_chord else root_pitch

            # --- SECTION FILTERING ---
            # 1. Intro (Bars 0 - 8): Silent (leave space for filtered keys & foley)
            if bar_start < 8:
                current_beat += duration_beats
                continue

            # 2. Verse 1 (Bars 8 - 24): Bass only enters on bar 16
            if 8 <= bar_start < 16:
                current_beat += duration_beats
                continue

            # 3. Pre-Drop Vacuum on Bar 31 (Pre-Chorus final bar): Mute beat 4 for drop impact
            is_pre_drop_bar = (bar_start == 30 or bar_start == 31)

            # 4. Outro (Bars 88 - 96): Only sustain first bar, then silence
            if bar_start >= 88:
                if bar_start == 88:
                    notes.append(NoteEvent(pitch=root_pitch, start=current_beat, duration=7.5, velocity=85))
                current_beat += duration_beats
                continue

            # --- RHYTHMIC GROOVE PATTERN PER 8-BEAT BLOCK (2 BARS) ---
            if duration_beats >= 8.0:
                # Hit 1: Downbeat bar 1 (beat 0.0)
                notes.append(NoteEvent(pitch=root_pitch, start=current_beat + 0.0, duration=1.75, velocity=115))

                # Hit 2: Syncopated bounce on beat 2.5 (the "and" of 3)
                notes.append(NoteEvent(pitch=root_pitch, start=current_beat + 2.5, duration=1.25, velocity=98))

                # Hit 3: Downbeat bar 2 (beat 4.0)
                notes.append(NoteEvent(pitch=root_pitch, start=current_beat + 4.0, duration=1.50, velocity=108))

                # Hit 4: Turnaround slide / Octave jump / Chromatic approach on bar 2 beat 6.5 & 7.5
                if not is_pre_drop_bar:
                    if enable_slides and (bar_start % 4 == 2 or bar_start % 4 == 3):
                        # Octave jump on beat 6.5 (+12 semitones)
                        notes.append(NoteEvent(pitch=root_pitch + 12, start=current_beat + 6.5, duration=0.75, velocity=102))

                    if enable_chromatic_approach and next_root_pitch != root_pitch:
                        # Chromatic leading tone on beat 7.5 (half-step below target)
                        leading_tone = next_root_pitch - 1 if next_root_pitch > 24 else next_root_pitch + 1
                        notes.append(NoteEvent(pitch=leading_tone, start=current_beat + 7.5, duration=0.45, velocity=95))
                    else:
                        # Standard syncopated pulse
                        notes.append(NoteEvent(pitch=root_pitch, start=current_beat + 6.0, duration=1.50, velocity=95))

            else:
                # 4-beat block (1 bar)
                notes.append(NoteEvent(pitch=root_pitch, start=current_beat + 0.0, duration=1.75, velocity=112))
                if not is_pre_drop_bar:
                    notes.append(NoteEvent(pitch=root_pitch, start=current_beat + 2.5, duration=1.25, velocity=96))

            current_beat += duration_beats

        return notes

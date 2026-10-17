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
from engine.music.melody.hook_contour import HookContourEngine, HookContourType, HookEvaluationReport


class TopLineMelodyEngine:
    """Composes conversational, singable top-line lead melodies and commercial hooks across sections."""

    @classmethod
    def evaluate_melody_hook(cls, notes: List[NoteEvent]) -> HookEvaluationReport:
        """Evaluates melodic memorability, leap-step integrity, and vocal range confinement."""
        return HookContourEngine.evaluate_hook(notes)

    @classmethod
    def generate_commercial_hook(
        cls,
        start_beat: float = 0.0,
        key_root: str = "F",
        scale: str = "natural_minor",
        energy_level: float = 0.85,
        contour: str = "ARCH",
        seed: int = 42
    ) -> List[NoteEvent]:
        """Generates a commercial hook obeying Hook Theory and cognitive retention principles."""
        c_type = getattr(HookContourType, contour.upper(), HookContourType.ARCH)
        return HookContourEngine.generate_hook_motif(
            key_root=key_root,
            scale=scale,
            start_beat=start_beat,
            contour=c_type,
            energy_level=energy_level,
            phrase_seed=seed
        )

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
        Generates an 8-bar (32 beats) structured Call-and-Response melodic statement
        dynamically mapped to the project key root and modal scale degrees.
        """
        name_to_midi = {
            "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4,
            "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9,
            "A#": 10, "BB": 10, "B": 11
        }
        root_pc = name_to_midi.get(key_root.upper(), 5)
        oct4_base = 60 + root_pc
        if oct4_base > 71:
            oct4_base -= 12

        scale_l = scale.lower()
        if "dorian" in scale_l:
            scale_intervals = [0, 2, 3, 5, 7, 9, 10]
        elif "phrygian" in scale_l:
            scale_intervals = [0, 1, 3, 5, 7, 8, 10]
        elif "lydian" in scale_l:
            scale_intervals = [0, 2, 4, 6, 7, 9, 11]
        elif "mixolydian" in scale_l:
            scale_intervals = [0, 2, 4, 5, 7, 9, 10]
        elif "locrian" in scale_l:
            scale_intervals = [0, 1, 3, 5, 6, 8, 10]
        elif "harmonic" in scale_l and ("min" in scale_l or "menor" in scale_l):
            scale_intervals = [0, 2, 3, 5, 7, 8, 11]
        elif "melodic" in scale_l and ("min" in scale_l or "menor" in scale_l):
            scale_intervals = [0, 2, 3, 5, 7, 9, 11]
        elif "blues" in scale_l:
            scale_intervals = [0, 3, 5, 6, 7, 10]
        elif "pentatonic" in scale_l and ("min" in scale_l or "menor" in scale_l):
            scale_intervals = [0, 3, 5, 7, 10]
        elif "pentatonic" in scale_l and ("maj" in scale_l or "mayor" in scale_l):
            scale_intervals = [0, 2, 4, 7, 9]
        elif any(k in scale_l for k in ["minor", "menor", "dark"]):
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]
        else:
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]

        n_iv = len(scale_intervals)
        deg_1 = oct4_base + scale_intervals[0]
        deg_2 = oct4_base + scale_intervals[1 % n_iv]
        deg_3 = oct4_base + scale_intervals[2 % n_iv]
        deg_4 = oct4_base + scale_intervals[3 % n_iv]
        deg_5 = oct4_base + scale_intervals[4 % n_iv]
        deg_apex = oct4_base + 12 + scale_intervals[min(4, n_iv - 1)]

        notes: List[NoteEvent] = []

        # 1. QUESTION (Call) - Bars 1-2 (Beats 0 to 7)
        call_pitches = [deg_1, deg_3, deg_4, deg_5] if energy_level > 0.6 else [deg_1 - 12, deg_1, deg_2, deg_3]
        notes.append(NoteEvent(pitch=call_pitches[0], start=start_beat + 0.5, duration=0.75, velocity=85))
        notes.append(NoteEvent(pitch=call_pitches[1], start=start_beat + 1.5, duration=1.00, velocity=92))
        notes.append(NoteEvent(pitch=call_pitches[2], start=start_beat + 3.0, duration=0.75, velocity=90))
        notes.append(NoteEvent(pitch=call_pitches[3], start=start_beat + 4.5, duration=2.25, velocity=102))

        # 2. ANSWER (Response) - Bars 3-4 (Beats 8 to 15)
        resp_pitches = [deg_5, deg_4, deg_3, deg_1]
        notes.append(NoteEvent(pitch=resp_pitches[0], start=start_beat + 8.5, duration=0.75, velocity=94))
        notes.append(NoteEvent(pitch=resp_pitches[1], start=start_beat + 9.5, duration=1.00, velocity=88))
        notes.append(NoteEvent(pitch=resp_pitches[2], start=start_beat + 11.0, duration=1.25, velocity=86))
        notes.append(NoteEvent(pitch=resp_pitches[3], start=start_beat + 12.5, duration=2.50, velocity=95))

        # 3. CLIMAX / APEX - Bars 5-6 (Beats 16 to 23)
        notes.append(NoteEvent(pitch=deg_4, start=start_beat + 16.5, duration=0.50, velocity=88))
        notes.append(NoteEvent(pitch=deg_5, start=start_beat + 17.0, duration=0.50, velocity=94))
        notes.append(NoteEvent(pitch=deg_apex, start=start_beat + 18.0, duration=1.75, velocity=112))
        notes.append(NoteEvent(pitch=deg_apex - 2, start=start_beat + 20.25, duration=0.75, velocity=98))
        notes.append(NoteEvent(pitch=deg_4, start=start_beat + 21.5, duration=1.75, velocity=95))

        # 4. RESOLUTION CADENCE - Bars 7-8 (Beats 24 to 31)
        notes.append(NoteEvent(pitch=deg_3, start=start_beat + 24.5, duration=0.75, velocity=88))
        notes.append(NoteEvent(pitch=deg_2, start=start_beat + 25.5, duration=0.75, velocity=84))
        notes.append(NoteEvent(pitch=deg_1, start=start_beat + 26.5, duration=3.50, velocity=96))

        return notes

    @classmethod
    def generate_full_song_melody(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor",
        sections: Optional[List[Dict[str, Any]]] = None,
        total_bars: int = 64
    ) -> List[NoteEvent]:
        """
        Generates full-song melodic arrangement across active sections dynamically.
        Adapts seamlessly to arbitrary sections and bar lengths.
        """
        notes: List[NoteEvent] = []

        if sections:
            for s_idx, sec in enumerate(sections):
                s_name = sec.get("name", "").lower()
                s_bars = sec.get("bars", 8)
                s_start = sec.get("start_bar", 0) * 4.0
                if any(k in s_name for k in ["verse", "verso", "chorus", "coro", "hook", "drop", "bridge", "puente"]):
                    e_level = 0.90 if any(k in s_name for k in ["chorus", "coro", "hook", "drop", "climax"]) else 0.60
                    chunks = max(1, s_bars // 8)
                    for c_i in range(chunks):
                        c_start = s_start + (c_i * 32.0)
                        notes.extend(cls.generate_8bar_phrase(
                            start_beat=c_start,
                            key_root=key_root,
                            scale=scale,
                            energy_level=e_level,
                            phrase_seed=100 + (s_idx * 17) + c_i
                        ))
        else:
            b1 = (total_bars // 4) * 4.0
            b2 = (total_bars // 2) * 4.0
            notes.extend(cls.generate_8bar_phrase(start_beat=b1, key_root=key_root, scale=scale, energy_level=0.60, phrase_seed=101))
            notes.extend(cls.generate_8bar_phrase(start_beat=b2, key_root=key_root, scale=scale, energy_level=0.92, phrase_seed=202))

        return notes

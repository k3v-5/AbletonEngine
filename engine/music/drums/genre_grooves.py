# engine/music/drums/genre_grooves.py
"""
Genre Rhythm & Groove Articulation Engine:
Generates authentic, highly articulated drum patterns tailored to specific genres
(Trap, House, Neo-Soul, Reggaeton, Synthwave, Boom-Bap), replacing generic loops
with professional groove-pool micro-timing, ghost notes, and hi-hat roll dynamics.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
import random
import copy
from engine.music.models import NoteEvent


class GenreDrumStyle(str, Enum):
    TRAP = "trap"
    HOUSE = "house"
    NEO_SOUL = "neo_soul"
    REGGAETON = "reggaeton"
    SYNTHWAVE = "synthwave"
    BOOM_BAP = "boom_bap"
    TECHNO = "techno"


class GenreRhythmGrooveEngine:
    """Procedural rhythm generator with genre-authentic pocket and groove templates."""

    # Standard General MIDI / Drum Rack Pitches
    KICK_PITCH = 36
    SNARE_PITCH = 38
    CLAP_PITCH = 39
    CLOSED_HAT_PITCH = 42
    OPEN_HAT_PITCH = 46
    PERC_PITCH = 37
    HIGH_TOM = 50
    MID_TOM = 47
    LOW_TOM = 45

    @classmethod
    def get_supported_genres(cls) -> List[str]:
        return [g.value for g in GenreDrumStyle]

    @classmethod
    def generate_rhythm_pattern(
        cls,
        genre: Union[str, GenreDrumStyle],
        length_bars: int = 4,
        tempo: float = 120.0,
        swing_amount: float = 0.0,
        humanize_ms: float = 6.0
    ) -> List[NoteEvent]:
        """
        Generates a complete multi-layered drum pattern for the requested genre and length.
        """
        if isinstance(genre, str):
            g_clean = genre.lower().strip()
            if "trap" in g_clean or "hip hop" in g_clean or "hiphop" in g_clean:
                style = GenreDrumStyle.TRAP
            elif "house" in g_clean:
                style = GenreDrumStyle.HOUSE
            elif "soul" in g_clean or "rnb" in g_clean:
                style = GenreDrumStyle.NEO_SOUL
            elif "reggaeton" in g_clean or "latin" in g_clean or "dembow" in g_clean:
                style = GenreDrumStyle.REGGAETON
            elif "synth" in g_clean or "80s" in g_clean or "retro" in g_clean:
                style = GenreDrumStyle.SYNTHWAVE
            elif "boom" in g_clean:
                style = GenreDrumStyle.BOOM_BAP
            elif "techno" in g_clean:
                style = GenreDrumStyle.TECHNO
            else:
                style = GenreDrumStyle.TRAP
        else:
            style = genre

        generator_map = {
            GenreDrumStyle.TRAP: cls._generate_trap,
            GenreDrumStyle.HOUSE: cls._generate_house,
            GenreDrumStyle.NEO_SOUL: cls._generate_neo_soul,
            GenreDrumStyle.REGGAETON: cls._generate_reggaeton,
            GenreDrumStyle.SYNTHWAVE: cls._generate_synthwave,
            GenreDrumStyle.BOOM_BAP: cls._generate_boom_bap,
            GenreDrumStyle.TECHNO: cls._generate_techno,
        }

        gen_fn = generator_map.get(style, cls._generate_trap)
        raw_notes = gen_fn(length_bars)

        # Apply swing if specified
        if swing_amount > 0.0:
            raw_notes = cls.apply_mpc_swing(raw_notes, swing_amount)

        # Apply subtle micro-timing humanization
        if humanize_ms > 0.0:
            raw_notes = cls.apply_micro_timing_humanization(raw_notes, humanize_ms=humanize_ms, tempo=tempo)

        return sorted(raw_notes, key=lambda n: n.start)

    @classmethod
    def _generate_trap(cls, length_bars: int) -> List[NoteEvent]:
        """
        Trap pattern:
        - Snare/Clap on half-time beat 3 (beat 2.0 in 4/4)
        - Punchy syncopated 808-aligned kick
        - Dynamic rolling hi-hats with triplets (1/12) and velocity ramps
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # Snare/Clap on beat 3 (offset 2.0)
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 2.0, duration=0.25, velocity=115))

            # Kick pattern (syncopated)
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.30, velocity=122))
            if bar % 2 == 0:
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.75, duration=0.25, velocity=110))
            else:
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.5, duration=0.25, velocity=112))
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 3.25, duration=0.25, velocity=105))

            # Hi-hats: straight 8ths with dynamic rolls
            # Last bar gets high-speed triplet roll
            if bar == length_bars - 1:
                # Normal hats first 3 beats
                for step in range(6):
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + step * 0.5, duration=0.15, velocity=85 if step % 2 == 0 else 70))
                # Triplet roll on beat 4 (start 3.0 to 4.0) -> 6 hits (1/24)
                for r in range(6):
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + 3.0 + r * (1.0 / 6.0), duration=0.08, velocity=60 + r * 10))
            else:
                # 8th notes with alternating accents
                for step in range(8):
                    t = bar_start + step * 0.5
                    v = 95 if step % 2 == 0 else 72
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=t, duration=0.15, velocity=v))
                # In bar 2 or 4 inject a 1/12 triplet burst at beat 1.5
                if bar % 2 == 1:
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + 1.667, duration=0.10, velocity=88))
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + 1.833, duration=0.10, velocity=98))

        return notes

    @classmethod
    def _generate_house(cls, length_bars: int) -> List[NoteEvent]:
        """
        House pattern:
        - Four-on-the-floor kick
        - Clap/Snare on beats 2 & 4 (offsets 1.0 & 3.0)
        - Offbeat Open Hi-Hat (0.5, 1.5, 2.5, 3.5)
        - 16th-note closed hat groove
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # 4-on-the-floor Kick
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + b * 1.0, duration=0.25, velocity=118))

            # Clap on 2 and 4
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 1.0, duration=0.20, velocity=110))
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 3.0, duration=0.20, velocity=112))

            # Offbeat Open Hat
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.OPEN_HAT_PITCH, start=bar_start + b * 1.0 + 0.5, duration=0.35, velocity=95))

            # Subtle closed hat 16ths
            for s in range(16):
                if s % 4 != 2:  # Don't clash with open hat
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.25, duration=0.12, velocity=65 if s % 2 == 0 else 50))

        return notes

    @classmethod
    def _generate_neo_soul(cls, length_bars: int) -> List[NoteEvent]:
        """
        Neo-Soul pattern:
        - Laid-back delayed snare timing (+0.035 beat)
        - Syncopated kick with variable velocities
        - Ghost notes on snare (vel 35-48)
        - Dynamic 16th hats with organic velocity waves
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # Kick
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.25, velocity=102))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 1.75, duration=0.20, velocity=88))
            if bar % 2 == 1:
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.5, duration=0.20, velocity=94))

            # Laid-back snare on 2 and 4 (+0.035 behind beat)
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.035, duration=0.22, velocity=106))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.035, duration=0.22, velocity=108))

            # Ghost snares
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 2.25, duration=0.12, velocity=42))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.75, duration=0.12, velocity=45))

            # 16th hats with dynamic velocity curve
            hat_vels = [88, 55, 72, 48, 85, 52, 70, 46, 90, 54, 75, 50, 84, 52, 78, 55]
            for s in range(16):
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.25, duration=0.15, velocity=hat_vels[s]))

        return notes

    @classmethod
    def _generate_reggaeton(cls, length_bars: int) -> List[NoteEvent]:
        """
        Reggaeton / Latin Dembow:
        - Kick on 1, 2, 3, 4
        - Snare at 0.75, 1.5, 2.75, 3.5 (Dembow syncopation)
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # 4-on-the-floor Kick
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + b * 1.0, duration=0.25, velocity=120))

            # Dembow Snare rhythm
            dembow_offsets = [0.75, 1.50, 2.75, 3.50]
            for off in dembow_offsets:
                notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + off, duration=0.20, velocity=114))

            # Closed hat on 8ths
            for s in range(8):
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.5, duration=0.15, velocity=85 if s % 2 == 0 else 70))

        return notes

    @classmethod
    def _generate_synthwave(cls, length_bars: int) -> List[NoteEvent]:
        """
        Synthwave 80s pattern:
        - Driving kick on 1 and 3 (0.0, 2.0)
        - Gated snare on 2 and 4 (1.0, 3.0) with maximum impact
        - Relentless driving 16th hats
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # Kick on 1 and 3 (and 3.5 in alternate bars)
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.28, velocity=122))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.0, duration=0.28, velocity=120))
            if bar % 2 == 1:
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.5, duration=0.25, velocity=110))

            # Snare on 2 and 4
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.0, duration=0.35, velocity=125))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.0, duration=0.35, velocity=127))

            # Running 16th hats
            for s in range(16):
                v = 100 if s % 4 == 0 else (80 if s % 2 == 0 else 65)
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.25, duration=0.18, velocity=v))

        return notes

    @classmethod
    def _generate_boom_bap(cls, length_bars: int) -> List[NoteEvent]:
        """Boom-Bap classic hip hop pattern."""
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.28, velocity=115))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 1.75, duration=0.22, velocity=100))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.0, duration=0.25, velocity=118))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.0, duration=0.25, velocity=120))
            for s in range(8):
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.5, duration=0.18, velocity=90 if s % 2 == 0 else 72))
        return notes

    @classmethod
    def _generate_techno(cls, length_bars: int) -> List[NoteEvent]:
        """Techno driving industrial pattern."""
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + b * 1.0, duration=0.25, velocity=124))
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.OPEN_HAT_PITCH, start=bar_start + b * 1.0 + 0.5, duration=0.25, velocity=98))
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 1.0, duration=0.20, velocity=115))
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 3.0, duration=0.20, velocity=116))
        return notes

    @staticmethod
    def apply_mpc_swing(notes: List[NoteEvent], swing_percent: float = 0.58) -> List[NoteEvent]:
        """
        Shifts every second 16th note (odd sixteenths: 0.25, 0.75, 1.25, etc.) forward
        according to the MPC swing percentage (0.50 = straight, 0.58 = classic MPC, 0.66 = triplet swing).
        """
        swung = []
        for n in notes:
            n_copy = copy.deepcopy(n)
            quarter_pos = n_copy.start % 1.0
            is_second_16th = abs(quarter_pos - 0.25) < 0.04
            is_fourth_16th = abs(quarter_pos - 0.75) < 0.04

            if is_second_16th or is_fourth_16th:
                shift = (swing_percent - 0.50) * 0.5
                n_copy.start = round(n_copy.start + shift, 4)

            swung.append(n_copy)
        return swung

    @staticmethod
    def apply_micro_timing_humanization(
        notes: List[NoteEvent],
        humanize_ms: float = 6.0,
        tempo: float = 120.0
    ) -> List[NoteEvent]:
        """
        Applies deterministic organic humanization (+/- ms) and subtle velocity fluctuations
        to eliminate robotic DAW rigidity while locking downbeat kicks.
        """
        ms_per_beat = 60000.0 / tempo
        max_beat_offset = (humanize_ms / ms_per_beat)

        humanized = []
        for n in notes:
            n_copy = copy.deepcopy(n)
            # Preserve beat 1.0 kick anchors strictly locked
            if n_copy.pitch == 36 and (n_copy.start % 4.0 == 0.0):
                humanized.append(n_copy)
                continue

            seed = int((n_copy.start * 1000) + n_copy.pitch) % 100
            offset = ((seed / 50.0) - 1.0) * max_beat_offset
            vel_jitter = int((seed % 7) - 3)

            n_copy.start = max(0.0, round(n_copy.start + offset, 4))
            n_copy.velocity = max(1, min(127, n_copy.velocity + vel_jitter))
            humanized.append(n_copy)

        return humanized

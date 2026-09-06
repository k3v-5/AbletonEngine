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
    CUMBIA = "cumbia"
    AFROBEAT = "afrobeat"
    EDM = "edm"
    DRUM_AND_BASS = "drum_and_bass"
    POP = "pop"
    ROCK = "rock"


class GenreRhythmGrooveEngine:
    """
    Procedural rhythm generator with genre-authentic pocket and groove templates.
    FEATURE STATUS: EXPERIMENTAL (OFF BY DEFAULT).
    This engine is dormant and strictly optional. The standard/custom workflow is preserved.
    """
    IS_EXPERIMENTAL: bool = True
    ENABLED_BY_DEFAULT: bool = False

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
        if isinstance(genre, GenreDrumStyle):
            style = genre
        else:
            g_clean = str(genre).lower().strip().replace("-", "_").replace(" ", "_")
            try:
                style = GenreDrumStyle(g_clean)
            except ValueError:
                if "cumbia" in g_clean or "guira" in g_clean:
                    style = GenreDrumStyle.CUMBIA
                elif "trap" in g_clean or "hip_hop" in g_clean or "hiphop" in g_clean:
                    style = GenreDrumStyle.TRAP
                elif "rock" in g_clean or "indie" in g_clean:
                    style = GenreDrumStyle.ROCK
                elif "afro" in g_clean or "dancehall" in g_clean:
                    style = GenreDrumStyle.AFROBEAT
                elif "dnb" in g_clean or "drum_and_bass" in g_clean or "jungle" in g_clean:
                    style = GenreDrumStyle.DRUM_AND_BASS
                elif "edm" in g_clean or "festival" in g_clean or "big_room" in g_clean:
                    style = GenreDrumStyle.EDM
                elif "house" in g_clean:
                    style = GenreDrumStyle.HOUSE
                elif "soul" in g_clean or "rnb" in g_clean:
                    style = GenreDrumStyle.NEO_SOUL
                elif "reggaeton" in g_clean or "latin" in g_clean or "dembow" in g_clean:
                    style = GenreDrumStyle.REGGAETON
                elif "synth" in g_clean or "80s" in g_clean or "retro" in g_clean:
                    style = GenreDrumStyle.SYNTHWAVE
                elif "boom" in g_clean or "rap" in g_clean:
                    style = GenreDrumStyle.BOOM_BAP
                elif "techno" in g_clean:
                    style = GenreDrumStyle.TECHNO
                elif "pop" in g_clean:
                    style = GenreDrumStyle.POP
                else:
                    style = GenreDrumStyle.TRAP

        generator_map = {
            GenreDrumStyle.TRAP: cls._generate_trap,
            GenreDrumStyle.HOUSE: cls._generate_house,
            GenreDrumStyle.NEO_SOUL: cls._generate_neo_soul,
            GenreDrumStyle.REGGAETON: cls._generate_reggaeton,
            GenreDrumStyle.SYNTHWAVE: cls._generate_synthwave,
            GenreDrumStyle.BOOM_BAP: cls._generate_boom_bap,
            GenreDrumStyle.TECHNO: cls._generate_techno,
            GenreDrumStyle.CUMBIA: cls._generate_cumbia,
            GenreDrumStyle.AFROBEAT: cls._generate_afrobeat,
            GenreDrumStyle.EDM: cls._generate_edm,
            GenreDrumStyle.DRUM_AND_BASS: cls._generate_drum_and_bass,
            GenreDrumStyle.POP: cls._generate_pop,
            GenreDrumStyle.ROCK: cls._generate_rock,
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

    @classmethod
    def _generate_cumbia(cls, length_bars: int) -> List[NoteEvent]:
        """
        Cumbia Latina / Sonidera / Electrocumbia pattern:
        - Continuous 16th Güira scrape pattern with iconic syncopated accent on the 3rd sixteenth ("ch-ch-CHII-ka")
        - Walking/syncopated Kick on beats 1 and 3 (0.0, 2.0) with pickup
        - Conga tumbao: slap on beat 2 & 4 (1.0, 3.0) and double open tones on 1.5 & 3.5
        - Timbal fill on bar 4 turnaround
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # 1. Kick on 1 and 3 (0.0, 2.0)
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.25, velocity=115))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.0, duration=0.25, velocity=112))
            if bar % 2 == 1:
                # Syncopated cumbia kick pickup
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 3.75, duration=0.20, velocity=98))

            # 2. Güira continua raspada (16th notes: down, up, long accented stroke, release)
            # Step 0: down (70), Step 1: up (80), Step 2: ACCENT (118), Step 3: soft (50)
            guira_vels = [70, 80, 118, 50]
            for beat in range(4):
                for step in range(4):
                    t = bar_start + beat * 1.0 + step * 0.25
                    notes.append(NoteEvent(
                        pitch=cls.CLOSED_HAT_PITCH,
                        start=t,
                        duration=0.18 if step == 2 else 0.10,
                        velocity=guira_vels[step]
                    ))

            # 3. Congas / Percussion Tumbao
            # Slap on beats 2 & 4 (1.0, 3.0)
            notes.append(NoteEvent(pitch=cls.PERC_PITCH, start=bar_start + 1.0, duration=0.15, velocity=105))
            notes.append(NoteEvent(pitch=cls.PERC_PITCH, start=bar_start + 3.0, duration=0.15, velocity=108))
            # Open tones (Low / High Tom) on contratiempos (1.5, 1.75, 3.5, 3.75)
            notes.append(NoteEvent(pitch=cls.LOW_TOM, start=bar_start + 1.50, duration=0.22, velocity=92))
            notes.append(NoteEvent(pitch=cls.HIGH_TOM, start=bar_start + 1.75, duration=0.20, velocity=95))
            notes.append(NoteEvent(pitch=cls.LOW_TOM, start=bar_start + 3.50, duration=0.22, velocity=94))
            notes.append(NoteEvent(pitch=cls.HIGH_TOM, start=bar_start + 3.75, duration=0.20, velocity=96))

            # 4. Timbal / Rim accents (or fill on last bar)
            if bar == length_bars - 1:
                # Timbal turnaround fill on beat 3.0 to 4.0
                timbal_steps = [3.0, 3.25, 3.5, 3.667, 3.833]
                for ts in timbal_steps:
                    notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + ts, duration=0.12, velocity=118))
            else:
                # Subtle cascara / timbal rim tap on 1.0 and 3.0
                notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.0, duration=0.15, velocity=88))
                notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.0, duration=0.15, velocity=92))

        return notes

    @classmethod
    def _generate_rock(cls, length_bars: int) -> List[NoteEvent]:
        """
        Modern / Indie / Alternative Rock pattern:
        - Solid driving Kick on 1 and 3 (0.0, 2.0) with pickup kicks on alternate bars
        - High-velocity Snare crack on 2 and 4 (1.0, 3.0) with natural stick impact
        - Relentless 8th-note Hi-Hats / Ride with accents on the downbeats
        - Crash cymbal on bar 1 downbeat and turnaround
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # Crash on first downbeat or turnaround
            if bar == 0 or bar == length_bars - 1:
                notes.append(NoteEvent(pitch=cls.OPEN_HAT_PITCH, start=bar_start + 0.0, duration=0.50, velocity=124))

            # Kick on 1 and 3
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.28, velocity=125))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.0, duration=0.28, velocity=122))
            if bar % 2 == 1:
                # Dynamic rock kick pickup on 2.5 or 3.5
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.5, duration=0.22, velocity=108))

            # Aggressive Snare on 2 and 4
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.0, duration=0.25, velocity=126))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.0, duration=0.25, velocity=127))

            # 8th-note Hi-Hats (heavy on downbeats, lighter on '&'s)
            for s in range(8):
                t = bar_start + s * 0.5
                v = 105 if s % 2 == 0 else 82
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=t, duration=0.20, velocity=v))

            # Last bar turnaround fill on toms/snare
            if bar == length_bars - 1:
                notes.append(NoteEvent(pitch=cls.HIGH_TOM, start=bar_start + 3.25, duration=0.15, velocity=115))
                notes.append(NoteEvent(pitch=cls.MID_TOM, start=bar_start + 3.50, duration=0.15, velocity=118))
                notes.append(NoteEvent(pitch=cls.LOW_TOM, start=bar_start + 3.75, duration=0.15, velocity=122))

        return notes

    @classmethod
    def _generate_afrobeat(cls, length_bars: int) -> List[NoteEvent]:
        """
        Afrobeat / Afropop / Urban Dancehall pattern:
        - Syncopated cross-rhythm Kick (0.0, 1.75, 2.5)
        - Crisp rimshot / snare accents (1.5, 2.75, 3.5)
        - Grooving 16th shaker / hat wave with African syncopation
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # Syncopated Kick
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.25, velocity=118))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 1.75, duration=0.22, velocity=106))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.50, duration=0.25, velocity=112))

            # Rimshot / Snare cross-rhythm
            rim_offsets = [1.50, 2.75, 3.50]
            for ro in rim_offsets:
                notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + ro, duration=0.18, velocity=110))

            # Percussion / Conga syncopation
            notes.append(NoteEvent(pitch=cls.PERC_PITCH, start=bar_start + 0.75, duration=0.15, velocity=92))
            notes.append(NoteEvent(pitch=cls.PERC_PITCH, start=bar_start + 2.25, duration=0.15, velocity=95))

            # 16th Shaker / Closed Hat wave
            shaker_vels = [90, 60, 75, 55, 85, 58, 72, 52, 92, 62, 78, 54, 88, 58, 75, 50]
            for s in range(16):
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.25, duration=0.15, velocity=shaker_vels[s]))

        return notes

    @classmethod
    def _generate_edm(cls, length_bars: int) -> List[NoteEvent]:
        """
        EDM / Festival Big Room pattern:
        - 4-on-the-floor heavy kick at maximum impact
        - Clap/Snare on 2 and 4 (1.0, 3.0)
        - Offbeat Open Hi-Hat (0.5, 1.5, 2.5, 3.5)
        - Fast driving 16th hats with build
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # 4-on-the-floor kick
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + b * 1.0, duration=0.25, velocity=125))

            # Clap on 2 and 4
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 1.0, duration=0.22, velocity=118))
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 3.0, duration=0.22, velocity=120))

            # Offbeat open hat
            for b in range(4):
                notes.append(NoteEvent(pitch=cls.OPEN_HAT_PITCH, start=bar_start + b * 1.0 + 0.5, duration=0.30, velocity=102))

            # 16th closed hats
            for s in range(16):
                if s % 4 != 2:
                    notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.25, duration=0.12, velocity=75 if s % 2 == 0 else 60))

        return notes

    @classmethod
    def _generate_drum_and_bass(cls, length_bars: int) -> List[NoteEvent]:
        """
        Drum & Bass 2-step breakbeat pattern (170-175 BPM):
        - Kick on 0.0 and syncopated pickup at 2.75
        - Snare crack on 1.0 and 3.0
        - Fast 16th hats and ghost snares (vel ~40)
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # 2-step kick
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.22, velocity=124))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.75, duration=0.20, velocity=116))

            # Snare on 2 and 4
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.0, duration=0.25, velocity=125))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.0, duration=0.25, velocity=127))

            # Ghost snares for DnB groove
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 1.75, duration=0.12, velocity=45))
            notes.append(NoteEvent(pitch=cls.SNARE_PITCH, start=bar_start + 3.50, duration=0.12, velocity=42))

            # Relentless 16th hats
            for s in range(16):
                v = 95 if s % 4 == 0 else (75 if s % 2 == 0 else 60)
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.25, duration=0.14, velocity=v))

        return notes

    @classmethod
    def _generate_pop(cls, length_bars: int) -> List[NoteEvent]:
        """
        Commercial / Latin Pop pattern:
        - Modern radio pocket: Kick on 0.0, 1.75, 2.0
        - Clean Clap/Snare on 1.0 and 3.0
        - Polished 8th/16th hats with dynamic accentuation
        """
        notes = []
        for bar in range(length_bars):
            bar_start = bar * 4.0

            # Pocket kick
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 0.0, duration=0.25, velocity=118))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 1.75, duration=0.20, velocity=102))
            notes.append(NoteEvent(pitch=cls.KICK_PITCH, start=bar_start + 2.0, duration=0.25, velocity=114))

            # Clap/Snare on 2 and 4
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 1.0, duration=0.22, velocity=112))
            notes.append(NoteEvent(pitch=cls.CLAP_PITCH, start=bar_start + 3.0, duration=0.22, velocity=114))

            # Dynamic 8th hats
            for s in range(8):
                v = 90 if s % 2 == 0 else 70
                notes.append(NoteEvent(pitch=cls.CLOSED_HAT_PITCH, start=bar_start + s * 0.5, duration=0.18, velocity=v))

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

    @classmethod
    def offer_genre_options(cls, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Offers structured production options grouped by genre categories:
        - Rap & Trap (Trap, Boom-Bap)
        - Cumbia (Cumbia Latina / Sonidera / Electrocumbia)
        - Electro (House, Techno, Synthwave, EDM, Drum & Bass)
        - Urbana & Pop (Reggaeton, Afrobeat, Pop Comercial)
        - Rock (Rock Moderno / Indie)

        IMPORTANT: These options are an optional creative accelerator, NOT a limitation.
        Custom and freeform workflows are fully preserved and respected.
        """
        all_catalog = {
            "rap_trap": {
                "category_title": "Rap & Trap",
                "genres": {
                    "trap": {
                        "name": "Modern Trap / Hip-Hop",
                        "bpm_default": 140.0,
                        "bpm_range": [130.0, 165.0],
                        "groove": "Syncopated 808 kick, clap on beat 3 (half-time), dynamic triplet hi-hat rolls (1/12 and 1/24) with velocity ramps.",
                        "recommended_roles": ["bass (808)", "drums", "lead", "keys", "pad"],
                        "target_lufs": -7.5
                    },
                    "boom_bap": {
                        "name": "Boom-Bap / 90s Golden Era Rap",
                        "bpm_default": 92.0,
                        "bpm_range": [85.0, 98.0],
                        "groove": "Classic MPC swing (58-62%), behind-the-beat snare crack on 2 & 4, chopped sample pocket, kick pickups.",
                        "recommended_roles": ["drums", "bass", "keys (rhodes)", "horns", "scratch_fx"],
                        "target_lufs": -9.0
                    }
                }
            },
            "cumbia": {
                "category_title": "Cumbia & Ritmos Latinos",
                "genres": {
                    "cumbia": {
                        "name": "Cumbia Latina / Sonidera / Electrocumbia",
                        "bpm_default": 92.0,
                        "bpm_range": [85.0, 105.0],
                        "groove": "Güira continua 16th con acento sincopado en la 3ra semicorchea ('ch-ch-CHII-ka'), conga tumbao y slap en tiempos 2 & 4, bajo caminado sincopado, timbales con remates.",
                        "recommended_roles": ["percussion (güira)", "congas_tumbao", "bass (caminado)", "keys (piano/acordeón)", "lead_synth"],
                        "target_lufs": -8.0
                    }
                }
            },
            "electro": {
                "category_title": "Electro de Todo Tipo",
                "genres": {
                    "house": {
                        "name": "House / Tech House / Deep House",
                        "bpm_default": 126.0,
                        "bpm_range": [122.0, 130.0],
                        "groove": "Four-on-the-floor kick, offbeat open hat (0.5, 1.5, 2.5, 3.5), clap on 2 & 4, 16th closed hat pocket con swing MPC.",
                        "recommended_roles": ["drums", "bass", "lead", "pad", "fx"],
                        "target_lufs": -6.5
                    },
                    "techno": {
                        "name": "Techno / Peak-Time / Melodic",
                        "bpm_default": 132.0,
                        "bpm_range": [128.0, 142.0],
                        "groove": "Driving industrial rumble kick 4/4, relentless 16th open/closed hat patterns, percussive synth stabs.",
                        "recommended_roles": ["drums", "sub_rumble", "synth_stab", "noise_fx", "lead"],
                        "target_lufs": -6.0
                    },
                    "synthwave": {
                        "name": "Synthwave / Outrun / 80s Retro",
                        "bpm_default": 115.0,
                        "bpm_range": [100.0, 125.0],
                        "groove": "Driving kick on 1 & 3, massive gated snare on 2 & 4, running 16th hats, bass arpeggiator rolling octave pocket.",
                        "recommended_roles": ["bass (arp)", "lead", "pad", "drums", "keys"],
                        "target_lufs": -8.5
                    },
                    "edm": {
                        "name": "EDM / Festival Big Room / Progressive",
                        "bpm_default": 128.0,
                        "bpm_range": [125.0, 132.0],
                        "groove": "Heavy impact 4-on-the-floor kick, wide layered claps on 2 & 4, offbeat open hat, massive supersaw sidechain.",
                        "recommended_roles": ["drums", "supersaw_lead", "sub_bass", "white_noise_riser", "chords"],
                        "target_lufs": -6.0
                    },
                    "drum_and_bass": {
                        "name": "Drum & Bass / Liquid / Jungle",
                        "bpm_default": 174.0,
                        "bpm_range": [170.0, 178.0],
                        "groove": "Fast 2-step breakbeat (kick at 0.0 & 2.75, snare at 1.0 & 3.0), rolling ghost snares, reese sub bass.",
                        "recommended_roles": ["drums", "reese_bass", "sub_bass", "pad", "arp"],
                        "target_lufs": -6.5
                    }
                }
            },
            "urbano_pop": {
                "category_title": "Música Urbana & Pop",
                "genres": {
                    "reggaeton": {
                        "name": "Reggaetón / Dembow Urbano",
                        "bpm_default": 94.0,
                        "bpm_range": [88.0, 100.0],
                        "groove": "4-on-the-floor kick con caja sincopada Dembow en 0.75, 1.5, 2.75, 3.5. Sub bass redondo con amplio espacio vocal.",
                        "recommended_roles": ["drums", "bass (sub 808)", "keys", "lead_vocal", "synth_pluck"],
                        "target_lufs": -7.5
                    },
                    "afrobeat": {
                        "name": "Afrobeat / Afropop / Dancehall",
                        "bpm_default": 102.0,
                        "bpm_range": [95.0, 108.0],
                        "groove": "Kick con síncopa africana (0.0, 1.75, 2.5), rimshots cruzados (1.5, 2.75, 3.5), shaker 16ths orgánico y percusión polirrítmica.",
                        "recommended_roles": ["drums", "bass", "guitar_skank", "keys", "percussion (shekere/congas)"],
                        "target_lufs": -8.0
                    },
                    "pop": {
                        "name": "Commercial Pop / Latin Pop",
                        "bpm_default": 122.0,
                        "bpm_range": [112.0, 128.0],
                        "groove": "Radio pocket: kick dinámico (0.0, 1.75, 2.0), clap/snare definido en 2 & 4, hi-hats pulidos con articulación de volumen.",
                        "recommended_roles": ["drums", "bass", "keys (rhodes/piano)", "lead_synth", "pad", "guitar"],
                        "target_lufs": -8.0
                    }
                }
            },
            "rock": {
                "category_title": "Rock (Moderno & Indie)",
                "genres": {
                    "rock": {
                        "name": "Modern Rock / Indie Rock / Alternative",
                        "bpm_default": 128.0,
                        "bpm_range": [110.0, 145.0],
                        "groove": "Batería acústica potente: kick sólido en 1 & 3 con pickups dinámicos, golpe seco y agresivo de tarola en 2 & 4, hi-hats/ride continuos en corcheas (8ths), crash en compás 1.",
                        "recommended_roles": ["drums (acoustic kit)", "bass (distorted/drive)", "guitar_rhythm", "guitar_lead", "keys/organ"],
                        "target_lufs": -8.5
                    }
                }
            }
        }

        if category:
            cat_clean = category.lower().strip()
            for k, v in all_catalog.items():
                if cat_clean in k or cat_clean in v["category_title"].lower():
                    return {
                        "status": "success",
                        "filter": category,
                        "catalog": {k: v},
                        "notice": "Estas opciones son una sugerencia/extra creativo del motor para la IA; el flujo de producción libre o personalizado se respeta por completo sin restricciones."
                    }

        return {
            "status": "success",
            "categories_available": list(all_catalog.keys()),
            "catalog": all_catalog,
            "notice": "Estas opciones son un extra y catalizador creativo para la IA. Todo flujo personalizado o no catalogado sigue siendo 100% válido y soportado por el motor."
        }

    @classmethod
    def get_genre_descriptor(cls, genre: str) -> Dict[str, Any]:
        """Returns the specific production profile descriptor for a genre."""
        g_clean = genre.lower().strip()
        catalog = cls.offer_genre_options()["catalog"]
        for cat_data in catalog.values():
            for g_key, g_val in cat_data["genres"].items():
                if g_key in g_clean or g_clean in g_key:
                    return {
                        "status": "found",
                        "genre_id": g_key,
                        "profile": g_val
                    }
        # Fallback default
        return {
            "status": "custom",
            "genre_id": g_clean,
            "profile": {
                "name": f"Custom / Freeform ({genre})",
                "bpm_default": 120.0,
                "bpm_range": [60.0, 200.0],
                "groove": "Libre / personalizable según la intención creativa de la IA.",
                "recommended_roles": ["drums", "bass", "keys", "lead"],
                "target_lufs": -9.0
            }
        }

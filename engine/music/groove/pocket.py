# engine/music/groove/pocket.py
"""
Groove Pocket Engine:
Advanced genre-specific micro-timing, swing, humanization budgets, and chord strumming.
Replaces robotic 100% quantization with authentic physiological and genre-defined pockets.
"""

from enum import Enum
import random
import math
from typing import List, Dict, Any, Optional, Union
from ..models import NoteEvent


class PocketStyle(str, Enum):
    ATLANTA_TRAP = "atlanta_trap"
    NEO_SOUL_DILLA = "neo_soul_dilla"
    BOOM_BAP = "boom_bap"
    DARK_RAGE = "dark_rage"
    FRENCH_PUMP = "french_pump"
    ORGANIC_HUMAN = "organic_human"


# Budget per role: (offset_ms_mean, jitter_ms_std)
ROLE_POCKET_BUDGETS: Dict[PocketStyle, Dict[str, tuple]] = {
    PocketStyle.ATLANTA_TRAP: {
        "kick": (0.0, 1.2),           # Locked punch
        "sub_bass": (4.0, 2.0),       # Dragging 808
        "bass": (3.5, 2.0),
        "snare": (8.0, 2.5),          # Laid-back snap
        "clap": (8.0, 2.5),
        "hihat": (1.0, 3.5),          # Rolling with micro-triplet bias
        "hat_closed": (1.0, 3.0),
        "hat_open": (3.0, 4.0),
        "percussion": (6.0, 5.0),
        "piano": (3.0, 2.5),
        "lead": (2.0, 3.0),
        "chords": (2.0, 2.0),
    },
    PocketStyle.NEO_SOUL_DILLA: {
        "kick": (-2.5, 3.5),          # Pushing ahead
        "sub_bass": (6.0, 4.5),       # Drunken late bass
        "bass": (6.0, 4.5),
        "snare": (12.0, 5.0),         # Heavy delayed backbeat
        "clap": (11.0, 4.5),
        "hihat": (4.0, 6.0),          # Organic unquantized swing
        "hat_closed": (3.5, 5.0),
        "hat_open": (5.0, 6.0),
        "percussion": (8.0, 7.0),
        "piano": (5.0, 4.0),          # Laid-back chord strums
        "lead": (4.0, 4.5),
        "chords": (5.0, 4.0),
    },
    PocketStyle.BOOM_BAP: {
        "kick": (0.0, 2.0),
        "sub_bass": (2.0, 2.5),
        "bass": (2.0, 2.5),
        "snare": (5.0, 3.0),
        "clap": (5.0, 3.0),
        "hihat": (2.0, 4.0),
        "hat_closed": (2.0, 3.5),
        "hat_open": (3.0, 4.0),
        "percussion": (4.0, 5.0),
        "piano": (1.5, 2.5),
        "lead": (1.0, 2.0),
        "chords": (1.5, 2.5),
    },
    PocketStyle.DARK_RAGE: {
        "kick": (0.0, 0.8),           # Laser locked
        "sub_bass": (1.5, 1.2),
        "bass": (1.5, 1.2),
        "snare": (3.0, 1.5),
        "clap": (3.0, 1.5),
        "hihat": (-1.0, 2.0),         # Pushing driving energy
        "hat_closed": (-1.0, 2.0),
        "hat_open": (1.0, 2.5),
        "percussion": (3.0, 3.0),
        "piano": (1.0, 1.5),
        "lead": (0.0, 1.5),
        "chords": (1.0, 1.5),
    },
    PocketStyle.FRENCH_PUMP: {
        "kick": (0.0, 0.5),           # Hard quantized 4-on-the-floor
        "sub_bass": (2.0, 1.5),       # Tight French sidechain feel
        "bass": (2.0, 1.5),
        "snare": (2.0, 1.5),
        "clap": (2.0, 1.5),
        "hihat": (1.5, 2.5),          # Micro-pushed 16th hats
        "hat_closed": (1.5, 2.0),
        "hat_open": (2.5, 2.5),
        "percussion": (2.0, 3.0),
        "piano": (1.5, 2.0),
        "lead": (1.0, 1.8),
        "chords": (1.0, 1.5),
    },
    PocketStyle.ORGANIC_HUMAN: {
        "kick": (0.0, 2.5),
        "sub_bass": (2.0, 3.0),
        "bass": (2.0, 3.0),
        "snare": (5.0, 4.0),
        "clap": (5.0, 4.0),
        "hihat": (3.0, 5.0),
        "hat_closed": (3.0, 4.5),
        "hat_open": (4.0, 5.5),
        "percussion": (6.0, 6.0),
        "piano": (4.0, 4.0),
        "lead": (3.0, 3.5),
        "chords": (3.0, 3.5),
    }
}


class GroovePocketEngine:
    """Orchestrates musical micro-timing, genre swing, and chord humanization."""

    @classmethod
    def producer_to_pocket_style(cls, producer_name: Optional[str]) -> PocketStyle:
        """Maps a producer name or stylistic prompt to a canonical PocketStyle."""
        name = str(producer_name or "").lower()
        if "dilla" in name or "soul" in name:
            return PocketStyle.NEO_SOUL_DILLA
        elif "metro" in name or "boomin" in name or "trap" in name:
            return PocketStyle.ATLANTA_TRAP
        elif "daft" in name or "punk" in name or "french" in name or "house" in name:
            return PocketStyle.FRENCH_PUMP
        elif "dean" in name or "rage" in name or "travis" in name:
            return PocketStyle.DARK_RAGE
        elif "bap" in name or "vinyl" in name or "lofi" in name or "lo-fi" in name:
            return PocketStyle.BOOM_BAP
        return PocketStyle.ORGANIC_HUMAN

    POCKET_LEVEL_SCALERS: Dict[int, float] = {
        1: 0.20,  # Level 1: Ultra subtle
        2: 0.45,  # Level 2: Sutil Natural (Default)
        3: 0.70,  # Level 3: Moderado Expresivo
        4: 0.90,  # Level 4: Pronunciado Neo-Soul / Funk
        5: 1.25,  # Level 5: Brusco Agradable / Dilla Time Slip
    }

    # Deterministic micro push/pull per role (base offsets in ms)
    ROLE_MICRO_PUSH_PULL_MS: Dict[str, float] = {
        "snare": 8.0,        # Lazy snare behind the beat
        "SNARE": 8.0,
        "clap": 7.5,
        "CLAP": 7.5,
        "hihat": -3.0,       # Rushed hats ahead of the beat (urgency)
        "HIHAT": -3.0,
        "hi_hats": -3.0,
        "HI_HATS": -3.0,
        "hat_closed": -2.5,
        "hat_open": -1.0,
        "sub_bass": 4.5,     # Dragging 808/sub-bass
        "SUB_BASS": 4.5,
        "bass": 4.0,
        "BASS": 4.0,
        "808": 4.5,
        "percussion": 3.0,
        "PERCUSSION": 3.0,
        "kick": 0.0,         # Absolute grid lock
        "KICK": 0.0,
    }

    @classmethod
    def clamp_ghost_note_velocity(cls, accent_velocity: int, candidate_velocity: int) -> int:
        """Clamps ghost note velocity strictly between 35% and 45% of peak accent velocity."""
        min_v = int(round(accent_velocity * 0.35))
        max_v = int(round(accent_velocity * 0.45))
        return max(min_v, min(max_v, candidate_velocity))

    @classmethod
    def apply_pocket_by_level(
        cls,
        notes: List[NoteEvent],
        level: int = 2,
        role: str = "drums",
        pocket_style: Union[PocketStyle, str] = PocketStyle.ATLANTA_TRAP,
        tempo: float = 120.0,
        bpm: Optional[float] = None,
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Applies parameterized micro-timing pocket matching the 5 discrete humanization levels.
        Scales deterministic push/pull (lazy snare, rushed hats, dragging 808) and ghost note dynamics.
        """
        if not notes:
            return []
        effective_tempo = bpm if bpm is not None else tempo
        clamped_level = max(1, min(5, int(level)))
        scaler = cls.POCKET_LEVEL_SCALERS.get(clamped_level, 0.45)
        return cls.apply_pocket_to_notes(
            notes=notes,
            role=role,
            pocket_style=pocket_style,
            tempo=effective_tempo,
            strength=scaler,
            seed=seed
        )

    @classmethod
    def apply_pocket_to_notes(
        cls,
        notes: List[NoteEvent],
        role: str = "lead",
        pocket_style: Union[PocketStyle, str] = PocketStyle.ATLANTA_TRAP,
        tempo: float = 120.0,
        strength: float = 1.0,
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Applies role-specific micro-timing displacement, velocity variance,
        and swing to NoteEvents based on genre pocket physics and deterministic push/pull.
        """
        if strength <= 0.0 or not notes:
            return [NoteEvent(**n.__dict__) for n in notes]

        style = PocketStyle(pocket_style) if isinstance(pocket_style, str) else pocket_style
        budgets = ROLE_POCKET_BUDGETS.get(style, ROLE_POCKET_BUDGETS[PocketStyle.ORGANIC_HUMAN])

        role_clean = role.lower().replace("-", "_").replace(" ", "_")
        mean_offset_ms, std_jitter_ms = budgets.get(role_clean, (2.0, 3.0))

        # Use deterministic role push/pull if explicitly defined for this role
        if role_clean in cls.ROLE_MICRO_PUSH_PULL_MS:
            mean_offset_ms = cls.ROLE_MICRO_PUSH_PULL_MS[role_clean]

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        rng = random.Random(seed)
        pocketed: List[NoteEvent] = []

        # Detect max velocity to calculate proportional ghost note ratio
        max_vel = max((n.velocity for n in notes), default=100)

        for note in notes:
            # Velocity-correlated jitter: louder notes are more accurately timed
            vel_norm = note.velocity / 127.0
            jitter_scale = (1.4 - vel_norm * 0.6) * strength

            offset_ms = (mean_offset_ms * strength) + rng.gauss(0.0, std_jitter_ms * jitter_scale)
            offset_beats = offset_ms * beats_per_ms

            # Organic velocity variance (+/- 4 to 8 units)
            vel_jitter = int(rng.gauss(0.0, 5.0 * strength))
            new_vel = max(1, min(127, note.velocity + vel_jitter))

            # Ghost note dynamic ratio: strictly 35% to 45% of peak accent
            if note.velocity <= 55 or note.accent < -0.3:
                target_ghost_ratio = 0.38 + rng.uniform(-0.03, 0.03) * strength
                new_vel = max(15, min(65, int(max_vel * target_ghost_ratio)))

            # Duration subtle variance (+/- 3%)
            dur_scale = 1.0 + rng.uniform(-0.03, 0.03) * strength
            new_dur = max(0.05, note.duration * dur_scale)

            new_start = max(0.0, note.start + offset_beats)

            pocketed.append(NoteEvent(
                pitch=note.pitch,
                pitch_class=note.pitch_class,
                octave=note.octave,
                start=round(new_start, 5),
                duration=round(new_dur, 5),
                velocity=new_vel,
                channel=note.channel,
                probability=note.probability,
                accent=note.accent,
                mute=note.mute
            ))

        return pocketed

    @staticmethod
    def apply_chord_strum(
        notes: List[NoteEvent],
        tempo: float = 120.0,
        strum_ms: float = 12.0,
        direction: str = "up",
        velocity_tilt: float = 0.15,
        tolerance_beats: float = 0.04,
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Groups simultaneous notes into chords and spreads note start times
        with natural human strumming (finger roll) and velocity contour.
        """
        if not notes or strum_ms <= 0.0:
            return [NoteEvent(**n.__dict__) for n in notes]

        rng = random.Random(seed)
        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        # 1. Group notes by start time within tolerance window
        sorted_notes = sorted(notes, key=lambda n: n.start)
        chord_clusters: List[List[NoteEvent]] = []
        curr_cluster: List[NoteEvent] = []

        for note in sorted_notes:
            if not curr_cluster:
                curr_cluster.append(note)
            else:
                if abs(note.start - curr_cluster[0].start) <= tolerance_beats:
                    curr_cluster.append(note)
                else:
                    chord_clusters.append(curr_cluster)
                    curr_cluster = [note]
        if curr_cluster:
            chord_clusters.append(curr_cluster)

        strummed_notes: List[NoteEvent] = []

        # 2. Apply strum spread per chord
        for cluster in chord_clusters:
            if len(cluster) <= 1:
                strummed_notes.extend(cluster)
                continue

            # Sort cluster by pitch (ascending)
            ordered = sorted(cluster, key=lambda n: n.pitch, reverse=(direction.lower() == "down"))
            n_notes = len(ordered)
            base_start = ordered[0].start

            for i, note in enumerate(ordered):
                # Strum offset for this voice
                spread_ms = (i * strum_ms) + rng.gauss(0.0, 1.5)
                voice_offset_beats = spread_ms * beats_per_ms
                new_start = base_start + voice_offset_beats

                # Velocity tilt: higher notes in roll receive dynamic emphasis
                tilt_factor = 1.0 + (i / max(1, n_notes - 1) - 0.5) * velocity_tilt
                new_vel = max(1, min(127, int(round(note.velocity * tilt_factor))))

                strummed_notes.append(NoteEvent(
                    pitch=note.pitch,
                    pitch_class=note.pitch_class,
                    octave=note.octave,
                    start=round(new_start, 5),
                    duration=max(0.05, round(note.duration - voice_offset_beats, 5)),
                    velocity=new_vel,
                    channel=note.channel,
                    probability=note.probability,
                    accent=note.accent,
                    mute=note.mute
                ))

        return sorted(strummed_notes, key=lambda n: n.start)


# Module-level convenience aliases
POCKET_LEVEL_SCALERS = GroovePocketEngine.POCKET_LEVEL_SCALERS
ROLE_MICRO_PUSH_PULL_MS = GroovePocketEngine.ROLE_MICRO_PUSH_PULL_MS

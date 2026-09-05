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

    @staticmethod
    def apply_pocket_to_notes(
        notes: List[NoteEvent],
        role: str = "lead",
        pocket_style: Union[PocketStyle, str] = PocketStyle.ATLANTA_TRAP,
        tempo: float = 120.0,
        strength: float = 1.0,
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Applies role-specific micro-timing displacement, velocity variance,
        and swing to NoteEvents based on genre pocket physics.
        """
        if strength <= 0.0 or not notes:
            return [NoteEvent(**n.__dict__) for n in notes]

        style = PocketStyle(pocket_style) if isinstance(pocket_style, str) else pocket_style
        budgets = ROLE_POCKET_BUDGETS.get(style, ROLE_POCKET_BUDGETS[PocketStyle.ORGANIC_HUMAN])

        role_clean = role.lower().replace("-", "_").replace(" ", "_")
        mean_offset_ms, std_jitter_ms = budgets.get(role_clean, (2.0, 3.0))

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        rng = random.Random(seed)
        pocketed: List[NoteEvent] = []

        for note in notes:
            # Velocity-correlated jitter: louder notes are more accurately timed
            vel_norm = note.velocity / 127.0
            jitter_scale = (1.4 - vel_norm * 0.6) * strength

            offset_ms = (mean_offset_ms * strength) + rng.gauss(0.0, std_jitter_ms * jitter_scale)
            offset_beats = offset_ms * beats_per_ms

            # Organic velocity variance (+/- 4 to 8 units)
            vel_jitter = int(rng.gauss(0.0, 5.0 * strength))
            new_vel = max(1, min(127, note.velocity + vel_jitter))

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
                accent=note.accent
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
                    accent=note.accent
                ))

        return sorted(strummed_notes, key=lambda n: n.start)

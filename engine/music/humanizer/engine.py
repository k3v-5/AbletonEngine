# engine/music/humanizer/engine.py
import random
import math
from typing import List, Optional
from ..models import NoteEvent

# Milliseconds of jitter deviation per role
ROLE_TIMING_JITTER_MS = {
    "kick": 1.5,
    "bass": 3.0,
    "sub_bass": 2.0,
    "snare": 5.0,
    "clap": 5.0,
    "hihat": 7.0,
    "hat_closed": 6.0,
    "hat_open": 7.0,
    "percussion": 12.0,
    "foley": 14.0,
    "lead": 6.0,
    "chords": 4.0,
    "pad": 2.0
}

def humanize_notes(
    notes: List[NoteEvent],
    role: str = "lead",
    strength: float = 0.5,
    tempo: float = 120.0,
    seed: Optional[int] = 12345,
    profile_name: Optional[str] = None
) -> List[NoteEvent]:
    """
    Applies correlated physiological humanization to NoteEvents:
    - Micro-timing jitter is inversely correlated with note velocity.
    - Accents and ghost notes have differentiated variance.
    - Role-aware timing budgets prevent chaotic mud.
    - 100% deterministic reproducibility when seed is provided.
    """
    if profile_name:
        p_low = profile_name.lower()
        if p_low == "subtle": strength = 0.3 * strength
        elif p_low == "pocket": strength = 0.6 * strength
        elif p_low == "loose": strength = 1.0 * strength
    if strength <= 0.0:
        return [NoteEvent(**note.__dict__) for note in notes]

    rng = random.Random(seed)
    role_key = role.lower().replace("-", "_").replace(" ", "_")
    base_jitter_ms = ROLE_TIMING_JITTER_MS.get(role_key, 6.0)

    ms_per_beat = (60.0 / tempo) * 1000.0
    beats_per_ms = 1.0 / ms_per_beat

    humanized: List[NoteEvent] = []

    for note in notes:
        # Velocity correlation:
        # Notes with high velocity (>= 105) have tighter timing and slight anticipation (-1 to -3ms)
        # Ghost notes (<= 50) have wider timing jitter
        vel_norm = note.velocity / 127.0
        jitter_scaler = (1.5 - vel_norm) * strength

        jitter_ms = rng.gauss(0.0, base_jitter_ms * jitter_scaler)

        # High velocity anticipation
        if note.velocity > 105:
            jitter_ms -= (2.0 * strength)

        offset_beats = jitter_ms * beats_per_ms

        # Velocity jitter (3-8 units depending on strength)
        vel_jitter = int(rng.gauss(0.0, 7.0 * strength))
        new_velocity = max(1, min(127, note.velocity + vel_jitter))

        # Duration jitter (subtle +/- 3%)
        dur_jitter = 1.0 + rng.uniform(-0.04, 0.04) * strength
        new_duration = max(0.05, note.duration * dur_jitter)

        new_start = max(0.0, note.start + offset_beats)

        h_ev = NoteEvent(
            pitch=note.pitch,
            pitch_class=note.pitch_class,
            octave=note.octave,
            start=round(new_start, 5),
            duration=round(new_duration, 5),
            velocity=new_velocity,
            channel=note.channel,
            probability=note.probability,
            accent=note.accent
        )
        humanized.append(h_ev)

    return humanized

def apply_velocity_curve(
    notes: List[NoteEvent],
    curve_type: str = "accented",
    intensity: float = 0.5,
    start_vel: Optional[int] = None,
    end_vel: Optional[int] = None
) -> List[NoteEvent]:
    """Applies musical velocity contours (linear, exponential, accented, wave, phrase)"""
    if not notes:
        return []

    c_type = curve_type.lower()
    total_notes = len(notes)
    curved: List[NoteEvent] = []

    for idx, note in enumerate(notes):
        factor = idx / max(1, total_notes - 1)
        if start_vel is not None and end_vel is not None:
            new_vel = start_vel + factor * (end_vel - start_vel)
        else:
            new_vel = float(note.velocity)

            if c_type == "linear":
                # Crescendo from -15% to +15%
                delta = (factor - 0.5) * 30 * intensity
                new_vel += delta

            elif c_type == "exponential":
                # Steep swell toward the end
                delta = (factor ** 2.5) * 35 * intensity
                new_vel += delta

            elif c_type == "wave":
                # Sinusoidal breathing swell
                wave = math.sin(factor * math.pi * 2)
                new_vel += wave * 20 * intensity

            elif c_type == "accented":
                # Downbeats get extra velocity
                if note.start % 1.0 == 0.0:
                    new_vel += 18 * intensity
                elif note.start % 0.5 == 0.0:
                    new_vel += 8 * intensity

        curved.append(NoteEvent(
            pitch=note.pitch,
            pitch_class=note.pitch_class,
            octave=note.octave,
            start=note.start,
            duration=note.duration,
            velocity=max(1, min(127, int(new_vel))),
            channel=note.channel,
            probability=note.probability,
            accent=note.accent
        ))

    return curved

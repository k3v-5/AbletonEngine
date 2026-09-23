# engine/music/humanizer/engine.py
import random
import math
from typing import List, Optional, Dict, Any
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


class HumanizerEngine:
    """
    Humanizes velocity curves and micro-timing of note events to eliminate robotic grid feel.
    Supports both dict notes and NoteEvent objects.
    """

    WRIST_PATTERNS = {
        "standard_wrist": [110, 70, 85, 60],      # Primary accent, weak stroke, rebound, ghost
        "driving_funk": [115, 65, 95, 75],        # Heavy syncopation
        "laid_back_trap": [105, 60, 80, 55],      # Soft floating hi-hats
        "melodic_rubato": [100, 85, 95, 80]       # Natural expressive phrasing
    }

    @classmethod
    def apply_drummer_wrist_physics(
        cls,
        notes: List[Dict[str, Any]],
        pattern_name: str = "standard_wrist",
        custom_pattern: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Applies a 4-step drummer wrist velocity pattern to consecutive 16th-note steps.
        """
        pattern = custom_pattern or cls.WRIST_PATTERNS.get(pattern_name, cls.WRIST_PATTERNS["standard_wrist"])
        if not notes or not pattern:
            return notes

        humanized = []
        for n in notes:
            new_n = dict(n)
            t = float(n.get("start_time", n.get("time", n.get("start", 0.0))))
            sub_beat_idx = int(round((t % 1.0) * 4.0)) % len(pattern)
            target_base_vel = pattern[sub_beat_idx]
            
            subtle_var = random.randint(-4, 4)
            final_vel = max(1, min(127, target_base_vel + subtle_var))
            new_n["velocity"] = final_vel
            humanized.append(new_n)

        return humanized

    @classmethod
    def apply_microtiming(
        cls,
        notes: List[Dict[str, Any]],
        bpm: float = 120.0,
        jitter_ms: float = 8.0,
        role: str = "drums"
    ) -> List[Dict[str, Any]]:
        """
        Displaces note timings by +/- 5 to 15 ms converted to beats based on BPM.
        Applies role-specific groove pocketing (e.g. laid-back claps, rushed snares).
        """
        if not notes:
            return []

        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0
        r_upper = str(role or "").upper()

        role_pocket_ms = 0.0
        if "CLAP" in r_upper:
            role_pocket_ms = 8.0   # Laid-back clap (+8 ms behind grid)
        elif "SNARE" in r_upper:
            role_pocket_ms = -3.0  # Rushed snare (-3 ms pushing ahead)
        elif "HAT" in r_upper:
            role_pocket_ms = 4.0   # Relaxed hi-hat pocket

        humanized = []
        for n in notes:
            new_n = dict(n)
            cur_t = float(n.get("start_time", n.get("time", n.get("start", 0.0))))

            if "KICK" in r_upper and abs(cur_t % 4.0) < 0.02:
                random_ms = random.uniform(-1.5, 1.5)
            else:
                random_ms = random.uniform(-jitter_ms, jitter_ms)

            total_offset_ms = role_pocket_ms + random_ms
            offset_beats = total_offset_ms / ms_per_beat

            new_t = max(0.0, cur_t + offset_beats)
            new_n["start_time"] = round(new_t, 4)
            new_n["time"] = round(new_t, 4)
            humanized.append(new_n)

        return humanized

    @classmethod
    def humanize_clip(
        cls,
        notes: List[Dict[str, Any]],
        bpm: float = 120.0,
        role: str = "drums",
        humanize_velocity: bool = True,
        humanize_timing: bool = True
    ) -> List[Dict[str, Any]]:
        """Complete humanization pass over a clip's note events."""
        result = [dict(n) for n in notes]
        if humanize_velocity:
            result = cls.apply_drummer_wrist_physics(result)
        if humanize_timing:
            result = cls.apply_microtiming(result, bpm=bpm, jitter_ms=8.0, role=role)
        return result


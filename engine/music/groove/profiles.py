import json
from pathlib import Path
from typing import List, Dict, Any
import random
from ..models import NoteEvent

GROOVE_CONFIG_CACHE: Dict[str, Any] = {}

def get_groove_configuration() -> Dict[str, Any]:
    """Loads and caches groove profiles from config/groove_config.json."""
    global GROOVE_CONFIG_CACHE
    if not GROOVE_CONFIG_CACHE:
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "groove_config.json"
        if config_path.exists():
            try:
                GROOVE_CONFIG_CACHE = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                GROOVE_CONFIG_CACHE = {}
    return GROOVE_CONFIG_CACHE

GROOVE_SWING_RATIOS = {
    "straight": 0.50,
    "sutil_minima": 0.51,
    "mpc_60_swing": 0.56,
    "dangelo_laid_back": 0.53,
    "energetic_push": 0.50,
    "light_swing": 0.54,
    "medium_swing": 0.58,
    "heavy_swing": 0.64,
    "swing_16th_light": 0.54,
    "swing_16th_medium": 0.58,
    "swing_16th_heavy": 0.64,
    "swing_8th": 0.58,
    "laid_back": 0.50,
    "pushing": 0.50,
    "human": 0.53
}

GROOVE_PROFILES = GROOVE_SWING_RATIOS

def apply_groove_to_notes(
    notes: List[NoteEvent],
    profile: str = "sutil_minima",
    tempo: float = 120.0,
    strength: float = 1.0,
    profile_name: str = None
) -> List[NoteEvent]:
    """
    Punto 28: Applies musical micro-groove, swing, and timing offsets.
    Reads profiles from config/groove_config.json (default: SUTIL_MINIMA).
    """
    conf = get_groove_configuration()
    prof_key = (profile_name or profile or conf.get("default_profile", "SUTIL_MINIMA")).upper()

    cfg_profiles = conf.get("profiles", {})
    matched_profile = cfg_profiles.get(prof_key, cfg_profiles.get(prof_key.lower(), {}))

    swing_ratio = matched_profile.get("swing_ratio", GROOVE_SWING_RATIOS.get(prof_key.lower(), 0.51))
    push_pull_ms = matched_profile.get("push_pull_ms", 0.0) * strength
    jitter_ms = matched_profile.get("timing_jitter_ms", 0.0) * strength
    vel_jitter = int(matched_profile.get("velocity_jitter", 0) * strength)

    # Legacy fallback
    if not matched_profile:
        if prof_key.lower() == "laid_back":
            push_pull_ms = 6.0 * strength
        elif prof_key.lower() == "pushing":
            push_pull_ms = -4.0 * strength

    # Milliseconds per beat = (60 / tempo) * 1000
    ms_per_beat = (60.0 / tempo) * 1000.0
    beats_per_ms = 1.0 / ms_per_beat
    offset_beats = push_pull_ms * beats_per_ms


    adjusted: List[NoteEvent] = []
    for note in notes:
        # Calculate position within the current beat (0.0 to 1.0)
        beat_phase = note.start % 1.0
        new_start = note.start + offset_beats
        new_vel = note.velocity

        if jitter_ms > 0 or vel_jitter > 0:
            seed = int((note.start * 1000 + note.pitch) % 10000)
            prng = random.Random(seed)
            if jitter_ms > 0:
                new_start += prng.uniform(-jitter_ms, jitter_ms) * beats_per_ms
            if vel_jitter > 0:
                new_vel = max(1, min(127, note.velocity + prng.randint(-vel_jitter, vel_jitter)))

        # Check if note sits on the 2nd or 4th sixteenth note of a beat (0.25 or 0.75)
        # Swing delays the off-sixteenth
        is_swingable = abs(beat_phase - 0.25) < 0.03 or abs(beat_phase - 0.75) < 0.03
        if is_swingable and swing_ratio > 0.50:
            # Shift = (swing_ratio - 0.5) * 0.5 beats * strength
            swing_shift = (swing_ratio - 0.50) * 0.5 * strength
            new_start += swing_shift

        adj_ev = NoteEvent(
            pitch=note.pitch,
            pitch_class=note.pitch_class,
            octave=note.octave,
            start=max(0.0, round(new_start, 5)),
            duration=note.duration,
            velocity=new_vel,
            channel=note.channel,
            probability=note.probability,
            accent=note.accent
        )
        adjusted.append(adj_ev)

    return adjusted

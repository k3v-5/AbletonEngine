"""
Pre-defined Production Sound Profiles across genres and characters.
"""
from typing import Dict
from .models import SoundProfile

SOUND_PROFILES: Dict[str, SoundProfile] = {
    "sub_deep": SoundProfile(
        id="sub_deep", role="SUB_BASS", character="dark",
        weight=0.95, brightness=0.10, warmth=0.60, aggression=0.10,
        movement=0.05, space=0.00, width=0.00, stereo=False,
        register_min_hz=20.0, register_max_hz=90.0
    ),
    "bass_dark_club": SoundProfile(
        id="bass_dark_club", role="BASS", character="dark_club",
        weight=0.90, brightness=0.30, warmth=0.70, aggression=0.50,
        movement=0.35, space=0.05, width=0.10, stereo=False,
        register_min_hz=40.0, register_max_hz=400.0
    ),
    "bass_rolling_techno": SoundProfile(
        id="bass_rolling_techno", role="BASS", character="rolling",
        weight=0.85, brightness=0.35, warmth=0.65, aggression=0.40,
        movement=0.60, space=0.10, width=0.15, stereo=False,
        register_min_hz=45.0, register_max_hz=500.0
    ),
    "lead_analog_warm": SoundProfile(
        id="lead_analog_warm", role="LEAD", character="analog_warm",
        weight=0.40, brightness=0.65, warmth=0.80, aggression=0.30,
        movement=0.50, space=0.45, width=0.60, stereo=True,
        register_min_hz=250.0, register_max_hz=8000.0
    ),
    "lead_hypnotic_bright": SoundProfile(
        id="lead_hypnotic_bright", role="LEAD", character="bright",
        weight=0.30, brightness=0.85, warmth=0.40, aggression=0.60,
        movement=0.75, space=0.55, width=0.70, stereo=True,
        register_min_hz=350.0, register_max_hz=12000.0
    ),
    "pad_cinematic_wide": SoundProfile(
        id="pad_cinematic_wide", role="PAD", character="cinematic",
        weight=0.50, brightness=0.50, warmth=0.75, aggression=0.10,
        movement=0.65, space=0.85, width=0.95, stereo=True,
        register_min_hz=150.0, register_max_hz=10000.0
    ),
    "chords_deep_lush": SoundProfile(
        id="chords_deep_lush", role="CHORDS", character="lush",
        weight=0.55, brightness=0.55, warmth=0.85, aggression=0.20,
        movement=0.40, space=0.60, width=0.75, stereo=True,
        register_min_hz=180.0, register_max_hz=9000.0
    ),
    "drums_punchy_techno": SoundProfile(
        id="drums_punchy_techno", role="DRUMS", character="punchy",
        weight=0.90, brightness=0.70, warmth=0.60, aggression=0.65,
        movement=0.20, space=0.25, width=0.50, stereo=True,
        register_min_hz=30.0, register_max_hz=18000.0
    )
}

def get_sound_profile(profile_id_or_role: str, character: str = "dark_club") -> SoundProfile:
    """Retrieves or builds a matching SoundProfile."""
    key = profile_id_or_role.lower().strip()
    if key in SOUND_PROFILES:
        return SOUND_PROFILES[key]
    for p in SOUND_PROFILES.values():
        if p.role.lower() == key or p.character.lower() == character.lower():
            return p
    return SOUND_PROFILES["bass_dark_club"]

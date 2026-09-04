# engine/instruments/profiles/sound_profiles.py
from typing import Dict, Optional
from ..roles import SoundProfile, InstrumentRole

SOUND_PROFILES: Dict[str, SoundProfile] = {
    # Bass Profiles
    "deep_sub": SoundProfile(
        name="deep_sub",
        role=InstrumentRole.SUB_BASS,
        character="deep_clean_sub",
        frequency_bias="sub",
        attack_ms=5.0,
        decay_ms=400.0,
        sustain_level=0.9,
        release_ms=100.0,
        preferred_sources=["instrument", "simpler"],
        tags=["sine", "sub", "clean", "monophonic"]
    ),
    "rolling_bass": SoundProfile(
        name="rolling_bass",
        role=InstrumentRole.BASS,
        character="rolling_16th_saw",
        frequency_bias="low_mid",
        attack_ms=2.0,
        decay_ms=120.0,
        sustain_level=0.4,
        release_ms=60.0,
        preferred_sources=["instrument", "preset"],
        tags=["sawtooth", "filter_envelope", "rolling", "punchy"]
    ),
    "dark_bass": SoundProfile(
        name="dark_bass",
        role=InstrumentRole.BASS,
        character="dark_distorted",
        frequency_bias="low_mid",
        attack_ms=3.0,
        decay_ms=250.0,
        sustain_level=0.7,
        release_ms=150.0,
        preferred_sources=["instrument", "preset"],
        tags=["drive", "techno", "dark", "heavy"]
    ),

    # Pad & Harmony Profiles
    "warm_pad": SoundProfile(
        name="warm_pad",
        role=InstrumentRole.PAD,
        character="warm_lush_analog",
        frequency_bias="mid",
        attack_ms=400.0,
        decay_ms=1200.0,
        sustain_level=0.8,
        release_ms=800.0,
        preferred_sources=["instrument", "preset"],
        tags=["analog", "chorus", "lush", "warm", "strings"]
    ),
    "bright_pad": SoundProfile(
        name="bright_pad",
        role=InstrumentRole.PAD,
        character="bright_shimmering",
        frequency_bias="high",
        attack_ms=250.0,
        decay_ms=1000.0,
        sustain_level=0.75,
        release_ms=600.0,
        preferred_sources=["instrument", "preset"],
        tags=["digital", "air", "shimmer", "reverb"]
    ),

    # Lead & Melodic Profiles
    "analog_lead": SoundProfile(
        name="analog_lead",
        role=InstrumentRole.LEAD,
        character="cutting_analog_mono",
        frequency_bias="mid",
        attack_ms=5.0,
        decay_ms=300.0,
        sustain_level=0.85,
        release_ms=200.0,
        preferred_sources=["instrument", "preset"],
        tags=["drift", "wavetable", "analog", "lead", "glide"]
    ),
    "pluck": SoundProfile(
        name="pluck",
        role=InstrumentRole.PLUCK,
        character="short_crisp_decay",
        frequency_bias="high",
        attack_ms=1.0,
        decay_ms=180.0,
        sustain_level=0.1,
        release_ms=120.0,
        preferred_sources=["instrument", "simpler"],
        tags=["short", "pizzicato", "melodic_techno", "fast"]
    ),

    # Drum Profiles
    "deep_kick": SoundProfile(
        name="deep_kick",
        role=InstrumentRole.KICK,
        character="deep_punchy",
        frequency_bias="sub",
        attack_ms=1.0,
        decay_ms=320.0,
        sustain_level=0.0,
        release_ms=80.0,
        preferred_sources=["sample", "simpler"],
        tags=["kick", "sub", "techno", "4_on_the_floor"]
    ),
    "tight_kick": SoundProfile(
        name="tight_kick",
        role=InstrumentRole.KICK,
        character="tight_clicky",
        frequency_bias="low_mid",
        attack_ms=1.0,
        decay_ms=200.0,
        sustain_level=0.0,
        release_ms=50.0,
        preferred_sources=["sample", "simpler"],
        tags=["kick", "tight", "click", "short"]
    ),
    "techno_hat": SoundProfile(
        name="techno_hat",
        role=InstrumentRole.CLOSED_HAT,
        character="tight_metallic_click",
        frequency_bias="high",
        attack_ms=1.0,
        decay_ms=50.0,
        sustain_level=0.0,
        release_ms=30.0,
        preferred_sources=["sample", "simpler"],
        tags=["hat", "closed", "909", "crisp"]
    ),
    "industrial_percussion": SoundProfile(
        name="industrial_percussion",
        role=InstrumentRole.PERCUSSION,
        character="metallic_clang_decay",
        frequency_bias="mid",
        attack_ms=2.0,
        decay_ms=350.0,
        sustain_level=0.0,
        release_ms=150.0,
        preferred_sources=["sample", "simpler"],
        tags=["perc", "metal", "industrial", "rim"]
    )
}

def get_sound_profile(name: str) -> Optional[SoundProfile]:
    key = name.lower().replace("-", "_").replace(" ", "_")
    return SOUND_PROFILES.get(key)

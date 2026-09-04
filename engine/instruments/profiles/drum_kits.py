# engine/instruments/profiles/drum_kits.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class DrumKitPadConfig:
    role: str
    sound_profile: str
    character: str = ""
    frequency_bias: str = "balanced"
    optional: bool = False

@dataclass
class DrumKitProfile:
    genre: str
    name: str
    description: str
    pads: Dict[str, DrumKitPadConfig] = field(default_factory=dict)
    tempo_range: tuple = (120, 130)
    preset_uri: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genre": self.genre,
            "name": self.name,
            "description": self.description,
            "tempo_range": list(self.tempo_range),
            "preset_uri": self.preset_uri,
            "pads": {k: {"role": v.role, "sound_profile": v.sound_profile, "character": v.character, "frequency_bias": v.frequency_bias, "optional": v.optional} for k, v in self.pads.items()}
        }

DRUM_KIT_PROFILES: Dict[str, DrumKitProfile] = {
    "melodic_techno": DrumKitProfile(
        genre="melodic_techno",
        name="Melodic Techno Core Kit",
        description="Deep punchy kick with sub pressure, crisp snappy claps, tight 16th hats, and atmospheric percs",
        tempo_range=(122, 128),
        preset_uri="query:Drums#FileId_5367",
        pads={
            "KICK": DrumKitPadConfig("KICK", "techno_deep_kick", character="deep_punchy", frequency_bias="sub"),
            "KICK_ALT": DrumKitPadConfig("KICK_ALT", "techno_rumble_kick", character="rumble", frequency_bias="sub", optional=True),
            "SNARE": DrumKitPadConfig("SNARE", "techno_tight_snare", character="tight", frequency_bias="mid"),
            "CLAP": DrumKitPadConfig("CLAP", "melodic_techno_clap", character="crisp_snappy", frequency_bias="mid"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "techno_closed_hat", character="tight_crisp", frequency_bias="high"),
            "OPEN_HAT": DrumKitPadConfig("OPEN_HAT", "techno_open_hat", character="bright_sizzle", frequency_bias="high"),
            "PERC_1": DrumKitPadConfig("PERC_1", "melodic_techno_perc", character="dark_wood", frequency_bias="mid"),
            "PERC_2": DrumKitPadConfig("PERC_2", "melodic_techno_metal", character="metallic_rim", frequency_bias="high"),
            "SHAKER": DrumKitPadConfig("SHAKER", "techno_shaker", character="subtle_rolling", frequency_bias="high", optional=True),
            "TOM": DrumKitPadConfig("TOM", "techno_low_tom", character="deep_acoustic", frequency_bias="low_mid", optional=True),
            "FX": DrumKitPadConfig("FX", "techno_laser_fx", character="atmospheric_sweep", frequency_bias="high", optional=True),
            "IMPACT": DrumKitPadConfig("IMPACT", "techno_sub_impact", character="sub_drop", frequency_bias="sub", optional=True),
        }
    ),
    "techno": DrumKitProfile(
        genre="techno",
        name="Peak Time Industrial Techno Kit",
        description="Heavy driving industrial kicks, aggressive claps, razor sharp hats and metallic percussions",
        tempo_range=(130, 140),
        pads={
            "KICK": DrumKitPadConfig("KICK", "industrial_kick", character="distorted_punchy", frequency_bias="sub"),
            "CLAP": DrumKitPadConfig("CLAP", "harsh_clap", character="industrial_wide", frequency_bias="mid"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "razor_hat", character="cutting_short", frequency_bias="high"),
            "OPEN_HAT": DrumKitPadConfig("OPEN_HAT", "sizzling_open_hat", character="metallic_bright", frequency_bias="high"),
            "PERC_1": DrumKitPadConfig("PERC_1", "industrial_percussion", character="anvil_clang", frequency_bias="mid"),
            "PERC_2": DrumKitPadConfig("PERC_2", "concrete_perc", character="stomp_reverb", frequency_bias="low_mid"),
        }
    ),
    "house": DrumKitProfile(
        genre="house",
        name="Classic House 909 Kit",
        description="Round 909 kick, organic snappy snare, swinging hats and acoustic shaker",
        tempo_range=(122, 126),
        pads={
            "KICK": DrumKitPadConfig("KICK", "house_round_kick", character="warm_round", frequency_bias="sub"),
            "SNARE": DrumKitPadConfig("SNARE", "house_909_snare", character="snappy", frequency_bias="mid"),
            "CLAP": DrumKitPadConfig("CLAP", "house_analog_clap", character="layered", frequency_bias="mid"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "house_909_hat", character="swing_ch", frequency_bias="high"),
            "OPEN_HAT": DrumKitPadConfig("OPEN_HAT", "house_909_oh", character="classic_open", frequency_bias="high"),
            "SHAKER": DrumKitPadConfig("SHAKER", "house_groove_shaker", character="organic", frequency_bias="high"),
        }
    ),
    "trance": DrumKitProfile(
        genre="trance",
        name="Driving Uplifting Trance Kit",
        description="Hard punchy trance kick with click transient, gated claps and sizzling open hats",
        tempo_range=(136, 142),
        pads={
            "KICK": DrumKitPadConfig("KICK", "trance_driving_kick", character="click_punch", frequency_bias="sub"),
            "CLAP": DrumKitPadConfig("CLAP", "trance_reverb_clap", character="wide_gated", frequency_bias="mid"),
            "OPEN_HAT": DrumKitPadConfig("OPEN_HAT", "trance_offbeat_hat", character="high_energy", frequency_bias="high"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "trance_fast_hat", character="tight_16th", frequency_bias="high"),
        }
    ),
    "trap": DrumKitProfile(
        genre="trap",
        name="Modern 808 Trap Kit",
        description="Short punchy kick, snappy 808 snare, pitchable hi-hats and chant FX",
        tempo_range=(130, 160),
        pads={
            "KICK": DrumKitPadConfig("KICK", "trap_punchy_kick", character="short_punch", frequency_bias="low_mid"),
            "SNARE": DrumKitPadConfig("SNARE", "trap_808_snare", character="snappy_bright", frequency_bias="mid"),
            "CLAP": DrumKitPadConfig("CLAP", "trap_layered_clap", character="tight", frequency_bias="mid"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "trap_roll_hat", character="clean_click", frequency_bias="high"),
            "OPEN_HAT": DrumKitPadConfig("OPEN_HAT", "trap_open_hat", character="short_decay", frequency_bias="high"),
            "FX": DrumKitPadConfig("FX", "trap_chant_fx", character="vocal_stab", frequency_bias="mid"),
        }
    ),
    "hip_hop": DrumKitProfile(
        genre="hip_hop",
        name="Boom Bap Vintage Kit",
        description="Dusty sampled kick, fat vintage acoustic snare, warm lo-fi hats and vinyl percs",
        tempo_range=(85, 95),
        pads={
            "KICK": DrumKitPadConfig("KICK", "boombap_dusty_kick", character="warm_fat", frequency_bias="low_mid"),
            "SNARE": DrumKitPadConfig("SNARE", "boombap_fat_snare", character="crack_wood", frequency_bias="mid"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "boombap_lofi_hat", character="dusty_tape", frequency_bias="high"),
            "PERC_1": DrumKitPadConfig("PERC_1", "boombap_rimshot", character="organic_rim", frequency_bias="mid"),
        }
    ),
    "dnb": DrumKitProfile(
        genre="dnb",
        name="Drum & Bass Fast Roller Kit",
        description="Tight punchy kick, piercing crack snare, rapid rolling hats and ghost hits",
        tempo_range=(170, 178),
        pads={
            "KICK": DrumKitPadConfig("KICK", "dnb_tight_kick", character="punchy_short", frequency_bias="low_mid"),
            "SNARE": DrumKitPadConfig("SNARE", "dnb_crack_snare", character="piercing_200hz", frequency_bias="mid"),
            "CLOSED_HAT": DrumKitPadConfig("CLOSED_HAT", "dnb_roller_hat", character="rapid_ghost", frequency_bias="high"),
            "SHAKER": DrumKitPadConfig("SHAKER", "dnb_fast_shaker", character="light_rolling", frequency_bias="high"),
        }
    )
}

def get_drum_kit_profile(genre_or_name: str) -> DrumKitProfile:
    key = genre_or_name.lower().replace("-", "_").replace(" ", "_")
    if key in DRUM_KIT_PROFILES:
        return DRUM_KIT_PROFILES[key]
    return DRUM_KIT_PROFILES["melodic_techno"]

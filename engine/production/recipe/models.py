"""
Data models and error classes for the Production Recipe Engine.
Includes genre profiles, catalogs, blueprints, sections, and verified URIs.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


class DeviceLoadFailureError(RuntimeError):
    """Raised when an instrument or effect fails to physically load into Live."""
    pass


class PhysicalAcousticSilenceError(RuntimeError):
    """Raised when a track produces zero audible signal (meter < 0.001) during playback."""
    pass


class MasterLoudnessComplianceError(RuntimeError):
    """Raised when master audio fails integrated LUFS or True Peak criteria."""
    pass


class ArrangementMissingClipsError(RuntimeError):
    """Raised when one or more tracks have zero clips in the Arrangement view timeline."""
    pass


class DrumRackEmptyError(RuntimeError):
    """Raised when a Drum Rack device contains zero playable sample pads."""
    pass


@dataclass
class GenreProductionProfile:
    genre_id: str
    display_name: str
    bpm_range: Tuple[float, float]
    default_bpm: float
    target_lufs: float
    true_peak_ceiling: float
    typical_scales: List[str]
    typical_roles: List[str]
    recommended_instruments: Dict[str, str]
    mix_headroom_target_db: float = -6.0


GENRE_PRODUCTION_CATALOG: Dict[str, GenreProductionProfile] = {
    "trap_hiphop": GenreProductionProfile(
        genre_id="trap_hiphop",
        display_name="Trap / Hip-Hop Moderno",
        bpm_range=(130.0, 165.0),
        default_bpm=140.0,
        target_lufs=-7.5,
        true_peak_ceiling=-0.5,
        typical_scales=["C Minor", "F Minor", "G Minor", "D# Minor"],
        typical_roles=["bass", "drums", "lead", "keys", "pad"],
        recommended_instruments={"bass": "Vital", "drums": "808 Core Kit", "keys": "Analog Lab V", "lead": "Serum 2", "pad": "Pigments"}
    ),
    "zomboy_brostep": GenreProductionProfile(
        genre_id="zomboy_brostep",
        display_name="Heavy Brostep / Tearout Dubstep (Zomboy Style)",
        bpm_range=(140.0, 150.0),
        default_bpm=145.0,
        target_lufs=-7.5,
        true_peak_ceiling=-0.3,
        typical_scales=["F Minor", "D Minor", "E Minor"],
        typical_roles=["drums", "bass", "growl_call", "screech_response", "pad", "fx", "vocal_chant", "master"],
        recommended_instruments={"drums": "808 Core Kit", "growl_call": "Serum 2", "screech_response": "Vital", "bass": "Vital", "pad": "Analog Lab V", "fx": "ShaperBox 3"}
    ),
    "pop_commercial": GenreProductionProfile(
        genre_id="pop_commercial",
        display_name="Commercial Pop / Dance Pop",
        bpm_range=(115.0, 128.0),
        default_bpm=122.0,
        target_lufs=-8.0,
        true_peak_ceiling=-0.5,
        typical_scales=["C Major", "G Major", "A Minor", "D Major"],
        typical_roles=["keys", "bass", "drums", "lead", "pad", "arp"],
        recommended_instruments={"keys": "Analog Lab V", "bass": "Massive X", "drums": "Drum Rack", "lead": "Serum 2", "pad": "Pigments"}
    ),
    "neo_soul_ballad": GenreProductionProfile(
        genre_id="neo_soul_ballad",
        display_name="Neo-Soul / Emotional Ballad (Tyler, The Creator)",
        bpm_range=(75.0, 92.0),
        default_bpm=82.0,
        target_lufs=-9.5,
        true_peak_ceiling=-0.5,
        typical_scales=["Eb Major", "Ab Major", "Db Major", "Bb Minor"],
        typical_roles=["keys", "bass", "drums", "lead", "pad", "reese", "arp"],
        recommended_instruments={"keys": "Analog Lab V", "bass": "Vital", "reese": "Massive", "drums": "808 Core Kit", "lead": "Serum 2", "pad": "Pigments", "arp": "Massive X"}
    ),
    "house_club": GenreProductionProfile(
        genre_id="house_club",
        display_name="House / Tech House / Club",
        bpm_range=(122.0, 130.0),
        default_bpm=126.0,
        target_lufs=-6.5,
        true_peak_ceiling=-0.3,
        typical_scales=["A Minor", "F Minor", "D Minor", "G Minor"],
        typical_roles=["drums", "bass", "lead", "pad", "fx"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Serum 2", "lead": "Massive X", "pad": "Pigments"}
    ),
    "synthwave_retro": GenreProductionProfile(
        genre_id="synthwave_retro",
        display_name="Synthwave / Retro Electro",
        bpm_range=(100.0, 125.0),
        default_bpm=115.0,
        target_lufs=-8.5,
        true_peak_ceiling=-0.5,
        typical_scales=["D Minor", "A Minor", "E Minor"],
        typical_roles=["bass", "arp", "lead", "pad", "drums"],
        recommended_instruments={"bass": "Massive", "arp": "Massive X", "lead": "Serum 2", "pad": "Analog Lab V", "drums": "808 Core Kit"}
    ),
    "rnb_contemporary": GenreProductionProfile(
        genre_id="rnb_contemporary",
        display_name="Contemporary R&B / Soul",
        bpm_range=(85.0, 105.0),
        default_bpm=95.0,
        target_lufs=-9.0,
        true_peak_ceiling=-0.5,
        typical_scales=["F Minor", "Bb Minor", "Eb Major", "C Minor"],
        typical_roles=["keys", "bass", "drums", "pad", "lead"],
        recommended_instruments={"keys": "Analog Lab V", "bass": "Vital", "drums": "Drum Rack", "pad": "Pigments", "lead": "Serum 2"}
    ),
    "reggaeton_latin": GenreProductionProfile(
        genre_id="reggaeton_latin",
        display_name="Reggaeton / Latin Urban",
        bpm_range=(88.0, 100.0),
        default_bpm=94.0,
        target_lufs=-7.5,
        true_peak_ceiling=-0.5,
        typical_scales=["G Minor", "D Minor", "A Minor", "C Minor"],
        typical_roles=["drums", "bass", "keys", "lead", "pad"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "keys": "Analog Lab V", "lead": "Serum 2"}
    ),
    "ambient_cinematic": GenreProductionProfile(
        genre_id="ambient_cinematic",
        display_name="Cinematic / Ambient",
        bpm_range=(60.0, 90.0),
        default_bpm=72.0,
        target_lufs=-14.0,
        true_peak_ceiling=-1.0,
        typical_scales=["D Minor", "C Major", "F Lydian", "A Aeolian"],
        typical_roles=["pad", "keys", "arp", "fx"],
        recommended_instruments={"pad": "Pigments", "keys": "Analog Lab V", "arp": "Massive X"}
    ),
    "cumbia_latina": GenreProductionProfile(
        genre_id="cumbia_latina",
        display_name="Cumbia Latina / Sonidera / Electrocumbia",
        bpm_range=(85.0, 105.0),
        default_bpm=92.0,
        target_lufs=-8.0,
        true_peak_ceiling=-0.5,
        typical_scales=["A Minor", "D Minor", "E Minor", "C Major"],
        typical_roles=["drums", "bass", "keys", "lead", "percussion"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "keys": "Analog Lab V", "lead": "Serum 2", "percussion": "Drum Rack"}
    ),
    "boom_bap_rap": GenreProductionProfile(
        genre_id="boom_bap_rap",
        display_name="Boom-Bap / 90s Rap & Hip-Hop",
        bpm_range=(85.0, 98.0),
        default_bpm=92.0,
        target_lufs=-9.0,
        true_peak_ceiling=-0.5,
        typical_scales=["C Minor", "F Minor", "G Minor", "Eb Major"],
        typical_roles=["drums", "bass", "keys", "lead", "horns"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "keys": "Analog Lab V", "lead": "Massive X"}
    ),
    "edm_festival": GenreProductionProfile(
        genre_id="edm_festival",
        display_name="EDM / Big Room / Festival Progressive",
        bpm_range=(125.0, 132.0),
        default_bpm=128.0,
        target_lufs=-6.0,
        true_peak_ceiling=-0.3,
        typical_scales=["F Minor", "G Minor", "A Minor", "D# Minor"],
        typical_roles=["drums", "bass", "lead", "pad", "arp", "fx"],
        recommended_instruments={"drums": "Drum Rack", "lead": "Serum 2", "bass": "Vital", "pad": "Pigments", "arp": "Massive X"}
    ),
    "drum_and_bass": GenreProductionProfile(
        genre_id="drum_and_bass",
        display_name="Drum & Bass / Liquid / Jungle",
        bpm_range=(170.0, 178.0),
        default_bpm=174.0,
        target_lufs=-6.5,
        true_peak_ceiling=-0.3,
        typical_scales=["F Minor", "D Minor", "C Minor"],
        typical_roles=["drums", "bass", "pad", "arp", "lead"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "pad": "Pigments", "lead": "Serum 2"}
    ),
    "afrobeat_urban": GenreProductionProfile(
        genre_id="afrobeat_urban",
        display_name="Afrobeat / Afropop / Urban Dancehall",
        bpm_range=(95.0, 108.0),
        default_bpm=102.0,
        target_lufs=-8.0,
        true_peak_ceiling=-0.5,
        typical_scales=["F Major", "C Major", "G Minor", "D Minor"],
        typical_roles=["drums", "bass", "keys", "lead", "percussion"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "keys": "Analog Lab V", "lead": "Serum 2"}
    ),
    "rock_modern": GenreProductionProfile(
        genre_id="rock_modern",
        display_name="Modern Rock / Indie / Alternative",
        bpm_range=(110.0, 145.0),
        default_bpm=128.0,
        target_lufs=-8.5,
        true_peak_ceiling=-0.5,
        typical_scales=["E Minor", "A Minor", "D Major", "G Major"],
        typical_roles=["drums", "bass", "guitar", "lead", "keys"],
        recommended_instruments={"drums": "Drum Rack", "bass": "Vital", "keys": "Analog Lab V", "lead": "Serum 2"}
    )
}

# Exact Verified Browser URIs from Ableton Live's Browser
VERIFIED_PLUGIN_URIS = {
    # Synths & Instruments
    "Analog Lab V": "query:Plugins#VST3:Arturia:Analog%20Lab%20V",
    "Solina V2": "query:Plugins#VST3:Arturia:Solina%20V2",
    "Stage-73 V2": "query:Plugins#VST3:Arturia:Stage-73%20V2",
    "Vital": "query:Plugins#VST3:Vital%20Audio:Vital",
    "Serum 2": "query:Plugins#VST3:Xfer%20Records:Serum%202",
    "Serum 2 FX": "query:Plugins#VST3:Xfer%20Records:Serum%202%20FX",
    "Massive X": "query:Plugins#VST3:Native%20Instruments:Massive%20X",
    "Massive": "query:Plugins#VST3:Native%20Instruments:Massive",
    "Pigments": "query:Plugins#VST3:Arturia:Pigments",
    "Omnisphere": "query:Plugins#VST3:Spectrasonics:Omnisphere",
    "ZENOLOGY": "query:Plugins#VST3:Roland%20Cloud:ZENOLOGY",
    "Fraction": "query:Plugins#VST3:Prototype%20Audio:Fraction",
    "Drum Rack": "query:Drums#Drum%20Rack",
    "808 Core Kit": "query:Drums#FileId_5422",
    "Wavetable": "query:Synths#Wavetable",
    "Operator": "query:Synths#Operator",
    "Drift": "query:Synths#Drift",
    # Audio Effects & Processors
    "ShaperBox 3": "query:Plugins#VST3:Cableguys:ShaperBox%203",
    "Saturn 2": "query:Plugins#VST3:FabFilter:Saturn%202",
    "Thermal": "query:Plugins#VST3:Output:Thermal",
    "Efx FRAGMENTS": "query:Plugins#VST3:Arturia:Efx%20FRAGMENTS",
    "Efx MOTIONS": "query:Plugins#VST3:Arturia:Efx%20MOTIONS",
    "Efx REFRACT": "query:Plugins#VST3:Arturia:Efx%20REFRACT",
    "Pro-Q 4": "query:Plugins#VST3:FabFilter:Pro-Q%204",
    "Pro-L 2": "query:Plugins#VST3:FabFilter:Pro-L%202",
    "Pro-C 3": "query:Plugins#VST3:FabFilter:Pro-C%203",
    "Pro-MB": "query:Plugins#VST3:FabFilter:Pro-MB",
    "The God Particle": "query:Plugins#VST3:Cradle:The%20God%20Particle",
    "OTT": "query:Plugins#VST3:Xfer%20Records:OTT",
    "Decapitator": "query:Plugins#VST:Custom:SoundToys:Decapitator",
    "EchoBoy": "query:Plugins#VST:Custom:SoundToys:EchoBoy",
    "LittleAlterBoy": "query:Plugins#VST:Custom:SoundToys:LittleAlterBoy",
    # Native Ableton Effects
    "EQ Eight": "query:AudioFx#EQ%20Eight",
    "Drum Buss": "query:AudioFx#Drum%20Buss",
    "Saturator": "query:AudioFx#Saturator",
    "Compressor": "query:AudioFx#Compressor",
    "Glue Compressor": "query:AudioFx#Glue%20Compressor",
    "Limiter": "query:AudioFx#Limiter",
    "Utility": "query:AudioFx#Utility"
}


@dataclass
class RecipeSection:
    name: str
    start_bar: int
    length_bars: int
    active_roles: List[str]
    description: str = ""


@dataclass
class TrackBlueprint:
    track_index: int
    name: str
    role: str  # 'keys', 'bass', 'reese', 'lead', 'pad', 'arp', 'drums', 'fx', 'vocal', 'foley', 'master'
    instrument_name: Optional[str] = None
    instrument_uri: Optional[str] = None
    preset_name: Optional[str] = None
    effects: List[Dict[str, str]] = field(default_factory=list)  # [{'name': ..., 'uri': ...}]
    parameter_sculpting: Dict[str, float] = field(default_factory=dict)
    clip_notes: List[Dict[str, Any]] = field(default_factory=list)
    nominal_volume: float = 0.85
    is_audio: bool = False
    audio_sample_path: Optional[str] = None
    warp_mode: str = "complex"
    clip_gain: float = 1.0
    pitch_coarse: int = 0
    procedural_sample_type: Optional[str] = None


@dataclass
class ProductionRecipe:
    title: str
    genre_reference: str
    bpm: float
    key: str
    scale: str
    chord_progression: List[str]
    tracks: List[TrackBlueprint]
    sections: List[RecipeSection] = field(default_factory=list)
    target_lufs: float = -7.0
    max_true_peak: float = -0.5
    total_bars: int = 60
    enable_sidechain: bool = True
    enable_mastering_chain: bool = True
    master_bus_track_index: Optional[int] = None

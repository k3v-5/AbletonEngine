# engine/creative/models.py
"""
Data models for Phase 1: DNA & Creative Direction.
Defines strong contracts for sonic world-building, reference acoustic profiles,
harmonic/modal DNA, instrumentation scaffolding, and arrangement energy blueprints.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class AestheticMood(str, Enum):
    DARK_MELANCHOLIC_TRAP = "dark_melancholic_trap"
    NEO_SOUL_GROOVE = "neo_soul_groove"
    AGGRESSIVE_INDUSTRIAL_BOUNCE = "aggressive_industrial_bounce"
    CINEMATIC_SOUL_HYBRID = "cinematic_soul_hybrid"
    LOFI_CHILL_HOP = "lofi_chill_hop"
    FUTURISTIC_SYNTHWAVE = "futuristic_synthwave"


class ModalFlavor(str, Enum):
    NATURAL_MINOR = "natural_minor"     # Aeolian
    DORIAN = "dorian"                   # Minor with raised 6th (Jazzy/Soulful)
    PHRYGIAN = "phrygian"               # Minor with b2 (Tension/Darkness)
    HARMONIC_MINOR = "harmonic_minor"   # Minor with raised 7th (Classical/Dramatic)
    MELODIC_MINOR = "melodic_minor"     # Jazz minor
    MAJOR_PENTATONIC = "major_pentatonic"


@dataclass
class SonicWorld:
    """Aesthetic, textural and acoustic spatial identity of the song."""
    mood: AestheticMood = AestheticMood.NEO_SOUL_GROOVE
    harmonic_warmth: float = 0.70       # 0.0 = clean digital, 1.0 = heavy tape/tube saturation
    acoustic_space: str = "intimate_dry" # "intimate_dry", "room_ambient", "cathedral_lush"
    reverb_decay_seconds: float = 1.6
    dynamic_spread_db: float = 12.0     # Target crest factor (peak to RMS spread)
    saturation_character: str = "tape_warmth" # "tape_warmth", "analog_clip", "tube_drive", "digital_clean"
    foley_texture: str = "vinyl_dust"   # "vinyl_dust", "cassette_hiss", "rain_ambient", "room_foley", "none"


@dataclass
class SpectralTargetBand:
    """Target acoustic energy balance for a specific frequency band."""
    frequency_min_hz: float
    frequency_max_hz: float
    target_energy_pct: float            # Percentage of total spectral energy
    width_stereo_pct: float             # Stereo spread (0% = mono, 100% = normal, 150% = ultra-wide)


@dataclass
class ReferenceProfile:
    """Acoustic DNA and fingerprint extracted from top-tier reference productions."""
    reference_name: str
    target_lufs: float = -14.0
    true_peak_dbtp: float = -1.0
    spectral_bands: Dict[str, SpectralTargetBand] = field(default_factory=dict)
    groove_signature: str = "dilla_swing" # "rigid_grid", "mpc_60_swing", "dilla_swing", "atlanta_trap"
    groove_swing_amount: float = 0.58     # Microtiming swing percentage
    transient_character: str = "punchy_clipped" # "punchy_clipped", "soft_warm", "snappy_dynamic"


@dataclass
class HarmonicDNA:
    """Harmonic vocabulary, modal structure, and voicing rules."""
    key_root: str = "F"
    scale: str = "natural_minor"
    secondary_modes: List[ModalFlavor] = field(default_factory=lambda: [ModalFlavor.DORIAN, ModalFlavor.PHRYGIAN])
    chord_tension_level: float = 0.65     # 0.0 = triads, 0.5 = 7ths, 0.8 = 9ths/11ths, 1.0 = altered extensions
    voicing_density: int = 4             # Number of voices per chord (3 to 6)
    voicing_spread: str = "drop_2"       # "closed", "drop_2", "open_spread", "quartal"
    allow_modal_interchange: bool = True # Injects borrowed chords from Dorian/Phrygian
    bass_root_motion: str = "functional_stepwise" # "pedal_point", "functional_stepwise", "chromatic_descending"


@dataclass
class TrackRoleAllocation:
    """Acoustic role reservation and slot allocation per track."""
    track_name: str
    role: str                            # "KICK", "BASS", "SNARE", "HATS", "CHORDS", "LEAD", "VOCAL_HOOK", "FOLEY"
    frequency_reservation: str           # e.g. "40-120 Hz", "30-90 Hz", "200-8000 Hz"
    pan: float = 0.0                     # -1.0 (Left) to 1.0 (Right)
    initial_volume_db: float = 0.0       # Target initial fader gain
    instrument_suggestion: str = ""      # Native or VST3 instrument
    recommended_preset: str = ""         # Recommended preset or timbre category
    track_color: str = "#808080"        # Hex color code for DAW visualization


@dataclass
class ArrangementSectionBlueprint:
    """Structural blueprint for an individual song section."""
    name: str                            # "Intro", "Verse 1", "Pre-Chorus", "Chorus", etc.
    start_bar: int
    duration_bars: int
    target_energy: float                 # 0.0 to 1.0
    active_roles: List[str]              # Which track roles play in this section
    description: str = ""


@dataclass
class ArrangementBlueprint:
    """Macro structural arrangement and dynamic energy trajectory of the whole song."""
    total_bars: int = 96
    tempo_bpm: float = 142.0
    meter: str = "4/4"
    sections: List[ArrangementSectionBlueprint] = field(default_factory=list)


@dataclass
class SongCreativeDNA:
    """Master contract representing the complete Phase 1 Creative Direction."""
    title: str
    artist: str
    genre: str
    sonic_world: SonicWorld = field(default_factory=SonicWorld)
    reference_profile: ReferenceProfile = field(default_factory=lambda: ReferenceProfile(reference_name="default"))
    harmonic_dna: HarmonicDNA = field(default_factory=HarmonicDNA)
    track_scaffold: List[TrackRoleAllocation] = field(default_factory=list)
    arrangement_blueprint: ArrangementBlueprint = field(default_factory=ArrangementBlueprint)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire creative brief into a clean JSON-ready dictionary."""
        return {
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "sonic_world": {
                "mood": self.sonic_world.mood.value if hasattr(self.sonic_world.mood, "value") else str(self.sonic_world.mood),
                "harmonic_warmth": self.sonic_world.harmonic_warmth,
                "acoustic_space": self.sonic_world.acoustic_space,
                "reverb_decay_seconds": self.sonic_world.reverb_decay_seconds,
                "dynamic_spread_db": self.sonic_world.dynamic_spread_db,
                "saturation_character": self.sonic_world.saturation_character,
                "foley_texture": self.sonic_world.foley_texture
            },
            "reference_profile": {
                "reference_name": self.reference_profile.reference_name,
                "target_lufs": self.reference_profile.target_lufs,
                "true_peak_dbtp": self.reference_profile.true_peak_dbtp,
                "groove_signature": self.reference_profile.groove_signature,
                "groove_swing_amount": self.reference_profile.groove_swing_amount,
                "transient_character": self.reference_profile.transient_character,
                "spectral_bands": {
                    k: {
                        "min_hz": v.frequency_min_hz,
                        "max_hz": v.frequency_max_hz,
                        "energy_pct": v.target_energy_pct,
                        "stereo_pct": v.width_stereo_pct
                    }
                    for k, v in self.reference_profile.spectral_bands.items()
                }
            },
            "harmonic_dna": {
                "key_root": self.harmonic_dna.key_root,
                "scale": self.harmonic_dna.scale,
                "secondary_modes": [m.value if hasattr(m, "value") else str(m) for m in self.harmonic_dna.secondary_modes],
                "chord_tension_level": self.harmonic_dna.chord_tension_level,
                "voicing_density": self.harmonic_dna.voicing_density,
                "voicing_spread": self.harmonic_dna.voicing_spread,
                "allow_modal_interchange": self.harmonic_dna.allow_modal_interchange,
                "bass_root_motion": self.harmonic_dna.bass_root_motion
            },
            "track_scaffold": [
                {
                    "track_name": t.track_name,
                    "role": t.role,
                    "frequency_reservation": t.frequency_reservation,
                    "pan": t.pan,
                    "initial_volume_db": t.initial_volume_db,
                    "instrument_suggestion": t.instrument_suggestion,
                    "recommended_preset": t.recommended_preset,
                    "track_color": t.track_color
                }
                for t in self.track_scaffold
            ],
            "arrangement_blueprint": {
                "total_bars": self.arrangement_blueprint.total_bars,
                "tempo_bpm": self.arrangement_blueprint.tempo_bpm,
                "meter": self.arrangement_blueprint.meter,
                "sections": [
                    {
                        "name": s.name,
                        "start_bar": s.start_bar,
                        "duration_bars": s.duration_bars,
                        "target_energy": s.target_energy,
                        "active_roles": s.active_roles,
                        "description": s.description
                    }
                    for s in self.arrangement_blueprint.sections
                ]
            },
            "metadata": self.metadata
        }

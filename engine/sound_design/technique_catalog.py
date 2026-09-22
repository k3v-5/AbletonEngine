# engine/sound_design/technique_catalog.py
"""
Technique Catalog (Level H - Sound Design System):
Codifies the 18 production technique families into a structured, modular catalog.
Maps creative sound design techniques to deterministic Ableton Live device chains
and DSP parameter configurations.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("TechniqueCatalog")


class ProductionTechniqueFamily(str, Enum):
    """The 18 fundamental families of sound design and sonic identity."""
    TEMPORAL_TRANSFORM = "TEMPORAL_TRANSFORM"                 # 1. Freeze, Stretch, Reverse, Tape-Stop, Stutter
    PITCH_HARMONIC = "PITCH_HARMONIC"                         # 2. Pitch shifting, Octave layer, Harmonic 5th/7th, Drones
    TRANSIENT_DESIGN = "TRANSIENT_DESIGN"                     # 3. Attack, Transient, Body, Tail 4-stage separation
    SATURATION_DISTORTION = "SATURATION_DISTORTION"           # 4. Tape, Tube, Soft/Hard clip, Bitcrush, Mid-only saturation
    CREATIVE_FILTER = "CREATIVE_FILTER"                       # 5. Sweeps, Resonant notches, Comb/Formant, Dynamic rhythm
    FRANKENSTEIN_LAYERING = "FRANKENSTEIN_LAYERING"           # 6. Hybrid multi-source composite sound generator
    TEXTURE_AND_NOISE = "TEXTURE_AND_NOISE"                   # 7. Self-derived organic vinyl, tape, room, 1200% stretch bed
    CREATIVE_SPACE = "CREATIVE_SPACE"                         # 8. Reverse reverb, Gated reverb, Freeze infinite, Pitch delay
    SPATIAL_NARRATIVE = "SPATIAL_NARRATIVE"                   # 9. Stereo width timeline, M/S, Haas, Sectional mono/stereo
    SPECTRAL_DESIGN = "SPECTRAL_DESIGN"                       # 10. Spectral freeze, Spectral blur, Resonators, Partials
    CONVOLUTION_RECONTEXT = "CONVOLUTION_RECONTEXT"           # 11. Self-impulse responses, cross-element excitation
    MICRO_CHOPPING = "MICRO_CHOPPING"                         # 12. Micro-slices (10-100ms), glitches, rhythmic gates
    MODULATION_MATRIX = "MODULATION_MATRIX"                   # 13. LFOs, Envelope followers, Ring mod, Reactive sidechain
    AUDIO_TO_MIDI_CYCLE = "AUDIO_TO_MIDI_CYCLE"               # 14. Audio transient/pitch analysis -> MIDI -> New sound
    BASS_LAB = "BASS_LAB"                                     # 15. Sub mono, Body stereo, Upper harmonic saturation
    DRUM_LAB = "DRUM_LAB"                                     # 16. Transient click + saturated body + sub punch + tail
    EAR_CANDY_ENGINE = "EAR_CANDY_ENGINE"                     # 17. Arrangement density valley scanner & micro-events
    SONIC_MUTATION_LAB = "SONIC_MUTATION_LAB"                 # 18. Combinatorial mutation generator & psychoacoustic filter


@dataclass
class DeviceRecipe:
    """A concrete processor configuration mapped to Ableton Live devices."""
    recipe_name: str
    device_name: str
    device_uri: str
    parameters: Dict[str, Any]
    purpose: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "device_name": self.device_name,
            "device_uri": self.device_uri,
            "parameters": dict(self.parameters),
            "purpose": self.purpose,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeviceRecipe:
        return cls(
            recipe_name=data.get("recipe_name", "Recipe"),
            device_name=data.get("device_name", "AudioFx"),
            device_uri=data.get("device_uri", ""),
            parameters=data.get("parameters", {}),
            purpose=data.get("purpose", ""),
        )


@dataclass
class TechniqueDefinition:
    """Detailed definition of a production technique and its processing chain."""
    family: ProductionTechniqueFamily
    technique_id: str
    name: str
    description: str
    recipes: List[DeviceRecipe] = field(default_factory=list)
    time_stretch_ratio: float = 1.0
    reverse: bool = False
    pitch_semitones: int = 0
    slice_length_ms: Optional[int] = None
    character_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family.value if isinstance(self.family, ProductionTechniqueFamily) else str(self.family),
            "technique_id": self.technique_id,
            "name": self.name,
            "description": self.description,
            "recipes": [r.to_dict() for r in self.recipes],
            "time_stretch_ratio": self.time_stretch_ratio,
            "reverse": self.reverse,
            "pitch_semitones": self.pitch_semitones,
            "slice_length_ms": self.slice_length_ms,
            "character_tags": list(self.character_tags),
        }


class TechniqueCatalog:
    """
    Central repository of production techniques across all 18 families.
    Provides deterministic templates, device parameters, and artistic guidelines.
    """

    _catalog: Dict[str, TechniqueDefinition] = {}

    @classmethod
    def initialize_catalog(cls) -> None:
        """Populates the catalog with recipes across all 18 families."""
        if cls._catalog:
            return

        # 1. Temporal Transform
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.TEMPORAL_TRANSFORM,
            technique_id="EXTREME_STRETCH_REVERSE",
            name="Extreme Stretch + Spectral Reverse",
            description="Time-stretch 400-800% in Texture mode followed by reverse rendering to create an ethereal tail.",
            time_stretch_ratio=4.0,
            reverse=True,
            character_tags=["ethereal", "atmospheric", "ghostly"],
            recipes=[
                DeviceRecipe("Highpass Notch", "EQ Eight", "query:AudioFx#EQ%20Eight", {"Band 1 Freq": "420 Hz", "Band 1 Mode": "High Pass 48dB/oct"}, "Clear low bass"),
                DeviceRecipe("Diffusion Reverb", "Reverb", "query:AudioFx#Reverb", {"Decay Time": "8.5 s", "Diffusion": "85%", "Dry/Wet": "50%"}, "Smear reverse transients"),
            ]
        ))

        # 2. Pitch & Harmonic
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.PITCH_HARMONIC,
            technique_id="FIFTH_SEVENTH_HARMONIC_LAYER",
            name="Fifths and Sevenths Harmonic Re-pitch",
            description="Derives a parallel harmonic layer transposed +7 or +10 semitones for modal depth.",
            pitch_semitones=7,
            character_tags=["modal", "harmonic_richness", "neo_soul"],
            recipes=[
                DeviceRecipe("Harmonic Shifter", "Shifter", "query:AudioFx#Shifter", {"Coarse": "+7 st", "Mode": "Pitch"}, "Generate perfect fifth"),
                DeviceRecipe("Bandpass Focus", "Auto Filter", "query:AudioFx#Auto%20Filter", {"Frequency": "1.2 kHz", "Resonance": "25%"}, "Isolate midrange halo"),
            ]
        ))

        # 3. Transient Design
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.TRANSIENT_DESIGN,
            technique_id="FOUR_STAGE_SPLIT",
            name="Attack / Transient / Body / Tail Sculpting",
            description="Isolates punch transient from low-end sustain to allow aggressive drive on attack without muddying the body.",
            character_tags=["punchy", "controlled", "clinical_transients"],
            recipes=[
                DeviceRecipe("Transient Accent", "Drum Buss", "query:AudioFx#Drum%20Buss", {"Transients": "+0.45", "Drive": "20%", "Crunch": "Medium"}, "Crisp punch"),
                DeviceRecipe("Tail Tamer Gate", "Gate", "query:AudioFx#Gate", {"Threshold": "-28 dB", "Release": "120 ms"}, "Tighten sustain decay"),
            ]
        ))

        # 4. Saturation & Distortion
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.SATURATION_DISTORTION,
            technique_id="MID_ONLY_TAPE_SATURATION",
            name="Mid-Band Focused Tape Compression",
            description="Warm tape saturation targeted exclusively at 300-3000 Hz, leaving sub and airy top-end pristine.",
            character_tags=["warm", "vintage", "tape_glue"],
            recipes=[
                DeviceRecipe("Warm Tape Drive", "Saturator", "query:AudioFx#Saturator", {"Drive": "+4.0 dB", "Curve": "Analog Clip", "Color": "On", "Base": "2.0 dB"}, "Analog warmth"),
                DeviceRecipe("Band Tilt", "EQ Eight", "query:AudioFx#EQ%20Eight", {"Band 2 Freq": "280 Hz", "Band 2 Gain": "+1.8 dB", "Band 8 Freq": "7.5 kHz", "Band 8 Gain": "-2.5 dB"}, "Vintage high roll-off"),
            ]
        ))

        # 5. Creative Filter
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.CREATIVE_FILTER,
            technique_id="TEMPO_SYNCED_FORMANT_SWEEP",
            name="Tempo-Synced Rhythmic Formant Filter",
            description="Filter modulation that moves in 1/2 bar or 1/4 note cycles to introduce vocal vowel qualities.",
            character_tags=["vocalic", "rhythmic_motion", "organic"],
            recipes=[
                DeviceRecipe("Rhythmic Filter", "Auto Filter", "query:AudioFx#Auto%20Filter", {"Filter Type": "Morph", "LFO Sync": "On", "LFO Rate": "1/2", "LFO Amount": "40%"}, "Cyclic vowel motion"),
            ]
        ))

        # 6. Frankenstein Layering
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.FRANKENSTEIN_LAYERING,
            technique_id="HYBRID_SNARE_COMPOSITE",
            name="Multi-Source Hybrid Composite",
            description="Combines transient of a clap, body of an acoustic snare, low-mid of a tom, and tail of resampled piano.",
            character_tags=["hybrid", "unrepeatable", "signature_drum"],
            recipes=[
                DeviceRecipe("Glue Compressor", "Glue Compressor", "query:AudioFx#Glue%20Compressor", {"Attack": "10 ms", "Release": "Auto", "Threshold": "-18 dB"}, "Bind distinct sources"),
            ]
        ))

        # 7. Texture & Noise
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.TEXTURE_AND_NOISE,
            technique_id="HARMONIC_REPROCESSED_PAD",
            name="Harmonic Reprocessed Pad & Formant Halo",
            description="Polifonic pad playing song's progression, reprocessed through wavefolding saturation, formant bandpass filtering, and upward OTT dynamics.",
            character_tags=["harmonic_pad", "wavefolding", "formant_halo", "reprocessed_texture"],
            recipes=[
                DeviceRecipe("Harmonic Saturator", "Saturator", "query:AudioFx#Saturator", {"Drive": "+6.5 dB", "Curve": "Sinoid Fold", "Color": "Warm"}, "Generate intermodulation overtones"),
                DeviceRecipe("Formant Sculptor", "EQ Eight", "query:AudioFx#EQ%20Eight", {"Band 1 Freq": "380 Hz", "Band 1 Mode": "High Pass 48dB/oct", "Band 3 Freq": "1.4 kHz", "Band 3 Gain": "+4.5 dB", "Band 3 Q": "2.2"}, "Vocal formant resonance & sub clean"),
                DeviceRecipe("OTT Dynamics", "Multiband Dynamics", "query:AudioFx#Multiband%20Dynamics", {"Amount": "45%", "Time": "100%", "Output": "0.0 dB"}, "Upward compression of micro-harmonics"),
                DeviceRecipe("Pumping Sidechain", "Compressor", "query:AudioFx#Compressor", {"Sidechain On": "1.0", "Ratio": "4:1", "Attack": "15 ms", "Release": "180 ms"}, "Rhythmic breathing locked to Kick"),
            ]
        ))

        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.TEXTURE_AND_NOISE,
            technique_id="SELF_DERIVED_VINYL_BED",
            name="Autogenous Texture Generator (Stretch 1200%)",
            description="Stretches the song's own harmonic stems by 1200% with high-pass filtering to create custom ambient noise.",
            time_stretch_ratio=12.0,
            character_tags=["autogenous", "ambient_bed", "organic_dust"],
            recipes=[
                DeviceRecipe("Sub Cutoff", "EQ Eight", "query:AudioFx#EQ%20Eight", {"Band 1 Freq": "600 Hz", "Band 1 Mode": "High Pass 48dB/oct"}, "Remove conflicting weight"),
                DeviceRecipe("Vinyl Crackle", "Vinyl Distortion", "query:AudioFx#Vinyl%20Distortion", {"Tracing Model": "On", "Pinch": "Soft", "Crackle": "-26 dB"}, "Subtle dust texture"),
            ]
        ))

        # 8. Creative Space
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.CREATIVE_SPACE,
            technique_id="REVERSE_REVERB_THROW",
            name="Pre-Drop Reverse Reverb Bloom",
            description="Captures the first chord of a hook, applies 100% wet reverb with 10s decay, and reverses the tail leading into the drop.",
            reverse=True,
            character_tags=["tension_riser", "spatial_suction", "pre_drop"],
            recipes=[
                DeviceRecipe("Deep Space Reverb", "Reverb", "query:AudioFx#Reverb", {"Decay Time": "10.0 s", "PreDelay": "30 ms", "Dry/Wet": "100%"}, "Infinite tail bloom"),
            ]
        ))

        # 9. Spatial Narrative
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.SPATIAL_NARRATIVE,
            technique_id="SECTIONAL_STEREO_EXPANSION",
            name="Architectural Spatial Narrative Progression",
            description="Dynamic width control across sections: Intro 40% -> Verse 70% -> Hook 120% -> Bridge 30% -> Hook 3 140%.",
            character_tags=["spatial_contrast", "physical_movement", "macro_dynamics"],
            recipes=[
                DeviceRecipe("Width Utility", "Utility", "query:AudioFx#Utility", {"Width": "100%", "Bass Mono": "110 Hz"}, "Sectional stereo fader"),
            ]
        ))

        # 10. Spectral Design
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.SPECTRAL_DESIGN,
            technique_id="SPECTRAL_FREEZE_PAD",
            name="Chordal Spectral Freeze & Blur",
            description="Freezes the spectral partials of a harmonic chord to synthesize a sustained crystalline pad.",
            character_tags=["spectral", "crystalline", "frozen_time"],
            recipes=[
                DeviceRecipe("Spectral Smear", "Echo", "query:AudioFx#Echo", {"Feedback": "88%", "Echo Time": "1/16", "Filter": "On"}, "Spectral diffusion feedback"),
            ]
        ))

        # 11. Convolution Recontextualization
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.CONVOLUTION_RECONTEXT,
            technique_id="SELF_IMPULSE_EXCITATION",
            name="Stem Impulse Cross-Convolution",
            description="Uses a transient stem (e.g. rimshot) as an impulse response to excite harmonic pads.",
            character_tags=["cross_timbre", "acoustic_mutation", "experimental"],
            recipes=[
                DeviceRecipe("Resonant Convolver", "Hybrid Reverb", "query:AudioFx#Hybrid%20Reverb", {"Decay": "4.2 s", "Blend": "Convolution Only"}, "Cross-synthesis excitation"),
            ]
        ))

        # 12. Micro-Chopping
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.MICRO_CHOPPING,
            technique_id="GRANULAR_MICRO_SLICE",
            name="Micro-Temporal Chopping (25-80ms)",
            description="Slices harmonic chord decay into 25-80ms grains and rearranges them into syncopated fills.",
            slice_length_ms=45,
            character_tags=["glitch", "micro_rhythm", "ear_candy"],
            recipes=[
                DeviceRecipe("Beat Repeat", "Beat Repeat", "query:AudioFx#Beat%20Repeat", {"Grid": "1/32", "Interval": "2", "Chance": "40%", "Gate": "65%"}, "Micro-stutter bursts"),
            ]
        ))

        # 13. Modulation Matrix
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.MODULATION_MATRIX,
            technique_id="DYNAMIC_ENVELOPE_FOLLOWING",
            name="Envelope-Followed Resonant Drive",
            description="Modulates filter cutoff and saturation drive proportional to the incoming audio amplitude.",
            character_tags=["reactive", "living_sound", "dynamic_timbre"],
            recipes=[
                DeviceRecipe("Auto Filter Envelope", "Auto Filter", "query:AudioFx#Auto%20Filter", {"Envelope": "+45", "Attack": "8 ms", "Release": "180 ms"}, "Dynamic opening on peaks"),
            ]
        ))

        # 14. Audio to MIDI Cycle
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.AUDIO_TO_MIDI_CYCLE,
            technique_id="TRANSIENT_PULSE_EXTRACTION",
            name="Audio Transient -> Percussion Trigger Cycle",
            description="Analyzes rendered audio transients, extracts rhythmic velocity pulses to trigger a secondary acoustic layer.",
            character_tags=["causality", "interlocked_layers", "generative_trigger"],
            recipes=[
                DeviceRecipe("Transient Extractor", "Drum Buss", "query:AudioFx#Drum%20Buss", {"Transients": "+0.60"}, "Peak accentuation for detector"),
            ]
        ))

        # 15. Bass Lab
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.BASS_LAB,
            technique_id="TRI_BAND_BASS_SCULPTOR",
            name="Tri-Band Bass Architecture",
            description="Separates sub (30-85 Hz, pure mono), warm body (100-350 Hz), and saturated upper harmonics (500 Hz+ stereo).",
            character_tags=["deep_sub", "club_punch", "analog_grit"],
            recipes=[
                DeviceRecipe("Sub Mono Anchor", "Utility", "query:AudioFx#Utility", {"Bass Mono": "110 Hz", "Width": "100%"}, "Mono sub anchor"),
                DeviceRecipe("Upper Harmonic Drive", "Saturator", "query:AudioFx#Saturator", {"Drive": "+5.5 dB", "Curve": "Analog Clip"}, "Cuts on small speakers"),
            ]
        ))

        # 16. Drum Lab
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.DRUM_LAB,
            technique_id="HYBRID_KICK_ENVELOPE",
            name="Multi-Stage Kick Architecture",
            description="Separates 55Hz sub impact, 2.5kHz beater transient, and saturated room resonance.",
            character_tags=["heavy_kick", "precise_beater", "boom_bap"],
            recipes=[
                DeviceRecipe("Kick Punch EQ", "EQ Eight", "query:AudioFx#EQ%20Eight", {"Band 1 Freq": "52 Hz", "Band 1 Gain": "+2.5 dB", "Band 3 Freq": "2800 Hz", "Band 3 Gain": "+3.0 dB"}, "Sculpt punch and click"),
                DeviceRecipe("Drum Glue", "Glue Compressor", "query:AudioFx#Glue%20Compressor", {"Attack": "30 ms", "Release": "0.2 s", "Ratio": "4:1"}, "Punch preservation"),
            ]
        ))

        # 17. Ear Candy Engine
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.EAR_CANDY_ENGINE,
            technique_id="VALLEY_ONE_SHOT_EVENT",
            name="Low-Density Valley Micro-Event",
            description="Injects a single, memorable sonic gesture (e.g. reverse vocal whisper, delay throw, pitch drop) into an arrangement gap.",
            character_tags=["ear_candy", "non_repetitive", "hook_accent"],
            recipes=[
                DeviceRecipe("Ping Pong Throw", "Echo", "query:AudioFx#Echo", {"Echo Time": "3/16", "Feedback": "60%", "Dry/Wet": "45%"}, "One-shot delay splash"),
            ]
        ))

        # 18. Sonic Mutation Lab
        cls._register(TechniqueDefinition(
            family=ProductionTechniqueFamily.SONIC_MUTATION_LAB,
            technique_id="COMBINATORIAL_MUTATION_PIPELINE",
            name="10-to-3 Combinatorial Mutation Generator",
            description="Permutes multiple technique families, generates candidate mutations, and filters them through psychoacoustic safety gates.",
            character_tags=["genetic_mutation", "laboratory", "aesthetic_selection"],
            recipes=[
                DeviceRecipe("Master Mutation Bus", "Utility", "query:AudioFx#Utility", {"Gain": "-1.5 dB"}, "Safety headroom"),
            ]
        ))

    @classmethod
    def _register(cls, tech: TechniqueDefinition) -> None:
        cls._catalog[tech.technique_id] = tech

    @classmethod
    def get_technique(cls, technique_id: str) -> Optional[TechniqueDefinition]:
        cls.initialize_catalog()
        return cls._catalog.get(technique_id)

    @classmethod
    def list_techniques_for_family(cls, family: ProductionTechniqueFamily) -> List[TechniqueDefinition]:
        cls.initialize_catalog()
        return [t for t in cls._catalog.values() if t.family == family]

    @classmethod
    def get_all_families(cls) -> List[ProductionTechniqueFamily]:
        return list(ProductionTechniqueFamily)

    @classmethod
    def get_all_techniques(cls) -> Dict[str, TechniqueDefinition]:
        cls.initialize_catalog()
        return dict(cls._catalog)

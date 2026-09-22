# engine/sound_design/harmonic_transformation_suite.py
"""
Universal Harmonic Transformation Suite (UHTS):
Comprehensive 20-Profile Sound Design & Reprocessing Architecture.
Enables musical material originating from ANY plugin or instrument
(Arturia Pigments, Serum, Vital, FAW SubLab XL, Analog Lab, Drift, Operator,
Simpler, audio tracks, or live vocals) to be dynamically reprocessed into
cohesive, harmonic overtones, non-linear wavefolding, vocal formant resonance,
and upward dynamic textures tailored to the song's musical DNA.

Supports:
1. Real-Time In-DAW Live Suite: Builds and injects physical device chains (Saturator,
   EQ Eight, Auto Filter, Multiband Dynamics, Redux, Drum Buss, Chorus, Utility, Reverb, Delay)
   directly onto tracks in Ableton Live 12 Suite.
2. Offline Resampling & Resynthesis: Renders phrase from source plugin/track, applies
   the multi-stage HRP DSP pipeline (polyphonic detuning, wavefolding, formant resonance,
   OTT upward expansion, Butterworth HPF, time-stretch, reverse), and deploys as a new
   transformed layer or instrument.
"""

from __future__ import annotations
import os
import math
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from engine.sound_design.technique_catalog import (
    DeviceRecipe,
    ProductionTechniqueFamily,
    TechniqueDefinition,
)
from engine.audio_genesis.render_engine import RenderToAudioEngine, RenderRequest
from engine.audio_genesis.mutation_engine import SampleMutationEngine, GenesisPipelineType
from engine.audio_genesis.provenance import AudioProvenanceEngine
from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("HarmonicTransformationSuite")


class HarmonicProfile(str, Enum):
    """The 20 canonical harmonic transformation profiles."""
    PAD_ATMOSPHERE = "PAD_ATMOSPHERE"                     # 1. Expansive harmonic pad with dense overtones & space
    METALLIC_WAVEFOLDER = "METALLIC_WAVEFOLDER"           # 2. Sharp inharmonic FM bite for leads, plucks, bells
    VOCAL_FORMANT = "VOCAL_FORMANT"                       # 3. Organic human vowel/throat body on synths & chords
    INDUSTRIAL_CRUNCH = "INDUSTRIAL_CRUNCH"               # 4. Dark distorted texture with OTT upward tail
    SUB_SAFE_BASS = "SUB_SAFE_BASS"                       # 5. Upper harmonic warmth while keeping sub mono & clean
    ETHEREAL_SHIMMER = "ETHEREAL_SHIMMER"                 # 6. Octave-lifted diffuse shimmer halo
    DARK_DRONE_SUB_GROWL = "DARK_DRONE_SUB_GROWL"         # 7. Cinematic low-end rumble with 2nd harmonic saturation
    GRANULAR_TEXTURE_CLOUD = "GRANULAR_TEXTURE_CLOUD"     # 8. Granular cloud with extreme time-stretch & micro-jitter
    RESAMPLE_TAPE_WARP = "RESAMPLE_TAPE_WARP"             # 9. Vintage tape wow/flutter & analog bias saturation
    INHARMONIC_BELL_CLUSTER = "INHARMONIC_BELL_CLUSTER"   # 10. Inharmonic metallic ring modulation & 5th/7th partials
    REVERSE_SPECTRAL_GHOST = "REVERSE_SPECTRAL_GHOST"     # 11. Pre-drop reverse swell with 100% wet diffusion tail
    LOFI_BIT_CRUSHER_DIRT = "LOFI_BIT_CRUSHER_DIRT"       # 12. 12-bit decimation & tube dirt with low-pass roll
    PSYCHOACOUSTIC_HAAS_WIDENER = "PSYCHOACOUSTIC_HAAS_WIDENER" # 13. Micro-delay Haas (15-25ms) & side excitation
    VOCAL_CHOP_DISSECTOR = "VOCAL_CHOP_DISSECTOR"         # 14. 16th-note rhythmic chop with formant envelope pumping
    OCTAVE_FUZZ_MONSTER = "OCTAVE_FUZZ_MONSTER"           # 15. Upper octave rectifier fuzz & mid-scoop wavefolding
    CHOPPED_RHYTHMIC_GATE = "CHOPPED_RHYTHMIC_GATE"       # 16. Patterned syncopated tremolo gating & ping-pong delay
    SPECTRAL_FREEZE_INFINITE = "SPECTRAL_FREEZE_INFINITE" # 17. Endless ambient background drone & spectral blur
    ANALOG_WARMTH_SATURATOR = "ANALOG_WARMTH_SATURATOR"   # 18. Transparent triode tube & soft-knee tape gluing
    NEOPERREO_METALLIC_SNARE = "NEOPERREO_METALLIC_SNARE" # 19. Comb-filtered metallic snare & industrial room snap
    PITCH_DIVE_TENSION_RISER = "PITCH_DIVE_TENSION_RISER" # 20. Exponential pitch dive/rise with tension LPF sweep


@dataclass
class HarmonicSuiteConfig:
    """Configurable acoustic and processing parameters for a transformation profile."""
    profile: HarmonicProfile
    name: str
    description: str
    drive_db: float = 6.0
    curve_type: str = "Sinoid Fold"            # Sinoid Fold, Hard Curve, Analog Clip, Soft Sine
    formant_freq_hz: float = 1800.0
    formant_q: float = 6.0
    hpf_cutoff_hz: float = 350.0
    ott_depth: float = 0.65                    # 0.0 to 1.0 upward dynamics intensity
    space_wet: float = 0.28
    stereo_spread: float = 0.75
    time_stretch_ratio: float = 1.0            # For offline resampling
    reverse: bool = False                      # For offline reverse tails
    pitch_semitones: int = 0                   # Transposition offset
    special_device: Optional[str] = None       # redux, drum_buss, beat_repeat, haas_delay, chorus
    source_instrument_type: str = "general"    # pigments, serum, vital, sublab, drift, simpler, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile.value,
            "name": self.name,
            "description": self.description,
            "drive_db": self.drive_db,
            "curve_type": self.curve_type,
            "formant_freq_hz": self.formant_freq_hz,
            "formant_q": self.formant_q,
            "hpf_cutoff_hz": self.hpf_cutoff_hz,
            "ott_depth": self.ott_depth,
            "space_wet": self.space_wet,
            "stereo_spread": self.stereo_spread,
            "time_stretch_ratio": self.time_stretch_ratio,
            "reverse": self.reverse,
            "pitch_semitones": self.pitch_semitones,
            "special_device": self.special_device,
            "source_instrument_type": self.source_instrument_type,
        }


class HarmonicTransformationSuite:
    """
    Coordinates real-time effect chains and offline self-sampling resynthesis
    for any instrument or plugin in the project across 20 distinct profiles.
    """

    DEFAULT_PROFILES: Dict[HarmonicProfile, HarmonicSuiteConfig] = {
        # 1. Atmospheric Pad Reprocessor
        HarmonicProfile.PAD_ATMOSPHERE: HarmonicSuiteConfig(
            profile=HarmonicProfile.PAD_ATMOSPHERE,
            name="Atmospheric Pad Reprocessor",
            description="Transforms any keys/synth chord into an evolving harmonic pad with sinoid fold warmth and long space.",
            drive_db=5.8,
            curve_type="Sinoid Fold",
            formant_freq_hz=1650.0,
            formant_q=4.5,
            hpf_cutoff_hz=350.0,
            ott_depth=0.70,
            space_wet=0.35,
            stereo_spread=0.85,
            time_stretch_ratio=2.5,
        ),
        # 2. Metallic FM Wavefolder
        HarmonicProfile.METALLIC_WAVEFOLDER: HarmonicSuiteConfig(
            profile=HarmonicProfile.METALLIC_WAVEFOLDER,
            name="Metallic FM Wavefolder",
            description="Adds sharp non-linear inharmonic overtones to leads and plucks with fast compression.",
            drive_db=8.5,
            curve_type="Hard Curve",
            formant_freq_hz=2400.0,
            formant_q=7.0,
            hpf_cutoff_hz=250.0,
            ott_depth=0.55,
            space_wet=0.18,
            stereo_spread=0.60,
            special_device="chorus",
        ),
        # 3. Vocal Formant Throat Body
        HarmonicProfile.VOCAL_FORMANT: HarmonicSuiteConfig(
            profile=HarmonicProfile.VOCAL_FORMANT,
            name="Vocal Formant Throat Body",
            description="Imparts organic human vowel resonance to synths and textured loops with M/S width.",
            drive_db=4.5,
            curve_type="Soft Sine",
            formant_freq_hz=1850.0,
            formant_q=8.0,
            hpf_cutoff_hz=300.0,
            ott_depth=0.60,
            space_wet=0.25,
            stereo_spread=0.70,
        ),
        # 4. Industrial Crunch & OTT
        HarmonicProfile.INDUSTRIAL_CRUNCH: HarmonicSuiteConfig(
            profile=HarmonicProfile.INDUSTRIAL_CRUNCH,
            name="Industrial Crunch & OTT",
            description="Heavy saturation and extreme upward dynamics for dark reggaeton, midtempo, and industrial perreo.",
            drive_db=11.2,
            curve_type="Sinoid Fold",
            formant_freq_hz=1200.0,
            formant_q=5.0,
            hpf_cutoff_hz=180.0,
            ott_depth=0.90,
            space_wet=0.12,
            stereo_spread=0.50,
            special_device="drum_buss",
        ),
        # 5. Sub-Safe Harmonic Bass Exciter
        HarmonicProfile.SUB_SAFE_BASS: HarmonicSuiteConfig(
            profile=HarmonicProfile.SUB_SAFE_BASS,
            name="Sub-Safe Harmonic Bass Exciter",
            description="Adds rich 2nd and 3rd harmonics to 808/sub-bass while strictly preserving sub <100Hz in pure mono.",
            drive_db=7.0,
            curve_type="Analog Clip",
            formant_freq_hz=650.0,
            formant_q=3.0,
            hpf_cutoff_hz=35.0,
            ott_depth=0.40,
            space_wet=0.0,
            stereo_spread=0.0,  # Strict mono
        ),
        # 6. Ethereal Shimmer Diffusion
        HarmonicProfile.ETHEREAL_SHIMMER: HarmonicSuiteConfig(
            profile=HarmonicProfile.ETHEREAL_SHIMMER,
            name="Ethereal Shimmer Diffusion",
            description="Upper-octave harmonic resonance and wide modulated diffusion halo floating behind the main signal.",
            drive_db=3.5,
            curve_type="Soft Sine",
            formant_freq_hz=3200.0,
            formant_q=5.5,
            hpf_cutoff_hz=500.0,
            ott_depth=0.80,
            space_wet=0.50,
            stereo_spread=1.0,
            pitch_semitones=12,
        ),
        # 7. Dark Drone & Sub Growl
        HarmonicProfile.DARK_DRONE_SUB_GROWL: HarmonicSuiteConfig(
            profile=HarmonicProfile.DARK_DRONE_SUB_GROWL,
            name="Dark Drone & Sub Growl",
            description="Cinematic low-end rumble with 2nd harmonic saturation, slow LPF modulation, and strict mono lock.",
            drive_db=9.5,
            curve_type="Hard Curve",
            formant_freq_hz=140.0,
            formant_q=3.5,
            hpf_cutoff_hz=28.0,
            ott_depth=0.50,
            space_wet=0.05,
            stereo_spread=0.0,  # Mono lock
            time_stretch_ratio=3.0,
        ),
        # 8. Granular Cloud & Micro-Jitter
        HarmonicProfile.GRANULAR_TEXTURE_CLOUD: HarmonicSuiteConfig(
            profile=HarmonicProfile.GRANULAR_TEXTURE_CLOUD,
            name="Granular Cloud & Micro-Jitter",
            description="Dense granular cloud with extreme time-stretch (400%), micro-pitch detuning, and ambient freeze.",
            drive_db=4.0,
            curve_type="Sinoid Fold",
            formant_freq_hz=2100.0,
            formant_q=4.0,
            hpf_cutoff_hz=400.0,
            ott_depth=0.75,
            space_wet=0.45,
            stereo_spread=0.95,
            time_stretch_ratio=4.0,
        ),
        # 9. Vintage Tape Wow & Flutter
        HarmonicProfile.RESAMPLE_TAPE_WARP: HarmonicSuiteConfig(
            profile=HarmonicProfile.RESAMPLE_TAPE_WARP,
            name="Vintage Tape Wow & Flutter",
            description="Saturated analog tape bias, subtle pitch flutter (1.2 Hz), and soft high-shelf damping at 5.5 kHz.",
            drive_db=5.0,
            curve_type="Analog Clip",
            formant_freq_hz=900.0,
            formant_q=2.5,
            hpf_cutoff_hz=150.0,
            ott_depth=0.45,
            space_wet=0.15,
            stereo_spread=0.65,
            special_device="chorus",
        ),
        # 10. Inharmonic Bell Cluster
        HarmonicProfile.INHARMONIC_BELL_CLUSTER: HarmonicSuiteConfig(
            profile=HarmonicProfile.INHARMONIC_BELL_CLUSTER,
            name="Inharmonic Bell Cluster",
            description="Inharmonic ring modulation overtones with resonant 5th and 7th harmonic partials and crisp attack.",
            drive_db=7.5,
            curve_type="Sinoid Fold",
            formant_freq_hz=2800.0,
            formant_q=6.5,
            hpf_cutoff_hz=350.0,
            ott_depth=0.65,
            space_wet=0.30,
            stereo_spread=0.80,
            pitch_semitones=7,
        ),
        # 11. Pre-Drop Reverse Spectral Halo
        HarmonicProfile.REVERSE_SPECTRAL_GHOST: HarmonicSuiteConfig(
            profile=HarmonicProfile.REVERSE_SPECTRAL_GHOST,
            name="Pre-Drop Reverse Spectral Halo",
            description="100% wet reverse reverb swell with exponential blooming tail prior to drop impacts.",
            drive_db=5.0,
            curve_type="Soft Sine",
            formant_freq_hz=2200.0,
            formant_q=4.0,
            hpf_cutoff_hz=450.0,
            ott_depth=0.85,
            space_wet=0.60,
            stereo_spread=1.0,
            reverse=True,
            time_stretch_ratio=2.0,
        ),
        # 12. 12-Bit Decimation & Tube Dirt
        HarmonicProfile.LOFI_BIT_CRUSHER_DIRT: HarmonicSuiteConfig(
            profile=HarmonicProfile.LOFI_BIT_CRUSHER_DIRT,
            name="12-Bit Decimation & Tube Dirt",
            description="Aggressive 12-bit decimation, controlled downsampling, and warm valve tube saturation.",
            drive_db=6.5,
            curve_type="Analog Clip",
            formant_freq_hz=1400.0,
            formant_q=3.0,
            hpf_cutoff_hz=200.0,
            ott_depth=0.60,
            space_wet=0.10,
            stereo_spread=0.45,
            special_device="redux",
        ),
        # 13. Psychoacoustic Haas Spatializer
        HarmonicProfile.PSYCHOACOUSTIC_HAAS_WIDENER: HarmonicSuiteConfig(
            profile=HarmonicProfile.PSYCHOACOUSTIC_HAAS_WIDENER,
            name="Psychoacoustic Haas Spatializer",
            description="Micro-delay Haas spatialization (18ms) with anti-comb filtering and side-channel harmonic excitation.",
            drive_db=3.0,
            curve_type="Soft Sine",
            formant_freq_hz=3500.0,
            formant_q=2.0,
            hpf_cutoff_hz=250.0,
            ott_depth=0.40,
            space_wet=0.20,
            stereo_spread=1.20,
            special_device="haas_delay",
        ),
        # 14. Rhythmic Vocal Chop Dissector
        HarmonicProfile.VOCAL_CHOP_DISSECTOR: HarmonicSuiteConfig(
            profile=HarmonicProfile.VOCAL_CHOP_DISSECTOR,
            name="Rhythmic Vocal Chop Dissector",
            description="16th-note rhythmic chop gating with formant envelope following and rhythmic sidechain ducking.",
            drive_db=6.0,
            curve_type="Sinoid Fold",
            formant_freq_hz=2600.0,
            formant_q=5.0,
            hpf_cutoff_hz=220.0,
            ott_depth=0.70,
            space_wet=0.25,
            stereo_spread=0.75,
            special_device="beat_repeat",
        ),
        # 15. Octave Fuzz & Mid Scoop
        HarmonicProfile.OCTAVE_FUZZ_MONSTER: HarmonicSuiteConfig(
            profile=HarmonicProfile.OCTAVE_FUZZ_MONSTER,
            name="Octave Fuzz & Mid Scoop",
            description="Rectifier upper octave fuzz, severe non-linear wavefolding, mid-box notch (650Hz), and hard ceiling.",
            drive_db=12.0,
            curve_type="Hard Curve",
            formant_freq_hz=3000.0,
            formant_q=3.5,
            hpf_cutoff_hz=180.0,
            ott_depth=0.85,
            space_wet=0.10,
            stereo_spread=0.60,
            pitch_semitones=12,
        ),
        # 16. Syncopated Patterned Gater
        HarmonicProfile.CHOPPED_RHYTHMIC_GATE: HarmonicSuiteConfig(
            profile=HarmonicProfile.CHOPPED_RHYTHMIC_GATE,
            name="Syncopated Patterned Gater",
            description="1/16 syncopated tremolo gating with resonant filter movement and dotted-8th ping-pong delay.",
            drive_db=5.5,
            curve_type="Sinoid Fold",
            formant_freq_hz=1500.0,
            formant_q=4.5,
            hpf_cutoff_hz=250.0,
            ott_depth=0.70,
            space_wet=0.30,
            stereo_spread=0.85,
            special_device="beat_repeat",
        ),
        # 17. Infinite Spectral Blur Bed
        HarmonicProfile.SPECTRAL_FREEZE_INFINITE: HarmonicSuiteConfig(
            profile=HarmonicProfile.SPECTRAL_FREEZE_INFINITE,
            name="Infinite Spectral Blur Bed",
            description="Endless ambient background drone with spectral blur, zero attack transients, and slow chorus drift.",
            drive_db=2.5,
            curve_type="Soft Sine",
            formant_freq_hz=1100.0,
            formant_q=2.0,
            hpf_cutoff_hz=320.0,
            ott_depth=0.60,
            space_wet=0.55,
            stereo_spread=0.90,
            time_stretch_ratio=5.0,
        ),
        # 18. Triode Tube & Tape Warmth
        HarmonicProfile.ANALOG_WARMTH_SATURATOR: HarmonicSuiteConfig(
            profile=HarmonicProfile.ANALOG_WARMTH_SATURATOR,
            name="Triode Tube & Tape Warmth",
            description="Transparent even-harmonic excitation, soft-knee analog gluing, and subtle high-frequency air.",
            drive_db=3.8,
            curve_type="Soft Sine",
            formant_freq_hz=850.0,
            formant_q=1.5,
            hpf_cutoff_hz=80.0,
            ott_depth=0.35,
            space_wet=0.08,
            stereo_spread=0.70,
        ),
        # 19. Comb-Filter Metallic Resonator
        HarmonicProfile.NEOPERREO_METALLIC_SNARE: HarmonicSuiteConfig(
            profile=HarmonicProfile.NEOPERREO_METALLIC_SNARE,
            name="Comb-Filter Metallic Resonator",
            description="Resonant comb-filter tuned to 1.2 kHz, sinoid wavefold sizzle, and industrial small-room snap.",
            drive_db=8.0,
            curve_type="Sinoid Fold",
            formant_freq_hz=1200.0,
            formant_q=9.0,
            hpf_cutoff_hz=160.0,
            ott_depth=0.50,
            space_wet=0.18,
            stereo_spread=0.55,
            special_device="drum_buss",
        ),
        # 20. Exponential Pitch-Dive Riser
        HarmonicProfile.PITCH_DIVE_TENSION_RISER: HarmonicSuiteConfig(
            profile=HarmonicProfile.PITCH_DIVE_TENSION_RISER,
            name="Exponential Pitch-Dive Riser",
            description="Exponential pitch glide riser with dynamic opening high-pass filter sweep and vacuum cut.",
            drive_db=7.0,
            curve_type="Hard Curve",
            formant_freq_hz=2500.0,
            formant_q=4.0,
            hpf_cutoff_hz=200.0,
            ott_depth=0.85,
            space_wet=0.40,
            stereo_spread=0.90,
            time_stretch_ratio=2.0,
        ),
    }

    @classmethod
    def get_config(
        cls,
        profile: HarmonicProfile | str,
        source_instrument_type: str = "general"
    ) -> HarmonicSuiteConfig:
        """Resolves configuration for the given profile and adapts to source instrument type."""
        p_enum = HarmonicProfile(profile) if isinstance(profile, str) else profile
        base = cls.DEFAULT_PROFILES.get(p_enum, cls.DEFAULT_PROFILES[HarmonicProfile.PAD_ATMOSPHERE])

        # Adapt slightly according to source plugin/instrument
        inst = source_instrument_type.lower()
        adapted = HarmonicSuiteConfig(
            profile=base.profile,
            name=base.name,
            description=base.description,
            drive_db=base.drive_db,
            curve_type=base.curve_type,
            formant_freq_hz=base.formant_freq_hz,
            formant_q=base.formant_q,
            hpf_cutoff_hz=base.hpf_cutoff_hz,
            ott_depth=base.ott_depth,
            space_wet=base.space_wet,
            stereo_spread=base.stereo_spread,
            time_stretch_ratio=base.time_stretch_ratio,
            reverse=base.reverse,
            pitch_semitones=base.pitch_semitones,
            special_device=base.special_device,
            source_instrument_type=source_instrument_type,
        )

        if "sublab" in inst or "808" in inst or "bass" in inst:
            # Protect sub even more vigorously
            adapted.hpf_cutoff_hz = max(28.0, min(adapted.hpf_cutoff_hz, 40.0))
            adapted.stereo_spread = 0.0
        elif "pigments" in inst or "serum" in inst or "vital" in inst:
            # Digital wavetable/FM can take slightly warmer sinoid fold
            if adapted.profile not in [HarmonicProfile.INDUSTRIAL_CRUNCH, HarmonicProfile.OCTAVE_FUZZ_MONSTER]:
                adapted.drive_db = min(adapted.drive_db, 7.5)

        return adapted

    @classmethod
    def build_device_chain(
        cls,
        profile: HarmonicProfile | str,
        source_instrument_type: str = "general",
        prefer_vst: bool = True
    ) -> List[DeviceRecipe]:
        """
        Builds a concrete list of DeviceRecipes ready to be loaded onto any Ableton Live track.
        Adapts dynamically based on the chosen HarmonicProfile and special devices.
        """
        cfg = cls.get_config(profile, source_instrument_type)
        recipes: List[DeviceRecipe] = []

        # 1. Pre-EQ: High-Pass Filter & Formant Body / Notch
        eq_params = {
            "Filter 1 Type": 1,          # High Pass
            "Filter 1 Frequency": cfg.hpf_cutoff_hz,
            "Filter 1 Q": 0.71,
            "Filter 4 Type": 3,          # Peak for formant body
            "Filter 4 Frequency": cfg.formant_freq_hz,
            "Filter 4 Q": cfg.formant_q,
            "Filter 4 Gain": 3.5,
        }
        recipes.append(DeviceRecipe(
            recipe_name="Pre_EQ_Formant_Guard",
            device_name="EQ Eight",
            device_uri="query:AudioFx#EQ%20Eight",
            parameters=eq_params,
            purpose=f"High-pass low cut at {cfg.hpf_cutoff_hz}Hz and formant shaping at {cfg.formant_freq_hz}Hz."
        ))

        # 2. Special Pre-processor: Redux (for Lo-Fi bit crushing)
        if cfg.special_device == "redux":
            recipes.append(DeviceRecipe(
                recipe_name="Bit_Decimator",
                device_name="Redux",
                device_uri="query:AudioFx#Redux",
                parameters={"Bit Depth": 12.0, "Downsample Rate": 3.0},
                purpose="12-bit decimation and retro sub-sampling."
            ))

        # 3. Wavefolder / Non-linear Saturator
        sat_params = {
            "Drive": cfg.drive_db,
            "Curve Type": 4 if "sinoid" in cfg.curve_type.lower() else (2 if "hard" in cfg.curve_type.lower() else 0),
            "Output": -1.5,
            "Dry/Wet": 100.0,
            "Color": 0.35,
        }
        recipes.append(DeviceRecipe(
            recipe_name="Harmonic_Wavefolder",
            device_name="Saturator",
            device_uri="query:AudioFx#Saturator",
            parameters=sat_params,
            purpose=f"Non-linear {cfg.curve_type} saturation adding 2nd, 3rd, and 5th harmonic overtones."
        ))

        # 4. Special Dynamic / Character Processor: Drum Buss (for Industrial Crunch / Neoperreo Snare)
        if cfg.special_device == "drum_buss":
            recipes.append(DeviceRecipe(
                recipe_name="Drum_Buss_Punch",
                device_name="Drum Buss",
                device_uri="query:AudioFx#Drum%20Buss",
                parameters={"Drive": 0.30, "Crunch": 0.40, "Transients": 1.5},
                purpose="Aggressive crunch and physical transient bite."
            ))

        # 5. Formant Shaping / Auto Filter (for resonant, vocal, or gating profiles)
        if cfg.formant_q >= 4.0 or cfg.profile in [
            HarmonicProfile.VOCAL_FORMANT,
            HarmonicProfile.PAD_ATMOSPHERE,
            HarmonicProfile.METALLIC_WAVEFOLDER,
            HarmonicProfile.NEOPERREO_METALLIC_SNARE,
            HarmonicProfile.CHOPPED_RHYTHMIC_GATE,
        ]:
            filter_params = {
                "Filter Type": 1,        # Bandpass
                "Frequency": cfg.formant_freq_hz,
                "Resonance": min(0.95, cfg.formant_q / 10.0),
                "Env Modulation": 0.20,
                "Dry/Wet": 75.0,
            }
            recipes.append(DeviceRecipe(
                recipe_name="Formant_Vowel_Resonator",
                device_name="Auto Filter",
                device_uri="query:AudioFx#Auto%20Filter",
                parameters=filter_params,
                purpose="Organic vocal vowel formant shaping."
            ))

        # 6. Special Modulation: Beat Repeat (for rhythmic vocal chopping or gating)
        if cfg.special_device == "beat_repeat":
            recipes.append(DeviceRecipe(
                recipe_name="Rhythmic_Slicer_Gate",
                device_name="Beat Repeat",
                device_uri="query:AudioFx#Beat%20Repeat",
                parameters={"Grid": "1/16", "Chance": 70.0, "Gate": 4.0, "Mix": 100.0},
                purpose="Syncopated 16th-note slicing and stutter gating."
            ))

        # 7. Special Modulation: Chorus-Ensemble (for tape wow/flutter, shimmer, or metallic widening)
        if cfg.special_device == "chorus" or cfg.profile in [HarmonicProfile.RESAMPLE_TAPE_WARP, HarmonicProfile.ETHEREAL_SHIMMER]:
            recipes.append(DeviceRecipe(
                recipe_name="Modulation_Chorus",
                device_name="Chorus-Ensemble",
                device_uri="query:AudioFx#Chorus-Ensemble",
                parameters={"Rate": 1.2, "Amount": 0.45, "Warmth": 0.30},
                purpose="Micro-pitch detuning and organic wow/flutter modulation."
            ))

        # 8. Upward Dynamics (Multiband Dynamics / OTT)
        if cfg.ott_depth > 0.1:
            mb_params = {
                "Amount": cfg.ott_depth * 100.0,
                "Time": 100.0,
                "Output": 0.0,
            }
            recipes.append(DeviceRecipe(
                recipe_name="OTT_Upward_Expander",
                device_name="Multiband Dynamics",
                device_uri="query:AudioFx#Multiband%20Dynamics",
                parameters=mb_params,
                purpose=f"Upward dynamics expansion (depth {int(cfg.ott_depth*100)}%) exhuming subtle harmonic decay details."
            ))

        # 9. Special Delay: Haas Spatializer
        if cfg.special_device == "haas_delay":
            recipes.append(DeviceRecipe(
                recipe_name="Haas_Micro_Delay",
                device_name="Delay",
                device_uri="query:AudioFx#Delay",
                parameters={"Delay 1 Time": 1.0, "Delay 2 Time": 18.0, "Feedback": 0.0, "Dry/Wet": 100.0},
                purpose="Psychoacoustic Haas micro-delay widening (18ms offset)."
            ))

        # 10. Spatial Diffusion / Space (if space_wet > 0)
        if cfg.space_wet > 0.0:
            if prefer_vst:
                recipes.append(DeviceRecipe(
                    recipe_name="Valhalla_Lush_Space",
                    device_name="ValhallaVintageVerb",
                    device_uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
                    parameters={"Mix": cfg.space_wet, "Decay": 2.5 if cfg.profile != HarmonicProfile.NEOPERREO_METALLIC_SNARE else 0.8},
                    purpose="Silky vintage diffusion and spatial depth."
                ))
            else:
                recipes.append(DeviceRecipe(
                    recipe_name="Native_Reverb_Space",
                    device_name="Reverb",
                    device_uri="query:AudioFx#Reverb",
                    parameters={"Dry/Wet": cfg.space_wet * 100.0, "Decay Time": 2200.0},
                    purpose="Native spatial diffusion tail."
                ))

        # 11. Utility (Stereo Width & Bass Mono Guard)
        util_params = {
            "Width": cfg.stereo_spread * 100.0,
            "Bass Mono": 1 if cfg.stereo_spread < 0.9 else 0,
            "Bass Mono Frequency": 120.0,
            "Gain": -1.0,
        }
        recipes.append(DeviceRecipe(
            recipe_name="Stereo_Width_Mono_Guard",
            device_name="Utility",
            device_uri="query:AudioFx#Utility",
            parameters=util_params,
            purpose=f"Stereo spread ({int(cfg.stereo_spread*100)}%) with sub-mono safety guard."
        ))

        return recipes

    @classmethod
    def apply_to_live_track(
        cls,
        track_index: int,
        profile: HarmonicProfile | str = HarmonicProfile.PAD_ATMOSPHERE,
        source_instrument_type: str = "general",
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Loads the physical device chain of the chosen HarmonicProfile directly onto
        the specified track in Ableton Live 12 Suite via AbletonMCP socket connection.
        """
        recipes = cls.build_device_chain(profile, source_instrument_type)
        loaded_devices: List[str] = []

        if conn is None:
            try:
                from server import get_ableton_connection
                conn = get_ableton_connection()
            except Exception as e:
                logger.warning(f"Could not initialize direct Ableton connection: {e}")

        if conn:
            for r in recipes:
                try:
                    logger.info(f"Loading device '{r.device_name}' on track {track_index}...")
                    conn.send_command("load_browser_item", {
                        "track_index": track_index,
                        "item_uri": r.device_uri
                    })
                    loaded_devices.append(r.device_name)
                except Exception as ex:
                    logger.warning(f"Failed to load device URI {r.device_uri}: {ex}. Attempting native fallback...")
                    if "Valhalla" in r.device_name:
                        conn.send_command("load_browser_item", {
                            "track_index": track_index,
                            "item_uri": "query:AudioFx#Reverb"
                        })
                        loaded_devices.append("Reverb (Fallback)")

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "profile": str(profile),
            "source_instrument_type": source_instrument_type,
            "recipes_count": len(recipes),
            "loaded_devices": loaded_devices,
        }

    @classmethod
    def transform_source_to_layer(
        cls,
        source_track_index: int,
        target_role: str = "TEXTURE_FOLEY",
        song_dna: Optional[CompositionalDNA] = None,
        profile: HarmonicProfile | str = HarmonicProfile.PAD_ATMOSPHERE,
        source_instrument_name: str = "Synthesizer Plugin",
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Self-Sampling Resynthesis:
        1. Takes any track/plugin as source.
        2. Renders source audio (or synthesizes reference phrase based on song DNA).
        3. Runs through the HRP dynamic mutation DSP (frequencies, wavefolding, formant resonance, OTT).
        4. Returns the physical asset ready for deployment into Simpler or Audio clip.
        """
        cfg = cls.get_config(profile, source_instrument_name)
        provenance_engine = AudioProvenanceEngine()
        render_engine = RenderToAudioEngine(provenance_engine=provenance_engine, conn=conn)
        mutation_engine = SampleMutationEngine(provenance_engine=provenance_engine)

        # Step 1: Render material from source plugin/instrument
        render_req = RenderRequest(
            track_name=f"Track_{source_track_index}_{source_instrument_name}",
            clip_name="Phrase",
            bars=(1, 4),
            instrument_name=source_instrument_name,
            device_category="keys" if "pad" in str(profile).lower() else "lead",
            song_dna=song_dna,
            role=target_role
        )
        render_res = render_engine.render_material(render_req)

        # Step 2: Mutate with Harmonic Reprocessed Pad DSP
        mutation_res = mutation_engine.execute_genesis(
            source_record=render_res.provenance_record,
            pipeline_type=GenesisPipelineType.FREEZE_PAD,
            target_destination="Simpler",
            custom_params={
                "pitch_shift_semitones": cfg.pitch_semitones,
                "drive_db": cfg.drive_db,
                "stretch_ratio": cfg.time_stretch_ratio,
                "target_key": getattr(song_dna.harmonic_palette, "key_root", "F") if song_dna and hasattr(song_dna, "harmonic_palette") and song_dna.harmonic_palette else "F",
                "scale_mode": getattr(song_dna.harmonic_palette, "scale", getattr(song_dna.harmonic_palette, "scale_mode", "phrygian")) if song_dna and hasattr(song_dna, "harmonic_palette") and song_dna.harmonic_palette else "phrygian",
                "formant_freq_hz": cfg.formant_freq_hz,
            }
        )

        return {
            "status": "SUCCESS",
            "source_track_index": source_track_index,
            "source_instrument": source_instrument_name,
            "profile": cfg.profile.value,
            "transformed_sample_id": mutation_res.mutated_sample_id,
            "audio_path": mutation_res.audio_path,
            "target_role": target_role,
            "duration_sec": mutation_res.metadata.duration_sec,
            "description": mutation_res.mutation_description,
        }

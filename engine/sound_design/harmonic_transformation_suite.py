# engine/sound_design/harmonic_transformation_suite.py
"""
Universal Harmonic Transformation Suite (UHTS):
Enables musical material originating from ANY plugin or instrument
(Arturia Pigments, Serum, Vital, FAW SubLab XL, Analog Lab, Drift, Operator,
Simpler, audio tracks, or live vocals) to be dynamically reprocessed into
cohesive, harmonic overtones, non-linear wavefolding, vocal formant resonance,
and upward dynamic textures tailored to the song's musical DNA.

Supports:
1. Real-Time In-DAW Live Suite: Builds and injects physical device chains (Saturator,
   EQ Eight, Auto Filter, Multiband Dynamics, Chorus, Utility, Reverb) directly onto tracks.
2. Offline Resampling & Resynthesis: Renders phrase from source plugin/track, applies
   the multi-stage HRP DSP pipeline (polyphonic detuning, wavefolding, formant resonance,
   OTT upward expansion, Butterworth HPF), and deploys as a new transformed layer.
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
    """Specialized harmonic transformation profiles tailored to sonic roles."""
    PAD_ATMOSPHERE = "PAD_ATMOSPHERE"          # Expansive harmonic pad with dense overtones & space
    METALLIC_WAVEFOLDER = "METALLIC_WAVEFOLDER"  # Sharp inharmonic FM bite for leads, plucks, bells
    VOCAL_FORMANT = "VOCAL_FORMANT"            # Organic human vowel/throat body on synths & chords
    INDUSTRIAL_CRUNCH = "INDUSTRIAL_CRUNCH"    # Dark distorted texture with OTT upward tail
    SUB_SAFE_BASS = "SUB_SAFE_BASS"            # Upper harmonic warmth while keeping sub mono & clean
    ETHEREAL_SHIMMER = "ETHEREAL_SHIMMER"      # Octave-lifted diffuse shimmer halo


@dataclass
class HarmonicSuiteConfig:
    """Configurable acoustic parameters for a transformation profile."""
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
            "source_instrument_type": self.source_instrument_type,
        }


class HarmonicTransformationSuite:
    """
    Coordinates real-time effect chains and offline self-sampling resynthesis
    for any instrument or plugin in the project.
    """

    DEFAULT_PROFILES: Dict[HarmonicProfile, HarmonicSuiteConfig] = {
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
        ),
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
        ),
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
        ),
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
        ),
    }

    @classmethod
    def get_config(
        cls,
        profile: HarmonicProfile | str,
        source_instrument_type: str = "general"
    ) -> HarmonicSuiteConfig:
        """Resolves configuration for the given profile and source instrument type."""
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
            source_instrument_type=source_instrument_type,
        )

        if "sublab" in inst or "808" in inst or "bass" in inst:
            # Protect sub even more vigorously
            adapted.hpf_cutoff_hz = max(30.0, min(adapted.hpf_cutoff_hz, 40.0))
            adapted.stereo_spread = 0.0
        elif "pigments" in inst or "serum" in inst or "vital" in inst:
            # Digital wavetable/FM can take slightly warmer sinoid fold
            if adapted.profile != HarmonicProfile.INDUSTRIAL_CRUNCH:
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
        Combines EQ Eight (pre-cleaning & formant resonance), Saturator (wavefolding),
        Multiband Dynamics (OTT upward lift), Chorus-Ensemble / Utility, and Reverb.
        """
        cfg = cls.get_config(profile, source_instrument_type)
        recipes: List[DeviceRecipe] = []

        # 1. Pre-EQ: High-Pass Filter & Mud Notch
        eq_params = {
            "Filter 1 Type": 1,          # High Pass
            "Filter 1 Frequency": cfg.hpf_cutoff_hz,
            "Filter 1 Q": 0.71,
            "Filter 4 Type": 3,          # Peak Notch for formant body
            "Filter 4 Frequency": cfg.formant_freq_hz,
            "Filter 4 Q": cfg.formant_q,
            "Filter 4 Gain": 3.0,
        }
        recipes.append(DeviceRecipe(
            recipe_name="Pre_EQ_Formant_Guard",
            device_name="EQ Eight",
            device_uri="query:AudioFx#EQ%20Eight",
            parameters=eq_params,
            purpose=f"High-pass protection at {cfg.hpf_cutoff_hz}Hz and formant body peaking at {cfg.formant_freq_hz}Hz."
        ))

        # 2. Wavefolder / Non-linear Saturator
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

        # 3. Formant Shaping / Auto Filter (for vocal/resonant profiles)
        if cfg.profile in [HarmonicProfile.VOCAL_FORMANT, HarmonicProfile.PAD_ATMOSPHERE, HarmonicProfile.METALLIC_WAVEFOLDER]:
            filter_params = {
                "Filter Type": 1,        # Bandpass
                "Frequency": cfg.formant_freq_hz,
                "Resonance": 0.65,
                "Env Modulation": 0.15,
                "Dry/Wet": 75.0,
            }
            recipes.append(DeviceRecipe(
                recipe_name="Formant_Vowel_Resonator",
                device_name="Auto Filter",
                device_uri="query:AudioFx#Auto%20Filter",
                parameters=filter_params,
                purpose="Organic vocal vowel formant shaping."
            ))

        # 4. Upward Dynamics (Multiband Dynamics / OTT)
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

        # 5. Spatial Diffusion / Space (if space_wet > 0)
        if cfg.space_wet > 0.0:
            if prefer_vst:
                recipes.append(DeviceRecipe(
                    recipe_name="Valhalla_Lush_Space",
                    device_name="ValhallaVintageVerb",
                    device_uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
                    parameters={"Mix": cfg.space_wet, "Decay": 2.2, "PreDelay": 15.0},
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

        # 6. Utility (Stereo Width & Bass Mono Guard)
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
                "pitch_shift_semitones": 0,
                "drive_db": cfg.drive_db,
                "stretch_ratio": 2.5,
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

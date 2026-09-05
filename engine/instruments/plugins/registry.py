# engine/instruments/plugins/registry.py
import re
import difflib
from typing import Dict, List, Optional, Union, Any
from .models import PluginProfile, PluginSemanticRole

class PluginRegistry:
    """
    Central registry of plugin parameter maps for native Ableton devices
    and 3rd party VST3s (Vital, Omnisphere, Analog Lab, Kontakt, Thermal, etc.).
    Extensible and non-limiting: Unknown devices fall back to generic semantic matching.
    """
    
    def __init__(self):
        self._profiles: Dict[str, PluginProfile] = {}
        self._init_default_profiles()

    def register_profile(self, profile: PluginProfile) -> None:
        key = self._normalize_key(profile.plugin_name)
        self._profiles[key] = profile
        for alias in profile.aliases:
            self._profiles[self._normalize_key(alias)] = profile

    def get_profile(self, device_name: str) -> Optional[PluginProfile]:
        key = self._normalize_key(device_name)
        if key in self._profiles:
            return self._profiles[key]
        
        # Exact substring search
        for prof_key, prof in self._profiles.items():
            if prof_key in key or key in prof_key:
                return prof
                
        # Difflib close match
        matches = difflib.get_close_matches(key, list(self._profiles.keys()), n=1, cutoff=0.6)
        if matches:
            return self._profiles[matches[0]]
            
        return None

    def list_registered_plugins(self) -> List[str]:
        names = set(p.plugin_name for p in self._profiles.values())
        return sorted(list(names))

    @staticmethod
    def _normalize_key(name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

    def _init_default_profiles(self) -> None:
        # 1. Vital (Matt Tytel)
        self.register_profile(PluginProfile(
            plugin_name="Vital",
            category="synth",
            is_native=False,
            aliases=["Vital", "Vital VST3", "VitalSynth", "Vital.vst3"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "filter_1_cutoff",
                PluginSemanticRole.RESONANCE: "filter_1_resonance",
                PluginSemanticRole.DRIVE: "distortion_drive",
                PluginSemanticRole.DRY_WET: "distortion_mix",
                PluginSemanticRole.ATTACK: "env_1_attack",
                PluginSemanticRole.DECAY: "env_1_decay",
                PluginSemanticRole.SUSTAIN: "env_1_sustain",
                PluginSemanticRole.RELEASE: "env_1_release",
                PluginSemanticRole.MACRO_1: "macro_1",
                PluginSemanticRole.MACRO_2: "macro_2",
                PluginSemanticRole.MACRO_3: "macro_3",
                PluginSemanticRole.MACRO_4: "macro_4",
                PluginSemanticRole.VOLUME: "volume",
            },
            semantic_aliases={
                PluginSemanticRole.CUTOFF: ["filter cutoff", "filter 1 cutoff", "cutoff", "filter_1_cutoff", "filt 1 cut"],
                PluginSemanticRole.RESONANCE: ["resonance", "filter 1 res", "filter_1_resonance", "res"],
                PluginSemanticRole.DRIVE: ["distortion drive", "drive", "distortion_drive"],
                PluginSemanticRole.ATTACK: ["env 1 attack", "attack", "env_1_attack", "amp attack"],
                PluginSemanticRole.DECAY: ["env 1 decay", "decay", "env_1_decay"],
            }
        ))

        # 2. Spectrasonics Omnisphere
        self.register_profile(PluginProfile(
            plugin_name="Omnisphere",
            category="synth",
            is_native=False,
            aliases=["Omnisphere", "Omnisphere 2", "Omnisphere.vst3"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "Filter Freq A",
                PluginSemanticRole.RESONANCE: "Filter Res A",
                PluginSemanticRole.ATTACK: "Amp Env Attack",
                PluginSemanticRole.DECAY: "Amp Env Decay",
                PluginSemanticRole.SUSTAIN: "Amp Env Sustain",
                PluginSemanticRole.RELEASE: "Amp Env Release",
                PluginSemanticRole.GLIDE: "Glide Time",
                PluginSemanticRole.VOLUME: "Master Vol",
            },
            semantic_aliases={
                PluginSemanticRole.CUTOFF: ["filter freq a", "filter cutoff", "cutoff", "freq a", "filter frequency"],
                PluginSemanticRole.RESONANCE: ["filter res a", "resonance", "res a"],
                PluginSemanticRole.VOLUME: ["master vol", "volume", "master volume", "main vol"],
            }
        ))

        # 3. Arturia Analog Lab V
        self.register_profile(PluginProfile(
            plugin_name="Analog Lab V",
            category="synth",
            is_native=False,
            aliases=["Analog Lab", "Analog Lab V", "Analog Lab Pro", "AnalogLabV.vst3"],
            parameter_mappings={
                PluginSemanticRole.MACRO_1: "Macro 1",  # Brightness
                PluginSemanticRole.MACRO_2: "Macro 2",  # Timbre
                PluginSemanticRole.MACRO_3: "Macro 3",  # Time
                PluginSemanticRole.MACRO_4: "Macro 4",  # Movement
                PluginSemanticRole.CUTOFF: "Macro 1",
                PluginSemanticRole.COLOR: "Macro 2",
                PluginSemanticRole.TIME: "Macro 3",
                PluginSemanticRole.DRY_WET: "FX1 Dry/Wet",
                PluginSemanticRole.VOLUME: "Master Volume",
            },
            semantic_aliases={
                PluginSemanticRole.CUTOFF: ["macro 1", "brightness", "cutoff", "filter cutoff"],
                PluginSemanticRole.COLOR: ["macro 2", "timbre", "color"],
                PluginSemanticRole.TIME: ["macro 3", "time"],
                PluginSemanticRole.DRY_WET: ["fx1 dry/wet", "fx 1 dry/wet", "dry/wet", "delay dry/wet", "reverb dry/wet"],
            }
        ))

        # 4. Native Instruments Kontakt 8
        self.register_profile(PluginProfile(
            plugin_name="Kontakt 8",
            category="sampler",
            is_native=False,
            aliases=["Kontakt", "Kontakt 8", "Kontakt 7", "Kontakt.vst3"],
            parameter_mappings={
                PluginSemanticRole.VOLUME: "Master Volume",
                PluginSemanticRole.DYNAMICS: "Dynamics",
                PluginSemanticRole.EXPRESSION: "Expression",
                PluginSemanticRole.CUTOFF: "Cutoff",
                PluginSemanticRole.ATTACK: "Attack",
                PluginSemanticRole.RELEASE: "Release",
            },
            semantic_aliases={
                PluginSemanticRole.VOLUME: ["master volume", "volume", "instrument volume"],
                PluginSemanticRole.DYNAMICS: ["dynamics", "modwheel", "cc1"],
                PluginSemanticRole.EXPRESSION: ["expression", "cc11"],
                PluginSemanticRole.CUTOFF: ["cutoff", "filter cutoff", "filter freq"],
            }
        ))

        # 5. Output Thermal
        self.register_profile(PluginProfile(
            plugin_name="Output Thermal",
            category="effect",
            is_native=False,
            aliases=["Thermal", "Output Thermal", "Thermal.vst3"],
            parameter_mappings={
                PluginSemanticRole.DRIVE: "Drive",
                PluginSemanticRole.COLOR: "Tone",
                PluginSemanticRole.WIDTH: "Width",
                PluginSemanticRole.DRY_WET: "Master Mix",
                PluginSemanticRole.VOLUME: "Output Volume",
            },
            semantic_aliases={
                PluginSemanticRole.DRIVE: ["drive", "stage 1 drive", "distortion", "gain"],
                PluginSemanticRole.COLOR: ["tone", "color", "frequency"],
                PluginSemanticRole.WIDTH: ["width", "stereo width", "spread"],
                PluginSemanticRole.DRY_WET: ["master mix", "mix", "dry/wet", "blend"],
            }
        ))

        # 6. Dada Life Sausage Fattener
        self.register_profile(PluginProfile(
            plugin_name="Sausage Fattener",
            category="effect",
            is_native=False,
            aliases=["Sausage Fattener", "Sausage", "SausageFattener.vst3"],
            parameter_mappings={
                PluginSemanticRole.FATNESS: "Fatness",
                PluginSemanticRole.DRIVE: "Fatness",
                PluginSemanticRole.COLOR: "Color",
                PluginSemanticRole.VOLUME: "Gain",
            },
            semantic_aliases={
                PluginSemanticRole.FATNESS: ["fatness", "fat"],
                PluginSemanticRole.DRIVE: ["fatness", "fat"],
                PluginSemanticRole.COLOR: ["color", "colour"],
                PluginSemanticRole.VOLUME: ["gain", "master gain", "output"],
            }
        ))

        # 7. The God Particle
        self.register_profile(PluginProfile(
            plugin_name="The God Particle",
            category="mastering",
            is_native=False,
            aliases=["The God Particle", "God Particle", "GodParticle.vst3"],
            parameter_mappings={
                PluginSemanticRole.DRIVE: "Input Level",
                PluginSemanticRole.FATNESS: "Amount",
                PluginSemanticRole.LIMITER_CEILING: "Limiter Ceiling",
                PluginSemanticRole.VOLUME: "Limiter Ceiling",
            },
            semantic_aliases={
                PluginSemanticRole.DRIVE: ["input level", "input", "input gain"],
                PluginSemanticRole.FATNESS: ["amount", "character", "processing"],
                PluginSemanticRole.LIMITER_CEILING: ["limiter ceiling", "ceiling", "output ceiling"],
            }
        ))

        # 8. Arturia Efx REFRACT & MOTIONS
        self.register_profile(PluginProfile(
            plugin_name="Arturia Efx REFRACT",
            category="effect",
            is_native=False,
            aliases=["Efx REFRACT", "Refract", "Efx Refract", "EfxRefract.vst3"],
            parameter_mappings={
                PluginSemanticRole.MORPH: "Morph",
                PluginSemanticRole.DEPTH: "Amount",
                PluginSemanticRole.RATE: "Rate",
                PluginSemanticRole.DRY_WET: "Dry/Wet",
            },
            semantic_aliases={
                PluginSemanticRole.MORPH: ["morph", "refraction"],
                PluginSemanticRole.DEPTH: ["amount", "depth", "refract amount"],
                PluginSemanticRole.RATE: ["rate", "speed", "frequency"],
                PluginSemanticRole.DRY_WET: ["dry/wet", "dry wet", "mix"],
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Arturia Efx MOTIONS",
            category="effect",
            is_native=False,
            aliases=["Efx MOTIONS", "Motions", "Efx Motions", "EfxMotions.vst3"],
            parameter_mappings={
                PluginSemanticRole.MORPH: "Morph",
                PluginSemanticRole.DEPTH: "Amount",
                PluginSemanticRole.RATE: "Rate",
                PluginSemanticRole.DRIVE: "Drive",
                PluginSemanticRole.DRY_WET: "Dry/Wet",
            },
            semantic_aliases={
                PluginSemanticRole.MORPH: ["morph", "motion morph"],
                PluginSemanticRole.DEPTH: ["amount", "depth", "motion amount"],
                PluginSemanticRole.RATE: ["rate", "speed", "beat division"],
                PluginSemanticRole.DRIVE: ["drive", "warmth", "saturation"],
                PluginSemanticRole.DRY_WET: ["dry/wet", "dry wet", "mix"],
            }
        ))

        # 9. Ableton Native Synths
        self.register_profile(PluginProfile(
            plugin_name="Drift",
            category="synth",
            is_native=True,
            aliases=["Drift"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "Filter Freq",
                PluginSemanticRole.RESONANCE: "Filter Res",
                PluginSemanticRole.DRIVE: "Filter Drive",
                PluginSemanticRole.ATTACK: "Env 1 Attack",
                PluginSemanticRole.DECAY: "Env 1 Decay",
                PluginSemanticRole.VOLUME: "Volume",
            },
            semantic_aliases={
                PluginSemanticRole.CUTOFF: ["filter freq", "filter frequency", "cutoff"],
                PluginSemanticRole.RESONANCE: ["filter res", "resonance", "res"],
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Wavetable",
            category="synth",
            is_native=True,
            aliases=["Wavetable"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "Filter 1 Freq",
                PluginSemanticRole.RESONANCE: "Filter 1 Res",
                PluginSemanticRole.DRIVE: "Filter 1 Drive",
                PluginSemanticRole.ATTACK: "Amp Attack",
                PluginSemanticRole.DECAY: "Amp Decay",
                PluginSemanticRole.VOLUME: "Volume",
            },
            semantic_aliases={
                PluginSemanticRole.CUTOFF: ["filter 1 freq", "filter freq", "cutoff"],
                PluginSemanticRole.RESONANCE: ["filter 1 res", "resonance"],
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Operator",
            category="synth",
            is_native=True,
            aliases=["Operator"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "Filter Freq",
                PluginSemanticRole.RESONANCE: "Filter Res",
                PluginSemanticRole.ATTACK: "A Attack",
                PluginSemanticRole.DECAY: "A Decay",
                PluginSemanticRole.VOLUME: "Volume",
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Analog",
            category="synth",
            is_native=True,
            aliases=["Analog"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "F1 Freq",
                PluginSemanticRole.RESONANCE: "F1 Res",
                PluginSemanticRole.ATTACK: "Amp1 Attack",
                PluginSemanticRole.VOLUME: "Volume",
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Simpler",
            category="sampler",
            is_native=True,
            aliases=["Simpler"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "Filter Freq",
                PluginSemanticRole.RESONANCE: "Filter Res",
                PluginSemanticRole.ATTACK: "Amp Attack",
                PluginSemanticRole.DECAY: "Amp Decay",
                PluginSemanticRole.VOLUME: "Volume",
            }
        ))

        # 10. Ableton Native Effects
        self.register_profile(PluginProfile(
            plugin_name="Auto Filter",
            category="effect",
            is_native=True,
            aliases=["Auto Filter", "AutoFilter"],
            parameter_mappings={
                PluginSemanticRole.CUTOFF: "Frequency",
                PluginSemanticRole.RESONANCE: "Resonance",
                PluginSemanticRole.DRIVE: "Drive",
                PluginSemanticRole.DRY_WET: "Dry/Wet",
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Glue Compressor",
            category="effect",
            is_native=True,
            aliases=["Glue Compressor", "GlueCompressor"],
            parameter_mappings={
                PluginSemanticRole.THRESHOLD: "Threshold",
                PluginSemanticRole.DRIVE: "Make Up",
                PluginSemanticRole.ATTACK: "Attack",
                PluginSemanticRole.RELEASE: "Release",
                PluginSemanticRole.DRY_WET: "Dry/Wet",
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Utility",
            category="effect",
            is_native=True,
            aliases=["Utility"],
            parameter_mappings={
                PluginSemanticRole.VOLUME: "Gain",
                PluginSemanticRole.PANNING: "Panorama",
                PluginSemanticRole.WIDTH: "Width",
                PluginSemanticRole.DRY_WET: "Mute",
            }
        ))

        self.register_profile(PluginProfile(
            plugin_name="Drum Rack",
            category="drum_machine",
            is_native=True,
            aliases=["Drum Rack", "DrumGroupDevice"],
            parameter_mappings={
                PluginSemanticRole.MACRO_1: "Macro 1",
                PluginSemanticRole.MACRO_2: "Macro 2",
                PluginSemanticRole.MACRO_3: "Macro 3",
                PluginSemanticRole.MACRO_4: "Macro 4",
                PluginSemanticRole.MACRO_5: "Macro 5",
                PluginSemanticRole.MACRO_6: "Macro 6",
                PluginSemanticRole.MACRO_7: "Macro 7",
                PluginSemanticRole.MACRO_8: "Macro 8",
            }
        ))

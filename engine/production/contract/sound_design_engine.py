# engine/production/contract/sound_design_engine.py
"""
Sound Design Engine (Level H):
Generates deterministic, emotionally coherent sound design transformation chains
based on intentional aesthetic archetypes.

Strictly avoids arbitrary or random effects stacking, enforcing that every
transformation serves an explicit narrative purpose:
- MAKE_IT_DAMAGED
- MAKE_IT_ENORMOUS
- MAKE_IT_GHOSTLY
- TAPE_DEGRADATION
- GRANULAR_SCATTER
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("SoundDesignEngine")


class DestructionArchetype(str, Enum):
    """Artistic transformation archetypes for controlled sound sculpting."""
    MAKE_IT_DAMAGED = "MAKE_IT_DAMAGED"       # 12-bit SP-1200 grit, harmonic overdrive, transient rounding
    MAKE_IT_ENORMOUS = "MAKE_IT_ENORMOUS"     # Time-stretch 300%, sub-weight, stereo expansion, endless convolution
    MAKE_IT_GHOSTLY = "MAKE_IT_GHOSTLY"       # Reverse, 500% stretch, HPF @ 400Hz, spectral shimmer diffusion
    TAPE_DEGRADATION = "TAPE_DEGRADATION"     # Wow & flutter, head compression, 7kHz high cut, vintage warmth
    GRANULAR_SCATTER = "GRANULAR_SCATTER"     # Micro-grain fragmentation, pitch scatter, spatial dispersion


@dataclass
class SoundDesignStep:
    """A discrete processing stage within a sound design chain."""
    name: str
    device_name: str
    device_uri: str
    parameters: Dict[str, Any]
    purpose: str
    order: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "device_name": self.device_name,
            "device_uri": self.device_uri,
            "parameters": dict(self.parameters),
            "purpose": self.purpose,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SoundDesignStep:
        return cls(
            name=data.get("name", "Step"),
            device_name=data.get("device_name", "AudioFx"),
            device_uri=data.get("device_uri", ""),
            parameters=data.get("parameters", {}),
            purpose=data.get("purpose", ""),
            order=int(data.get("order", 0)),
        )


@dataclass
class SoundDesignChain:
    """Complete chain of transformations designed for an archetype."""
    archetype: DestructionArchetype
    steps: List[SoundDesignStep]
    dry_wet: float = 1.0
    output_gain_db: float = 0.0
    time_stretch_ratio: float = 1.0
    reverse: bool = False
    pitch_semitones: int = 0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archetype": self.archetype.value if isinstance(self.archetype, DestructionArchetype) else str(self.archetype),
            "steps": [s.to_dict() for s in self.steps],
            "dry_wet": self.dry_wet,
            "output_gain_db": self.output_gain_db,
            "time_stretch_ratio": self.time_stretch_ratio,
            "reverse": self.reverse,
            "pitch_semitones": self.pitch_semitones,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SoundDesignChain:
        arch_str = data.get("archetype", "MAKE_IT_DAMAGED")
        try:
            archetype = DestructionArchetype(arch_str)
        except ValueError:
            archetype = DestructionArchetype.MAKE_IT_DAMAGED
        steps = [SoundDesignStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            archetype=archetype,
            steps=steps,
            dry_wet=float(data.get("dry_wet", 1.0)),
            output_gain_db=float(data.get("output_gain_db", 0.0)),
            time_stretch_ratio=float(data.get("time_stretch_ratio", 1.0)),
            reverse=bool(data.get("reverse", False)),
            pitch_semitones=int(data.get("pitch_semitones", 0)),
            description=data.get("description", ""),
        )


class SoundDesignEngine:
    """
    Factory creating structured, intentional sound design recipes.
    Maps emotional intentions into concrete Ableton Live native audio effects
    and parameter targets.
    """

    @classmethod
    def build_chain(
        cls,
        archetype: DestructionArchetype,
        intensity: float = 0.8,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> SoundDesignChain:
        """
        Builds an archetype-specific transformation chain.
        Intensity is normalized from 0.1 to 1.0.
        """
        custom_params = custom_params or {}

        if archetype == DestructionArchetype.MAKE_IT_DAMAGED:
            return cls._build_damaged_chain(intensity, custom_params)
        elif archetype == DestructionArchetype.MAKE_IT_ENORMOUS:
            return cls._build_enormous_chain(intensity, custom_params)
        elif archetype == DestructionArchetype.MAKE_IT_GHOSTLY:
            return cls._build_ghostly_chain(intensity, custom_params)
        elif archetype == DestructionArchetype.TAPE_DEGRADATION:
            return cls._build_tape_chain(intensity, custom_params)
        elif archetype == DestructionArchetype.GRANULAR_SCATTER:
            return cls._build_granular_chain(intensity, custom_params)
        else:
            return cls._build_damaged_chain(intensity, custom_params)

    @classmethod
    def _build_damaged_chain(cls, intensity: float, custom: Dict[str, Any]) -> SoundDesignChain:
        drive = 3.0 + (intensity * 4.0)  # 3.4 dB to 7.0 dB
        bit_depth = 12 if intensity < 0.7 else 10

        steps = [
            SoundDesignStep(
                name="Harmonic Overdrive",
                device_name="Saturator",
                device_uri="query:AudioFx#Saturator",
                parameters={"Drive": f"{drive:.1f} dB", "Curve": "Analog Clip", "Color": "On", "Base": "2.5 dB"},
                purpose="Inject harmonic richness and round aggressive transients",
                order=1,
            ),
            SoundDesignStep(
                name="SP-1200 Lo-Fi Grit",
                device_name="Redux",
                device_uri="query:AudioFx#Redux",
                parameters={"Bit Depth": bit_depth, "Downsample": 2 if intensity > 0.6 else 1},
                purpose="Vintage 12-bit sampler texture and slight quantization aliasing",
                order=2,
            ),
            SoundDesignStep(
                name="Tone Shaping EQ",
                device_name="EQ Eight",
                device_uri="query:AudioFx#EQ%20Eight",
                parameters={
                    "Band 1 Freq": "85 Hz", "Band 1 Gain": "-2.0 dB",
                    "Band 2 Freq": "280 Hz", "Band 2 Gain": "+2.2 dB",
                    "Band 8 Freq": "6200 Hz", "Band 8 Gain": "-4.5 dB",
                },
                purpose="Attenuate brittle digital highs and warm up lower body",
                order=3,
            ),
        ]
        return SoundDesignChain(
            archetype=DestructionArchetype.MAKE_IT_DAMAGED,
            steps=steps,
            dry_wet=0.85,
            output_gain_db=-1.5,
            time_stretch_ratio=1.0,
            reverse=False,
            pitch_semitones=0,
            description="Gritty, saturated 12-bit sampler character with rounded top-end and vintage body.",
        )

    @classmethod
    def _build_enormous_chain(cls, intensity: float, custom: Dict[str, Any]) -> SoundDesignChain:
        decay_time = 6.0 + (intensity * 6.0)  # 6.6s to 12.0s
        stretch = custom.get("time_stretch_ratio", 3.0)

        steps = [
            SoundDesignStep(
                name="Sub-Harmonic Foundation",
                device_name="EQ Eight",
                device_uri="query:AudioFx#EQ%20Eight",
                parameters={
                    "Band 1 Freq": "48 Hz", "Band 1 Gain": "+3.0 dB",
                    "Band 4 Freq": "420 Hz", "Band 4 Gain": "-2.5 dB",
                },
                purpose="Bolster low-end weight while clearing vocal clutter space",
                order=1,
            ),
            SoundDesignStep(
                name="Stereo Dimensional Field",
                device_name="Chorus-Ensemble",
                device_uri="query:AudioFx#Chorus-Ensemble",
                parameters={"Mode": "Ensemble", "Amount": "45%", "Warmth": "On"},
                purpose="Widen spatial footprint across stereo spectrum",
                order=2,
            ),
            SoundDesignStep(
                name="Infinite Convolutive Decay",
                device_name="Reverb",
                device_uri="query:AudioFx#Reverb",
                parameters={"Decay Time": f"{decay_time:.1f} s", "Room Size": 100, "Stereo": "120%", "Dry/Wet": "55%"},
                purpose="Immense architectural space that surrounds rather than invades the mix",
                order=3,
            ),
        ]
        return SoundDesignChain(
            archetype=DestructionArchetype.MAKE_IT_ENORMOUS,
            steps=steps,
            dry_wet=1.0,
            output_gain_db=-2.0,
            time_stretch_ratio=stretch,
            reverse=False,
            pitch_semitones=-12 if custom.get("sub_octave", False) else 0,
            description="Expansive, cinematic sonic cloud with wide stereo spread and deep spatial presence.",
        )

    @classmethod
    def _build_ghostly_chain(cls, intensity: float, custom: Dict[str, Any]) -> SoundDesignChain:
        stretch = custom.get("time_stretch_ratio", 4.0)

        steps = [
            SoundDesignStep(
                name="Surgical High-Pass De-coupling",
                device_name="EQ Eight",
                device_uri="query:AudioFx#EQ%20Eight",
                parameters={
                    "Band 1 Mode": "High Pass 48dB/oct",
                    "Band 1 Freq": "420 Hz",
                    "Band 8 Freq": "11000 Hz",
                    "Band 8 Gain": "+3.5 dB",
                },
                purpose="Remove bass/sub fundamentals so ghost texture floats freely without mix collision",
                order=1,
            ),
            SoundDesignStep(
                name="Shimmer Delay Reflection",
                device_name="Echo",
                device_uri="query:AudioFx#Echo",
                parameters={"Echo Time": "1/4 D", "Feedback": "65%", "Modulation Depth": "30%", "Dry/Wet": "40%"},
                purpose="Diffuse repeating halo echoing reverse acoustic transients",
                order=2,
            ),
            SoundDesignStep(
                name="Spectral Mist Diffusion",
                device_name="Reverb",
                device_uri="query:AudioFx#Reverb",
                parameters={"Decay Time": "10.0 s", "PreDelay": "25 ms", "Diffusion": "90%", "Dry/Wet": "70%"},
                purpose="Disintegrate discrete harmonic edges into an ethereal spectral aura",
                order=3,
            ),
        ]
        return SoundDesignChain(
            archetype=DestructionArchetype.MAKE_IT_GHOSTLY,
            steps=steps,
            dry_wet=0.9,
            output_gain_db=-3.0,
            time_stretch_ratio=stretch,
            reverse=True,
            pitch_semitones=custom.get("pitch_semitones", 12),
            description="Reversed, stretched, high-passed spectral ghost tailored for bridge or hook pre-drops.",
        )

    @classmethod
    def _build_tape_chain(cls, intensity: float, custom: Dict[str, Any]) -> SoundDesignChain:
        steps = [
            SoundDesignStep(
                name="Tape Head Saturation",
                device_name="Saturator",
                device_uri="query:AudioFx#Saturator",
                parameters={"Drive": "+3.2 dB", "Curve": "Soft Sine", "Depth": "15%"},
                purpose="Gentle analog compression and head-bump saturation",
                order=1,
            ),
            SoundDesignStep(
                name="Tape Wow & Flutter",
                device_name="Chorus-Ensemble",
                device_uri="query:AudioFx#Chorus-Ensemble",
                parameters={"Mode": "Vibrato", "Rate": "0.75 Hz", "Amount": "18%"},
                purpose="Subtle cyclic pitch instability reminiscent of physical reel-to-reel tape",
                order=2,
            ),
            SoundDesignStep(
                name="Vintage High-End Roll-off",
                device_name="EQ Eight",
                device_uri="query:AudioFx#EQ%20Eight",
                parameters={
                    "Band 8 Mode": "Low Pass 24dB/oct",
                    "Band 8 Freq": "7200 Hz",
                    "Band 2 Freq": "260 Hz",
                    "Band 2 Gain": "+1.8 dB",
                },
                purpose="Natural magnetic tape HF absorption and low-mid warmth",
                order=3,
            ),
        ]
        return SoundDesignChain(
            archetype=DestructionArchetype.TAPE_DEGRADATION,
            steps=steps,
            dry_wet=1.0,
            output_gain_db=-0.8,
            time_stretch_ratio=1.0,
            reverse=False,
            pitch_semitones=0,
            description="Physical magnetic tape character with organic wow & flutter and smooth 7.2kHz roll-off.",
        )

    @classmethod
    def _build_granular_chain(cls, intensity: float, custom: Dict[str, Any]) -> SoundDesignChain:
        steps = [
            SoundDesignStep(
                name="Grain Dispersal Delay",
                device_name="Grain Delay",
                device_uri="query:AudioFx#Grain%20Delay",
                parameters={"Grain Size": "75 ms", "Spray": "35 ms", "Pitch": "0.00", "Random Pitch": "1.20"},
                purpose="Micro-temporal grain slicing and pitch scattering",
                order=1,
            ),
            SoundDesignStep(
                name="Diffusion Bed",
                device_name="Reverb",
                device_uri="query:AudioFx#Reverb",
                parameters={"Decay Time": "4.5 s", "Room Size": 75, "Dry/Wet": "35%"},
                purpose="Bind scattered micro-particles into a cohesive ambient bed",
                order=2,
            ),
        ]
        return SoundDesignChain(
            archetype=DestructionArchetype.GRANULAR_SCATTER,
            steps=steps,
            dry_wet=0.75,
            output_gain_db=-1.2,
            time_stretch_ratio=1.0,
            reverse=False,
            pitch_semitones=0,
            description="Granular cloud of micro-temporal fragments scattering across the stereo field.",
        )

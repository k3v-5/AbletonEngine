# engine/sound_design/surge_xt_fx/schema.py
"""
Surge XT FX Parameter Schema & Hardware/DSP Specifications.

Directly mirrors the official Surge XT C++ source code:
- n_fx_params = 12 (p0 .. p11 per slot)
- n_fx_slots = 16 (4 chains x 4 slots)
- n_fx_chains = 4 (Scene A, Scene B, Send, Global)
- 32 algorithmic DSP processors (fxt_off to fxt_convolution)
"""

from typing import Dict, List, Tuple, Optional, Any
from enum import IntEnum


class FXType(IntEnum):
    """Canonical fx_type enumeration matching Surge XT source (SurgeStorage.h)."""
    OFF = 0
    DELAY = 1
    REVERB1 = 2
    PHASER = 3
    ROTARY_SPEAKER = 4
    DISTORTION = 5
    EQ = 6
    FREQ_SHIFT = 7
    CONDITIONER = 8
    CHORUS = 9
    VOCODER = 10
    REVERB2 = 11
    FLANGER = 12
    RING_MOD = 13
    AIRWINDOWS = 14
    NEURON = 15
    GRAPHIC_EQ = 16
    RESONATOR = 17
    CHOW = 18
    EXCITER = 19
    ENSEMBLE = 20
    COMBULATOR = 21
    NIMBUS = 22
    TAPE = 23
    TREEMONSTER = 24
    WAVESHAPER = 25
    MID_SIDE = 26
    SPRING_REVERB = 27
    BONSAI = 28
    AUDIO_INPUT = 29
    FLOATY_DELAY = 30
    CONVOLUTION = 31


class FXChain(IntEnum):
    """Canonical fxchains enum from Surge XT."""
    SCENE_A = 0
    SCENE_B = 1
    SEND = 2
    GLOBAL = 3


class FXBypass(IntEnum):
    """Canonical fx_bypass enum from Surge XT."""
    ALL_FX = 0              # All active
    NO_SENDS = 1            # Bypasses sends
    SCENE_FX_ONLY = 2       # Bypasses sends and globals
    NO_FX = 3               # Everything bypassed


class SurgeFXSchema:
    """Complete specification of Surge XT's modular multi-FX engine."""

    NUM_PARAMS_PER_SLOT = 12  # n_fx_params
    NUM_SLOTS = 16            # n_fx_slots
    NUM_CHAINS = 4            # n_fx_chains
    SLOTS_PER_CHAIN = 4       # n_fx_per_chain
    STREAMING_VERSION = 30    # ff_revision in Surge XT 1.3 / 1.4

    # Canonical type and chain aliases
    CANONICAL_FX_TYPES: List[str] = [t.name.lower() for t in FXType] + [f"fxt_{t.name.lower()}" for t in FXType]
    FX_TAPE = FXType.TAPE
    FX_CHOW = FXType.CHOW
    CHAIN_A = FXChain.SCENE_A
    CHAIN_B = FXChain.SCENE_B
    CHAIN_SEND = FXChain.SEND
    CHAIN_GLOBAL = FXChain.GLOBAL

    # 32 FX Types with full name, short name, acronym
    FX_TYPE_SPECS: Dict[FXType, Dict[str, str]] = {
        FXType.OFF: {"name": "Off", "short": "Off", "acronym": "OFF", "desc": "Disabled slot"},
        FXType.DELAY: {"name": "Delay", "short": "Delay", "acronym": "DLY", "desc": "Stereo digital delay with modulation and filters"},
        FXType.REVERB1: {"name": "Reverb 1", "short": "Reverb 1", "acronym": "RV1", "desc": "Original feedback-delay network reverb"},
        FXType.PHASER: {"name": "Phaser", "short": "Phaser", "acronym": "PH", "desc": "Multi-stage analog modeled phaser"},
        FXType.ROTARY_SPEAKER: {"name": "Rotary Speaker", "short": "Rotary", "acronym": "ROT", "desc": "Leslie speaker emulation with horn/rotor speed"},
        FXType.DISTORTION: {"name": "Distortion", "short": "Distortion", "acronym": "DIST", "desc": "Overdrive/distortion with feedback and filters"},
        FXType.EQ: {"name": "EQ", "short": "EQ", "acronym": "EQ", "desc": "3-band parametric equalizer"},
        FXType.FREQ_SHIFT: {"name": "Frequency Shifter", "short": "Freq Shift", "acronym": "FRQ", "desc": "Bode-style linear frequency shifter"},
        FXType.CONDITIONER: {"name": "Conditioner", "short": "Conditioner", "acronym": "DYN", "desc": "Audio conditioner (gate/comp/limiting/EQ)"},
        FXType.CHORUS: {"name": "Chorus", "short": "Chorus", "acronym": "CH", "desc": "4-voice thick stereo chorus"},
        FXType.VOCODER: {"name": "Vocoder", "short": "Vocoder", "acronym": "VOC", "desc": "Multi-band carrier/modulator vocoder"},
        FXType.REVERB2: {"name": "Reverb 2", "short": "Reverb 2", "acronym": "RV2", "desc": "Modern high-density diffuse algorithmic reverb"},
        FXType.FLANGER: {"name": "Flanger", "short": "Flanger", "acronym": "FL", "desc": "True bucket-brigade style comb flanging"},
        FXType.RING_MOD: {"name": "Ring Modulator", "short": "Ring Mod", "acronym": "RM", "desc": "Sine/carrier ring modulation"},
        FXType.AIRWINDOWS: {"name": "Airwindows", "short": "Airwindows", "acronym": "AW", "desc": "50+ bespoke DSP processors by Chris Johnson"},
        FXType.NEURON: {"name": "Neuron", "short": "Neuron", "acronym": "NEU", "desc": "Non-linear neural saturation model by ChowDSP"},
        FXType.GRAPHIC_EQ: {"name": "Graphic EQ", "short": "Graphic EQ", "acronym": "GEQ", "desc": "11-band octave graphic equalizer"},
        FXType.RESONATOR: {"name": "Resonator", "short": "Resonator", "acronym": "RES", "desc": "Multi-mode resonant bandpass bank"},
        FXType.CHOW: {"name": "CHOW", "short": "CHOW", "acronym": "CHW", "desc": "ChowDSP half-wave rectifier tape saturation"},
        FXType.EXCITER: {"name": "Exciter", "short": "Exciter", "acronym": "XCT", "desc": "Harmonic exciter and perceptual high enhancer"},
        FXType.ENSEMBLE: {"name": "Ensemble", "short": "Ensemble", "acronym": "ENS", "desc": "BBD vintage string machine ensemble modulation"},
        FXType.COMBULATOR: {"name": "Combulator", "short": "Combulator", "acronym": "CMB", "desc": "Tuned comb filter resonator with feedback"},
        FXType.NIMBUS: {"name": "Nimbus", "short": "Nimbus", "acronym": "NIM", "desc": "Granular cloud reverb / mangler (Clouds port)"},
        FXType.TAPE: {"name": "Tape", "short": "Tape", "acronym": "TAPE", "desc": "Full ChowTape physical magnetic tape emulation"},
        FXType.TREEMONSTER: {"name": "Treemonster", "short": "Treemonster", "acronym": "TM", "desc": "Dynamic ring-modulator pitch tracking follower"},
        FXType.WAVESHAPER: {"name": "Waveshaper", "short": "Waveshaper", "acronym": "WS", "desc": "Comprehensive transfer function waveshaper"},
        FXType.MID_SIDE: {"name": "Mid-Side Tool", "short": "Mid-Side Tool", "acronym": "M-S", "desc": "M/S matrix encoding, stereo width & balancing"},
        FXType.SPRING_REVERB: {"name": "Spring Reverb", "short": "Spring Reverb", "acronym": "SRV", "desc": "Physical dual-spring tank reverberator"},
        FXType.BONSAI: {"name": "Bonsai", "short": "Bonsai", "acronym": "BON", "desc": "ChowDSP Bonsai asymmetric saturation & tone"},
        FXType.AUDIO_INPUT: {"name": "Audio Input", "short": "Audio In", "acronym": "IN", "desc": "Sidechain & external DAW audio receiver"},
        FXType.FLOATY_DELAY: {"name": "Floaty Delay", "short": "Floaty Delay", "acronym": "FDL", "desc": "Multi-tap pitch shifting ambient delay"},
        FXType.CONVOLUTION: {"name": "Convolution", "short": "Convolution", "acronym": "IR", "desc": "Zero-latency impulse response processor"},
    }

    # Slot names indexed 0 to 15 (matching fxslot_positions and fxslot_names in SurgeStorage.h)
    SLOT_NAMES: List[str] = [
        "A Insert FX 1", "A Insert FX 2", "B Insert FX 1", "B Insert FX 2",
        "Send FX 1",     "Send FX 2",     "Global FX 1",   "Global FX 2",
        "A Insert FX 3", "A Insert FX 4", "B Insert FX 3", "B Insert FX 4",
        "Send FX 3",     "Send FX 4",     "Global FX 3",   "Global FX 4",
    ]

    # Logical slot ordering per chain (4 slots each):
    # Scene A: slots [0, 1, 8, 9] (ains1, ains2, ains3, ains4)
    # Scene B: slots [2, 3, 10, 11] (bins1, bins2, bins3, bins4)
    # Send:    slots [4, 5, 12, 13] (send1, send2, send3, send4)
    # Global:  slots [6, 7, 14, 15] (global1, global2, global3, global4)
    CHAIN_TO_SLOT_INDICES: Dict[FXChain, List[int]] = {
        FXChain.SCENE_A: [0, 1, 8, 9],
        FXChain.SCENE_B: [2, 3, 10, 11],
        FXChain.SEND:    [4, 5, 12, 13],
        FXChain.GLOBAL:  [6, 7, 14, 15],
    }

    # Inverse lookup: slot index to (Chain, slot_position_in_chain [0..3])
    SLOT_TO_CHAIN: Dict[int, Tuple[FXChain, int]] = {
        0: (FXChain.SCENE_A, 0),
        1: (FXChain.SCENE_A, 1),
        8: (FXChain.SCENE_A, 2),
        9: (FXChain.SCENE_A, 3),
        2: (FXChain.SCENE_B, 0),
        3: (FXChain.SCENE_B, 1),
        10: (FXChain.SCENE_B, 2),
        11: (FXChain.SCENE_B, 3),
        4: (FXChain.SEND, 0),
        5: (FXChain.SEND, 1),
        12: (FXChain.SEND, 2),
        13: (FXChain.SEND, 3),
        6: (FXChain.GLOBAL, 0),
        7: (FXChain.GLOBAL, 1),
        14: (FXChain.GLOBAL, 2),
        15: (FXChain.GLOBAL, 3),
    }

    # Parameter definitions for flagship DSP algorithms
    PARAM_DESCRIPTIONS: Dict[FXType, Dict[int, str]] = {
        FXType.CHOW: {
            0: "Threshold (dB attenuation)",
            1: "Ratio (saturation curve steepness)",
            2: "Flip (half-wave rectification invert: 0=normal, 1=flipped)",
            3: "Mix (wet/dry balance 0.0 to 1.0)",
        },
        FXType.TAPE: {
            0: "Drive (dB saturation input boost)",
            1: "Saturation (hysteresis core nonlinearity)",
            2: "Bias (tape bias calibration level)",
            3: "Speed (IPS tape speed: 7.5, 15, 30)",
            4: "Gap (reproduce playback head gap loss)",
            5: "Spacing (head-to-tape spacing loss)",
            6: "Thickness (tape oxide layer thickness)",
            7: "Degrade Depth (wow/flutter/dropout intensity)",
            8: "Degrade Amount (flutter rate & variance)",
            9: "Degrade Variance (random tape dropouts)",
            10: "Tone (high-frequency emphasis / damping)",
            11: "Output Gain / Mix",
        },
        FXType.NIMBUS: {
            0: "Mode (0=Granular, 1=Pitch Shift, 2=Looping Delay)",
            1: "Position (grain buffer playback window)",
            2: "Size (grain duration / window size)",
            3: "Pitch (semitones / transpose -24 to +24)",
            4: "Density (grain generation rate / overlap)",
            5: "Texture (grain envelope shape / diffusion)",
            6: "Dry/Wet Mix",
            7: "Stereo Spread",
            8: "Feedback (reverb feedback / feedback delay)",
            9: "Reverb (internal post-diffusion level)",
            10: "Low Cut",
            11: "High Cut",
        },
        FXType.DELAY: {
            0: "Time Left",
            1: "Time Right",
            2: "Feedback",
            3: "Crossfeed",
            4: "Low Cut",
            5: "High Cut",
            6: "Mod Rate",
            7: "Mod Depth",
            8: "Input Channel",
            9: "Mix",
            10: "Width",
        },
        FXType.REVERB2: {
            0: "Decay Time",
            1: "Pre-Delay",
            2: "Low Cut",
            3: "High Cut",
            4: "High Damping",
            5: "Room Size",
            6: "Diffusion",
            7: "Mix",
            8: "Stereo Width",
        },
    }

    @classmethod
    def resolve_type(cls, val: Any) -> FXType:
        """Resolve an int or string into an FXType enum."""
        if isinstance(val, FXType):
            return val
        if isinstance(val, int):
            return FXType(val)
        if isinstance(val, str):
            cleaned = val.strip().lower()
            if cleaned.startswith("fxt_"):
                cleaned = cleaned[4:]
            # Check by enum name
            for t in FXType:
                if t.name.lower() == cleaned:
                    return t
            # Check by full name or short name
            for t, specs in cls.FX_TYPE_SPECS.items():
                if specs["name"].lower() == cleaned or specs["short"].lower() == cleaned or specs["acronym"].lower() == cleaned:
                    return t
            # Try integer string
            try:
                return FXType(int(val))
            except ValueError:
                pass
        raise ValueError(f"Unknown Surge FX type '{val}'.")

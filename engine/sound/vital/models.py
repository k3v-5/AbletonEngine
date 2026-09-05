# engine/sound/vital/models.py
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

class VitalPresetStyle(str, Enum):
    BASS = "Bass"
    LEAD = "Lead"
    PAD = "Pad"
    KEYS = "Keys"
    PLUCK = "Pluck"
    FX = "FX"
    DRUMS = "Drums"
    EXPERIMENTAL = "Experimental"

@dataclass
class VitalOscillatorSpec:
    on: bool = True
    wave_frame: float = 0.0          # Wavetable position (0.0 to 256.0)
    level: float = 0.707             # Output volume level
    pan: float = 0.0                 # -1.0 to 1.0
    transpose: int = 0               # Semitones (-48 to 48)
    tune: float = 0.0                # Fine tune (-1.0 to 1.0)
    unison_voices: int = 1           # 1 to 16
    unison_detune: float = 2.0       # Detune spread
    unison_blend: float = 0.8
    distortion_type: int = 0         # 0=None, 1=Sync, 2=Formant, 3=Quantize, 4=Bend, etc.
    distortion_amount: float = 0.0   # 0.0 to 1.0
    spectral_morph_type: int = 0     # 0=None, Vocode, Harmonic, Inharmonic, Smear, etc.
    spectral_morph_amount: float = 0.0
    destination: int = 1             # 1=Filter 1, 2=Filter 2, 3=Direct Out

@dataclass
class VitalFilterSpec:
    on: bool = True
    model: int = 0                   # 0=Analog, 1=Dirty, 2=Ladder, 3=Digital, 4=Diode, 5=Formant, 6=Comb
    style: int = 0                   # 0=12dB, 1=24dB
    cutoff: float = 80.0             # Semitones: 8.0 (~20Hz) to 136.0 (~20kHz)
    resonance: float = 0.0           # 0.0 to 1.0
    drive: float = 0.0               # Filter drive in dB (0.0 to 24.0)
    blend: float = 0.0               # 0.0=Lowpass, 1.0=Bandpass, 2.0=Highpass
    keytrack: float = 0.0            # 0.0 to 1.0

@dataclass
class VitalEnvelopeSpec:
    attack: float = 0.01             # Seconds (e.g. 0.01 to 10.0)
    decay: float = 0.5               # Seconds
    sustain: float = 0.8             # Level 0.0 to 1.0
    release: float = 0.3             # Seconds
    attack_power: float = 0.0        # Curvature: -10 to 10 (0 = linear)
    decay_power: float = -2.0
    release_power: float = -2.0

@dataclass
class VitalLfoSpec:
    frequency: float = 1.0           # Hz when not synced
    sync: bool = True                # Tempo synced
    tempo: int = 6                   # Division: 5=1/2, 6=1/4, 7=1/8, 8=1/16, 9=1/32
    smooth_time: float = -7.5        # Smoothing
    waveform_name: str = "Triangle"  # "Triangle", "Saw", "Square", "Sine"

@dataclass
class VitalEffectsSpec:
    distortion_on: bool = False
    distortion_drive: float = 0.0    # dB (0.0 to 30.0)
    distortion_mix: float = 1.0
    distortion_type: int = 0         # 0=Soft Clip, 1=Hard Clip, 2=Linear Fold, 3=Sine Fold, 4=Bitcrush
    
    compressor_on: bool = False
    compressor_attack: float = 0.03
    compressor_release: float = 0.2
    compressor_mix: float = 1.0
    compressor_band_gain: float = 0.0
    
    chorus_on: bool = False
    chorus_dry_wet: float = 0.3
    chorus_voices: int = 4
    
    delay_on: bool = False
    delay_dry_wet: float = 0.25
    delay_tempo: int = 7             # 1/8
    delay_feedback: float = 0.4
    delay_style: int = 1             # 0=Mono, 1=Stereo, 2=Ping Pong
    
    reverb_on: bool = False
    reverb_dry_wet: float = 0.2
    reverb_decay_time: float = 2.0   # Seconds
    reverb_size: float = 0.5

@dataclass
class VitalModulationRouting:
    source: str                      # e.g. "lfo_1", "env_2", "macro_control_1", "mod_wheel"
    destination: str                 # e.g. "filter_1_cutoff", "distortion_drive", "osc_1_level"
    amount: float = 0.5              # -1.0 to 1.0
    bipolar: bool = False

@dataclass
class VitalPresetSpec:
    preset_name: str
    author: str = "PIE Engine"
    comments: str = "Synthesized by Ableton PIE Engine"
    preset_style: VitalPresetStyle = VitalPresetStyle.BASS
    macro1: str = "Macro 1"
    macro2: str = "Macro 2"
    macro3: str = "Macro 3"
    macro4: str = "Macro 4"
    oscillators: List[VitalOscillatorSpec] = field(default_factory=list)
    filters: List[VitalFilterSpec] = field(default_factory=list)
    envelopes: List[VitalEnvelopeSpec] = field(default_factory=list)
    lfos: List[VitalLfoSpec] = field(default_factory=list)
    effects: VitalEffectsSpec = field(default_factory=VitalEffectsSpec)
    modulations: List[VitalModulationRouting] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

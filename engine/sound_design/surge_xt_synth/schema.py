# engine/sound_design/surge_xt_synth/schema.py
"""
Surge XT Synthesizer Parameter Schema & DSP Specifications.

Directly mirrors official Surge XT Synthesizer architecture:
- 10 Oscillator DSP types (Classic, Modern, Wavetable, Sine, FM2, FM3, String, Twist, Alias, AudioIn)
- 20+ Filter models (Ladder, K35, Diode, OB-Xd, Chowdhury Tri-Pole, Comb, etc.)
- Dual Scene (Scene A & B), 3 Oscillators per scene
- Dedicated AHDSR Envelopes (Amp, Filter) and Unison Engine (1 to 16 voices)
"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class SurgeOscillatorType(str, Enum):
    """10 Canonical Oscillator Types in Surge XT."""
    CLASSIC = "Classic"
    MODERN = "Modern"
    WAVETABLE = "Wavetable"
    SINE = "Sine"
    FM2 = "FM2"
    FM3 = "FM3"
    STRING = "String"
    TWIST = "Twist"
    ALIAS = "Alias"
    AUDIO_IN = "AudioIn"


class SurgeFilterType(str, Enum):
    """Canonical Filter Types in Surge XT."""
    LOWPASS_12 = "Lowpass 12dB"
    LOWPASS_24 = "Lowpass 24dB"
    HIGHPASS_12 = "Highpass 12dB"
    HIGHPASS_24 = "Highpass 24dB"
    BANDPASS_12 = "Bandpass 12dB"
    BANDPASS_24 = "Bandpass 24dB"
    NOTCH = "Notch"
    LADDER_LP = "Ladder Lowpass"
    K35_LP = "K35 Lowpass"
    DIODE_LP = "Diode Lowpass"
    OBXD_LP = "OB-Xd Lowpass"
    OBXD_BP = "OB-Xd Bandpass"
    TRIPOLE = "Chowdhury Tri-Pole"
    COMB_POS = "Comb+"
    COMB_NEG = "Comb-"
    ALLPASS = "Allpass"


class SurgeFilterSubtype(str, Enum):
    STANDARD = "Standard"
    DRIVEN = "Driven"


class SurgeFilterConfig(str, Enum):
    SERIAL = "Serial"
    PARALLEL = "Parallel"
    WIDE = "Wide"
    DUAL = "Dual"


class SurgeXTSynthSchema:
    """Canonical specification and bounds for Surge XT Synthesizer."""

    PLUGIN_NAME = "Surge XT"
    DEFAULT_VERSION = "1.3.0"

    OSCILLATOR_TYPES: List[str] = [t.value for t in SurgeOscillatorType]
    FILTER_TYPES: List[str] = [f.value for f in SurgeFilterType]

    OSCILLATOR_DESCRIPTIONS: Dict[str, str] = {
        "Classic": "Classic subtractive analog oscillator (Saw, Pulse with PW, Sub-oscillator, Hard Sync).",
        "Modern": "Low-aliasing DPW multi-shape oscillator with continuous morphing.",
        "Wavetable": "Interpolating wavetable oscillator with morph, windowing and sub-tables.",
        "Sine": "Pure sine wave oscillator with non-linear wavefolding drive.",
        "FM2": "2-to-3 operator Frequency Modulation system with feedback and ratio tuning.",
        "FM3": "4-operator FM system with multiple algorithm configurations.",
        "String": "Physical modeling waveguide oscillator for acoustic plucks and bowed strings.",
        "Twist": "Eurorack modal synthesis based on Mutable Instruments Plaits.",
        "Alias": "Digital chiptune oscillator with intentional lo-fi aliasing.",
        "AudioIn": "Live audio input routing into synth voice.",
    }

    # Parameter boundaries
    BOUNDS: Dict[str, Tuple[float, float]] = {
        "volume": (0.0, 1.0),
        "cutoff": (0.0, 1.0),
        "resonance": (0.0, 1.0),
        "drive": (0.0, 1.0),
        "attack": (0.0, 1.0),     # 0.0s to 10.0s
        "decay": (0.0, 1.0),      # 0.0s to 10.0s
        "sustain": (0.0, 1.0),    # 0.0 to 1.0 amplitude
        "release": (0.0, 1.0),    # 0.005s to 10.0s
        "unison_detune": (0.0, 1.0),
        "pan": (-1.0, 1.0),
    }

    UNISON_MIN_VOICES: int = 1
    UNISON_MAX_VOICES: int = 16

    OCTAVE_MIN: int = -3
    OCTAVE_MAX: int = 3
    SEMITONE_MIN: int = -12
    SEMITONE_MAX: int = 12

    MIN_RELEASE_SEC: float = 0.005  # Anti-click safety floor

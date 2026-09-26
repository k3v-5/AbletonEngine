# engine/sound_design/valhalla_vintage_verb/schema.py
"""
Valhalla VintageVerb Parameter Schema & Specifications.

Defines the 22 algorithmic reverb modes, 3 color eras, exact parameter bounds,
and metadata specifications for Valhalla DSP's Valhalla VintageVerb.
"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class VintageVerbColor(str, Enum):
    """3 Canonical Color Modes in Valhalla VintageVerb."""
    COLOR_1970S = "1970s"
    COLOR_1980S = "1980s"
    COLOR_NOW = "Now"


class ValhallaVintageVerbSchema:
    """Canonical schema for Valhalla DSP's Valhalla VintageVerb reverb plugin."""

    PLUGIN_NAME = "ValhallaVintageVerb"
    DEFAULT_VERSION = "2.2.0"

    # Exact 22 Algorithmic Modes (in index order 0 to 21)
    MODES: List[str] = [
        "Concert Hall",
        "Bright Hall",
        "Plate",
        "Room",
        "Chamber",
        "Random Space",
        "Chorus Space",
        "Ambience",
        "Sanctuary",
        "Dirty Hall",
        "Dirty Plate",
        "Smooth Plate",
        "Smooth Room",
        "Smooth Random",
        "Nonlin",
        "Chaotic Hall",
        "Chaotic Chamber",
        "Chaotic Neutral",
        "Cathedral",
        "Palace",
        "Chamber1979",
        "Hall1984",
    ]

    NUM_MODES = len(MODES)  # 22
    MODE_NAMES = MODES

    # 3 Color Modes
    COLORS: List[str] = [
        VintageVerbColor.COLOR_1970S.value,
        VintageVerbColor.COLOR_1980S.value,
        VintageVerbColor.COLOR_NOW.value,
    ]

    # Mode descriptions and acoustic characteristics
    MODE_DESCRIPTIONS: Dict[str, str] = {
        "Concert Hall": "Late 70s / early 80s hall algorithm. Large spatial image, adjustable echo density, lush chorusing.",
        "Bright Hall": "Brighter initial sound than Concert Hall with deeper, lusher chorused modulation.",
        "Plate": "Early 80s plate algorithm. High echo density, bright initial sound, lush chorused modulation.",
        "Room": "Early 80s room algorithm. Darker sound, medium diffusion, early echo density, chorused modulation.",
        "Chamber": "Transparent, dense and highly diffuse with low coloration compared to Plate/Room.",
        "Random Space": "Deep, wide reverb with slow attack and high diffusion. Randomized delay modulation without pitch shift.",
        "Chorus Space": "Same underlying structure as Random Space but with lush chorused modulation.",
        "Ambience": "Short, dense reflections designed for adding space without adding an audible tail.",
        "Sanctuary": "Inspired by 1970s German digital reverb. Dense late tail, rapid echo buildup and detuned modulation.",
        "Dirty Hall": "Vintage hall with intentional 12-bit quantization noise and vintage digital character.",
        "Dirty Plate": "Plate algorithm with vintage digital grittiness and lo-fi warmth.",
        "Smooth Plate": "Modern transparent plate algorithm. Clean, high diffusion with zero metallic ringing.",
        "Smooth Room": "Modern transparent room algorithm. Natural acoustics for drums and acoustic instruments.",
        "Smooth Random": "Transparent room/hall with randomized delays. Clean attack and smooth decay.",
        "Nonlin": "Non-linear gated/reverse reverb modeled after classic 1980s AMS RMX-16 drum reverbs.",
        "Chaotic Hall": "Chaotic delay network with evolving recirculation patterns.",
        "Chaotic Chamber": "Dense chamber with chaotic recirculating delays for evolving acoustic depth.",
        "Chaotic Neutral": "Colorless chaotic reverb topology with balanced diffusion.",
        "Cathedral": "Expansive cathedral space inspired by FV-1 DSP architecture with smooth damping.",
        "Palace": "Versatile space scaling from small studio to grand palace with vintage warmth.",
        "Chamber1979": "Authentic late 70s chamber algorithm with warm analog-modeled input/output stages.",
        "Hall1984": "Refined 1984 digital hall with lush warmth and smooth high-frequency rolloff.",
    }

    # Color descriptions
    COLOR_DESCRIPTIONS: Dict[str, str] = {
        "1970s": "Bandwidth limited to 10 kHz. 12-bit quantization artifacts with noisy vintage chorusing.",
        "1980s": "Bandwidth up to 15 kHz. Lush, full-range classic studio plate/hall character.",
        "Now": "Full 20 kHz modern bandwidth. Clean, transparent, zero quantization noise.",
    }

    # Complete Parameter specifications with bounds, defaults and units
    PARAMETERS: Dict[str, Dict[str, Any]] = {
        "Mix": {
            "name": "Mix (Dry/Wet)",
            "min": 0.0,
            "max": 1.0,
            "default": 0.20,
            "unit": "norm",
            "physical_range": "0% to 100%",
            "description": "Dry/Wet balance. 0.0 = 100% dry, 1.0 = 100% wet.",
        },
        "PreDelay": {
            "name": "Pre-delay",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "unit": "norm",
            "physical_range": "0 ms to 500 ms",
            "description": "Delay before reverb onset. Protects dry transients.",
        },
        "Decay": {
            "name": "Decay (RT60)",
            "min": 0.0,
            "max": 1.0,
            "default": 0.25,
            "unit": "norm",
            "physical_range": "0.2 s to 70.0 s",
            "description": "Reverb decay time (RT60). Length of reverb tail.",
        },
        "Size": {
            "name": "Room Size",
            "min": 0.0,
            "max": 1.0,
            "default": 0.50,
            "unit": "norm",
            "physical_range": "0% to 100%",
            "description": "Perceived size and dimension of virtual space.",
        },
        "Attack": {
            "name": "Attack Shape",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "unit": "norm",
            "physical_range": "0% to 100%",
            "description": "Onset slope. In Nonlin mode, transitions from gated to reverse.",
        },
        "BassMult": {
            "name": "Bass Multiply",
            "min": 0.0,
            "max": 1.0,
            "default": 0.50,
            "unit": "norm",
            "physical_range": "0.25x to 4.0x",
            "description": "Low frequency decay time multiplier relative to Decay.",
        },
        "BassXover": {
            "name": "Bass Crossover",
            "min": 0.0,
            "max": 1.0,
            "default": 0.50,
            "unit": "norm",
            "physical_range": "100 Hz to 1000 Hz",
            "description": "Crossover frequency separating low and mid/high decay.",
        },
        "HighShelf": {
            "name": "High Shelf Damping",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "unit": "norm",
            "physical_range": "-24 dB to 0 dB",
            "description": "High frequency shelf attenuation in reverb tank.",
        },
        "HighCut": {
            "name": "High Cut (LPF)",
            "min": 0.0,
            "max": 1.0,
            "default": 0.65,
            "unit": "norm",
            "physical_range": "1000 Hz to 20000 Hz",
            "description": "Low-pass filter on output to tame brittle sibilance.",
        },
        "LowCut": {
            "name": "Low Cut (HPF)",
            "min": 0.0,
            "max": 1.0,
            "default": 0.20,
            "unit": "norm",
            "physical_range": "10 Hz to 500 Hz",
            "description": "High-pass filter on output to prevent low-end mud buildup.",
        },
        "EarlyDiffusion": {
            "name": "Early Diffusion",
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "unit": "norm",
            "physical_range": "0% to 100%",
            "description": "Density of initial early reflections. High settings prevent rattle.",
        },
        "LateDiffusion": {
            "name": "Late Diffusion",
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "unit": "norm",
            "physical_range": "0% to 100%",
            "description": "Density of late reverb tail. High settings provide lush wash.",
        },
        "ModRate": {
            "name": "Modulation Rate",
            "min": 0.0,
            "max": 1.0,
            "default": 0.25,
            "unit": "norm",
            "physical_range": "0.05 Hz to 5.0 Hz",
            "description": "Speed of chorusing LFO in reverb delay lines.",
        },
        "ModDepth": {
            "name": "Modulation Depth",
            "min": 0.0,
            "max": 1.0,
            "default": 0.50,
            "unit": "norm",
            "physical_range": "0% to 100%",
            "description": "Depth of chorusing modulation in reverb tank.",
        },
        "Mode": {
            "name": "Reverb Mode (Algorithm)",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,  # Concert Hall
            "unit": "index_norm",
            "physical_range": "22 Algorithmic Modes",
            "description": "Selects the core reverb DSP algorithm.",
        },
        "ColorMode": {
            "name": "Color Mode (Era)",
            "min": 0.0,
            "max": 1.0,
            "default": 0.50,  # 1980s
            "unit": "color_norm",
            "physical_range": "1970s, 1980s, Now",
            "description": "Selects vintage hardware era and bandwidth limits.",
        },
    }

    # Physical conversion formulas
    @classmethod
    def predelay_to_ms(cls, norm_val: float) -> float:
        """Converts normalized predelay (0..1) to physical milliseconds (0..500 ms)."""
        return round(float(norm_val) * 500.0, 2)

    @classmethod
    def ms_to_predelay(cls, ms: float) -> float:
        """Converts milliseconds (0..500 ms) to normalized predelay (0..1)."""
        return max(0.0, min(1.0, float(ms) / 500.0))

    @classmethod
    def decay_to_seconds(cls, norm_val: float) -> float:
        """Converts normalized decay (0..1) to physical seconds (0.2s..70.0s, exponential curve)."""
        # Valhalla VintageVerb uses an exponential mapping for decay
        # decay_sec = 0.2 * (70.0 / 0.2) ** norm_val
        norm = max(0.0, min(1.0, float(norm_val)))
        return round(0.2 * ((70.0 / 0.2) ** norm), 2)

    @classmethod
    def seconds_to_decay(cls, sec: float) -> float:
        """Converts physical seconds (0.2s..70.0s) to normalized decay (0..1)."""
        import math
        s = max(0.2, min(70.0, float(sec)))
        norm = math.log(s / 0.2) / math.log(70.0 / 0.2)
        return max(0.0, min(1.0, round(norm, 4)))

    @classmethod
    def mode_to_float(cls, mode_name: str) -> float:
        """Maps mode name to exact normalized float value [0.0, 1.0]."""
        clean = mode_name.strip()
        for idx, m in enumerate(cls.MODES):
            if m.lower() == clean.lower():
                return round(idx / (cls.NUM_MODES - 1), 6)
        return 0.0

    @classmethod
    def float_to_mode(cls, val: float) -> str:
        """Maps normalized float [0.0, 1.0] to mode name."""
        idx = int(round(float(val) * (cls.NUM_MODES - 1)))
        idx = max(0, min(idx, cls.NUM_MODES - 1))
        return cls.MODES[idx]

    @classmethod
    def color_to_float(cls, color_name: str) -> float:
        """Maps color name ('1970s', '1980s', 'Now') to float [0.0, 0.5, 1.0]."""
        clean = str(color_name).strip().lower()
        if "70" in clean:
            return 0.0
        elif "80" in clean:
            return 0.5
        elif "now" in clean or "modern" in clean:
            return 1.0
        return 0.5

    @classmethod
    def float_to_color(cls, val: float) -> str:
        """Maps normalized float to color name."""
        f = float(val)
        if f < 0.25:
            return VintageVerbColor.COLOR_1970S.value
        elif f < 0.75:
            return VintageVerbColor.COLOR_1980S.value
        else:
            return VintageVerbColor.COLOR_NOW.value

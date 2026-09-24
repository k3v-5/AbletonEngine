# engine/sound_design/valhalla_supermassive/schema.py
"""
Valhalla Supermassive Parameter Schema & Specifications.

Defines the exact algorithmic modes, delay sync modes, parameter bounds,
and metadata specifications for Valhalla Supermassive.
"""

from typing import Dict, List, Tuple, Optional


class ValhallaSupermassiveSchema:
    """Canonical schema for Valhalla DSP's Valhalla Supermassive reverb/delay plugin."""

    PLUGIN_NAME = "ValhallaSupermassive"
    DEFAULT_VERSION = "2.5.0"

    # Exact 22 Algorithmic Modes (in index order 0 to 21)
    MODES: List[str] = [
        "Gemini",
        "Hydra",
        "Centaurus",
        "Sagittarius",
        "Great Annihilator",
        "Andromeda",
        "Lyra",
        "Capricorn",
        "Large Magellanic Cloud",
        "Triangulum",
        "Cirrus Major",
        "Cirrus Minor",
        "Cassiopeia",
        "Orion",
        "Aquarius",
        "Pisces",
        "Scorpio",
        "Libra",
        "Leo",
        "Virgo",
        "Pleiades",
        "Sirius",
    ]

    NUM_MODES = len(MODES)  # 22
    MODE_NAMES = MODES

    # Mode descriptions and acoustic characteristics
    MODE_DESCRIPTIONS: Dict[str, str] = {
        "Gemini": "Fast attack, shorter decay, high echo density. Good for drums and tight ambiences.",
        "Hydra": "Fast attack, shorter decay, low to high echo density. Highly modulated chorus/delay.",
        "Centaurus": "Medium attack, longer decay, medium to high echo density. Luscious spatial reverb.",
        "Sagittarius": "Long attack, long decay, high echo density. Expansive lush synth pads.",
        "Great Annihilator": "Slow attack, ultra-long decay, massive spatial diffusion. Deep ambient drones.",
        "Andromeda": "Very slow attack, massive decay, vast cosmic washes. Classic ambient cloud.",
        "Lyra": "Fast attack, shorter decay, low echo density. Crisp rhythmic echoes and ping-pong.",
        "Capricorn": "Fast attack, medium decay, medium echo density. Versatile pointillistic echoes.",
        "Large Magellanic Cloud": "Slow attack, gargantuan decay, huge evolving spatial tail.",
        "Triangulum": "Long attack, long decay with diffuse repeats. Ethereal swells.",
        "Cirrus Major": "Medium attack, sparse to dense delay clusters. Shimmering spatial reverb.",
        "Cirrus Minor": "Short attack, delicate high-frequency diffusion. Transparent spaces.",
        "Cassiopeia": "Granular-like diffusion, metallic reverberation, unique complex reflections.",
        "Orion": "Warm vintage chamber response with deep spatial modulation.",
        "Aquarius": "Fluid, liquid-like reflections with dynamic phase cancellation effects.",
        "Pisces": "Soft, rolling diffusion cloud with subdued high frequencies.",
        "Scorpio": "Fast, biting transient response with dense stereo crossfeed.",
        "Libra": "Balanced, symmetrical stereo diffusion for master buses and group stems.",
        "Leo": "Loud, forward, resonant character with pronounced early reflections.",
        "Virgo": "Clean, analytical, high-fidelity diffusion with zero low-end mud.",
        "Pleiades": "Sparkling multi-tap clustered reflections with celestial chorusing.",
        "Sirius": "Bright, direct, shimmering space ideal for plucked strings and leads.",
    }

    # Delay Sync options
    # Valhalla maps DelaySync to discrete normalized steps
    SYNC_MODES: Dict[str, float] = {
        "unsynced": 0.0,
        "ms": 0.0,
        "synced": 0.25,
        "straight": 0.25,
        "dotted": 0.5,
        "triplet": 0.75,
    }

    # Delay Note division table (approximate normalized step representations)
    NOTE_DIVISIONS: Dict[str, float] = {
        "1/64": 0.0,
        "1/32": 0.071428575,
        "1/16": 0.142857149,
        "1/8": 0.285714298,
        "1/4": 0.428571433,
        "1/2": 0.571428597,
        "1/1": 0.714285731,
        "2/1": 0.857142866,
        "4/1": 1.0,
    }

    # All 16 XML Float Parameters and their valid range [min, max]
    PARAMETER_SPECS: Dict[str, Tuple[float, float, float]] = {
        # name: (min_val, max_val, default_val)
        "Mix": (0.0, 1.0, 1.0),
        "DelaySync": (0.0, 1.0, 0.25),
        "DelayNote": (0.0, 1.0, 0.285714298),
        "Delay_Ms": (0.0, 1.0, 0.5),
        "DelayWarp": (0.0, 1.0, 0.5),
        "Clear": (0.0, 1.0, 0.0),
        "Feedback": (0.0, 1.0, 0.5),
        "Density": (0.0, 1.0, 0.5),
        "Width": (0.0, 1.0, 1.0),
        "LowCut": (0.0, 1.0, 0.0),
        "HighCut": (0.0, 1.0, 1.0),
        "ModRate": (0.0, 1.0, 0.5),
        "ModDepth": (0.0, 1.0, 0.5),
        "Mode": (0.0, 1.0, 0.0),
        "Reserved1": (0.0, 1.0, 0.0),
        "Reserved2": (0.0, 1.0, 0.0),
        "Reserved3": (0.0, 1.0, 0.0),
        "Reserved4": (0.0, 1.0, 0.0),
    }

    @classmethod
    def mode_to_float(cls, mode: str) -> float:
        """
        Convert mode name or index string to normalized float in [0.0, 1.0].
        Formula: index / 21.0
        """
        cleaned = mode.strip().lower()
        for idx, m in enumerate(cls.MODES):
            if m.lower() == cleaned:
                return idx / float(cls.NUM_MODES - 1)
        # Check if numeric string
        try:
            val = float(mode)
            if 0 <= val < cls.NUM_MODES and val.is_integer():
                return int(val) / float(cls.NUM_MODES - 1)
            if 0.0 <= val <= 1.0:
                return val
        except ValueError:
            pass
        raise ValueError(
            f"Unknown Valhalla Supermassive mode '{mode}'. "
            f"Valid modes: {', '.join(cls.MODES)}"
        )

    @classmethod
    def float_to_mode(cls, value: float) -> str:
        """
        Convert normalized float to closest canonical mode name.
        """
        clamped = max(0.0, min(1.0, value))
        idx = int(round(clamped * (cls.NUM_MODES - 1)))
        idx = max(0, min(cls.NUM_MODES - 1, idx))
        return cls.MODES[idx]

    @classmethod
    def float_to_mode_index(cls, value: float) -> int:
        """Convert normalized float to mode integer index [0, 21]."""
        clamped = max(0.0, min(1.0, value))
        idx = int(round(clamped * (cls.NUM_MODES - 1)))
        return max(0, min(cls.NUM_MODES - 1, idx))

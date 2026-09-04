"""
Capability Registry:
Maintains the single source of truth of available Ableton devices, formats, and libraries.
Enforces Native-First policy: Ableton Native > Max for Live > Third-Party > Fallback.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

@dataclass
class CapabilityRegistry:
    ableton_version: str = "12.4.5"
    is_live_suite: bool = True
    native_instruments: Set[str] = field(default_factory=lambda: {
        "Wavetable", "Drift", "Operator", "Analog", "Simpler", "Sampler", "Tension", "Collision"
    })
    native_effects: Set[str] = field(default_factory=lambda: {
        "EQ Eight", "Channel EQ", "Saturator", "Compressor", "Glue Compressor",
        "Drum Buss", "Utility", "Delay", "Reverb", "Hybrid Reverb",
        "Chorus-Ensemble", "Phaser-Flanger", "Redux", "Erosion", "Limiter"
    })
    installed_plugins: Set[str] = field(default_factory=set)
    sample_libraries: List[str] = field(default_factory=lambda: [
        r"C:\Users\sasuk\Music",
        r"D:\Samples"
    ])

    def is_instrument_available(self, name: str) -> bool:
        return name in self.native_instruments or name in self.installed_plugins

    def is_effect_available(self, name: str) -> bool:
        return name in self.native_effects or name in self.installed_plugins

    def select_instrument(self, role: str, preference: Optional[List[str]] = None) -> str:
        """Native-first instrument selection."""
        pref_list = preference or ["Wavetable", "Drift", "Operator", "Simpler"]
        for p in pref_list:
            if self.is_instrument_available(p):
                return p
        return "Simpler"

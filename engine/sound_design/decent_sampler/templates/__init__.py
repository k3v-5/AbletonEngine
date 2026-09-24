# engine/sound_design/decent_sampler/templates/__init__.py
"""
Decent Sampler Instrument Archetype Templates.

Pre-configured compilation archetypes covering:
- Acoustic: Grand Piano (multi-velocity, release triggers)
- Acoustic: Orchestral Strings (expressive attack, room reverb)
- Percussive: Drum Kit (round-robin, choke groups)
- Designed: 808 Sub Bass (pitch tracking, wave folder drive)
"""

from .acoustic_piano import create_acoustic_piano
from .orchestral_strings import create_orchestral_strings
from .drum_kit import create_drum_kit
from .designed_808 import create_808_sub_bass
from .dual_layer_pad import create_dual_layer_pad

__all__ = [
    "create_acoustic_piano",
    "create_orchestral_strings",
    "create_drum_kit",
    "create_808_sub_bass",
    "create_dual_layer_pad",
]


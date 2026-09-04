"""
Universal 8-Macro Architecture:
Defines standard macro controls and their multi-parameter bindings.
"""
from typing import Dict, List, Any

UNIVERSAL_MACROS = [
    "WEIGHT", "GRIT", "PUNCH", "MOVEMENT",
    "SPACE", "WIDTH", "BRIGHTNESS", "CHARACTER"
]

ROLE_MACRO_PROFILES: Dict[str, Dict[str, str]] = {
    "BASS": {
        "Macro 1": "WEIGHT",
        "Macro 2": "GRIT",
        "Macro 3": "PUNCH",
        "Macro 4": "MOVEMENT",
        "Macro 5": "SPACE",
        "Macro 6": "WIDTH",
        "Macro 7": "BRIGHTNESS",
        "Macro 8": "DECAY"
    },
    "LEAD": {
        "Macro 1": "BRIGHTNESS",
        "Macro 2": "SPACE",
        "Macro 3": "MOVEMENT",
        "Macro 4": "GRIT",
        "Macro 5": "WIDTH",
        "Macro 6": "ATTACK",
        "Macro 7": "DELAY_SEND",
        "Macro 8": "REVERB_SEND"
    },
    "PAD": {
        "Macro 1": "SPACE",
        "Macro 2": "WIDTH",
        "Macro 3": "BRIGHTNESS",
        "Macro 4": "WARMTH",
        "Macro 5": "MOVEMENT",
        "Macro 6": "ATTACK",
        "Macro 7": "DECAY",
        "Macro 8": "AIR"
    }
}

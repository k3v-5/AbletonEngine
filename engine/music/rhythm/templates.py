# engine/music/rhythm/templates.py
from typing import Dict, List, Any
from ...instruments.drum_map import DrumMap

# Canonical DrumMap link (Single Source of Truth)
GM_DRUM_MAP = {
    "kick": DrumMap.KICK,             # 36 (C1)
    "snare": DrumMap.SNARE,           # 38 (D1)
    "clap": DrumMap.CLAP,             # 39 (D#1)
    "hat_closed": DrumMap.CLOSED_HAT, # 40 (E1)
    "hat_pedal": DrumMap.CLOSED_HAT,  # 40 (E1)
    "hat_open": DrumMap.OPEN_HAT,     # 41 (F1)
    "perc_1": DrumMap.PERC_1,         # 42 (F#1)
    "perc_2": DrumMap.PERC_2,         # 43 (G1)
    "foley": DrumMap.PERC_1,          # 42 (F#1)
    "shaker": DrumMap.SHAKER,         # 44 (G#1)
    "tom_low": DrumMap.TOM,           # 45 (A1)
    "tom_mid": DrumMap.TOM,           # 45 (A1)
    "tom_high": DrumMap.TOM,          # 45 (A1)
    "crash": DrumMap.IMPACT,          # 47 (B1)
    "ride": DrumMap.OPEN_HAT,         # 41 (F1)
    "fx": DrumMap.FX,                 # 46 (A#1)
    "impact": DrumMap.IMPACT          # 47 (B1)
}


# 1-bar pattern templates (offsets in beats 0.0 to 3.75 for 1/16 grid)
GENRE_TEMPLATES: Dict[str, Dict[str, List[float]]] = {
    "techno": {
        "kick": [0.0, 1.0, 2.0, 3.0],
        "clap": [1.0, 3.0],
        "hat_open": [0.5, 1.5, 2.5, 3.5],
        "hat_closed": [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75],
        "ride": [0.5, 1.5, 2.5, 3.5]
    },
    "melodic_techno": {
        "kick": [0.0, 1.0, 2.0, 3.0],
        "clap": [1.0, 3.0],
        "hat_open": [0.5, 1.5, 2.5, 3.5],
        "hat_closed": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75],
        "foley": [0.75, 1.75, 2.75, 3.75]
    },
    "house": {
        "kick": [0.0, 1.0, 2.0, 3.0],
        "clap": [1.0, 3.0],
        "hat_open": [0.5, 1.5, 2.5, 3.5],
        "hat_closed": [0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 2.25, 2.5, 2.75, 3.25, 3.5, 3.75]
    },
    "trap": {
        "kick": [0.0, 1.75, 2.5],
        "snare": [2.0],
        "clap": [2.0],
        "hat_closed": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75],
        "hat_open": [1.5, 3.5]
    },
    "drill": {
        "kick": [0.0, 1.75, 3.0],
        "snare": [1.5, 3.25],
        "hat_closed": [0.0, 0.333, 0.666, 1.0, 1.333, 1.666, 2.0, 2.333, 2.666, 3.0, 3.333, 3.666]
    },
    "dnb": {
        "kick": [0.0, 2.5],
        "snare": [1.0, 3.0],
        "hat_closed": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75]
    }
}

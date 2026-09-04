# engine/music/rhythm/grid.py
from typing import Dict, List

SUBDIVISION_BEATS: Dict[str, float] = {
    "1/1": 4.0,
    "1/2": 2.0,
    "1/4": 1.0,
    "1/8": 0.5,
    "1/16": 0.25,
    "1/32": 0.125,
    "1/4T": 4.0 / 3.0,
    "1/8T": 2.0 / 3.0,
    "1/16T": 1.0 / 3.0,
    "1/32T": 1.0 / 6.0
}

def get_subdivision_duration(subdivision: str) -> float:
    return SUBDIVISION_BEATS.get(subdivision.upper(), 0.25)

def generate_grid_offsets(total_bars: int, subdivision: str = "1/16") -> List[float]:
    """Generate all rhythmic grid beat offsets across total_bars"""
    step = get_subdivision_duration(subdivision)
    total_beats = total_bars * 4.0
    offsets = []
    curr = 0.0
    while curr < total_beats - 1e-5:
        offsets.append(round(curr, 5))
        curr += step
    return offsets

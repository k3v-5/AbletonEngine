# engine/music/theory/scales.py
from typing import List, Dict, Optional, Tuple
from .notes import (
    normalize_pitch_class, PC_TO_SHARP_NAME,
    PC_TO_FLAT_NAME, midi_to_note
)

SCALE_INTERVALS: Dict[str, List[int]] = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
}

def normalize_scale_name(scale: str) -> str:
    s = scale.strip().lower().replace(" ", "_").replace("-", "_")
    if s in SCALE_INTERVALS:
        return s
    # Common aliases
    aliases = {
        "aeolian": "natural_minor",
        "ionian": "major",
        "penta_minor": "pentatonic_minor",
        "penta_major": "pentatonic_major",
        "harmonic": "harmonic_minor",
        "melodic": "melodic_minor"
    }
    if s in aliases:
        return aliases[s]
    raise ValueError(f"Unknown scale '{scale}'. Soportadas: {list(SCALE_INTERVALS.keys())}")

def get_scale_intervals(scale_name: str) -> List[int]:
    norm = normalize_scale_name(scale_name)
    return SCALE_INTERVALS[norm]

def get_scale_pitch_classes(key: str, scale_name: str) -> List[int]:
    """Returns the list of pitch classes (0-11) belonging to the key and scale"""
    root_pc = normalize_pitch_class(key)
    intervals = get_scale_intervals(scale_name)
    return [(root_pc + interval) % 12 for interval in intervals]

def get_scale_notes(key: str, scale_name: str) -> List[str]:
    """Returns note names of the scale, e.g. 'F', 'G', 'Ab', 'Bb', 'C', 'Db', 'Eb'"""
    pcs = get_scale_pitch_classes(key, scale_name)
    # If key contains 'b' or is 'F', format with flats for readability
    use_flats = "B" in key.upper() or key.upper() in ["F", "D", "G"] and "minor" in scale_name
    return [PC_TO_FLAT_NAME[pc] if use_flats else PC_TO_SHARP_NAME[pc] for pc in pcs]

def scale_degree_to_midi(key: str, scale_name: str, degree: int, octave: int = 4) -> int:
    """
    Convert a 1-based scale degree (e.g. 1=tonic, 3=third, 5=fifth) to a MIDI pitch.
    Handles degree overflow across octaves (e.g. degree 8 = octave + 1 tonic).
    """
    root_pc = normalize_pitch_class(key)
    intervals = get_scale_intervals(scale_name)
    scale_len = len(intervals)

    # 1-indexed conversion
    deg_zero_indexed = degree - 1
    octave_shift = deg_zero_indexed // scale_len
    deg_idx = deg_zero_indexed % scale_len

    interval = intervals[deg_idx]
    final_pc = (root_pc + interval) % 12
    final_octave = octave + octave_shift + ((root_pc + interval) // 12)

    midi_val = (final_octave + 1) * 12 + final_pc
    return max(0, min(127, midi_val))

def midi_to_scale_degree(key: str, scale_name: str, midi_pitch: int) -> Optional[int]:
    """Finds the 1-based scale degree of a MIDI pitch, or returns None if outside scale"""
    root_pc = normalize_pitch_class(key)
    intervals = get_scale_intervals(scale_name)
    pc = midi_pitch % 12

    for i, interval in enumerate(intervals):
        if (root_pc + interval) % 12 == pc:
            return i + 1
    return None

def is_in_scale(key: str, scale_name: str, midi_pitch: int) -> bool:
    return midi_to_scale_degree(key, scale_name, midi_pitch) is not None

def snap_to_scale(key: str, scale_name: str, midi_pitch: int) -> int:
    """Diatonic pitch quantizer: snaps a chromatic MIDI pitch to the closest note in the scale"""
    if is_in_scale(key, scale_name, midi_pitch):
        return midi_pitch

    pcs = get_scale_pitch_classes(key, scale_name)
    current_pc = midi_pitch % 12

    # Find closest pitch class
    closest_pc = min(pcs, key=lambda pc: min(abs(pc - current_pc), 12 - abs(pc - current_pc)))
    delta = closest_pc - current_pc
    if delta > 6:
        delta -= 12
    elif delta < -6:
        delta += 12

    return max(0, min(127, midi_pitch + delta))

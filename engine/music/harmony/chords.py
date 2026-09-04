# engine/music/harmony/chords.py
from typing import List, Dict, Tuple
from ..models import Chord
from ..theory.notes import normalize_pitch_class

CHORD_INTERVALS: Dict[str, List[int]] = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "dominant7": [0, 4, 7, 10],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "minor7b5": [0, 3, 6, 10],
    "diminished7": [0, 3, 6, 9],
    "major9": [0, 4, 7, 11, 14],
    "minor9": [0, 3, 7, 10, 14],
    "dominant9": [0, 4, 7, 10, 14],
    "major11": [0, 4, 7, 11, 14, 17],
    "minor11": [0, 3, 7, 10, 14, 17],
    "dominant13": [0, 4, 7, 10, 14, 21]
}

def get_chord_intervals(quality: str, extensions: List[str] = None) -> List[int]:
    """Get relative semitone intervals for a chord quality and optional extensions"""
    exts = extensions or []
    # If 9 is in extensions, check composite names
    if "9" in exts:
        if quality == "major": return CHORD_INTERVALS["major9"]
        if quality == "minor": return CHORD_INTERVALS["minor9"]
        if quality == "dominant7" or quality == "dominant": return CHORD_INTERVALS["dominant9"]
    if "7" in exts:
        if quality == "major": return CHORD_INTERVALS["major7"]
        if quality == "minor": return CHORD_INTERVALS["minor7"]
        if quality == "diminished": return CHORD_INTERVALS["diminished7"]
    
    q_norm = quality.lower()
    if q_norm in CHORD_INTERVALS:
        return CHORD_INTERVALS[q_norm]
    return CHORD_INTERVALS.get("major", [0, 4, 7])

def get_chord_pitches(chord: Chord, base_octave: int = 3) -> List[int]:
    """Returns raw MIDI pitches for a Chord in basic closed position at base_octave"""
    root_pc = normalize_pitch_class(chord.root)
    intervals = get_chord_intervals(chord.quality, chord.extensions)
    root_midi = (base_octave + 1) * 12 + root_pc

    pitches = [root_midi + interval for interval in intervals]

    # Apply inversion
    inv = chord.inversion % len(pitches) if pitches else 0
    for i in range(inv):
        pitches[i] += 12
    pitches.sort()

    return pitches

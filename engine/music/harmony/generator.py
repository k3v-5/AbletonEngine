# engine/music/harmony/generator.py
from typing import List, Dict, Any, Optional
from ..models import Chord
from .roman import roman_progression_to_chords, parse_progression_string

def generate_harmonic_structure(
    key: str,
    scale: str,
    progression: str = "i - VI - III - VII",
    bars: int = 16,
    chord_density: float = 0.5,
    extensions: bool = False,
    tension: float = 0.5
) -> List[Chord]:
    """
    Generates a structured timeline of Chord objects filling the specified number of bars.
    """
    tokens = parse_progression_string(progression) if isinstance(progression, str) else list(progression)
    if not tokens:
        tokens = ["i", "VI", "III", "VII"]

    # Calculate chord duration in musical beats (4 beats per bar in 4/4)
    total_beats = bars * 4.0
    # Determine how many chords fit across the bars
    # density ~0.5 means 1 chord every 2 bars (8 beats) or 1 chord per bar (4 beats)
    if chord_density <= 0.25:
        beats_per_chord = 8.0   # 1 chord every 2 bars
    elif chord_density <= 0.75:
        beats_per_chord = 4.0   # 1 chord per bar
    else:
        beats_per_chord = 2.0   # 2 chords per bar

    # If tension is high and extensions requested, add 7ths or 9ths
    enhanced_tokens = []
    for token in tokens:
        tok = token
        if extensions or tension > 0.6:
            if "7" not in tok and "9" not in tok:
                tok = f"{tok}7"
        enhanced_tokens.append(tok)

    base_chords = roman_progression_to_chords(key, scale, enhanced_tokens, chord_duration=beats_per_chord)

    # Tile or stretch chords to fill total_beats
    timeline_chords: List[Chord] = []
    current_beat = 0.0
    idx = 0

    while current_beat < total_beats:
        orig = base_chords[idx % len(base_chords)]
        dur = min(beats_per_chord, total_beats - current_beat)
        c = Chord(
            root=orig.root,
            quality=orig.quality,
            extensions=list(orig.extensions),
            inversion=orig.inversion,
            bass_note=orig.bass_note,
            duration=dur,
            roman_numeral=orig.roman_numeral
        )
        timeline_chords.append(c)
        current_beat += dur
        idx += 1

    return timeline_chords

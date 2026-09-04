# engine/music/voicing/profiles.py
from typing import List, Optional
from ..models import Chord
from ..harmony.chords import get_chord_pitches

def apply_voicing_profile(
    chord: Chord,
    style: str = "close",
    register: str = "mid",
    min_pitch: int = 36,
    max_pitch: int = 84,
    register_center: Optional[int] = None
) -> List[int]:
    """
    Transforms a Chord's raw pitches into a specific voicing style and register.
    Styles supported: close, open, drop_2, drop_3, spread, rootless, quartal
    """
    base_octave = 3
    if register_center is not None:
        base_octave = max(1, min(6, (register_center // 12) - 1))
    elif register == "low":
        base_octave = 2
    elif register == "high":
        base_octave = 4

    pitches = get_chord_pitches(chord, base_octave=base_octave)
    if not pitches:
        return []

    style_lower = style.lower()

    if style_lower == "drop_2" and len(pitches) >= 4:
        # Drop the second highest voice down by one octave
        dropped = pitches[-2] - 12
        new_pitches = [dropped] + [pitches[i] for i in range(len(pitches)) if i != len(pitches) - 2]
        new_pitches.sort()
        pitches = new_pitches

    elif style_lower == "drop_3" and len(pitches) >= 4:
        # Drop the third highest voice down by one octave
        dropped = pitches[-3] - 12
        new_pitches = [dropped] + [pitches[i] for i in range(len(pitches)) if i != len(pitches) - 3]
        new_pitches.sort()
        pitches = new_pitches

    elif style_lower == "open" or style_lower == "spread":
        # Spread alternate voices up an octave
        spread_pitches = []
        for idx, p in enumerate(pitches):
            if idx % 2 == 1:
                spread_pitches.append(p + 12)
            else:
                spread_pitches.append(p)
        spread_pitches.sort()
        pitches = spread_pitches

    elif style_lower == "rootless" and len(pitches) >= 3:
        # Remove root, add an upper extension (e.g. 9th)
        pitches = pitches[1:]
        pitches.append(pitches[-1] + 4)
        pitches.sort()

    elif style_lower == "quartal":
        # Build stack of fourths from root
        root = pitches[0]
        pitches = [root, root + 5, root + 10, root + 15]

    # Constrain within bounds
    clamped = []
    for p in pitches:
        while p < min_pitch: p += 12
        while p > max_pitch: p -= 12
        clamped.append(p)
    clamped.sort()
    return clamped

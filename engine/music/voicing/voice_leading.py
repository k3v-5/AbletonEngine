# engine/music/voicing/voice_leading.py
import itertools
from typing import List, Tuple
from ..models import Chord
from .profiles import apply_voicing_profile

def voice_leading_cost(
    prev_voicing: List[int],
    curr_voicing: List[int],
    max_leap_allowed: int = 7
) -> float:
    """
    Cost function evaluating voice leading quality:
    - Movement distance: sum of squared differences between voice lines
    - Penalty for voice crossing
    - Penalty for large leaps (> max_leap_allowed)
    - Bonus for common tones retained exactly
    """
    if len(prev_voicing) != len(curr_voicing):
        # Difference in voice count: pad with common register
        min_len = min(len(prev_voicing), len(curr_voicing))
        prev_voicing = prev_voicing[:min_len]
        curr_voicing = curr_voicing[:min_len]

    cost = 0.0
    for p_v, c_v in zip(prev_voicing, curr_voicing):
        dist = abs(c_v - p_v)
        cost += (dist ** 2)
        if dist == 0:
            cost -= 4.0  # Reward retaining common tone
        elif dist > max_leap_allowed:
            cost += 15.0 * (dist - max_leap_allowed)  # Heavy penalty for leaps

    # Penalty for voice crossing (ensure sorted order)
    for i in range(len(curr_voicing) - 1):
        if curr_voicing[i] >= curr_voicing[i + 1]:
            cost += 30.0

    return cost

def optimize_voice_leading(
    chords: List[Chord],
    style: str = "open",
    register: str = "mid",
    min_pitch: int = 40,
    max_pitch: int = 84,
    register_center: Optional[int] = None
) -> List[List[int]]:
    """
    Smooths a progression of Chords using a Voice Leading Solver that minimizes intervallic leaps.
    Returns a list of voicings (each voicing is a list of MIDI note pitches).
    """
    if not chords:
        return []

    # 1. Voice first chord
    voicings: List[List[int]] = []
    first_v = apply_voicing_profile(
        chords[0], style=style, register=register,
        min_pitch=min_pitch, max_pitch=max_pitch,
        register_center=register_center
    )
    voicings.append(first_v)

    target_voice_count = len(first_v)

    # 2. Iteratively voice remaining chords
    for c_idx in range(1, len(chords)):
        chord = chords[c_idx]
        prev_v = voicings[-1]

        # Generate candidate permutations by applying different octave shifts to the chord's pitch classes
        base_v = apply_voicing_profile(chord, style="close", register=register, min_pitch=min_pitch - 12, max_pitch=max_pitch + 12)
        pitch_classes = [(p % 12) for p in base_v]

        best_voicing = None
        best_cost = float("inf")

        # Explore candidate voicings by placing each pitch class in the octave closest to prev_v
        candidate_notes_options = []
        for pc in pitch_classes:
            options = []
            for oct_val in range(2, 6):
                m = (oct_val + 1) * 12 + pc
                if min_pitch <= m <= max_pitch:
                    options.append(m)
            if not options:
                options = [(4 + 1) * 12 + pc]
            candidate_notes_options.append(options)

        # Search combinations (bounded Cartesian product)
        for combo in itertools.product(*candidate_notes_options):
            sorted_combo = sorted(list(set(combo)))
            if len(sorted_combo) < 3:
                continue

            cost = voice_leading_cost(prev_v, sorted_combo)
            if cost < best_cost:
                best_cost = cost
                best_voicing = sorted_combo

        if best_voicing is None:
            best_voicing = apply_voicing_profile(chord, style=style, register=register, min_pitch=min_pitch, max_pitch=max_pitch)

        voicings.append(best_voicing)

    return voicings

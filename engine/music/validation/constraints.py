# engine/music/validation/constraints.py
from typing import List, Dict, Any, Tuple
from ..models import NoteEvent
from ..theory.scales import is_in_scale

# Pitch boundaries per role
ROLE_REGISTER_BOUNDS: Dict[str, Tuple[int, int]] = {
    "sub_bass": (28, 48),  # E0 to C2 (~41 Hz - 130 Hz)
    "bass": (28, 60),      # E0 to C3
    "kick": (35, 38),      # Fixed acoustic/electronic kick region
    "chords": (48, 84),    # C2 to C5
    "pad": (48, 88),       # C2 to E5
    "lead": (60, 96),      # C3 to C6
    "counter_lead": (60, 96),
    "arpeggio": (55, 96)
}

def validate_notes(
    notes: List[NoteEvent],
    role: str = "bass",
    key: str = "F",
    scale: str = "natural_minor",
    allow_dissonance_on_weak_beats: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validates NoteEvents against fundamental musical and physical production constraints.
    Returns (is_valid, list_of_warning_or_error_messages).
    """
    warnings = []
    role_key = role.lower().replace("-", "_").replace(" ", "_")

    if not notes:
        return True, []

    bounds = ROLE_REGISTER_BOUNDS.get(role_key, (0, 127))
    min_p, max_p = bounds

    sorted_notes = sorted(notes, key=lambda n: n.start)

    # 1. Monophony check for sub_bass and kick
    if role_key in ["sub_bass", "kick"]:
        for i in range(len(sorted_notes) - 1):
            n1 = sorted_notes[i]
            n2 = sorted_notes[i + 1]
            if n2.start < (n1.start + n1.duration - 0.01):
                warnings.append(f"Polyphony detected in strictly monophonic role '{role}' at beat {n2.start}")

    # 2. Register boundaries check
    for n in sorted_notes:
        if n.pitch < min_p or n.pitch > max_p:
            warnings.append(f"Pitch {n.pitch} is outside allowed range [{min_p}, {max_p}] for role '{role}'")

    # 3. Scale coherence check on downbeats
    for n in sorted_notes:
        is_downbeat = (n.start % 1.0 == 0.0)
        if is_downbeat or not allow_dissonance_on_weak_beats:
            if not is_in_scale(key, scale, n.pitch):
                warnings.append(f"Out-of-scale pitch {n.pitch} detected on downbeat {n.start} in {key} {scale}")

    # 4. Duration & Timing validity
    for n in sorted_notes:
        if n.start < 0.0:
            warnings.append(f"Negative note start time {n.start}")
        if n.duration <= 0.0:
            warnings.append(f"Invalid non-positive note duration {n.duration}")

    is_valid = len(warnings) == 0
    return is_valid, warnings

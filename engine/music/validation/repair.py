# engine/music/validation/repair.py
from typing import List, Tuple
from ..models import NoteEvent
from .constraints import ROLE_REGISTER_BOUNDS, validate_notes
from ..theory.scales import snap_to_scale, is_in_scale

def repair_notes(
    notes: List[NoteEvent],
    role: str = "bass",
    key: str = "F",
    scale: str = "natural_minor"
) -> Tuple[List[NoteEvent], List[str]]:
    """
    Deterministically repairs musical constraint violations:
    - Shifts pitches by octaves if outside registered bounds.
    - Snaps chromatic downbeats to the closest diatonic scale degree.
    - Enforces monophony on sub-bass and kick.
    """
    repaired: List[NoteEvent] = []
    actions: List[str] = []
    role_key = role.lower().replace("-", "_").replace(" ", "_")
    min_p, max_p = ROLE_REGISTER_BOUNDS.get(role_key, (0, 127))

    for note in notes:
        p = note.pitch

        # Register clamp via octave transposition
        while p < min_p:
            p += 12
            actions.append(f"Transposed pitch up 1 octave to {p}")
        while p > max_p:
            p -= 12
            actions.append(f"Transposed pitch down 1 octave to {p}")

        # Scale snapping on downbeats
        if note.start % 1.0 == 0.0 and not is_in_scale(key, scale, p):
            snapped = snap_to_scale(key, scale, p)
            actions.append(f"Snapped chromatic pitch {p} to diatonic {snapped}")
            p = snapped

        repaired.append(NoteEvent(
            pitch=p,
            pitch_class=p % 12,
            octave=(p // 12) - 1,
            start=max(0.0, note.start),
            duration=max(0.1, note.duration),
            velocity=max(1, min(127, note.velocity)),
            channel=note.channel,
            probability=note.probability,
            accent=note.accent
        ))

    # Monophony collapse for sub_bass and kick
    if role_key in ["sub_bass", "kick"]:
        repaired.sort(key=lambda n: n.start)
        monophonic: List[NoteEvent] = []
        for n in repaired:
            if not monophonic:
                monophonic.append(n)
                continue
            prev = monophonic[-1]
            if n.start < prev.start + prev.duration:
                # Overlap! Keep the lowest pitch or shorten prev duration
                if n.pitch < prev.pitch:
                    # Replace previous or truncate
                    prev.duration = max(0.1, n.start - prev.start)
                    monophonic.append(n)
                    actions.append(f"Truncated overlapping sub-bass note at beat {prev.start}")
                else:
                    # Truncate previous note before this note
                    prev.duration = max(0.1, n.start - prev.start)
                    monophonic.append(n)
            else:
                monophonic.append(n)
        repaired = monophonic

    return repaired, actions

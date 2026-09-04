# engine/music/variation/engine.py
import random
from typing import List, Optional
from ..models import NoteEvent
from ..theory.scales import snap_to_scale, get_scale_pitch_classes

def apply_variation(
    notes: List[NoteEvent],
    variation_amount: float = 0.3,
    key: str = "F",
    scale: str = "natural_minor",
    seed: Optional[int] = 12345
) -> List[NoteEvent]:
    """
    Applies musical variation to avoid static looping while preserving motif identity:
    - variation_amount = 0.0 -> exact identical copy
    - variation_amount = 1.0 -> deep progressive evolution
    - Controlled by seed for deterministic reproducibility.
    """
    if variation_amount <= 0.0 or not notes:
        return [NoteEvent(**n.__dict__) for n in notes]

    rng = random.Random(seed)
    pcs = get_scale_pitch_classes(key, scale)
    varied: List[NoteEvent] = []

    for note in notes:
        # Determine if this specific note undergoes variation
        if rng.random() > variation_amount:
            varied.append(NoteEvent(**note.__dict__))
            continue

        dice = rng.random()

        # Option A: Rhythmic extension or shortening
        if dice < 0.30:
            factor = rng.choice([0.5, 1.5, 2.0])
            new_dur = max(0.125, note.duration * factor)
            ev = NoteEvent(
                pitch=note.pitch,
                pitch_class=note.pitch_class,
                octave=note.octave,
                start=note.start,
                duration=new_dur,
                velocity=note.velocity,
                accent=note.accent
            )
            varied.append(ev)

        # Option B: Octave shift (+/- 12 semitones)
        elif dice < 0.60:
            shift = rng.choice([-12, 12])
            new_pitch = max(28, min(100, note.pitch + shift))
            ev = NoteEvent(
                pitch=new_pitch,
                pitch_class=new_pitch % 12,
                octave=(new_pitch // 12) - 1,
                start=note.start,
                duration=note.duration,
                velocity=note.velocity,
                accent=note.accent
            )
            varied.append(ev)

        # Option C: Diatonic neighbor tone (step up or down in scale)
        elif dice < 0.85:
            step = rng.choice([-2, -1, 1, 2])
            shifted_pitch = snap_to_scale(key, scale, note.pitch + step)
            ev = NoteEvent(
                pitch=shifted_pitch,
                pitch_class=shifted_pitch % 12,
                octave=(shifted_pitch // 12) - 1,
                start=note.start,
                duration=note.duration,
                velocity=note.velocity,
                accent=note.accent
            )
            varied.append(ev)

        # Option D: Rest insertion (drop note) if density reduction desired
        else:
            # Drop note occasionally to let the phrase breathe
            pass

    return sorted(varied, key=lambda n: n.start)

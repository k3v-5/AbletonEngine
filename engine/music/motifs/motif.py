# engine/music/motifs/motif.py
from typing import List, Optional
from ..models import Motif, NoteEvent
from ..theory.notes import normalize_pitch_class
from ..models import generate_id

def create_motif_from_notes(
    name: str,
    notes: List[NoteEvent],
    role: Optional[str] = None,
    section: Optional[str] = None
) -> Motif:
    """
    Extracts invariant structural intervals, rhythmic durations and accents from a list of NoteEvents.
    """
    if not notes:
        return Motif(id=generate_id("motif"), name=name, length_beats=4.0)

    sorted_notes = sorted(notes, key=lambda n: n.start)
    first_pitch = sorted_notes[0].pitch
    start_time = sorted_notes[0].start
    last_end = max(n.start + n.duration for n in sorted_notes)
    total_length = last_end - start_time

    intervals = [n.pitch - first_pitch for n in sorted_notes]
    rhythm = [n.duration for n in sorted_notes]
    offsets = [n.start - start_time for n in sorted_notes]
    accents = [n.accent for n in sorted_notes]

    return Motif(
        id=generate_id("motif"),
        name=name,
        length_beats=total_length,
        intervals=intervals,
        rhythm=rhythm,
        offsets=offsets,
        accents=accents,
        role=role,
        section=section
    )

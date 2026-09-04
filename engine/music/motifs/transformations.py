# engine/music/motifs/transformations.py
from typing import List, Optional
from ..models import Motif, NoteEvent, generate_id
from ..theory.notes import normalize_pitch_class
from ..theory.scales import snap_to_scale

def transform_motif(
    motif: Motif,
    transformation: str,
    params: Optional[dict] = None
) -> Motif:
    """
    Applies musical motif transformations:
    - 'transpose': shifts intervals by semitones
    - 'invert': mirror reflection of intervals around pivot
    - 'retrograde': reverse order of notes
    - 'augmentation': stretch time by factor (half-time)
    - 'diminution': compress time by factor (double-time)
    - 'displacement': rhythmic syncopation shift
    - 'fragment': extract slice of motif
    """
    p = params or {}
    t_name = transformation.lower()

    new_intervals = list(motif.intervals)
    new_rhythm = list(motif.rhythm)
    new_offsets = list(motif.offsets)
    new_accents = list(motif.accents)
    new_length = motif.length_beats

    if t_name == "transpose":
        semitones = int(p.get("semitones", 2))
        new_intervals = [i + semitones for i in new_intervals]

    elif t_name == "invert":
        pivot = int(p.get("pivot", 0))
        # Mirror: interval -> pivot - (interval - pivot)
        new_intervals = [2 * pivot - i for i in new_intervals]

    elif t_name == "retrograde":
        # Reverse notes in time
        new_intervals = list(reversed(new_intervals))
        new_rhythm = list(reversed(new_rhythm))
        new_accents = list(reversed(new_accents))
        # Re-compute offsets from end
        if new_offsets:
            max_off = max(new_offsets)
            new_offsets = [max_off - off for off in reversed(new_offsets)]

    elif t_name == "augmentation":
        factor = float(p.get("factor", 2.0))
        new_rhythm = [r * factor for r in new_rhythm]
        new_offsets = [off * factor for off in new_offsets]
        new_length = new_length * factor

    elif t_name == "diminution":
        factor = float(p.get("factor", 0.5))
        new_rhythm = [max(0.1, r * factor) for r in new_rhythm]
        new_offsets = [off * factor for off in new_offsets]
        new_length = new_length * factor

    elif t_name == "displacement" or t_name == "rhythmic_displacement":
        shift = float(p.get("shift_beats", 0.5))
        new_offsets = [(off + shift) % max(1.0, new_length) for off in new_offsets]

    elif t_name == "fragment":
        start_b = float(p.get("start_beat", 0.0))
        end_b = float(p.get("end_beat", new_length / 2.0))
        indices = [idx for idx, off in enumerate(new_offsets) if start_b <= off < end_b]
        if indices:
            new_intervals = [new_intervals[i] for i in indices]
            new_rhythm = [new_rhythm[i] for i in indices]
            base_off = new_offsets[indices[0]]
            new_offsets = [new_offsets[i] - base_off for i in indices]
            new_accents = [new_accents[i] for i in indices]
            new_length = end_b - start_b

    return Motif(
        id=generate_id("motif"),
        name=f"{motif.name}_{t_name}",
        length_beats=new_length,
        intervals=new_intervals,
        rhythm=new_rhythm,
        offsets=new_offsets,
        accents=new_accents,
        role=motif.role,
        section=motif.section
    )

def realize_motif_as_notes(
    motif: Motif,
    root_pitch: int = 60,
    start_beat: float = 0.0,
    key: str = "F",
    scale: str = "natural_minor",
    base_velocity: int = 95
) -> List[NoteEvent]:
    """Converts a relative Motif into concrete, scale-quantized NoteEvents"""
    notes: List[NoteEvent] = []
    for interval, dur, off, acc in zip(motif.intervals, motif.rhythm, motif.offsets, motif.accents):
        raw_pitch = root_pitch + interval
        # Ensure diatonic scale coherence
        final_pitch = snap_to_scale(key, scale, raw_pitch)
        vel = max(1, min(127, int(base_velocity + acc * 25)))
        ev = NoteEvent(
            pitch=final_pitch,
            pitch_class=final_pitch % 12,
            octave=(final_pitch // 12) - 1,
            start=round(start_beat + off, 4),
            duration=round(dur, 4),
            velocity=vel,
            accent=acc
        )
        notes.append(ev)
    return notes

# engine/music/theory/__init__.py
from .notes import (
    parse_note_string, note_to_midi, midi_to_note,
    normalize_pitch_class, NOTE_NAME_TO_PC,
    pitch_class_to_name, get_enharmonic
)
from .scales import (
    get_scale_intervals, get_scale_pitch_classes,
    get_scale_notes, scale_degree_to_midi, midi_to_scale_degree,
    is_in_scale, snap_to_scale, normalize_scale_name, SCALE_INTERVALS
)

__all__ = [
    "parse_note_string",
    "note_to_midi",
    "midi_to_note",
    "normalize_pitch_class",
    "NOTE_NAME_TO_PC",
    "get_scale_intervals",
    "get_scale_pitch_classes",
    "get_scale_notes",
    "scale_degree_to_midi",
    "midi_to_scale_degree",
    "is_in_scale",
    "snap_to_scale",
    "normalize_scale_name",
    "SCALE_INTERVALS"
]

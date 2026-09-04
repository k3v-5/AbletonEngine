# engine/music/theory/notes.py
from typing import Dict, Tuple, Optional

# Pitch class maps (0-11)
NOTE_NAME_TO_PC: Dict[str, int] = {
    "C": 0, "B#": 0,
    "C#": 1, "DB": 1,
    "D": 2,
    "D#": 3, "EB": 3,
    "E": 4, "FB": 4,
    "F": 5, "E#": 5,
    "F#": 6, "GB": 6,
    "G": 7,
    "G#": 8, "AB": 8,
    "A": 9,
    "A#": 10, "BB": 10,
    "B": 11, "CB": 11
}

PC_TO_SHARP_NAME: Dict[int, str] = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
}

PC_TO_FLAT_NAME: Dict[int, str] = {
    0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F",
    6: "Gb", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"
}

def parse_note_string(note_str: str) -> Tuple[int, int]:
    """Parse a note string like 'F3', 'C#4', 'Bb2' into (pitch_class, octave)"""
    note_str = note_str.strip()
    if not note_str:
        raise ValueError("Empty note string")

    octave = 4  # default octave
    # Find where letters end and digits begin
    idx = len(note_str) - 1
    while idx >= 0 and (note_str[idx].isdigit() or note_str[idx] == '-'):
        idx -= 1

    name_part = note_str[:idx + 1].upper()
    octave_part = note_str[idx + 1:]

    if octave_part:
        octave = int(octave_part)

    if name_part not in NOTE_NAME_TO_PC:
        raise ValueError(f"Unknown note name '{name_part}' in '{note_str}'")

    pc = NOTE_NAME_TO_PC[name_part]
    return pc, octave

def note_to_midi(note_str: str) -> int:
    """Convert a note string like 'C4', 'A0', 'F#2', 'Bb3' into a standard MIDI integer (0-127)"""
    pc, octave = parse_note_string(note_str)
    # MIDI formula: MIDI = (octave + 1) * 12 + pitch_class  (where C4 is MIDI 60)
    midi_val = (octave + 1) * 12 + pc
    return max(0, min(127, midi_val))

def midi_to_note(midi_pitch: int, use_flats: bool = False) -> str:
    """Convert a MIDI integer (0-127) to note name with octave, e.g. 60 -> 'C4', 42 -> 'F#2'"""
    midi_pitch = max(0, min(127, int(midi_pitch)))
    pc = midi_pitch % 12
    octave = (midi_pitch // 12) - 1
    name = PC_TO_FLAT_NAME[pc] if use_flats else PC_TO_SHARP_NAME[pc]
    return f"{name}{octave}"

def normalize_pitch_class(note_name: str) -> int:
    """Normalize any root string like 'F', 'Eb', 'c#' into pitch class 0-11"""
    clean = note_name.strip().upper()
    if clean in NOTE_NAME_TO_PC:
        return NOTE_NAME_TO_PC[clean]
    raise ValueError(f"Invalid root pitch name '{note_name}'")

def pitch_class_to_name(pc: int, use_flats: bool = False) -> str:
    """Convert a pitch class 0-11 to note name string"""
    pc_mod = pc % 12
    return PC_TO_FLAT_NAME[pc_mod] if use_flats else PC_TO_SHARP_NAME[pc_mod]

def get_enharmonic(note_name: str) -> str:
    """Return common enharmonic equivalent, e.g. C# -> Db, Eb -> D#"""
    pc = normalize_pitch_class(note_name)
    sharp = PC_TO_SHARP_NAME[pc]
    flat = PC_TO_FLAT_NAME[pc]
    return flat if note_name.upper() == sharp.upper() else sharp

# engine/sound_design/decent_sampler/sample_analyzer.py
"""
Sample Asset Metadata & Filename Analysis Engine.

Extracts musical metadata (root pitch, velocity layer, round robin index,
release trigger flag) from filenames and audio file properties.
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


NOTE_NAME_TO_SEMITONE: Dict[str, int] = {
    "C": 0, "C#": 1, "DB": 1,
    "D": 2, "D#": 3, "EB": 3,
    "E": 4,
    "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10,
    "B": 11,
}


def note_name_to_midi(note_str: str) -> Optional[int]:
    """
    Converts note strings like 'C4', 'A#3', 'Eb2', 'C-1' to MIDI note numbers (0-127).
    Standard: C4 = 60.
    """
    pattern = r"^([A-Ga-g][#bB]?)(-?\d+)$"
    match = re.match(pattern, note_str.strip())
    if not match:
        return None
    name, octave = match.groups()
    name = name.upper()
    octave = int(octave)

    semitone = NOTE_NAME_TO_SEMITONE.get(name)
    if semitone is None:
        return None

    # MIDI note formula where C4 = 60 -> (octave + 1) * 12 + semitone
    midi = (octave + 1) * 12 + semitone
    if 0 <= midi <= 127:
        return midi
    return None


def midi_to_note_name(midi_note: int) -> str:
    """Converts a MIDI note number (0-127) to note name (e.g., 60 -> 'C4')."""
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_note // 12) - 1
    semitone = midi_note % 12
    return f"{names[semitone]}{octave}"


@dataclass
class SampleAsset:
    """Metadata representing an audio sample asset on disk."""
    path: str
    root_note: int = 60
    lo_note: Optional[int] = None
    hi_note: Optional[int] = None
    velocity_layer: Optional[str] = None  # e.g. "soft", "loud", "v1", "v2"
    lo_vel: int = 0
    hi_vel: int = 127
    round_robin_index: int = 1
    is_release_sample: bool = False
    duration_sec: float = 0.0
    channels: int = 2
    sample_rate: int = 44100
    peak_db: float = 0.0

    @classmethod
    def from_filename(cls, file_path: str) -> "SampleAsset":
        """
        Infers musical metadata from filename patterns:
        - Root note: 'piano_C4_...', 'violin_A#3_...'
        - MIDI numbers: 'sample_60_...'
        - Velocity layers: '_v1_', '_v2_', '_soft_', '_loud_', '_mf_'
        - Round robin: '_rr1', '_rr2', '_RR3'
        - Release samples: '_rel', '_release', 'pedal_up'
        """
        p = Path(file_path)
        stem = p.stem.lower()

        root = 60
        # Try note name match like c4, f#3, bb2
        note_match = re.search(r"[_\-\s]([a-g][#b]?\d)[_\-\s\.]?", p.stem, re.IGNORECASE)
        if note_match:
            midi = note_name_to_midi(note_match.group(1))
            if midi is not None:
                root = midi
        else:
            # Try raw MIDI note number match like _060_, _60_
            num_match = re.search(r"[_\-\s](\d{2,3})[_\-\s\.]?", p.stem)
            if num_match:
                candidate = int(num_match.group(1))
                if 0 <= candidate <= 127:
                    root = candidate

        # Detect round-robin
        rr = 1
        rr_match = re.search(r"rr[-_]?(\d+)", stem)
        if rr_match:
            rr = int(rr_match.group(1))

        # Detect velocity layer
        vel_layer = None
        vel_match = re.search(r"v(\d+)", stem)
        if vel_match:
            vel_layer = f"v{vel_match.group(1)}"
        elif "soft" in stem or "pianissimo" in stem or "pp" in stem:
            vel_layer = "soft"
        elif "hard" in stem or "forte" in stem or "ff" in stem:
            vel_layer = "hard"
        elif "medium" in stem or "mf" in stem:
            vel_layer = "medium"

        # Detect release trigger
        is_release = any(k in stem for k in ("rel", "release", "pedal_up", "key_up"))

        # Normalize relative path to forward slashes
        clean_path = str(file_path).replace("\\", "/")

        return cls(
            path=clean_path,
            root_note=root,
            velocity_layer=vel_layer,
            round_robin_index=rr,
            is_release_sample=is_release,
        )

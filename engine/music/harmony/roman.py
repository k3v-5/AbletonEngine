# engine/music/harmony/roman.py
import re
from typing import List, Dict, Tuple, Optional
from ..models import Chord
from ..theory.scales import get_scale_pitch_classes, normalize_scale_name
from ..theory.notes import PC_TO_SHARP_NAME

# Roman numerals mapping to 0-based scale degree
ROMAN_TO_DEGREE: Dict[str, int] = {
    "i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6
}

def parse_roman_numeral(
    roman_str: str,
    key: Optional[str] = None,
    scale_name: str = "minor",
    duration: float = 4.0
):
    """
    Parse Roman numeral token like 'VI', 'i7', 'IIImaj7', 'ii°', 'V7'.
    If key is None, returns (scale_degree_0_based, quality, extensions).
    If key is provided, returns concrete Chord object.
    """
    token = roman_str.strip()
    match = re.match(r"^([b#]?)([ivIV]+)(°|dim|aug|maj|m|sus2|sus4)?([0-9]*)(.*)$", token)
    if not match:
        if key is not None:
            return Chord(root=key, quality="minor", duration=duration, roman_numeral=token)
        return 0, "minor", []

    accidental, roman_base, quality_mod, num_ext, extra = match.groups()
    is_lower = roman_base.islower()
    base_lower = roman_base.lower()

    if base_lower not in ROMAN_TO_DEGREE:
        if key is not None:
            return Chord(root=key, quality="minor", duration=duration, roman_numeral=token)
        return 0, "minor", []

    deg_0 = ROMAN_TO_DEGREE[base_lower]

    # Quality determination
    quality = "minor" if is_lower else "major"
    if quality_mod in ["°", "dim"]:
        quality = "diminished"
    elif quality_mod == "aug":
        quality = "augmented"
    elif quality_mod in ["sus2", "sus4"]:
        quality = quality_mod
    elif is_lower and quality_mod == "m":
        quality = "minor"
    elif not is_lower and quality_mod == "maj":
        quality = "major"

    # Extensions
    extensions = []
    if num_ext:
        extensions.append(num_ext)
    if "7" in extra:
        if "7" not in extensions: extensions.append("7")
    if "9" in extra:
        if "9" not in extensions: extensions.append("9")

    if key is not None:
        scale_pcs = get_scale_pitch_classes(key, scale_name)
        actual_deg = deg_0 % len(scale_pcs)
        root_pc = scale_pcs[actual_deg]
        root_name = PC_TO_SHARP_NAME[root_pc]
        return Chord(
            root=root_name,
            quality=quality,
            extensions=extensions,
            inversion=0,
            duration=duration,
            roman_numeral=token
        )

    return deg_0, quality, extensions

def roman_progression_to_chords(*args, **kwargs) -> List[Chord]:
    """
    Convert a list or string of Roman numeral tokens into concrete Chord objects.
    Flexible signatures supported:
    - roman_progression_to_chords(progression, key="F", scale="natural_minor", bars=4)
    - roman_progression_to_chords(key, scale_name, progression, chord_duration=4.0)
    """
    progression = None
    key = "C"
    scale_name = "natural_minor"
    chord_duration = None

    if len(args) == 1:
        progression = args[0]
    elif len(args) == 2:
        if isinstance(args[0], (list, tuple)) or ("-" in str(args[0]) or " " in str(args[0])):
            progression, key = args[0], args[1]
        else:
            key, scale_name = args[0], args[1]
    elif len(args) >= 3:
        if isinstance(args[2], (list, tuple)) or ("-" in str(args[2])):
            key, scale_name, progression = args[0], args[1], args[2]
            if len(args) > 3: chord_duration = float(args[3])
        else:
            progression, key, scale_name = args[0], args[1], args[2]
            if len(args) > 3: chord_duration = float(args[3])

    # Overlay kwargs
    if "progression" in kwargs: progression = kwargs["progression"]
    if "key" in kwargs: key = kwargs["key"]
    if "scale" in kwargs: scale_name = kwargs["scale"]
    if "scale_name" in kwargs: scale_name = kwargs["scale_name"]
    if "chord_duration" in kwargs: chord_duration = float(kwargs["chord_duration"])

    if progression is None:
        progression = "i - VI - III - VII"

    if isinstance(progression, str):
        tokens = parse_progression_string(progression)
    else:
        tokens = list(progression)

    bars = kwargs.get("bars")
    if bars is not None and chord_duration is None:
        chord_duration = (float(bars) * 4.0) / max(1, len(tokens))
    elif chord_duration is None:
        chord_duration = 4.0

    scale_pcs = get_scale_pitch_classes(key, scale_name)
    chords = []

    for token in tokens:
        deg_0, quality, exts = parse_roman_numeral(token)
        actual_deg = deg_0 % len(scale_pcs)
        root_pc = scale_pcs[actual_deg]
        root_name = PC_TO_SHARP_NAME[root_pc]

        chord = Chord(
            root=root_name,
            quality=quality,
            extensions=exts,
            inversion=0,
            duration=chord_duration,
            roman_numeral=token
        )
        chords.append(chord)

    return chords

def parse_progression_string(prog_str: str) -> List[str]:
    """Splits 'i - VI - III - VII' or 'i, VI, III, VII' into clean token list"""
    delimiters = r"[,\-\s]+"
    tokens = [t.strip() for t in re.split(delimiters, prog_str) if t.strip()]
    return tokens

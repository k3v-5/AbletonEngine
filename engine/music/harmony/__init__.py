# engine/music/harmony/__init__.py
from .chords import CHORD_INTERVALS, get_chord_intervals, get_chord_pitches
from .roman import parse_roman_numeral, roman_progression_to_chords, parse_progression_string
from .generator import generate_harmonic_structure
from .reharmonizer import ModalReharmonizer, ReharmStyle
from .functional_harmony_engine import FunctionalHarmonyEngine
from .vertical_harmonic_validator import VerticalHarmonicValidator, VerticalHarmonicReport, HarmonicClashEvent, HarmonicTensionEvent

__all__ = [
    "CHORD_INTERVALS",
    "get_chord_intervals",
    "get_chord_pitches",
    "parse_roman_numeral",
    "roman_progression_to_chords",
    "parse_progression_string",
    "generate_harmonic_structure",
    "ModalReharmonizer",
    "ReharmStyle",
    "FunctionalHarmonyEngine",
    "VerticalHarmonicValidator",
    "VerticalHarmonicReport",
    "HarmonicClashEvent",
    "HarmonicTensionEvent"
]


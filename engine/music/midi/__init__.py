# engine/music/midi/__init__.py
from .compiler import compile_notes_to_ableton_format, compute_part_fingerprint, compare_fingerprints

__all__ = ["compile_notes_to_ableton_format", "compute_part_fingerprint", "compare_fingerprints"]

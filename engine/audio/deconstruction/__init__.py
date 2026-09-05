# engine/audio/deconstruction/__init__.py
"""
Audio Reference Deconstruction & Stem Transcription Module.
"""

from engine.audio.deconstruction.models import (
    StemCategory,
    DeconstructedStem,
    TranscribedNoteEvent,
    AudioTranscriptionResult
)
from engine.audio.deconstruction.separator import AudioStemSeparator
from engine.audio.deconstruction.transcriber import ReferenceTranscriber
from engine.audio.deconstruction.reconstructor import ReferenceReconstructor

__all__ = [
    "StemCategory",
    "DeconstructedStem",
    "TranscribedNoteEvent",
    "AudioTranscriptionResult",
    "AudioStemSeparator",
    "ReferenceTranscriber",
    "ReferenceReconstructor"
]

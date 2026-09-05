# engine/audio/deconstruction/models.py
"""
Data models for audio reference deconstruction, stem separation, and MIDI transcription.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class StemCategory(str, Enum):
    DRUMS = "drums"
    BASS = "bass"
    VOCALS = "vocals"
    OTHER = "other"

@dataclass
class DeconstructedStem:
    category: StemCategory
    audio_path: str
    sample_rate: int
    duration_seconds: float
    rms_db: float
    peak_db: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TranscribedNoteEvent:
    pitch: int                   # MIDI pitch (0 - 127)
    start_beat: float            # Start time in beats (1.0 = beat 1, or relative to clip start)
    duration_beats: float        # Duration in beats
    velocity: int = 100          # Velocity (1 - 127)
    confidence: float = 1.0      # Confidence score (0.0 - 1.0)
    articulation: str = "normal" # "normal", "legato", "staccato", "transient"

@dataclass
class AudioTranscriptionResult:
    source_path: str
    detected_tempo: float
    detected_key: str
    duration_seconds: float
    sample_rate: int
    stems: Dict[str, DeconstructedStem] = field(default_factory=dict)
    drum_notes: List[TranscribedNoteEvent] = field(default_factory=list)
    bass_notes: List[TranscribedNoteEvent] = field(default_factory=list)
    chord_notes: List[TranscribedNoteEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

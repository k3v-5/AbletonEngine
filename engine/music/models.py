# engine/music/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ..models.ids import generate_id

@dataclass
class NoteEvent:
    """Internal high-fidelity representation of a musical note event"""
    pitch: int                          # MIDI note number (0 - 127)
    pitch_class: int                    # Pitch class 0-11 (C=0, C#=1, etc.)
    octave: int                         # Octave index (e.g. 1, 2, 3, 4)
    start: float                        # Start time in musical beats (0.0 = bar 1 beat 1)
    duration: float                     # Duration in musical beats
    velocity: int = 90                  # MIDI velocity (1 - 127)
    channel: int = 0                    # MIDI channel (0 - 15)
    probability: float = 1.0            # Trigger probability (0.0 to 1.0)
    accent: float = 0.0                 # Accent strength (-1.0 to 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pitch": self.pitch,
            "pitch_class": self.pitch_class,
            "octave": self.octave,
            "start": round(self.start, 4),
            "duration": round(self.duration, 4),
            "velocity": self.velocity,
            "channel": self.channel,
            "probability": self.probability,
            "accent": round(self.accent, 2)
        }

    @classmethod
    def from_pitch_and_time(cls, pitch: int, start: float, duration: float, velocity: int = 90, accent: float = 0.0):
        pitch_cl = pitch % 12
        octv = (pitch // 12) - 1
        return cls(
            pitch=pitch,
            pitch_class=pitch_cl,
            octave=octv,
            start=start,
            duration=duration,
            velocity=velocity,
            accent=accent
        )

@dataclass
class Chord:
    """Harmonic chord representation with root, quality, extensions, and bass inversion"""
    root: str                           # Root pitch name, e.g. "F", "C#", "Bb"
    quality: str                        # "major", "minor", "diminished", "augmented", "sus4", etc.
    extensions: List[str] = field(default_factory=list)  # ["7", "9", "11"]
    inversion: int = 0                  # 0 = root position, 1 = 1st, 2 = 2nd, 3 = 3rd
    bass_note: Optional[str] = None     # Override bass for slash chords, e.g. "Eb" for Fm/Eb
    duration: float = 4.0               # Duration in musical beats
    roman_numeral: str = ""             # e.g. "i", "VI", "III7", "V"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root": self.root,
            "quality": self.quality,
            "extensions": self.extensions,
            "inversion": self.inversion,
            "bass_note": self.bass_note or self.root,
            "duration": self.duration,
            "roman_numeral": self.roman_numeral
        }

@dataclass
class RhythmPattern:
    """Rhythmic pattern grid representation"""
    name: str
    subdivision: str = "1/16"          # "1/4", "1/8", "1/16", "1/32", "1/8T", "1/16T"
    steps: List[float] = field(default_factory=list)      # Step beat offsets
    accent_map: Dict[int, float] = field(default_factory=dict) # step_idx -> accent
    density: float = 0.5
    swing: float = 0.0

@dataclass
class Motif:
    """Structural invariant melodic motif"""
    id: str
    name: str
    length_beats: float
    intervals: List[int] = field(default_factory=list)    # Semitone intervals relative to root
    rhythm: List[float] = field(default_factory=list)      # Durations of each step in beats
    offsets: List[float] = field(default_factory=list)     # Beat offset of each note within motif
    accents: List[float] = field(default_factory=list)     # Accent/intensity per note
    role: Optional[str] = None
    section: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "length_beats": self.length_beats,
            "intervals": self.intervals,
            "rhythm": self.rhythm,
            "offsets": self.offsets,
            "accents": self.accents,
            "role": self.role,
            "section": self.section
        }

@dataclass
class PartFingerprint:
    """Musical statistical fingerprint for similarity comparison"""
    note_count: int
    pitch_class_histogram: Dict[int, int]
    rhythm_histogram: Dict[str, int]
    density: float
    range_semitones: int
    min_pitch: int
    max_pitch: int

# engine/music/expression/mpe.py
"""
MIDI Polyphonic Expression (MPE) & Continuous Pitch Bend Engine:
Generates vocal scoops, organic vibrato curves, and aftertouch dynamics for expressive lead instruments.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from engine.music.models import NoteEvent


@dataclass
class PitchBendPoint:
    beat: float
    bend_semitones: float  # e.g. -0.5 to +0.5 semitones
    normalized_val: float  # -1.0 to +1.0


@dataclass
class ExpressiveNoteModifier:
    pitch: int
    start_time: float
    duration: float
    velocity: int
    probability: float = 1.0
    velocity_deviation: int = 5
    release_velocity: int = 64
    pitch_bend_points: List[PitchBendPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pitch": self.pitch,
            "start_time": round(self.start_time, 5),
            "duration": round(self.duration, 5),
            "velocity": self.velocity,
            "probability": round(self.probability, 2),
            "velocity_deviation": self.velocity_deviation,
            "release_velocity": self.release_velocity,
        }


class MPEExpressionEngine:
    """Calculates attack scoops, delayed vibrato oscillations, and MPE note specifications."""

    @classmethod
    def generate_pitch_bend_envelope_for_note(
        cls,
        start_beat: float,
        duration: float,
        tempo: float = 142.0,
        enable_scoop: bool = True,
        enable_vibrato: bool = True,
        vibrato_rate_hz: float = 5.2,
        vibrato_depth_semitones: float = 0.35,
        scoop_depth_semitones: float = 0.45
    ) -> List[PitchBendPoint]:
        """
        Generates dense pitch bend curve points across a single sustained note:
        - Scoop in the first 0.25 beats (gliding from -0.45 semitones to 0.0)
        - Sinusoidal vibrato starting after 1.0 beat of sustain until note end
        """
        points: List[PitchBendPoint] = []
        beats_per_second = tempo / 60.0
        seconds_per_beat = 60.0 / tempo

        # 1. Attack Scoop (first 0.25 beats)
        if enable_scoop and duration >= 0.75:
            scoop_beats = min(0.30, duration * 0.3)
            steps = 6
            for s in range(steps + 1):
                t = s / steps
                # Exponential curve from -depth to 0
                bend = -scoop_depth_semitones * ((1.0 - t) ** 2)
                b_pos = start_beat + (t * scoop_beats)
                points.append(PitchBendPoint(
                    beat=round(b_pos, 5),
                    bend_semitones=round(bend, 4),
                    normalized_val=round(bend / 2.0, 4)  # standard +/- 2 semitone range
                ))

        # 2. Delayed Vibrato (after 1.0 beat if sustained)
        vibrato_start = start_beat + 1.0
        if enable_vibrato and duration >= 1.5 and vibrato_start < (start_beat + duration - 0.2):
            vibrato_duration = (start_beat + duration - 0.1) - vibrato_start
            vibrato_samples = int(vibrato_duration * 16)  # 16 points per beat
            for s in range(vibrato_samples + 1):
                b_offset = s * (vibrato_duration / max(1, vibrato_samples))
                curr_beat = vibrato_start + b_offset
                curr_time_sec = b_offset * seconds_per_beat

                # Envelope for vibrato: swells from 0 to full depth
                swell = min(1.0, b_offset / 0.75)
                # Sine wave oscillation
                osc = math.sin(2.0 * math.pi * vibrato_rate_hz * curr_time_sec)
                bend = osc * vibrato_depth_semitones * swell

                points.append(PitchBendPoint(
                    beat=round(curr_beat, 5),
                    bend_semitones=round(bend, 4),
                    normalized_val=round(bend / 2.0, 4)
                ))

        # Ensure return to center pitch at end of note
        end_beat = start_beat + duration
        points.append(PitchBendPoint(beat=round(end_beat, 5), bend_semitones=0.0, normalized_val=0.0))

        return points

    @classmethod
    def add_expression_to_melody(
        cls,
        notes: List[NoteEvent],
        tempo: float = 142.0,
        scoop_chance: float = 0.60,
        vibrato_chance: float = 0.80
    ) -> Tuple[List[ExpressiveNoteModifier], List[PitchBendPoint]]:
        """
        Processes melodic line notes and attaches MPE specifications and global pitch bend timeline points.
        """
        expressive_notes: List[ExpressiveNoteModifier] = []
        global_bends: List[PitchBendPoint] = []

        for i, n in enumerate(notes):
            # Phrase lead gets scoops; long notes get vibrato
            is_phrase_lead = (i == 0) or (notes[i].start - notes[i - 1].start > 1.5)
            has_scoop = is_phrase_lead or (n.duration >= 1.0 and (i % 2 == 0))
            has_vibrato = (n.duration >= 1.5)

            bends = cls.generate_pitch_bend_envelope_for_note(
                start_beat=n.start,
                duration=n.duration,
                tempo=tempo,
                enable_scoop=has_scoop,
                enable_vibrato=has_vibrato
            )
            global_bends.extend(bends)

            expressive_notes.append(ExpressiveNoteModifier(
                pitch=n.pitch,
                start_time=n.start,
                duration=n.duration,
                velocity=n.velocity,
                probability=1.0,
                velocity_deviation=6,
                release_velocity=int(n.velocity * 0.8),
                pitch_bend_points=bends
            ))

        return expressive_notes, sorted(global_bends, key=lambda b: b.beat)

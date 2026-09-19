# engine/music/bass/intelligent_808_slide.py
"""
Intelligent 808 Slide & Pitch Bend Engine:
Punto 27: Generates authentic modern 808 legato pitch slides and portamento overlaps.
Enables explosive bass turns (octave leaps, leading tones, 5th slides) by orchestrating
overlapping MIDI notes and pitch bend automation envelopes.
"""

from typing import Dict, Any, List, Optional, Tuple
from engine.music.models import NoteEvent


class Intelligent808SlideEngine:
    """Creates legato slide notes and pitch bend envelopes for 808 sub-bass."""

    @classmethod
    def apply_808_slides(
        cls,
        base_bass_notes: List[NoteEvent],
        slide_probability: float = 0.50,
        slide_interval_semitones: int = 12,
        tempo: float = 120.0
    ) -> List[NoteEvent]:
        """
        Punto 27: Scans bass notes and injects overlapping legato slide notes
        at bar turnarounds (e.g. at the end of 2-bar or 4-bar cycles).
        """
        if not base_bass_notes:
            return []

        modified_notes: List[NoteEvent] = []
        # Sort notes by start time
        sorted_notes = sorted(base_bass_notes, key=lambda n: n.start)

        for i, note in enumerate(sorted_notes):
            # Check if this note is at a turnaround position (e.g. beat 6.0-7.5 of an 8-beat cycle)
            bar_phase = note.start % 8.0
            is_turnaround = 5.5 <= bar_phase <= 7.5
            is_long_note = note.duration >= 1.5

            if is_turnaround and is_long_note and (i % 2 == 1 or i == len(sorted_notes) - 1):
                # Split note: Root sustains, then slides up in the last 0.5 - 0.75 beats
                slide_duration = min(0.75, note.duration * 0.40)
                root_duration = note.duration - slide_duration + 0.10  # 0.10 beat legato overlap!

                # 1. Sustained root note
                modified_notes.append(NoteEvent(
                    pitch=note.pitch,
                    start=note.start,
                    duration=round(root_duration, 3),
                    velocity=note.velocity
                ))

                # 2. Legato slide note (overlapping root note to trigger VST portamento/glide)
                slide_start = note.start + note.duration - slide_duration
                slide_pitch = note.pitch + slide_interval_semitones
                # Keep slide in reasonable bass range (<= 50)
                if slide_pitch > 50:
                    slide_pitch = note.pitch + 7  # 5th slide fallback

                modified_notes.append(NoteEvent(
                    pitch=slide_pitch,
                    start=round(slide_start, 3),
                    duration=round(slide_duration, 3),
                    velocity=min(127, note.velocity + 5)  # Slightly higher velocity for slide accent
                ))
            else:
                modified_notes.append(note)

        return modified_notes

    @classmethod
    def generate_pitch_bend_slide_envelope(
        cls,
        start_beat: float,
        duration_beats: float = 0.5,
        target_semitones: int = 12,
        bend_range_semitones: int = 24,
        steps: int = 16
    ) -> List[Dict[str, float]]:
        """
        Generates physical pitch bend envelope (values -8192 to +8191) for slide automation.
        """
        points = []
        max_val = 8191.0
        target_normalized_bend = (target_semitones / float(bend_range_semitones)) * max_val

        # Anchor at 0 before slide
        points.append({"time": round(max(0.0, start_beat - 0.02), 3), "value": 0.0})

        for i in range(steps + 1):
            t = i / float(steps)
            b_time = start_beat + t * duration_beats
            # Exponential glide curve
            curve_factor = t ** 1.6
            val = round(target_normalized_bend * curve_factor, 1)
            points.append({"time": round(b_time, 3), "value": val})

        # Instant reset at end of slide
        points.append({"time": round(start_beat + duration_beats + 0.01, 3), "value": 0.0})

        return points

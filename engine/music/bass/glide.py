# engine/music/bass/glide.py
"""
Bass Glide & 808 Pitch-Bend Engine:
Generates authentic drill/trap 808 slides, octave glides, pitch drop-offs,
and legato overlap articulations for monophonic sub-bass synths and samplers.
"""

from enum import Enum
import random
import math
from typing import List, Dict, Any, Optional, Union, Tuple
from ..models import NoteEvent


class SlideMode(str, Enum):
    DRILL_OCTAVE_GLIDE = "drill_octave_glide"      # +12 semitones fast slide at note tail
    PITCH_DROP = "pitch_drop"                      # -12 to -24 semitones downward glide
    CHORD_FIFTH_GLIDE = "chord_fifth_glide"        # +7 semitones harmonic glide
    VIBRATO_TAIL = "vibrato_tail"                  # subtle pitch oscillation on long notes


class BassGlideEngine:
    """Computes pitch bend curves and legato slide notes for 808 and sub-bass tracks."""

    @classmethod
    def generate_808_slides(
        cls,
        notes: List[NoteEvent],
        slide_mode: Union[SlideMode, str] = SlideMode.DRILL_OCTAVE_GLIDE,
        bend_range_semitones: int = 12,
        glide_probability: float = 0.5,
        turnaround_only: bool = True,
        seed: Optional[int] = 42
    ) -> Dict[str, Any]:
        """
        Takes bass notes and generates:
        1. Injected legato notes overlapping the parent note tail (for portamento synths).
        2. Timestamped pitch bend breakpoint points in range [-8192, 8191].
        """
        if not notes:
            return {
                "legato_notes": [],
                "pitch_bend_points": [],
                "slides_applied": 0,
                "slide_details": []
            }

        mode = SlideMode(slide_mode) if isinstance(slide_mode, str) else slide_mode
        rng = random.Random(seed)

        # Sort notes by start time
        sorted_notes = sorted(notes, key=lambda n: n.start)
        max_beat = max((n.start + n.duration for n in sorted_notes), default=16.0)

        legato_notes: List[NoteEvent] = []
        pitch_bend_points: List[Dict[str, float]] = []
        slide_details: List[Dict[str, Any]] = []

        # Pitch bend center is 0.0 (in range -8192 to +8191)
        # We ensure baseline 0 at start
        pitch_bend_points.append({"time": 0.0, "value": 0.0})

        for idx, note in enumerate(sorted_notes):
            # Base copy
            legato_notes.append(NoteEvent(**note.__dict__))

            # Eligibility criteria: note duration >= 0.75 beats
            if note.duration < 0.75:
                continue

            # Is turnaround note (in last 4 beats of section, e.g. bar 4 / beat 12 to 16)
            is_turnaround = (note.start % 16.0) >= 12.0

            should_slide = False
            if turnaround_only:
                if is_turnaround and rng.random() < max(0.6, glide_probability):
                    should_slide = True
            else:
                if rng.random() < glide_probability:
                    should_slide = True

            if not should_slide:
                continue

            # Calculate slide parameters
            # Slide occurs in the final 0.25 to 0.5 beats of the note
            slide_duration = min(0.5, max(0.2, note.duration * 0.35))
            slide_start = round(note.start + note.duration - slide_duration, 4)

            if mode == SlideMode.DRILL_OCTAVE_GLIDE:
                target_semitones = 12
                # Target pitch
                target_pitch = min(127, note.pitch + 12)
            elif mode == SlideMode.CHORD_FIFTH_GLIDE:
                target_semitones = 7
                target_pitch = min(127, note.pitch + 7)
            elif mode == SlideMode.PITCH_DROP:
                target_semitones = -12
                target_pitch = max(0, note.pitch - 12)
            else: # VIBRATO_TAIL
                target_semitones = 0
                target_pitch = note.pitch

            # 1. Legato Overlapping Note:
            # Overlaps the tail of parent note by 0.05 beats to trigger synth portamento/glide
            if mode != SlideMode.VIBRATO_TAIL:
                overlap = 0.04
                legato_slide_event = NoteEvent(
                    pitch=target_pitch,
                    start=round(slide_start - overlap, 4),
                    duration=round(slide_duration + overlap, 4),
                    velocity=min(127, note.velocity + 10),
                    accent=True
                )
                legato_notes.append(legato_slide_event)

            # 2. Pitch Bend Curve Breakpoints:
            # Full scale bend: 8191 corresponds to bend_range_semitones
            bend_ratio = target_semitones / max(1, bend_range_semitones)
            peak_bend_val = round(max(-8192.0, min(8191.0, bend_ratio * 8191.0)), 2)

            if mode == SlideMode.VIBRATO_TAIL:
                # Vibrato oscillation
                steps = 6
                vib_amplitude = 8191.0 * (0.3 / max(1, bend_range_semitones))
                for s in range(steps):
                    t_osc = slide_start + (s / steps) * slide_duration
                    val_osc = math.sin(s * math.pi) * vib_amplitude
                    pitch_bend_points.append({"time": round(t_osc, 4), "value": round(val_osc, 2)})
                pitch_bend_points.append({"time": round(note.start + note.duration, 4), "value": 0.0})
            else:
                # Flat before slide
                pitch_bend_points.append({"time": max(0.0, round(slide_start - 0.01, 4)), "value": 0.0})
                # Ramp to peak
                t_peak = round(slide_start + slide_duration * 0.7, 4)
                pitch_bend_points.append({"time": t_peak, "value": peak_bend_val})
                # Hold at peak until end of note
                pitch_bend_points.append({"time": round(note.start + note.duration, 4), "value": peak_bend_val})
                # Reset to zero immediately upon note release
                pitch_bend_points.append({"time": round(note.start + note.duration + 0.01, 4), "value": 0.0})

            slide_details.append({
                "parent_note_start": note.start,
                "parent_pitch": note.pitch,
                "slide_start": slide_start,
                "slide_duration": slide_duration,
                "target_pitch": target_pitch,
                "semitone_shift": target_semitones,
                "mode": mode.value
            })

        # Ensure trailing zero point
        if pitch_bend_points[-1]["time"] < max_beat:
            pitch_bend_points.append({"time": round(max_beat, 4), "value": 0.0})

        # Sort and deduplicate
        sorted_legato = sorted(legato_notes, key=lambda n: n.start)
        sorted_bend = sorted(pitch_bend_points, key=lambda p: p["time"])

        return {
            "legato_notes": sorted_legato,
            "pitch_bend_points": sorted_bend,
            "slides_applied": len(slide_details),
            "slide_details": slide_details
        }

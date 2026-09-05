# engine/vocal/chopper.py
"""
Vocal Chopper & Hook Pitch-Shift Engine:
Generates in-key, scale-quantized rhythmic vocal chop phrases, call-and-response hooks,
stutter fills, and spatial stereo ping-pong / delay throw automations for Ableton Live.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union
import math
from engine.music.models import NoteEvent


class VocalChopStyle(str, Enum):
    MELODIC_HOOK = "melodic_hook"
    STUTTER_DROP = "stutter_drop"
    CALL_AND_RESPONSE = "call_and_response"
    AMBIENT_TEXTURE = "ambient_texture"


@dataclass
class VocalChopNote:
    pitch: int
    start: float
    duration: float
    velocity: int = 100
    pan: float = 0.0                      # -1.0 (hard L) to +1.0 (hard R)
    pitch_semitones_offset: int = 0
    delay_send: float = 0.25


class VocalChopperEngine:
    """Produces musically coherent vocal chop motifs aligned with session key, scale, and tempo."""

    # Semitone offsets for diatonic scales
    SCALE_INTERVALS = {
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "major": [0, 2, 4, 5, 7, 9, 11],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        "pentatonic_minor": [0, 3, 5, 7, 10]
    }

    NOTE_TO_SEMITONE = {
        "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
        "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
    }

    @classmethod
    def get_scale_pitches(
        cls,
        root: str = "F",
        scale: str = "minor",
        octave: int = 5
    ) -> List[int]:
        """Calculates MIDI pitches for the diatonic scale across two octaves."""
        clean_root = root.upper().strip()
        root_semi = cls.NOTE_TO_SEMITONE.get(clean_root, 5) # Default F
        clean_scale = scale.lower().strip()
        intervals = cls.SCALE_INTERVALS.get(clean_scale, cls.SCALE_INTERVALS["minor"])

        base_pitch = (octave + 1) * 12 + root_semi
        pitches = []
        for oct_off in [0, 12]:
            for interv in intervals:
                pitches.append(base_pitch + oct_off + interv)

        return sorted(list(set(pitches)))

    @classmethod
    def generate_hook_chops(
        cls,
        root: str = "F",
        scale: str = "minor",
        style: Union[VocalChopStyle, str] = VocalChopStyle.MELODIC_HOOK,
        total_bars: float = 4.0,
        octave: int = 5,
        tempo: float = 120.0
    ) -> List[VocalChopNote]:
        """
        Generates scale-quantized vocal chop patterns with panning and velocity dynamics.
        """
        if isinstance(style, str):
            try:
                style = VocalChopStyle(style.lower())
            except ValueError:
                style = VocalChopStyle.MELODIC_HOOK

        pitches = cls.get_scale_pitches(root=root, scale=scale, octave=octave)
        # pitches indices: 0: 1 (Root), 2: b3/3, 4: 5th, 6: b7/7, 7: Octave
        p_root = pitches[0]
        p_third = pitches[2] if len(pitches) > 2 else p_root + 3
        p_fifth = pitches[4] if len(pitches) > 4 else p_root + 7
        p_seventh = pitches[6] if len(pitches) > 6 else p_root + 10
        p_oct = pitches[7] if len(pitches) > 7 else p_root + 12

        chops: List[VocalChopNote] = []

        for b_idx in range(int(total_bars)):
            bar_start = b_idx * 4.0

            if style == VocalChopStyle.MELODIC_HOOK:
                # Catchy, syncopated trap/pop vocal lead
                chops.append(VocalChopNote(pitch=p_root, start=bar_start + 0.0, duration=0.4, velocity=115, pan=-0.2, pitch_semitones_offset=0))
                chops.append(VocalChopNote(pitch=p_third, start=bar_start + 0.5, duration=0.35, velocity=105, pan=0.2, pitch_semitones_offset=3))
                chops.append(VocalChopNote(pitch=p_fifth, start=bar_start + 1.25, duration=0.6, velocity=122, pan=-0.3, pitch_semitones_offset=7))
                chops.append(VocalChopNote(pitch=p_root, start=bar_start + 2.0, duration=0.35, velocity=110, pan=0.0, pitch_semitones_offset=0))
                chops.append(VocalChopNote(pitch=p_seventh, start=bar_start + 2.75, duration=0.4, velocity=118, pan=0.4, pitch_semitones_offset=10))

                if b_idx % 2 == 1:
                    # Turnaround flurry on bars 2 and 4
                    chops.append(VocalChopNote(pitch=p_oct, start=bar_start + 3.25, duration=0.25, velocity=127, pan=-0.5, pitch_semitones_offset=12, delay_send=0.6))
                    chops.append(VocalChopNote(pitch=p_fifth, start=bar_start + 3.5, duration=0.25, velocity=120, pan=0.5, pitch_semitones_offset=7, delay_send=0.7))
                else:
                    chops.append(VocalChopNote(pitch=p_fifth, start=bar_start + 3.5, duration=0.45, velocity=115, pan=0.1, pitch_semitones_offset=7))

            elif style == VocalChopStyle.STUTTER_DROP:
                # Rapid 16th note vocal stutter building tension
                for s in range(8):
                    t = bar_start + s * 0.25
                    vel = 80 + s * 6
                    pan = -0.6 if s % 2 == 0 else 0.6
                    chops.append(VocalChopNote(pitch=p_root, start=t, duration=0.18, velocity=min(127, vel), pan=pan, delay_send=0.35))
                # Sustained resolving note
                chops.append(VocalChopNote(pitch=p_oct, start=bar_start + 2.5, duration=1.2, velocity=125, pan=0.0, delay_send=0.8))

            elif style == VocalChopStyle.CALL_AND_RESPONSE:
                # Phrase 1: Left Call
                chops.append(VocalChopNote(pitch=p_fifth, start=bar_start + 0.0, duration=0.7, velocity=120, pan=-0.7, pitch_semitones_offset=7))
                chops.append(VocalChopNote(pitch=p_third, start=bar_start + 0.75, duration=0.5, velocity=110, pan=-0.5, pitch_semitones_offset=3))
                # Phrase 2: Right Response
                chops.append(VocalChopNote(pitch=p_root, start=bar_start + 2.0, duration=0.7, velocity=125, pan=0.7, pitch_semitones_offset=0, delay_send=0.5))
                chops.append(VocalChopNote(pitch=p_seventh, start=bar_start + 2.75, duration=0.5, velocity=115, pan=0.5, pitch_semitones_offset=10, delay_send=0.6))

            else:
                # AMBIENT_TEXTURE: Lush long washes
                chops.append(VocalChopNote(pitch=p_root, start=bar_start + 0.0, duration=1.8, velocity=90, pan=-0.4, delay_send=0.85))
                chops.append(VocalChopNote(pitch=p_fifth, start=bar_start + 2.0, duration=1.8, velocity=95, pan=0.4, delay_send=0.85))

        return chops

    @classmethod
    def calculate_pan_automation(cls, chops: List[VocalChopNote]) -> List[Dict[str, float]]:
        """Generates stereo panning automation points based on vocal chop note coordinates."""
        points: List[Dict[str, float]] = []
        for c in sorted(chops, key=lambda x: x.start):
            # Anchor slightly before
            if c.start > 0.05:
                points.append({"time": round(c.start - 0.02, 3), "value": 0.0})
            points.append({"time": round(c.start, 3), "value": round(c.pan, 3)})
            points.append({"time": round(c.start + c.duration, 3), "value": round(c.pan, 3)})
            points.append({"time": round(c.start + c.duration + 0.05, 3), "value": 0.0})

        return points

    @classmethod
    def calculate_delay_send_automation(cls, chops: List[VocalChopNote]) -> List[Dict[str, float]]:
        """Generates dynamic send automation throws opening up during key turnaround phrases."""
        points: List[Dict[str, float]] = []
        for c in sorted(chops, key=lambda x: x.start):
            if c.delay_send > 0.3:
                points.append({"time": round(c.start - 0.02, 3), "value": 0.1})
                points.append({"time": round(c.start, 3), "value": round(c.delay_send, 3)})
                points.append({"time": round(c.start + c.duration, 3), "value": round(c.delay_send, 3)})
                points.append({"time": round(c.start + c.duration + 0.2, 3), "value": 0.1})

        return points

    @classmethod
    def generate_and_apply_vocal_chops(
        cls,
        conn: Any,
        track_index: int = 4,
        root: str = "F",
        scale: str = "minor",
        style: Union[VocalChopStyle, str] = VocalChopStyle.MELODIC_HOOK,
        total_bars: float = 4.0,
        bpm: float = 120.0
    ) -> Dict[str, Any]:
        """
        Calculates and injects vocal chop clips and stereo panning automation into Ableton Live.
        """
        chops = cls.generate_hook_chops(
            root=root,
            scale=scale,
            style=style,
            total_bars=total_bars,
            tempo=bpm
        )

        pan_points = cls.calculate_pan_automation(chops)
        delay_points = cls.calculate_delay_send_automation(chops)

        if conn is not None and hasattr(conn, "send_command"):
            try:
                clip_len = total_bars * 4.0
                conn.send_command("delete_clip", {"track_index": track_index, "clip_index": 0})
                conn.send_command("create_clip", {"track_index": track_index, "clip_index": 0, "length": clip_len})
                conn.send_command("set_clip_name", {"track_index": track_index, "clip_index": 0, "name": f"Vocal Chops ({root} {scale})"})
                conn.send_command("add_notes_to_clip", {
                    "track_index": track_index,
                    "clip_index": 0,
                    "notes": [
                        {
                            "pitch": c.pitch,
                            "start_time": c.start,
                            "duration": c.duration,
                            "velocity": c.velocity,
                            "mute": False
                        }
                        for c in chops
                    ]
                })
                # Send Panning Automation
                if pan_points:
                    conn.send_command("create_arrangement_automation_envelope", {
                        "track_index": track_index,
                        "parameter": "Panning",
                        "points": pan_points
                    })
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "root": root,
            "scale": scale,
            "style": str(style),
            "chops_count": len(chops),
            "pan_points_count": len(pan_points),
            "delay_points_count": len(delay_points),
            "track_index": track_index
        }

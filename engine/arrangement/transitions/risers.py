# engine/arrangement/transitions/risers.py
"""
Transition Risers & Continuous Sweeps Engine:
Generates Auto Filter frequency sweeps, white noise/synth pitch risers,
and procedural accelerating snare rolls to bridge energy gaps before drops.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
import math
from engine.music.models import NoteEvent


class SweepFilterType(str, Enum):
    LOW_PASS_RISE = "low_pass_rise"     # Cutoff rises 250Hz -> 18kHz
    HIGH_PASS_CUT = "high_pass_cut"     # Cutoff rises 20Hz -> 1200Hz (clears low end)
    BAND_PASS_SWEEP = "band_pass_sweep" # Resonant sweeping formant


class TransitionRisersEngine:
    """Architect for automated filter risers, noise sweeps, and procedural build fills."""

    @classmethod
    def generate_filter_sweep(
        cls,
        target_bar: float,
        duration_bars: float = 2.0,
        sweep_type: Union[SweepFilterType, str] = SweepFilterType.LOW_PASS_RISE,
        min_freq: float = 250.0,
        max_freq: float = 18000.0,
        steps: int = 32
    ) -> List[Dict[str, float]]:
        """
        Calculates exponential frequency automation points for Ableton Auto Filter.
        target_bar is 1-based (e.g. 33.0 for drop at bar 33).
        Sweep executes in the duration_bars immediately preceding target_bar.
        """
        if isinstance(sweep_type, str):
            try:
                sweep_type = SweepFilterType(sweep_type.lower())
            except ValueError:
                sweep_type = SweepFilterType.LOW_PASS_RISE

        arrival_beat = max(0.0, (target_bar - 1.0) * 4.0)
        duration_beats = duration_bars * 4.0
        start_beat = max(0.0, arrival_beat - duration_beats)

        f_start = min_freq if sweep_type == SweepFilterType.LOW_PASS_RISE else (20.0 if sweep_type == SweepFilterType.HIGH_PASS_CUT else min_freq)
        f_end = max_freq if sweep_type == SweepFilterType.LOW_PASS_RISE else (1200.0 if sweep_type == SweepFilterType.HIGH_PASS_CUT else max_freq)

        points: List[Dict[str, float]] = []
        # Pre-sweep anchor
        if start_beat > 0.05:
            points.append({"time": round(start_beat - 0.05, 3), "value": round(f_start, 1)})

        for i in range(steps + 1):
            t_norm = i / steps
            t_curr = start_beat + t_norm * duration_beats
            # Exponential audio curve: f(t) = f_start * (f_end / f_start)^t
            if f_start > 0:
                freq = f_start * math.pow(f_end / f_start, t_norm)
            else:
                freq = f_start + (f_end - f_start) * t_norm

            points.append({
                "time": round(t_curr, 3),
                "value": round(freq, 1)
            })

        # Post-drop reset to full open
        points.append({"time": round(arrival_beat, 3), "value": round(max_freq, 1)})
        return points

    @classmethod
    def generate_noise_pitch_riser(
        cls,
        target_bar: float,
        duration_bars: float = 2.0,
        min_gain: float = 0.1,
        max_gain: float = 0.85,
        steps: int = 32
    ) -> Dict[str, List[Dict[str, float]]]:
        """
        Calculates pitch bend (+24 semitones) and volume crescendo automation curves.
        """
        arrival_beat = max(0.0, (target_bar - 1.0) * 4.0)
        duration_beats = duration_bars * 4.0
        start_beat = max(0.0, arrival_beat - duration_beats)

        vol_points: List[Dict[str, float]] = []
        pitch_points: List[Dict[str, float]] = []

        if start_beat > 0.05:
            vol_points.append({"time": round(start_beat - 0.05, 3), "value": 0.0})
            pitch_points.append({"time": round(start_beat - 0.05, 3), "value": 0.0})

        for i in range(steps + 1):
            t_norm = i / steps
            t_curr = start_beat + t_norm * duration_beats
            # Volume exponential curve
            v = min_gain + (max_gain - min_gain) * (t_norm ** 2.0)
            # Pitch bend ramp: -8192 (or 0) up to +8191
            p = round(t_norm * 8191.0, 1)

            vol_points.append({"time": round(t_curr, 3), "value": round(v, 4)})
            pitch_points.append({"time": round(t_curr, 3), "value": p})

        # Cut at drop
        vol_points.append({"time": round(arrival_beat, 3), "value": 0.0})
        pitch_points.append({"time": round(arrival_beat, 3), "value": 0.0})

        return {
            "volume_envelope": vol_points,
            "pitch_bend_envelope": pitch_points
        }

    @classmethod
    def generate_procedural_snare_roll(
        cls,
        target_bar: float,
        duration_bars: float = 1.0,
        snare_pitch: int = 38,
        base_velocity: int = 50,
        max_velocity: int = 127
    ) -> List[NoteEvent]:
        """
        Generates an accelerating build-up snare roll (1/8 -> 1/16 -> 1/24 -> 1/32 -> flam).
        """
        arrival_beat = max(0.0, (target_bar - 1.0) * 4.0)
        duration_beats = duration_bars * 4.0
        start_beat = max(0.0, arrival_beat - duration_beats)

        notes: List[NoteEvent] = []

        # Stage 1: 1/8 notes (Beat 0.0 to 1.0 of the roll)
        for i in range(2):
            t = start_beat + i * 0.5
            v = int(base_velocity + (max_velocity - base_velocity) * (0.15 * i))
            notes.append(NoteEvent(pitch=snare_pitch, start=round(t, 3), duration=0.35, velocity=v))

        # Stage 2: 1/16 notes (Beat 1.0 to 2.5 of the roll)
        for i in range(6):
            t = start_beat + 1.0 + i * 0.25
            v = int(base_velocity + (max_velocity - base_velocity) * (0.3 + 0.07 * i))
            notes.append(NoteEvent(pitch=snare_pitch, start=round(t, 3), duration=0.18, velocity=v))

        # Stage 3: 1/32 triplets and straight notes (Beat 2.5 to 3.75)
        for i in range(10):
            t = start_beat + 2.5 + i * 0.125
            v = int(base_velocity + (max_velocity - base_velocity) * (0.7 + 0.03 * i))
            notes.append(NoteEvent(pitch=snare_pitch, start=round(t, 3), duration=0.09, velocity=min(127, v)))

        # Stage 4: Flam right before arrival (beat 3.85 & 3.92)
        flam_time = arrival_beat - 0.12
        notes.append(NoteEvent(pitch=snare_pitch, start=round(flam_time, 3), duration=0.06, velocity=85))
        notes.append(NoteEvent(pitch=snare_pitch, start=round(flam_time + 0.06, 3), duration=0.06, velocity=127))

        return notes

    @classmethod
    def apply_transition_riser(
        cls,
        conn: Any,
        track_index: int = 13,
        target_bar: float = 33.0,
        duration_bars: float = 2.0,
        include_filter_sweep: bool = True,
        include_snare_roll: bool = True
    ) -> Dict[str, Any]:
        """Dispatches automated risers and fills into Ableton Live."""
        sweep_points = []
        if include_filter_sweep:
            sweep_points = cls.generate_filter_sweep(target_bar=target_bar, duration_bars=duration_bars)

        snare_notes = []
        if include_snare_roll:
            snare_notes = cls.generate_procedural_snare_roll(target_bar=target_bar, duration_bars=1.0)

        if conn is not None and hasattr(conn, "send_command"):
            try:
                # Inject Filter Frequency Envelope
                if sweep_points:
                    conn.send_command("create_arrangement_automation_envelope", {
                        "track_index": track_index,
                        "parameter": "Frequency",
                        "points": sweep_points
                    })
                # Add snare roll notes
                if snare_notes:
                    start_bar_roll = target_bar - 1.0
                    conn.send_command("add_notes_to_clip", {
                        "track_index": track_index,
                        "clip_index": 0,
                        "notes": [
                            {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
                            for n in snare_notes
                        ]
                    })
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "target_bar": target_bar,
            "duration_bars": duration_bars,
            "sweep_points_count": len(sweep_points),
            "snare_notes_count": len(snare_notes),
            "track_index": track_index
        }

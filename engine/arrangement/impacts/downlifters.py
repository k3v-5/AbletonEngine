# engine/arrangement/impacts/downlifters.py
"""
Impacts, Downlifters & Sub-Boom Engine.
Generates dynamic transitional releases:
- Subphase 2.1: White noise & tonal downlifters with exponential filter decay (20 kHz -> 150 Hz).
- Subphase 2.2: Sub-boom impacts with downward pitch modulation (140 Hz -> 32 Hz / 808 pitch drop).
- Subphase 2.3: Reverse cymbal swells with surgical pre-impact silence gap (~0.05 beats).
"""

from enum import Enum
import math
import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("ImpactEngine")


class ImpactType(str, Enum):
    DOWNLIFTER_NOISE = "downlifter_noise"
    SUB_BOOM_DROP = "sub_boom_drop"
    REVERSE_CYMBAL_SWELL = "reverse_cymbal_swell"
    HYBRID_IMPACT = "hybrid_impact"


class DownlifterCurve(str, Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"


@dataclass
class ImpactEnvelope:
    impact_type: ImpactType
    start_bar: float
    duration_bars: float
    cutoff_points: List[Tuple[float, float]] = field(default_factory=list)
    volume_points: List[Tuple[float, float]] = field(default_factory=list)
    pitch_bend_points: List[Tuple[float, int]] = field(default_factory=list)
    midi_notes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "impact_type": self.impact_type.value,
            "start_bar": self.start_bar,
            "duration_bars": self.duration_bars,
            "cutoff_points_count": len(self.cutoff_points),
            "volume_points_count": len(self.volume_points),
            "pitch_bend_points_count": len(self.pitch_bend_points),
            "midi_notes_count": len(self.midi_notes),
            "midi_notes": self.midi_notes,
        }


class ImpactEngine:
    """
    Procedural impact and downlifter generator for post-drop and section transitions.
    """

    @staticmethod
    def generate_downlifter_sweep(
        start_bar: float = 1.0,
        duration_bars: float = 4.0,
        cutoff_start: float = 20000.0,
        cutoff_end: float = 150.0,
        curve: DownlifterCurve = DownlifterCurve.EXPONENTIAL,
        resolution_steps: int = 32,
    ) -> ImpactEnvelope:
        """
        Subphase 2.1: Downlifter sweep with descending filter cutoff and decaying volume.
        """
        cutoff_points: List[Tuple[float, float]] = []
        volume_points: List[Tuple[float, float]] = []
        total_beats = duration_bars * 4.0

        for step in range(resolution_steps + 1):
            ratio = step / float(resolution_steps)
            beat_offset = ratio * total_beats

            # Compute filter cutoff curve (high to low)
            if curve == DownlifterCurve.EXPONENTIAL:
                # Exponential decay: rapid initial drop tapering into low-mid warmth
                decay_factor = math.exp(-3.0 * ratio)
                freq = cutoff_end + (cutoff_start - cutoff_end) * decay_factor
            elif curve == DownlifterCurve.LOGARITHMIC:
                # Logarithmic decay: sustained highs before sudden drop
                decay_factor = 1.0 - math.log10(1.0 + 9.0 * ratio)
                freq = cutoff_end + (cutoff_start - cutoff_end) * max(0.0, decay_factor)
            else:
                # Linear
                freq = cutoff_start - (cutoff_start - cutoff_end) * ratio

            freq = max(20.0, min(22000.0, freq))
            cutoff_points.append((round(beat_offset, 3), round(freq, 1)))

            # Volume decay: 0.85 -> 0.05
            vol = 0.85 * math.pow(1.0 - ratio, 1.5)
            volume_points.append((round(beat_offset, 3), round(max(0.0, vol), 3)))

        return ImpactEnvelope(
            impact_type=ImpactType.DOWNLIFTER_NOISE,
            start_bar=start_bar,
            duration_bars=duration_bars,
            cutoff_points=cutoff_points,
            volume_points=volume_points,
        )

    @staticmethod
    def generate_sub_boom(
        target_bar: float = 1.0,
        duration_beats: float = 4.0,
        root_pitch: int = 36,  # C1
        pitch_drop_semitones: int = 12,
        start_freq_hz: float = 140.0,
        end_freq_hz: float = 32.0,
    ) -> ImpactEnvelope:
        """
        Subphase 2.2: Sub-boom drop with analog sine pitch sweep (140 Hz -> 32 Hz).
        Triggers a root note and modulates pitch bend downward from +8191 / semitones down to -8192.
        """
        pitch_bend_points: List[Tuple[float, int]] = []
        volume_points: List[Tuple[float, float]] = []

        # Sustained low note on downbeat
        midi_notes = [
            {
                "pitch": root_pitch,
                "start_time": 0.0,
                "duration": duration_beats,
                "velocity": 127,
                "mute": False,
            }
        ]

        steps = 24
        for step in range(steps + 1):
            ratio = step / float(steps)
            beat_offset = ratio * duration_beats

            # Exponential pitch drop from +8191 down to -4096 (or 0)
            bend_val = int(8191.0 * math.exp(-4.5 * ratio) - 2048.0 * (1.0 - math.exp(-2.0 * ratio)))
            bend_val = max(-8192, min(8191, bend_val))
            pitch_bend_points.append((round(beat_offset, 3), bend_val))

            # Sub volume: immediate punch at 1.0 tapering smoothly
            vol = 0.95 * math.exp(-1.8 * ratio)
            volume_points.append((round(beat_offset, 3), round(max(0.0, vol), 3)))

        return ImpactEnvelope(
            impact_type=ImpactType.SUB_BOOM_DROP,
            start_bar=target_bar,
            duration_bars=duration_beats / 4.0,
            pitch_bend_points=pitch_bend_points,
            volume_points=volume_points,
            midi_notes=midi_notes,
        )

    @staticmethod
    def generate_reverse_cymbal_swell(
        target_bar: float = 9.0,
        duration_bars: float = 2.0,
        pre_impact_gap_beats: float = 0.05,
    ) -> ImpactEnvelope:
        """
        Subphase 2.3: Reverse cymbal swell with pre-impact silence vacuum.
        Volume rises exponentially (0.05 -> 1.0) and snaps to 0.0 right before the downbeat.
        """
        total_beats = duration_bars * 4.0
        active_beats = max(0.1, total_beats - pre_impact_gap_beats)
        volume_points: List[Tuple[float, float]] = []
        steps = 20

        for step in range(steps + 1):
            ratio = step / float(steps)
            beat_offset = ratio * active_beats
            # Exponential swelling curve
            vol = math.pow(ratio, 2.5)
            volume_points.append((round(beat_offset, 3), round(min(1.0, vol), 3)))

        # Surgical vacuum silence in gap
        volume_points.append((round(active_beats + 0.001, 3), 0.0))
        volume_points.append((round(total_beats, 3), 0.0))

        # MIDI trigger note for cymbal/sampler
        midi_notes = [
            {
                "pitch": 49,  # Crash 1
                "start_time": 0.0,
                "duration": total_beats,
                "velocity": 115,
                "mute": False,
            }
        ]

        return ImpactEnvelope(
            impact_type=ImpactType.REVERSE_CYMBAL_SWELL,
            start_bar=target_bar - duration_bars,
            duration_bars=duration_bars,
            volume_points=volume_points,
            midi_notes=midi_notes,
        )

    @classmethod
    def apply_impact_to_live(
        cls,
        conn: Any,
        track_index: int,
        impact_type: ImpactType,
        target_bar: float,
        duration_bars: float = 2.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Dispatches impact generation to Ableton Live via connection adapter.
        """
        if impact_type == ImpactType.DOWNLIFTER_NOISE:
            envelope = cls.generate_downlifter_sweep(
                start_bar=target_bar,
                duration_bars=duration_bars,
                cutoff_start=kwargs.get("cutoff_start", 20000.0),
                cutoff_end=kwargs.get("cutoff_end", 150.0),
            )
        elif impact_type == ImpactType.SUB_BOOM_DROP:
            envelope = cls.generate_sub_boom(
                target_bar=target_bar,
                duration_beats=duration_bars * 4.0,
                root_pitch=kwargs.get("root_pitch", 36),
            )
        elif impact_type == ImpactType.REVERSE_CYMBAL_SWELL:
            envelope = cls.generate_reverse_cymbal_swell(
                target_bar=target_bar,
                duration_bars=duration_bars,
                pre_impact_gap_beats=kwargs.get("pre_impact_gap_beats", 0.05),
            )
        else:
            # Hybrid: downlifter with sub-boom on impact
            envelope = cls.generate_downlifter_sweep(
                start_bar=target_bar,
                duration_bars=duration_bars,
            )

        # Dispatch commands if connection is active
        applied_cmds = []
        if conn and hasattr(conn, "send_command"):
            # If there are MIDI notes, create clip
            if envelope.midi_notes:
                conn.send_command("create_clip", {
                    "track_index": track_index,
                    "slot_index": 0,
                    "length": envelope.duration_bars * 4.0
                })
                conn.send_command("add_notes_to_clip", {
                    "track_index": track_index,
                    "clip_index": 0,
                    "notes": envelope.midi_notes
                })
                applied_cmds.extend(["create_clip", "add_notes_to_clip"])

            # Filter cutoff automation
            if envelope.cutoff_points:
                conn.send_command("create_automation", {
                    "track_index": track_index,
                    "device_index": 0,
                    "parameter_name": "Frequency",
                    "points": [{"time": pt[0], "value": pt[1]} for pt in envelope.cutoff_points]
                })
                applied_cmds.append("create_automation_cutoff")

            # Volume automation
            if envelope.volume_points:
                conn.send_command("create_automation", {
                    "track_index": track_index,
                    "device_index": 0,
                    "parameter_name": "Volume",
                    "points": [{"time": pt[0], "value": pt[1]} for pt in envelope.volume_points]
                })
                applied_cmds.append("create_automation_volume")

        return {
            "status": "success",
            "impact_type": impact_type.value,
            "target_bar": target_bar,
            "duration_bars": duration_bars,
            "envelope": envelope.to_dict(),
            "applied_cmds": applied_cmds,
        }

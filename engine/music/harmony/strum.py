# engine/music/harmony/strum.py
"""
Physical Chord Strummer:
Applies natural keyboard finger-roll staggering (8-18 ms) and physiological velocity tilt
to polyphonic chord voicings, eliminating synthetic simultaneous key-strikes.
"""

import random
from typing import List, Dict, Any, Optional
from engine.music.models import NoteEvent
from engine.music.groove.pocket import GroovePocketEngine


class PhysicalChordStrummer:
    """Master keyboard chord strummer with alternating strum directions and velocity tilt."""

    @classmethod
    def strum_notes(
        cls,
        notes: List[NoteEvent],
        tempo: float = 142.0,
        strum_ms: float = 14.0,
        direction: str = "alternating",
        velocity_tilt: float = 0.15,
        tolerance_beats: float = 0.05,
        seed: int = 42
    ) -> List[NoteEvent]:
        """
        Staggers simultaneous notes into realistic human chord finger-rolls.
        If direction == 'alternating', even bars strum up, odd bars strum down.
        """
        if not notes or strum_ms <= 0.0:
            return [NoteEvent(**n.__dict__) for n in notes]

        # 1. Cluster notes occurring at the same start time
        sorted_notes = sorted(notes, key=lambda n: n.start)
        clusters: List[List[NoteEvent]] = []
        curr_cluster: List[NoteEvent] = []

        for n in sorted_notes:
            if not curr_cluster:
                curr_cluster.append(n)
            else:
                if abs(n.start - curr_cluster[0].start) <= tolerance_beats:
                    curr_cluster.append(n)
                else:
                    clusters.append(curr_cluster)
                    curr_cluster = [n]
        if curr_cluster:
            clusters.append(curr_cluster)

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat
        rng = random.Random(seed)

        strummed_notes: List[NoteEvent] = []

        for cluster in clusters:
            if len(cluster) <= 1:
                strummed_notes.extend(cluster)
                continue

            bar_number = int(cluster[0].start // 4.0)
            # Decide strum direction
            if direction == "alternating":
                dir_actual = "up" if (bar_number % 2 == 0) else "down"
            else:
                dir_actual = direction.lower()

            # Sort cluster by pitch
            ordered = sorted(cluster, key=lambda n: n.pitch, reverse=(dir_actual == "down"))
            n_voices = len(ordered)
            base_start = ordered[0].start

            for i, note in enumerate(ordered):
                spread_ms = max(0.0, (i * strum_ms) + (0.0 if i == 0 else rng.gauss(0.0, 1.0)))
                voice_offset_beats = spread_ms * beats_per_ms
                new_start = max(base_start, base_start + voice_offset_beats)

                # Velocity tilt: thumb/bass voice has full weight, inner/upper voices nuanced
                tilt = 1.0 + (i / max(1, n_voices - 1) - 0.5) * velocity_tilt
                new_vel = max(1, min(127, int(round(note.velocity * tilt))))

                strummed_notes.append(NoteEvent(
                    pitch=note.pitch,
                    pitch_class=note.pitch_class,
                    octave=note.octave,
                    start=round(new_start, 5),
                    duration=max(0.05, round(note.duration - voice_offset_beats, 5)),
                    velocity=new_vel,
                    channel=note.channel,
                    probability=note.probability,
                    accent=note.accent
                ))

        return sorted(strummed_notes, key=lambda n: n.start)

    @classmethod
    def strum_dict_notes(
        cls,
        dict_notes: List[Dict[str, Any]],
        tempo: float = 142.0,
        strum_ms: float = 14.0,
        direction: str = "alternating",
        velocity_tilt: float = 0.15
    ) -> List[Dict[str, Any]]:
        """Helper to process dict notes from Live's get_clip_notes directly."""
        note_events = [
            NoteEvent(
                pitch=d.get("pitch", 60),
                start=d.get("start_time", 0.0),
                duration=d.get("duration", 1.0),
                velocity=d.get("velocity", 90)
            )
            for d in dict_notes
        ]

        strummed = cls.strum_notes(
            notes=note_events,
            tempo=tempo,
            strum_ms=strum_ms,
            direction=direction,
            velocity_tilt=velocity_tilt
        )

        return [
            {
                "pitch": n.pitch,
                "start_time": n.start,
                "duration": n.duration,
                "velocity": n.velocity,
                "mute": False
            }
            for n in strummed
        ]

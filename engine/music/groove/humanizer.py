# engine/music/groove/humanizer.py
"""
Dynamic Groove Humanizer:
Orchestrates micro-timing displacement, MPC 60 / Dilla hardware swing, and Gaussian velocity shaping
across MIDI notes and Ableton Live clips.
"""

import random
from typing import List, Dict, Any, Optional, Union
from engine.music.models import NoteEvent
from .pocket import GroovePocketEngine, PocketStyle
from .pool import GroovePoolEngine, GroovePreset


class DynamicGrooveHumanizer:
    """Master humanization engine unifying micro-timing, hardware swing, and expressive velocity."""

    @classmethod
    def humanize_notes(
        cls,
        notes: List[NoteEvent],
        role: str = "drums",
        pocket_style: str = "atlanta_trap",
        tempo: float = 142.0,
        strength: float = 1.0,
        swing_percentage: float = 58.0,
        seed: int = 42
    ) -> List[NoteEvent]:
        """
        Applies genre-specific micro-timing, MPC hardware swing, and velocity dynamics to NoteEvents.
        """
        if not notes:
            return []

        # 1. Apply hardware swing offsets from GroovePoolEngine
        dna = GroovePoolEngine.get_preset_dna(
            preset=GroovePreset.MPC_60,
            swing_percentage=swing_percentage,
            bpm=tempo
        )
        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        swung_notes: List[NoteEvent] = []
        for n in notes:
            # Determine 16th note step index (0-15 within a 4-beat bar)
            step_in_bar = int(round((n.start % 4.0) / 0.25)) % 16
            offset_ms = dna.timing_offsets_ms[step_in_bar] * strength
            vel_mult = dna.velocity_multipliers[step_in_bar]

            new_start = max(0.0, n.start + (offset_ms * beats_per_ms))
            new_vel = int(round(n.velocity * vel_mult))

            swung_notes.append(NoteEvent(
                pitch=n.pitch,
                pitch_class=n.pitch_class,
                octave=n.octave,
                start=round(new_start, 5),
                duration=n.duration,
                velocity=max(1, min(127, new_vel)),
                channel=n.channel,
                probability=n.probability,
                accent=n.accent
            ))

        # 2. Apply micro-timing jitter and pocket physics via GroovePocketEngine
        pocketed = GroovePocketEngine.apply_pocket_to_notes(
            notes=swung_notes,
            role=role,
            pocket_style=pocket_style,
            tempo=tempo,
            strength=strength,
            seed=seed
        )

        return pocketed

    @classmethod
    def humanize_clip_dict_notes(
        cls,
        dict_notes: List[Dict[str, Any]],
        role: str = "drums",
        pocket_style: str = "atlanta_trap",
        tempo: float = 142.0,
        strength: float = 1.0,
        swing_percentage: float = 58.0,
        seed: int = 42
    ) -> List[Dict[str, Any]]:
        """Helper to process standard Live dictionary notes format directly."""
        note_events = [
            NoteEvent(
                pitch=d.get("pitch", 60),
                start=d.get("start_time", 0.0),
                duration=d.get("duration", 0.25),
                velocity=d.get("velocity", 100)
            )
            for d in dict_notes
        ]

        humanized = cls.humanize_notes(
            notes=note_events,
            role=role,
            pocket_style=pocket_style,
            tempo=tempo,
            strength=strength,
            swing_percentage=swing_percentage,
            seed=seed
        )

        return [
            {
                "pitch": n.pitch,
                "start_time": n.start,
                "duration": n.duration,
                "velocity": n.velocity,
                "mute": False
            }
            for n in humanized
        ]

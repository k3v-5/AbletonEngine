# engine/music/drums/ghost_notes.py
"""
Drum Ghost Note & Hi-Hat Dynamics Injector:
Enriches drum patterns with authentic ghost snares, turnaround fills, and 16th-note dynamic velocity waves.
"""

import random
from typing import List, Dict, Any, Optional
from engine.music.models import NoteEvent


class DrumGhostNoteInjector:
    """Injects subtle ghost snare notes and shapes hi-hat dynamics with velocity waves."""

    SNARE_NOTE = 38
    CLOSED_HAT_NOTE = 42
    OPEN_HAT_NOTE = 46

    # 4-step 16th note velocity wave profile: Accent -> Soft -> Medium -> Quiet
    HAT_VELOCITY_PROFILE = [105, 72, 92, 65]

    @classmethod
    def inject_ghost_notes(
        cls,
        notes: List[NoteEvent],
        total_bars: int = 96,
        snare_note: int = 38,
        seed: int = 42
    ) -> List[NoteEvent]:
        """
        Detects turnaround bars (bars 4, 8, 12, 16...) and injects realistic low-velocity ghost snares.
        """
        if not notes:
            return []

        rng = random.Random(seed)
        existing_positions = {(round(n.start, 3), n.pitch) for n in notes}
        augmented = [NoteEvent(**n.__dict__) for n in notes]

        for bar in range(total_bars):
            bar_start = float(bar * 4)
            is_turnaround = ((bar + 1) % 4 == 0)

            # In turnaround bars, inject ghost snares in the 4th beat
            if is_turnaround:
                # 16th positions in beat 4: 3.25, 3.5, 3.75
                candidate_offsets = [3.25, 3.75]
                for offset in candidate_offsets:
                    g_pos = bar_start + offset
                    if (round(g_pos, 3), snare_note) not in existing_positions:
                        g_vel = rng.randint(28, 44)
                        augmented.append(NoteEvent(
                            pitch=snare_note,
                            start=round(g_pos, 5),
                            duration=0.15,
                            velocity=g_vel,
                            probability=0.90,
                            accent=False
                        ))
            elif (bar + 1) % 2 == 0:
                # Occasional single ghost note pickup at 3.75
                g_pos = bar_start + 3.75
                if (round(g_pos, 3), snare_note) not in existing_positions and rng.random() > 0.40:
                    g_vel = rng.randint(24, 38)
                    augmented.append(NoteEvent(
                        pitch=snare_note,
                        start=round(g_pos, 5),
                        duration=0.15,
                        velocity=g_vel,
                        probability=0.85,
                        accent=False
                    ))

        return sorted(augmented, key=lambda n: n.start)

    @classmethod
    def shape_hihat_velocities(
        cls,
        notes: List[NoteEvent],
        hat_note: int = 42,
        seed: int = 42
    ) -> List[NoteEvent]:
        """
        Applies a dynamic 4-step velocity wave pattern across 16th-note hi-hat events.
        """
        if not notes:
            return []

        rng = random.Random(seed)
        shaped: List[NoteEvent] = []

        for n in notes:
            if n.pitch == hat_note:
                # Step 0-3 within the beat
                step_in_beat = int(round((n.start % 1.0) / 0.25)) % 4
                base_target = cls.HAT_VELOCITY_PROFILE[step_in_beat]
                jitter = rng.randint(-4, 4)
                new_vel = max(35, min(127, base_target + jitter))

                shaped.append(NoteEvent(
                    pitch=n.pitch,
                    pitch_class=n.pitch_class,
                    octave=n.octave,
                    start=n.start,
                    duration=n.duration,
                    velocity=new_vel,
                    channel=n.channel,
                    probability=n.probability,
                    accent=(step_in_beat == 0)
                ))
            else:
                shaped.append(NoteEvent(**n.__dict__))

        return shaped

    @classmethod
    def process_drum_track_notes(
        cls,
        notes: List[NoteEvent],
        total_bars: int = 96,
        seed: int = 42
    ) -> List[NoteEvent]:
        """Applies both ghost snare injection and hi-hat velocity shaping in a single pass."""
        with_ghosts = cls.inject_ghost_notes(notes, total_bars=total_bars, seed=seed)
        shaped = cls.shape_hihat_velocities(with_ghosts, seed=seed)
        return shaped

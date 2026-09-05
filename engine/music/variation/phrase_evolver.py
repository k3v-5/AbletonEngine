# engine/music/variation/phrase_evolver.py
"""
Phrase Evolver Engine:
Implements formal musical phrase evolution (A -> A' -> B -> A'') across 16-bar and 32-bar sections.
Prevents static 4-bar looping by generating organic variations, tension departures, and climactic returns.
"""

from enum import Enum
import random
from typing import List, Dict, Any, Optional
from ..models import NoteEvent
from ..theory.scales import snap_to_scale, get_scale_pitch_classes


class PhraseFunction(str, Enum):
    STATEMENT_A = "STATEMENT_A"      # Bar 1-4: Core theme establish
    VARIATION_A_PRIME = "VARIATION_A_PRIME" # Bar 5-8: Subtle ornament & fill
    DEPARTURE_B = "DEPARTURE_B"      # Bar 9-12: Contrast / density shift
    CLIMAX_A_DOUBLE_PRIME = "CLIMAX_A_DOUBLE_PRIME" # Bar 13-16: Climax & transition cutoff


class PhraseEvolver:
    """Evolves 4-bar clips across multi-phrase arrangement sections."""

    @classmethod
    def evolve_phrase(
        cls,
        notes: List[NoteEvent],
        phrase_index: int = 0,
        total_phrases: int = 4,
        role: str = "drums",
        genre: str = "trap",
        key: str = "F",
        scale: str = "natural_minor",
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Evolves a 4-bar motif based on its phrase function in the section.
        phrase_index: 0 -> A, 1 -> A', 2 -> B, 3 -> A'' (repeats modulo 4).
        """
        if not notes:
            return []

        func_idx = phrase_index % 4
        rng = random.Random((seed or 42) + phrase_index * 17)
        role_clean = role.lower().replace("-", "_").replace(" ", "_")

        # 1. Statement A (Theme established - exact baseline)
        if func_idx == 0:
            return [NoteEvent(**n.__dict__) for n in notes]

        # 2. Variation A' (Subtle embellishment)
        elif func_idx == 1:
            return cls._apply_a_prime(notes, role_clean, rng, key, scale)

        # 3. Departure B (Contrast / tension)
        elif func_idx == 2:
            return cls._apply_departure_b(notes, role_clean, rng, key, scale)

        # 4. Climax A'' (Climactic resolution & section wrap-up)
        else:
            return cls._apply_climax_a_double_prime(notes, role_clean, rng, key, scale)

    @classmethod
    def _apply_a_prime(
        cls,
        notes: List[NoteEvent],
        role: str,
        rng: random.Random,
        key: str,
        scale: str
    ) -> List[NoteEvent]:
        """Subtle ornament: 1/32 rolls on hats, ghost note on snare, octave jump in bar 4."""
        varied: List[NoteEvent] = []
        max_beat = max((n.start + n.duration for n in notes), default=16.0)

        for n in notes:
            # Embellish end of phrase (last 4 beats: beats 12 to 16)
            is_end_of_phrase = n.start >= (max_beat - 4.0)

            # A. Bass / 808: octave jump on last note
            if "bass" in role and is_end_of_phrase and rng.random() < 0.65:
                jump_pitch = min(50, n.pitch + 12)
                varied.append(NoteEvent(
                    pitch=jump_pitch,
                    pitch_class=jump_pitch % 12,
                    octave=(jump_pitch // 12) - 1,
                    start=n.start,
                    duration=max(0.2, n.duration * 0.75),
                    velocity=min(127, n.velocity + 8),
                    accent=True
                ))

            # B. Drums: add hi-hat roll or ghost snare
            elif "drum" in role or "hat" in role:
                varied.append(NoteEvent(**n.__dict__))
                if is_end_of_phrase and n.pitch in [42, 44] and rng.random() < 0.5:
                    # Inject 1/32 roll note
                    roll_start = n.start + 0.125
                    varied.append(NoteEvent(
                        pitch=n.pitch,
                        start=roll_start,
                        duration=0.1,
                        velocity=max(40, n.velocity - 15)
                    ))
            else:
                varied.append(NoteEvent(**n.__dict__))

        # Inject subtle ghost snare around beat 14.5 if drums
        if "drum" in role:
            varied.append(NoteEvent(pitch=38, start=14.5, duration=0.15, velocity=38))

        return sorted(varied, key=lambda n: n.start)

    @classmethod
    def _apply_departure_b(
        cls,
        notes: List[NoteEvent],
        role: str,
        rng: random.Random,
        key: str,
        scale: str
    ) -> List[NoteEvent]:
        """Departure B: Contrast, density reduction, syncopation shifts."""
        varied: List[NoteEvent] = []

        for n in notes:
            # A. Kick dropout in bar 1 (beats 0 to 4) for breathing space
            if ("kick" in role or ("drum" in role and n.pitch == 36)) and n.start < 4.0:
                continue

            # B. Bass: staccato / shorter duration
            if "bass" in role:
                varied.append(NoteEvent(
                    pitch=n.pitch,
                    pitch_class=n.pitch_class,
                    octave=n.octave,
                    start=n.start,
                    duration=max(0.25, n.duration * 0.5), # punchy staccato
                    velocity=n.velocity,
                    accent=n.accent
                ))
            # C. Melody / Lead: diatonic transposition / step shift
            elif "lead" in role and rng.random() < 0.35:
                shifted = snap_to_scale(key, scale, n.pitch + rng.choice([-2, 2, 3]))
                varied.append(NoteEvent(
                    pitch=shifted,
                    pitch_class=shifted % 12,
                    octave=(shifted // 12) - 1,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity
                ))
            else:
                varied.append(NoteEvent(**n.__dict__))

        return sorted(varied, key=lambda n: n.start)

    @classmethod
    def _apply_climax_a_double_prime(
        cls,
        notes: List[NoteEvent],
        role: str,
        rng: random.Random,
        key: str,
        scale: str
    ) -> List[NoteEvent]:
        """Climax A'': Full return with peak energy and pre-transition fill."""
        varied: List[NoteEvent] = []
        max_beat = max((n.start + n.duration for n in notes), default=16.0)

        for n in notes:
            # Pre-drop silence: clear the very last beat (beat 15 to 16)
            if n.start >= (max_beat - 1.0):
                continue

            # Velocity boost (+5% to +10%) for climax feel
            climax_vel = min(127, int(n.velocity * 1.08))
            varied.append(NoteEvent(
                pitch=n.pitch,
                pitch_class=n.pitch_class,
                octave=n.octave,
                start=n.start,
                duration=n.duration,
                velocity=climax_vel,
                accent=True
            ))

        # Add 4-snare turnaround roll on beats 14.0, 14.25, 14.5, 14.75 if drums
        if "drum" in role:
            for idx, st in enumerate([14.0, 14.25, 14.5, 14.75]):
                varied.append(NoteEvent(
                    pitch=38,
                    start=st,
                    duration=0.15,
                    velocity=80 + idx * 12
                ))

        return sorted(varied, key=lambda n: n.start)

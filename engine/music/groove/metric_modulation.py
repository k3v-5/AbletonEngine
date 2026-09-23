# engine/music/groove/metric_modulation.py
"""
Micro-Rhythmic Metric Modulation & Polyrhythm Engine:
Implements mathematical rhythmic subdivisions and metric modulation for modern commercial styles:
- Trap, Drill, Afrobeat, Modern Reggaetón / Dembow.
- Alternates binary grids (1/8, 1/16) with triplets (1/8T, 1/16T, 1/24), quintuplets (5:4),
  septuplets (7:4), and nested polyrhythms.
- Features velocity micro-ramps and micro-pitch drops across rapid rolls.
- Governed strictly by 5 discrete complexity levels.
"""

from enum import IntEnum
from typing import List, Dict, Any, Optional, Tuple
import math
import random
import logging

from engine.music.models import NoteEvent

logger = logging.getLogger("MetricModulationEngine")


class MetricModulationLevel(IntEnum):
    STRAIGHT_CLASSIC = 1       # 100% binary 8th/16th notes. Clean, minimal, rock/pop grid.
    COMMERCIAL_TRIPLETS = 2    # Standard 1/8T & 1/16T rolls at turnaround bars 4 and 8 (Atlanta trap standard).
    METRIC_SHIFTING = 3        # Fluid shifting: Binary 1/16 -> Hemiola 3:4 -> Triplet burst.
    ODD_GROUPINGS = 4          # 5:4 Quintuplets & 7:4 Septuplets with micro pitch drop (UK Drill / Afrobeat).
    VIRTUOSO_POLYRHYTHMIC = 5  # Nested polyrhythms, rapid metric illusions, and stereo pan sweeps.


class MetricModulationEngine:
    """Generates and modulates advanced rhythmic subdivisions and polyrhythmic rolls."""

    LEVEL_CONFIGS: Dict[int, Dict[str, Any]] = {
        1: {
            "name": "Recto Clásico (Straight Grid)",
            "subdivisions": ["1/8", "1/16"],
            "has_triplets": False,
            "has_quintuplets": False,
            "has_pitch_glides": False,
            "description": "Subdivisiones binarias puras sin modulación métrica. Base limpia y sólida."
        },
        2: {
            "name": "Tresillos Comerciales (Commercial Triplets)",
            "subdivisions": ["1/16", "1/12 (1/8T)", "1/24 (1/16T)"],
            "has_triplets": True,
            "has_quintuplets": False,
            "has_pitch_glides": False,
            "description": "Rolls estándar en tresillos (1/8T y 1/16T) en compases 4 y 8 de resolución."
        },
        3: {
            "name": "Modulación Métrica Polirrítmica (Metric Shifting)",
            "subdivisions": ["1/16", "3:4 Hemiola", "1/24", "1/32"],
            "has_triplets": True,
            "has_quintuplets": False,
            "has_pitch_glides": True,
            "description": "Alternancia de pulso: binario a hemiola 3:4 con aceleración a tresillos."
        },
        4: {
            "name": "Quintillos y Septillos Matemáticos (Drill & Afrobeat)",
            "subdivisions": ["5:4 Quintuplets", "7:4 Septuplets", "1/32", "1/24"],
            "has_triplets": True,
            "has_quintuplets": True,
            "has_pitch_glides": True,
            "description": "Subdivisiones impares (5 y 7 notas por tiempo) con caídas microtonales de pitch."
        },
        5: {
            "name": "Virtuosismo Matemático y Polirritmias Anidadas",
            "subdivisions": ["Nested 5:3", "7:4", "Stereo Sweeps", "Metric Illusion"],
            "has_triplets": True,
            "has_quintuplets": True,
            "has_pitch_glides": True,
            "description": "Polirritmias anidadas, barridos estéreo y aceleraciones no euclidianas."
        }
    }

    @classmethod
    def get_config(cls, level: int = 2) -> Dict[str, Any]:
        clamped = max(1, min(5, int(level)))
        return cls.LEVEL_CONFIGS.get(clamped, cls.LEVEL_CONFIGS[2])

    @classmethod
    def generate_metric_roll(
        cls,
        target_beat: float,
        duration_beats: float = 1.0,
        level: int = 2,
        base_pitch: int = 42,           # Default F#1 closed hat
        base_velocity: int = 90,
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Generates a rhythmic roll leading up to target_beat, applying mathematical subdivisions
        matching the chosen complexity level.
        """
        clamped_level = max(1, min(5, int(level)))
        rng = random.Random(seed)
        events: List[NoteEvent] = []

        start_beat = max(0.0, target_beat - duration_beats)

        if clamped_level == 1:
            # Straight 16th notes (4 notes per beat)
            step = 0.25
            n_notes = int(round(duration_beats / step))
            for i in range(n_notes):
                t = start_beat + (i * step)
                vel = min(127, int(base_velocity * (0.80 + 0.20 * (i / max(1, n_notes - 1)))))
                events.append(NoteEvent(pitch=base_pitch, start=round(t, 4), duration=round(step * 0.85, 4), velocity=vel))

        elif clamped_level == 2:
            # Triplet roll: 1/8T into 1/16T acceleration (6 notes per beat)
            # First half 1/16 (step 0.25), second half 1/24 (step 0.1667)
            half = duration_beats * 0.5
            # First half
            step1 = 0.25
            n1 = int(round(half / step1))
            for i in range(n1):
                t = start_beat + (i * step1)
                vel = int(base_velocity * 0.82)
                events.append(NoteEvent(pitch=base_pitch, start=round(t, 4), duration=round(step1 * 0.85, 4), velocity=vel))

            # Second half: triplets (step = 1/6 beat = ~0.1667 beat)
            step2 = 1.0 / 6.0
            n2 = int(round(half / step2))
            for j in range(n2):
                t = start_beat + half + (j * step2)
                # Dynamic ramp
                ramp = 0.85 + 0.25 * (j / max(1, n2 - 1))
                vel = min(127, int(base_velocity * ramp))
                events.append(NoteEvent(pitch=base_pitch, start=round(t, 4), duration=round(step2 * 0.85, 4), velocity=vel))

        elif clamped_level == 3:
            # Hemiola shift (3 notes across 2 beats or 3 against 4) then 1/32 burst
            step = 1.0 / 8.0 # 32nd notes in last half
            first_part_len = duration_beats * 0.4
            second_part_len = duration_beats * 0.6

            # First part: dotted 16th hemiola (step = 0.375 beats)
            t_curr = start_beat
            while t_curr < (start_beat + first_part_len):
                events.append(NoteEvent(pitch=base_pitch, start=round(t_curr, 4), duration=0.20, velocity=int(base_velocity * 0.85)))
                t_curr += 0.375

            # Second part: rapid 1/32nd acceleration
            t_curr = start_beat + first_part_len
            n_fast = int(round(second_part_len / 0.125))
            for k in range(n_fast):
                t = t_curr + (k * 0.125)
                vel = min(127, int(base_velocity * (0.80 + 0.30 * (k / max(1, n_fast - 1)))))
                events.append(NoteEvent(pitch=base_pitch, start=round(t, 4), duration=0.09, velocity=vel))

        elif clamped_level == 4:
            # Quintuplets (5 notes per beat) with micro pitch descent
            step = 1.0 / 5.0 # exactly 0.20 beats
            n_notes = int(round(duration_beats * 5))
            for idx in range(n_notes):
                t = start_beat + (idx * step)
                vel = min(127, int(base_velocity * (0.75 + 0.35 * (idx / max(1, n_notes - 1)))))
                # Micro pitch descent on the tail (-2 st on final 2 notes)
                p_offset = -2 if idx >= (n_notes - 2) else 0
                events.append(NoteEvent(pitch=base_pitch + p_offset, start=round(t, 4), duration=round(step * 0.85, 4), velocity=vel))

        else: # Level 5: Nested polyrhythms / Septuplets (7 notes per beat)
            step = 1.0 / 7.0 # ~0.1428 beats
            n_notes = int(round(duration_beats * 7))
            for idx in range(n_notes):
                t = start_beat + (idx * step)
                vel = min(127, int(base_velocity * (0.70 + 0.40 * (idx / max(1, n_notes - 1)))))
                # Alternating pitch micro-texture
                p_offset = -1 if (idx % 2 == 1) else 0
                events.append(NoteEvent(pitch=base_pitch + p_offset, start=round(t, 4), duration=round(step * 0.80, 4), velocity=vel))

        return sorted(events, key=lambda e: e.start)

    @classmethod
    def apply_metric_modulation_to_pattern(
        cls,
        pattern_notes: List[NoteEvent],
        level: int = 2,
        total_bars: int = 8,
        seed: Optional[int] = 42
    ) -> List[NoteEvent]:
        """
        Embeds mathematical rolls into turnaround bars (e.g. bar 4 and bar 8) of a rhythmic pattern.
        """
        if level <= 1 or not pattern_notes:
            return [NoteEvent(**n.__dict__) for n in pattern_notes]

        # Identify turnaround beats: beat 15.0 to 16.0 (end of bar 4), beat 31.0 to 32.0 (end of bar 8)
        turnaround_beats = [16.0, 32.0]
        rolls: List[NoteEvent] = []

        for t_beat in turnaround_beats:
            if t_beat <= (total_bars * 4.0):
                roll = cls.generate_metric_roll(
                    target_beat=t_beat,
                    duration_beats=1.0,
                    level=level,
                    base_pitch=42, # Hi-hat
                    base_velocity=95,
                    seed=seed
                )
                rolls.extend(roll)

        # Filter out existing notes that overlap with roll windows
        roll_windows = [(r_beat - 1.0, r_beat) for r_beat in turnaround_beats]
        kept_notes = []
        for n in pattern_notes:
            overlaps = any(w_start <= n.start < w_end for w_start, w_end in roll_windows)
            if not overlaps:
                kept_notes.append(NoteEvent(**n.__dict__))

        combined = kept_notes + rolls
        return sorted(combined, key=lambda n: n.start)

    @classmethod
    def render_markdown_summary(cls, level: int = 2) -> str:
        """Formats the active metric modulation configuration."""
        cfg = cls.get_config(level)
        lines = [
            f"### 🥁 Modulación Métrica y Polirritmias (`MetricModulationEngine`)",
            f"- **Nivel de Complejidad Rítmica:** **Nivel {level}/5 ({cfg['name']})**",
            f"- **Subdivisiones Activas:** `{', '.join(cfg['subdivisions'])}`",
            f"- **Tresillos (Triplets):** `{'Sí' if cfg['has_triplets'] else 'No'}`",
            f"- **Quintillos / Septillos (Odd Groupings):** `{'Sí (5:4 y 7:4)' if cfg['has_quintuplets'] else 'No'}`",
            f"- **Micro-Glides de Pitch en Rolls:** `{'Sí' if cfg['has_pitch_glides'] else 'No'}`",
            f"- **Descripción:** {cfg['description']}\n",
            "💡 *Beneficio: Transforma patrones estáticos en secuencias dinámicas de alto virtuosismo rítmico comercial.*"
        ]
        return "\n".join(lines)

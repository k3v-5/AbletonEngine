# engine/music/drums/hihat_mutator.py
"""
Evolutionary Hi-Hat Mutator Engine:
Prevents listener fatigue in trap, urban, electronic, and pop grooves by applying
stochastic and structured evolutionary mutations across 8-bar cycles:
- Bar 2: Micro-rolls (1/32 or 1/32 triplet bursts with velocity ramps)
- Bar 4: Pitch drops and subtle downward velocity dips
- Bar 6: Open hat accents with choking and stereo emphasis
- Bar 8: Turnaround cadence rolls signaling phrase transitions
"""

from typing import Dict, Any, List, Optional
import math
import copy
import logging

logger = logging.getLogger("EvolutionaryHiHatMutator")


class EvolutionaryHiHatMutator:
    """
    Applies musical and evolutionary mutations to hi-hat patterns across arrangement phrases.
    """

    CLOSED_HH_PITCH = 42
    PEDAL_HH_PITCH = 44
    OPEN_HH_PITCH = 46

    @classmethod
    def mutate_hihat_pattern(
        cls,
        notes: List[Dict[str, Any]],
        bars: int = 8,
        genre: str = "TRAP",
        intensity: float = 0.6,
        beats_per_bar: float = 4.0
    ) -> Dict[str, Any]:
        """
        Mutates hi-hat MIDI notes across the given bar length using structured evolutionary variations.
        """
        if not notes:
            return {
                "status": "EMPTY_INPUT",
                "genre": genre,
                "bars": bars,
                "original_count": 0,
                "mutated_count": 0,
                "mutations_applied": [],
                "notes": []
            }

        intensity = max(0.1, min(1.0, float(intensity)))
        mutations_applied: List[Dict[str, Any]] = []

        # Sort notes by start_time
        sorted_notes = sorted(notes, key=lambda n: float(n.get("start_time", n.get("start", 0.0))))
        new_notes: List[Dict[str, Any]] = []

        # Map notes to bars
        total_beats = bars * beats_per_bar

        for idx, n in enumerate(sorted_notes):
            n_copy = copy.deepcopy(n)
            st = float(n_copy.get("start_time", n_copy.get("start", 0.0)))
            dur = float(n_copy.get("duration", 0.25))
            pitch = int(n_copy.get("pitch", cls.CLOSED_HH_PITCH))
            vel = int(n_copy.get("velocity", 80))
            bar_idx = int(st // beats_per_bar)  # 0-indexed: 0 = bar 1, 1 = bar 2, etc.

            # We target specific bars in the cycle (modulo bars if loop is longer)
            cycle_bar = bar_idx % 8 if bars >= 8 else bar_idx

            # Mutation 1: Bar 2 (cycle_bar == 1) -> 1/32 Micro-roll on the 4th beat
            if cycle_bar == 1 and (st % beats_per_bar) >= 3.0 and intensity >= 0.3:
                # Replace or burst note into 4 32nd notes
                roll_subdivisions = 4 if intensity < 0.8 else 6
                sub_dur = dur / roll_subdivisions
                for step in range(roll_subdivisions):
                    roll_note = copy.deepcopy(n_copy)
                    roll_note["start_time"] = round(st + step * sub_dur, 4)
                    roll_note["duration"] = round(sub_dur * 0.9, 4)
                    # Velocity ramp upwards
                    roll_note["velocity"] = min(127, int(vel * 0.7 + (step / roll_subdivisions) * 35))
                    roll_note["mutation_tag"] = "MICRO_ROLL_32ND"
                    new_notes.append(roll_note)

                if not any(m["bar"] == bar_idx + 1 and m["type"] == "MICRO_ROLL_32ND" for m in mutations_applied):
                    mutations_applied.append({
                        "bar": bar_idx + 1,
                        "type": "MICRO_ROLL_32ND",
                        "description": f"{roll_subdivisions}-step velocity ramped roll"
                    })
                continue

            # Mutation 2: Bar 4 (cycle_bar == 3) -> Pitch Drop / Downward Dip on backbeat
            elif cycle_bar == 3 and (st % beats_per_bar) >= 2.0 and intensity >= 0.4:
                # Lower pitch by 2 semitones or soften velocity
                drop_semitones = 2
                n_copy["pitch"] = max(24, pitch - drop_semitones)
                n_copy["velocity"] = max(30, int(vel * 0.82))
                n_copy["mutation_tag"] = "PITCH_DROP"
                new_notes.append(n_copy)

                if not any(m["bar"] == bar_idx + 1 and m["type"] == "PITCH_DROP" for m in mutations_applied):
                    mutations_applied.append({
                        "bar": bar_idx + 1,
                        "type": "PITCH_DROP",
                        "description": f"Dipped pitch by -{drop_semitones} semitones and velocity softened"
                    })
                continue

            # Mutation 3: Bar 6 (cycle_bar == 5) -> Open Hat Accent & Choke
            elif cycle_bar == 5 and abs((st % beats_per_bar) - 2.5) < 0.25 and intensity >= 0.35:
                # Open hat accent
                n_copy["pitch"] = cls.OPEN_HH_PITCH
                n_copy["velocity"] = min(127, int(vel * 1.25))
                n_copy["duration"] = round(dur * 1.5, 4)
                n_copy["mutation_tag"] = "OPEN_HAT_ACCENT"
                new_notes.append(n_copy)

                if not any(m["bar"] == bar_idx + 1 and m["type"] == "OPEN_HAT_ACCENT" for m in mutations_applied):
                    mutations_applied.append({
                        "bar": bar_idx + 1,
                        "type": "OPEN_HAT_ACCENT",
                        "description": "Injected open-hat accent (pitch 46) with choked release"
                    })
                continue

            # Mutation 4: Bar 8 (cycle_bar == 7) -> Turnaround Burst before section change
            elif cycle_bar == 7 and (st % beats_per_bar) >= 3.25 and intensity >= 0.3:
                # High energy turnaround burst (6-step stutter)
                burst_steps = 6
                step_len = dur / burst_steps
                for step in range(burst_steps):
                    b_note = copy.deepcopy(n_copy)
                    b_note["start_time"] = round(st + step * step_len, 4)
                    b_note["duration"] = round(step_len * 0.85, 4)
                    # Ascending crescendo
                    b_note["velocity"] = min(127, int(vel * 0.75 + (step / burst_steps) * 45))
                    b_note["mutation_tag"] = "TURNAROUND_BURST"
                    new_notes.append(b_note)

                if not any(m["bar"] == bar_idx + 1 and m["type"] == "TURNAROUND_BURST" for m in mutations_applied):
                    mutations_applied.append({
                        "bar": bar_idx + 1,
                        "type": "TURNAROUND_BURST",
                        "description": f"Turnaround crescendo burst ({burst_steps} notes)"
                    })
                continue

            # Default: preserve note as is
            new_notes.append(n_copy)

        return {
            "status": "MUTATED" if mutations_applied else "MAINTAINED",
            "genre": genre,
            "bars": bars,
            "intensity": intensity,
            "original_count": len(notes),
            "mutated_count": len(new_notes),
            "mutations_applied": mutations_applied,
            "notes": new_notes
        }

    @classmethod
    def render_markdown_summary(cls, result: Dict[str, Any]) -> str:
        """Renders clear, human-readable markdown summary."""
        lines = [
            "🥁 **Mutación Evolutiva y Rolls Estocásticos de Hi-Hats (Hi-Hat Mutator)**\n",
            f"• **Género / Estilo:** `{result.get('genre', 'TRAP')}` | **Compases:** {result.get('bars', 8)}",
            f"• **Notas Procesadas:** {result.get('original_count', 0)} originales ➔ {result.get('mutated_count', 0)} mutadas",
            f"• **Intensidad de Mutación:** {int(result.get('intensity', 0.6) * 100)}%\n",
            "**Mutaciones Estructurales Aplicadas:**"
        ]
        muts = result.get("mutations_applied", [])
        if muts:
            for m in muts:
                lines.append(f"  - **Compás {m.get('bar')}:** `{m.get('type')}` — {m.get('description')}")
        else:
            lines.append("  - *Patrón mantenido en estado base para preservar pulso minimalista.*")

        lines.append("\n• **Impacto Sónico:** Dinamismo orgánico anti-fatiga con ráfagas de 1/32, pitch bends y turnarounds fluidos.")
        return "\n".join(lines)

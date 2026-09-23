# engine/music/groove/metric_displacement.py
"""
Off-Beat Metric Displacer Engine:
Applies rhythmic push/pull and intentional off-beat metric displacement in phrase turnarounds.
Shifts accents and downbeat attacks in bars 2 and 6 by 1/16 or 1/8 beat, creating the infectious
physical "bounce" found in top-tier Pop, Funk, Afrobeats, and Modern R&B productions.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("OffBeatMetricDisplacer")


class OffBeatMetricDisplacer:
    """
    Coordinates intentional metric displacement and syncopation shifts across arrangement bars.
    """

    ELIGIBLE_ROLES = ["BASS", "KEYS", "GUITAR", "SYNTH", "PLUCK", "PIANO", "RHODES"]

    @classmethod
    def apply_metric_displacement(
        cls,
        notes: List[Dict[str, Any]],
        role: str = "BASS",
        bars: int = 8,
        displacement_level: int = 2,
        beats_per_bar: float = 4.0
    ) -> Dict[str, Any]:
        """
        Displaces on-beat notes in bars 2 and 6 to off-beat grid positions (e.g. +0.25 or +0.50 beats),
        infusing groove bounce without harmonic collisions.
        """
        if not notes:
            return {
                "status": "EMPTY_NOTES",
                "notes": [],
                "displaced_bars": [],
                "displacement_level": displacement_level
            }

        r_up = str(role or "").upper()
        is_eligible = any(el in r_up for el in cls.ELIGIBLE_ROLES)
        if not is_eligible:
            return {
                "status": "ROLE_NOT_ELIGIBLE",
                "notes": list(notes),
                "displaced_bars": [],
                "displacement_level": displacement_level
            }

        # Displacement step sizes based on level (1 = subtle 1/16th, 5 = bold 1/8th push/pull)
        shift_beat_map = {
            1: 0.125,  # 32nd note micro-push
            2: 0.250,  # 16th note syncopation
            3: 0.250,  # 16th note syncopation with duration extension
            4: 0.375,  # Dotted 16th pull
            5: 0.500   # 8th note half-beat metric anticipation
        }
        shift_amount = shift_beat_map.get(displacement_level, 0.25)

        # Target bars 2 and 6 (0-indexed: bar 1 and bar 5)
        target_bars = [1, 5] if bars >= 8 else ([1] if bars >= 4 else [])
        displaced_bars_applied = []

        new_notes: List[Dict[str, Any]] = []
        sorted_notes = sorted(notes, key=lambda n: float(n.get("start_time", n.get("start", 0.0))))

        for idx, n in enumerate(sorted_notes):
            n_copy = dict(n)
            st = float(n_copy.get("start_time", n_copy.get("start", 0.0)))
            dur = float(n_copy.get("duration", 1.0))
            bar_idx = int(st // beats_per_bar)

            if bar_idx in target_bars:
                # Check if note is on or very close to an integer downbeat (beat 1, 2, 3, or 4 of the bar)
                beat_in_bar = st % beats_per_bar
                is_on_beat = abs(beat_in_bar - round(beat_in_bar)) < 0.08

                if is_on_beat:
                    # Displace forward into the pocket
                    new_st = round(st + shift_amount, 3)
                    # Next note boundary check to guarantee non-overlap
                    next_st = float(sorted_notes[idx + 1].get("start_time", sorted_notes[idx + 1].get("start", 999.0))) if idx + 1 < len(sorted_notes) else (bars * beats_per_bar)
                    if new_st < next_st:
                        n_copy["start_time"] = new_st
                        n_copy["duration"] = round(max(0.15, min(dur, next_st - new_st - 0.05)), 3)
                        n_copy["metric_displaced"] = True
                        if (bar_idx + 1) not in displaced_bars_applied:
                            displaced_bars_applied.append(bar_idx + 1)

            new_notes.append(n_copy)

        return {
            "status": "DISPLACED" if displaced_bars_applied else "MAINTAINED",
            "role": r_up,
            "displacement_level": displacement_level,
            "shift_beat": shift_amount,
            "displaced_bars": displaced_bars_applied,
            "note_count": len(new_notes),
            "notes": new_notes
        }

    @classmethod
    def render_markdown_summary(cls, result: Dict[str, Any]) -> str:
        """Renders clear, human-readable markdown summary."""
        bars_str = ", ".join([f"Compás {b}" for b in result.get("displaced_bars", [])]) if result.get("displaced_bars") else "Ninguno (patrón ya sincopado)"
        return (
            "🕺 **Motor de Acentos de Contratiempo y Desplazamiento Métrico (Metric Displacer)**\n\n"
            f"• **Rol Procesado:** `{result.get('role', 'BASS')}`\n"
            f"• **Nivel de Desplazamiento:** {result.get('displacement_level', 2)}/5 (Shift: {result.get('shift_beat', 0.25)} beats)\n"
            f"• **Compases con Micro-Síncopa:** {bars_str}\n"
            "• **Efecto Acústico:** Inyecta 'bounce' orgánico y relajación rítmica bailable sin alterar la tonalidad."
        )

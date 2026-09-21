# engine/creative/artistic_critic/genre_plausibility_critic.py
"""
7. Cultural / Genre Plausibility Critic:
Core Question: "¿La mezcla de géneros es coherente o es un monstruo de Frankenstein sin identidad?"

Prevents chaotic genre collisions (e.g. Boom Bap + Drill 808 slides + Ambient Pad + EDM Snare Roll).
Enforces:
  GENRE ANCHOR ➔ EXPECTED VOCABULARY ➔ DELIBERATE DEVIATIONS ➔ MAXIMUM DEVIATION BUDGET

VETO Condition:
- Incoherent stylistic collision exceeding the genre deviation budget without artistic justification.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity
from engine.creative.artistic_intent import ArtisticIntent

logger = logging.getLogger("CulturalGenrePlausibilityCritic")


class CulturalGenrePlausibilityCritic:
    """Regulates genre vocabulary and deviation budget to prevent stylistic Frankenstein abominations."""

    # Incompatible clashing tropes when combined without intentional intent
    CLASHING_TROPES = [
        {"drill_slides", "smooth_jazz_rhodes", "heavy_edm_white_noise"},
        {"trap_triplet_rolls", "ambient_drone", "polka_rhythm"},
    ]

    @classmethod
    def evaluate(
        cls,
        candidate_data: Dict[str, Any],
        intent: Optional[ArtisticIntent] = None
    ) -> CriticScore:
        genre_anchor = intent.genre_anchor if intent else candidate_data.get("genre", "neo_soul")
        elements = set(str(e).lower() for e in candidate_data.get("elements", []))
        genre_deviation = float(candidate_data.get("genre_deviation", 0.25))
        max_budget = intent.deviation_budget if intent else 0.40

        details = {
            "genre_anchor": genre_anchor,
            "detected_elements": list(elements),
            "genre_deviation": round(genre_deviation, 2),
            "max_budget": round(max_budget, 2),
        }

        # 1. Check for blatant uncurated clashing tropes
        for clash_set in cls.CLASHING_TROPES:
            matches = clash_set.intersection(elements)
            if len(matches) >= 2 and intent and intent.risk_tolerance < 0.80:
                return CriticScore(
                    dimension=CriticDimension.GENRE_PLAUSIBILITY,
                    score=0.35,
                    severity=VetoSeverity.VETO_REJECT,
                    explanation=f"VETO: Monstruo de Frankenstein detectado. Colisión estilística incoherente entre elementos incompatibles ({', '.join(matches)}).",
                    details=details
                )

        # 2. Deviation exceeds genre budget: VETO
        if genre_deviation > (max_budget + 0.30):
            return CriticScore(
                dimension=CriticDimension.GENRE_PLAUSIBILITY,
                score=0.40,
                severity=VetoSeverity.VETO_REJECT,
                explanation=f"VETO: Desviación cultural excesiva ({genre_deviation:.2f} > presupuesto {max_budget:.2f}). Se pierde el ancla del género.",
                details=details
            )

        if genre_deviation > max_budget:
            return CriticScore(
                dimension=CriticDimension.GENRE_PLAUSIBILITY,
                score=0.70,
                severity=VetoSeverity.WARNING,
                explanation=f"ADVERTENCIA: La mezcla de influencias estira el género ({genre_anchor}) al límite del presupuesto.",
                details=details
            )

        score = round(min(1.0, max(0.60, 0.95 - (genre_deviation * 0.30))), 3)
        return CriticScore(
            dimension=CriticDimension.GENRE_PLAUSIBILITY,
            score=score,
            severity=VetoSeverity.PASS,
            explanation=f"Coherencia estilística respetada para '{genre_anchor}' (Desviación controlada: {genre_deviation:.2f}).",
            details=details
        )

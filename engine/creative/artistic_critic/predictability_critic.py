# engine/creative/artistic_critic/predictability_critic.py
"""
3. Predictability Critic:
Core Question: "¿La sorpresa ocurre en el momento y proporción correctos?"

Musical Principle:
Surprise requires context. A special piece does not break every rule;
it breaks the right rule at the right moment.

Audits:
- Ratio of established pattern to sudden deviation.
- Adherence to the song's `deviation_budget`.
- Detection of Chaos (Deviation >> Budget) vs Boredom (Deviation == 0).
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity
from engine.creative.artistic_intent import ArtisticIntent

logger = logging.getLogger("PredictabilityCritic")


class PredictabilityCritic:
    """Balances pattern recognition with purposeful unexpected disruptions."""

    @classmethod
    def evaluate(
        cls,
        candidate_data: Dict[str, Any],
        intent: Optional[ArtisticIntent] = None
    ) -> CriticScore:
        expectation_strength = float(candidate_data.get("expectation_strength", 0.75))
        deviation_amount = float(candidate_data.get("deviation_amount", 0.30))
        budget = intent.deviation_budget if intent else 0.40
        has_repetitions = candidate_data.get("has_repetitions", True)

        details = {
            "expectation_strength": round(expectation_strength, 2),
            "deviation_amount": round(deviation_amount, 2),
            "deviation_budget": round(budget, 2),
        }

        # 1. Chaos VETO: Deviation far exceeds the budget
        if deviation_amount > (budget + 0.35):
            return CriticScore(
                dimension=CriticDimension.PREDICTABILITY,
                score=0.35,
                severity=VetoSeverity.VETO_REJECT,
                explanation=f"VETO: Caos musical. La desviación ({deviation_amount:.2f}) desborda el presupuesto ({budget:.2f}), rompiendo la coherencia de la obra.",
                details=details
            )

        # 2. Cliche VETO: Zero deviation when repetition occurs
        if has_repetitions and deviation_amount < 0.08:
            return CriticScore(
                dimension=CriticDimension.PREDICTABILITY,
                score=0.40,
                severity=VetoSeverity.VETO_REJECT,
                explanation="VETO: Predicibilidad robótica. Repetición idéntica sin ninguna desviación o mutación que mantenga el interés.",
                details=details
            )

        # 3. Warning if deviation is slightly high or low
        if deviation_amount > budget:
            excess = deviation_amount - budget
            score = round(max(0.60, 0.85 - excess), 3)
            return CriticScore(
                dimension=CriticDimension.PREDICTABILITY,
                score=score,
                severity=VetoSeverity.WARNING,
                explanation=f"ADVERTENCIA: Desviación ({deviation_amount:.2f}) excede ligeramente el presupuesto ({budget:.2f}). Vigilar cohesión.",
                details=details
            )

        # 4. Golden ratio of useful surprise
        # Ideal: Solid established pattern (0.7-0.9) with controlled tasteful deviation (0.2-0.4)
        useful_surprise = expectation_strength * (1.0 - abs(deviation_amount - 0.30))
        final_score = round(min(1.0, max(0.60, 0.70 + (useful_surprise * 0.25))), 3)

        return CriticScore(
            dimension=CriticDimension.PREDICTABILITY,
            score=final_score,
            severity=VetoSeverity.PASS,
            explanation=f"Sorpresa útil calibrada ({deviation_amount:.2f} desviación sobre {expectation_strength:.2f} expectativa). Ruptura justificada.",
            details=details
        )

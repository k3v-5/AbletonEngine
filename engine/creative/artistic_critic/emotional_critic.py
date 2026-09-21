# engine/creative/artistic_critic/emotional_critic.py
"""
4. Emotional Critic:
Core Question: "¿La emoción realmente cambia o solamente cambian los parámetros?"

Differentiates:
- Parameter change: numbers fluctuating in Live (density 0.4 -> 0.8 -> 0.3)
- Perceived change: actual psychoacoustic shift in tension, release, valence, and intimacy.

VETO Conditions:
- "Empty Mathematical Gymnastics": High parameter movement with near-zero perceived emotional impact.
- Severe contradiction of the `ArtisticIntent` narrative emotional journey.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity
from engine.creative.artistic_intent import ArtisticIntent

logger = logging.getLogger("EmotionalCritic")


class EmotionalCritic:
    """Evaluates psychoacoustic emotional shift vs mere parameter oscillation."""

    @classmethod
    def evaluate(
        cls,
        candidate_data: Dict[str, Any],
        intent: Optional[ArtisticIntent] = None
    ) -> CriticScore:
        param_delta = float(candidate_data.get("parameter_delta", 0.50))
        perceived_delta = float(candidate_data.get("perceived_emotional_delta", 0.45))
        emotional_coherence = float(candidate_data.get("emotional_coherence", 0.85))

        details = {
            "parameter_delta": round(param_delta, 2),
            "perceived_emotional_delta": round(perceived_delta, 2),
            "emotional_coherence": round(emotional_coherence, 2),
        }

        # 1. Empty Mathematical Gymnastics VETO:
        # Parameters move wildly, but perceived emotional feeling is dead/flat
        if param_delta > 0.55 and perceived_delta < 0.15:
            return CriticScore(
                dimension=CriticDimension.EMOTIONAL_PERCEPTION,
                score=0.30,
                severity=VetoSeverity.VETO_REJECT,
                explanation="VETO: Gimnasia matemática vacía. Los parámetros fluctúan en el DAW pero el cambio emocional percibido es plano (<0.15).",
                details=details
            )

        # 2. Intent Emotional Trajectory Contradiction VETO
        if intent:
            cand_beginning_mood = str(candidate_data.get("beginning_mood", "")).lower()
            intent_beginning = intent.listener_experience.beginning.lower()
            if "intimate" in intent_beginning or "fragile" in intent_beginning:
                if "aggressive" in cand_beginning_mood or "overwhelming" in cand_beginning_mood:
                    return CriticScore(
                        dimension=CriticDimension.EMOTIONAL_PERCEPTION,
                        score=0.35,
                        severity=VetoSeverity.VETO_REJECT,
                        explanation=f"VETO: Contradicción narrativa. La introducción es agresiva/abrumadora cuando el ArtisticIntent exige '{intent.listener_experience.beginning}'.",
                        details=details
                    )

        # 3. Ratio between perceived and parameter change
        # Ideal: High perceived change achieved with focused, deliberate parameter adjustments
        ratio = perceived_delta / max(0.1, param_delta)
        efficiency_bonus = min(0.20, ratio * 0.12)
        base = (perceived_delta * 0.50) + (emotional_coherence * 0.45)
        final_score = round(min(1.0, max(0.50, base + efficiency_bonus)), 3)

        if final_score < 0.65:
            return CriticScore(
                dimension=CriticDimension.EMOTIONAL_PERCEPTION,
                score=final_score,
                severity=VetoSeverity.WARNING,
                explanation="ADVERTENCIA: La curva emocional es tibia o muestra desconexión entre dinámica y armonía.",
                details=details
            )

        return CriticScore(
            dimension=CriticDimension.EMOTIONAL_PERCEPTION,
            score=final_score,
            severity=VetoSeverity.PASS,
            explanation=f"Impacto emocional auténtico (Delta percibido: {perceived_delta:.2f}, coherencia: {emotional_coherence:.2f}).",
            details=details
        )

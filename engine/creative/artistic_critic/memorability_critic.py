# engine/creative/artistic_critic/memorability_critic.py
"""
2. Memorability Critic:
Core Question: "¿Qué queda en la cabeza después de que desaparece la canción?"

Audits:
- Recognizable motif hook
- Distinctive signature rhythmic pocket
- Signature ear candy or sound design artifact
- Signature vocal gesture / chop
- Unforgettable structural transition or silence

The Law of Memorability:
A great piece requires exactly ONE or TWO high-memorability events.
- 0 events = VETO: Flat, sterile, forgettable.
- >4 competing hooks = VETO: Cognitive overload, hooks cancel each other out.
- 1-2 events = EXCELLENT: Clean auditory retention.
"""
from __future__ import annotations
from typing import Dict, List, Any
import logging

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity

logger = logging.getLogger("MemorabilityCritic")


class MemorabilityCritic:
    """Enforces the rule of 1-2 iconic memorable events per musical work."""

    @classmethod
    def evaluate(cls, candidate_data: Dict[str, Any]) -> CriticScore:
        memorable_events = candidate_data.get("memorable_events", [])
        if not isinstance(memorable_events, list):
            memorable_events = []

        # Auto-detect memorable events from candidate properties if not explicitly tagged
        detected_events = list(memorable_events)
        if candidate_data.get("has_signature_gesture") and "signature_gesture" not in detected_events:
            detected_events.append("signature_gesture")
        if candidate_data.get("has_primary_motif") and "primary_motif" not in detected_events:
            detected_events.append("primary_motif")
        if candidate_data.get("rhythmic_vacuum_drop") and "rhythmic_vacuum" not in detected_events:
            detected_events.append("rhythmic_vacuum")
        if candidate_data.get("vocal_hook_chop") and "vocal_hook_chop" not in detected_events:
            detected_events.append("vocal_hook_chop")

        count = len(detected_events)

        details = {
            "event_count": count,
            "detected_events": detected_events,
            "optimal_range": [1, 2],
        }

        # 1. Zero memorable events: Fatal flaw
        if count == 0:
            return CriticScore(
                dimension=CriticDimension.MEMORABILITY,
                score=0.25,
                severity=VetoSeverity.VETO_REJECT,
                explanation="VETO: Canción plana y olvidable. Carece de cualquier evento o gancho memorable que permanezca en la mente del oyente.",
                details=details
            )

        # 2. Cognitive saturation: More than 4 competing hooks
        if count > 4:
            return CriticScore(
                dimension=CriticDimension.MEMORABILITY,
                score=0.45,
                severity=VetoSeverity.VETO_REJECT,
                explanation=f"VETO: Saturación cognitiva ({count} ganchos compitiendo). Los ganchos se cancelan mutuamente; reduce a 1 o 2 eventos principales.",
                details=details
            )

        # 3. 3 or 4 events: Warning
        if count in (3, 4):
            return CriticScore(
                dimension=CriticDimension.MEMORABILITY,
                score=0.72,
                severity=VetoSeverity.WARNING,
                explanation=f"ADVERTENCIA: {count} eventos memorables detectados. Podría beneficiarse de enfocar la atención en 1 o 2 ganchos cardinales.",
                details=details
            )

        # 4. Ideal range: 1 or 2 events
        score = 0.95 if count == 2 else 0.88
        return CriticScore(
            dimension=CriticDimension.MEMORABILITY,
            score=score,
            severity=VetoSeverity.PASS,
            explanation=f"Memorabilidad óptima ({count} eventos clave: {', '.join(detected_events)}). Retención auditiva máxima sin saturación.",
            details=details
        )

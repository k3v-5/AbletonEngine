# engine/creative/artistic_critic/human_plausibility_critic.py
"""
5. Human Plausibility Critic:
Core Question: "¿Parece que alguien tomó decisiones o que fue generada por una máquina?"

Hunts for the signature: "esto fue generado por una máquina":
- Excessively perfect repetition and rigid mathematical symmetry.
- Flat velocity distribution (std dev < 5) or mechanical step LFOs.
- Automations without intention (e.g. arbitrary linear filter sweeps every 8 bars).
- Formulaic drum fills occurring solely on clock boundaries.
- Microtiming disconnected from physical pocket and groove.

VETO Condition:
- `machine_signature_score > 0.70` = Discard immediately.
"""
from __future__ import annotations
from typing import Dict, Any, List
import logging
import math

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity

logger = logging.getLogger("HumanPlausibilityCritic")


class HumanPlausibilityCritic:
    """Detects robotic and algorithmic artifacts, demanding intentional human-like decision making."""

    @classmethod
    def evaluate(cls, candidate_data: Dict[str, Any]) -> CriticScore:
        # 1. Analyze velocity dynamics
        velocities = candidate_data.get("sample_velocities", [])
        velocity_std_dev = 14.0
        if velocities and len(velocities) >= 4:
            mean = sum(velocities) / len(velocities)
            variance = sum((v - mean) ** 2 for v in velocities) / len(velocities)
            velocity_std_dev = math.sqrt(variance)

        # 2. Check symmetry and robotic indicators
        is_perfectly_symmetric = bool(candidate_data.get("rigid_symmetry", False))
        automations_without_intention = bool(candidate_data.get("unintentional_automation", False))
        mechanical_clock_fills = bool(candidate_data.get("clock_boundary_fills_only", False))
        groove_pocket_affinity = float(candidate_data.get("groove_pocket_affinity", 0.85))

        # Calculate Machine Signature Score (0.0 = completely human, 1.0 = obvious robot)
        machine_score = 0.0

        if velocity_std_dev < 5.0:
            machine_score += 0.35  # Flat, robotic velocities
        elif velocity_std_dev < 8.0:
            machine_score += 0.15

        if is_perfectly_symmetric:
            machine_score += 0.30

        if automations_without_intention:
            machine_score += 0.25

        if mechanical_clock_fills:
            machine_score += 0.20

        if groove_pocket_affinity < 0.50:
            machine_score += 0.20

        machine_score = round(min(1.0, machine_score), 2)
        human_score = round(max(0.0, 1.0 - machine_score), 3)

        details = {
            "machine_signature_score": machine_score,
            "human_plausibility_score": human_score,
            "velocity_std_dev": round(velocity_std_dev, 2),
            "is_perfectly_symmetric": is_perfectly_symmetric,
            "automations_without_intention": automations_without_intention,
        }

        # VETO: Blatant machine generation
        if machine_score >= 0.70:
            reasons = []
            if velocity_std_dev < 5.0:
                reasons.append("velocities planas/mecánicas (StdDev < 5)")
            if is_perfectly_symmetric:
                reasons.append("simetría algorítmica sospechosa")
            if automations_without_intention:
                reasons.append("automatizaciones lineales sin intención")
            return CriticScore(
                dimension=CriticDimension.HUMAN_PLAUSIBILITY,
                score=human_score,
                severity=VetoSeverity.VETO_REJECT,
                explanation=f"VETO: Firma de máquina evidente ({', '.join(reasons)}). La obra parece ensamblada por un algoritmo sin intención humana.",
                details=details
            )

        if machine_score >= 0.40:
            return CriticScore(
                dimension=CriticDimension.HUMAN_PLAUSIBILITY,
                score=human_score,
                severity=VetoSeverity.WARNING,
                explanation="ADVERTENCIA: Ciertos elementos muestran rigidez matemática en microtiming o dinámicas.",
                details=details
            )

        return CriticScore(
            dimension=CriticDimension.HUMAN_PLAUSIBILITY,
            score=human_score,
            severity=VetoSeverity.PASS,
            explanation=f"Sensación de autoría humana ({human_score:.2f}). Decisiones orgánicas de fraseo, dinámicas y pausas.",
            details=details
        )

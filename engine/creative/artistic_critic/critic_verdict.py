# engine/creative/artistic_critic/critic_verdict.py
"""
Artistic Critic Verdict & Score Models:
Data structures representing the evaluations, scores, warnings, and absolute vetos
emitted by the 7 independent perspectives of the Artistic Critic Engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class CriticDimension(str, Enum):
    IDENTITY = "identity"
    MEMORABILITY = "memorability"
    PREDICTABILITY = "predictability"
    EMOTIONAL_PERCEPTION = "emotional_perception"
    HUMAN_PLAUSIBILITY = "human_plausibility"
    SONIC_SIGNATURE = "sonic_signature"
    GENRE_PLAUSIBILITY = "genre_plausibility"


class VetoSeverity(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    VETO_REJECT = "veto_reject"


@dataclass
class CriticScore:
    """Individual score and diagnosis from one of the 7 critics."""
    dimension: CriticDimension
    score: float                         # 0.0 to 1.0
    severity: VetoSeverity = VetoSeverity.PASS
    explanation: str = "Passed artistic criteria."
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_veto(self) -> bool:
        return self.severity == VetoSeverity.VETO_REJECT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 3),
            "severity": self.severity.value,
            "explanation": self.explanation,
            "details": self.details,
        }


@dataclass
class CriticVerdict:
    """
    Holistic adjudication by the full Artistic Critic Engine.
    Determines whether a candidate is accepted for DAW production or rejected for mutation.
    """
    candidate_id: str
    passed: bool
    overall_artistic_score: float
    scores: Dict[CriticDimension, CriticScore] = field(default_factory=dict)
    vetos: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    feedback_for_mutation: List[str] = field(default_factory=list)

    @property
    def has_veto(self) -> bool:
        return len(self.vetos) > 0 or any(s.is_veto for s in self.scores.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "passed": self.passed,
            "overall_artistic_score": round(self.overall_artistic_score, 3),
            "scores": {dim.value: score.to_dict() for dim, score in self.scores.items()},
            "vetos": list(self.vetos),
            "warnings": list(self.warnings),
            "feedback_for_mutation": list(self.feedback_for_mutation),
        }

    def format_markdown_verdict(self) -> str:
        status_icon = "✅ ACEPTADO PARA PRODUCCIÓN" if self.passed else "❌ RECHAZADO POR EL TRIBUNAL ARTÍSTICO"
        lines = [
            f"### ⚖️ Veredicto Crítico: {status_icon} (Puntaje: `{self.overall_artistic_score:.2f}`)",
            f"**Candidato:** `{self.candidate_id}` | **Vetos Activos:** `{len(self.vetos)}`\n",
            "| Dimensión Crítica | Score | Estado | Diagnóstico |",
            "|---|---|---|---|"
        ]
        for dim, s in self.scores.items():
            icon = "✅" if s.severity == VetoSeverity.PASS else ("⚠️" if s.severity == VetoSeverity.WARNING else "⛔ VETO")
            lines.append(f"| **{dim.value.replace('_', ' ').title()}** | `{s.score:.2f}` | {icon} | {s.explanation} |")

        if self.vetos:
            lines.append("\n#### ⛔ Motivos de Veto y Destrucción:")
            for v in self.vetos:
                lines.append(f"- **VETO:** {v}")

        if self.feedback_for_mutation:
            lines.append("\n#### 🧬 Instrucciones de Mutación para el Motor:")
            for fb in self.feedback_for_mutation:
                lines.append(f"- 💡 {fb}")

        return "\n".join(lines)

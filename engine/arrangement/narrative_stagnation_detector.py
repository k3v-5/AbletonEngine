# engine/arrangement/narrative_stagnation_detector.py
"""
Narrative Stagnation Detector (Level L - Emotional Arc):
Audits the arrangement to detect static, uncreative repetitions between sections.

Enforces the artistic mandate:
"El segundo Hook no puede ser simplemente el primer Hook con más volumen.
Cada repetición debe aportar nueva información emocional, armónica o textural."
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

from .emotional_arc_engine import SectionEmotionalProfile, EmotionalArcEngine

logger = logging.getLogger("NarrativeStagnationDetector")


@dataclass
class StagnationIssue:
    """A detected instance of narrative stagnation between two analogous sections."""
    section_a_name: str
    section_b_name: str
    novelty_score: float              # 0.0 (identical duplicate) to 1.0 (radical contrast)
    threshold: float                  # Minimum acceptable novelty (e.g. 0.25)
    is_stagnant: bool
    diagnosis: str
    suggested_interventions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_a_name": self.section_a_name,
            "section_b_name": self.section_b_name,
            "novelty_score": round(self.novelty_score, 2),
            "threshold": self.threshold,
            "is_stagnant": self.is_stagnant,
            "diagnosis": self.diagnosis,
            "suggested_interventions": list(self.suggested_interventions),
        }


@dataclass
class StagnationAuditReport:
    """Master report of the arrangement's narrative evolution."""
    total_comparisons: int
    stagnant_count: int
    is_arrangement_dynamic: bool
    overall_evolution_index: float    # 0.0 to 1.0
    issues: List[StagnationIssue] = field(default_factory=list)
    verdict: str = "PENDING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_comparisons": self.total_comparisons,
            "stagnant_count": self.stagnant_count,
            "is_arrangement_dynamic": self.is_arrangement_dynamic,
            "overall_evolution_index": round(self.overall_evolution_index, 2),
            "issues": [i.to_dict() for i in self.issues],
            "verdict": self.verdict,
        }


class NarrativeStagnationDetector:
    """
    Scans pairs of analogous sections (Hook 1 ↔ Hook 2, Verse 1 ↔ Verse 2)
    and verifies that the piece maintains developmental narrative momentum.
    """

    MIN_ACCEPTABLE_NOVELTY = 0.20  # At least 20% emotional delta required between repeats

    @classmethod
    def compare_sections(
        cls,
        sec_a: SectionEmotionalProfile,
        sec_b: SectionEmotionalProfile,
        threshold: float = MIN_ACCEPTABLE_NOVELTY
    ) -> StagnationIssue:
        """
        Calculates emotional difference and diagnoses narrative stagnation.
        """
        novelty = EmotionalArcEngine.compute_novelty_distance(sec_a, sec_b)
        is_stagnant = novelty < threshold

        if is_stagnant:
            diagnosis = (
                f"Alerta de Estancamiento Narrativo: '{sec_b.section_name}' solo aporta un {int(novelty * 100)}% "
                f"de novedad frente a '{sec_a.section_name}' (umbral requerido: {int(threshold * 100)}%)."
            )
            interventions = [
                "Variación Rítmica: silenciar el bombo/caja en los compases 1–2 de la repetición para crear anticipación.",
                "Mutación de Motivo: aplicar inversión interválica o desplazamiento métrico en la melodía.",
                "Evolución Tímbrica: introducir un contracanto o elevar la apertura estéreo (Utility Width +20%).",
                "Dinámica de Capas: agregar percusión secundaria o un pad atmosférico sutil."
            ]
        else:
            diagnosis = (
                f"Evolución Saludable: '{sec_b.section_name}' aporta un {int(novelty * 100)}% "
                f"de contraste y nueva información respecto a '{sec_a.section_name}'."
            )
            interventions = []

        return StagnationIssue(
            section_a_name=sec_a.section_name,
            section_b_name=sec_b.section_name,
            novelty_score=novelty,
            threshold=threshold,
            is_stagnant=is_stagnant,
            diagnosis=diagnosis,
            suggested_interventions=interventions,
        )

    @classmethod
    def audit_arrangement_timeline(
        cls,
        profiles: List[SectionEmotionalProfile],
        threshold: float = MIN_ACCEPTABLE_NOVELTY
    ) -> StagnationAuditReport:
        """
        Audits all analogous section pairs in the arrangement timeline.
        """
        issues: List[StagnationIssue] = []

        # Find repeating hooks
        hooks = [p for p in profiles if "hook" in p.section_name.lower() or "chorus" in p.section_name.lower()]
        verses = [p for p in profiles if "verse" in p.section_name.lower()]

        # Compare successive hooks
        for i in range(len(hooks) - 1):
            issue = cls.compare_sections(hooks[i], hooks[i + 1], threshold=threshold)
            issues.append(issue)

        # Compare successive verses
        for i in range(len(verses) - 1):
            issue = cls.compare_sections(verses[i], verses[i + 1], threshold=threshold)
            issues.append(issue)

        total = len(issues)
        stagnant_count = sum(1 for iss in issues if iss.is_stagnant)
        is_dynamic = stagnant_count == 0 if total > 0 else True

        overall_novelty = sum(iss.novelty_score for iss in issues) / max(1, total) if total > 0 else 1.0

        if is_dynamic:
            verdict = "NARRATIVELY_DYNAMIC"
        elif stagnant_count <= 1:
            verdict = "ACCEPTABLE_NEEDS_MINOR_VARIATION"
        else:
            verdict = "STAGNANT_REPETITION_DETECTED"

        return StagnationAuditReport(
            total_comparisons=total,
            stagnant_count=stagnant_count,
            is_arrangement_dynamic=is_dynamic,
            overall_evolution_index=overall_novelty,
            issues=issues,
            verdict=verdict,
        )

# engine/arrangement/intelligence/arrangement_intelligence_engine.py
"""
Arrangement Intelligence Engine (Level J - Arrangement Intelligence):
The central intelligence engine that analyzes, plans, and audits the dynamic
development of the complete musical work.

Guarantees that:
1. Every repeating section brings fresh developmental information.
2. Layers and densities modulate intentionally to tell an emotional story.
3. Pre-drop silences and structural anticipations are woven into key boundaries.
4. The song possesses an overarching narrative arc rather than repetitive loops.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import logging

from .layer_orchestrator import LayerOrchestrator, LayerOrchestrationPlan
from .anticipation_and_silence_weaver import AnticipationAndSilenceWeaver, AnticipationEvent
from ..emotional_arc_engine import EmotionalArcEngine, SectionEmotionalProfile
from ..narrative_stagnation_detector import NarrativeStagnationDetector, StagnationAuditReport

logger = logging.getLogger("ArrangementIntelligenceEngine")


@dataclass
class ArrangementIntelligenceAuditReport:
    """Master audit report of the arrangement's structural and narrative intelligence."""
    song_id: str
    evolution_score: float              # 0.0 to 1.0
    layer_plan: LayerOrchestrationPlan
    emotional_profiles: List[SectionEmotionalProfile]
    anticipations: List[AnticipationEvent]
    stagnation_audit: StagnationAuditReport
    is_development_complete: bool
    verdict: str
    producer_dilemmas: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "evolution_score": round(self.evolution_score, 2),
            "layer_plan": self.layer_plan.to_dict(),
            "emotional_profiles": [p.to_dict() for p in self.emotional_profiles],
            "anticipations": [a.to_dict() for a in self.anticipations],
            "stagnation_audit": self.stagnation_audit.to_dict(),
            "is_development_complete": self.is_development_complete,
            "verdict": self.verdict,
            "producer_dilemmas": list(self.producer_dilemmas),
        }


class ArrangementIntelligenceEngine:
    """
    Orchestrates the entire Level J arrangement intelligence pipeline.
    """

    @classmethod
    def analyze_and_orchestrate(
        cls,
        sections: List[Dict[str, Any]],
        available_roles: Optional[Set[str]] = None,
        song_id: str = "default_song"
    ) -> ArrangementIntelligenceAuditReport:
        """
        Executes full arrangement analysis, builds layer plans, weaves silences,
        computes the 9D emotional arc, and audits against narrative stagnation.
        """
        # 1. Generate Sectional Layer Orchestration
        layer_plan = LayerOrchestrator.generate_orchestration_plan(
            sections=sections,
            available_roles=available_roles,
            song_id=song_id
        )

        # 2. Weave Anticipations and Pre-Drop Silences
        anticipations = AnticipationAndSilenceWeaver.weave_anticipations(sections)

        # 3. Build 9D Emotional Arc Profiles
        emotional_profiles = EmotionalArcEngine.build_narrative_arc(sections)

        # 4. Audit Narrative Stagnation
        stagnation_report = NarrativeStagnationDetector.audit_arrangement_timeline(emotional_profiles)

        # 5. Compute Overall Evolution Score
        # Factor 1: Stagnation novelty fulfillment against target threshold (40%)
        # Factor 2: Dynamic layer contrast across sections (30%)
        # Factor 3: Presence of structural anticipation events (30%)
        target_novelty = NarrativeStagnationDetector.MIN_ACCEPTABLE_NOVELTY
        novelty_fulfillment = min(1.0, stagnation_report.overall_evolution_index / target_novelty) if target_novelty > 0 else 1.0
        anticipation_factor = min(1.0, len(anticipations) / 2.0)
        layer_contrast_factor = 1.0 if len(layer_plan.section_plans) >= 4 else 0.6
        evol_score = (
            novelty_fulfillment * 0.40 +
            layer_contrast_factor * 0.30 +
            anticipation_factor * 0.30
        )
        evol_score = round(min(1.0, max(0.0, evol_score)), 2)

        is_complete = evol_score >= 0.70 and stagnation_report.is_arrangement_dynamic

        # 6. Formulate Actionable Producer Dilemmas for any issues
        dilemmas: List[Dict[str, Any]] = []
        for issue in stagnation_report.issues:
            if issue.is_stagnant:
                dilemmas.append({
                    "type": "STAGNATION_RESOLVE",
                    "title": f"Diferenciar '{issue.section_b_name}' de '{issue.section_a_name}'",
                    "diagnosis": issue.diagnosis,
                    "proposals": issue.suggested_interventions,
                })

        verdict = (
            "DYNAMIC_NARRATIVE_DEVELOPMENT" if is_complete
            else ("ACCEPTABLE_MINOR_REPETITION" if evol_score >= 0.50 else "STATIC_ARRANGEMENT_STAGNATION")
        )

        return ArrangementIntelligenceAuditReport(
            song_id=song_id,
            evolution_score=evol_score,
            layer_plan=layer_plan,
            emotional_profiles=emotional_profiles,
            anticipations=anticipations,
            stagnation_audit=stagnation_report,
            is_development_complete=is_complete,
            verdict=verdict,
            producer_dilemmas=dilemmas,
        )

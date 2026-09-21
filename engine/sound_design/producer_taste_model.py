# engine/sound_design/producer_taste_model.py
"""
Producer Taste Model (Gen 2):
Replaces blind loudness or generic quality metrics with a 7-dimensional
perceptual model of artistic identity:
1. Originality         (Distance from generic factory presets)
2. Coherence           (Genetic loyalty to the song's SonicDNA)
3. Memorability        (Stickiness and auditory footprint)
4. Contrast            (Dynamic distance from the clean acoustic state)
5. Source Relationship (Traceability to its autogenous ancestor)
6. Narrative Relevance (Structural purpose in the song's emotional arc)
7. Reusability         (Viability across multiple sections without fatigue)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

from .sonic_dna import SonicDNA

logger = logging.getLogger("ProducerTasteModel")


@dataclass
class TasteMetrics:
    """The 7 perceptual axes defining sonic identity value."""
    originality: float = 0.85          # 0.0 (generic preset) to 1.0 (unmistakable)
    coherence: float = 0.90            # 0.0 (alien collision) to 1.0 (perfect DNA match)
    memorability: float = 0.88         # 0.0 (forgettable background noise) to 1.0 (earworm gesture)
    contrast: float = 0.80             # 0.0 (no perceptible change) to 1.0 (radical timbral shift)
    source_relationship: float = 0.85  # 0.0 (disconnected sample) to 1.0 (audibly derived)
    narrative_relevance: float = 0.92  # 0.0 (gratuitous plugin flex) to 1.0 (vital story transition)
    reusability: float = 0.78          # 0.0 (one-hit gimmick) to 1.0 (reappears in varied forms)

    @property
    def composite_identity_score(self) -> float:
        """
        Weighted calculation prioritizing Coherence, Memorability, and Narrative Relevance.
        """
        weights = {
            "coherence": 0.20,
            "memorability": 0.20,
            "narrative_relevance": 0.20,
            "originality": 0.15,
            "contrast": 0.10,
            "source_relationship": 0.10,
            "reusability": 0.05,
        }
        return (
            (self.coherence * weights["coherence"]) +
            (self.memorability * weights["memorability"]) +
            (self.narrative_relevance * weights["narrative_relevance"]) +
            (self.originality * weights["originality"]) +
            (self.contrast * weights["contrast"]) +
            (self.source_relationship * weights["source_relationship"]) +
            (self.reusability * weights["reusability"])
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "originality": round(self.originality, 2),
            "coherence": round(self.coherence, 2),
            "memorability": round(self.memorability, 2),
            "contrast": round(self.contrast, 2),
            "source_relationship": round(self.source_relationship, 2),
            "narrative_relevance": round(self.narrative_relevance, 2),
            "reusability": round(self.reusability, 2),
            "composite_identity_score": round(self.composite_identity_score, 3),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TasteMetrics:
        return cls(
            originality=float(data.get("originality", 0.85)),
            coherence=float(data.get("coherence", 0.90)),
            memorability=float(data.get("memorability", 0.88)),
            contrast=float(data.get("contrast", 0.80)),
            source_relationship=float(data.get("source_relationship", 0.85)),
            narrative_relevance=float(data.get("narrative_relevance", 0.92)),
            reusability=float(data.get("reusability", 0.78)),
        )


@dataclass
class ProducerTasteEvaluation:
    """An artistic evaluation report for a candidate sound."""
    candidate_id: str
    name: str
    metrics: TasteMetrics
    artistic_justification: str
    verdict: str  # EXCEPTIONAL_IDENTITY, COHERENT_CONTRIBUTION, MARGINAL_VALUE, REJECTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "metrics": self.metrics.to_dict(),
            "artistic_justification": self.artistic_justification,
            "verdict": self.verdict,
        }


class ProducerTasteModel:
    """
    Evaluates candidate transformations to ensure they make the song more recognizable.
    """

    MIN_IDENTITY_SCORE_THRESHOLD = 0.70

    @classmethod
    def evaluate_candidate(
        cls,
        candidate_id: str,
        name: str,
        source_desc: str,
        mutation_desc: str,
        target_section: str,
        sonic_dna: SonicDNA
    ) -> ProducerTasteEvaluation:
        """
        Assesses candidate gesture against SonicDNA and section context.
        """
        # Calculate coherence with DNA
        is_source_in_dna, _ = sonic_dna.validate_mutation_compatibility("SIGNATURE", source_desc)
        coherence = 0.95 if is_source_in_dna else 0.40

        # Calculate originality and memorability based on transform depth
        m_lower = mutation_desc.lower()
        originality = 0.90 if any(k in m_lower for k in ["reverse", "stretch", "spectral", "shimmer", "12-bit"]) else 0.65
        memorability = 0.88 if ("bridge" in target_section.lower() or "hook" in target_section.lower()) else 0.70
        contrast = 0.85 if ("reverse" in m_lower or "stretch" in m_lower or "distortion" in m_lower) else 0.60
        source_rel = 0.90 if is_source_in_dna else 0.30
        narrative_rel = 0.92 if ("bridge" in target_section.lower() or "pre-drop" in m_lower) else 0.75
        reusability = 0.80

        metrics = TasteMetrics(
            originality=originality,
            coherence=coherence,
            memorability=memorability,
            contrast=contrast,
            source_relationship=source_rel,
            narrative_relevance=narrative_rel,
            reusability=reusability,
        )

        score = metrics.composite_identity_score
        if score >= 0.85:
            verdict = "EXCEPTIONAL_IDENTITY"
            justification = f"El sonido aporta personalidad inconfundible y desciende con fidelidad del Sonic DNA ({source_desc})."
        elif score >= cls.MIN_IDENTITY_SCORE_THRESHOLD:
            verdict = "COHERENT_CONTRIBUTION"
            justification = "Contribución sonora sólida que respeta el universo estético sin invadir la mezcla."
        else:
            verdict = "REJECTED"
            justification = "Rechazado: bajo índice de identidad sonora o débil relación con el ADN del tema."

        return ProducerTasteEvaluation(
            candidate_id=candidate_id,
            name=name,
            metrics=metrics,
            artistic_justification=justification,
            verdict=verdict,
        )

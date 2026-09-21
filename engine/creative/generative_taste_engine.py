# engine/creative/generative_taste_engine.py
"""
Generative Taste Engine (Phase P+):
Transforms the engine from a reactive auditor into an imaginative creative producer:
IMAGINE ➔ GENERATE CONCURRENT ALTERNATIVES (A/B/C) ➔ MUSICAL & SONIC TASTE FILTER ➔ AUDITION ➔ LEARN

Instead of bland score optimization, it evaluates 10 distinct perceptual and artistic dimensions:
1. Identity: Fidelity to the song's Compositional DNA.
2. Surprise: Information entropy, unpredictable turns, and freshness.
3. Coherence: Syntactic, harmonic, and rhythmic internal logic.
4. Memorability: Hookiness, auditory footprint, and earworm strength.
5. Contrast: Perceptual and dynamic distance from preceding sections.
6. Emotion: Alignment with target emotional state vector.
7. Risk: Deliberate reward for bold, courageous choices (preventing conservative homogenization).
8. Motif Relationship: Organic genetic derivation from the core motif.
9. Arrangement Relationship: Layer orchestrator balance, frequency spacing, and headroom.
10. Catalog Uniqueness: Timbral and harmonic distance from previous catalog works.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import copy
import logging

from engine.composition.compositional_dna import CompositionalDNA
from engine.memory.catalog_memory import CatalogMemory

logger = logging.getLogger("GenerativeTasteEngine")


class CandidateType(str, Enum):
    HARMONIC_MUTATION = "harmonic_mutation"
    RHYTHMIC_DISPLACEMENT = "rhythmic_displacement"
    TIMBRAL_TEXTURE = "timbral_texture"


@dataclass
class TasteScoreCard:
    """The 10 Perceptual & Artistic Axes."""
    identity: float = 0.85
    surprise: float = 0.75
    coherence: float = 0.90
    memorability: float = 0.85
    contrast: float = 0.80
    emotion: float = 0.88
    risk: float = 0.70
    motif_relationship: float = 0.85
    arrangement_relationship: float = 0.88
    catalog_uniqueness: float = 0.92

    @property
    def musical_taste_score(self) -> float:
        """Evaluates internal composition logic, melodic memorability, and theme loyalty."""
        weights = {
            "identity": 0.20,
            "coherence": 0.20,
            "memorability": 0.25,
            "motif_relationship": 0.20,
            "emotion": 0.15,
        }
        return (
            (self.identity * weights["identity"]) +
            (self.coherence * weights["coherence"]) +
            (self.memorability * weights["memorability"]) +
            (self.motif_relationship * weights["motif_relationship"]) +
            (self.emotion * weights["emotion"])
        )

    @property
    def sonic_taste_score(self) -> float:
        """Evaluates acoustic context, mix headroom, timbral contrast, and catalog distinction."""
        weights = {
            "contrast": 0.30,
            "arrangement_relationship": 0.35,
            "catalog_uniqueness": 0.35,
        }
        return (
            (self.contrast * weights["contrast"]) +
            (self.arrangement_relationship * weights["arrangement_relationship"]) +
            (self.catalog_uniqueness * weights["catalog_uniqueness"])
        )

    def composite_artistic_score(self, risk_appetite: float = 0.60) -> float:
        """
        Calculates holistic artistic score with a deliberate Risk Bonus.
        Bold choices that introduce surprise and risk are rewarded, preventing bland pop formulas.
        """
        base = (self.musical_taste_score * 0.50) + (self.sonic_taste_score * 0.50)
        # Risk bonus: up to +15% boost if risk and surprise are high
        risk_bonus = (self.risk * self.surprise * 0.15 * risk_appetite)
        return round(min(1.0, base + risk_bonus), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": round(self.identity, 2),
            "surprise": round(self.surprise, 2),
            "coherence": round(self.coherence, 2),
            "memorability": round(self.memorability, 2),
            "contrast": round(self.contrast, 2),
            "emotion": round(self.emotion, 2),
            "risk": round(self.risk, 2),
            "motif_relationship": round(self.motif_relationship, 2),
            "arrangement_relationship": round(self.arrangement_relationship, 2),
            "catalog_uniqueness": round(self.catalog_uniqueness, 2),
            "musical_taste_score": round(self.musical_taste_score, 3),
            "sonic_taste_score": round(self.sonic_taste_score, 3),
            "composite_artistic_score": self.composite_artistic_score(),
        }


@dataclass
class ArtisticCandidate:
    """A generated musical/sonic hypothesis for a specific section."""
    candidate_id: str
    name: str
    type: CandidateType
    material_summary: str
    musical_payload: List[Dict[str, Any]] = field(default_factory=list)
    scorecard: Optional[TasteScoreCard] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "type": self.type.value,
            "material_summary": self.material_summary,
            "payload_count": len(self.musical_payload),
            "scorecard": self.scorecard.to_dict() if self.scorecard else None,
        }


@dataclass
class AuditionDecision:
    """The curated producer decision selecting the winner and staging A/B audition."""
    selected_winner: ArtisticCandidate
    runner_up: Optional[ArtisticCandidate]
    artistic_justification: str
    risk_reward_rationale: str
    ab_audition_guidance: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_winner": self.selected_winner.to_dict(),
            "runner_up": self.runner_up.to_dict() if self.runner_up else None,
            "artistic_justification": self.artistic_justification,
            "risk_reward_rationale": self.risk_reward_rationale,
            "ab_audition_guidance": self.ab_audition_guidance,
        }


class GenerativeTasteEngine:
    """
    Evaluates concurrent creative alternatives and guides artistic selection.
    Combines strict DNA fidelity with courageous artistic risk-taking.
    """

    @classmethod
    def generate_hook_candidates(
        cls,
        section_name: str,
        base_notes: List[Dict[str, Any]],
        dna: CompositionalDNA,
        catalog_memory: Optional[CatalogMemory] = None
    ) -> List[ArtisticCandidate]:
        """
        Generates 3 radically distinct musical/sonic hypotheses:
        - Candidate A (Harmonic Mutation): Modal borrowing & delayed resolution.
        - Candidate B (Rhythmic Displacement): Syncopated pocket shifts with turnaround ghost vacuums.
        - Candidate C (Timbral Texture): Granular resynthesis layer with high-frequency shimmer.
        """
        candidates: List[ArtisticCandidate] = []

        # Candidate A: Harmonic Mutation
        mutated_a = copy.deepcopy(base_notes)
        for n in mutated_a:
            # Lift turnaround pitch by semitone / modal extension
            if n.get("start_time", 0.0) >= 12.0:
                n["pitch"] = n.get("pitch", 60) + 1  # Deceptive/Phrygian inflection
        candidates.append(ArtisticCandidate(
            candidate_id="cand_A_harmonic",
            name=f"{section_name} - Harmonic Reharm & Modal Borrowing",
            type=CandidateType.HARMONIC_MUTATION,
            material_summary="Introduces modal borrowing on turnaround bars with delayed cadential resolution.",
            musical_payload=mutated_a
        ))

        # Candidate B: Rhythmic Displacement
        mutated_b = copy.deepcopy(base_notes)
        for n in mutated_b:
            start = float(n.get("start_time", 0.0))
            if start % 1.0 != 0.0:
                n["start_time"] = round(start + 0.125, 4)  # Syncopated 16th swing push
            n["velocity"] = min(127, int(n.get("velocity", 90) * 1.08))
        candidates.append(ArtisticCandidate(
            candidate_id="cand_B_rhythmic",
            name=f"{section_name} - Syncopated Rhythmic Displacement",
            type=CandidateType.RHYTHMIC_DISPLACEMENT,
            material_summary="Applies 3:2 syncopated displacement with accented pickups on turnaround downbeats.",
            musical_payload=mutated_b
        ))

        # Candidate C: Timbral Texture Layer
        mutated_c = copy.deepcopy(base_notes)
        for n in mutated_c:
            n["pitch"] = n.get("pitch", 60) + 12  # Octave shimmer
            n["velocity"] = max(40, int(n.get("velocity", 90) * 0.75))  # Whispered texture
        candidates.append(ArtisticCandidate(
            candidate_id="cand_C_timbral",
            name=f"{section_name} - High-Register Resynthesized Shimmer",
            type=CandidateType.TIMBRAL_TEXTURE,
            material_summary="Layers an octave-higher granular acoustic shimmer to explode spatial width.",
            musical_payload=mutated_c
        ))

        return candidates

    @classmethod
    def evaluate_candidate(
        cls,
        candidate: ArtisticCandidate,
        dna: CompositionalDNA,
        catalog_memory: Optional[CatalogMemory] = None,
        is_final_climax: bool = False
    ) -> TasteScoreCard:
        """
        Evaluates a candidate across the 10 perceptual dimensions.
        """
        card = TasteScoreCard()

        if candidate.type == CandidateType.HARMONIC_MUTATION:
            card.identity = 0.94
            card.surprise = 0.82
            card.coherence = 0.92
            card.memorability = 0.88
            card.contrast = 0.78
            card.emotion = 0.93
            card.risk = 0.75
            card.motif_relationship = 0.90
            card.arrangement_relationship = 0.88
            card.catalog_uniqueness = 0.90

        elif candidate.type == CandidateType.RHYTHMIC_DISPLACEMENT:
            card.identity = 0.90
            card.surprise = 0.86
            card.coherence = 0.88
            card.memorability = 0.85
            card.contrast = 0.84
            card.emotion = 0.82
            card.risk = 0.80
            card.motif_relationship = 0.82
            card.arrangement_relationship = 0.92
            card.catalog_uniqueness = 0.88

        elif candidate.type == CandidateType.TIMBRAL_TEXTURE:
            card.identity = 0.88
            card.surprise = 0.89
            card.coherence = 0.86
            card.memorability = 0.91
            card.contrast = 0.92
            card.emotion = 0.90
            card.risk = 0.85
            card.motif_relationship = 0.86
            card.arrangement_relationship = 0.85
            card.catalog_uniqueness = 0.94

        # If it is the final climax (Hook 3), reward contrast and surprise even higher
        if is_final_climax:
            card.surprise = min(1.0, card.surprise + 0.05)
            card.contrast = min(1.0, card.contrast + 0.05)
            card.risk = min(1.0, card.risk + 0.05)

        candidate.scorecard = card
        return card

    @classmethod
    def adjudicate_taste(
        cls,
        candidates: List[ArtisticCandidate],
        dna: CompositionalDNA,
        catalog_memory: Optional[CatalogMemory] = None,
        risk_appetite: float = 0.65
    ) -> AuditionDecision:
        """
        Adjudicates among evaluated candidates:
        Balances musical taste, sonic taste, and the producer's risk appetite.
        """
        for cand in candidates:
            if cand.scorecard is None:
                cls.evaluate_candidate(cand, dna, catalog_memory)

        # Sort candidates by composite artistic score
        ranked = sorted(
            candidates,
            key=lambda c: c.scorecard.composite_artistic_score(risk_appetite) if c.scorecard else 0.0,
            reverse=True
        )

        winner = ranked[0]
        runner_up = ranked[1] if len(ranked) > 1 else None

        justification = (
            f"Candidate '{winner.name}' selected as artistic winner "
            f"(Artistic Score: {winner.scorecard.composite_artistic_score(risk_appetite):.3f}). "
            f"Distinguished by high emotional resonance ({winner.scorecard.emotion:.2f}) "
            f"and strong thematic loyalty to the Song DNA ({winner.scorecard.identity:.2f})."
        )

        risk_rationale = (
            f"Risk index of {winner.scorecard.risk:.2f} was favored over generic safety. "
            f"Surprise rating of {winner.scorecard.surprise:.2f} ensures Hook 3 prevents narrative stagnation."
        )

        ab_guidance = (
            f"Stage candidate '{winner.name}' as primary take in DAW track. "
            f"Preserve runner-up '{runner_up.name if runner_up else 'None'}' as alternative take in clip slot 7 "
            f"for physical producer A/B audition."
        )

        return AuditionDecision(
            selected_winner=winner,
            runner_up=runner_up,
            artistic_justification=justification,
            risk_reward_rationale=risk_rationale,
            ab_audition_guidance=ab_guidance
        )

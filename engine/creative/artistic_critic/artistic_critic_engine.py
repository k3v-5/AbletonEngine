# engine/creative/artistic_critic/artistic_critic_engine.py
"""
Artistic Critic Engine:
The internal judicial court uniting all 7 specialized critics:
1. IdentityCritic (Fingerprints & Uniqueness vs Catalog)
2. MemorabilityCritic (The 1-2 Iconic Events Rule)
3. PredictabilityCritic (Contextual Surprise vs Chaos & Cliche)
4. EmotionalCritic (Perceived Impact vs Mathematical Parameter Changes)
5. HumanPlausibilityCritic (Detection of Machine Generation Artifacts)
6. SonicSignatureCritic (Bespoke Unrepeatable Sound Requirement)
7. CulturalGenrePlausibilityCritic (Genre Deviation Budget)

Emits a comprehensive CriticVerdict. If any critic issues an absolute VETO,
or if the overall score falls below the threshold (default 0.78), the candidate is REJECTED.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging

from .critic_verdict import CriticVerdict, CriticScore, CriticDimension, VetoSeverity
from .identity_critic import IdentityCritic
from .memorability_critic import MemorabilityCritic
from .predictability_critic import PredictabilityCritic
from .emotional_critic import EmotionalCritic
from .human_plausibility_critic import HumanPlausibilityCritic
from .sonic_signature_critic import SonicSignatureCritic
from .genre_plausibility_critic import CulturalGenrePlausibilityCritic

from engine.creative.artistic_intent import ArtisticIntent
from engine.memory.catalog_memory import CatalogMemory

logger = logging.getLogger("ArtisticCriticEngine")


class ArtisticCriticEngine:
    """The ruthless internal judge filtering out 80-90% of sub-par musical proposals."""

    CRITIC_WEIGHTS = {
        CriticDimension.IDENTITY: 0.18,
        CriticDimension.MEMORABILITY: 0.20,
        CriticDimension.PREDICTABILITY: 0.14,
        CriticDimension.EMOTIONAL_PERCEPTION: 0.16,
        CriticDimension.HUMAN_PLAUSIBILITY: 0.14,
        CriticDimension.SONIC_SIGNATURE: 0.10,
        CriticDimension.GENRE_PLAUSIBILITY: 0.08,
    }

    ACCEPTANCE_THRESHOLD = 0.78

    @classmethod
    def critique_candidate(
        cls,
        candidate_data: Dict[str, Any],
        intent: Optional[ArtisticIntent] = None,
        catalog_memory: Optional[CatalogMemory] = None,
        strict_threshold: Optional[float] = None
    ) -> CriticVerdict:
        candidate_id = str(candidate_data.get("id") or candidate_data.get("name") or "candidate_proposal")
        threshold = strict_threshold or cls.ACCEPTANCE_THRESHOLD

        # 1. First priority: Artistic Intent preliminary gate
        vetos: List[str] = []
        warnings: List[str] = []
        feedback: List[str] = []

        if intent:
            serves, reason = intent.serves_intent(candidate_data)
            if not serves:
                vetos.append(reason)
                feedback.append("Reconfigurar propuesta para alinearla con el manifiesto de ArtisticIntent.")

        # 2. Run all 7 independent critics
        scores: Dict[CriticDimension, CriticScore] = {}

        # 1. Identity Critic
        score_id = IdentityCritic.evaluate(candidate_data, catalog_memory=catalog_memory)
        scores[CriticDimension.IDENTITY] = score_id

        # 2. Memorability Critic
        score_mem = MemorabilityCritic.evaluate(candidate_data)
        scores[CriticDimension.MEMORABILITY] = score_mem

        # 3. Predictability Critic
        score_pred = PredictabilityCritic.evaluate(candidate_data, intent=intent)
        scores[CriticDimension.PREDICTABILITY] = score_pred

        # 4. Emotional Critic
        score_emo = EmotionalCritic.evaluate(candidate_data, intent=intent)
        scores[CriticDimension.EMOTIONAL_PERCEPTION] = score_emo

        # 5. Human Plausibility Critic
        score_hum = HumanPlausibilityCritic.evaluate(candidate_data)
        scores[CriticDimension.HUMAN_PLAUSIBILITY] = score_hum

        # 6. Sonic Signature Critic
        score_son = SonicSignatureCritic.evaluate(candidate_data, intent=intent)
        scores[CriticDimension.SONIC_SIGNATURE] = score_son

        # 7. Genre Plausibility Critic
        score_gen = CulturalGenrePlausibilityCritic.evaluate(candidate_data, intent=intent)
        scores[CriticDimension.GENRE_PLAUSIBILITY] = score_gen

        # 3. Harvest vetos, warnings and mutation feedback
        total_weighted_score = 0.0
        for dim, score_obj in scores.items():
            w = cls.CRITIC_WEIGHTS.get(dim, 0.14)
            total_weighted_score += score_obj.score * w

            if score_obj.severity == VetoSeverity.VETO_REJECT:
                vetos.append(score_obj.explanation)
                feedback.append(f"Resolver fallo crítico en {dim.value}: {score_obj.explanation}")
            elif score_obj.severity == VetoSeverity.WARNING:
                warnings.append(score_obj.explanation)
                feedback.append(f"Mejorar {dim.value}: {score_obj.explanation}")

        overall_score = round(total_weighted_score, 3)

        # 4. Final Verdict: Passes only if no vetos AND score >= threshold
        passed = (len(vetos) == 0) and (overall_score >= threshold)
        if not passed and len(vetos) == 0 and overall_score < threshold:
            vetos.append(f"Puntaje artístico insuficiente ({overall_score:.2f} < umbral {threshold:.2f}).")
            feedback.append("Elevar audacia e impacto del motivo principal y texturas tímbricas.")

        verdict = CriticVerdict(
            candidate_id=candidate_id,
            passed=passed,
            overall_artistic_score=overall_score,
            scores=scores,
            vetos=vetos,
            warnings=warnings,
            feedback_for_mutation=feedback
        )

        log_level = logging.INFO if passed else logging.WARNING
        logger.log(log_level, f"Critic Verdict for '{candidate_id}': Passed={passed}, Score={overall_score:.2f}, Vetos={len(vetos)}")
        return verdict

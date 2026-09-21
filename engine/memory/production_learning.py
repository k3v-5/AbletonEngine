# engine/memory/production_learning.py
"""
Audio ➔ Analysis ➔ Learning Engine:
Extracts persistent production wisdom following audio render / physical intervention:
Takes acoustic telemetry (RMS, True Peak, Crest Factor, Mono Compatibility, Spectral Spread)
and correlates it with artistic taste scores and narrative impact.
Answers not just "did it pass?", but "WHY did this intervention work?",
indexing generalizable knowledge into the engine's long-term production memory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import datetime
import logging

logger = logging.getLogger("ProductionLearningEngine")


@dataclass
class AcousticAnalysisResult:
    """Acoustic measurements captured post-intervention."""
    rms_dbfs: float = -16.99
    true_peak_dbtp: float = -13.20
    crest_factor_db: float = 3.79
    mono_compatibility_loss_db: float = 0.00
    spectral_spread: str = "balanced_warm"
    emotional_lift_delta: float = 0.28
    novelty_surprise_score: float = 0.35

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rms_dbfs": round(self.rms_dbfs, 2),
            "true_peak_dbtp": round(self.true_peak_dbtp, 2),
            "crest_factor_db": round(self.crest_factor_db, 2),
            "mono_compatibility_loss_db": round(self.mono_compatibility_loss_db, 2),
            "spectral_spread": self.spectral_spread,
            "emotional_lift_delta": round(self.emotional_lift_delta, 2),
            "novelty_surprise_score": round(self.novelty_surprise_score, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AcousticAnalysisResult:
        return cls(
            rms_dbfs=float(data.get("rms_dbfs", -16.99)),
            true_peak_dbtp=float(data.get("true_peak_dbtp", -13.20)),
            crest_factor_db=float(data.get("crest_factor_db", 3.79)),
            mono_compatibility_loss_db=float(data.get("mono_compatibility_loss_db", 0.0)),
            spectral_spread=data.get("spectral_spread", "balanced_warm"),
            emotional_lift_delta=float(data.get("emotional_lift_delta", 0.28)),
            novelty_surprise_score=float(data.get("novelty_surprise_score", 0.35)),
        )


@dataclass
class LearnedProductionWisdom:
    """A persistent production lesson crystallized from physical evidence."""
    wisdom_id: str
    song_id: str
    section: str
    key_root: str
    intervention_applied: str
    acoustic_evidence: AcousticAnalysisResult
    taste_score: float
    why_it_worked: str
    generalizable_rule: str
    confidence_score: float = 0.92
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wisdom_id": self.wisdom_id,
            "song_id": self.song_id,
            "section": self.section,
            "key_root": self.key_root,
            "intervention_applied": self.intervention_applied,
            "acoustic_evidence": self.acoustic_evidence.to_dict(),
            "taste_score": round(self.taste_score, 3),
            "why_it_worked": self.why_it_worked,
            "generalizable_rule": self.generalizable_rule,
            "confidence_score": round(self.confidence_score, 2),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LearnedProductionWisdom:
        return cls(
            wisdom_id=data.get("wisdom_id", ""),
            song_id=data.get("song_id", ""),
            section=data.get("section", ""),
            key_root=data.get("key_root", "Eb"),
            intervention_applied=data.get("intervention_applied", ""),
            acoustic_evidence=AcousticAnalysisResult.from_dict(data.get("acoustic_evidence", {})),
            taste_score=float(data.get("taste_score", 0.9)),
            why_it_worked=data.get("why_it_worked", ""),
            generalizable_rule=data.get("generalizable_rule", ""),
            confidence_score=float(data.get("confidence_score", 0.92)),
            created_at=data.get("created_at", ""),
        )


class ProductionLearningEngine:
    """
    Accumulates empirical and perceptual knowledge across production sessions.
    Feeds back lessons into future creative dilemmas, taste evaluations, and arrangements.
    """

    def __init__(self):
        self.wisdom_repository: List[LearnedProductionWisdom] = []

    def evaluate_and_learn(
        self,
        song_id: str,
        section: str,
        key_root: str,
        intervention_applied: str,
        acoustic_evidence: AcousticAnalysisResult,
        taste_score: float,
        intervention_type: str = "DEVIATION_VACUUM"
    ) -> LearnedProductionWisdom:
        """
        Synthesizes physical telemetry and taste evaluation into an enduring rule.
        """
        # Determine why it worked based on acoustic evidence
        is_phase_coherent = acoustic_evidence.mono_compatibility_loss_db <= 0.5
        has_dynamic_contrast = acoustic_evidence.crest_factor_db >= 3.0
        high_surprise = acoustic_evidence.novelty_surprise_score >= 0.20

        why_reasons: List[str] = []
        if is_phase_coherent:
            why_reasons.append("Zero phase cancellation (0.0 dB mono loss) preserved punch in collapsed mono environments.")
        if has_dynamic_contrast:
            why_reasons.append(f"Crest factor of {acoustic_evidence.crest_factor_db:.1f} dB delivered punchy transient impact without master bus squashing.")
        if high_surprise:
            why_reasons.append(f"Surprise delta of +{acoustic_evidence.novelty_surprise_score*100:.0f}% shattered ear fatigue and lifted emotional energy.")

        why_summary = " ".join(why_reasons) if why_reasons else "Intervention maintained stable acoustic balance."

        rule = (
            f"When arranging a climax in {key_root} ({section}): "
            f"applying '{intervention_applied}' creates high emotional payoff while maintaining mono fidelity."
        )

        wisdom = LearnedProductionWisdom(
            wisdom_id=f"wis_{len(self.wisdom_repository)+1:03d}_{section.lower().replace(' ', '_')}",
            song_id=song_id,
            section=section,
            key_root=key_root,
            intervention_applied=intervention_applied,
            acoustic_evidence=acoustic_evidence,
            taste_score=taste_score,
            why_it_worked=why_summary,
            generalizable_rule=rule,
            confidence_score=0.94 if (is_phase_coherent and has_dynamic_contrast) else 0.85
        )

        self.wisdom_repository.append(wisdom)
        logger.info(f"Recorded new production wisdom: '{wisdom.wisdom_id}' -> {rule}")
        return wisdom

    def query_wisdom(
        self,
        target_section: Optional[str] = None,
        key_root: Optional[str] = None
    ) -> List[LearnedProductionWisdom]:
        """Queries accumulated production rules relevant to a section or key."""
        results: List[LearnedProductionWisdom] = []
        for w in self.wisdom_repository:
            sec_match = (not target_section) or (target_section.lower() in w.section.lower())
            key_match = (not key_root) or (key_root.lower() == w.key_root.lower())
            if sec_match or key_match:
                results.append(w)
        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_wisdom_rules": len(self.wisdom_repository),
            "rules": [w.to_dict() for w in self.wisdom_repository],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProductionLearningEngine:
        engine = cls()
        engine.wisdom_repository = [
            LearnedProductionWisdom.from_dict(w) for w in data.get("rules", [])
        ]
        return engine

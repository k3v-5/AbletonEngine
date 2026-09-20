"""
Creative Yield Tracker & Empirical Mechanism Efficacy:
Measures whether musical production techniques actually contribute to final song quality,
identity preservation, and mix survival, or merely add unhelpful complexity.

Computes:
Creative Yield = Perceptual Improvement * Identity Preservation * Survival Probability

Dynamically modulates base probabilities and priorities based on historical empirical efficacy.
"""

import os
import json
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("CreativeYieldTracker")

DEFAULT_YIELD_STORAGE_PATH = os.path.join("state", "learned", "creative_yield_priors.json")


class ExplorationPolicy:
    """
    Manages the balance between Exploitation (75-85% yield-driven)
    and Exploration (15-25% deliberate exploration budget).
    Prevents the engine from falling into an exploitation feedback loop trap.
    """
    def __init__(self, exploration_rate: float = 0.20, seed: Optional[int] = None):
        self.exploration_rate = exploration_rate
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.total_decisions: int = 0
        self.exploration_decisions: int = 0

    def decide_strategy(self, force_explore: bool = False, force_exploit: bool = False) -> str:
        """Decides whether current decision is 'EXPLOIT' or 'EXPLORE'."""
        self.total_decisions += 1
        if force_explore:
            self.exploration_decisions += 1
            return "EXPLORE"
        if force_exploit:
            return "EXPLOIT"
        if self.rng.random() < self.exploration_rate:
            self.exploration_decisions += 1
            return "EXPLORE"
        return "EXPLOIT"

    @property
    def empirical_exploration_ratio(self) -> float:
        if self.total_decisions == 0:
            return self.exploration_rate
        return round(self.exploration_decisions / self.total_decisions, 3)


@dataclass
class MechanismYieldRecord:
    """Historical record of an individual production mechanism's efficacy."""
    technique_name: str
    total_invocations: int = 0
    survived_in_final_mix: int = 0
    perceptual_improvements: List[float] = field(default_factory=list)
    identity_preservations: List[float] = field(default_factory=list)

    @property
    def survival_rate(self) -> float:
        if self.total_invocations == 0:
            return 0.50
        return round(self.survived_in_final_mix / self.total_invocations, 3)

    @property
    def average_improvement(self) -> float:
        if not self.perceptual_improvements:
            return 0.50
        return round(sum(self.perceptual_improvements) / len(self.perceptual_improvements), 3)

    @property
    def average_identity_preservation(self) -> float:
        if not self.identity_preservations:
            return 0.70
        return round(sum(self.identity_preservations) / len(self.identity_preservations), 3)

    @property
    def creative_yield(self) -> float:
        """
        Creative Yield = Improvement * Identity Preservation * Survival Probability.
        Yield in [0.0, 1.0].
        """
        cy = self.average_improvement * self.average_identity_preservation * self.survival_rate
        return round(min(1.0, max(0.0, cy)), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technique_name": self.technique_name,
            "total_invocations": self.total_invocations,
            "survived_in_final_mix": self.survived_in_final_mix,
            "survival_rate": self.survival_rate,
            "average_improvement": self.average_improvement,
            "average_identity_preservation": self.average_identity_preservation,
            "creative_yield": self.creative_yield,
            "recent_improvements": self.perceptual_improvements[-10:],
            "recent_identity": self.identity_preservations[-10:]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MechanismYieldRecord":
        return cls(
            technique_name=str(data.get("technique_name", "unknown")),
            total_invocations=int(data.get("total_invocations", 0)),
            survived_in_final_mix=int(data.get("survived_in_final_mix", 0)),
            perceptual_improvements=list(data.get("recent_improvements", [])),
            identity_preservations=list(data.get("recent_identity", []))
        )


class CreativeYieldTracker:
    """
    Tracks, updates, and persists the empirical yield of all production mechanisms.
    Translates historical performance into adaptive probability weights.
    """

    def __init__(self, storage_path: str = DEFAULT_YIELD_STORAGE_PATH, exploration_rate: float = 0.20):
        self.storage_path = storage_path
        self.exploration_policy = ExplorationPolicy(exploration_rate=exploration_rate)
        self.records: Dict[str, MechanismYieldRecord] = {}
        self.load()

    def record_mechanism_application(
        self,
        technique_name: str,
        delta_improvement: float,
        identity_preserved: float,
        survived_in_final_mix: bool,
        auto_save: bool = False
    ) -> MechanismYieldRecord:
        """
        Records an application of a mechanism with its outcome metrics.
        """
        norm_name = technique_name.lower().strip()
        if norm_name not in self.records:
            self.records[norm_name] = MechanismYieldRecord(technique_name=norm_name)

        rec = self.records[norm_name]
        rec.total_invocations += 1
        if survived_in_final_mix:
            rec.survived_in_final_mix += 1

        # Bound delta improvement to [0.0, 1.0] scale
        norm_improvement = min(1.0, max(0.0, delta_improvement))
        norm_ident = min(1.0, max(0.0, identity_preserved))

        rec.perceptual_improvements.append(norm_improvement)
        rec.identity_preservations.append(norm_ident)

        if auto_save:
            self.save()
        return rec

    def get_yield(self, technique_name: str) -> float:
        """Returns the calculated creative yield for a technique (default 0.50 if no prior data)."""
        norm_name = technique_name.lower().strip()
        rec = self.records.get(norm_name)
        if not rec or rec.total_invocations == 0:
            return 0.50
        return rec.creative_yield

    def modulate_probability(self, technique_name: str, base_probability: float) -> float:
        """
        Modulates a mechanism's base probability based on historical creative yield:
        - High yield (>= 0.55): Multiplier up to 1.35x (boosted priority)
        - Low yield (< 0.25): Multiplier down to 0.50x (attenuated priority)
        """
        norm_name = technique_name.lower().strip()
        rec = self.records.get(norm_name)
        if not rec or rec.total_invocations < 3:
            # Insufficient statistical history, keep base probability
            return base_probability

        yield_val = rec.creative_yield
        if yield_val >= 0.55:
            # Boost probability
            multiplier = 1.0 + (yield_val - 0.55) * 0.80  # Up to ~1.36x
        elif yield_val < 0.25:
            # Penalize low yield
            multiplier = max(0.40, 1.0 - (0.25 - yield_val) * 2.0)
        else:
            multiplier = 1.0

        modulated = base_probability * multiplier
        return round(min(0.95, max(0.05, modulated)), 3)

    def modulate_probability_with_budget(
        self,
        technique_name: str,
        base_probability: float,
        force_explore: bool = False,
        force_exploit: bool = False
    ) -> Tuple[float, str]:
        """
        Applies exploration budget policy:
        - In 'EXPLOIT' mode (default 80%): modulates based on empirical yield.
        - In 'EXPLORE' mode (default 20%): lifts penalties on low-yield techniques
          or gives exploration boost to under-tested/under-represented techniques,
          preventing an exploitation monopoly.
        """
        strategy = self.exploration_policy.decide_strategy(
            force_explore=force_explore,
            force_exploit=force_exploit
        )
        if strategy == "EXPLORE":
            norm_name = technique_name.lower().strip()
            rec = self.records.get(norm_name)
            if rec and rec.creative_yield < 0.35:
                # Lift historical penalty to allow rediscovery in new contexts
                explored_prob = max(base_probability, 0.45)
            else:
                # Moderate boost to encourage non-dominant pathways
                explored_prob = min(0.90, max(0.40, base_probability * 1.25))
            return (round(explored_prob, 3), "EXPLORE")
        else:
            exploited_prob = self.modulate_probability(technique_name, base_probability)
            return (exploited_prob, "EXPLOIT")

    def get_yield_report(self) -> Dict[str, Any]:
        """Returns comprehensive diagnostic audit of mechanism yields."""
        if not self.records:
            return {"status": "NO_YIELD_DATA", "total_tracked_mechanisms": 0}

        table: List[Dict[str, Any]] = []
        high_yield = []
        low_yield = []

        for name, rec in self.records.items():
            entry = rec.to_dict()
            table.append(entry)
            if rec.creative_yield >= 0.50 and rec.total_invocations >= 3:
                high_yield.append(name)
            elif rec.creative_yield < 0.25 and rec.total_invocations >= 3:
                low_yield.append(name)

        return {
            "status": "YIELD_AUDITED",
            "total_tracked_mechanisms": len(self.records),
            "mechanisms": table,
            "high_yield_recommendations": high_yield,
            "low_yield_penalties": low_yield
        }

    def save(self, filepath: Optional[str] = None) -> None:
        """Persists yield records to JSON file."""
        target = filepath or self.storage_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = {
            "version": "1.0",
            "records": {k: v.to_dict() for k, v in self.records.items()}
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.records)} yield records to {target}")

    def load(self, filepath: Optional[str] = None) -> None:
        """Loads yield records from JSON file if it exists."""
        target = filepath or self.storage_path
        if not os.path.exists(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.records = {
                k: MechanismYieldRecord.from_dict(v)
                for k, v in data.get("records", {}).items()
            }
            logger.info(f"Loaded {len(self.records)} yield records from {target}")
        except Exception as e:
            logger.warning(f"Failed to load yield records from {target}: {e}")

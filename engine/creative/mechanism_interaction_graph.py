"""
Mechanism Interaction Graph:
Models non-linear interactions between musical production mechanisms.
Measures whether combining techniques creates Creative Synergy:
  Yield(A + B) > (Yield(A) + Yield(B)) / 2
or Destructive Interference (overcrowding, narrative confusion):
  Yield(A + B) < (Yield(A) + Yield(B)) / 2 - 0.15
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("MechanismInteractionGraph")

DEFAULT_INTERACTIONS_STORAGE_PATH = os.path.join("state", "learned", "mechanism_interactions.json")


def normalize_pair_key(tech_a: str, tech_b: str) -> Tuple[str, str]:
    """Returns a canonical, sorted tuple for an unordered pair of techniques."""
    a = tech_a.lower().strip()
    b = tech_b.lower().strip()
    return (a, b) if a <= b else (b, a)


@dataclass
class MechanismPairRecord:
    """Historical interaction record between two production techniques."""
    tech_a: str
    tech_b: str
    co_invocations: int = 0
    survived_together: int = 0
    pair_delta_improvements: List[float] = field(default_factory=list)
    pair_identity_preservations: List[float] = field(default_factory=list)

    @property
    def pair_key(self) -> str:
        a, b = normalize_pair_key(self.tech_a, self.tech_b)
        return f"{a}:::{b}"

    @property
    def survival_rate(self) -> float:
        if self.co_invocations == 0:
            return 0.50
        return round(self.survived_together / self.co_invocations, 3)

    @property
    def average_improvement(self) -> float:
        if not self.pair_delta_improvements:
            return 0.50
        return round(sum(self.pair_delta_improvements) / len(self.pair_delta_improvements), 3)

    @property
    def average_identity_preservation(self) -> float:
        if not self.pair_identity_preservations:
            return 0.70
        return round(sum(self.pair_identity_preservations) / len(self.pair_identity_preservations), 3)

    @property
    def pair_yield(self) -> float:
        """
        Combined yield of the pair:
        Improvement * Identity Preservation * Joint Survival Rate.
        """
        py = self.average_improvement * self.average_identity_preservation * self.survival_rate
        return round(min(1.0, max(0.0, py)), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tech_a": self.tech_a,
            "tech_b": self.tech_b,
            "co_invocations": self.co_invocations,
            "survived_together": self.survived_together,
            "survival_rate": self.survival_rate,
            "average_improvement": self.average_improvement,
            "average_identity_preservation": self.average_identity_preservation,
            "pair_yield": self.pair_yield,
            "recent_improvements": self.pair_delta_improvements[-10:],
            "recent_identity": self.pair_identity_preservations[-10:]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MechanismPairRecord":
        return cls(
            tech_a=str(data.get("tech_a", "")),
            tech_b=str(data.get("tech_b", "")),
            co_invocations=int(data.get("co_invocations", 0)),
            survived_together=int(data.get("survived_together", 0)),
            pair_delta_improvements=list(data.get("recent_improvements", [])),
            pair_identity_preservations=list(data.get("recent_identity", []))
        )


class MechanismInteractionGraph:
    """
    Graph of mechanism interactions.
    Nodes: Individual mechanisms.
    Edges: Co-occurrence statistics, synergies, and destructive interferences.
    """

    def __init__(self, storage_path: str = DEFAULT_INTERACTIONS_STORAGE_PATH):
        self.storage_path = storage_path
        self.edges: Dict[str, MechanismPairRecord] = {}
        self.load()

    def record_interaction(
        self,
        tech_a: str,
        tech_b: str,
        delta_improvement: float,
        identity_preserved: float,
        survived_together: bool,
        auto_save: bool = False
    ) -> MechanismPairRecord:
        """Records a joint application of two mechanisms and its outcome."""
        a, b = normalize_pair_key(tech_a, tech_b)
        if a == b:
            # Self-interaction is not tracked as a pair
            raise ValueError(f"Cannot record interaction between identical techniques: {tech_a}")

        key = f"{a}:::{b}"
        if key not in self.edges:
            self.edges[key] = MechanismPairRecord(tech_a=a, tech_b=b)

        rec = self.edges[key]
        rec.co_invocations += 1
        if survived_together:
            rec.survived_together += 1

        rec.pair_delta_improvements.append(min(1.0, max(0.0, delta_improvement)))
        rec.pair_identity_preservations.append(min(1.0, max(0.0, identity_preserved)))

        if auto_save:
            self.save()
        return rec

    def get_pair_record(self, tech_a: str, tech_b: str) -> Optional[MechanismPairRecord]:
        """Retrieves edge record for two techniques."""
        a, b = normalize_pair_key(tech_a, tech_b)
        return self.edges.get(f"{a}:::{b}")

    def calculate_synergy(
        self,
        tech_a: str,
        tech_b: str,
        yield_tracker: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Calculates interaction synergy between two techniques:
        Synergy = PairYield(A, B) - (Yield(A) + Yield(B)) / 2

        Status:
        - CREATIVE_SYNERGY: Synergy > +0.10
        - DESTRUCTIVE_INTERFERENCE: Synergy < -0.15
        - NEUTRAL_ADDITIVE: otherwise
        - INSUFFICIENT_DATA: if co_invocations < 2
        """
        a, b = normalize_pair_key(tech_a, tech_b)
        rec = self.get_pair_record(a, b)

        if not rec or rec.co_invocations < 2:
            return {
                "tech_a": a,
                "tech_b": b,
                "co_invocations": rec.co_invocations if rec else 0,
                "pair_yield": rec.pair_yield if rec else 0.50,
                "expected_yield": 0.50,
                "synergy": 0.0,
                "status": "INSUFFICIENT_DATA"
            }

        yield_a = yield_tracker.get_yield(a) if yield_tracker else 0.50
        yield_b = yield_tracker.get_yield(b) if yield_tracker else 0.50
        expected_yield = round((yield_a + yield_b) / 2.0, 3)

        synergy = round(rec.pair_yield - expected_yield, 3)

        if synergy > 0.10:
            status = "CREATIVE_SYNERGY"
        elif synergy < -0.15:
            status = "DESTRUCTIVE_INTERFERENCE"
        else:
            status = "NEUTRAL_ADDITIVE"

        return {
            "tech_a": a,
            "tech_b": b,
            "co_invocations": rec.co_invocations,
            "pair_yield": rec.pair_yield,
            "expected_yield": expected_yield,
            "synergy": synergy,
            "status": status
        }

    def get_best_synergies(
        self,
        technique_name: str,
        yield_tracker: Optional[Any] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Returns top synergistic partners for a given technique."""
        target = technique_name.lower().strip()
        synergies = []

        for key, rec in self.edges.items():
            if rec.tech_a == target or rec.tech_b == target:
                other = rec.tech_b if rec.tech_a == target else rec.tech_a
                syn_eval = self.calculate_synergy(target, other, yield_tracker)
                if syn_eval["status"] != "INSUFFICIENT_DATA":
                    syn_eval["partner"] = other
                    synergies.append(syn_eval)

        synergies.sort(key=lambda x: x["synergy"], reverse=True)
        return synergies[:limit]

    def get_destructive_interferences(
        self,
        technique_name: Optional[str] = None,
        yield_tracker: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Returns detected destructive interferences (pairs with synergy < -0.15)."""
        target = technique_name.lower().strip() if technique_name else None
        conflicts = []

        for key, rec in self.edges.items():
            if target and (rec.tech_a != target and rec.tech_b != target):
                continue
            syn_eval = self.calculate_synergy(rec.tech_a, rec.tech_b, yield_tracker)
            if syn_eval["status"] == "DESTRUCTIVE_INTERFERENCE":
                conflicts.append(syn_eval)

        conflicts.sort(key=lambda x: x["synergy"])
        return conflicts

    def save(self, filepath: Optional[str] = None) -> None:
        """Persists graph edges to JSON."""
        target = filepath or self.storage_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = {
            "version": "1.0",
            "edges": {k: v.to_dict() for k, v in self.edges.items()}
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.edges)} mechanism interaction edges to {target}")

    def load(self, filepath: Optional[str] = None) -> None:
        """Loads graph edges from JSON if present."""
        target = filepath or self.storage_path
        if not os.path.exists(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.edges = {
                k: MechanismPairRecord.from_dict(v)
                for k, v in data.get("edges", {}).items()
            }
            logger.info(f"Loaded {len(self.edges)} interaction edges from {target}")
        except Exception as e:
            logger.warning(f"Failed to load mechanism interactions from {target}: {e}")

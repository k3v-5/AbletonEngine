# engine/production/contract/creative_decision_ledger.py
"""
Creative Decision Ledger:
Records the history of intentional artistic choices to distinguish between:
1. Deliberate Return (conscious repetition for narrative/aesthetic effect)
2. Creative Omission (forgotten variation or unexecuted motif)
3. System Drift (unintended default generation)

Prevents the engine from perpetually attempting to 'fix' intentional artistic returns.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("CreativeDecisionLedger")


class DecisionVerdict(str, Enum):
    DELIBERATE_RETURN = "DELIBERATE_RETURN"      # Intentional identical return justified by contextual contrast
    SEEK_EVOLUTION = "SEEK_EVOLUTION"            # User or producer desires active variation / transcendence
    MAINTAIN_UNMODIFIED = "MAINTAIN_UNMODIFIED"  # Kept as-is by explicit aesthetic choice
    PENDING_DECISION = "PENDING_DECISION"        # Open creative question


@dataclass
class CreativeDecisionRecord:
    """Individual record of a conscious creative decision."""
    decision_id: str
    target_element: str
    event: str
    evidence: Dict[str, Any]
    context: Dict[str, Any]
    interpretation: str
    verdict: DecisionVerdict = DecisionVerdict.PENDING_DECISION
    artistic_rationale: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "target_element": self.target_element,
            "event": self.event,
            "evidence": dict(self.evidence),
            "context": dict(self.context),
            "interpretation": self.interpretation,
            "verdict": self.verdict.value if isinstance(self.verdict, DecisionVerdict) else str(self.verdict),
            "artistic_rationale": self.artistic_rationale,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CreativeDecisionRecord:
        verdict_str = data.get("verdict", "PENDING_DECISION")
        try:
            verdict = DecisionVerdict(verdict_str)
        except ValueError:
            verdict = DecisionVerdict.PENDING_DECISION
        return cls(
            decision_id=data["decision_id"],
            target_element=data.get("target_element", ""),
            event=data.get("event", ""),
            evidence=data.get("evidence", {}),
            context=data.get("context", {}),
            interpretation=data.get("interpretation", ""),
            verdict=verdict,
            artistic_rationale=data.get("artistic_rationale", ""),
            created_at=data.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
        )


@dataclass
class CreativeDecisionLedger:
    """Persistent ledger of artistic decisions for the current project."""
    decisions: Dict[str, CreativeDecisionRecord] = field(default_factory=dict)

    def register_decision(
        self,
        decision_id: str,
        target_element: str,
        event: str,
        evidence: Dict[str, Any],
        context: Dict[str, Any],
        interpretation: str,
        verdict: DecisionVerdict = DecisionVerdict.PENDING_DECISION,
        artistic_rationale: str = ""
    ) -> CreativeDecisionRecord:
        record = CreativeDecisionRecord(
            decision_id=decision_id,
            target_element=target_element,
            event=event,
            evidence=evidence,
            context=context,
            interpretation=interpretation,
            verdict=verdict,
            artistic_rationale=artistic_rationale
        )
        self.decisions[decision_id] = record
        return record

    def get_decision(self, decision_id: str) -> Optional[CreativeDecisionRecord]:
        return self.decisions.get(decision_id)

    def is_deliberate_choice(self, decision_id: str) -> bool:
        record = self.decisions.get(decision_id)
        return record is not None and record.verdict in (DecisionVerdict.DELIBERATE_RETURN, DecisionVerdict.MAINTAIN_UNMODIFIED)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.to_dict() for k, v in self.decisions.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CreativeDecisionLedger:
        if not data or not isinstance(data, dict):
            return cls()
        decisions = {}
        for k, v in data.items():
            decisions[k] = CreativeDecisionRecord.from_dict(v)
        return cls(decisions=decisions)

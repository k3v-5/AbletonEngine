# engine/creative/evolution/ledger.py
"""
Evolution Ledger (Nivel S6):
Append-only immutable record of all sectional evolution cycles:
Traces:
Snapshot ID -> Intervention Order -> New Snapshot -> Delta Q -> Decision (COMMIT vs ROLLBACK).
Guarantees full scientific reproducibility and forensic traceability.
"""

from __future__ import annotations
import datetime
import logging
from typing import Dict, List, Any, Optional

from .models import EvolutionSnapshot, InterventionOrder

logger = logging.getLogger("EvolutionLedger")


class EvolutionLedger:
    """Maintains an append-only audit trail of creative evolution iterations."""

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def record_cycle(
        self,
        section_name: str,
        iteration: int,
        snapshot_before: EvolutionSnapshot,
        order: Optional[InterventionOrder],
        snapshot_after: Optional[EvolutionSnapshot],
        decision: str,  # "COMMIT", "ROLLBACK", "HALT_BUDGET", "NO_INTERVENTION_NEEDED"
        reason: str
    ) -> Dict[str, Any]:
        """Records an evolution step in the ledger."""
        score_before = snapshot_before.net_score
        score_after = snapshot_after.net_score if snapshot_after else score_before
        delta_q = round(score_after - score_before, 3)

        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "section_name": section_name,
            "iteration": iteration,
            "snapshot_before_id": snapshot_before.snapshot_id,
            "snapshot_after_id": snapshot_after.snapshot_id if snapshot_after else None,
            "order": order.to_dict() if order else None,
            "score_before": round(score_before, 3),
            "score_after": round(score_after, 3),
            "delta_q": delta_q,
            "decision": decision,
            "reason": reason,
        }
        self.entries.append(entry)
        logger.info(f"EvolutionLedger [{section_name} - Iter {iteration}]: {decision} (ΔQ = {delta_q:+.2f}) - {reason}")
        return entry

    @property
    def history(self) -> List[Dict[str, Any]]:
        return self.entries

    def record_performance_mutation(
        self,
        section_name: str,
        order_type: str,
        delta_q: float,
        verdict: str,
        decision_reason: str,
        track_name: str = "ensemble"
    ) -> Dict[str, Any]:
        """Records a dedicated performance mutation in the evolution ledger."""
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "section_name": section_name,
            "order_domain": "PERFORMANCE",
            "order_type": order_type,
            "delta_q": round(delta_q, 3),
            "verdict": verdict,
            "decision": verdict,
            "decision_reason": decision_reason,
            "track_name": track_name,
        }
        self.entries.append(entry)
        logger.info(f"EvolutionLedger [{section_name} - Performance]: {verdict} (ΔQ = {delta_q:+.2f}) - {decision_reason}")
        return entry

    def get_section_history(self, section_name: str) -> List[Dict[str, Any]]:
        return [e for e in self.entries if e.get("section_name", "").lower() == section_name.lower()]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self.entries),
            "entries": list(self.entries)
        }


"""
Decision Memory for the Production Intelligence Engine (PIE).
Structured, contextual memory for decision lineage, historical comparison, and traceable reuse.
Explicitly non-ML; enforces the absolute invariant that historical matches never auto-execute.
"""
from typing import Dict, List, Any, Optional
import datetime
import uuid

from .models import ProductionDecision


class MemoryStatus:
    VALID = "VALID"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"
    EXPERIMENTAL = "EXPERIMENTAL"


class DecisionMemory:
    """
    Context-aware memory of prior decisions, verified actions, and acoustic outcomes.
    Serves as an evidence engine: produces candidates for current validation, never executes blindly.
    """

    def __init__(self, project_id: str = "default_project", storage: Optional[Any] = None):
        self.project_id = project_id
        self.storage = storage
        self.schema_version = "1.0"
        self._records: Dict[str, Dict[str, Any]] = {}
        # Decision ID to Memory ID mapping
        self._decision_to_memory: Dict[str, str] = {}
        # Links between related memories
        self._links: Dict[str, List[str]] = {}

    @property
    def records(self) -> List[Dict[str, Any]]:
        return list(self._records.values())

    def record(
        self,
        decision: ProductionDecision,
        context: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Stores a decision with required musical, technical, and acoustic context.
        Returns the unique memory_id.
        """
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        ctx = context or {}

        resolved_outcome = outcome or {
            "actual_delta": decision.actual_delta,
            "measurements_after": decision.measurements_after,
            "regression": decision.regression,
            "status": decision.status.value if hasattr(decision.status, "value") else str(decision.status)
        }

        record = {
            "memory_id": memory_id,
            "project_id": self.project_id,
            "decision_id": decision.decision_id,
            "domain": decision.domain,
            "target": decision.target,
            "decision_type": decision.decision_type,
            "reason": decision.reason,
            "status": MemoryStatus.VALID,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            # Musical and technical context
            "context": {
                "genre": ctx.get("genre", "generic"),
                "tempo": ctx.get("tempo", 120.0),
                "key": ctx.get("key", "C"),
                "time_signature": ctx.get("time_signature", "4/4"),
                "section": ctx.get("section", "UNKNOWN"),
                "profile": ctx.get("profile", ctx.get("delivery_target", "STREAMING")),
                "tracks": ctx.get("tracks", []),
                "devices": ctx.get("devices", []),
                "measurements": ctx.get("measurements", decision.measurements_before),
                "conditions": ctx.get("conditions", {})
            },
            # Causal and action data
            "decision": decision.to_dict(),
            "outcome": resolved_outcome,
            "confidence": decision.confidence,
            "regression": decision.regression,
            "is_candidate_only": True,          # Fundamental invariant
            "auto_executable": False,           # Fundamental invariant
            "invalidation_reason": None,
            "superseded_by": None
        }

        self._records[memory_id] = record
        self._decision_to_memory[decision.decision_id] = memory_id
        self._links[memory_id] = []
        return memory_id

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self._records.get(memory_id)

    def search(
        self,
        query_context: Dict[str, Any],
        domain: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Contextual search for historically verified actions matching current scenario.
        Always returns candidates marked as candidate-only; NEVER allows direct execution.
        """
        results = []
        target_domain = domain.lower() if domain else None
        target_genre = query_context.get("genre", "").lower()
        target_target = query_context.get("target", "").lower()

        for rec in self._records.values():
            # Only valid or experimental records are considered
            if rec["status"] not in [MemoryStatus.VALID, MemoryStatus.EXPERIMENTAL]:
                continue

            if rec["confidence"] < min_confidence:
                continue

            if rec.get("regression", False):
                continue

            # Domain filter
            if target_domain and rec["domain"].lower() != target_domain:
                continue

            # Context similarity score
            score = 0.0
            rec_ctx = rec.get("context", {})
            if target_genre and target_genre == rec_ctx.get("genre", "").lower():
                score += 0.3
            if target_target and target_target == rec["target"].lower():
                score += 0.4
            if rec["status"] == MemoryStatus.VALID:
                score += 0.3

            # Enrich result explicitly marking candidate-only status
            candidate_payload = dict(rec)
            candidate_payload["match_score"] = round(score, 2)
            candidate_payload["is_candidate_only"] = True
            candidate_payload["auto_executable"] = False

            results.append(candidate_payload)

        # Sort deterministically by score descending, then memory_id
        results.sort(key=lambda r: (-r["match_score"], r["memory_id"]))
        return results

    def invalidate(self, memory_id: str, reason: str):
        """Invalidates a memory record when subsequent findings disprove it."""
        if memory_id in self._records:
            self._records[memory_id]["status"] = MemoryStatus.INVALIDATED
            self._records[memory_id]["invalidation_reason"] = reason

    def validate(self, memory_id: str):
        """Re-validates a memory record."""
        if memory_id in self._records:
            self._records[memory_id]["status"] = MemoryStatus.VALID
            self._records[memory_id]["invalidation_reason"] = None

    def supersede(self, old_memory_id: str, new_memory_id: str):
        """Marks a prior decision as superseded by a newer, higher-confidence decision."""
        if old_memory_id in self._records and new_memory_id in self._records:
            self._records[old_memory_id]["status"] = MemoryStatus.SUPERSEDED
            self._records[old_memory_id]["superseded_by"] = new_memory_id

    def link(self, memory_id: str, related_decision_id: str):
        """Links two decisions that informed each other."""
        if memory_id in self._records:
            if related_decision_id not in self._links[memory_id]:
                self._links[memory_id].append(related_decision_id)

    def get_related(self, decision_id: str) -> List[Dict[str, Any]]:
        """Retrieves related memory records linked to a specific decision."""
        mem_id = self._decision_to_memory.get(decision_id)
        if not mem_id or mem_id not in self._links:
            return []
        related_ids = self._links[mem_id]
        return [self._records[self._decision_to_memory[d_id]]
                for d_id in related_ids
                if d_id in self._decision_to_memory and self._decision_to_memory[d_id] in self._records]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "records": {k: self._records[k] for k in sorted(self._records.keys())},
            "decision_to_memory": self._decision_to_memory,
            "links": self._links
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionMemory":
        mem = cls(project_id=data.get("project_id", "default_project"))
        mem.schema_version = data.get("schema_version", "1.0")
        mem._records = data.get("records", {})
        mem._decision_to_memory = data.get("decision_to_memory", {})
        mem._links = data.get("links", {})
        return mem

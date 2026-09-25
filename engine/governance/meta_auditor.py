"""
Meta-Auditor Conflict Resolutor (Unified Authority Engine).
Arbitrates conflicts between the Four Authority Tiers:
Invariants (Hard Fail) > Artistic Intent > Contextual Constraints > Heuristics
"""

from typing import Any, Dict, List, Optional
import logging
from pydantic import BaseModel, Field

from engine.governance.contract import (
    StructuralDecisionContract,
    DecisionType,
    ResolutionStatus,
)
from engine.governance.evidence import (
    ContextEvaluationResult,
    IntegrityResult,
    VerificationResult,
    EvidenceStatus,
    GovernancePolicy,
)
from engine.governance.coordinator import ExecutionCoordinator, CoordinatorResult
from engine.governance.context_evaluator import ContextualConstraintEvaluator
from engine.governance.heuristics_advisor import HeuristicsAdvisor

logger = logging.getLogger("MetaAuditor")


class MetaAuditReport(BaseModel):
    decision_id: str
    dominant_authority_tier: str  # "TIER_1_INVARIANT", "TIER_2_CONTEXT", "TIER_3_HEURISTIC", "TIER_4_ARTISTIC"
    resolution_status: ResolutionStatus
    commit_approved: bool
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    coordinator_result: Optional[CoordinatorResult] = None


class MetaAuditor:
    """
    Arbitrates multi-tier governance decisions.
    Ensures the engine never halts on creative intent while strictly upholding safety invariants.
    """

    @classmethod
    def audit_and_execute(
        cls,
        contract: StructuralDecisionContract,
        session_data: Dict[str, Any],
        coordinator: ExecutionCoordinator,
        state_bus: Optional[Any] = None,
        conn: Any = None,
        is_test_env: bool = False,
    ) -> MetaAuditReport:
        """
        Executes full multi-tier arbitration and physical coordination.
        """
        # 1. Tier 2 Contextual Constraint Evaluation
        context_result = ContextualConstraintEvaluator.evaluate_decision_context(
            contract=contract,
            session_data=session_data,
            state_bus=state_bus,
        )

        # 2. Tier 3 Psychoacoustic Heuristics Audit
        heuristic_warnings = HeuristicsAdvisor.audit_psychoacoustics(
            session_data=session_data,
            tracks=session_data.get("tracks"),
        )
        context_result.warnings.extend(heuristic_warnings)

        # 3. Tier 4 Artistic Sovereignty Arbitration:
        # Artistic Intent supersedes soft contextual constraints when contracted
        is_artistic_sovereignty = (
            contract.justification in {"ARTISTIC_SOVEREIGNTY", "ORCHESTRAL_TACET"}
            or contract.exception_type in {"rejected_by_artist", "intentional_silence", "pre_drop_vacuum"}
        )

        dominant_tier = "TIER_2_CONTEXT"
        if not contract.is_valid:
            dominant_tier = "TIER_1_INVARIANT"
        elif is_artistic_sovereignty:
            dominant_tier = "TIER_4_ARTISTIC"
            # Authorize the contextual constraint via sovereign artistic intent
            if not context_result.satisfied:
                context_result.warnings.extend(context_result.unmet_constraints)
                context_result.unmet_constraints = []
                context_result.satisfied = True
        elif not context_result.satisfied:
            dominant_tier = "TIER_2_CONTEXT"
        elif context_result.warnings:
            dominant_tier = "TIER_3_HEURISTIC"

        # 4. Physical Coordination Execution
        coord_res = coordinator.execute(
            contract=contract,
            conn=conn,
            session=None,
            context_result=context_result,
            is_test_env=is_test_env,
        )

        return MetaAuditReport(
            decision_id=contract.contract_id,
            dominant_authority_tier=dominant_tier,
            resolution_status=coord_res.status,
            commit_approved=coord_res.success,
            reasons=coord_res.resolution.reasons,
            warnings=coord_res.resolution.warnings,
            coordinator_result=coord_res,
        )

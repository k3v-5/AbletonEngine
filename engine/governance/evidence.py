"""
Evidence Records and Coherence Validators for Governance Framework.
Immutable observation models for execution, verification, integrity, and provenance.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, model_validator
from .contract import ExecutionStatus, MutationState, EvidenceStatus


class ExecutionResult(BaseModel):
    execution_id: str
    status: ExecutionStatus
    mutation_state: MutationState = MutationState.NOT_MUTATED
    error_message: Optional[str] = None

    @model_validator(mode="after")
    def validate_execution_coherence(self) -> "ExecutionResult":
        # 1. NO_OP cannot declare a mutated state
        if self.status == ExecutionStatus.NO_OP and self.mutation_state != MutationState.NOT_MUTATED:
            raise ValueError(
                f"Semantic incoherence: status=NO_OP requires mutation_state=NOT_MUTATED (got {self.mutation_state})."
            )

        # 2. SUCCESS strictly requires MUTATED state
        if self.status == ExecutionStatus.SUCCESS and self.mutation_state != MutationState.MUTATED:
            raise ValueError(
                f"Semantic incoherence: status=SUCCESS requires mutation_state=MUTATED (got {self.mutation_state})."
            )

        # 3. FAILED cannot declare MUTATED without triggering physical alarm (must be NOT_MUTATED or UNKNOWN)
        if self.status == ExecutionStatus.FAILED and self.mutation_state == MutationState.MUTATED:
            raise ValueError(
                "Semantic incoherence: status=FAILED cannot declare mutation_state=MUTATED."
            )

        return self


class VerificationResult(BaseModel):
    verification_id: str
    status: EvidenceStatus
    mismatch_detail: Optional[str] = None
    observed_state: Optional[Dict[str, Any]] = None
    override_passed: Optional[bool] = None

    @property
    def passed(self) -> bool:
        """Strict certification: ONLY EvidenceStatus.VERIFIED is considered passed."""
        return self.status == EvidenceStatus.VERIFIED


class IntegrityResult(BaseModel):
    is_intact: bool = True
    violations: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ProvenanceCompleteness(BaseModel):
    complete: bool = True
    missing_links: List[str] = Field(default_factory=list)
    lineage_hash: Optional[str] = None


class ContextEvaluationResult(BaseModel):
    satisfied: bool = True
    unmet_constraints: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class GovernancePolicy(BaseModel):
    policy_id: str
    policy_version: str = "1.0.0"
    enabled: bool = True
    policy_hash: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.enabled and bool(self.policy_hash) and bool(self.policy_id)

"""
Structural Decision Contracts for Verifiable Production Governance.
Pure declarations of intent, expected physical states, and artistic overrides.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    APPLY = "APPLY"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    DEFER = "DEFER"
    CUSTOM = "CUSTOM"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NO_OP = "NO_OP"


class MutationState(str, Enum):
    NOT_MUTATED = "NOT_MUTATED"  # Physical certainty that Live did not mutate
    MUTATED = "MUTATED"          # Physical mutation was performed
    UNKNOWN = "UNKNOWN"          # Partial failure or uncertain mutation state


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResolutionStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    SUSPENDED = "SUSPENDED"
    HARD_FAIL = "HARD_FAIL"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    PROVENANCE_INCOMPLETE = "PROVENANCE_INCOMPLETE"


class OverrideProposal(BaseModel):
    reason: str
    verification_criteria: Optional[Dict[str, Any]] = None
    approved_by: Optional[str] = None


class ExpectedState(BaseModel):
    target_parameter: str
    expected_value: Any
    tolerance: float = 0.04


class StructuralDecisionContract(BaseModel):
    contract_id: str
    decision: DecisionType
    target_track: Optional[str] = None
    target_device: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_state: Optional[ExpectedState] = None
    override_proposal: Optional[OverrideProposal] = None
    is_valid: bool = True
    intent: Optional[str] = None
    justification: Optional[str] = None
    exception_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    contract_hash: Optional[str] = None

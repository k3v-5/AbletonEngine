"""
Exception hierarchy for the Production Intelligence Engine (PIE) Governance Layer.
All errors provide structured error details for auditable diagnosis.
"""
from typing import Dict, Any, Optional


class ProductionError(Exception):
    """Base exception for all production governance, causal graph, and policy errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# --- Model Validation Exceptions (Document 5 Contract) ---

class ModelValidationError(ProductionError, ValueError):
    """Raised when a production model violates its contract."""
    pass


class InvalidNodeTypeError(ModelValidationError):
    """Raised when an invalid or unknown node type is specified."""
    pass


class InvalidEdgeTypeError(ModelValidationError):
    """Raised when an invalid or unknown edge type is specified."""
    pass


class InvalidDecisionStateError(ModelValidationError):
    """Raised when a decision status or transition violates lifecycle rules."""
    pass


class InvalidEvidenceError(ModelValidationError):
    """Raised when evidence records are malformed or invalid."""
    pass


# --- Graph Integrity Exceptions ---

class GraphIntegrityError(ProductionError):
    """Raised when an operation would violate graph integrity (e.g. cycle formation)."""
    pass


class DuplicateNodeError(GraphIntegrityError):
    """Raised when attempting to add a node with an ID that already exists with conflicting data."""
    pass


class NodeNotFoundError(GraphIntegrityError):
    """Raised when referencing a node that does not exist in the graph."""
    pass


class EdgeNotFoundError(GraphIntegrityError):
    """Raised when referencing an edge that does not exist in the graph."""
    pass


# --- Policy Exceptions ---

class PolicyViolationError(ProductionError):
    """Raised when an action or plan violates an unbypassable production policy."""

    def __init__(
        self,
        message: str,
        evaluation: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        eval_dict = evaluation.to_dict() if (evaluation is not None and hasattr(evaluation, "to_dict")) else {}
        merged_details = details or eval_dict
        super().__init__(message, details=merged_details)
        self.evaluation = evaluation



class TransactionRequiredError(PolicyViolationError):
    """Raised when a state-mutating operation is executed without an active transaction."""
    pass


class LockedObjectError(PolicyViolationError):
    """Raised when attempting to mutate an entity that is locked by user or engine."""
    pass


# --- Planning & Execution Exceptions (Document 10 Section 81) ---

class ProductionExecutionError(ProductionError):
    """Base exception for all production execution failures."""
    pass


class StalePlanError(ProductionExecutionError):
    """Raised when attempting to execute a plan whose relevant dependencies have changed."""
    pass


class PlanAlreadyExecutedError(ProductionExecutionError):
    """Raised when attempting to re-execute a plan that has already been committed."""
    pass


class TargetNotFoundError(ProductionExecutionError):
    """Raised when a target track, device, parameter, or clip does not exist."""
    pass


class ExecutionStateUnknownError(ProductionExecutionError):
    """Raised when execution state is ambiguous (e.g. connection drops during mutate call)."""
    pass


class ConcurrentExecutionError(ProductionExecutionError):
    """Raised when an execution cannot acquire the session or target execution lock."""
    pass


class CriticalRecoveryRequiredError(ProductionExecutionError):
    """Raised when the session is in an unverified/inconsistent state requiring manual recovery."""
    pass


class PlanNotFoundError(ProductionError):
    """Raised when a specified production plan cannot be found in memory or storage."""
    pass


class DecisionNotFoundError(ProductionError):
    """Raised when a specified production decision cannot be found in graph or memory."""
    pass


class InvalidPlanError(ProductionError):
    """Raised when a plan definition is malformed or internally contradictory."""
    pass


class ExecutionError(ProductionExecutionError):
    """Raised when staging or committing a planned transaction fails."""
    pass


# --- Verification & Rollback Exceptions ---

class VerificationError(ProductionError):
    """Base exception for all verification failures."""
    pass


class VerificationFailedError(VerificationError):
    """Raised when post-execution verification detects an unhandled acoustic regression or failure."""
    pass


class AcousticRegressionError(VerificationFailedError):
    """Raised when post-execution verification detects an acoustic regression (e.g. true peak clipping, phase collapse)."""
    pass


class InvalidMeasurementError(VerificationError):
    """Raised when an acoustic measurement is missing, corrupt, or mathematically invalid."""
    pass


class VerificationDataMismatchError(VerificationError):
    """Raised when algorithm versions or context data between before and after snapshots mismatch."""
    pass


class RollbackVerificationError(VerificationError):
    """Raised when verifying a rollback reveals the rollback is incomplete or divergent."""
    pass


class RollbackRequiredError(ProductionError):
    """Raised when an automated rollback is triggered and required."""
    pass


class RollbackFailureError(ProductionExecutionError):
    """Raised when an atomic rollback operation fails or restored fingerprint does not match."""
    pass


# Alias for backward compatibility
RollbackError = RollbackFailureError


class RollbackTargetNotFoundError(TargetNotFoundError):
    """Raised when the target decision, action, or transaction to roll back does not exist."""
    pass


class NonReversibleActionError(ProductionExecutionError):
    """Raised when attempting to roll back an action declared as irreversible."""
    pass


class ConflictingStateError(ProductionExecutionError):
    """Raised when the session was modified externally/manually after the target action."""
    pass


class DependencyConflictError(ProductionExecutionError):
    """Raised when subsequent decisions depend on the target decision and scope is SINGLE_DECISION."""
    pass


class InvalidSnapshotError(ProductionExecutionError):
    """Raised when snapshot is missing, corrupted, from another project, or incomplete."""
    pass


class StaleRollbackPlanError(StalePlanError):
    """Raised when the session fingerprint changed in a way that invalidates the rollback plan."""
    pass


class RollbackExecutionInterruptedError(ProductionExecutionError):
    """Raised when socket disconnect or crash occurs during rollback execution, requiring recovery."""
    pass


class MaxRollbackDepthExceededError(ProductionExecutionError):
    """Raised when automatic rollback depth limit is exceeded to prevent infinite loops."""
    pass


class RollbackBlockedLockedObjectError(LockedObjectError):
    """Raised when an entity affected by rollback is locked by user or engine."""
    pass


# --- Persistence & Serialization Exceptions ---

class PersistenceError(ProductionError):
    """Raised when loading or saving production state to disk fails."""
    pass


class SerializationError(PersistenceError):
    """Raised when graph, memory, or plan serialization/deserialization fails or encounters corruption."""
    pass


class ProductionStateCorruptionError(SerializationError):
    """Raised when persisted state (e.g. graph.json) is corrupted on disk."""
    pass


# Alias for backward compatibility
StateCorruptionError = ProductionStateCorruptionError

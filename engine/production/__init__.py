"""
Production Intelligence Engine (PIE) Governance Layer.
Documento 5 — PRODUCTION MODELS & GOVERNANCE CONTRACT (PIE-H1-D05).

Canonical contracts, data models, enumerations, and exceptions for production governance.

ARCHITECTURAL PRINCIPLES:
- Production Models son contratos de dominio, no motores de ejecución.
- Ningún modelo de producción puede ejecutar una acción por sí mismo.
- Toda mutación futura deberá pasar por:
  Policy -> Plan -> Validation -> Transaction -> Execution -> Verification.
- Los modelos existen y se validan completamente sin Ableton Live, MCP, red,
  filesystem ni bibliotecas de grafos externas.
"""

# 1. Canonical Domain Models & Enumerations (Section 49 & Section 58)
from .models import (
    NodeType,
    EdgeType,
    EvidenceType,
    DecisionStatus,
    PolicyResult,
    PolicySeverity,
    PolicyStatus,
    ProductionReference,
    Evidence,
    ProductionIntent,
    ProductionNode,
    ProductionDecision,
    ProductionAction,
    PolicyViolation,
    PolicyEvaluation,
    MeasurementReference,
    VerificationResult,
    RollbackReference,
    ProductionContextSnapshot,
    ProductionCandidate,
    ProductionPlan,
    ProductionResult,
    generate_node_id,
    # Document 10 Models
    ParameterRef,
    DeviceRef,
    ClipRef,
    TrackRef,
    SessionFingerprint,
    PlanValidationResult,
    ExecutionResult,
    # Document 12 Models
    RollbackStatus,
    RollbackType,
    RollbackScope,
    RecoveryStatus,
    IncompleteTransactionState,
    VerificationTolerance,
    RollbackRequest,
    RollbackPlan,
    RollbackResult,
    RecoveryResult,
    RollbackJournalEvent,
)

# 2. Public Exceptions (Section 5 & Section 49, Doc 10 Section 81, Doc 12)
from .exceptions import (
    ProductionError,
    ModelValidationError,
    InvalidNodeTypeError,
    InvalidEdgeTypeError,
    InvalidDecisionStateError,
    InvalidEvidenceError,
    GraphIntegrityError,
    DuplicateNodeError,
    NodeNotFoundError,
    EdgeNotFoundError,
    PolicyViolationError,
    TransactionRequiredError,
    LockedObjectError,
    StalePlanError,
    PlanNotFoundError,
    DecisionNotFoundError,
    ExecutionError,
    VerificationFailedError,
    VerificationError,
    AcousticRegressionError,
    RollbackRequiredError,
    RollbackError,
    PersistenceError,
    SerializationError,
    InvalidPlanError,
    InvalidMeasurementError,
    # Document 10 Exceptions
    ProductionExecutionError,
    PlanAlreadyExecutedError,
    TargetNotFoundError,
    ExecutionStateUnknownError,
    ConcurrentExecutionError,
    CriticalRecoveryRequiredError,
    RollbackFailureError,
    StateCorruptionError,
    # Document 12 Exceptions
    RollbackTargetNotFoundError,
    NonReversibleActionError,
    ConflictingStateError,
    DependencyConflictError,
    InvalidSnapshotError,
    StaleRollbackPlanError,
    RollbackExecutionInterruptedError,
    MaxRollbackDepthExceededError,
    RollbackBlockedLockedObjectError,
    RollbackVerificationError,
)

__all__ = [
    # Canonical Enums
    "NodeType",
    "EdgeType",
    "EvidenceType",
    "DecisionStatus",
    "PolicyResult",
    "PolicySeverity",
    "PolicyStatus",
    # Canonical Models
    "ProductionReference",
    "Evidence",
    "ProductionIntent",
    "ProductionNode",
    "ProductionDecision",
    "ProductionAction",
    "PolicyViolation",
    "PolicyEvaluation",
    "MeasurementReference",
    "VerificationResult",
    "RollbackReference",
    "ProductionContextSnapshot",
    "ProductionCandidate",
    "ProductionPlan",
    "ProductionResult",
    "generate_node_id",
    # Document 10 Models
    "ParameterRef",
    "DeviceRef",
    "ClipRef",
    "TrackRef",
    "SessionFingerprint",
    "PlanValidationResult",
    "ExecutionResult",
    # Public Exceptions
    "ProductionError",
    "ModelValidationError",
    "InvalidNodeTypeError",
    "InvalidEdgeTypeError",
    "InvalidDecisionStateError",
    "InvalidEvidenceError",
    "GraphIntegrityError",
    "DuplicateNodeError",
    "NodeNotFoundError",
    "EdgeNotFoundError",
    "PolicyViolationError",
    "TransactionRequiredError",
    "LockedObjectError",
    "StalePlanError",
    "PlanNotFoundError",
    "DecisionNotFoundError",
    "ExecutionError",
    "VerificationFailedError",
    "VerificationError",
    "AcousticRegressionError",
    "RollbackRequiredError",
    "RollbackError",
    "PersistenceError",
    "SerializationError",
    "InvalidPlanError",
    "InvalidMeasurementError",
    # Document 10 Exceptions
    "ProductionExecutionError",
    "PlanAlreadyExecutedError",
    "TargetNotFoundError",
    "ExecutionStateUnknownError",
    "ConcurrentExecutionError",
    "CriticalRecoveryRequiredError",
    "RollbackFailureError",
    "StateCorruptionError",
    # Document 12 Models
    "RollbackStatus",
    "RollbackType",
    "RollbackScope",
    "RecoveryStatus",
    "IncompleteTransactionState",
    "VerificationTolerance",
    "RollbackRequest",
    "RollbackPlan",
    "RollbackResult",
    "RecoveryResult",
    "RollbackJournalEvent",
    # Document 12 Exceptions
    "RollbackTargetNotFoundError",
    "NonReversibleActionError",
    "ConflictingStateError",
    "DependencyConflictError",
    "InvalidSnapshotError",
    "StaleRollbackPlanError",
    "RollbackExecutionInterruptedError",
    "MaxRollbackDepthExceededError",
    "RollbackBlockedLockedObjectError",
    "RollbackVerificationError",
    # Subsystems
    "RollbackEngine",
    # Completeness Gate
    "ProductionCompletenessGate",
    "CompletenessReport",
    "CompletenessViolation",
    "CompletenessViolationType",
    "RemediationResult",
]


def __getattr__(name: str):
    """
    Lazy accessor for subsystem components (graph, memory, policies, planner, executor, rollback).
    Preserves strict module isolation for `import engine.production` while supporting
    downstream subsystem consumers.
    """
    if name in (
        "ProductionCompletenessGate", "CompletenessReport",
        "CompletenessViolation", "CompletenessViolationType", "RemediationResult"
    ):
        from . import completeness
        return getattr(completeness, name)
    elif name == "ProductionGraph":
        from .graph import ProductionGraph
        return ProductionGraph
    elif name in ("DecisionMemory", "MemoryStatus"):
        from . import memory
        return getattr(memory, name)
    elif name in (
        "ProductionPolicy", "ProductionPolicyEngine", "MasterLimitPolicy",
        "MasterEQPolicy", "MixMasterBoundaryPolicy", "LockedObjectPolicy",
        "TransactionRequiredPolicy", "StalePlanPolicy", "RegressionPolicy"
    ):
        from . import policies
        return getattr(policies, name)
    elif name == "ProductionContext":
        from .context import ProductionContext
        return ProductionContext
    elif name == "ProductionPlanner":
        from .planner import ProductionPlanner
        return ProductionPlanner
    elif name == "ProductionExecutor":
        from .executor import ProductionExecutor
        return ProductionExecutor
    elif name in ("ProductionStorage", "production_storage"):
        from . import serializer
        return getattr(serializer, name)
    elif name == "VerificationMatrix":
        from .verification import VerificationMatrix
        return VerificationMatrix
    elif name in ("RollbackEngine", "DEFAULT_ROLLBACK_TOLERANCES"):
        from . import rollback
        return getattr(rollback, name)
    elif name in (
        "ProductionPhase", "CopilotState", "ExecutiveCopilotEngine",
        "executive_copilot", "MacroProductionRecipes"
    ):
        from . import copilot
        return getattr(copilot, name)
    elif name in (
        "ProductionAPIBoundary", "get_production_boundary", "reset_production_boundary",
        "production_status", "production_plan", "production_validate",
        "production_execute", "production_explain", "production_history",
        "production_graph", "production_rollback", "production_memory_search"
    ):
        from . import boundary
        return getattr(boundary, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

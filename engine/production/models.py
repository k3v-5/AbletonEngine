"""
Canonical Data Models for the Production Intelligence Engine (PIE) Governance Layer.
Documento 5 — PRODUCTION MODELS & GOVERNANCE CONTRACT (PIE-H1-D05).

ARCHITECTURAL INVARIANTS:
1. Production Models son contratos de dominio, no motores de ejecución.
2. Ningún modelo de producción puede ejecutar una acción por sí mismo.
3. Toda mutación futura deberá pasar por:
   Policy -> Plan -> Validation -> Transaction -> Execution -> Verification.
4. Los modelos existen y se validan completamente sin Ableton Live, MCP, red,
   filesystem ni bibliotecas de grafos externas.
"""
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union, Tuple, Mapping
import datetime
import uuid
import copy
import json

from .exceptions import (
    ProductionError,
    ModelValidationError,
    InvalidNodeTypeError,
    InvalidEdgeTypeError,
    InvalidDecisionStateError,
    InvalidEvidenceError,
)


# =====================================================================
# 1. Canonical Enumerations (Document 5 Sections 6 - 11)
# =====================================================================

class NodeType(str, Enum):
    """The 15 canonical node classifications representing production causality."""
    INTENT = "INTENT"                    # High-level prompt / user musical objective
    OBSERVATION = "OBSERVATION"          # Concrete state inspected in Live / environment
    ANALYSIS = "ANALYSIS"                # DSP or theoretical interpretation of observation
    HYPOTHESIS = "HYPOTHESIS"            # Proposed cause or theory behind an issue
    CANDIDATE = "CANDIDATE"              # Candidate intervention to achieve intent or fix issue
    DECISION = "DECISION"                # Concrete choice made among candidates
    POLICY_CHECK = "POLICY_CHECK"        # Evaluation record from the Policy Engine
    SIMULATION = "SIMULATION"            # Dry-run acoustic / structural prediction
    ACTION = "ACTION"                    # Specific physical parameter mutation on an entity
    MEASUREMENT = "MEASUREMENT"          # Post-execution acoustic measurement
    VERIFICATION = "VERIFICATION"        # Formal comparison: expected vs actual delta
    RESULT = "RESULT"                    # Final outcome (SUCCESS, REGRESSION, NO_OP)
    ROLLBACK = "ROLLBACK"                # Rollback action reverting a prior decision
    REJECTION = "REJECTION"              # Discarded candidate with explicit rationale
    NO_OP = "NO_OP"                      # Decision to perform no intervention (already optimal)


class EdgeType(str, Enum):
    """Causal relationship between nodes in the Production DAG (Section 7 & Test 2)."""
    DERIVED_FROM = "DERIVED_FROM"        # A was inferred or computed from B
    CAUSED_BY = "CAUSED_BY"              # A occurred as a consequence of B
    PARENT_OF = "PARENT_OF"              # Hierarchical decomposition (Intent -> Plan -> Action)
    ALTERNATIVE_TO = "ALTERNATIVE_TO"    # A was considered as an alternative to B
    VALIDATED_BY = "VALIDATED_BY"        # A was approved by Policy Check B
    REJECTED_BY = "REJECTED_BY"          # A was declined by Policy Check B
    EXECUTED_BY = "EXECUTED_BY"          # Action A was carried out by Transaction B
    MEASURED_BY = "MEASURED_BY"          # Result A was quantified by Measurement B
    VERIFIED_BY = "VERIFIED_BY"          # Action A was verified by Verification B
    ROLLED_BACK_BY = "ROLLED_BACK_BY"    # Decision/Action A was reverted by Rollback B


class EvidenceType(str, Enum):
    """Classification of causal evidence in the production lineage (Section 8)."""
    FACT = "FACT"
    MEASUREMENT = "MEASUREMENT"
    INFERENCE = "INFERENCE"
    DECISION = "DECISION"
    ACTION = "ACTION"
    RESULT = "RESULT"


class DecisionStatus(str, Enum):
    """Lifecycle state of a production decision (Section 9)."""
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"
    INVALIDATED = "INVALIDATED"
    NO_OP = "NO_OP"
    SUPERSEDED = "SUPERSEDED"            # Alias for backward compatibility with memory.py


class PolicyDecision(str, Enum):
    """Policy evaluation outcome decision (Document 9 Section 6)."""
    ALLOW = "ALLOW"
    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    REJECT = "REJECT"


# Canonical aliases for backward compatibility
PolicyResult = PolicyDecision
PolicyStatus = PolicyDecision


class PolicySeverity(str, Enum):
    """Enforcement severity of a production policy (Section 11)."""
    INFO = "INFO"                        # Informational guideline; no restriction
    WARNING = "WARNING"                  # Acoustic recommendation; allows execution with warning
    ERROR = "ERROR"                      # Rule violation; requires explicit confirmation or alternative
    CRITICAL = "CRITICAL"                # Inviolable guardrail; CANNOT be bypassed by LLM or user flag



def generate_node_id(prefix: str = "prd_node") -> str:
    """Generates a stable, unique node identifier conforming to prd_<type>_<uuid>."""
    clean_prefix = prefix if prefix.startswith("prd_") else f"prd_{prefix}"
    return f"{clean_prefix}_{uuid.uuid4().hex[:12]}"


# =====================================================================
# 2. Canonical Dataclasses (Document 5 Sections 12 - 42)
# =====================================================================

@dataclass(frozen=True)
class ProductionReference:
    """
    Reference to a real object in the Ableton Live project (Section 12 & 13).
    Purely declarative: does not verify whether the object currently exists.
    """
    object_type: str
    object_id: str
    name: Optional[str] = None

    def __post_init__(self):
        if not self.object_type or not str(self.object_type).strip():
            raise ModelValidationError("object_type cannot be empty.")
        if not self.object_id or not isinstance(self.object_id, str) or not str(self.object_id).strip():
            raise ModelValidationError("object_id must be a non-empty string.")
        if self.name is not None and not str(self.name).strip():
            raise ModelValidationError("name, if provided, cannot be an empty string.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "name": self.name
        }


@dataclass(frozen=True)
class Evidence:
    """
    Verifiable piece of acoustic, structural, or user evidence (Section 14 & 15).
    """
    evidence_id: str
    evidence_type: EvidenceType
    source: str
    value: Any
    unit: Optional[str] = None
    confidence: Optional[float] = None
    reference: Optional[ProductionReference] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.evidence_id or not str(self.evidence_id).strip():
            raise ModelValidationError("evidence_id must be a non-empty string.")
        if not self.source or not str(self.source).strip():
            raise ModelValidationError("source must identify the origin.")
        if isinstance(self.evidence_type, str):
            try:
                object.__setattr__(self, "evidence_type", EvidenceType(self.evidence_type))
            except ValueError:
                raise InvalidEvidenceError(f"Invalid evidence_type: {self.evidence_type}")
        elif not isinstance(self.evidence_type, EvidenceType):
            raise InvalidEvidenceError(f"evidence_type must be an EvidenceType enum, got {type(self.evidence_type)}")

        if self.confidence is not None:
            if not (0.0 <= self.confidence <= 1.0):
                raise ModelValidationError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Defensive copy of metadata to prevent mutable contamination
        object.__setattr__(self, "metadata", copy.deepcopy(dict(self.metadata)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "source": self.source,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "reference": self.reference.to_dict() if self.reference else None,
            "metadata": dict(self.metadata)
        }


@dataclass(frozen=True)
class ProductionIntent:
    """
    High-level user musical or technical objective (Section 16 & 17).
    Describes WHAT the user wants to achieve, NOT how to do it.
    """
    intent_id: Optional[str] = None
    description: str = ""
    domain: Optional[str] = None
    target: Optional[str] = "Master"
    project_id: Optional[str] = None
    context: Mapping[str, Any] = field(default_factory=dict)
    text: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def __post_init__(self):
        desc = self.description or self.text
        if not desc or not str(desc).strip():
            raise ModelValidationError("description or text must be a non-empty string.")

        if self.intent_id is not None and not str(self.intent_id).strip():
            raise ModelValidationError("intent_id cannot be an empty string.")

        if self.domain is not None and not str(self.domain).strip():
            raise ModelValidationError("domain cannot be an empty string.")

        if self.project_id is not None and not str(self.project_id).strip():
            raise ModelValidationError("project_id cannot be an empty string.")

        i_id = self.intent_id if self.intent_id else f"intent_{uuid.uuid4().hex[:8]}"
        p_id = self.project_id if self.project_id else "default_project"
        dom = self.domain if self.domain else "mastering"

        object.__setattr__(self, "intent_id", i_id)
        object.__setattr__(self, "description", desc)
        object.__setattr__(self, "text", desc)
        object.__setattr__(self, "domain", dom)
        object.__setattr__(self, "project_id", p_id)
        object.__setattr__(self, "context", copy.deepcopy(dict(self.context)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "description": self.description,
            "domain": self.domain,
            "target": self.target,
            "project_id": self.project_id,
            "context": dict(self.context),
            "created_at": self.created_at
        }


@dataclass(frozen=True)
class ProductionAction:
    """
    Specific physical parameter mutation or structural operation (Section 24 & 25).
    Defaults to transaction_required=True.
    """
    action_id: str
    action_type: str
    target: ProductionReference
    parameters: Mapping[str, Any]
    reversible: bool = True
    transaction_required: bool = True
    expected_delta: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.action_id or not str(self.action_id).strip():
            raise ModelValidationError("action_id must be a non-empty string.")
        if not self.action_type or not str(self.action_type).strip():
            raise ModelValidationError("action_type must be a non-empty string.")
        if not isinstance(self.target, ProductionReference):
            if isinstance(self.target, dict):
                object.__setattr__(self, "target", ProductionReference(**self.target))
            else:
                raise ModelValidationError("target must be a ProductionReference instance.")

        # Defensive copies
        object.__setattr__(self, "parameters", copy.deepcopy(dict(self.parameters)))
        object.__setattr__(self, "expected_delta", copy.deepcopy(dict(self.expected_delta)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target": self.target.to_dict(),
            "parameters": dict(self.parameters),
            "reversible": self.reversible,
            "transaction_required": self.transaction_required,
            "expected_delta": dict(self.expected_delta)
        }


@dataclass(frozen=True)
class PolicyViolation:
    """
    Specific violation record explaining why a policy declined an action (Document 9 Section 7).
    """
    policy_id: str
    severity: PolicySeverity
    message: str
    decision: PolicyDecision = PolicyDecision.REJECT
    code: str = "POLICY_VIOLATION"
    field: Optional[str] = None
    actual_value: Any = None
    expected_value: Any = None
    remediation: Optional[str] = None

    def __post_init__(self):
        if not self.policy_id or not str(self.policy_id).strip():
            raise ModelValidationError("policy_id must be a non-empty string.")
        if not self.message or not str(self.message).strip():
            raise ModelValidationError("message must be a non-empty string.")
        if isinstance(self.severity, str):
            try:
                object.__setattr__(self, "severity", PolicySeverity(self.severity))
            except ValueError:
                raise ModelValidationError(f"Invalid PolicySeverity: {self.severity}")
        if isinstance(self.decision, str):
            try:
                object.__setattr__(self, "decision", PolicyDecision(self.decision))
            except ValueError:
                raise ModelValidationError(f"Invalid PolicyDecision: {self.decision}")

    def __contains__(self, item: str) -> bool:
        """Enables pythonic substring checking: 'gain reduction' in violation."""
        if not isinstance(item, str):
            return False
        return item.lower() in self.message.lower()

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "decision": self.decision.value,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "remediation": self.remediation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyViolation":
        return cls(
            policy_id=data.get("policy_id", "unknown"),
            message=data.get("message", ""),
            decision=PolicyDecision(data["decision"]) if "decision" in data else PolicyDecision.REJECT,
            severity=PolicySeverity(data["severity"]) if "severity" in data else PolicySeverity.ERROR,
            code=data.get("code", "POLICY_VIOLATION"),
            field=data.get("field"),
            actual_value=data.get("actual_value"),
            expected_value=data.get("expected_value"),
            remediation=data.get("remediation")
        )


@dataclass(frozen=True)
class PolicyEvaluation:
    """
    Outcome emitted by the ProductionPolicyEngine (Document 9 Section 8).
    Strict Precedence: CRITICAL -> ERROR -> WARNING -> INFO.
    Inviolable Invariant: CRITICAL violation CAN NEVER be ALLOW or ALLOW_WITH_WARNING.
    """
    decision: PolicyDecision = PolicyDecision.ALLOW
    violations: Tuple[PolicyViolation, ...] = ()
    warnings: Tuple[PolicyViolation, ...] = ()
    evaluated_policy_ids: Tuple[str, ...] = ()
    policy_version: str = "1.0.0"
    context_fingerprint: str = ""
    action_fingerprint: str = ""
    evaluation_fingerprint: str = ""
    requires_confirmation: bool = False
    result: Optional[PolicyDecision] = None
    policy_id: Optional[str] = None
    severity: Optional[PolicySeverity] = None
    required_conditions: Tuple[str, ...] = ()
    alternatives: Tuple[Dict[str, Any], ...] = ()

    def __post_init__(self):
        # Synchronize result and decision
        dec = self.decision
        if self.result is not None:
            dec = self.result

        if isinstance(dec, str):
            try:
                dec = PolicyDecision(dec)
            except ValueError:
                raise ModelValidationError(f"Invalid PolicyDecision: {dec}")

        object.__setattr__(self, "decision", dec)
        object.__setattr__(self, "result", dec)

        # Normalize violations to PolicyViolation objects
        norm_violations: List[PolicyViolation] = []
        for v in self.violations:
            if isinstance(v, PolicyViolation):
                norm_violations.append(v)
            elif isinstance(v, str):
                norm_violations.append(PolicyViolation(
                    policy_id=self.policy_id or "unknown",
                    severity=self.severity or PolicySeverity.ERROR,
                    message=v,
                    decision=PolicyDecision.REJECT
                ))
            elif isinstance(v, dict):
                norm_violations.append(PolicyViolation(**v))
        object.__setattr__(self, "violations", tuple(norm_violations))

        # Normalize warnings
        norm_warnings: List[PolicyViolation] = []
        for w in self.warnings:
            if isinstance(w, PolicyViolation):
                norm_warnings.append(w)
            elif isinstance(w, str):
                norm_warnings.append(PolicyViolation(
                    policy_id=self.policy_id or "unknown",
                    severity=PolicySeverity.WARNING,
                    message=w,
                    decision=PolicyDecision.ALLOW_WITH_WARNING
                ))
            elif isinstance(w, dict):
                norm_warnings.append(PolicyViolation(**w))
        object.__setattr__(self, "warnings", tuple(norm_warnings))

        # Check CRITICAL invariant (Section 11 & 28)
        has_critical = any(v.severity == PolicySeverity.CRITICAL for v in self.violations)
        if has_critical and self.decision in (PolicyDecision.ALLOW, PolicyDecision.ALLOW_WITH_WARNING):
            raise ModelValidationError(
                "CRITICAL violation invariant breached: a CRITICAL violation CANNOT result in ALLOW or ALLOW_WITH_WARNING."
            )

    @property
    def allowed(self) -> bool:
        return self.decision in (PolicyDecision.ALLOW, PolicyDecision.ALLOW_WITH_WARNING)

    @property
    def status(self) -> PolicyDecision:
        return self.decision

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "result": self.decision.value,
            "status": self.decision.value,
            "allowed": self.allowed,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "evaluated_policy_ids": list(self.evaluated_policy_ids),
            "policy_version": self.policy_version,
            "context_fingerprint": self.context_fingerprint,
            "action_fingerprint": self.action_fingerprint,
            "evaluation_fingerprint": self.evaluation_fingerprint,
            "requires_confirmation": self.requires_confirmation,
            "policy_id": self.policy_id,
            "severity": self.severity.value if self.severity else None,
            "required_conditions": list(self.required_conditions),
            "alternatives": [copy.deepcopy(a) for a in self.alternatives]
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializes the PolicyEvaluation to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyEvaluation":
        """Reconstructs PolicyEvaluation from a dictionary without loss of types, enums, or floats."""
        violations = tuple(PolicyViolation.from_dict(v) if isinstance(v, dict) else v for v in data.get("violations", ()))
        warnings = tuple(PolicyViolation.from_dict(w) if isinstance(w, dict) else w for w in data.get("warnings", ()))

        decision_raw = data.get("decision", data.get("result", "ALLOW"))
        decision = PolicyDecision(decision_raw) if isinstance(decision_raw, str) else decision_raw

        sev_raw = data.get("severity")
        severity = PolicySeverity(sev_raw) if isinstance(sev_raw, str) and sev_raw else None

        return cls(
            decision=decision,
            violations=violations,
            warnings=warnings,
            evaluated_policy_ids=tuple(data.get("evaluated_policy_ids", ())),
            policy_version=data.get("policy_version", "1.0.0"),
            context_fingerprint=data.get("context_fingerprint", ""),
            action_fingerprint=data.get("action_fingerprint", ""),
            evaluation_fingerprint=data.get("evaluation_fingerprint", ""),
            requires_confirmation=bool(data.get("requires_confirmation", False)),
            result=decision,
            policy_id=data.get("policy_id"),
            severity=severity,
            required_conditions=tuple(data.get("required_conditions", ())),
            alternatives=tuple(data.get("alternatives", ()))
        )

    @classmethod
    def from_json(cls, json_str: str) -> "PolicyEvaluation":
        """Reconstructs PolicyEvaluation from a JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass(frozen=True)
class ProductionPolicy:
    """
    Metadata representation of a production policy rule (Document 9 Section 9).
    """
    policy_id: str
    name: str
    description: str
    version: str = "1.0.0"
    severity: PolicySeverity = PolicySeverity.CRITICAL
    enabled: bool = True
    domains: Tuple[str, ...] = ("master", "mix")

    def __post_init__(self):
        if not self.policy_id or not str(self.policy_id).strip():
            raise ModelValidationError("policy_id cannot be empty.")
        if not self.name or not str(self.name).strip():
            raise ModelValidationError("name cannot be empty.")
        if not self.version or not str(self.version).strip():
            raise ModelValidationError("version cannot be empty.")
        object.__setattr__(self, "domains", tuple(self.domains))
        if isinstance(self.severity, str):
            try:
                object.__setattr__(self, "severity", PolicySeverity(self.severity))
            except ValueError:
                raise ModelValidationError(f"Invalid PolicySeverity: {self.severity}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "domains": list(self.domains)
        }



@dataclass(frozen=True)
class MeasurementReference:
    """
    Lightweight pointer to an external DSP LoudnessMeasurement (Section 29).
    Prevents duplicating heavy signal arrays or DSP logic in the production layer.
    """
    measurement_id: str
    algorithm_version: str
    captured_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def __post_init__(self):
        if not self.measurement_id or not str(self.measurement_id).strip():
            raise ModelValidationError("measurement_id must be a non-empty string.")
        if not self.algorithm_version or not str(self.algorithm_version).strip():
            raise ModelValidationError("algorithm_version must be a non-empty string.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "algorithm_version": self.algorithm_version,
            "captured_at": self.captured_at
        }


@dataclass(frozen=True)
class VerificationResult:
    """
    Comparison record: expected acoustic delta vs actual delta (Sections 30 & 31).
    Distinguishes RESULT (what occurred) from VERIFICATION (whether it met specs).
    """
    verification_id: str
    passed: bool
    primary_metric_delta: Mapping[str, float]
    regression_metrics: Mapping[str, float]
    violations: Tuple[PolicyViolation, ...] = ()
    expected_delta_met: bool = True
    regression_detected: bool = False
    notes: Tuple[str, ...] = ()

    def __post_init__(self):
        if not self.verification_id or not str(self.verification_id).strip():
            raise ModelValidationError("verification_id must be a non-empty string.")
        object.__setattr__(self, "primary_metric_delta", copy.deepcopy(dict(self.primary_metric_delta)))
        object.__setattr__(self, "regression_metrics", copy.deepcopy(dict(self.regression_metrics)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "passed": self.passed,
            "primary_metric_delta": dict(self.primary_metric_delta),
            "regression_metrics": dict(self.regression_metrics),
            "violations": [v.to_dict() for v in self.violations],
            "expected_delta_met": self.expected_delta_met,
            "regression_detected": self.regression_detected,
            "notes": list(self.notes)
        }


@dataclass(frozen=True)
class RollbackReference:
    """
    Explicit pointer linking a rollback action to the original decision (Sections 32 & 33).
    Preserves audit history: decisions are never physically deleted.
    """
    rollback_id: str
    original_decision_id: str
    transaction_id: str
    reason: str

    def __post_init__(self):
        if not self.rollback_id or not str(self.rollback_id).strip():
            raise ModelValidationError("rollback_id must be a non-empty string.")
        if not self.original_decision_id or not str(self.original_decision_id).strip():
            raise ModelValidationError("original_decision_id must be a non-empty string.")
        if not self.transaction_id or not str(self.transaction_id).strip():
            raise ModelValidationError("transaction_id must be a non-empty string.")
        if not self.reason or not str(self.reason).strip():
            raise ModelValidationError("reason must be a non-empty string.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "original_decision_id": self.original_decision_id,
            "transaction_id": self.transaction_id,
            "reason": self.reason
        }


# =====================================================================
# Reference Contracts (Document 10 Section 43)
# =====================================================================

@dataclass(frozen=True)
class ParameterRef:
    device_id: str
    name: str
    value: float
    min_value: float = 0.0
    max_value: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "value": float(self.value),
            "min_value": float(self.min_value),
            "max_value": float(self.max_value)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterRef":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class DeviceRef:
    track_id: str
    device_id: str
    name: str
    device_type: str = "audio_effect"
    enabled: bool = True
    parameters: Tuple[ParameterRef, ...] = ()

    def __post_init__(self):
        if not isinstance(self.parameters, tuple):
            p_list = []
            for p in self.parameters:
                if isinstance(p, ParameterRef):
                    p_list.append(p)
                elif isinstance(p, dict):
                    p_list.append(ParameterRef.from_dict(p))
                else:
                    p_list.append(p)
            object.__setattr__(self, "parameters", tuple(p_list))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.device_type,
            "enabled": self.enabled,
            "parameters": [p.to_dict() if hasattr(p, "to_dict") else dict(p) for p in self.parameters]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceRef":
        data_copy = dict(data)
        if "parameters" in data_copy and isinstance(data_copy["parameters"], (list, tuple)):
            data_copy["parameters"] = tuple(
                ParameterRef.from_dict(p) if isinstance(p, dict) else p for p in data_copy["parameters"]
            )
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data_copy.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class ClipRef:
    clip_id: str
    track_id: str
    name: str
    start_time: float = 0.0
    length: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "track_id": self.track_id,
            "name": self.name,
            "start_time": float(self.start_time),
            "length": float(self.length)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClipRef":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class TrackRef:
    track_id: str
    name: str
    track_type: str = "audio"
    index: int = 0
    role: Optional[str] = None
    volume: float = 0.85
    pan: float = 0.0
    mute: bool = False
    solo: bool = False
    locked: bool = False
    devices: Tuple[DeviceRef, ...] = ()

    def __post_init__(self):
        if not isinstance(self.devices, tuple):
            d_list = []
            for d in self.devices:
                if isinstance(d, DeviceRef):
                    d_list.append(d)
                elif isinstance(d, dict):
                    d_list.append(DeviceRef.from_dict(d))
                else:
                    d_list.append(d)
            object.__setattr__(self, "devices", tuple(d_list))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "name": self.name,
            "track_type": self.track_type,
            "index": self.index,
            "role": self.role,
            "volume": float(self.volume),
            "pan": float(self.pan),
            "mute": bool(self.mute),
            "solo": bool(self.solo),
            "locked": bool(self.locked),
            "devices": [d.to_dict() if hasattr(d, "to_dict") else dict(d) for d in self.devices]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackRef":
        data_copy = dict(data)
        if "devices" in data_copy and isinstance(data_copy["devices"], (list, tuple)):
            data_copy["devices"] = tuple(
                DeviceRef.from_dict(d) if isinstance(d, dict) else d for d in data_copy["devices"]
            )
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data_copy.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class ProductionContextSnapshot:
    """
    Immutable context snapshot under which a decision or plan was conceived (Sections 34 & 35, Doc 10 Sec 43).
    Stores session_fingerprint without computing it.
    """
    project_id: str
    session_fingerprint: str
    tempo: Optional[float] = None
    key: Optional[str] = None
    genre: Optional[str] = None
    sample_rate: Optional[int] = None
    relevant_object_ids: Tuple[str, ...] = ()
    captured_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    created_at: Optional[str] = None
    session_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    tracks: Tuple[TrackRef, ...] = ()
    devices: Tuple[DeviceRef, ...] = ()
    active_transaction_id: Optional[str] = None
    locks: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.project_id or not str(self.project_id).strip():
            raise ModelValidationError("project_id must be a non-empty string.")
        if not self.session_fingerprint or not str(self.session_fingerprint).strip():
            raise ModelValidationError("session_fingerprint is mandatory and cannot be empty.")
        if self.created_at and not self.captured_at:
            object.__setattr__(self, "captured_at", self.created_at)
        elif self.captured_at and not self.created_at:
            object.__setattr__(self, "created_at", self.captured_at)
        if self.session_id is None:
            object.__setattr__(self, "session_id", self.project_id)
        if self.snapshot_id is None:
            object.__setattr__(self, "snapshot_id", f"snap_{self.session_fingerprint[:8]}")
        if not isinstance(self.relevant_object_ids, tuple):
            object.__setattr__(self, "relevant_object_ids", tuple(self.relevant_object_ids))
        if isinstance(self.tracks, dict):
            t_list = []
            for k, v in self.tracks.items():
                if isinstance(v, dict):
                    t_list.append(TrackRef(track_id=str(k), name=str(k), volume=float(v.get("volume", 0.85))))
                else:
                    t_list.append(TrackRef(track_id=str(k), name=str(k)))
            object.__setattr__(self, "tracks", tuple(t_list))
        elif not isinstance(self.tracks, tuple):
            t_list = []
            for t in self.tracks:
                if isinstance(t, TrackRef):
                    t_list.append(t)
                elif isinstance(t, dict):
                    t_list.append(TrackRef.from_dict(t))
                else:
                    t_list.append(t)
            object.__setattr__(self, "tracks", tuple(t_list))
        if not isinstance(self.devices, tuple):
            d_list = []
            for d in self.devices:
                if isinstance(d, DeviceRef):
                    d_list.append(d)
                elif isinstance(d, dict):
                    d_list.append(DeviceRef.from_dict(d))
                else:
                    d_list.append(d)
            object.__setattr__(self, "devices", tuple(d_list))
        object.__setattr__(self, "locks", copy.deepcopy(dict(self.locks)))

    @property
    def timestamp(self) -> str:
        return self.captured_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "session_id": self.session_id,
            "session_fingerprint": self.session_fingerprint,
            "tempo": self.tempo,
            "key": self.key,
            "genre": self.genre,
            "sample_rate": self.sample_rate,
            "relevant_object_ids": list(self.relevant_object_ids),
            "captured_at": self.captured_at,
            "timestamp": self.captured_at,
            "tracks": [t.to_dict() if hasattr(t, "to_dict") else dict(t) for t in self.tracks],
            "devices": [d.to_dict() if hasattr(d, "to_dict") else dict(d) for d in self.devices],
            "active_transaction_id": self.active_transaction_id,
            "locks": dict(self.locks)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionContextSnapshot":
        data_copy = dict(data)
        if "timestamp" in data_copy and "captured_at" not in data_copy:
            data_copy["captured_at"] = data_copy["timestamp"]
        if "tracks" in data_copy and isinstance(data_copy["tracks"], (list, tuple)):
            data_copy["tracks"] = tuple(
                TrackRef.from_dict(t) if isinstance(t, dict) else t for t in data_copy["tracks"]
            )
        if "devices" in data_copy and isinstance(data_copy["devices"], (list, tuple)):
            data_copy["devices"] = tuple(
                DeviceRef.from_dict(d) if isinstance(d, dict) else d for d in data_copy["devices"]
            )
        if "relevant_object_ids" in data_copy and isinstance(data_copy["relevant_object_ids"], (list, tuple)):
            data_copy["relevant_object_ids"] = tuple(data_copy["relevant_object_ids"])
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data_copy.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class ProductionCandidate:
    """
    Purely declarative candidate strategy (Sections 36, 37, 38).
    Strictly normalized scores: 0.0 to 1.0. No side effects or global references.
    """
    candidate_id: str
    description: str
    actions: Tuple[ProductionAction, ...]
    expected_delta: Mapping[str, float]
    estimated_risk: float
    estimated_impact: float
    reversibility_score: float
    confidence: float

    def __post_init__(self):
        if not self.candidate_id or not str(self.candidate_id).strip():
            raise ModelValidationError("candidate_id must be a non-empty string.")
        if not self.description or not str(self.description).strip():
            raise ModelValidationError("description must be a non-empty string.")

        for name, val in [
            ("estimated_risk", self.estimated_risk),
            ("estimated_impact", self.estimated_impact),
            ("reversibility_score", self.reversibility_score),
            ("confidence", self.confidence)
        ]:
            if not (0.0 <= val <= 1.0):
                raise ModelValidationError(f"{name} must be normalized between 0.0 and 1.0, got {val}")

        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "expected_delta", copy.deepcopy(dict(self.expected_delta)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions],
            "expected_delta": dict(self.expected_delta),
            "estimated_risk": self.estimated_risk,
            "estimated_impact": self.estimated_impact,
            "reversibility_score": self.reversibility_score,
            "confidence": self.confidence
        }


@dataclass(frozen=True)
class ProductionNode:
    """
    Verifiable node in the Production Causal DAG (Sections 18, 19, 20).
    Represents WHY an action occurred or WHAT state justified it.
    Deeply immutable: defensive copying prevents external mutation contamination (Section 51).
    """
    node_id: str
    node_type: NodeType
    project_id: str = "default_project"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    payload: Mapping[str, Any] = field(default_factory=dict)
    evidence: Tuple[Evidence, ...] = ()
    references: Tuple[ProductionReference, ...] = ()
    confidence: Optional[float] = None
    status: Optional[DecisionStatus] = None
    parent_nodes: Tuple[str, ...] = ()
    evidence_type: Optional[EvidenceType] = None
    session_id: str = "default_session"
    source: str = "engine"
    engine: str = "production_intelligence_engine"
    engine_version: str = "1.0.0"
    related_entities: Mapping[str, Any] = field(default_factory=dict)
    transaction_id: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.node_id or not str(self.node_id).strip():
            raise ModelValidationError("node_id must be a non-empty string.")
        if not self.project_id or not str(self.project_id).strip():
            raise ModelValidationError("project_id must be a non-empty string.")

        # Validate node_type
        if isinstance(self.node_type, str):
            try:
                object.__setattr__(self, "node_type", NodeType(self.node_type))
            except ValueError:
                raise InvalidNodeTypeError(f"Invalid NodeType: {self.node_type}")
        elif not isinstance(self.node_type, NodeType):
            raise InvalidNodeTypeError(f"node_type must be a NodeType enum, got {type(self.node_type)}")

        if self.confidence is not None:
            if not (0.0 <= self.confidence <= 1.0):
                raise ModelValidationError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Deep defensive copy to guarantee absolute immutability against outside mutation (Section 51)
        object.__setattr__(self, "payload", copy.deepcopy(dict(self.payload)))
        object.__setattr__(self, "metadata", copy.deepcopy(dict(self.metadata)))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "references", tuple(self.references))
        object.__setattr__(self, "parent_nodes", tuple(self.parent_nodes))

        # Infer evidence type if not provided
        if self.evidence_type is None:
            object.__setattr__(self, "evidence_type", self._infer_evidence_type(self.node_type))
        elif isinstance(self.evidence_type, str):
            object.__setattr__(self, "evidence_type", EvidenceType(self.evidence_type))

    @staticmethod
    def _infer_evidence_type(nt: NodeType) -> EvidenceType:
        if nt == NodeType.OBSERVATION:
            return EvidenceType.FACT
        elif nt == NodeType.MEASUREMENT:
            return EvidenceType.MEASUREMENT
        elif nt in (NodeType.ANALYSIS, NodeType.HYPOTHESIS, NodeType.POLICY_CHECK, NodeType.SIMULATION):
            return EvidenceType.INFERENCE
        elif nt in (NodeType.INTENT, NodeType.CANDIDATE, NodeType.DECISION, NodeType.REJECTION):
            return EvidenceType.DECISION
        elif nt == NodeType.ACTION:
            return EvidenceType.ACTION
        else:
            return EvidenceType.RESULT

    @property
    def parent_ids(self) -> Tuple[str, ...]:
        return self.parent_nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "payload": copy.deepcopy(dict(self.payload)),
            "evidence": [e.to_dict() for e in self.evidence],
            "references": [r.to_dict() for r in self.references],
            "confidence": self.confidence,
            "status": self.status.value if isinstance(self.status, DecisionStatus) else (str(self.status) if self.status else None),
            "parent_nodes": list(self.parent_nodes),
            "evidence_type": self.evidence_type.value if self.evidence_type else None,
            "session_id": self.session_id,
            "source": self.source,
            "transaction_id": self.transaction_id,
            "metadata": copy.deepcopy(dict(self.metadata))
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionNode":
        data_copy = dict(data)
        if "node_type" in data_copy and isinstance(data_copy["node_type"], str):
            data_copy["node_type"] = NodeType(data_copy["node_type"])
        if "evidence_type" in data_copy and data_copy["evidence_type"] is not None:
            data_copy["evidence_type"] = EvidenceType(data_copy["evidence_type"])
        if "parent_ids" in data_copy and "parent_nodes" not in data_copy:
            data_copy["parent_nodes"] = tuple(data_copy.pop("parent_ids"))
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data_copy.items() if k in valid_fields}
        return cls(**filtered)


VALID_DECISION_TRANSITIONS = {
    DecisionStatus.PROPOSED: {DecisionStatus.VALIDATED, DecisionStatus.REJECTED},
    DecisionStatus.VALIDATED: {DecisionStatus.COMMITTED, DecisionStatus.REJECTED},
    DecisionStatus.COMMITTED: {DecisionStatus.ROLLED_BACK, DecisionStatus.SUPERSEDED, DecisionStatus.INVALIDATED},
    DecisionStatus.REJECTED: set(),
    DecisionStatus.ROLLED_BACK: set(),
    DecisionStatus.INVALIDATED: set(),
    DecisionStatus.NO_OP: set(),
    DecisionStatus.SUPERSEDED: set(),
}


@dataclass(frozen=True)
class ProductionDecision:
    """
    Complete causal record of a music production decision (Sections 21, 22, 23).
    Validates COMMITTED invariant: requires candidate, evidence, hypothesis, and rationale
    unless classified as NO_OP.
    """
    decision_id: str
    project_id: str = "default_project"
    category: str = "MIX_CORRECTION"
    target: Optional[Union[ProductionReference, str]] = None
    hypothesis: str = ""
    rationale: str = ""
    status: DecisionStatus = DecisionStatus.PROPOSED
    confidence: float = 1.0
    selected_candidate_id: Optional[str] = None
    evidence_ids: Tuple[str, ...] = ()
    parent_decision_id: Optional[str] = None
    expected_delta: Mapping[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Compatibility fields for earlier executor / memory drafts
    intent_id: str = ""
    domain: Optional[str] = None
    decision_type: Optional[str] = None
    reason: Optional[str] = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    candidate_actions: Tuple[Dict[str, Any], ...] = ()
    selected_action: Mapping[str, Any] = field(default_factory=dict)
    measurements_before: Mapping[str, Any] = field(default_factory=dict)
    measurements_after: Mapping[str, Any] = field(default_factory=dict)
    actual_delta: Mapping[str, Any] = field(default_factory=dict)
    regression: bool = False
    transaction_id: Optional[str] = None
    rollback_available: bool = True
    rollback_id: Optional[str] = None

    def __post_init__(self):
        if not self.decision_id or not str(self.decision_id).strip():
            raise ModelValidationError("decision_id must be a non-empty string.")
        if not (0.0 <= self.confidence <= 1.0):
            raise ModelValidationError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Normalize status
        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", DecisionStatus(self.status))
            except ValueError:
                raise InvalidDecisionStateError(f"Invalid DecisionStatus: {self.status}")

        # Synchronize backward-compatible aliases
        if not self.domain and self.category:
            object.__setattr__(self, "domain", self.category)
        elif not self.category and self.domain:
            object.__setattr__(self, "category", self.domain)

        if not self.rationale and self.reason:
            object.__setattr__(self, "rationale", self.reason)
        elif not self.reason and self.rationale:
            object.__setattr__(self, "reason", self.rationale)

        # Defensive copies
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        object.__setattr__(self, "expected_delta", copy.deepcopy(dict(self.expected_delta)))
        object.__setattr__(self, "actual_delta", copy.deepcopy(dict(self.actual_delta)))
        object.__setattr__(self, "evidence", copy.deepcopy(dict(self.evidence)))

        # Section 22 Invariant: COMMITTED decision requires candidate, evidence, hypothesis, rationale
        # unless it is a NO_OP decision
        if self.status == DecisionStatus.COMMITTED:
            is_no_op = (
                self.category == "NO_OP" or
                self.decision_type == "NO_OP" or
                (isinstance(self.status, DecisionStatus) and self.status == DecisionStatus.NO_OP)
            )
            if not is_no_op:
                if not self.selected_candidate_id:
                    raise ModelValidationError("A COMMITTED decision must specify selected_candidate_id (unless NO_OP).")

                has_evidence = len(self.evidence_ids) > 0 or len(self.evidence) > 0
                if not has_evidence:
                    raise ModelValidationError("A COMMITTED decision requires evidence.")

                if not self.hypothesis or not str(self.hypothesis).strip():
                    raise ModelValidationError("A COMMITTED decision requires a hypothesis.")

                if not self.rationale or not str(self.rationale).strip():
                    raise ModelValidationError("A COMMITTED decision requires a rationale.")

    def transition_to(self, target_status: Union[DecisionStatus, str]) -> "ProductionDecision":
        """Transitions decision status validating lifecycle rules."""
        target = DecisionStatus(target_status) if isinstance(target_status, str) else target_status
        current = self.status
        allowed = VALID_DECISION_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidDecisionStateError(
                f"Invalid decision status transition from '{current.value}' to '{target.value}'. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )
        object.__setattr__(self, "status", target)
        return self

    def to_dict(self) -> Dict[str, Any]:
        target_dict = self.target.to_dict() if isinstance(self.target, ProductionReference) else self.target
        return {
            "decision_id": self.decision_id,
            "project_id": self.project_id,
            "category": self.category,
            "target": target_dict,
            "hypothesis": self.hypothesis,
            "rationale": self.rationale,
            "status": self.status.value if isinstance(self.status, DecisionStatus) else str(self.status),
            "confidence": self.confidence,
            "selected_candidate_id": self.selected_candidate_id,
            "evidence_ids": list(self.evidence_ids),
            "parent_decision_id": self.parent_decision_id,
            "expected_delta": dict(self.expected_delta),
            "created_at": self.created_at,
            "intent_id": self.intent_id,
            "domain": self.domain,
            "decision_type": self.decision_type,
            "reason": self.reason,
            "evidence": dict(self.evidence),
            "candidate_actions": list(self.candidate_actions),
            "selected_action": dict(self.selected_action),
            "measurements_before": dict(self.measurements_before),
            "measurements_after": dict(self.measurements_after),
            "actual_delta": dict(self.actual_delta),
            "regression": self.regression,
            "transaction_id": self.transaction_id,
            "rollback_available": self.rollback_available,
            "rollback_id": self.rollback_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionDecision":
        data_copy = dict(data)
        if "status" in data_copy and isinstance(data_copy["status"], str):
            try:
                data_copy["status"] = DecisionStatus(data_copy["status"])
            except ValueError:
                pass
        if "target" in data_copy and isinstance(data_copy["target"], dict):
            try:
                data_copy["target"] = ProductionReference(**data_copy["target"])
            except Exception:
                pass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data_copy.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class ProductionPlan:
    """
    Declarative production plan (Sections 39 & 40).
    Pure data + decisions + references + validations.
    Never includes sockets, live objects, callbacks, or execution threads.
    """
    plan_id: str
    project_id: str = "default_project"
    intent_id: str = ""
    context: Optional[Union[ProductionContextSnapshot, Mapping[str, Any]]] = None
    candidate_ids: Tuple[str, ...] = ()
    selected_candidate_id: Optional[str] = None
    policy_evaluation: Optional[PolicyEvaluation] = None
    status: DecisionStatus = DecisionStatus.PROPOSED
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Additional fields for compatibility with existing planner / executor
    domain: str = ""
    target: str = ""
    decision_type: str = ""
    actions: Tuple[Any, ...] = ()
    expected_delta: Mapping[str, float] = field(default_factory=dict)
    session_fingerprint: str = ""
    relevant_entities: Tuple[str, ...] = ()
    tolerances: Mapping[str, float] = field(default_factory=dict)
    selected_candidate: Mapping[str, Any] = field(default_factory=dict)
    rejected_candidates: Tuple[Any, ...] = ()
    candidates: Tuple[Any, ...] = ()
    historical_evidence: Tuple[Any, ...] = ()
    policy_result: Mapping[str, Any] = field(default_factory=dict)
    is_no_op: bool = False

    def __post_init__(self):
        if not self.plan_id or not str(self.plan_id).strip():
            raise ModelValidationError("plan_id must be a non-empty string.")
        if not self.project_id or not str(self.project_id).strip():
            raise ModelValidationError("project_id must be a non-empty string.")
        if not self.intent_id or not str(self.intent_id).strip():
            raise ModelValidationError("intent_id must be a non-empty string.")

        # Normalize status
        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", DecisionStatus(self.status))
            except ValueError:
                pass

        object.__setattr__(self, "candidate_ids", tuple(self.candidate_ids))
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "relevant_entities", tuple(self.relevant_entities))
        object.__setattr__(self, "expected_delta", copy.deepcopy(dict(self.expected_delta)))
        object.__setattr__(self, "tolerances", copy.deepcopy(dict(self.tolerances)))

    def transition_to(self, target_status: Union[DecisionStatus, str]) -> "ProductionPlan":
        """Transitions plan status."""
        target = DecisionStatus(target_status) if isinstance(target_status, str) and target_status in [s.value for s in DecisionStatus] else target_status
        object.__setattr__(self, "status", target)
        return self

    def to_dict(self) -> Dict[str, Any]:
        def _to_json_val(val: Any) -> Any:
            if hasattr(val, "to_dict"):
                return val.to_dict()
            elif isinstance(val, (list, tuple)):
                return [_to_json_val(x) for x in val]
            elif isinstance(val, (dict, Mapping)):
                return {k: _to_json_val(v) for k, v in val.items()}
            elif isinstance(val, Enum):
                return val.value
            return val

        ctx_dict = self.context.to_dict() if isinstance(self.context, ProductionContextSnapshot) else (dict(self.context) if self.context else None)
        return {
            "plan_id": self.plan_id,
            "project_id": self.project_id,
            "intent_id": self.intent_id,
            "context": ctx_dict,
            "candidate_ids": list(self.candidate_ids),
            "selected_candidate_id": self.selected_candidate_id,
            "policy_evaluation": self.policy_evaluation.to_dict() if self.policy_evaluation else None,
            "status": self.status.value if isinstance(self.status, DecisionStatus) else str(self.status),
            "created_at": self.created_at,
            "domain": self.domain,
            "target": self.target,
            "decision_type": self.decision_type,
            "actions": [_to_json_val(a) for a in self.actions],
            "expected_delta": dict(self.expected_delta),
            "session_fingerprint": self.session_fingerprint,
            "relevant_entities": list(self.relevant_entities),
            "tolerances": dict(self.tolerances),
            "selected_candidate": _to_json_val(dict(self.selected_candidate)),
            "rejected_candidates": [_to_json_val(r) for r in self.rejected_candidates],
            "candidates": [_to_json_val(c) for c in self.candidates],
            "historical_evidence": [_to_json_val(h) for h in self.historical_evidence],
            "policy_result": _to_json_val(dict(self.policy_result)),
            "is_no_op": self.is_no_op
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionPlan":
        data_copy = dict(data)
        if "status" in data_copy and isinstance(data_copy["status"], str):
            try:
                data_copy["status"] = DecisionStatus(data_copy["status"])
            except ValueError:
                pass
        return cls(**data_copy)


@dataclass(frozen=True)
class ProductionResult:
    """
    Final execution result model (Sections 41 & 42).
    Requires error_code when success=False.
    """
    result_id: str
    plan_id: str
    decision_id: str
    success: bool
    transaction_id: Optional[str] = None
    before_metrics: Mapping[str, float] = field(default_factory=dict)
    after_metrics: Mapping[str, float] = field(default_factory=dict)
    verification: Optional[VerificationResult] = None
    rolled_back: bool = False
    error_code: Optional[str] = None
    message: str = ""

    def __post_init__(self):
        if not self.result_id or not str(self.result_id).strip():
            raise ModelValidationError("result_id must be a non-empty string.")
        if not self.plan_id or not str(self.plan_id).strip():
            raise ModelValidationError("plan_id must be a non-empty string.")
        if not self.decision_id or not str(self.decision_id).strip():
            raise ModelValidationError("decision_id must be a non-empty string.")

        # Section 42 Invariant: If success is False, error_code must exist and be non-empty
        if self.success is False:
            if not self.error_code or not str(self.error_code).strip():
                raise ModelValidationError("A failed ProductionResult (success=False) MUST provide an error_code.")

        object.__setattr__(self, "before_metrics", copy.deepcopy(dict(self.before_metrics)))
        object.__setattr__(self, "after_metrics", copy.deepcopy(dict(self.after_metrics)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "plan_id": self.plan_id,
            "decision_id": self.decision_id,
            "success": self.success,
            "transaction_id": self.transaction_id,
            "before_metrics": dict(self.before_metrics),
            "after_metrics": dict(self.after_metrics),
            "verification": self.verification.to_dict() if self.verification else None,
            "rolled_back": self.rolled_back,
            "error_code": self.error_code,
            "message": self.message
        }


# =====================================================================
# Document 10 Models: Fingerprint, Validation and Execution
# =====================================================================

@dataclass(frozen=True)
class SessionFingerprint:
    """
    Cryptographic SHA-256 fingerprint of Live session state (Document 10 Sections 8-13).
    Ensures safe commit and stale plan rejection.
    """
    value: str
    algorithm: str = "SHA-256"
    algorithm_version: str = "1.0.0"
    scope: str = "PLAN_RELEVANT"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    source_version: str = "PIE-1.0"
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.value or not str(self.value).strip():
            raise ModelValidationError("value must be a non-empty string.")
        object.__setattr__(self, "details", copy.deepcopy(dict(self.details)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "algorithm": self.algorithm,
            "algorithm_version": self.algorithm_version,
            "scope": self.scope,
            "created_at": self.created_at,
            "source_version": self.source_version,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionFingerprint":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class PlanValidationResult:
    """
    Result of validating a ProductionPlan before execution (Document 10 Sections 15 & 38).
    """
    valid: bool
    status: str
    plan_id: str
    expected_fingerprint: str
    actual_fingerprint: str
    violations: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    affected_objects: Tuple[str, ...] = ()
    reason: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.violations, tuple):
            object.__setattr__(self, "violations", tuple(self.violations))
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))
        if not isinstance(self.affected_objects, tuple):
            object.__setattr__(self, "affected_objects", tuple(self.affected_objects))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "status": self.status,
            "plan_id": self.plan_id,
            "expected_fingerprint": self.expected_fingerprint,
            "actual_fingerprint": self.actual_fingerprint,
            "violations": list(self.violations),
            "warnings": list(self.warnings),
            "affected_objects": list(self.affected_objects),
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanValidationResult":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass(frozen=True)
class ExecutionResult:
    """
    Detailed result of executing a ProductionPlan through ProductionExecutor (Document 10 Section 38).
    """
    execution_id: str
    plan_id: str
    status: str
    pre_fingerprint: str
    transaction_id: Optional[str] = None
    post_fingerprint: Optional[str] = None
    actions_attempted: int = 0
    actions_applied: int = 0
    actions_failed: int = 0
    verification_passed: bool = False
    rollback_performed: bool = False
    errors: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    started_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    finished_at: Optional[str] = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.execution_id or not str(self.execution_id).strip():
            raise ModelValidationError("execution_id must be a non-empty string.")
        if not self.plan_id or not str(self.plan_id).strip():
            raise ModelValidationError("plan_id must be a non-empty string.")
        if not isinstance(self.errors, tuple):
            object.__setattr__(self, "errors", tuple(self.errors))
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "details", copy.deepcopy(dict(self.details)))

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "transaction_id": self.transaction_id,
            "status": self.status,
            "pre_fingerprint": self.pre_fingerprint,
            "post_fingerprint": self.post_fingerprint,
            "actions_attempted": self.actions_attempted,
            "actions_applied": self.actions_applied,
            "actions_failed": self.actions_failed,
            "verification_passed": self.verification_passed,
            "rollback_performed": self.rollback_performed,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "details": dict(self.details)
        }
        for k, v in self.details.items():
            if k not in res:
                res[k] = v
        return res

    def __getitem__(self, key: str) -> Any:
        d = self.to_dict()
        if key in d:
            return d[key]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def keys(self):
        return self.to_dict().keys()

    def values(self):
        return self.to_dict().values()

    def items(self):
        return self.to_dict().items()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# =====================================================================
# Document 12 Rollback & Recovery Models (PIE-H1-D12)
# =====================================================================

class RollbackStatus(str, Enum):
    """Lifecycle status for a first-class rollback operation (Doc 12 Sec 4.1)."""
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    ALREADY_REVERTED = "ALREADY_REVERTED"


class RollbackType(str, Enum):
    """Taxonomy of rollback triggers (Doc 12 Sec 5)."""
    USER_REQUESTED = "USER_REQUESTED"
    AUTO_REGRESSION = "AUTO_REGRESSION"
    TRANSACTION_RECOVERY = "TRANSACTION_RECOVERY"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    POLICY_REQUIRED = "POLICY_REQUIRED"
    SYSTEM_RECOVERY = "SYSTEM_RECOVERY"


class RollbackScope(str, Enum):
    """Scope of rollback execution (Doc 12 Sec 15)."""
    SINGLE_DECISION = "SINGLE_DECISION"
    TRANSACTION = "TRANSACTION"
    DEPENDENCY_CHAIN = "DEPENDENCY_CHAIN"


class RecoveryStatus(str, Enum):
    """Crash recovery and transaction journal states (Doc 12 Sec 23)."""
    CLEAN = "CLEAN"
    TRANSACTION_ACTIVE = "TRANSACTION_ACTIVE"
    COMMIT_PENDING = "COMMIT_PENDING"
    ROLLBACK_PENDING = "ROLLBACK_PENDING"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    RECOVERY_IN_PROGRESS = "RECOVERY_IN_PROGRESS"
    RECOVERED = "RECOVERED"
    RECOVERY_FAILED = "RECOVERY_FAILED"


class IncompleteTransactionState(str, Enum):
    """Evaluation of incomplete transaction state on crash recovery (Doc 12 Sec 25)."""
    NOT_STARTED = "NOT_STARTED"
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED"
    FULLY_APPLIED = "FULLY_APPLIED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class VerificationTolerance:
    """Centralized tolerances for post-rollback verification (Doc 12 Sec 19)."""
    absolute: float
    relative: float

    def to_dict(self) -> Dict[str, float]:
        return {"absolute": self.absolute, "relative": self.relative}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationTolerance":
        return cls(absolute=float(data.get("absolute", 0.05)), relative=float(data.get("relative", 0.02)))


@dataclass(frozen=True)
class RollbackRequest:
    """
    Formal request to revert a prior production decision or transaction (Doc 12 Sec 6).
    """
    rollback_id: str
    target_decision_id: str
    requested_by: str
    rollback_type: RollbackType
    reason: str
    created_at: str
    current_session_fingerprint: str
    expected_target_fingerprint: Optional[str] = None
    project_id: str = "default_project"
    scope: RollbackScope = RollbackScope.SINGLE_DECISION
    auto_verify: bool = True
    auto_commit: bool = True
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.rollback_id or not str(self.rollback_id).strip():
            raise ModelValidationError("rollback_id must be a non-empty string.")
        if not self.target_decision_id or not str(self.target_decision_id).strip():
            raise ModelValidationError("target_decision_id must be a non-empty string.")
        if self.rollback_id == self.target_decision_id:
            raise ModelValidationError("rollback_id cannot be identical to target_decision_id.")
        object.__setattr__(self, "details", dict(self.details))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "target_decision_id": self.target_decision_id,
            "requested_by": self.requested_by,
            "rollback_type": self.rollback_type.value if isinstance(self.rollback_type, Enum) else str(self.rollback_type),
            "reason": self.reason,
            "created_at": self.created_at,
            "current_session_fingerprint": self.current_session_fingerprint,
            "expected_target_fingerprint": self.expected_target_fingerprint,
            "project_id": self.project_id,
            "scope": self.scope.value if isinstance(self.scope, Enum) else str(self.scope),
            "auto_verify": self.auto_verify,
            "auto_commit": self.auto_commit,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollbackRequest":
        r_type = RollbackType(data["rollback_type"]) if "rollback_type" in data else RollbackType.USER_REQUESTED
        scope = RollbackScope(data.get("scope", "SINGLE_DECISION"))
        return cls(
            rollback_id=str(data["rollback_id"]),
            target_decision_id=str(data["target_decision_id"]),
            requested_by=str(data.get("requested_by", "USER")),
            rollback_type=r_type,
            reason=str(data.get("reason", "")),
            created_at=str(data.get("created_at", "")),
            current_session_fingerprint=str(data.get("current_session_fingerprint", "")),
            expected_target_fingerprint=data.get("expected_target_fingerprint"),
            project_id=str(data.get("project_id", "default_project")),
            scope=scope,
            auto_verify=bool(data.get("auto_verify", True)),
            auto_commit=bool(data.get("auto_commit", True)),
            details=dict(data.get("details", {}))
        )


@dataclass(frozen=True)
class RollbackPlan:
    """
    Immutable specification of atomic operations needed to restore session state (Doc 12 Sec 7).
    """
    rollback_id: str
    target_decision_id: str
    source_transaction_id: str
    source_snapshot_id: Optional[str]
    pre_rollback_fingerprint: str
    expected_post_rollback_fingerprint: str
    operations: Tuple[Mapping[str, Any], ...]
    protected_objects: Tuple[str, ...]
    verification_requirements: Tuple[str, ...]
    policy_status: str
    created_at: str
    project_id: str = "default_project"
    scope: RollbackScope = RollbackScope.SINGLE_DECISION
    dependent_decisions: Tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.rollback_id or not str(self.rollback_id).strip():
            raise ModelValidationError("rollback_id must be a non-empty string.")
        if not self.target_decision_id or not str(self.target_decision_id).strip():
            raise ModelValidationError("target_decision_id must be a non-empty string.")
        if not isinstance(self.operations, tuple):
            object.__setattr__(self, "operations", tuple(copy.deepcopy(dict(op)) for op in self.operations))
        if not isinstance(self.protected_objects, tuple):
            object.__setattr__(self, "protected_objects", tuple(self.protected_objects))
        if not isinstance(self.verification_requirements, tuple):
            object.__setattr__(self, "verification_requirements", tuple(self.verification_requirements))
        if not isinstance(self.dependent_decisions, tuple):
            object.__setattr__(self, "dependent_decisions", tuple(self.dependent_decisions))
        object.__setattr__(self, "details", dict(self.details))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "target_decision_id": self.target_decision_id,
            "source_transaction_id": self.source_transaction_id,
            "source_snapshot_id": self.source_snapshot_id,
            "pre_rollback_fingerprint": self.pre_rollback_fingerprint,
            "expected_post_rollback_fingerprint": self.expected_post_rollback_fingerprint,
            "operations": [dict(op) for op in self.operations],
            "protected_objects": list(self.protected_objects),
            "verification_requirements": list(self.verification_requirements),
            "policy_status": self.policy_status,
            "created_at": self.created_at,
            "project_id": self.project_id,
            "scope": self.scope.value if isinstance(self.scope, Enum) else str(self.scope),
            "dependent_decisions": list(self.dependent_decisions),
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollbackPlan":
        scope = RollbackScope(data.get("scope", "SINGLE_DECISION"))
        return cls(
            rollback_id=str(data["rollback_id"]),
            target_decision_id=str(data["target_decision_id"]),
            source_transaction_id=str(data.get("source_transaction_id", "")),
            source_snapshot_id=data.get("source_snapshot_id"),
            pre_rollback_fingerprint=str(data.get("pre_rollback_fingerprint", "")),
            expected_post_rollback_fingerprint=str(data.get("expected_post_rollback_fingerprint", "")),
            operations=tuple(dict(op) for op in data.get("operations", [])),
            protected_objects=tuple(data.get("protected_objects", [])),
            verification_requirements=tuple(data.get("verification_requirements", [])),
            policy_status=str(data.get("policy_status", "APPROVED")),
            created_at=str(data.get("created_at", "")),
            project_id=str(data.get("project_id", "default_project")),
            scope=scope,
            dependent_decisions=tuple(data.get("dependent_decisions", [])),
            details=dict(data.get("details", {}))
        )


@dataclass(frozen=True)
class RollbackResult:
    """
    Final verified outcome of executing a RollbackPlan (Doc 12 Sec 63).
    """
    rollback_id: str
    status: RollbackStatus
    transaction_id: str
    operations_planned: int
    operations_applied: int
    structural_verification: str         # "PASS", "FAIL", "SKIPPED"
    fingerprint_verification: str        # "PASS", "FAIL", "SKIPPED"
    acoustic_verification: str           # "PASS", "FAIL", "SKIPPED"
    regressions_detected: Tuple[str, ...]
    conflicts_detected: Tuple[str, ...]
    pre_fingerprint: str
    post_fingerprint: str
    rollback_committed: bool
    recovery_required: bool
    completed_at: str
    target_decision_id: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "transaction_id": self.transaction_id,
            "operations_planned": self.operations_planned,
            "operations_applied": self.operations_applied,
            "structural_verification": self.structural_verification,
            "fingerprint_verification": self.fingerprint_verification,
            "acoustic_verification": self.acoustic_verification,
            "regressions_detected": list(self.regressions_detected),
            "conflicts_detected": list(self.conflicts_detected),
            "pre_fingerprint": self.pre_fingerprint,
            "post_fingerprint": self.post_fingerprint,
            "rollback_committed": self.rollback_committed,
            "recovery_required": self.recovery_required,
            "completed_at": self.completed_at,
            "target_decision_id": self.target_decision_id,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollbackResult":
        status = RollbackStatus(data["status"]) if "status" in data else RollbackStatus.COMMITTED
        return cls(
            rollback_id=str(data["rollback_id"]),
            status=status,
            transaction_id=str(data.get("transaction_id", "")),
            operations_planned=int(data.get("operations_planned", 0)),
            operations_applied=int(data.get("operations_applied", 0)),
            structural_verification=str(data.get("structural_verification", "PASS")),
            fingerprint_verification=str(data.get("fingerprint_verification", "PASS")),
            acoustic_verification=str(data.get("acoustic_verification", "PASS")),
            regressions_detected=tuple(data.get("regressions_detected", ())),
            conflicts_detected=tuple(data.get("conflicts_detected", ())),
            pre_fingerprint=str(data.get("pre_fingerprint", "")),
            post_fingerprint=str(data.get("post_fingerprint", "")),
            rollback_committed=bool(data.get("rollback_committed", False)),
            recovery_required=bool(data.get("recovery_required", False)),
            completed_at=str(data.get("completed_at", "")),
            target_decision_id=str(data.get("target_decision_id", "")),
            details=dict(data.get("details", {}))
        )


@dataclass(frozen=True)
class RecoveryResult:
    """
    Outcome of an automated or requested transaction recovery (Doc 12 Sec 24 & 25).
    """
    transaction_id: str
    recovery_status: RecoveryStatus
    initial_state: IncompleteTransactionState
    strategy: str
    operations_reverted: int
    restored_fingerprint: str
    recovered_at: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "recovery_status": self.recovery_status.value if isinstance(self.recovery_status, Enum) else str(self.recovery_status),
            "initial_state": self.initial_state.value if isinstance(self.initial_state, Enum) else str(self.initial_state),
            "strategy": self.strategy,
            "operations_reverted": self.operations_reverted,
            "restored_fingerprint": self.restored_fingerprint,
            "recovered_at": self.recovered_at,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecoveryResult":
        r_status = RecoveryStatus(data.get("recovery_status", "RECOVERED"))
        init_state = IncompleteTransactionState(data.get("initial_state", "UNKNOWN"))
        return cls(
            transaction_id=str(data["transaction_id"]),
            recovery_status=r_status,
            initial_state=init_state,
            strategy=str(data.get("strategy", "")),
            operations_reverted=int(data.get("operations_reverted", 0)),
            restored_fingerprint=str(data.get("restored_fingerprint", "")),
            recovered_at=str(data.get("recovered_at", "")),
            details=dict(data.get("details", {}))
        )


@dataclass(frozen=True)
class RollbackJournalEvent:
    """
    Append-only journal entry tracking granular rollback steps (Doc 12 Sec 26).
    """
    event_id: str
    rollback_id: str
    transaction_id: str
    event_type: str
    timestamp: str
    operation_index: int = 0
    operation: Mapping[str, Any] = field(default_factory=dict)
    result: Mapping[str, Any] = field(default_factory=dict)
    fingerprint: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "rollback_id": self.rollback_id,
            "transaction_id": self.transaction_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "operation_index": self.operation_index,
            "operation": dict(self.operation),
            "result": dict(self.result),
            "fingerprint": self.fingerprint,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollbackJournalEvent":
        return cls(
            event_id=str(data["event_id"]),
            rollback_id=str(data["rollback_id"]),
            transaction_id=str(data.get("transaction_id", "")),
            event_type=str(data.get("event_type", "")),
            timestamp=str(data.get("timestamp", "")),
            operation_index=int(data.get("operation_index", 0)),
            operation=dict(data.get("operation", {})),
            result=dict(data.get("result", {})),
            fingerprint=str(data.get("fingerprint", "")),
            details=dict(data.get("details", {}))
        )



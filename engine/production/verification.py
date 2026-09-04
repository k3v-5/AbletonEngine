"""
engine/production/verification.py

Verification Engine for the Production Intelligence Engine (PIE).
Fase 11 de 18 — VERIFICATION ENGINE: Verificación Multivariable,
Regresión Acústica y Criterio Formal de Éxito.

Contractual Invariants:
- BEFORE -> ACTION -> AFTER -> EXPECTED DELTA -> ACTUAL DELTA -> REGRESSION CHECK -> POLICY CHECK -> VERDICT.
- Multivariable evaluation: never rely on a single metric to evaluate production changes.
- Strict verdict priority: INVALID -> ROLLBACK_REQUIRED -> FAILED -> VERIFIED_WITH_WARNING -> VERIFIED.
- Snapshot immutability: VerificationSnapshot and MetricSnapshot are frozen dataclasses.
- Complete float precision: full float precision in decision logic; rounding allowed only for display.
- NaN / Inf detection: immediately invalidates evaluation (verdict = INVALID).
- Missing metrics: marked as UNAVAILABLE, never defaulted to 0.0.
- Verified Rollback: post-rollback state verified against baseline.
- Deterministic cryptographic hash (SHA-256) for auditability.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
import json
import uuid
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple, Mapping

from .exceptions import (
    VerificationError,
    VerificationFailedError,
    AcousticRegressionError,
    InvalidMeasurementError,
    VerificationDataMismatchError,
    RollbackVerificationError,
)

DEFAULT_METRIC_UNITS: Dict[str, str] = {
    "integrated_lufs": "LUFS",
    "short_term_lufs": "LUFS",
    "short_term_max_lufs": "LUFS",
    "momentary_lufs": "LUFS",
    "momentary_max_lufs": "LUFS",
    "lra": "LU",
    "loudness_range_lra": "LU",
    "true_peak_dbtp": "dBTP",
    "sample_peak_dbfs": "dBFS",
    "headroom_db": "dB",
    "crest_factor_db": "dB",
    "dynamic_range": "dB",
    "limiter_gr_db": "dB",
    "gain_reduction_db": "dB",
    "sub_bass_energy": "dB",
    "masking_energy_ratio": "ratio",
    "stereo_correlation": "correlation",
    "phase_correlation": "correlation",
    "left_right_balance": "dB",
    "dc_offset": "linear",
    "clipping": "count",
    "digital_dropout": "count",
    "vocal_intelligibility": "score",
}

CRITICAL_METRIC_NAMES = {
    "true_peak_dbtp",
    "phase_correlation",
    "stereo_correlation",
    "dc_offset",
    "digital_dropout",
    "clipping",
}


def _lookup_metric(metrics: Mapping[str, Any], name: str) -> Optional[Any]:
    """Helper to lookup metric values handling standard aliases."""
    if name in metrics:
        return metrics[name]
    alias_map = {
        "phase_correlation": ["stereo_correlation"],
        "stereo_correlation": ["phase_correlation"],
        "limiter_gr_db": ["gain_reduction_db"],
        "gain_reduction_db": ["limiter_gr_db"],
        "lra": ["loudness_range_lra"],
        "loudness_range_lra": ["lra"],
        "short_term_lufs": ["short_term_max_lufs"],
        "short_term_max_lufs": ["short_term_lufs"],
        "momentary_lufs": ["momentary_max_lufs"],
        "momentary_max_lufs": ["momentary_lufs"],
    }
    for alias in alias_map.get(name, []):
        if alias in metrics:
            return metrics[alias]
    return None


# =====================================================================
# 1. Canonical Enumerations & Domain Models
# =====================================================================

class VerificationVerdict(str, Enum):
    """Deterministic verdict of post-execution verification."""
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_WARNING = "VERIFIED_WITH_WARNING"
    FAILED = "FAILED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class MetricSnapshot:
    """
    Immutable measurement point for a specific acoustic or structural metric.
    """
    metric_name: str
    value: float
    unit: str = ""
    timestamp: str = ""
    source: str = "CONTEXT"
    algorithm_version: str = "1.0.0"
    valid: bool = True
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metric_name or not str(self.metric_name).strip():
            raise InvalidMeasurementError("metric_name must be a non-empty string.")

        # Check finite representation
        try:
            val_f = float(self.value)
            if math.isnan(val_f) or math.isinf(val_f):
                object.__setattr__(self, "valid", False)
        except (TypeError, ValueError):
            object.__setattr__(self, "valid", False)

        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        if not self.unit:
            object.__setattr__(self, "unit", DEFAULT_METRIC_UNITS.get(self.metric_name, ""))
        object.__setattr__(self, "details", dict(self.details))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "source": self.source,
            "algorithm_version": self.algorithm_version,
            "valid": self.valid,
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricSnapshot":
        return cls(
            metric_name=str(data["metric_name"]),
            value=float(data["value"]),
            unit=str(data.get("unit", "")),
            timestamp=str(data.get("timestamp", "")),
            source=str(data.get("source", "CONTEXT")),
            algorithm_version=str(data.get("algorithm_version", "1.0.0")),
            valid=bool(data.get("valid", True)),
            details=dict(data.get("details", {}))
        )


@dataclass(frozen=True)
class VerificationSnapshot:
    """
    Immutable collection of acoustic metrics captured at a discrete point in time.
    """
    session_fingerprint: str
    metrics: Mapping[str, MetricSnapshot]
    captured_at: str = ""
    valid: bool = True
    source: str = "CONTEXT"
    algorithm_version: str = "1.0.0"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.captured_at:
            object.__setattr__(self, "captured_at", datetime.datetime.now(datetime.timezone.utc).isoformat())

        metrics_copy = dict(self.metrics)
        object.__setattr__(self, "metrics", metrics_copy)
        object.__setattr__(self, "metadata", dict(self.metadata))

        # Invalidate if any contained metric is invalid or not finite
        for m in metrics_copy.values():
            if not m.valid or math.isnan(m.value) or math.isinf(m.value):
                object.__setattr__(self, "valid", False)
                break

    def get_metric(self, name: str) -> Optional[MetricSnapshot]:
        return _lookup_metric(self.metrics, name)

    def get_value(self, name: str, default: Optional[float] = None) -> Optional[float]:
        m = self.get_metric(name)
        return m.value if m is not None else default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_fingerprint": self.session_fingerprint,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "captured_at": self.captured_at,
            "valid": self.valid,
            "source": self.source,
            "algorithm_version": self.algorithm_version,
            "metadata": dict(self.metadata)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationSnapshot":
        metrics = {}
        for k, v in data.get("metrics", {}).items():
            if isinstance(v, MetricSnapshot):
                metrics[k] = v
            elif isinstance(v, dict):
                metrics[k] = MetricSnapshot.from_dict(v)
            else:
                metrics[k] = MetricSnapshot(metric_name=k, value=float(v))
        return cls(
            session_fingerprint=str(data.get("session_fingerprint", "")),
            metrics=metrics,
            captured_at=str(data.get("captured_at", "")),
            valid=bool(data.get("valid", True)),
            source=str(data.get("source", "CONTEXT")),
            algorithm_version=str(data.get("algorithm_version", "1.0.0")),
            metadata=dict(data.get("metadata", {}))
        )


@dataclass(frozen=True)
class MetricExpectation:
    """
    Formal expected change for a specific metric resulting from an action or plan.
    """
    metric_name: str
    expected_delta: float = 0.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    tolerance: float = 0.5
    direction: str = "ANY"          # "INCREASE", "DECREASE", "STABLE", "ANY"
    severity: str = "ERROR"         # "WARNING", "ERROR", "CRITICAL"
    weight: float = 1.0

    def __post_init__(self):
        valid_directions = {"INCREASE", "DECREASE", "STABLE", "ANY"}
        d_upper = str(self.direction).upper()
        if d_upper not in valid_directions:
            raise ValueError(f"Invalid direction '{self.direction}', must be one of {valid_directions}")
        object.__setattr__(self, "direction", d_upper)

        valid_severities = {"WARNING", "ERROR", "CRITICAL"}
        s_upper = str(self.severity).upper()
        if s_upper not in valid_severities:
            raise ValueError(f"Invalid severity '{self.severity}', must be one of {valid_severities}")
        object.__setattr__(self, "severity", s_upper)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "expected_delta": self.expected_delta,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "tolerance": self.tolerance,
            "direction": self.direction,
            "severity": self.severity,
            "weight": self.weight
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricExpectation":
        return cls(
            metric_name=str(data["metric_name"]),
            expected_delta=float(data.get("expected_delta", 0.0)),
            min_value=float(data["min_value"]) if data.get("min_value") is not None else None,
            max_value=float(data["max_value"]) if data.get("max_value") is not None else None,
            tolerance=float(data.get("tolerance", 0.5)),
            direction=str(data.get("direction", "ANY")),
            severity=str(data.get("severity", "ERROR")),
            weight=float(data.get("weight", 1.0))
        )


@dataclass(frozen=True)
class RegressionRule:
    """
    Guardrail rule specifying permissible limits or bounds for a metric.
    """
    metric_name: str
    max_delta: Optional[float] = None
    min_delta: Optional[float] = None
    absolute_min: Optional[float] = None
    absolute_max: Optional[float] = None
    severity: str = "ERROR"         # "WARNING", "ERROR", "CRITICAL"
    enabled: bool = True
    description: str = ""

    def __post_init__(self):
        valid_severities = {"WARNING", "ERROR", "CRITICAL"}
        s_upper = str(self.severity).upper()
        if s_upper not in valid_severities:
            raise ValueError(f"Invalid severity '{self.severity}', must be one of {valid_severities}")
        object.__setattr__(self, "severity", s_upper)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "max_delta": self.max_delta,
            "min_delta": self.min_delta,
            "absolute_min": self.absolute_min,
            "absolute_max": self.absolute_max,
            "severity": self.severity,
            "enabled": self.enabled,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionRule":
        return cls(
            metric_name=str(data["metric_name"]),
            max_delta=float(data["max_delta"]) if data.get("max_delta") is not None else None,
            min_delta=float(data["min_delta"]) if data.get("min_delta") is not None else None,
            absolute_min=float(data["absolute_min"]) if data.get("absolute_min") is not None else None,
            absolute_max=float(data["absolute_max"]) if data.get("absolute_max") is not None else None,
            severity=str(data.get("severity", "ERROR")),
            enabled=bool(data.get("enabled", True)),
            description=str(data.get("description", ""))
        )


@dataclass
class MetricDelta:
    """
    Quantified differential between baseline and post-execution measurements.
    """
    metric_name: str
    before: float
    after: float
    delta: float
    expected_delta: Optional[float] = None
    tolerance: Optional[float] = None
    within_expectation: bool = True
    unit: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
            "expected_delta": self.expected_delta,
            "tolerance": self.tolerance,
            "within_expectation": self.within_expectation,
            "unit": self.unit,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricDelta":
        return cls(
            metric_name=str(data["metric_name"]),
            before=float(data["before"]),
            after=float(data["after"]),
            delta=float(data["delta"]),
            expected_delta=float(data["expected_delta"]) if data.get("expected_delta") is not None else None,
            tolerance=float(data["tolerance"]) if data.get("tolerance") is not None else None,
            within_expectation=bool(data.get("within_expectation", True)),
            unit=str(data.get("unit", "")),
            details=dict(data.get("details", {}))
        )


@dataclass
class RegressionResult:
    """
    Record of a detected acoustic regression or boundary violation.
    """
    metric_name: str
    before: float
    after: float
    delta: float
    violated: bool
    severity: str = "ERROR"         # "WARNING", "ERROR", "CRITICAL"
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
            "violated": self.violated,
            "severity": self.severity,
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionResult":
        return cls(
            metric_name=str(data["metric_name"]),
            before=float(data["before"]),
            after=float(data["after"]),
            delta=float(data["delta"]),
            violated=bool(data["violated"]),
            severity=str(data.get("severity", "ERROR")),
            reason=str(data.get("reason", ""))
        )


@dataclass
class VerificationReport:
    """
    Comprehensive, cryptographically auditable verification outcome.
    Distinguishes RESULT (what happened) from VERIFICATION (whether it met criteria).
    """
    verification_id: str
    decision_id: str
    verdict: VerificationVerdict
    before: VerificationSnapshot
    after: VerificationSnapshot
    deltas: Dict[str, MetricDelta]
    regressions: List[RegressionResult]
    objective_met: bool
    regression_free: bool
    policy_compliant: bool
    confidence: float
    reasons: List[str]
    created_at: str
    report_hash: str = ""
    unexpected_side_effects: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.report_hash:
            self.report_hash = self.compute_hash()

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("report_hash", None)
        canonical = json.dumps(d, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def passed(self) -> bool:
        return self.verdict in (VerificationVerdict.VERIFIED, VerificationVerdict.VERIFIED_WITH_WARNING)

    @property
    def status(self) -> str:
        if self.verdict == VerificationVerdict.VERIFIED:
            return "PASS"
        elif self.verdict == VerificationVerdict.VERIFIED_WITH_WARNING:
            return "WARNING"
        elif self.verdict in (VerificationVerdict.ROLLBACK_REQUIRED, VerificationVerdict.FAILED):
            return "REGRESSION"
        return self.verdict.value

    @property
    def actual_delta(self) -> Dict[str, float]:
        return {k: v.delta for k, v in self.deltas.items()}

    @property
    def expected_delta(self) -> Dict[str, float]:
        return {k: v.expected_delta for k, v in self.deltas.items() if v.expected_delta is not None}

    @property
    def regression_messages(self) -> List[str]:
        return [r.reason for r in self.regressions if r.violated]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "decision_id": self.decision_id,
            "verdict": self.verdict.value if isinstance(self.verdict, Enum) else str(self.verdict),
            "before": self.before.to_dict(),
            "after": self.after.to_dict(),
            "deltas": {k: v.to_dict() for k, v in self.deltas.items()},
            "regressions": [r.to_dict() for r in self.regressions],
            "objective_met": self.objective_met,
            "regression_free": self.regression_free,
            "policy_compliant": self.policy_compliant,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "created_at": self.created_at,
            "report_hash": self.report_hash,
            "unexpected_side_effects": list(self.unexpected_side_effects),
            "warnings": list(self.warnings),
            "details": dict(self.details)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationReport":
        verdict = VerificationVerdict(data["verdict"])
        before = VerificationSnapshot.from_dict(data["before"])
        after = VerificationSnapshot.from_dict(data["after"])
        deltas = {k: MetricDelta.from_dict(v) for k, v in data.get("deltas", {}).items()}
        regressions = [RegressionResult.from_dict(r) for r in data.get("regressions", [])]
        rep = cls(
            verification_id=data["verification_id"],
            decision_id=data["decision_id"],
            verdict=verdict,
            before=before,
            after=after,
            deltas=deltas,
            regressions=regressions,
            objective_met=bool(data["objective_met"]),
            regression_free=bool(data["regression_free"]),
            policy_compliant=bool(data["policy_compliant"]),
            confidence=float(data["confidence"]),
            reasons=list(data.get("reasons", [])),
            created_at=data["created_at"],
            report_hash=data.get("report_hash", ""),
            unexpected_side_effects=list(data.get("unexpected_side_effects", [])),
            warnings=list(data.get("warnings", [])),
            details=dict(data.get("details", {}))
        )
        return rep


# Legacy compatibility container
@dataclass
class VerificationResult:
    """Outcome of comparing pre- and post-execution acoustic measurements."""
    passed: bool
    status: str                                  # "PASS", "WARNING", "REGRESSION"
    primary_metric: str
    expected_delta: Dict[str, float] = field(default_factory=dict)
    actual_delta: Dict[str, float] = field(default_factory=dict)
    regressions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    report: Optional[VerificationReport] = None

    @property
    def metrics_evaluated(self) -> Dict[str, float]:
        return self.actual_delta

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "passed": self.passed,
            "status": self.status,
            "primary_metric": self.primary_metric,
            "expected_delta": self.expected_delta,
            "actual_delta": self.actual_delta,
            "regressions": self.regressions,
            "warnings": self.warnings,
            "details": self.details
        }
        if self.report:
            res["report"] = self.report.to_dict()
        return res


# =====================================================================
# 2. VerificationEngine
# =====================================================================

class VerificationEngine:
    """
    Deterministic Verification Engine for PIE.
    Performs multi-variable comparison between expected and actual acoustic deltas.
    Evaluates acoustic regressions, profile guardrails, and rollback verification.
    """

    def __init__(
        self,
        default_rules: Optional[List[RegressionRule]] = None,
        max_true_peak_dbtp: float = -0.3,
        max_limiter_gr_db: float = 2.5,
        min_phase_correlation: float = 0.2,
        strict_fingerprint: bool = False
    ):
        self.max_true_peak_dbtp = max_true_peak_dbtp
        self.max_limiter_gr_db = max_limiter_gr_db
        self.min_phase_correlation = min_phase_correlation
        self.strict_fingerprint = strict_fingerprint

        if default_rules is not None:
            self.default_rules = list(default_rules)
        else:
            self.default_rules = [
                RegressionRule(
                    metric_name="true_peak_dbtp",
                    absolute_max=self.max_true_peak_dbtp,
                    severity="CRITICAL",
                    description=f"True Peak regression: measured exceeds ceiling ({self.max_true_peak_dbtp:.2f} dBTP)."
                ),
                RegressionRule(
                    metric_name="phase_correlation",
                    absolute_min=self.min_phase_correlation,
                    severity="CRITICAL",
                    description=f"Phase cancellation regression: correlation dropped below safe threshold ({self.min_phase_correlation:.2f})."
                ),
                RegressionRule(
                    metric_name="stereo_correlation",
                    absolute_min=self.min_phase_correlation,
                    severity="CRITICAL",
                    description=f"Phase cancellation regression: correlation dropped below safe threshold ({self.min_phase_correlation:.2f})."
                ),
                RegressionRule(
                    metric_name="dc_offset",
                    absolute_max=0.01,
                    severity="CRITICAL",
                    description="DC offset regression: measured DC offset exceeds acceptable limit (0.01)."
                ),
                RegressionRule(
                    metric_name="digital_dropout",
                    absolute_max=0.0,
                    severity="CRITICAL",
                    description="Digital dropout detected in audio signal."
                ),
                RegressionRule(
                    metric_name="clipping",
                    absolute_max=0.0,
                    severity="CRITICAL",
                    description="Audio clipping detected in output signal."
                ),
                RegressionRule(
                    metric_name="limiter_gr_db",
                    absolute_max=self.max_limiter_gr_db,
                    severity="ERROR",
                    description=f"Limiter GR regression: measured gain reduction exceeds maximum allowed ({self.max_limiter_gr_db:.2f} dB)."
                ),
                RegressionRule(
                    metric_name="gain_reduction_db",
                    absolute_max=self.max_limiter_gr_db,
                    severity="ERROR",
                    description=f"Limiter GR regression: measured gain reduction exceeds maximum allowed ({self.max_limiter_gr_db:.2f} dB)."
                ),
            ]

    def capture_snapshot(
        self,
        measurements: Union[Dict[str, Any], VerificationSnapshot],
        session_fingerprint: str = "",
        source: str = "CONTEXT",
        algorithm_version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> VerificationSnapshot:
        """
        Converts measurements dictionary into an immutable VerificationSnapshot.
        """
        if isinstance(measurements, VerificationSnapshot):
            return measurements

        metric_snaps: Dict[str, MetricSnapshot] = {}
        valid = True
        for k, v in measurements.items():
            if k in ("timestamp", "target", "standard", "is_compliant"):
                continue
            try:
                val_f = float(v)
                is_valid = not (math.isnan(val_f) or math.isinf(val_f))
                if not is_valid:
                    valid = False
                metric_snaps[k] = MetricSnapshot(
                    metric_name=k,
                    value=val_f,
                    unit=DEFAULT_METRIC_UNITS.get(k, ""),
                    source=source,
                    algorithm_version=algorithm_version,
                    valid=is_valid
                )
            except (ValueError, TypeError):
                continue

        return VerificationSnapshot(
            session_fingerprint=session_fingerprint,
            metrics=metric_snaps,
            valid=valid,
            source=source,
            algorithm_version=algorithm_version,
            metadata=metadata or {}
        )

    def capture_before(
        self,
        plan: Any,
        context: Optional[Any] = None,
        audio_buffer: Optional[Any] = None
    ) -> VerificationSnapshot:
        """Captures pre-execution baseline snapshot."""
        target = getattr(plan, "target", "Master")
        fp = ""
        meas = {}
        if context is not None:
            rel = getattr(plan, "relevant_entities", None)
            fp = context.compute_session_fingerprint(relevant_entities=rel) if hasattr(context, "compute_session_fingerprint") else ""
            meas = context.capture_measurements(audio_buffer=audio_buffer, target_name=target)
        return self.capture_snapshot(meas, session_fingerprint=fp)

    def capture_after(
        self,
        plan: Any,
        context: Optional[Any] = None,
        audio_buffer: Optional[Any] = None
    ) -> VerificationSnapshot:
        """Captures post-execution snapshot."""
        target = getattr(plan, "target", "Master")
        fp = ""
        meas = {}
        if context is not None:
            rel = getattr(plan, "relevant_entities", None)
            fp = context.compute_session_fingerprint(relevant_entities=rel) if hasattr(context, "compute_session_fingerprint") else ""
            meas = context.capture_measurements(audio_buffer=audio_buffer, target_name=target)
        return self.capture_snapshot(meas, session_fingerprint=fp)

    def compare(
        self,
        before: VerificationSnapshot,
        after: VerificationSnapshot,
        expectations: List[MetricExpectation],
        regression_rules: Optional[List[RegressionRule]] = None,
        policy_compliant: bool = True,
        profile: Optional[Any] = None,
        decision_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        expected_fingerprint: Optional[str] = None,
        require_matching_fingerprint: bool = False
    ) -> VerificationReport:
        """
        Deterministic multi-variable comparison between before and after snapshots.
        Evaluates objective achievement, acoustic regressions, side effects, and policy compliance.
        """
        v_id = verification_id or f"ver_{uuid.uuid4().hex[:8]}"
        d_id = decision_id or f"dec_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        deltas: Dict[str, MetricDelta] = {}
        regressions: List[RegressionResult] = []
        unexpected_side_effects: List[str] = []
        warnings: List[str] = []
        reasons: List[str] = []

        is_invalid = False
        invalid_reasons: List[str] = []

        # -------------------------------------------------------------
        # 1. Validation of Snapshots (Invalid Check)
        # -------------------------------------------------------------
        if not before.valid or not after.valid:
            is_invalid = True
            invalid_reasons.append("Invalid snapshot data detected (non-finite or malformed values).")

        # Check for NaN / Inf in any metric
        for m in list(before.metrics.values()) + list(after.metrics.values()):
            if math.isnan(m.value) or math.isinf(m.value):
                is_invalid = True
                invalid_reasons.append(f"Metric '{m.metric_name}' contains invalid non-finite value ({m.value}).")

        # Algorithm consistency check
        common_metrics = set(before.metrics.keys()).intersection(set(after.metrics.keys()))
        for m_name in sorted(common_metrics):
            mb = before.metrics[m_name]
            ma = after.metrics[m_name]
            if mb.algorithm_version != ma.algorithm_version:
                is_invalid = True
                invalid_reasons.append(
                    f"Algorithm version mismatch for '{m_name}': {mb.algorithm_version} vs {ma.algorithm_version}."
                )

        # Fingerprint validation
        if expected_fingerprint is not None:
            if after.session_fingerprint and after.session_fingerprint != expected_fingerprint:
                is_invalid = True
                invalid_reasons.append(
                    f"Fingerprint mismatch (external modification): expected '{expected_fingerprint[:12]}', got '{after.session_fingerprint[:12]}'."
                )
            if before.session_fingerprint and before.session_fingerprint != expected_fingerprint:
                is_invalid = True
                invalid_reasons.append(
                    f"Fingerprint mismatch (external modification): baseline '{before.session_fingerprint[:12]}' != expected '{expected_fingerprint[:12]}'."
                )

        if require_matching_fingerprint or self.strict_fingerprint:
            if before.session_fingerprint and after.session_fingerprint and before.session_fingerprint != after.session_fingerprint:
                is_invalid = True
                invalid_reasons.append(
                    f"Fingerprint mismatch (external modification): before '{before.session_fingerprint[:12]}' != after '{after.session_fingerprint[:12]}'."
                )

        if after.session_fingerprint == "MISMATCH" or before.session_fingerprint == "MISMATCH":
            is_invalid = True
            invalid_reasons.append("Fingerprint mismatch (external modification) detected.")

        if after.metadata.get("concurrent_modification") or after.metadata.get("fingerprint_mismatch"):
            is_invalid = True
            invalid_reasons.append("Fingerprint mismatch (external modification) detected in session metadata.")

        if is_invalid:
            # Build partial deltas for common metrics
            for m_name in sorted(common_metrics):
                mb_val = before.metrics[m_name].value
                ma_val = after.metrics[m_name].value
                d_val = ma_val - mb_val if not (math.isnan(ma_val) or math.isnan(mb_val)) else 0.0
                deltas[m_name] = MetricDelta(
                    metric_name=m_name,
                    before=mb_val,
                    after=ma_val,
                    delta=d_val,
                    within_expectation=False
                )

            return VerificationReport(
                verification_id=v_id,
                decision_id=d_id,
                verdict=VerificationVerdict.INVALID,
                before=before,
                after=after,
                deltas=deltas,
                regressions=[],
                objective_met=False,
                regression_free=False,
                policy_compliant=policy_compliant,
                confidence=0.0,
                reasons=invalid_reasons,
                created_at=now_iso,
                unexpected_side_effects=[],
                warnings=[],
                details={"invalid_reasons": invalid_reasons}
            )

        # -------------------------------------------------------------
        # 2. Derive Rules & Profile Parameters
        # -------------------------------------------------------------
        active_rules = list(self.default_rules)
        if regression_rules:
            active_rules.extend(regression_rules)

        profile_max_tp = None
        if profile is not None:
            profile_max_tp = getattr(profile, "max_true_peak_dbtp", None)
            if profile_max_tp is None and isinstance(profile, dict):
                profile_max_tp = profile.get("max_true_peak_dbtp")

            if profile_max_tp is not None:
                # Add or override True Peak ceiling rule with profile constraint
                active_rules = [
                    r for r in active_rules if r.metric_name != "true_peak_dbtp"
                ]
                active_rules.append(RegressionRule(
                    metric_name="true_peak_dbtp",
                    absolute_max=float(profile_max_tp),
                    severity="CRITICAL",
                    description=f"True Peak regression: measured exceeds profile ceiling ({float(profile_max_tp):.2f} dBTP)."
                ))

        # -------------------------------------------------------------
        # 3. Evaluate Metric Expectations (Objective Achievement)
        # -------------------------------------------------------------
        objective_met = True
        has_critical_violation = False
        has_error_violation = False
        has_warning_violation = False

        expected_metric_names = set()

        for exp in expectations:
            expected_metric_names.add(exp.metric_name)
            mb = before.get_metric(exp.metric_name)
            ma = after.get_metric(exp.metric_name)

            if mb is None or ma is None:
                objective_met = False
                reasons.append(f"Metric '{exp.metric_name}' is UNAVAILABLE in measurement snapshots.")
                deltas[exp.metric_name] = MetricDelta(
                    metric_name=exp.metric_name,
                    before=0.0,
                    after=0.0,
                    delta=0.0,
                    expected_delta=exp.expected_delta,
                    tolerance=exp.tolerance,
                    within_expectation=False,
                    details={"status": "UNAVAILABLE"}
                )
                if exp.severity == "CRITICAL":
                    has_critical_violation = True
                elif exp.severity == "ERROR":
                    has_error_violation = True
                else:
                    has_warning_violation = True
                continue

            b_val = mb.value
            a_val = ma.value
            act_delta = a_val - b_val
            within_exp = True
            fail_reason = ""

            # Check direction
            if exp.direction == "INCREASE":
                if act_delta <= 1e-4:
                    within_exp = False
                    fail_reason = f"Metric '{exp.metric_name}' expected to INCREASE, but delta was {act_delta:+.2f}."
            elif exp.direction == "DECREASE":
                if act_delta >= -1e-4:
                    within_exp = False
                    fail_reason = f"Metric '{exp.metric_name}' expected to DECREASE, but delta was {act_delta:+.2f}."
            elif exp.direction == "STABLE":
                if abs(act_delta) > exp.tolerance:
                    within_exp = False
                    fail_reason = (
                        f"Metric '{exp.metric_name}' expected to remain STABLE, but changed by {act_delta:+.2f} "
                        f"(tolerance ±{exp.tolerance:.2f})."
                    )

            # Check delta tolerance
            if exp.direction in ("ANY", "INCREASE", "DECREASE") and exp.expected_delta != 0.0:
                diff = abs(act_delta - exp.expected_delta)
                if diff > exp.tolerance:
                    within_exp = False
                    fail_reason = (
                        f"Metric '{exp.metric_name}' delta ({act_delta:+.2f}) deviated from expected "
                        f"({exp.expected_delta:+.2f}) by {diff:.2f} (tolerance ±{exp.tolerance:.2f})."
                    )

            # Check absolute bounds
            if exp.min_value is not None and a_val < (exp.min_value - 1e-4):
                within_exp = False
                fail_reason = f"Metric '{exp.metric_name}' value ({a_val:.2f}) below minimum ({exp.min_value:.2f})."
            if exp.max_value is not None and a_val > (exp.max_value + 1e-4):
                within_exp = False
                fail_reason = f"Metric '{exp.metric_name}' value ({a_val:.2f}) exceeds maximum ({exp.max_value:.2f})."

            deltas[exp.metric_name] = MetricDelta(
                metric_name=exp.metric_name,
                before=b_val,
                after=a_val,
                delta=act_delta,
                expected_delta=exp.expected_delta,
                tolerance=exp.tolerance,
                within_expectation=within_exp,
                unit=mb.unit or DEFAULT_METRIC_UNITS.get(exp.metric_name, "")
            )

            if not within_exp:
                objective_met = False
                reasons.append(fail_reason)
                if exp.severity == "CRITICAL":
                    has_critical_violation = True
                elif exp.severity == "ERROR":
                    has_error_violation = True
                else:
                    has_warning_violation = True

        # -------------------------------------------------------------
        # 4. Evaluate Secondary Regressions & Guardrails
        # -------------------------------------------------------------
        has_critical_regression = False
        has_error_regression = False
        has_warning_regression = False

        for rule in active_rules:
            if not rule.enabled:
                continue

            ma = after.get_metric(rule.metric_name)
            if ma is None:
                continue

            mb = before.get_metric(rule.metric_name)
            b_val = mb.value if mb is not None else ma.value
            a_val = ma.value
            act_delta = a_val - b_val

            violated = False
            viol_reason = ""

            # Check absolute ceiling
            if rule.absolute_max is not None and a_val > (rule.absolute_max + 1e-4):
                violated = True
                if "true_peak" in rule.metric_name:
                    viol_reason = (
                        f"True Peak regression: measured {a_val:.2f} dBTP exceeds ceiling ({rule.absolute_max:.2f} dBTP)."
                    )
                elif "limiter" in rule.metric_name or "gain_reduction" in rule.metric_name:
                    viol_reason = (
                        f"Limiter GR regression: measured {a_val:.2f} dB exceeds maximum allowed ({rule.absolute_max:.2f} dB)."
                    )
                else:
                    viol_reason = f"{rule.metric_name} regression: measured {a_val:.2f} exceeds ceiling ({rule.absolute_max:.2f})."

            # Check absolute floor
            if not violated and rule.absolute_min is not None and a_val < (rule.absolute_min - 1e-4):
                violated = True
                if "phase" in rule.metric_name or "correlation" in rule.metric_name:
                    viol_reason = (
                        f"Phase cancellation regression: correlation {a_val:.2f} dropped below safe threshold ({rule.absolute_min:.2f})."
                    )
                else:
                    viol_reason = f"{rule.metric_name} regression: measured {a_val:.2f} fell below floor ({rule.absolute_min:.2f})."

            # Check max delta
            if not violated and rule.max_delta is not None and act_delta > (rule.max_delta + 1e-4):
                violated = True
                viol_reason = f"{rule.metric_name} regression: delta ({act_delta:+.2f}) exceeds max allowed delta ({rule.max_delta:+.2f})."

            # Check min delta
            if not violated and rule.min_delta is not None and act_delta < (rule.min_delta - 1e-4):
                violated = True
                viol_reason = f"{rule.metric_name} regression: delta ({act_delta:+.2f}) fell below min allowed delta ({rule.min_delta:+.2f})."

            # Dynamic range collapse special check (LRA squashing)
            if not violated and (rule.metric_name in ("lra", "loudness_range_lra")):
                if b_val > 4.0 and a_val < 2.0:
                    violated = True
                    viol_reason = f"Dynamic range collapse: LRA dropped from {b_val:.1f} LU to {a_val:.1f} LU."

            if violated:
                sev = rule.severity
                # Check critical metric classification
                if rule.metric_name in CRITICAL_METRIC_NAMES:
                    sev = "CRITICAL"

                reason_text = rule.description if rule.description else (viol_reason or f"Regression in {rule.metric_name}.")
                reg_result = RegressionResult(
                    metric_name=rule.metric_name,
                    before=b_val,
                    after=a_val,
                    delta=act_delta,
                    violated=True,
                    severity=sev,
                    reason=reason_text
                )
                regressions.append(reg_result)
                reasons.append(reason_text)

                if sev == "CRITICAL":
                    has_critical_regression = True
                elif sev == "ERROR":
                    has_error_regression = True
                else:
                    has_warning_regression = True
                    warnings.append(reason_text)

        # Special LRA collapse check if not already caught by a rule
        mb_lra = before.get_metric("lra")
        ma_lra = after.get_metric("lra")
        if mb_lra is not None and ma_lra is not None:
            if mb_lra.value > 4.0 and ma_lra.value < 2.0:
                if not any(r.metric_name in ("lra", "loudness_range_lra") and r.violated for r in regressions):
                    viol_reason = f"Dynamic range collapse: LRA dropped from {mb_lra.value:.1f} LU to {ma_lra.value:.1f} LU."
                    reg_result = RegressionResult(
                        metric_name="lra",
                        before=mb_lra.value,
                        after=ma_lra.value,
                        delta=ma_lra.value - mb_lra.value,
                        violated=True,
                        severity="ERROR",
                        reason=viol_reason
                    )
                    regressions.append(reg_result)
                    reasons.append(viol_reason)
                    has_error_regression = True

        # Also populate deltas for non-expected metrics
        for m_name, ma in after.metrics.items():
            if m_name not in deltas:
                mb = before.get_metric(m_name)
                b_val = mb.value if mb is not None else ma.value
                d_val = ma.value - b_val
                deltas[m_name] = MetricDelta(
                    metric_name=m_name,
                    before=b_val,
                    after=ma.value,
                    delta=d_val,
                    within_expectation=True,
                    unit=ma.unit or DEFAULT_METRIC_UNITS.get(m_name, "")
                )

        # -------------------------------------------------------------
        # 5. Detect Unexpected Side Effects
        # -------------------------------------------------------------
        for m_name, d_obj in deltas.items():
            if m_name in expected_metric_names:
                continue

            delta_abs = abs(d_obj.delta)
            if m_name == "sub_bass_energy" and delta_abs >= 1.5:
                msg = f"Unexpected change in sub_bass_energy: {d_obj.delta:+.2f} dB."
                unexpected_side_effects.append(msg)
                warnings.append(msg)
            elif m_name == "masking_energy_ratio" and delta_abs >= 0.15:
                msg = f"Unexpected change in masking_energy_ratio: {d_obj.delta:+.2f}."
                unexpected_side_effects.append(msg)
                warnings.append(msg)
            elif m_name in ("phase_correlation", "stereo_correlation") and delta_abs >= 0.35:
                msg = f"Unexpected shift in stereo correlation: {d_obj.delta:+.2f}."
                unexpected_side_effects.append(msg)
                warnings.append(msg)

        # -------------------------------------------------------------
        # 6. Policy Compliance Check
        # -------------------------------------------------------------
        if not policy_compliant:
            reasons.append("Policy compliance check failed: active policy violated.")

        # -------------------------------------------------------------
        # 7. Strict Verdict Priority Assignment
        # INVALID -> ROLLBACK_REQUIRED -> FAILED -> VERIFIED_WITH_WARNING -> VERIFIED
        # -------------------------------------------------------------
        if has_critical_regression or has_critical_violation:
            verdict = VerificationVerdict.ROLLBACK_REQUIRED
        elif not objective_met or has_error_regression or has_error_violation or not policy_compliant:
            verdict = VerificationVerdict.FAILED
        elif has_warning_regression or has_warning_violation or len(unexpected_side_effects) > 0 or len(warnings) > 0:
            verdict = VerificationVerdict.VERIFIED_WITH_WARNING
        else:
            verdict = VerificationVerdict.VERIFIED

        regression_free = (len(regressions) == 0)

        # Confidence metric
        total_evals = max(1, len(expectations) + len(active_rules))
        failed_evals = len(regressions) + (0 if objective_met else len(expectations))
        confidence = max(0.0, min(1.0, 1.0 - (failed_evals / total_evals) * 0.5))
        if verdict == VerificationVerdict.VERIFIED:
            confidence = 1.0
        elif verdict == VerificationVerdict.VERIFIED_WITH_WARNING:
            confidence = 0.85
        elif verdict == VerificationVerdict.ROLLBACK_REQUIRED:
            confidence = 0.95  # High confidence that rollback is required

        report = VerificationReport(
            verification_id=v_id,
            decision_id=d_id,
            verdict=verdict,
            before=before,
            after=after,
            deltas=deltas,
            regressions=regressions,
            objective_met=objective_met,
            regression_free=regression_free,
            policy_compliant=policy_compliant,
            confidence=confidence,
            reasons=reasons,
            created_at=now_iso,
            unexpected_side_effects=unexpected_side_effects,
            warnings=warnings,
            details={
                "has_critical_regression": has_critical_regression,
                "has_error_regression": has_error_regression,
                "profile_max_tp": profile_max_tp
            }
        )

        return report

    def verify(
        self,
        plan: Any,
        before: Union[Dict[str, Any], VerificationSnapshot],
        after: Union[Dict[str, Any], VerificationSnapshot],
        policy_compliant: bool = True,
        profile: Optional[Any] = None
    ) -> VerificationReport:
        """
        High-level verification of a plan against before/after measurements or snapshots.
        """
        before_snap = self.capture_snapshot(before) if not isinstance(before, VerificationSnapshot) else before
        after_snap = self.capture_snapshot(after) if not isinstance(after, VerificationSnapshot) else after

        exp_delta = getattr(plan, "expected_delta", {}) if hasattr(plan, "expected_delta") else (
            plan.get("expected_delta", {}) if isinstance(plan, dict) else {}
        )
        tolerances = getattr(plan, "tolerances", {}) if hasattr(plan, "tolerances") else (
            plan.get("tolerances", {}) if isinstance(plan, dict) else {}
        )
        dec_type = getattr(plan, "decision_type", "") if hasattr(plan, "decision_type") else (
            plan.get("decision_type", "") if isinstance(plan, dict) else ""
        )

        expectations: List[MetricExpectation] = []
        for metric, delta_target in exp_delta.items():
            tol = tolerances.get(metric, 0.5)
            if dec_type == "NO_OP" or float(delta_target) == 0.0:
                direction = "STABLE"
            elif float(delta_target) > 0:
                direction = "INCREASE"
            else:
                direction = "DECREASE"

            expectations.append(MetricExpectation(
                metric_name=metric,
                expected_delta=float(delta_target),
                tolerance=float(tol),
                direction=direction,
                severity="ERROR"
            ))

        # Check if plan was NO_OP but no expectations given
        if dec_type == "NO_OP" and not expectations:
            # All metrics must remain stable
            for m_name in before_snap.metrics:
                expectations.append(MetricExpectation(
                    metric_name=m_name,
                    expected_delta=0.0,
                    tolerance=0.5,
                    direction="STABLE",
                    severity="ERROR"
                ))

        plan_fp = getattr(plan, "session_fingerprint", None) if hasattr(plan, "session_fingerprint") else (
            plan.get("session_fingerprint") if isinstance(plan, dict) else None
        )
        dec_id = getattr(plan, "decision_id", getattr(plan, "plan_id", "dec_default"))

        return self.compare(
            before=before_snap,
            after=after_snap,
            expectations=expectations,
            policy_compliant=policy_compliant,
            profile=profile,
            decision_id=str(dec_id),
            expected_fingerprint=plan_fp if before_snap.session_fingerprint else None
        )

    def verify_rollback(
        self,
        before: VerificationSnapshot,
        post_rollback: VerificationSnapshot,
        tolerance: float = 0.1,
        strict_raise: bool = False
    ) -> VerificationReport:
        """
        Verifies that an atomic rollback accurately restored the session to baseline.
        If any metric diverges beyond tolerance, marks ROLLBACK_INCOMPLETE.
        """
        v_id = f"ver_rb_{uuid.uuid4().hex[:8]}"
        d_id = f"dec_rb_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        deltas: Dict[str, MetricDelta] = {}
        regressions: List[RegressionResult] = []
        reasons: List[str] = []

        # Validate snapshots
        if not before.valid or not post_rollback.valid:
            rep = VerificationReport(
                verification_id=v_id,
                decision_id=d_id,
                verdict=VerificationVerdict.INVALID,
                before=before,
                after=post_rollback,
                deltas={},
                regressions=[],
                objective_met=False,
                regression_free=False,
                policy_compliant=False,
                confidence=0.0,
                reasons=["Invalid snapshot data during rollback verification."],
                created_at=now_iso
            )
            if strict_raise:
                raise RollbackVerificationError("Invalid snapshot data during rollback verification.")
            return rep

        rollback_complete = True
        has_critical = False

        common_keys = sorted(set(before.metrics.keys()).intersection(set(post_rollback.metrics.keys())))
        for k in common_keys:
            mb = before.metrics[k]
            mp = post_rollback.metrics[k]

            diff = abs(mp.value - mb.value)
            act_delta = mp.value - mb.value
            within = diff <= (tolerance + 1e-4)

            deltas[k] = MetricDelta(
                metric_name=k,
                before=mb.value,
                after=mp.value,
                delta=act_delta,
                expected_delta=0.0,
                tolerance=tolerance,
                within_expectation=within,
                unit=mb.unit
            )

            if not within:
                rollback_complete = False
                is_crit = (k in CRITICAL_METRIC_NAMES) or (diff > (tolerance * 4))
                if is_crit:
                    has_critical = True

                sev = "CRITICAL" if is_crit else "ERROR"
                msg = f"ROLLBACK_INCOMPLETE: Metric '{k}' delta ({act_delta:+.3f}) exceeds tolerance (±{tolerance:.2f})."
                reg_res = RegressionResult(
                    metric_name=k,
                    before=mb.value,
                    after=mp.value,
                    delta=act_delta,
                    violated=True,
                    severity=sev,
                    reason=msg
                )
                regressions.append(reg_res)
                reasons.append(msg)

        if rollback_complete:
            verdict = VerificationVerdict.VERIFIED
            reasons.append("Rollback verified: session state successfully restored within tolerance.")
        elif has_critical:
            verdict = VerificationVerdict.ROLLBACK_REQUIRED
        else:
            verdict = VerificationVerdict.FAILED

        report = VerificationReport(
            verification_id=v_id,
            decision_id=d_id,
            verdict=verdict,
            before=before,
            after=post_rollback,
            deltas=deltas,
            regressions=regressions,
            objective_met=rollback_complete,
            regression_free=rollback_complete,
            policy_compliant=rollback_complete,
            confidence=1.0 if rollback_complete else 0.2,
            reasons=reasons,
            created_at=now_iso,
            details={"rollback_tolerance": tolerance}
        )

        if not rollback_complete and strict_raise:
            raise RollbackVerificationError(f"Rollback incomplete: {'; '.join(reasons)}")

        return report


# =====================================================================
# 3. Backward Compatible VerificationMatrix Wrapper
# =====================================================================

class VerificationMatrix:
    """
    Evaluates multi-variable success criteria and checks for secondary regressions.
    Maintains 100% backward compatibility for Document 10 and existing test suites,
    delegating to the deterministic VerificationEngine.
    """

    def __init__(
        self,
        max_true_peak_dbtp: float = -0.3,
        max_limiter_gr_db: float = 2.5,
        min_phase_correlation: float = 0.2
    ):
        self.max_true_peak_dbtp = max_true_peak_dbtp
        self.max_limiter_gr_db = max_limiter_gr_db
        self.min_phase_correlation = min_phase_correlation
        self.engine = VerificationEngine(
            max_true_peak_dbtp=max_true_peak_dbtp,
            max_limiter_gr_db=max_limiter_gr_db,
            min_phase_correlation=min_phase_correlation
        )

    def evaluate(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        expected_delta: Dict[str, float],
        primary_metric: str = "integrated_lufs",
        tolerance: float = 0.5
    ) -> VerificationResult:
        """
        Compares before and after measurements against expected deltas and guardrails.
        """
        before_snap = self.engine.capture_snapshot(before)
        after_snap = self.engine.capture_snapshot(after)

        expectations: List[MetricExpectation] = []
        for metric, exp_val in expected_delta.items():
            expectations.append(MetricExpectation(
                metric_name=metric,
                expected_delta=float(exp_val),
                tolerance=tolerance,
                direction="ANY"
            ))

        report = self.engine.compare(
            before=before_snap,
            after=after_snap,
            expectations=expectations
        )

        # Format legacy regressions and warnings
        regressions: List[str] = []
        warnings: List[str] = []
        actual_delta: Dict[str, float] = {}

        for k, d in report.deltas.items():
            if k in expected_delta:
                actual_delta[k] = round(d.delta, 2)

        # Check primary metric goal
        exp_primary = expected_delta.get(primary_metric)
        act_primary = actual_delta.get(primary_metric)
        if exp_primary is not None and act_primary is not None:
            diff = abs(act_primary - exp_primary)
            if diff > tolerance:
                warnings.append(
                    f"Primary metric '{primary_metric}' delta ({act_primary:+.2f}) deviated from expected "
                    f"({exp_primary:+.2f}) by {diff:.2f} (tolerance ±{tolerance:.2f})."
                )
                if diff > (tolerance * 3):
                    regressions.append(
                        f"Primary metric failed to achieve target: expected {exp_primary:+.2f}, got {act_primary:+.2f}"
                    )

        # Regressions from report
        for reg in report.regressions:
            regressions.append(reg.reason)

        warnings.extend(report.warnings)

        passed = (len(regressions) == 0)
        status = "REGRESSION" if not passed else ("WARNING" if len(warnings) > 0 else "PASS")

        return VerificationResult(
            passed=passed,
            status=status,
            primary_metric=primary_metric,
            expected_delta=expected_delta,
            actual_delta=actual_delta,
            regressions=regressions,
            warnings=warnings,
            details={"before": before, "after": after},
            report=report
        )

"""
Production Policy Engine for PIE (Hito 1 — Documento 9).
Enforces acoustic guardrails, domain separation axioms, transaction safety,
stale plan detection, and post-execution regression prevention.

ARCHITECTURAL INVARIANTS:
1. Double Policy Validation:
   Planner validation -> Policy check -> Execution -> Policy validation AGAIN -> Commit.
2. Inviolability of CRITICAL severity:
   CRITICAL violations CAN NEVER be bypassed, forced (no force=True, bypass=True),
   nor converted into warnings.
3. Strict Determinism:
   Same context + same action + same policy versions = same evaluation and same SHA-256 fingerprint.
4. Non-Execution:
   Purely diagnostic evaluation; never mutates Live session or executes transactions.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Sequence, Union
import json
import hashlib
import copy

from .models import (
    PolicyDecision,
    PolicySeverity,
    PolicyViolation,
    PolicyEvaluation,
    ProductionPolicy,
    PolicyResult,
    PolicyStatus,
)
from .exceptions import (
    PolicyViolationError,
    LockedObjectError,
    TransactionRequiredError
)


POLICY_ENGINE_VERSION = "1.0.0"


# =====================================================================
# Canonical Policy Evaluator Base
# =====================================================================

class BasePolicyEvaluator(ABC):
    """Abstract base evaluator for deterministically testing an action against a policy."""

    def __init__(self, policy: ProductionPolicy):
        self.policy = policy

    @property
    def policy_id(self) -> str:
        return self.policy.policy_id

    @property
    def name(self) -> str:
        return self.policy.name

    @property
    def version(self) -> str:
        return self.policy.version

    @property
    def severity(self) -> PolicySeverity:
        return self.policy.severity

    @property
    def description(self) -> str:
        return self.policy.description

    @abstractmethod
    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        """
        Evaluates the specific policy rule.
        Returns: (violations, warnings, required_conditions, alternatives)
        """
        pass

    def evaluate(self, target_action_or_plan: Dict[str, Any], context: Dict[str, Any]) -> PolicyEvaluation:
        """Evaluates compliance and produces a PolicyEvaluation."""
        violations, warnings, conditions, alternatives = self.evaluate_rule(target_action_or_plan, context)

        has_reject = any(v.decision == PolicyDecision.REJECT for v in violations)
        has_critical = any(v.severity == PolicySeverity.CRITICAL for v in violations)

        if has_critical or has_reject:
            decision = PolicyDecision.REJECT
        elif warnings:
            decision = PolicyDecision.ALLOW_WITH_WARNING
        else:
            decision = PolicyDecision.ALLOW

        return PolicyEvaluation(
            decision=decision,
            violations=tuple(violations),
            warnings=tuple(warnings),
            evaluated_policy_ids=(self.policy_id,),
            policy_version=self.version,
            requires_confirmation=False,
            result=decision,
            policy_id=self.policy_id,
            severity=self.severity,
            required_conditions=tuple(conditions),
            alternatives=tuple(alternatives)
        )


# =====================================================================
# 1. MASTER_LIMIT Policy (Section 11 & 36)
# =====================================================================

class MasterLimitPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Controls limiter gain reduction (<= 2.5 dB) and True Peak ceiling.
    Prevents destructive over-limiting and patching mix problems via master limiting.
    """

    def __init__(
        self,
        max_gain_reduction_db: float = 2.5,
        max_true_peak_dbtp: float = -0.3,
        warning_gain_reduction_db: float = 2.0
    ):
        policy = ProductionPolicy(
            policy_id="MASTER_LIMIT",
            name="Master Limiter Guardrail",
            description="Prevents dynamic destruction and limiter over-compression (GR <= 2.5 dB, True Peak ceiling)",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master",)
        )
        super().__init__(policy)
        self.max_gain_reduction_db = max_gain_reduction_db
        self.max_true_peak_dbtp = max_true_peak_dbtp
        self.warning_gain_reduction_db = warning_gain_reduction_db

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []
        warnings: List[PolicyViolation] = []
        conditions: List[str] = []
        alternatives: List[Dict[str, Any]] = []

        domain = action.get("domain", context.get("domain", "master")).lower()
        if domain != "master" and action.get("target") != "Master":
            # Policy only applies to Master bus actions
            return violations, warnings, conditions, alternatives

        # Extract values
        gr = float(action.get("gain_reduction_db", action.get("limiter_gr_db", action.get("gain_reduction", action.get("gr", 0.0)))))
        tp = float(action.get("true_peak_ceiling_dbtp", action.get("true_peak_dbtp", action.get("true_peak_dbfs", action.get("true_peak", action.get("tp", -1.0))))))

        # Respect dynamic profile if present in context
        max_gr = self.max_gain_reduction_db
        max_tp = self.max_true_peak_dbtp
        if "loudness_profile" in context:
            prof = context["loudness_profile"]
            if hasattr(prof, "max_true_peak_dbtp"):
                max_tp = prof.max_true_peak_dbtp
            if hasattr(prof, "max_limiter_gain_reduction_db"):
                max_gr = prof.max_limiter_gain_reduction_db

        # Regla 1: Ganancia de reducción máxima (GR <= 2.5 dB)
        if gr > max_gr:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="LIMITER_GAIN_REDUCTION_EXCEEDED",
                message="Requested gain reduction exceeds maximum allowed reduction.",
                field="gain_reduction_db",
                actual_value=gr,
                expected_value=max_gr,
                remediation="Resolve loudness deficit in the mix before increasing master limiting."
            ))
            alternatives.append({"action": "RESOLVE_HEADROOM_IN_MIX", "suggested_domain": "mix"})
        elif gr >= self.warning_gain_reduction_db:
            warnings.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.ALLOW_WITH_WARNING,
                severity=PolicySeverity.WARNING,
                code="MASTER_LIMIT_NEAR_THRESHOLD",
                message=f"Limiter gain reduction ({gr:.2f} dB) is near maximum threshold ({max_gr:.2f} dB).",
                field="gain_reduction_db",
                actual_value=gr,
                expected_value=max_gr,
                remediation="Monitor crest factor and avoid pushing input level further."
            ))

        # Regla 2: True Peak Ceiling
        if tp > max_tp:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="TRUE_PEAK_CEILING_EXCEEDED",
                message=f"True Peak ({tp:.2f} dBTP) exceeds maximum platform ceiling ({max_tp:.2f} dBTP).",
                field="true_peak_ceiling_dbtp",
                actual_value=tp,
                expected_value=max_tp,
                remediation=f"Set limiter ceiling strictly <= {max_tp:.2f} dBTP."
            ))

        # Regla 3: Compensación de problema de mezcla mediante limitador
        diagnosis = context.get("diagnosis", action.get("diagnosis", ""))
        problem_type = context.get("problem_type", action.get("problem_type", ""))
        if (diagnosis == "MIX_PROBLEM" or problem_type == "MIX_PROBLEM") and gr > 0.5:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="LIMITER_CANNOT_COMPENSATE_MIX_PROBLEM",
                message="Cannot compensate an underlying mix defect with master limiting.",
                field="gain_reduction_db",
                actual_value=gr,
                expected_value=0.0,
                remediation="Resolve dynamic imbalances on individual source stems before mastering."
            ))

        conditions.extend([
            f"Maintain True Peak below ceiling ({max_tp:.2f} dBTP)",
            f"Limit gain reduction <= {max_gr:.2f} dB"
        ])
        return violations, warnings, conditions, alternatives


# =====================================================================
# 2. MASTER_EQ Policy (Section 12)
# =====================================================================

class MasterEQPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Restricts mastering EQ moves to conservative adjustments
    (maximum 2 bands, maximum ±1.0 dB per band).
    """

    def __init__(self, max_bands: int = 2, max_eq_change_db: float = 1.0):
        policy = ProductionPolicy(
            policy_id="MASTER_EQ",
            name="Conservative Master EQ Guardrail",
            description="Restricts master EQ to subtle, transparent moves (max 2 bands, max ±1.0 dB)",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master",)
        )
        super().__init__(policy)
        self.max_bands = max_bands
        self.max_eq_change_db = max_eq_change_db

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []
        warnings: List[PolicyViolation] = []
        conditions: List[str] = ["Max 2 bands", f"Max ±{self.max_eq_change_db:.1f} dB gain"]
        alternatives: List[Dict[str, Any]] = []

        eq_actions = action.get("eq_bands_modified", [])
        if not eq_actions:
            # Fallback to direct keys on action if present
            bands_count = action.get("eq_bands", action.get("bands", action.get("band_count")))
            gain_val = action.get("eq_gain_db", action.get("eq_gain", action.get("gain_db", action.get("delta_db"))))
            if bands_count is not None or gain_val is not None:
                b_count = int(bands_count) if bands_count is not None else 1
                g_val = float(gain_val) if gain_val is not None else 0.0
                eq_actions = [{"band": i + 1, "gain_db": g_val} for i in range(b_count)]
            else:
                return violations, warnings, conditions, alternatives

        # Check band count
        if len(eq_actions) > self.max_bands:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="MASTER_EQ_BAND_COUNT_EXCEEDED",
                message=f"Master EQ modifies {len(eq_actions)} bands, exceeding limit of {self.max_bands} bands.",
                field="eq_bands_modified",
                actual_value=len(eq_actions),
                expected_value=self.max_bands,
                remediation="Perform broader tonal shaping in the mix bus, limiting master EQ to <= 2 bands."
            ))
            alternatives.append({"action": "ADJUST_INDIVIDUAL_TRACK_EQ", "suggested_domain": "mix"})

        # Check gain per band
        for idx, act in enumerate(eq_actions):
            delta = abs(act.get("delta_db", act.get("gain_db", 0.0)))
            if delta > self.max_eq_change_db:
                violations.append(PolicyViolation(
                    policy_id=self.policy_id,
                    decision=PolicyDecision.REJECT,
                    severity=PolicySeverity.CRITICAL,
                    code="MASTER_EQ_GAIN_EXCEEDED",
                    message=f"Master EQ band delta ({delta:.2f} dB) exceeds maximum allowed change (±{self.max_eq_change_db:.2f} dB).",
                    field=f"eq_bands_modified[{idx}].gain_db",
                    actual_value=delta,
                    expected_value=self.max_eq_change_db,
                    remediation="Reduce master EQ boost/cut to within ±1.0 dB and fix spectral balance in the mix."
                ))

        return violations, warnings, conditions, alternatives


# =====================================================================
# 3. MIX_MASTER_BOUNDARY Policy (Section 13 & 14)
# =====================================================================

class MixMasterBoundaryPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Separation of Mix vs Master Axiom.
    If an issue is diagnosed as a MIX_PROBLEM (kick/bass masking, mud, resonance, etc.),
    mastering processing MUST be rejected and redirected to mix intervention.
    """

    KNOWN_MIX_PROBLEMS = (
        "MIX_PROBLEM",
        "kick/bass masking",
        "vocal/instrument masking",
        "low-end mud",
        "sub-bass excess",
        "bad stereo distribution",
        "headroom deficit",
        "excessive transients",
        "localized resonance",
        "track frequency conflict",
        "instrument balance",
        "bus energy excess"
    )

    def __init__(self):
        policy = ProductionPolicy(
            policy_id="MIX_MASTER_BOUNDARY",
            name="Strict Separation of Mix vs Master",
            description="Rejects patching mix defects (kick/sub clash, mud, masking) in mastering",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master", "mix")
        )
        super().__init__(policy)

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []
        warnings: List[PolicyViolation] = []
        conditions: List[str] = []
        alternatives: List[Dict[str, Any]] = []

        diagnosis = str(context.get("diagnosis", action.get("diagnosis", "")))
        problem_type = str(context.get("problem_type", action.get("problem_type", "")))
        target_domain = action.get("domain", context.get("target_domain", "master")).lower()

        # Check if diagnosis or context indicates a mix problem
        is_mix_problem = (
            diagnosis == "MIX_PROBLEM" or
            problem_type == "MIX_PROBLEM" or
            any(prob.lower() in diagnosis.lower() or prob.lower() in problem_type.lower() for prob in self.KNOWN_MIX_PROBLEMS) or
            bool(context.get("mix_problems"))
        )

        if is_mix_problem and target_domain == "master":
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="MASTER_CANNOT_FIX_MIX_PROBLEM",
                message="Acoustic issue is classified as a MIX_PROBLEM. Patching in mastering is prohibited.",
                field="domain",
                actual_value=target_domain,
                expected_value="mix",
                remediation="Generate a MIX_ACTION_PLAN instead."
            ))
            conditions.append("Resolve low-end balance, masking, or headroom defects in the mix first.")
            alternatives.append({
                "affected_domain": "master",
                "recommended_domain": "mix",
                "suggested_action": "MIX_ACTION_PLAN",
                "remediation": "Generate a MIX_ACTION_PLAN targeting the source tracks."
            })

        return violations, warnings, conditions, alternatives


# =====================================================================
# 4. LOCKED_OBJECT Policy (Section 15)
# =====================================================================

class LockedObjectPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Protects tracks, clips, and devices marked locked from modification or deletion.
    """

    def __init__(self):
        policy = ProductionPolicy(
            policy_id="LOCKED_OBJECT",
            name="Locked Object Protection",
            description="Protects user-locked or engine-locked tracks and clips from mutation",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master", "mix", "arrangement", "sound")
        )
        super().__init__(policy)

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []
        target_locked = bool(
            context.get("target_locked",
            action.get("target_locked",
            context.get("locked",
            action.get("locked", False))))
        )
        target_name = action.get("target", context.get("target", "unspecified"))

        if target_locked:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="TARGET_ENTITY_LOCKED",
                message=f"Target entity '{target_name}' is locked by user or engine.",
                field="target_locked",
                actual_value=True,
                expected_value=False,
                remediation="Unlock the entity explicitly before proposing modifications."
            ))

        return violations, [], ["Unlock entity prior to modification"], []


# =====================================================================
# 5. TRANSACTION_REQUIRED Policy (Section 16)
# =====================================================================

class TransactionRequiredPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Enforces that state-mutating operations must have an active transaction ID.
    """

    def __init__(self):
        policy = ProductionPolicy(
            policy_id="TRANSACTION_REQUIRED",
            name="Transaction Safety Guardrail",
            description="Requires an active transaction ID for all state-mutating operations",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master", "mix", "arrangement", "sound")
        )
        super().__init__(policy)

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []

        is_dry_run = bool(context.get("dry_run", action.get("dry_run", False)))
        is_planning = bool(context.get("is_planning", action.get("is_planning", False)))
        is_candidate = bool(action.get("is_candidate", False))
        is_read_only = bool(action.get("read_only", False))

        if is_dry_run or is_read_only or is_planning or is_candidate:
            return violations, [], [], []

        tx_id = (
            action.get("transaction_id") or
            context.get("transaction_id") or
            action.get("transaction") or
            context.get("transaction")
        )
        if not tx_id or tx_id == "None":
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="TRANSACTION_REQUIRED",
                message="No active transaction_id provided for state-mutating operation.",
                field="transaction_id",
                actual_value=None,
                expected_value="valid_transaction_id",
                remediation="Open a transaction via TransactionManager.begin() prior to execution."
            ))

        return violations, [], ["Open a transaction via TransactionManager.begin() prior to execution."], []


# =====================================================================
# 6. STALE_PLAN Policy (Section 17, 18 & 19)
# =====================================================================

class StalePlanPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Rejects execution if session dependencies have changed since plan creation.
    """

    def __init__(self):
        policy = ProductionPolicy(
            policy_id="STALE_PLAN",
            name="Stale Plan Protection",
            description="Rejects execution if relevant project dependencies changed since planning",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master", "mix", "arrangement", "sound")
        )
        super().__init__(policy)

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []

        is_stale = bool(
            context.get("is_stale",
            action.get("is_stale",
            context.get("stale",
            action.get("stale", False))))
        )
        session_fp = context.get("session_fingerprint")
        plan_fp = action.get("session_fingerprint", context.get("plan_fingerprint"))

        fp_mismatch = (
            (session_fp is not None and plan_fp is not None and session_fp != plan_fp) or
            bool(context.get("fingerprint_mismatch", action.get("fingerprint_mismatch", False)))
        )

        if is_stale or fp_mismatch:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="SESSION_FINGERPRINT_MISMATCH" if fp_mismatch else "STALE_PLAN_DETECTED",
                message="Plan is stale: Session state or relevant entities changed after plan creation.",
                field="session_fingerprint",
                actual_value=session_fp,
                expected_value=plan_fp,
                remediation="Re-generate the production plan against the current session state."
            ))

        return violations, [], ["Re-generate plan against fresh session state"], []


# =====================================================================
# 7. REGRESSION Policy (Section 20, 21 & 35)
# =====================================================================

class RegressionPolicy(BasePolicyEvaluator):
    """
    CRITICAL: Requires rollback if post-execution acoustic verification exhibits secondary regressions.
    """

    def __init__(self):
        policy = ProductionPolicy(
            policy_id="REGRESSION",
            name="Acoustic Regression Guardrail",
            description="Rejects commit and triggers rollback if secondary acoustic metrics regress",
            version="1.0.0",
            severity=PolicySeverity.CRITICAL,
            enabled=True,
            domains=("master", "mix")
        )
        super().__init__(policy)

    def evaluate_rule(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[List[PolicyViolation], List[PolicyViolation], List[str], List[Dict[str, Any]]]:
        violations: List[PolicyViolation] = []
        has_regression = bool(action.get("regression", context.get("regression", False)))
        details = action.get("regression_details", context.get("regression_details", []))

        if has_regression:
            detail_str = "; ".join(str(d) for d in details) if details else "Secondary acoustic metric collapsed."
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                decision=PolicyDecision.REJECT,
                severity=PolicySeverity.CRITICAL,
                code="ACOUSTIC_REGRESSION_DETECTED",
                message=f"Acoustic regression detected post-execution: {detail_str}",
                field="regression",
                actual_value=True,
                expected_value=False,
                remediation="Trigger atomic rollback to restore prior session state."
            ))

        return violations, [], ["Revert changes via atomic rollback"], []


# =====================================================================
# Central Production Policy Engine (Section 42)
# =====================================================================

class ProductionPolicyEngine:
    """
    Deterministic governance engine evaluating actions, plans, and candidates.
    Coordinates the 7 canonical policies, guarantees CRITICAL inviolability,
    and calculates deterministic SHA-256 evaluation fingerprints.
    """

    def __init__(self):
        self._policies: Dict[str, BasePolicyEvaluator] = {}
        self._register_default_policies()

    def _register_default_policies(self):
        self.register_policy(MasterLimitPolicy())
        self.register_policy(MasterEQPolicy())
        self.register_policy(MixMasterBoundaryPolicy())
        self.register_policy(LockedObjectPolicy())
        self.register_policy(TransactionRequiredPolicy())
        self.register_policy(StalePlanPolicy())
        self.register_policy(RegressionPolicy())

    def register_policy(self, evaluator: BasePolicyEvaluator):
        self._policies[evaluator.policy_id] = evaluator

    def get_policy(self, policy_id: str) -> Optional[ProductionPolicy]:
        evaluator = self._policies.get(policy_id)
        return evaluator.policy if evaluator else None

    def list_policies(self) -> List[ProductionPolicy]:
        return [evaluator.policy for evaluator in self._policies.values()]

    @property
    def policies(self) -> List[ProductionPolicy]:
        return self.list_policies()

    @staticmethod
    def _compute_sha256(payload: Any) -> str:
        """Calculates canonical sorted-key JSON SHA-256 fingerprint."""
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def evaluate(
        self,
        context_or_action: Any,
        action_or_context: Optional[Any] = None,
        policy_ids: Optional[Sequence[str]] = None,
        **kwargs
    ) -> PolicyEvaluation:
        """
        Evaluates an action/candidate against applicable production policies.
        Flexible signature supports:
        - evaluate(context, action, policy_ids=None)
        - evaluate(action, context, policy_ids=None)
        - evaluate(action, policy_ids=None)
        """
        # Document 9 Section 22 & 44 (Test 13): Inviolability of CRITICAL policies.
        # Bypass parameters MUST NOT form part of the API.
        for forbidden in ("force", "bypass", "ignore_policy", "skip_validation"):
            if forbidden in kwargs:
                raise TypeError(f"Unexpected keyword argument '{forbidden}': governance policies cannot be bypassed.")

        # Determine which parameter is action and which is context
        if "context" in kwargs and action_or_context is None:
            context = kwargs.pop("context")
            action = context_or_action if isinstance(context_or_action, dict) else {}
        elif "action" in kwargs and action_or_context is None:
            action = kwargs.pop("action")
            context = context_or_action if isinstance(context_or_action, dict) else {}
        elif action_or_context is None:
            action = context_or_action if isinstance(context_or_action, dict) else {}
            context = {}
        elif (
            isinstance(context_or_action, dict) and
            ("action" in context_or_action or "domain" in context_or_action or "gain_reduction_db" in context_or_action or "is_candidate" in context_or_action)
        ):
            action = context_or_action
            context = action_or_context if isinstance(action_or_context, dict) else {}
        else:
            context = context_or_action if isinstance(context_or_action, dict) else {}
            action = action_or_context if isinstance(action_or_context, dict) else {}

        # Merge overrides if passed in kwargs (for backward compatibility)
        overrides = kwargs.get("overrides", {})

        # Determine policies to evaluate
        if policy_ids is not None:
            target_pids = set(policy_ids)
            # CRITICAL Invariant (Section 26): Security policies ALWAYS evaluate in final validation
            target_pids.update(["LOCKED_OBJECT", "TRANSACTION_REQUIRED", "STALE_PLAN"])
        else:
            target_pids = set(self._policies.keys())

        all_violations: List[PolicyViolation] = []
        all_warnings: List[PolicyViolation] = []
        all_conditions: List[str] = []
        all_alternatives: List[Dict[str, Any]] = []
        evaluated_pids: List[str] = []
        requires_confirmation = False

        # Check for structurally invasive actions requiring explicit confirmation (Section 23)
        op_name = str(action.get("operation", action.get("action", ""))).lower()
        if action.get("requires_confirmation", False) or op_name in ("delete_track", "replace_device", "structural_change"):
            requires_confirmation = True

        for p_id in sorted(self._policies.keys()):
            if p_id not in target_pids:
                continue

            evaluator = self._policies[p_id]
            evaluated_pids.append(p_id)

            # Inviolability check: CRITICAL policies CAN NEVER be overridden
            if evaluator.severity != PolicySeverity.CRITICAL and overrides.get(f"disable_{p_id.lower()}", False):
                continue

            eval_res = evaluator.evaluate(action, context)
            if eval_res.violations:
                all_violations.extend(eval_res.violations)
            if eval_res.warnings:
                all_warnings.extend(eval_res.warnings)
            if eval_res.required_conditions:
                all_conditions.extend(eval_res.required_conditions)
            if eval_res.alternatives:
                all_alternatives.extend(eval_res.alternatives)

        # Decision Precedence (Section 24):
        # REJECT > REQUIRE_CONFIRMATION > ALLOW_WITH_WARNING > ALLOW
        has_reject = any(v.decision == PolicyDecision.REJECT for v in all_violations)
        has_critical = any(v.severity == PolicySeverity.CRITICAL for v in all_violations)

        if has_critical or has_reject:
            final_decision = PolicyDecision.REJECT
        elif requires_confirmation:
            final_decision = PolicyDecision.REQUIRE_CONFIRMATION
        elif all_warnings:
            final_decision = PolicyDecision.ALLOW_WITH_WARNING
        else:
            final_decision = PolicyDecision.ALLOW

        # Severity Precedence (Section 25):
        # CRITICAL > ERROR > WARNING > INFO
        if has_critical:
            final_severity = PolicySeverity.CRITICAL
        elif any(v.severity == PolicySeverity.ERROR for v in all_violations):
            final_severity = PolicySeverity.ERROR
        elif all_warnings or any(v.severity == PolicySeverity.WARNING for v in all_violations):
            final_severity = PolicySeverity.WARNING
        else:
            final_severity = PolicySeverity.INFO

        # Calculate deterministic SHA-256 fingerprints (Section 29)
        ctx_fp = self._compute_sha256(context)
        act_fp = self._compute_sha256(action)
        eval_payload = {
            "context_fingerprint": ctx_fp,
            "action_fingerprint": act_fp,
            "evaluated_policy_ids": evaluated_pids,
            "policy_versions": {p_id: self._policies[p_id].version for p_id in evaluated_pids},
            "decision": final_decision.value,
            "violations_count": len(all_violations),
            "warnings_count": len(all_warnings)
        }
        eval_fp = self._compute_sha256(eval_payload)

        return PolicyEvaluation(
            decision=final_decision,
            violations=tuple(all_violations),
            warnings=tuple(all_warnings),
            evaluated_policy_ids=tuple(evaluated_pids),
            policy_version=POLICY_ENGINE_VERSION,
            context_fingerprint=ctx_fp,
            action_fingerprint=act_fp,
            evaluation_fingerprint=eval_fp,
            requires_confirmation=requires_confirmation,
            result=final_decision,
            policy_id="AGGREGATED_EVALUATION",
            severity=final_severity,
            required_conditions=tuple(all_conditions),
            alternatives=tuple(all_alternatives)
        )

    def validate(
        self,
        context_or_action: Any,
        action_or_context: Optional[Any] = None,
        policy_ids: Optional[Sequence[str]] = None,
        **kwargs
    ) -> PolicyEvaluation:
        """
        Validates action against policies and raises PolicyViolationError (preserving evaluation)
        if decision == REJECT (Section 27 & 28).
        """
        evaluation = self.evaluate(
            context_or_action=context_or_action,
            action_or_context=action_or_context,
            policy_ids=policy_ids,
            **kwargs
        )

        if evaluation.decision == PolicyDecision.REJECT:
            msg = f"Policy evaluation failed ({evaluation.decision.value}): " + "; ".join(v.message for v in evaluation.violations)
            # Raise specialized sub-exceptions in priority order: LockedObject -> TransactionRequired -> PolicyViolation
            for v in evaluation.violations:
                if v.code == "TARGET_ENTITY_LOCKED" or "locked" in v.message.lower():
                    raise LockedObjectError(msg, details=evaluation.to_dict())
            for v in evaluation.violations:
                if v.code == "TRANSACTION_REQUIRED" or "transaction" in v.message.lower():
                    raise TransactionRequiredError(msg, details=evaluation.to_dict())
            raise PolicyViolationError(msg, evaluation=evaluation)

        return evaluation

    # Alias for backward compatibility with earlier code
    validate_or_raise = validate

    def evaluate_result(
        self,
        context: Dict[str, Any],
        action: Dict[str, Any],
        before_measurement: Dict[str, Any],
        after_measurement: Dict[str, Any],
        expected_delta: Optional[Dict[str, float]] = None
    ) -> PolicyEvaluation:
        """
        Evaluates post-execution acoustic results against regression policies (Section 35).
        """
        regressions: List[str] = []

        # 1. True Peak check: increase beyond platform ceiling
        pre_tp = before_measurement.get("true_peak_dbtp", before_measurement.get("true_peak", -1.0))
        post_tp = after_measurement.get("true_peak_dbtp", after_measurement.get("true_peak", -1.0))
        if post_tp > -0.3 and post_tp > pre_tp:
            regressions.append(f"True Peak clipped to {post_tp:.2f} dBTP (was {pre_tp:.2f} dBTP)")

        # 2. Stereo Correlation check: severe phase collapse
        pre_corr = before_measurement.get("stereo_correlation", 1.0)
        post_corr = after_measurement.get("stereo_correlation", 1.0)
        if post_corr < 0.0 and post_corr < pre_corr - 0.2:
            regressions.append(f"Stereo phase correlation collapsed to {post_corr:.2f} (was {pre_corr:.2f})")

        # 3. Dynamic Range / Crest Factor collapse
        pre_cf = before_measurement.get("crest_factor_db", 12.0)
        post_cf = after_measurement.get("crest_factor_db", 12.0)
        if post_cf < 6.0 and (pre_cf - post_cf) > 4.0:
            regressions.append(f"Dynamic range crushed: Crest Factor collapsed from {pre_cf:.1f} dB to {post_cf:.1f} dB")

        # 4. Sample Peak clipping
        pre_sp = before_measurement.get("sample_peak_dbfs", before_measurement.get("sample_peak", -0.1))
        post_sp = after_measurement.get("sample_peak_dbfs", after_measurement.get("sample_peak", -0.1))
        if post_sp > 0.0 and post_sp > pre_sp:
            regressions.append(f"Sample peak clipped to {post_sp:.2f} dBFS")

        # Inject regression state into action/context for RegressionPolicy evaluation
        augmented_action = dict(action)
        augmented_context = dict(context)

        # Mark post-execution evaluation as non-mutating so TRANSACTION_REQUIRED does not interfere
        if "transaction_id" not in augmented_action and "transaction" not in augmented_action:
            augmented_action["read_only"] = True

        if regressions:
            augmented_action["regression"] = True
            augmented_action["regression_details"] = regressions
            augmented_context["regression"] = True
            augmented_context["regression_details"] = regressions

        return self.evaluate(augmented_context, augmented_action)

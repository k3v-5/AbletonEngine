"""
Tests for ProductionPolicyEngine and specific policy rules in PIE (Hito 1 — Documento 9).
Verifies acoustic limits, domain boundary axioms, transaction guardrails,
strict determinism, lossless JSON serialization, regression detection,
and the absolute inviolability of CRITICAL policies.
"""
import pytest
import json
from engine.production.policies import (
    ProductionPolicyEngine,
    MasterLimitPolicy,
    MasterEQPolicy,
    MixMasterBoundaryPolicy,
    LockedObjectPolicy,
    TransactionRequiredPolicy,
    StalePlanPolicy,
    RegressionPolicy
)
from engine.production.models import (
    PolicyDecision,
    PolicySeverity,
    PolicyStatus,
    PolicyResult,
    PolicyViolation,
    PolicyEvaluation,
    ProductionPolicy
)
from engine.production.exceptions import (
    PolicyViolationError,
    LockedObjectError,
    TransactionRequiredError
)


# =====================================================================
# Document 9 Section 44: Tests Obligatorios (Tests 1 - 13)
# =====================================================================

def test_doc9_test1_master_limiter_gr_2_4():
    """Test 1 — Master limiter: GR = 2.4 -> ALLOW (or ALLOW_WITH_WARNING)."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 2.4,
        "true_peak_dbtp": -0.5,
        "transaction_id": "tx_01"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is True
    assert eval_res.decision in (PolicyDecision.ALLOW, PolicyDecision.ALLOW_WITH_WARNING)


def test_doc9_test2_master_limiter_gr_2_5():
    """Test 2 — Master limiter: GR = 2.5 -> ALLOW."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 2.5,
        "true_peak_dbtp": -0.5,
        "transaction_id": "tx_02"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is True
    assert eval_res.decision in (PolicyDecision.ALLOW, PolicyDecision.ALLOW_WITH_WARNING)


def test_doc9_test3_master_limiter_gr_2_51():
    """Test 3 — Master limiter: GR = 2.51 -> REJECT."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 2.51,
        "true_peak_dbtp": -0.5,
        "transaction_id": "tx_03"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert any("LIMITER_GAIN_REDUCTION_EXCEEDED" in v.code for v in eval_res.violations)


def test_doc9_test4_eq_gain_1_0():
    """Test 4 — EQ: +1.0 dB -> ALLOW."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 1.0,
        "eq_bands_modified": [{"band": 1, "gain_db": 1.0}],
        "transaction_id": "tx_04"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is True
    assert eval_res.decision == PolicyDecision.ALLOW


def test_doc9_test5_eq_gain_1_01():
    """Test 5 — EQ: +1.01 dB -> REJECT."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "eq_bands_modified": [{"band": 1, "gain_db": 1.01}],
        "transaction_id": "tx_05"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert any("MASTER_EQ_GAIN_EXCEEDED" in v.code for v in eval_res.violations)


def test_doc9_test6_eq_2_bands():
    """Test 6 — EQ: 2 EQ bands -> ALLOW."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 1.0,
        "eq_bands_modified": [
            {"band": 1, "gain_db": 0.5},
            {"band": 2, "gain_db": -0.5}
        ],
        "transaction_id": "tx_06"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is True
    assert eval_res.decision == PolicyDecision.ALLOW


def test_doc9_test7_eq_3_bands():
    """Test 7 — EQ: 3 EQ bands -> REJECT."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "eq_bands_modified": [
            {"band": 1, "gain_db": 0.5},
            {"band": 2, "gain_db": -0.5},
            {"band": 3, "gain_db": 0.2}
        ],
        "transaction_id": "tx_07"
    }
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert any("MASTER_EQ_BAND_COUNT_EXCEEDED" in v.code for v in eval_res.violations)


def test_doc9_test8_locked_track():
    """Test 8 — Locked track: locked=True -> REJECT."""
    engine = ProductionPolicyEngine()
    candidate = {"target": "Vocal_Lead", "action": "TUNE_VOCAL", "transaction_id": "tx_08"}
    eval_res = engine.evaluate(candidate, context={"locked": True})
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert any("TARGET_ENTITY_LOCKED" in v.code for v in eval_res.violations)


def test_doc9_test9_no_transaction():
    """Test 9 — No transaction: transaction=None -> REJECT."""
    engine = ProductionPolicyEngine()
    candidate = {"action": "SET_VOLUME", "target": "Track 1", "transaction": None}
    eval_res = engine.evaluate(candidate)
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert any("TRANSACTION_REQUIRED" in v.code for v in eval_res.violations)


def test_doc9_test10_stale_plan_fingerprint_mismatch():
    """Test 10 — Stale plan: fingerprint mismatch -> REJECT."""
    engine = ProductionPolicyEngine()
    candidate = {
        "action": "MUTATE",
        "transaction_id": "tx_10",
        "session_fingerprint": "hash_version_old"
    }
    context = {"session_fingerprint": "hash_version_new"}
    eval_res = engine.evaluate(candidate, context=context)
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert any("SESSION_FINGERPRINT_MISMATCH" in v.code for v in eval_res.violations)


def test_doc9_test11_mix_problem_master_action():
    """Test 11 — Mix problem: MIX_PROBLEM + master action -> REJECT (CRITICAL)."""
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "action": "MASTER_LIMITING",
        "transaction_id": "tx_11"
    }
    context = {
        "diagnosis": "MIX_PROBLEM",
        "problem_type": "MIX_PROBLEM"
    }
    eval_res = engine.evaluate(candidate, context=context)
    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert eval_res.severity == PolicySeverity.CRITICAL
    assert any("MASTER_CANNOT_FIX_MIX_PROBLEM" in v.code for v in eval_res.violations)
    assert len(eval_res.alternatives) > 0
    assert eval_res.alternatives[0]["recommended_domain"] == "mix"


def test_doc9_test12_correct_master_action():
    """
    Test 12 — Correct master action:
    domain=master, GR=1.2 dB, TP=-1.0 dBTP, EQ bands=1 (+0.7 dB),
    transaction=active, locked=false, stale=false -> ALLOW
    """
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "action": "MASTER_CHAIN",
        "gain_reduction_db": 1.2,
        "true_peak_dbtp": -1.0,
        "eq_bands_modified": [{"band": 1, "gain_db": 0.7}],
        "transaction": "active",
        "transaction_id": "tx_active_12"
    }
    context = {
        "locked": False,
        "stale": False,
        "is_stale": False,
        "session_fingerprint": "fp_match",
        "target_locked": False
    }
    eval_res = engine.evaluate(candidate, context=context)
    assert eval_res.allowed is True
    assert eval_res.decision == PolicyDecision.ALLOW
    assert len(eval_res.violations) == 0


def test_doc9_test13_critical_cannot_be_bypassed():
    """
    Test 13 — Critical cannot be bypassed:
    Passing force=True or bypass=True must fail because those parameters
    are not part of the API, and setting force inside payload cannot override.
    """
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 5.0,  # Exceeds 2.5 dB
        "transaction_id": "tx_13"
    }

    # 1. Parameter cannot form part of API: must raise TypeError
    with pytest.raises(TypeError) as exc_info:
        engine.evaluate(candidate, force=True)
    assert "force" in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info2:
        engine.evaluate(candidate, bypass=True)
    assert "bypass" in str(exc_info2.value)

    with pytest.raises(TypeError) as exc_info3:
        engine.validate(candidate, ignore_policy=True)
    assert "ignore_policy" in str(exc_info3.value)

    # 2. Embedding force in payload does not bypass CRITICAL severity
    candidate_with_force = dict(candidate)
    candidate_with_force["force"] = True
    res = engine.evaluate(candidate_with_force)
    assert res.allowed is False
    assert res.decision == PolicyDecision.REJECT
    assert res.severity == PolicySeverity.CRITICAL


# =====================================================================
# Document 9 Section 45: Tests de Determinismo
# =====================================================================

def test_doc9_test14_determinism_100_iterations():
    """
    Test 14 — Determinism:
    Running the exact same evaluation 100 times must produce:
    - same decision
    - same violations
    - same warnings
    - same SHA-256 fingerprints
    """
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 2.2,
        "true_peak_dbtp": -0.8,
        "eq_bands_modified": [{"band": 1, "gain_db": 0.4}],
        "transaction_id": "tx_det_01"
    }
    context = {"target": "MasterBus", "is_stale": False}

    first_eval = engine.evaluate(candidate, context=context)

    for i in range(100):
        current_eval = engine.evaluate(candidate, context=context)
        assert current_eval.decision == first_eval.decision
        assert current_eval.severity == first_eval.severity
        assert current_eval.evaluation_fingerprint == first_eval.evaluation_fingerprint
        assert current_eval.context_fingerprint == first_eval.context_fingerprint
        assert current_eval.action_fingerprint == first_eval.action_fingerprint
        assert len(current_eval.violations) == len(first_eval.violations)
        assert len(current_eval.warnings) == len(first_eval.warnings)


# =====================================================================
# Document 9 Section 46: Combinación de Políticas y Precedencia
# =====================================================================

def test_doc9_test15_policy_combinations_precedence():
    """
    Test 15 — Combinations precedence:
    MASTER_LIMIT -> WARNING + LOCKED_OBJECT -> REJECT  => REJECT
    MASTER_LIMIT -> ALLOW + MASTER_EQ -> ALLOW       => ALLOW
    """
    engine = ProductionPolicyEngine()

    # Case 1: Limiter warning (GR 2.3 dB) + Locked Object (REJECT) -> REJECT
    res_comb1 = engine.evaluate(
        {
            "domain": "master",
            "gain_reduction_db": 2.3,  # triggers warning in limiter
            "target": "Master",
            "transaction_id": "tx_15a"
        },
        context={"locked": True}      # triggers REJECT
    )
    assert res_comb1.allowed is False
    assert res_comb1.decision == PolicyDecision.REJECT

    # Case 2: Limiter ALLOW + EQ ALLOW -> ALLOW
    res_comb2 = engine.evaluate(
        {
            "domain": "master",
            "gain_reduction_db": 1.5,
            "eq_bands_modified": [{"band": 1, "gain_db": 0.5}],
            "transaction_id": "tx_15b"
        },
        context={"locked": False, "is_stale": False}
    )
    assert res_comb2.allowed is True
    assert res_comb2.decision == PolicyDecision.ALLOW


# =====================================================================
# Document 9 Section 47: Tests de Serialización
# =====================================================================

def test_doc9_test16_serialization_roundtrip_lossless():
    """
    Test 16 — Lossless JSON serialization:
    Every PolicyEvaluation must serialize to JSON and deserialize back without losing:
    - enums (PolicyDecision, PolicySeverity)
    - floats (actual_value, expected_value)
    - fingerprints (context, action, evaluation)
    - policy IDs
    - severities
    - codes
    """
    engine = ProductionPolicyEngine()
    candidate = {
        "domain": "master",
        "gain_reduction_db": 3.4567,
        "true_peak_dbtp": 0.25,
        "transaction_id": "tx_serial_01"
    }
    evaluation = engine.evaluate(candidate)

    # 1. to_dict -> from_dict
    dict_repr = evaluation.to_dict()
    restored_from_dict = PolicyEvaluation.from_dict(dict_repr)
    assert restored_from_dict.decision == evaluation.decision
    assert restored_from_dict.severity == evaluation.severity
    assert restored_from_dict.evaluation_fingerprint == evaluation.evaluation_fingerprint
    assert len(restored_from_dict.violations) == len(evaluation.violations)

    # Verify float preservation
    assert restored_from_dict.violations[0].actual_value == 3.4567
    assert isinstance(restored_from_dict.violations[0].severity, PolicySeverity)
    assert isinstance(restored_from_dict.violations[0].decision, PolicyDecision)

    # 2. to_json -> from_json
    json_str = evaluation.to_json(indent=2)
    restored_from_json = PolicyEvaluation.from_json(json_str)
    assert restored_from_json.decision == evaluation.decision
    assert restored_from_json.severity == evaluation.severity
    assert restored_from_json.action_fingerprint == evaluation.action_fingerprint
    assert restored_from_json.evaluation_fingerprint == evaluation.evaluation_fingerprint


# =====================================================================
# Document 9 Section 48: Tests de Regresión
# =====================================================================

def test_doc9_test17_regression_test():
    """
    Test 17 — Regression testing:
    Simulate before: true_peak = -1.2, after: true_peak = +0.1
    Must produce: REGRESSION with CRITICAL severity.
    """
    engine = ProductionPolicyEngine()
    context = {}
    action = {"action": "APPLY_SATURATION", "domain": "master"}
    before = {"true_peak": -1.2, "crest_factor_db": 10.0}
    after = {"true_peak": 0.1, "crest_factor_db": 9.5}

    eval_result = engine.evaluate_result(
        context=context,
        action=action,
        before_measurement=before,
        after_measurement=after
    )

    assert eval_result.allowed is False
    assert eval_result.decision == PolicyDecision.REJECT
    assert eval_result.severity == PolicySeverity.CRITICAL
    assert any("REGRESSION" in v.policy_id for v in eval_result.violations)
    assert any("True Peak clipped" in v.message for v in eval_result.violations)


# =====================================================================
# Document 9 Section 49: Tests de Frontera (Strict Float Boundaries)
# =====================================================================

def test_doc9_test18_boundary_tests_strict_floats():
    """
    Test 18 — Exact numeric float boundaries:
    2.499999 -> ALLOW
    2.5 -> ALLOW
    2.500001 -> REJECT
    1.0 -> ALLOW
    1.000001 -> REJECT
    """
    policy_limit = MasterLimitPolicy(max_gain_reduction_db=2.5, max_true_peak_dbtp=-0.3)
    policy_eq = MasterEQPolicy(max_bands=2, max_eq_change_db=1.0)

    # Master Limiter GR boundaries
    assert policy_limit.evaluate({"gain_reduction_db": 2.499999}, {}).allowed is True
    assert policy_limit.evaluate({"gain_reduction_db": 2.5}, {}).allowed is True
    assert policy_limit.evaluate({"gain_reduction_db": 2.500001}, {}).allowed is False

    # True Peak boundaries
    assert policy_limit.evaluate({"true_peak_dbtp": -0.300001}, {}).allowed is True
    assert policy_limit.evaluate({"true_peak_dbtp": -0.3}, {}).allowed is True
    assert policy_limit.evaluate({"true_peak_dbtp": -0.299999}, {}).allowed is False

    # Master EQ gain boundaries
    assert policy_eq.evaluate({"eq_bands_modified": [{"band": 1, "gain_db": 0.999999}]}, {}).allowed is True
    assert policy_eq.evaluate({"eq_bands_modified": [{"band": 1, "gain_db": 1.0}]}, {}).allowed is True
    assert policy_eq.evaluate({"eq_bands_modified": [{"band": 1, "gain_db": 1.000001}]}, {}).allowed is False


# =====================================================================
# Document 9 Section 51: Criterio Final de Aceptación
# =====================================================================

def test_doc9_acceptance_criteria_conceptual_rejection():
    """
    Section 51 Acceptance Criteria:
    The LLM requests a technically hazardous master action when a mix problem exists.
    The system MUST respond:
    REJECT
    Policy: MIX_MASTER_BOUNDARY
    Severity: CRITICAL
    Reason: The detected problem belongs to the mix domain.
    Evidence: Masking between Kick and Bass detected at 63–91 Hz.
    Forbidden Action: Master EQ / Master Limiting
    Required Remediation: Generate a MIX_ACTION_PLAN.
    Executable: FALSE
    """
    engine = ProductionPolicyEngine()
    context = {
        "diagnosis": "Masking between Kick and Bass detected at 63–91 Hz",
        "problem_type": "MIX_PROBLEM"
    }
    candidate = {
        "domain": "master",
        "action": "MASTER_LIMITING",
        "gain_reduction_db": 2.0,
        "transaction_id": "tx_llm_hazard"
    }

    eval_res = engine.evaluate(candidate, context=context)

    assert eval_res.allowed is False
    assert eval_res.decision == PolicyDecision.REJECT
    assert eval_res.severity == PolicySeverity.CRITICAL

    boundary_violations = [v for v in eval_res.violations if v.policy_id == "MIX_MASTER_BOUNDARY"]
    assert len(boundary_violations) > 0
    violation = boundary_violations[0]
    assert violation.code == "MASTER_CANNOT_FIX_MIX_PROBLEM"
    assert "MIX_ACTION_PLAN" in violation.remediation


# =====================================================================
# Specialized Exception Handling Tests
# =====================================================================

def test_specialized_policy_exceptions():
    """Verifies validate raises specialized exceptions for locked object and transaction required."""
    engine = ProductionPolicyEngine()

    # Locked object raises LockedObjectError
    with pytest.raises(LockedObjectError):
        engine.validate({"target": "Vocal"}, context={"locked": True})

    # Transaction required raises TransactionRequiredError
    with pytest.raises(TransactionRequiredError):
        engine.validate({"action": "MUTATE", "target": "Master"}, context={"dry_run": False})

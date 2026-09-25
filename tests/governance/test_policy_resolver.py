"""
Canonical Fault Injection Test Suite for Verifiable Governance (Phase 1).
Validates all 12 canonical scenarios, edge cases, and model invariants.
"""

import pytest
from pydantic import ValidationError

from engine.governance.contract import (
    DecisionType,
    ExecutionStatus,
    MutationState,
    EvidenceStatus,
    ResolutionStatus,
    OverrideProposal,
    ExpectedState,
    StructuralDecisionContract,
)
from engine.governance.evidence import (
    ExecutionResult,
    VerificationResult,
    IntegrityResult,
    ProvenanceCompleteness,
    ContextEvaluationResult,
    GovernancePolicy,
)
from engine.governance.release_profile import (
    ComparisonMode,
    MetricPolicy,
    ReleaseProfile,
)
from engine.governance.policy_resolver import resolve_policy


@pytest.fixture
def nominal_policy():
    return GovernancePolicy(
        policy_id="gov-live-12-master",
        policy_version="1.0.0",
        enabled=True,
        policy_hash="sha256:4f83b1a20c9e6f3d1b7a5e8c4b2d0f9a",
    )


@pytest.fixture
def nominal_contract():
    return StructuralDecisionContract(
        contract_id="contract-001",
        decision=DecisionType.APPLY,
        target_track="Kick",
        target_device="Drum Buss",
        parameters={"Drive": 0.35, "Boom": 0.50},
        expected_state=ExpectedState(target_parameter="Drive", expected_value=0.35),
        is_valid=True,
        contract_hash="sha256:contract001hash",
    )


@pytest.fixture
def nominal_execution():
    return ExecutionResult(
        execution_id="exec-001",
        status=ExecutionStatus.SUCCESS,
        mutation_state=MutationState.MUTATED,
    )


@pytest.fixture
def nominal_verification():
    return VerificationResult(
        verification_id="verif-001",
        status=EvidenceStatus.VERIFIED,
        observed_state={"Drive": 0.35},
    )


@pytest.fixture
def nominal_integrity():
    return IntegrityResult(is_intact=True)


@pytest.fixture
def nominal_provenance():
    return ProvenanceCompleteness(
        complete=True,
        lineage_hash="sha256:provenance001hash",
    )


@pytest.fixture
def nominal_context():
    return ContextEvaluationResult(satisfied=True)


# ==============================================================================
# CANONICAL SCENARIO 1: Nominal correct write -> PASS
# ==============================================================================
def test_scenario_1_nominal_write_passes(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.PASS
    assert res.commit_approved is True
    assert res.rollback_required is False


# ==============================================================================
# CANONICAL SCENARIO 2: Read-back mismatch -> ROLLBACK_REQUIRED
# ==============================================================================
def test_scenario_2_read_back_mismatch_triggers_rollback(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    mismatch_verification = VerificationResult(
        verification_id="verif-002",
        status=EvidenceStatus.FAILED,
        mismatch_detail="Target parameter Drive expected 0.35, physical read-back returned 0.10",
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=mismatch_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.ROLLBACK_REQUIRED
    assert res.commit_approved is False
    assert res.rollback_required is True
    assert any("mismatch" in r.lower() for r in res.reasons)


# ==============================================================================
# CANONICAL SCENARIO 3: Socket rejection
# (a) NOT_MUTATED -> EXECUTION_FAILED, rollback_required=False
# (b) UNKNOWN -> ROLLBACK_REQUIRED, rollback_required=True
# ==============================================================================
def test_scenario_3a_socket_rejection_clean_no_mutation(
    nominal_contract,
    nominal_context,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    exec_failed = ExecutionResult(
        execution_id="exec-003a",
        status=ExecutionStatus.FAILED,
        mutation_state=MutationState.NOT_MUTATED,
        error_message="Live socket connection reset by peer before write",
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=exec_failed,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.EXECUTION_FAILED
    assert res.commit_approved is False
    assert res.rollback_required is False


def test_scenario_3b_socket_rejection_unknown_mutation_triggers_rollback(
    nominal_contract,
    nominal_context,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    exec_unknown = ExecutionResult(
        execution_id="exec-003b",
        status=ExecutionStatus.FAILED,
        mutation_state=MutationState.UNKNOWN,
        error_message="Pipe broken during transmission; partial write possible",
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=exec_unknown,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.ROLLBACK_REQUIRED
    assert res.commit_approved is False
    assert res.rollback_required is True


# ==============================================================================
# CANONICAL SCENARIO 4: Read-back timeout -> ROLLBACK_REQUIRED
# ==============================================================================
def test_scenario_4_read_back_timeout_triggers_rollback(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    verif_timeout = VerificationResult(
        verification_id="verif-004",
        status=EvidenceStatus.UNKNOWN,
        mismatch_detail="Timeout waiting for Live physical confirmation",
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=verif_timeout,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.ROLLBACK_REQUIRED
    assert res.commit_approved is False
    assert res.rollback_required is True


# ==============================================================================
# CANONICAL SCENARIO 5: Invalid read-back -> ROLLBACK_REQUIRED
# ==============================================================================
def test_scenario_5_invalid_read_back_triggers_rollback(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    verif_invalid = VerificationResult(
        verification_id="verif-005",
        status=EvidenceStatus.FAILED,
        mismatch_detail="Corrupt response payload received from LOM adapter",
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=verif_invalid,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.ROLLBACK_REQUIRED
    assert res.commit_approved is False
    assert res.rollback_required is True


# ==============================================================================
# CANONICAL SCENARIO 6: Accidental digital clipping -> HARD_FAIL
# ==============================================================================
def test_scenario_6_accidental_clipping_triggers_hard_fail(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_verification,
    nominal_provenance,
    nominal_policy,
):
    integrity_violated = IntegrityResult(
        is_intact=False,
        violations=["Master bus peak exceeded 0.0 dBFS (+1.8 dBFS detected)"],
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=integrity_violated,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.HARD_FAIL
    assert res.commit_approved is False
    assert res.rollback_required is True
    assert any("0.0 dBFS" in r for r in res.reasons)


# ==============================================================================
# CANONICAL SCENARIO 7: REJECT with NO_OP + NOT_MUTATED verified -> PASS
# ==============================================================================
def test_scenario_7_reject_decision_verified_passes(
    nominal_context,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    reject_contract = StructuralDecisionContract(
        contract_id="contract-reject-007",
        decision=DecisionType.REJECT,
        target_track="Synth",
        parameters={},
        is_valid=True,
    )
    exec_noop = ExecutionResult(
        execution_id="exec-noop-007",
        status=ExecutionStatus.NO_OP,
        mutation_state=MutationState.NOT_MUTATED,
    )
    verif_noop = VerificationResult(
        verification_id="verif-noop-007",
        status=EvidenceStatus.VERIFIED,
    )
    res = resolve_policy(
        contract=reject_contract,
        context_result=nominal_context,
        execution_result=exec_noop,
        verification_result=verif_noop,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.PASS
    assert res.commit_approved is True
    assert res.rollback_required is False


# ==============================================================================
# CANONICAL SCENARIO 8: DEFER with NO_OP + NOT_MUTATED verified -> PASS
# ==============================================================================
def test_scenario_8_defer_decision_verified_passes(
    nominal_context,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    defer_contract = StructuralDecisionContract(
        contract_id="contract-defer-008",
        decision=DecisionType.DEFER,
        target_track="Vocals",
        parameters={},
        is_valid=True,
    )
    exec_noop = ExecutionResult(
        execution_id="exec-noop-008",
        status=ExecutionStatus.NO_OP,
        mutation_state=MutationState.NOT_MUTATED,
    )
    verif_noop = VerificationResult(
        verification_id="verif-noop-008",
        status=EvidenceStatus.VERIFIED,
    )
    res = resolve_policy(
        contract=defer_contract,
        context_result=nominal_context,
        execution_result=exec_noop,
        verification_result=verif_noop,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.PASS
    assert res.commit_approved is True
    assert res.rollback_required is False


# ==============================================================================
# CANONICAL SCENARIO 9: Override with successful verification -> PASS_WITH_WARNING
# ==============================================================================
def test_scenario_9_artistic_override_verified_passes_with_warning(
    nominal_execution,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    override_contract = StructuralDecisionContract(
        contract_id="contract-override-009",
        decision=DecisionType.APPLY,
        target_track="Bass",
        override_proposal=OverrideProposal(
            reason="Aggressive distortion intended for French Electro aesthetic",
            verification_criteria={"thd_max": 0.25},
        ),
        is_valid=True,
    )
    unmet_context = ContextEvaluationResult(
        satisfied=False,
        unmet_constraints=["Harmonic distortion threshold (0.05) exceeded"],
    )
    verified_override = VerificationResult(
        verification_id="verif-override-009",
        status=EvidenceStatus.VERIFIED,
        override_passed=True,
    )
    res = resolve_policy(
        contract=override_contract,
        context_result=unmet_context,
        execution_result=nominal_execution,
        verification_result=verified_override,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.PASS_WITH_WARNING
    assert res.commit_approved is True
    assert res.rollback_required is False
    assert any("Override artístico verificado" in w for w in res.warnings)


# ==============================================================================
# CANONICAL SCENARIO 10: Declared override unverified -> ROLLBACK_REQUIRED
# ==============================================================================
def test_scenario_10_declared_override_unverified_triggers_rollback(
    nominal_execution,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    override_contract = StructuralDecisionContract(
        contract_id="contract-override-010",
        decision=DecisionType.APPLY,
        target_track="Bass",
        override_proposal=OverrideProposal(
            reason="Extreme sub bass resonance",
        ),
        is_valid=True,
    )
    unmet_context = ContextEvaluationResult(
        satisfied=False,
        unmet_constraints=["Sub energy +6dB above safe ceiling"],
    )
    unverified_override = VerificationResult(
        verification_id="verif-override-010",
        status=EvidenceStatus.VERIFIED,
        override_passed=False,  # Override verification failed!
    )
    res = resolve_policy(
        contract=override_contract,
        context_result=unmet_context,
        execution_result=nominal_execution,
        verification_result=unverified_override,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.ROLLBACK_REQUIRED
    assert res.commit_approved is False
    assert res.rollback_required is True


# ==============================================================================
# CANONICAL SCENARIO 11: Unmet constraint without override -> SUSPENDED
# ==============================================================================
def test_scenario_11_unmet_constraint_without_override_suspends(
    nominal_contract,
    nominal_execution,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    unmet_context = ContextEvaluationResult(
        satisfied=False,
        unmet_constraints=["Frequency masking between 120Hz - 250Hz on Lead Synth"],
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=unmet_context,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.SUSPENDED
    assert res.commit_approved is False
    assert res.rollback_required is False
    assert res.required_action is not None


# ==============================================================================
# CANONICAL SCENARIO 12: Heuristic acoustic warning -> PASS_WITH_WARNING
# ==============================================================================
def test_scenario_12_acoustic_warning_passes_with_warning(
    nominal_contract,
    nominal_execution,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    context_with_warning = ContextEvaluationResult(
        satisfied=True,
        warnings=["Low headroom on snare transient: recommend +1dB limiter threshold headroom"],
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=context_with_warning,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.PASS_WITH_WARNING
    assert res.commit_approved is True
    assert res.rollback_required is False
    assert len(res.warnings) == 1


# ==============================================================================
# ADDITIONAL SANITY TESTS: Provenance, Invalid Policy, Invalid Contract, Coherence
# ==============================================================================
def test_provenance_incomplete_triggers_provenance_incomplete(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_verification,
    nominal_integrity,
    nominal_policy,
):
    incomplete_provenance = ProvenanceCompleteness(
        complete=False,
        missing_links=["Parent commit hash is missing"],
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=incomplete_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.PROVENANCE_INCOMPLETE
    assert res.commit_approved is False
    assert res.rollback_required is True


def test_invalid_policy_triggers_hard_fail(
    nominal_contract,
    nominal_context,
    nominal_execution,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
):
    disabled_policy = GovernancePolicy(
        policy_id="gov-disabled",
        enabled=False,
        policy_hash=None,
    )
    res = resolve_policy(
        contract=nominal_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=disabled_policy,
    )
    assert res.status == ResolutionStatus.HARD_FAIL
    assert res.commit_approved is False
    assert res.rollback_required is True


def test_invalid_contract_triggers_execution_failed(
    nominal_context,
    nominal_execution,
    nominal_verification,
    nominal_integrity,
    nominal_provenance,
    nominal_policy,
):
    invalid_contract = StructuralDecisionContract(
        contract_id="contract-invalid",
        decision=DecisionType.APPLY,
        is_valid=False,
    )
    res = resolve_policy(
        contract=invalid_contract,
        context_result=nominal_context,
        execution_result=nominal_execution,
        verification_result=nominal_verification,
        integrity_result=nominal_integrity,
        provenance=nominal_provenance,
        policy=nominal_policy,
    )
    assert res.status == ResolutionStatus.EXECUTION_FAILED
    assert res.commit_approved is False
    assert res.rollback_required is False


def test_execution_result_coherence_validator():
    # NO_OP + MUTATED -> Must raise ValueError
    with pytest.raises(ValidationError):
        ExecutionResult(
            execution_id="e1",
            status=ExecutionStatus.NO_OP,
            mutation_state=MutationState.MUTATED,
        )

    # SUCCESS + NOT_MUTATED -> Must raise ValueError
    with pytest.raises(ValidationError):
        ExecutionResult(
            execution_id="e2",
            status=ExecutionStatus.SUCCESS,
            mutation_state=MutationState.NOT_MUTATED,
        )

    # FAILED + MUTATED -> Must raise ValueError
    with pytest.raises(ValidationError):
        ExecutionResult(
            execution_id="e3",
            status=ExecutionStatus.FAILED,
            mutation_state=MutationState.MUTATED,
        )


def test_release_profile_metric_policies():
    profile = ReleaseProfile(
        profile_name="Streaming_Target",
        metrics={
            "integrated_lufs": MetricPolicy(
                metric_name="integrated_lufs",
                mode=ComparisonMode.RANGE,
                threshold=-14.0,
                upper_bound=-13.0,
            ),
            "true_peak_max": MetricPolicy(
                metric_name="true_peak_max",
                mode=ComparisonMode.MAXIMUM,
                threshold=-1.0,
            ),
            "lra_min": MetricPolicy(
                metric_name="lra_min",
                mode=ComparisonMode.MINIMUM,
                threshold=5.0,
            ),
            "sample_rate_target": MetricPolicy(
                metric_name="sample_rate_target",
                mode=ComparisonMode.TARGET,
                threshold=44100.0,
                tolerance=0.0,
            ),
        },
    )

    observed_nominal = {
        "integrated_lufs": -13.5,
        "true_peak_max": -1.2,
        "lra_min": 6.0,
        "sample_rate_target": 44100.0,
    }
    evaluation = profile.evaluate_all(observed_nominal)
    assert all(evaluation.values()) is True

    observed_failing = {
        "integrated_lufs": -10.0,  # Too loud
        "true_peak_max": -0.5,    # Exceeds maximum threshold
        "lra_min": 3.0,           # Lower than minimum
        "sample_rate_target": 48000.0,
    }
    eval_failing = profile.evaluate_all(observed_failing)
    assert eval_failing["integrated_lufs"] is False
    assert eval_failing["true_peak_max"] is False
    assert eval_failing["lra_min"] is False
    assert eval_failing["sample_rate_target"] is False

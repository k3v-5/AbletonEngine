"""
Hypothesis Property-Based Axiomatic Invariance Tests for Governance.
Proves the biconditional equivalence:
CommitApproved <=> Eligibility(facts) across >= 200 random permutations.
"""

from typing import Optional
import pytest
from pydantic import BaseModel
hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, HealthCheck, strategies as st

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
from engine.governance.policy_resolver import resolve_policy


class FactPattern(BaseModel):
    contract: StructuralDecisionContract
    context_result: ContextEvaluationResult
    execution_result: ExecutionResult
    verification_result: VerificationResult
    integrity_result: IntegrityResult
    provenance: ProvenanceCompleteness
    policy: GovernancePolicy

    def as_kwargs(self):
        return {
            "contract": self.contract,
            "context_result": self.context_result,
            "execution_result": self.execution_result,
            "verification_result": self.verification_result,
            "integrity_result": self.integrity_result,
            "provenance": self.provenance,
            "policy": self.policy,
        }


def expected_commit_eligibility(facts: FactPattern) -> bool:
    """
    Función Oráculo Matemática Independiente:
    Determina si un conjunto de hechos tiene derecho a Commit,
    sin invocar ni consultar el código de resolve_policy.
    """
    if not facts.contract.is_valid:
        return False

    if not facts.policy.is_valid:
        return False

    if not facts.provenance.complete:
        return False

    if not facts.integrity_result.is_intact:
        return False

    if facts.verification_result.status != EvidenceStatus.VERIFIED:
        return False

    # Contrato para REJECT / DEFER
    if facts.contract.decision in {DecisionType.REJECT, DecisionType.DEFER}:
        return (
            facts.execution_result.status == ExecutionStatus.NO_OP
            and facts.execution_result.mutation_state == MutationState.NOT_MUTATED
        )

    # Contrato para APPLY / MODIFY / CUSTOM
    if facts.contract.decision in {DecisionType.APPLY, DecisionType.MODIFY, DecisionType.CUSTOM}:
        if facts.execution_result.status != ExecutionStatus.SUCCESS:
            return False
        if facts.execution_result.mutation_state != MutationState.MUTATED:
            return False
    else:
        return False

    # Evaluación Contextual y Override
    if facts.context_result.satisfied:
        return True

    return (
        facts.contract.override_proposal is not None
        and facts.verification_result.override_passed is True
    )


# Strategy for coherent ExecutionResult
coherent_execution_pairs = st.sampled_from([
    (ExecutionStatus.NO_OP, MutationState.NOT_MUTATED),
    (ExecutionStatus.SUCCESS, MutationState.MUTATED),
    (ExecutionStatus.FAILED, MutationState.NOT_MUTATED),
    (ExecutionStatus.FAILED, MutationState.UNKNOWN),
])


@st.composite
def execution_result_strategy(draw):
    status, mutation_state = draw(coherent_execution_pairs)
    error_msg = draw(st.one_of(st.none(), st.just("Physical write error"))) if status == ExecutionStatus.FAILED else None
    return ExecutionResult(
        execution_id="exec-prop",
        status=status,
        mutation_state=mutation_state,
        error_message=error_msg,
    )


@st.composite
def fact_pattern_strategy(draw):
    # Decision & Override
    decision = draw(st.sampled_from(DecisionType))
    has_override = draw(st.booleans())
    override_proposal = (
        OverrideProposal(reason=draw(st.text(min_size=1, max_size=30)))
        if has_override
        else None
    )
    is_contract_valid = draw(st.booleans())

    contract = StructuralDecisionContract(
        contract_id="contract-prop",
        decision=decision,
        target_track="Lead",
        override_proposal=override_proposal,
        is_valid=is_contract_valid,
        contract_hash="sha256:contract_prop_hash",
    )

    # Policy
    policy_enabled = draw(st.booleans())
    has_policy_hash = draw(st.booleans())
    policy = GovernancePolicy(
        policy_id="gov-policy-prop",
        enabled=policy_enabled,
        policy_hash="sha256:policy_prop_hash" if has_policy_hash else None,
    )

    # Provenance
    provenance_complete = draw(st.booleans())
    provenance = ProvenanceCompleteness(
        complete=provenance_complete,
        lineage_hash="sha256:provenance_prop_hash" if provenance_complete else None,
    )

    # Integrity
    is_intact = draw(st.booleans())
    violations = [] if is_intact else ["Loudness threshold violation +3.2 dBFS"]
    integrity_result = IntegrityResult(is_intact=is_intact, violations=violations)

    # Execution
    execution_result = draw(execution_result_strategy())

    # Verification
    verification_status = draw(st.sampled_from(EvidenceStatus))
    override_passed = draw(st.one_of(st.none(), st.booleans()))
    verification_result = VerificationResult(
        verification_id="verif-prop",
        status=verification_status,
        mismatch_detail="Mismatch on parameter" if verification_status == EvidenceStatus.FAILED else None,
        override_passed=override_passed,
    )

    # Context
    context_satisfied = draw(st.booleans())
    warnings = draw(st.lists(st.text(min_size=1, max_size=20), max_size=2))
    unmet = [] if context_satisfied else ["Masking with Kick"]
    context_result = ContextEvaluationResult(
        satisfied=context_satisfied,
        unmet_constraints=unmet,
        warnings=warnings,
    )

    return FactPattern(
        contract=contract,
        context_result=context_result,
        execution_result=execution_result,
        verification_result=verification_result,
        integrity_result=integrity_result,
        provenance=provenance,
        policy=policy,
    )


@given(facts=fact_pattern_strategy())
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_commit_biconditional_equivalence(facts: FactPattern):
    """
    Universal Axiom:
    resolve_policy APPROVES commit IF AND ONLY IF expected_commit_eligibility returns True.
    """
    result = resolve_policy(**facts.as_kwargs())
    expected = expected_commit_eligibility(facts)

    assert result.commit_approved is expected, (
        f"Equivalence violation! expected={expected}, got={result.commit_approved}, "
        f"status={result.status}, reasons={result.reasons}"
    )

    if result.commit_approved:
        assert result.status in {ResolutionStatus.PASS, ResolutionStatus.PASS_WITH_WARNING}
        assert result.rollback_required is False
    else:
        assert result.status not in {ResolutionStatus.PASS, ResolutionStatus.PASS_WITH_WARNING}

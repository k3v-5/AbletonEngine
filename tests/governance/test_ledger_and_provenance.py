"""
Comprehensive Test Suite for Cryptographic Provenance and Append-Only Ledger (Phase 2).
Validates deterministic hashing, unbroken lineage verification, tamper-evident chains,
JSONL persistence, and CommitReceipt emission.
"""

import json
from pathlib import Path
import pytest
import tempfile

from engine.governance.contract import (
    DecisionType,
    ExecutionStatus,
    MutationState,
    EvidenceStatus,
    ResolutionStatus,
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
from engine.governance.receipt import CommitReceipt
from engine.governance.policy_resolver import ResolutionResult, resolve_policy
from engine.governance.provenance import (
    canonical_json,
    compute_sha256,
    compute_contract_hash,
    compute_policy_hash,
    compute_evidence_hash,
    compute_lineage_hash,
    build_provenance,
)
from engine.governance.ledger import (
    GENESIS_PREVIOUS_HASH,
    TransitionType,
    LedgerEntry,
    GovernanceLedger,
)


@pytest.fixture
def sample_contract():
    return StructuralDecisionContract(
        contract_id="contract-test-101",
        decision=DecisionType.APPLY,
        target_track="Kick",
        target_device="Glue Compressor",
        parameters={"Threshold": -18.5, "Ratio": 4.0},
        expected_state=ExpectedState(target_parameter="Threshold", expected_value=-18.5),
        is_valid=True,
    )


@pytest.fixture
def sample_policy():
    return GovernancePolicy(
        policy_id="gov-master-policy",
        policy_version="1.0.0",
        enabled=True,
        policy_hash="sha256:policysamplehash123",
    )


@pytest.fixture
def sample_evidence_pack():
    execution = ExecutionResult(
        execution_id="exec-101",
        status=ExecutionStatus.SUCCESS,
        mutation_state=MutationState.MUTATED,
    )
    verification = VerificationResult(
        verification_id="verif-101",
        status=EvidenceStatus.VERIFIED,
        observed_state={"Threshold": -18.5},
    )
    integrity = IntegrityResult(is_intact=True)
    context = ContextEvaluationResult(satisfied=True)
    return execution, verification, integrity, context


# ==============================================================================
# 1. HASH DETERMINISM AND SENSITIVITY
# ==============================================================================
def test_canonical_json_sorts_keys_and_handles_enums():
    data_a = {"b": 2, "a": 1, "status": ExecutionStatus.SUCCESS}
    data_b = {"a": 1, "status": ExecutionStatus.SUCCESS, "b": 2}
    assert canonical_json(data_a) == canonical_json(data_b)
    assert canonical_json(data_a) == '{"a":1,"b":2,"status":"SUCCESS"}'


def test_contract_hash_determinism_and_sensitivity(sample_contract):
    h1 = compute_contract_hash(sample_contract)
    h2 = compute_contract_hash(sample_contract)
    assert h1 == h2
    assert h1.startswith("sha256:")

    # Sensitivity: changing one parameter must change the hash
    modified = sample_contract.model_copy(deep=True)
    modified.parameters["Threshold"] = -18.6
    h_mod = compute_contract_hash(modified)
    assert h1 != h_mod


def test_evidence_hash_sensitivity(sample_evidence_pack):
    exec_res, verif_res, integ_res, ctx_res = sample_evidence_pack
    h_nominal = compute_evidence_hash(exec_res, verif_res, integ_res, ctx_res)

    # Change integrity violation
    integ_violated = IntegrityResult(is_intact=False, violations=["Clipping at +0.5 dBFS"])
    h_violated = compute_evidence_hash(exec_res, verif_res, integ_violated, ctx_res)
    assert h_nominal != h_violated


# ==============================================================================
# 2. PROVENANCE VERIFICATION AND LINEAGE
# ==============================================================================
def test_build_provenance_nominal_complete(sample_contract, sample_policy, sample_evidence_pack):
    exec_res, verif_res, integ_res, ctx_res = sample_evidence_pack

    # Set calculated policy hash on policy
    sample_policy.policy_hash = compute_policy_hash(sample_policy)
    sample_contract.contract_hash = compute_contract_hash(sample_contract)

    prov = build_provenance(
        contract=sample_contract,
        policy=sample_policy,
        execution_result=exec_res,
        verification_result=verif_res,
        integrity_result=integ_res,
        context_result=ctx_res,
        parent_commit_hash=None,
        is_genesis=True,
    )
    assert prov.complete is True
    assert len(prov.missing_links) == 0
    assert prov.lineage_hash is not None
    assert prov.lineage_hash.startswith("sha256:")


def test_build_provenance_detects_contract_hash_mismatch(sample_contract, sample_policy, sample_evidence_pack):
    exec_res, verif_res, integ_res, ctx_res = sample_evidence_pack
    sample_policy.policy_hash = compute_policy_hash(sample_policy)

    # Deliberately spoof contract hash
    sample_contract.contract_hash = "sha256:forged_contract_hash_0000"

    prov = build_provenance(
        contract=sample_contract,
        policy=sample_policy,
        execution_result=exec_res,
        verification_result=verif_res,
        integrity_result=integ_res,
        context_result=ctx_res,
        is_genesis=True,
    )
    assert prov.complete is False
    assert any("Contract hash mismatch" in m for m in prov.missing_links)
    assert prov.lineage_hash is None


def test_build_provenance_detects_missing_parent_hash_on_non_genesis(sample_contract, sample_policy, sample_evidence_pack):
    exec_res, verif_res, integ_res, ctx_res = sample_evidence_pack
    sample_policy.policy_hash = compute_policy_hash(sample_policy)
    sample_contract.contract_hash = compute_contract_hash(sample_contract)

    prov = build_provenance(
        contract=sample_contract,
        policy=sample_policy,
        execution_result=exec_res,
        verification_result=verif_res,
        integrity_result=integ_res,
        context_result=ctx_res,
        parent_commit_hash=None,
        require_parent_if_non_genesis=True,
        is_genesis=False,  # Not genesis, but parent is missing!
    )
    assert prov.complete is False
    assert any("Missing parent commit hash" in m for m in prov.missing_links)


# ==============================================================================
# 3. APPEND-ONLY LEDGER LIFECYCLE & HASH CHAINS
# ==============================================================================
def test_governance_ledger_in_memory_chain(sample_contract, sample_policy):
    ledger = GovernanceLedger()
    assert len(ledger) == 0
    assert ledger.get_head() is None

    # Step 1: Initial state
    res_initial = ResolutionResult(
        status=ResolutionStatus.PASS,
        rollback_required=False,
        commit_approved=False,
    )
    e1 = ledger.record_transition(
        transaction_id="tx-001",
        transition_type=TransitionType.INITIAL,
        contract=sample_contract,
        resolution_result=res_initial,
        evidence_hash="sha256:ev01",
        lineage_hash="sha256:lin01",
        policy_hash=sample_policy.policy_hash,
    )
    assert e1.sequence_number == 0
    assert e1.previous_entry_hash == GENESIS_PREVIOUS_HASH
    assert e1.receipt is None
    assert len(ledger) == 1

    # Step 2: Commit state
    res_commit = ResolutionResult(
        status=ResolutionStatus.PASS,
        rollback_required=False,
        commit_approved=True,
    )
    e2 = ledger.record_transition(
        transaction_id="tx-001",
        transition_type=TransitionType.COMMIT,
        contract=sample_contract,
        resolution_result=res_commit,
        evidence_hash="sha256:ev02",
        lineage_hash="sha256:lin02",
        policy_hash=sample_policy.policy_hash,
        previous_snapshot_hash="sha256:snap_before",
        resulting_snapshot_hash="sha256:snap_after",
    )
    assert e2.sequence_number == 1
    assert e2.previous_entry_hash == e1.entry_hash
    assert e2.receipt is not None
    assert e2.receipt.status == "COMMITTED"
    assert e2.receipt.previous_snapshot_hash == "sha256:snap_before"
    assert len(ledger) == 2

    # Step 3: Rollback state
    res_rollback = ResolutionResult(
        status=ResolutionStatus.ROLLBACK_REQUIRED,
        rollback_required=True,
        commit_approved=False,
        reasons=["Verification physical mismatch"],
    )
    e3 = ledger.record_transition(
        transaction_id="tx-002",
        transition_type=TransitionType.ROLLBACK,
        contract=sample_contract,
        resolution_result=res_rollback,
        evidence_hash="sha256:ev03",
        lineage_hash="sha256:lin03",
        policy_hash=sample_policy.policy_hash,
    )
    assert e3.sequence_number == 2
    assert e3.previous_entry_hash == e2.entry_hash
    assert e3.receipt is None
    assert len(ledger) == 3

    # Cryptographic chain verification
    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is True
    assert errors == []


# ==============================================================================
# 4. TAMPER DETECTION AUDITING
# ==============================================================================
def test_ledger_tamper_detection_modified_payload(sample_contract, sample_policy):
    ledger = GovernanceLedger()
    res_pass = ResolutionResult(
        status=ResolutionStatus.PASS,
        rollback_required=False,
        commit_approved=True,
    )
    ledger.record_transition(
        transaction_id="tx-001",
        transition_type=TransitionType.COMMIT,
        contract=sample_contract,
        resolution_result=res_pass,
        evidence_hash="sha256:ev1",
        lineage_hash="sha256:lin1",
        policy_hash=sample_policy.policy_hash,
    )

    # Verify initially intact
    assert ledger.verify_chain_integrity()[0] is True

    # Tampering: silently modify reasons or resolution_status in memory
    ledger._entries[0].resolution_status = ResolutionStatus.HARD_FAIL

    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is False
    assert any("Tampered entry detected" in e for e in errors)


def test_ledger_tamper_detection_broken_previous_hash(sample_contract, sample_policy):
    ledger = GovernanceLedger()
    res = ResolutionResult(status=ResolutionStatus.PASS, rollback_required=False, commit_approved=False)
    ledger.record_transition("tx-1", TransitionType.INITIAL, sample_contract, res, "sha256:1", "sha256:1", "sha256:p")
    ledger.record_transition("tx-1", TransitionType.COMMIT, sample_contract, res, "sha256:2", "sha256:2", "sha256:p")

    # Break hash link between entry 0 and entry 1
    ledger._entries[1].previous_entry_hash = "sha256:fraudulent_link_0000"

    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is False
    assert any("Hash link broken" in e for e in errors)


# ==============================================================================
# 5. DISK PERSISTENCE AND RELOADING (JSONL)
# ==============================================================================
def test_governance_ledger_disk_persistence(sample_contract, sample_policy):
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger_path = Path(tmp_dir) / "session_ledger.jsonl"

        # Instance 1: write entries
        ledger1 = GovernanceLedger(ledger_file=ledger_path)
        res_init = ResolutionResult(status=ResolutionStatus.PASS, rollback_required=False, commit_approved=False)
        res_commit = ResolutionResult(status=ResolutionStatus.PASS, rollback_required=False, commit_approved=True)

        e1 = ledger1.record_transition("tx-disk-1", TransitionType.INITIAL, sample_contract, res_init, "sha256:e1", "sha256:l1", "sha256:p1")
        e2 = ledger1.record_transition("tx-disk-1", TransitionType.COMMIT, sample_contract, res_commit, "sha256:e2", "sha256:l2", "sha256:p1")

        assert ledger_path.exists()

        # Instance 2: reload from disk
        ledger2 = GovernanceLedger(ledger_file=ledger_path)
        assert len(ledger2) == 2
        assert ledger2.get_head().entry_id == e2.entry_id
        assert ledger2.get_head().previous_entry_hash == e1.entry_hash

        is_valid, errors = ledger2.verify_chain_integrity()
        assert is_valid is True
        assert errors == []

        # Receipts verification
        receipts = ledger2.get_receipts()
        assert len(receipts) == 1
        assert receipts[0].contract_id == sample_contract.contract_id


# ==============================================================================
# 6. END-TO-END GOVERNANCE INTEGRATION
# ==============================================================================
def test_end_to_end_governance_flow(sample_contract, sample_policy, sample_evidence_pack):
    exec_res, verif_res, integ_res, ctx_res = sample_evidence_pack
    sample_policy.policy_hash = compute_policy_hash(sample_policy)
    sample_contract.contract_hash = compute_contract_hash(sample_contract)

    # 1. Evaluate Provenance
    prov = build_provenance(
        contract=sample_contract,
        policy=sample_policy,
        execution_result=exec_res,
        verification_result=verif_res,
        integrity_result=integ_res,
        context_result=ctx_res,
        is_genesis=True,
    )
    assert prov.complete is True

    # 2. Resolve Policy
    resolution = resolve_policy(
        contract=sample_contract,
        context_result=ctx_res,
        execution_result=exec_res,
        verification_result=verif_res,
        integrity_result=integ_res,
        provenance=prov,
        policy=sample_policy,
    )
    assert resolution.status == ResolutionStatus.PASS
    assert resolution.commit_approved is True

    # 3. Record in Ledger
    ledger = GovernanceLedger()
    entry = ledger.record_transition(
        transaction_id="tx-e2e-001",
        transition_type=TransitionType.COMMIT,
        contract=sample_contract,
        resolution_result=resolution,
        evidence_hash=compute_evidence_hash(exec_res, verif_res, integ_res, ctx_res),
        lineage_hash=prov.lineage_hash,
        policy_hash=sample_policy.policy_hash,
        previous_snapshot_hash="sha256:pre_snap",
        resulting_snapshot_hash="sha256:post_snap",
    )

    # 4. Verify Entry & Receipt
    assert entry.receipt is not None
    assert entry.receipt.commit_id.startswith("commit-")
    assert entry.receipt.status == "COMMITTED"
    assert entry.receipt.policy_hash == sample_policy.policy_hash

    # 5. Verify Ledger Chain Integrity
    is_intact, errors = ledger.verify_chain_integrity()
    assert is_intact is True
    assert errors == []

"""
Tests for ExecutionCoordinator (Phase 3).
Validates atomic execution loop, physical read-back verification, automated rollback,
suspension retention, and append-only ledger cryptographic continuity.
"""

from unittest.mock import MagicMock
import pytest

from engine.governance.contract import (
    DecisionType,
    ExecutionStatus,
    MutationState,
    EvidenceStatus,
    ResolutionStatus,
    ExpectedState,
    OverrideProposal,
    StructuralDecisionContract,
)
from engine.governance.evidence import (
    ExecutionResult,
    VerificationResult,
    IntegrityResult,
    ContextEvaluationResult,
    GovernancePolicy,
)
from engine.governance.provenance import compute_policy_hash, compute_contract_hash
from engine.governance.receipt import CommitReceipt
from engine.governance.ledger import TransitionType, GovernanceLedger
from engine.governance.coordinator import CoordinatorResult, ExecutionCoordinator
from engine.session.transaction_guard import TransactionGuard


class MockLiveConnection:
    """Mock connection providing realistic LOM send_command responses."""

    def __init__(self, parameter_values=None):
        self.parameter_values = parameter_values or {"drive": 0.50, "volume": 0.85}
        self.sent_commands = []

    def send_command(self, cmd: str, args: dict = None) -> dict:
        self.sent_commands.append((cmd, args or {}))
        if cmd == "get_track_info":
            return {
                "result": {
                    "volume": self.parameter_values.get("volume", 0.85),
                    "devices": [{"name": "Drum Buss", "class_name": "DrumBuss"}],
                }
            }
        elif cmd == "get_device_parameters":
            return {
                "result": {
                    "parameters": [
                        {"name": k, "value": v}
                        for k, v in self.parameter_values.items()
                    ]
                }
            }
        elif cmd == "set_device_parameter":
            param = args.get("parameter", "").strip().lower()
            val = args.get("value", 0.0)
            self.parameter_values[param] = float(val)
            return {"status": "SUCCESS"}
        elif cmd == "set_track_volume":
            self.parameter_values["volume"] = float(args.get("volume", 0.85))
            return {"status": "SUCCESS"}
        return {"status": "SUCCESS"}


class MockSession:
    """Mock Copilot Guided Session object."""

    def __init__(self):
        self.data = {
            "current_phase": "PHASE_5_INSERTS",
            "phase_index": 5,
            "tracks": [{"name": "Kick", "volume": 0.85}],
        }

    def _save_state(self):
        pass


@pytest.fixture
def mock_conn():
    return MockLiveConnection(parameter_values={"drive": 0.50, "volume": 0.85})


@pytest.fixture
def mock_session():
    return MockSession()


@pytest.fixture
def valid_policy():
    p = GovernancePolicy(
        policy_id="gov-live-12-test",
        policy_version="1.0.0",
        enabled=True,
    )
    p.policy_hash = compute_policy_hash(p)
    return p


# ==============================================================================
# 1. NOMINAL MUTATION AND COMMIT FLOW
# ==============================================================================
def test_coordinator_nominal_commit_flow(mock_conn, mock_session, valid_policy):
    ledger = GovernanceLedger()
    coordinator = ExecutionCoordinator(ledger=ledger, default_policy=valid_policy)

    contract = StructuralDecisionContract(
        contract_id="contract-nom-01",
        decision=DecisionType.APPLY,
        target_track="0",
        target_device="Drum Buss",
        parameters={"drive": 0.50},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.50),
        is_valid=True,
    )

    result = coordinator.execute(
        contract=contract,
        conn=mock_conn,
        session=mock_session,
        is_test_env=False,
    )

    assert result.success is True
    assert result.status == ResolutionStatus.PASS
    assert result.rolled_back is False
    assert result.receipt is not None
    assert result.receipt.status == "COMMITTED"
    assert TransactionGuard._ACTIVE_SNAPSHOT is None
    assert len(ledger) == 1
    assert ledger.get_head().transition_type == TransitionType.COMMIT

    # Cryptographic ledger integrity check
    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is True
    assert errors == []


# ==============================================================================
# 2. PHYSICAL READ-BACK MISMATCH AND AUTOMATED ROLLBACK
# ==============================================================================
def test_coordinator_read_back_mismatch_triggers_physical_rollback(mock_session, valid_policy):
    # Simulated conn where physical value diverges from expected target
    bad_conn = MockLiveConnection(parameter_values={"drive": 0.10, "volume": 0.85})
    # Override set_device_parameter so it fails to update the physical param
    def stuck_set_parameter(cmd, args):
        bad_conn.sent_commands.append((cmd, args or {}))
        return {"status": "SUCCESS"}
    bad_conn.send_command = stuck_set_parameter

    ledger = GovernanceLedger()
    coordinator = ExecutionCoordinator(ledger=ledger, default_policy=valid_policy)

    contract = StructuralDecisionContract(
        contract_id="contract-mismatch-02",
        decision=DecisionType.APPLY,
        target_track="0",
        target_device="Drum Buss",
        parameters={"drive": 0.80},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.80),
        is_valid=True,
    )

    result = coordinator.execute(
        contract=contract,
        conn=bad_conn,
        session=mock_session,
        is_test_env=False,
    )

    assert result.success is False
    assert result.status == ResolutionStatus.ROLLBACK_REQUIRED
    assert result.rolled_back is True
    assert result.receipt is None
    assert len(ledger) == 1
    assert ledger.get_head().transition_type == TransitionType.ROLLBACK

    # Cryptographic ledger integrity check
    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is True
    assert errors == []


# ==============================================================================
# 3. ARTISTIC SILENCE / REJECT DECISION
# ==============================================================================
def test_coordinator_reject_decision_passes_with_no_mutation(mock_conn, mock_session, valid_policy):
    ledger = GovernanceLedger()
    coordinator = ExecutionCoordinator(ledger=ledger, default_policy=valid_policy)

    reject_contract = StructuralDecisionContract(
        contract_id="contract-reject-03",
        decision=DecisionType.REJECT,
        target_track="0",
        parameters={},
        is_valid=True,
    )

    result = coordinator.execute(
        contract=reject_contract,
        conn=mock_conn,
        session=mock_session,
    )

    assert result.success is True
    assert result.status == ResolutionStatus.PASS
    assert result.rolled_back is False
    assert result.receipt is not None
    # No parameter writes should have been sent to Live
    assert not any(cmd == "set_device_parameter" for cmd, _ in mock_conn.sent_commands)
    assert len(ledger) == 1
    assert ledger.get_head().transition_type == TransitionType.COMMIT


# ==============================================================================
# 4. CONTEXT VIOLATION WITHOUT OVERRIDE -> SUSPENDED
# ==============================================================================
def test_coordinator_unmet_context_suspends_transaction(mock_conn, mock_session, valid_policy):
    ledger = GovernanceLedger()
    coordinator = ExecutionCoordinator(ledger=ledger, default_policy=valid_policy)

    contract = StructuralDecisionContract(
        contract_id="contract-suspend-04",
        decision=DecisionType.APPLY,
        target_track="0",
        parameters={"drive": 0.50},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.50),
        is_valid=True,
    )

    unmet_context = ContextEvaluationResult(
        satisfied=False,
        unmet_constraints=["Dynamic range squashed below 6dB ceiling"],
    )

    result = coordinator.execute(
        contract=contract,
        conn=mock_conn,
        session=mock_session,
        context_result=unmet_context,
        is_test_env=False,
    )

    assert result.success is False
    assert result.status == ResolutionStatus.SUSPENDED
    assert result.suspended is True
    assert result.rolled_back is False
    assert result.receipt is None
    assert len(ledger) == 1
    assert ledger.get_head().transition_type == TransitionType.SUSPEND

    # Cryptographic ledger integrity check
    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is True
    assert errors == []


# ==============================================================================
# 5. CONTEXT VIOLATION WITH ARTISTIC OVERRIDE -> PASS_WITH_WARNING
# ==============================================================================
def test_coordinator_override_passes_with_warning(mock_conn, mock_session, valid_policy):
    ledger = GovernanceLedger()
    coordinator = ExecutionCoordinator(ledger=ledger, default_policy=valid_policy)

    contract = StructuralDecisionContract(
        contract_id="contract-override-05",
        decision=DecisionType.APPLY,
        target_track="0",
        parameters={"drive": 0.50},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.50),
        override_proposal=OverrideProposal(
            reason="Aggressive saturation intentional for Cyberpunk aesthetic"
        ),
        is_valid=True,
    )

    unmet_context = ContextEvaluationResult(
        satisfied=False,
        unmet_constraints=["Distortion ceiling exceeded"],
    )

    result = coordinator.execute(
        contract=contract,
        conn=mock_conn,
        session=mock_session,
        context_result=unmet_context,
        is_test_env=False,
    )

    assert result.success is True
    assert result.status == ResolutionStatus.PASS_WITH_WARNING
    assert result.rolled_back is False
    assert result.receipt is not None
    assert len(ledger) == 1
    assert ledger.get_head().transition_type == TransitionType.COMMIT


# ==============================================================================
# 6. SEQUENTIAL MULTI-STEP LIFECYCLE (UNBROKEN HASH CHAIN)
# ==============================================================================
def test_coordinator_sequential_multistep_hash_continuity(mock_conn, mock_session, valid_policy):
    ledger = GovernanceLedger()
    coordinator = ExecutionCoordinator(ledger=ledger, default_policy=valid_policy)

    # Step 1: Nominal Apply
    c1 = StructuralDecisionContract(
        contract_id="c-step-1",
        decision=DecisionType.APPLY,
        parameters={"drive": 0.50},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.50),
        is_valid=True,
    )
    r1 = coordinator.execute(c1, conn=mock_conn, session=mock_session, is_test_env=False)
    assert r1.success is True

    # Step 2: Rejection (No-op)
    c2 = StructuralDecisionContract(
        contract_id="c-step-2",
        decision=DecisionType.REJECT,
        is_valid=True,
    )
    r2 = coordinator.execute(c2, conn=mock_conn, session=mock_session)
    assert r2.success is True

    # Step 3: Integrity Violation (Clipping) -> Hard Fail & Rollback
    c3 = StructuralDecisionContract(
        contract_id="c-step-3",
        decision=DecisionType.APPLY,
        parameters={"drive": 0.50},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.50),
        is_valid=True,
    )
    clipping_integrity = IntegrityResult(is_intact=False, violations=["+2.1 dBFS clipping"])
    r3 = coordinator.execute(
        c3,
        conn=mock_conn,
        session=mock_session,
        integrity_result=clipping_integrity,
        is_test_env=False,
    )
    assert r3.success is False
    assert r3.rolled_back is True

    # Step 4: Corrected Apply
    c4 = StructuralDecisionContract(
        contract_id="c-step-4",
        decision=DecisionType.APPLY,
        parameters={"drive": 0.50},
        expected_state=ExpectedState(target_parameter="drive", expected_value=0.50),
        is_valid=True,
    )
    r4 = coordinator.execute(c4, conn=mock_conn, session=mock_session, is_test_env=False)
    assert r4.success is True

    # Assert exactly 4 transitions recorded
    assert len(ledger) == 4
    entries = ledger.get_entries()
    assert [e.sequence_number for e in entries] == [0, 1, 2, 3]
    assert [e.transition_type for e in entries] == [
        TransitionType.COMMIT,
        TransitionType.COMMIT,
        TransitionType.ROLLBACK,
        TransitionType.COMMIT,
    ]

    # Cryptographic ledger integrity check across all 4 entries
    is_valid, errors = ledger.verify_chain_integrity()
    assert is_valid is True
    assert errors == []

"""
Execution Coordinator for Verifiable Production Governance.
Unifies atomic transaction boundaries, physical LOM execution, read-back verification,
pure policy resolution, and append-only ledger audits.
"""

from typing import Any, Dict, List, Optional
import logging
from pydantic import BaseModel, Field

from .contract import (
    DecisionType,
    ExecutionStatus,
    MutationState,
    EvidenceStatus,
    ResolutionStatus,
    StructuralDecisionContract,
)
from .evidence import (
    ExecutionResult,
    VerificationResult,
    IntegrityResult,
    ContextEvaluationResult,
    GovernancePolicy,
)
from .receipt import CommitReceipt
from .policy_resolver import ResolutionResult, resolve_policy
from .provenance import (
    canonical_json,
    compute_sha256,
    compute_contract_hash,
    compute_policy_hash,
    compute_evidence_hash,
    compute_lineage_hash,
    build_provenance,
)
from .ledger import TransitionType, LedgerEntry, GovernanceLedger

logger = logging.getLogger("ExecutionCoordinator")


class CoordinatorResult(BaseModel):
    success: bool
    status: ResolutionStatus
    resolution: ResolutionResult
    ledger_entry: Optional[LedgerEntry] = None
    receipt: Optional[CommitReceipt] = None
    rolled_back: bool = False
    suspended: bool = False
    compensations_applied: List[str] = Field(default_factory=list)


class ExecutionCoordinator:
    """
    Physical execution and governance gatekeeper.
    Enforces atomic lifecycle: Snapshot -> Physical Execution -> Read-Back -> Pure Resolve -> Commit/Rollback.
    """

    def __init__(
        self,
        ledger: Optional[GovernanceLedger] = None,
        default_policy: Optional[GovernancePolicy] = None,
    ):
        self.ledger = ledger if ledger is not None else GovernanceLedger()
        if default_policy is not None:
            self.default_policy = default_policy
        else:
            pol = GovernancePolicy(
                policy_id="gov-master-live-12",
                policy_version="1.0.0",
                enabled=True,
            )
            pol.policy_hash = compute_policy_hash(pol)
            self.default_policy = pol

    def execute(
        self,
        contract: StructuralDecisionContract,
        conn: Any = None,
        session: Any = None,
        context_result: Optional[ContextEvaluationResult] = None,
        integrity_result: Optional[IntegrityResult] = None,
        policy: Optional[GovernancePolicy] = None,
        is_test_env: bool = False,
    ) -> CoordinatorResult:
        """
        Coordinates full governance lifecycle for a single structural decision.
        """
        active_policy = policy if policy is not None else self.default_policy
        if not active_policy.policy_hash:
            active_policy.policy_hash = compute_policy_hash(active_policy)
        if not contract.contract_hash:
            contract.contract_hash = compute_contract_hash(contract)

        ctx_result = context_result if context_result is not None else ContextEvaluationResult(satisfied=True)
        integ_result = integrity_result if integrity_result is not None else IntegrityResult(is_intact=True)

        from engine.session.transaction_guard import TransactionGuard

        # ----------------------------------------------------------------------
        # Paso 1: Captura de Snapshot Pre-Mutación
        # ----------------------------------------------------------------------
        session_data = session.data if (session and hasattr(session, "data")) else {}
        live_tracks = []
        if conn and hasattr(conn, "send_command") and contract.target_track is not None:
            try:
                # If target_track is numeric or convertible
                t_idx = int(contract.target_track) if str(contract.target_track).isdigit() else 0
                live_tracks = [TransactionGuard.capture_live_track_state(conn, t_idx)]
            except Exception:
                live_tracks = []

        snap = TransactionGuard.begin_transaction(session_data, live_tracks)
        prev_snapshot_payload = {
            "session_data": snap.session_data,
            "live_tracks_state": snap.live_tracks_state,
        }
        previous_snapshot_hash = compute_sha256(canonical_json(prev_snapshot_payload))

        # ----------------------------------------------------------------------
        # Paso 2: Ejecución Física en Live
        # ----------------------------------------------------------------------
        exec_id = f"exec-{contract.contract_id}"
        exec_result: ExecutionResult

        if contract.decision in {DecisionType.REJECT, DecisionType.DEFER}:
            # Ausencia deliberada de mutación
            exec_result = ExecutionResult(
                execution_id=exec_id,
                status=ExecutionStatus.NO_OP,
                mutation_state=MutationState.NOT_MUTATED,
            )
        else:
            # Operaciones mutacionales (APPLY, MODIFY, CUSTOM)
            if conn and hasattr(conn, "send_command") and not is_test_env:
                try:
                    # Aplica parámetros declarados en el contrato
                    t_idx = int(contract.target_track) if str(contract.target_track).isdigit() else 0
                    for p_name, p_val in contract.parameters.items():
                        conn.send_command(
                            "set_device_parameter",
                            {
                                "track_index": t_idx,
                                "device_index": 0,
                                "parameter": p_name,
                                "value": float(p_val),
                            },
                        )
                    exec_result = ExecutionResult(
                        execution_id=exec_id,
                        status=ExecutionStatus.SUCCESS,
                        mutation_state=MutationState.MUTATED,
                    )
                except Exception as ex:
                    logger.error(f"[ExecutionCoordinator] Fallo en Live LOM: {ex}")
                    exec_result = ExecutionResult(
                        execution_id=exec_id,
                        status=ExecutionStatus.FAILED,
                        mutation_state=MutationState.UNKNOWN,
                        error_message=str(ex),
                    )
            else:
                # Entorno de pruebas o mock
                exec_result = ExecutionResult(
                    execution_id=exec_id,
                    status=ExecutionStatus.SUCCESS,
                    mutation_state=MutationState.MUTATED,
                )

        # ----------------------------------------------------------------------
        # Paso 3: Verificación Física LOM Post-Mutación
        # ----------------------------------------------------------------------
        verif_id = f"verif-{contract.contract_id}"
        verif_result: VerificationResult

        if contract.decision in {DecisionType.REJECT, DecisionType.DEFER}:
            verif_result = VerificationResult(
                verification_id=verif_id,
                status=EvidenceStatus.VERIFIED,
                mismatch_detail=None,
            )
        elif contract.expected_state:
            target_p = contract.expected_state.target_parameter.strip().lower()
            expected_v = float(contract.expected_state.expected_value)
            tolerance = contract.expected_state.tolerance

            observed_val = None
            if conn and hasattr(conn, "send_command") and not is_test_env:
                try:
                    from engine.core.device_execution_verifier import DeviceExecutionVerifier
                    t_idx = int(contract.target_track) if str(contract.target_track).isdigit() else 0
                    params = DeviceExecutionVerifier.read_device_parameters(conn, t_idx, 0)
                    observed_val = params.get(target_p)
                except Exception:
                    observed_val = None
            else:
                # Mock / Test Env: default to contract parameters or expected
                observed_val = float(contract.parameters.get(contract.expected_state.target_parameter, expected_v))

            if observed_val is None:
                verif_result = VerificationResult(
                    verification_id=verif_id,
                    status=EvidenceStatus.UNKNOWN,
                    mismatch_detail=f"Parámetro {target_p} no legible en Live LOM.",
                )
            elif abs(observed_val - expected_v) <= tolerance:
                verif_result = VerificationResult(
                    verification_id=verif_id,
                    status=EvidenceStatus.VERIFIED,
                    observed_state={target_p: observed_val},
                    override_passed=True if contract.override_proposal else None,
                )
            else:
                verif_result = VerificationResult(
                    verification_id=verif_id,
                    status=EvidenceStatus.FAILED,
                    observed_state={target_p: observed_val},
                    mismatch_detail=f"Valor físico {observed_val} difiere de {expected_v} (tol={tolerance})",
                    override_passed=False if contract.override_proposal else None,
                )
        else:
            verif_result = VerificationResult(
                verification_id=verif_id,
                status=EvidenceStatus.VERIFIED if exec_result.status == ExecutionStatus.SUCCESS else EvidenceStatus.FAILED,
                override_passed=True if contract.override_proposal else None,
            )

        # ----------------------------------------------------------------------
        # Paso 4: Auditoría de Provenance Criptográfica
        # ----------------------------------------------------------------------
        head_entry = self.ledger.get_head()
        parent_hash = head_entry.entry_hash if head_entry else None

        prov = build_provenance(
            contract=contract,
            policy=active_policy,
            execution_result=exec_result,
            verification_result=verif_result,
            integrity_result=integ_result,
            context_result=ctx_result,
            parent_commit_hash=parent_hash,
            is_genesis=head_entry is None,
        )

        # ----------------------------------------------------------------------
        # Paso 5: Resolución de Política Pura
        # ----------------------------------------------------------------------
        resolution = resolve_policy(
            contract=contract,
            context_result=ctx_result,
            execution_result=exec_result,
            verification_result=verif_result,
            integrity_result=integ_result,
            provenance=prov,
            policy=active_policy,
        )

        evidence_hash = compute_evidence_hash(
            execution_result=exec_result,
            verification_result=verif_result,
            integrity_result=integ_result,
            context_result=ctx_result,
        )
        lineage_hash = prov.lineage_hash or compute_lineage_hash(
            parent_commit_hash=parent_hash,
            contract_hash=contract.contract_hash or compute_sha256(canonical_json(contract.model_dump())),
            evidence_hash=evidence_hash,
            policy_hash=active_policy.policy_hash or "sha256:unknown",
        )

        # ----------------------------------------------------------------------
        # Paso 6: Commit, Rollback o Suspensión Transaccional
        # ----------------------------------------------------------------------
        tx_id = f"tx-{contract.contract_id}"
        compensations: List[str] = []

        if resolution.commit_approved:
            # Commit exitoso
            TransactionGuard.commit_transaction()
            resulting_snapshot_payload = {
                "session_data": session.data if (session and hasattr(session, "data")) else {},
                "contract_id": contract.contract_id,
            }
            resulting_snapshot_hash = compute_sha256(canonical_json(resulting_snapshot_payload))

            entry = self.ledger.record_transition(
                transaction_id=tx_id,
                transition_type=TransitionType.COMMIT,
                contract=contract,
                resolution_result=resolution,
                evidence_hash=evidence_hash,
                lineage_hash=lineage_hash,
                policy_hash=active_policy.policy_hash or "sha256:unknown",
                previous_snapshot_hash=previous_snapshot_hash,
                resulting_snapshot_hash=resulting_snapshot_hash,
            )
            return CoordinatorResult(
                success=True,
                status=resolution.status,
                resolution=resolution,
                ledger_entry=entry,
                receipt=entry.receipt,
                rolled_back=False,
                suspended=False,
            )

        elif resolution.rollback_required:
            # Fallo que requiere reversión física del estado
            rollback_report = TransactionGuard.rollback_transaction(conn, session)
            compensations = rollback_report.get("compensations", [])

            entry = self.ledger.record_transition(
                transaction_id=tx_id,
                transition_type=TransitionType.ROLLBACK,
                contract=contract,
                resolution_result=resolution,
                evidence_hash=evidence_hash,
                lineage_hash=lineage_hash,
                policy_hash=active_policy.policy_hash or "sha256:unknown",
                previous_snapshot_hash=previous_snapshot_hash,
            )
            return CoordinatorResult(
                success=False,
                status=resolution.status,
                resolution=resolution,
                ledger_entry=entry,
                receipt=None,
                rolled_back=True,
                suspended=False,
                compensations_applied=compensations,
            )

        elif resolution.status == ResolutionStatus.SUSPENDED:
            # Transacción suspendida para aclaración o re-pregunta
            entry = self.ledger.record_transition(
                transaction_id=tx_id,
                transition_type=TransitionType.SUSPEND,
                contract=contract,
                resolution_result=resolution,
                evidence_hash=evidence_hash,
                lineage_hash=lineage_hash,
                policy_hash=active_policy.policy_hash or "sha256:unknown",
                previous_snapshot_hash=previous_snapshot_hash,
            )
            return CoordinatorResult(
                success=False,
                status=resolution.status,
                resolution=resolution,
                ledger_entry=entry,
                receipt=None,
                rolled_back=False,
                suspended=True,
            )

        else:
            # EXECUTION_FAILED limpio (sin mutación, cancela transacción)
            TransactionGuard._ACTIVE_SNAPSHOT = None
            entry = self.ledger.record_transition(
                transaction_id=tx_id,
                transition_type=TransitionType.ROLLBACK,
                contract=contract,
                resolution_result=resolution,
                evidence_hash=evidence_hash,
                lineage_hash=lineage_hash,
                policy_hash=active_policy.policy_hash or "sha256:unknown",
                previous_snapshot_hash=previous_snapshot_hash,
            )
            return CoordinatorResult(
                success=False,
                status=resolution.status,
                resolution=resolution,
                ledger_entry=entry,
                receipt=None,
                rolled_back=False,
                suspended=False,
            )

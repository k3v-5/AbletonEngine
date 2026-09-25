"""
Pure Deterministic Policy Resolver for AbletonEngine Governance.
Zero I/O, zero socket, zero Live, zero mutable dependencies.
Transforms observed facts and governance policy into immutable resolution decisions.
"""

from typing import List, Optional
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
    ProvenanceCompleteness,
    ContextEvaluationResult,
    GovernancePolicy,
)
from .receipt import CommitReceipt


class ResolutionResult(BaseModel):
    status: ResolutionStatus
    rollback_required: bool
    commit_approved: bool
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    required_action: Optional[str] = None
    receipt: Optional[CommitReceipt] = None


def resolve_policy(
    contract: StructuralDecisionContract,
    context_result: ContextEvaluationResult,
    execution_result: ExecutionResult,
    verification_result: VerificationResult,
    integrity_result: IntegrityResult,
    provenance: ProvenanceCompleteness,
    policy: GovernancePolicy,
) -> ResolutionResult:
    """
    Función Pura Determinista: (Hechos Observados + Política) -> Resolución
    Cero I/O, cero socket, cero Live, cero dependencias mutables.
    """
    # 1. Validez del Contrato
    if not contract.is_valid:
        return ResolutionResult(
            status=ResolutionStatus.EXECUTION_FAILED,
            rollback_required=False,
            commit_approved=False,
            reasons=["El contrato estructural es inválido o contiene campos incompletos."],
        )

    # 2. Validez de la Política de Gobernanza
    if not policy.is_valid:
        return ResolutionResult(
            status=ResolutionStatus.HARD_FAIL,
            rollback_required=True,
            commit_approved=False,
            reasons=["La política de gobernanza es inválida, está deshabilitada o carece de hash."],
        )

    # 3. Provenance Completeness (Precedencia sobre Integrity en diagnóstico)
    if not provenance.complete:
        return ResolutionResult(
            status=ResolutionStatus.PROVENANCE_INCOMPLETE,
            rollback_required=True,
            commit_approved=False,
            reasons=["Cadena de provenance incompleta: commit prohibido por falta de trazabilidad."],
        )

    # 4. Integridad del Sistema
    if not integrity_result.is_intact:
        return ResolutionResult(
            status=ResolutionStatus.HARD_FAIL,
            rollback_required=True,
            commit_approved=False,
            reasons=integrity_result.violations or ["Integrity violation detected."],
        )

    # 5. Semántica NO_MUTATION (REJECT / DEFER) con verificación de MutationState
    if contract.decision in {DecisionType.REJECT, DecisionType.DEFER}:
        if (
            execution_result.status != ExecutionStatus.NO_OP
            or execution_result.mutation_state != MutationState.NOT_MUTATED
        ):
            return ResolutionResult(
                status=ResolutionStatus.EXECUTION_FAILED,
                rollback_required=False,
                commit_approved=False,
                reasons=["NO_MUTATION requiere ExecutionStatus.NO_OP y MutationState.NOT_MUTATED."],
            )

        if verification_result.status != EvidenceStatus.VERIFIED:
            return ResolutionResult(
                status=ResolutionStatus.ROLLBACK_REQUIRED,
                rollback_required=True,
                commit_approved=False,
                reasons=["NO_MUTATION no pudo verificarse físicamente."],
            )

        return ResolutionResult(
            status=ResolutionStatus.PASS,
            rollback_required=False,
            commit_approved=True,
            reasons=[f"{contract.decision.value} verificado: ausencia de mutación confirmada."],
        )

    # 6. Semántica de Operaciones Mutacionales (APPLY / MODIFY / CUSTOM)
    if contract.decision in {DecisionType.APPLY, DecisionType.MODIFY, DecisionType.CUSTOM}:
        if execution_result.status != ExecutionStatus.SUCCESS:
            if execution_result.mutation_state == MutationState.UNKNOWN:
                return ResolutionResult(
                    status=ResolutionStatus.ROLLBACK_REQUIRED,
                    rollback_required=True,
                    commit_approved=False,
                    reasons=["Live falló con estado de mutación UNKNOWN: rollback preventivo requerido."],
                )
            return ResolutionResult(
                status=ResolutionStatus.EXECUTION_FAILED,
                rollback_required=False,
                commit_approved=False,
                reasons=[f"Live rechazó la orden de ejecución: {execution_result.error_message}"],
            )

        if execution_result.mutation_state != MutationState.MUTATED:
            return ResolutionResult(
                status=ResolutionStatus.ROLLBACK_REQUIRED,
                rollback_required=True,
                commit_approved=False,
                reasons=["Operación mutacional declarada como SUCCESS pero mutation_state != MUTATED."],
            )

    # 7. Estado de Verificación Física
    if verification_result.status == EvidenceStatus.UNKNOWN:
        return ResolutionResult(
            status=ResolutionStatus.ROLLBACK_REQUIRED,
            rollback_required=True,
            commit_approved=False,
            reasons=["Estado de verificación UNKNOWN (timeout o lectura nula): commit prohibido."],
        )

    if verification_result.status == EvidenceStatus.FAILED or not verification_result.passed:
        return ResolutionResult(
            status=ResolutionStatus.ROLLBACK_REQUIRED,
            rollback_required=True,
            commit_approved=False,
            reasons=[f"Mismatch de verificación física: {verification_result.mismatch_detail}"],
        )

    # 8. Restricciones Contextuales y Override Verificado
    if not context_result.satisfied:
        if contract.override_proposal:
            if verification_result.override_passed is not True:
                return ResolutionResult(
                    status=ResolutionStatus.ROLLBACK_REQUIRED,
                    rollback_required=True,
                    commit_approved=False,
                    reasons=["El override propuesto no fue verificado o no cumplió los criterios de corte."],
                )
            return ResolutionResult(
                status=ResolutionStatus.PASS_WITH_WARNING,
                rollback_required=False,
                commit_approved=True,
                warnings=[f"Override artístico verificado y aceptado: {contract.override_proposal.reason}"],
            )
        else:
            return ResolutionResult(
                status=ResolutionStatus.SUSPENDED,
                rollback_required=False,
                commit_approved=False,
                reasons=context_result.unmet_constraints,
                required_action="Aportar OverrideProposal justificado o modificar la decisión.",
            )

    # 9. Warnings y Commit Aprobado
    return ResolutionResult(
        status=ResolutionStatus.PASS_WITH_WARNING if context_result.warnings else ResolutionStatus.PASS,
        rollback_required=False,
        commit_approved=True,
        warnings=context_result.warnings,
    )

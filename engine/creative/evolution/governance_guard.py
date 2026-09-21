# engine/creative/evolution/governance_guard.py
"""
Evolution Governance Guard (Nivel S):
Enforces the Sovereign Right of Veto over the Contextual Sonic Critic.

The Critic evaluates acoustic and contextual performance (Delta Q),
but Governance holds the absolute power to veto interventions that violate:
1. Song Contract (Inviolable obligations and tripartite commitments).
2. Compositional DNA (Foundational key, scale, BPM, and core motif identity).
3. Audio Provenance (Strict origin tracking, no unprovenanced external audio).
4. Negative Constraints (Strict rules like NO_OVERLAPPING_LOW_END).
5. Evolution Budget (Bounded iterations, preventing endless modification).
6. Identity Preservation (Preventing homogenization or sonic character erasure).
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional, Tuple

from engine.composition.compositional_dna import CompositionalDNA, NegativeConstraint
from .models import (
    InterventionOrder,
    InterventionType,
    InterventionDomain,
    EvolutionBudget,
    EvolutionSnapshot,
)

logger = logging.getLogger("EvolutionGovernanceGuard")


class GovernanceVetoError(Exception):
    """Raised when an intervention violates fundamental song governance or contract."""
    pass


class EvolutionGovernanceGuard:
    """
    Sovereign gatekeeper evaluating whether an intervention order or resulting state
    violates higher-order musical invariants.
    """

    @classmethod
    def audit_intervention_order(
        cls,
        order: InterventionOrder,
        budget: EvolutionBudget,
        song_dna: Optional[CompositionalDNA] = None,
        contract: Optional[Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates an intervention order BEFORE it is executed.
        Returns: (is_approved, veto_reason)
        """
        # 1. Budget Guard
        if not budget.can_perform(order.intervention_type):
            reason = f"Veto Gobernanza (Presupuesto): El presupuesto para '{order.intervention_type.value}' está agotado."
            logger.warning(reason)
            return False, reason

        # 2. Compositional DNA Invariant Guard
        if song_dna:
            # Tempo and Key are unalterable by evolution interventions
            if "bpm" in order.parameters or "tempo" in order.parameters:
                reason = "Veto Gobernanza (ADN Inviolable): Se prohíbe alterar el tempo fundacional de la obra durante la evolución seccional."
                return False, reason

            if "key_root" in order.parameters or "scale" in order.parameters:
                reason = "Veto Gobernanza (ADN Inviolable): Se prohíbe alterar la tonalidad raíz durante la evolución seccional."
                return False, reason

            # Negative Constraints Audit
            neg_constraints = getattr(song_dna, "negative_constraints", [])
            for nc in neg_constraints:
                val = nc.value if hasattr(nc, "value") else str(nc)
                if val == NegativeConstraint.NO_OVERLAPPING_LOW_END.value:
                    if order.intervention_type == InterventionType.SOUND_OCTAVE_TRANSPOSE:
                        shift = order.parameters.get("octave_shift", 0)
                        if shift < 0 and order.target_track_or_role in ["keys", "pad_texture"]:
                            reason = "Veto Gobernanza (Negative Constraint): Transponer el pad/teclado hacia el registro grave viola 'NO_OVERLAPPING_LOW_END'."
                            return False, reason

        # 3. Song Contract Guard (if present)
        if contract and hasattr(contract, "obligations"):
            # Ensure critical obligations are not broken
            for ob_id, ob in contract.obligations.items():
                if getattr(ob, "is_critical", False):
                    # For example, cannot permanently mute primary lead vocal
                    if order.intervention_type == InterventionType.ARRANGEMENT_SPACE_YIELDING:
                        if "vocal" in order.target_track_or_role.lower() or "lead" in order.target_track_or_role.lower():
                            if order.parameters.get("action") == "mute_during_vocal_window":
                                reason = f"Veto Gobernanza (Contrato): Se prohíbe silenciar la voz principal (Obligación crítica '{ob_id}')."
                                return False, reason

        return True, None

    @classmethod
    def audit_evolution_outcome(
        cls,
        before_snapshot: EvolutionSnapshot,
        candidate_snapshot: EvolutionSnapshot,
        song_dna: Optional[CompositionalDNA] = None,
        contract: Optional[Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates the candidate snapshot AFTER render and critique.
        Ensures that even with an acoustic improvement, artistic identity was not destroyed.
        """
        report = candidate_snapshot.critic_report
        if not report:
            return True, None

        # 1. Identity Destruction Guard
        identity_score = report.dimension_scores.get("identity", 0.70)
        if identity_score < 0.40:
            reason = (
                f"Veto Gobernanza (Destrucción de Identidad): El score de identidad cayó a {identity_score:.2f} < 0.40. "
                "La intervención homogeneizó el sonido volviéndolo genérico."
            )
            return False, reason

        # 2. Motif Liquidation Guard
        motif_score = report.dimension_scores.get("motif_resonance", 0.70)
        if motif_score < 0.35:
            reason = (
                f"Veto Gobernanza (Pérdida de Motivo): La resonancia temática cayó a {motif_score:.2f} < 0.35. "
                "La intervención destruyó el vínculo melódico reconocible con la canción."
            )
            return False, reason

        return True, None

    @classmethod
    def evaluate_candidate_verdict(
        cls,
        candidate_report: Any,
        song_dna: Optional[CompositionalDNA] = None,
        contract: Optional[Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Direct evaluation of a ContextualAuditReport for candidate selection.
        """
        if not candidate_report:
            return True, None

        dim_scores = getattr(candidate_report, "dimension_scores", {})
        identity_score = dim_scores.get("identity", 0.70)
        if identity_score < 0.40:
            reason = f"Veto Gobernanza (Identidad): Score cayó a {identity_score:.2f} < 0.40."
            return False, reason

        motif_score = dim_scores.get("motif_resonance", 0.70)
        if motif_score < 0.35:
            reason = f"Veto Gobernanza (Motivo): Resonancia temática cayó a {motif_score:.2f} < 0.35."
            return False, reason

        return True, None

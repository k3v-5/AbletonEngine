# engine/creative/evolution/closed_loop_engine.py
"""
Closed-Loop Creative Evolution Engine (Nivel S0 - Master Facade):
Orchestrates the active closed-loop feedback between Composition, Sound, Arrangement, and Mix.

Circuit:
Critic (Diagnosis) -> InterventionPlanner (Domain permission) -> GovernanceGuard (Veto audit)
  -> Router (State execution) -> Re-render -> Critic (A/B evaluation)
  -> COMMIT (if improved) or ROLLBACK (if degraded or vetoed)
  -> Memory/Ledger inscription.

Guarantees:
1. Multi-domain root-cause interventions (Arrangement, Sound, Composition, Mix).
2. Strict intervention budget (No infinite thrashing; preserves best known state).
3. Deterministic snapshotting and instant rollback.
4. Sovereign Governance Veto over acoustic critique.
"""

from __future__ import annotations
import uuid
import hashlib
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import numpy as np

from engine.composition.compositional_dna import CompositionalDNA
from engine.creative.contextual_sonic_critic import (
    ContextualSonicCritic,
    ContextualAuditReport,
    ContextualVerdict,
)
from .models import (
    EvolutionBudget,
    EvolutionSnapshot,
    InterventionOrder,
    EvolutionResult,
)
from .intervention_planner import InterventionPlanner
from .governance_guard import EvolutionGovernanceGuard
from .router import MultiDomainInterventionRouter
from .ledger import EvolutionLedger

logger = logging.getLogger("ClosedLoopCreativeEvolutionEngine")


class ClosedLoopCreativeEvolutionEngine:
    """
    Master evolutionary engine closing the feedback loop of music production.
    """

    def __init__(
        self,
        critic: Optional[ContextualSonicCritic] = None,
        planner: Optional[InterventionPlanner] = None,
        router: Optional[MultiDomainInterventionRouter] = None,
        governance_guard: Optional[EvolutionGovernanceGuard] = None,
        ledger: Optional[EvolutionLedger] = None
    ):
        self.critic = critic or ContextualSonicCritic()
        self.planner = planner or InterventionPlanner()
        self.router = router or MultiDomainInterventionRouter(critic=self.critic)
        self.governance = governance_guard or EvolutionGovernanceGuard()
        self.ledger = ledger or EvolutionLedger()

    def evolve_section(
        self,
        section_name: str,
        baseline_audio: Union[str, Path, np.ndarray, Dict[str, Any]],
        initial_staged_audio: Optional[Union[str, Path, np.ndarray, Dict[str, Any]]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        song_dna: Optional[CompositionalDNA] = None,
        contract: Optional[Any] = None,
        target_role: str = "pad_texture",
        budget: Optional[EvolutionBudget] = None,
        max_iterations: int = 5
    ) -> EvolutionResult:
        """
        Executes bounded closed-loop evolution for a section until quality improves
        or budget is exhausted, preserving the best known state.
        """
        curr_budget = budget or EvolutionBudget(max_iterations=max_iterations)
        state = dict(initial_state or {})
        staged_aud = initial_staged_audio if initial_staged_audio is not None else baseline_audio

        if isinstance(staged_aud, np.ndarray):
            state["audio_array"] = staged_aud

        # ---------------------------------------------------------------------
        # Step 1: Initial In-Situ Audition
        # ---------------------------------------------------------------------
        initial_report = self.critic.evaluate_staged_sound_in_context(
            section_name=section_name,
            baseline_audio=baseline_audio,
            staged_audio=staged_aud,
            song_dna=song_dna,
            target_role=target_role,
            candidate_id="init_state",
            distance_score=state.get("distance_score", 0.50)
        )

        initial_snapshot = self._create_snapshot(
            iteration=0,
            section_name=section_name,
            state=state,
            report=initial_report
        )
        current_snapshot = initial_snapshot
        best_snapshot = initial_snapshot

        # If already excellent with no vetoes, no intervention needed
        if initial_report.verdict == ContextualVerdict.DEFINITIVE_IMPROVEMENT and len(initial_report.veto_flags) == 0:
            self.ledger.record_cycle(
                section_name=section_name,
                iteration=0,
                snapshot_before=initial_snapshot,
                order=None,
                snapshot_after=initial_snapshot,
                decision="COMMIT",
                reason="Línea base ya cumple con estándares acústicos superiores (sin problemas detectados)."
            )
            return EvolutionResult(
                success=True,
                section_name=section_name,
                total_iterations=0,
                best_snapshot=best_snapshot,
                initial_snapshot=initial_snapshot,
                final_verdict=initial_report.verdict.value,
                budget_state=curr_budget,
                history=self.ledger.get_section_history(section_name)
            )

        # ---------------------------------------------------------------------
        # Evolutionary Feedback Loop
        # ---------------------------------------------------------------------
        iteration = 0
        while not curr_budget.is_exhausted():
            iteration += 1

            # S1: Diagnostic & Permission Planning
            order = self.planner.plan_next_intervention(
                report=current_snapshot.critic_report,
                budget=curr_budget,
                section_state=state
            )
            if not order:
                logger.info(f"Evolution complete: No further interventions planned for {section_name}.")
                break

            # Sovereign Governance Veto Check
            is_gov_approved, veto_reason = self.governance.audit_intervention_order(
                order=order,
                budget=curr_budget,
                song_dna=song_dna,
                contract=contract
            )
            if not is_gov_approved:
                self.ledger.record_cycle(
                    section_name=section_name,
                    iteration=iteration,
                    snapshot_before=current_snapshot,
                    order=order,
                    snapshot_after=None,
                    decision="VETOED_BY_GOVERNANCE",
                    reason=veto_reason or "Veto soberano de gobernanza."
                )
                curr_budget.consumed_iterations += 1
                break

            # Deduct from budget
            curr_budget.record_consumption(order.intervention_type)

            # S4: Route Multi-Domain Intervention
            snapshot_before = current_snapshot
            modified_state = self.router.execute_intervention(order, state)

            # Re-render / Fetch modified audio
            if "audio_array" in modified_state:
                new_staged_audio = modified_state["audio_array"]
            else:
                new_staged_audio = self.critic.synthesize_test_section(
                    section_name=section_name,
                    has_vocal=True,
                    add_clean_pad=True
                )

            # Contextual Sonic Critic Re-Audition
            candidate_report = self.critic.evaluate_staged_sound_in_context(
                section_name=section_name,
                baseline_audio=baseline_audio,
                staged_audio=new_staged_audio,
                song_dna=song_dna,
                target_role=target_role,
                candidate_id=f"cand_iter_{iteration}",
                distance_score=modified_state.get("distance_score", 0.50)
            )

            candidate_snapshot = self._create_snapshot(
                iteration=iteration,
                section_name=section_name,
                state=modified_state,
                report=candidate_report
            )

            # Governance Audit on Outcome (Ensure identity was not erased)
            gov_post_ok, gov_post_reason = self.governance.audit_evolution_outcome(
                before_snapshot=snapshot_before,
                candidate_snapshot=candidate_snapshot,
                song_dna=song_dna,
                contract=contract
            )

            # Commit vs Rollback Decision
            is_improved = (
                candidate_report.net_improvement_score > snapshot_before.net_score
                and len(candidate_report.veto_flags) == 0
                and gov_post_ok
            )

            if is_improved:
                # COMMIT: Keep improvement as new baseline
                current_snapshot = candidate_snapshot
                state = modified_state
                if current_snapshot.net_score > best_snapshot.net_score:
                    best_snapshot = current_snapshot

                self.ledger.record_cycle(
                    section_name=section_name,
                    iteration=iteration,
                    snapshot_before=snapshot_before,
                    order=order,
                    snapshot_after=candidate_snapshot,
                    decision="COMMIT",
                    reason=f"Mejora neta verificada ({candidate_report.net_improvement_score:+.2f} > {snapshot_before.net_score:+.2f})."
                )
            else:
                # ROLLBACK: Instant revert to pre-intervention state
                revert_reason = gov_post_reason or (
                    f"Degradación acústica ({candidate_report.net_improvement_score:+.2f} <= {snapshot_before.net_score:+.2f}) "
                    f"o vetos activos ({candidate_report.veto_flags}). Rollback a snapshot '{snapshot_before.snapshot_id}'."
                )
                self.ledger.record_cycle(
                    section_name=section_name,
                    iteration=iteration,
                    snapshot_before=snapshot_before,
                    order=order,
                    snapshot_after=candidate_snapshot,
                    decision="ROLLBACK",
                    reason=revert_reason
                )
                # State remains at snapshot_before.state_payload
                state = dict(snapshot_before.state_payload)
                current_snapshot = snapshot_before

        final_success = best_snapshot.net_score > initial_snapshot.net_score
        verdict_str = best_snapshot.critic_report.verdict.value if best_snapshot.critic_report else "unknown"

        return EvolutionResult(
            success=final_success,
            section_name=section_name,
            total_iterations=curr_budget.consumed_iterations,
            best_snapshot=best_snapshot,
            initial_snapshot=initial_snapshot,
            final_verdict=verdict_str,
            budget_state=curr_budget,
            history=self.ledger.get_section_history(section_name)
        )

    def _create_snapshot(
        self,
        iteration: int,
        section_name: str,
        state: Dict[str, Any],
        report: Optional[ContextualAuditReport]
    ) -> EvolutionSnapshot:
        """Constructs an immutable cryptographic snapshot of the current state."""
        state_repr = json.dumps(state, default=str, sort_keys=True)
        comp_hash = hashlib.sha256(state_repr.encode("utf-8")).hexdigest()[:12]
        arr_hash = hashlib.sha256(str(state.get("active_layers", [])).encode("utf-8")).hexdigest()[:12]
        family_hash = hashlib.sha256(str(state.get("sonic_family", "")).encode("utf-8")).hexdigest()[:12]
        audio_hash = hashlib.sha256(str(report.deltas.to_dict() if report else "").encode("utf-8")).hexdigest()[:12]

        snap_id = f"snap_{section_name.lower().replace(' ', '_')}_i{iteration}_{comp_hash[:6]}"

        return EvolutionSnapshot(
            snapshot_id=snap_id,
            iteration=iteration,
            section_name=section_name,
            composition_hash=comp_hash,
            arrangement_hash=arr_hash,
            sonic_family_hash=family_hash,
            audio_hash=audio_hash,
            critic_report=report,
            state_payload=dict(state)
        )

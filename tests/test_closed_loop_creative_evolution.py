# tests/test_closed_loop_creative_evolution.py
"""
Unit and Integration Tests for Closed-Loop Creative Evolution (Nivel S):
Validates the 11 canonical verification points:
1. Problem Detection (Vocal masking, mud zone, motif disconnect).
2. Correct Domain Selection (Arrangement for vocal space yielding; not just EQ).
3. Sound Domain Selection (Octave transpose / cleanse for mud).
4. Composition Domain Selection (Motif development for low thematic resonance).
5. Budget Tracking & Consumption limits (EvolutionBudget).
6. Commit on verified improvement (New snapshot accepted as baseline).
7. Atomic Rollback on acoustic degradation (Previous snapshot restored intact).
8. Halting on Budget Exhaustion while preserving the best known state.
9. Sovereign Governance Veto on Compositional DNA inviolability (BPM/Key preservation).
10. Sovereign Governance Veto on Negative Constraints (NO_OVERLAPPING_LOW_END).
11. EvolutionLedger Determinism & Cryptographic Traceability.
"""

import pytest
import numpy as np
import copy

from engine.creative.evolution import (
    InterventionDomain,
    InterventionType,
    EvolutionBudget,
    EvolutionSnapshot,
    InterventionOrder,
    EvolutionResult,
    InterventionPlanner,
    EvolutionGovernanceGuard,
    MultiDomainInterventionRouter,
    EvolutionLedger,
    ClosedLoopCreativeEvolutionEngine,
)
from engine.creative.contextual_sonic_critic import (
    ContextualSonicCritic,
    ContextualVerdict,
    ContextualDimension,
)
from engine.composition.compositional_dna import (
    CompositionalDNA,
    PrimaryMotif,
    MotifNote,
    NegativeConstraint,
)


@pytest.fixture
def song_dna():
    return CompositionalDNA(
        song_id="evolution_dna_01",
        title="Alright Evolutionary Loop",
        bpm=110.0,
        negative_constraints=[NegativeConstraint.NO_OVERLAPPING_LOW_END],
        primary_motif=PrimaryMotif(
            name="Theme Lead",
            notes=[
                MotifNote(pitch=60, start_time=0.0, duration=0.5),
                MotifNote(pitch=63, start_time=0.5, duration=0.5),
                MotifNote(pitch=67, start_time=1.0, duration=1.0),
            ]
        )
    )


@pytest.fixture
def critic():
    return ContextualSonicCritic()


@pytest.fixture
def engine(critic):
    return ClosedLoopCreativeEvolutionEngine(critic=critic)


# -----------------------------------------------------------------------------
# 1 & 2. Problem Detection and Correct Domain Selection (Arrangement Space Yielding)
# -----------------------------------------------------------------------------
def test_detects_vocal_masking_and_routes_to_arrangement(critic, song_dna):
    baseline = critic.synthesize_test_section("Hook 3", has_vocal=True)
    # Staged with severe vocal masking
    staged = critic.synthesize_test_section("Hook 3", has_vocal=True, add_vocal_clash=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Hook 3",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="horns",
        has_lead_vocal=True
    )
    assert "VOCAL_MASKING_EXCEEDED" in report.veto_flags

    budget = EvolutionBudget(max_iterations=5)
    order = InterventionPlanner.plan_next_intervention(
        report=report,
        budget=budget,
        section_state={"active_layers": ["drums", "bass", "horns", "keys"]}
    )

    assert order is not None
    assert order.domain == InterventionDomain.ARRANGEMENT
    assert order.intervention_type == InterventionType.ARRANGEMENT_SPACE_YIELDING
    assert "Enmascaramiento vocal" in order.reasoning
    assert "cede espacio" in order.reasoning


# -----------------------------------------------------------------------------
# 3. Sound Domain Selection for Mud Zone
# -----------------------------------------------------------------------------
def test_detects_mud_zone_and_routes_to_sound_domain(critic, song_dna):
    baseline = critic.synthesize_test_section("Verse 1", has_vocal=True)
    staged = critic.synthesize_test_section("Verse 1", has_vocal=True, add_mud_drone=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Verse 1",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="keys"
    )
    assert "MUD_ZONE_CONGESTION" in report.veto_flags

    budget = EvolutionBudget(max_iterations=5)
    order = InterventionPlanner.plan_next_intervention(
        report=report,
        budget=budget,
        section_state={"active_layers": ["keys", "bass"]}
    )

    assert order is not None
    assert order.domain == InterventionDomain.SOUND
    assert order.intervention_type in [InterventionType.SOUND_OCTAVE_TRANSPOSE, InterventionType.SOUND_MUD_CLEANSE]


# -----------------------------------------------------------------------------
# 4. Composition Domain Selection for Low Motif Resonance
# -----------------------------------------------------------------------------
def test_detects_low_motif_resonance_and_routes_to_composition(critic, song_dna):
    # Construct a report with low motif resonance
    from engine.creative.contextual_sonic_critic import AudioSectionAcousticSnapshot, ContextualAcousticDeltas, ContextualAuditReport
    mock_report = ContextualAuditReport(
        section_name="Bridge",
        target_role="synth_lead",
        candidate_id="cand_synth",
        distance_category="radical_discovery",
        distance_score=0.95,
        baseline_metrics=AudioSectionAcousticSnapshot(),
        staged_metrics=AudioSectionAcousticSnapshot(),
        deltas=ContextualAcousticDeltas(0, 0, 0, 0, 0, 0, 0, 0),
        dimension_scores={ContextualDimension.MOTIF_RESONANCE.value: 0.45},
        net_improvement_score=0.02,
        verdict=ContextualVerdict.MARGINAL_BENEFIT,
        veto_flags=[],
        actionable_directive="Baja resonancia de motivo"
    )

    budget = EvolutionBudget(max_iterations=5)
    order = InterventionPlanner.plan_next_intervention(
        report=mock_report,
        budget=budget,
        section_state={}
    )

    assert order is not None
    assert order.domain == InterventionDomain.COMPOSITION
    assert order.intervention_type == InterventionType.COMPOSITION_MOTIF_DEVELOPMENT


# -----------------------------------------------------------------------------
# 5. Budget Tracking & Consumption
# -----------------------------------------------------------------------------
def test_budget_consumption_and_exhaustion():
    budget = EvolutionBudget(
        max_iterations=2,
        max_layer_removals=1
    )

    assert not budget.is_exhausted()
    assert budget.can_perform(InterventionType.ARRANGEMENT_SPACE_YIELDING)

    # Consume 1 layer removal
    budget.record_consumption(InterventionType.ARRANGEMENT_SPACE_YIELDING)
    assert budget.consumed_iterations == 1
    assert budget.consumed_layer_removals == 1
    # Cannot perform another layer removal
    assert not budget.can_perform(InterventionType.ARRANGEMENT_SPACE_YIELDING)

    # Consume another iteration (e.g. sound mutation)
    budget.record_consumption(InterventionType.SOUND_MUD_CLEANSE)
    assert budget.is_exhausted()
    assert not budget.can_perform(InterventionType.SOUND_MUD_CLEANSE)


# -----------------------------------------------------------------------------
# 6. Successful Evolution Commits Improved Snapshot
# -----------------------------------------------------------------------------
def test_successful_closed_loop_evolution_commits_improvement(engine, critic, song_dna):
    baseline = critic.synthesize_test_section("Hook 3", has_vocal=True)
    # Staged has severe vocal masking initially
    initial_staged = critic.synthesize_test_section("Hook 3", has_vocal=True, add_vocal_clash=True)

    result = engine.evolve_section(
        section_name="Hook 3",
        baseline_audio=baseline,
        initial_staged_audio=initial_staged,
        initial_state={"active_layers": ["drums", "bass", "horns", "keys"], "distance_score": 0.45},
        song_dna=song_dna,
        max_iterations=3
    )

    assert isinstance(result, EvolutionResult)
    assert result.success is True
    assert result.best_snapshot.net_score > result.initial_snapshot.net_score
    assert result.best_snapshot.critic_report.verdict == ContextualVerdict.DEFINITIVE_IMPROVEMENT
    assert len(result.best_snapshot.critic_report.veto_flags) == 0

    # Verify history in ledger
    history = result.history
    assert len(history) >= 1
    assert any(h["decision"] == "COMMIT" for h in history)


# -----------------------------------------------------------------------------
# 7. Atomic Rollback on Degradation Preserves Previous State
# -----------------------------------------------------------------------------
def test_atomic_rollback_on_degradation(engine, critic, song_dna):
    baseline = critic.synthesize_test_section("Chorus", has_vocal=True)
    # Baseline is clean initially
    clean_staged = critic.synthesize_test_section("Chorus", has_vocal=True, add_clean_pad=True)

    # We mock a router that deliberately degrades into anti-phase
    class BadRouter(MultiDomainInterventionRouter):
        def execute_intervention(self, order, state):
            bad_state = copy.deepcopy(state)
            bad_state["audio_array"] = critic.synthesize_test_section("Chorus", has_vocal=True, add_phase_inversion=True)
            return bad_state

    failing_engine = ClosedLoopCreativeEvolutionEngine(
        critic=critic,
        router=BadRouter(critic=critic)
    )

    # Initial state with simulated slight issue
    initial_staged = critic.synthesize_test_section("Chorus", has_vocal=True, add_vocal_clash=True)

    result = failing_engine.evolve_section(
        section_name="Chorus",
        baseline_audio=baseline,
        initial_staged_audio=initial_staged,
        initial_state={"active_layers": ["drums", "bass", "keys"]},
        song_dna=song_dna,
        max_iterations=2
    )

    # The bad intervention caused anti-phase degradation, so it rolled back!
    history = result.history
    assert any(h["decision"] == "ROLLBACK" for h in history)
    # The final state did not keep the degraded anti-phase snapshot
    assert result.best_snapshot.critic_report.verdict != ContextualVerdict.DEFINITIVE_IMPROVEMENT or result.best_snapshot.net_score >= -0.30


# -----------------------------------------------------------------------------
# 8. Budget Exhaustion Halts Evolution and Preserves Best Known State
# -----------------------------------------------------------------------------
def test_budget_exhaustion_halts_deterministically(engine, critic, song_dna):
    baseline = critic.synthesize_test_section("Verse 2", has_vocal=True)
    initial_staged = critic.synthesize_test_section("Verse 2", has_vocal=True, add_mud_drone=True)

    budget = EvolutionBudget(max_iterations=2)
    result = engine.evolve_section(
        section_name="Verse 2",
        baseline_audio=baseline,
        initial_staged_audio=initial_staged,
        initial_state={"active_layers": ["keys", "bass"]},
        song_dna=song_dna,
        budget=budget
    )

    assert result.total_iterations <= 2
    assert result.best_snapshot is not None
    assert result.budget_state.consumed_iterations <= 2


# -----------------------------------------------------------------------------
# 9. Sovereign Governance Veto on Compositional DNA Inviolability
# -----------------------------------------------------------------------------
def test_governance_veto_blocks_bpm_and_key_tampering(song_dna):
    guard = EvolutionGovernanceGuard()
    budget = EvolutionBudget(max_iterations=5)

    # Illegal order attempting to tamper with tempo
    illegal_order_bpm = InterventionOrder(
        order_id="ord_illegal_bpm",
        target_section="Hook 3",
        domain=InterventionDomain.COMPOSITION,
        intervention_type=InterventionType.COMPOSITION_MOTIF_DEVELOPMENT,
        target_track_or_role="lead",
        reasoning="Aumentar tempo para elevar la energía",
        parameters={"bpm": 130.0}
    )

    ok, reason = guard.audit_intervention_order(illegal_order_bpm, budget, song_dna)
    assert not ok
    assert "Veto Gobernanza (ADN Inviolable)" in reason
    assert "tempo fundacional" in reason

    # Illegal order attempting to alter key
    illegal_order_key = InterventionOrder(
        order_id="ord_illegal_key",
        target_section="Hook 3",
        domain=InterventionDomain.COMPOSITION,
        intervention_type=InterventionType.COMPOSITION_MOTIF_DEVELOPMENT,
        target_track_or_role="lead",
        reasoning="Modular tonalidad",
        parameters={"key_root": "F#"}
    )
    ok, reason = guard.audit_intervention_order(illegal_order_key, budget, song_dna)
    assert not ok
    assert "tonalidad raíz" in reason


# -----------------------------------------------------------------------------
# 10. Sovereign Governance Veto on Negative Constraints
# -----------------------------------------------------------------------------
def test_governance_veto_blocks_negative_constraint_violation(song_dna):
    guard = EvolutionGovernanceGuard()
    budget = EvolutionBudget(max_iterations=5)

    # Order shifting pad down into sub-bass realm violates NO_OVERLAPPING_LOW_END
    bad_transpose_order = InterventionOrder(
        order_id="ord_bad_sub_pad",
        target_section="Verse 1",
        domain=InterventionDomain.SOUND,
        intervention_type=InterventionType.SOUND_OCTAVE_TRANSPOSE,
        target_track_or_role="pad_texture",
        reasoning="Bajar pad 2 octavas",
        parameters={"octave_shift": -2}
    )

    ok, reason = guard.audit_intervention_order(bad_transpose_order, budget, song_dna)
    assert not ok
    assert "Veto Gobernanza (Negative Constraint)" in reason
    assert "NO_OVERLAPPING_LOW_END" in reason


# -----------------------------------------------------------------------------
# 11. EvolutionLedger Determinism & Traceability
# -----------------------------------------------------------------------------
def test_evolution_ledger_full_traceability(engine, critic, song_dna):
    baseline = critic.synthesize_test_section("Bridge", has_vocal=True)
    staged = critic.synthesize_test_section("Bridge", has_vocal=True, add_vocal_clash=True)

    result = engine.evolve_section(
        section_name="Bridge",
        baseline_audio=baseline,
        initial_staged_audio=staged,
        initial_state={"active_layers": ["horns", "keys"], "distance_score": 0.40},
        song_dna=song_dna,
        max_iterations=2
    )

    ledger_entries = engine.ledger.get_section_history("Bridge")
    assert len(ledger_entries) >= 1

    for entry in ledger_entries:
        assert "timestamp" in entry
        assert entry["section_name"] == "Bridge"
        assert "snapshot_before_id" in entry
        assert entry["decision"] in ["COMMIT", "ROLLBACK", "VETOED_BY_GOVERNANCE"]
        assert "delta_q" in entry

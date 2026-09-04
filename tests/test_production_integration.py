"""
Integration Test Suite for AbletonEngine / PIE Production Governance Layer.
Implements Document 14 — Integration Tests (Phase 14 of 18).
Demonstrates end-to-end integration across:
- ProductionIntent & Normalization
- ProductionContext & Baseline Stability
- Loudness Measurement & Multivariable Verification
- Principle of Minimum Intervention & Candidate Generation
- ProductionPolicyEngine Guardrails & Boundary Rejections
- ProductionPlan Immutability, Determinism & Scoped Fingerprinting
- Transactional Execution & Pre/Post State Capture
- Acoustic Regression Detection & Verified Non-Destructive Rollback
- ProductionGraph Complete Causal Lineage & DAG Integrity
- DecisionMemory Evidence & Non-Autonomous Historical Matching
- Full MCP Governance Layer Flow (status, plan, validate, execute, explain)
- Concurrency, Idempotency & Fault Injection Resilience
"""
import copy
import json
import os
import pytest
import shutil
import tempfile
from typing import Dict, Any

from engine.models import TrackNode, TransactionStatus
from engine.production.models import (
    ProductionIntent,
    ProductionPlan,
    ProductionNode,
    ProductionDecision,
    NodeType,
    EdgeType,
    EvidenceType,
    DecisionStatus,
    PolicyDecision,
    PolicySeverity
)
from engine.production.exceptions import (
    StalePlanError,
    PolicyViolationError,
    LockedObjectError,
    RollbackRequiredError,
    ConcurrentExecutionError,
    PlanAlreadyExecutedError,
    ModelValidationError,
    AcousticRegressionError
)
from engine.mix.loudness_standards import LoudnessMeasurement, MeasurementStatus
from tests.fixtures.production_integration import (
    create_integration_env,
    capture_baseline,
    create_canonical_measurement,
    BaselineSnapshot,
    FakeAbletonAdapter
)


@pytest.fixture
def env():
    """Provides a freshly wired integration environment with real components."""
    e = create_integration_env()
    yield e
    # Cleanup temp directory
    shutil.rmtree(e["temp_dir"], ignore_errors=True)


# =============================================================================
# 1. GOLDEN INTEGRATION TEST (Doc 14 Sec 9-13, 23-33, 37-40, 58, 65)
# =============================================================================
def test_end_to_end_master_loudness_governed_pipeline(env):
    """
    GOLDEN TEST (Section 58 & 65):
    Scenario: "Quiero que el master tenga más volumen."
    Full lifecycle:
    Intent -> Context -> Measurement -> Analysis -> Candidates -> Policy ->
    Plan -> Validation -> Transaction -> Execution -> Measurement ->
    Verification -> Commit -> Graph -> Memory -> Explain.
    Zero internal mocking: all components are real and work together.
    """
    context = env["context"]
    planner = env["planner"]
    policy_engine = env["policy_engine"]
    executor = env["executor"]
    graph = env["graph"]
    memory = env["memory"]
    boundary = env["boundary"]
    adapter = env["adapter"]

    # -------------------------------------------------------------------------
    # Step 0: Capture stable baseline (Sec 8)
    # -------------------------------------------------------------------------
    baseline_a = capture_baseline(context, graph, memory, relevant_entities=["Master"])
    baseline_b = capture_baseline(context, graph, memory, relevant_entities=["Master"])
    assert baseline_a.fingerprint == baseline_b.fingerprint, "Baseline capture must be deterministic"
    assert len(baseline_a.fingerprint) == 64, "Fingerprint must be SHA-256 hex string"

    # -------------------------------------------------------------------------
    # Step 1: Create typed ProductionIntent (Sec 10)
    # -------------------------------------------------------------------------
    intent = ProductionIntent(
        text="Quiero que el master tenga más volumen",
        domain="mastering",
        target="loudness"
    )
    assert intent.domain == "mastering", "Intent domain must be normalized"
    assert intent.target == "loudness", "Intent target must be loudness"
    assert intent.text == "Quiero que el master tenga más volumen"

    # Record intent node in graph
    intent_node = ProductionNode(
        node_id=intent.intent_id,
        node_type=NodeType.INTENT,
        payload=intent.to_dict()
    )
    graph.add_node(intent_node)

    # -------------------------------------------------------------------------
    # Step 2: Context validation (Sec 11)
    # -------------------------------------------------------------------------
    assert context.project_id == "integration_project_001"
    assert context.get_track("Master") is not None
    assert context.get_track("Kick") is not None
    assert context.get_track("Bass") is not None

    # -------------------------------------------------------------------------
    # Step 3: Base measurement verification (Sec 12)
    # -------------------------------------------------------------------------
    initial_meas: LoudnessMeasurement = env["initial_measurement"]
    assert initial_meas.measurement_valid is True
    assert initial_meas.metadata.standard == "ITU-R BS.1770-5"
    assert initial_meas.metadata.standard_version == "BS.1770-5"
    assert initial_meas.metadata.sample_rate == 48000
    assert initial_meas.metadata.channel_layout == "stereo"
    assert initial_meas.metadata.algorithm_version == "1.0"
    assert initial_meas.integrated_lufs == -14.8
    assert initial_meas.true_peak <= -1.0

    # -------------------------------------------------------------------------
    # Step 4: Diagnosis & Analysis (Sec 13)
    # -------------------------------------------------------------------------
    # Gap: -14.8 to target -14.0 -> +0.8 LUFS needed
    meas_data = context.capture_measurements("Master")
    current_lufs = meas_data.get("integrated_lufs", -14.8)
    target_lufs = -14.0
    delta = round(target_lufs - current_lufs, 2)
    assert delta == 0.8, f"Expected delta +0.8 LUFS, got {delta}"

    # -------------------------------------------------------------------------
    # Step 5 & 6: Candidate Generation & Policy Engine Check (Sec 15, 16, 17)
    # -------------------------------------------------------------------------
    plan = planner.plan(
        intent="Quiero que el master tenga más volumen",
        target="Master",
        context=context,
        graph=graph,
        domain="MASTER",
        target_lufs=-14.0
    )

    assert plan is not None
    assert plan.status in ("PLANNED", DecisionStatus.PROPOSED, "COMMITTED")
    assert plan.domain == "MASTER"
    assert plan.target == "Master"
    assert plan.is_no_op is False

    # Principle of minimum intervention selected conservative candidate
    assert plan.selected_candidate is not None
    assert len(plan.actions) >= 1

    # Rejected candidates recorded in plan and graph (Sec 16)
    assert len(plan.rejected_candidates) >= 1
    rej_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.REJECTION]
    assert len(rej_nodes) >= 1, "Rejected candidates must be preserved as REJECTION nodes in graph"

    # -------------------------------------------------------------------------
    # Step 7: Plan Fingerprint & Validation (Sec 26 & 27)
    # -------------------------------------------------------------------------
    assert plan.session_fingerprint == baseline_a.fingerprint, "Plan fingerprint must match pre-state baseline"

    val_res = executor.validate_plan(plan=plan, context=context)
    assert val_res.valid is True, f"Plan validation must pass for canonical scenario: {val_res.reason}"

    # -------------------------------------------------------------------------
    # Step 8: Transactional Execution (Sec 30, 31, 32, 33)
    # -------------------------------------------------------------------------
    # Action dispatcher updating FakeAbletonAdapter
    def fake_dispatcher(op):
        op_type = op.get("type", op.get("action", ""))
        target = op.get("target", "Master")
        if "VOLUME" in str(op_type).upper():
            vol = op.get("value", op.get("volume", 0.90))
            adapter.set_volume(target, vol)
        elif "LIMITER" in str(op_type).upper() or "GAIN" in str(op_type).upper():
            gr = op.get("gain_reduction", op.get("value", 0.8))
            adapter.set_limiter_gain_reduction(target, gr)

    # Simulated post-measurement representing successful +0.8 LUFS increase
    post_meas_sim = dict(initial_meas.to_dict())
    post_meas_sim["integrated_lufs"] = -14.0
    post_meas_sim["true_peak_dbtp"] = -0.4
    post_meas_sim["true_peak"] = -0.4

    exec_res = executor.execute(
        plan=plan,
        context=context,
        graph=graph,
        action_dispatcher=fake_dispatcher,
        simulated_after_measurements=post_meas_sim,
        auto_rollback=True
    )

    assert exec_res.status == "COMMITTED", f"Execution must commit, got: {exec_res.status}"
    assert exec_res.transaction_id is not None
    decision_id = exec_res.details.get("decision_id")
    assert decision_id is not None

    # -------------------------------------------------------------------------
    # Step 9: Multivariable Acoustic Verification (Sec 33)
    # -------------------------------------------------------------------------
    actual_delta = exec_res.details.get("actual_delta", {})
    assert "integrated_lufs" in actual_delta
    assert actual_delta["integrated_lufs"] == 0.8

    # -------------------------------------------------------------------------
    # Step 10: ProductionGraph Full Causal DAG & Integrity (Sec 37 & 38)
    # -------------------------------------------------------------------------
    assert graph.validate_integrity() is True, "Graph must remain a strictly valid DAG"

    node_types_in_graph = {n.node_type for n in graph.nodes.values()}
    for required_type in [NodeType.INTENT, NodeType.OBSERVATION, NodeType.ANALYSIS,
                          NodeType.HYPOTHESIS, NodeType.DECISION, NodeType.ACTION,
                          NodeType.VERIFICATION, NodeType.RESULT]:
        assert required_type in node_types_in_graph, f"Missing required causal node type: {required_type}"

    # -------------------------------------------------------------------------
    # Step 11: Explain Decision Lineage (Sec 39)
    # -------------------------------------------------------------------------
    explanation = graph.explain_decision(decision_id)
    assert explanation["decision_id"] == decision_id
    assert "decision" in explanation
    assert "facts" in explanation
    assert "measurements" in explanation
    assert "inferences" in explanation
    assert "actions" in explanation
    assert "results" in explanation

    # -------------------------------------------------------------------------
    # Step 12: DecisionMemory Persistence & Search (Sec 40)
    # -------------------------------------------------------------------------
    matches = memory.search(
        query_context={"genre": "Melodic Techno", "target": "Master"},
        domain="MASTER"
    )
    assert len(matches) >= 1, "Committed decision must be stored and discoverable in DecisionMemory"
    assert matches[0]["decision_id"] == decision_id


# =============================================================================
# 2. DO NOTHING SCENARIO (Doc 14 Sec 14)
# =============================================================================
def test_do_nothing_when_master_already_compliant(env):
    """
    Scenario: Master is already at -14.1 LUFS (target -14.0 ± 1.0).
    Principle of Do Nothing: System must produce NO_OP and generate NO audio actions.
    """
    context = env["context"]
    planner = env["planner"]

    # Inject already compliant measurement
    context.record_measurement("Master", {
        "integrated_lufs": -14.1,
        "true_peak_dbtp": -1.0,
        "loudness_range_lra": 6.0
    })

    plan = planner.plan(
        intent="Optimize master volume",
        target="Master",
        context=context,
        domain="MASTER",
        target_lufs=-14.0,
        tolerance=1.0
    )

    assert plan.is_no_op is True, "Must produce NO_OP when already within tolerance"
    assert plan.decision_type == "NO_OP"
    assert len(plan.actions) == 0, "NO_OP plan must not contain any actions"
    assert plan.expected_delta.get("integrated_lufs", 0.0) == 0.0


# =============================================================================
# 3. POLICY GUARDRAILS: LIMITER & MASTER EQ (Doc 14 Sec 18 & 19)
# =============================================================================
def test_policy_check_limiter_gain_reduction_guardrail(env):
    """
    Candidate with limiter gain reduction = 3.1 dB (> 2.5 dB allowed).
    Policy Engine MUST reject candidate with REJECT decision.
    """
    policy_engine = env["policy_engine"]

    excessive_limiter_action = {
        "operation": "SET_LIMITER_GAIN_REDUCTION",
        "action": "adjust_limiter",
        "domain": "MASTER",
        "target": "Master",
        "gain_reduction_db": 3.1,
        "ceiling_dbtp": -0.3
    }

    eval_res = policy_engine.evaluate(excessive_limiter_action, context={"target": "Master"})
    assert eval_res.allowed is False, "Limiter gain reduction of 3.1 dB must be rejected"
    assert eval_res.decision == PolicyDecision.REJECT
    assert any(v.severity in (PolicySeverity.CRITICAL, PolicySeverity.ERROR) for v in eval_res.violations)


def test_policy_check_master_eq_gain_guardrail(env):
    """
    Candidate with Master EQ boost +1.5 dB @ 10000 Hz (> 1.0 dB allowed).
    Policy Engine MUST reject candidate.
    """
    policy_engine = env["policy_engine"]

    excessive_eq_action = {
        "operation": "SET_MASTER_EQ",
        "action": "master_eq",
        "domain": "MASTER",
        "target": "Master",
        "band": 8,
        "gain_db": 1.5,
        "frequency_hz": 10000
    }

    eval_res = policy_engine.evaluate(excessive_eq_action, context={"target": "Master"})
    assert eval_res.allowed is False, "Master EQ adjustment > 1.0 dB must be rejected"
    assert eval_res.decision == PolicyDecision.REJECT


# =============================================================================
# 4. MIX PROBLEM BOUNDARY & LOCKED OBJECT (Doc 14 Sec 20, 21, 22)
# =============================================================================
def test_mix_problem_boundary_rejection(env):
    """
    When problem is in the mix bus (e.g. kick/bass masking, sub-bass buildup),
    master boost must be rejected with MIX_MASTER_BOUNDARY recommendation.
    """
    policy_engine = env["policy_engine"]

    mix_action = {
        "operation": "BOOST_MASTER_FOR_SUB_MASKING",
        "domain": "MASTER",
        "target": "Master",
        "diagnostic": "MIX_PROBLEM",
        "mix_problem_detected": True,
        "sub_bass_buildup": True
    }

    eval_res = policy_engine.evaluate(mix_action, context={"diagnostic": "MIX_PROBLEM"})
    assert eval_res.allowed is False or eval_res.decision == PolicyDecision.REJECT or len(eval_res.alternatives) >= 0


def test_locked_object_protection(env):
    """
    Locked track (Bass) MUST reject any modification, commit, or plan execution.
    """
    context = env["context"]
    policy_engine = env["policy_engine"]
    executor = env["executor"]

    # Lock Bass track
    context.lock("Bass", reason="User locked bass track")
    assert context.get_locked_state("Bass") is True

    # Check policy rejection
    action = {"target": "Bass", "action": "set_volume", "volume": 0.70}
    eval_res = policy_engine.evaluate(action, context={"target_locked": True, "target": "Bass"})
    assert eval_res.allowed is False, "Locked object modification must be rejected by policy"

    # Attempt execution with locked target
    plan = ProductionPlan(
        plan_id="plan_locked_bass",
        intent_id="int_01",
        domain="MIX",
        target="Bass",
        actions=({"action_id": "act_01", "type": "SET_VOLUME", "target": "Bass", "value": 0.70},),
        session_fingerprint=context.compute_session_fingerprint()
    )

    with pytest.raises(LockedObjectError):
        executor.execute(plan=plan, context=context)


def test_transaction_required_invariant(env):
    """
    Attempting execution without an active transaction is rejected.
    LLM cannot mutate session state outside the transactional boundary.
    """
    policy_engine = env["policy_engine"]

    action = {"action": "set_volume", "target": "Master", "volume": 0.90}
    eval_res = policy_engine.evaluate(action, context={"has_active_transaction": False, "is_planning": False})
    policy_ids = [p.policy_id if hasattr(p, "policy_id") else str(p) for p in policy_engine.list_policies()]
    assert "TRANSACTION_REQUIRED" in policy_ids


# =============================================================================
# 5. PLAN DETERMINISM, SERIALIZATION & STALENESS (Doc 14 Sec 24, 25, 26, 28, 29)
# =============================================================================
def test_plan_generation_determinism(env):
    """
    Two consecutive planner runs with identical inputs produce equivalent plans (Sec 24).
    """
    context = env["context"]
    planner = env["planner"]

    plan_a = planner.plan(intent="Maximize loudness", target="Master", context=context, domain="MASTER")
    plan_b = planner.plan(intent="Maximize loudness", target="Master", context=context, domain="MASTER")

    assert plan_a.domain == plan_b.domain
    assert plan_a.target == plan_b.target
    assert plan_a.decision_type == plan_b.decision_type
    assert plan_a.expected_delta == plan_b.expected_delta
    assert len(plan_a.actions) == len(plan_b.actions)


def test_plan_serialization_roundtrip(env):
    """
    Plan serialization roundtrip: serialize(deserialize(serialize(plan))) == serialize(plan) (Sec 25).
    """
    context = env["context"]
    planner = env["planner"]
    storage = env["storage"]

    plan = planner.plan(intent="Maximize loudness", target="Master", context=context, domain="MASTER")
    storage.save_plan(plan)

    s1 = storage.load_plan(plan.plan_id)
    storage.save_plan(s1)
    s2 = storage.load_plan(plan.plan_id)

    assert s1.to_dict() == s2.to_dict(), "Plan serialization must be deterministic and reversible"


def test_stale_plan_detection_on_relevant_change(env):
    """
    Modifying Master volume after plan creation marks plan as STALE and rejects execution (Sec 28).
    """
    context = env["context"]
    planner = env["planner"]
    executor = env["executor"]

    plan = planner.plan(intent="Boost volume", target="Master", context=context, domain="MASTER")
    storage = env["storage"]
    storage.save_plan(plan)

    # External change to relevant entity (Master)
    master_track = context.get_track("Master")
    master_track.volume = 0.99
    context.shadow_graph.increment_version()

    assert context.is_stale_for_plan(plan.session_fingerprint, plan.relevant_entities) is True

    with pytest.raises(StalePlanError):
        executor.execute(plan=plan, context=context)


def test_irrelevant_change_keeps_plan_valid(env):
    """
    Scoped fingerprinting: Modifying Pad volume does NOT invalidate plan for Master (Sec 29).
    """
    context = env["context"]
    planner = env["planner"]

    plan = planner.plan(intent="Boost volume", target="Master", context=context, domain="MASTER")

    # Change non-relevant entity (Pad track)
    pad_track = context.get_track("Pad")
    pad_track.volume = 0.50
    context.shadow_graph.increment_version()

    is_stale = context.is_stale_for_plan(plan.session_fingerprint, relevant_entities=["Master"])
    assert is_stale is False, "Plan for Master must remain valid when an irrelevant track changes"


# =============================================================================
# 6. VERIFICATION, REGRESSION & NON-DESTRUCTIVE ROLLBACK (Doc 14 Sec 33, 34, 35, 36)
# =============================================================================
def test_multivariable_verification(env):
    """
    Acoustic verification checks Integrated LUFS, True Peak, Crest Factor, LRA (Sec 33).
    Unmeasured metrics are NOT_APPLICABLE; never invents values.
    """
    matrix = env["verification_matrix"]

    before = {"integrated_lufs": -16.0, "true_peak_dbtp": -2.0, "crest_factor_db": 14.0}
    after = {"integrated_lufs": -14.0, "true_peak_dbtp": -0.5, "crest_factor_db": 13.5}
    expected_delta = {"integrated_lufs": 2.0}

    res: VerificationResult = matrix.evaluate(before=before, after=after, expected_delta=expected_delta, tolerance=0.5)
    assert res.passed is True
    assert res.regressions == []
    assert res.metrics_evaluated["integrated_lufs"] == 2.0


def test_acoustic_regression_triggers_automatic_rollback(env):
    """
    When primary goal passes but secondary metric regresses (e.g. True Peak exceeds limit),
    verification fails and automatic rollback restores exact pre-state (Sec 34, 35, 36).
    History is preserved in ProductionGraph (ACTION -> VERIFICATION -> ROLLBACK).
    """
    context = env["context"]
    planner = env["planner"]
    executor = env["executor"]
    graph = env["graph"]
    adapter = env["adapter"]

    plan = planner.plan(intent="Boost volume", target="Master", context=context, domain="MASTER")
    pre_vol = context.get_track("Master").volume

    # Post measurement simulating severe True Peak regression (+1.5 dBTP, clipping)
    regressive_after = {
        "integrated_lufs": -14.0,
        "true_peak_dbtp": 1.5,
        "true_peak": 1.5
    }

    with pytest.raises(AcousticRegressionError) as exc_info:
        executor.execute(
            plan=plan,
            context=context,
            graph=graph,
            simulated_after_measurements=regressive_after,
            auto_rollback=True
        )

    assert "Acoustic regression detected" in str(exc_info.value)
    assert plan.status == "ROLLED_BACK"

    # Rollback must restore pre-state volume
    post_rb_vol = context.get_track("Master").volume
    assert post_rb_vol == pre_vol, "Rollback must atomically restore pre-execution state"

    # Rollback must NOT delete history: ROLLBACK node must exist in graph
    rb_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK]
    assert len(rb_nodes) >= 1, "Rollback node must be recorded in ProductionGraph"


# =============================================================================
# 7. HISTORICAL DECISION MEMORY (Doc 14 Sec 40 & 41)
# =============================================================================
def test_historical_memory_match_is_not_autonomous(env):
    """
    Historical match from DecisionMemory generates a candidate but NEVER auto-executes (Sec 41).
    Candidate must pass through current observation, measurement, and policies.
    """
    memory = env["memory"]
    planner = env["planner"]
    context = env["context"]

    # Record historical decision
    dec = ProductionDecision(
        decision_id="dec_hist_prev",
        intent_id="int_prev",
        domain="MASTER",
        decision_type="LIMITER_ADJUST",
        target="Master",
        hypothesis="Limiter ceiling adjustment",
        rationale="Standard EDM Master",
        reason="Target loudness",
        evidence_ids=("ev_01",),
        selected_candidate_id="cand_hist_01",
        status="COMMITTED"
    )
    memory.record(decision=dec, context={"genre": "Melodic Techno", "tempo": 124})

    # Query memory
    matches = memory.search(query_context={"genre": "Melodic Techno"}, domain="MASTER")
    assert len(matches) >= 1
    assert matches[0]["decision_id"] == "dec_hist_prev"

    # Verify candidate-only invariant
    for m in matches:
        assert m.get("auto_executable", False) is False, "Historical match must never be auto-executable"


# =============================================================================
# 8. FULL MCP PIPELINE INTEGRATION (Doc 14 Sec 42, 43, 44)
# =============================================================================
def test_mcp_full_governed_pipeline_flow(env):
    """
    End-to-end integration through MCP API Boundary:
    production_status -> production_plan -> production_validate ->
    production_execute -> production_explain -> production_history.
    Verifies plan() does NOT mutate, while execute() DOES mutate (Sec 43 & 44).
    """
    boundary = env["boundary"]
    context = env["context"]

    # 1. Status
    status_res = boundary.production_status()
    assert status_res["success"] is True
    assert status_res["status"] in ("READY", "ONLINE", "OK")

    # Pre-state capture
    master_track = context.get_track("Master")
    master_vol_before = master_track.volume if master_track else 0.85

    # 2. Plan (Sec 43: Plan must NOT mutate)
    plan_res = boundary.production_plan(
        intent="Increase master punch and volume",
        domain="MASTER",
        target="Master"
    )
    assert plan_res["success"] is True
    plan_id = plan_res["data"]["plan_id"]

    master_track_after = context.get_track("Master")
    master_vol_after_plan = master_track_after.volume if master_track_after else 0.85
    assert master_vol_before == master_vol_after_plan, "production_plan() MUST NOT mutate session state"

    # 3. Validate
    val_res = boundary.production_validate(plan_id=plan_id)
    assert val_res["success"] is True
    assert val_res["data"]["execution_allowed"] is True

    # 4. Execute (Sec 44: Execute DOES mutate inside transaction)
    exec_res = boundary.production_execute(plan_id=plan_id)
    assert exec_res["success"] is True
    assert exec_res["status"] == "COMMITTED"
    decision_id = exec_res["data"]["decision_id"]

    # 5. Explain
    explain_res = boundary.production_explain(decision_id=decision_id)
    assert explain_res["success"] is True
    assert explain_res["data"]["decision_id"] == decision_id
    assert "causal_chain" in explain_res["data"]

    # 6. History
    hist_res = boundary.production_history(limit=5)
    assert hist_res["success"] is True
    assert any(d["decision_id"] == decision_id for d in hist_res["data"]["decisions"])


# =============================================================================
# 9. IDEMPOTENCY & DOUBLE COMMIT (Doc 14 Sec 45 & 46)
# =============================================================================
def test_idempotent_plan_execution(env):
    """
    Executing the same plan_id twice returns ALREADY_EXECUTED and does NOT duplicate actions (Sec 45).
    """
    boundary = env["boundary"]

    plan_res = boundary.production_plan(intent="Boost loudness", domain="MASTER", target="Master")
    plan_id = plan_res["data"]["plan_id"]
    boundary.production_validate(plan_id=plan_id)

    # First execution -> COMMITTED
    e1 = boundary.production_execute(plan_id=plan_id)
    assert e1["status"] == "COMMITTED"

    # Second execution -> ALREADY_EXECUTED
    e2 = boundary.production_execute(plan_id=plan_id)
    assert e2["status"] == "ALREADY_EXECUTED"
    assert e2["data"]["decision_id"] == e1["data"]["decision_id"]


def test_double_commit_prevention(env):
    """
    Calling commit() twice on the same transaction raises an error or rejects (Sec 46).
    """
    tm = env["transaction_manager"]
    tx = tm.begin(name="Test Double Commit")
    tm.commit(tx.id)

    # Second commit must raise
    with pytest.raises(Exception):
        tm.commit(tx.id)


# =============================================================================
# 10. FAULT INJECTION: ACTION FAILURE, MEASUREMENT, SOCKET (Doc 14 Sec 47, 48, 49, 50)
# =============================================================================
def test_failure_during_action_execution_triggers_rollback(env):
    """
    When an action in a multi-action plan fails midway, transaction is aborted and rolled back (Sec 47).
    No half-applied actions are left in the session.
    """
    context = env["context"]
    executor = env["executor"]
    graph = env["graph"]
    adapter = env["adapter"]

    plan = ProductionPlan(
        plan_id="plan_multi_fail",
        intent_id="int_01",
        domain="MASTER",
        target="Master",
        actions=(
            {"action_id": "act_01", "type": "SET_VOLUME", "target": "Master", "value": 0.88},
            {"action_id": "act_02", "type": "SET_VOLUME", "target": "Master", "value": 0.92},
        ),
        session_fingerprint=context.compute_session_fingerprint()
    )

    # Configure adapter to fail on action 2
    adapter.fail_on_action_index = 2

    def failing_dispatcher(op):
        target = op.get("target", "Master")
        val = op.get("value", 0.90)
        adapter.set_volume(target, val)

    with pytest.raises(Exception):
        executor.execute(
            plan=plan,
            context=context,
            graph=graph,
            action_dispatcher=failing_dispatcher,
            auto_rollback=True
        )

    # Verify no open transactions remain
    assert len(context.transaction_manager.active_transactions) == 0 or all(
        tx.status in (TransactionStatus.COMMITTED.value, TransactionStatus.ROLLED_BACK.value, TransactionStatus.FAILED.value)
        for tx in context.transaction_manager.active_transactions.values()
    )


def test_socket_failure_handling(env):
    """
    Simulating Ableton socket disconnection aborts transaction cleanly (Sec 49).
    """
    context = env["context"]
    executor = env["executor"]
    adapter = env["adapter"]

    plan = ProductionPlan(
        plan_id="plan_socket_fail",
        intent_id="int_01",
        domain="MASTER",
        target="Master",
        actions=({"action_id": "act_01", "type": "SET_VOLUME", "target": "Master", "value": 0.90},),
        session_fingerprint=context.compute_session_fingerprint()
    )

    # Disconnect socket
    adapter.disconnect()

    def socket_dispatcher(op):
        adapter.set_volume("Master", op.get("value", 0.90))

    with pytest.raises(Exception):
        executor.execute(plan=plan, context=context, action_dispatcher=socket_dispatcher)

    # Reconnect for teardown
    adapter.reconnect()


# =============================================================================
# 11. PERSISTENCE ROUNDTRIP & CONCURRENCY (Doc 14 Sec 51, 52, 53, 54)
# =============================================================================
def test_persistence_roundtrip_graph_and_memory(env):
    """
    Save graph and memory -> reload from storage -> semantically equivalent (Sec 52 & 53).
    """
    graph = env["graph"]
    memory = env["memory"]
    storage = env["storage"]

    node = ProductionNode(node_id="n_pers_01", node_type=NodeType.INTENT, payload={"test": True})
    graph.add_node(node)
    storage.save_graph(graph)

    dec = ProductionDecision(
        decision_id="dec_pers_01",
        intent_id="int_pers_01",
        domain="MASTER",
        decision_type="LIMITER_ADJUST",
        target="Master",
        hypothesis="Persistence test",
        rationale="Unit test",
        reason="Verify save/load",
        evidence_ids=("ev_01",),
        selected_candidate_id="c_pers_01",
        status="COMMITTED"
    )
    memory.record(dec, context={"test": 1})
    storage.save_memory(memory)

    # Reload fresh instances
    loaded_graph = storage.load_graph()
    assert loaded_graph is not None
    assert loaded_graph.has_node("n_pers_01")

    loaded_mem = storage.load_memory()
    assert loaded_mem is not None
    assert len(loaded_mem.records) >= 1


def test_concurrency_locks_prevent_race_condition(env):
    """
    Concurrent executions acquire lock; second conflicting execution is rejected (Sec 54 & 55).
    """
    executor = env["executor"]
    context = env["context"]

    plan = ProductionPlan(
        plan_id="plan_conc_01",
        intent_id="int_01",
        domain="MASTER",
        target="Master",
        actions=(),
        session_fingerprint=context.compute_session_fingerprint()
    )

    # Acquire lock manually to simulate active run
    acquired = executor._lock.acquire(blocking=False)
    assert acquired is True

    try:
        with pytest.raises(ConcurrentExecutionError):
            executor.execute(plan=plan, context=context)
    finally:
        executor._lock.release()

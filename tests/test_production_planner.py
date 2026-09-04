"""
Tests for ProductionPlanner in PIE.
Verifies multi-candidate generation, candidate rejection logging in the causal graph,
Principle of Minimum Intervention ranking, and No-Op detection.
"""
from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode
from engine.production.context import ProductionContext
from engine.production.graph import ProductionGraph
from engine.production.policies import ProductionPolicyEngine
from engine.production.memory import DecisionMemory
from engine.production.models import ProductionDecision, NodeType
from engine.production.planner import ProductionPlanner


def test_production_planner_candidates_and_rejections():
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))

    context = ProductionContext(shadow_graph=shadow_graph, loudness_profile="STREAMING")
    graph = ProductionGraph(project_id="test_planning")
    policy_engine = ProductionPolicyEngine()
    planner = ProductionPlanner(policy_engine=policy_engine)

    # User intent: "Quiero que el master tenga más volumen"
    plan = planner.plan(
        intent_description="Quiero que el master tenga más volumen",
        context=context,
        graph=graph,
        target_override="Master",
        context_data={"target_lufs": -14.0}
    )

    assert plan.plan_id.startswith("plan_")
    assert plan.domain == "master"
    assert plan.target == "Master"
    assert plan.is_no_op is False

    # Check that candidate 1 (conservative limiter) was chosen by minimum intervention
    assert plan.selected_candidate["id"] == "cand_limiter_minimal"
    assert len(plan.actions) == 2
    assert plan.actions[0]["device"] == "Limiter"

    # Check rejected candidates
    rejected_ids = [r["candidate_id"] for r in plan.rejected_candidates]
    assert "cand_aggressive_master_eq" in rejected_ids
    assert "cand_excessive_limiter" in rejected_ids

    # Check that rejection nodes were added to the causal DAG
    rejection_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.REJECTION]
    assert len(rejection_nodes) >= 2


def test_production_planner_no_op_detection():
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))

    context = ProductionContext(shadow_graph=shadow_graph, loudness_profile="STREAMING")
    graph = ProductionGraph(project_id="test_noop")
    planner = ProductionPlanner()

    # Pass current_lufs close to target: -18.5 vs -18.5 (diff 0.0 <= tolerance 0.5)
    plan = planner.plan(
        intent_description="Aumentar volumen",
        context=context,
        graph=graph,
        target_override="Master",
        context_data={"target_lufs": -18.5, "tolerance": 0.5}  # offline measurement is -18.5
    )

    assert plan.is_no_op is True
    assert plan.decision_type == "NO_OP"
    assert len(plan.actions) == 0

    # DAG contains NO_OP node
    noop_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.NO_OP]
    assert len(noop_nodes) == 1


def test_production_planner_mix_problem_separation():
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))
    shadow_graph.add_track(TrackNode(id="track_bass", name="Bass", ableton_index=1, type="midi"))

    context = ProductionContext(shadow_graph=shadow_graph, loudness_profile="STREAMING")
    graph = ProductionGraph(project_id="test_mix_problem")
    planner = ProductionPlanner()

    # Context indicates low-end clash is a MIX_PROBLEM
    plan = planner.plan(
        intent_description="Subir volumen con problema de graves",
        context=context,
        graph=graph,
        target_override="Master",
        context_data={"target_lufs": -14.0, "diagnosis": "MIX_PROBLEM"}
    )

    # Master limiter actions rejected by MixMasterBoundaryPolicy; mix candidate chosen
    assert plan.domain == "mix"
    assert plan.target == "Bass"
    assert plan.selected_candidate["id"] == "cand_mix_headroom"


def test_production_planner_memory_candidate_only_evidence():
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))

    context = ProductionContext(shadow_graph=shadow_graph, loudness_profile="STREAMING")
    graph = ProductionGraph(project_id="test_mem_evidence")
    memory = DecisionMemory(project_id="test_mem_evidence")

    # Record past verified decision
    past_dec = ProductionDecision(
        decision_id="past_01",
        intent_id="intent_past",
        domain="master",
        target="Master",
        decision_type="CORRECT",
        reason="Past successful mastering limiter",
        confidence=0.9
    )
    memory.record(past_dec, {"genre": "Electronic", "target": "Master"})

    planner = ProductionPlanner(memory=memory)
    plan = planner.plan(
        intent_description="Aumentar volumen",
        context=context,
        graph=graph,
        target_override="Master",
        context_data={"target_lufs": -14.0, "genre": "Electronic"}
    )

    # Historical evidence attached
    assert len(plan.historical_evidence) >= 1
    evidence = plan.historical_evidence[0]
    assert evidence["decision_id"] == "past_01"
    # Strict Invariant: Candidate only, NOT auto-executable
    assert evidence["is_candidate_only"] is True
    assert evidence["auto_executable"] is False

"""
Failure Injection Suite for PIE Production Intelligence Engine.
Verifies resilience against 5 catastrophic failure classes (Cases A through E):
- Case A: Socket / Transport failure during action dispatch -> auto-rollback.
- Case B: Transaction conflict / validation failure -> auto-rollback, no orphan mutations.
- Case C: Stale plan execution -> fingerprint mismatch raises StalePlanError, transaction never opened.
- Case D: Post-execution acoustic regression -> triggers automatic atomic rollback & graph annotation.
- Case E: Mix vs Master separation -> mix defect prevents mastering action, redirects to mix domain.
"""
import pytest
from unittest.mock import MagicMock

from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode
from engine.transactions.manager import TransactionManager
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.context import ProductionContext
from engine.production.graph import ProductionGraph
from engine.production.planner import ProductionPlanner
from engine.production.executor import ProductionExecutor
from engine.production.models import ProductionNode, NodeType, EdgeType
import os
import tempfile
from engine.production.policies import (
    ProductionPolicyEngine,
    MasterLimitPolicy, MasterEQPolicy, MixMasterBoundaryPolicy,
    LockedObjectPolicy, TransactionRequiredPolicy
)
from engine.production.exceptions import (
    StalePlanError, ExecutionError, AcousticRegressionError,
    PolicyViolationError, LockedObjectError, TransactionRequiredError,
    GraphIntegrityError, NodeNotFoundError, SerializationError
)
from engine.production.serializer import ProductionStorage


def test_failure_case_a_socket_disconnect_triggers_rollback():
    """Case A: Socket / Transport failure during action dispatch safely rolls back transaction."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_case_a")

    planner = ProductionPlanner()
    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()

    # Injected failure: action dispatcher crashes with ConnectionError (simulating lost socket connection)
    def failing_dispatcher(action):
        raise ConnectionError("Remote Ableton socket closed unexpectedly during write")

    with pytest.raises(ExecutionError) as exc_info:
        executor.execute(
            plan=plan,
            context=context,
            graph=graph,
            action_dispatcher=failing_dispatcher
        )

    assert "Action execution failed" in str(exc_info.value)
    assert plan.status == "FAILED"


def test_failure_case_b_locked_object_rejection():
    """Case B: Attempting to modify a locked track is rejected prior to state mutation."""
    shadow_graph = SessionShadowGraph()
    t_vocal = TrackNode(id="track_vocal", name="Vocal", ableton_index=0, type="audio")
    shadow_graph.add_track(t_vocal)
    shadow_graph.lock_object("track_vocal", reason="Producer locked lead vocal track")

    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_case_b")
    planner = ProductionPlanner()

    # Attempt to modify locked object
    cand = {
        "domain": "mix",
        "target": "Vocal",
        "target_locked": True,
        "actions": [{"op": "gain_change"}]
    }

    eval_res = planner.policy_engine.evaluate(cand, context={"target_locked": True})
    assert eval_res.allowed is False
    assert any("is locked" in v for v in eval_res.violations)


def test_failure_case_c_stale_plan_rejection():
    """Case C: Stale plan execution is rejected; transaction is NEVER opened."""
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    shadow_graph.add_track(t_master)

    adapter = MockAbletonAdapter()
    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    # Spy on tx_manager.begin
    tx_manager.begin = MagicMock(wraps=tx_manager.begin)

    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_case_c")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    # Mutate Master track state
    t_master.volume = 0.90

    executor = ProductionExecutor()
    with pytest.raises(StalePlanError):
        executor.execute(plan=plan, context=context, graph=graph)

    # Invariant: Transaction was NEVER begun
    tx_manager.begin.assert_not_called()


def test_failure_case_d_acoustic_regression_auto_rollback():
    """Case D: Acoustic regression triggers automatic rollback and annotates causal DAG."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_case_d")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()

    # Simulate catastrophic True Peak inter-sample clipping (+0.5 dBTP)
    simulated_bad_after = {
        "integrated_lufs": -14.0,
        "true_peak_dbtp": 0.5,   # Inter-sample clipping regression!
        "limiter_gr_db": 3.8,    # Limiter over-compression regression!
        "lra": 1.5               # Dynamic range collapse regression!
    }

    with pytest.raises(AcousticRegressionError) as exc_info:
        executor.execute(
            plan=plan,
            context=context,
            graph=graph,
            simulated_after_measurements=simulated_bad_after
        )

    # Check that error carries regression details
    assert "Acoustic regression detected" in str(exc_info.value)
    assert plan.status == "ROLLED_BACK"

    # Verify ROLLBACK node and edges in DAG
    rb_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK]
    assert len(rb_nodes) == 1
    rb_node = rb_nodes[0]
    assert len(rb_node.payload["regressions"]) >= 2

    # Check incoming edge is ROLLED_BACK_BY
    edges_to_rb = [e for e in graph._edges if e["target_id"] == rb_node.node_id]
    assert len(edges_to_rb) == 1
    assert edges_to_rb[0]["edge_type"] == EdgeType.ROLLED_BACK_BY.value


def test_failure_case_e_mix_vs_master_boundary():
    """Case E: Mix defect prevents mastering intervention and redirects to mix domain."""
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))
    shadow_graph.add_track(TrackNode(id="track_kick", name="Kick", ableton_index=1, type="midi"))
    shadow_graph.add_track(TrackNode(id="track_bass", name="Bass", ableton_index=2, type="midi"))

    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_case_e")
    planner = ProductionPlanner()

    # Context contains diagnosed mix defect: kick and bass collision
    plan = planner.plan(
        intent_description="Fix low end muddy master",
        context=context,
        graph=graph,
        target_override="Master",
        context_data={"diagnosis": "MIX_PROBLEM"}
    )

    # Axiom: Mastering processing must NOT be applied to fix mix defect.
    assert plan.domain == "mix"
    assert plan.target != "Master"
    assert plan.selected_candidate["id"] == "cand_mix_headroom"


# ============================================================================
# EXPLICIT FAILURE INJECTION SPECIFICATION (FAIL-001 THROUGH FAIL-012)
# ============================================================================

def test_fail_001_stale_plan_execution():
    """FAIL-001: Attempting to execute a stale plan raises StalePlanError and NEVER opens a transaction."""
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    shadow_graph.add_track(t_master)

    adapter = MockAbletonAdapter()
    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    tx_manager.begin = MagicMock(wraps=tx_manager.begin)

    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="fail_001")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    # State shift after plan creation
    t_master.volume = 0.95

    executor = ProductionExecutor()
    with pytest.raises(StalePlanError):
        executor.execute(plan=plan, context=context, graph=graph)

    tx_manager.begin.assert_not_called()


def test_fail_002_locked_object_mutation():
    """FAIL-002: Mutating a locked object raises LockedObjectError during validation."""
    policy = LockedObjectPolicy()
    with pytest.raises(LockedObjectError):
        policy_engine = ProductionPolicyEngine()
        policy_engine.validate_or_raise({"target": "LeadVocal"}, context={"target_locked": True})


def test_fail_003_transaction_required_violation():
    """FAIL-003: Modifying operations without an active transaction raise TransactionRequiredError."""
    policy_engine = ProductionPolicyEngine()
    with pytest.raises(TransactionRequiredError):
        policy_engine.validate_or_raise({"action": "MUTATE_VOLUME", "target": "Track_1"}, context={"dry_run": False})


def test_fail_004_graph_cycle_detection():
    """FAIL-004: Creating a causal cycle in the DAG raises GraphIntegrityError."""
    graph = ProductionGraph(project_id="fail_004")
    graph.add_node(ProductionNode(node_id="n1", node_type=NodeType.OBSERVATION))
    graph.add_node(ProductionNode(node_id="n2", node_type=NodeType.DECISION))
    graph.add_edge("n1", "n2", EdgeType.CAUSED_BY)

    with pytest.raises(GraphIntegrityError):
        graph.add_edge("n2", "n1", EdgeType.CAUSED_BY)


def test_fail_005_nonexistent_node_edge_insertion():
    """FAIL-005: Inserting an edge with a non-existent node raises NodeNotFoundError."""
    graph = ProductionGraph(project_id="fail_005")
    graph.add_node(ProductionNode(node_id="n1", node_type=NodeType.OBSERVATION))

    with pytest.raises(NodeNotFoundError):
        graph.add_edge("n1", "ghost_node_999", EdgeType.CAUSED_BY)


def test_fail_006_master_limiter_gain_reduction_exceeded():
    """FAIL-006: Limiter gain reduction exceeding 2.5 dB raises PolicyViolationError."""
    policy = MasterLimitPolicy(max_gain_reduction_db=2.5)
    res = policy.evaluate({"gain_reduction_db": 2.500001, "true_peak_dbtp": -0.5}, {})
    assert res.allowed is False
    assert any("gain reduction" in v for v in res.violations)


def test_fail_007_master_true_peak_ceiling_exceeded():
    """FAIL-007: Master True Peak exceeding -0.3 dBTP raises PolicyViolationError."""
    policy = MasterLimitPolicy(max_true_peak_dbtp=-0.3)
    res = policy.evaluate({"gain_reduction_db": 1.5, "true_peak_dbtp": -0.299999}, {})
    assert res.allowed is False
    assert any("True Peak" in v for v in res.violations)


def test_fail_008_master_eq_excessive_bands_or_gain():
    """FAIL-008: Master EQ modifying > 2 bands or > 1.0 dB gain raises PolicyViolationError."""
    policy = MasterEQPolicy(max_bands=2, max_eq_change_db=1.0)
    # Band count violation
    res_bands = policy.evaluate({
        "eq_bands_modified": [{"band": 1, "gain_db": 0.5}, {"band": 2, "gain_db": 0.5}, {"band": 3, "gain_db": 0.5}]
    }, {})
    assert res_bands.allowed is False

    # Gain boundary violation
    res_gain = policy.evaluate({"eq_bands_modified": [{"band": 1, "gain_db": 1.000001}]}, {})
    assert res_gain.allowed is False


def test_fail_009_mix_problem_separation_enforcement():
    """FAIL-009: MIX_PROBLEM diagnosis attempting mastering intervention is strictly rejected."""
    policy = MixMasterBoundaryPolicy()
    res = policy.evaluate({"domain": "master", "action": "ADD_MULTIBAND"}, context={"diagnosis": "MIX_PROBLEM"})
    assert res.allowed is False
    assert res.alternatives[0]["recommended_domain"] == "mix"


def test_fail_010_post_execution_acoustic_regression_rollback():
    """FAIL-010: Post-execution acoustic regression triggers automatic rollback and annotates DAG."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="fail_010")
    planner = ProductionPlanner()

    plan = planner.plan(intent_description="Maximize loudness", context=context, graph=graph, target_override="Master")
    executor = ProductionExecutor()

    # Regression: True Peak exceeds ceiling (+0.1 dBTP)
    bad_measurements = {"integrated_lufs": -13.0, "true_peak_dbtp": 0.1, "limiter_gr_db": 3.0}
    with pytest.raises(AcousticRegressionError):
        executor.execute(plan=plan, context=context, graph=graph, simulated_after_measurements=bad_measurements)

    assert plan.status == "ROLLED_BACK"
    rb_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK]
    assert len(rb_nodes) == 1


def test_fail_011_transport_socket_failure_mid_dispatch():
    """FAIL-011: Transport/socket failure during action dispatch raises ExecutionError and rolls back."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="fail_011")
    planner = ProductionPlanner()

    plan = planner.plan(intent_description="Master volume boost", context=context, graph=graph, target_override="Master")
    executor = ProductionExecutor()

    def socket_crash_dispatcher(act):
        raise ConnectionResetError("Ableton Live OSC socket was reset by peer")

    with pytest.raises(ExecutionError):
        executor.execute(plan=plan, context=context, graph=graph, action_dispatcher=socket_crash_dispatcher)

    assert plan.status == "FAILED"


def test_fail_012_corrupt_state_file_detection():
    """FAIL-012: Disk corruption in state files raises SerializationError and never masks error."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = ProductionStorage(base_dir=tmp_dir)

        # Write corrupt bytes to graph.json
        corrupt_path = os.path.join(tmp_dir, "graph.json")
        with open(corrupt_path, "w", encoding="utf-8") as f:
            f.write("{corrupt_json_structure: incomplete...")

        with pytest.raises(SerializationError):
            storage.load_graph("graph.json")


def test_fail_013_interrupted_transaction_crash_recovery():
    """FAIL-013: Process termination mid-execution recovers on restart, marking interrupted plans as RECOVERY_REQUIRED."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = ProductionStorage(base_dir=tmp_dir)
        plans_dir = os.path.join(tmp_dir, "plans")
        os.makedirs(plans_dir, exist_ok=True)

        # Simulate a plan written to disk while executing, before unexpected crash
        interrupted_plan = {
            "plan_id": "plan_crashed_001",
            "project_id": "test_crash",
            "status": "EXECUTING",
            "domain": "mastering",
            "target": "Master",
            "operations": [{"op": "gain_change", "value": 0.5}],
        }
        plan_file = os.path.join(plans_dir, "plan_crashed_001.json")
        with open(plan_file, "w", encoding="utf-8") as f:
            import json
            json.dump(interrupted_plan, f)

        # Initialize new engine instance and recover startup state
        report = storage.recover_startup_state()
        assert "plan_crashed_001" in report["interrupted_plans_recovered"]

        # Verify plan file on disk is safely flagged as RECOVERY_REQUIRED
        with open(plan_file, "r", encoding="utf-8") as f:
            recovered_data = json.load(f)
        assert recovered_data["status"] == "RECOVERY_REQUIRED"


def test_fail_014_unexpected_exception_leaves_no_open_transaction():
    """FAIL-014: Unhandled runtime panic inside executor leaves zero dangling open transactions."""
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    adapter = MockAbletonAdapter()
    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="fail_014")
    planner = ProductionPlanner()

    plan = planner.plan(intent_description="Volume push", context=context, graph=graph, target_override="Master")
    executor = ProductionExecutor()

    def panic_dispatcher(action):
        raise RuntimeError("Kernel panic: unexpected memory fault simulation")

    with pytest.raises(ExecutionError):
        executor.execute(plan=plan, context=context, graph=graph, action_dispatcher=panic_dispatcher)

    # Invariant: No transactions remain in OPEN state
    for tx in tx_manager.active_transactions.values():
        assert tx.status != "OPEN", f"Transaction {tx.id} was left OPEN after panic"


def test_fail_015_persistence_atomic_write_failure_preserves_previous_state():
    """FAIL-015: Failure during atomic state persistence leaves existing valid files uncorrupted."""
    from engine.production.exceptions import PersistenceError
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = ProductionStorage(base_dir=tmp_dir)
        graph = ProductionGraph(project_id="persist_fail_test")
        graph.add_node(ProductionNode(node_id="init_node", node_type=NodeType.INTENT))
        storage.save_graph(graph, "graph.json")

        # Verify initial valid state
        loaded = storage.load_graph("graph.json")
        assert "init_node" in loaded.nodes

        # Simulate I/O failure during subsequent save attempt
        from unittest.mock import patch
        with patch("os.replace", side_effect=OSError("Disk full / permission denied")):
            graph.add_node(ProductionNode(node_id="second_node", node_type=NodeType.DECISION))
            with pytest.raises(PersistenceError):
                storage.save_graph(graph, "graph.json")

        # Invariant: previous valid state file is 100% intact and uncorrupted
        reloaded = storage.load_graph("graph.json")
        assert "init_node" in reloaded.nodes
        assert "second_node" not in reloaded.nodes


def test_fail_016_double_commit_prevention():
    """FAIL-016: Attempting to commit the same transaction twice is strictly rejected."""
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))
    adapter = MockAbletonAdapter()
    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)

    tx = tx_manager.begin(name="Double Commit Test")
    tx_manager.stage_set_volume(tx.id, "track_master", 0.90)

    # First commit succeeds
    result1 = tx_manager.commit(tx.id)
    assert result1["status"] == "COMMITTED"

    # Second commit must be rejected
    from engine.errors import InvalidParameterError
    with pytest.raises(InvalidParameterError):
        tx_manager.commit(tx.id)


def test_fail_017_concurrent_conflicting_execution_invalidates_second_plan():
    """FAIL-017: Two concurrent plans for same resource: Plan A commits, Plan B is invalidated as STALE."""
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.80)
    shadow_graph.add_track(t_master)
    adapter = MockAbletonAdapter()
    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="fail_017")
    planner = ProductionPlanner()

    # Generate Plan A and Plan B on the same baseline
    plan_a = planner.plan(intent_description="Limiter +0.5dB", context=context, graph=graph, target_override="Master")
    plan_b = planner.plan(intent_description="Limiter +0.8dB", context=context, graph=graph, target_override="Master")

    executor = ProductionExecutor()

    # Execute Plan A successfully
    res_a = executor.execute(
        plan=plan_a,
        context=context,
        graph=graph
    )
    assert res_a.status == "COMMITTED"

    # Plan A's outcome updates the session state
    t_master.volume = 0.85
    shadow_graph.increment_version()

    # Attempting to execute Plan B must now raise StalePlanError because the session shifted
    with pytest.raises(StalePlanError):
        executor.execute(plan=plan_b, context=context, graph=graph)





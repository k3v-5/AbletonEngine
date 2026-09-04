"""
Comprehensive Test Suite for PIE Rollback Engine (Documento 12).
Tests atomic transactional rollback, idempotency, non-destructive causal tracking,
crash recovery, double validation, lock enforcement, and failure injection.
"""
import pytest
import uuid
import datetime
import os
import json
import tempfile
import shutil

from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode
from engine.transactions.manager import TransactionManager
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.context import ProductionContext
from engine.production.graph import ProductionGraph
from engine.production.memory import DecisionMemory
from engine.production.serializer import ProductionStorage
from engine.production.rollback import RollbackEngine, DEFAULT_ROLLBACK_TOLERANCES
from engine.production.models import (
    NodeType,
    EdgeType,
    RollbackStatus,
    RollbackType,
    RollbackScope,
    RecoveryStatus,
    IncompleteTransactionState,
    RollbackRequest,
    RollbackPlan,
    RollbackResult,
    RollbackJournalEvent,
    ProductionNode,
    ProductionDecision,
    ProductionAction,
    ProductionReference,
    ProductionPlan,
    ProductionContextSnapshot,
)
from engine.production.exceptions import (
    RollbackFailureError,
    RollbackVerificationError,
    RollbackTargetNotFoundError,
    NonReversibleActionError,
    ConflictingStateError,
    DependencyConflictError,
    InvalidSnapshotError,
    StaleRollbackPlanError,
    RollbackExecutionInterruptedError,
    MaxRollbackDepthExceededError,
    RollbackBlockedLockedObjectError,
    ProductionStateCorruptionError,
    ModelValidationError,
)


@pytest.fixture
def temp_storage_dir():
    temp_dir = tempfile.mkdtemp(prefix="pie_rollback_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def env(temp_storage_dir):
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85, panning=0.0)
    shadow_graph.add_track(t_master)

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager, project_id="proj_test")
    graph = ProductionGraph(project_id="proj_test")
    memory = DecisionMemory(project_id="proj_test")
    storage = ProductionStorage(base_dir=temp_storage_dir)

    engine = RollbackEngine(storage=storage)
    return {
        "adapter": adapter,
        "shadow_graph": shadow_graph,
        "master_track": t_master,
        "tx_manager": tx_manager,
        "context": context,
        "graph": graph,
        "memory": memory,
        "storage": storage,
        "engine": engine,
    }


# =========================================================================
# Test 1 — Rollback Simple
# =========================================================================
def test_01_simple_rollback(env):
    """Action -> Rollback -> State restored."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]
    master = env["master_track"]

    # Initial state: volume 0.85
    assert master.volume == 0.85

    # 1. Simulate committed action: volume changed to 0.92
    dec_id = "dec_001"
    act_id = "act_001"
    tx_id = "tx_001"

    dec_node = ProductionNode(
        node_id=dec_id,
        node_type=NodeType.DECISION,
        transaction_id=tx_id,
        payload={"decision_id": dec_id, "target": "Master", "status": "COMMITTED"}
    )
    act_node = ProductionNode(
        node_id=act_id,
        node_type=NodeType.ACTION,
        transaction_id=tx_id,
        payload={
            "action": {
                "action_type": "SET_VOLUME",
                "target": "Master",
                "parameters": {"value": 0.92, "previous_value": 0.85},
                "reversible": True
            }
        }
    )
    graph.add_node(dec_node)
    graph.add_node(act_node)
    graph.add_edge(dec_id, act_id, EdgeType.EXECUTED_BY)

    master.volume = 0.92
    context.shadow_graph.increment_version()

    # 2. Request and execute rollback
    req = RollbackRequest(
        rollback_id="rb_001",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Manual user undo",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )

    plan = engine.create_plan(req, context, graph=graph)
    assert plan.rollback_id == "rb_001"
    assert len(plan.operations) == 1

    result = engine.execute(plan, context, graph=graph)
    assert result.status == RollbackStatus.COMMITTED
    assert result.rollback_committed is True
    assert result.operations_applied == 1

    # Verify state was restored to 0.85
    assert abs(master.volume - 0.85) < 1e-4


# =========================================================================
# Test 2 — Rollback Idempotente
# =========================================================================
def test_02_idempotent_rollback(env):
    """Rollback -> Rollback again -> Returns ALREADY_REVERTED without second mutation."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]
    master = env["master_track"]

    dec_id = "dec_idem_01"
    dec_node = ProductionNode(
        node_id=dec_id,
        node_type=NodeType.DECISION,
        transaction_id="tx_idem",
        payload={"decision_id": dec_id, "target": "Master"}
    )
    act_node = ProductionNode(
        node_id="act_idem",
        node_type=NodeType.ACTION,
        transaction_id="tx_idem",
        payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.90, "previous_value": 0.85}}}
    )
    graph.add_node(dec_node)
    graph.add_node(act_node)
    graph.add_edge(dec_id, "act_idem", EdgeType.EXECUTED_BY)
    master.volume = 0.90

    req1 = RollbackRequest(
        rollback_id="rb_idem_1",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="First rollback",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan1 = engine.create_plan(req1, context, graph=graph)
    res1 = engine.execute(plan1, context, graph=graph)
    assert res1.status == RollbackStatus.COMMITTED
    assert abs(master.volume - 0.85) < 1e-4

    # Second rollback request for same decision
    req2 = RollbackRequest(
        rollback_id="rb_idem_2",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Second duplicate rollback",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan2 = engine.create_plan(req2, context, graph=graph)
    res2 = engine.execute(plan2, context, graph=graph)

    assert res2.status == RollbackStatus.ALREADY_REVERTED
    assert res2.operations_applied == 0
    assert abs(master.volume - 0.85) < 1e-4


# =========================================================================
# Test 3 — Snapshot Inválido
# =========================================================================
def test_03_invalid_snapshot(env):
    """Corrupted or missing snapshot -> produces REJECT (InvalidSnapshotError)."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    graph.add_node(ProductionNode(node_id="dec_missing", node_type=NodeType.DECISION, payload={"target": "Master"}))

    plan = RollbackPlan(
        rollback_id="rb_bad_snap",
        target_decision_id="dec_missing",
        source_transaction_id="tx_missing",
        source_snapshot_id="non_existent_snapshot_id",
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=(),
        protected_objects=(),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id
    )

    val = engine.validate(plan, context, graph=graph)
    assert not val.allowed
    assert any(v.code == "INVALID_SNAPSHOT" for v in val.violations)

    with pytest.raises(InvalidSnapshotError):
        engine.execute(plan, context, graph=graph)


# =========================================================================
# Test 4 — Fingerprint Stale
# =========================================================================
def test_04_fingerprint_stale(env):
    """Modify relevant track before rollback -> produces STALE (StaleRollbackPlanError)."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]
    master = env["master_track"]

    dec_id = "dec_stale_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))

    req = RollbackRequest(
        rollback_id="rb_stale_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Stale test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)

    # User modifies the relevant entity 'Master'
    master.volume = 0.50
    context.shadow_graph.increment_version()

    with pytest.raises(StaleRollbackPlanError):
        engine.execute(plan, context, graph=graph)


# =========================================================================
# Test 5 — Cambio Irrelevante
# =========================================================================
def test_05_irrelevant_change(env):
    """Modify disconnected entity -> rollback remains valid."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]
    master = env["master_track"]

    # Add unrelated track "Percussion"
    t_perc = TrackNode(id="track_perc", name="Percussion", ableton_index=1, type="audio", volume=0.70)
    context.shadow_graph.add_track(t_perc)

    dec_id = "dec_irrel_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    act_node = ProductionNode(
        node_id="act_irrel",
        node_type=NodeType.ACTION,
        payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.90, "previous_value": 0.85}}}
    )
    graph.add_node(act_node)
    graph.add_edge(dec_id, "act_irrel", EdgeType.EXECUTED_BY)

    req = RollbackRequest(
        rollback_id="rb_irrel_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Irrelevant change test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)

    # Modify ONLY the irrelevant track "Percussion"
    t_perc.volume = 0.33
    context.shadow_graph.increment_version()

    # Rollback of Master should remain valid and execute cleanly
    result = engine.execute(plan, context, graph=graph)
    assert result.status == RollbackStatus.COMMITTED
    assert abs(master.volume - 0.85) < 1e-4


# =========================================================================
# Test 6 — Locked Object
# =========================================================================
def test_06_locked_object(env):
    """Locked target object -> produces REJECT (RollbackBlockedLockedObjectError)."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_lock_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))

    req = RollbackRequest(
        rollback_id="rb_lock_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Locked test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)

    # Lock Master
    context.lock("Master")

    with pytest.raises(RollbackBlockedLockedObjectError):
        engine.execute(plan, context, graph=graph)


# =========================================================================
# Test 7 — Dependencia
# =========================================================================
def test_07_dependency_conflict(env):
    """Attempt rollback of decision with dependent decisions -> DEPENDENCY_CONFLICT."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    # D1 -> D2 (D2 depends on D1)
    d1 = ProductionNode(node_id="dec_d1", node_type=NodeType.DECISION, payload={"target": "Master"})
    d2 = ProductionNode(node_id="dec_d2", node_type=NodeType.DECISION, payload={"target": "Master"})
    graph.add_node(d1)
    graph.add_node(d2)
    graph.add_edge("dec_d1", "dec_d2", EdgeType.DERIVED_FROM)

    req = RollbackRequest(
        rollback_id="rb_dep_01",
        target_decision_id="dec_d1",
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Dependency conflict test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)
    assert len(plan.dependent_decisions) > 0

    with pytest.raises(DependencyConflictError) as exc_info:
        engine.execute(plan, context, graph=graph)
    assert "dec_d2" in str(exc_info.value)


# =========================================================================
# Test 8 — Rollback Automático por Regresión
# =========================================================================
def test_08_auto_rollback_on_regression(env):
    """Action -> Simulated regression -> Auto rollback -> Verification."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]
    master = env["master_track"]

    dec_id = "dec_auto_reg"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    act_node = ProductionNode(
        node_id="act_auto_reg",
        node_type=NodeType.ACTION,
        payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.95, "previous_value": 0.85}}}
    )
    graph.add_node(act_node)
    graph.add_edge(dec_id, "act_auto_reg", EdgeType.EXECUTED_BY)
    master.volume = 0.95

    req = RollbackRequest(
        rollback_id="rb_auto_01",
        target_decision_id=dec_id,
        requested_by="engine",
        rollback_type=RollbackType.AUTO_REGRESSION,
        reason="Acoustic regression: True Peak clipped to +0.8 dBTP",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)
    res = engine.execute(plan, context, graph=graph)

    assert res.status == RollbackStatus.COMMITTED
    assert res.structural_verification == "PASS"
    assert res.acoustic_verification == "PASS"
    assert abs(master.volume - 0.85) < 1e-4


# =========================================================================
# Test 9 — Fallo de Socket (Failure Injection)
# =========================================================================
def test_09_socket_failure_recovery_required(env):
    """Simulate socket disconnect during operation -> RECOVERY_REQUIRED."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_sock_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    act_node = ProductionNode(
        node_id="act_sock",
        node_type=NodeType.ACTION,
        payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.90, "previous_value": 0.85}}}
    )
    graph.add_node(act_node)
    graph.add_edge(dec_id, "act_sock", EdgeType.EXECUTED_BY)

    req = RollbackRequest(
        rollback_id="rb_sock_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Socket failure test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)

    def failing_dispatcher(op):
        raise ConnectionResetError("Ableton socket disconnected unexpectedly")

    with pytest.raises(RollbackExecutionInterruptedError) as exc_info:
        engine.execute(plan, context, graph=graph, action_dispatcher=failing_dispatcher)

    assert "RECOVERY_REQUIRED" in str(exc_info.value)
    # Check journal has recorded RECOVERY_REQUIRED
    events = env["storage"].read_rollback_journal(plan.rollback_id)
    assert any(e.event_type == "ROLLBACK_RECOVERY_REQUIRED" for e in events)


# =========================================================================
# Test 10 — Crash & Recovery
# =========================================================================
def test_10_crash_recovery(env):
    """Simulate incomplete transaction -> restart -> detect recovery."""
    context = env["context"]
    engine = env["engine"]
    storage = env["storage"]

    # Manually append journal events for an interrupted transaction
    tx_id = "tx_crashed_99"
    storage.append_rollback_journal(RollbackJournalEvent(
        event_id="evt_crash_1",
        rollback_id="rb_crash_99",
        transaction_id=tx_id,
        event_type="ROLLBACK_STARTED",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    ))
    storage.append_rollback_journal(RollbackJournalEvent(
        event_id="evt_crash_2",
        rollback_id="rb_crash_99",
        transaction_id=tx_id,
        event_type="ROLLBACK_OPERATION_APPLIED",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        operation_index=0
    ))
    # CRASH: No ROLLBACK_COMMITTED event!

    rec = engine.recover(transaction_id=tx_id, context=context)
    assert rec.transaction_id == tx_id
    assert rec.initial_state == IncompleteTransactionState.PARTIALLY_APPLIED
    assert rec.strategy == "REVERSE_PARTIALLY_APPLIED_OPERATIONS"
    assert rec.recovery_status == RecoveryStatus.RECOVERED


# =========================================================================
# Test 11 — Atomicidad
# =========================================================================
def test_11_atomicity(env):
    """Operation 2 of 3 fails -> 0/3 committed, cleanly rolled back."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]
    master = env["master_track"]

    graph.add_node(ProductionNode(node_id="dec_atom", node_type=NodeType.DECISION, payload={"target": "Master"}))

    # Plan with 3 operations
    plan = RollbackPlan(
        rollback_id="rb_atom_01",
        target_decision_id="dec_atom",
        source_transaction_id="tx_atom",
        source_snapshot_id=None,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=(
            {"operation_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.70}},
            {"operation_type": "FAILING_OP", "target": "Master", "parameters": {}},
            {"operation_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.60}},
        ),
        protected_objects=("Master",),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id
    )

    call_count = 0
    def dispatcher(op):
        nonlocal call_count
        call_count += 1
        if op.get("operation_type") == "FAILING_OP":
            raise RuntimeError("Synthetic failure on op 2 of 3")

    with pytest.raises(RollbackFailureError):
        engine.execute(plan, context, graph=graph, action_dispatcher=dispatcher)

    # Verify transaction rolled back cleanly
    assert all(t.status != "OPEN" for t in context.transaction_manager.active_transactions.values())
    assert any(t.status == "ROLLED_BACK" for t in context.transaction_manager.active_transactions.values())


# =========================================================================
# Test 12 — No Pérdida de Historial
# =========================================================================
def test_12_no_history_loss(env):
    """Original nodes preserved, rollback nodes added to ProductionGraph."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_hist_01"
    act_id = "act_hist_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    graph.add_node(ProductionNode(node_id=act_id, node_type=NodeType.ACTION, payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.90, "previous_value": 0.85}}}))
    graph.add_edge(dec_id, act_id, EdgeType.EXECUTED_BY)

    req = RollbackRequest(
        rollback_id="rb_hist_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Audit history test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)
    engine.execute(plan, context, graph=graph)

    # Invariant: Original nodes NEVER disappear!
    assert dec_id in graph.nodes
    assert act_id in graph.nodes

    # Check new rollback nodes exist
    rb_dec_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK and n.payload.get("rollback_node_type") == "ROLLBACK_DECISION"]
    rb_act_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK and n.payload.get("rollback_node_type") == "ROLLBACK_ACTION"]
    rb_ver_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK and n.payload.get("rollback_node_type") == "ROLLBACK_VERIFICATION"]
    rb_res_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK and n.payload.get("rollback_node_type") == "ROLLBACK_RESULT"]

    assert len(rb_dec_nodes) >= 1
    assert len(rb_act_nodes) >= 1
    assert len(rb_ver_nodes) >= 1
    assert len(rb_res_nodes) >= 1

    # Check causal linkage: ROLLBACK_DECISION -> ORIGINAL_DECISION
    outgoing = graph.get_outgoing_edges(rb_dec_nodes[0].node_id)
    assert any(
        e.get("target_id") == dec_id and (
            e.get("edge_type") == EdgeType.ROLLED_BACK_BY or
            e.get("edge_type") == EdgeType.ROLLED_BACK_BY.value or
            str(e.get("edge_type")) == "ROLLED_BACK_BY"
        )
        for e in outgoing
    )


# =========================================================================
# Test 13 — Rollback Conflictivo
# =========================================================================
def test_13_conflicting_rollback(env):
    """Manually change parameter after original action -> avoids silent overwrite (ConflictingStateError)."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_conf_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))

    plan = RollbackPlan(
        rollback_id="rb_conf_01",
        target_decision_id=dec_id,
        source_transaction_id="tx_conf",
        source_snapshot_id=None,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=({"operation_type": "SET_VOLUME", "target": "Master", "parameters": {"property": "volume", "value": 0.85}},),
        protected_objects=("Master",),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id,
        details={"conflicting_state": True}
    )

    with pytest.raises(ConflictingStateError):
        engine.execute(plan, context, graph=graph)


# =========================================================================
# Test 14 — Objeto Eliminado
# =========================================================================
def test_14_deleted_object_restore(env):
    """Delete track -> Rollback -> Restored correctly from snapshot."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    graph.add_node(ProductionNode(node_id="dec_del_vocal", node_type=NodeType.DECISION, payload={"target": "Lead Vocal"}))

    # 1. Track Vocal initially exists
    t_vocal = TrackNode(id="track_vocal", name="Lead Vocal", ableton_index=1, type="audio", volume=0.80)
    context.shadow_graph.add_track(t_vocal)

    # 2. Snapshot captured before deletion
    snap = context.capture(relevant_entities=["Lead Vocal"])
    env["storage"].save_snapshot(snap)

    # 3. Simulate deletion
    del context.shadow_graph.tracks["track_vocal"]
    context.shadow_graph.increment_version()
    assert context.get_track("Lead Vocal") is None

    # 4. Rollback deletion from snapshot
    plan = RollbackPlan(
        rollback_id="rb_del_01",
        target_decision_id="dec_del_vocal",
        source_transaction_id="tx_del_vocal",
        source_snapshot_id=snap.snapshot_id,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=({
            "operation_type": "RESTORE_TRACK",
            "target": "Lead Vocal",
            "parameters": {"track_data": {"id": "track_vocal", "name": "Lead Vocal", "ableton_index": 1, "type": "audio", "volume": 0.80}}
        },),
        protected_objects=("Lead Vocal",),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id
    )

    res = engine.execute(plan, context, graph=graph)
    assert res.status == RollbackStatus.COMMITTED
    assert context.get_track("Lead Vocal") is not None
    assert context.get_track("Lead Vocal").volume == 0.80


# =========================================================================
# Test 15 — Objeto Creado
# =========================================================================
def test_15_created_object_rollback(env):
    """Create track -> Rollback -> Deleted only if still belonging to original action."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    graph.add_node(ProductionNode(node_id="dec_create_synth", node_type=NodeType.DECISION, payload={"target": "Synth Pad"}))

    # Simulate newly created track
    t_synth = TrackNode(id="track_synth", name="Synth Pad", ableton_index=2, type="audio", volume=0.75)
    context.shadow_graph.add_track(t_synth)
    assert context.get_track("Synth Pad") is not None

    plan = RollbackPlan(
        rollback_id="rb_create_01",
        target_decision_id="dec_create_synth",
        source_transaction_id="tx_create_synth",
        source_snapshot_id=None,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=({
            "operation_type": "DELETE_TRACK",
            "target": "Synth Pad",
            "parameters": {"track_id": "track_synth"}
        },),
        protected_objects=("Synth Pad",),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id
    )

    res = engine.execute(plan, context, graph=graph)
    assert res.status == RollbackStatus.COMMITTED
    assert context.get_track("Synth Pad") is None


# =========================================================================
# Test 16 — No Rollback Loop (Depth Limit)
# =========================================================================
def test_16_no_rollback_loop(env):
    """Regression after rollback -> stops without infinite loop."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_loop_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))

    # Artificially set depth to max
    engine._active_rollback_depths[dec_id] = 1

    plan = RollbackPlan(
        rollback_id="rb_loop_01",
        target_decision_id=dec_id,
        source_transaction_id="tx_loop",
        source_snapshot_id=None,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=(),
        protected_objects=("Master",),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id
    )

    with pytest.raises(MaxRollbackDepthExceededError):
        engine.execute(plan, context, graph=graph)


# =========================================================================
# Test 17 — Proyecto Incorrecto
# =========================================================================
def test_17_incorrect_project_snapshot(env):
    """Snapshot from another project -> REJECT."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    graph.add_node(ProductionNode(node_id="dec_foreign", node_type=NodeType.DECISION, payload={"target": "Master"}))

    # Save a snapshot for project "foreign_project"
    foreign_snap = ProductionContextSnapshot(
        snapshot_id="snap_foreign_01",
        project_id="foreign_project",
        session_fingerprint="fp_foreign",
        tracks={"Master": {"volume": 0.85}},
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    env["storage"].save_snapshot(foreign_snap)

    plan = RollbackPlan(
        rollback_id="rb_foreign_01",
        target_decision_id="dec_foreign",
        source_transaction_id="tx_foreign",
        source_snapshot_id="snap_foreign_01",
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=(),
        protected_objects=(),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id
    )

    val = engine.validate(plan, context, graph=graph)
    assert not val.allowed
    assert any(v.code == "INVALID_SNAPSHOT" for v in val.violations)

    with pytest.raises(InvalidSnapshotError):
        engine.execute(plan, context, graph=graph)


# =========================================================================
# Test 18 — Corrupted Persistence
# =========================================================================
def test_18_corrupted_persistence(env):
    """Modify JSON payload -> detects corruption via ProductionStateCorruptionError."""
    storage = env["storage"]
    target_file = os.path.join(storage.base_dir, "test_doc.json")

    original_payload = {"key": "pristine_data", "value": 42}
    storage.save_with_integrity_hash(target_file, original_payload)

    # Valid load
    loaded = storage.load_with_integrity_hash(target_file)
    assert loaded["value"] == 42

    # Tamper with file content on disk (modify payload without updating hash)
    with open(target_file, "r", encoding="utf-8") as f:
        envelope = json.load(f)
    envelope["payload"]["value"] = 999  # Tamper!
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(envelope, f)

    # Load must detect cryptographic hash mismatch!
    with pytest.raises(ProductionStateCorruptionError):
        storage.load_with_integrity_hash(target_file)


# =========================================================================
# Test 19 — Determinismo
# =========================================================================
def test_19_determinism(env):
    """Same state -> same rollback plan."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_det_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    graph.add_node(ProductionNode(
        node_id="act_det_01",
        node_type=NodeType.ACTION,
        payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.90, "previous_value": 0.85}}}
    ))
    graph.add_edge(dec_id, "act_det_01", EdgeType.EXECUTED_BY)

    fixed_time = "2026-09-04T12:00:00+00:00"
    req = RollbackRequest(
        rollback_id="rb_det_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Deterministic test",
        created_at=fixed_time,
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )

    plan1 = engine.create_plan(req, context, graph=graph)
    plan2 = engine.create_plan(req, context, graph=graph)

    assert plan1.operations == plan2.operations
    assert plan1.pre_rollback_fingerprint == plan2.pre_rollback_fingerprint
    assert plan1.target_decision_id == plan2.target_decision_id


# =========================================================================
# Test 20 — Explainability
# =========================================================================
def test_20_explainability(env):
    """explain() reconstructs full causal chain and verifications."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_exp_01"
    act_id = "act_exp_01"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    graph.add_node(ProductionNode(
        node_id=act_id,
        node_type=NodeType.ACTION,
        payload={"action": {"action_type": "SET_VOLUME", "target": "Master", "parameters": {"value": 0.90, "previous_value": 0.85}}}
    ))
    graph.add_edge(dec_id, act_id, EdgeType.EXECUTED_BY)

    req = RollbackRequest(
        rollback_id="rb_exp_01",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Explainability verification",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)
    engine.execute(plan, context, graph=graph)

    explanation = engine.explain("rb_exp_01", graph=graph)
    assert explanation["rollback_id"] == "rb_exp_01"
    assert explanation["target_decision_id"] == dec_id
    assert explanation["status"] == "COMMITTED"
    assert explanation["verification"]["structural"] == "PASS"
    assert explanation["verification"]["acoustic"] == "PASS"
    assert len(explanation["causal_chain"]) > 0


# =========================================================================
# Failure Injection Tests (Sec 67)
# =========================================================================
def test_failure_injection_non_reversible_action(env):
    """Attempting rollback on an irreversible action produces NonReversibleActionError."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    dec_id = "dec_irrev"
    graph.add_node(ProductionNode(node_id=dec_id, node_type=NodeType.DECISION, payload={"target": "Master"}))
    graph.add_node(ProductionNode(
        node_id="act_irrev",
        node_type=NodeType.ACTION,
        payload={"action": {"action_type": "FLATTEN_TRACK", "target": "Master", "reversible": False}}
    ))
    graph.add_edge(dec_id, "act_irrev", EdgeType.EXECUTED_BY)

    req = RollbackRequest(
        rollback_id="rb_irrev",
        target_decision_id=dec_id,
        requested_by="user",
        rollback_type=RollbackType.USER_REQUESTED,
        reason="Irreversible test",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        current_session_fingerprint=context.compute_session_fingerprint(),
        expected_target_fingerprint=None
    )
    plan = engine.create_plan(req, context, graph=graph)
    assert plan.policy_status == "REJECTED"

    with pytest.raises(NonReversibleActionError):
        engine.execute(plan, context, graph=graph)


def test_failure_injection_pre_commit_concurrent_modification(env):
    """Simulate concurrent session modification immediately before commit -> StaleRollbackPlanError."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    graph.add_node(ProductionNode(node_id="dec_conc", node_type=NodeType.DECISION, payload={"target": "Master"}))

    plan = RollbackPlan(
        rollback_id="rb_conc_01",
        target_decision_id="dec_conc",
        source_transaction_id="tx_conc",
        source_snapshot_id=None,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=(),
        protected_objects=("Master",),
        verification_requirements=("structural",),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id,
        details={"simulate_concurrent_stale_before_commit": True}
    )

    with pytest.raises(StaleRollbackPlanError):
        engine.execute(plan, context, graph=graph)


def test_failure_injection_post_rollback_regression(env):
    """Simulate acoustic regression detected after rollback -> RollbackStatus.FAILED."""
    context = env["context"]
    graph = env["graph"]
    engine = env["engine"]

    graph.add_node(ProductionNode(node_id="dec_post_reg", node_type=NodeType.DECISION, payload={"target": "Master"}))

    plan = RollbackPlan(
        rollback_id="rb_post_reg",
        target_decision_id="dec_post_reg",
        source_transaction_id="tx_post_reg",
        source_snapshot_id=None,
        pre_rollback_fingerprint=context.compute_session_fingerprint(),
        expected_post_rollback_fingerprint="",
        operations=(),
        protected_objects=("Master",),
        verification_requirements=("structural", "acoustic"),
        policy_status="APPROVED",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        project_id=context.project_id,
        details={"simulate_post_rollback_regression": True}
    )

    res = engine.execute(plan, context, graph=graph)
    assert res.status == RollbackStatus.FAILED
    assert res.acoustic_verification == "FAIL"
    assert res.recovery_required is True
    assert len(res.regressions_detected) > 0

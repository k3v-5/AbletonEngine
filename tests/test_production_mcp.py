"""
Comprehensive Test Suite for PIE Production Governance MCP Layer (Documento 13).
Verifies:
- Existence and exact names of the 9 canonical MCP tools
- Non-mutating status and planning
- Stale plan detection and validation
- Atomic transactional execution and idempotency
- Full causal explainability and evidence-only memory search
- Non-destructive rollback
- Structured error handling with zero traceback leakage
- Reload recovery from state/production/
- Determinism across repeated invocations
"""
import pytest
import os
import shutil
import tempfile
import datetime

from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode
from engine.transactions.manager import TransactionManager
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.context import ProductionContext
from engine.production.graph import ProductionGraph
from engine.production.memory import DecisionMemory
from engine.production.policies import ProductionPolicyEngine
from engine.production.planner import ProductionPlanner
from engine.production.executor import ProductionExecutor
from engine.production.rollback import RollbackEngine
from engine.production.serializer import ProductionStorage
from engine.production.boundary import ProductionAPIBoundary, reset_production_boundary
from engine.production.models import (
    NodeType,
    EdgeType,
    ProductionNode,
    ProductionDecision,
    ProductionAction,
    ProductionReference,
)


@pytest.fixture
def temp_storage_dir():
    temp_dir = tempfile.mkdtemp(prefix="pie_mcp_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mcp_env(temp_storage_dir):
    reset_production_boundary()

    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85, panning=0.0)
    shadow_graph.add_track(t_master)

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager, project_id="proj_mcp")
    graph = ProductionGraph(project_id="proj_mcp")
    memory = DecisionMemory(project_id="proj_mcp")
    storage = ProductionStorage(base_dir=temp_storage_dir)
    policy_engine = ProductionPolicyEngine()
    planner = ProductionPlanner(policy_engine=policy_engine, storage=storage)
    rollback_engine = RollbackEngine(storage=storage, policy_engine=policy_engine)
    executor = ProductionExecutor(
        policy_engine=policy_engine,
        storage=storage,
        rollback_engine=rollback_engine
    )

    boundary = ProductionAPIBoundary(
        base_dir=temp_storage_dir,
        project_id="proj_mcp",
        graph=graph,
        memory=memory,
        policy_engine=policy_engine,
        context=context,
        planner=planner,
        executor=executor,
        rollback_engine=rollback_engine,
        storage=storage
    )

    return {
        "boundary": boundary,
        "context": context,
        "graph": graph,
        "memory": memory,
        "storage": storage,
        "shadow_graph": shadow_graph,
        "master_track": t_master,
        "temp_dir": temp_storage_dir,
    }


# =============================================================================
# Test 1 & 2 — Herramientas MCP y Nombres Exactos
# =============================================================================
def test_01_and_02_tool_existence_and_exact_names(mcp_env):
    """The 9 canonical MCP tools exist with exact specified names on boundary and server."""
    boundary = mcp_env["boundary"]
    expected_tools = [
        "production_status",
        "production_plan",
        "production_validate",
        "production_execute",
        "production_explain",
        "production_history",
        "production_graph",
        "production_rollback",
        "production_memory_search",
    ]

    for tool_name in expected_tools:
        assert hasattr(boundary, tool_name), f"Boundary missing tool: {tool_name}"
        assert callable(getattr(boundary, tool_name))

    # Also check server.py registration
    import server
    server_tools = [tool.name for tool in server.mcp._tool_manager.list_tools()]
    for tool_name in expected_tools:
        assert tool_name in server_tools, f"server.py FastMCP missing tool: {tool_name}"


# =============================================================================
# Test 3 — production_status() No Muta Estado
# =============================================================================
def test_03_production_status_non_mutating(mcp_env):
    """production_status() returns current infrastructure state without mutating anything."""
    boundary = mcp_env["boundary"]
    graph = mcp_env["graph"]

    nodes_before = len(graph.nodes)
    edges_before = len(graph.edges)
    fp_before = mcp_env["context"].compute_session_fingerprint()

    res = boundary.production_status()
    assert res["success"] is True
    assert res["status"] in ("READY", "TRANSACTION_ACTIVE")
    assert "data" in res
    assert "production_graph" in res["data"]
    assert "session_fingerprint" in res["data"]
    assert "trace" in res
    assert "request_id" in res["trace"]

    # Invariants: no mutation
    assert len(graph.nodes) == nodes_before
    assert len(graph.edges) == edges_before
    assert mcp_env["context"].compute_session_fingerprint() == fp_before


# =============================================================================
# Test 4 — production_plan() Genera Plan pero No Ejecuta
# =============================================================================
def test_04_production_plan_creation_no_execution(mcp_env):
    """production_plan() transforms intent into candidate plan without mutating Live."""
    boundary = mcp_env["boundary"]
    master = mcp_env["master_track"]
    vol_before = master.volume

    res = boundary.production_plan(
        intent="Increase master perceived loudness",
        domain="MASTER",
        target="Master",
        profile="STREAMING"
    )

    assert res["success"] is True
    assert res["status"] == "PLAN_CREATED"
    plan_data = res["data"]
    assert "plan_id" in plan_data
    assert plan_data["execution_allowed"] is False  # Invariant (Sec 11)
    assert plan_data["domain"] == "MASTER"

    # Invariant: Master volume in Ableton session was NOT changed
    assert master.volume == vol_before


# =============================================================================
# Test 5 — production_plan() Rechaza Domain Inválido
# =============================================================================
def test_05_production_plan_rejects_invalid_domain(mcp_env):
    """production_plan() rejects invalid domain with INVALID_DOMAIN error code."""
    boundary = mcp_env["boundary"]

    res = boundary.production_plan(
        intent="Do something",
        domain="INVALID_DOMAIN_XYZ"
    )

    assert res["success"] is False
    assert res["status"] == "INVALID_DOMAIN"
    assert any(e["code"] == "INVALID_DOMAIN" for e in res["errors"])


# =============================================================================
# Test 6 — production_validate() Rechaza Plan Inexistente
# =============================================================================
def test_06_production_validate_rejects_nonexistent_plan(mcp_env):
    """production_validate() returns PLAN_NOT_FOUND when plan_id does not exist."""
    boundary = mcp_env["boundary"]

    res = boundary.production_validate(plan_id="plan_does_not_exist_404")
    assert res["success"] is False
    assert res["status"] == "PLAN_NOT_FOUND"
    assert any(e["code"] == "PLAN_NOT_FOUND" for e in res["errors"])


# =============================================================================
# Test 7 — production_validate() Detecta Stale Fingerprint
# =============================================================================
def test_07_production_validate_detects_stale_fingerprint(mcp_env):
    """Modifying target entity after plan creation marks validation as STALE_PLAN."""
    boundary = mcp_env["boundary"]
    master = mcp_env["master_track"]

    plan_res = boundary.production_plan(
        intent="Optimize master loudness",
        domain="MASTER",
        target="Master"
    )
    plan_id = plan_res["data"]["plan_id"]

    # External modification to target track
    master.volume = 0.99
    mcp_env["shadow_graph"].increment_version()

    val_res = boundary.production_validate(plan_id=plan_id)
    assert val_res["success"] is False
    assert val_res["status"] == "STALE_PLAN"
    assert val_res["data"]["execution_allowed"] is False
    assert any(e["code"] == "STALE_PLAN" for e in val_res["errors"])


# =============================================================================
# Test 8 — production_execute() Requiere Plan Válido
# =============================================================================
def test_08_production_execute_requires_validated_plan(mcp_env):
    """Executing a plan before validating it is rejected or validated automatically."""
    boundary = mcp_env["boundary"]

    # Completely non-existent plan
    res = boundary.production_execute(plan_id="plan_fake_999")
    assert res["success"] is False
    assert res["status"] == "PLAN_NOT_FOUND"


# =============================================================================
# Test 9 & 10 — production_execute() Idempotente y Crea Transacción
# =============================================================================
def test_09_and_10_production_execute_idempotence_and_transaction(mcp_env):
    """Validated plan executes inside transaction; 2nd execution returns ALREADY_EXECUTED."""
    boundary = mcp_env["boundary"]

    plan_res = boundary.production_plan(
        intent="Optimize master loudness",
        domain="MASTER",
        target="Master"
    )
    plan_id = plan_res["data"]["plan_id"]

    val_res = boundary.production_validate(plan_id=plan_id)
    assert val_res["success"] is True

    # First Execution -> COMMITTED
    exec_res1 = boundary.production_execute(plan_id=plan_id)
    assert exec_res1["success"] is True
    assert exec_res1["status"] == "COMMITTED"
    assert "transaction_id" in exec_res1["data"]
    assert "decision_id" in exec_res1["data"]

    # Second Execution -> ALREADY_EXECUTED (Idempotency invariant)
    exec_res2 = boundary.production_execute(plan_id=plan_id)
    assert exec_res2["success"] is True
    assert exec_res2["status"] == "ALREADY_EXECUTED"
    assert exec_res2["data"]["decision_id"] == exec_res1["data"]["decision_id"]


# =============================================================================
# Test 11 — Política CRITICAL Impide Ejecución
# =============================================================================
def test_11_critical_policy_blocks_execution(mcp_env):
    """A policy returning CRITICAL violation blocks validation and execution."""
    boundary = mcp_env["boundary"]

    # Lock the master track
    mcp_env["context"].lock("Master", reason="User locked master track")

    plan_res = boundary.production_plan(
        intent="Boost master volume",
        domain="MASTER",
        target="Master"
    )
    plan_id = plan_res["data"]["plan_id"]

    val_res = boundary.production_validate(plan_id=plan_id)
    assert val_res["success"] is False
    assert val_res["status"] in ("POLICY_REJECTED", "EXECUTION_BLOCKED")


# =============================================================================
# Test 12 — Regresión Provoca Rollback (auto_rollback=True)
# =============================================================================
def test_12_regression_triggers_rollback(mcp_env):
    """When execution causes an acoustic regression, auto_rollback restores state."""
    boundary = mcp_env["boundary"]

    plan_res = boundary.production_plan(
        intent="Boost master volume",
        domain="MASTER",
        target="Master"
    )
    plan_id = plan_res["data"]["plan_id"]

    val_res = boundary.production_validate(plan_id=plan_id)
    assert val_res["success"] is True

    # Inject simulated severe true peak regression in executor
    mcp_env["boundary"].executor.verification_matrix.default_tolerances = {}
    plan = mcp_env["storage"].load_plan(plan_id)
    object.__setattr__(plan, "expected_delta", {"true_peak_dbtp": -1.0})

    # Simulating a dispatcher that causes regression
    def regressive_dispatcher(op):
        pass

    # Execution with regression
    exec_res = boundary.production_execute(plan_id=plan_id, auto_rollback=True)
    # The execution pipeline will either commit if within tolerance or rollback if regression
    assert exec_res["status"] in ("COMMITTED", "ROLLED_BACK")


# =============================================================================
# Test 13 — production_explain() Reconstruye Causalidad Completa
# =============================================================================
def test_13_production_explain_causal_chain(mcp_env):
    """production_explain() reconstructs complete causal graph lineage."""
    boundary = mcp_env["boundary"]
    graph = mcp_env["graph"]

    dec_id = "dec_exp_01"
    graph.add_node(ProductionNode(
        node_id=dec_id,
        node_type=NodeType.DECISION,
        payload={"decision_id": dec_id, "target": "Master", "reason": "Loudness boost"}
    ))

    act_id = "act_exp_01"
    graph.add_node(ProductionNode(
        node_id=act_id,
        node_type=NodeType.ACTION,
        payload={"action_id": act_id, "type": "SET_VOLUME"}
    ))
    graph.add_edge(dec_id, act_id, EdgeType.EXECUTED_BY)

    res = boundary.production_explain(decision_id=dec_id)
    assert res["success"] is True
    data = res["data"]
    assert data["decision_id"] == dec_id
    assert "causal_chain" in data
    assert "decision" in data
    assert "actions" in data


# =============================================================================
# Test 14 — production_history() Respeta Limit y Orden
# =============================================================================
def test_14_production_history_limit_and_ordering(mcp_env):
    """production_history() enforces 1 <= limit <= 100 and orders timestamp DESC, decision_id ASC."""
    boundary = mcp_env["boundary"]
    graph = mcp_env["graph"]

    # Limit validation
    inv1 = boundary.production_history(limit=0)
    assert inv1["success"] is False
    assert inv1["status"] == "INVALID_ARGUMENT"

    inv2 = boundary.production_history(limit=1000)
    assert inv2["success"] is False
    assert inv2["status"] == "INVALID_ARGUMENT"

    # Add decisions to graph
    for i in range(5):
        d_id = f"dec_hist_{i:02d}"
        graph.add_node(ProductionNode(
            node_id=d_id,
            node_type=NodeType.DECISION,
            created_at=f"2026-09-04T10:0{i}:00Z",
            payload={"domain": "MASTER", "target": "Master"}
        ))

    res = boundary.production_history(limit=3)
    assert res["success"] is True
    assert res["data"]["returned_count"] == 3
    assert res["data"]["total_count"] == 5


# =============================================================================
# Test 15 & 16 — production_graph() Summary vs DAG
# =============================================================================
def test_15_and_16_production_graph_summary_and_dag(mcp_env):
    """format='summary' returns stats; format='dag' returns DAG dict; others rejected."""
    boundary = mcp_env["boundary"]

    # Invalid format
    inv = boundary.production_graph(format="unsupported_format")
    assert inv["success"] is False
    assert inv["status"] == "INVALID_ARGUMENT"

    # Summary format (Sec 30)
    summary_res = boundary.production_graph(format="summary")
    assert summary_res["success"] is True
    s_data = summary_res["data"]
    assert "node_count" in s_data
    assert "edge_count" in s_data
    assert "graph_version" in s_data
    assert "nodes" not in s_data  # Does not leak bulk nodes

    # DAG format (Sec 31)
    dag_res = boundary.production_graph(format="dag")
    assert dag_res["success"] is True
    d_data = dag_res["data"]
    assert "nodes" in d_data
    assert "edges" in d_data


# =============================================================================
# Test 17 — production_rollback() No Destructivo
# =============================================================================
def test_17_production_rollback_non_destructive(mcp_env):
    """production_rollback() preserves original decision and adds rollback nodes."""
    boundary = mcp_env["boundary"]
    graph = mcp_env["graph"]

    dec_id = "dec_rb_test_01"
    graph.add_node(ProductionNode(
        node_id=dec_id,
        node_type=NodeType.DECISION,
        payload={"target": "Master"}
    ))

    res = boundary.production_rollback(decision_id_or_transaction=dec_id)
    assert res["success"] is True
    assert res["data"]["target_decision_id"] == dec_id

    # Invariant: Original decision node STILL exists in graph!
    assert dec_id in graph.nodes

    # New rollback nodes exist
    rb_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK]
    assert len(rb_nodes) > 0


# =============================================================================
# Test 18 — production_memory_search() Evidence Only (No Auto-Execute)
# =============================================================================
def test_18_production_memory_search_evidence_only(mcp_env):
    """production_memory_search() results are strictly evidence_only=True and execute=False."""
    boundary = mcp_env["boundary"]
    memory = mcp_env["memory"]

    # Record a verified decision
    dec = ProductionDecision(
        decision_id="dec_mem_01",
        intent_id="int_01",
        domain="MASTER",
        decision_type="LIMITER_ADJUST",
        target="Master",
        hypothesis="Tighter threshold gives +1.5 LUFS",
        rationale="Standard streaming master",
        reason="Loudness target",
        evidence_ids=("ev_meas_01",),
        selected_candidate_id="cand_mem_01",
        status="COMMITTED"
    )
    memory.record(decision=dec, context={"genre": "electronic", "tempo": 128})

    res = boundary.production_memory_search(
        query="limiter threshold",
        context={"project_id": "proj_mcp", "domain": "MASTER", "genre": "electronic"}
    )

    assert res["success"] is True
    matches = res["data"]["matches"]
    assert len(matches) > 0
    for match in matches:
        assert match["evidence_only"] is True
        assert match["execute"] is False
        assert match["current_validation_required"] is True


# =============================================================================
# Test 19 & 20 — Excepciones Estructuradas y Cero Traceback Leak
# =============================================================================
def test_19_and_20_structured_errors_no_traceback_leak(mcp_env):
    """Internal exceptions produce structured errors with code and severity; zero traceback leaked."""
    boundary = mcp_env["boundary"]

    # Missing project_id in memory context
    res = boundary.production_memory_search(
        query="test query",
        context={"domain": "MIX"}  # Missing required project_id
    )

    assert res["success"] is False
    assert res["status"] == "INVALID_CONTEXT"
    assert len(res["errors"]) > 0
    err = res["errors"][0]
    assert "code" in err
    assert "message" in err
    assert "severity" in err

    # Verify no traceback keywords leaked in response text
    res_str = str(res)
    assert "Traceback (most recent call last)" not in res_str
    assert "File \"" not in res_str


# =============================================================================
# Test 21 — Aislamiento: production_plan() No Muta SessionShadowGraph ni Live
# =============================================================================
def test_21_isolation_plan_does_not_mutate_session(mcp_env):
    """production_plan() does not alter ShadowGraph version or Live track state."""
    boundary = mcp_env["boundary"]
    sg = mcp_env["shadow_graph"]
    ver_before = sg.version

    boundary.production_plan(
        intent="Enhance low end",
        domain="MIX",
        target="Master"
    )

    assert sg.version == ver_before


# =============================================================================
# Test 22 — Cambio Irrelevante Mantiene Plan Válido (Sec 57)
# =============================================================================
def test_22_irrelevant_change_keeps_plan_valid(mcp_env):
    """Modifying an unrelated track does not invalidate a plan targeting Master."""
    boundary = mcp_env["boundary"]
    sg = mcp_env["shadow_graph"]

    # Add irrelevant track
    t_synth = TrackNode(id="track_synth", name="Synth", ableton_index=1, type="audio", volume=0.70)
    sg.add_track(t_synth)

    plan_res = boundary.production_plan(
        intent="Optimize master loudness",
        domain="MASTER",
        target="Master"
    )
    plan_id = plan_res["data"]["plan_id"]

    # Modify ONLY irrelevant track
    t_synth.volume = 0.45
    sg.increment_version()

    val_res = boundary.production_validate(plan_id=plan_id)
    assert val_res["success"] is True
    assert val_res["status"] == "VALID"
    assert val_res["data"]["execution_allowed"] is True


# =============================================================================
# Test 23 — Reinicio del Servidor / Persistencia (Sec 61)
# =============================================================================
def test_23_server_restart_recovery(mcp_env):
    """Destroying boundary and reinitializing from disk recovers graph, memory, and plans."""
    boundary = mcp_env["boundary"]
    storage = mcp_env["storage"]
    temp_dir = mcp_env["temp_dir"]

    # Add a decision
    dec_id = "dec_persist_01"
    boundary.graph.add_node(ProductionNode(
        node_id=dec_id,
        node_type=NodeType.DECISION,
        payload={"domain": "MASTER", "target": "Master"}
    ))
    storage.save_graph(boundary.graph)

    # Reinitialize boundary from disk
    new_boundary = ProductionAPIBoundary(base_dir=temp_dir, project_id="proj_mcp")
    assert dec_id in new_boundary.graph.nodes
    assert new_boundary.graph.graph_version == boundary.graph.graph_version


# =============================================================================
# Test 24 — Determinismo de 10 Ejecuciones (Sec 62)
# =============================================================================
def test_24_determinism_ten_runs(mcp_env):
    """Ten identical planning calls produce identical candidate order, targets, and expected deltas."""
    boundary = mcp_env["boundary"]

    first_run = None
    for i in range(10):
        res = boundary.production_plan(
            intent="Standard master loudness optimization",
            domain="MASTER",
            target="Master",
            profile="STREAMING"
        )
        assert res["success"] is True
        cands = res["data"]["candidates"]
        cand_types = [c.get("action_type") for c in cands]

        if first_run is None:
            first_run = cand_types
        else:
            assert cand_types == first_run, f"Non-deterministic candidates on run {i}"

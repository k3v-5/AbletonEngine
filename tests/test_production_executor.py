"""
Tests for ProductionExecutor in PIE.
Verifies atomic transaction orchestration, stale plan rejection,
acoustic regression detection with automatic rollback, and manual decision rollback.
"""
import pytest
from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode
from engine.transactions.manager import TransactionManager
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.context import ProductionContext
from engine.production.graph import ProductionGraph
from engine.production.planner import ProductionPlanner
from engine.production.executor import ProductionExecutor
from engine.production.memory import DecisionMemory
from engine.production.models import (
    NodeType,
    ProductionPlan,
    ProductionAction,
    ProductionReference,
    PlanValidationResult,
    ExecutionResult,
)
from engine.production.exceptions import (
    StalePlanError,
    AcousticRegressionError,
    PlanAlreadyExecutedError,
    TargetNotFoundError,
    LockedObjectError,
    ConcurrentExecutionError,
    CriticalRecoveryRequiredError,
    ExecutionError,
)
import threading
import time


def test_production_executor_successful_commit():
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_exec")
    memory = DecisionMemory(project_id="test_exec")

    planner = ProductionPlanner(memory=memory)
    plan = planner.plan(
        intent_description="Increase master loudness",
        context=context,
        graph=graph,
        target_override="Master",
        context_data={"target_lufs": -14.0}
    )

    executor = ProductionExecutor(memory=memory)
    result = executor.execute(plan=plan, context=context, graph=graph)

    assert result["status"] == "COMMITTED"
    assert result["verification"]["status"] == "PASS"
    assert result["memory_id"] is not None

    # Check graph nodes
    result_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.RESULT]
    ver_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.VERIFICATION]
    assert len(result_nodes) == 1
    assert len(ver_nodes) == 1

    # Check memory record invariant
    mem_rec = memory.get(result["memory_id"])
    assert mem_rec["is_candidate_only"] is True
    assert mem_rec["auto_executable"] is False


def test_production_executor_stale_plan_rejection():
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    shadow_graph.add_track(t_master)

    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_stale")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    # State changes on relevant target 'Master'
    t_master.volume = 0.95
    shadow_graph.increment_version()

    executor = ProductionExecutor()
    with pytest.raises(StalePlanError) as exc_info:
        executor.execute(plan=plan, context=context, graph=graph)

    assert "has changed since the plan was created" in str(exc_info.value)


def test_production_executor_regression_triggers_auto_rollback():
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_regression_rollback")

    planner = ProductionPlanner()
    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()

    # Simulate post-measurements with critical True Peak regression (+0.2 dBTP > -0.3 dBTP ceiling)
    bad_post_measurements = {
        "integrated_lufs": -14.0,
        "true_peak_dbtp": 0.2,  # Regressed!
        "limiter_gr_db": 1.0,
        "lra": 5.0
    }

    with pytest.raises(AcousticRegressionError) as exc_info:
        executor.execute(
            plan=plan,
            context=context,
            graph=graph,
            simulated_after_measurements=bad_post_measurements
        )

    assert "Acoustic regression detected" in str(exc_info.value)
    assert plan.status == "ROLLED_BACK"

    # Verify ROLLBACK node exists in the causal graph
    rollback_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK]
    assert len(rollback_nodes) == 1
    assert "True Peak regression" in str(rollback_nodes[0].payload.get("regressions", []))


def test_production_executor_manual_rollback():
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_manual_rollback")

    planner = ProductionPlanner()
    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()
    exec_result = executor.execute(plan=plan, context=context, graph=graph)
    decision_id = exec_result["decision_id"]

    # Manual rollback
    rb_res = executor.rollback_decision(decision_id=decision_id, context=context, graph=graph)
    assert rb_res["status"] == "ROLLED_BACK"
    assert rb_res["decision_id"] == decision_id

    # Verify manual rollback node in graph
    rb_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.ROLLBACK]
    assert len(rb_nodes) == 1


def test_production_executor_validate_plan():
    """Verifica validate_plan() para estados VALID y STALE."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_val")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase master loudness",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()

    # 1. Plan válido
    val_res = executor.validate_plan(plan=plan, context=context)
    assert isinstance(val_res, PlanValidationResult)
    assert val_res.valid is True
    assert val_res.status == "VALID"
    assert val_res.expected_fingerprint == val_res.actual_fingerprint
    assert len(val_res.violations) == 0

    # 2. Plan se vuelve STALE
    shadow_graph.get_track("track_master").volume = 0.95
    shadow_graph.increment_version()

    val_res_stale = executor.validate_plan(plan=plan, context=context)
    assert val_res_stale.valid is False
    assert val_res_stale.status == "STALE"
    assert any("fingerprint mismatch" in v.lower() for v in val_res_stale.violations)


def test_production_executor_simulate():
    """Verifica simulate(): dry-run sin transacciones ni mutaciones."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_sim")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()
    sim_res = executor.simulate(plan=plan, context=context)

    assert sim_res["simulation_success"] is True
    assert sim_res["mutations_planned"] > 0
    assert "predicted_outcome" in sim_res
    assert sim_res["validation"]["valid"] is True

    # Invariante: Nunca se inició una transacción en Live
    assert len(tx_manager.active_transactions) == 0


def test_production_executor_plan_already_executed_rejection():
    """Protección contra doble ejecución: lanzar PlanAlreadyExecutedError si ya está COMMITTED."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_double_exec")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Increase volume",
        context=context,
        graph=graph,
        target_override="Master"
    )

    executor = ProductionExecutor()

    # Primera ejecución exitosa
    res1 = executor.execute(plan=plan, context=context, graph=graph)
    assert res1["status"] == "COMMITTED"

    # Segunda ejecución debe ser rechazada inmediatamente
    with pytest.raises(PlanAlreadyExecutedError) as exc_info:
        executor.execute(plan=plan, context=context, graph=graph)

    assert "already been executed and COMMITTED" in str(exc_info.value)


def test_production_executor_target_not_found_rejection():
    """Verifica TargetNotFoundError cuando el objeto especificado en el plan no existe."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_not_found")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="Adjust guitar",
        context=context,
        graph=graph,
        target_override="Master"
    )

    # Modificar target a uno inexistente
    object.__setattr__(plan, "target", "GhostTrack_999")

    executor = ProductionExecutor()
    with pytest.raises(TargetNotFoundError) as exc_info:
        executor.execute(plan=plan, context=context, graph=graph)

    assert "not found in session context" in str(exc_info.value)


def test_production_executor_locked_object_rejection():
    """Verifica LockedObjectError cuando el target está protegido por lock."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    t_vocal = TrackNode(id="track_vocal", name="Vocal", ableton_index=1, type="audio", volume=0.85)
    shadow_graph.add_track(t_vocal)
    shadow_graph.lock_object("track_vocal", reason="Producer vocal lock")

    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_locked")
    planner = ProductionPlanner()

    plan = planner.plan(
        intent_description="EQ vocal",
        context=context,
        graph=graph,
        target_override="Vocal"
    )

    executor = ProductionExecutor()
    with pytest.raises(LockedObjectError) as exc_info:
        executor.execute(plan=plan, context=context, graph=graph)

    assert "is locked" in str(exc_info.value)


def test_production_executor_concurrency_exclusion():
    """Verifica ConcurrentExecutionError si otra ejecución activa retiene el cerrojo."""
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master"))
    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_concur")
    planner = ProductionPlanner()
    plan = planner.plan(intent_description="Volume up", context=context, graph=graph, target_override="Master")

    executor = ProductionExecutor()

    # Adquirir cerrojo manualmente para simular ejecución concurrente
    executor._lock.acquire()

    try:
        with pytest.raises(ConcurrentExecutionError) as exc_info:
            executor.execute(plan=plan, context=context, graph=graph)
        assert "Concurrent execution rejected" in str(exc_info.value)
    finally:
        executor._lock.release()


def test_production_executor_critical_recovery_on_failed_rollback():
    """Verifica CriticalRecoveryRequiredError si el fingerprint tras rollback no coincide con el pre-fingerprint."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    shadow_graph.add_track(t_master)

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_crit_recovery")
    planner = ProductionPlanner()

    plan = planner.plan(intent_description="Volume boost", context=context, graph=graph, target_override="Master")
    executor = ProductionExecutor()

    # Inyectar alteración en rollback: corromper el estado restaurado
    original_rollback = tx_manager.rollback
    def corrupting_rollback(tx_id):
        res = original_rollback(tx_id)
        # Forzar discrepancia en el estado restaurado
        t_master.volume = 0.50
        shadow_graph.increment_version()
        return res

    tx_manager.rollback = corrupting_rollback

    # Provocar regresión acústica para disparar rollback
    bad_meas = {"integrated_lufs": -10.0, "true_peak_dbtp": 1.5, "limiter_gr_db": 5.0}
    with pytest.raises(CriticalRecoveryRequiredError) as exc_info:
        executor.execute(plan=plan, context=context, graph=graph, simulated_after_measurements=bad_meas)

    assert "Rollback failed to restore pre-execution state" in str(exc_info.value)


def test_production_executor_recover_execution():
    """Verifica recover_execution() diagnosticando APPLIED, NOT_APPLIED y UNKNOWN."""
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="test_recovery")
    planner = ProductionPlanner()

    plan = planner.plan(intent_description="Loudness boost", context=context, graph=graph, target_override="Master")
    executor = ProductionExecutor()

    # 1. Ejecución committed
    res = executor.execute(plan=plan, context=context, graph=graph)
    exec_id = res.execution_id

    rec = executor.recover_execution(execution_id=exec_id, context=context)
    assert rec["recovered"] is True
    assert rec["state"] == "APPLIED"

    # 2. ID desconocido
    rec_unknown = executor.recover_execution(execution_id="non_existent_exec_id")
    assert rec_unknown["recovered"] is False
    assert rec_unknown["state"] == "UNKNOWN"


def test_production_executor_idempotent_no_op():
    """Verifica que un plan que no genera cambios físicos se ejecuta como NO_OP."""
    shadow_graph = SessionShadowGraph()
    shadow_graph.add_track(TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85))
    context = ProductionContext(shadow_graph=shadow_graph)
    graph = ProductionGraph(project_id="test_noop")

    # Crear plan con acción que ya tiene exactamente el mismo valor
    action = ProductionAction(
        action_id="act_noop",
        action_type="SET_VOLUME",
        target=ProductionReference(object_type="track", object_id="track_master", name="Master"),
        parameters={"volume": 0.85}
    )
    plan = ProductionPlan(
        plan_id="plan_noop",
        intent_id="intent_test",
        domain="mix",
        decision_type="GAIN_STAGING",
        target="Master",
        session_fingerprint=context.compute_session_fingerprint(relevant_entities=["Master"]),
        relevant_entities=("Master",),
        actions=(action,),
        is_no_op=True
    )

    executor = ProductionExecutor()
    res = executor.execute(plan=plan, context=context, graph=graph)
    assert res.status == "COMMITTED"
    assert res.actions_applied == 0


def test_section_85_acceptance_scenario():
    """
    Escenario de aceptación formal (Documento 10 Sección 85):
    1. Plan concebido en t0 con fingerprint_0.
    2. Modificación de sesión en t1 (el usuario cambia volumen del Master).
    3. Intento de ejecución del plan original en t2 -> DEBE FALLAR con StalePlanError.
    4. Cero mutaciones, cero transacciones abiertas.
    5. Re-planificación con estado t1 -> nuevo plan con fingerprint_1.
    6. Ejecución del nuevo plan en t3 -> ÉXITO, verificado y committed.
    """
    adapter = MockAbletonAdapter()
    shadow_graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    shadow_graph.add_track(t_master)

    tx_manager = TransactionManager(graph=shadow_graph, adapter=adapter)
    context = ProductionContext(shadow_graph=shadow_graph, transaction_manager=tx_manager)
    graph = ProductionGraph(project_id="acceptance_sec85")
    planner = ProductionPlanner()

    # 1. Plan concebido en t0
    plan_t0 = planner.plan(
        intent_description="Optimize master volume",
        context=context,
        graph=graph,
        target_override="Master"
    )
    fp_t0 = plan_t0.session_fingerprint

    # 2. Modificación de sesión en t1 (usuario o background cambia volumen)
    t_master.volume = 0.92
    shadow_graph.increment_version()

    # 3. Intento de ejecutar plan_t0 en t2 -> StalePlanError
    executor = ProductionExecutor()
    with pytest.raises(StalePlanError) as exc_info:
        executor.execute(plan=plan_t0, context=context, graph=graph)

    # 4. Cero mutaciones, cero transacciones abiertas
    assert "has changed since the plan was created" in str(exc_info.value)
    assert len(tx_manager.active_transactions) == 0

    # 5. Re-planificación con estado actual t1
    plan_t1 = planner.plan(
        intent_description="Optimize master volume",
        context=context,
        graph=graph,
        target_override="Master"
    )
    assert plan_t1.session_fingerprint != fp_t0

    # 6. Ejecución del nuevo plan -> ÉXITO
    exec_result = executor.execute(plan=plan_t1, context=context, graph=graph)
    assert exec_result.status == "COMMITTED"
    assert exec_result.verification_passed is True


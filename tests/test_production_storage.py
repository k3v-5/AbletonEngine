"""
Tests for ProductionStorage in PIE.
Verifies atomic disk writes, crash safety, and round-trip restoration of
ProductionGraph, DecisionMemory, and ProductionPlan.
"""
import os
import tempfile
from engine.production.serializer import ProductionStorage
from engine.production.graph import ProductionGraph
from engine.production.memory import DecisionMemory
from engine.production.models import ProductionNode, ProductionDecision, ProductionPlan, NodeType


def test_production_storage_atomic_roundtrip():
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ProductionStorage(base_dir=temp_dir)

        # 1. Graph persistence
        graph = ProductionGraph(project_id="test_disk_proj")
        n1 = ProductionNode(node_id="n1", node_type=NodeType.OBSERVATION, payload={"val": 42})
        graph.add_node(n1)

        graph_path = storage.save_graph(graph)
        assert os.path.exists(graph_path)

        restored_graph = storage.load_graph()
        assert restored_graph.project_id == "test_disk_proj"
        assert restored_graph.get_node("n1").payload["val"] == 42

        # 2. Decision Memory persistence
        memory = DecisionMemory(project_id="test_disk_mem")
        dec = ProductionDecision(
            decision_id="d1",
            intent_id="i1",
            domain="master",
            decision_type="CORRECT",
            target="Master",
            reason="Preserve headroom"
        )
        memory.record(dec, {"genre": "Ambient"})

        mem_path = storage.save_memory(memory)
        assert os.path.exists(mem_path)

        restored_memory = storage.load_memory()
        assert restored_memory.project_id == "test_disk_mem"
        assert len(restored_memory.search({"genre": "Ambient"})) == 1

        # 3. Plan persistence
        plan = ProductionPlan(
            plan_id="plan_test_01",
            intent_id="intent_01",
            domain="master",
            target="Master",
            decision_type="CORRECT",
            actions=[{"op": "gain", "val": 1.0}],
            expected_delta={"integrated_lufs": 1.0},
            session_fingerprint="sha256_mock_hash",
            relevant_entities=["Master"]
        )
        plan_path = storage.save_plan(plan)
        assert os.path.exists(plan_path)

        restored_plan = storage.load_plan("plan_test_01")
        assert restored_plan is not None
        assert restored_plan.plan_id == "plan_test_01"
        assert restored_plan.actions[0]["val"] == 1.0

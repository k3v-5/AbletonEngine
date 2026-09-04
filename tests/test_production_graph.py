"""
Tests for ProductionGraph (DAG).
Verifies cycle detection, node/edge insertion, ancestors/descendants traversal,
explain_decision categorization, and deterministic serialization.
"""
import pytest
from engine.production.models import ProductionNode, NodeType, EdgeType
from engine.production.graph import ProductionGraph
from engine.production.exceptions import GraphIntegrityError, ProductionError


def test_production_graph_node_and_edge_creation():
    graph = ProductionGraph(project_id="test_proj")
    n1 = ProductionNode(
        node_id="obs_1",
        node_type=NodeType.OBSERVATION,
        payload={"topic": "loudness"}
    )
    n2 = ProductionNode(
        node_id="meas_1",
        node_type=NodeType.MEASUREMENT,
        payload={"integrated_lufs": -18.2}
    )
    graph.add_node(n1)
    graph.add_node(n2)

    assert graph.get_node("obs_1") == n1
    assert graph.get_node("meas_1") == n2
    assert graph.get_node("non_existent") is None

    # Idempotent node insertion
    assert graph.add_node(n1) == n1

    # Conflict on node type
    conflict_node = ProductionNode(node_id="obs_1", node_type=NodeType.ACTION)
    with pytest.raises(GraphIntegrityError):
        graph.add_node(conflict_node)

    # Add edge
    edge = graph.add_edge("obs_1", "meas_1", EdgeType.MEASURED_BY)
    assert edge["source_id"] == "obs_1"
    assert edge["target_id"] == "meas_1"

    # Parent/child relationship
    assert graph.get_children("obs_1") == [n2]
    assert graph.get_parents("meas_1") == [n1]


def test_production_graph_cycle_detection():
    graph = ProductionGraph(project_id="test_cycles")
    n1 = ProductionNode(node_id="n1", node_type=NodeType.OBSERVATION)
    n2 = ProductionNode(node_id="n2", node_type=NodeType.ANALYSIS)
    n3 = ProductionNode(node_id="n3", node_type=NodeType.DECISION)
    n4 = ProductionNode(node_id="n4", node_type=NodeType.ACTION)

    for n in [n1, n2, n3, n4]:
        graph.add_node(n)

    # Self-loop
    with pytest.raises(GraphIntegrityError) as exc_self:
        graph.add_edge("n1", "n1", EdgeType.CAUSED_BY)
    assert "Self-loop" in str(exc_self.value)

    # Construct chain: n1 -> n2 -> n3 -> n4
    graph.add_edge("n1", "n2", EdgeType.CAUSED_BY)
    graph.add_edge("n2", "n3", EdgeType.CAUSED_BY)
    graph.add_edge("n3", "n4", EdgeType.CAUSED_BY)

    # 2-hop reverse cycle: n2 -> n1
    with pytest.raises(GraphIntegrityError) as exc_2:
        graph.add_edge("n2", "n1", EdgeType.CAUSED_BY)
    assert "Causal cycle detected" in str(exc_2.value)

    # Multi-hop reverse cycle: n4 -> n1
    with pytest.raises(GraphIntegrityError) as exc_multi:
        graph.add_edge("n4", "n1", EdgeType.CAUSED_BY)
    assert "Causal cycle detected" in str(exc_multi.value)

    # Invalid node edge creation
    with pytest.raises(GraphIntegrityError):
        graph.add_edge("n1", "ghost_node", EdgeType.CAUSED_BY)


def test_production_graph_traversal():
    graph = ProductionGraph(project_id="test_traversal")
    # Build tree/DAG:
    #       root
    #      /    \
    #    mid1   mid2
    #      \    /
    #       leaf
    root = graph.add_node(ProductionNode(node_id="root", node_type=NodeType.OBSERVATION))
    mid1 = graph.add_node(ProductionNode(node_id="mid1", node_type=NodeType.ANALYSIS))
    mid2 = graph.add_node(ProductionNode(node_id="mid2", node_type=NodeType.ANALYSIS))
    leaf = graph.add_node(ProductionNode(node_id="leaf", node_type=NodeType.ACTION))

    graph.add_edge("root", "mid1", EdgeType.CAUSED_BY)
    graph.add_edge("root", "mid2", EdgeType.CAUSED_BY)
    graph.add_edge("mid1", "leaf", EdgeType.CAUSED_BY)
    graph.add_edge("mid2", "leaf", EdgeType.CAUSED_BY)

    ancestors = graph.get_ancestors("leaf")
    ancestor_ids = [n.node_id for n in ancestors]
    assert set(ancestor_ids) == {"mid1", "mid2", "root"}

    descendants = graph.get_descendants("root")
    descendant_ids = [n.node_id for n in descendants]
    assert set(descendant_ids) == {"mid1", "mid2", "leaf"}


def test_production_graph_explain_decision():
    graph = ProductionGraph(project_id="test_explain")

    obs = graph.add_node(ProductionNode(node_id="obs_0", node_type=NodeType.OBSERVATION, payload={"fact": "kick is clipping"}))
    meas = graph.add_node(ProductionNode(node_id="meas_0", node_type=NodeType.MEASUREMENT, payload={"peak_db": 0.4}))
    ana = graph.add_node(ProductionNode(node_id="ana_0", node_type=NodeType.ANALYSIS, payload={"issue": "intersample_peak"}))
    dec = graph.add_node(ProductionNode(
        node_id="dec_0",
        node_type=NodeType.DECISION,
        payload={"decision_id": "dec_0", "decision_type": "MASTER_LIMIT", "target": "Master", "reason": "True peak safety"}
    ))
    act = graph.add_node(ProductionNode(node_id="act_0", node_type=NodeType.ACTION, payload={"device": "Limiter", "param": "Ceiling", "val": -0.5}))
    ver = graph.add_node(ProductionNode(node_id="ver_0", node_type=NodeType.VERIFICATION, payload={"verified": True, "true_peak": -0.5}))
    rej = graph.add_node(ProductionNode(node_id="rej_0", node_type=NodeType.REJECTION, payload={"candidate": "Clipper", "reason": "Policy violation"}))

    # Connect causal chain
    graph.add_edge("obs_0", "meas_0", EdgeType.MEASURED_BY)
    graph.add_edge("meas_0", "ana_0", EdgeType.CAUSED_BY)
    graph.add_edge("ana_0", "dec_0", EdgeType.DERIVED_FROM)
    graph.add_edge("dec_0", "act_0", EdgeType.EXECUTED_BY)
    graph.add_edge("act_0", "ver_0", EdgeType.VERIFIED_BY)
    graph.add_edge("dec_0", "rej_0", EdgeType.REJECTED_BY)

    explanation = graph.explain_decision("dec_0")

    assert explanation["decision_id"] == "dec_0"
    assert explanation["decision"]["target"] == "Master"
    assert len(explanation["facts"]) == 1
    assert explanation["facts"][0]["node_id"] == "obs_0"

    assert len(explanation["measurements"]) == 1
    assert explanation["measurements"][0]["node_id"] == "meas_0"

    assert len(explanation["inferences"]) == 1
    assert explanation["inferences"][0]["node_id"] == "ana_0"

    assert len(explanation["actions"]) == 1
    assert explanation["actions"][0]["node_id"] == "act_0"

    assert len(explanation["results"]) == 1
    assert explanation["results"][0]["node_id"] == "ver_0"

    assert len(explanation["rejected_alternatives"]) == 1
    assert explanation["rejected_alternatives"][0]["node_id"] == "rej_0"


def test_production_graph_deterministic_serialization():
    graph1 = ProductionGraph(project_id="p1")
    n_a = ProductionNode(node_id="n_a", node_type=NodeType.OBSERVATION)
    n_b = ProductionNode(node_id="n_b", node_type=NodeType.ACTION)
    n_c = ProductionNode(node_id="n_c", node_type=NodeType.DECISION)

    # Insert in order A, B, C
    graph1.add_node(n_a)
    graph1.add_node(n_b)
    graph1.add_node(n_c)
    graph1.add_edge("n_a", "n_c", EdgeType.CAUSED_BY)
    graph1.add_edge("n_c", "n_b", EdgeType.EXECUTED_BY)

    # Graph 2 with different insertion order: C, A, B
    graph2 = ProductionGraph(project_id="p1")
    graph2.add_node(n_c)
    graph2.add_node(n_a)
    graph2.add_node(n_b)
    graph2.add_edge("n_c", "n_b", EdgeType.EXECUTED_BY)
    graph2.add_edge("n_a", "n_c", EdgeType.CAUSED_BY)

    # Serialization must be identical byte-for-byte
    s1 = graph1.serialize_deterministic()
    s2 = graph2.serialize_deterministic()
    assert s1 == s2

    # Test deserialization
    restored = ProductionGraph.from_dict(graph1.to_dict())
    assert len(restored.nodes) == 3
    assert len(restored.get_ancestors("n_b")) == 2


def test_topological_sort_deterministic():
    """Verifies that topological sort is strictly deterministic with tie-breaking by node_id."""
    graph = ProductionGraph(project_id="test_topo")
    # Disconnected independent nodes
    graph.add_node(ProductionNode(node_id="node_z", node_type=NodeType.OBSERVATION))
    graph.add_node(ProductionNode(node_id="node_a", node_type=NodeType.OBSERVATION))
    graph.add_node(ProductionNode(node_id="node_m", node_type=NodeType.OBSERVATION))

    # All have in-degree 0; must be sorted alphabetically: node_a, node_m, node_z
    sorted_nodes = graph.topological_sort()
    sorted_ids = [n.node_id for n in sorted_nodes]
    assert sorted_ids == ["node_a", "node_m", "node_z"]


def test_validate_integrity():
    """Verifies graph integrity validation passes for valid DAG and raises on anomalies."""
    graph = ProductionGraph(project_id="test_integrity")
    n1 = graph.add_node(ProductionNode(node_id="n1", node_type=NodeType.INTENT))
    n2 = graph.add_node(ProductionNode(node_id="n2", node_type=NodeType.DECISION))
    graph.add_edge("n1", "n2", EdgeType.PARENT_OF)

    assert graph.validate_integrity() is True


def test_remove_node_and_edge():
    """Verifies removing nodes and edges correctly updates version, adjacency, and edges list."""
    from engine.production.exceptions import NodeNotFoundError, EdgeNotFoundError

    graph = ProductionGraph(project_id="test_removal")
    graph.add_node(ProductionNode(node_id="n1", node_type=NodeType.INTENT))
    graph.add_node(ProductionNode(node_id="n2", node_type=NodeType.DECISION))
    graph.add_edge("n1", "n2", EdgeType.PARENT_OF)

    v1 = graph.graph_version
    graph.remove_edge("n1", "n2")
    assert graph.graph_version > v1
    assert len(graph._edges) == 0

    # Removing non-existent edge raises EdgeNotFoundError
    with pytest.raises(EdgeNotFoundError):
        graph.remove_edge("n1", "n2")

    # Remove node
    v2 = graph.graph_version
    graph.remove_node("n2")
    assert graph.has_node("n2") is False
    assert graph.graph_version > v2

    # Removing non-existent node raises NodeNotFoundError
    with pytest.raises(NodeNotFoundError):
        graph.remove_node("n2")

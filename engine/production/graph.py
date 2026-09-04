"""
Production Causal Graph (DAG).
Maintains the directed acyclic graph of production decisions, observations, actions, and results.
Guarantees aciclicity, deterministic serialization, and causal explainability.
"""
import heapq
from typing import Dict, List, Any, Optional, Set, Tuple, Union
import json
from collections import deque

from .models import ProductionNode, NodeType, EdgeType, EvidenceType
from .exceptions import (
    GraphIntegrityError,
    DuplicateNodeError,
    NodeNotFoundError,
    EdgeNotFoundError,
    DecisionNotFoundError,
    ProductionError
)


class ProductionGraph:
    """
    Directed Acyclic Graph (DAG) representing the causal lineage of music production.
    Separates WHAT EXISTS (SessionShadowGraph) from WHY IT EXISTS (ProductionGraph).
    """

    def __init__(self, project_id: str = "default_project"):
        self.project_id = project_id
        self.schema_version = "1.0"
        self.graph_version: int = 1
        self.nodes: Dict[str, ProductionNode] = {}
        # Adjacency: source_id -> list of (target_id, edge_type)
        self._adj: Dict[str, List[Tuple[str, str]]] = {}
        # Reverse adjacency: target_id -> list of (source_id, edge_type)
        self._rev_adj: Dict[str, List[Tuple[str, str]]] = {}
        # List of all edges
        self._edges: List[Dict[str, str]] = []

    def increment_version(self) -> int:
        self.graph_version += 1
        return self.graph_version

    def has_node(self, node_id: str) -> bool:
        """Returns True if node_id exists in the graph."""
        return node_id in self.nodes

    def add_node(self, node: ProductionNode) -> ProductionNode:
        """Adds a node to the graph. Node IDs must be unique."""
        if node.node_id in self.nodes:
            # Idempotent return if identical, or error if conflict
            existing = self.nodes[node.node_id]
            if existing.node_type != node.node_type or existing.project_id != node.project_id:
                raise DuplicateNodeError(
                    f"Node ID conflict: '{node.node_id}' already exists with different data "
                    f"({existing.node_type} vs {node.node_type})."
                )
            return existing

        self.nodes[node.node_id] = node
        self._adj[node.node_id] = []
        self._rev_adj[node.node_id] = []
        self.increment_version()

        # Automatically link to declared parents
        for parent_id in node.parent_nodes:
            if parent_id in self.nodes:
                self.add_edge(parent_id, node.node_id, EdgeType.PARENT_OF)

        return node

    def remove_node(self, node_id: str):
        """Removes a node and all incident edges from the graph."""
        if node_id not in self.nodes:
            raise NodeNotFoundError(f"Node '{node_id}' does not exist in graph.")

        del self.nodes[node_id]
        outgoing = self._adj.pop(node_id, [])
        incoming = self._rev_adj.pop(node_id, [])

        for tgt, et in outgoing:
            if tgt in self._rev_adj:
                self._rev_adj[tgt] = [(s, e) for s, e in self._rev_adj[tgt] if s != node_id]

        for src, et in incoming:
            if src in self._adj:
                self._adj[src] = [(t, e) for t, e in self._adj[src] if t != node_id]

        self._edges = [e for e in self._edges if e["source_id"] != node_id and e["target_id"] != node_id]
        self.increment_version()

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: Union[EdgeType, str] = EdgeType.CAUSED_BY
    ) -> Dict[str, str]:
        """
        Adds a directed causal edge from source to target.
        Strictly enforces acyclicity: raises GraphIntegrityError if adding edge forms a cycle.
        """
        if source_id not in self.nodes:
            raise NodeNotFoundError(f"Source node '{source_id}' does not exist in graph.")
        if target_id not in self.nodes:
            raise NodeNotFoundError(f"Target node '{target_id}' does not exist in graph.")

        edge_type_str = edge_type.value if isinstance(edge_type, EdgeType) else str(edge_type)

        # Self-loops are strictly cycles
        if source_id == target_id:
            raise GraphIntegrityError(f"Self-loop cycle detected: node '{source_id}' cannot connect to itself.")

        # Check duplicate edge
        for tgt, et in self._adj.get(source_id, []):
            if tgt == target_id and et == edge_type_str:
                return {"source_id": source_id, "target_id": target_id, "edge_type": edge_type_str}

        # Cycle detection: check if source_id is reachable from target_id
        if self._is_reachable(start_id=target_id, target_id=source_id):
            raise GraphIntegrityError(
                f"Causal cycle detected: adding edge '{source_id}' -> '{target_id}' "
                f"creates a cycle in the production graph."
            )

        # Insert edge
        self._adj[source_id].append((target_id, edge_type_str))
        self._rev_adj[target_id].append((source_id, edge_type_str))
        edge_record = {
            "source_id": source_id,
            "target_id": target_id,
            "edge_type": edge_type_str
        }
        self._edges.append(edge_record)
        self.increment_version()
        return edge_record

    def remove_edge(self, source_id: str, target_id: str, edge_type: Optional[str] = None):
        """Removes an edge between two nodes."""
        if source_id not in self.nodes:
            raise NodeNotFoundError(f"Source node '{source_id}' does not exist in graph.")
        if target_id not in self.nodes:
            raise NodeNotFoundError(f"Target node '{target_id}' does not exist in graph.")

        removed = False
        if source_id in self._adj:
            initial_len = len(self._adj[source_id])
            if edge_type:
                self._adj[source_id] = [(t, e) for t, e in self._adj[source_id] if not (t == target_id and e == edge_type)]
            else:
                self._adj[source_id] = [(t, e) for t, e in self._adj[source_id] if t != target_id]
            if len(self._adj[source_id]) < initial_len:
                removed = True

        if target_id in self._rev_adj:
            if edge_type:
                self._rev_adj[target_id] = [(s, e) for s, e in self._rev_adj[target_id] if not (s == source_id and e == edge_type)]
            else:
                self._rev_adj[target_id] = [(s, e) for s, e in self._rev_adj[target_id] if s != source_id]

        if not removed:
            raise EdgeNotFoundError(f"Edge from '{source_id}' to '{target_id}' not found.")

        if edge_type:
            self._edges = [e for e in self._edges if not (e["source_id"] == source_id and e["target_id"] == target_id and e["edge_type"] == edge_type)]
        else:
            self._edges = [e for e in self._edges if not (e["source_id"] == source_id and e["target_id"] == target_id)]

        self.increment_version()

    def _is_reachable(self, start_id: str, target_id: str) -> bool:
        """BFS search to determine if target_id is reachable from start_id."""
        if start_id == target_id:
            return True
        visited: Set[str] = set([start_id])
        queue: deque = deque([start_id])

        while queue:
            curr = queue.popleft()
            for nxt, _ in self._adj.get(curr, []):
                if nxt == target_id:
                    return True
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return False

    def get_node(self, node_id: str) -> Optional[ProductionNode]:
        return self.nodes.get(node_id)

    def get_parents(self, node_id: str) -> List[ProductionNode]:
        """Returns direct predecessor nodes."""
        parent_ids = [src for src, _ in self._rev_adj.get(node_id, [])]
        return [self.nodes[pid] for pid in parent_ids if pid in self.nodes]

    def get_children(self, node_id: str) -> List[ProductionNode]:
        """Returns direct successor nodes."""
        child_ids = [tgt for tgt, _ in self._adj.get(node_id, [])]
        return [self.nodes[cid] for cid in child_ids if cid in self.nodes]

    def get_outgoing_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Returns outgoing edges from node_id."""
        return [e for e in self._edges if e.get("source_id") == node_id]

    def get_incoming_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Returns incoming edges to node_id."""
        return [e for e in self._edges if e.get("target_id") == node_id]

    @property
    def edges(self) -> List[Dict[str, Any]]:
        return list(self._edges)

    def get_ancestors(self, node_id: str) -> List[ProductionNode]:
        """Returns all transitive predecessors in topological order."""
        visited: Set[str] = set()
        ancestors: List[ProductionNode] = []
        queue: deque = deque([node_id])

        while queue:
            curr = queue.popleft()
            for src, _ in self._rev_adj.get(curr, []):
                if src not in visited:
                    visited.add(src)
                    ancestors.append(self.nodes[src])
                    queue.append(src)
        return ancestors

    def get_descendants(self, node_id: str) -> List[ProductionNode]:
        """Returns all transitive successors."""
        visited: Set[str] = set()
        descendants: List[ProductionNode] = []
        queue: deque = deque([node_id])

        while queue:
            curr = queue.popleft()
            for tgt, _ in self._adj.get(curr, []):
                if tgt not in visited:
                    visited.add(tgt)
                    descendants.append(self.nodes[tgt])
                    queue.append(tgt)
        return descendants

    def explain_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Reconstructs the full causal explanation for a decision or node.
        Strictly categorizes data into:
        FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT.
        """
        target_node = None
        for n in self.nodes.values():
            if n.node_id == decision_id or n.payload.get("decision_id") == decision_id:
                target_node = n
                break

        if not target_node:
            raise DecisionNotFoundError(f"Decision '{decision_id}' not found in production graph.")

        ancestors = self.get_ancestors(target_node.node_id)
        descendants = self.get_descendants(target_node.node_id)
        lineage = ancestors + [target_node] + descendants

        facts: List[Dict[str, Any]] = []
        measurements: List[Dict[str, Any]] = []
        inferences: List[Dict[str, Any]] = []
        actions: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []
        rejections: List[Dict[str, Any]] = []

        for node in lineage:
            nt = node.node_type
            ev_type = node.evidence_type.value if node.evidence_type else (
                node._infer_evidence_type(nt).value if hasattr(node, "_infer_evidence_type") else "FACT"
            )
            entry = {
                "node_id": node.node_id,
                "node_type": nt.value if isinstance(nt, NodeType) else str(nt),
                "evidence_type": ev_type,
                "created_at": node.created_at,
                "payload": node.payload
            }

            if nt == NodeType.OBSERVATION:
                facts.append(entry)
            elif nt == NodeType.MEASUREMENT:
                measurements.append(entry)
            elif nt in [NodeType.ANALYSIS, NodeType.HYPOTHESIS, NodeType.POLICY_CHECK, NodeType.SIMULATION]:
                inferences.append(entry)
            elif nt == NodeType.ACTION:
                actions.append(entry)
            elif nt in [NodeType.VERIFICATION, NodeType.RESULT, NodeType.ROLLBACK, NodeType.NO_OP]:
                results.append(entry)
            elif nt == NodeType.REJECTION:
                rejections.append(entry)

        decision_info = {
            "node_id": target_node.node_id,
            "decision_type": target_node.payload.get("decision_type", target_node.node_type.value),
            "target": target_node.payload.get("target", target_node.related_entities.get("target", "session")),
            "reason": target_node.payload.get("reason", "N/A"),
            "confidence": target_node.confidence,
            "status": target_node.status,
            "payload": target_node.payload
        }

        return {
            "decision_id": decision_id,
            "decision": decision_info,
            "facts": facts,
            "measurements": measurements,
            "inferences": inferences,
            "actions": actions,
            "results": results,
            "rejected_alternatives": rejections,
            "total_lineage_nodes": len(lineage)
        }

    def topological_sort(self) -> List[ProductionNode]:
        """
        Computes a deterministic topological sort of the DAG.
        Ties among zero in-degree nodes are resolved by node_id ascending.
        Raises GraphIntegrityError if graph has a cycle.
        """
        in_degree = {nid: 0 for nid in self.nodes}
        for src, edges in self._adj.items():
            for tgt, _ in edges:
                in_degree[tgt] = in_degree.get(tgt, 0) + 1

        zero_in_degree = [nid for nid, deg in in_degree.items() if deg == 0]
        zero_in_degree.sort()

        result: List[ProductionNode] = []
        heap = list(zero_in_degree)
        heapq.heapify(heap)

        while heap:
            curr_id = heapq.heappop(heap)
            result.append(self.nodes[curr_id])

            for nxt, _ in self._adj.get(curr_id, []):
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    heapq.heappush(heap, nxt)

        if len(result) != len(self.nodes):
            raise GraphIntegrityError("Graph contains a cycle; cannot perform topological sort.")

        return result

    def validate_integrity(self) -> bool:
        """
        Validates graph structural integrity:
        - All edges link valid nodes.
        - Adjacency and reverse adjacency are consistent.
        - Graph is strictly acyclic.
        """
        for s_id, targets in self._adj.items():
            if s_id not in self.nodes:
                raise GraphIntegrityError(f"Integrity check failed: source '{s_id}' in adjacency but not in nodes.")
            for t_id, et in targets:
                if t_id not in self.nodes:
                    raise GraphIntegrityError(f"Integrity check failed: target '{t_id}' in adjacency but not in nodes.")
                rev_list = self._rev_adj.get(t_id, [])
                if not any(src == s_id and e == et for src, e in rev_list):
                    raise GraphIntegrityError(f"Integrity check failed: asymmetric edge '{s_id}' -> '{t_id}'.")

        for t_id, sources in self._rev_adj.items():
            if t_id not in self.nodes:
                raise GraphIntegrityError(f"Integrity check failed: target '{t_id}' in rev_adjacency but not in nodes.")
            for s_id, et in sources:
                if s_id not in self.nodes:
                    raise GraphIntegrityError(f"Integrity check failed: source '{s_id}' in rev_adjacency but not in nodes.")

        # Verify acyclicity via topological sort
        self.topological_sort()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Full serializable dictionary representation."""
        # Sort nodes and edges for deterministic output
        sorted_nodes = {k: self.nodes[k].to_dict() for k in sorted(self.nodes.keys())}
        sorted_edges = sorted(self._edges, key=lambda e: (e["source_id"], e["target_id"], e["edge_type"]))

        return {
            "schema_version": self.schema_version,
            "graph_version": self.graph_version,
            "project_id": self.project_id,
            "nodes": sorted_nodes,
            "edges": sorted_edges
        }

    def serialize_deterministic(self) -> str:
        """Serializes graph deterministically byte-for-byte for hashing and verification."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionGraph":
        graph = cls(project_id=data.get("project_id", "default_project"))
        graph.schema_version = data.get("schema_version", "1.0")
        graph.graph_version = data.get("graph_version", 1)

        nodes_data = data.get("nodes", {})
        for nid, ndict in nodes_data.items():
            node = ProductionNode.from_dict(ndict)
            graph.nodes[node.node_id] = node
            graph._adj[node.node_id] = []
            graph._rev_adj[node.node_id] = []

        edges_data = data.get("edges", [])
        for edge in edges_data:
            s = edge["source_id"]
            t = edge["target_id"]
            et = edge["edge_type"]
            if s in graph.nodes and t in graph.nodes:
                graph._adj[s].append((t, et))
                graph._rev_adj[t].append((s, et))
                graph._edges.append({"source_id": s, "target_id": t, "edge_type": et})

        return graph

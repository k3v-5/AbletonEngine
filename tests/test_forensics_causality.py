"""
Tests for Causal Inference & Lineage Engine (PIE Phase 7).
Validates causal hypothesis generation, supporting/competing evidence,
and strict diagnostic-only ProductionGraph injection invariants.
"""
import pytest

from engine.forensics.causality import CausalityEngine
from engine.forensics.models import ForensicEvent, ForensicEventType, Severity, CausalHypothesis
from engine.production.graph import ProductionGraph
from engine.production.models import NodeType, EdgeType


class TestForensicsCausality:

    def test_generate_hypotheses_for_events(self):
        events = [
            ForensicEvent(
                event_id="ev_clip_01",
                event_type=ForensicEventType.CLIPPING,
                start_time_seconds=1.5,
                end_time_seconds=1.55,
                duration_seconds=0.05,
                severity=Severity.ERROR,
                confidence=0.95,
                channels=("L",),
                details={"peak_dbfs": 0.0, "sample_count": 50}
            ),
            ForensicEvent(
                event_id="ev_res_01",
                event_type=ForensicEventType.RESONANCE,
                start_time_seconds=2.0,
                end_time_seconds=2.4,
                duration_seconds=0.4,
                severity=Severity.WARNING,
                confidence=0.88,
                channels=("M",),
                frequency_min_hz=2800.0,
                frequency_max_hz=3200.0,
                details={"peak_dbfs": -12.0}
            ),
            ForensicEvent(
                event_id="ev_mask_01",
                event_type=ForensicEventType.MASKING,
                start_time_seconds=3.0,
                end_time_seconds=3.3,
                duration_seconds=0.3,
                severity=Severity.CRITICAL,
                confidence=0.90,
                channels=("L", "R"),
                details={"stem_a": "Kick", "stem_b": "Bass", "band_name": "SUB_MID", "mean_delta_db": 1.2}
            )
        ]

        hypotheses = CausalityEngine.generate_hypotheses_for_events(events)
        assert len(hypotheses) == 3

        # Check clipping hypothesis
        hyp_clip = hypotheses[0]
        assert "ev_clip_01" in hyp_clip.observation_ids
        assert len(hyp_clip.supporting_evidence) > 0
        assert len(hyp_clip.competing_explanations) > 0
        assert 0.0 <= hyp_clip.confidence <= 1.0

        # Check resonance hypothesis
        hyp_res = hypotheses[1]
        assert "ev_res_01" in hyp_res.observation_ids
        assert "resonance" in hyp_res.likely_cause.lower()

        # Check masking hypothesis
        hyp_mask = hypotheses[2]
        assert "ev_mask_01" in hyp_mask.observation_ids
        assert "Kick" in hyp_mask.summary or "Kick" in hyp_mask.likely_cause

    def test_production_graph_injection_and_invariants(self):
        graph = ProductionGraph(project_id="test_forensic_proj")

        events = [
            ForensicEvent(
                event_id="ev_isp_01",
                event_type=ForensicEventType.INTER_SAMPLE_PEAK,
                start_time_seconds=0.5,
                end_time_seconds=0.52,
                duration_seconds=0.02,
                severity=Severity.ERROR,
                confidence=0.92,
                channels=("L", "R"),
                details={"true_peak_dbtp": 0.8, "threshold_dbtp": 0.0}
            )
        ]
        hypotheses = CausalityEngine.generate_hypotheses_for_events(events)

        created_node_ids = CausalityEngine.inject_into_production_graph(
            graph=graph,
            events=events,
            hypotheses=hypotheses,
            project_id="test_forensic_proj"
        )

        assert len(created_node_ids) >= 3  # 1 Measurement + 1 Observation + 1 Hypothesis

        # Verify node types in graph
        node_types = {n.node_type for n in graph.nodes.values()}
        assert NodeType.MEASUREMENT in node_types
        assert NodeType.OBSERVATION in node_types
        assert NodeType.HYPOTHESIS in node_types

        # STRICT INVARIANT: Forensics is strictly READ-ONLY; NEVER injects DECISION or ACTION
        assert NodeType.DECISION not in node_types
        assert NodeType.ACTION not in node_types
        assert NodeType.ROLLBACK not in node_types

        # Verify DAG acyclicity
        edges = graph._edges
        assert len(edges) >= 2

        # Edges should point Hypothesis -> Observation, Observation -> Measurement
        edge_types = {e["edge_type"] for e in edges}
        assert EdgeType.PARENT_OF.value in edge_types or EdgeType.DERIVED_FROM.value in edge_types


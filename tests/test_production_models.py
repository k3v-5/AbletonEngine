"""
Test Suite for Production Models and Governance Contract (GATE 2 - Documento 5).
Fase: 05 de 18 — PRODUCTION MODELS & GOVERNANCE CONTRACT (PIE-H1-D05).
Covers all 22 mandatory tests specified in Documento 5 (Sections 50, 51, 52, 58, 59).
"""
import unittest
import json
import copy
from dataclasses import FrozenInstanceError

from engine.production.models import (
    NodeType,
    EdgeType,
    EvidenceType,
    DecisionStatus,
    PolicyResult,
    PolicySeverity,
    PolicyStatus,
    ProductionReference,
    Evidence,
    ProductionIntent,
    ProductionNode,
    ProductionDecision,
    ProductionAction,
    PolicyViolation,
    PolicyEvaluation,
    MeasurementReference,
    VerificationResult,
    RollbackReference,
    ProductionContextSnapshot,
    ProductionCandidate,
    ProductionPlan,
    ProductionResult,
    generate_node_id,
    VALID_DECISION_TRANSITIONS
)
from engine.production.exceptions import (
    ProductionError,
    ModelValidationError,
    InvalidNodeTypeError,
    InvalidDecisionStateError,
    InvalidEvidenceError
)


class TestProductionModels(unittest.TestCase):
    """Exhaustive test suite for Documento 5 canonical production models."""

    def test_01_all_canonical_node_types(self):
        """Test 1 — Node types: Verifies all 15 canonical NodeType members exist."""
        expected_types = [
            "INTENT", "OBSERVATION", "ANALYSIS", "HYPOTHESIS", "CANDIDATE",
            "DECISION", "POLICY_CHECK", "SIMULATION", "ACTION", "MEASUREMENT",
            "VERIFICATION", "RESULT", "ROLLBACK", "REJECTION", "NO_OP"
        ]
        self.assertEqual(len(NodeType), 15)
        for t in expected_types:
            self.assertIn(t, NodeType.__members__)
            self.assertEqual(NodeType(t).value, t)

    def test_02_all_canonical_edge_types(self):
        """Test 2 — Edge types: Verifies all 10 canonical EdgeType members exist."""
        expected_edges = [
            "DERIVED_FROM", "CAUSED_BY", "PARENT_OF", "ALTERNATIVE_TO",
            "VALIDATED_BY", "REJECTED_BY", "EXECUTED_BY", "MEASURED_BY",
            "VERIFIED_BY", "ROLLED_BACK_BY"
        ]
        self.assertEqual(len(EdgeType), 10)
        for e in expected_edges:
            self.assertIn(e, EdgeType.__members__)
            self.assertEqual(EdgeType(e).value, e)

    def test_03_all_evidence_types(self):
        """Test 3 — Evidence types: Verifies FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT."""
        expected_evidence = ["FACT", "MEASUREMENT", "INFERENCE", "DECISION", "ACTION", "RESULT"]
        self.assertEqual(len(EvidenceType), 6)
        for ev in expected_evidence:
            self.assertIn(ev, EvidenceType.__members__)

    def test_04_valid_confidence_boundaries(self):
        """Test 4 — Confidence válido: Tests 0.0, 0.5, and 1.0 across models."""
        for conf in [0.0, 0.5, 1.0]:
            ev = Evidence(evidence_id="ev1", evidence_type=EvidenceType.FACT, source="test", value=42, confidence=conf)
            self.assertEqual(ev.confidence, conf)

            node = ProductionNode(node_id="n1", node_type=NodeType.INTENT, confidence=conf)
            self.assertEqual(node.confidence, conf)

            dec = ProductionDecision(decision_id="d1", confidence=conf)
            self.assertEqual(dec.confidence, conf)

            cand = ProductionCandidate(
                candidate_id="c1", description="cand", actions=(), expected_delta={},
                estimated_risk=0.1, estimated_impact=0.5, reversibility_score=0.9, confidence=conf
            )
            self.assertEqual(cand.confidence, conf)

    def test_05_invalid_confidence_boundaries(self):
        """Test 5 — Confidence inválido: Tests -0.01 and 1.01 raise ModelValidationError."""
        for invalid_conf in [-0.01, 1.01, -1.0, 2.5]:
            with self.assertRaises(ModelValidationError):
                Evidence(evidence_id="ev_inv", evidence_type=EvidenceType.FACT, source="test", value=1, confidence=invalid_conf)

            with self.assertRaises(ModelValidationError):
                ProductionNode(node_id="n_inv", node_type=NodeType.INTENT, confidence=invalid_conf)

            with self.assertRaises(ModelValidationError):
                ProductionDecision(decision_id="d_inv", confidence=invalid_conf)

            with self.assertRaises(ModelValidationError):
                ProductionCandidate(
                    candidate_id="c_inv", description="cand", actions=(), expected_delta={},
                    estimated_risk=0.1, estimated_impact=0.5, reversibility_score=0.9, confidence=invalid_conf
                )

    def test_06_production_intent_valid(self):
        """Test 6 — Intent: Creates a valid user musical intent describing WHAT, not HOW."""
        intent = ProductionIntent(
            intent_id="intent_001",
            description="hacer el master más fuerte",
            domain="mastering",
            target="loudness",
            project_id="project_001",
            context={"profile": "STREAMING", "tolerance_lufs": 0.5}
        )
        self.assertEqual(intent.intent_id, "intent_001")
        self.assertEqual(intent.domain, "mastering")
        self.assertEqual(intent.context["profile"], "STREAMING")

    def test_07_production_intent_empty_fields_rejected(self):
        """Test 7 — Intent vacío: Rejects empty project_id, description, or domain."""
        with self.assertRaises(ModelValidationError):
            ProductionIntent(intent_id="", description="desc", domain="mix", target=None, project_id="p1", context={})
        with self.assertRaises(ModelValidationError):
            ProductionIntent(intent_id="i1", description="   ", domain="mix", target=None, project_id="p1", context={})
        with self.assertRaises(ModelValidationError):
            ProductionIntent(intent_id="i1", description="desc", domain="", target=None, project_id="p1", context={})
        with self.assertRaises(ModelValidationError):
            ProductionIntent(intent_id="i1", description="desc", domain="mix", target=None, project_id="", context={})

    def test_08_action_reversibility_and_transaction_defaults(self):
        """Test 8 — Action: Verifies default reversible=True and transaction_required=True."""
        ref = ProductionReference(object_type="device", object_id="eq_001", name="EQ Eight")
        act = ProductionAction(
            action_id="act_01",
            action_type="SET_DEVICE_PARAMETER",
            target=ref,
            parameters={"band": 3, "gain_db": -1.5}
        )
        self.assertTrue(act.reversible)
        self.assertTrue(act.transaction_required)
        self.assertEqual(act.target.object_id, "eq_001")

    def test_09_candidate_normalized_ranges(self):
        """Test 9 — Candidate: Verifies normalized scores (0.0 to 1.0) and rejects breaches."""
        cand_ok = ProductionCandidate(
            candidate_id="cand_1",
            description="Apply gentle bus glue compression",
            actions=(),
            expected_delta={"integrated_lufs": 0.8, "true_peak_dbtp": -0.1},
            estimated_risk=0.2,
            estimated_impact=0.7,
            reversibility_score=1.0,
            confidence=0.9
        )
        self.assertEqual(cand_ok.estimated_risk, 0.2)

        # Risk > 1.0
        with self.assertRaises(ModelValidationError):
            ProductionCandidate(
                candidate_id="c_bad", description="bad", actions=(), expected_delta={},
                estimated_risk=1.1, estimated_impact=0.5, reversibility_score=0.9, confidence=0.8
            )
        # Reversibility < 0.0
        with self.assertRaises(ModelValidationError):
            ProductionCandidate(
                candidate_id="c_bad", description="bad", actions=(), expected_delta={},
                estimated_risk=0.1, estimated_impact=0.5, reversibility_score=-0.1, confidence=0.8
            )

    def test_10_policy_violation_representation(self):
        """Test 10 — PolicyViolation: Verifies representation, fields, and pythonic in-operator."""
        v = PolicyViolation(
            policy_id="MASTER_LIMIT",
            severity=PolicySeverity.CRITICAL,
            message="Gain reduction 3.2 dB exceeds maximum allowable 2.5 dB",
            field="gain_reduction_db",
            actual_value=3.2,
            expected_value=2.5,
            remediation="Reduce input gain or resolve headroom in the mix"
        )
        self.assertEqual(v.severity, PolicySeverity.CRITICAL)
        self.assertIn("gain reduction", v)
        self.assertIn("exceeds maximum", str(v))
        self.assertEqual(v.actual_value, 3.2)

    def test_11_policy_evaluation_and_critical_inviolability(self):
        """Test 11 — PolicyEvaluation: Verifies multiple violations and inviolability of CRITICAL."""
        crit_v = PolicyViolation(
            policy_id="MIX_MASTER_BOUNDARY",
            severity=PolicySeverity.CRITICAL,
            message="Mix problem cannot be resolved on Master Bus"
        )
        warn_v = PolicyViolation(
            policy_id="MASTER_EQ",
            severity=PolicySeverity.WARNING,
            message="EQ move is close to threshold"
        )

        eval_reject = PolicyEvaluation(
            result=PolicyResult.REJECT,
            violations=(crit_v,),
            warnings=(warn_v,),
            evaluated_policy_ids=("MIX_MASTER_BOUNDARY", "MASTER_EQ")
        )
        self.assertFalse(eval_reject.allowed)
        self.assertEqual(eval_reject.status, PolicyResult.REJECT)

        # INVARIANT: A CRITICAL violation CANNOT produce an ALLOW or ALLOW_WITH_WARNING result
        with self.assertRaises(ModelValidationError):
            PolicyEvaluation(
                result=PolicyResult.ALLOW,
                violations=(crit_v,)
            )

        with self.assertRaises(ModelValidationError):
            PolicyEvaluation(
                result=PolicyResult.ALLOW_WITH_WARNING,
                violations=(crit_v,)
            )

    def test_12_decision_committed_validation(self):
        """Test 12 — Decision: COMMITTED decision requires candidate, evidence, hypothesis, rationale."""
        # Valid COMMITTED decision
        dec = ProductionDecision(
            decision_id="dec_01",
            project_id="proj_1",
            category="MIX_CORRECTION",
            target=ProductionReference("track", "trk_01", "Bass"),
            hypothesis="Cutting 80 Hz will unmask kick drum",
            rationale="Acoustic masking ratio measured at 0.84",
            status=DecisionStatus.COMMITTED,
            confidence=0.92,
            selected_candidate_id="cand_eq_01",
            evidence_ids=("ev_masking_01",),
            expected_delta={"masking_ratio": -0.2}
        )
        self.assertEqual(dec.status, DecisionStatus.COMMITTED)

        # Missing selected_candidate_id on COMMITTED non-noop decision
        with self.assertRaises(ModelValidationError):
            ProductionDecision(
                decision_id="dec_bad",
                category="MIX_CORRECTION",
                hypothesis="Some hyp",
                rationale="Some rat",
                status=DecisionStatus.COMMITTED,
                selected_candidate_id=None,
                evidence_ids=("ev1",)
            )

        # Missing evidence on COMMITTED decision
        with self.assertRaises(ModelValidationError):
            ProductionDecision(
                decision_id="dec_bad",
                category="MIX_CORRECTION",
                hypothesis="Some hyp",
                rationale="Some rat",
                status=DecisionStatus.COMMITTED,
                selected_candidate_id="c1",
                evidence_ids=()
            )

    def test_13_no_op_decision_without_candidate(self):
        """Test 13 — NO_OP: A NO_OP decision can be COMMITTED without a selected candidate."""
        noop_dec = ProductionDecision(
            decision_id="dec_noop",
            category="NO_OP",
            decision_type="NO_OP",
            hypothesis="Current state already complies with streaming delivery specification",
            rationale="Integrated loudness is -14.1 LUFS (target -14.0 LUFS)",
            status=DecisionStatus.COMMITTED,
            selected_candidate_id=None,
            evidence_ids=("meas_lufs_01",)
        )
        self.assertEqual(noop_dec.status, DecisionStatus.COMMITTED)
        self.assertIsNone(noop_dec.selected_candidate_id)

    def test_14_rollback_reference_linkage(self):
        """Test 14 — Rollback: Verifies link to original_decision_id and transaction_id."""
        rb = RollbackReference(
            rollback_id="rb_001",
            original_decision_id="dec_master_001",
            transaction_id="tx_12345",
            reason="True Peak inter-sample clipping detected post-execution"
        )
        self.assertEqual(rb.original_decision_id, "dec_master_001")
        self.assertEqual(rb.transaction_id, "tx_12345")
        self.assertIn("clipping", rb.reason)

    def test_15_context_snapshot_mandatory_fingerprint(self):
        """Test 15 — Context Snapshot: Verifies session_fingerprint is mandatory and validated."""
        snap = ProductionContextSnapshot(
            project_id="proj_01",
            session_fingerprint="sha256_e3b0c44298fc1c149afbf4c8996fb924",
            tempo=124.0,
            key="F# minor",
            genre="Techno"
        )
        self.assertEqual(snap.session_fingerprint, "sha256_e3b0c44298fc1c149afbf4c8996fb924")

        # Empty fingerprint raises ModelValidationError
        with self.assertRaises(ModelValidationError):
            ProductionContextSnapshot(
                project_id="proj_01",
                session_fingerprint=""
            )

    def test_16_plan_immutability(self):
        """Test 16 — Plan: Verifies ProductionPlan is immutable and declarative."""
        snap = ProductionContextSnapshot(project_id="p1", session_fingerprint="fp_123")
        plan = ProductionPlan(
            plan_id="plan_01",
            project_id="p1",
            intent_id="int_01",
            context=snap,
            candidate_ids=("c1", "c2"),
            selected_candidate_id="c1",
            status=DecisionStatus.PROPOSED
        )
        self.assertEqual(plan.plan_id, "plan_01")
        with self.assertRaises(FrozenInstanceError):
            plan.plan_id = "plan_mutated"

    def test_17_result_mandatory_error_code_on_failure(self):
        """Test 17 — Result: Verifies error_code is mandatory when success=False."""
        # Success=True with no error code is valid
        res_ok = ProductionResult(
            result_id="res_01",
            plan_id="plan_01",
            decision_id="dec_01",
            success=True,
            message="Plan executed cleanly"
        )
        self.assertTrue(res_ok.success)

        # Success=False without error_code raises ModelValidationError
        with self.assertRaises(ModelValidationError):
            ProductionResult(
                result_id="res_bad",
                plan_id="plan_01",
                decision_id="dec_01",
                success=False,
                error_code=None,
                message="Something failed"
            )

        # Success=False with valid error_code succeeds
        res_fail = ProductionResult(
            result_id="res_fail",
            plan_id="plan_01",
            decision_id="dec_01",
            success=False,
            error_code="ACOUSTIC_REGRESSION",
            message="True peak exceeded brickwall ceiling"
        )
        self.assertEqual(res_fail.error_code, "ACOUSTIC_REGRESSION")

    def test_18_model_equality_and_determinism(self):
        """Test 18 — Igualdad: Verifies two identical model instances compare equal."""
        ref_a = ProductionReference("device", "dev_01", "Limiter")
        ref_b = ProductionReference("device", "dev_01", "Limiter")
        self.assertEqual(ref_a, ref_b)

        cand_a = ProductionCandidate(
            candidate_id="c1", description="Boost", actions=(), expected_delta={"lufs": 1.0},
            estimated_risk=0.1, estimated_impact=0.8, reversibility_score=1.0, confidence=0.95
        )
        cand_b = ProductionCandidate(
            candidate_id="c1", description="Boost", actions=(), expected_delta={"lufs": 1.0},
            estimated_risk=0.1, estimated_impact=0.8, reversibility_score=1.0, confidence=0.95
        )
        self.assertEqual(cand_a, cand_b)

    def test_19_immutability_frozen_instance(self):
        """Test 19 — Inmutabilidad: Modifying a frozen model attribute raises FrozenInstanceError."""
        ref = ProductionReference("track", "t1", "Vocal")
        with self.assertRaises(FrozenInstanceError):
            ref.object_id = "mutated"

        node = ProductionNode(node_id="n1", node_type=NodeType.INTENT)
        with self.assertRaises(FrozenInstanceError):
            node.confidence = 0.42

    def test_20_json_serialization_compatibility(self):
        """Test 20 — JSON compatibility: All models convert to valid JSON."""
        ref = ProductionReference("track", "t1", "Master")
        ev = Evidence("ev1", EvidenceType.MEASUREMENT, "dsp", -14.2, unit="LUFS")
        node = ProductionNode("n1", NodeType.MEASUREMENT, payload={"val": -14.2}, evidence=(ev,), references=(ref,))
        snap = ProductionContextSnapshot("p1", "fp_abc")
        plan = ProductionPlan("p1", "proj", "int_1", snap, ("c1",), "c1")
        res = ProductionResult("r1", "p1", "d1", True, message="OK")

        models = [ref, ev, node, snap, plan, res]
        for m in models:
            d = m.to_dict()
            json_str = json.dumps(d)
            self.assertIsInstance(json_str, str)
            self.assertGreater(len(json_str), 0)

    def test_21_mutable_contamination_defense(self):
        """Test 21 (Section 51) — Contaminación mutable: Mutating input payload does not mutate node."""
        nested_payload = {"x": {"value": 1}, "list": [10, 20]}
        node = ProductionNode(node_id="n_safe", node_type=NodeType.INTENT, payload=nested_payload)

        # Mutate outside dictionary
        nested_payload["x"]["value"] = 999
        nested_payload["list"].append(30)

        # Node's defensive copy remains pristine
        self.assertEqual(node.payload["x"]["value"], 1)
        self.assertEqual(node.payload["list"], [10, 20])

    def test_22_module_isolation(self):
        """Test 22 (Section 52 & 58) — Aislamiento: Importing engine.production does not load external libs."""
        import subprocess
        import sys
        import engine.production.models as prod_models
        import engine.production.exceptions as prod_exc

        # 1. In-process inspection: verify models and exceptions have zero external dependencies
        prohibited_in_models = ["networkx", "soundfile", "mcp", "numpy", "socket", "Live"]
        for mod_name in prohibited_in_models:
            self.assertNotIn(mod_name, prod_models.__dict__)
            self.assertNotIn(mod_name, prod_exc.__dict__)

        # 2. Clean subprocess inspection: verify fresh import of engine.production doesn't pull mcp or soundfile
        cmd = [
            sys.executable,
            "-c",
            "import sys; "
            "import engine.production; "
            "prohibited = ['mcp', 'Ableton', 'Live']; "
            "loaded = [p for p in prohibited if p in sys.modules]; "
            "sys.exit(len(loaded))"
        ]
        res = subprocess.run(cmd, capture_output=True)
        self.assertEqual(res.returncode, 0, f"Prohibited module loaded by engine.production: {res.stderr.decode()}")

    def test_23_decision_state_transitions(self):
        """Test 23 — Decision Transitions: Valid and invalid lifecycle status transitions."""
        dec = ProductionDecision(
            decision_id="dec_trans",
            project_id="p1",
            category="MIX_CORRECTION",
            status=DecisionStatus.PROPOSED
        )
        dec.transition_to(DecisionStatus.VALIDATED)
        self.assertEqual(dec.status, DecisionStatus.VALIDATED)
        dec.transition_to(DecisionStatus.COMMITTED)
        self.assertEqual(dec.status, DecisionStatus.COMMITTED)
        dec.transition_to(DecisionStatus.ROLLED_BACK)
        self.assertEqual(dec.status, DecisionStatus.ROLLED_BACK)

        # Terminal state cannot transition to COMMITTED
        with self.assertRaises(ProductionError):
            dec.transition_to(DecisionStatus.COMMITTED)


if __name__ == "__main__":
    unittest.main()

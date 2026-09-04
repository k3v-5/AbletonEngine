"""
ProductionPlanner for the Production Intelligence Engine (PIE).
Formulates causal, policy-compliant production plans.
Generates multi-candidate interventions, records policy rejections in the graph,
and selects the optimal plan following the Principle of Minimum Intervention.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import uuid
import datetime

from .models import (
    ProductionPlan, ProductionNode, NodeType, EdgeType,
    PolicyStatus
)
from .context import ProductionContext
from .graph import ProductionGraph
from .policies import ProductionPolicyEngine
from .memory import DecisionMemory
from .exceptions import PolicyViolationError, ProductionError


class ProductionPlanner:
    """
    Deterministic production planner.
    Explores candidate interventions, checks policy compliance, logs rejections,
    and returns a minimal-intervention plan bound by session fingerprint.
    """

    def __init__(
        self,
        policy_engine: Optional[ProductionPolicyEngine] = None,
        memory: Optional[DecisionMemory] = None,
        storage: Optional[Any] = None
    ):
        self.policy_engine = policy_engine or ProductionPolicyEngine()
        self.memory = memory
        self.storage = storage

    def plan(
        self,
        intent_description: Optional[str] = None,
        context: Optional[ProductionContext] = None,
        graph: Optional[ProductionGraph] = None,
        target_override: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        domain: Optional[str] = None,
        profile: Optional[str] = None,
        intent: Optional[Union[str, Any]] = None,
        target: Optional[str] = None,
        target_lufs: Optional[float] = None,
        tolerance: Optional[float] = None,
        **kwargs
    ) -> ProductionPlan:
        """
        Plans intervention based on musical intent, acoustic measurements, and policies.
        """
        # Resolve intent string
        desc = intent_description
        if not desc and intent:
            desc = getattr(intent, "text", getattr(intent, "description", str(intent)))
        if not desc and "description" in kwargs:
            desc = kwargs["description"]
        desc = desc or "Production plan"

        # Resolve context
        ctx = context or kwargs.get("ctx")
        if not ctx:
            raise ValueError("context is required for planning.")

        # Resolve target
        chosen_target = target_override or target or (getattr(intent, "target", None) if intent else None) or "Master"

        # Resolve graph
        g = graph or kwargs.get("g") or ProductionGraph(project_id=ctx.project_id)

        ctx_data = dict(context_data or {})
        ctx_data["is_planning"] = True
        if target_lufs is not None:
            ctx_data["target_lufs"] = target_lufs
        if tolerance is not None:
            ctx_data["tolerance"] = tolerance

        intent_id = f"intent_{uuid.uuid4().hex[:8]}"
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # 1. Capture baseline observation and measurements
        target = chosen_target
        domain = domain or ctx_data.get("domain") or ("master" if chosen_target.lower() == "master" else "mix")
        context = ctx
        graph = g
        target_lufs = ctx_data.get("target_lufs", getattr(ctx.loudness_profile, "target_lufs", -14.0))
        tolerance = ctx_data.get("tolerance", getattr(ctx.loudness_profile, "tolerance", 0.5))
        if profile:
            ctx_data["profile"] = profile

        measurements = context.capture_measurements(
            audio_buffer=ctx_data.get("audio_buffer"),
            sample_rate=ctx_data.get("sample_rate", 48000),
            target_name=target
        )

        current_lufs = measurements.get("integrated_lufs", -18.5)

        # 2. Add Intent and Observation nodes to causal graph
        intent_node = ProductionNode(
            node_id=intent_id,
            node_type=NodeType.INTENT,
            payload={"intent": desc, "domain": domain, "target": target}
        )
        obs_node = ProductionNode(
            node_id=f"obs_{uuid.uuid4().hex[:8]}",
            node_type=NodeType.OBSERVATION,
            payload={"current_lufs": current_lufs, "target_lufs": target_lufs, "target": target}
        )
        meas_node = ProductionNode(
            node_id=f"meas_{uuid.uuid4().hex[:8]}",
            node_type=NodeType.MEASUREMENT,
            payload=measurements
        )

        analysis_node = ProductionNode(
            node_id=f"analysis_{uuid.uuid4().hex[:8]}",
            node_type=NodeType.ANALYSIS,
            payload={
                "current_lufs": current_lufs,
                "target_lufs": target_lufs,
                "gap_lufs": round(target_lufs - current_lufs, 2),
                "diagnostic": "HEADROOM_AVAILABLE" if current_lufs < target_lufs else "COMPLIANT"
            }
        )
        hypo_node = ProductionNode(
            node_id=f"hypo_{uuid.uuid4().hex[:8]}",
            node_type=NodeType.HYPOTHESIS,
            payload={
                "hypothesis": f"Loudness can be adjusted by {round(target_lufs - current_lufs, 2)} LUFS to meet target",
                "target": target
            }
        )

        graph.add_node(intent_node)
        graph.add_node(obs_node)
        graph.add_node(meas_node)
        graph.add_node(analysis_node)
        graph.add_node(hypo_node)
        graph.add_edge(intent_node.node_id, obs_node.node_id, EdgeType.CAUSED_BY)
        graph.add_edge(obs_node.node_id, meas_node.node_id, EdgeType.MEASURED_BY)
        graph.add_edge(meas_node.node_id, analysis_node.node_id, EdgeType.DERIVED_FROM)
        graph.add_edge(analysis_node.node_id, hypo_node.node_id, EdgeType.DERIVED_FROM)

        # 3. Check if current state already complies (No-Op check)
        lufs_diff = target_lufs - current_lufs
        is_already_compliant = abs(lufs_diff) <= tolerance

        if is_already_compliant:
            no_op_node = ProductionNode(
                node_id=f"noop_{uuid.uuid4().hex[:8]}",
                node_type=NodeType.NO_OP,
                payload={
                    "reason": f"Loudness {current_lufs:.1f} LUFS is already within ±{tolerance} LUFS of target {target_lufs:.1f} LUFS.",
                    "target": target
                }
            )
            graph.add_node(no_op_node)
            graph.add_edge(meas_node.node_id, no_op_node.node_id, EdgeType.DERIVED_FROM)

            relevant_entities = [target]
            session_fp = context.compute_session_fingerprint(relevant_entities=relevant_entities)

            return ProductionPlan(
                plan_id=plan_id,
                intent_id=intent_id,
                domain=domain,
                target=target,
                decision_type="NO_OP",
                actions=[],
                expected_delta={"integrated_lufs": 0.0, "true_peak_dbtp": 0.0},
                session_fingerprint=session_fp,
                relevant_entities=relevant_entities,
                tolerances={"integrated_lufs": tolerance},
                is_no_op=True,
                status="PLANNED"
            )

        # 4. Generate candidate strategies
        candidates = self._generate_candidates(
            target=target,
            domain=domain,
            current_lufs=current_lufs,
            target_lufs=target_lufs,
            ctx_data=ctx_data
        )

        # 5. Evaluate each candidate against Policy Engine
        valid_candidates = []
        rejected_candidates = []

        for cand in candidates:
            # Combine context with candidate data
            eval_ctx = dict(ctx_data)
            policy_res = self.policy_engine.evaluate(cand, context=eval_ctx)

            if policy_res.allowed:
                valid_candidates.append({
                    "candidate": cand,
                    "policy_result": policy_res.to_dict(),
                    "intervention_cost": cand.get("intervention_cost", 1.0)
                })
            else:
                rej_info = {
                    "candidate_id": cand.get("id"),
                    "description": cand.get("description"),
                    "violations": [v.to_dict() if hasattr(v, "to_dict") else str(v) for v in policy_res.violations],
                    "alternatives": policy_res.alternatives,
                    "policy_id": policy_res.policy_id
                }
                rejected_candidates.append(rej_info)

                # Record rejection in ProductionGraph
                rej_node = ProductionNode(
                    node_id=f"rej_{cand.get('id', uuid.uuid4().hex[:8])}",
                    node_type=NodeType.REJECTION,
                    payload=rej_info
                )
                graph.add_node(rej_node)
                graph.add_edge(meas_node.node_id, rej_node.node_id, EdgeType.REJECTED_BY)

        if not valid_candidates:
            # If all candidates rejected, raise PolicyViolationError with alternatives
            first_rej = rejected_candidates[0] if rejected_candidates else {}
            v_items = first_rej.get("violations", [])
            v_msgs = [str(v.get("message", v)) if isinstance(v, dict) else (v.message if hasattr(v, "message") else str(v)) for v in v_items]
            raise PolicyViolationError(
                f"All production candidates were rejected by policy engine. Primary violation: {'; '.join(v_msgs)}",
                details={"rejected_candidates": rejected_candidates}
            )

        # 6. Rank valid candidates by Principle of Minimum Intervention
        valid_candidates.sort(key=lambda c: c["intervention_cost"])
        selected = valid_candidates[0]["candidate"]
        selected_policy_result = valid_candidates[0]["policy_result"]

        # 7. Search historical evidence from DecisionMemory (Candidate-Only invariant)
        historical_evidence = []
        if self.memory:
            historical_matches = self.memory.search(
                query_context={"genre": ctx_data.get("genre", "generic"), "target": target},
                domain=domain
            )
            # Take top 3
            historical_evidence = historical_matches[:3]

        chosen_domain = selected.get("domain", domain)
        chosen_target = selected.get("target", target)

        relevant_entities = [chosen_target]
        if target != chosen_target:
            relevant_entities.append(target)
        if "additional_entities" in ctx_data:
            relevant_entities.extend(ctx_data["additional_entities"])

        session_fp = context.compute_session_fingerprint(relevant_entities=relevant_entities)

        # 8. Construct final ProductionPlan
        return ProductionPlan(
            plan_id=plan_id,
            intent_id=intent_id,
            domain=chosen_domain,
            target=chosen_target,
            decision_type=selected.get("decision_type", "CORRECT"),
            actions=selected.get("actions", []),
            expected_delta=selected.get("expected_delta", {"integrated_lufs": round(lufs_diff, 2)}),

            session_fingerprint=session_fp,
            relevant_entities=relevant_entities,
            tolerances={"integrated_lufs": tolerance, "true_peak_dbtp": 0.2},
            selected_candidate=selected,
            rejected_candidates=rejected_candidates,
            candidates=tuple(c["candidate"] for c in valid_candidates),
            historical_evidence=historical_evidence,
            policy_result=selected_policy_result,
            is_no_op=False,
            status="PLANNED"
        )

    def _generate_candidates(
        self,
        target: str,
        domain: str,
        current_lufs: float,
        target_lufs: float,
        ctx_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generates a spectrum of candidates: minimal, aggressive, and alternative."""
        lufs_gap = round(target_lufs - current_lufs, 2)
        candidates = []

        # Candidate 1: Conservative Limiter Ceiling and Gain Adjustment (Minimum Intervention)
        needed_gain = min(lufs_gap, 2.0)
        candidates.append({
            "id": "cand_limiter_minimal",
            "description": f"Transparent master limiter boost (+{needed_gain:.1f} dB gain, ceiling -0.5 dBTP)",
            "domain": domain,
            "target": target,
            "decision_type": "CORRECT",
            "gain_reduction_db": min(needed_gain * 0.8, 1.8),
            "true_peak_dbtp": -0.5,
            "expected_delta": {"integrated_lufs": needed_gain, "true_peak_dbtp": 0.2},
            "intervention_cost": 1.0,  # Minimal intervention
            "actions": [
                {
                    "op_type": "set_device_parameter",
                    "device": "Limiter",
                    "parameter": "Ceiling",
                    "value": -0.5
                },
                {
                    "op_type": "set_device_parameter",
                    "device": "Limiter",
                    "parameter": "Gain",
                    "value": needed_gain
                }
            ]
        })

        # Candidate 2: Aggressive EQ Boost (violates MASTER_EQ policy)
        candidates.append({
            "id": "cand_aggressive_master_eq",
            "description": "Multi-band high and low shelf boost on master bus (+3.0 dB)",
            "domain": domain,
            "target": target,
            "decision_type": "OPTIMIZE",
            "intervention_cost": 3.5,
            "eq_bands_modified": [
                {"band": 1, "gain_db": 3.0, "freq": 100},
                {"band": 2, "gain_db": 2.5, "freq": 1000},
                {"band": 3, "gain_db": 3.0, "freq": 10000}
            ],
            "actions": [{"op_type": "eq_boost"}]
        })

        # Candidate 3: Over-compressed Limiter (violates MASTER_LIMIT policy)
        candidates.append({
            "id": "cand_excessive_limiter",
            "description": "Hard limiter slam (+6.0 dB gain, GR > 4.0 dB)",
            "domain": domain,
            "target": target,
            "decision_type": "CORRECT",
            "intervention_cost": 4.0,
            "gain_reduction_db": 4.5,   # Violates <= 2.5 dB
            "true_peak_dbtp": 0.1,      # Violates <= -0.3 dBTP
            "actions": [{"op_type": "slam_limiter"}]
        })

        # If a mix problem is noted, include a mix candidate
        if ctx_data.get("diagnosis") == "MIX_PROBLEM":
            candidates.append({
                "id": "cand_mix_headroom",
                "description": "Clean up low-end masking on Kick and Bass to reclaim master headroom",
                "domain": "mix",
                "target": "Bass",
                "decision_type": "CORRECT",
                "intervention_cost": 1.5,
                "actions": [
                    {
                        "op_type": "set_device_parameter",
                        "target": "Bass",
                        "device": "EQ Eight",
                        "parameter": "Band 1 Freq",
                        "value": 35.0
                    }
                ],
                "expected_delta": {"integrated_lufs": 1.5, "true_peak_dbtp": -0.4}
            })

        return candidates

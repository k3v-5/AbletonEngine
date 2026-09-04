"""
Production API Boundary for MCP Layer (Documento 13).
Encapsulates all 9 canonical MCP production tools with deterministic validation,
error mapping, concurrency protection, idempotency, and audit logging.
Prevents business logic leakage into server.py while enforcing strict safety invariants.
"""
import os
import json
import uuid
import datetime
import logging
import threading
from typing import Optional, List, Dict, Any, Union

from .models import (
    NodeType,
    EdgeType,
    PolicySeverity,
    PolicyDecision,
    RollbackStatus,
    RollbackType,
    RollbackScope,
    RollbackRequest,
    ProductionPlan,
)
from .graph import ProductionGraph
from .memory import DecisionMemory, MemoryStatus
from .policies import ProductionPolicyEngine
from .planner import ProductionPlanner
from .context import ProductionContext
from .executor import ProductionExecutor
from .rollback import RollbackEngine
from .serializer import ProductionStorage
from .exceptions import (
    ProductionError,
    PlanNotFoundError,
    StalePlanError,
    PolicyViolationError,
    RollbackFailureError,
    NonReversibleActionError,
    ConflictingStateError,
    DependencyConflictError,
    InvalidSnapshotError,
    StaleRollbackPlanError,
    RollbackBlockedLockedObjectError,
    MaxRollbackDepthExceededError,
    DecisionNotFoundError,
    ModelValidationError,
    AcousticRegressionError,
)

logger = logging.getLogger("PIE.MCPBoundary")

VALID_DOMAINS = {"MUSIC", "ARRANGEMENT", "SOUND", "MIX", "MASTER", "PERFORMANCE", "SESSION"}
VALID_PROFILES = {"EBU_R128", "STREAMING", "CLUB"}


class ProductionAPIBoundary:
    """
    Singleton-capable boundary providing the 9 canonical MCP production tools.
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        project_id: str = "default_project",
        graph: Optional[ProductionGraph] = None,
        memory: Optional[DecisionMemory] = None,
        policy_engine: Optional[ProductionPolicyEngine] = None,
        context: Optional[ProductionContext] = None,
        planner: Optional[ProductionPlanner] = None,
        executor: Optional[ProductionExecutor] = None,
        rollback_engine: Optional[RollbackEngine] = None,
        storage: Optional[ProductionStorage] = None,
    ):
        self.project_id = project_id
        self.storage = storage or ProductionStorage(base_dir=base_dir)

        # 1. Production Graph (loaded from disk or freshly created)
        self.graph = graph or self.storage.load_graph()
        if not self.graph:
            self.graph = ProductionGraph(project_id=project_id)

        # 2. Decision Memory (loaded from disk or freshly created)
        self.memory = memory or self.storage.load_memory()
        if not self.memory:
            self.memory = DecisionMemory(project_id=project_id)

        # 3. Policy Engine
        self.policy_engine = policy_engine or ProductionPolicyEngine()

        # 4. Production Context
        if context:
            self.context = context
        else:
            from engine.session.graph import SessionShadowGraph
            from engine.transactions.manager import TransactionManager
            from engine.adapters.mock_adapter import MockAbletonAdapter
            _sg = SessionShadowGraph()
            _ad = MockAbletonAdapter()
            _tm = TransactionManager(graph=_sg, adapter=_ad)
            self.context = ProductionContext(shadow_graph=_sg, transaction_manager=_tm, project_id=project_id)

        # 5. Planner
        self.planner = planner or ProductionPlanner(
            policy_engine=self.policy_engine,
            storage=self.storage
        )

        # 6. Rollback Engine
        self.rollback_engine = rollback_engine or RollbackEngine(
            storage=self.storage,
            policy_engine=self.policy_engine
        )

        # 7. Executor
        self.executor = executor or ProductionExecutor(
            policy_engine=self.policy_engine,
            storage=self.storage,
            rollback_engine=self.rollback_engine
        )

        # Concurrency & Idempotency Controls
        self._global_lock = threading.Lock()
        self._plan_locks: Dict[str, threading.Lock] = {}
        self._validated_plans: Dict[str, Dict[str, Any]] = {}
        self._executed_plans: Dict[str, Dict[str, Any]] = {}
        self._execution_history: List[Dict[str, Any]] = []

    def _get_plan_lock(self, plan_id: str) -> threading.Lock:
        with self._global_lock:
            if plan_id not in self._plan_locks:
                self._plan_locks[plan_id] = threading.Lock()
            return self._plan_locks[plan_id]

    def _success_response(
        self,
        status: str = "OK",
        data: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "status": status,
            "data": data or {},
            "errors": [],
            "warnings": warnings or [],
            "trace": {
                "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "engine_version": "PIE-1.0"
            }
        }

    def _error_response(
        self,
        code: str,
        message: str,
        status: str = "ERROR",
        severity: str = "ERROR",
        data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "success": False,
            "status": status,
            "data": data or {},
            "errors": [
                {
                    "code": code,
                    "message": message,
                    "severity": severity
                }
            ],
            "warnings": [],
            "trace": {
                "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "engine_version": "PIE-1.0"
            }
        }

    # =========================================================================
    # 1. production_status (Doc 13 Sec 6)
    # =========================================================================
    def production_status(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns the current state of Production Governance infrastructure.
        Strictly non-mutating: zero node creation, zero DSP execution, zero Live mutation.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            active_tx_id = None
            if self.context.transaction_manager:
                for tx_id, tx in self.context.transaction_manager.active_transactions.items():
                    if tx.status == "OPEN":
                        active_tx_id = tx_id
                        break

            status_val = "TRANSACTION_ACTIVE" if active_tx_id else "READY"

            # Pending plans in storage
            pending_plans = 0
            plans_dir = os.path.join(self.storage.base_dir, "plans")
            if os.path.exists(plans_dir):
                pending_plans = len([f for f in os.listdir(plans_dir) if f.endswith(".json")])

            # Last decision and transaction
            last_dec_id = None
            last_tx_id = None
            for node in reversed(list(self.graph.nodes.values())):
                if node.node_type == NodeType.DECISION:
                    last_dec_id = node.node_id
                    last_tx_id = node.transaction_id
                    break

            data = {
                "production_graph": {
                    "node_count": len(self.graph.nodes),
                    "edge_count": len(self.graph.edges),
                    "graph_version": self.graph.graph_version
                },
                "decision_memory": {
                    "records_count": len(self.memory.records) if hasattr(self.memory, "records") else len(self.memory._records),
                    "project_id": self.memory.project_id
                },
                "policy_engine": {
                    "policies_count": len(self.policy_engine.policies),
                    "status": "ACTIVE"
                },
                "planner": {
                    "status": "READY",
                    "supported_domains": sorted(list(VALID_DOMAINS))
                },
                "executor": {
                    "status": "READY"
                },
                "active_transaction": active_tx_id,
                "session_fingerprint": self.context.compute_session_fingerprint(),
                "pending_plans": pending_plans,
                "last_decision_id": last_dec_id,
                "last_transaction_id": last_tx_id
            }
            return self._success_response(status=status_val, data=data, request_id=req_id)

        except Exception as exc:
            logger.exception("Error in production_status")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 2. production_plan (Doc 13 Sec 7-13)
    # =========================================================================
    def production_plan(
        self,
        intent: str,
        domain: str,
        target: Optional[str] = None,
        profile: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transforms a musical intent into a candidate plan without executing any mutations.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            # 1. Validate intent (Sec 8)
            if not isinstance(intent, str) or not intent.strip():
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="Intent must be a non-empty string.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )
            clean_intent = intent.strip()
            if len(clean_intent) > 2000:
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="Intent exceeds maximum length of 2000 characters.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )

            # 2. Validate domain (Sec 9)
            if not isinstance(domain, str) or not domain.strip():
                return self._error_response(
                    code="INVALID_DOMAIN",
                    message=f"Domain must be specified. Valid domains: {sorted(list(VALID_DOMAINS))}",
                    status="INVALID_DOMAIN",
                    request_id=req_id
                )
            clean_domain = domain.strip().upper()
            if clean_domain not in VALID_DOMAINS:
                return self._error_response(
                    code="INVALID_DOMAIN",
                    message=f"Invalid domain '{clean_domain}'. Valid domains are: {sorted(list(VALID_DOMAINS))}",
                    status="INVALID_DOMAIN",
                    request_id=req_id
                )

            # 3. Validate profile (Sec 10)
            clean_profile = None
            if profile is not None:
                clean_profile = profile.strip().upper()
                if clean_profile not in VALID_PROFILES:
                    return self._error_response(
                        code="INVALID_PROFILE",
                        message=f"Invalid profile '{clean_profile}'. Valid profiles are: {sorted(list(VALID_PROFILES))}",
                        status="INVALID_PROFILE",
                        request_id=req_id
                    )

            # 4. Generate plan via planner
            plan = self.planner.plan(
                intent_description=clean_intent,
                domain=clean_domain,
                target_override=target,
                profile=clean_profile,
                context=self.context,
                graph=self.graph
            )

            # 5. Persist plan
            self.storage.save_plan(plan)

            expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)).isoformat()

            # Format result (Sec 11)
            raw_cands = getattr(plan, "candidates", ()) or (
                [plan.selected_candidate] if getattr(plan, "selected_candidate", None) else []
            )
            cands_list = [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in raw_cands]

            data = {
                "plan_id": plan.plan_id,
                "intent_id": plan.intent_id,
                "session_fingerprint": plan.session_fingerprint,
                "created_at": plan.created_at,
                "domain": plan.domain,
                "target": plan.target,
                "profile": clean_profile or "STREAMING",
                "candidates": cands_list,
                "rejected_candidates": list(plan.rejected_candidates),
                "selected_candidate": plan.selected_candidate,
                "policy_status": plan.status,
                "requires_confirmation": False,
                "estimated_risk": 0.1,
                "estimated_impact": 0.3,
                "reversible": all(a.get("reversible", True) for a in plan.actions),
                "expires_at": expires_at,
                "execution_allowed": False  # Invariant: must pass production_validate()
            }

            return self._success_response(status="PLAN_CREATED", data=data, request_id=req_id)

        except Exception as exc:
            logger.exception("Error in production_plan")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 3. production_validate (Doc 13 Sec 14-17)
    # =========================================================================
    def production_validate(
        self,
        plan_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates a previously created plan against current session state,
        fingerprints, policies, and object locks.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            if not isinstance(plan_id, str) or not plan_id.strip():
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="plan_id must be a non-empty string.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )
            clean_plan_id = plan_id.strip()

            # 1. Load Plan (Sec 15)
            plan = self.storage.load_plan(clean_plan_id)
            if not plan:
                return self._error_response(
                    code="PLAN_NOT_FOUND",
                    message=f"Production plan '{clean_plan_id}' does not exist.",
                    status="PLAN_NOT_FOUND",
                    request_id=req_id
                )

            # 2. Staleness Check (Sec 16)
            is_stale = False
            relevant_entities = list(plan.relevant_entities)
            if not relevant_entities and plan.target:
                relevant_entities = [plan.target]

            if plan.session_fingerprint:
                is_stale = self.context.is_stale_for_plan(
                    plan.session_fingerprint,
                    relevant_entities=relevant_entities if relevant_entities else None
                )

            # 3. Policy Check
            target_eval = plan.selected_candidate or plan.to_dict()
            eval_ctx = {
                "is_planning": False,
                "dry_run": True,
                "target": plan.target,
                "domain": plan.domain,
                "target_locked": self.context.get_locked_state(plan.target) if plan.target else False
            }
            policy_res = self.policy_engine.evaluate(target_eval, context=eval_ctx)

            # 4. Lock Check
            is_locked = self.context.get_locked_state(plan.target) if plan.target else False

            checks = [
                {"name": "FINGERPRINT", "status": "FAIL" if is_stale else "PASS"},
                {"name": "POLICY", "status": "PASS" if policy_res.allowed else "FAIL"},
                {"name": "LOCKS", "status": "FAIL" if is_locked else "PASS"},
            ]

            if is_stale:
                return self._error_response(
                    code="STALE_PLAN",
                    message="Session state for target track has changed since plan was generated.",
                    status="STALE_PLAN",
                    data={"plan_id": clean_plan_id, "execution_allowed": False, "checks": checks},
                    request_id=req_id
                )

            if not policy_res.allowed:
                return self._error_response(
                    code="POLICY_REJECTED",
                    message="; ".join(str(v.message) for v in policy_res.violations),
                    status="POLICY_REJECTED",
                    data={"plan_id": clean_plan_id, "execution_allowed": False, "checks": checks},
                    request_id=req_id
                )

            if is_locked:
                return self._error_response(
                    code="ROLLBACK_BLOCKED_LOCKED_OBJECT",
                    message=f"Target object '{plan.target}' is locked.",
                    status="EXECUTION_BLOCKED",
                    data={"plan_id": clean_plan_id, "execution_allowed": False, "checks": checks},
                    request_id=req_id
                )

            # Record plan as validated in memory
            self._validated_plans[clean_plan_id] = {
                "validated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "fingerprint": self.context.compute_session_fingerprint(relevant_entities=relevant_entities)
            }

            data = {
                "plan_id": clean_plan_id,
                "execution_allowed": True,
                "policy_status": "ALLOW",
                "fingerprint_status": "MATCH",
                "transaction_required": True,
                "requires_confirmation": False,
                "checks": checks
            }
            return self._success_response(status="VALID", data=data, request_id=req_id)

        except Exception as exc:
            logger.exception("Error in production_validate")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 4. production_execute (Doc 13 Sec 18-22)
    # =========================================================================
    def production_execute(
        self,
        plan_id: str,
        auto_rollback: bool = True,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a validated production plan atomically through the ProductionExecutor.
        Enforces idempotency, validation preconditions, and non-destructive failure handling.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            if not isinstance(plan_id, str) or not plan_id.strip():
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="plan_id must be a non-empty string.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )
            clean_plan_id = plan_id.strip()

            # 1. Load Plan
            plan = self.storage.load_plan(clean_plan_id)
            if not plan:
                return self._error_response(
                    code="PLAN_NOT_FOUND",
                    message=f"Production plan '{clean_plan_id}' does not exist.",
                    status="PLAN_NOT_FOUND",
                    request_id=req_id
                )

            # 2. Idempotency Check (Sec 45 & 55)
            is_committed = (
                str(getattr(plan, "status", "")) in ("COMMITTED", "DecisionStatus.COMMITTED") or
                clean_plan_id in self._executed_plans
            )
            if not is_committed:
                for node in self.graph.nodes.values():
                    if node.node_type == NodeType.DECISION and (node.node_id == clean_plan_id or node.payload.get("plan_id") == clean_plan_id):
                        is_committed = True
                        break

            if is_committed:
                exec_info = self._executed_plans.get(clean_plan_id, {})
                orig_dec_id = exec_info.get("decision_id")
                if not orig_dec_id:
                    for node in self.graph.nodes.values():
                        if node.node_type == NodeType.DECISION and (node.node_id == clean_plan_id or node.payload.get("plan_id") == clean_plan_id):
                            orig_dec_id = node.node_id
                            break
                return self._success_response(
                    status="ALREADY_EXECUTED",
                    data={
                        "plan_id": clean_plan_id,
                        "decision_id": orig_dec_id or f"dec_{clean_plan_id}",
                        "message": "Plan was already executed. Idempotent NO_OP returned."
                    },
                    request_id=req_id
                )

            # 3. Validation Precondition (Sec 11 & 19)
            if clean_plan_id not in self._validated_plans:
                val_res = self.production_validate(clean_plan_id, request_id=req_id)
                if not val_res.get("success") or not val_res.get("data", {}).get("execution_allowed"):
                    return self._error_response(
                        code="PLAN_NOT_VALIDATED",
                        message="Plan has not passed production_validate() or validation failed.",
                        status="INVALID_ARGUMENT",
                        data=val_res.get("data"),
                        request_id=req_id
                    )

            # 4. Concurrency Protection (Sec 46)
            plan_lock = self._get_plan_lock(clean_plan_id)
            acquired = plan_lock.acquire(blocking=False)
            if not acquired:
                return self._error_response(
                    code="CONCURRENT_EXECUTION",
                    message=f"Another execution is already active for plan '{clean_plan_id}'.",
                    status="EXECUTION_BLOCKED",
                    request_id=req_id
                )

            try:
                # 5. Execute via ProductionExecutor
                exec_res = self.executor.execute(
                    plan=plan,
                    context=self.context,
                    graph=self.graph,
                    auto_rollback=auto_rollback
                )

                if exec_res.status == "COMMITTED":
                    self._executed_plans[clean_plan_id] = {
                        "status": "COMMITTED",
                        "decision_id": exec_res.details.get("decision_id"),
                        "transaction_id": exec_res.transaction_id,
                        "committed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                    try:
                        object.__setattr__(plan, "status", DecisionStatus.COMMITTED)
                        self.storage.save_plan(plan)
                    except Exception:
                        pass

                    data = {
                        "plan_id": clean_plan_id,
                        "decision_id": exec_res.details.get("decision_id"),
                        "transaction_id": exec_res.transaction_id,
                        "verification_id": exec_res.details.get("verification_id"),
                        "rollback_performed": False,
                        "expected_delta": plan.expected_delta,
                        "actual_delta": exec_res.details.get("actual_delta", {}),
                        "regressions": [],
                        "session_fingerprint_before": exec_res.pre_fingerprint,
                        "session_fingerprint_after": exec_res.post_fingerprint
                    }
                    return self._success_response(status="COMMITTED", data=data, request_id=req_id)

                elif exec_res.status == "ROLLED_BACK":
                    data = {
                        "original_decision_id": exec_res.details.get("decision_id"),
                        "rollback_decision_id": exec_res.details.get("rollback_decision_id"),
                        "transaction_id": exec_res.transaction_id,
                        "rollback_reason": exec_res.details.get("reason", "Acoustic regression detected"),
                        "regressions": list(exec_res.details.get("regressions", []))
                    }
                    return {
                        "success": False,
                        "status": "ROLLED_BACK",
                        "data": data,
                        "errors": [
                            {
                                "code": "REGRESSION_DETECTED",
                                "message": "Acoustic regression detected; automatic rollback performed.",
                                "severity": "WARNING"
                            }
                        ],
                        "warnings": [],
                        "trace": {
                            "request_id": req_id,
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "engine_version": "PIE-1.0"
                        }
                    }

                else:
                    return self._error_response(
                        code="EXECUTION_FAILED",
                        message=f"Execution finished with status '{exec_res.status}'.",
                        status=exec_res.status,
                        data=exec_res.to_dict(),
                        request_id=req_id
                    )

            finally:
                plan_lock.release()

        except StalePlanError as exc:
            return self._error_response(
                code="STALE_PLAN",
                message=str(exc),
                status="STALE_PLAN",
                request_id=req_id
            )
        except PolicyViolationError as exc:
            return self._error_response(
                code="POLICY_REJECTED",
                message=str(exc),
                status="POLICY_REJECTED",
                request_id=req_id
            )
        except AcousticRegressionError as exc:
            details = getattr(exc, "details", {})
            data = {
                "original_decision_id": details.get("decision_id"),
                "rollback_decision_id": details.get("rollback_id"),
                "rollback_reason": str(exc),
                "regressions": details.get("verification", {}).get("regressions", [])
            }
            return {
                "success": False,
                "status": "ROLLED_BACK",
                "data": data,
                "errors": [
                    {
                        "code": "REGRESSION_DETECTED",
                        "message": str(exc),
                        "severity": "WARNING"
                    }
                ],
                "warnings": [],
                "trace": {
                    "request_id": req_id,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "engine_version": "PIE-1.0"
                }
            }
        except Exception as exc:
            logger.exception("Error in production_execute")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 5. production_explain (Doc 13 Sec 23-25)
    # =========================================================================
    def production_explain(
        self,
        decision_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reconstructs the full causal explanation for a decision or node.
        Categorizes data strictly into FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            if not isinstance(decision_id, str) or not decision_id.strip():
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="decision_id must be a non-empty string.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )
            clean_dec_id = decision_id.strip()
            explanation = self.graph.explain_decision(clean_dec_id)

            # Build causal chain in lineage order
            chain_nodes = []
            for group in [explanation.get("facts", []),
                          explanation.get("measurements", []),
                          explanation.get("inferences", [])]:
                for item in group:
                    chain_nodes.append(item.get("node_id"))

            chain_nodes.append(clean_dec_id)

            for group in [explanation.get("actions", []),
                          explanation.get("results", [])]:
                for item in group:
                    chain_nodes.append(item.get("node_id"))

            dec_info = explanation.get("decision", {})
            summary_str = f"Decision {clean_dec_id} ({dec_info.get('decision_type', 'DECISION')}): {dec_info.get('reason', 'N/A')}"

            data = {
                "decision_id": clean_dec_id,
                "summary": summary_str,
                "causal_chain": chain_nodes,
                "facts": explanation.get("facts", []),
                "measurements": explanation.get("measurements", []),
                "inferences": explanation.get("inferences", []),
                "decision": dec_info,
                "actions": explanation.get("actions", []),
                "results": explanation.get("results", []),
                "policies": [inf for inf in explanation.get("inferences", []) if inf.get("node_type") == "POLICY_CHECK"],
                "alternatives_rejected": explanation.get("rejected_alternatives", []),
                "rollback": next((res for res in explanation.get("results", []) if res.get("node_type") == "ROLLBACK"), None),
                "total_lineage_nodes": explanation.get("total_lineage_nodes", len(chain_nodes))
            }
            return self._success_response(status="OK", data=data, request_id=req_id)

        except DecisionNotFoundError:
            return self._error_response(
                code="DECISION_NOT_FOUND",
                message=f"Decision '{decision_id}' not found in production graph.",
                status="DECISION_NOT_FOUND",
                request_id=req_id
            )
        except Exception as exc:
            logger.exception("Error in production_explain")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 6. production_history (Doc 13 Sec 26-28)
    # =========================================================================
    def production_history(
        self,
        limit: int = 20,
        domain: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries historical decisions ordered by timestamp DESC, decision_id ASC.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            # 1. Validate limit (Sec 26)
            if not isinstance(limit, int) or limit < 1 or limit > 100:
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="limit must be an integer between 1 and 100.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )

            # 2. Validate domain filter (Sec 28)
            target_domain = None
            if domain is not None:
                target_domain = domain.strip().upper()
                if target_domain not in VALID_DOMAINS:
                    return self._error_response(
                        code="INVALID_DOMAIN",
                        message=f"Invalid domain filter '{target_domain}'. Valid domains: {sorted(list(VALID_DOMAINS))}",
                        status="INVALID_DOMAIN",
                        request_id=req_id
                    )

            # 3. Retrieve decision nodes from graph
            decisions = []
            for node in self.graph.nodes.values():
                if node.node_type == NodeType.DECISION:
                    node_domain = str(node.payload.get("domain", "")).upper()
                    if target_domain and node_domain != target_domain:
                        continue
                    decisions.append({
                        "decision_id": node.node_id,
                        "domain": node_domain,
                        "target": node.payload.get("target"),
                        "decision_type": node.payload.get("decision_type"),
                        "transaction_id": node.transaction_id,
                        "timestamp": node.created_at,
                        "status": node.payload.get("status", "COMMITTED"),
                        "hypothesis": node.payload.get("hypothesis", node.payload.get("reason")),
                    })

            # Deterministic sorting (Sec 27): timestamp DESC, decision_id ASC
            decisions.sort(key=lambda d: (-datetime.datetime.fromisoformat(d["timestamp"]).timestamp() if d.get("timestamp") else 0, d["decision_id"]))

            sliced = decisions[:limit]
            data = {
                "total_count": len(decisions),
                "returned_count": len(sliced),
                "limit": limit,
                "domain_filter": target_domain,
                "decisions": sliced
            }
            return self._success_response(status="OK", data=data, request_id=req_id)

        except Exception as exc:
            logger.exception("Error in production_history")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 7. production_graph (Doc 13 Sec 29-32)
    # =========================================================================
    def production_graph(
        self,
        format: str = "summary",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries ProductionGraph statistics ('summary') or DAG structure ('dag').
        Strictly READ-ONLY: mutations are rejected.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            clean_format = format.strip().lower()
            if clean_format not in ("summary", "dag"):
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="Format must be strictly 'summary' or 'dag'.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )

            if clean_format == "summary":
                # Sec 30
                node_types: Dict[str, int] = {}
                for n in self.graph.nodes.values():
                    nt_val = n.node_type.value if hasattr(n.node_type, "value") else str(n.node_type)
                    node_types[nt_val] = node_types.get(nt_val, 0) + 1

                edge_types: Dict[str, int] = {}
                for e in self.graph.edges:
                    et = e.get("edge_type")
                    et_val = et.value if hasattr(et, "value") else str(et)
                    edge_types[et_val] = edge_types.get(et_val, 0) + 1

                decisions_count = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.DECISION)
                rollbacks_count = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.ROLLBACK)
                rejections_count = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.REJECTION)
                no_ops_count = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.NO_OP)

                data = {
                    "node_count": len(self.graph.nodes),
                    "edge_count": len(self.graph.edges),
                    "node_types": node_types,
                    "edge_types": edge_types,
                    "decisions": decisions_count,
                    "rollbacks": rollbacks_count,
                    "rejections": rejections_count,
                    "no_ops": no_ops_count,
                    "graph_version": self.graph.graph_version
                }
                return self._success_response(status="OK", data=data, request_id=req_id)

            else:
                # Sec 31: format == "dag"
                dag_dict = self.graph.to_dict()
                data = {
                    "nodes": [n for n in dag_dict.get("nodes", {}).values()],
                    "edges": dag_dict.get("edges", []),
                    "graph_version": self.graph.graph_version
                }
                return self._success_response(status="OK", data=data, request_id=req_id)

        except Exception as exc:
            logger.exception("Error in production_graph")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 8. production_rollback (Doc 13 Sec 33-36)
    # =========================================================================
    def production_rollback(
        self,
        decision_id_or_transaction: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reverts a decision or transaction atomically, non-destructively,
        and records causal rollback nodes.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            if not isinstance(decision_id_or_transaction, str) or not decision_id_or_transaction.strip():
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="decision_id_or_transaction must be a non-empty string.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )
            target = decision_id_or_transaction.strip()

            # Target existence resolution
            target_dec_id = target
            if target not in self.graph.nodes:
                found_tx = False
                for node in self.graph.nodes.values():
                    if node.transaction_id == target:
                        target_dec_id = node.node_id
                        found_tx = True
                        break
                if not found_tx and not self.storage.load_plan(target):
                    return self._error_response(
                        code="ROLLBACK_TARGET_NOT_FOUND",
                        message=f"Target decision or transaction '{target}' does not exist.",
                        status="TARGET_NOT_FOUND",
                        request_id=req_id
                    )

            # Build request
            rb_id = f"rb_mcp_{uuid.uuid4().hex[:8]}"
            req = RollbackRequest(
                rollback_id=rb_id,
                target_decision_id=target_dec_id,
                requested_by="mcp_user",
                rollback_type=RollbackType.USER_REQUESTED,
                reason=f"MCP requested rollback for target {target}",
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                current_session_fingerprint=self.context.compute_session_fingerprint(),
                expected_target_fingerprint=None,
                project_id=self.project_id
            )

            # Create plan
            plan = self.rollback_engine.create_plan(req, self.context, graph=self.graph)

            # Execute plan
            res = self.rollback_engine.execute(plan, self.context, graph=self.graph)

            data = {
                "rollback_id": res.rollback_id,
                "status": res.status.value if hasattr(res.status, "value") else str(res.status),
                "target_decision_id": target_dec_id,
                "transaction_id": res.transaction_id,
                "operations_planned": res.operations_planned,
                "operations_applied": res.operations_applied,
                "structural_verification": res.structural_verification,
                "fingerprint_verification": res.fingerprint_verification,
                "acoustic_verification": res.acoustic_verification,
                "regressions_detected": list(res.regressions_detected)
            }
            return self._success_response(status="COMMITTED" if res.rollback_committed else "FAILED", data=data, request_id=req_id)

        except NonReversibleActionError as exc:
            return self._error_response(
                code="NON_REVERSIBLE_ACTION",
                message=str(exc),
                status="ROLLBACK_UNAVAILABLE",
                severity="CRITICAL",
                request_id=req_id
            )
        except RollbackBlockedLockedObjectError as exc:
            return self._error_response(
                code="ROLLBACK_BLOCKED_LOCKED_OBJECT",
                message=str(exc),
                status="EXECUTION_BLOCKED",
                severity="CRITICAL",
                request_id=req_id
            )
        except StaleRollbackPlanError as exc:
            return self._error_response(
                code="STALE_ROLLBACK_PLAN",
                message=str(exc),
                status="STALE_PLAN",
                severity="CRITICAL",
                request_id=req_id
            )
        except Exception as exc:
            logger.exception("Error in production_rollback")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )

    # =========================================================================
    # 9. production_memory_search (Doc 13 Sec 37-41)
    # =========================================================================
    def production_memory_search(
        self,
        query: str,
        context: dict,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Searches historical decision memory.
        Enforces absolute invariant: matches are evidence-only and NEVER auto-executed.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        try:
            # 1. Validate query
            if not isinstance(query, str) or not query.strip():
                return self._error_response(
                    code="INVALID_ARGUMENT",
                    message="query must be a non-empty string.",
                    status="INVALID_ARGUMENT",
                    request_id=req_id
                )
            clean_query = query.strip()

            # 2. Validate context & project_id (Sec 39)
            if not isinstance(context, dict):
                return self._error_response(
                    code="INVALID_CONTEXT",
                    message="context must be a dictionary.",
                    status="INVALID_CONTEXT",
                    request_id=req_id
                )
            proj_id = context.get("project_id")
            if not proj_id or not str(proj_id).strip():
                return self._error_response(
                    code="INVALID_CONTEXT",
                    message="context must contain a non-empty 'project_id'.",
                    status="INVALID_CONTEXT",
                    request_id=req_id
                )

            # 3. Deterministic search & ranking (Sec 40)
            matches = []
            target_domain = context.get("domain", "").lower() if context.get("domain") else None
            target_target = context.get("target", "").lower() if context.get("target") else None
            target_genre = context.get("genre", "").lower() if context.get("genre") else None

            # Scan memory records
            records = self.memory._records if hasattr(self.memory, "_records") else {}
            for memory_id, rec in records.items():
                if rec.get("status") not in [MemoryStatus.VALID, MemoryStatus.EXPERIMENTAL]:
                    continue

                rec_ctx = rec.get("context", {})
                rec_proj = rec.get("project_id", "")
                rec_domain = rec.get("domain", "").lower()
                rec_target = rec.get("target", "").lower()
                rec_genre = rec_ctx.get("genre", "").lower()

                # Ranking criteria score
                score = 0.0
                if rec_proj == proj_id:
                    score += 0.35
                if target_domain and rec_domain == target_domain:
                    score += 0.25
                if target_target and rec_target == target_target:
                    score += 0.20
                if target_genre and rec_genre == target_genre:
                    score += 0.10
                if clean_query.lower() in rec.get("reason", "").lower() or clean_query.lower() in rec.get("decision_type", "").lower():
                    score += 0.10

                if score > 0.1:
                    matches.append({
                        "decision_id": rec.get("decision_id", memory_id),
                        "similarity_score": round(min(1.0, score), 2),
                        "evidence_only": True,                     # Invariant (Sec 41)
                        "current_validation_required": True,       # Invariant (Sec 41)
                        "execute": False,                          # Invariant (Sec 38 & 41)
                        "historical_action": rec.get("decision", {}),
                        "historical_result": rec.get("outcome", {})
                    })

            # Deterministic sorting (Sec 40): similarity_score DESC, decision_id ASC
            matches.sort(key=lambda m: (-m["similarity_score"], m["decision_id"]))

            data = {
                "query": clean_query,
                "matches_count": len(matches),
                "matches": matches
            }
            return self._success_response(status="OK", data=data, request_id=req_id)

        except Exception as exc:
            logger.exception("Error in production_memory_search")
            return self._error_response(
                code="INTERNAL_ERROR",
                message=str(exc),
                status="ERROR",
                request_id=req_id
            )


# =============================================================================
# Global Boundary Lifecycle & Registration Helpers
# =============================================================================
_GLOBAL_BOUNDARY: Optional[ProductionAPIBoundary] = None
_BOUNDARY_INIT_LOCK = threading.Lock()


def get_production_boundary(
    base_dir: Optional[str] = None,
    project_id: str = "default_project"
) -> ProductionAPIBoundary:
    """Returns the managed singleton instance of ProductionAPIBoundary."""
    global _GLOBAL_BOUNDARY
    if _GLOBAL_BOUNDARY is None:
        with _BOUNDARY_INIT_LOCK:
            if _GLOBAL_BOUNDARY is None:
                _GLOBAL_BOUNDARY = ProductionAPIBoundary(base_dir=base_dir, project_id=project_id)
    return _GLOBAL_BOUNDARY


def reset_production_boundary():
    """Resets singleton instance for testing isolation."""
    global _GLOBAL_BOUNDARY
    with _BOUNDARY_INIT_LOCK:
        _GLOBAL_BOUNDARY = None


# Standalone function wrappers forwarding to singleton boundary
def production_status(request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_status(request_id=request_id)


def production_plan(
    intent: str,
    domain: str,
    target: Optional[str] = None,
    profile: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    return get_production_boundary().production_plan(intent=intent, domain=domain, target=target, profile=profile, request_id=request_id)


def production_validate(plan_id: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_validate(plan_id=plan_id, request_id=request_id)


def production_execute(plan_id: str, auto_rollback: bool = True, request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_execute(plan_id=plan_id, auto_rollback=auto_rollback, request_id=request_id)


def production_explain(decision_id: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_explain(decision_id=decision_id, request_id=request_id)


def production_history(limit: int = 20, domain: Optional[str] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_history(limit=limit, domain=domain, request_id=request_id)


def production_graph(format: str = "summary", request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_graph(format=format, request_id=request_id)


def production_rollback(decision_id_or_transaction: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_rollback(decision_id_or_transaction=decision_id_or_transaction, request_id=request_id)


def production_memory_search(query: str, context: dict, request_id: Optional[str] = None) -> Dict[str, Any]:
    return get_production_boundary().production_memory_search(query=query, context=context, request_id=request_id)

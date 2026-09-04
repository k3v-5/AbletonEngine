"""
Atomic persistence for PIE ProductionGraph, DecisionMemory, and Plans.
Uses atomic file writes (write to temp file in target dir then atomic os.replace)
to guarantee persistence safety against crashes and power failures.
"""
import os
import json
import tempfile
import hashlib
import shutil
import datetime
from typing import Optional, List, Dict, Any

from .graph import ProductionGraph
from .memory import DecisionMemory
from .models import (
    ProductionPlan,
    ProductionDecision,
    ExecutionResult,
    ProductionContextSnapshot,
    SessionFingerprint,
    RollbackPlan,
    RollbackResult,
    RollbackJournalEvent,
)
from .exceptions import SerializationError, PersistenceError, ProductionStateCorruptionError


DEFAULT_PRODUCTION_STATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "state",
    "production"
)


class ProductionStorage:
    """
    Manages disk persistence for production state.
    Guarantees atomic writes (flush + fsync + os.replace) and explicit corruption detection.
    """

    def __init__(self, base_dir: Optional[str] = None, base_path: Optional[str] = None, project_id: Optional[str] = None):
        self.base_dir = base_dir or base_path or DEFAULT_PRODUCTION_STATE_DIR
        self.project_id = project_id or "default_project"
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "plans"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "executions"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "snapshots"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "fingerprints"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "verification"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "rollbacks"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "rollbacks", "plans"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "rollbacks", "results"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "journal"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "backups"), exist_ok=True)

    def _atomic_write(self, target_path: str, data: str):
        """Writes content to a temp file in target directory, flushes, fsyncs, then atomically replaces."""
        dir_name = os.path.dirname(target_path)
        os.makedirs(dir_name, exist_ok=True)

        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                tf.write(data)
                tf.flush()
                os.fsync(tf.fileno())
                temp_name = tf.name

            os.replace(temp_name, target_path)
        except Exception as exc:
            raise PersistenceError(f"Failed atomic write to '{target_path}': {str(exc)}") from exc

    def save_graph(self, graph: ProductionGraph, filename: str = "graph.json") -> str:
        target = os.path.join(self.base_dir, filename)
        content = graph.serialize_deterministic()
        self._atomic_write(target, content)
        return target

    def load_graph(self, filename: str = "graph.json") -> ProductionGraph:
        target = os.path.join(self.base_dir, filename)
        # Check alternative filename for backward compatibility
        if not os.path.exists(target):
            alt_target = os.path.join(self.base_dir, "production_graph.json")
            if os.path.exists(alt_target):
                target = alt_target
            else:
                return ProductionGraph(project_id="default_project")

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ProductionGraph.from_dict(data)
        except Exception as exc:
            raise ProductionStateCorruptionError(
                f"Corruption or format error loading graph from '{target}': {str(exc)}"
            ) from exc

    def save_memory(self, memory: DecisionMemory, filename: str = "memory.json") -> str:
        target = os.path.join(self.base_dir, filename)
        content = json.dumps(memory.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_memory(self, filename: str = "memory.json") -> DecisionMemory:
        target = os.path.join(self.base_dir, filename)
        # Check alternative filename for backward compatibility
        if not os.path.exists(target):
            alt_target = os.path.join(self.base_dir, "decision_memory.json")
            if os.path.exists(alt_target):
                target = alt_target
            else:
                return DecisionMemory(project_id="default_project")

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DecisionMemory.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading memory from '{target}': {str(exc)}"
            ) from exc

    def save_decisions(self, decisions: List[ProductionDecision], filename: str = "decisions.json") -> str:
        target = os.path.join(self.base_dir, filename)
        payload = [d.to_dict() for d in decisions]
        content = json.dumps(payload, indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_decisions(self, filename: str = "decisions.json") -> List[ProductionDecision]:
        target = os.path.join(self.base_dir, filename)
        if not os.path.exists(target):
            return []

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ProductionDecision.from_dict(d) for d in data]
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading decisions from '{target}': {str(exc)}"
            ) from exc

    def save_metadata(self, metadata: Dict[str, Any], filename: str = "metadata.json") -> str:
        target = os.path.join(self.base_dir, filename)
        content = json.dumps(metadata, indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_metadata(self, filename: str = "metadata.json") -> Dict[str, Any]:
        target = os.path.join(self.base_dir, filename)
        if not os.path.exists(target):
            return {"schema_version": "1.0", "engine": "production_intelligence_engine"}

        try:
            with open(target, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading metadata from '{target}': {str(exc)}"
            ) from exc

    def save_plan(self, plan: ProductionPlan) -> str:
        target = os.path.join(self.base_dir, "plans", f"{plan.plan_id}.json")
        content = json.dumps(plan.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_plan(self, plan_id: str) -> Optional[ProductionPlan]:
        target = os.path.join(self.base_dir, "plans", f"{plan_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ProductionPlan.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading plan '{plan_id}': {str(exc)}"
            ) from exc

    def save_execution(self, execution: ExecutionResult) -> str:
        target = os.path.join(self.base_dir, "executions", f"{execution.execution_id}.json")
        content = json.dumps(execution.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        target = os.path.join(self.base_dir, "executions", f"{execution_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ExecutionResult.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading execution '{execution_id}': {str(exc)}"
            ) from exc

    def save_snapshot(self, snapshot: ProductionContextSnapshot, snapshot_id: Optional[str] = None) -> str:
        s_id = snapshot_id or getattr(snapshot, "snapshot_id", None) or f"snap_{snapshot.project_id}_{snapshot.captured_at.replace(':', '-').replace('.', '-')}"
        target = os.path.join(self.base_dir, "snapshots", f"{s_id}.json")
        content = json.dumps(snapshot.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_snapshot(self, snapshot_id: str) -> Optional[ProductionContextSnapshot]:
        target = os.path.join(self.base_dir, "snapshots", f"{snapshot_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ProductionContextSnapshot.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading snapshot '{snapshot_id}': {str(exc)}"
            ) from exc

    def save_fingerprint(self, fingerprint: SessionFingerprint, fingerprint_id: Optional[str] = None) -> str:
        f_id = fingerprint_id or f"fp_{fingerprint.value[:16]}"
        target = os.path.join(self.base_dir, "fingerprints", f"{f_id}.json")
        content = json.dumps(fingerprint.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_fingerprint(self, fingerprint_id: str) -> Optional[SessionFingerprint]:
        target = os.path.join(self.base_dir, "fingerprints", f"{fingerprint_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SessionFingerprint.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading fingerprint '{fingerprint_id}': {str(exc)}"
            ) from exc

    def save_verification(self, report: Any) -> str:
        target = os.path.join(self.base_dir, "verification", f"{report.verification_id}.json")
        content = json.dumps(report.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_verification(self, verification_id: str) -> Optional[Any]:
        target = os.path.join(self.base_dir, "verification", f"{verification_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            from .verification import VerificationReport
            return VerificationReport.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading verification '{verification_id}': {str(exc)}"
            ) from exc

    def save_rollback_plan(self, plan: RollbackPlan) -> str:
        target = os.path.join(self.base_dir, "rollbacks", "plans", f"{plan.rollback_id}.json")
        content = json.dumps(plan.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_rollback_plan(self, rollback_id: str) -> Optional[RollbackPlan]:
        target = os.path.join(self.base_dir, "rollbacks", "plans", f"{rollback_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RollbackPlan.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading rollback plan '{rollback_id}': {str(exc)}"
            ) from exc

    def save_rollback_result(self, result: RollbackResult) -> str:
        target = os.path.join(self.base_dir, "rollbacks", "results", f"{result.rollback_id}.json")
        content = json.dumps(result.to_dict(), indent=2, sort_keys=True)
        self._atomic_write(target, content)
        return target

    def load_rollback_result(self, rollback_id: str) -> Optional[RollbackResult]:
        target = os.path.join(self.base_dir, "rollbacks", "results", f"{rollback_id}.json")
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RollbackResult.from_dict(data)
        except Exception as exc:
            raise SerializationError(
                f"Corruption or format error loading rollback result '{rollback_id}': {str(exc)}"
            ) from exc

    def append_rollback_journal(self, event: RollbackJournalEvent) -> str:
        journal_path = os.path.join(self.base_dir, "journal", "rollback_journal.jsonl")
        line = json.dumps(event.to_dict(), sort_keys=True) + "\n"
        try:
            with open(journal_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            return journal_path
        except Exception as exc:
            raise PersistenceError(f"Failed to append to rollback journal: {str(exc)}") from exc

    def read_rollback_journal(self, rollback_id: Optional[str] = None) -> List[RollbackJournalEvent]:
        journal_path = os.path.join(self.base_dir, "journal", "rollback_journal.jsonl")
        if not os.path.exists(journal_path):
            return []
        events: List[RollbackJournalEvent] = []
        try:
            with open(journal_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    evt_data = json.loads(line_str)
                    evt = RollbackJournalEvent.from_dict(evt_data)
                    if rollback_id is None or evt.rollback_id == rollback_id:
                        events.append(evt)
            return events
        except Exception as exc:
            raise SerializationError(f"Failed reading rollback journal: {str(exc)}") from exc

    def create_backup(self, target_path: str) -> Optional[str]:
        """Creates a timestamped backup before modifying critical state (Doc 12 Sec 30)."""
        if not os.path.exists(target_path):
            return None
        basename = os.path.basename(target_path)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{basename}.{timestamp}.bak"
        backup_path = os.path.join(self.base_dir, "backups", backup_name)
        try:
            shutil.copy2(target_path, backup_path)
            return backup_path
        except Exception as exc:
            raise PersistenceError(f"Failed creating backup for '{target_path}': {str(exc)}") from exc

    def save_with_integrity_hash(self, target_path: str, payload: Dict[str, Any], schema_version: int = 1) -> str:
        """Saves document with schema version and canonical SHA-256 content hash (Doc 12 Sec 29)."""
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        content_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        envelope = {
            "schema_version": schema_version,
            "content_hash": content_hash,
            "created_at": now_iso,
            "updated_at": now_iso,
            "payload": payload
        }
        content = json.dumps(envelope, indent=2, sort_keys=True)
        self._atomic_write(target_path, content)
        return target_path

    def load_with_integrity_hash(self, target_path: str) -> Dict[str, Any]:
        """Loads document and cryptographically validates content hash against payload (Doc 12 Sec 29)."""
        if not os.path.exists(target_path):
            raise PersistenceError(f"File '{target_path}' not found.")
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                envelope = json.load(f)
        except Exception as exc:
            raise ProductionStateCorruptionError(f"JSON corruption reading '{target_path}': {str(exc)}") from exc

        if not isinstance(envelope, dict) or "payload" not in envelope or "content_hash" not in envelope:
            raise ProductionStateCorruptionError(f"Malformed envelope schema in '{target_path}'.")

        payload = envelope["payload"]
        recorded_hash = envelope["content_hash"]
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        computed_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

        if computed_hash != recorded_hash:
            raise ProductionStateCorruptionError(
                f"Content hash integrity check failed for '{target_path}': "
                f"recorded '{recorded_hash}', computed '{computed_hash}'."
            )
        return payload

    def recover_startup_state(self) -> Dict[str, Any]:
        """
        Validates state on startup (Section 71):
        - Loads graph, memory, plans
        - Validates graph DAG integrity
        - Detects plans in 'EXECUTING' state and sets them to 'RECOVERY_REQUIRED'
        """
        graph = self.load_graph()
        graph.validate_integrity()
        memory = self.load_memory()

        plans_dir = os.path.join(self.base_dir, "plans")
        recovered_plans = []
        if os.path.exists(plans_dir):
            for fname in os.listdir(plans_dir):
                if fname.endswith(".json"):
                    plan_path = os.path.join(plans_dir, fname)
                    try:
                        with open(plan_path, "r", encoding="utf-8") as f:
                            pdata = json.load(f)
                        if pdata.get("status") == "EXECUTING":
                            pdata["status"] = "RECOVERY_REQUIRED"
                            self._atomic_write(plan_path, json.dumps(pdata, indent=2, sort_keys=True))
                            recovered_plans.append(pdata.get("plan_id"))
                    except Exception:
                        pass

        return {
            "graph_nodes": len(graph.nodes),
            "memory_records": len(memory._records),
            "interrupted_plans_recovered": recovered_plans
        }


production_storage = ProductionStorage()

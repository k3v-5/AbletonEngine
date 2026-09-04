# engine/transactions/manager.py
import datetime
from typing import Dict, Any, List, Optional, Union
from ..models import (
    Transaction, Operation, TransactionStatus,
    generate_id, TrackNode, ClipNode
)
from ..session.graph import SessionShadowGraph
from ..adapters.base import BaseAbletonAdapter
from ..snapshots.manager import snapshot_manager
from ..persistence.storage import storage
from ..events.event_logger import event_logger
from ..errors import (
    TransactionFailedError, TransactionConflictError,
    InvalidParameterError, ObjectNotFoundError
)
from .validator import TransactionValidator
from .rollback import RollbackEngine

class TransactionManager:
    """Manages transactional units of work with optimistic concurrency and atomic rollback"""
    def __init__(self, graph: SessionShadowGraph, adapter: BaseAbletonAdapter):
        self.graph = graph
        self.adapter = adapter
        self.active_transactions: Dict[str, Transaction] = {}
        self.transaction_history_list: List[Dict[str, Any]] = []

    def begin(self, name: str = "", description: str = "") -> Transaction:
        """Start a new transaction, take an automatic baseline snapshot and record base_version"""
        tx_id = generate_id("tx")
        
        # Create baseline snapshot for safe rollback
        snapshot = snapshot_manager.create_snapshot(
            self.graph,
            name=f"Baseline for {tx_id}",
            description=f"Auto snapshot prior to transaction '{name or tx_id}'"
        )

        tx = Transaction(
            id=tx_id,
            name=name or f"Transaction {tx_id}",
            description=description,
            status=TransactionStatus.OPEN.value,
            base_version=self.graph.version,
            snapshot_id=snapshot.id
        )

        self.active_transactions[tx_id] = tx
        storage.save_transaction(tx_id, tx.to_dict())
        
        event_logger.log_event(
            operation="transaction_begin",
            transaction_id=tx_id,
            details={"name": tx.name, "base_version": tx.base_version, "snapshot_id": snapshot.id}
        )
        return tx

    def get_transaction(self, tx_id: Union[str, Transaction]) -> Transaction:
        if isinstance(tx_id, Transaction):
            return tx_id
        if hasattr(tx_id, "id") and not isinstance(tx_id, str):
            tx_id = str(tx_id.id)
        if tx_id in self.active_transactions:
            return self.active_transactions[tx_id]
        disk_data = storage.load_transaction(str(tx_id))
        if disk_data:
            tx = Transaction.from_dict(disk_data)
            self.active_transactions[str(tx_id)] = tx
            return tx
        raise InvalidParameterError(f"Transaction '{tx_id}' not found", {"transaction_id": str(tx_id)})

    # Staging Operations with automatic inverse generation for WAL
    def stage_create_track(self, tx_id: str, name: str, track_type: str = "midi", role: Optional[str] = None) -> Operation:
        tx = self.get_transaction(tx_id)
        if tx.status != TransactionStatus.OPEN.value:
            raise InvalidParameterError(f"Cannot stage on {tx.status} transaction {tx_id}")

        temp_track_id = generate_id("track")
        next_ableton_idx = len(self.graph.tracks)
        
        op = Operation(
            id=generate_id("op"),
            op_type="create_track",
            target_id=temp_track_id,
            parameters={
                "name": name,
                "type": track_type,
                "role": role,
                "assigned_id": temp_track_id,
                "target_index": next_ableton_idx
            },
            inverse_op={
                "op_type": "delete_track",
                "parameters": {"track_id": temp_track_id, "ableton_index": next_ableton_idx}
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx_id, tx.to_dict())
        return op

    def stage_set_volume(self, tx_id: str, track_id: str, volume: float) -> Operation:
        tx = self.get_transaction(tx_id)
        track = self.graph.get_track(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

        old_volume = track.volume
        op = Operation(
            id=generate_id("op"),
            op_type="set_volume",
            target_id=track_id,
            parameters={"volume": volume, "ableton_index": track.ableton_index},
            inverse_op={
                "op_type": "set_volume",
                "parameters": {"track_id": track_id, "volume": old_volume, "ableton_index": track.ableton_index}
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx_id, tx.to_dict())
        return op

    def stage_set_panning(self, tx_id: str, track_id: str, panning: float) -> Operation:
        tx = self.get_transaction(tx_id)
        track = self.graph.get_track(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

        old_panning = track.panning
        op = Operation(
            id=generate_id("op"),
            op_type="set_panning",
            target_id=track_id,
            parameters={"panning": panning, "ableton_index": track.ableton_index},
            inverse_op={
                "op_type": "set_panning",
                "parameters": {"track_id": track_id, "panning": old_panning, "ableton_index": track.ableton_index}
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx_id, tx.to_dict())
        return op

    def stage_set_mute(self, tx_id: str, track_id: str, mute: bool) -> Operation:
        tx = self.get_transaction(tx_id)
        track = self.graph.get_track(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

        old_mute = track.mute
        op = Operation(
            id=generate_id("op"),
            op_type="set_mute",
            target_id=track_id,
            parameters={"mute": mute, "ableton_index": track.ableton_index},
            inverse_op={
                "op_type": "set_mute",
                "parameters": {"track_id": track_id, "mute": old_mute, "ableton_index": track.ableton_index}
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx_id, tx.to_dict())
        return op

    def stage_set_role(self, tx_id: str, track_id: str, role: Optional[str]) -> Operation:
        tx = self.get_transaction(tx_id)
        track = self.graph.get_track(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

        old_role = track.metadata.role
        op = Operation(
            id=generate_id("op"),
            op_type="set_role",
            target_id=track_id,
            parameters={"role": role},
            inverse_op={
                "op_type": "set_role",
                "parameters": {"track_id": track_id, "role": old_role}
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx_id, tx.to_dict())
        return op

    def stage_set_tempo(self, tx_id: str, tempo: float) -> Operation:
        tx = self.get_transaction(tx_id)
        old_tempo = self.graph.project_state.tempo
        op = Operation(
            id=generate_id("op"),
            op_type="set_tempo",
            parameters={"tempo": tempo},
            inverse_op={
                "op_type": "set_tempo",
                "parameters": {"tempo": old_tempo}
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx_id, tx.to_dict())
        return op

    def stage_add_notes(
        self,
        tx_id: str,
        track_id: str,
        clip_index: int,
        notes: List[Dict[str, Any]],
        mode: str = "create"
    ) -> Operation:
        tx = self.get_transaction(tx_id)
        track = self.graph.get_track(track_id)
        if not track:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

        existing_notes = []
        if self.adapter and self.adapter.is_connected():
            try:
                existing_notes = self.adapter.get_clip_notes(track.ableton_index, clip_index)
            except Exception:
                existing_notes = []

        op = Operation(
            id=generate_id("op"),
            op_type="add_notes",
            target_id=track_id,
            parameters={
                "clip_index": clip_index,
                "notes": notes,
                "mode": mode,
                "ableton_index": track.ableton_index
            },
            inverse_op={
                "op_type": "restore_notes",
                "parameters": {
                    "track_id": track_id,
                    "clip_index": clip_index,
                    "previous_notes": existing_notes,
                    "ableton_index": track.ableton_index
                }
            }
        )
        tx.operations.append(op)
        storage.save_transaction(tx.id, tx.to_dict())
        return op

    def preview(self, tx_id: str) -> Dict[str, Any]:
        """Dry-run preview calculating impacts without modifying Ableton Live"""
        tx = self.get_transaction(tx_id)
        warnings = []
        changes = []

        for op in tx.operations:
            change_item = {"type": op.op_type, "target": op.target_id, "parameters": op.parameters}
            if op.target_id:
                track = self.graph.get_track(op.target_id)
                if track and track.metadata.locked:
                    warnings.append(f"Target object '{track.name}' ({op.target_id}) is locked!")
            changes.append(change_item)

        return {
            "transaction_id": tx.id,
            "name": tx.name,
            "status": tx.status,
            "operations_count": len(tx.operations),
            "changes": changes,
            "warnings": warnings,
            "dry_run": True
        }

    def validate(self, tx_id: str) -> bool:
        tx = self.get_transaction(tx_id)
        return TransactionValidator.validate(tx, self.graph)

    def commit(self, tx_id: str) -> Dict[str, Any]:
        """Atomically commit the transaction. Validates, checks optimistic concurrency, executes, or auto-rolls back"""
        tx = self.get_transaction(tx_id)
        if tx.status != TransactionStatus.OPEN.value:
            raise InvalidParameterError(f"Cannot commit transaction {tx_id} in state {tx.status}")

        # 1. Optimistic Concurrency Check
        if self.graph.version != tx.base_version:
            raise TransactionConflictError(
                f"Concurrency conflict: Graph version has changed from {tx.base_version} to {self.graph.version} while transaction was open. Please refresh and re-stage.",
                {"base_version": tx.base_version, "current_version": self.graph.version}
            )

        # 2. Pre-commit validation
        TransactionValidator.validate(tx, self.graph)

        # 3. Execution loop
        executed_ops = []
        try:
            for op in tx.operations:
                self._execute_single_op(op)
                op.executed = True
                executed_ops.append(op)

            tx.status = TransactionStatus.COMMITTED.value
            tx.completed_at = datetime.datetime.now().isoformat()
            storage.save_transaction(tx.id, tx.to_dict())
            storage.save_graph(self.graph.to_dict())

            event_logger.log_event(
                operation="transaction_commit",
                transaction_id=tx.id,
                details={"operations_count": len(executed_ops)},
                status="success"
            )

            return {
                "transaction_id": tx.id,
                "status": "COMMITTED",
                "operations_executed": len(executed_ops),
                "graph_version": self.graph.version
            }

        except Exception as e:
            # Auto-rollback on any failure
            event_logger.log_event(
                operation="transaction_execution_failed",
                transaction_id=tx.id,
                details={"error": str(e)},
                status="failed"
            )
            tx.status = TransactionStatus.FAILED.value
            tx.error_message = str(e)
            
            # Execute compensating rollback
            rollback_result = RollbackEngine.execute_rollback(tx, self.graph, self.adapter)
            tx.status = TransactionStatus.ROLLED_BACK.value
            storage.save_transaction(tx.id, tx.to_dict())

            raise TransactionFailedError(
                f"Transaction failed during execution: {str(e)}. Changes have been safely rolled back.",
                {"transaction_id": tx.id, "error": str(e), "rollback": rollback_result}
            )

    def rollback(self, tx_id: str) -> Dict[str, Any]:
        """Manually trigger rollback for an open or failed transaction"""
        tx = self.get_transaction(tx_id)
        if tx.status not in [TransactionStatus.OPEN.value, TransactionStatus.FAILED.value, TransactionStatus.COMMITTED.value]:
            raise InvalidParameterError(f"Cannot rollback transaction {tx.id} with status {tx.status}")

        result = RollbackEngine.execute_rollback(tx, self.graph, self.adapter)
        tx.status = TransactionStatus.ROLLED_BACK.value
        tx.completed_at = datetime.datetime.now().isoformat()
        storage.save_transaction(tx.id, tx.to_dict())
        storage.save_graph(self.graph.to_dict())

        event_logger.log_event(
            operation="transaction_manual_rollback",
            transaction_id=tx.id,
            details=result,
            status="success"
        )
        return {
            "transaction_id": tx.id,
            "status": "ROLLED_BACK",
            "rollback_details": result
        }

    def status(self, tx_id: str) -> Dict[str, Any]:
        tx = self.get_transaction(tx_id)
        return tx.to_dict()

    def history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return storage.list_transactions(limit=limit)

    def _execute_single_op(self, op: Operation):
        """Dispatches an operation to both Ableton Live (via adapter) and the Shadow Graph"""
        op_type = op.op_type
        params = op.parameters

        if op_type == "create_track":
            name = params["name"]
            track_type = params.get("type", "midi")
            role = params.get("role")
            target_id = op.target_id

            # Ableton creation
            res = self.adapter.create_midi_track(-1)
            created_idx = res.get("track_index", len(self.graph.tracks))
            self.adapter.set_track_name(created_idx, name)

            # Update inverse_op with actual created index
            if op.inverse_op and "parameters" in op.inverse_op:
                op.inverse_op["parameters"]["ableton_index"] = created_idx

            # Graph update
            new_track = TrackNode(
                id=target_id,
                ableton_index=created_idx,
                name=name,
                type=track_type
            )
            if role:
                new_track.metadata.role = role
            self.graph.add_track(new_track)

        elif op_type == "set_volume":
            t_id = op.target_id
            track = self.graph.get_track(t_id)
            vol = float(params["volume"])
            if track:
                self.adapter.set_track_volume(track.ableton_index, vol)
                track.volume = vol
                self.graph.increment_version()

        elif op_type == "set_panning":
            t_id = op.target_id
            track = self.graph.get_track(t_id)
            pan = float(params["panning"])
            if track:
                self.adapter.set_track_panning(track.ableton_index, pan)
                track.panning = pan
                self.graph.increment_version()

        elif op_type == "set_mute":
            t_id = op.target_id
            track = self.graph.get_track(t_id)
            mute = bool(params["mute"])
            if track:
                self.adapter.set_track_mute(track.ableton_index, mute)
                track.mute = mute
                self.graph.increment_version()

        elif op_type == "set_role":
            t_id = op.target_id
            role = params.get("role")
            self.graph.set_track_role(t_id, role)

        elif op_type == "set_tempo":
            tempo = float(params["tempo"])
            self.adapter.set_tempo(tempo)
            self.graph.project_state.tempo = tempo
            self.graph.increment_version()

        elif op_type == "add_notes":
            t_id = op.target_id
            track = self.graph.get_track(t_id)
            clip_idx = params["clip_index"]
            notes_list = params["notes"]
            mode = params.get("mode", "create")
            if track:
                self.adapter.add_notes_to_clip(track.ableton_index, clip_idx, notes_list, mode=mode)
                self.graph.increment_version()

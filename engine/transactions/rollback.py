# engine/transactions/rollback.py
from typing import Dict, Any, List
from ..models import Transaction, Operation, TransactionStatus
from ..session.graph import SessionShadowGraph
from ..adapters.base import BaseAbletonAdapter
from ..snapshots.manager import snapshot_manager
from ..events.event_logger import event_logger
from ..errors import RollbackFailedError

class RollbackEngine:
    """Executes atomic rollbacks via WAL inverse operations (Level 1) or snapshot restoration (Level 2)"""
    @staticmethod
    def execute_rollback(
        transaction: Transaction,
        graph: SessionShadowGraph,
        adapter: BaseAbletonAdapter
    ) -> Dict[str, Any]:
        reversed_ops = []
        errors = []

        # Level 1: Logical Rollback (LIFO walk of executed operations)
        executed_ops = [op for op in transaction.operations if op.executed]
        for op in reversed(executed_ops):
            inv = op.inverse_op
            if not inv:
                errors.append(f"Operation {op.id} ({op.op_type}) has no inverse_op defined")
                continue

            inv_type = inv.get("op_type")
            inv_params = inv.get("parameters", {})
            try:
                # 1. Reverse on Ableton Adapter if connected
                if adapter and adapter.is_connected():
                    if inv_type == "delete_track":
                        t_idx = inv_params.get("ableton_index")
                        if t_idx is not None:
                            adapter.delete_track(t_idx)

                    elif inv_type == "set_volume":
                        t_idx = inv_params.get("ableton_index")
                        vol = inv_params.get("volume")
                        if t_idx is not None and vol is not None:
                            adapter.set_track_volume(t_idx, vol)

                    elif inv_type == "set_panning":
                        t_idx = inv_params.get("ableton_index")
                        pan = inv_params.get("panning")
                        if t_idx is not None and pan is not None:
                            adapter.set_track_panning(t_idx, pan)

                    elif inv_type == "set_mute":
                        t_idx = inv_params.get("ableton_index")
                        mute = inv_params.get("mute")
                        if t_idx is not None and mute is not None:
                            adapter.set_track_mute(t_idx, mute)

                    elif inv_type == "set_tempo":
                        tempo = inv_params.get("tempo")
                        if tempo is not None:
                            adapter.set_tempo(tempo)

                    elif inv_type == "delete_clip":
                        t_idx = inv_params.get("ableton_index")
                        slot_idx = inv_params.get("slot_index")
                        if t_idx is not None and slot_idx is not None:
                            adapter.delete_clip(t_idx, slot_idx)

                    elif inv_type == "restore_notes":
                        t_idx = inv_params.get("ableton_index")
                        slot_idx = inv_params.get("clip_index")
                        prev_notes = inv_params.get("previous_notes", [])
                        if t_idx is not None and slot_idx is not None:
                            adapter.delete_clip(t_idx, slot_idx)
                            if prev_notes:
                                adapter.create_clip(t_idx, slot_idx, length=16.0)
                                adapter.add_notes_to_clip(t_idx, slot_idx, prev_notes)

                # 2. Reverse on Shadow Graph
                if inv_type == "delete_track":
                    tr_id = inv_params.get("track_id") or op.target_id
                    if tr_id and tr_id in graph.tracks:
                        del graph.tracks[tr_id]

                elif inv_type == "set_volume":
                    tr_id = inv_params.get("track_id") or op.target_id
                    if tr_id and tr_id in graph.tracks:
                        graph.tracks[tr_id].volume = inv_params["volume"]

                elif inv_type == "set_panning":
                    tr_id = inv_params.get("track_id") or op.target_id
                    if tr_id and tr_id in graph.tracks:
                        graph.tracks[tr_id].panning = inv_params["panning"]

                elif inv_type == "set_mute":
                    tr_id = inv_params.get("track_id") or op.target_id
                    if tr_id and tr_id in graph.tracks:
                        graph.tracks[tr_id].mute = inv_params["mute"]

                elif inv_type == "set_role":
                    tr_id = inv_params.get("track_id") or op.target_id
                    if tr_id and tr_id in graph.tracks:
                        graph.tracks[tr_id].metadata.role = inv_params.get("role")

                elif inv_type == "set_tempo":
                    graph.project_state.tempo = inv_params["tempo"]

                reversed_ops.append(op.id)
                event_logger.log_event(
                    operation=f"rollback_{op.op_type}",
                    transaction_id=transaction.id,
                    target_id=op.target_id,
                    status="success"
                )

            except Exception as e:
                errors.append(f"Failed to reverse op {op.id} ({inv_type}): {str(e)}")

        # If logical rollback had errors, fallback to Level 2: Snapshot Rollback
        if errors and transaction.snapshot_id:
            try:
                snapshot_manager.restore_snapshot(transaction.snapshot_id, graph)
                event_logger.log_event(
                    operation="snapshot_rollback_fallback",
                    transaction_id=transaction.id,
                    details={"snapshot_id": transaction.snapshot_id},
                    status="success"
                )
                return {
                    "method": "snapshot_fallback",
                    "snapshot_id": transaction.snapshot_id,
                    "reversed_operations_count": len(reversed_ops),
                    "success": True
                }
            except Exception as e:
                raise RollbackFailedError(f"Both logical rollback and snapshot rollback failed: {str(e)}", {
                    "logical_errors": errors,
                    "snapshot_error": str(e)
                })

        if errors:
            raise RollbackFailedError(f"Logical rollback encountered errors: {'; '.join(errors)}", {
                "errors": errors
            })

        graph.increment_version()
        return {
            "method": "logical_wal",
            "reversed_operations_count": len(reversed_ops),
            "reversed_operations": reversed_ops,
            "success": True
        }

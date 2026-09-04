# engine/transactions/validator.py
from typing import Dict, Any, List
from ..models import Transaction, Operation, TransactionStatus
from ..session.graph import SessionShadowGraph
from ..errors import (
    ObjectNotFoundError, ObjectLockedError, InvalidParameterError,
    TransactionLimitExceededError, TransactionConflictError
)
from ..config import config

class TransactionValidator:
    """Pre-commit validation engine enforcing graph consistency, locks, parameter bounds and limits"""
    @staticmethod
    def validate(transaction: Transaction, graph: SessionShadowGraph) -> bool:
        # 1. Check status
        if transaction.status != TransactionStatus.OPEN.value:
            raise InvalidParameterError(f"Transaction {transaction.id} is not OPEN (status: {transaction.status})")

        # 2. Check operation limit
        if len(transaction.operations) > config.MAX_OPERATIONS_PER_TRANSACTION:
            raise TransactionLimitExceededError(
                f"Transaction exceeded maximum operations ({len(transaction.operations)} > {config.MAX_OPERATIONS_PER_TRANSACTION})",
                {"limit": config.MAX_OPERATIONS_PER_TRANSACTION, "actual": len(transaction.operations)}
            )

        # 3. Check track creation limit
        tracks_created = sum(1 for op in transaction.operations if op.op_type == "create_track")
        if tracks_created > config.MAX_TRACKS_CREATED_PER_TRANSACTION:
            raise TransactionLimitExceededError(
                f"Transaction exceeded track creation limit ({tracks_created} > {config.MAX_TRACKS_CREATED_PER_TRANSACTION})",
                {"limit": config.MAX_TRACKS_CREATED_PER_TRANSACTION, "actual": tracks_created}
            )

        # 4. Check each operation
        for op in transaction.operations:
            # Check target locks
            if op.target_id:
                track = graph.get_track(op.target_id)
                if track and track.metadata.locked:
                    raise ObjectLockedError(
                        f"Target object '{track.name}' ({op.target_id}) is locked. Reason: {track.metadata.lock_reason}",
                        {"object_id": op.target_id, "lock_reason": track.metadata.lock_reason}
                    )

            # Check parameter bounds
            if op.op_type == "set_volume":
                vol = float(op.parameters.get("volume", 0.85))
                if vol < 0.0 or vol > 1.0:
                    raise InvalidParameterError(f"Volume {vol} is outside valid range [0.0, 1.0]")

            elif op.op_type == "set_panning":
                pan = float(op.parameters.get("panning", 0.0))
                if pan < -1.0 or pan > 1.0:
                    raise InvalidParameterError(f"Panning {pan} is outside valid range [-1.0, 1.0]")

            elif op.op_type == "set_tempo":
                tempo = float(op.parameters.get("tempo", 120.0))
                if tempo < 20.0 or tempo > 999.0:
                    raise InvalidParameterError(f"Tempo {tempo} is outside valid range [20.0, 999.0]")

        return True

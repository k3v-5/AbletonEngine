# engine/models/transactions.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import datetime

class TransactionStatus(str, Enum):
    OPEN = "OPEN"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"

@dataclass
class Operation:
    id: str
    op_type: str
    target_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    inverse_op: Optional[Dict[str, Any]] = None  # Compensating operation for WAL logical rollback
    is_reversible: bool = True
    executed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "op_type": self.op_type,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "inverse_op": self.inverse_op,
            "is_reversible": self.is_reversible,
            "executed": self.executed,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            op_type=data["op_type"],
            target_id=data.get("target_id"),
            parameters=data.get("parameters", {}),
            inverse_op=data.get("inverse_op"),
            is_reversible=data.get("is_reversible", True),
            executed=data.get("executed", False),
            timestamp=data.get("timestamp", "")
        )

@dataclass
class Transaction:
    id: str
    name: str = ""
    description: str = ""
    status: str = TransactionStatus.OPEN.value
    started_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    completed_at: Optional[str] = None
    base_version: int = 1
    snapshot_id: Optional[str] = None
    operations: List[Operation] = field(default_factory=list)
    is_reversible: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "base_version": self.base_version,
            "snapshot_id": self.snapshot_id,
            "operations": [op.to_dict() for op in self.operations],
            "is_reversible": self.is_reversible,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: dict):
        tx = cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", TransactionStatus.OPEN.value),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at"),
            base_version=data.get("base_version", 1),
            snapshot_id=data.get("snapshot_id"),
            is_reversible=data.get("is_reversible", True),
            error_message=data.get("error_message")
        )
        tx.operations = [Operation.from_dict(op) for op in data.get("operations", [])]
        return tx

@dataclass
class DiffReport:
    added: List[Dict[str, Any]] = field(default_factory=list)
    removed: List[Dict[str, Any]] = field(default_factory=list)
    modified: List[Dict[str, Any]] = field(default_factory=list)
    moved: List[Dict[str, Any]] = field(default_factory=list)
    renamed: List[Dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.modified or self.moved or self.renamed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_changes": not self.is_empty(),
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "moved": self.moved,
            "renamed": self.renamed
        }

@dataclass
class Snapshot:
    id: str
    name: str = ""
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    version: int = 1
    project_state: Dict[str, Any] = field(default_factory=dict)
    tracks: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "timestamp": self.timestamp,
            "version": self.version,
            "project_state": self.project_state,
            "tracks": self.tracks,
            "sections": self.sections
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", 1),
            project_state=data.get("project_state", {}),
            tracks=data.get("tracks", {}),
            sections=data.get("sections", {})
        )

# engine/errors.py
from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(str, Enum):
    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    AMBIGUOUS_OBJECT = "AMBIGUOUS_OBJECT"
    OBJECT_LOCKED = "OBJECT_LOCKED"
    SESSION_DESYNCHRONIZED = "SESSION_DESYNCHRONIZED"
    TRANSACTION_CONFLICT = "TRANSACTION_CONFLICT"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_RELATIONSHIP = "INVALID_RELATIONSHIP"
    SNAPSHOT_NOT_FOUND = "SNAPSHOT_NOT_FOUND"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    ABLETON_CONNECTION_ERROR = "ABLETON_CONNECTION_ERROR"
    REMOTE_SCRIPT_ERROR = "REMOTE_SCRIPT_ERROR"
    TRANSACTION_LIMIT_EXCEEDED = "TRANSACTION_LIMIT_EXCEEDED"

class EngineError(Exception):
    """Base exception class for all Engine operations with structured error payload"""
    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details
        }

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"

class ObjectNotFoundError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.OBJECT_NOT_FOUND, message, details)

class AmbiguousObjectError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.AMBIGUOUS_OBJECT, message, details)

class ObjectLockedError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.OBJECT_LOCKED, message, details)

class SessionDesynchronizedError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.SESSION_DESYNCHRONIZED, message, details)

class TransactionConflictError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.TRANSACTION_CONFLICT, message, details)

class TransactionFailedError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.TRANSACTION_FAILED, message, details)

class RollbackFailedError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.ROLLBACK_FAILED, message, details)

class InvalidParameterError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INVALID_PARAMETER, message, details)

class InvalidRelationshipError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INVALID_RELATIONSHIP, message, details)

class SnapshotNotFoundError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.SNAPSHOT_NOT_FOUND, message, details)

class UnsupportedOperationError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.UNSUPPORTED_OPERATION, message, details)

class AbletonConnectionError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.ABLETON_CONNECTION_ERROR, message, details)

class RemoteScriptError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.REMOTE_SCRIPT_ERROR, message, details)

class TransactionLimitExceededError(EngineError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.TRANSACTION_LIMIT_EXCEEDED, message, details)

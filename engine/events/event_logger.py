# engine/events/event_logger.py
import json
import os
import datetime
from typing import Optional, Dict, Any, List
from ..config import config

class EventLogger:
    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or config.EVENTS_DIR
        os.makedirs(self.log_dir, exist_ok=True)
        self.in_memory_events: List[Dict[str, Any]] = []

    def log_event(
        self,
        operation: str,
        transaction_id: Optional[str] = None,
        target_id: Optional[str] = None,
        before: Any = None,
        after: Any = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "transaction_id": transaction_id,
            "operation": operation,
            "target": target_id,
            "before": before,
            "after": after,
            "status": status,
            "details": details or {}
        }
        self.in_memory_events.append(event)
        
        # Persist event to daily log file
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"events_{today}.jsonl")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass  # Fallback to in-memory only if disk write fails
            
        return event

    def get_events_for_transaction(self, transaction_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.in_memory_events if e.get("transaction_id") == transaction_id]

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.in_memory_events[-limit:]

# Global event logger instance
event_logger = EventLogger()

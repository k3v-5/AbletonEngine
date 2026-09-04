# engine/persistence/storage.py
import json
import os
import shutil
from typing import Optional, Dict, Any, List
from ..config import config

class StorageManager:
    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = state_dir or config.STATE_DIR
        self.snapshots_dir = os.path.join(self.state_dir, "snapshots")
        self.transactions_dir = os.path.join(self.state_dir, "transactions")
        self.graph_file = os.path.join(self.state_dir, "session_graph.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)
        os.makedirs(self.transactions_dir, exist_ok=True)

    # Session Graph persistence
    def save_graph(self, graph_data: Dict[str, Any]) -> bool:
        self._ensure_dirs()
        temp_file = f"{self.graph_file}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2)
            shutil.move(temp_file, self.graph_file)
            return True
        except Exception:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

    def load_graph(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.graph_file):
            return None
        try:
            with open(self.graph_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # Snapshot persistence
    def save_snapshot(self, snapshot_id: str, snapshot_data: Dict[str, Any]) -> bool:
        self._ensure_dirs()
        path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2)
            return True
        except Exception:
            return False

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def list_snapshots(self) -> List[Dict[str, Any]]:
        self._ensure_dirs()
        snapshots = []
        for filename in sorted(os.listdir(self.snapshots_dir), reverse=True):
            if filename.endswith(".json"):
                path = os.path.join(self.snapshots_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        snapshots.append({
                            "id": data.get("id", filename[:-5]),
                            "name": data.get("name", ""),
                            "timestamp": data.get("timestamp", ""),
                            "version": data.get("version", 1)
                        })
                except Exception:
                    continue
        return snapshots

    # Transaction persistence
    def save_transaction(self, tx_id: str, tx_data: Dict[str, Any]) -> bool:
        self._ensure_dirs()
        path = os.path.join(self.transactions_dir, f"{tx_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tx_data, f, indent=2)
            return True
        except Exception:
            return False

    def load_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.transactions_dir, f"{tx_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def list_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        self._ensure_dirs()
        txs = []
        for filename in sorted(os.listdir(self.transactions_dir), reverse=True):
            if filename.endswith(".json"):
                path = os.path.join(self.transactions_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        txs.append({
                            "id": data.get("id", filename[:-5]),
                            "name": data.get("name", ""),
                            "status": data.get("status", ""),
                            "started_at": data.get("started_at", ""),
                            "operations_count": len(data.get("operations", []))
                        })
                        if len(txs) >= limit:
                            break
                except Exception:
                    continue
        return txs

storage = StorageManager()

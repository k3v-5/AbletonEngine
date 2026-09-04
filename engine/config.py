# engine/config.py
import os
from dataclasses import dataclass

@dataclass
class EngineConfig:
    # Storage and State Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATE_DIR: str = os.path.join(BASE_DIR, "state")
    SNAPSHOTS_DIR: str = os.path.join(STATE_DIR, "snapshots")
    TRANSACTIONS_DIR: str = os.path.join(STATE_DIR, "transactions")
    EVENTS_DIR: str = os.path.join(STATE_DIR, "events")
    GRAPH_FILE: str = os.path.join(STATE_DIR, "session_graph.json")

    # Safety limits per transaction
    MAX_OPERATIONS_PER_TRANSACTION: int = 500
    MAX_TRACKS_CREATED_PER_TRANSACTION: int = 20
    MAX_CLIPS_CREATED_PER_TRANSACTION: int = 50
    MAX_DEVICES_MODIFIED_PER_TRANSACTION: int = 100

    # Auto-snapshot before every transaction
    AUTO_SNAPSHOT_ON_BEGIN: bool = True

    # Socket connection
    ABLETON_HOST: str = os.environ.get("ABLETON_HOST", "localhost")
    ABLETON_PORT: int = int(os.environ.get("ABLETON_PORT", "9877"))

    def ensure_directories(self):
        for path in [self.STATE_DIR, self.SNAPSHOTS_DIR, self.TRANSACTIONS_DIR, self.EVENTS_DIR]:
            os.makedirs(path, exist_ok=True)

config = EngineConfig()
config.ensure_directories()

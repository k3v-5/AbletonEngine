# engine/production/contract/__init__.py
"""
SongContract Suite:
Cross-phase obligations ledger, tripartite evidence verification, creative continuity memory,
and omission audit gatekeeper.
"""
from .song_contract import (
    SongContract,
    TripartiteObligation,
    ObligationCategory,
    ObligationStatus,
)
from .song_intent_memory import (
    SongIntentMemory,
    EmotionalAxis,
    SonicThesis,
)
from .evidence_ledger import EvidenceLedger
from .omission_audit import (
    OmissionAuditor,
    OmissionReport,
)

__all__ = [
    "SongContract",
    "TripartiteObligation",
    "ObligationCategory",
    "ObligationStatus",
    "SongIntentMemory",
    "EmotionalAxis",
    "SonicThesis",
    "EvidenceLedger",
    "OmissionAuditor",
    "OmissionReport",
]

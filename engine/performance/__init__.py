# engine/performance/__init__.py
"""
Performance & Humanization Engine (Nivel T):
Music-theoretically intentional, correlated, and closed-loop performance modeling.

Architecture:
- T1: PerformanceCore (microtiming, velocity hierarchy, chord strumming, articulation, snapshots)
- T2: GrooveMemory & CorrelatedHumanizer (inter-instrument coupling, anchors, collective emergent pocket)
- T3: PhraseBreathingEngine (morphological phrase analysis, arrival target weight, breath gaps)
- T4: PerformanceIdentity (cryptographic interpretive fingerprints across catalog songs)
- T5: PerformanceClosedLoopAdapter (S <-> T mechanical fatigue detection, multi-candidate audition, 0 ms rollback)
"""

from .models import (
    PocketTendency,
    VelocityProfile,
    ArticulationStyle,
    PerformanceIntent,
    InstrumentPerformanceProfile,
    PerformanceSnapshot,
    PerformanceMutation,
)
from .core import PerformanceCore
from .groove_intelligence import (
    SongGrooveTemplate,
    GrooveMemory,
    CorrelatedHumanizer,
)
from .phrase_breathing import (
    PhraseSegment,
    PhraseBreathingEngine,
)
from .identity import (
    PerformanceSignature,
    PerformanceIdentityEngine,
)
from .closed_loop_adapter import PerformanceClosedLoopAdapter

__all__ = [
    "PocketTendency",
    "VelocityProfile",
    "ArticulationStyle",
    "PerformanceIntent",
    "InstrumentPerformanceProfile",
    "PerformanceSnapshot",
    "PerformanceMutation",
    "PerformanceCore",
    "SongGrooveTemplate",
    "GrooveMemory",
    "CorrelatedHumanizer",
    "PhraseSegment",
    "PhraseBreathingEngine",
    "PerformanceSignature",
    "PerformanceIdentityEngine",
    "PerformanceClosedLoopAdapter",
]

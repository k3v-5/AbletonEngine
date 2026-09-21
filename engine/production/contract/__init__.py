# engine/production/contract/__init__.py
"""
SongContract Suite:
Cross-phase obligations ledger, tripartite evidence verification, creative continuity memory,
omission audit gatekeeper, creative decision ledger, creative X-ray,
performance character (Level E), interaction consequence (Level F), and musical narrative memory.
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
from .creative_decision_ledger import (
    CreativeDecisionLedger,
    CreativeDecisionRecord,
    DecisionVerdict,
)
from .performance_character import (
    TimingIntention,
    VelocityExpression,
    ChordArticulation,
    PhraseEvolution,
    ConversationalRole,
    TimingMethodologyAudit,
    TrackPerformanceProfile,
    PerformanceCharacterReport,
    PerformanceAuditor,
)
from .interaction_audit import (
    InteractionPosture,
    SpaceYieldingDiagnostic,
    RhythmicInterlockingDiagnostic,
    SectionalReactionDiagnostic,
    InteractionConsequenceReport,
    InteractionAuditor,
)
from .musical_memory import (
    NarrativeMilestone,
    MusicalMemory,
)
from .creative_intervention import (
    CreativeProposal,
    CreativeProposalEngine,
    InterventionExecutor,
)
from .creative_xray import CreativeXRay
from .sonic_identity import (
    SoundDesignRole,
    SonicIdentityBudget,
    SonicObject,
    SonicIdentityAudit,
    SonicIdentityAuditReport,
)
from .sound_design_engine import (
    DestructionArchetype,
    SoundDesignStep,
    SoundDesignChain,
    SoundDesignEngine,
)
from .resampling_engine import (
    MutationBranch,
    MaterialMutation,
    MutationFilter,
    RecursiveResamplingEngine,
)
from .sonic_memory import (
    SonicLifeStage,
    SonicOccurrence,
    SonicObjectGenealogy,
    SonicMemory,
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
    "CreativeDecisionLedger",
    "CreativeDecisionRecord",
    "DecisionVerdict",
    "TimingIntention",
    "VelocityExpression",
    "ChordArticulation",
    "PhraseEvolution",
    "ConversationalRole",
    "TimingMethodologyAudit",
    "TrackPerformanceProfile",
    "PerformanceCharacterReport",
    "PerformanceAuditor",
    "InteractionPosture",
    "SpaceYieldingDiagnostic",
    "RhythmicInterlockingDiagnostic",
    "SectionalReactionDiagnostic",
    "InteractionConsequenceReport",
    "InteractionAuditor",
    "NarrativeMilestone",
    "MusicalMemory",
    "CreativeProposal",
    "CreativeProposalEngine",
    "InterventionExecutor",
    "CreativeXRay",
    "SoundDesignRole",
    "SonicIdentityBudget",
    "SonicObject",
    "SonicIdentityAudit",
    "SonicIdentityAuditReport",
    "DestructionArchetype",
    "SoundDesignStep",
    "SoundDesignChain",
    "SoundDesignEngine",
    "MutationBranch",
    "MaterialMutation",
    "MutationFilter",
    "RecursiveResamplingEngine",
    "SonicLifeStage",
    "SonicOccurrence",
    "SonicObjectGenealogy",
    "SonicMemory",
]

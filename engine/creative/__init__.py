# engine/creative/__init__.py
"""
Phase 1 Creative Direction & Song DNA Package.
"""

from .models import (
    SongCreativeDNA,
    SonicWorld,
    AestheticMood,
    ReferenceProfile,
    SpectralTargetBand,
    HarmonicDNA,
    ModalFlavor,
    TrackRoleAllocation,
    ArrangementBlueprint,
    ArrangementSectionBlueprint
)
from .dna_engine import CreativeDirectionEngine
from .music_dna import (
    MusicDNA,
    MusicDNAIdentity,
    MusicDNARhythm,
    MusicDNAHarmony,
    MusicDNAMelody,
    MusicDNAStructure,
    MusicDNASoundIdentity,
    MusicDNANovelty
)
from .leitmotif_engine import Leitmotif, LeitmotifEngine
from .cliche_detector import ClicheDetector, ClicheAuditReport
from .generative_taste_engine import (
    GenerativeTasteEngine,
    CandidateType,
    TasteScoreCard,
    ArtisticCandidate,
    AuditionDecision
)
from .artistic_intent import ArtisticIntent, EmotionalJourney
from .artistic_critic import (
    CriticDimension,
    VetoSeverity,
    CriticScore,
    CriticVerdict,
    IdentityCritic,
    MemorabilityCritic,
    PredictabilityCritic,
    EmotionalCritic,
    HumanPlausibilityCritic,
    SonicSignatureCritic,
    CulturalGenrePlausibilityCritic,
    ArtisticCriticEngine,
)
from .selection_loop import TasteAndSelectionLoop, CandidateProposal, SelectionResult
from .identity_stress_test import IdentityStressTest, IdentityStressTestReport, SongArchetypeResult
from .contextual_sonic_critic import (
    ContextualDimension,
    ContextualVerdict,
    AudioSectionAcousticSnapshot,
    ContextualAcousticDeltas,
    ContextualAuditReport,
    ContextualSonicCritic,
)
from .evolution import (
    InterventionDomain,
    InterventionType,
    EvolutionBudget,
    EvolutionSnapshot,
    InterventionOrder,
    EvolutionResult,
    InterventionPlanner,
    EvolutionGovernanceGuard,
    GovernanceVetoError,
    MultiDomainInterventionRouter,
    EvolutionLedger,
    ClosedLoopCreativeEvolutionEngine,
)

__all__ = [
    "SongCreativeDNA",
    "SonicWorld",
    "AestheticMood",
    "ReferenceProfile",
    "SpectralTargetBand",
    "HarmonicDNA",
    "ModalFlavor",
    "TrackRoleAllocation",
    "ArrangementBlueprint",
    "ArrangementSectionBlueprint",
    "CreativeDirectionEngine",
    "MusicDNA",
    "MusicDNAIdentity",
    "MusicDNARhythm",
    "MusicDNAHarmony",
    "MusicDNAMelody",
    "MusicDNAStructure",
    "MusicDNASoundIdentity",
    "MusicDNANovelty",
    "Leitmotif",
    "LeitmotifEngine",
    "ClicheDetector",
    "ClicheAuditReport",
    "GenerativeTasteEngine",
    "CandidateType",
    "TasteScoreCard",
    "ArtisticCandidate",
    "AuditionDecision",
    "ArtisticIntent",
    "EmotionalJourney",
    "CriticDimension",
    "VetoSeverity",
    "CriticScore",
    "CriticVerdict",
    "IdentityCritic",
    "MemorabilityCritic",
    "PredictabilityCritic",
    "EmotionalCritic",
    "HumanPlausibilityCritic",
    "SonicSignatureCritic",
    "CulturalGenrePlausibilityCritic",
    "ArtisticCriticEngine",
    "TasteAndSelectionLoop",
    "CandidateProposal",
    "SelectionResult",
    "IdentityStressTest",
    "IdentityStressTestReport",
    "SongArchetypeResult",
    "ContextualDimension",
    "ContextualVerdict",
    "AudioSectionAcousticSnapshot",
    "ContextualAcousticDeltas",
    "ContextualAuditReport",
    "ContextualSonicCritic",
    "InterventionDomain",
    "InterventionType",
    "EvolutionBudget",
    "EvolutionSnapshot",
    "InterventionOrder",
    "EvolutionResult",
    "InterventionPlanner",
    "EvolutionGovernanceGuard",
    "GovernanceVetoError",
    "MultiDomainInterventionRouter",
    "EvolutionLedger",
    "ClosedLoopCreativeEvolutionEngine",
]



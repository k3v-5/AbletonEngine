# engine/audio_genesis/__init__.py
"""
Audio Genesis & Provenance Subsystem:
Implements strict audio provenance and closed-loop autogenous sound synthesis.
"""

from .provenance import (
    SampleOrigin,
    CreativeUsagePolicy,
    CreativeGovernanceError,
    AudioSourceLocation,
    InstrumentProvenance,
    ProcessingStep,
    RenderMetadata,
    SampleProvenanceRecord,
    GenealogicalNode,
    AudioGenealogyTree,
    AudioProvenanceEngine,
)

from .render_engine import (
    RenderRequest,
    RenderResult,
    RenderToAudioEngine,
)

from .mutation_engine import (
    GenesisPipelineType,
    SampleMutationResult,
    SampleMutationEngine,
)

from .instrument_builder import (
    TargetInstrumentDestination,
    InstrumentBuildPlan,
    InstrumentBuildResult,
    SampleInstrumentBuilder,
)

from .audio_genesis_engine import (
    GenesisSoundResult,
    AudioGenesisEngine,
)

from .sonic_recursion import (
    RecursiveTargetRole,
    DistanceCategory,
    SonicFamily,
    SonicFamilyRegistry,
    SeedMusicalSignificance,
    PerceptualDistanceAuditor,
    RoleDependentMutator,
    GenerationDepthGuard,
)

from .self_sampling_engine import (
    EmergentSoundCandidate,
    EmergentProposalBatch,
    SelfSamplingEngine,
)

__all__ = [
    # Provenance
    "SampleOrigin",
    "CreativeUsagePolicy",
    "CreativeGovernanceError",
    "AudioSourceLocation",
    "InstrumentProvenance",
    "ProcessingStep",
    "RenderMetadata",
    "SampleProvenanceRecord",
    "GenealogicalNode",
    "AudioGenealogyTree",
    "AudioProvenanceEngine",
    # Render
    "RenderRequest",
    "RenderResult",
    "RenderToAudioEngine",
    # Mutation
    "GenesisPipelineType",
    "SampleMutationResult",
    "SampleMutationEngine",
    # Instrument
    "TargetInstrumentDestination",
    "InstrumentBuildPlan",
    "InstrumentBuildResult",
    "SampleInstrumentBuilder",
    # Master
    "GenesisSoundResult",
    "AudioGenesisEngine",
    # Sonic Recursion & Self-Sampling
    "RecursiveTargetRole",
    "DistanceCategory",
    "SonicFamily",
    "SonicFamilyRegistry",
    "SeedMusicalSignificance",
    "PerceptualDistanceAuditor",
    "RoleDependentMutator",
    "GenerationDepthGuard",
    "EmergentSoundCandidate",
    "EmergentProposalBatch",
    "SelfSamplingEngine",
]


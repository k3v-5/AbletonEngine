# engine/sound_design/__init__.py
"""
Sound Design System & Autonomous Sonic Identity (Level H - Gen 2):
Comprehensive framework spanning the 18 production technique families,
Sonic DNA extraction, Resynthesis Engine with Destruction Pass,
Frankenstein 2.0 autogenous composites, Signature Sound Generator (1-3 sounds),
Contrast Engine (8 polarities), Producer Taste Model (7 axes),
and the 10-point Sonic Identity Audit.
"""
from .technique_catalog import (
    ProductionTechniqueFamily,
    DeviceRecipe,
    TechniqueDefinition,
    TechniqueCatalog,
)
from .spatial_narrative import (
    SpatialPoint,
    SpatialNarrativePlan,
    SpatialNarrativeEngine,
)
from .transient_sculptor import (
    EnvelopeZone,
    ZoneSculptConfig,
    TransientSculptProfile,
    TransientSculptor,
)
from .frankenstein_engine import (
    ComponentRole,
    FrankensteinLayer,
    FrankensteinComposite,
    FrankensteinEngine,
)
from .ear_candy_engine import (
    EarCandyType,
    EarCandyOpportunity,
    EarCandyEngine,
)
from .sonic_mutation_lab import (
    MutationCandidate,
    SonicMutationLab,
)
from .sonic_dna import (
    HarmonicDNA,
    RhythmicDNA,
    TimbralDNA,
    TextureDNA,
    SpatialDNA,
    MotifFingerprint,
    SonicDNA,
)
from .resynthesis_engine import (
    ComponentBand,
    DestructionBranch,
    CandidateMoment,
    DecomposedComponent,
    DestructionVariant,
    FabricatedInstrument,
    ResynthesisEngine,
)
from .frankenstein_v2 import (
    AutogenousComponentSource,
    FrankensteinV2Object,
    FrankensteinV2Engine,
)
from .signature_sound_generator import (
    SignatureAppearance,
    SignatureSoundRecord,
    SignatureSoundRegistry,
)
from .contrast_engine import (
    ContrastPolarity,
    SectionPolarityState,
    ContrastEngine,
)
from .producer_taste_model import (
    TasteMetrics,
    ProducerTasteEvaluation,
    ProducerTasteModel,
)
from .sonic_identity_audit_v2 import (
    AuditPointResult,
    SonicIdentityAuditV2Report,
    SonicIdentityAuditV2,
)

__all__ = [
    "ProductionTechniqueFamily",
    "DeviceRecipe",
    "TechniqueDefinition",
    "TechniqueCatalog",
    "SpatialPoint",
    "SpatialNarrativePlan",
    "SpatialNarrativeEngine",
    "EnvelopeZone",
    "ZoneSculptConfig",
    "TransientSculptProfile",
    "TransientSculptor",
    "ComponentRole",
    "FrankensteinLayer",
    "FrankensteinComposite",
    "FrankensteinEngine",
    "EarCandyType",
    "EarCandyOpportunity",
    "EarCandyEngine",
    "MutationCandidate",
    "SonicMutationLab",
    "HarmonicDNA",
    "RhythmicDNA",
    "TimbralDNA",
    "TextureDNA",
    "SpatialDNA",
    "MotifFingerprint",
    "SonicDNA",
    "ComponentBand",
    "DestructionBranch",
    "CandidateMoment",
    "DecomposedComponent",
    "DestructionVariant",
    "FabricatedInstrument",
    "ResynthesisEngine",
    "AutogenousComponentSource",
    "FrankensteinV2Object",
    "FrankensteinV2Engine",
    "SignatureAppearance",
    "SignatureSoundRecord",
    "SignatureSoundRegistry",
    "ContrastPolarity",
    "SectionPolarityState",
    "ContrastEngine",
    "TasteMetrics",
    "ProducerTasteEvaluation",
    "ProducerTasteModel",
    "AuditPointResult",
    "SonicIdentityAuditV2Report",
    "SonicIdentityAuditV2",
]

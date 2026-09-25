# engine/fx/__init__.py
"""
Audio Effects, Role-Based Insert Chains, Parameter Supervision, and Channel Strip Engines.
"""

from .role_fx_catalog import (
    ROLE_INSERT_EFFECTS,
    ROLE_FREQUENCY_GUIDE,
    VALHALLA_VINTAGE_VERB_PARAMS,
)
from .device_parameter_supervisor import DeviceParameterSupervisor
from .track_fx_rack import TrackFXRack
from .aesthetic_profile_engine import (
    AestheticProfileEngine,
    AestheticGenreProfile,
    RoleFXProfile,
    InstrumentDecision,
)
from .ultra_acoustic_catalog import (
    UltraAcousticCatalog,
    AcousticArchetype,
    AcousticProfileSpec,
    EQBandSetting,
)
from .semantic_intent_resolver import (
    SemanticIntentResolver,
    ResolvedAcousticIntent,
)
from engine.core.device_execution_verifier import DeviceExecutionVerifier, VerificationError

__all__ = [
    "ROLE_INSERT_EFFECTS",
    "ROLE_FREQUENCY_GUIDE",
    "VALHALLA_VINTAGE_VERB_PARAMS",
    "DeviceParameterSupervisor",
    "TrackFXRack",
    "AestheticProfileEngine",
    "AestheticGenreProfile",
    "RoleFXProfile",
    "InstrumentDecision",
    "UltraAcousticCatalog",
    "AcousticArchetype",
    "AcousticProfileSpec",
    "EQBandSetting",
    "SemanticIntentResolver",
    "ResolvedAcousticIntent",
    "DeviceExecutionVerifier",
    "VerificationError",
]

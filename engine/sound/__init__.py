"""
Ableton Production Intelligence Engine - Fase 4: Sound Design & Production Engine.
Instruments, Drum Racks, Samples, Device Chains, Macros, and Adaptive Mix Context.
"""
from .profiles.models import SoundProfile
from .profiles.profiles import SOUND_PROFILES, get_sound_profile
from .parameters.semantic import SemanticParameter, UNIVERSAL_SEMANTIC_PARAMETERS
from .parameters.curves import ParameterCurve
from .parameters.mapper import ParameterMapper
from .intent import SoundIntent, SidechainIntent
from .context import MixContext, FrequencyBand, FrequencyRoleMap, AdaptiveAdvisor
from .chains.models import (
    SemanticDevice, DeviceChain,
    DEVICE_PRIMARY_INSTRUMENT, DEVICE_SATURATION, DEVICE_EQ,
    DEVICE_COMPRESSOR, DEVICE_REVERB, DEVICE_DELAY, DEVICE_UTILITY,
    DEVICE_SIDECHAIN, DEVICE_CHORUS, DEVICE_DRUM_BUSS
)
from .chains.templates import CHAIN_TEMPLATES, get_chain_template
from .chains.builder import ChainBuilder
from .capabilities.registry import CapabilityRegistry
from .capabilities.discovery import CapabilityDiscovery
from .capabilities.cache import DeviceCapabilityCache
from .presets.scoring import PresetScoringEngine
from .presets.resolver import PresetResolver
from .drum_rack.models import SampleMetadata, DrumPadSpec, DrumRackSpec
from .drum_rack.resolver import DrumSoundResolver
from .drum_rack.verifier import DrumRackVerifier
from .drum_rack.engine import DrumRackEngine
from .macros.mappings import UNIVERSAL_MACROS, ROLE_MACRO_PROFILES
from .macros.system import MacroSystem
from .evolution import PatchIdentity, SoundEvolutionManager
from .snapshots.snapshots import SoundSnapshot, SoundSnapshotManager
from .linter import SoundLinter, SoundLintIssue
from .engine import SoundEngine

__all__ = [
    "SoundProfile", "SOUND_PROFILES", "get_sound_profile",
    "SemanticParameter", "UNIVERSAL_SEMANTIC_PARAMETERS",
    "ParameterCurve", "ParameterMapper",
    "SoundIntent", "SidechainIntent",
    "MixContext", "FrequencyBand", "FrequencyRoleMap", "AdaptiveAdvisor",
    "SemanticDevice", "DeviceChain",
    "DEVICE_PRIMARY_INSTRUMENT", "DEVICE_SATURATION", "DEVICE_EQ",
    "DEVICE_COMPRESSOR", "DEVICE_REVERB", "DEVICE_DELAY", "DEVICE_UTILITY",
    "DEVICE_SIDECHAIN", "DEVICE_CHORUS", "DEVICE_DRUM_BUSS",
    "CHAIN_TEMPLATES", "get_chain_template", "ChainBuilder",
    "CapabilityRegistry", "CapabilityDiscovery", "DeviceCapabilityCache",
    "PresetScoringEngine", "PresetResolver",
    "SampleMetadata", "DrumPadSpec", "DrumRackSpec",
    "DrumSoundResolver", "DrumRackVerifier", "DrumRackEngine",
    "UNIVERSAL_MACROS", "ROLE_MACRO_PROFILES", "MacroSystem",
    "PatchIdentity", "SoundEvolutionManager",
    "SoundSnapshot", "SoundSnapshotManager",
    "SoundLinter", "SoundLintIssue",
    "SoundEngine"
]

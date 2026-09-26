# engine/sound_design/decent_sampler/__init__.py
"""
Decent Sampler Instrument Compiler & Engine.

A clean, multi-layered architecture for assembling, validating, and compiling
production-grade multi-sampled instruments (.dspreset) for Decent Sampler.

Architecture:
- Level 1: XML Specification & Canonical Schema (schema.py)
- Level 2: Structural Consistency & Intermediate Domain Model (model.py)
- Level 3: Audio Safety Policies & Resource Heuristics (policies.py)
- Sample Asset Planning: SampleMapPlanner & Audio Metadata (sample_mapper.py, sample_analyzer.py)
- Validation & Sanitization: 3-Tier Auditor & Resilient Fixer (validator.py, sanitizer.py)
- Serialization & Round-Trip: Deterministic XML Engine (serializer.py)
- High-Level API: Instrument Compiler (builder.py)
"""

from .schema import DecentSamplerSchema
from .model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ModulatorModel,
    BindingModel,
    UIModel,
    ControlModel,
)
from .policies import AudioSafetyPolicy, ResourcePolicy
from .sample_mapper import SampleMapPlanner, PlannedZone, PlannedLayer
from .validator import DecentSamplerValidator, ValidationReport, ValidationError
from .sanitizer import DecentSamplerSanitizer
from .serializer import DSPresetSerializer
from .builder import DecentSamplerBuilder
from .completeness import InstrumentCompletenessAuditor, CompletenessReport, CompletenessIssue
from .library_manager import DecentSamplerLibraryManager, DecentSamplerLibraryInfo

__all__ = [
    "DecentSamplerSchema",
    "InstrumentModel",
    "GroupModel",
    "SampleZoneModel",
    "EffectModel",
    "ModulatorModel",
    "BindingModel",
    "UIModel",
    "ControlModel",
    "AudioSafetyPolicy",
    "ResourcePolicy",
    "SampleMapPlanner",
    "PlannedZone",
    "PlannedLayer",
    "DecentSamplerValidator",
    "ValidationReport",
    "ValidationError",
    "DecentSamplerSanitizer",
    "DSPresetSerializer",
    "DecentSamplerBuilder",
    "InstrumentCompletenessAuditor",
    "CompletenessReport",
    "CompletenessIssue",
    "DecentSamplerLibraryManager",
    "DecentSamplerLibraryInfo",
]



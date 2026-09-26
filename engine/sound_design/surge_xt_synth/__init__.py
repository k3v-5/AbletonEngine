# engine/sound_design/surge_xt_synth/__init__.py
"""
Surge XT Synthesizer Sound Design & Synthesis Module.
"""

from .schema import (
    SurgeXTSynthSchema,
    SurgeOscillatorType,
    SurgeFilterType,
    SurgeFilterSubtype,
    SurgeFilterConfig
)
from .model import (
    SurgeSynthPatchModel,
    SurgeSynthOscillatorModel,
    SurgeSynthFilterModel,
    SurgeSynthEnvelopeModel
)
from .validator import (
    SurgeSynthValidator,
    SurgeSynthValidationReport,
    SurgeSynthValidationError
)
from .sanitizer import SurgeSynthSanitizer
from .serializer import SurgeSynthSerializer
from .patch_factory import SurgeSynthPatchFactory

__all__ = [
    "SurgeXTSynthSchema",
    "SurgeOscillatorType",
    "SurgeFilterType",
    "SurgeFilterSubtype",
    "SurgeFilterConfig",
    "SurgeSynthPatchModel",
    "SurgeSynthOscillatorModel",
    "SurgeSynthFilterModel",
    "SurgeSynthEnvelopeModel",
    "SurgeSynthValidator",
    "SurgeSynthValidationReport",
    "SurgeSynthValidationError",
    "SurgeSynthSanitizer",
    "SurgeSynthSerializer",
    "SurgeSynthPatchFactory",
]

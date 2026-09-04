"""
Audio Forensics Engine (PIE Phase 7).
Temporal, spectral, dynamic, and causal DSP diagnostic framework.
"""

from .exceptions import (
    ForensicsError,
    InvalidAudioError,
    InvalidAnalysisConfigError,
    UnsupportedSampleRateError,
    UnsupportedChannelLayoutError,
    UnsupportedWindowError,
    InsufficientAudioError,
    ForensicsPersistenceError,
    ForensicsIntegrityError,
)

from .models import (
    ForensicEventType,
    Severity,
    AnalysisConfig,
    AudioFrame,
    SpectralMeasurement,
    ForensicEvent,
    CausalHypothesis,
    TrackBaseline,
    ForensicReport,
)

from .config import (
    STANDARD_FREQUENCY_BANDS,
    DEFAULT_ANALYSIS_CONFIG,
    VOCAL_FORENSICS_CONFIG,
    LOW_END_FORENSICS_CONFIG,
)

from .stft import STFTEngine
from .temporal import TemporalEngine
from .spectral import SpectralEngine
from .clipping import ClippingEngine
from .anomalies import AnomalyEngine
from .masking import MaskingEngine
from .correlation import CorrelationEngine
from .baseline import BaselineEngine
from .causality import CausalityEngine
from .report import ForensicReportGenerator
from .serializer import ForensicsStorage
from .analyzer import AudioForensicsEngine

__all__ = [
    # Exceptions
    "ForensicsError",
    "InvalidAudioError",
    "InvalidAnalysisConfigError",
    "UnsupportedSampleRateError",
    "UnsupportedChannelLayoutError",
    "UnsupportedWindowError",
    "InsufficientAudioError",
    "ForensicsPersistenceError",
    "ForensicsIntegrityError",
    # Models & Enums
    "ForensicEventType",
    "Severity",
    "AnalysisConfig",
    "AudioFrame",
    "SpectralMeasurement",
    "ForensicEvent",
    "CausalHypothesis",
    "TrackBaseline",
    "ForensicReport",
    # Config & Presets
    "STANDARD_FREQUENCY_BANDS",
    "DEFAULT_ANALYSIS_CONFIG",
    "VOCAL_FORENSICS_CONFIG",
    "LOW_END_FORENSICS_CONFIG",
    # Sub-engines
    "STFTEngine",
    "TemporalEngine",
    "SpectralEngine",
    "ClippingEngine",
    "AnomalyEngine",
    "MaskingEngine",
    "CorrelationEngine",
    "BaselineEngine",
    "CausalityEngine",
    "ForensicReportGenerator",
    "ForensicsStorage",
    # Master Facade
    "AudioForensicsEngine",
]

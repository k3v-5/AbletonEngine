"""
Canonical Domain Models for Audio Forensics Engine (PIE Phase 7).
Defines strictly typed, immutable contracts for temporal, spectral, dynamic,
and causal audio forensic diagnostics.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Mapping, Union
import math
import copy
import datetime

from .exceptions import (
    InvalidAnalysisConfigError,
    InvalidAudioError,
    ForensicsIntegrityError
)


class ForensicEventType(str, Enum):
    """Canonical classification of forensic audio anomalies and acoustic phenomena."""
    CLIPPING = "CLIPPING"
    INTER_SAMPLE_PEAK = "INTER_SAMPLE_PEAK"
    RESONANCE = "RESONANCE"
    SPECTRAL_ANOMALY = "SPECTRAL_ANOMALY"
    DROPOUT = "DROPOUT"
    CLICK = "CLICK"
    POP = "POP"
    SILENCE_ANOMALY = "SILENCE_ANOMALY"
    CHANNEL_LOSS = "CHANNEL_LOSS"
    DC_OFFSET = "DC_OFFSET"
    PHASE_ANOMALY = "PHASE_ANOMALY"
    MASKING = "MASKING"
    ENERGY_SPIKE = "ENERGY_SPIKE"
    ENERGY_DROP = "ENERGY_DROP"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    """Hierarchical severity levels for forensic events."""
    INFO = "INFO"          # Informative diagnostic
    WARNING = "WARNING"    # Potential mix or acoustic risk
    ERROR = "ERROR"        # Confirmed acoustic defect
    CRITICAL = "CRITICAL"  # Severe defect compromising delivery or headroom


@dataclass(frozen=True)
class AnalysisConfig:
    """
    Configuration parameters for forensic temporal/spectral audio analysis.
    Guarantees deterministic, reproducible analysis runs.
    """
    fft_size: int = 2048
    hop_size: int = 512
    window: str = "hann"
    min_frequency_hz: float = 20.0
    max_frequency_hz: float = 20000.0
    peak_threshold_db: float = -0.1
    resonance_threshold_db: float = 6.0
    minimum_event_duration_ms: float = 50.0
    maximum_event_gap_ms: float = 100.0
    correlation_threshold: float = 0.75
    clipping_threshold_dbfs: float = -0.01
    algorithm_version: str = "1.0.0"

    def __post_init__(self):
        if self.fft_size <= 0:
            raise InvalidAnalysisConfigError(f"fft_size must be positive, got {self.fft_size}")
        if self.hop_size <= 0:
            raise InvalidAnalysisConfigError(f"hop_size must be positive, got {self.hop_size}")
        if self.hop_size > self.fft_size:
            raise InvalidAnalysisConfigError(f"hop_size ({self.hop_size}) cannot exceed fft_size ({self.fft_size})")
        if self.min_frequency_hz < 0.0:
            raise InvalidAnalysisConfigError(f"min_frequency_hz must be >= 0, got {self.min_frequency_hz}")
        if self.max_frequency_hz <= self.min_frequency_hz:
            raise InvalidAnalysisConfigError(
                f"max_frequency_hz ({self.max_frequency_hz}) must be greater than min_frequency_hz ({self.min_frequency_hz})"
            )
        for threshold_name, val in [
            ("peak_threshold_db", self.peak_threshold_db),
            ("resonance_threshold_db", self.resonance_threshold_db),
            ("clipping_threshold_dbfs", self.clipping_threshold_dbfs),
        ]:
            if not math.isfinite(val):
                raise InvalidAnalysisConfigError(f"{threshold_name} must be finite, got {val}")
        if self.minimum_event_duration_ms <= 0.0:
            raise InvalidAnalysisConfigError(f"minimum_event_duration_ms must be > 0, got {self.minimum_event_duration_ms}")
        if not (-1.0 <= self.correlation_threshold <= 1.0):
            raise InvalidAnalysisConfigError(f"correlation_threshold must be between -1.0 and 1.0, got {self.correlation_threshold}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fft_size": self.fft_size,
            "hop_size": self.hop_size,
            "window": self.window,
            "min_frequency_hz": self.min_frequency_hz,
            "max_frequency_hz": self.max_frequency_hz,
            "peak_threshold_db": self.peak_threshold_db,
            "resonance_threshold_db": self.resonance_threshold_db,
            "minimum_event_duration_ms": self.minimum_event_duration_ms,
            "maximum_event_gap_ms": self.maximum_event_gap_ms,
            "correlation_threshold": self.correlation_threshold,
            "clipping_threshold_dbfs": self.clipping_threshold_dbfs,
            "algorithm_version": self.algorithm_version
        }


@dataclass(frozen=True)
class AudioFrame:
    """Represents a single time-windowed slice of analysis."""
    index: int
    start_sample: int
    end_sample: int
    start_time_seconds: float
    end_time_seconds: float
    rms_dbfs: float
    peak_dbfs: float
    spectral_centroid_hz: float
    spectral_flux: float

    def __post_init__(self):
        for name, val in [
            ("rms_dbfs", self.rms_dbfs),
            ("peak_dbfs", self.peak_dbfs),
            ("spectral_centroid_hz", self.spectral_centroid_hz),
            ("spectral_flux", self.spectral_flux),
            ("start_time_seconds", self.start_time_seconds),
            ("end_time_seconds", self.end_time_seconds),
        ]:
            if not math.isfinite(val):
                raise InvalidAudioError(f"AudioFrame field '{name}' must be finite, got {val}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "start_sample": self.start_sample,
            "end_sample": self.end_sample,
            "start_time_seconds": self.start_time_seconds,
            "end_time_seconds": self.end_time_seconds,
            "rms_dbfs": self.rms_dbfs,
            "peak_dbfs": self.peak_dbfs,
            "spectral_centroid_hz": self.spectral_centroid_hz,
            "spectral_flux": self.spectral_flux
        }


@dataclass(frozen=True)
class SpectralMeasurement:
    """Localized point measurement on the time-frequency plane."""
    timestamp_seconds: float
    frequency_hz: float
    magnitude_dbfs: float
    channel: str
    frame_index: int

    def __post_init__(self):
        if not math.isfinite(self.magnitude_dbfs):
            raise InvalidAudioError(f"magnitude_dbfs must be finite, got {self.magnitude_dbfs}")
        if self.frequency_hz < 0.0 or not math.isfinite(self.frequency_hz):
            raise InvalidAudioError(f"frequency_hz must be finite and >= 0, got {self.frequency_hz}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_seconds": self.timestamp_seconds,
            "frequency_hz": self.frequency_hz,
            "magnitude_dbfs": self.magnitude_dbfs,
            "channel": self.channel,
            "frame_index": self.frame_index
        }


@dataclass(frozen=True)
class ForensicEvent:
    """
    Principal record of a detected forensic acoustic event or anomaly.
    Correlates exact time span, affected frequencies, severity, and evidence pointers.
    """
    event_id: str
    event_type: str
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    severity: str
    confidence: float
    channels: Tuple[str, ...]
    frequency_min_hz: Optional[float] = None
    frequency_max_hz: Optional[float] = None
    evidence_ids: Tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id or not str(self.event_id).strip():
            raise ForensicsIntegrityError("event_id must be a non-empty string.")
        if not (0.0 <= self.confidence <= 1.0):
            raise ForensicsIntegrityError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.duration_seconds < 0.0 or not math.isfinite(self.duration_seconds):
            raise ForensicsIntegrityError(f"duration_seconds must be >= 0 and finite, got {self.duration_seconds}")

        # Normalize enum strings
        ev_type = self.event_type.value if isinstance(self.event_type, ForensicEventType) else str(self.event_type)
        object.__setattr__(self, "event_type", ev_type)

        sev = self.severity.value if isinstance(self.severity, Severity) else str(self.severity)
        object.__setattr__(self, "severity", sev)

        # Defensive copies
        object.__setattr__(self, "channels", tuple(self.channels))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        object.__setattr__(self, "details", copy.deepcopy(dict(self.details)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "start_time_seconds": round(self.start_time_seconds, 4),
            "end_time_seconds": round(self.end_time_seconds, 4),
            "duration_seconds": round(self.duration_seconds, 4),
            "severity": self.severity,
            "confidence": round(self.confidence, 4),
            "channels": list(self.channels),
            "frequency_min_hz": round(self.frequency_min_hz, 2) if self.frequency_min_hz is not None else None,
            "frequency_max_hz": round(self.frequency_max_hz, 2) if self.frequency_max_hz is not None else None,
            "evidence_ids": list(self.evidence_ids),
            "details": copy.deepcopy(dict(self.details))
        }


@dataclass(frozen=True)
class CausalHypothesis:
    """
    Hypothesis explaining the likely origin or source of a forensic phenomenon.
    Includes supporting evidence, competing alternative explanations, and confidence.
    """
    hypothesis_id: str
    likely_cause: str
    summary: str
    confidence: float
    observation_ids: Tuple[str, ...] = ()
    supporting_evidence: Tuple[str, ...] = ()
    competing_explanations: Tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.hypothesis_id or not str(self.hypothesis_id).strip():
            raise ForensicsIntegrityError("hypothesis_id must be a non-empty string.")
        if not (0.0 <= self.confidence <= 1.0):
            raise ForensicsIntegrityError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        object.__setattr__(self, "observation_ids", tuple(self.observation_ids))
        object.__setattr__(self, "supporting_evidence", tuple(self.supporting_evidence))
        object.__setattr__(self, "competing_explanations", tuple(self.competing_explanations))
        object.__setattr__(self, "details", copy.deepcopy(dict(self.details)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "likely_cause": self.likely_cause,
            "summary": self.summary,
            "confidence": round(self.confidence, 4),
            "observation_ids": list(self.observation_ids),
            "supporting_evidence": list(self.supporting_evidence),
            "competing_explanations": list(self.competing_explanations),
            "details": copy.deepcopy(dict(self.details))
        }


@dataclass(frozen=True)
class TrackBaseline:
    """
    Statistical distribution profile representing the baseline behavior of a specific signal.
    Prevents relying on arbitrary static thresholds by establishing dynamic context.
    """
    track_id: str
    rms_stats: Mapping[str, float] = field(default_factory=dict)
    peak_stats: Mapping[str, float] = field(default_factory=dict)
    centroid_stats: Mapping[str, float] = field(default_factory=dict)
    band_baselines: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    crest_factor_stats: Mapping[str, float] = field(default_factory=dict)
    stereo_correlation_stats: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "rms_stats", copy.deepcopy(dict(self.rms_stats)))
        object.__setattr__(self, "peak_stats", copy.deepcopy(dict(self.peak_stats)))
        object.__setattr__(self, "centroid_stats", copy.deepcopy(dict(self.centroid_stats)))
        object.__setattr__(self, "band_baselines", copy.deepcopy(dict(self.band_baselines)))
        object.__setattr__(self, "crest_factor_stats", copy.deepcopy(dict(self.crest_factor_stats)))
        object.__setattr__(self, "stereo_correlation_stats", copy.deepcopy(dict(self.stereo_correlation_stats)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "rms_stats": dict(self.rms_stats),
            "peak_stats": dict(self.peak_stats),
            "centroid_stats": dict(self.centroid_stats),
            "band_baselines": {k: dict(v) for k, v in self.band_baselines.items()},
            "crest_factor_stats": dict(self.crest_factor_stats),
            "stereo_correlation_stats": dict(self.stereo_correlation_stats)
        }


@dataclass(frozen=True)
class ForensicReport:
    """
    Complete deterministic forensic audit report for an audio stream or stem.
    Provides verifiable SHA-256 fingerprint for forensic provenance.
    """
    report_id: str
    analysis_version: str
    sample_rate: int
    duration_seconds: float
    channels: int
    config: AnalysisConfig
    frames_analyzed: int
    measurements_count: int
    events: Tuple[ForensicEvent, ...]
    hypotheses: Tuple[CausalHypothesis, ...] = ()
    baseline: Optional[TrackBaseline] = None
    processing_time_seconds: float = 0.0
    deterministic_hash: str = ""

    def __post_init__(self):
        if not self.report_id or not str(self.report_id).strip():
            raise ForensicsIntegrityError("report_id must be a non-empty string.")
        if self.sample_rate <= 0:
            raise ForensicsIntegrityError(f"sample_rate must be positive, got {self.sample_rate}")
        if self.channels not in (1, 2):
            raise ForensicsIntegrityError(f"channels must be 1 or 2, got {self.channels}")

        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "hypotheses", tuple(self.hypotheses))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "analysis_version": self.analysis_version,
            "sample_rate": self.sample_rate,
            "duration_seconds": round(self.duration_seconds, 4),
            "channels": self.channels,
            "config": self.config.to_dict(),
            "frames_analyzed": self.frames_analyzed,
            "measurements_count": self.measurements_count,
            "events": [e.to_dict() for e in self.events],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "processing_time_seconds": self.processing_time_seconds,
            "deterministic_hash": self.deterministic_hash
        }

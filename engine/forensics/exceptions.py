"""
Exception hierarchy for the Audio Forensics Engine (PIE Phase 7).
Provides structured, auditable error types for deterministic DSP forensic analysis.
"""
from typing import Dict, Any, Optional


class ForensicsError(Exception):
    """Base exception for all Audio Forensics Engine errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class InvalidAudioError(ForensicsError, ValueError):
    """Raised when audio array is empty, non-float, incorrect shape, or contains NaN/Infinity."""
    pass


class InvalidAnalysisConfigError(ForensicsError, ValueError):
    """Raised when analysis configuration parameters violate numerical invariants."""
    pass


class UnsupportedSampleRateError(InvalidAudioError):
    """Raised when sample rate is <= 0 or outside supported boundaries (8000 Hz to 192000 Hz)."""
    pass



class UnsupportedChannelLayoutError(InvalidAudioError):
    """Raised when channel count is not 1 (mono) or 2 (stereo)."""
    pass


class UnsupportedWindowError(ForensicsError, ValueError):
    """Raised when an unsupported STFT window function is requested."""
    pass


class InsufficientAudioError(InvalidAudioError):
    """Raised when audio length is shorter than the minimum FFT window size."""
    pass



class ForensicsPersistenceError(ForensicsError, IOError):
    """Raised when persistence or atomic report writing fails."""
    pass


class ForensicsIntegrityError(ForensicsError):
    """Raised when report structure, hashes, or causal assertions are corrupted."""
    pass

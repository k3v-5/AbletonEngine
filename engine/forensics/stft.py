"""
Deterministic Short-Time Fourier Transform (STFT) Engine for Audio Forensics (PIE Phase 7).
Operates strictly on real-valued signals with explicit frequency and time resolutions.
"""
from typing import Tuple, Dict, Any, Optional
import numpy as np

from .models import AnalysisConfig
from .exceptions import (
    InvalidAudioError,
    UnsupportedWindowError,
    InsufficientAudioError,
    UnsupportedSampleRateError,
    UnsupportedChannelLayoutError
)


class STFTEngine:
    """
    Computes deterministic time-frequency representations (STFT) for audio analysis.
    Guarantees mathematical reproducibility and explicit resolution tracking.
    """

    SUPPORTED_WINDOWS = {"hann", "hamming", "blackman"}

    @classmethod
    def get_window(cls, window_name: str, fft_size: int) -> np.ndarray:
        """Generates window array, raising UnsupportedWindowError if unknown."""
        w_lower = str(window_name).lower().strip()
        if w_lower not in cls.SUPPORTED_WINDOWS:
            raise UnsupportedWindowError(
                f"Unsupported STFT window '{window_name}'. Supported windows: {sorted(list(cls.SUPPORTED_WINDOWS))}"
            )
        if w_lower == "hann":
            return np.hanning(fft_size).astype(np.float64)
        elif w_lower == "hamming":
            return np.hamming(fft_size).astype(np.float64)
        elif w_lower == "blackman":
            return np.blackman(fft_size).astype(np.float64)
        raise UnsupportedWindowError(f"Unsupported window: {window_name}")

    @classmethod
    def validate_audio(cls, audio: np.ndarray, sample_rate: int, min_samples: int = 1):
        """Validates numerical integrity of audio array and sample rate."""
        if not isinstance(audio, np.ndarray):
            raise InvalidAudioError(f"Audio must be a numpy ndarray, got {type(audio)}")
        if audio.size == 0:
            raise InvalidAudioError("Audio array is empty.")
        if not np.issubdtype(audio.dtype, np.floating):
            raise InvalidAudioError(f"Audio must be float dtype, got {audio.dtype}")
        if np.isnan(audio).any() or np.isinf(audio).any():
            raise InvalidAudioError("Audio contains NaN or Infinity values.")
        if sample_rate <= 0 or sample_rate < 8000 or sample_rate > 192000:
            raise UnsupportedSampleRateError(
                f"Sample rate {sample_rate} Hz is outside supported boundaries [8000, 192000] Hz."
            )

        # Dimension checks: 1D (mono) or 2D (channels, samples)
        if audio.ndim == 1:
            n_channels = 1
            n_samples = audio.shape[0]
        elif audio.ndim == 2:
            n_channels, n_samples = audio.shape
            if n_channels not in (1, 2):
                raise UnsupportedChannelLayoutError(
                    f"Unsupported channel count {n_channels}. Only mono (1) or stereo (2) are supported."
                )
        else:
            raise InvalidAudioError(f"Audio array must be 1D or 2D, got shape {audio.shape}")

        if n_samples < min_samples:
            raise InsufficientAudioError(
                f"Audio length ({n_samples} samples) is shorter than required minimum ({min_samples} samples)."
            )

    @classmethod
    def compute_stft(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        config: Optional[AnalysisConfig] = None
    ) -> Dict[str, Any]:
        """
        Computes STFT magnitude, power, frequency bins, and time frames.
        Returns:
            {
                "magnitudes": np.ndarray of shape (channels, num_frames, num_bins),
                "powers": np.ndarray of shape (channels, num_frames, num_bins),
                "frequencies_hz": np.ndarray of shape (num_bins,),
                "time_stamps_seconds": np.ndarray of shape (num_frames,),
                "frequency_resolution_hz": float,
                "time_resolution_seconds": float,
                "num_frames": int,
                "num_bins": int,
                "window": np.ndarray
            }
        """
        if config is None:
            from .config import DEFAULT_ANALYSIS_CONFIG
            config = DEFAULT_ANALYSIS_CONFIG

        cls.validate_audio(audio, sample_rate, min_samples=config.fft_size)

        # Standardize to 2D (channels, samples)
        if audio.ndim == 1:
            signal = audio[np.newaxis, :]
        else:
            signal = audio

        n_channels, n_samples = signal.shape
        fft_size = config.fft_size
        hop_size = config.hop_size
        window = cls.get_window(config.window, fft_size)

        num_frames = 1 + (n_samples - fft_size) // hop_size
        if num_frames <= 0:
            raise InsufficientAudioError(
                f"Signal of {n_samples} samples yields 0 frames for fft_size={fft_size} and hop_size={hop_size}."
            )

        num_bins = fft_size // 2 + 1
        freq_bins = np.fft.rfftfreq(fft_size, d=1.0 / sample_rate)

        # Explicit mathematical resolutions (Section 12)
        freq_resolution = float(sample_rate / fft_size)
        time_resolution = float(hop_size / sample_rate)

        # Window normalization factor (for correct magnitude scaling)
        window_norm = np.sum(window)
        if window_norm == 0:
            window_norm = 1.0

        magnitudes = np.zeros((n_channels, num_frames, num_bins), dtype=np.float64)
        powers = np.zeros((n_channels, num_frames, num_bins), dtype=np.float64)
        time_stamps = np.zeros((num_frames,), dtype=np.float64)

        for ch in range(n_channels):
            ch_data = signal[ch]
            for f_idx in range(num_frames):
                start = f_idx * hop_size
                end = start + fft_size
                frame = ch_data[start:end] * window

                # Real FFT
                spectrum = np.fft.rfft(frame)
                mag = np.abs(spectrum) / (window_norm / 2.0)
                power = mag ** 2

                magnitudes[ch, f_idx, :] = mag
                powers[ch, f_idx, :] = power
                if ch == 0:
                    time_stamps[f_idx] = float(start / sample_rate)

        return {
            "magnitudes": magnitudes,
            "powers": powers,
            "frequencies_hz": freq_bins,
            "time_stamps_seconds": time_stamps,
            "frequency_resolution_hz": freq_resolution,
            "time_resolution_seconds": time_resolution,
            "num_frames": num_frames,
            "num_bins": num_bins,
            "window": window,
            "channels": n_channels,
            "sample_rate": sample_rate,
            "config": config
        }

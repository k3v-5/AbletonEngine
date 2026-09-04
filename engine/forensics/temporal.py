"""
Temporal Feature Analysis Engine for Audio Forensics (PIE Phase 7).
Computes frame-level RMS, peaks, crest factors, attack/decay profiles, and constructs AudioFrame objects.
"""
from typing import List, Dict, Any, Optional, Union
import numpy as np

from .models import AudioFrame, AnalysisConfig
from .config import DEFAULT_ANALYSIS_CONFIG
from .spectral import SpectralEngine
from .stft import STFTEngine


class TemporalEngine:
    """
    Extracts time-domain envelope, dynamics, and builds AudioFrame sequences.
    """

    @classmethod
    def calculate_frame_rms(cls, slice_data: np.ndarray) -> float:
        """Calculates RMS level in dBFS for a 1D slice of audio."""
        if len(slice_data) == 0:
            return -100.0
        rms_lin = np.sqrt(np.mean(slice_data.astype(np.float64) ** 2) + 1e-12)
        return float(20.0 * np.log10(rms_lin))

    @classmethod
    def calculate_frame_peak(cls, slice_data: np.ndarray) -> float:
        """Calculates peak level in dBFS for a 1D slice of audio."""
        if len(slice_data) == 0:
            return -100.0
        peak_lin = np.max(np.abs(slice_data.astype(np.float64))) + 1e-12
        return float(20.0 * np.log10(peak_lin))

    @classmethod
    def calculate_crest_factor(cls, peak_dbfs: float, rms_dbfs: float) -> float:
        """Calculates crest factor in dB (peak_dbfs - rms_dbfs)."""
        return float(peak_dbfs - rms_dbfs)

    @classmethod
    def analyze_frames(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        arg3: Optional[Union[AnalysisConfig, Dict[str, Any]]] = None,
        config: Optional[AnalysisConfig] = None,
        stft_result: Optional[Dict[str, Any]] = None
    ) -> List[AudioFrame]:
        """
        Builds AudioFrame objects for all frames in the STFT representation.
        Accepts flexible signatures:
        - analyze_frames(audio, sample_rate, config)
        - analyze_frames(audio, sample_rate, stft_result, config)
        """
        # Standardize audio to 2D
        if audio.ndim == 1:
            signal = audio[np.newaxis, :]
        else:
            signal = audio

        n_channels, n_samples = signal.shape

        # Resolve config and stft_result
        if isinstance(arg3, AnalysisConfig):
            cfg = arg3
            stft = stft_result
        elif isinstance(arg3, dict):
            stft = arg3
            cfg = config or stft.get("config", DEFAULT_ANALYSIS_CONFIG)
        else:
            cfg = config or DEFAULT_ANALYSIS_CONFIG
            stft = stft_result

        # If STFT was not computed beforehand, compute it now
        if stft is None:
            stft = STFTEngine.compute_stft(signal, sample_rate, cfg)

        fft_size = cfg.fft_size
        hop_size = cfg.hop_size
        num_frames = stft["num_frames"]
        time_stamps = stft["time_stamps_seconds"]
        magnitudes = stft["magnitudes"]
        freqs = stft["frequencies_hz"]

        # If stereo, average channels for frame-level mono summary features
        mono_signal = np.mean(signal, axis=0) if n_channels > 1 else signal[0]
        avg_magnitudes = np.mean(magnitudes, axis=0) if n_channels > 1 else magnitudes[0]

        frames: List[AudioFrame] = []
        prev_mag: Optional[np.ndarray] = None

        for f_idx in range(num_frames):
            start_s = f_idx * hop_size
            end_s = start_s + fft_size
            slice_data = mono_signal[start_s:end_s]

            rms_db = cls.calculate_frame_rms(slice_data)
            peak_db = cls.calculate_frame_peak(slice_data)

            start_t = float(time_stamps[f_idx])
            end_t = float(start_t + (fft_size / sample_rate))

            curr_mag = avg_magnitudes[f_idx]
            centroid = SpectralEngine.calculate_spectral_centroid(curr_mag, freqs)
            flux = SpectralEngine.calculate_spectral_flux(curr_mag, prev_mag)
            prev_mag = curr_mag

            frame = AudioFrame(
                index=f_idx,
                start_sample=start_s,
                end_sample=end_s,
                start_time_seconds=start_t,
                end_time_seconds=end_t,
                rms_dbfs=rms_db,
                peak_dbfs=peak_db,
                spectral_centroid_hz=centroid,
                spectral_flux=flux
            )
            frames.append(frame)

        return frames

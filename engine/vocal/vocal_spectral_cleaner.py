# engine/vocal/vocal_spectral_cleaner.py
"""
Spectral Vocal Cleaner & Dynamics Guardian:
- Sibilance & Harshness Detector (5.5 kHz - 9.0 kHz) for dynamic de-essing.
- Plosive & Wind Pop Detector (<60 Hz) for micro-fade protection.
- Adaptive Noise Floor Estimator & Downward Expander configurator.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import signal


class VocalSpectralCleaner:
    """Performs pre-fx spectral acoustics analysis on raw and tracked vocals."""

    @classmethod
    def analyze_sibilance(cls, audio: np.ndarray, sr: int = 44100) -> Dict[str, Any]:
        """
        Detects excess high-frequency friction / sibilance (/s/, /z/, /sh/) in 5.5 kHz - 9.0 kHz.
        Calculates spectral centroid and recommended de-esser threshold.
        """
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        if len(mono) < 1024:
            return {"has_excess_sibilance": False, "recommended_deesser_threshold_db": -20.0}

        # Bandpass filter 5.5k - 9k
        nyq = 0.5 * sr
        low = max(0.01, min(0.85, 5500.0 / nyq))
        high = max(low + 0.05, min(0.99, 9000.0 / nyq))
        sos_sib = signal.butter(4, [low, high], 'bandpass', output='sos')
        sib_band = signal.sosfilt(sos_sib, mono)

        # RMS ratio
        rms_total = np.sqrt(np.mean(mono ** 2) + 1e-12)
        rms_sib = np.sqrt(np.mean(sib_band ** 2) + 1e-12)
        ratio_db = 20.0 * np.log10(rms_sib / rms_total)

        # Typical natural vocal sibilance ratio is -16 to -22 dB. Ratio > -12 dB is harsh.
        is_harsh = ratio_db > -13.0
        peak_sib_db = 20.0 * np.log10(np.max(np.abs(sib_band)) + 1e-12)
        rec_thresh = max(-36.0, peak_sib_db - 6.0)

        return {
            "has_excess_sibilance": bool(is_harsh),
            "sibilance_ratio_db": round(float(ratio_db), 2),
            "peak_sibilance_dbfs": round(float(peak_sib_db), 2),
            "recommended_frequency_hz": 6800.0,
            "recommended_deesser_threshold_db": round(float(rec_thresh), 1),
            "action": "ENGAGE_DEESSER" if is_harsh else "NATURAL_PASS"
        }

    @classmethod
    def analyze_plosives(cls, audio: np.ndarray, sr: int = 44100) -> Dict[str, Any]:
        """
        Detects high-energy sub-bass bursts (<60 Hz) caused by microphone pops / plosives (/p/, /b/).
        """
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        if len(mono) < 1024:
            return {"has_plosives": False, "plosive_count": 0}

        nyq = 0.5 * sr
        sos_sub = signal.butter(4, min(60.0 / nyq, 0.49), 'lowpass', output='sos')
        sub_bursts = signal.sosfilt(sos_sub, mono)

        # Detect transient peaks in sub
        peak_sub = np.max(np.abs(sub_bursts))
        peak_sub_db = 20.0 * np.log10(peak_sub + 1e-12)
        total_peak_db = 20.0 * np.log10(np.max(np.abs(mono)) + 1e-12)

        # Plosive exists if <60Hz energy is within 6 dB of the full track peak
        has_plosives = (peak_sub_db > (total_peak_db - 6.0)) and (peak_sub_db > -24.0)

        return {
            "has_plosives": bool(has_plosives),
            "sub_energy_peak_dbfs": round(float(peak_sub_db), 2),
            "recommendation": "APPLY_100HZ_HPF" if has_plosives else "PASS"
        }

    @classmethod
    def estimate_noise_floor_and_expander(cls, audio: np.ndarray, sr: int = 44100) -> Dict[str, Any]:
        """
        Estimates ambient room noise floor in pauses between vocal phrases
        and calculates downward expander/gate thresholds.
        """
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        if len(mono) < 2048:
            return {"noise_floor_dbfs": -60.0, "recommended_gate_threshold_dbfs": -48.0}

        frame_len = int(sr * 0.05)
        hop_len = int(sr * 0.025)
        n_frames = max(1, (len(mono) - frame_len) // hop_len)

        rms_frames = []
        for i in range(n_frames):
            frame = mono[i * hop_len : i * hop_len + frame_len]
            rms_frames.append(20.0 * np.log10(np.sqrt(np.mean(frame ** 2) + 1e-12)))

        rms_arr = np.array(rms_frames)
        # Noise floor is approximated by the 15th percentile of frames (background room level)
        noise_floor_db = float(np.percentile(rms_arr, 15))
        gate_threshold_db = min(-35.0, noise_floor_db + 6.0)

        return {
            "noise_floor_dbfs": round(noise_floor_db, 2),
            "recommended_gate_threshold_dbfs": round(gate_threshold_db, 2),
            "recommended_ratio": 1.5,
            "recommended_attack_ms": 2.0,
            "recommended_release_ms": 120.0
        }

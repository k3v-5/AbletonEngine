"""
Confidence and statistical reliability estimation for audio measurements.
Enforces rule: never perform automatic modifications on low-confidence data.
"""
from typing import Optional
import numpy as np


AUTO_CORRECTION_MIN_CONFIDENCE = 0.80


class ConfidenceEvaluator:
    """Calculates statistical confidence [0.0, 1.0] for various DSP measurements."""

    @staticmethod
    def estimate_fundamental_confidence(spectrum: np.ndarray, freqs: np.ndarray,
                                         peak_idx: int, band_mask: np.ndarray) -> float:
        """
        Estimates confidence of fundamental frequency detection based on:
        1. Peak-to-secondary-peak prominence ratio.
        2. Signal-to-noise ratio in the target band.
        3. Ambiguity / harmonic ambiguity penalty.
        """
        if len(spectrum) == 0 or not np.any(band_mask):
            return 0.0
            
        band_vals = spectrum[band_mask]
        if len(band_vals) < 2:
            return 0.2
            
        peak_val = spectrum[peak_idx]
        if peak_val <= 1e-9:
            return 0.0

        # Sort peak heights in band
        sorted_vals = np.sort(band_vals)[::-1]
        top1 = sorted_vals[0]
        top2 = sorted_vals[1] if len(sorted_vals) > 1 else 0.0
        
        # Prominence ratio
        prominence = (top1 - top2) / (top1 + 1e-9)
        
        # Energy concentration: ratio of top peak energy to median energy in band
        median_val = np.median(band_vals) + 1e-9
        snr = top1 / median_val
        snr_factor = min(1.0, snr / 10.0)
        
        # Combined confidence
        raw_conf = 0.5 * prominence + 0.5 * snr_factor
        return float(np.clip(raw_conf, 0.0, 1.0))

    @staticmethod
    def estimate_transient_confidence(audio: np.ndarray, num_onsets: int, duration_sec: float) -> float:
        """Estimates confidence of transient detection based on duration and onset count."""
        if duration_sec < 0.1 or len(audio) == 0:
            return 0.1
            
        rate = num_onsets / duration_sec
        # For music, typical onsets are between 0.5 and 16 per second
        if 0.5 <= rate <= 24.0:
            rate_factor = 1.0
        elif rate < 0.5:
            rate_factor = max(0.2, rate / 0.5)
        else:
            rate_factor = max(0.2, 1.0 - (rate - 24.0) / 24.0)
            
        # Check audio length adequacy (at least 1 second preferred)
        dur_factor = min(1.0, duration_sec / 1.5)
        return float(np.clip(0.4 * rate_factor + 0.6 * dur_factor, 0.0, 1.0))

    @staticmethod
    def estimate_stereo_confidence(audio: np.ndarray) -> float:
        """Estimates confidence of stereo metrics based on channel count and audio energy."""
        if audio.ndim < 2 or audio.shape[0] < 2:
            return 1.0  # Mono is 100% reliably mono
            
        rms_l = np.sqrt(np.mean(audio[0]**2) + 1e-12)
        rms_r = np.sqrt(np.mean(audio[1]**2) + 1e-12)
        
        if rms_l < 1e-5 and rms_r < 1e-5:
            return 0.1  # Silence yields low confidence
            
        # Duration confidence
        dur = audio.shape[1] / 44100.0
        dur_factor = min(1.0, dur / 0.5)
        return float(np.clip(0.8 * dur_factor + 0.2, 0.0, 1.0))

    @staticmethod
    def is_safe_for_auto_correction(confidence: float, threshold: float = AUTO_CORRECTION_MIN_CONFIDENCE) -> bool:
        """Checks if confidence meets strict guardrail for automatic modification."""
        return confidence >= threshold

"""
DSP Transient, Kick, and Bass Analyzers.
Extracts attack time, decay time, sub-frequency fundamentals, and punch.
"""
from typing import Tuple
import numpy as np

from .models import TransientFeatures, KickAnalysis, BassAnalysis
from .confidence import ConfidenceEvaluator


class TransientAnalyzer:
    """Analyzes envelope, attack times, decay times, and onset events."""

    @classmethod
    def analyze_transients(cls, audio: np.ndarray, sr: int) -> TransientFeatures:
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        n = len(mono)
        if n < 256:
            return TransientFeatures(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        # Hilbert-envelope / rectified smoothed envelope
        rect = np.abs(mono)
        kernel_size = int(0.005 * sr)  # 5ms smoothing
        if kernel_size > 1:
            kernel = np.ones(kernel_size) / kernel_size
            env = np.convolve(rect, kernel, mode="same")
        else:
            env = rect

        peak_env = np.max(env) + 1e-12
        mean_env = np.mean(env) + 1e-12
        peak_to_body = float(peak_env / mean_env)
        
        # Onset detection via first-order difference
        diff_env = np.diff(env)
        diff_pos = np.maximum(0, diff_env)
        onset_thresh = np.mean(diff_pos) + 2.0 * np.std(diff_pos)
        onsets = np.where(diff_pos > onset_thresh)[0]
        duration_sec = n / sr
        onsets_per_sec = float(len(onsets) / max(0.1, duration_sec))

        # Attack time: time from 10% to 90% of maximum peak
        max_idx = np.argmax(env)
        thresh_10 = 0.10 * peak_env
        thresh_90 = 0.90 * peak_env
        
        pre_peak = env[:max_idx]
        idx_10 = np.where(pre_peak >= thresh_10)[0]
        idx_90 = np.where(pre_peak >= thresh_90)[0]
        
        if len(idx_10) > 0 and len(idx_90) > 0:
            attack_samples = max(1, idx_90[0] - idx_10[0])
            attack_ms = float((attack_samples / sr) * 1000.0)
        else:
            attack_ms = 5.0

        # Decay time: time from peak to 36.8% (1/e) of peak
        post_peak = env[max_idx:]
        decay_thresh = peak_env / np.e
        decay_idx = np.where(post_peak <= decay_thresh)[0]
        if len(decay_idx) > 0:
            decay_samples = decay_idx[0]
            decay_ms = float((decay_samples / sr) * 1000.0)
        else:
            decay_ms = float((len(post_peak) / sr) * 1000.0)

        transient_strength = min(1.0, peak_to_body / 8.0)
        body_energy = float(mean_env)

        return TransientFeatures(
            attack_time_ms=attack_ms,
            decay_time_ms=decay_ms,
            transient_strength=transient_strength,
            body_energy=body_energy,
            peak_to_body_ratio=peak_to_body,
            onsets_per_second=onsets_per_sec
        )

    @classmethod
    def analyze_kick(cls, audio: np.ndarray, sr: int) -> KickAnalysis:
        """Isolates kick drum characteristics: fundamental frequency, click, sub energy, decay."""
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        n = len(mono)
        if n < 512:
            return KickAnalysis(50.0, 0.5, -20.0, -20.0, -20.0, 150.0, 0.1)

        # FFT
        n_fft = min(8192, max(512, 1 << (n - 1).bit_length()))
        fft_vals = np.fft.rfft(mono[:n_fft] * np.hanning(min(n, n_fft)))
        mag = np.abs(fft_vals)
        freqs = np.fft.rfftfreq(n_fft, d=1.0/sr)

        # Fundamental in 40-90 Hz
        sub_mask = (freqs >= 40.0) & (freqs <= 90.0)
        if np.any(sub_mask):
            sub_mag = mag[sub_mask]
            sub_freqs = freqs[sub_mask]
            peak_sub_idx = np.argmax(sub_mag)
            
            # Parabolic interpolation for sub-Hz peak accuracy
            k = peak_sub_idx
            if 0 < k < len(sub_mag) - 1:
                alpha = sub_mag[k-1]
                beta = sub_mag[k]
                gamma = sub_mag[k+1]
                delta = 0.5 * (alpha - gamma) / (alpha - 2*beta + gamma + 1e-12)
                fund_hz = float(sub_freqs[k] + delta * (sub_freqs[1] - sub_freqs[0]))
            else:
                fund_hz = float(sub_freqs[k])
            confidence = ConfidenceEvaluator.estimate_fundamental_confidence(mag, freqs, np.argmax(mag * sub_mask), sub_mask)
        else:
            fund_hz = 50.0
            confidence = 0.2

        # Energies in sub (20-60), body (60-140), click (>2kHz)
        sub_energy = 20.0 * np.log10(np.mean(mag[(freqs >= 20.0) & (freqs <= 60.0)]**2) + 1e-12)
        body_energy = 20.0 * np.log10(np.mean(mag[(freqs >= 60.0) & (freqs <= 140.0)]**2) + 1e-12)
        click_energy = 20.0 * np.log10(np.mean(mag[freqs >= 2000.0]**2) + 1e-12)

        trans_feats = cls.analyze_transients(audio, sr)

        return KickAnalysis(
            fundamental_hz=fund_hz,
            transient_strength=trans_feats.transient_strength,
            sub_energy_db=float(sub_energy),
            body_energy_db=float(body_energy),
            click_energy_db=float(click_energy),
            decay_ms=trans_feats.decay_time_ms,
            confidence=confidence
        )

    @classmethod
    def analyze_bass(cls, audio: np.ndarray, sr: int) -> BassAnalysis:
        """Analyzes bassline fundamental, harmonic saturation, low-end stereo width."""
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        n = len(mono)
        if n < 512:
            return BassAnalysis(55.0, 0.5, -20.0, 0.0, 3.0, 0.1)

        # FFT
        n_fft = min(8192, max(512, 1 << (n - 1).bit_length()))
        fft_vals = np.fft.rfft(mono[:n_fft] * np.hanning(min(n, n_fft)))
        mag = np.abs(fft_vals)
        freqs = np.fft.rfftfreq(n_fft, d=1.0/sr)

        # Fundamental in 30-180 Hz
        bass_mask = (freqs >= 30.0) & (freqs <= 180.0)
        if np.any(bass_mask):
            peak_idx = np.argmax(mag * bass_mask)
            fund_hz = float(freqs[peak_idx])
            confidence = ConfidenceEvaluator.estimate_fundamental_confidence(mag, freqs, peak_idx, bass_mask)
        else:
            fund_hz = 55.0
            confidence = 0.3

        # Harmonics ratio: energy between 200Hz - 2kHz vs energy < 200Hz
        low_energy = np.sum(mag[freqs < 200.0]**2) + 1e-12
        mid_energy = np.sum(mag[(freqs >= 200.0) & (freqs <= 2000.0)]**2)
        harmonics_ratio = float(mid_energy / low_energy)

        sub_energy = float(20.0 * np.log10(np.mean(mag[(freqs >= 20.0) & (freqs <= 90.0)]**2) + 1e-12))

        # Low-end stereo width
        if audio.ndim > 1 and audio.shape[0] >= 2:
            left = audio[0]
            right = audio[1]
            side = (left - right) / np.sqrt(2.0)
            mid = (left + right) / np.sqrt(2.0)
            side_rms = np.sqrt(np.mean(side**2) + 1e-12)
            mid_rms = np.sqrt(np.mean(mid**2) + 1e-12)
            low_width = float(side_rms / mid_rms)
        else:
            low_width = 0.0

        return BassAnalysis(
            fundamental_hz=fund_hz,
            harmonics_energy_ratio=harmonics_ratio,
            sub_energy_db=sub_energy,
            low_end_stereo_width=low_width,
            dynamic_variation_db=4.5,
            confidence=confidence
        )

"""
DSP Stereo and Mono Compatibility Analyzer.
Measures Pearson correlation, Mid/Side energy, low-frequency stereo energy, and mono loss.
"""
from typing import Tuple
import numpy as np

from .models import StereoFeatures


class StereoAnalyzer:
    """Analyzes stereo imaging and checks mono compatibility."""

    @classmethod
    def analyze_stereo(cls, audio: np.ndarray, sr: int) -> StereoFeatures:
        if audio.ndim < 2 or audio.shape[0] < 2:
            # Pure mono signal
            rms = float(20.0 * np.log10(np.sqrt(np.mean(audio**2) + 1e-12)))
            return StereoFeatures(
                correlation=1.0,
                mid_energy_db=rms,
                side_energy_db=-100.0,
                width=0.0,
                low_end_width=0.0,
                high_end_width=0.0,
                mono_energy_loss_db=0.0,
                low_frequency_stereo_severity=0.0,
                mono_compatibility_warning=False
            )

        left = audio[0]
        right = audio[1]
        
        # Pearson correlation: sum(L*R) / sqrt(sum(L^2) * sum(R^2))
        dot_lr = np.sum(left * right)
        norm_l = np.sqrt(np.sum(left**2) + 1e-12)
        norm_r = np.sqrt(np.sum(right**2) + 1e-12)
        correlation = float(np.clip(dot_lr / (norm_l * norm_r), -1.0, 1.0))

        # Mid/Side decomposition
        mid = (left + right) / np.sqrt(2.0)
        side = (left - right) / np.sqrt(2.0)

        mid_rms = np.sqrt(np.mean(mid**2) + 1e-12)
        side_rms = np.sqrt(np.mean(side**2) + 1e-12)
        
        mid_db = float(20.0 * np.log10(mid_rms))
        side_db = float(20.0 * np.log10(side_rms))
        width = float(side_rms / mid_rms)

        # Low frequency filter (below 120Hz)
        # Using FFT band-pass
        n = len(left)
        fft_side = np.fft.rfft(side)
        fft_mid = np.fft.rfft(mid)
        freqs = np.fft.rfftfreq(n, d=1.0/sr)
        
        low_mask = freqs <= 120.0
        high_mask = freqs >= 2000.0
        
        low_side_energy = np.sum(np.abs(fft_side[low_mask])**2)
        low_mid_energy = np.sum(np.abs(fft_mid[low_mask])**2) + 1e-12
        low_width = float(np.sqrt(low_side_energy / low_mid_energy))

        high_side_energy = np.sum(np.abs(fft_side[high_mask])**2)
        high_mid_energy = np.sum(np.abs(fft_mid[high_mask])**2) + 1e-12
        high_width = float(np.sqrt(high_side_energy / high_mid_energy))

        # Low frequency stereo severity:
        # In professional club mixes, sub-120Hz should be almost entirely mono (<0.10 width)
        if low_width > 0.35:
            low_stereo_severity = min(1.0, low_width)
        elif low_width > 0.15:
            low_stereo_severity = (low_width - 0.15) / 0.20 * 0.6 + 0.3
        else:
            low_stereo_severity = low_width

        # Mono compatibility simulation:
        # Compare stereo energy with mono sum (L+R)/2
        stereo_energy = np.mean(left**2 + right**2) / 2.0 + 1e-12
        mono_sum = (left + right) / 2.0
        mono_energy = np.mean(mono_sum**2) + 1e-12
        loss_db = float(10.0 * np.log10(stereo_energy / mono_energy))
        loss_db = max(0.0, loss_db)

        # Warning triggered if energy loss > 2.0 dB or negative correlation
        mono_warning = bool(loss_db > 2.0 or correlation < 0.0 or low_stereo_severity > 0.65)

        return StereoFeatures(
            correlation=correlation,
            mid_energy_db=mid_db,
            side_energy_db=side_db,
            width=width,
            low_end_width=low_width,
            high_end_width=high_width,
            mono_energy_loss_db=loss_db,
            low_frequency_stereo_severity=float(low_stereo_severity),
            mono_compatibility_warning=mono_warning
        )

"""
Vocal role acoustic feature and balance analyzer.
"""
import numpy as np

from .models import VocalAnalysis


class VocalAnalyzer:
    """Analyzes presence, boxiness, sibilance, and stereo placement of vocal tracks."""

    @classmethod
    def analyze_vocal(cls, audio: np.ndarray, sr: int) -> VocalAnalysis:
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        n = len(mono)
        if n < 512:
            return VocalAnalysis(-20.0, -20.0, 0.05, 10.0, 0.2, 0.1, 0.1)

        fft_vals = np.abs(np.fft.rfft(mono * np.hanning(n)))
        freqs = np.fft.rfftfreq(n, d=1.0/sr)

        # Vocal presence (1.5 kHz - 4.5 kHz)
        pres_mask = (freqs >= 1500.0) & (freqs <= 4500.0)
        pres_db = float(20.0 * np.log10(np.mean(fft_vals[pres_mask]) + 1e-12))

        # Low-mid mud / boxiness (250 Hz - 500 Hz)
        low_mid_mask = (freqs >= 250.0) & (freqs <= 500.0)
        low_mid_db = float(20.0 * np.log10(np.mean(fft_vals[low_mid_mask]) + 1e-12))

        # Sibilance region (5.5 kHz - 9.0 kHz) vs presence
        sib_mask = (freqs >= 5500.0) & (freqs <= 9000.0)
        sib_energy = np.sum(fft_vals[sib_mask]**2) + 1e-12
        pres_energy = np.sum(fft_vals[pres_mask]**2) + 1e-12
        sibilance_ratio = float(sib_energy / pres_energy)

        # Dynamic range
        rms_val = np.sqrt(np.mean(mono**2) + 1e-12)
        peak_val = np.max(np.abs(mono)) + 1e-12
        dyn_db = float(20.0 * np.log10(peak_val / rms_val))

        # Stereo width
        if audio.ndim > 1 and audio.shape[0] >= 2:
            side = (audio[0] - audio[1]) / np.sqrt(2.0)
            mid = (audio[0] + audio[1]) / np.sqrt(2.0)
            width = float(np.sqrt(np.mean(side**2) + 1e-12) / (np.sqrt(np.mean(mid**2) + 1e-12)))
        else:
            width = 0.0

        return VocalAnalysis(
            presence_db=pres_db,
            low_mid_energy_db=low_mid_db,
            sibilance_ratio=sibilance_ratio,
            dynamic_range_db=dyn_db,
            stereo_width=width,
            reverb_energy_estimate=min(1.0, width * 0.5),
            confidence=0.85
        )

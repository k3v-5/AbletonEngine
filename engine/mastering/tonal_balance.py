"""
Tonal Balance Analyzer across 7 standard mastering frequency bands.
"""
from typing import Dict, Any
import numpy as np
from .models import TonalDifferenceMap

BANDS = {
    "sub": (20, 60),
    "low": (60, 250),
    "low_mid": (250, 500),
    "mid": (500, 2000),
    "high_mid": (2000, 6000),
    "presence": (6000, 10000),
    "brilliance": (10000, 20000)
}


class TonalBalanceAnalyzer:
    """Extracts energy across 7 mastering bands and computes spectral difference maps."""

    @classmethod
    def analyze_tonal_balance(cls, audio: np.ndarray, sr: int) -> Dict[str, float]:
        if audio.ndim > 1:
            mono = np.mean(audio, axis=0) if audio.shape[0] < audio.shape[1] else np.mean(audio, axis=1)
        else:
            mono = audio

        n_samples = len(mono)
        n_fft = min(4096, n_samples)
        fft_vals = np.abs(np.fft.rfft(mono[:n_fft]))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

        band_energies = {}
        for band_name, (low_f, high_f) in BANDS.items():
            mask = (freqs >= low_f) & (freqs < high_f)
            if np.any(mask):
                energy = float(np.mean(fft_vals[mask] ** 2)) + 1e-12
                db = float(10.0 * np.log10(energy))
            else:
                db = -60.0
            band_energies[band_name] = db

        # Relative to mid band
        mid_db = band_energies["mid"]
        return {k: round(v - mid_db, 2) for k, v in band_energies.items()}

    @classmethod
    def compute_difference_map(cls, current: Dict[str, float], reference: Dict[str, float]) -> TonalDifferenceMap:
        deltas = {}
        sq_sum = 0.0
        for band in BANDS.keys():
            cur_val = current.get(band, 0.0)
            ref_val = reference.get(band, 0.0)
            diff = cur_val - ref_val
            deltas[band] = diff
            sq_sum += diff ** 2

        rms_gap = float(np.sqrt(sq_sum / len(BANDS)))
        return TonalDifferenceMap(deltas=deltas, rms_spectral_gap=round(rms_gap, 2))

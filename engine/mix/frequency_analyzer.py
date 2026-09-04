"""
DSP Frequency and Spectral Profile Analyzer.
Computes STFT across 12 standard frequency bands and derives acoustic features.
"""
from typing import Dict, List, Tuple
import numpy as np

from .models import FrequencyBandData, SpectralProfile


STANDARD_BANDS = [
    ("20-40Hz", 20.0, 40.0),
    ("40-60Hz", 40.0, 60.0),
    ("60-90Hz", 60.0, 90.0),
    ("90-120Hz", 90.0, 120.0),
    ("120-200Hz", 120.0, 200.0),
    ("200-400Hz", 200.0, 400.0),
    ("400-800Hz", 400.0, 800.0),
    ("800-2kHz", 800.0, 2000.0),
    ("2k-4kHz", 2000.0, 4000.0),
    ("4k-8kHz", 4000.0, 8000.0),
    ("8k-12kHz", 8000.0, 12000.0),
    ("12k-20kHz", 12000.0, 20000.0)
]


class FrequencyAnalyzer:
    """Performs FFT/STFT analysis across 12 frequency bands and derives spectral features."""

    @classmethod
    def analyze_bands(cls, audio: np.ndarray, sr: int) -> List[FrequencyBandData]:
        """
        Calculates power spectrum and energy metrics across 12 frequency bands.
        audio: shape (channels, samples).
        """
        # Downmix to mono for frequency distribution
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        n_samples = len(mono)
        if n_samples < 64:
            return [FrequencyBandData(name, fmin, fmax, -100.0, 0.0, -100.0, -100.0)
                    for name, fmin, fmax in STANDARD_BANDS]

        # STFT with Hann window (n_fft = 2048 or smaller if short clip)
        n_fft = min(4096, max(256, 1 << (n_samples - 1).bit_length()))
        hop_length = n_fft // 2
        window = np.hanning(n_fft)
        
        # Frame extraction
        num_frames = max(1, (n_samples - n_fft) // hop_length + 1)
        stft_matrix = []
        for i in range(num_frames):
            start = i * hop_length
            frame = mono[start:start+n_fft]
            if len(frame) < n_fft:
                frame = np.pad(frame, (0, n_fft - len(frame)))
            stft_matrix.append(np.fft.rfft(frame * window))
            
        stft_matrix = np.array(stft_matrix)  # shape: (frames, bins)
        power_spectrum = np.abs(stft_matrix)**2
        mean_power = np.mean(power_spectrum, axis=0)  # shape: (bins,)
        peak_power = np.max(power_spectrum, axis=0)
        
        freqs = np.fft.rfftfreq(n_fft, d=1.0/sr)
        total_power = np.sum(mean_power) + 1e-12

        band_results = []
        for name, f_min, f_max in STANDARD_BANDS:
            mask = (freqs >= f_min) & (freqs < f_max)
            if not np.any(mask):
                band_results.append(FrequencyBandData(name, f_min, f_max, -100.0, 0.0, -100.0, -100.0))
                continue
                
            band_mean_p = np.sum(mean_power[mask])
            band_peak_p = np.max(peak_power[mask])
            rel_energy = float(band_mean_p / total_power)
            
            # dBFS conversion
            energy_db = float(10.0 * np.log10(max(1e-12, band_mean_p)))
            peak_db = float(10.0 * np.log10(max(1e-12, band_peak_p)))
            avg_db = energy_db
            
            band_results.append(FrequencyBandData(
                band_name=name,
                f_min=f_min,
                f_max=f_max,
                energy_db=energy_db,
                relative_energy=rel_energy,
                peak_energy=peak_db,
                average_energy=avg_db
            ))
            
        return band_results

    @classmethod
    def get_spectral_profile(cls, audio: np.ndarray, sr: int) -> SpectralProfile:
        """Computes centroid, rolloff, flatness, zero crossing rate, and classification."""
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        n_samples = len(mono)
        if n_samples < 64:
            return SpectralProfile("balanced", 0.5, 1000.0, 3000.0, 0.1, 0.05)

        # FFT
        fft_vals = np.fft.rfft(mono * np.hanning(n_samples))
        mag = np.abs(fft_vals)
        power = mag**2
        freqs = np.fft.rfftfreq(n_samples, d=1.0/sr)
        total_power = np.sum(power) + 1e-12
        
        # 1. Spectral Centroid
        centroid = float(np.sum(freqs * mag) / (np.sum(mag) + 1e-12))
        
        # 2. Spectral Rolloff (85% energy)
        cumsum = np.cumsum(power)
        rolloff_idx = np.searchsorted(cumsum, 0.85 * total_power)
        rolloff = float(freqs[min(rolloff_idx, len(freqs)-1)])
        
        # 3. Spectral Flatness (geometric mean / arithmetic mean)
        power_safe = power + 1e-12
        geometric_mean = np.exp(np.mean(np.log(power_safe)))
        arithmetic_mean = np.mean(power_safe)
        flatness = float(geometric_mean / arithmetic_mean)
        
        # 4. Zero Crossing Rate
        zero_crossings = np.sum(np.diff(np.signbit(mono)))
        zcr = float(zero_crossings / max(1, n_samples))
        
        # Band energies
        bands = cls.analyze_bands(audio, sr)
        band_dict = {b.band_name: b.relative_energy for b in bands}
        
        # Classification heuristics
        sub_energy = sum(band_dict.get(k, 0.0) for k in ["20-40Hz", "40-60Hz", "60-90Hz"])
        mid_energy = sum(band_dict.get(k, 0.0) for k in ["200-400Hz", "400-800Hz", "800-2kHz"])
        high_energy = sum(band_dict.get(k, 0.0) for k in ["4k-8kHz", "8k-12kHz", "12k-20kHz"])
        
        if sub_energy > 0.45:
            classification = "sub-heavy"
            confidence = min(0.95, sub_energy * 1.6)
        elif high_energy > 0.35 or centroid > 4500.0:
            classification = "bright"
            confidence = 0.85
        elif centroid < 1200.0:
            classification = "dark"
            confidence = 0.88
        elif mid_energy > 0.50:
            classification = "mid-heavy"
            confidence = 0.82
        elif flatness > 0.25:
            classification = "dense"
            confidence = 0.78
        elif total_power < 1e-4:
            classification = "thin"
            confidence = 0.75
        else:
            classification = "balanced"
            confidence = 0.80

        return SpectralProfile(
            classification=classification,
            confidence=confidence,
            spectral_centroid=centroid,
            spectral_rolloff=rolloff,
            spectral_flatness=flatness,
            zero_crossing_rate=zcr,
            band_energies={b.band_name: b.energy_db for b in bands}
        )

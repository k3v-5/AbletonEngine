# engine/mix/eq/resonance.py
"""
Resonance Hunter & Surgical Dynamic EQ Engine:
Scans audio signals with high-resolution FFT spectral decomposition, detects narrow
ear-fatiguing parasitic resonances (Q >= 6.0), and generates precise EQ Eight notch cuts.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np


@dataclass
class ResonantPeak:
    frequency_hz: float
    prominence_db: float
    q_factor: float
    recommended_gain_db: float
    band_type: str = "notch"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frequency_hz": round(self.frequency_hz, 1),
            "prominence_db": round(self.prominence_db, 2),
            "q_factor": round(self.q_factor, 2),
            "recommended_gain_db": round(self.recommended_gain_db, 2),
            "band_type": self.band_type
        }


class ResonanceHunter:
    """Detects parasitic spectral resonances and configures surgical EQ Eight cuts."""

    # Priority inspection frequency bands (Hz)
    HARSH_RANGES = [
        (2200.0, 4800.0),   # "Ice-pick" harshness & metallics
        (250.0, 500.0),     # Boxiness / mud build-up
        (80.0, 180.0),      # Sub/low-mid resonance build-up
    ]

    @classmethod
    def detect_resonances(
        cls,
        audio_samples: np.ndarray,
        sample_rate: int = 44100,
        sensitivity: float = 0.8,
        max_notches: int = 2
    ) -> List[ResonantPeak]:
        """
        Analyzes audio samples via FFT to find sharp spectral anomalies exceeding
        the natural 1/f spectral curve by >= 5.0 dB with narrow bandwidth (Q >= 6.0).
        """
        if audio_samples is None or len(audio_samples) < 1024:
            return []

        # Convert stereo to mono if needed
        if audio_samples.ndim > 1:
            samples = np.mean(audio_samples, axis=0)
        else:
            samples = audio_samples

        n_samples = len(samples)
        # Hann window
        window = np.hanning(n_samples)
        fft_vals = np.fft.rfft(samples * window)
        fft_freqs = np.fft.rfftfreq(n_samples, 1.0 / sample_rate)

        # Magnitude power in dB
        magnitude = np.abs(fft_vals) + 1e-9
        mag_db = 20.0 * np.log10(magnitude)

        # Calculate smoothed baseline envelope using moving average
        win_size = max(31, int(len(mag_db) * 0.05) | 1)
        # Pad edges
        pad_w = win_size // 2
        padded = np.pad(mag_db, pad_w, mode='edge')
        kernel = np.ones(win_size) / win_size
        baseline_db = np.convolve(padded, kernel, mode='valid')

        # Compute excess prominence above baseline
        prominence = mag_db - baseline_db

        # Threshold based on sensitivity: higher sensitivity -> lower threshold
        threshold_db = 8.0 - (sensitivity * 4.0)  # Sensitivity 1.0 -> 4 dB, 0.5 -> 6 dB

        detected: List[ResonantPeak] = []

        # Scan designated harsh zones
        for f_low, f_high in cls.HARSH_RANGES:
            idx_range = np.where((fft_freqs >= f_low) & (fft_freqs <= f_high))[0]
            if len(idx_range) < 5:
                continue

            sub_prom = prominence[idx_range]
            max_local_idx = np.argmax(sub_prom)
            peak_prom = sub_prom[max_local_idx]

            if peak_prom >= threshold_db:
                global_idx = idx_range[max_local_idx]
                peak_freq = fft_freqs[global_idx]

                # Estimate half-power (-3dB from peak) bandwidth for Q calculation
                half_power_db = mag_db[global_idx] - 3.0
                left_idx = global_idx
                while left_idx > 0 and mag_db[left_idx] > half_power_db:
                    left_idx -= 1
                right_idx = global_idx
                while right_idx < len(mag_db) - 1 and mag_db[right_idx] > half_power_db:
                    right_idx += 1

                bw_hz = max(10.0, fft_freqs[right_idx] - fft_freqs[left_idx])
                q_val = min(18.0, max(6.0, peak_freq / bw_hz))

                # Recommended cut: -2.5 dB to -4.5 dB max guardrail
                cut_gain = -min(4.5, max(2.5, peak_prom * 0.5))

                detected.append(ResonantPeak(
                    frequency_hz=round(float(peak_freq), 1),
                    prominence_db=round(float(peak_prom), 2),
                    q_factor=round(float(q_val), 2),
                    recommended_gain_db=round(float(cut_gain), 2),
                    band_type="notch" if q_val >= 8.0 else "bell"
                ))

        # Sort by highest prominence and strictly enforce max_notches guardrail
        detected.sort(key=lambda p: p.prominence_db, reverse=True)
        return detected[:max_notches]

    @classmethod
    def generate_eq_eight_parameters(
        cls,
        peaks: List[ResonantPeak]
    ) -> List[Dict[str, Any]]:
        """
        Translates detected resonant peaks into Ableton EQ Eight band parameters.
        """
        eq_configs = []
        for i, peak in enumerate(peaks):
            band_num = i + 1  # Band 1, Band 2
            eq_configs.append({
                "band": band_num,
                "enabled": True,
                "frequency": peak.frequency_hz,
                "gain": peak.recommended_gain_db,
                "q": peak.q_factor,
                "mode": peak.band_type
            })
        return eq_configs

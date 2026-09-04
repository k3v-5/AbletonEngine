"""
Cross-Track Envelope & Spectral Correlation Engine (PIE Phase 7).
Computes deterministic Pearson correlation, lag alignment, and
source-attribution correlation across multitrack stems.
"""
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import math

from .exceptions import InvalidAudioError, ForensicsIntegrityError
from .models import ForensicEvent


class CorrelationEngine:
    """
    Deterministic correlation analysis across tracks for causal source attribution
    and phase/bleed diagnostic checks.
    """

    @staticmethod
    def _validate_signal(audio: np.ndarray, name: str) -> np.ndarray:
        if not isinstance(audio, np.ndarray):
            raise InvalidAudioError(f"Signal '{name}' must be a numpy.ndarray, got {type(audio)}")
        if audio.ndim == 2:
            # Average stereo to mono for correlation
            audio = np.mean(audio, axis=0)
        elif audio.ndim != 1:
            raise InvalidAudioError(f"Signal '{name}' must have 1 or 2 dimensions, got shape {audio.shape}")
        if audio.size == 0:
            raise InvalidAudioError(f"Signal '{name}' cannot be empty.")
        if not np.all(np.isfinite(audio)):
            raise InvalidAudioError(f"Signal '{name}' contains non-finite values (NaN or Inf).")
        return audio

    @classmethod
    def compute_envelope(cls, signal: np.ndarray, window_size: int = 256) -> np.ndarray:
        """Computes moving RMS envelope of a 1D audio signal."""
        squared = signal ** 2
        window = np.ones(window_size) / window_size
        env = np.sqrt(np.convolve(squared, window, mode="same") + 1e-12)
        return env

    @classmethod
    def calculate_pearson_correlation(cls, x: np.ndarray, y: np.ndarray) -> float:
        """Calculates normalized Pearson correlation coefficient between two 1D series."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0

        x_slice = x[:n] - np.mean(x[:n])
        y_slice = y[:n] - np.mean(y[:n])

        norm_x = np.linalg.norm(x_slice)
        norm_y = np.linalg.norm(y_slice)

        if norm_x < 1e-12 or norm_y < 1e-12:
            return 0.0

        corr = float(np.dot(x_slice, y_slice) / (norm_x * norm_y))
        return float(np.clip(corr, -1.0, 1.0))

    @classmethod
    def calculate_lag_correlation(
        cls,
        x: np.ndarray,
        y: np.ndarray,
        sample_rate: int,
        max_lag_ms: float = 50.0,
    ) -> Tuple[float, float]:
        """
        Calculates maximum correlation and optimal lag in milliseconds within +/- max_lag_ms.
        Returns: (max_correlation, optimal_lag_ms)
        """
        x_mono = cls._validate_signal(x, "x")
        y_mono = cls._validate_signal(y, "y")

        n = min(len(x_mono), len(y_mono))
        x_slice = x_mono[:n]
        y_slice = y_mono[:n]

        max_lag_samples = int((max_lag_ms / 1000.0) * sample_rate)
        if max_lag_samples <= 0 or n <= max_lag_samples * 2:
            corr = cls.calculate_pearson_correlation(x_slice, y_slice)
            return corr, 0.0

        corr_full = np.correlate(x_slice, y_slice, mode="full")
        lags = np.arange(-n + 1, n)

        center_idx = n - 1
        valid_range = slice(center_idx - max_lag_samples, center_idx + max_lag_samples + 1)
        sub_corr = corr_full[valid_range]
        sub_lags = lags[valid_range]

        norm = (np.linalg.norm(x_slice) * np.linalg.norm(y_slice)) + 1e-12
        sub_corr_norm = sub_corr / norm

        best_idx = int(np.argmax(np.abs(sub_corr_norm)))
        best_corr = float(np.clip(sub_corr_norm[best_idx], -1.0, 1.0))
        best_lag_samples = int(sub_lags[best_idx])
        # Positive lag indicates signal y is delayed relative to signal x
        best_lag_ms = float((-best_lag_samples / sample_rate) * 1000.0)


        return best_corr, best_lag_ms

    @classmethod
    def attribute_event_to_sources(
        cls,
        event: ForensicEvent,
        stems: Dict[str, np.ndarray],
        sample_rate: int,
        window_padding_ms: float = 20.0,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Attributes an event (e.g. Master clipping or resonance) to the candidate stems
        by computing localized energy and envelope correlation during the event interval.
        Returns list of (stem_name, attribution_score, stats) sorted descending.
        """
        if not stems:
            return []

        pad_samples = int((window_padding_ms / 1000.0) * sample_rate)
        start_sample = max(0, int(event.start_time_seconds * sample_rate) - pad_samples)
        end_sample = int(event.end_time_seconds * sample_rate) + pad_samples

        scores: List[Tuple[str, float, Dict[str, Any]]] = []

        for stem_name, stem_audio in stems.items():
            mono = cls._validate_signal(stem_audio, stem_name)
            if len(mono) <= start_sample:
                scores.append((stem_name, 0.0, {"energy_dbfs": -100.0, "peak_dbfs": -100.0}))
                continue

            event_slice = mono[start_sample:min(len(mono), end_sample)]
            if len(event_slice) == 0:
                scores.append((stem_name, 0.0, {"energy_dbfs": -100.0, "peak_dbfs": -100.0}))
                continue

            rms = float(np.sqrt(np.mean(event_slice ** 2))) + 1e-12
            rms_db = float(20.0 * np.log10(rms))
            peak = float(np.max(np.abs(event_slice))) + 1e-12
            peak_db = float(20.0 * np.log10(peak))

            # Score combines absolute energy (how loud is the stem during the event)
            # normalized to 0.0 - 1.0 range (assuming active range -60 to 0 dBFS)
            energy_score = max(0.0, min(1.0, (rms_db + 60.0) / 60.0))
            peak_score = max(0.0, min(1.0, (peak_db + 40.0) / 40.0))

            combined_score = 0.6 * energy_score + 0.4 * peak_score

            scores.append((
                stem_name,
                float(round(combined_score, 4)),
                {
                    "energy_dbfs": round(rms_db, 2),
                    "peak_dbfs": round(peak_db, 2),
                    "samples_evaluated": len(event_slice)
                }
            ))

        return sorted(scores, key=lambda item: item[1], reverse=True)

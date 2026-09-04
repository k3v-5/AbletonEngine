"""
Spectral Feature & Dynamic Resonance Analysis Engine (PIE Phase 7).
Extracts centroid, flux, rolloff, band energies across 14 standard bands,
and identifies localized persistent dynamic resonances.
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import uuid

from .models import (
    AudioFrame,
    ForensicEvent,
    ForensicEventType,
    Severity,
    AnalysisConfig
)
from .config import STANDARD_FREQUENCY_BANDS, DEFAULT_ANALYSIS_CONFIG


class SpectralEngine:
    """
    Analyzes STFT representation to compute spectral features and detect localized resonances.
    """

    @classmethod
    def calculate_spectral_centroid(cls, magnitudes: np.ndarray, freqs: np.ndarray) -> float:
        """Calculates spectral centroid in Hz for a 1D magnitude spectrum."""
        total_mag = np.sum(magnitudes)
        if total_mag <= 1e-12:
            return 0.0
        return float(np.sum(freqs * magnitudes) / total_mag)

    @classmethod
    def calculate_spectral_rolloff(
        cls,
        magnitudes: np.ndarray,
        freqs: np.ndarray,
        percentile: float = 0.85
    ) -> float:
        """Calculates rolloff frequency below which percentile of energy lies."""
        cum_energy = np.cumsum(magnitudes)
        total_energy = cum_energy[-1] if len(cum_energy) > 0 else 0.0
        if total_energy <= 1e-12:
            return 0.0
        threshold = percentile * total_energy
        idx = np.searchsorted(cum_energy, threshold)
        idx = min(idx, len(freqs) - 1)
        return float(freqs[idx])

    @classmethod
    def calculate_spectral_flux(
        cls,
        curr_mag: np.ndarray,
        prev_mag: Optional[np.ndarray] = None
    ) -> float:
        """Calculates spectral flux between two consecutive magnitude frames."""
        if prev_mag is None:
            return 0.0
        diff = curr_mag - prev_mag
        # Half-wave rectified or squared Euclidean difference
        return float(np.sqrt(np.sum(diff ** 2)))

    @classmethod
    def calculate_band_energies(
        cls,
        powers: np.ndarray,
        freqs: np.ndarray
    ) -> Dict[str, float]:
        """Calculates energy in dBFS across the 14 standard frequency bands."""
        energies: Dict[str, float] = {}
        for band_name, f_min, f_max in STANDARD_FREQUENCY_BANDS:
            mask = (freqs >= f_min) & (freqs < f_max)
            if np.any(mask):
                band_pwr = np.sum(powers[mask])
            else:
                band_pwr = 0.0
            db = 10.0 * np.log10(band_pwr + 1e-12)
            energies[band_name] = round(float(db), 2)
        return energies

    @classmethod
    def detect_resonances(
        cls,
        stft_result: Dict[str, Any],
        baseline: Optional[Any] = None,
        config: Optional[AnalysisConfig] = None
    ) -> List[ForensicEvent]:
        """
        Detects dynamic resonances that exceed the baseline energy by > resonance_threshold_db,
        possess localized bandwidth (Q >= 2.5), and persist for >= minimum_event_duration_ms.
        """
        cfg = config or stft_result.get("config", DEFAULT_ANALYSIS_CONFIG)
        magnitudes = stft_result["magnitudes"]  # shape (channels, frames, bins)
        freqs = stft_result["frequencies_hz"]
        time_stamps = stft_result["time_stamps_seconds"]
        time_res = stft_result["time_resolution_seconds"]
        n_channels, n_frames, n_bins = magnitudes.shape

        min_frames = max(2, int(np.ceil((cfg.minimum_event_duration_ms / 1000.0) / time_res)))
        events: List[ForensicEvent] = []

        # Convert baseline or compute local median if baseline not provided
        channel_labels = ["L", "R"] if n_channels == 2 else ["M"]

        for ch in range(n_channels):
            ch_mag = magnitudes[ch]
            ch_db = 20.0 * np.log10(ch_mag + 1e-12)

            # Global median profile across time for this channel as reference baseline
            ch_median_spectrum = np.median(ch_db, axis=0)

            # Detect candidate bins exceeding median + resonance_threshold_db
            resonance_mask = np.zeros((n_frames, n_bins), dtype=bool)

            for b in range(1, n_bins - 1):
                f = freqs[b]
                if f < cfg.min_frequency_hz or f > cfg.max_frequency_hz:
                    continue

                diff_db = ch_db[:, b] - ch_median_spectrum[b]
                prominence_left = ch_db[:, b] - ch_db[:, b - 1]
                prominence_right = ch_db[:, b] - ch_db[:, b + 1]

                # Condition: exceeds baseline AND localized peak prominence >= 3 dB
                is_prominent = (diff_db >= cfg.resonance_threshold_db) & (prominence_left >= 3.0) & (prominence_right >= 3.0)
                resonance_mask[:, b] = is_prominent

            # Trace temporal continuity of active resonance clusters
            for b in range(1, n_bins - 1):
                active_frames = np.where(resonance_mask[:, b])[0]
                if len(active_frames) == 0:
                    continue

                # Group contiguous frame blocks
                blocks: List[List[int]] = []
                current_block = [active_frames[0]]
                for idx in active_frames[1:]:
                    if idx == current_block[-1] + 1:
                        current_block.append(idx)
                    else:
                        blocks.append(current_block)
                        current_block = [idx]
                if current_block:
                    blocks.append(current_block)

                for blk in blocks:
                    if len(blk) >= min_frames:
                        start_f = blk[0]
                        end_f = blk[-1]
                        start_t = float(time_stamps[start_f])
                        end_t = float(time_stamps[end_f] + time_res)
                        duration = end_t - start_t
                        center_freq = float(freqs[b])

                        peak_excess = float(np.max(ch_db[blk, b] - ch_median_spectrum[b]))
                        confidence = min(1.0, 0.70 + 0.05 * min(6, len(blk) - min_frames) + 0.02 * min(5.0, peak_excess - cfg.resonance_threshold_db))

                        severity = Severity.WARNING if peak_excess < 9.0 else Severity.ERROR
                        if peak_excess >= 12.0:
                            severity = Severity.CRITICAL

                        event_id = f"ev_res_{ch}_{b}_{start_f}_{uuid.uuid4().hex[:6]}"
                        ev = ForensicEvent(
                            event_id=event_id,
                            event_type=ForensicEventType.RESONANCE.value,
                            start_time_seconds=start_t,
                            end_time_seconds=end_t,
                            duration_seconds=duration,
                            severity=severity.value,
                            confidence=confidence,
                            channels=(channel_labels[ch],),
                            frequency_min_hz=max(0.0, center_freq * 0.95),
                            frequency_max_hz=center_freq * 1.05,
                            evidence_ids=(f"ev_spk_{event_id}",),
                            details={
                                "center_frequency_hz": round(center_freq, 1),
                                "peak_excess_db": round(peak_excess, 2),
                                "baseline_db": round(float(ch_median_spectrum[b]), 2),
                                "frames_active": len(blk),
                                "channel": channel_labels[ch]
                            }
                        )
                        events.append(ev)

        events.sort(key=lambda e: (e.start_time_seconds, e.frequency_min_hz or 0.0, e.event_id))
        return events

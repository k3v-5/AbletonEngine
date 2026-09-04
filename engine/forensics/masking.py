"""
Dynamic Spectral Masking Engine (PIE Phase 7).
Detects time-localized frequency masking and spectral collision between
audio stems (e.g., Kick vs Bass, Vocal vs Instruments).
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import math

from .models import ForensicEvent, ForensicEventType, Severity, AnalysisConfig
from .config import STANDARD_FREQUENCY_BANDS, DEFAULT_ANALYSIS_CONFIG
from .stft import STFTEngine
from .spectral import SpectralEngine
from .exceptions import InvalidAudioError, ForensicsIntegrityError


class MaskingEngine:
    """
    Deterministic detector of time-frequency spectral collision and acoustic masking
    between multi-track stems.
    """

    @staticmethod
    def _validate_stem(audio: np.ndarray, name: str) -> np.ndarray:
        if not isinstance(audio, np.ndarray):
            raise InvalidAudioError(f"Stem '{name}' must be a numpy.ndarray, got {type(audio)}")
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        elif audio.ndim != 2:
            raise InvalidAudioError(f"Stem '{name}' must have 1 or 2 dimensions, got shape {audio.shape}")
        if audio.shape[0] not in (1, 2):
            raise InvalidAudioError(f"Stem '{name}' must have 1 or 2 channels, got {audio.shape[0]}")
        if audio.size == 0:
            raise InvalidAudioError(f"Stem '{name}' buffer cannot be empty.")
        if not np.all(np.isfinite(audio)):
            raise InvalidAudioError(f"Stem '{name}' contains non-finite values (NaN or Inf).")
        return audio

    @classmethod
    def detect_masking(
        cls,
        stem_a: np.ndarray,
        stem_b: np.ndarray,
        sample_rate: int,
        stem_a_name: str = "Stem_A",
        stem_b_name: str = "Stem_B",
        config: Optional[AnalysisConfig] = None,
        clash_threshold_db: float = 6.0,
        activity_threshold_db: float = -45.0,
    ) -> List[ForensicEvent]:
        """
        Detects time-frequency masking between two stems across standard spectral bands.
        clash_threshold_db: maximum energy difference (dB) for signals to be considered competing.
        activity_threshold_db: minimum energy (dBFS) for a stem to be considered actively competing.
        """
        cfg = config or DEFAULT_ANALYSIS_CONFIG
        if sample_rate <= 0:
            raise InvalidAudioError(f"Sample rate must be positive, got {sample_rate}")

        stem_a = cls._validate_stem(stem_a, stem_a_name)
        stem_b = cls._validate_stem(stem_b, stem_b_name)

        # Match lengths
        common_len = min(stem_a.shape[1], stem_b.shape[1])
        if common_len < cfg.fft_size:
            return []

        stem_a_aligned = stem_a[:, :common_len]
        stem_b_aligned = stem_b[:, :common_len]

        # Compute STFT for both stems
        stft_a = STFTEngine.compute_stft(stem_a_aligned, sample_rate, cfg)
        stft_b = STFTEngine.compute_stft(stem_b_aligned, sample_rate, cfg)

        powers_a = stft_a["powers"]  # (ch, frames, bins)
        powers_b = stft_b["powers"]
        freqs = stft_a["frequencies_hz"]
        time_stamps = stft_a["time_stamps_seconds"]
        time_res = stft_a["time_resolution_seconds"]
        n_frames = min(powers_a.shape[1], powers_b.shape[1])

        # Sum powers across channels for mono spectral analysis
        mono_pwr_a = np.mean(powers_a, axis=0)[:n_frames]  # (frames, bins)
        mono_pwr_b = np.mean(powers_b, axis=0)[:n_frames]

        min_frames = max(2, int(math.ceil((cfg.minimum_event_duration_ms / 1000.0) / time_res)))
        events: List[ForensicEvent] = []
        event_counter = 1

        for band_name, f_min, f_max in STANDARD_FREQUENCY_BANDS:
            mask = (freqs >= f_min) & (freqs < f_max)
            if not np.any(mask):
                continue

            # Band energy across time for both stems
            band_pwr_a = np.sum(mono_pwr_a[:, mask], axis=1)
            band_pwr_b = np.sum(mono_pwr_b[:, mask], axis=1)

            band_db_a = 10.0 * np.log10(band_pwr_a + 1e-12)
            band_db_b = 10.0 * np.log10(band_pwr_b + 1e-12)

            # Both active and energy delta <= clash_threshold_db
            is_active = (band_db_a >= activity_threshold_db) & (band_db_b >= activity_threshold_db)
            diff_db = np.abs(band_db_a - band_db_b)
            clash_mask = is_active & (diff_db <= clash_threshold_db)

            clash_indices = np.where(clash_mask)[0]
            if len(clash_indices) == 0:
                continue

            # Cluster consecutive clashing frames
            max_gap_frames = max(1, int(cfg.maximum_event_gap_ms / 1000.0 / time_res))
            clusters: List[List[int]] = []
            curr: List[int] = [int(clash_indices[0])]

            for idx in clash_indices[1:]:
                idx = int(idx)
                if idx - curr[-1] <= max_gap_frames:
                    curr.append(idx)
                else:
                    clusters.append(curr)
                    curr = [idx]
            if curr:
                clusters.append(curr)

            for cluster in clusters:
                if len(cluster) >= min_frames:
                    start_frame = cluster[0]
                    end_frame = cluster[-1]
                    start_time = float(time_stamps[start_frame])
                    end_time = float(time_stamps[end_frame] + time_res)
                    duration = float(end_time - start_time)

                    mean_a = float(np.mean(band_db_a[cluster]))
                    mean_b = float(np.mean(band_db_b[cluster]))
                    mean_diff = float(np.mean(diff_db[cluster]))

                    dominant = stem_a_name if mean_a >= mean_b else stem_b_name
                    masked = stem_b_name if dominant == stem_a_name else stem_a_name

                    # Severity: low-end or mids masking is more destructive than brilliance
                    is_critical_band = f_min <= 500.0
                    if duration >= 0.500 or (is_critical_band and duration >= 0.250):
                        severity = Severity.CRITICAL
                    elif duration >= 0.150:
                        severity = Severity.ERROR
                    else:
                        severity = Severity.WARNING

                    confidence = min(1.0, 0.75 + 0.25 * (1.0 - mean_diff / clash_threshold_db))

                    event = ForensicEvent(
                        event_id=f"ev_mask_{band_name.lower()}_{event_counter:04d}_{int(start_time * 1000)}ms",
                        event_type=ForensicEventType.MASKING,
                        start_time_seconds=start_time,
                        end_time_seconds=end_time,
                        duration_seconds=duration,
                        severity=severity,
                        confidence=confidence,
                        channels=("L", "R") if stem_a.shape[0] == 2 or stem_b.shape[0] == 2 else ("M",),
                        frequency_min_hz=float(f_min),
                        frequency_max_hz=float(f_max),
                        evidence_ids=(f"mask_frames_{start_frame}_{end_frame}",),
                        details={
                            "band_name": band_name,
                            "stem_a": stem_a_name,
                            "stem_b": stem_b_name,
                            "dominant_stem": dominant,
                            "masked_stem": masked,
                            "stem_a_mean_dbfs": round(mean_a, 2),
                            "stem_b_mean_dbfs": round(mean_b, 2),
                            "mean_delta_db": round(mean_diff, 2),
                            "clash_frames_count": len(cluster),
                        }
                    )
                    events.append(event)
                    event_counter += 1

        return sorted(events, key=lambda e: (e.start_time_seconds, e.frequency_min_hz or 0.0))

    @classmethod
    def analyze_multitrack(
        cls,
        stems: Dict[str, np.ndarray],
        sample_rate: int,
        config: Optional[AnalysisConfig] = None,
        clash_threshold_db: float = 6.0,
    ) -> List[ForensicEvent]:
        """
        Analyzes pairwise spectral masking across a multitrack dictionary of stems.
        """
        stem_keys = sorted(stems.keys())
        all_events: List[ForensicEvent] = []

        for i in range(len(stem_keys)):
            for j in range(i + 1, len(stem_keys)):
                key_a = stem_keys[i]
                key_b = stem_keys[j]
                pair_events = cls.detect_masking(
                    stem_a=stems[key_a],
                    stem_b=stems[key_b],
                    sample_rate=sample_rate,
                    stem_a_name=key_a,
                    stem_b_name=key_b,
                    config=config,
                    clash_threshold_db=clash_threshold_db,
                )
                all_events.extend(pair_events)

        return sorted(all_events, key=lambda e: (e.start_time_seconds, e.event_type))

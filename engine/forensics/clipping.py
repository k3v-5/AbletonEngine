"""
Temporal and Inter-Sample Clipping Detection Engine (PIE Phase 7).
Implements deterministic sample clipping clustering and ITU-R BS.1770-5
4x sinc-interpolated True Peak oversampling detection.
"""
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import math

from .models import ForensicEvent, ForensicEventType, Severity, AnalysisConfig
from .exceptions import InvalidAudioError, ForensicsIntegrityError


class ClippingEngine:
    """
    Deterministic detection of digital full-scale sample clipping and
    inter-sample reconstructed True Peak overshoots.
    """

    @staticmethod
    def _validate_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        if not isinstance(audio, np.ndarray):
            raise InvalidAudioError(f"Audio must be a numpy.ndarray, got {type(audio)}")
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        elif audio.ndim != 2:
            raise InvalidAudioError(f"Audio must have 1 or 2 dimensions, got shape {audio.shape}")
        if audio.shape[0] not in (1, 2):
            raise InvalidAudioError(f"Forensics supports 1 or 2 channels, got {audio.shape[0]}")
        if audio.size == 0:
            raise InvalidAudioError("Audio buffer cannot be empty.")
        if not np.all(np.isfinite(audio)):
            raise InvalidAudioError("Audio buffer contains non-finite values (NaN or Inf).")
        if sample_rate <= 0:
            raise InvalidAudioError(f"Sample rate must be positive, got {sample_rate}")
        return audio

    @classmethod
    def detect_sample_clipping(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        threshold_dbfs: float = -0.01,
        max_gap_ms: float = 10.0,
        min_duration_ms: float = 0.0,
    ) -> List[ForensicEvent]:
        """
        Detects digital full-scale sample clipping and clusters adjacent clipped
        samples into continuous ForensicEvents.
        """
        audio = cls._validate_audio(audio, sample_rate)
        linear_thresh = 10.0 ** (threshold_dbfs / 20.0)
        gap_samples = int(math.ceil((max_gap_ms / 1000.0) * sample_rate))
        min_samples = int(math.floor((min_duration_ms / 1000.0) * sample_rate))

        events: List[ForensicEvent] = []
        channel_names = ("L", "R") if audio.shape[0] == 2 else ("M",)

        event_counter = 1

        for ch_idx, ch_name in enumerate(channel_names):
            channel_data = np.abs(audio[ch_idx])
            clipped_indices = np.where(channel_data >= linear_thresh)[0]

            if len(clipped_indices) == 0:
                continue

            # Cluster adjacent or near indices
            clusters: List[List[int]] = []
            current_cluster: List[int] = [int(clipped_indices[0])]

            for idx in clipped_indices[1:]:
                idx = int(idx)
                if idx - current_cluster[-1] <= gap_samples + 1:
                    current_cluster.append(idx)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [idx]
            if current_cluster:
                clusters.append(current_cluster)

            # Build ForensicEvent for each cluster
            for cluster in clusters:
                start_sample = cluster[0]
                end_sample = cluster[-1]
                duration_samples = end_sample - start_sample + 1

                if duration_samples < min_samples:
                    continue

                start_time = float(start_sample / sample_rate)
                end_time = float((end_sample + 1) / sample_rate)
                duration = float(end_time - start_time)

                cluster_vals = channel_data[cluster]
                max_val = float(np.max(cluster_vals))
                peak_dbfs = float(20.0 * np.log10(max_val + 1e-12))
                num_clipped = len(cluster)

                # Severity heuristic
                if num_clipped >= 20 or duration >= 0.005:
                    severity = Severity.CRITICAL
                elif num_clipped >= 4 or duration >= 0.001:
                    severity = Severity.ERROR
                else:
                    severity = Severity.WARNING

                # Confidence
                confidence = min(1.0, 0.7 + 0.3 * (num_clipped / max(num_clipped, 10)))

                event_id = f"ev_clip_{ch_name}_{event_counter:04d}_{int(start_time * 1000)}ms"
                event_counter += 1

                event = ForensicEvent(
                    event_id=event_id,
                    event_type=ForensicEventType.CLIPPING,
                    start_time_seconds=start_time,
                    end_time_seconds=end_time,
                    duration_seconds=duration,
                    severity=severity,
                    confidence=confidence,
                    channels=(ch_name,),
                    frequency_min_hz=20.0,
                    frequency_max_hz=float(sample_rate / 2.0),
                    evidence_ids=(f"samples_{start_sample}_{end_sample}",),
                    details={
                        "channel": ch_name,
                        "sample_count": num_clipped,
                        "start_sample": start_sample,
                        "end_sample": end_sample,
                        "peak_dbfs": round(peak_dbfs, 3),
                        "threshold_dbfs": round(threshold_dbfs, 3),
                        "is_inter_sample": False,
                    }
                )
                events.append(event)

        return sorted(events, key=lambda e: e.start_time_seconds)

    @classmethod
    def detect_true_peak_clipping(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        threshold_dbtp: float = 0.0,
        oversample_factor: int = 4,
        max_gap_ms: float = 10.0,
    ) -> List[ForensicEvent]:
        """
        Calculates 4x oversampled True Peak continuous signal according to
        ITU-R BS.1770-5 Annex 2, detecting inter-sample peak overshoots.
        """
        audio = cls._validate_audio(audio, sample_rate)
        linear_thresh = 10.0 ** (threshold_dbtp / 20.0)

        # Design 4x sinc interpolation filter with Hann window
        half_len = 16
        k = np.arange(-half_len * oversample_factor, half_len * oversample_factor + 1)
        sinc = np.sinc(k / oversample_factor)
        win = np.hanning(len(k))
        h = sinc * win
        h = h * oversample_factor / np.sum(h)

        events: List[ForensicEvent] = []
        channel_names = ("L", "R") if audio.shape[0] == 2 else ("M",)
        oversampled_sr = sample_rate * oversample_factor
        gap_samples = int(math.ceil((max_gap_ms / 1000.0) * oversampled_sr))

        event_counter = 1

        for ch_idx, ch_name in enumerate(channel_names):
            x = audio[ch_idx].astype(np.float64)
            x_up = np.zeros(len(x) * oversample_factor, dtype=np.float64)
            x_up[::oversample_factor] = x

            interpolated = np.convolve(x_up, h, mode="same")
            abs_interp = np.abs(interpolated)

            over_indices = np.where(abs_interp > linear_thresh)[0]
            if len(over_indices) == 0:
                continue

            # Cluster oversampled peak points
            clusters: List[List[int]] = []
            current_cluster: List[int] = [int(over_indices[0])]

            for idx in over_indices[1:]:
                idx = int(idx)
                if idx - current_cluster[-1] <= gap_samples + 1:
                    current_cluster.append(idx)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [idx]
            if current_cluster:
                clusters.append(current_cluster)

            for cluster in clusters:
                start_s = cluster[0]
                end_s = cluster[-1]
                start_time = float(start_s / oversampled_sr)
                end_time = float((end_s + 1) / oversampled_sr)
                duration = float(end_time - start_time)

                max_val = float(np.max(abs_interp[cluster]))
                peak_dbtp = float(20.0 * np.log10(max_val + 1e-12))
                overshoot_db = float(peak_dbtp - threshold_dbtp)

                if overshoot_db >= 1.0:
                    severity = Severity.CRITICAL
                elif overshoot_db >= 0.2:
                    severity = Severity.ERROR
                else:
                    severity = Severity.WARNING

                confidence = min(1.0, 0.85 + 0.15 * min(1.0, overshoot_db))

                event_id = f"ev_isp_{ch_name}_{event_counter:04d}_{int(start_time * 1000)}ms"
                event_counter += 1

                event = ForensicEvent(
                    event_id=event_id,
                    event_type=ForensicEventType.INTER_SAMPLE_PEAK,
                    start_time_seconds=start_time,
                    end_time_seconds=end_time,
                    duration_seconds=duration,
                    severity=severity,
                    confidence=confidence,
                    channels=(ch_name,),
                    frequency_min_hz=20.0,
                    frequency_max_hz=float(sample_rate / 2.0),
                    evidence_ids=(f"isp_samples_{start_s}_{end_s}",),
                    details={
                        "channel": ch_name,
                        "true_peak_dbtp": round(peak_dbtp, 3),
                        "overshoot_db": round(overshoot_db, 3),
                        "threshold_dbtp": round(threshold_dbtp, 3),
                        "oversample_factor": oversample_factor,
                        "is_inter_sample": True,
                    }
                )
                events.append(event)

        return sorted(events, key=lambda e: e.start_time_seconds)

    @classmethod
    def analyze(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        config: Optional[AnalysisConfig] = None,
    ) -> List[ForensicEvent]:
        """
        Runs comprehensive clipping and True Peak analysis using provided or default config.
        """
        cfg = config or AnalysisConfig()
        sample_events = cls.detect_sample_clipping(
            audio=audio,
            sample_rate=sample_rate,
            threshold_dbfs=cfg.clipping_threshold_dbfs,
            max_gap_ms=cfg.maximum_event_gap_ms,
            min_duration_ms=0.0
        )
        isp_events = cls.detect_true_peak_clipping(
            audio=audio,
            sample_rate=sample_rate,
            threshold_dbtp=0.0,
            oversample_factor=4,
            max_gap_ms=cfg.maximum_event_gap_ms
        )

        all_events = sample_events + isp_events
        return sorted(all_events, key=lambda e: (e.start_time_seconds, e.event_type))

"""
Acoustic Anomaly Detection Engine (PIE Phase 7).
Implements deterministic detection of DC offset, clicks, pops,
dropouts, channel loss, and stereo phase cancellation anomalies.
"""
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import math

from .models import ForensicEvent, ForensicEventType, Severity, AnalysisConfig, AudioFrame
from .exceptions import InvalidAudioError, ForensicsIntegrityError


class AnomalyEngine:
    """
    Deterministic detector for acoustic defects: DC offset, transient impulses
    (clicks/pops), dropouts, channel asymmetry/loss, and negative phase correlation.
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
    def detect_dc_offset(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        threshold: float = 0.005,
    ) -> List[ForensicEvent]:
        """
        Detects continuous DC offset across audio channels.
        threshold: linear offset threshold (0.005 = approx -46 dBFS).
        """
        audio = cls._validate_audio(audio, sample_rate)
        events: List[ForensicEvent] = []
        channel_names = ("L", "R") if audio.shape[0] == 2 else ("M",)
        total_duration = float(audio.shape[1] / sample_rate)

        for ch_idx, ch_name in enumerate(channel_names):
            ch_data = audio[ch_idx]
            mean_val = float(np.mean(ch_data))
            abs_mean = abs(mean_val)

            if abs_mean >= threshold:
                offset_dbfs = float(20.0 * np.log10(abs_mean + 1e-12))
                severity = Severity.ERROR if abs_mean >= 0.02 else Severity.WARNING
                confidence = min(1.0, 0.75 + 0.25 * min(1.0, abs_mean / 0.05))

                event = ForensicEvent(
                    event_id=f"ev_dc_{ch_name}_{int(abs_mean * 10000)}",
                    event_type=ForensicEventType.DC_OFFSET,
                    start_time_seconds=0.0,
                    end_time_seconds=total_duration,
                    duration_seconds=total_duration,
                    severity=severity,
                    confidence=confidence,
                    channels=(ch_name,),
                    frequency_min_hz=0.0,
                    frequency_max_hz=5.0,
                    evidence_ids=(f"dc_meas_{ch_name}",),
                    details={
                        "channel": ch_name,
                        "dc_offset_linear": round(mean_val, 6),
                        "dc_offset_dbfs": round(offset_dbfs, 2),
                        "threshold_linear": round(threshold, 6),
                    }
                )
                events.append(event)

        return events

    @classmethod
    def detect_clicks_and_pops(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        diff_threshold: float = 0.35,
        max_duration_ms: float = 25.0,
    ) -> List[ForensicEvent]:
        """
        Detects localized transient impulse anomalies (clicks < 3ms, pops 3-25ms)
        via high derivative and immediate decay signatures.
        """
        audio = cls._validate_audio(audio, sample_rate)
        events: List[ForensicEvent] = []
        channel_names = ("L", "R") if audio.shape[0] == 2 else ("M",)
        event_counter = 1

        for ch_idx, ch_name in enumerate(channel_names):
            ch_data = audio[ch_idx]
            if len(ch_data) < 4:
                continue

            # Compute first difference (discrete derivative)
            diffs = np.abs(np.diff(ch_data))
            # Candidates exceeding derivative threshold
            spike_indices = np.where(diffs > diff_threshold)[0]

            if len(spike_indices) == 0:
                continue

            # Group adjacent spikes (within 5ms)
            group_gap = int(0.005 * sample_rate)
            clusters: List[List[int]] = []
            current: List[int] = [int(spike_indices[0])]

            for idx in spike_indices[1:]:
                idx = int(idx)
                if idx - current[-1] <= group_gap:
                    current.append(idx)
                else:
                    clusters.append(current)
                    current = [idx]
            if current:
                clusters.append(current)

            for cluster in clusters:
                start_s = cluster[0]
                end_s = cluster[-1]
                duration_s = max(1 / sample_rate, (end_s - start_s + 1) / sample_rate)
                duration_ms = duration_s * 1000.0

                if duration_ms > max_duration_ms:
                    continue  # Prolonged energetic event, not an impulse click/pop

                # Verify impulse characteristic: surrounding samples must be significantly lower
                pad = max(10, int(0.002 * sample_rate))
                pre_start = max(0, start_s - pad)
                post_end = min(len(ch_data), end_s + pad)

                impulse_peak = float(np.max(np.abs(ch_data[start_s:end_s + 1])))
                pre_rms = float(np.sqrt(np.mean(ch_data[pre_start:start_s] ** 2))) if start_s > pre_start else 0.0
                post_rms = float(np.sqrt(np.mean(ch_data[end_s + 1:post_end] ** 2))) if post_end > end_s + 1 else 0.0
                surrounding_max = max(pre_rms, post_rms)

                # Ratio of impulse to surrounding
                ratio = impulse_peak / (surrounding_max + 1e-4)
                if ratio < 2.5:
                    continue  # Part of continuous energetic signal, not an isolated click

                is_click = duration_ms < 3.0
                ev_type = ForensicEventType.CLICK if is_click else ForensicEventType.POP
                severity = Severity.WARNING if impulse_peak < 0.7 else Severity.ERROR
                confidence = min(1.0, 0.7 + 0.3 * min(1.0, ratio / 10.0))

                start_time = float(start_s / sample_rate)
                end_time = float((end_s + 1) / sample_rate)

                event = ForensicEvent(
                    event_id=f"ev_{ev_type.value.lower()}_{ch_name}_{event_counter:04d}_{int(start_time * 1000)}ms",
                    event_type=ev_type,
                    start_time_seconds=start_time,
                    end_time_seconds=end_time,
                    duration_seconds=duration_s,
                    severity=severity,
                    confidence=confidence,
                    channels=(ch_name,),
                    frequency_min_hz=1000.0 if is_click else 60.0,
                    frequency_max_hz=min(20000.0, float(sample_rate / 2.0)),
                    evidence_ids=(f"samples_{start_s}_{end_s}",),
                    details={
                        "channel": ch_name,
                        "impulse_peak": round(impulse_peak, 4),
                        "duration_ms": round(duration_ms, 2),
                        "surrounding_ratio": round(ratio, 2),
                    }
                )
                events.append(event)
                event_counter += 1

        return sorted(events, key=lambda e: e.start_time_seconds)

    @classmethod
    def detect_dropouts(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        drop_threshold_db: float = 30.0,
        min_duration_ms: float = 30.0,
    ) -> List[ForensicEvent]:
        """
        Detects dropouts: sudden unexpected collapse of audio energy (> drop_threshold_db)
        where signal was previously active, lasting >= min_duration_ms.
        """
        audio = cls._validate_audio(audio, sample_rate)
        events: List[ForensicEvent] = []
        channel_names = ("L", "R") if audio.shape[0] == 2 else ("M",)

        # Sliding window for short-term power
        win_size = int(0.010 * sample_rate)  # 10ms window
        hop_size = int(0.005 * sample_rate)  # 5ms hop
        if audio.shape[1] < win_size * 4:
            return events

        num_frames = (audio.shape[1] - win_size) // hop_size + 1
        event_counter = 1

        for ch_idx, ch_name in enumerate(channel_names):
            ch = audio[ch_idx]
            # Compute frame RMS dBFS
            rms_db_list = []
            for i in range(num_frames):
                s = i * hop_size
                block = ch[s:s + win_size]
                rms = float(np.sqrt(np.mean(block ** 2))) + 1e-12
                rms_db_list.append(20.0 * np.log10(rms))

            rms_db = np.array(rms_db_list)

            # Look for active frames (e.g. > -45 dBFS) followed by a sudden deep drop (< -70 dBFS or > drop_threshold_db drop)
            min_drop_frames = max(2, int(math.ceil((min_duration_ms / 1000.0) / (hop_size / sample_rate))))

            i = 2
            while i < num_frames - min_drop_frames - 2:
                pre_energy = float(np.max(rms_db[max(0, i - 4):i]))
                if pre_energy > -45.0:  # Audio was definitely active
                    # Check if there is an abrupt drop
                    drop_val = pre_energy - rms_db[i]
                    if drop_val >= drop_threshold_db or rms_db[i] < -75.0:
                        # Find how many frames this drop persists
                        drop_start_frame = i
                        while (
                            i < num_frames
                            and (pre_energy - rms_db[i] >= drop_threshold_db or rms_db[i] < -75.0)
                        ):
                            i += 1
                        drop_end_frame = i

                        duration_frames = drop_end_frame - drop_start_frame
                        if duration_frames >= min_drop_frames:
                            # Verify if audio resumes after (true dropout) or if it's end-of-track silence
                            post_energy = float(np.max(rms_db[drop_end_frame:min(num_frames, drop_end_frame + 6)])) if drop_end_frame < num_frames else -90.0
                            is_true_dropout = post_energy > -55.0

                            ev_type = ForensicEventType.DROPOUT if is_true_dropout else ForensicEventType.SILENCE_ANOMALY
                            start_time = float(drop_start_frame * hop_size / sample_rate)
                            end_time = float((drop_end_frame * hop_size + win_size) / sample_rate)
                            duration_s = float(end_time - start_time)

                            severity = Severity.ERROR if is_true_dropout else Severity.WARNING
                            confidence = min(1.0, 0.8 + 0.2 * min(1.0, duration_s / 0.2))

                            event = ForensicEvent(
                                event_id=f"ev_drop_{ch_name}_{event_counter:04d}_{int(start_time * 1000)}ms",
                                event_type=ev_type,
                                start_time_seconds=start_time,
                                end_time_seconds=end_time,
                                duration_seconds=duration_s,
                                severity=severity,
                                confidence=confidence,
                                channels=(ch_name,),
                                frequency_min_hz=20.0,
                                frequency_max_hz=float(sample_rate / 2.0),
                                evidence_ids=(f"frames_{drop_start_frame}_{drop_end_frame}",),
                                details={
                                    "channel": ch_name,
                                    "pre_energy_dbfs": round(pre_energy, 2),
                                    "min_dropout_dbfs": round(float(np.min(rms_db[drop_start_frame:drop_end_frame])), 2),
                                    "post_energy_dbfs": round(post_energy, 2),
                                    "is_recovered": is_true_dropout,
                                }
                            )
                            events.append(event)
                            event_counter += 1
                i += 1

        return sorted(events, key=lambda e: e.start_time_seconds)

    @classmethod
    def detect_channel_loss(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        imbalance_threshold_db: float = 35.0,
        min_duration_ms: float = 100.0,
    ) -> List[ForensicEvent]:
        """
        Detects channel loss: one stereo channel drops > imbalance_threshold_db
        relative to the other for sustained duration (>= min_duration_ms).
        """
        audio = cls._validate_audio(audio, sample_rate)
        if audio.shape[0] != 2:
            return []  # Only applicable to stereo signals

        win_size = int(0.050 * sample_rate)  # 50ms window
        hop_size = int(0.025 * sample_rate)  # 25ms hop
        if audio.shape[1] < win_size * 2:
            return []

        num_frames = (audio.shape[1] - win_size) // hop_size + 1
        l_rms = np.zeros(num_frames)
        r_rms = np.zeros(num_frames)

        for i in range(num_frames):
            s = i * hop_size
            b_l = audio[0, s:s + win_size]
            b_r = audio[1, s:s + win_size]
            l_rms[i] = 20.0 * np.log10(np.sqrt(np.mean(b_l ** 2)) + 1e-12)
            r_rms[i] = 20.0 * np.log10(np.sqrt(np.mean(b_r ** 2)) + 1e-12)

        min_frames = max(2, int(math.ceil((min_duration_ms / 1000.0) / (hop_size / sample_rate))))
        events: List[ForensicEvent] = []
        event_counter = 1

        # Check L active, R silent
        diff_lr = l_rms - r_rms
        diff_rl = r_rms - l_rms

        for condition, lost_ch, active_ch, diff_arr, active_rms in [
            (diff_lr > imbalance_threshold_db, "R", "L", diff_lr, l_rms),
            (diff_rl > imbalance_threshold_db, "L", "R", diff_rl, r_rms),
        ]:
            indices = np.where(condition & (active_rms > -40.0))[0]
            if len(indices) == 0:
                continue

            clusters: List[List[int]] = []
            curr: List[int] = [int(indices[0])]
            for idx in indices[1:]:
                idx = int(idx)
                if idx - curr[-1] <= 2:
                    curr.append(idx)
                else:
                    clusters.append(curr)
                    curr = [idx]
            if curr:
                clusters.append(curr)

            for cluster in clusters:
                if len(cluster) >= min_frames:
                    start_s = float(cluster[0] * hop_size / sample_rate)
                    end_s = float((cluster[-1] * hop_size + win_size) / sample_rate)
                    dur_s = float(end_s - start_s)

                    max_diff = float(np.max(diff_arr[cluster]))
                    severity = Severity.CRITICAL if dur_s >= 0.5 else Severity.ERROR

                    event = ForensicEvent(
                        event_id=f"ev_chloss_{lost_ch}_{event_counter:04d}_{int(start_s * 1000)}ms",
                        event_type=ForensicEventType.CHANNEL_LOSS,
                        start_time_seconds=start_s,
                        end_time_seconds=end_s,
                        duration_seconds=dur_s,
                        severity=severity,
                        confidence=0.90,
                        channels=(lost_ch,),
                        frequency_min_hz=20.0,
                        frequency_max_hz=float(sample_rate / 2.0),
                        evidence_ids=(f"ch_imbalance_{cluster[0]}_{cluster[-1]}",),
                        details={
                            "lost_channel": lost_ch,
                            "active_channel": active_ch,
                            "max_imbalance_db": round(max_diff, 2),
                            "duration_ms": round(dur_s * 1000.0, 2),
                        }
                    )
                    events.append(event)
                    event_counter += 1

        return sorted(events, key=lambda e: e.start_time_seconds)

    @classmethod
    def detect_phase_anomalies(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        correlation_threshold: float = -0.3,
        min_duration_ms: float = 100.0,
    ) -> List[ForensicEvent]:
        """
        Detects sustained negative phase correlation across stereo channels.
        correlation_threshold: correlation below which phase cancellation occurs (default: -0.3).
        """
        audio = cls._validate_audio(audio, sample_rate)
        if audio.shape[0] != 2:
            return []

        win_size = int(0.050 * sample_rate)
        hop_size = int(0.025 * sample_rate)
        if audio.shape[1] < win_size * 2:
            return []

        num_frames = (audio.shape[1] - win_size) // hop_size + 1
        correlations = np.zeros(num_frames)
        active_mask = np.zeros(num_frames, dtype=bool)

        for i in range(num_frames):
            s = i * hop_size
            l_buf = audio[0, s:s + win_size]
            r_buf = audio[1, s:s + win_size]

            l_rms = float(np.sqrt(np.mean(l_buf ** 2)))
            r_rms = float(np.sqrt(np.mean(r_buf ** 2)))

            if l_rms > 1e-4 and r_rms > 1e-4:
                active_mask[i] = True
                norm = (np.sqrt(np.sum(l_buf ** 2)) * np.sqrt(np.sum(r_buf ** 2))) + 1e-12
                correlations[i] = float(np.sum(l_buf * r_buf) / norm)
            else:
                correlations[i] = 1.0

        min_frames = max(2, int(math.ceil((min_duration_ms / 1000.0) / (hop_size / sample_rate))))
        neg_indices = np.where((correlations < correlation_threshold) & active_mask)[0]

        if len(neg_indices) == 0:
            return []

        clusters: List[List[int]] = []
        curr: List[int] = [int(neg_indices[0])]
        for idx in neg_indices[1:]:
            idx = int(idx)
            if idx - curr[-1] <= 2:
                curr.append(idx)
            else:
                clusters.append(curr)
                curr = [idx]
        if curr:
            clusters.append(curr)

        events: List[ForensicEvent] = []
        event_counter = 1

        for cluster in clusters:
            if len(cluster) >= min_frames:
                start_s = float(cluster[0] * hop_size / sample_rate)
                end_s = float((cluster[-1] * hop_size + win_size) / sample_rate)
                dur_s = float(end_s - start_s)

                min_corr = float(np.min(correlations[cluster]))
                mean_corr = float(np.mean(correlations[cluster]))

                severity = Severity.CRITICAL if min_corr < -0.7 else Severity.ERROR if min_corr < -0.5 else Severity.WARNING
                confidence = min(1.0, 0.8 + 0.2 * abs(min_corr))

                event = ForensicEvent(
                    event_id=f"ev_phase_{event_counter:04d}_{int(start_s * 1000)}ms",
                    event_type=ForensicEventType.PHASE_ANOMALY,
                    start_time_seconds=start_s,
                    end_time_seconds=end_s,
                    duration_seconds=dur_s,
                    severity=severity,
                    confidence=confidence,
                    channels=("L", "R"),
                    frequency_min_hz=20.0,
                    frequency_max_hz=20000.0,
                    evidence_ids=(f"corr_frames_{cluster[0]}_{cluster[-1]}",),
                    details={
                        "min_correlation": round(min_corr, 3),
                        "mean_correlation": round(mean_corr, 3),
                        "correlation_threshold": round(correlation_threshold, 3),
                        "duration_ms": round(dur_s * 1000.0, 2),
                    }
                )
                events.append(event)
                event_counter += 1

        return sorted(events, key=lambda e: e.start_time_seconds)

    @classmethod
    def analyze(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        config: Optional[AnalysisConfig] = None,
    ) -> List[ForensicEvent]:
        """
        Runs complete battery of acoustic anomaly detections.
        """
        cfg = config or AnalysisConfig()
        events: List[ForensicEvent] = []

        # 1. DC Offset
        events.extend(cls.detect_dc_offset(audio, sample_rate))
        # 2. Clicks and Pops
        events.extend(cls.detect_clicks_and_pops(audio, sample_rate))
        # 3. Dropouts
        events.extend(cls.detect_dropouts(audio, sample_rate, min_duration_ms=cfg.minimum_event_duration_ms))
        # 4. Channel loss (stereo only)
        events.extend(cls.detect_channel_loss(audio, sample_rate, min_duration_ms=cfg.minimum_event_duration_ms))
        # 5. Phase anomalies (stereo only)
        events.extend(cls.detect_phase_anomalies(audio, sample_rate, correlation_threshold=-0.3, min_duration_ms=cfg.minimum_event_duration_ms))

        return sorted(events, key=lambda e: (e.start_time_seconds, e.event_type))

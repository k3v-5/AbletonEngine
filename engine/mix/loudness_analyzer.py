"""
DSP Loudness and Headroom Analyzer.
Complies with ITU-R BS.1770-5 (LUFS Integrated, Short-term, Momentary, True Peak, RMS, and LRA).
Provides strict separation between acoustic measurement and profile compliance.
"""
from typing import Tuple, Dict, Any, Optional
import numpy as np

from .models import HeadroomClassification, DynamicClassification
from .loudness_standards import (
    LoudnessMeasurement,
    MeasurementMetadata,
    LoudnessProfile,
    ProfileRegistry,
    ProfileEvaluationResult,
    MeasurementStatus
)


class LoudnessAnalyzer:
    """
    Analyzes perceptual loudness, peak, and True Peak per ITU-R BS.1770-5 and EBU R 128.
    """

    def __init__(self, profile: Optional[LoudnessProfile] = None):
        self.profile = profile or ProfileRegistry.STREAMING

    @staticmethod
    def _apply_k_weighting(signal: np.ndarray, sr: int) -> np.ndarray:

        """
        Applies ITU-R BS.1770-5 K-weighting pre-filter (Stage 1 High-Shelf + Stage 2 RLB High-Pass).
        Uses exact digital biquad filter coefficients recalculated for the given sample rate.
        """
        filtered = np.copy(signal).astype(np.float64)

        # High shelf filter coefficients (ITU-R BS.1770-5 Stage 1)
        f0_hs = 1681.974450955533
        gain_db_hs = 3.999843853973347
        A = 10.0 ** (gain_db_hs / 40.0)
        w0_hs = 2.0 * np.pi * f0_hs / sr
        alpha_hs = np.sin(w0_hs) / 2.0 * np.sqrt(2.0)
        cos_w0_hs = np.cos(w0_hs)

        b0_hs = A * ((A + 1.0) + (A - 1.0) * cos_w0_hs + 2.0 * np.sqrt(A) * alpha_hs)
        b1_hs = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0_hs)
        b2_hs = A * ((A + 1.0) + (A - 1.0) * cos_w0_hs - 2.0 * np.sqrt(A) * alpha_hs)
        a0_hs = (A + 1.0) - (A - 1.0) * cos_w0_hs + 2.0 * np.sqrt(A) * alpha_hs
        a1_hs = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0_hs)
        a2_hs = (A + 1.0) - (A - 1.0) * cos_w0_hs - 2.0 * np.sqrt(A) * alpha_hs

        b_hs = np.array([b0_hs, b1_hs, b2_hs]) / a0_hs
        a_hs = np.array([a0_hs, a1_hs, a2_hs]) / a0_hs

        # Stage 2: RLB High-pass filter
        f0_hp = 38.13547087602444
        w0_hp = 2.0 * np.pi * f0_hp / sr
        cos_w0_hp = np.cos(w0_hp)
        alpha_hp = np.sin(w0_hp) / (2.0 * 0.5)

        b0_hp = (1.0 + cos_w0_hp) / 2.0
        b1_hp = -(1.0 + cos_w0_hp)
        b2_hp = (1.0 + cos_w0_hp) / 2.0
        a0_hp = 1.0 + alpha_hp
        a1_hp = -2.0 * cos_w0_hp
        a2_hp = 1.0 - alpha_hp

        b_hp = np.array([b0_hp, b1_hp, b2_hp]) / a0_hp
        a_hp = np.array([a0_hp, a1_hp, a2_hp]) / a0_hp

        # Run 2-stage IIR difference equation per channel
        for ch in range(filtered.shape[0]):
            x = filtered[ch]
            # Stage 1
            y1 = np.zeros_like(x)
            for i in range(len(x)):
                x0 = x[i]
                x1 = x[i - 1] if i > 0 else 0.0
                x2 = x[i - 2] if i > 1 else 0.0
                y_prev1 = y1[i - 1] if i > 0 else 0.0
                y_prev2 = y1[i - 2] if i > 1 else 0.0
                y1[i] = b_hs[0] * x0 + b_hs[1] * x1 + b_hs[2] * x2 - a_hs[1] * y_prev1 - a_hs[2] * y_prev2

            # Stage 2
            y2 = np.zeros_like(y1)
            for i in range(len(y1)):
                x0 = y1[i]
                x1 = y1[i - 1] if i > 0 else 0.0
                x2 = y1[i - 2] if i > 1 else 0.0
                y_prev1 = y2[i - 1] if i > 0 else 0.0
                y_prev2 = y2[i - 2] if i > 1 else 0.0
                y2[i] = b_hp[0] * x0 + b_hp[1] * x1 + b_hp[2] * x2 - a_hp[1] * y_prev1 - a_hp[2] * y_prev2

            filtered[ch] = y2

        return filtered

    @classmethod
    def calculate_lufs_with_blocks(
        cls, audio: np.ndarray, sr: int
    ) -> Tuple[float, float, float, np.ndarray, np.ndarray]:
        """
        Calculates ITU-R BS.1770-5 LUFS and returns internal block powers and short-term values.
        audio shape: (channels, samples).
        Returns: (integrated_lufs, short_term_lufs, momentary_lufs, block_lufs, st_lufs)
        """
        if audio.size == 0:
            return -70.0, -70.0, -70.0, np.array([]), np.array([])

        k_filtered = cls._apply_k_weighting(audio, sr)

        block_size_m = int(0.400 * sr)
        step_size = int(0.100 * sr)
        total_samples = k_filtered.shape[1]

        if total_samples < block_size_m:
            mean_sq = np.mean(k_filtered ** 2) + 1e-12
            val = float(-0.691 + 10.0 * np.log10(mean_sq))
            return val, val, val, np.array([val]), np.array([val])

        num_channels = k_filtered.shape[0]
        channel_weights = np.ones(num_channels)
        if num_channels >= 5:
            # BS.1770-5 surround channel weighting (+1.5 dB = ~1.41)
            channel_weights[3] = 1.41
            channel_weights[4] = 1.41

        num_blocks = (total_samples - block_size_m) // step_size + 1
        block_powers = np.zeros(num_blocks)

        for b in range(num_blocks):
            start = b * step_size
            end = start + block_size_m
            block = k_filtered[:, start:end]
            ch_powers = np.mean(block ** 2, axis=1)
            block_powers[b] = np.sum(channel_weights * ch_powers)

        block_lufs = -0.691 + 10.0 * np.log10(block_powers + 1e-12)
        lufs_momentary = float(np.max(block_lufs))

        # Short-term (3.0s sliding window = 30 blocks of 100ms)
        st_blocks = int(3.0 / 0.1)
        if num_blocks < st_blocks:
            lufs_short_term = lufs_momentary
            st_lufs = block_lufs
        else:
            st_powers = np.array([
                np.mean(block_powers[i : i + st_blocks])
                for i in range(num_blocks - st_blocks + 1)
            ])
            st_lufs = -0.691 + 10.0 * np.log10(st_powers + 1e-12)
            lufs_short_term = float(np.max(st_lufs))

        # Integrated loudness with dual gating per ITU-R BS.1770-5:
        # 1. Absolute gate at -70 LKFS
        abs_gate_mask = block_lufs > -70.0
        if not np.any(abs_gate_mask):
            return -70.0, lufs_short_term, lufs_momentary, block_lufs, st_lufs

        mean_above_abs = np.mean(block_powers[abs_gate_mask])
        gamma_a = -0.691 + 10.0 * np.log10(mean_above_abs + 1e-12)

        # 2. Relative gate at -10 LKFS relative to gamma_a
        gamma_rel = gamma_a - 10.0
        rel_gate_mask = (block_lufs > gamma_rel) & abs_gate_mask
        if not np.any(rel_gate_mask):
            lufs_integrated = float(gamma_a)
        else:
            final_mean_power = np.mean(block_powers[rel_gate_mask])
            lufs_integrated = float(-0.691 + 10.0 * np.log10(final_mean_power + 1e-12))

        return lufs_integrated, lufs_short_term, lufs_momentary, block_lufs, st_lufs

    @classmethod
    def calculate_lufs(cls, audio: np.ndarray, sr: int) -> Tuple[float, float, float]:
        """Backwards-compatible wrapper returning (Integrated, Short-term, Momentary)."""
        l_int, l_st, l_mom, _, _ = cls.calculate_lufs_with_blocks(audio, sr)
        return l_int, l_st, l_mom

    @classmethod
    def calculate_lra(cls, st_lufs: np.ndarray) -> float:
        """
        Calculates Loudness Range (LRA) according to EBU Tech 3342 / ITU-R BS.1770-5.
        Uses dual-gating (-70 LKFS absolute, -20 LKFS relative).
        LRA = 95th percentile - 10th percentile.
        """
        if len(st_lufs) < 2:
            return 0.0

        # Absolute gate (-70 LKFS)
        abs_gated = st_lufs[st_lufs > -70.0]
        if len(abs_gated) < 2:
            return 0.0

        # Relative gate (-20 LKFS below ungated mean power)
        mean_power = np.mean(10.0 ** (abs_gated / 10.0))
        gamma_lra = 10.0 * np.log10(mean_power + 1e-12)
        rel_gated = abs_gated[abs_gated > (gamma_lra - 20.0)]
        if len(rel_gated) < 2:
            return 0.0

        low_p = float(np.percentile(rel_gated, 10))
        high_p = float(np.percentile(rel_gated, 95))
        return float(max(0.0, high_p - low_p))

    @staticmethod
    def calculate_true_peak(audio: np.ndarray, oversample_factor: int = 4) -> float:
        """
        Calculates True Peak per ITU-R BS.1770-5 Annex 2 using a 4x oversampling
        reconstruction filter (windowed sinc FIR).
        Detects inter-sample peaks that exceed 0 dBFS.
        """
        if audio.size == 0:
            return -100.0

        # Design 4x sinc interpolation filter with Hann window
        half_len = 16
        k = np.arange(-half_len * oversample_factor, half_len * oversample_factor + 1)
        sinc = np.sinc(k / oversample_factor)
        win = np.hanning(len(k))
        h = sinc * win
        h = h * oversample_factor / np.sum(h)

        max_tp = -100.0
        for ch in range(audio.shape[0]):
            x = audio[ch].astype(np.float64)
            # 4x zero-stuffed upsampling
            x_up = np.zeros(len(x) * oversample_factor, dtype=np.float64)
            x_up[::oversample_factor] = x
            # Convolve with reconstruction filter
            interpolated = np.convolve(x_up, h, mode="same")
            peak_val = float(np.max(np.abs(interpolated))) + 1e-12
            tp_db = float(20.0 * np.log10(peak_val))
            if tp_db > max_tp:
                max_tp = tp_db

        return max_tp

    @classmethod
    def calculate_headroom(cls, peak_db: float, true_peak_db: float) -> HeadroomClassification:
        """Classifies headroom status according to standard thresholds."""
        if peak_db > 0.0 or true_peak_db > 0.0:
            return HeadroomClassification.MASTER_CLIPPING
        elif true_peak_db >= -0.5:
            return HeadroomClassification.NEAR_CLIPPING
        elif true_peak_db < -12.0:
            return HeadroomClassification.EXCESSIVE_HEADROOM
        else:
            return HeadroomClassification.HEALTHY_HEADROOM

    @classmethod
    def measure(
        cls,
        audio: np.ndarray,
        sr: int = 44100,
        bit_depth: int = 24,
        channel_layout: str = "stereo"
    ) -> LoudnessMeasurement:
        """
        Normative ITU-R BS.1770-5 measurement generating a full LoudnessMeasurement.
        Does not evaluate compliance against delivery targets.
        """
        if sr <= 0:
            raise ValueError(f"sample_rate must be a positive integer > 0, got {sr}")

        if audio.ndim > 2:
            raise ValueError(f"Unsupported audio dimensions: expected 1D or 2D array, got {audio.ndim}D")

        # Ensure 2D (channels, samples)
        if audio.ndim == 1:
            audio_2d = np.stack([audio, audio], axis=0)
        elif audio.ndim == 2 and audio.shape[0] > audio.shape[1]:
            audio_2d = audio.T
        else:
            audio_2d = audio

        n_samples = audio_2d.shape[1] if audio_2d.ndim > 1 else len(audio_2d)
        duration = float(n_samples / sr) if sr > 0 else 0.0

        if audio_2d.size == 0 or n_samples == 0:
            metadata = MeasurementMetadata(
                sample_rate=sr,
                bit_depth=bit_depth,
                channel_layout=channel_layout,
                duration_seconds=0.0
            )
            return LoudnessMeasurement(
                integrated_lufs=-70.0,
                short_term_lufs=-70.0,
                momentary_lufs=-70.0,
                loudness_range_lra=0.0,
                sample_peak_dbfs=-100.0,
                true_peak_dbtp=-100.0,
                crest_factor_db=0.0,
                measurement_valid=False,
                metadata=metadata,
                status=MeasurementStatus.INVALID_INPUT
            )

        # Check for NaN / Inf in audio samples (Section 10 & 13)
        if np.isnan(audio_2d).any() or np.isinf(audio_2d).any():
            metadata = MeasurementMetadata(
                sample_rate=sr,
                bit_depth=bit_depth,
                channel_layout=channel_layout,
                duration_seconds=float(duration)
            )
            return LoudnessMeasurement(
                integrated_lufs=-70.0,
                short_term_lufs=-70.0,
                momentary_lufs=-70.0,
                loudness_range_lra=0.0,
                sample_peak_dbfs=-100.0,
                true_peak_dbtp=-100.0,
                crest_factor_db=0.0,
                measurement_valid=False,
                metadata=metadata,
                status=MeasurementStatus.NUMERIC_FAILURE
            )

        # 1. BS.1770-5 LUFS and LRA
        l_int, l_st, l_mom, _, st_lufs = cls.calculate_lufs_with_blocks(audio_2d, sr)
        lra = cls.calculate_lra(st_lufs)

        # 2. Sample Peak
        sample_peak = float(np.max(np.abs(audio_2d))) + 1e-12
        sample_peak_dbfs = float(20.0 * np.log10(sample_peak))

        # 3. True Peak (Annex 2 4x FIR)
        true_peak_dbfs = cls.calculate_true_peak(audio_2d)

        # 4. Crest Factor
        rms = float(np.sqrt(np.mean(audio_2d ** 2))) + 1e-12
        crest_factor_db = float(sample_peak_dbfs - (20.0 * np.log10(rms)))

        metadata = MeasurementMetadata(
            standard="ITU-R BS.1770-5",
            standard_version="BS.1770-5 (2023)",
            algorithm_version="1.0.0",
            sample_rate=sr,
            bit_depth=bit_depth,
            channel_layout=channel_layout,
            duration_seconds=float(duration)
        )

        return LoudnessMeasurement(
            integrated_lufs=float(l_int),
            short_term_lufs=float(l_st),
            momentary_lufs=float(l_mom),
            loudness_range_lra=float(lra),
            sample_peak_dbfs=float(sample_peak_dbfs),
            true_peak_dbtp=float(true_peak_dbfs),
            crest_factor_db=float(crest_factor_db),
            measurement_valid=True,
            metadata=metadata,
            status=MeasurementStatus.VALID
        )

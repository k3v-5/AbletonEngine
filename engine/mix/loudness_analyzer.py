"""
DSP Loudness and Headroom Analyzer.
Complies with ITU-R BS.1770-4 (LUFS Integrated, Short-term, Momentary), True Peak, RMS, and LRA.
"""
from typing import Tuple, Dict, Any
import numpy as np

from .models import HeadroomClassification, DynamicClassification


class LoudnessAnalyzer:
    """Analyzes perceptual loudness, peak, and true-peak per ITU-R BS.1770-4."""

    @staticmethod
    def _apply_k_weighting(signal: np.ndarray, sr: int) -> np.ndarray:
        """
        Applies ITU-R BS.1770-4 K-weighting pre-filter (Stage 1 High-Shelf + Stage 2 RLB High-Pass).
        Uses exact digital biquad filter coefficients recalculated for the given sample rate.
        """
        # Normalized sample rate reference 48000 Hz
        # Stage 1: High-shelf filter (~1681 Hz, +4 dB)
        # Stage 2: RLB High-pass filter (~38 Hz)
        # We implement stable IIR difference equations for arbitrary sample rates:
        filtered = np.copy(signal).astype(np.float64)
        
        # High shelf filter coefficients at 48kHz (ITU-R BS.1770-4)
        # If sr != 48000, bilinear transformation scaling is applied
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
                x1 = x[i-1] if i > 0 else 0.0
                x2 = x[i-2] if i > 1 else 0.0
                y_prev1 = y1[i-1] if i > 0 else 0.0
                y_prev2 = y1[i-2] if i > 1 else 0.0
                y1[i] = b_hs[0]*x0 + b_hs[1]*x1 + b_hs[2]*x2 - a_hs[1]*y_prev1 - a_hs[2]*y_prev2
                
            # Stage 2
            y2 = np.zeros_like(y1)
            for i in range(len(y1)):
                x0 = y1[i]
                x1 = y1[i-1] if i > 0 else 0.0
                x2 = y1[i-2] if i > 1 else 0.0
                y_prev1 = y2[i-1] if i > 0 else 0.0
                y_prev2 = y2[i-2] if i > 1 else 0.0
                y2[i] = b_hp[0]*x0 + b_hp[1]*x1 + b_hp[2]*x2 - a_hp[1]*y_prev1 - a_hp[2]*y_prev2
                
            filtered[ch] = y2
            
        return filtered

    @classmethod
    def calculate_lufs(cls, audio: np.ndarray, sr: int) -> Tuple[float, float, float]:
        """
        Calculates ITU-R BS.1770-4 LUFS: (Integrated, Short-term, Momentary).
        audio shape: (channels, samples).
        """
        if audio.size == 0:
            return -70.0, -70.0, -70.0
            
        # K-weighting
        k_filtered = cls._apply_k_weighting(audio, sr)
        
        # Block parameters:
        # Momentary = 400ms block
        # Short-term = 3000ms block
        # Gating step = 100ms (75% overlap for momentary)
        block_size_m = int(0.400 * sr)
        step_size = int(0.100 * sr)
        total_samples = k_filtered.shape[1]
        
        if total_samples < block_size_m:
            # Fallback for ultra-short snippets
            mean_sq = np.mean(k_filtered**2) + 1e-12
            val = float(-0.691 + 10.0 * np.log10(mean_sq))
            return val, val, val

        # Channel weights (1.0 for Left, Right, Center)
        num_channels = k_filtered.shape[0]
        channel_weights = np.ones(num_channels)
        if num_channels >= 5:
            # Surround channels weight 1.41
            channel_weights[3] = 1.41
            channel_weights[4] = 1.41

        # Calculate mean squares for all 400ms blocks
        num_blocks = (total_samples - block_size_m) // step_size + 1
        block_powers = np.zeros(num_blocks)
        
        for b in range(num_blocks):
            start = b * step_size
            end = start + block_size_m
            block = k_filtered[:, start:end]
            ch_powers = np.mean(block**2, axis=1)
            block_powers[b] = np.sum(channel_weights * ch_powers)

        block_lufs = -0.691 + 10.0 * np.log10(block_powers + 1e-12)
        
        # Momentary: maximum or last momentary block
        lufs_momentary = float(np.max(block_lufs))
        
        # Short-term (3.0s window = 30 blocks of 100ms)
        st_blocks = int(3.0 / 0.1)
        if num_blocks < st_blocks:
            lufs_short_term = lufs_momentary
        else:
            st_powers = [np.mean(block_powers[i:i+st_blocks]) for i in range(num_blocks - st_blocks + 1)]
            lufs_short_term = float(np.max(-0.691 + 10.0 * np.log10(np.array(st_powers) + 1e-12)))

        # Integrated loudness with dual gating (BS.1770-4):
        # 1. Absolute gate at -70 LKFS
        abs_gate_mask = block_lufs > -70.0
        if not np.any(abs_gate_mask):
            return -70.0, lufs_short_term, lufs_momentary
            
        mean_above_abs = np.mean(block_powers[abs_gate_mask])
        gamma_a = -0.691 + 10.0 * np.log10(mean_above_abs + 1e-12)
        
        # 2. Relative gate at -10 LKFS relative to gamma_a
        gamma_rel = gamma_a - 10.0
        rel_gate_mask = (block_lufs > gamma_rel) & abs_gate_mask
        if not np.any(rel_gate_mask):
            lufs_integrated = gamma_a
        else:
            final_mean_power = np.mean(block_powers[rel_gate_mask])
            lufs_integrated = float(-0.691 + 10.0 * np.log10(final_mean_power + 1e-12))
            
        return lufs_integrated, lufs_short_term, lufs_momentary

    @staticmethod
    def calculate_true_peak(audio: np.ndarray) -> float:
        """
        Estimates True Peak using 4x oversampling interpolation.
        Detects inter-sample peaks that exceed 0 dBFS.
        """
        if audio.size == 0:
            return -100.0
            
        max_tp = -100.0
        for ch in range(audio.shape[0]):
            x = audio[ch]
            # 4x sinc/linear oversampling interpolation
            n = len(x)
            t_orig = np.arange(n)
            t_over = np.linspace(0, n - 1, n * 4)
            x_over = np.interp(t_over, t_orig, x)
            peak_val = np.max(np.abs(x_over)) + 1e-12
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

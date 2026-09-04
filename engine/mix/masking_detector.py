"""
Low-End Masking and Collision Detector (Kick vs Bass / Sub).
Evaluates frequency overlap, temporal coincidence, energy distribution, and phase correlation.
"""
from typing import List, Tuple
import numpy as np

from .models import MaskingResult, Severity, severity_from_score


class MaskingDetector:
    """Detects and scores spectral/temporal masking between rhythmic and melodic low-end roles."""

    @classmethod
    def detect_low_end_conflict(cls, kick_audio: np.ndarray, bass_audio: np.ndarray, sr: int) -> MaskingResult:
        # Convert both to mono 1D arrays
        kick_mono = np.mean(kick_audio, axis=0) if kick_audio.ndim > 1 else kick_audio
        bass_mono = np.mean(bass_audio, axis=0) if bass_audio.ndim > 1 else bass_audio

        min_len = min(len(kick_mono), len(bass_mono))
        if min_len < 256:
            return MaskingResult(
                masking_score=0.0,
                frequency_overlap=0.0,
                temporal_overlap=0.0,
                energy_overlap=0.0,
                phase_correlation=1.0,
                conflict_frequency_hz=50.0,
                severity=Severity.INFO,
                evidence=["Insufficient audio length for masking analysis."],
                probable_causes=[],
                recommended_actions=[]
            )

        k = kick_mono[:min_len]
        b = bass_mono[:min_len]

        # 1. Frequency overlap in critical band (20 - 120 Hz)
        n_fft = min(8192, max(512, 1 << (min_len - 1).bit_length()))
        fft_k = np.abs(np.fft.rfft(k[:n_fft] * np.hanning(min(min_len, n_fft))))
        fft_b = np.abs(np.fft.rfft(b[:n_fft] * np.hanning(min(min_len, n_fft))))
        freqs = np.fft.rfftfreq(n_fft, d=1.0/sr)

        low_mask = (freqs >= 20.0) & (freqs <= 120.0)
        if not np.any(low_mask):
            return MaskingResult(0.0, 0.0, 0.0, 0.0, 1.0, 50.0, Severity.INFO, [], [], [])

        k_low = fft_k[low_mask]
        b_low = fft_b[low_mask]
        low_freqs = freqs[low_mask]

        # Normalized cross-spectral cosine similarity
        norm_product_spec = (np.sqrt(np.sum(k_low**2)) * np.sqrt(np.sum(b_low**2)) + 1e-12)
        freq_overlap = float(np.sum(k_low * b_low) / norm_product_spec)
        freq_overlap = float(np.clip(freq_overlap, 0.0, 1.0))

        # Collision frequency: peak of overlap product
        overlap_product = k_low * b_low
        peak_overlap_idx = np.argmax(overlap_product)
        conflict_hz = float(low_freqs[peak_overlap_idx])

        # 2. Temporal overlap (envelope cosine similarity)
        rect_k = np.abs(k)
        rect_b = np.abs(b)
        # Smooth with 10ms window
        kernel_len = max(1, int(0.010 * sr))
        kernel = np.ones(kernel_len) / kernel_len
        env_k = np.convolve(rect_k, kernel, mode="same")
        env_b = np.convolve(rect_b, kernel, mode="same")

        norm_product_env = (np.sqrt(np.sum(env_k**2)) * np.sqrt(np.sum(env_b**2)) + 1e-12)
        temporal_coincidence = float(np.sum(env_k * env_b) / norm_product_env)
        temporal_overlap = float(np.clip(temporal_coincidence, 0.0, 1.0))

        # 3. Energy overlap
        rms_k = np.sqrt(np.mean(k**2) + 1e-12)
        rms_b = np.sqrt(np.mean(b**2) + 1e-12)
        ratio = min(rms_k, rms_b) / max(rms_k, rms_b)
        energy_overlap = float(ratio)

        # 4. Phase correlation in 30-100Hz
        # Bandpass filter via FFT
        fft_k_filt = np.fft.rfft(k)
        fft_b_filt = np.fft.rfft(b)
        all_freqs = np.fft.rfftfreq(min_len, d=1.0/sr)
        bp_mask = (all_freqs >= 30.0) & (all_freqs <= 100.0)
        
        k_bp = np.fft.irfft(fft_k_filt * bp_mask, n=min_len)
        b_bp = np.fft.irfft(fft_b_filt * bp_mask, n=min_len)

        dot = np.sum(k_bp * b_bp)
        norm_product = (np.sqrt(np.sum(k_bp**2) + 1e-12) * np.sqrt(np.sum(b_bp**2) + 1e-12))
        phase_corr = float(np.clip(dot / norm_product, -1.0, 1.0))

        # Composite masking score
        # Base: 45% freq overlap + 35% temporal overlap + 20% energy balance
        base_score = 0.45 * freq_overlap + 0.35 * temporal_overlap + 0.20 * energy_overlap
        # Phase penalty: if phase is inverted (-1.0), it causes cancellation (severe collision)
        if phase_corr < -0.2:
            phase_penalty = abs(phase_corr) * 0.15
            base_score = min(1.0, base_score + phase_penalty)

        masking_score = float(np.clip(base_score, 0.0, 1.0))
        severity = severity_from_score(masking_score)

        # Formulate Evidence, Causes, and Actions
        evidence: List[str] = []
        probable_causes: List[str] = []
        recommended_actions: List[str] = []

        if freq_overlap > 0.35:
            evidence.append(f"Strong spectral overlap detected around {conflict_hz:.1f} Hz (overlap index: {freq_overlap:.2f})")
            probable_causes.append(f"Bass fundamental coincides with kick drum punch zone near {conflict_hz:.1f} Hz.")
        if temporal_overlap > 0.40:
            evidence.append(f"High temporal coincidence between kick attack and bass note envelope ({temporal_overlap:.2f})")
            probable_causes.append("Bass note onset triggers simultaneously with 4-on-the-floor kick hit.")
            recommended_actions.append("Increase sidechain ducking depth on bass channel.")
            recommended_actions.append("Shorten bass envelope attack or add 10-20ms pre-delay.")
        if phase_corr < -0.2:
            evidence.append(f"Destructive phase cancellation in 30-100 Hz band (correlation: {phase_corr:.2f})")
            probable_causes.append("Kick and sub-bass waveforms are out of phase during simultaneous transient hits.")
            recommended_actions.append("Invert polarity (phase) on bass or adjust kick start offset.")
        if freq_overlap > 0.50:
            recommended_actions.append(f"Apply dynamic EQ cut of -1.5 dB on bass at {conflict_hz:.1f} Hz (Q=1.4).")

        return MaskingResult(
            masking_score=masking_score,
            frequency_overlap=freq_overlap,
            temporal_overlap=temporal_overlap,
            energy_overlap=energy_overlap,
            phase_correlation=phase_corr,
            conflict_frequency_hz=conflict_hz,
            severity=severity,
            evidence=evidence,
            probable_causes=probable_causes,
            recommended_actions=recommended_actions
        )

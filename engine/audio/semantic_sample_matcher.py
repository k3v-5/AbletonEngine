# engine/audio/semantic_sample_matcher.py
"""
Semantic Sample Matcher and Acoustic Feature Extractor.
Extracts 6D physical acoustic signatures from audio samples and matches
natural language intent (e.g. 'punchy kick', 'dark boomy 808', 'crisp snappy snare')
using normalized acoustic vector space and cosine similarity.
Zero external network calls, 100% deterministic, high-speed DSP.
"""

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import soundfile as sf
from scipy import signal


@dataclass
class AcousticSignature:
    """Normalized physical acoustic representation of an audio sample."""
    attack_time_ms: float
    spectral_centroid_hz: float
    sub_energy_ratio: float
    harmonic_ratio: float
    crest_factor_db: float
    decay_time_ms: float
    vector: np.ndarray = field(default_factory=lambda: np.zeros(6, dtype=np.float32))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_time_ms": round(float(self.attack_time_ms), 2),
            "spectral_centroid_hz": round(float(self.spectral_centroid_hz), 1),
            "sub_energy_ratio": round(float(self.sub_energy_ratio), 3),
            "harmonic_ratio": round(float(self.harmonic_ratio), 3),
            "crest_factor_db": round(float(self.crest_factor_db), 2),
            "decay_time_ms": round(float(self.decay_time_ms), 2),
            "vector": [round(float(v), 4) for v in self.vector]
        }


class AcousticFeatureExtractor:
    """Extracts physical timbre, envelope, and frequency metrics from audio signals."""

    @classmethod
    def extract(cls, audio: np.ndarray, sr: int) -> AcousticSignature:
        """Computes 6D physical acoustic signature from raw audio."""
        if audio.ndim > 1:
            audio_mono = np.mean(audio, axis=1)
        else:
            audio_mono = audio.copy()

        n_samples = len(audio_mono)
        if n_samples < 64:
            return AcousticSignature(
                attack_time_ms=0.0,
                spectral_centroid_hz=0.0,
                sub_energy_ratio=0.0,
                harmonic_ratio=0.0,
                crest_factor_db=0.0,
                decay_time_ms=0.0,
                vector=np.zeros(6, dtype=np.float32)
            )

        # Normalize amplitude
        peak = float(np.max(np.abs(audio_mono)))
        if peak > 1e-6:
            norm_audio = audio_mono / peak
        else:
            norm_audio = audio_mono

        # 1. Envolvente Hilbert para Attack y Decay
        analytic_signal = signal.hilbert(norm_audio)
        envelope = np.abs(analytic_signal)

        # Smooth envelope (window 5ms)
        win_len = max(1, int(sr * 0.005))
        smooth_env = signal.convolve(envelope, np.ones(win_len) / win_len, mode="same")

        peak_idx = int(np.argmax(smooth_env))
        attack_time_ms = float((peak_idx / sr) * 1000.0)

        # Decay time: time from peak until envelope drops below -20dB (0.1 of peak)
        decay_samples = 0
        threshold_amp = 0.10
        for i in range(peak_idx, n_samples):
            if smooth_env[i] < threshold_amp:
                decay_samples = i - peak_idx
                break
        if decay_samples == 0:
            decay_samples = n_samples - peak_idx
        decay_time_ms = float((decay_samples / sr) * 1000.0)

        # 2. Spectral Centroid (Brillo tímbrico en Hz)
        n_fft = min(4096, max(256, 1 << (n_samples - 1).bit_length()))
        windowed = norm_audio[:n_fft] * np.hanning(min(n_samples, n_fft))
        mag_spec = np.abs(np.fft.rfft(windowed, n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

        spec_sum = float(np.sum(mag_spec))
        if spec_sum > 1e-8:
            spectral_centroid_hz = float(np.sum(freqs * mag_spec) / spec_sum)
        else:
            spectral_centroid_hz = 0.0

        # 3. Sub-Bass & Low-End Energy Ratio (<= 120 Hz vs Total Energy)
        sub_mask = freqs <= 120.0
        sub_energy = float(np.sum(mag_spec[sub_mask] ** 2))
        total_energy = float(np.sum(mag_spec ** 2)) + 1e-12
        sub_energy_ratio = float(sub_energy / total_energy)
        sub_energy_ratio = float(np.clip(sub_energy_ratio, 0.0, 1.0))

        # 4. Harmonic Ratio (Autocorrelation peak prominence)
        corr_len = min(n_samples, int(sr * 0.05))  # 50 ms max lag
        if corr_len > 32:
            auto_corr = signal.correlate(norm_audio[:corr_len], norm_audio[:corr_len], mode="full")
            auto_corr = auto_corr[len(auto_corr) // 2:]
            auto_corr = auto_corr / (auto_corr[0] + 1e-12)
            # Find max peak outside zero lag (> 2ms)
            min_lag = max(1, int(sr * 0.002))
            if len(auto_corr) > min_lag:
                harmonic_ratio = float(np.clip(np.max(auto_corr[min_lag:]), 0.0, 1.0))
            else:
                harmonic_ratio = 0.0
        else:
            harmonic_ratio = 0.0

        # 5. Crest Factor (Peak to RMS ratio in dB)
        rms = float(np.sqrt(np.mean(norm_audio ** 2)) + 1e-8)
        crest_factor_db = float(20.0 * np.log10(max(1.0 / rms, 1.0)))

        # 6. Normalize into 6D vector [0.0, 1.0]
        # Dimensions: [attack, brightness, sub_energy, harmonicity, crest_factor, decay]
        norm_attack = float(np.clip(attack_time_ms / 50.0, 0.0, 1.0))  # 0 to 50ms
        norm_centroid = float(np.clip(spectral_centroid_hz / 8000.0, 0.0, 1.0))  # 0 to 8kHz
        norm_sub = float(np.clip(sub_energy_ratio, 0.0, 1.0))
        norm_harmonic = float(np.clip(harmonic_ratio, 0.0, 1.0))
        norm_crest = float(np.clip((crest_factor_db - 3.0) / 20.0, 0.0, 1.0))  # 3 to 23 dB
        norm_decay = float(np.clip(decay_time_ms / 1500.0, 0.0, 1.0))  # 0 to 1.5s

        vector = np.array([
            norm_attack,
            norm_centroid,
            norm_sub,
            norm_harmonic,
            norm_crest,
            norm_decay
        ], dtype=np.float32)

        return AcousticSignature(
            attack_time_ms=attack_time_ms,
            spectral_centroid_hz=spectral_centroid_hz,
            sub_energy_ratio=sub_energy_ratio,
            harmonic_ratio=harmonic_ratio,
            crest_factor_db=crest_factor_db,
            decay_time_ms=decay_time_ms,
            vector=vector
        )

    @classmethod
    def extract_from_file(cls, file_path: Union[str, Path]) -> Optional[AcousticSignature]:
        """Reads audio file from disk and returns acoustic signature."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return None
        try:
            audio, sr = sf.read(str(p), always_2d=False, dtype="float32")
            return cls.extract(audio, sr)
        except Exception:
            return None


class SemanticSampleMatcher:
    """Matches text descriptions to audio samples based on acoustic vectors."""

    # Semantic target descriptors [attack, brightness, sub_energy, harmonicity, crest, decay]
    SEMANTIC_ANCHORS: Dict[str, np.ndarray] = {
        # Drums & Percussion
        "punchy": np.array([0.02, 0.40, 0.35, 0.20, 0.85, 0.20], dtype=np.float32),
        "tight": np.array([0.01, 0.45, 0.20, 0.15, 0.80, 0.10], dtype=np.float32),
        "snappy": np.array([0.02, 0.65, 0.10, 0.15, 0.75, 0.15], dtype=np.float32),
        "clicky": np.array([0.01, 0.85, 0.05, 0.10, 0.90, 0.08], dtype=np.float32),
        "dry": np.array([0.02, 0.35, 0.15, 0.10, 0.70, 0.08], dtype=np.float32),
        "wet": np.array([0.15, 0.45, 0.20, 0.40, 0.35, 0.85], dtype=np.float32),
        # Bass & Sub
        "boomy": np.array([0.08, 0.10, 0.85, 0.70, 0.40, 0.65], dtype=np.float32),
        "subby": np.array([0.05, 0.08, 0.95, 0.85, 0.35, 0.70], dtype=np.float32),
        "808": np.array([0.04, 0.12, 0.90, 0.80, 0.45, 0.75], dtype=np.float32),
        "deep": np.array([0.06, 0.10, 0.80, 0.65, 0.40, 0.60], dtype=np.float32),
        # Timbre & Color
        "dark": np.array([0.08, 0.12, 0.50, 0.40, 0.40, 0.40], dtype=np.float32),
        "bright": np.array([0.04, 0.80, 0.05, 0.50, 0.60, 0.40], dtype=np.float32),
        "crisp": np.array([0.02, 0.75, 0.05, 0.30, 0.70, 0.25], dtype=np.float32),
        "warm": np.array([0.08, 0.25, 0.45, 0.65, 0.45, 0.45], dtype=np.float32),
        "distorted": np.array([0.02, 0.55, 0.40, 0.85, 0.15, 0.35], dtype=np.float32),
        "saturated": np.array([0.03, 0.45, 0.45, 0.75, 0.25, 0.40], dtype=np.float32),
        "clean": np.array([0.05, 0.35, 0.30, 0.40, 0.65, 0.30], dtype=np.float32),
        "ambient": np.array([0.35, 0.40, 0.20, 0.70, 0.20, 0.90], dtype=np.float32),
        "pad": np.array([0.40, 0.35, 0.25, 0.80, 0.20, 0.85], dtype=np.float32)
    }

    @classmethod
    def parse_intent_to_target_vector(cls, text: str) -> np.ndarray:
        """Parses words from text query and constructs normalized target acoustic vector."""
        tokens = text.lower().replace("-", " ").replace("_", " ").split()
        matched_vectors = []
        weights = []

        for token in tokens:
            if token in cls.SEMANTIC_ANCHORS:
                matched_vectors.append(cls.SEMANTIC_ANCHORS[token])
                weights.append(1.0)

        if not matched_vectors:
            # Neutral balanced profile
            return np.array([0.10, 0.40, 0.30, 0.50, 0.50, 0.40], dtype=np.float32)

        stacked = np.array(matched_vectors)
        target = np.average(stacked, axis=0, weights=weights)
        return target.astype(np.float32)

    @classmethod
    def compute_similarity(cls, target_vec: np.ndarray, sample_vec: np.ndarray) -> float:
        """
        Computes hybrid similarity (80% Cosine Similarity + 20% Euclidean Proximity).
        Returns a score in range [0.0, 1.0].
        """
        norm_target = np.linalg.norm(target_vec) + 1e-12
        norm_sample = np.linalg.norm(sample_vec) + 1e-12
        cosine_sim = float(np.dot(target_vec, sample_vec) / (norm_target * norm_sample))
        cosine_sim = float(np.clip(cosine_sim, 0.0, 1.0))

        dist = float(np.linalg.norm(target_vec - sample_vec))
        # Max distance in 6D unit hypercube is sqrt(6) ~ 2.45
        euclidean_score = float(np.clip(1.0 - (dist / 2.45), 0.0, 1.0))

        final_score = (0.80 * cosine_sim) + (0.20 * euclidean_score)
        return float(np.clip(final_score, 0.0, 1.0))

    @classmethod
    def rank_candidates(
        cls,
        prompt: str,
        candidates: Dict[str, AcousticSignature],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Ranks candidates by semantic similarity to prompt."""
        target_vec = cls.parse_intent_to_target_vector(prompt)
        results = []

        for sample_id, sig in candidates.items():
            sim = cls.compute_similarity(target_vec, sig.vector)
            results.append({
                "id": sample_id,
                "score": round(float(sim), 4),
                "signature": sig.to_dict()
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

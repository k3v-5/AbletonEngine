"""
Unified Audio Feature Extractor.
Extracts complete AudioFeatures using Loudness, Frequency, Dynamics, Stereo, and Transient analyzers.
"""
from typing import Tuple
import numpy as np

from .models import AudioFeatures
from .loudness_analyzer import LoudnessAnalyzer
from .frequency_analyzer import FrequencyAnalyzer
from .dynamics_analyzer import DynamicsAnalyzer
from .stereo_analyzer import StereoAnalyzer
from .transient_analyzer import TransientAnalyzer


class FeatureExtractor:
    """Pipelines DSP analyzers to produce a comprehensive AudioFeatures object."""

    @classmethod
    def extract_all(cls, audio: np.ndarray, sr: int) -> AudioFeatures:
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
            
        channels, n_samples = audio.shape
        duration = float(n_samples / sr)

        # 1. Loudness & Peaks
        rms = float(20.0 * np.log10(np.sqrt(np.mean(audio**2) + 1e-12)))
        peak = float(20.0 * np.log10(np.max(np.abs(audio)) + 1e-12))
        true_peak = LoudnessAnalyzer.calculate_true_peak(audio)
        lufs_int, lufs_st, lufs_m = LoudnessAnalyzer.calculate_lufs(audio, sr)
        headroom_cls = LoudnessAnalyzer.calculate_headroom(peak, true_peak)

        # 2. Frequency & Spectral Profile
        spectral_profile = FrequencyAnalyzer.get_spectral_profile(audio, sr)

        # 3. Stereo & Mono Compatibility
        stereo_feats = StereoAnalyzer.analyze_stereo(audio, sr)

        # 4. Dynamics & Crest Factor
        crest_fact, dyn_range, lra, dyn_cls = DynamicsAnalyzer.analyze_dynamics(audio, sr)

        # 5. Transients
        trans_feats = TransientAnalyzer.analyze_transients(audio, sr)

        return AudioFeatures(
            duration=duration,
            sample_rate=sr,
            channels=channels,
            rms_db=rms,
            peak_db=peak,
            true_peak_db=true_peak,
            crest_factor=crest_fact,
            lufs_integrated=lufs_int,
            lufs_short_term=lufs_st,
            lufs_momentary=lufs_m,
            dynamic_range=dyn_range,
            lra=lra,
            spectral_profile=spectral_profile,
            stereo=stereo_feats,
            transients=trans_feats,
            headroom_class=headroom_cls,
            dynamics_class=dyn_cls
        )

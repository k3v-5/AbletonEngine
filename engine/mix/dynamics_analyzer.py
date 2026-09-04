"""
DSP Dynamics and Crest Factor Analyzer.
Measures dynamic range, crest factor, and variations.
"""
from typing import Tuple
import numpy as np

from .models import DynamicClassification


class DynamicsAnalyzer:
    """Analyzes dynamic range and transient-to-body ratios."""

    @staticmethod
    def analyze_dynamics(audio: np.ndarray, sr: int) -> Tuple[float, float, float, DynamicClassification]:
        """
        Returns:
        (crest_factor, dynamic_range_db, lra_estimate, dynamic_class)
        """
        if audio.size == 0:
            return 0.0, 0.0, 0.0, DynamicClassification.FLAT

        # Downmix to mono
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        peak_val = np.max(np.abs(mono)) + 1e-12
        rms_val = np.sqrt(np.mean(mono**2)) + 1e-12
        
        peak_db = 20.0 * np.log10(peak_val)
        rms_db = 20.0 * np.log10(rms_val)
        crest_factor = float(peak_db - rms_db)
        
        # Frame-based short term dynamic range (100ms frames)
        frame_size = int(0.100 * sr)
        if len(mono) < frame_size * 2:
            return crest_factor, crest_factor, 0.0, DynamicClassification.BALANCED
            
        num_frames = len(mono) // frame_size
        frame_rms = []
        for i in range(num_frames):
            f = mono[i*frame_size:(i+1)*frame_size]
            r = np.sqrt(np.mean(f**2)) + 1e-12
            frame_rms.append(20.0 * np.log10(r))
            
        frame_rms = np.array(frame_rms)
        # 10th and 95th percentiles
        p10 = np.percentile(frame_rms, 10)
        p95 = np.percentile(frame_rms, 95)
        dynamic_range_db = float(p95 - p10)
        lra_estimate = float(np.percentile(frame_rms, 95) - np.percentile(frame_rms, 10))

        # Classification
        if crest_factor < 6.0:
            dyn_class = DynamicClassification.OVER_COMPRESSED
        elif crest_factor > 14.0 or dynamic_range_db > 16.0:
            dyn_class = DynamicClassification.HIGHLY_DYNAMIC
        elif crest_factor > 11.0:
            dyn_class = DynamicClassification.TRANSIENT_HEAVY
        elif dynamic_range_db < 3.0:
            dyn_class = DynamicClassification.FLAT
        else:
            dyn_class = DynamicClassification.BALANCED

        return crest_factor, dynamic_range_db, lra_estimate, dyn_class

"""
Reference Engine: Compares current production mix against commercial reference audio files.
Produces delta profiles for loudness, frequency balance, dynamic range, and stereo width.
"""
from typing import Dict, Any, Tuple
from pathlib import Path
import soundfile as sf
import numpy as np

from .models import AudioFeatures
from .feature_extractor import FeatureExtractor


class ReferenceEngine:
    """Analyzes reference tracks and extracts acoustic deltas without blind copying."""

    @classmethod
    def compare_to_reference(cls, current_features: AudioFeatures, reference_audio_path: str) -> Dict[str, Any]:
        p = Path(reference_audio_path)
        if not p.exists():
            raise FileNotFoundError(f"Reference track not found: {reference_audio_path}")

        data, sr = sf.read(str(p), dtype="float32")
        if data.ndim == 1:
            ref_audio = data[np.newaxis, :]
        else:
            ref_audio = data.T

        ref_features = FeatureExtractor.extract_all(ref_audio, sr)

        # Compute differences
        lufs_delta = current_features.lufs_integrated - ref_features.lufs_integrated
        peak_delta = current_features.true_peak_db - ref_features.true_peak_db
        crest_delta = current_features.crest_factor - ref_features.crest_factor
        width_delta = current_features.stereo.width - ref_features.stereo.width
        low_width_delta = current_features.stereo.low_end_width - ref_features.stereo.low_end_width

        # Spectral differences
        cur_bands = current_features.spectral_profile.band_energies
        ref_bands = ref_features.spectral_profile.band_energies
        band_deltas = {}
        for b in cur_bands.keys():
            if b in ref_bands:
                band_deltas[b] = round(cur_bands[b] - ref_bands[b], 2)

        # Formulate insights
        insights = []
        if lufs_delta < -3.0:
            insights.append(f"Current mix is {abs(lufs_delta):.1f} LUFS quieter than reference (Note: finalize mastering in Stage 6).")
        elif lufs_delta > 2.0:
            insights.append(f"Current mix is {lufs_delta:.1f} LUFS louder than reference. Consider easing compression.")

        if band_deltas.get("20-40Hz", 0) > 3.0:
            insights.append("Current mix has significantly more sub-bass energy than reference.")
        elif band_deltas.get("20-40Hz", 0) < -3.0:
            insights.append("Current mix lacks sub-bass weight compared to reference.")

        if low_width_delta > 0.10:
            insights.append("Current mix has wider low-end (<120Hz) than reference. Monoing low frequencies recommended.")

        return {
            "reference_file": str(p.name),
            "reference_lufs": round(ref_features.lufs_integrated, 2),
            "reference_true_peak": round(ref_features.true_peak_db, 2),
            "reference_crest_factor": round(ref_features.crest_factor, 2),
            "reference_stereo_width": round(ref_features.stereo.width, 2),
            "deltas": {
                "lufs_delta": round(lufs_delta, 2),
                "true_peak_delta": round(peak_delta, 2),
                "crest_factor_delta": round(crest_delta, 2),
                "stereo_width_delta": round(width_delta, 2),
                "low_end_width_delta": round(low_width_delta, 3),
                "band_deltas_db": band_deltas
            },
            "insights": insights
        }

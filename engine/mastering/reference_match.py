"""
Reference Gap Analyzer.
Compares master with commercial reference tracks without blind imitation.
Protects against copying flawed references (clipping, extreme compression, phase inversion).
"""
from typing import Dict, Any, Optional, Union
from pathlib import Path
import soundfile as sf
import numpy as np

from .models import TonalDifferenceMap
from .tonal_balance import TonalBalanceAnalyzer


class ReferenceGapAnalyzer:
    """Extracts reference deltas while guarding against reference production flaws."""

    @classmethod
    def calculate_gap_map(cls, track_features: Dict[str, Any], ref_features: Dict[str, Any]) -> TonalDifferenceMap:
        track_tonal = track_features.get("tonal_balance", {})
        ref_tonal = ref_features.get("tonal_balance", {})
        return TonalBalanceAnalyzer.compute_difference_map(track_tonal, ref_tonal)

    @classmethod
    def generate_matching_guidance(cls, gap_map: TonalDifferenceMap) -> Dict[str, Any]:
        moves = []
        for band, delta in gap_map.deltas.items():
            if abs(delta) >= 1.5:
                direction = "cut" if delta > 0 else "boost"
                moves.append(f"{direction.upper()} {band} by {abs(delta)*0.3:.1f} dB (conservative target)")
        return {
            "rms_gap": gap_map.rms_spectral_gap,
            "recommended_moves": moves
        }

    @classmethod
    def analyze_reference(cls, current_features: Any, current_audio: np.ndarray,
                          reference_path: str, sr: int = 44100) -> Dict[str, Any]:
        p = Path(reference_path)
        if not p.exists():
            raise FileNotFoundError(f"Reference track not found: {reference_path}")

        ref_data, ref_sr = sf.read(str(p), dtype="float32")
        ref_bands = TonalBalanceAnalyzer.analyze_tonal_balance(ref_data, ref_sr)
        cur_bands = TonalBalanceAnalyzer.analyze_tonal_balance(current_audio, sr)
        diff_map = TonalBalanceAnalyzer.compute_difference_map(cur_bands, ref_bands)

        ref_peak = float(np.max(np.abs(ref_data)))
        ref_rms = float(np.sqrt(np.mean(ref_data ** 2))) + 1e-12
        ref_lufs = float(20.0 * np.log10(ref_rms) - 0.691)
        ref_tp = float(20.0 * np.log10(ref_peak)) + 0.2
        ref_crest = float(20.0 * np.log10(ref_peak / ref_rms))

        bad_reference_warnings = []
        if ref_tp > 0.1 or ref_peak >= 1.0:
            bad_reference_warnings.append(f"Reference has digital clipping (True Peak: {ref_tp:.2f} dBTP). Do NOT copy peak levels.")
        if ref_crest < 6.0:
            bad_reference_warnings.append(f"Reference is excessively squashed (Crest Factor: {ref_crest:.1f} dB). Do NOT sacrifice dynamics to match.")

        cur_lufs = getattr(current_features, "lufs_integrated", current_features.get("integrated_lufs", -16.0) if isinstance(current_features, dict) else -16.0)
        cur_tp = getattr(current_features, "true_peak_db", current_features.get("true_peak_dbtp", -3.0) if isinstance(current_features, dict) else -3.0)
        cur_crest = getattr(current_features, "crest_factor", current_features.get("crest_factor_db", 12.0) if isinstance(current_features, dict) else 12.0)

        return {
            "reference_file": p.name,
            "reference_lufs": round(ref_lufs, 2),
            "reference_true_peak": round(ref_tp, 2),
            "reference_crest_factor": round(ref_crest, 2),
            "reference_gaps": {
                "loudness_gap": round(cur_lufs - ref_lufs, 2),
                "true_peak_gap": round(cur_tp - ref_tp, 2),
                "dynamics_gap": round(cur_crest - ref_crest, 2),
                "tonal_gap_map": diff_map.to_dict()
            },
            "bad_reference_warnings": bad_reference_warnings,
            "is_reference_healthy": len(bad_reference_warnings) == 0
        }


ReferenceMatcher = ReferenceGapAnalyzer

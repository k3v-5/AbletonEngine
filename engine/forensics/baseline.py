"""
Track Baseline Statistical Profile Engine (PIE Phase 7).
Computes track-specific distributions (mean, median, std, p10, p50, p90)
to establish dynamic acoustic reference baselines.
"""
from typing import Dict, List, Any, Optional, Union
import numpy as np

from .models import TrackBaseline, AudioFrame, AnalysisConfig
from .config import STANDARD_FREQUENCY_BANDS, DEFAULT_ANALYSIS_CONFIG
from .stft import STFTEngine


class BaselineEngine:
    """
    Computes statistical baseline distributions for RMS, peaks, centroids, and the 14 frequency bands.
    """

    @staticmethod
    def compute_distribution_stats(values: np.ndarray) -> Dict[str, float]:
        """Calculates standard percentile and summary statistics for a 1D array."""
        arr = np.asarray(values, dtype=np.float64)
        if len(arr) == 0:
            return {
                "mean": 0.0, "median": 0.0, "std": 0.0,
                "p10": 0.0, "p50": 0.0, "p90": 0.0,
                "percentile_10": 0.0, "percentile_50": 0.0, "percentile_90": 0.0
            }
        p10 = round(float(np.percentile(arr, 10)), 2)
        p50 = round(float(np.percentile(arr, 50)), 2)
        p90 = round(float(np.percentile(arr, 90)), 2)
        return {
            "mean": round(float(np.mean(arr)), 2),
            "median": round(float(np.median(arr)), 2),
            "std": round(float(np.std(arr)), 2),
            "p10": p10,
            "p50": p50,
            "p90": p90,
            "percentile_10": p10,
            "percentile_50": p50,
            "percentile_90": p90
        }

    # Backward compatibility alias
    _compute_distribution_stats = compute_distribution_stats

    @classmethod
    def compute_baseline(
        cls,
        *args,
        **kwargs
    ) -> TrackBaseline:
        """
        Flexible extractor of TrackBaseline supporting:
        - compute_baseline(frames, stft_result, track_id="default_track")
        - compute_baseline(audio, sample_rate, frames, config, track_id="...")
        - compute_baseline(audio=..., sample_rate=..., frames=..., config=..., track_id=...)
        """
        track_id = kwargs.get("track_id", "default_track")
        audio = kwargs.get("audio")
        sample_rate = kwargs.get("sample_rate", 44100)
        frames: Optional[List[AudioFrame]] = kwargs.get("frames")
        stft_result: Optional[Dict[str, Any]] = kwargs.get("stft_result")
        cfg = kwargs.get("config", DEFAULT_ANALYSIS_CONFIG)

        # Parse positional args if passed
        if len(args) == 2:
            # (frames, stft_result)
            frames = args[0]
            stft_result = args[1]
        elif len(args) == 3 and isinstance(args[2], str):
            # (frames, stft_result, track_id)
            frames = args[0]
            stft_result = args[1]
            track_id = args[2]
        elif len(args) >= 3 and isinstance(args[0], np.ndarray):
            # (audio, sample_rate, frames, [config], [track_id])
            audio = args[0]
            sample_rate = args[1]
            frames = args[2]
            if len(args) >= 4 and isinstance(args[3], AnalysisConfig):
                cfg = args[3]
            if len(args) >= 5 and isinstance(args[4], str):
                track_id = args[4]

        # Ensure STFT is available for spectral band baselines
        if stft_result is None:
            if audio is not None:
                stft_result = STFTEngine.compute_stft(audio, sample_rate, cfg)
            else:
                stft_result = {}

        if not frames:
            return TrackBaseline(track_id=track_id)

        rms_arr = np.array([f.rms_dbfs for f in frames], dtype=np.float64)
        peak_arr = np.array([f.peak_dbfs for f in frames], dtype=np.float64)
        centroid_arr = np.array([f.spectral_centroid_hz for f in frames], dtype=np.float64)
        crest_arr = peak_arr - rms_arr

        rms_stats = cls.compute_distribution_stats(rms_arr)
        peak_stats = cls.compute_distribution_stats(peak_arr)
        centroid_stats = cls.compute_distribution_stats(centroid_arr)
        crest_stats = cls.compute_distribution_stats(crest_arr)

        band_baselines: Dict[str, Dict[str, float]] = {}

        if "powers" in stft_result and "frequencies_hz" in stft_result:
            powers = stft_result["powers"]  # (channels, frames, bins)
            freqs = stft_result["frequencies_hz"]
            avg_powers = np.mean(powers, axis=0)  # (frames, bins)

            for band_name, f_min, f_max in STANDARD_FREQUENCY_BANDS:
                mask = (freqs >= f_min) & (freqs < f_max)
                if np.any(mask):
                    band_pwr_per_frame = np.sum(avg_powers[:, mask], axis=1)
                else:
                    band_pwr_per_frame = np.zeros(avg_powers.shape[0])

                band_db_per_frame = 10.0 * np.log10(band_pwr_per_frame + 1e-12)
                band_baselines[band_name] = cls.compute_distribution_stats(band_db_per_frame)
        else:
            for band_name, _, _ in STANDARD_FREQUENCY_BANDS:
                band_baselines[band_name] = cls.compute_distribution_stats(np.array([]))

        # Stereo correlation baseline if stereo audio is provided
        stereo_corr_stats = {}
        if audio is not None and audio.ndim == 2 and audio.shape[0] == 2:
            win_size = int(0.050 * sample_rate)
            hop_size = int(0.025 * sample_rate)
            if audio.shape[1] >= win_size:
                num_win = (audio.shape[1] - win_size) // hop_size + 1
                corrs = []
                for i in range(num_win):
                    s = i * hop_size
                    l_b = audio[0, s:s + win_size]
                    r_b = audio[1, s:s + win_size]
                    n_l = np.linalg.norm(l_b)
                    n_r = np.linalg.norm(r_b)
                    if n_l > 1e-6 and n_r > 1e-6:
                        c = np.dot(l_b, r_b) / (n_l * n_r)
                        corrs.append(c)
                if corrs:
                    stereo_corr_stats = cls.compute_distribution_stats(np.array(corrs))

        return TrackBaseline(
            track_id=track_id,
            rms_stats=rms_stats,
            peak_stats=peak_stats,
            centroid_stats=centroid_stats,
            band_baselines=band_baselines,
            crest_factor_stats=crest_stats,
            stereo_correlation_stats=stereo_corr_stats
        )

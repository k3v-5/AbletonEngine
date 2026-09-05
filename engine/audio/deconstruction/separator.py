# engine/audio/deconstruction/separator.py
"""
Audio Stem Separator using Pure DSP Multi-Band Crossover & Mid-Side Decomposition.
Produces 4 stems: drums, bass, vocals, other.
Zero heavy dependencies, fully deterministic, fast and robust.
"""

import os
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import soundfile as sf

from engine.audio.deconstruction.models import DeconstructedStem, StemCategory

class AudioStemSeparator:
    """Separates a mixed audio track into Drums, Bass, Vocals, and Other stems."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path(r"F:\Dev\AbletonEngine\stems")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _compute_rms_db(data: np.ndarray) -> float:
        """Calculates RMS level in decibels."""
        rms = np.sqrt(np.mean(data ** 2) + 1e-12)
        return float(20.0 * np.log10(max(rms, 1e-6)))

    @staticmethod
    def _compute_peak_db(data: np.ndarray) -> float:
        """Calculates peak level in decibels."""
        peak = np.max(np.abs(data)) + 1e-12
        return float(20.0 * np.log10(max(peak, 1e-6)))

    def _stft_mask(
        self,
        audio_stereo: np.ndarray,
        sr: int,
        low_freq: float,
        high_freq: float,
        mid_weight: float = 1.0,
        side_weight: float = 1.0
    ) -> np.ndarray:
        """
        Applies a smooth frequency bandpass and mid-side weighting mask via STFT.
        """
        n_samples = audio_stereo.shape[0]
        n_fft = 4096
        hop_length = 1024
        win = np.hanning(n_fft)
        
        # Mid / Side decomposition
        mid = 0.5 * (audio_stereo[:, 0] + audio_stereo[:, 1])
        side = 0.5 * (audio_stereo[:, 0] - audio_stereo[:, 1])
        
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)
        
        # Frequency band mask with sigmoid-like smooth edges
        band_mask = np.zeros(len(freqs), dtype=np.float32)
        for i, f in enumerate(freqs):
            if f < low_freq * 0.7:
                band_mask[i] = 0.0
            elif f < low_freq:
                band_mask[i] = 0.5 * (1.0 + np.sin(np.pi * (f - low_freq * 0.85) / (low_freq * 0.3)))
            elif f <= high_freq:
                band_mask[i] = 1.0
            elif f < high_freq * 1.3:
                band_mask[i] = 0.5 * (1.0 + np.cos(np.pi * (f - high_freq) / (high_freq * 0.3)))
            else:
                band_mask[i] = 0.0

        # Process Mid & Side channels with overlap-add
        out_mid = np.zeros(n_samples + n_fft, dtype=np.float32)
        out_side = np.zeros(n_samples + n_fft, dtype=np.float32)
        norm_window = np.zeros(n_samples + n_fft, dtype=np.float32)
        
        num_frames = max(1, (n_samples - n_fft) // hop_length + 1)
        for frame in range(num_frames):
            start = frame * hop_length
            end = start + n_fft
            if end > n_samples:
                break
                
            chunk_m = mid[start:end] * win
            chunk_s = side[start:end] * win
            
            fft_m = np.fft.rfft(chunk_m) * band_mask * mid_weight
            fft_s = np.fft.rfft(chunk_s) * band_mask * side_weight
            
            rec_m = np.fft.irfft(fft_m, n=n_fft) * win
            rec_s = np.fft.irfft(fft_s, n=n_fft) * win
            
            out_mid[start:end] += rec_m
            out_side[start:end] += rec_s
            norm_window[start:end] += win ** 2

        # Normalize overlap-add window
        valid = norm_window > 1e-6
        out_mid[valid] /= norm_window[valid]
        out_side[valid] /= norm_window[valid]
        
        out_mid = out_mid[:n_samples]
        out_side = out_side[:n_samples]
        
        # Reconstruct stereo from Mid/Side
        left = out_mid + out_side
        right = out_mid - out_side
        return np.column_stack([left, right])

    def _extract_transients(self, audio_stereo: np.ndarray, sr: int) -> np.ndarray:
        """
        Extracts sharp transient rhythmic energy (kick onsets, snare cracks, hats)
        using differential envelope detection.
        """
        mono = 0.5 * (audio_stereo[:, 0] + audio_stereo[:, 1])
        envelope = np.abs(mono)
        
        # Moving average filter for smoothing
        win_len = int(sr * 0.02)  # 20ms
        if win_len % 2 == 0:
            win_len += 1
        box = np.ones(win_len) / win_len
        local_mean = np.convolve(envelope, box, mode='same')
        
        # Transient ratio: where instant amplitude significantly exceeds local moving average
        transient_ratio = np.maximum(0.0, (envelope - local_mean * 1.3))
        # Smooth transient gain between 0.0 and 1.0
        gain = np.clip(transient_ratio / (np.max(transient_ratio) + 1e-6) * 2.5, 0.0, 1.0)
        
        drums = np.zeros_like(audio_stereo)
        drums[:, 0] = audio_stereo[:, 0] * gain
        drums[:, 1] = audio_stereo[:, 1] * gain
        return drums

    def separate(
        self,
        audio_input: Any,
        sample_rate: Optional[int] = None,
        base_name: str = "reference"
    ) -> Dict[str, DeconstructedStem]:
        """
        Separates audio into drums, bass, vocals, and other stems.
        audio_input can be a file path (str/Path) or a numpy array.
        """
        if isinstance(audio_input, (str, Path)):
            p = Path(audio_input)
            data, sr = sf.read(str(p), always_2d=True)
            if not base_name or base_name == "reference":
                base_name = p.stem
        else:
            data = np.asarray(audio_input, dtype=np.float32)
            if data.ndim == 1:
                data = np.column_stack([data, data])
            sr = sample_rate or 44100

        data = data.astype(np.float32)
        n_samples = data.shape[0]
        duration = float(n_samples / sr)

        # 1. BASS: 20 Hz - 220 Hz, Mid only (centered mono low-end)
        bass = self._stft_mask(data, sr, low_freq=20.0, high_freq=220.0, mid_weight=1.0, side_weight=0.1)

        # 2. VOCALS: 300 Hz - 3800 Hz, Mid-heavy (center isolation)
        vocals = self._stft_mask(data, sr, low_freq=300.0, high_freq=3800.0, mid_weight=1.0, side_weight=0.15)

        # 3. DRUMS: Transient energy extraction (kicks, snares, hats)
        drums = self._extract_transients(data, sr)

        # 4. OTHER: Harmonic residual (synths, guitars, pads, stereo ambience)
        combined = bass + vocals + drums
        other = data - combined * 0.7
        # Ensure 'other' retains stereo width and pleasant high end
        other = np.clip(other, -1.0, 1.0)

        stems_data = {
            StemCategory.DRUMS: drums,
            StemCategory.BASS: bass,
            StemCategory.VOCALS: vocals,
            StemCategory.OTHER: other
        }

        results: Dict[str, DeconstructedStem] = {}
        for category, stem_arr in stems_data.items():
            # Prevent digital clipping
            peak = np.max(np.abs(stem_arr))
            if peak > 1.0:
                stem_arr = stem_arr / peak

            stem_filename = f"{base_name}_{category.value}.wav"
            stem_filepath = self.output_dir / stem_filename
            sf.write(str(stem_filepath), stem_arr, sr)

            results[category.value] = DeconstructedStem(
                category=category,
                audio_path=str(stem_filepath),
                sample_rate=sr,
                duration_seconds=duration,
                rms_db=self._compute_rms_db(stem_arr),
                peak_db=self._compute_peak_db(stem_arr),
                metadata={"channels": 2, "samples": n_samples}
            )

        return results

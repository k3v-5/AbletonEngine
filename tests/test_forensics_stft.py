"""
Tests for STFT Analysis Engine (PIE Phase 7).
Validates STFT mathematical resolutions, shapes, windowing, and input guards.
"""
import pytest
import numpy as np

from engine.forensics.stft import STFTEngine
from engine.forensics.models import AnalysisConfig
from engine.forensics.exceptions import InvalidAudioError, UnsupportedWindowError


class TestForensicsSTFT:

    def test_stft_resolution_and_shapes(self):
        sr = 48000
        duration_s = 1.0
        n_samples = int(sr * duration_s)
        # Stereo audio
        audio = np.zeros((2, n_samples), dtype=np.float32)

        cfg = AnalysisConfig(fft_size=2048, hop_size=512, window="hann")
        res = STFTEngine.compute_stft(audio, sr, cfg)

        expected_f_res = sr / 2048.0
        expected_t_res = 512.0 / sr

        assert abs(res["frequency_resolution_hz"] - expected_f_res) < 1e-4
        assert abs(res["time_resolution_seconds"] - expected_t_res) < 1e-4

        magnitudes = res["magnitudes"]
        powers = res["powers"]
        freqs = res["frequencies_hz"]
        timestamps = res["time_stamps_seconds"]

        # Shape: (channels, frames, bins)
        expected_bins = 2048 // 2 + 1
        expected_frames = (n_samples - 2048) // 512 + 1

        assert magnitudes.shape == (2, expected_frames, expected_bins)
        assert powers.shape == (2, expected_frames, expected_bins)
        assert len(freqs) == expected_bins
        assert len(timestamps) == expected_frames
        assert freqs[0] == 0.0
        assert freqs[-1] == sr / 2.0

    def test_stft_sine_tone_peak_bin(self):
        sr = 44100
        freq_target = 1000.0  # 1 kHz
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        tone = 0.8 * np.sin(2 * np.pi * freq_target * t)

        res = STFTEngine.compute_stft(tone, sr)
        mag = res["magnitudes"][0]  # (frames, bins)
        freqs = res["frequencies_hz"]

        # Peak bin should match ~1000 Hz across frames
        avg_spectrum = np.mean(mag, axis=0)
        peak_bin = int(np.argmax(avg_spectrum))
        detected_freq = freqs[peak_bin]

        assert abs(detected_freq - freq_target) <= res["frequency_resolution_hz"]

    def test_stft_input_validation(self):
        sr = 44100
        # Empty array
        with pytest.raises(InvalidAudioError):
            STFTEngine.compute_stft(np.array([]), sr)

        # 3D array
        with pytest.raises(InvalidAudioError):
            STFTEngine.compute_stft(np.zeros((2, 3, 100)), sr)

        # NaN or Inf
        bad_audio = np.zeros((1, 1000))
        bad_audio[0, 50] = np.nan
        with pytest.raises(InvalidAudioError):
            STFTEngine.compute_stft(bad_audio, sr)

        # Negative sample rate
        with pytest.raises(InvalidAudioError):
            STFTEngine.compute_stft(np.zeros((1, 1000)), -44100)

        # Too short for FFT
        cfg = AnalysisConfig(fft_size=4096)
        with pytest.raises(InvalidAudioError):
            STFTEngine.compute_stft(np.zeros((1, 100)), sr, cfg)

        # Unsupported window
        bad_cfg = AnalysisConfig(window="invalid_window")
        with pytest.raises(UnsupportedWindowError):
            STFTEngine.compute_stft(np.zeros((1, 4000)), sr, bad_cfg)

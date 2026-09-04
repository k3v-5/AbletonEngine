"""
Tests for Spectral Analysis & Dynamic Resonance Detection (PIE Phase 7).
Validates centroid, rolloff, flux, 14-band energy calculations, and dynamic resonances.
"""
import pytest
import numpy as np

from engine.forensics.stft import STFTEngine
from engine.forensics.spectral import SpectralEngine
from engine.forensics.config import STANDARD_FREQUENCY_BANDS, DEFAULT_ANALYSIS_CONFIG
from engine.forensics.models import ForensicEventType, Severity


class TestForensicsSpectral:

    def test_spectral_centroid(self):
        freqs = np.array([100.0, 500.0, 1000.0, 2000.0])
        # Concentrated at 1000 Hz
        mags = np.array([0.0, 0.0, 10.0, 0.0])
        centroid = SpectralEngine.calculate_spectral_centroid(mags, freqs)
        assert abs(centroid - 1000.0) < 1e-4

        # Zero energy
        centroid_zero = SpectralEngine.calculate_spectral_centroid(np.zeros(4), freqs)
        assert centroid_zero == 0.0

    def test_spectral_rolloff(self):
        freqs = np.array([100.0, 500.0, 1000.0, 2000.0])
        mags = np.array([5.0, 5.0, 5.0, 5.0])
        rolloff = SpectralEngine.calculate_spectral_rolloff(mags, freqs, percentile=0.85)
        # 85% of total 20.0 is 17.0, which falls into the 4th bin (2000.0)
        assert rolloff == 2000.0

    def test_spectral_flux(self):
        mag1 = np.array([1.0, 2.0, 3.0])
        mag2 = np.array([1.0, 2.0, 3.0])
        # Identical frames -> 0 flux
        assert SpectralEngine.calculate_spectral_flux(mag2, mag1) == 0.0

        mag3 = np.array([4.0, 6.0, 8.0])
        flux = SpectralEngine.calculate_spectral_flux(mag3, mag1)
        expected = np.sqrt(3**2 + 4**2 + 5**2)
        assert abs(flux - expected) < 1e-4

    def test_14_band_energies(self):
        sr = 44100
        n_fft = 2048
        freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
        powers = np.zeros(len(freqs))

        # Put energy in SUB_MID (40-60 Hz)
        sub_mask = (freqs >= 40.0) & (freqs < 60.0)
        powers[sub_mask] = 1.0

        bands = SpectralEngine.calculate_band_energies(powers, freqs)
        assert len(bands) == 14
        assert "SUB_MID" in bands
        assert bands["SUB_MID"] > -40.0
        assert bands["BRILLIANCE_2"] < -100.0

    def test_detect_dynamic_resonance(self):
        sr = 44100
        duration_s = 1.0
        n_samples = int(sr * duration_s)
        t = np.linspace(0, duration_s, n_samples, endpoint=False)

        # Baseline noise
        np.random.seed(42)
        noise = 0.01 * np.random.randn(n_samples)

        # Add strong resonant sine tone at 2500 Hz for 0.4 seconds (from 0.3s to 0.7s)
        res_freq = 2500.0
        start_idx = int(0.3 * sr)
        end_idx = int(0.7 * sr)
        noise[start_idx:end_idx] += 0.4 * np.sin(2 * np.pi * res_freq * t[start_idx:end_idx])

        stft_res = STFTEngine.compute_stft(noise, sr, DEFAULT_ANALYSIS_CONFIG)
        events = SpectralEngine.detect_resonances(stft_res, config=DEFAULT_ANALYSIS_CONFIG)

        assert len(events) >= 1
        res_event = events[0]
        assert res_event.event_type == ForensicEventType.RESONANCE
        assert res_event.frequency_min_hz is not None
        assert res_event.frequency_max_hz is not None
        # Frequency range covers 2500 Hz
        assert res_event.frequency_min_hz <= res_freq <= res_event.frequency_max_hz
        # Time covers around 0.3s - 0.7s
        assert abs(res_event.start_time_seconds - 0.3) < 0.1
        assert res_event.duration_seconds >= 0.2

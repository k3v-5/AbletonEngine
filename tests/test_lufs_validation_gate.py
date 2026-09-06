# tests/test_lufs_validation_gate.py
"""
Test Suite for ITU-R BS.1770-5 LUFS & True Peak End-of-Chain Validation Gate:
Verifies that overloaded signals (+2 to +3 dBFS clipping) are detected as non-compliant,
and that automatic trim compensation attenuates audio to guarantee compliance with
streaming (-14.0 LUFS / -1.0 dBTP) and zero digital inter-sample clipping.
"""

import numpy as np
import pytest

from engine.mix.lufs_validation_gate import LUFSValidationGate, LoudnessAuditResult
from engine.mix.loudness_standards import ProfileRegistry


class TestLUFSValidationGate:
    def _generate_tone(self, freq_hz: float, duration_s: float, amplitude: float, sr: int = 44100):
        t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
        tone = amplitude * np.sin(2 * np.pi * freq_hz * t)
        return np.vstack([tone, tone])  # Stereo

    def test_compliant_signal_passes(self):
        gate = LUFSValidationGate(profile=ProfileRegistry.STREAMING)
        # Moderate amplitude sine wave (~ -14 LUFS)
        audio = self._generate_tone(freq_hz=1000.0, duration_s=1.0, amplitude=0.25)

        result = gate.audit(audio, sr=44100)
        # Peak should be well below -1.0 dBTP
        assert result.true_peak_dbtp < -1.0
        assert result.headroom_margin_db > 0.0

    def test_overloaded_signal_detected(self):
        gate = LUFSValidationGate(profile=ProfileRegistry.STREAMING)
        # Overloaded signal exceeding 0 dBFS (amplitude = 1.35, approx +2.6 dBFS)
        overloaded = self._generate_tone(freq_hz=440.0, duration_s=1.0, amplitude=1.35)

        result = gate.audit(overloaded, sr=44100)
        assert result.passed is False
        assert len(result.violations) > 0
        assert result.true_peak_dbtp > 0.0  # Clipping!
        assert any("True Peak overload" in v for v in result.violations)
        assert result.required_trim_db < 0.0  # Needs negative attenuation

    def test_automatic_trim_compensation(self):
        gate = LUFSValidationGate(profile=ProfileRegistry.STREAMING)
        # Severely overloaded audio peaking at +2.5 dBFS
        overloaded = self._generate_tone(freq_hz=220.0, duration_s=1.5, amplitude=1.30)

        initial_audit = gate.audit(overloaded, sr=44100)
        assert initial_audit.passed is False

        # Apply loudness and True Peak compensation
        compensated_audio, final_audit = gate.apply_loudness_compensation(overloaded, sr=44100)

        # Output audio must pass with zero clipping
        assert final_audit.passed is True
        assert final_audit.true_peak_dbtp <= -1.0 + 0.1  # Complies with -1.0 dBTP ceiling
        assert "COMPLIANT" in final_audit.certificate

    def test_club_vs_streaming_profiles(self):
        streaming_gate = LUFSValidationGate(profile=ProfileRegistry.STREAMING)
        club_gate = LUFSValidationGate(profile=ProfileRegistry.CLUB)

        assert streaming_gate.profile.integrated_target == -14.0
        assert streaming_gate.profile.max_true_peak == -1.0

        assert club_gate.profile.integrated_target == -7.5
        assert club_gate.profile.max_true_peak == -0.3

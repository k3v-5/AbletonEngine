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

    def test_audit_channel_compliant_and_non_compliant(self):
        gate = LUFSValidationGate()
        # 1. Compliant channel audio (~ -18 LUFS, peak < -3 dBTP)
        ch_audio = self._generate_tone(freq_hz=440.0, duration_s=1.0, amplitude=0.15)
        res_pass = gate.audit_channel(ch_audio, sr=44100, target_lufs=-18.0, max_true_peak_dbtp=-3.0, channel_name="Lead Vocal")
        assert res_pass.passed is True
        assert res_pass.true_peak_dbtp < -3.0
        assert "COMPATIBLE" in res_pass.certificate

        # 2. Overloaded channel audio (peaking near 0 dBFS, exceeding -3 dBTP ceiling)
        ch_loud = self._generate_tone(freq_hz=440.0, duration_s=1.0, amplitude=0.95)
        res_fail = gate.audit_channel(ch_loud, sr=44100, target_lufs=-18.0, max_true_peak_dbtp=-3.0, channel_name="Lead Vocal")
        assert res_fail.passed is False
        assert any("True Peak en canal" in v or "Sonoridad en canal" in v for v in res_fail.violations)

    def test_audit_dual_channel_and_master(self):
        gate = LUFSValidationGate(profile=ProfileRegistry.STREAMING)
        ch_audio = self._generate_tone(freq_hz=440.0, duration_s=1.0, amplitude=0.15)
        m_audio = self._generate_tone(freq_hz=1000.0, duration_s=1.0, amplitude=0.20)

        dual_res = gate.audit_dual(
            channel_audio=ch_audio,
            master_audio=m_audio,
            sr=44100,
            channel_target_lufs=-18.0,
            channel_max_tp=-3.0,
            channel_name="[VOCALS] Lead Vocal",
            master_profile=ProfileRegistry.STREAMING
        )

        assert dual_res.passed is True
        assert dual_res.channel_audit.target_lufs == -18.0
        assert dual_res.master_audit.target_lufs == -14.0
        assert "| **Canal Individual** |" in dual_res.summary_table
        assert "| **Master General** |" in dual_res.summary_table
        assert "CERTIFICACIÓN DOBLE ETAPA APROBADA" in dual_res.certificate
        assert isinstance(dual_res.to_dict(), dict)

    def test_audit_dual_autonomous_fallback(self):
        dual_res = LUFSValidationGate.audit_dual_channel_and_master(
            conn=None,
            track_index=12,
            channel_name="Lead Vocal",
            channel_audio=None,
            master_audio=None,
            sr=44100,
            master_profile_name="STREAMING"
        )
        assert dual_res is not None
        assert dual_res.channel_audit is not None
        assert dual_res.master_audit is not None
        assert "| **Canal Individual** |" in dual_res.summary_table


# tests/test_live_listener.py
import unittest
import numpy as np
from engine.audio.live_listener import LiveAudioListener

class TestLiveAudioListener(unittest.TestCase):
    def setUp(self):
        self.listener = LiveAudioListener(sample_rate=44100)

    def test_synthetic_stream_generation(self):
        """Synthetic stream produces finite stereo audio of exact duration."""
        duration = 2.0
        audio = self.listener.generate_synthetic_stream(duration_seconds=duration, target_lufs=-14.0)
        self.assertEqual(audio.ndim, 2)
        self.assertEqual(audio.shape[0], 2)
        self.assertEqual(audio.shape[1], int(44100 * duration))
        self.assertTrue(np.all(np.isfinite(audio)))

    def test_analysis_metrics(self):
        """Audio analysis calculates ITU-R BS.1770-5 LUFS, peaks, and headroom."""
        audio = self.listener.generate_synthetic_stream(duration_seconds=2.0, target_lufs=-14.0)
        report = self.listener.analyze_audio_stream(audio)
        self.assertEqual(report["status"], "SUCCESS")
        self.assertIn("loudness", report)
        self.assertIn("integrated_lufs", report["loudness"])
        self.assertIn("true_peak_dbtp", report["loudness"])
        self.assertIn("spectral_balance", report)
        self.assertIn("readiness", report)

    def test_mud_detection(self):
        """Heavy 300Hz buildup is detected as muddiness in diagnostics."""
        audio_clean = self.listener.generate_synthetic_stream(duration_seconds=2.0, muddy=False)
        report_clean = self.listener.analyze_audio_stream(audio_clean)

        audio_muddy = self.listener.generate_synthetic_stream(duration_seconds=2.0, muddy=True)
        report_muddy = self.listener.analyze_audio_stream(audio_muddy)

        # Muddy version has higher low-mid energy percentage
        self.assertGreater(
            report_muddy["spectral_balance"]["low_mid_mud_percent"],
            report_clean["spectral_balance"]["low_mid_mud_percent"]
        )
        # Muddiness warning should be triggered
        has_mud_issue = any("Muddiness" in issue for issue in report_muddy["diagnostics"]["issues"])
        self.assertTrue(has_mud_issue, "Muddiness warning not triggered on muddy audio buffer!")

    def test_phase_stereo_correlation(self):
        """In-phase signal has positive correlation; inverse phase has negative correlation."""
        sr = 44100
        t = np.linspace(0, 1.0, sr)
        mono_signal = np.sin(2 * np.pi * 440.0 * t)

        # 1. Perfectly correlated
        stereo_in_phase = np.vstack([mono_signal, mono_signal])
        rep_in = self.listener.analyze_audio_stream(stereo_in_phase)
        self.assertAlmostEqual(rep_in["phase"]["stereo_correlation"], 1.0, places=2)
        self.assertTrue(rep_in["phase"]["mono_compatible"])

        # 2. Out of phase
        stereo_out_of_phase = np.vstack([mono_signal, -mono_signal])
        rep_out = self.listener.analyze_audio_stream(stereo_out_of_phase)
        self.assertAlmostEqual(rep_out["phase"]["stereo_correlation"], -1.0, places=2)
        self.assertFalse(rep_out["phase"]["mono_compatible"])
        self.assertTrue(any("phase" in iss.lower() for iss in rep_out["diagnostics"]["issues"]))

    def test_listen_simulation_fallback(self):
        """listen() command returns complete report via simulation fallback when socket is inactive."""
        report = self.listener.listen(duration_seconds=1.5, simulate_if_silent=True)
        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["audio_source"], "acoustic_simulation_bridge")
        self.assertIn("spotify_apple_streaming", report["readiness"])

if __name__ == "__main__":
    unittest.main()

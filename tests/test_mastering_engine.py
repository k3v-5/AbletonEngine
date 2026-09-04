"""
Comprehensive Unit & Acceptance Test Suite for Fase 6: Mastering Engine.
Tests all 10 mandatory acceptance tests (A through J).
"""
import unittest
import numpy as np
import tempfile
import os
from pathlib import Path

from engine.mastering import (
    DeliveryTarget, MasteringMode, QualityGate, MasterReadiness,
    TonalDifferenceMap, FinalQualityScore, MasterPlan, MasterAction,
    LoudnessTargetCalculator, TruePeakEngine, DynamicPreservationEngine,
    TonalBalanceAnalyzer, MasterStereoEngine, MasterEQEngine,
    MasterCompressorEngine, MasterSaturationEngine, MasterLimiterEngine,
    TranslationTestEngine, ReferenceGapAnalyzer, FinalQualityControlEngine,
    MasteringOptimizer, MasterSnapshotManager, MasterRollbackManager,
    MasterExportManager, MasteringReportGenerator, MasterChainBuilder,
    MasteringAnalyzer, MasteringEngine
)


class TestMasteringEngine(unittest.TestCase):
    """Test suite covering the 10 Acceptance Criteria for Mastering Engine."""

    def setUp(self):
        self.sr = 44100
        self.duration = 2.0
        self.t = np.linspace(0, self.duration, int(self.sr * self.duration), endpoint=False)
        self.engine = MasteringEngine()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_a_clean_mix_do_nothing(self):
        """Test A: Clean Mix Ready -> DO NOTHING Principle."""
        # Mix already meeting streaming requirements (-14.0 LUFS, -1.1 dBTP, balanced)
        clean_features = {
            "integrated_lufs": -14.0,
            "lufs": -14.0,
            "true_peak_dbtp": -1.1,
            "true_peak": -1.1,
            "crest_factor_db": 12.0,
            "tonal_balance": {"sub": 0.0, "low": 0.0, "low_mid": 0.0, "mid": 0.0, "high_mid": 0.0, "presence": 0.0, "brilliance": 0.0},
            "stereo_correlation": 0.95,
            "stereo_width": 1.0,
            "clipping_detected": False
        }
        readiness = self.engine.check_readiness(clean_features, DeliveryTarget.STREAMING)
        self.assertTrue(readiness.is_ready, "Clean mix must be deemed ready")
        self.assertTrue(readiness.is_already_compliant, "Clean compliant mix must trigger is_already_compliant")

        plan = self.engine.generate_plan(clean_features, DeliveryTarget.STREAMING)
        self.assertTrue(plan.is_do_nothing, "Plan must recommend DO_NOTHING for already compliant mix")
        self.assertTrue(any(a.action_type == "DO_NOTHING" for a in plan.actions))

    def test_b_excessive_low_end_correction(self):
        """Test B: Excessive Low-End -> Reject as MIX_PROBLEM."""
        # Mix with massive low-end mud (+5.5 dB sub, +5.0 dB low)
        muddy_features = {
            "integrated_lufs": -16.0,
            "lufs": -16.0,
            "true_peak_dbtp": -2.0,
            "crest_factor_db": 11.0,
            "tonal_balance": {"sub": 5.5, "low": 5.0, "low_mid": 0.0, "mid": 0.0, "high_mid": 0.0, "presence": 0.0, "brilliance": 0.0},
            "stereo_correlation": 0.90,
            "clipping_detected": False
        }
        readiness = self.engine.check_readiness(muddy_features, DeliveryTarget.STREAMING)
        self.assertFalse(readiness.is_ready, "Mix with excessive low-end buildup must NOT be ready for mastering")
        self.assertEqual(readiness.status, "MIX_PROBLEM", "Status must be MIX_PROBLEM")
        self.assertTrue(any("MIX_PROBLEM" in p or "low-end" in p.lower() for p in readiness.mix_problems))

    def test_c_excessive_loudness_dynamic_damage(self):
        """Test C: Excessive Loudness Target -> Protect Dynamics (Max GR <= 2.5 dB)."""
        # Limiter gain calculation with quiet mix (-22 LUFS) aiming for -14 LUFS
        limiter_action = MasterLimiterEngine.calculate_settings(
            current_lufs=-22.0,
            target_lufs=-14.0,
            current_tp=-2.0,
            tp_ceiling=-1.0
        )
        # Verify gain applied is capped to prevent gain reduction exceeding 2.5 dB
        expected_gr = max(0.0, -2.0 + limiter_action.delta - (-1.0))
        self.assertLessEqual(expected_gr, MasterLimiterEngine.MAX_SAFE_GAIN_REDUCTION + 0.01,
                             "Limiter gain reduction must not exceed 2.5 dB guardrail")

    def test_d_clipping_fails_qc(self):
        """Test D: Clipping Source Audio -> QC Fails."""
        clipped_features = {
            "true_peak_dbtp": 0.6,
            "clipping_detected": True,
            "dc_offset": 0.0001,
            "stereo_correlation": 0.92,
            "channel_imbalance_db": 0.2
        }
        qc_result = self.engine.run_quality_control(clipped_features, DeliveryTarget.STREAMING)
        self.assertEqual(qc_result["quality_gate"], QualityGate.FAIL.value, "Clipping must fail QC")
        self.assertTrue(any("clipping" in err.lower() for err in qc_result["qc_errors"]))

    def test_e_stereo_phase_mono_translation_failure(self):
        """Test E: Destructive Stereo Phase -> Translation Failure."""
        out_of_phase_features = {
            "stereo_correlation": -0.45,
            "stereo_width": 1.8,
            "low_end_mono_correlation": 0.2,
            "tonal_balance": {"mid": 0.0, "high_mid": 0.0, "presence": 0.0, "sub": 0.0}
        }
        trans_result = self.engine.test_translation(out_of_phase_features)
        self.assertFalse(trans_result["mono_translation_passed"], "Negative phase must fail mono translation")
        self.assertLess(trans_result["breakdown"]["mono"], 50.0, "Mono score must be severely penalized")

    def test_f_reference_difference_gap_map(self):
        """Test F: Reference Gap Difference Map & Conservative EQ Moves."""
        track_features = {"tonal_balance": {"sub": 2.0, "low": 0.0, "low_mid": 0.0, "mid": 0.0, "high_mid": 0.0, "presence": -2.5, "brilliance": 0.0}}
        ref_features = {"tonal_balance": {"sub": 0.0, "low": 0.0, "low_mid": 0.0, "mid": 0.0, "high_mid": 0.0, "presence": 0.0, "brilliance": 0.0}}

        diff_map = ReferenceGapAnalyzer.calculate_gap_map(track_features, ref_features)
        self.assertAlmostEqual(diff_map.deltas["sub"], 2.0)
        self.assertAlmostEqual(diff_map.deltas["presence"], -2.5)

        eq_actions = MasterEQEngine.plan_eq_actions(diff_map)
        self.assertLessEqual(len(eq_actions), 2, "Master EQ must be restricted to top 2 critical bands")
        for act in eq_actions:
            self.assertLessEqual(abs(act.delta), MasterEQEngine.MAX_EQ_DELTA, "EQ moves must not exceed +-1.0 dB")

    def test_g_bad_reference_protection(self):
        """Test G: Bad Commercial Reference Protection."""
        # Create temporary audio file with digital clipping
        ref_path = Path(self.temp_dir.name) / "bad_ref.wav"
        t = np.linspace(0, 1.0, 44100, endpoint=False)
        clipped_signal = np.clip(1.5 * np.sin(2 * np.pi * 220.0 * t), -1.0, 1.0)
        import soundfile as sf
        sf.write(str(ref_path), np.stack([clipped_signal, clipped_signal], axis=1), 44100)

        track_dummy = np.zeros((2, 44100), dtype=np.float32)
        ref_analysis = ReferenceGapAnalyzer.analyze_reference(
            current_features={"lufs_integrated": -16.0, "true_peak_db": -3.0, "crest_factor": 12.0},
            current_audio=track_dummy,
            reference_path=str(ref_path),
            sr=44100
        )
        self.assertFalse(ref_analysis["is_reference_healthy"], "Clipped reference must be marked unhealthy")
        self.assertTrue(len(ref_analysis["bad_reference_warnings"]) > 0)
        self.assertTrue(any("clipping" in w.lower() for w in ref_analysis["bad_reference_warnings"]))

    def test_h_rollback_on_regression(self):
        """Test H: State Snapshot & ACID Rollback."""
        chain = self.engine.chain_builder
        chain.build_master_chain(track_id="master")

        # Snapshot pre-state
        snap = self.engine.snapshot_manager.create_snapshot(chain.get_chain_status(), notes="Pre-test")
        snap_id = snap["snapshot_id"]

        # Modify parameters
        chain.active_chain["LIMITER"]["parameters"]["Gain"] = 6.0
        self.assertEqual(chain.active_chain["LIMITER"]["parameters"]["Gain"], 6.0)

        # Rollback
        rollback_res = self.engine.rollback(snap_id)
        self.assertEqual(rollback_res["status"], "SUCCESS")
        self.assertEqual(chain.active_chain["LIMITER"]["parameters"]["Gain"], 0.0,
                         "Rollback must restore original gain parameter")

    def test_i_versioning_and_hashing(self):
        """Test I: Versioned Export with SHA-256 Hashing."""
        export_mgr = MasterExportManager(base_dir=self.temp_dir.name)
        exp1 = export_mgr.export_master(delivery_target=DeliveryTarget.STREAMING)
        self.assertEqual(exp1["version"], "v001")
        self.assertTrue(Path(exp1["file_path"]).exists())
        self.assertTrue(len(exp1["sha256_hash"]) == 64, "Must compute valid SHA-256 hash")

        exp2 = export_mgr.export_master(delivery_target=DeliveryTarget.STREAMING)
        self.assertEqual(exp2["version"], "v002")
        self.assertTrue(Path(exp2["file_path"]).exists())

    def test_j_full_pipeline_master_project(self):
        """Test J: Full Autonomous Master Pipeline."""
        result = self.engine.master_project(
            delivery_target="STREAMING",
            mode="BALANCED",
            auto_apply=True
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("plan", result)
        self.assertIn("score", result)
        self.assertIn("qc", result)
        self.assertIn("translation", result)
        self.assertIn("report", result)
        self.assertGreaterEqual(result["score"]["overall"], 75.0)
        self.assertTrue(len(self.engine.history) > 0, "Master history entry must be logged")


if __name__ == "__main__":
    unittest.main()

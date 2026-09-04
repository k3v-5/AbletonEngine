"""
Comprehensive Unit & Acceptance Test Suite for Fase 5: Digital Ear / Mix Intelligence Engine.
Tests all 10 mandatory acceptance tests specified in requirement documentation.
"""
import unittest
import numpy as np
import soundfile as sf
import tempfile
import os
from pathlib import Path

from MCP_Server.engine.mix.models import (
    AudioFeatures, MixContext, MixIssue, Severity, HeadroomClassification, DynamicClassification,
    CorrectionPlan
)
from MCP_Server.engine.mix.loudness_analyzer import LoudnessAnalyzer
from MCP_Server.engine.mix.frequency_analyzer import FrequencyAnalyzer
from MCP_Server.engine.mix.stereo_analyzer import StereoAnalyzer
from MCP_Server.engine.mix.transient_analyzer import TransientAnalyzer
from MCP_Server.engine.mix.masking_detector import MaskingDetector
from MCP_Server.engine.mix.mix_linter import MixLinter
from MCP_Server.engine.mix.diagnostic_engine import DiagnosticEngine
from MCP_Server.engine.mix.correction_engine import CorrectionEngine
from MCP_Server.engine.mix.reference_engine import ReferenceEngine
from MCP_Server.engine.mix.render_manager import RenderCache, RenderManager
from MCP_Server.engine.mix.confidence import ConfidenceEvaluator
from MCP_Server.engine.mix import MixEngine


class TestMixEngine(unittest.TestCase):
    """Test suite covering the 10 Acceptance Criteria for Digital Ear."""

    def setUp(self):
        self.sr = 44100
        self.duration = 2.0
        self.t = np.linspace(0, self.duration, int(self.sr * self.duration), endpoint=False)
        self.engine = MixEngine()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_low_end_conflict_detection(self):
        """Acceptance Test 1: Kick + Sub deliberately conflicting detected with evidence."""
        # Kick: 55Hz decaying punch
        env_k = np.exp(-self.t * 8.0)
        kick = 0.8 * np.sin(2 * np.pi * 55.0 * self.t) * env_k
        
        # Sub: 55Hz sustained tone
        sub = 0.8 * np.sin(2 * np.pi * 55.0 * self.t)

        masking = MaskingDetector.detect_low_end_conflict(kick, sub, self.sr)
        
        self.assertGreaterEqual(masking.masking_score, 0.50, "Should detect high masking between 55Hz kick and 55Hz sub")
        self.assertAlmostEqual(masking.conflict_frequency_hz, 55.0, delta=10.0)
        self.assertTrue(len(masking.evidence) > 0, "Must provide physical DSP evidence")
        self.assertTrue(any("55" in ev or "overlap" in ev.lower() for ev in masking.evidence))
        self.assertTrue(len(masking.recommended_actions) > 0)
        self.assertIn(masking.severity, (Severity.HIGH, Severity.CRITICAL, Severity.MEDIUM))

    def test_02_stereo_sub_mono_compatibility(self):
        """Acceptance Test 2: Sub with out-of-phase stereo info detected as LOW_FREQUENCY_STEREO."""
        # Out-of-phase 45Hz sub (L and R in antiphase)
        left = 0.5 * np.sin(2 * np.pi * 45.0 * self.t)
        right = -0.5 * np.sin(2 * np.pi * 45.0 * self.t)
        stereo_sub = np.vstack([left, right])

        mono_check = self.engine.check_mono(stereo_sub)
        
        self.assertLess(mono_check["correlation"], 0.0, "Antiphase stereo sub must yield negative correlation")
        self.assertGreater(mono_check["low_end_width"], 0.50, "Low-end width should be very wide")
        self.assertTrue(mono_check["mono_compatibility_warning"], "Mono compatibility warning must trigger")
        self.assertGreater(mono_check["mono_energy_loss_db"], 2.0, "Antiphase collapse causes severe energy loss")

    def test_03_master_clipping_true_peak(self):
        """Acceptance Test 3: Master clipping detected via True Peak without confusing with arrangement."""
        # Overshooting waveform with peaks > 0 dBFS
        clipping_sig = 1.25 * np.sin(2 * np.pi * 440.0 * self.t)
        stereo_clip = np.vstack([clipping_sig, clipping_sig])

        headroom = self.engine.check_headroom(stereo_clip)
        
        self.assertTrue(headroom["is_clipping"], "Signals > 0 dBFS must be classified as clipping")
        self.assertEqual(headroom["headroom_class"], HeadroomClassification.MASTER_CLIPPING.value)
        self.assertGreater(headroom["true_peak_db"], 0.0)

        # Ensure MixLinter catches it as CRITICAL
        context = MixContext()
        feats = self.engine.analyze(stereo_clip, context)
        lint = self.engine.lint(feats, context)
        self.assertFalse(lint["valid"])
        error_ids = [e["issue_id"] for e in lint["errors"]]
        self.assertIn("MIX-001-CLIPPING", error_ids)

    def test_04_correction_cycle_commit(self):
        """Acceptance Test 4: Correction that reduces masking and preserves bass weight is ACCEPTED (COMMITTED)."""
        plan = CorrectionPlan(
            plan_id="plan_test_commit",
            mode="AUTONOMOUS",
            target_issue="MIX-004-LOW-END-MASKING",
            actions=[],
            max_risk=0.15,
            estimated_improvement=0.35
        )
        dummy_audio = 0.2 * np.sin(2 * np.pi * 100.0 * self.t)
        feats = self.engine.analyze(dummy_audio)

        evaluation = self.engine.evaluate_correction(
            plan=plan,
            before_features=feats,
            after_features=feats,
            before_masking=0.82,
            after_masking=0.48,          # Masking greatly improved
            before_bass_weight=-12.0,
            after_bass_weight=-12.3      # Only 0.3 dB drop (well within 3dB limit)
        )
        self.assertTrue(evaluation.accepted, "Correction should be accepted when masking improves without regression")
        self.assertGreater(evaluation.score_delta, 0.0)
        self.assertEqual(len(evaluation.metrics_regressed), 0)

    def test_05_regression_rollback(self):
        """Acceptance Test 5: Correction that reduces masking but destroys bass weight is REJECTED (ROLLBACK)."""
        plan = CorrectionPlan(
            plan_id="plan_test_rollback",
            mode="AUTONOMOUS",
            target_issue="MIX-004-LOW-END-MASKING",
            actions=[],
            max_risk=0.15,
            estimated_improvement=0.35
        )
        dummy_audio = 0.2 * np.sin(2 * np.pi * 100.0 * self.t)
        feats = self.engine.analyze(dummy_audio)

        evaluation = self.engine.evaluate_correction(
            plan=plan,
            before_features=feats,
            after_features=feats,
            before_masking=0.82,
            after_masking=0.40,          # Masking improved...
            before_bass_weight=-12.0,
            after_bass_weight=-17.0      # ...but bass weight suffered 5.0 dB drop!
        )
        self.assertFalse(evaluation.accepted, "Must reject and rollback when bass weight is destroyed")
        self.assertLess(evaluation.score_delta, 0.0)
        self.assertTrue(any("bass weight" in reg.lower() for reg in evaluation.metrics_regressed))

    def test_06_confidence_gating(self):
        """Acceptance Test 6: Ambiguous signal yields LOW CONFIDENCE and prevents auto-correction."""
        # Pure white noise where no clear harmonic fundamental exists in low end
        np.random.seed(42)
        noise = np.random.uniform(-0.1, 0.1, len(self.t))
        
        kick_analysis = TransientAnalyzer.analyze_kick(noise, self.sr)
        self.assertLess(kick_analysis.confidence, 0.80, "Noisy signal should have low fundamental confidence")
        self.assertFalse(ConfidenceEvaluator.is_safe_for_auto_correction(kick_analysis.confidence))

        # Check that CorrectionEngine falls back to SAFE mode
        issue = MixIssue(
            issue_id="MIX-004-LOW-END-MASKING",
            category="LOW_END",
            severity=Severity.HIGH,
            severity_score=0.75,
            confidence=kick_analysis.confidence, # < 0.80
            target_roles=["BASS"],
            description="Ambiguous masking",
            evidence=[],
            probable_causes=[],
            recommended_actions=[]
        )
        plan = self.engine.correction_engine.create_correction_plan(issue, mode="AUTONOMOUS")
        self.assertEqual(plan.mode, "SAFE", "Low confidence must force mode to SAFE")

    def test_07_render_cache_idempotence(self):
        """Acceptance Test 7: Identical parameters reuse RenderCache."""
        cache = RenderCache()
        key = cache.make_cache_key("proj_1", "DROP_1", 64, 80, "trk_hash_a", "dev_hash_b", 128.0)
        
        # Initially empty
        self.assertIsNone(cache.get(key))
        
        # Cache results
        mock_data = {"lufs": -8.5, "status": "cached"}
        cache.set(key, mock_data)
        
        # Second call
        cached = cache.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["lufs"], -8.5)

    def test_08_section_awareness(self):
        """Acceptance Test 8: Contextual assessment differentiates between INTRO and DROP."""
        # Audio with low crest factor (squashed)
        squashed = 0.5 * np.sign(np.sin(2 * np.pi * 200.0 * self.t))
        
        ctx_drop = MixContext(section="DROP_1")
        feats_drop = self.engine.analyze(squashed, ctx_drop)
        lint_drop = self.engine.lint(feats_drop, ctx_drop)
        
        # In DROP, low crest factor is flagged as OVER_COMPRESSED
        warn_ids_drop = [w["issue_id"] for w in lint_drop["warnings"]]
        self.assertIn("MIX-005-OVER-COMPRESSED", warn_ids_drop)

        # In INTRO, ambient material without high crest factor is tolerated
        ctx_intro = MixContext(section="INTRO")
        feats_intro = self.engine.analyze(squashed, ctx_intro)
        lint_intro = self.engine.lint(feats_intro, ctx_intro)
        warn_ids_intro = [w["issue_id"] for w in lint_intro["warnings"]]
        self.assertNotIn("MIX-005-OVER-COMPRESSED", warn_ids_intro)

    def test_09_reference_track_differences(self):
        """Acceptance Test 9: Reference comparison extracts acoustic differences without blind copy."""
        ref_path = Path(self.temp_dir.name) / "reference.wav"
        # Reference: louder (-10 dB peak) and mono
        ref_sig = 0.35 * np.sin(2 * np.pi * 440.0 * self.t)
        sf.write(str(ref_path), np.vstack([ref_sig, ref_sig]).T, self.sr)

        # Current mix: quieter (-16 dB peak)
        cur_sig = 0.15 * np.sin(2 * np.pi * 440.0 * self.t)
        cur_feats = self.engine.analyze(np.vstack([cur_sig, cur_sig]))

        comp = self.engine.compare_reference(cur_feats, str(ref_path))
        
        self.assertIn("reference_lufs", comp)
        self.assertIn("deltas", comp)
        self.assertLess(comp["deltas"]["lufs_delta"], 0.0, "Current mix is quieter, so delta must be negative")
        self.assertTrue(len(comp["insights"]) > 0)

    def test_10_production_audit_multi_category(self):
        """Acceptance Test 10: production_audit() executes complete 12-category audit."""
        audit = self.engine.production_audit(section="DROP_1", mode="SAFE")
        
        self.assertIn("overall_status", audit)
        self.assertIn("categories", audit)
        self.assertIn("mix_health_score", audit)
        self.assertIn("top_priorities", audit)

        cats = audit["categories"]
        required_categories = [
            "ARRANGEMENT", "MIDI", "SOUND DESIGN", "LOW END", "MIDRANGE",
            "HIGH END", "DYNAMICS", "STEREO", "HEADROOM", "ROUTING", "GAIN STAGING", "MASTER"
        ]
        for cat in required_categories:
            self.assertIn(cat, cats, f"Category '{cat}' must be audited in production_audit")
            self.assertIn(cats[cat], ("PASS", "WARNING", "FAIL"))


if __name__ == "__main__":
    unittest.main()

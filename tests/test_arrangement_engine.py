"""
Unit & Integration Test Suite for Fase 3: Arrangement Engine.
Tests structure generation, multi-drop differentiation, energy curves,
role matrices, transitions, repetition linter, scoring, locking, and compiler.
"""
import unittest
import json
from engine import ProductionEngine
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.arrangement import (
    Song, Section, SectionType,
    EnergyDimensions, EnergyCurve, EnergyCurveGenerator,
    RoleMatrix, SectionRoleMap, RoleOrchestrator,
    TransitionEngine, TransitionType, PreDropGenerator,
    DropDifferentiationEngine, NarrativeArc,
    VariationPlanner, DensityController,
    SectionComparator, ArrangementLinter,
    ArrangementScorer, ArrangementLockManager,
    ArrangementCompiler, ArrangementGenerator,
    StructureLibrary, GenreTemplates
)

class TestArrangementEngine(unittest.TestCase):

    def setUp(self):
        self.mock_adapter = MockAbletonAdapter()
        self.engine = ProductionEngine(adapter=self.mock_adapter)
        self.generator = ArrangementGenerator(self.engine)

    def test_01_arrangement_generation_structure(self):
        """Test song structure generation and phrase duration math."""
        # 5 minutes at 128 BPM in 4/4:
        # 1 beat = 60/128 = 0.46875s; 1 bar = 1.875s; 300s / 1.875s = 160 bars
        song = self.generator.create_song_arrangement(
            name="Test Track",
            genre="melodic_techno",
            duration_seconds=300.0,
            tempo=128.0,
            key="F",
            scale="natural_minor",
            seed=2026
        )
        self.assertEqual(song.genre, "melodic_techno")
        self.assertEqual(song.tempo, 128.0)
        self.assertEqual(song.key, "F")
        self.assertEqual(song.total_bars, 160)
        self.assertAlmostEqual(song.duration_seconds, 300.0, delta=5.0)
        self.assertGreaterEqual(len(song.sections), 6)

    def test_02_multi_drop_differentiation(self):
        """Test that Drop 2 strictly escalates over Drop 1 in energy and variation."""
        song = self.generator.create_song_arrangement(
            genre="melodic_techno",
            duration_seconds=300.0,
            tempo=128.0
        )
        drops = [s for s in song.sections if s.section_type == SectionType.DROP]
        self.assertGreaterEqual(len(drops), 2, "Must have at least 2 drops")
        
        drop1 = drops[0]
        drop2 = drops[1]
        self.assertGreater(drop2.energy, drop1.energy, "Drop 2 energy must exceed Drop 1")
        self.assertNotEqual(drop1.variation_type, drop2.variation_type, "Drop 2 must have distinct variation profile")
        
        contrast = DropDifferentiationEngine.compute_drop_contrast(drop1, drop2)
        self.assertTrue(contrast["is_drop2_superior"])

    def test_03_energy_curves_interpolation(self):
        """Test smooth cosine interpolation and climax detection in EnergyCurve."""
        curve = EnergyCurve()
        curve.add_keypoint(1, EnergyDimensions(energy=0.2, density=0.3))
        curve.add_keypoint(33, EnergyDimensions(energy=0.9, density=0.85))
        
        # Midpoint at bar 17 should be around ~0.55
        mid_dims = curve.get_at_bar(17)
        self.assertGreater(mid_dims.energy, 0.2)
        self.assertLess(mid_dims.energy, 0.9)
        self.assertAlmostEqual(mid_dims.energy, 0.55, delta=0.05)

    def test_04_role_activation_matrix(self):
        """Test role matrix activation and density scaling across sections."""
        sec_intro = Section(name="Intro", type=SectionType.INTRO, bars=16, energy=0.25)
        sec_drop = Section(name="Drop", type=SectionType.DROP, bars=32, energy=0.95)
        
        matrix = RoleMatrix()
        matrix.initialize_for_sections([sec_intro, sec_drop])
        
        intro_roles = matrix.get_section_roles(0)
        drop_roles = matrix.get_section_roles(1)
        
        self.assertNotIn("sub_bass", intro_roles.active_roles(), "Sub bass should not be active in low-energy Intro")
        self.assertIn("kick", drop_roles.active_roles(), "Kick must be active in Drop")
        self.assertIn("lead", drop_roles.active_roles(), "Lead must be active in Drop")
        self.assertGreater(drop_roles.roles["kick"].density_factor, intro_roles.roles.get("pad", intro_roles.roles["kick"]).density_factor)

    def test_05_transition_engine_pre_drop(self):
        """Test pre-drop tension generator creates silence tension gaps."""
        sec_build = Section(name="Build", type=SectionType.BUILD, start_bar=17, bars=16, energy=0.75)
        sec_drop = Section(name="Drop", type=SectionType.DROP, start_bar=33, bars=32, energy=0.95)
        
        engine_trans = TransitionEngine()
        transitions = engine_trans.plan_transitions([sec_build, sec_drop])
        
        self.assertEqual(len(transitions), 1)
        t = transitions[0]
        self.assertEqual(t.transition_type, TransitionType.SILENCE_GAP)
        self.assertGreater(t.pre_drop_silence_beats, 0.0)
        self.assertIn("kick", t.affected_roles)

    def test_06_repetition_linter_duplicate_detection(self):
        """Test that copy-paste identical sections are caught as linter errors."""
        sec1 = Section(name="Drop 1", type=SectionType.DROP, bars=32, energy=0.90)
        sec1.variation_type = "same"
        sec2 = Section(name="Drop 2", type=SectionType.DROP, bars=32, energy=0.90)
        sec2.variation_type = "same"
        
        linter = ArrangementLinter()
        report = linter.lint([sec1, sec2])
        
        self.assertFalse(report["valid"], "Linter should invalidate identical sections")
        self.assertTrue(any(iss["rule_id"] == "ARR-001-COPY-PASTE" for iss in report["issues"]))

    def test_07_arrangement_scoring(self):
        """Test arrangement quality scoring metrics (contrast, pacing, overall)."""
        song = self.generator.create_song_arrangement(genre="melodic_techno")
        score = ArrangementScorer.score_arrangement(song.sections)
        
        self.assertGreater(score["overall_score"], 60.0)
        self.assertGreater(score["contrast_score"], 0.0)
        self.assertGreater(score["dynamic_range"], 0.5)

    def test_08_section_and_role_locking(self):
        """Test lock manager locks sections and roles."""
        lock_mgr = ArrangementLockManager()
        self.assertFalse(lock_mgr.is_section_locked(3))
        self.assertFalse(lock_mgr.is_role_locked("kick"))
        
        lock_mgr.lock_section(3)
        lock_mgr.lock_role("kick")
        
        self.assertTrue(lock_mgr.is_section_locked(3))
        self.assertTrue(lock_mgr.is_role_locked("kick"))
        self.assertTrue(lock_mgr.is_role_locked("KICK"))  # case-insensitive
        
        lock_mgr.unlock_section(3)
        self.assertFalse(lock_mgr.is_section_locked(3))

    def test_09_arrangement_preview_dry_run_invariant(self):
        """Test that preview mode generates full notes and does NOT mutate transactions or Ableton."""
        preview = self.generator.preview(
            name="Preview Track",
            genre="melodic_techno",
            duration_seconds=300.0,
            tempo=128.0
        )
        self.assertTrue(preview["dry_run"])
        self.assertEqual(preview["status"], "preview_success")
        self.assertGreater(preview["total_notes"], 0)
        self.assertEqual(preview["total_bars"], 160)
        # Transactions must not have been created or committed in dry run
        self.assertEqual(len(self.engine.transactions.active_transactions), 0, "Preview mode must not open transactions")
        self.assertEqual(len(self.engine.transactions.transaction_history_list), 0, "Preview mode must not commit history")

    def test_10_build_song_end_to_end_mock(self):
        """Test build mode compiles all sections and commits atomically via transaction."""
        build_res = self.generator.build(
            name="Live Song Build",
            genre="melodic_techno",
            duration_seconds=300.0,
            tempo=128.0,
            compile_to_arrangement=True
        )
        self.assertEqual(build_res["status"], "compiled_success")
        self.assertFalse(build_res["dry_run"])
        self.assertGreater(build_res["total_notes"], 0)
        self.assertIn("transaction", build_res)
        self.assertEqual(build_res["transaction"]["status"].upper(), "COMMITTED")

if __name__ == "__main__":
    unittest.main()

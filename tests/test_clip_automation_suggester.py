"""
Tests for ClipAutomationSuggester and proactive clip automation suggestions.
"""

import unittest
from unittest.mock import MagicMock
from engine.arrangement.automation.clip_suggester import ClipAutomationSuggester, ClipAutomationRecipe


class TestClipAutomationSuggester(unittest.TestCase):

    def test_recipe_catalog_completeness(self):
        """Verify all core recipes exist and are properly registered."""
        expected_recipes = [
            "timbre_swell", "filter_riser", "filter_breathing",
            "pre_drop_vacuum", "reverb_washout", "volume_crescendo", "sub_turnaround"
        ]
        for r_id in expected_recipes:
            recipe = ClipAutomationSuggester.get_recipe(r_id)
            self.assertIsNotNone(recipe, f"Recipe '{r_id}' should be found in catalog")
            self.assertEqual(recipe.recipe_id, r_id)
            self.assertTrue(len(recipe.parameter_candidates) > 0)

    def test_suggestions_for_pad_track(self):
        """Pad tracks should prioritize timbre swell, filter breathing, and filter riser."""
        pad_track_info = {
            "name": "06 - Analog Lab (Dark Pad)",
            "devices": [{"name": "Analog Lab V"}]
        }
        suggestions = ClipAutomationSuggester.suggest_for_track(pad_track_info, clip_length=16.0)
        self.assertGreaterEqual(len(suggestions), 3)
        recipe_ids = [s["recipe_id"] for s in suggestions]
        self.assertIn("timbre_swell", recipe_ids)
        self.assertIn("filter_breathing", recipe_ids)

    def test_suggestions_for_bass_track(self):
        """Bass tracks should prioritize pre-drop vacuum cut and sub turnaround."""
        bass_track_info = {
            "name": "05 - 808 Sub Bass (F Minor)",
            "devices": [{"name": "Vital"}]
        }
        suggestions = ClipAutomationSuggester.suggest_for_track(bass_track_info, clip_length=16.0)
        recipe_ids = [s["recipe_id"] for s in suggestions]
        self.assertIn("pre_drop_vacuum", recipe_ids)
        self.assertIn("sub_turnaround", recipe_ids)

    def test_suggestions_for_lead_track(self):
        """Lead tracks should prioritize filter riser, reverb washout, and volume crescendo."""
        lead_track_info = {
            "name": "04 - Vital (Metallic Screech)",
            "devices": [{"name": "Vital"}]
        }
        suggestions = ClipAutomationSuggester.suggest_for_track(lead_track_info, clip_length=16.0)
        recipe_ids = [s["recipe_id"] for s in suggestions]
        self.assertIn("filter_riser", recipe_ids)
        self.assertIn("reverb_washout", recipe_ids)

    def test_generate_points_curves(self):
        """Test mathematical point generation for different curve types."""
        # 1. Exponential riser
        exp_pts = ClipAutomationSuggester.generate_points("timbre_swell", clip_length=16.0, num_steps=16)
        self.assertEqual(len(exp_pts), 16)
        self.assertAlmostEqual(exp_pts[0]["value"], 0.15, places=2)
        self.assertAlmostEqual(exp_pts[-1]["value"], 0.85, places=2)
        # Verify it stays flatter earlier and rises faster later (exponential)
        mid_val = exp_pts[8]["value"]
        self.assertLess(mid_val, (0.15 + 0.85) / 2.0)

        # 2. Breathing LFO
        breath_pts = ClipAutomationSuggester.generate_points("filter_breathing", clip_length=16.0, num_steps=32)
        self.assertEqual(len(breath_pts), 32)
        min_seen = min(p["value"] for p in breath_pts)
        max_seen = max(p["value"] for p in breath_pts)
        self.assertGreaterEqual(min_seen, 0.44)
        self.assertLessEqual(max_seen, 0.66)

        # 3. Pre-Drop Vacuum Cut
        vac_pts = ClipAutomationSuggester.generate_points("pre_drop_vacuum", clip_length=16.0, num_steps=32)
        # Last points should drop to 0.0
        self.assertEqual(vac_pts[-1]["value"], 0.0)
        # Early points should hold normal value
        self.assertAlmostEqual(vac_pts[0]["value"], 0.85, places=2)

        # 4. Washout
        wash_pts = ClipAutomationSuggester.generate_points("reverb_washout", clip_length=16.0, num_steps=16)
        self.assertEqual(wash_pts[-1]["value"], 0.0) # snaps to 0.0 at drop
        self.assertGreater(wash_pts[-2]["value"], 0.50) # near max before drop

    def test_apply_recipe_to_clip_with_mock_conn(self):
        """Verify apply_recipe_to_clip injects the envelope and duplicates to arrangement."""
        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = lambda cmd, params: {
            "get_track_info": {"result": {"name": "Pad Track", "devices": [{"name": "Analog Lab V"}]}},
            "get_device_parameters": {"result": {"parameters": [{"index": 1, "name": "P1 Timbre"}]}},
            "get_clip_notes": {"result": {"notes": []}},
            "create_arrangement_automation_envelope": {"status": "success", "injected": 32},
            "duplicate_session_clip_to_arrangement": {"status": "success", "clip_name": "Pad Clip"}
        }.get(cmd, {"status": "success"})

        res = ClipAutomationSuggester.apply_recipe_to_clip(
            conn=mock_conn,
            track_index=10,
            clip_index=0,
            recipe_id="timbre_swell",
            destination_time=32.0
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["recipe_applied"], "timbre_swell")
        self.assertTrue(res["tangible_vector_active"])
        self.assertTrue(res["editable_with_A_key"])
        self.assertEqual(res["track_index"], 10)
        self.assertGreaterEqual(res["points_count"], 16)

        # Verify command invocations
        called_cmds = [call.args[0] for call in mock_conn.send_command.call_args_list]
        self.assertIn("create_arrangement_automation_envelope", called_cmds)
        self.assertIn("duplicate_session_clip_to_arrangement", called_cmds)


if __name__ == "__main__":
    unittest.main()

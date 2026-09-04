# tests/test_instrument_engine.py
import unittest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.instruments import (
    InstrumentEngine, DrumMap, InstrumentRole,
    DrumRackInspector, DrumRackBuilder, DrumRackVerifier,
    SampleLibraryResolver
)
from engine.music.rhythm.templates import GM_DRUM_MAP
from engine.music.rhythm.generator import generate_drums

class TestInstrumentEngine(unittest.TestCase):
    def setUp(self):
        self.mock_adapter = MockAbletonAdapter()
        # Initialize an empty drum track with an empty Drum Rack
        self.drum_track_idx = 0
        self.mock_adapter.tracks[self.drum_track_idx]["devices"] = []
        self.mock_adapter.load_instrument_or_effect(self.drum_track_idx, "query:Drums#Drum%20Rack")
        self.engine = InstrumentEngine(adapter=self.mock_adapter)

    def test_test1_empty_rack_detection(self):
        """Test 1: Empty Drum Rack detection reports status EMPTY."""
        report = self.engine.inspect_drum_rack(self.drum_track_idx)
        self.assertTrue(report["rack_exists"])
        self.assertEqual(report["status"], "EMPTY")
        self.assertEqual(report["populated"], 0)
        self.assertEqual(report["empty"], 16)
        self.assertIn("KICK", report["missing_roles"])
        self.assertIn("SNARE", report["missing_roles"])

    def test_test2_populate_drum_rack(self):
        """Test 2: drum_rack_populate() fills the pads with resolved samples."""
        res = self.engine.populate_drum_rack(
            track_index=self.drum_track_idx,
            style="melodic_techno",
            preview=False,
            seed=2026
        )
        self.assertEqual(res["status"], "SUCCESS")
        
        # Verify inspection after population
        post_report = self.engine.inspect_drum_rack(self.drum_track_idx)
        self.assertGreaterEqual(post_report["populated"], 5)
        self.assertEqual(post_report["status"], "POPULATED")

    def test_test3_idempotency_no_duplicate_rack(self):
        """Test 3: Calling populate_drum_rack() twice does not create duplicate racks or duplicate pads."""
        # First call
        self.engine.populate_drum_rack(track_index=self.drum_track_idx, style="melodic_techno", seed=2026)
        devices_before = len(self.mock_adapter.tracks[self.drum_track_idx]["devices"])
        pads_before = len(self.mock_adapter.tracks[self.drum_track_idx]["devices"][0]["drum_pads"])

        # Second call
        res2 = self.engine.populate_drum_rack(track_index=self.drum_track_idx, style="melodic_techno", seed=2026)
        devices_after = len(self.mock_adapter.tracks[self.drum_track_idx]["devices"])
        pads_after = len(self.mock_adapter.tracks[self.drum_track_idx]["devices"][0]["drum_pads"])

        self.assertEqual(devices_before, devices_after, "Idempotency violated: Drum Rack device was duplicated!")
        self.assertEqual(pads_before, pads_after, "Idempotency violated: Pads were duplicated!")

    def test_test4_verify_detects_missing_sample_or_pad(self):
        """Test 4: drum_rack_verify() detects problems when a core pad is unassigned or empty."""
        # Initially empty rack
        ver_empty = self.engine.verify_drum_rack(self.drum_track_idx)
        self.assertEqual(ver_empty["status"], "issues_found")
        self.assertGreater(ver_empty["missing"], 0)

        # Populate
        self.engine.populate_drum_rack(track_index=self.drum_track_idx, style="melodic_techno", seed=2026)
        ver_populated = self.engine.verify_drum_rack(self.drum_track_idx)
        self.assertEqual(ver_populated["status"], "verified")
        self.assertEqual(ver_populated["missing"], 0)

        # Tamper: remove devices from Pad 36 (Kick)
        dev = self.mock_adapter.tracks[self.drum_track_idx]["devices"][0]
        for p in dev["drum_pads"]:
            if p["note"] == 36:
                p["devices"] = [] # Empty chain device
                break

        ver_tampered = self.engine.verify_drum_rack(self.drum_track_idx)
        self.assertEqual(ver_tampered["status"], "issues_found")
        issues = [iss for iss in ver_tampered["issues"] if iss.get("note") == 36]
        self.assertTrue(len(issues) > 0, "Verifier failed to detect empty pad device!")

    def test_test5_preview_mode_modifies_nothing(self):
        """Test 5: preview=True generates full execution plan without touching Ableton state."""
        pads_before = len(self.mock_adapter.tracks[self.drum_track_idx]["devices"][0]["drum_pads"])
        
        preview_res = self.engine.populate_drum_rack(
            track_index=self.drum_track_idx,
            style="melodic_techno",
            preview=True,
            seed=2026
        )
        self.assertEqual(preview_res["status"], "PREVIEW")
        self.assertIn("plan", preview_res)
        self.assertGreater(len(preview_res["plan"]["assignments"]), 0)

        pads_after = len(self.mock_adapter.tracks[self.drum_track_idx]["devices"][0]["drum_pads"])
        self.assertEqual(pads_before, pads_after, "Preview mode modified Ableton state!")

    def test_test6_deterministic_seed_reproducibility(self):
        """Test 6: Same seed + same library produces identical sound assignments."""
        builder = DrumRackBuilder(self.mock_adapter)
        plan1 = builder.plan_population(track_index=self.drum_track_idx, style="melodic_techno", seed=9999, preview=True)
        plan2 = builder.plan_population(track_index=self.drum_track_idx, style="melodic_techno", seed=9999, preview=True)

        samples1 = [(a.pad, a.sample) for a in plan1.assignments]
        samples2 = [(a.pad, a.sample) for a in plan2.assignments]
        self.assertEqual(samples1, samples2, "Sound assignment is not deterministic across identical seeds!")

    def test_test7_music_engine_drum_map_equals_ableton_drum_map(self):
        """Test 7: Invariant check: Music Engine DrumMap == Ableton Drum Rack DrumMap."""
        # Check canonical Kick
        self.assertEqual(DrumMap.KICK, 36)
        self.assertEqual(GM_DRUM_MAP["kick"], DrumMap.KICK)

        # Check Snare
        self.assertEqual(DrumMap.SNARE, 38)
        self.assertEqual(GM_DRUM_MAP["snare"], DrumMap.SNARE)

        # Check Clap
        self.assertEqual(DrumMap.CLAP, 39)
        self.assertEqual(GM_DRUM_MAP["clap"], DrumMap.CLAP)

        # Check Closed Hat
        self.assertEqual(DrumMap.CLOSED_HAT, 40)
        self.assertEqual(GM_DRUM_MAP["hat_closed"], DrumMap.CLOSED_HAT)

        # Check Open Hat
        self.assertEqual(DrumMap.OPEN_HAT, 41)
        self.assertEqual(GM_DRUM_MAP["hat_open"], DrumMap.OPEN_HAT)

        # Check Percussion
        self.assertEqual(DrumMap.PERC_1, 42)
        self.assertEqual(GM_DRUM_MAP["perc_1"], DrumMap.PERC_1)

        # Check that generate_drums emits pitches consistent with DrumMap
        drums_notes = generate_drums(genre="melodic_techno", bars=2, seed=123)
        generated_pitches = {n.pitch for n in drums_notes}
        self.assertIn(DrumMap.KICK, generated_pitches)
        self.assertIn(DrumMap.CLOSED_HAT, generated_pitches)

if __name__ == "__main__":
    unittest.main()

# tests/test_sound_engine.py
import unittest
from engine.sound.profiles.models import SoundProfile
from engine.sound.profiles.profiles import SOUND_PROFILES, get_sound_profile
from engine.sound.parameters.curves import ParameterCurve
from engine.sound.parameters.mapper import ParameterMapper
from engine.sound.chains.templates import CHAIN_TEMPLATES, get_chain_template
from engine.sound.chains.builder import ChainBuilder
from engine.sound.chains.models import DEVICE_UTILITY
from engine.sound.capabilities.registry import CapabilityRegistry
from engine.sound.capabilities.discovery import CapabilityDiscovery
from engine.sound.presets.scoring import PresetScoringEngine
from engine.sound.presets.resolver import PresetResolver
from engine.sound.drum_rack.engine import DrumRackEngine
from engine.sound.drum_rack.verifier import DrumRackVerifier
from engine.sound.macros.system import MacroSystem
from engine.sound.context import AdaptiveAdvisor, MixContext
from engine.sound.linter import SoundLinter
from engine.sound.snapshots.snapshots import SoundSnapshotManager
from engine.sound.engine import SoundEngine
from engine.adapters.mock_adapter import MockAbletonAdapter

class TestSoundDesignEngine(unittest.TestCase):
    """Test Suite for Fase 4 — Sound Design & Production Engine."""

    def setUp(self):
        self.mock_adapter = MockAbletonAdapter()
        self.sound_engine = SoundEngine()
        self.sound_engine.set_adapter(self.mock_adapter)

    def test_sound_profile_normalization(self):
        """1. Verify all universal semantic parameters are normalized in [0.0, 1.0]."""
        self.assertGreater(len(SOUND_PROFILES), 0)
        for profile in SOUND_PROFILES.values():
            self.assertGreaterEqual(profile.brightness, 0.0)
            self.assertLessEqual(profile.brightness, 1.0)
            self.assertGreaterEqual(profile.warmth, 0.0)
            self.assertLessEqual(profile.warmth, 1.0)
            self.assertGreaterEqual(profile.weight, 0.0)
            self.assertLessEqual(profile.weight, 1.0)
            self.assertGreaterEqual(profile.punch, 0.0)
            self.assertLessEqual(profile.punch, 1.0)
            self.assertGreaterEqual(profile.space, 0.0)
            self.assertLessEqual(profile.space, 1.0)
            self.assertGreaterEqual(profile.width, 0.0)
            self.assertLessEqual(profile.width, 1.0)

    def test_parameter_translation_curves(self):
        """2. Semantic values correctly mapped across non-linear transfer curves."""
        # Check boundary values
        self.assertAlmostEqual(ParameterCurve.linear(0.0, 20.0, 20000.0), 20.0)
        self.assertAlmostEqual(ParameterCurve.linear(1.0, 20.0, 20000.0), 20000.0)
        self.assertAlmostEqual(ParameterCurve.exponential(0.0, 20.0, 20000.0), 20.0)
        self.assertAlmostEqual(ParameterCurve.exponential(1.0, 20.0, 20000.0), 20000.0)
        
        # Logarithmic curve at mid-point should be geometric mean
        mid_val = ParameterCurve.logarithmic(0.5, 20.0, 20000.0)
        self.assertAlmostEqual(mid_val, (20.0 * 20000.0) ** 0.5, delta=1.0)

        # Mapping test
        mappings = ParameterMapper.map_semantic_to_devices("brightness", 0.7)
        self.assertTrue(any(m["parameter"] in ["Filter Frequency", "Cutoff"] for m in mappings))
        for m in mappings:
            self.assertGreater(m["value"], 0.0)

    def test_native_first_priority(self):
        """3. Capability discovery prioritizes Native > M4L > VST3 > Fallback."""
        caps = CapabilityDiscovery.discover_capabilities()
        self.assertTrue(caps.is_live_suite)
        self.assertIn("Operator", caps.native_instruments)
        self.assertIn("Wavetable", caps.native_instruments)
        
        # Chain templates should pick native synths first
        chain = get_chain_template("BASS")
        self.assertIn(chain.devices[0].preferred_name, ["Wavetable", "Operator", "Drift", "Analog", "Simpler"])

    def test_role_chain_templates(self):
        """4. Validates standard templates for SUB, BASS, LEAD, PAD, DRUM_BUS."""
        for role in ["SUB_BASS", "BASS", "LEAD", "PAD", "DRUM_BUS"]:
            chain = get_chain_template(role)
            self.assertEqual(chain.role, role)
            self.assertGreater(len(chain.devices), 0)
            
            # SUB_BASS must contain utility with mono
            if role == "SUB_BASS":
                dev_ids = [d.identifier for d in chain.devices]
                self.assertIn(DEVICE_UTILITY, dev_ids)

    def test_preset_scoring(self):
        """5. Multi-factor scoring resolves best preset with high confidence."""
        res = PresetResolver.resolve_preset(
            role="BASS",
            character="dark_club",
            genre="melodic_techno",
            brightness=0.3
        )
        self.assertIn("instrument", res)
        self.assertIn("preset", res)
        self.assertGreaterEqual(res["confidence"], 0.7)

    def test_drum_rack_batch_build(self):
        """6. DrumRackEngine constructs full 8-16 pad kit specification."""
        engine = DrumRackEngine()
        res = engine.build_drum_rack(track_index=2, style="melodic_techno", preview=True)
        self.assertEqual(res["status"], "preview")
        spec = res["spec"]
        self.assertGreaterEqual(len(spec["pads"]), 8)
        self.assertTrue("36" in spec["pads"] or 36 in spec["pads"])  # Kick
        self.assertTrue("38" in spec["pads"] or 38 in spec["pads"])  # Snare
        self.assertTrue("40" in spec["pads"] or 40 in spec["pads"])  # Closed Hat

    def test_drum_rack_strict_verification(self):
        """7. Verifier enforces 'No Fake Success': flags empty pads as partial_failure."""
        # Case A: Track has rack with 0 pads
        class MockRackAdapter:
            def get_drum_rack_pads(self, track_index, device_index=0):
                return {"drum_rack_name": "Empty Rack", "pads": []}
                
        ver = DrumRackVerifier.verify_drum_rack(MockRackAdapter(), track_index=2)
        self.assertFalse(ver["verified"])
        self.assertEqual(ver["status"], "partial_failure")
        self.assertEqual(ver["active_pad_count"], 0)

        # Case B: Track has rack with empty device pad
        class MockEmptyPadAdapter:
            def get_drum_rack_pads(self, track_index, device_index=0):
                return {"drum_rack_name": "Rack", "pads": [{"note": 36, "devices": []}]}
                
        ver2 = DrumRackVerifier.verify_drum_rack(MockEmptyPadAdapter(), track_index=2)
        self.assertFalse(ver2["verified"])
        self.assertEqual(ver2["status"], "partial_failure")

    def test_macro_multi_parameter_modulation(self):
        """8. Setting macro modifies bound physical parameters."""
        macros = MacroSystem(self.mock_adapter)
        res = macros.set_macro(track_index=2, macro_name="brightness", value=0.85)
        self.assertEqual(res["status"], "macro_updated")
        self.assertEqual(res["macro"], "BRIGHTNESS")
        self.assertEqual(res["value"], 0.85)
        self.assertGreater(len(res["bindings"]), 0)
        self.assertEqual(macros.get_macro(2, "brightness"), 0.85)

    def test_mix_context_adaptive_advisor(self):
        """9. Mix context advisor flags stereo sub-bass clash and Kick-Bass collision."""
        advisor = AdaptiveAdvisor()
        
        # Centered sub is valid
        res_ok = advisor.check_low_end_phase(role="SUB_BASS", panning=0.0)
        self.assertTrue(res_ok["valid"])
        
        # Panned sub triggers warning and recommends mono
        res_panned = advisor.check_low_end_phase(role="SUB_BASS", panning=0.5)
        self.assertFalse(res_panned["valid"])
        self.assertIn("must be centered", res_panned["recommendation"])

        # Clashing kick and bass
        ctx = MixContext(kick_frequency_hz=55.0, bass_frequency_hz=50.0)
        clashes = advisor.evaluate_clashes(ctx)
        self.assertTrue(any(c["issue"] == "LOW_END_MASKING" for c in clashes))

    def test_sound_linter(self):
        """10. Linter detects empty tracks, panned sub, and clipping volume."""
        # Clean track
        clean_track = {
            "index": 2, "name": "Bass", "is_midi_track": True,
            "volume": 0.85, "panning": 0.0, "devices": [{"name": "Wavetable"}]
        }
        res_clean = SoundLinter.lint_track(clean_track, role="BASS")
        self.assertTrue(res_clean["valid"])
        self.assertEqual(res_clean["sound_health_score"], 100.0)

        # Defective track
        bad_track = {
            "index": 3, "name": "Sub", "is_midi_track": True,
            "volume": 1.25,  # clipping
            "panning": 0.4,  # stereo sub
            "devices": []    # empty
        }
        res_bad = SoundLinter.lint_track(bad_track, role="SUB_BASS")
        self.assertFalse(res_bad["valid"])
        self.assertLess(res_bad["sound_health_score"], 60.0)
        rule_ids = [i["rule_id"] for i in res_bad["issues"]]
        self.assertIn("SND-001-EMPTY-TRACK", rule_ids)
        self.assertIn("SND-003-STEREO-SUB", rule_ids)
        self.assertIn("SND-004-GAIN-STAGING", rule_ids)

    def test_sound_preview_dry_run(self):
        """11. Preview dry-run generates sound plan without modifying session."""
        res = self.sound_engine.build_sound_role(
            track_index_or_id=4,
            role="LEAD",
            character="bright_cutting",
            preview=True
        )
        self.assertEqual(res["status"], "preview")
        self.assertEqual(res["role"], "LEAD")
        self.assertIn("selected_instrument", res)
        self.assertIn("selected_preset", res)
        self.assertIn("chain", res)
        self.assertIn("macros", res)

    def test_snapshot_and_rollback(self):
        """12. SoundSnapshotManager captures state and restores on rollback."""
        mgr = SoundSnapshotManager()
        snap = mgr.capture(track_index=2, adapter=self.mock_adapter)
        self.assertIsNotNone(snap.snapshot_id)
        self.assertEqual(snap.track_index, 2)
        
        # Verify rollback returns successful restoration
        rollback_res = mgr.rollback(snap.snapshot_id, adapter=self.mock_adapter)
        self.assertTrue(rollback_res)

if __name__ == "__main__":
    unittest.main()

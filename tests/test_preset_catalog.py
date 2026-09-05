# tests/test_preset_catalog.py
import unittest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.instruments import (
    InstrumentEngine, InstrumentPlanner, PresetCatalog, PresetEntry, PRESET_CATALOG
)

class TestPresetCatalog(unittest.TestCase):
    def setUp(self):
        self.mock_adapter = MockAbletonAdapter()
        self.engine = InstrumentEngine(adapter=self.mock_adapter)

    def test_catalog_not_empty(self):
        """Test that the curated catalog has verified entries."""
        self.assertGreaterEqual(len(PRESET_CATALOG), 10)

    def test_resolve_piano_by_role(self):
        """Resolving PIANO returns a verified concert grand preset."""
        preset = PresetCatalog.resolve_preset("PIANO")
        self.assertIsNotNone(preset)
        self.assertEqual(preset.role, "PIANO")
        self.assertIn("query:Sounds#Piano%20&%20Keys", preset.uri)

    def test_resolve_felt_piano_by_character(self):
        """Resolving PIANO with lofi / felt mood returns Childhood Home Piano."""
        preset = PresetCatalog.resolve_preset("PIANO", genre="lofi", mood="felt")
        self.assertIsNotNone(preset)
        self.assertEqual(preset.name, "Childhood Home Piano")
        self.assertEqual(preset.character, "intimate_felt")

    def test_resolve_808_sub_bass(self):
        """Resolving SUB_BASS with trap genre returns a punchy 808."""
        preset = PresetCatalog.resolve_preset("SUB_BASS", genre="trap")
        self.assertIsNotNone(preset)
        self.assertIn("808", preset.name)
        self.assertIn("Bass", preset.category)

    def test_resolve_drum_kit(self):
        """Resolving DRUM_KIT returns full native drum rack preset."""
        preset = PresetCatalog.resolve_preset("DRUM_KIT", genre="trap")
        self.assertIsNotNone(preset)
        self.assertEqual(preset.name, "808 Core Kit")
        self.assertEqual(preset.uri, "query:Drums#FileId_5422")

    def test_search_presets(self):
        """Search query matches preset name and tags."""
        results = PresetCatalog.search("analog")
        self.assertGreaterEqual(len(results), 2)
        names = [p.name for p in results]
        self.assertTrue(any("Analog" in n for n in names))

    def test_list_presets_filter(self):
        """Filtering presets by role returns only that role."""
        strings = PresetCatalog.list_presets(role="STRINGS")
        self.assertGreaterEqual(len(strings), 1)
        for s in strings:
            self.assertEqual(s.role, "STRINGS")

    def test_instrument_planner_integration(self):
        """InstrumentPlanner.resolve_instrument uses curated presets instead of blank init synth."""
        desc = InstrumentPlanner.resolve_instrument("PIANO", sound_profile="lofi")
        self.assertEqual(desc.device_name, "Childhood Home Piano")
        self.assertIn("query:Sounds#Piano%20&%20Keys", desc.uri)
        self.assertFalse(desc.is_fallback)

    def test_load_preset_on_mock_adapter(self):
        """InstrumentEngine.load_preset loads target URI onto the track."""
        res = self.engine.load_preset(track_index=0, preset_name_or_role="808 Core Kit")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["preset"]["name"], "808 Core Kit")
        self.assertTrue(res["load_result"]["loaded"])
        self.assertEqual(res["load_result"]["uri"], "query:Drums#FileId_5422")

if __name__ == "__main__":
    unittest.main()

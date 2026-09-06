# tests/test_vst_preset_search.py
"""
Test Suite for Universal VST Preset Indexer and Multi-Criteria Search Engine:
Verifies indexing across Arturia, FabFilter, Vital, Serum, Valhalla, and Native devices,
and validates multi-criteria fuzzy search, ranking, and category filtering.
"""

import pytest
from engine.instruments.presets.models import (
    PresetRecord,
    SearchQuery,
    SearchResult,
    PresetCategory,
)
from engine.instruments.presets.adapters import (
    ArturiaDbAdapter,
    FabFilterTreeAdapter,
    VitalPresetAdapter,
    SerumPresetAdapter,
    ValhallaPresetAdapter,
    NativePresetAdapter,
)
from engine.instruments.presets.universal_indexer import UniversalIndexer
from engine.instruments.presets.search import PresetSearchEngine


class TestPresetModels:
    def test_preset_record_roundtrip(self):
        record = PresetRecord(
            id="test_preset_1",
            name="Dark 808 Rumble",
            plugin_name="Vital",
            vendor="Vital Audio",
            category=PresetCategory.BASS.value,
            subcategory="Sub",
            tags=["bass", "808", "dark", "trap"],
            file_path="/path/to/preset.vital",
            format="vital",
            is_factory=False,
            author="Producer",
            metadata={"drive": 0.8}
        )
        d = record.to_dict()
        assert d["name"] == "Dark 808 Rumble"
        assert d["category"] == "BASS"
        assert "808" in d["tags"]

        reconstructed = PresetRecord.from_dict(d)
        assert reconstructed.id == record.id
        assert reconstructed.metadata["drive"] == 0.8


class TestAdapters:
    def test_valhalla_adapter(self):
        adapter = ValhallaPresetAdapter()
        assert adapter.is_available() is True
        presets = adapter.scan()
        assert len(presets) >= 8
        plugin_names = {p.plugin_name for p in presets}
        assert "ValhallaVintageVerb" in plugin_names
        assert "ValhallaDelay" in plugin_names

        # Check metadata
        vv = next(p for p in presets if p.plugin_name == "ValhallaVintageVerb")
        assert "parameters" in vv.metadata
        assert "Mix" in vv.metadata["parameters"]

    def test_native_adapter(self):
        adapter = NativePresetAdapter()
        assert adapter.is_available() is True
        presets = adapter.scan()
        assert len(presets) > 10
        names = {p.name for p in presets}
        assert any("Piano" in n for n in names)
        assert any("Drift" in n for n in names)
        assert any("EQ Eight" in n for n in names)

    def test_arturia_adapter_if_installed(self):
        adapter = ArturiaDbAdapter()
        if adapter.is_available():
            presets = adapter.scan()
            assert len(presets) > 1000
            # Confirm presence of user's key plugins
            inst_names = {p.plugin_name for p in presets}
            assert any("Pigments" in i or "Analog Lab" in i or "Efx" in i for i in inst_names)

    def test_fabfilter_adapter_if_installed(self):
        adapter = FabFilterTreeAdapter()
        if adapter.is_available():
            presets = adapter.scan()
            assert len(presets) > 500
            plugins = {p.plugin_name for p in presets}
            assert any("Pro-Q" in pl for pl in plugins)


class TestSearchEngine:
    @pytest.fixture
    def mock_indexer(self):
        class MockIndexer:
            def get_all_presets(self):
                return [
                    PresetRecord(
                        id="p1",
                        name="Heavy Sub 808",
                        plugin_name="Vital",
                        vendor="Vital Audio",
                        category=PresetCategory.BASS.value,
                        subcategory="Sub",
                        tags=["bass", "808", "sub", "trap"],
                    ),
                    PresetRecord(
                        id="p2",
                        name="Lush Vocal Plate",
                        plugin_name="ValhallaVintageVerb",
                        vendor="Valhalla DSP",
                        category=PresetCategory.REVERB.value,
                        subcategory="Plate",
                        tags=["reverb", "vocal", "lush", "plate"],
                    ),
                    PresetRecord(
                        id="p3",
                        name="Warm Tape Delay",
                        plugin_name="ValhallaDelay",
                        vendor="Valhalla DSP",
                        category=PresetCategory.DELAY.value,
                        subcategory="Tape",
                        tags=["delay", "tape", "warm", "analog"],
                    ),
                    PresetRecord(
                        id="p4",
                        name="Clean Low Cut",
                        plugin_name="FabFilter Pro-Q 4",
                        vendor="FabFilter",
                        category=PresetCategory.EQ.value,
                        subcategory="Filter",
                        tags=["eq", "clean", "surgical", "hpf"],
                    ),
                    PresetRecord(
                        id="p5",
                        name="Analog Rhodes Dream",
                        plugin_name="Analog Lab V",
                        vendor="Arturia",
                        category=PresetCategory.KEYS.value,
                        subcategory="Rhodes",
                        tags=["keys", "rhodes", "vintage", "warm"],
                    ),
                ]
        return MockIndexer()

    def test_keyword_search(self, mock_indexer):
        engine = PresetSearchEngine(indexer=mock_indexer)
        results = engine.search(SearchQuery(query_text="808 sub"))
        assert len(results) > 0
        assert results[0].preset.name == "Heavy Sub 808"
        assert results[0].relevance_score > 0.6

    def test_category_and_role_filter(self, mock_indexer):
        engine = PresetSearchEngine(indexer=mock_indexer)
        results = engine.search(SearchQuery(category_filter="REVERB"))
        assert len(results) == 1
        assert results[0].preset.name == "Lush Vocal Plate"

    def test_plugin_filter(self, mock_indexer):
        engine = PresetSearchEngine(indexer=mock_indexer)
        results = engine.search(SearchQuery(plugin_filter=["FabFilter Pro-Q 4"]))
        assert len(results) == 1
        assert results[0].preset.plugin_name == "FabFilter Pro-Q 4"

    def test_find_by_role_convenience(self, mock_indexer):
        engine = PresetSearchEngine(indexer=mock_indexer)
        results = engine.find_by_role(role="KEYS", character="rhodes warm")
        assert len(results) > 0
        assert results[0].preset.name == "Analog Rhodes Dream"

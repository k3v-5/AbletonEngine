# tests/test_library_crawler.py
import os
import tempfile
import pytest
from engine.instruments.library.crawler import LibraryCrawler

def test_crawler_save_and_load_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "test_index.json")
        crawler = LibraryCrawler(cache_path=cache_file)
        
        # Mock query fn
        def mock_query(path):
            if path == "plugins/VST3":
                return {
                    "path": path,
                    "items": [
                        {"name": "Vital", "uri": "query:Plugins#VST3:Vital", "is_folder": False, "is_loadable": True},
                        {"name": "Arturia", "uri": "query:Plugins#VST3:Arturia", "is_folder": True, "is_loadable": False}
                    ]
                }
            elif path == "plugins/VST3/Arturia":
                return {
                    "path": path,
                    "items": [
                        {"name": "Analog Lab V", "uri": "query:Plugins#VST3:Arturia:AnalogLab", "is_folder": False, "is_loadable": True}
                    ]
                }
            return {"items": []}

        # Crawl
        res = crawler.crawl_category("plugins/VST3", mock_query, max_depth=2, rate_limit_sec=0.0)
        assert res["crawled_count"] == 3
        assert os.path.exists(cache_file)

        # Reload new crawler from cache
        crawler2 = LibraryCrawler(cache_path=cache_file)
        assert crawler2._index["total_items"] == 3
        
        # Search
        results = crawler2.search("Vital")
        assert len(results) == 1
        assert results[0]["name"] == "Vital"
        assert results[0]["is_loadable"] is True

        results_analog = crawler2.search("analog")
        assert len(results_analog) == 1
        assert results_analog[0]["name"] == "Analog Lab V"

        summary = crawler2.get_summary()
        assert summary["total_indexed"] == 3
        assert "plugins_vst3" in summary["categories"]

# engine/instruments/library/crawler.py
import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("LibraryCrawler")

class LibraryCrawler:
    """
    Automated crawler and indexer for Ableton Live 12 library and VST3 plugins.
    Indexes presets, instruments, audio effects, and 3rd party plugins into a searchable cache.
    """

    DEFAULT_CACHE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "state",
        "browser_index.json"
    )

    def __init__(self, cache_path: Optional[str] = None):
        self.cache_path = cache_path or self.DEFAULT_CACHE_PATH
        self._index: Dict[str, Any] = {
            "version": "1.0",
            "last_updated": 0,
            "categories": {},
            "items_by_uri": {},
            "total_items": 0
        }
        self.load_cache()

    def load_cache(self) -> bool:
        """Loads cached index from disk if present"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
                logger.info(f"Loaded {self._index.get('total_items', 0)} browser items from cache")
                return True
            except Exception as e:
                logger.warning(f"Failed to load cache from {self.cache_path}: {e}")
        return False

    def save_cache(self) -> None:
        """Saves current index to disk atomically"""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        temp_path = self.cache_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, self.cache_path)
        logger.info(f"Saved {self._index.get('total_items', 0)} browser items to {self.cache_path}")

    def crawl_category(
        self,
        category_path: str,
        query_fn: Callable[[str], Dict[str, Any]],
        max_depth: int = 2,
        rate_limit_sec: float = 0.02
    ) -> Dict[str, Any]:
        """
        Crawls a browser category path recursively using the provided query function.
        query_fn is a callable taking a path string and returning dict with 'items' list.
        """
        visited = set()
        collected_items = []
        queue = [(category_path, 0)]

        while queue:
            current_path, depth = queue.pop(0)
            if current_path in visited or depth > max_depth:
                continue
            visited.add(current_path)

            try:
                res = query_fn(current_path)
            except Exception as e:
                logger.warning(f"Error querying path {current_path}: {e}")
                continue

            if not res or not isinstance(res, dict):
                continue

            items = res.get("items", [])
            for item in items:
                name = item.get("name", "")
                uri = item.get("uri", "")
                is_folder = item.get("is_folder", False)
                is_loadable = item.get("is_loadable", False)

                collected_items.append({
                    "name": name,
                    "uri": uri,
                    "path": f"{current_path}/{name}" if current_path else name,
                    "is_folder": is_folder,
                    "is_loadable": is_loadable,
                    "category": category_path.split("/")[0]
                })

                if uri:
                    self._index["items_by_uri"][uri] = collected_items[-1]

                if is_folder and depth < max_depth:
                    next_path = f"{current_path}/{name}"
                    queue.append((next_path, depth + 1))

            if rate_limit_sec > 0:
                time.sleep(rate_limit_sec)

        cat_key = category_path.replace("/", "_").lower()
        self._index["categories"][cat_key] = {
            "path": category_path,
            "crawled_at": time.time(),
            "item_count": len(collected_items),
            "items": collected_items
        }
        self._index["last_updated"] = time.time()
        self._index["total_items"] = len(self._index["items_by_uri"])
        self.save_cache()

        return {
            "category": category_path,
            "crawled_count": len(collected_items),
            "total_indexed": self._index["total_items"]
        }

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 25,
        loadable_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Searches indexed items by name or URI.
        """
        query_lower = query.lower()
        results = []

        for item in self._index.get("items_by_uri", {}).values():
            if loadable_only and not item.get("is_loadable", False):
                continue
            if category and item.get("category", "").lower() != category.lower():
                continue

            name = item.get("name", "").lower()
            uri = item.get("uri", "").lower()

            if query_lower in name or query_lower in uri:
                # Basic scoring: exact match > prefix match > substring match
                score = 1.0 if name == query_lower else (0.8 if name.startswith(query_lower) else 0.5)
                results.append((score, item))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:max_results]]

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistics of the crawler index"""
        categories_stat = {}
        for k, v in self._index.get("categories", {}).items():
            categories_stat[k] = {
                "path": v.get("path"),
                "item_count": v.get("item_count", 0),
                "crawled_at": v.get("crawled_at", 0)
            }
        return {
            "total_indexed": self._index.get("total_items", 0),
            "last_updated": self._index.get("last_updated", 0),
            "categories": categories_stat
        }

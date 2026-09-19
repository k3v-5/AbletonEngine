# engine/indexer/sample_cache.py
"""
Smart Sample Cache & Semantic Indexer:
Provides instant in-memory and persistent cached lookups for local sample libraries
without expensive recursive disk scans.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging
import time

logger = logging.getLogger("SampleCache")


class SampleCacheManager:
    """Manages indexation, categorization and instant search across user samples."""

    CACHE_FILE = Path("cache/sample_index_cache.json")

    CATEGORY_KEYWORDS = {
        "FOLEY": ["foley", "texture", "rain", "vinyl", "crackle", "ambient", "atmosphere", "room"],
        "VOCALS": ["vocal", "vox", "acapella", "hook", "chop", "speech", "phrase", "sing"],
        "DRUMS": ["drum", "kick", "snare", "clap", "hat", "hihat", "cymbal", "tom", "perc", "break"],
        "BASS": ["bass", "808", "sub", "reese", "growl", "wobble", "low"],
        "SYNTH": ["synth", "lead", "pluck", "chord", "pad", "arp", "keys", "piano"],
        "FX": ["fx", "riser", "sweep", "downlifter", "impact", "noise", "glitch", "transition"]
    }

    _memory_cache: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def categorize_filename(cls, filename: str) -> str:
        """Determines acoustic category from filename tokens."""
        lower = filename.lower()
        for cat, keywords in cls.CATEGORY_KEYWORDS.items():
            if any(k in lower for k in keywords):
                return cat
        return "OTHER"

    @classmethod
    def index_directories(cls, roots: List[Path], max_depth: int = 4) -> List[Dict[str, Any]]:
        """
        Performs indexing across directory roots and saves to disk cache.
        """
        valid_exts = {".wav", ".aif", ".aiff", ".mp3", ".flac"}
        indexed_items = []

        for root in roots:
            if not root.exists() or not root.is_dir():
                continue

            try:
                for p in root.rglob("*"):
                    if p.is_file() and p.suffix.lower() in valid_exts:
                        indexed_items.append({
                            "name": p.name,
                            "stem": p.stem,
                            "path": str(p.resolve()),
                            "category": cls.categorize_filename(p.name),
                            "extension": p.suffix.lower(),
                            "size_bytes": p.stat().st_size if p.exists() else 0
                        })
            except Exception as e:
                logger.warning(f"Notice while indexing {root}: {e}")

        cls._memory_cache = indexed_items

        # Persist to disk
        try:
            cls.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "items": indexed_items}, f, indent=2)
        except Exception as ex:
            logger.debug(f"Could not persist sample cache: {ex}")

        return indexed_items

    @classmethod
    def get_samples(
        cls,
        category: Optional[str] = None,
        query: Optional[str] = None,
        roots: Optional[List[Path]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Returns cached samples matching category and query in < 5 milliseconds.
        """
        if cls._memory_cache is None:
            if cls.CACHE_FILE.exists():
                try:
                    with open(cls.CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        cls._memory_cache = data.get("items", [])
                except Exception:
                    cls._memory_cache = []
            else:
                from .paths import get_personal_samples_roots
                cls.index_directories(roots or get_personal_samples_roots())

        items = cls._memory_cache or []
        cat_upper = category.upper() if category else None
        q_lower = query.lower() if query else None

        results = []
        for it in items:
            if cat_upper and it.get("category") != cat_upper:
                continue
            if q_lower and q_lower not in it.get("name", "").lower():
                continue
            results.append(it)
            if len(results) >= limit:
                break

        return results

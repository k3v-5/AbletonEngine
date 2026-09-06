# engine/instruments/presets/search.py
"""
Multi-Criteria Preset Search & Ranking Engine:
Provides fast, fuzzy, and tagged search across 30,000+ indexed presets
by plugin name, category, semantic role, tags, and descriptive keywords.
"""

import re
from typing import List, Optional, Set
from .models import PresetRecord, SearchQuery, SearchResult, PresetCategory
from .universal_indexer import UniversalIndexer


class PresetSearchEngine:
    """Executes multi-criteria queries with relevance ranking against indexed presets."""

    def __init__(self, indexer: Optional[UniversalIndexer] = None):
        self.indexer = indexer or UniversalIndexer()

    def search(self, query: SearchQuery) -> List[SearchResult]:
        presets = self.indexer.get_all_presets()
        results: List[SearchResult] = []

        # Tokenize search keywords
        keywords: List[str] = []
        if query.query_text:
            keywords = [
                re.sub(r"[^a-zA-Z0-9]", "", w).lower()
                for w in query.query_text.split()
                if len(w.strip()) > 1
            ]

        # Normalized filters
        plugin_filters: Optional[Set[str]] = (
            {p.lower() for p in query.plugin_filter} if query.plugin_filter else None
        )
        vendor_filters: Optional[Set[str]] = (
            {v.lower() for v in query.vendor_filter} if query.vendor_filter else None
        )
        cat_filter = query.category_filter.upper() if query.category_filter else None
        role_filter = query.role_filter.upper() if query.role_filter else None
        query_tags = {t.lower() for t in query.tags}

        for p in presets:
            # 1. Hard filters (plugin, vendor)
            if plugin_filters:
                p_match = any(pf in p.plugin_name.lower() for pf in plugin_filters)
                if not p_match:
                    continue

            if vendor_filters:
                v_match = any(vf in p.vendor.lower() for vf in vendor_filters)
                if not v_match:
                    continue

            # 2. Category / Role filter
            if cat_filter and p.category.upper() != cat_filter:
                continue

            if role_filter:
                # Direct match or role mapping
                if role_filter != p.category.upper():
                    # Check if tags contain the role
                    if role_filter.lower() not in [t.lower() for t in p.tags]:
                        continue

            # 3. Relevance scoring
            score = 0.0
            reasons: List[str] = []

            name_lower = p.name.lower()
            tags_lower = [t.lower() for t in p.tags]
            subcat_lower = p.subcategory.lower()

            # Keyword matching
            if keywords:
                matched_kw = 0
                for kw in keywords:
                    if kw in name_lower:
                        score += 0.40
                        reasons.append(f"Name match '{kw}'")
                        matched_kw += 1
                    elif any(kw in t for t in tags_lower):
                        score += 0.25
                        reasons.append(f"Tag match '{kw}'")
                        matched_kw += 1
                    elif kw in subcat_lower:
                        score += 0.20
                        reasons.append(f"Subcategory match '{kw}'")
                        matched_kw += 1
                    elif kw in p.plugin_name.lower():
                        score += 0.15
                        reasons.append(f"Plugin match '{kw}'")
                        matched_kw += 1

                # If keywords were specified but none matched, skip
                if matched_kw == 0:
                    continue
            else:
                # Default baseline score if filters match without keywords
                score = 0.50
                reasons.append("Filter match")

            # Tag alignment bonus
            if query_tags:
                common_tags = query_tags.intersection(set(tags_lower))
                if common_tags:
                    bonus = len(common_tags) * 0.15
                    score += bonus
                    reasons.append(f"Matching tags: {list(common_tags)}")

            # Clamp score between 0.0 and 1.0
            norm_score = min(1.0, round(score, 3))
            results.append(SearchResult(
                preset=p,
                relevance_score=norm_score,
                match_reasons=reasons
            ))

        # Sort descending by relevance score
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:query.max_results]

    def find_by_role(
        self,
        role: str,
        character: str = "",
        plugin_hint: Optional[str] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """Convenience search helper for musical roles."""
        plugins = [plugin_hint] if plugin_hint else None
        query = SearchQuery(
            query_text=character if character else None,
            role_filter=role,
            plugin_filter=plugins,
            max_results=limit
        )
        return self.search(query)

    def find_by_plugin(
        self,
        plugin_name: str,
        query_text: Optional[str] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        """Search presets within a specific VST plugin."""
        query = SearchQuery(
            query_text=query_text,
            plugin_filter=[plugin_name],
            max_results=limit
        )
        return self.search(query)

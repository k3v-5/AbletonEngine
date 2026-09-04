# engine/instruments/library/search.py
import random
from typing import Dict, Any, List, Optional
from .resolver import SampleLibraryResolver, SampleCandidate
from ..roles import InstrumentRole

# Global resolver instance
_resolver: Optional[SampleLibraryResolver] = None

def get_sample_resolver() -> SampleLibraryResolver:
    global _resolver
    if _resolver is None:
        _resolver = SampleLibraryResolver()
    return _resolver

def search_samples(
    role: str,
    style: str = "",
    character: str = "",
    max_results: int = 10,
    resolver: Optional[SampleLibraryResolver] = None
) -> Dict[str, Any]:
    """MCP & Engine interface to search for samples without modifying Ableton."""
    res = resolver or get_sample_resolver()
    candidates = res.find_samples(role=role, style=style, character=character, max_results=max_results)
    return {
        "role": role,
        "style": style,
        "character": character,
        "results_count": len(candidates),
        "results": [c.to_dict() for c in candidates]
    }

def select_sample(
    role: str,
    style: str = "",
    character: str = "",
    seed: int = 2026,
    resolver: Optional[SampleLibraryResolver] = None
) -> SampleCandidate:
    """Deterministically select the best sample candidate using seed.
    
    Guarantees reproducibility:
    same seed + same sample library + same engine version = same sound assignment.
    """
    res = resolver or get_sample_resolver()
    candidates = res.find_samples(role=role, style=style, character=character, max_results=10)
    if not candidates:
        return res._generate_fallback(role, style, character)[0]

    # Select top candidates within 10% of the maximum confidence
    top_score = candidates[0].confidence
    tier_candidates = [c for c in candidates if c.confidence >= top_score * 0.90]

    # Deterministic pseudo-random selection using seed + role hash
    rng = random.Random(seed + hash(role) % 100000)
    selected = rng.choice(tier_candidates)
    return selected

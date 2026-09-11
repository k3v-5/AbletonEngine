"""
AbletonEngine User Learning & Persistent Memory Engine.
Stores favorite patterns (with 1-5 star ratings), user production preferences,
and session decision history in state/learned/ for continuous cross-session improvement.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Default directory for persistent learned state in AbletonEngine
DATA_DIR = Path(os.environ.get("ABLETON_LEARNED_DIR", Path(__file__).resolve().parent.parent.parent / "state" / "learned"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

PATTERNS_FILE = DATA_DIR / "user_patterns.json"
PREFERENCES_FILE = DATA_DIR / "user_preferences.json"
HISTORY_FILE = DATA_DIR / "session_history.json"


def _load_json(filepath: Path) -> dict:
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_json(filepath: Path, data: dict) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# FAVORITE & SUCCESSFUL PATTERNS
# ============================================================================

def save_favorite_pattern(
    pattern_type: str,
    name: str,
    notes: List[Dict[str, Any]],
    genre: str = "",
    key: str = "",
    bpm: float = 0.0,
    rating: int = 5,
    user_notes: str = "",
) -> str:
    """
    Saves a pattern approved or rated by the user into persistent memory.
    """
    patterns = _load_json(PATTERNS_FILE)
    if pattern_type not in patterns:
        patterns[pattern_type] = []

    entry = {
        "name": name,
        "notes": notes,
        "genre": genre.lower().strip(),
        "key": key.strip(),
        "bpm": float(bpm),
        "rating": max(1, min(5, int(rating))),
        "user_notes": user_notes.strip(),
        "created_at": datetime.now().isoformat(),
    }

    # Replace existing with same name and type, or append
    existing_idx = next((i for i, p in enumerate(patterns[pattern_type]) if p.get("name") == name), None)
    if existing_idx is not None:
        patterns[pattern_type][existing_idx] = entry
    else:
        patterns[pattern_type].append(entry)

    _save_json(PATTERNS_FILE, patterns)
    return f"Patrón '{name}' ({pattern_type}) guardado exitosamente con rating {rating}/5 estrellas."


def get_favorite_patterns(
    pattern_type: str = "",
    genre: str = "",
    min_rating: int = 4,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Retrieves saved favorite patterns filtered by type, genre, and minimum star rating.
    """
    patterns = _load_json(PATTERNS_FILE)
    results = []

    types_to_search = [pattern_type] if pattern_type and pattern_type in patterns else patterns.keys()
    genre_norm = genre.lower().strip()

    for ptype in types_to_search:
        for entry in patterns.get(ptype, []):
            if genre_norm and entry.get("genre") and entry.get("genre") != genre_norm:
                continue
            if entry.get("rating", 0) < min_rating:
                continue
            item = dict(entry)
            item["pattern_type"] = ptype
            results.append(item)

    results.sort(key=lambda x: (x.get("rating", 0), x.get("created_at", "")), reverse=True)
    return results[:limit]


# ============================================================================
# USER PRODUCTION PREFERENCES
# ============================================================================

def save_user_preference(category: str, key: str, value: Any) -> str:
    """
    Stores a durable user preference (e.g., favorite scale, default master target, preferred VSTs).
    """
    prefs = _load_json(PREFERENCES_FILE)
    cat_key = category.lower().strip()
    if cat_key not in prefs:
        prefs[cat_key] = {}

    prefs[cat_key][key] = {
        "value": value,
        "updated_at": datetime.now().isoformat(),
    }
    _save_json(PREFERENCES_FILE, prefs)
    return f"Preferencia guardada: [{category}] {key} = {value}"


def get_user_preferences(category: str = "", key: str = "") -> Any:
    """
    Retrieves stored preferences by category and optional key.
    """
    prefs = _load_json(PREFERENCES_FILE)
    if not category:
        return {cat: {k: v["value"] for k, v in items.items()} for cat, items in prefs.items()}

    cat_key = category.lower().strip()
    if cat_key not in prefs:
        return None

    if key:
        item = prefs[cat_key].get(key)
        return item["value"] if item else None

    return {k: v["value"] for k, v in prefs[cat_key].items()}


# ============================================================================
# HISTORICAL DECISION LOGGING & CONTEXT SUMMARY
# ============================================================================

def log_decision_feedback(tool_or_feature: str, context: Dict[str, Any], accepted: bool = True) -> None:
    """
    Logs whether a proposed decision/recipe was approved by the user.
    """
    history = _load_json(HISTORY_FILE)
    if "decisions" not in history:
        history["decisions"] = []

    history["decisions"].append({
        "tool": tool_or_feature,
        "context": context,
        "accepted": accepted,
        "timestamp": datetime.now().isoformat(),
    })
    # Keep last 500 decisions
    if len(history["decisions"]) > 500:
        history["decisions"] = history["decisions"][-500:]

    _save_json(HISTORY_FILE, history)


def get_learned_context_summary() -> str:
    """
    Generates a concise markdown summary of learned user preferences for Copilot context injection.
    """
    prefs = _load_json(PREFERENCES_FILE)
    patterns = _load_json(PATTERNS_FILE)

    lines = ["### [Memoria Persistente del Productor:"]
    if not prefs and not patterns:
        lines.append("- No hay preferencias guardadas aún. El motor usará configuraciones canónicas estándar.")
        return "\n".join(lines)

    if prefs:
        lines.append("**Preferencias Guardadas:**")
        for cat, items in prefs.items():
            for k, v in items.items():
                lines.append(f"  • [{cat.title()}] {k}: `{v['value']}`")

    total_patterns = sum(len(v) for v in patterns.values())
    if total_patterns > 0:
        lines.append(f"**Patrones de 5 Estrellas Guardados:** {total_patterns} patrones disponibles para inspiración.")

    return "\n".join(lines)

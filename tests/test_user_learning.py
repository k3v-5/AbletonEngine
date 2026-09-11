# tests/test_user_learning.py
import pytest
import tempfile
import os
from pathlib import Path
from engine.memory.user_learning import (
    save_favorite_pattern, get_favorite_patterns,
    save_user_preference, get_user_preferences,
    get_learned_context_summary
)

def test_save_and_retrieve_favorite_patterns():
    msg = save_favorite_pattern(
        pattern_type="bassline",
        name="Test 808 Phonk Dark",
        notes=[{"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 110}],
        genre="phonk",
        rating=5,
        user_notes="Hard punchy 808"
    )
    assert "5/5" in msg
    patterns = get_favorite_patterns(pattern_type="bassline", min_rating=5)
    assert len(patterns) >= 1
    found = any(p["name"] == "Test 808 Phonk Dark" for p in patterns)
    assert found

def test_user_preferences():
    save_user_preference("sound_design", "favorite_synth", "Serum 2")
    fav = get_user_preferences("sound_design", "favorite_synth")
    assert fav == "Serum 2"

def test_learned_context_summary():
    summary = get_learned_context_summary()
    assert "[Memoria Persistente" in summary

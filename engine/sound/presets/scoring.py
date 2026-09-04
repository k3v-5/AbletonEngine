"""
Preset Scoring Engine:
Evaluates preset candidates against role, genre, character, and brightness targets.
"""
from typing import Dict, Any

class PresetScoringEngine:
    """Calculates weighted match score for preset candidates."""

    @staticmethod
    def score_preset(candidate: Dict[str, Any], intent_data: Dict[str, Any]) -> float:
        # Weights: role=30%, genre=25%, character=20%, brightness=15%, availability=10%
        role_match = 1.0 if candidate.get("role", "").lower() == intent_data.get("role", "").lower() else 0.2
        genre_match = 1.0 if candidate.get("genre", "").lower() == intent_data.get("genre", "").lower() else 0.5
        char_match = 1.0 if candidate.get("character", "").lower() == intent_data.get("character", "").lower() else 0.4
        
        c_bright = float(candidate.get("brightness", 0.5))
        i_bright = float(intent_data.get("brightness", 0.5))
        bright_match = 1.0 - abs(c_bright - i_bright)
        avail = 1.0 if candidate.get("available", True) else 0.0

        total = (role_match * 30.0) + (genre_match * 25.0) + (char_match * 20.0) + (bright_match * 15.0) + (avail * 10.0)
        return round(total, 2)

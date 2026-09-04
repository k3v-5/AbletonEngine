"""
Preset Resolver:
Selects the optimal instrument and preset patch without random guessing.
"""
from typing import Dict, Any, List
from .scoring import PresetScoringEngine

PRESET_DATABASE: List[Dict[str, Any]] = [
    {"name": "Sub_Deep_Mono", "instrument": "Drift", "role": "SUB_BASS", "genre": "melodic_techno", "character": "dark", "brightness": 0.15, "available": True},
    {"name": "Bass_Club_Rolling", "instrument": "Wavetable", "role": "BASS", "genre": "melodic_techno", "character": "dark_club", "brightness": 0.35, "available": True},
    {"name": "Lead_Hypnotic_Saw", "instrument": "Wavetable", "role": "LEAD", "genre": "melodic_techno", "character": "bright", "brightness": 0.75, "available": True},
    {"name": "Lead_Analog_Square", "instrument": "Drift", "role": "LEAD", "genre": "melodic_techno", "character": "analog_warm", "brightness": 0.60, "available": True},
    {"name": "Pad_Dark_Cinematic", "instrument": "Wavetable", "role": "PAD", "genre": "melodic_techno", "character": "cinematic", "brightness": 0.45, "available": True}
]

class PresetResolver:
    """Resolves highest-confidence patch for a SoundIntent."""

    @classmethod
    def resolve_preset(cls, role: str, character: str = "dark_club", genre: str = "melodic_techno", brightness: float = 0.5) -> Dict[str, Any]:
        intent_data = {"role": role, "character": character, "genre": genre, "brightness": brightness}
        scored = []

        for p in PRESET_DATABASE:
            score = PresetScoringEngine.score_preset(p, intent_data)
            scored.append({"preset": p, "score": score})

        scored.sort(key=lambda s: s["score"], reverse=True)
        best = scored[0] if scored else None

        if best and best["score"] >= 50.0:
            return {
                "instrument": best["preset"]["instrument"],
                "preset": best["preset"]["name"],
                "confidence": round(best["score"] / 100.0, 2),
                "reason": f"Scored {best['score']}/100 match for {role} ({character} {genre})"
            }

        # Fallback safe preset
        inst = "Wavetable" if role.upper() in ["LEAD", "PAD"] else "Drift"
        return {
            "instrument": inst,
            "preset": f"Default_{role.capitalize()}",
            "confidence": 0.60,
            "reason": "Default native fallback patch"
        }

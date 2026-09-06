"""
Preset Resolver:
Selects the optimal instrument and preset patch without random guessing,
integrating with the Universal VST Indexer, Multi-Criteria Search, and Patch Decision Engine.
"""
from typing import Dict, Any, List, Optional
from .scoring import PresetScoringEngine
from ...instruments.presets.patch_decision import PatchDecisionEngine
from ...instruments.presets.models import DecisionAction

PRESET_DATABASE: List[Dict[str, Any]] = [
    {"name": "Sub_Deep_Mono", "instrument": "Drift", "role": "SUB_BASS", "genre": "melodic_techno", "character": "dark", "brightness": 0.15, "available": True},
    {"name": "Bass_Club_Rolling", "instrument": "Wavetable", "role": "BASS", "genre": "melodic_techno", "character": "dark_club", "brightness": 0.35, "available": True},
    {"name": "Lead_Hypnotic_Saw", "instrument": "Wavetable", "role": "LEAD", "genre": "melodic_techno", "character": "bright", "brightness": 0.75, "available": True},
    {"name": "Lead_Analog_Square", "instrument": "Drift", "role": "LEAD", "genre": "melodic_techno", "character": "analog_warm", "brightness": 0.60, "available": True},
    {"name": "Pad_Dark_Cinematic", "instrument": "Wavetable", "role": "PAD", "genre": "melodic_techno", "character": "cinematic", "brightness": 0.45, "available": True}
]

_decision_engine: Optional[PatchDecisionEngine] = None

def get_decision_engine() -> PatchDecisionEngine:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = PatchDecisionEngine()
    return _decision_engine


class PresetResolver:
    """Resolves highest-confidence patch for a SoundIntent across VSTs and native instruments."""

    @classmethod
    def resolve_preset(
        cls,
        role: str,
        character: str = "dark_club",
        genre: str = "melodic_techno",
        brightness: float = 0.5,
        preferred_plugin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolves the optimal patch. First queries the PatchDecisionEngine across all indexed
        user plugins (Arturia, FabFilter, Vital, Serum, etc.). If none match with high confidence,
        falls back to scored native profiles.
        """
        try:
            decision_eng = get_decision_engine()
            decision = decision_eng.decide(
                role=role,
                character=character,
                preferred_plugin=preferred_plugin
            )

            if decision.action == DecisionAction.LOAD_EXISTING_PRESET and decision.preset:
                return {
                    "instrument": decision.plugin_name,
                    "preset": decision.preset.name,
                    "vendor": decision.vendor,
                    "file_path": decision.preset.file_path,
                    "confidence": decision.confidence,
                    "reason": decision.rationale,
                    "action": decision.action.value,
                }
            elif decision.action == DecisionAction.APPLY_SEMANTIC_MACROS and decision.preset:
                return {
                    "instrument": decision.plugin_name,
                    "preset": decision.preset.name,
                    "vendor": decision.vendor,
                    "file_path": decision.preset.file_path,
                    "macro_parameters": decision.macro_parameters,
                    "confidence": decision.confidence,
                    "reason": decision.rationale,
                    "action": decision.action.value,
                }
            elif decision.action == DecisionAction.SYNTHESIZE_PROCEDURAL_PATCH:
                return {
                    "instrument": decision.plugin_name,
                    "preset": "Procedural_Patch",
                    "vendor": decision.vendor,
                    "file_path": decision.procedural_patch_path,
                    "confidence": decision.confidence,
                    "reason": decision.rationale,
                    "action": decision.action.value,
                }
        except Exception:
            pass

        # Fallback to local scored native database
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

        # Safe native fallback patch
        inst = "Wavetable" if role.upper() in ["LEAD", "PAD"] else "Drift"
        return {
            "instrument": inst,
            "preset": f"Default_{role.capitalize()}",
            "confidence": 0.60,
            "reason": "Default native fallback patch"
        }

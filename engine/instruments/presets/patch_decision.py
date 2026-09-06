# engine/instruments/presets/patch_decision.py
"""
Patch Decision Engine:
Decides whether to load an existing high-confidence preset from the user's library,
procedurally synthesize a tailored patch (e.g. via VitalBuilder),
or apply semantic macro adjustments to an existing preset.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from .models import (
    PatchDecision,
    DecisionAction,
    PresetRecord,
    SearchQuery,
    PresetCategory,
)
from .search import PresetSearchEngine
from ...sound.vital.builder import VitalPatchBuilder
from ...sound.vital.file_manager import VitalPresetManager


class PatchDecisionEngine:
    """Evaluates user library presets vs procedural synthesis capabilities."""

    def __init__(self, search_engine: Optional[PresetSearchEngine] = None):
        self.search_engine = search_engine or PresetSearchEngine()

    def decide(
        self,
        role: str,
        character: str = "dark",
        preferred_plugin: Optional[str] = None,
        force_synthesis: bool = False,
        procedural_output_dir: Optional[str] = None,
    ) -> PatchDecision:
        """
        Determines the optimal sound strategy:
        1. Procedural synthesis (if forced or high-precision custom 808/bass requested for Vital)
        2. High-confidence existing preset from user's library (Arturia, FabFilter, Vital, Serum)
        3. Semantic macro adjustments on existing preset
        4. Safe native Live fallback
        """
        role_upper = role.upper()

        # 1. Check procedural synthesis for Vital when requested or for tailored 808s
        if force_synthesis or (preferred_plugin and "vital" in preferred_plugin.lower() and "808" in character.lower()):
            out_dir = Path(procedural_output_dir or "presets/vital")
            out_dir.mkdir(parents=True, exist_ok=True)
            patch_name = f"Procedural_{role}_{character.replace(' ', '_')}.vital"
            out_file = out_dir / patch_name

            # Generate procedural patch using VitalPatchBuilder and VitalPresetManager
            spec = VitalPatchBuilder.build_reese_bass(
                sub_weight=0.9,
                detune_amount=1.5 if "808" in character.lower() else 3.5,
                filter_cutoff=65.0,
                name=patch_name.replace(".vital", "")
            )
            mgr = VitalPresetManager(engine_dir=out_dir)
            mgr.save_preset(spec, out_file)

            return PatchDecision(
                action=DecisionAction.SYNTHESIZE_PROCEDURAL_PATCH,
                plugin_name="Vital",
                vendor="Vital Audio",
                procedural_patch_path=str(out_file.resolve()),
                confidence=0.95,
                rationale=f"Synthesized procedural {role} patch tailored for '{character}'."
            )

        # 2. Search existing presets in the indexed library
        plugin_filter = [preferred_plugin] if preferred_plugin else None
        results = self.search_engine.find_by_role(
            role=role_upper,
            character=character,
            plugin_hint=preferred_plugin,
            limit=5
        )

        # If a top result with score >= 0.65 exists, use it
        if results and results[0].relevance_score >= 0.65:
            top_match = results[0]
            preset = top_match.preset

            # Check if semantic macros should be applied (e.g. Arturia Analog Lab or Pigments)
            macros = {}
            if "analog lab" in preset.plugin_name.lower() or "pigments" in preset.plugin_name.lower():
                # Derive semantic macros from character
                brightness = 0.35 if "dark" in character.lower() else (0.80 if "bright" in character.lower() else 0.50)
                timbre = 0.70 if "warm" in character.lower() else 0.50
                movement = 0.65 if "moving" in character.lower() or "hypnotic" in character.lower() else 0.30
                macros = {
                    "Brightness": brightness,
                    "Timbre": timbre,
                    "Time": 0.50,
                    "Movement": movement
                }
                return PatchDecision(
                    action=DecisionAction.APPLY_SEMANTIC_MACROS,
                    plugin_name=preset.plugin_name,
                    vendor=preset.vendor,
                    preset=preset,
                    macro_parameters=macros,
                    confidence=top_match.relevance_score,
                    rationale=f"Selected preset '{preset.name}' with tailored semantic macros for '{character}'."
                )

            return PatchDecision(
                action=DecisionAction.LOAD_EXISTING_PRESET,
                plugin_name=preset.plugin_name,
                vendor=preset.vendor,
                preset=preset,
                confidence=top_match.relevance_score,
                rationale=f"Found high-confidence library preset '{preset.name}' ({round(top_match.relevance_score*100)}% match)."
            )

        # 3. Fallback to native Live device
        native_inst = "Drift" if role_upper in ["BASS", "LEAD"] else "Wavetable"
        return PatchDecision(
            action=DecisionAction.FALLBACK_NATIVE,
            plugin_name=native_inst,
            vendor="Ableton",
            confidence=0.60,
            rationale=f"Defaulting to native Live '{native_inst}' for role {role_upper}."
        )

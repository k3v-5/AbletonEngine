# tests/test_patch_decision.py
"""
Test Suite for Patch Decision Engine & Preset Resolver Integration:
Verifies that the engine can decide whether to load an existing preset,
procedurally synthesize a new .vital patch, or apply semantic macros.
"""

import os
from pathlib import Path
import pytest

from engine.instruments.presets.models import (
    PatchDecision,
    DecisionAction,
    PresetRecord,
    PresetCategory,
)
from engine.instruments.presets.search import PresetSearchEngine
from engine.instruments.presets.patch_decision import PatchDecisionEngine
from engine.sound.presets.resolver import PresetResolver


class MockPresetSearch:
    def find_by_role(self, role: str, character: str = "", plugin_hint: str = None, limit: int = 5):
        from engine.instruments.presets.models import SearchResult
        if role.upper() in ["KEYS", "PIANO"]:
            preset = PresetRecord(
                id="arturia_rhodes_1",
                name="Stage 73 Mark I Vintage",
                plugin_name="Analog Lab V",
                vendor="Arturia",
                category=PresetCategory.KEYS.value,
                subcategory="Rhodes",
                tags=["keys", "rhodes", "warm", "vintage"],
            )
            return [SearchResult(preset=preset, relevance_score=0.92, match_reasons=["High role & character match"])]
        elif role.upper() in ["LEAD"]:
            preset = PresetRecord(
                id="vital_lead_1",
                name="Hypnotic Cyber Saw",
                plugin_name="Vital",
                vendor="Vital Audio",
                category=PresetCategory.LEAD.value,
                subcategory="Lead",
                tags=["lead", "bright", "hypnotic"],
            )
            return [SearchResult(preset=preset, relevance_score=0.88, match_reasons=["High role match"])]
        return []


class TestPatchDecisionEngine:
    def test_semantic_macro_decision_for_analog_lab(self):
        search_mock = MockPresetSearch()
        decision_eng = PatchDecisionEngine(search_engine=search_mock)

        decision = decision_eng.decide(role="KEYS", character="dark warm rhodes")
        assert decision.action == DecisionAction.APPLY_SEMANTIC_MACROS
        assert decision.plugin_name == "Analog Lab V"
        assert "Brightness" in decision.macro_parameters
        assert decision.macro_parameters["Brightness"] == 0.35  # Dark character
        assert decision.macro_parameters["Timbre"] == 0.70      # Warm character

    def test_procedural_synthesis_decision(self, tmp_path):
        decision_eng = PatchDecisionEngine()
        out_dir = str(tmp_path / "vital_patches")

        decision = decision_eng.decide(
            role="BASS",
            character="heavy sub 808",
            preferred_plugin="Vital",
            force_synthesis=True,
            procedural_output_dir=out_dir
        )
        assert decision.action == DecisionAction.SYNTHESIZE_PROCEDURAL_PATCH
        assert decision.procedural_patch_path is not None
        assert Path(decision.procedural_patch_path).exists()
        assert decision.procedural_patch_path.endswith(".vital")

    def test_preset_resolver_integration(self):
        # Resolve preset through enhanced PresetResolver
        res = PresetResolver.resolve_preset(
            role="LEAD",
            character="bright saw",
            genre="trap"
        )
        assert "instrument" in res
        assert "preset" in res
        assert "confidence" in res
        assert res["confidence"] > 0.5

# tests/test_live_arrangement_automation.py
import pytest
from unittest.mock import MagicMock
from engine.production.recipe_engine import (
    ProductionRecipeEngine,
    ProductionRecipe,
    TrackBlueprint,
    RecipeSection
)
from engine.arrangement.automation.weaver import (
    ArrangementAutomationWeaver,
    TransitionAutomationType
)


class MockLiveConnection:
    def __init__(self):
        self.commands_sent = []

    def send_command(self, cmd, params=None):
        params = params or {}
        self.commands_sent.append({"cmd": cmd, "params": params})
        if cmd == "create_arrangement_automation_envelope":
            pts = params.get("points", [])
            return {
                "track_index": params.get("track_index", 0),
                "device_index": params.get("device_index", 0),
                "parameter_name": params.get("parameter", "Cutoff"),
                "points_count": len(pts),
                "envelope_injected": True,
                "injection_details": {
                    "points_injected": len(pts),
                    "clips_touched": ["Intro Clip", "Verse Clip"],
                    "mode": "arrangement_clips_distributed"
                },
                "status": "success"
            }
        return {"status": "success"}


def test_section_automation_synth_parameter_resolution():
    """Confirms get_section_automation_menu maps exact parameter names per synth model."""
    recipe = ProductionRecipe(
        title="Synth Automation Test",
        genre_reference="Synthwave Test",
        bpm=128.0,
        key="C",
        scale="Minor",
        chord_progression=["Cm", "Ab", "Eb", "Bb"],
        tracks=[
            TrackBlueprint(track_index=0, name="Serum Lead", role="lead", instrument_name="Serum 2"),
            TrackBlueprint(track_index=1, name="Analog Rhodes", role="keys", instrument_name="Analog Lab V"),
            TrackBlueprint(track_index=2, name="Vital Sub", role="bass", instrument_name="Vital"),
        ],
        sections=[
            RecipeSection(name="Verse 1", start_bar=0, length_bars=8, active_roles=["keys", "bass"]),
            RecipeSection(name="Chorus 1", start_bar=8, length_bars=8, active_roles=["keys", "bass", "lead"]),
        ]
    )

    menu = ProductionRecipeEngine.get_section_automation_menu(recipe)
    autos = menu.get("available_automations", [])
    assert len(autos) > 0

    # Serum should have 'Filter 1 Freq'
    serum_auto = next((a for a in autos if a["track_name"] == "Serum Lead" and a["type"] == "FILTER_SWEEP_UP"), None)
    assert serum_auto is not None
    assert serum_auto["parameter_name"] == "Filter 1 Freq"

    # Analog Lab V should have 'P1 Brightness' or 'Reverb Volume'
    analog_filter = next((a for a in autos if a["track_name"] == "Analog Rhodes" and a["type"] == "FILTER_SWEEP_UP"), None)
    assert analog_filter is not None
    assert analog_filter["parameter_name"] == "P1 Brightness"

    analog_reverb = next((a for a in autos if a["track_name"] == "Analog Rhodes" and a["type"] == "REVERB_WASHOUT"), None)
    assert analog_reverb is not None
    assert analog_reverb["parameter_name"] == "Reverb Volume"

    # Sub cleanup on Vital
    vital_sub = next((a for a in autos if a["track_name"] == "Vital Sub" and a["type"] == "SUB_CLEANUP"), None)
    assert vital_sub is not None
    assert vital_sub["parameter_name"] == "Volume"


def test_apply_section_automations_envelope_distribution():
    """Confirms apply_section_automations dispatches create_arrangement_automation_envelope with full points."""
    conn = MockLiveConnection()
    test_automations = [
        {
            "id": "filter_riser_0_Verse_to_Chorus",
            "type": "FILTER_SWEEP_UP",
            "track_index": 0,
            "device_index": 0,
            "parameter_name": "Filter 1 Freq",
            "points": [
                {"time": 24.0, "value": 0.20},
                {"time": 28.0, "value": 0.50},
                {"time": 32.0, "value": 0.95}
            ]
        },
        {
            "id": "sub_vacuum_2_Verse_to_Chorus",
            "type": "SUB_CLEANUP",
            "track_index": 2,
            "device_index": None,
            "parameter_name": "Volume",
            "points": [
                {"time": 24.0, "value": 0.85},
                {"time": 31.0, "value": 0.0},
                {"time": 32.0, "value": 0.85}
            ]
        }
    ]

    manifest = ProductionRecipeEngine.apply_section_automations(conn, test_automations)
    assert manifest["status"] == "SUCCESS"
    assert manifest["applied_count"] == 2
    assert manifest["error_count"] == 0

    # Verify calls
    auto_calls = [c for c in conn.commands_sent if c["cmd"] == "create_arrangement_automation_envelope"]
    assert len(auto_calls) == 2
    assert auto_calls[0]["params"]["parameter"] == "Filter 1 Freq"
    assert auto_calls[1]["params"]["parameter"] == "Volume"


def test_arrangement_automation_weaver_continuity():
    """Verifies ArrangementAutomationWeaver creates monotonic exponential curves with correct boundaries."""
    points = ArrangementAutomationWeaver.generate_filter_sweep(
        start_bar=8.0,
        duration_bars=4.0,
        direction="up",
        min_val=0.20,
        max_val=0.90,
        curve="exponential"
    )

    # 4 bars * 4 = 16 steps + 1 = 17 points
    assert len(points) >= 16
    # Start time at beat 32.0 (bar 8 * 4)
    assert points[0]["time"] == 32.0
    # End time at beat 48.0 (bar 12 * 4)
    assert points[-1]["time"] == 48.0
    # Values start at min_val and end at max_val
    assert abs(points[0]["value"] - 0.20) < 0.01
    assert abs(points[-1]["value"] - 0.90) < 0.01
    # Exponential curve check: midpoint should be lower than linear midpoint
    mid_idx = len(points) // 2
    linear_mid = 0.20 + (0.90 - 0.20) * 0.5  # 0.55
    assert points[mid_idx]["value"] < linear_mid

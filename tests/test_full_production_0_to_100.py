# tests/test_full_production_0_to_100.py
"""
Fase 10: Complete 0-to-100 Commercial Production Integration Test.
Unifies all 9 preceding architectural phases into a single automated pipeline:
1. Questionaire & Recipe Assembly (Fase 10)
2. Strict Configuration Governance (Fase 1)
3. Semantic FX Mappings (Fase 2)
4. Real Presets & Macro Sculpting in Analog Lab V (Fase 3)
5. Deep Synthesizer Sculpting for Serum 2, Vital, Massive X, Pigments (Fase 4)
6. Section Automations & Boundary Transitions (Fase 5)
7. Genre-Authentic Rhythm & Grooves (Fase 6)
8. Vocal Lead Staging & Multitrack Ducking (Fase 7)
9. 5-Stage Pre-Mastering & Pro-L 2 True Peak Chain (Fase 8)
10. Live Acoustic Metering & Self-Healing Loop (Fase 9)
"""

import pytest
from unittest.mock import MagicMock
from engine.production.recipe_engine import (
    ProductionRecipeEngine,
    ProductionRecipe,
    TrackBlueprint,
    RecipeSection
)
from engine.supervisor.governance import governance_supervisor
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.music.drums.genre_grooves import GenreRhythmGrooveEngine
from engine.vocal.vocal_staging_supervisor import VocalStagingSupervisor
from engine.mastering.guided_mastering import GuidedMasteringEngine, DeliveryProfile


def test_full_production_0_to_100_pipeline():
    # 1. Initialize Mock Live Connection
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {
        "status": "success",
        "result": {
            "devices": [{"name": "Mock Device"}],
            "output_meter_level": 0.32,
            "volume": 0.85
        }
    }

    # Reset Governance Registry
    governance_supervisor._tracks.clear()
    DeviceParameterSupervisor._SCULPTED_REGISTRY.clear()

    # 2. Build 8-Track Commercial Recipe
    sections = [
        RecipeSection(name="1. Intro", start_bar=0, length_bars=8, active_roles=["keys", "pad"]),
        RecipeSection(name="2. Verse 1", start_bar=8, length_bars=16, active_roles=["keys", "bass", "drums"]),
        RecipeSection(name="3. Pre-Chorus", start_bar=24, length_bars=8, active_roles=["keys", "pad", "arp", "drums"]),
        RecipeSection(name="4. Chorus", start_bar=32, length_bars=16, active_roles=["keys", "bass", "drums", "lead", "pad", "arp"]),
        RecipeSection(name="5. Outro", start_bar=48, length_bars=12, active_roles=["keys", "pad"])
    ]

    # Generate Genre Rhythm for Drums (Fase 6)
    drum_notes = GenreRhythmGrooveEngine.generate_rhythm_pattern("neo_soul", length_bars=4, tempo=82.0)
    assert len(drum_notes) > 10

    tracks = [
        TrackBlueprint(
            track_index=0, name="Rhodes", role="keys",
            instrument_name="Analog Lab V", instrument_uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            parameter_sculpting={"MACRO_1": 0.75, "MACRO_2": 0.68, "REVERB_MIX": 0.35}
        ),
        TrackBlueprint(
            track_index=1, name="Sub Bass", role="bass",
            instrument_name="Vital", instrument_uri="query:Plugins#VST3:Vital%20Audio:Vital",
            parameter_sculpting={"MACRO_1": 0.82, "FILTER_CUTOFF": 0.45}
        ),
        TrackBlueprint(
            track_index=2, name="Lead Synth", role="lead",
            instrument_name="Serum 2", instrument_uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
            effects=[{"name": "Thermal", "uri": "query:Plugins#VST3:Output:Thermal"}],
            parameter_sculpting={"OSC_A_WT_POS": 0.65, "FILTER_CUTOFF": 0.70}
        ),
        TrackBlueprint(
            track_index=3, name="Ambient Pad", role="pad",
            instrument_name="Pigments", instrument_uri="query:Plugins#VST3:Arturia:Pigments",
            parameter_sculpting={"MACRO_1": 0.68, "FILTER_CUTOFF": 0.65}
        ),
        TrackBlueprint(
            track_index=4, name="Arp Texture", role="arp",
            instrument_name="Massive X", instrument_uri="query:Plugins#VST3:Native%20Instruments:Massive%20X",
            parameter_sculpting={"MACRO_1": 0.60, "FILTER_CUTOFF": 0.75}
        ),
        TrackBlueprint(
            track_index=5, name="Drums", role="drums",
            instrument_name="Drum Rack", instrument_uri="query:Drums#Drum%20Rack",
            clip_notes=[{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity} for n in drum_notes]
        ),
        TrackBlueprint(
            track_index=6, name="Vocal Lead", role="vocal",
            instrument_name=None, instrument_uri=None,
            effects=[{"name": "Pro-Q 4", "uri": "query:Plugins#VST3:FabFilter:Pro-Q%204"}]
        )
    ]

    recipe = ProductionRecipe(
        title="0-to-100 Commercial Masterpiece",
        genre_reference="Neo-Soul Ballad (Tyler / Lola Young Style)",
        bpm=82.0,
        key="Eb",
        scale="Major",
        chord_progression=["Abmaj7", "G7(b13)", "Cm7", "Bb9"],
        tracks=tracks,
        sections=sections,
        target_lufs=-8.5,
        max_true_peak=-0.5,
        total_bars=60
    )

    # 3. Register All Tracks with Governance (Fase 1)
    for tb in recipe.tracks:
        governance_supervisor.register_track(tb.track_index, name=tb.name, role=tb.role)
        if tb.instrument_name:
            governance_supervisor.notify_instrument_loaded(tb.track_index, tb.instrument_name, device_index=0)
            if tb.instrument_name.lower() in ["analog lab v", "analog lab"]:
                governance_supervisor.record_preset_selected(tb.track_index, "Warm Stage-73 Rhodes", device_index=0)
        for eff in tb.effects:
            governance_supervisor.request_add_effect(tb.track_index, eff["name"])

    # 4. Enforce Mandatory Parameter Sculpting on every instrument & effect (Fases 2, 3, 4)
    for tb in recipe.tracks:
        if tb.instrument_name:
            DeviceParameterSupervisor.enforce_mandatory_sculpting(mock_conn, tb.track_index, device_index=0, role=tb.role)
        for eff_idx, eff in enumerate(tb.effects):
            dev_idx = eff_idx + (1 if tb.instrument_name else 0)
            DeviceParameterSupervisor.enforce_mandatory_sculpting(mock_conn, tb.track_index, device_index=dev_idx, role=tb.role)

    # Strict Governance Assertion: Zero tolerance for unconfigured devices
    governance_supervisor.assert_session_fully_sculpted()

    # 5. Section Automations & Boundary Transitions (Fase 5)
    auto_menu = ProductionRecipeEngine.get_section_automation_menu(recipe)
    assert auto_menu["total_candidates"] > 0
    assert len(auto_menu["available_automations"]) > 0

    # 6. Vocal Lead Staging & Multitrack Frequency Carving (Fase 7)
    staging_plan = VocalStagingSupervisor.calculate_vocal_staging_plan(
        track_names=[t.name for t in recipe.tracks],
        vocal_ranges_beats=[(16.0, 32.0), (48.0, 64.0)],
        song_length_beats=240.0,
        duck_amount_db=-2.5
    )
    assert staging_plan["status"] == "SUCCESS"
    assert staging_plan["competing_tracks_count"] >= 3
    assert len(staging_plan["ducking_envelope"]) > 0

    # 7. Guided 5-Device Master Chain & Calibration (Fase 8)
    master_result = GuidedMasteringEngine.execute_guided_mastering(
        conn=mock_conn,
        master_track_index=-1,
        profile=DeliveryProfile.CLUB_STANDARD,
        target_lufs_override=-8.5
    )
    assert master_result["status"] == "MASTERING_SUCCESS"
    assert master_result["achieved_lufs"] == -8.5
    assert len(master_result["steps_executed"]) == 7

    # 8. Incremental Acoustic Audit & Self-Healing (Fase 9)
    audit = ProductionRecipeEngine.audit_incremental_addition(
        conn=mock_conn,
        track_index=0,
        role="keys",
        event_description="Keys loaded and sculpted",
        target_master_lufs=-8.5,
        settle_time=0.0
    )
    assert audit["track_status"] in ["OPTIMAL", "TOO_QUIET", "TOO_LOUD"]
    assert "ai_decision_menu" in audit
    assert "TRIM_FADER" in audit["ai_decision_menu"]

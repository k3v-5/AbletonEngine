# tests/test_recipe_engine.py
"""
Automated Unit Tests for ProductionRecipeEngine and Authoritative Musical Skeleton.
Verifies:
1. Skeleton Questionnaire structure and mandatory questions.
2. RecipeSection, TrackBlueprint, and ProductionRecipe dataclasses.
3. Accurate URI resolution for instruments and serial effect chains.
4. Section Cue Point generation and timeline arrangement orchestration (active roles vs silent slots).
5. Channel loudness category auditing and auto-trimming.
6. Iterative Master LUFS feedback loop convergence.
"""

import pytest
import math
from typing import Dict, Any, List
from engine.production.recipe_engine import (
    ProductionRecipeEngine,
    RecipeSection,
    TrackBlueprint,
    ProductionRecipe,
    DeviceLoadFailureError,
    ArrangementMissingClipsError,
    DrumRackEmptyError,
    VERIFIED_PLUGIN_URIS
)


class MockAbletonConnection:
    """Mock socket connection recording all commands and simulating Live responses."""

    def __init__(self):
        self.commands_sent: List[Dict[str, Any]] = []
        self.tracks_data: Dict[int, Dict[str, Any]] = {}
        self.cue_points: List[Dict[str, Any]] = []
        self.master_gain: float = 0.25
        self.is_playing: bool = False

        # Initialize mock tracks
        for idx in range(25):
            self.tracks_data[idx] = {
                "name": f"Track_{idx}",
                "volume": 0.85,
                "output_meter_level": 0.25,
                "devices": [{"name": "Mock Device"}]  # Pre-populated so loading is satisfied
            }
        # Master track
        self.tracks_data[-1] = {
            "name": "Master",
            "volume": 0.85,
            "output_meter_level": 0.35,
            "devices": [{"name": "Pro-L 2"}]
        }

    def send_command(self, cmd: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        self.commands_sent.append({"cmd": cmd, "params": params})

        if cmd == "set_tempo":
            return {"status": "success", "tempo": params.get("tempo")}

        elif cmd == "switch_to_arrangement_view":
            return {"status": "success"}

        elif cmd == "set_current_song_time":
            return {"status": "success", "time": params.get("time")}

        elif cmd == "create_cue_point":
            cue = {"name": params.get("name"), "time": params.get("time")}
            self.cue_points.append(cue)
            return {"action": "created", "name": cue["name"], "time": cue["time"]}

        elif cmd == "get_cue_points":
            return {"count": len(self.cue_points), "cue_points": self.cue_points}

        elif cmd == "get_track_info":
            t_idx = params.get("track_index", 0)
            return {"result": self.tracks_data.get(t_idx, {"devices": [], "output_meter_level": 0.20, "volume": 0.85})}

        elif cmd == "set_track_name":
            t_idx = params.get("track_index", 0)
            if t_idx in self.tracks_data:
                self.tracks_data[t_idx]["name"] = params.get("name")
            return {"status": "success"}

        elif cmd == "set_track_volume":
            t_idx = params.get("track_index", 0)
            if t_idx in self.tracks_data:
                self.tracks_data[t_idx]["volume"] = params.get("volume")
            return {"status": "success"}

        elif cmd in ("load_instrument_or_effect", "load_browser_item"):
            t_idx = params.get("track_index", 0)
            uri = params.get("item_uri") or params.get("uri", "")
            dev_name = uri.split("#")[-1].replace("%20", " ")
            if t_idx in self.tracks_data:
                self.tracks_data[t_idx]["devices"].append({"name": dev_name})
            return {"status": "success", "loaded": dev_name}

        elif cmd == "get_drum_rack_pads":
            return {
                "active_pad_count": 16,
                "pads": [{"note": 36 + i, "name": f"Pad {i}"} for i in range(16)]
            }

        elif cmd == "get_arrangement_clips":
            return {
                "track_index": params.get("track_index", 0),
                "clip_count": 4,
                "clips": [{"name": "Clip", "start_time": 0.0, "end_time": 16.0}]
            }

        elif cmd == "set_device_parameter":
            param = params.get("parameter")
            val = params.get("value")
            if param == "Gain" and params.get("track_index") == -1:
                self.master_gain = val
                # Simulate acoustic gain response scaling meter levels toward target LUFS
                for t_idx in (18, 13, 4, 2):
                    self.tracks_data[t_idx]["output_meter_level"] = 0.70
            return {"status": "success"}

        elif cmd in ("create_clip", "set_clip_name", "add_notes_to_clip", "duplicate_session_clip_to_arrangement", "create_arrangement_automation_envelope"):
            return {"status": "success", "points_count": len(params.get("points", []))}

        elif cmd == "start_playback":
            self.is_playing = True
            return {"status": "playing"}

        elif cmd == "stop_playback":
            self.is_playing = False
            return {"status": "stopped"}

        elif cmd == "fire_clip":
            return {"status": "fired"}

        return {"status": "success"}


def test_skeleton_questionnaire():
    """Confirms the engine provides the complete structured musical skeleton questionnaire."""
    q = ProductionRecipeEngine.get_skeleton_questionnaire()
    assert "questions" in q
    question_ids = [item["id"] for item in q["questions"]]
    expected_ids = [
        "genre_reference", "tempo_bpm", "key_scale", "chord_progression",
        "role_instruments", "effect_chains", "sections", "target_lufs"
    ]
    for eid in expected_ids:
        assert eid in question_ids, f"Falta la pregunta requerida '{eid}' en el cuestionario"


def test_recipe_section_dataclass():
    """Confirms RecipeSection stores proper metadata and timing."""
    sec = RecipeSection(
        name="1. Intro",
        start_bar=0,
        length_bars=8,
        active_roles=["keys", "pad"],
        description="Atmospheric Rhodes with filtered pads"
    )
    assert sec.name == "1. Intro"
    assert sec.start_bar == 0
    assert sec.length_bars == 8
    assert "keys" in sec.active_roles
    assert "pad" in sec.active_roles


def test_resolve_uri():
    """Confirms URI resolution matches verified plugin browser URIs."""
    assert ProductionRecipeEngine.resolve_uri("Analog Lab V") == "query:Plugins#VST3:Arturia:Analog%20Lab%20V"
    assert ProductionRecipeEngine.resolve_uri("Serum 2") == "query:Plugins#VST3:Xfer%20Records:Serum%202"
    assert ProductionRecipeEngine.resolve_uri("Vital") == "query:Plugins#VST3:Vital%20Audio:Vital"
    assert ProductionRecipeEngine.resolve_uri("Pro-L 2") == "query:Plugins#VST3:FabFilter:Pro-L%202"
    assert ProductionRecipeEngine.resolve_uri("ShaperBox 3") == "query:Plugins#VST3:Cableguys:ShaperBox%203"
    assert ProductionRecipeEngine.resolve_uri("NonExistentSynth12345") is None


def test_execute_physical_recipe_with_sections(monkeypatch):
    """
    Confirms execute_physical_recipe deploys sections, cue points, serial effects,
    active vs silent clips, and achieves master LUFS compliance.
    """
    monkeypatch.setattr("engine.production.recipe_engine.time.sleep", lambda s: None)
    conn = MockAbletonConnection()

    # Pre-configure simulated levels for channel category test
    conn.tracks_data[18]["output_meter_level"] = 0.22  # Keys
    conn.tracks_data[13]["output_meter_level"] = 0.28  # Lead
    conn.tracks_data[4]["output_meter_level"] = 0.32   # Bass
    conn.tracks_data[2]["output_meter_level"] = 0.40   # Drums

    recipe = ProductionRecipe(
        title="Test Like Him Recipe",
        genre_reference="Like Him - Tyler, The Creator ft. Lola Young",
        bpm=82.0,
        key="Eb",
        scale="major",
        chord_progression=["Abmaj7", "G7(b13)", "Cm7", "Bb9"],
        tracks=[
            TrackBlueprint(
                track_index=18,
                name="Rhodes - Analog Lab V",
                role="keys",
                instrument_name="Analog Lab V",
                instrument_uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
                preset_name="Stage-73 Warm Suitcase",
                clip_notes=[{"pitch": 60, "start_time": 0.0, "duration": 4.0, "velocity": 85}],
                effects=[{"name": "Efx FRAGMENTS", "uri": "query:Plugins#VST3:Arturia:Efx%20FRAGMENTS"}]
            ),
            TrackBlueprint(
                track_index=13,
                name="Lead - Serum 2",
                role="lead",
                instrument_name="Serum 2",
                instrument_uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
                clip_notes=[{"pitch": 72, "start_time": 0.0, "duration": 2.0, "velocity": 90}],
                effects=[{"name": "Thermal", "uri": "query:Plugins#VST3:Output:Thermal"}]
            ),
            TrackBlueprint(
                track_index=4,
                name="Sub Bass - Vital",
                role="bass",
                instrument_name="Vital",
                instrument_uri="query:Plugins#VST3:Vital%20Audio:Vital",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 4.0, "velocity": 100}],
                effects=[{"name": "The God Particle", "uri": "query:Plugins#VST3:Cradle:The%20God%20Particle"}]
            ),
            TrackBlueprint(
                track_index=2,
                name="808 Core Kit",
                role="drums",
                instrument_name="808 Core Kit",
                instrument_uri="query:Drums#FileId_5422",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 110}],
                effects=[]
            )
        ],
        sections=[
            RecipeSection(name="1. Intro", start_bar=0, length_bars=8, active_roles=["keys"]),
            RecipeSection(name="2. Verse 1", start_bar=8, length_bars=16, active_roles=["keys", "bass", "drums"]),
            RecipeSection(name="3. Pre-Chorus", start_bar=24, length_bars=8, active_roles=["keys", "drums"]),
            RecipeSection(name="4. Chorus", start_bar=32, length_bars=16, active_roles=["keys", "bass", "drums", "lead"]),
            RecipeSection(name="5. Outro", start_bar=48, length_bars=12, active_roles=["keys"])
        ],
        target_lufs=-7.0,
        max_true_peak=-0.5
    )

    manifest = ProductionRecipeEngine.execute_physical_recipe(conn, recipe)

    # 1. Verify Manifest Status
    assert manifest["status"] == "SUCCESS"
    assert manifest["tempo"] == 82.0

    # 2. Verify Cue Points were created for all 5 sections
    cue_commands = [c for c in conn.commands_sent if c["cmd"] == "create_cue_point"]
    assert len(cue_commands) >= 5
    cue_names = [c["params"]["name"] for c in cue_commands]
    for expected_sec in ["1. Intro", "2. Verse 1", "3. Pre-Chorus", "4. Chorus", "5. Outro"]:
        assert expected_sec in cue_names

    # 3. Verify Clip Arrangement Duplication (both musical slot 0 and silent slot 1)
    dup_commands = [c for c in conn.commands_sent if c["cmd"] == "duplicate_session_clip_to_arrangement"]
    assert len(dup_commands) > 0

    # Lead (track 13) should be inactive in Intro (start_bar 0..8) -> slot 1 used
    lead_intro_dups = [
        c for c in dup_commands
        if c["params"]["track_index"] == 13 and c["params"]["destination_time"] in (0.0, 16.0)
    ]
    assert len(lead_intro_dups) == 2
    for d in lead_intro_dups:
        assert d["params"]["clip_index"] == 1, "Lead debe usar clip slot 1 (silencio) durante Intro"

    # Lead (track 13) should be active in Chorus (start_bar 32..48, beats 128..192) -> slot 0 used
    lead_chorus_dups = [
        c for c in dup_commands
        if c["params"]["track_index"] == 13 and c["params"]["destination_time"] in (128.0, 144.0, 160.0, 176.0)
    ]
    assert len(lead_chorus_dups) == 4
    for d in lead_chorus_dups:
        assert d["params"]["clip_index"] == 0, "Lead debe usar clip slot 0 (musical) durante Chorus"

    # 4. Verify Master LUFS Audit
    assert manifest["lufs_audit"]["status"] == "PASSED"
    assert abs(manifest["lufs_audit"]["measured_lufs"] - (-7.0)) <= 1.5

    # 5. Verify Section Automations Manifest
    assert "section_automations" in manifest
    assert manifest["section_automations"].get("status") == "SUCCESS"
    assert manifest["section_automations"].get("applied_count", 0) > 0

    # 6. Verify Incremental Audits Recorded
    assert "incremental_audits" in manifest
    assert len(manifest["incremental_audits"]) == len(recipe.tracks)


def test_unlisted_device_bypass_and_acoustic_self_healing():
    """
    Verifies that:
    1. Unlisted devices on a track are automatically bypassed (Device On = 0.0).
    2. Acoustic self-healing recovers a silent track by disabling choking secondary plugins.
    """
    conn = MockAbletonConnection()

    # Configure track 4 with Vital (dev 0) and an unlisted rogue device (dev 1)
    conn.tracks_data[4] = {
        "name": "Sub Bass - Vital",
        "volume": 0.82,
        "output_meter_level": 0.00,  # Initially silent due to rogue device
        "devices": [
            {"name": "Vital"},
            {"name": "Unlisted Rogue Device"}
        ]
    }

    # Simulate that when Device 1 is turned off, the meter level jumps to 0.75
    original_send = conn.send_command
    def reactive_send_command(cmd, params=None):
        params = params or {}
        if cmd == "set_device_parameter":
            t_idx = params.get("track_index")
            d_idx = params.get("device_index")
            param = params.get("parameter")
            val = params.get("value")
            if t_idx == 4 and d_idx == 1 and param == "Device On" and val == 0.0:
                conn.tracks_data[4]["output_meter_level"] = 0.75
        return original_send(cmd, params)

    conn.send_command = reactive_send_command

    recipe = ProductionRecipe(
        title="Self Healing Test Recipe",
        genre_reference="Bass Test",
        bpm=82.0,
        key="Eb",
        scale="major",
        chord_progression=["Eb"],
        tracks=[
            TrackBlueprint(
                track_index=4,
                name="Sub Bass - Vital",
                role="bass",
                instrument_name="Vital",
                instrument_uri="query:Plugins#VST3:Vital%20Audio:Vital",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 4.0, "velocity": 100}],
                effects=[]  # Unlisted rogue device should be turned OFF
            )
        ],
        sections=[],
        target_lufs=-7.0,
        max_true_peak=-0.5
    )

    manifest = ProductionRecipeEngine.execute_physical_recipe(conn, recipe)

    # Verify unlisted device on track 4 was turned off
    off_commands = [
        c for c in conn.commands_sent
        if c["cmd"] == "set_device_parameter"
        and c["params"].get("track_index") == 4
        and c["params"].get("device_index") == 1
        and c["params"].get("parameter") == "Device On"
        and c["params"].get("value") == 0.0
    ]
    assert len(off_commands) >= 1, "Dispositivo no listado en pista 4 debe recibir Device On = 0.0"

    # Verify acoustic recovery and success status
    assert manifest["status"] == "SUCCESS"
    assert manifest["acoustic_meters"][4]["level"] >= 0.001


def test_audit_incremental_addition_silent_signal():
    """
    Confirms audit_incremental_addition correctly identifies inaudible signal (< 0.001),
    labels it INAUDIBLE_SILENT with CRITICAL severity, and provides an actionable AI decision menu.
    """
    conn = MockAbletonConnection()
    conn.tracks_data[5] = {
        "name": "Silent Synth",
        "volume": 0.85,
        "output_meter_level": 0.0000,
        "devices": []
    }

    audit = ProductionRecipeEngine.audit_incremental_addition(
        conn=conn,
        track_index=5,
        role="lead",
        event_description="Adición de sintetizador de prueba",
        settle_time=0.0
    )

    assert audit["track_status"] == "INAUDIBLE_SILENT"
    assert audit["severity"] == "CRITICAL"
    assert audit["track_meter_level"] < 0.001
    assert "¡ALERTA CRÍTICA DE SILENCIO!" in audit["engine_advisory"]
    assert "ai_decision_menu" in audit
    assert "TRIM_FADER" in audit["ai_decision_menu"]
    assert "ADJUST_VST_GAIN" in audit["ai_decision_menu"]
    assert "APPLY_FILTER_EQ" in audit["ai_decision_menu"]
    assert "ACCEPT_AND_PROCEED" in audit["ai_decision_menu"]


def test_audit_incremental_addition_too_loud():
    """
    Confirms audit_incremental_addition correctly identifies excessive volume (> category max),
    labels it TOO_HOT, and provides calculated fader trim recommendations.
    """
    conn = MockAbletonConnection()
    # Lead range is [0.20, 0.65], setting to 0.82
    conn.tracks_data[13] = {
        "name": "Overloaded Lead",
        "volume": 0.85,
        "output_meter_level": 0.82,
        "devices": [{"name": "Serum 2"}]
    }

    audit = ProductionRecipeEngine.audit_incremental_addition(
        conn=conn,
        track_index=13,
        role="lead",
        event_description="Prueba de volumen excesivo",
        settle_time=0.0
    )

    assert audit["track_status"] == "TOO_HOT"
    assert audit["severity"] == "MEDIUM"
    assert audit["track_meter_level"] == 0.82
    assert audit["category"] == "LEAD"
    fader_option = audit["ai_decision_menu"]["TRIM_FADER"]
    assert fader_option["target_volume"] < 0.85, "El volumen recomendado debe ser menor al actual"


def test_audit_incremental_addition_optimal():
    """
    Confirms audit_incremental_addition correctly classifies signals within category limits as OPTIMAL.
    """
    conn = MockAbletonConnection()
    # Bass range is [0.30, 0.75], setting to 0.48
    conn.tracks_data[4] = {
        "name": "Sub Bass",
        "volume": 0.80,
        "output_meter_level": 0.48,
        "devices": [{"name": "Vital"}]
    }

    audit = ProductionRecipeEngine.audit_incremental_addition(
        conn=conn,
        track_index=4,
        role="bass",
        event_description="Prueba de nivel óptimo",
        settle_time=0.0
    )

    assert audit["track_status"] == "OPTIMAL"
    assert audit["severity"] == "NONE"
    assert "bolsillo acústico ideal" in audit["engine_advisory"]


def test_execute_ai_loudness_decision_fader_trim():
    """
    Confirms execute_ai_loudness_decision executes TRIM_FADER via set_track_volume command.
    """
    conn = MockAbletonConnection()
    conn.tracks_data[13] = {
        "name": "Lead",
        "volume": 0.85,
        "output_meter_level": 0.80,
        "devices": []
    }

    audit = ProductionRecipeEngine.audit_incremental_addition(
        conn=conn,
        track_index=13,
        role="lead",
        event_description="Evaluación de lead",
        settle_time=0.0
    )

    result = ProductionRecipeEngine.execute_ai_loudness_decision(
        conn=conn,
        audit_result=audit,
        decision_key="TRIM_FADER"
    )

    assert result["executed"] is True
    assert conn.tracks_data[13]["volume"] == result["new_volume"]
    assert conn.tracks_data[13]["volume"] < 0.85


def test_get_section_automation_menu():
    """
    Confirms get_section_automation_menu analyzes transitions (Pre-Chorus -> Chorus, Chorus -> Outro)
    and generates candidate curves (Filter Riser, Reverb Washout, Sub Vacuum, Filter Down).
    """
    recipe = ProductionRecipe(
        title="Automation Test Recipe",
        genre_reference="Test Genre",
        bpm=120.0,
        key="C",
        scale="minor",
        chord_progression=["Cm", "Ab", "Fm", "G7"],
        tracks=[
            TrackBlueprint(
                track_index=1,
                name="Lead Synth",
                role="lead",
                instrument_name="Serum 2",
                instrument_uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
                clip_notes=[{"pitch": 72, "start_time": 0.0, "duration": 2.0, "velocity": 90}]
            ),
            TrackBlueprint(
                track_index=2,
                name="Sub Bass",
                role="bass",
                instrument_name="Vital",
                instrument_uri="query:Plugins#VST3:Vital%20Audio:Vital",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 4.0, "velocity": 100}]
            )
        ],
        sections=[
            RecipeSection(name="1. Pre-Chorus", start_bar=16, length_bars=8, active_roles=["lead", "bass"]),
            RecipeSection(name="2. Chorus", start_bar=24, length_bars=16, active_roles=["lead", "bass"]),
            RecipeSection(name="3. Outro", start_bar=40, length_bars=8, active_roles=["lead"])
        ]
    )

    menu = ProductionRecipeEngine.get_section_automation_menu(recipe)
    assert menu["total_candidates"] > 0
    candidate_types = [c["type"] for c in menu["available_automations"]]
    assert "FILTER_SWEEP_UP" in candidate_types
    assert "SUB_CLEANUP" in candidate_types
    assert "FILTER_SWEEP_DOWN" in candidate_types

    # Verify points were generated with positive durations and timestamps
    for cand in menu["available_automations"]:
        assert len(cand["points"]) >= 2
        assert cand["points"][-1]["time"] > cand["points"][0]["time"]


def test_apply_section_automations():
    """
    Confirms apply_section_automations injects arrangement envelopes via create_arrangement_automation_envelope.
    """
    conn = MockAbletonConnection()
    automations = [
        {
            "id": "test_filter_riser",
            "track_index": 1,
            "parameter_name": "Cutoff",
            "device_index": 0,
            "points": [
                {"time": 64.0, "value": 0.20},
                {"time": 80.0, "value": 0.70},
                {"time": 96.0, "value": 0.95}
            ]
        }
    ]

    manifest = ProductionRecipeEngine.apply_section_automations(conn, automations)
    assert manifest["status"] == "SUCCESS"
    assert manifest["applied_count"] == 1

    auto_cmds = [c for c in conn.commands_sent if c["cmd"] == "create_arrangement_automation_envelope"]
    assert len(auto_cmds) == 1
    assert auto_cmds[0]["params"]["track_index"] == 1
    assert auto_cmds[0]["params"]["parameter"] == "Cutoff"
    assert len(auto_cmds[0]["params"]["points"]) == 3


def test_arrangement_missing_clips_assertion():
    """
    Confirms the engine strictly raises ArrangementMissingClipsError if any track
    with notes has 0 clips in the Arrangement view timeline.
    """
    conn = MockAbletonConnection()
    # Override get_arrangement_clips to return 0 clips
    def mock_send(cmd: str, params: Dict[str, Any] = None):
        params = params or {}
        if cmd == "get_arrangement_clips":
            return {"track_index": params.get("track_index", 0), "clip_count": 0, "clips": []}
        return conn.send_command(cmd, params)

    class CustomMock(MockAbletonConnection):
        def send_command(self, cmd: str, params: Dict[str, Any] = None):
            params = params or {}
            if cmd == "get_arrangement_clips":
                return {"track_index": params.get("track_index", 0), "clip_count": 0, "clips": []}
            return super().send_command(cmd, params)

    bad_conn = CustomMock()
    recipe = ProductionRecipe(
        title="Test Recipe",
        genre_reference="Trap",
        bpm=140.0,
        key="C",
        scale="minor",
        chord_progression=["Cm"],
        tracks=[
            TrackBlueprint(
                track_index=1,
                name="Test Lead",
                role="lead",
                instrument_name="Serum 2",
                clip_notes=[{"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100}]
            )
        ]
    )

    with pytest.raises(ArrangementMissingClipsError):
        ProductionRecipeEngine.execute_physical_recipe(bad_conn, recipe)


def test_zomboy_brostep_recipe_and_0_to_100_flow():
    """
    Confirms the Zomboy Heavy Brostep recipe is properly structured and successfully executes
    through the authoritative engine 0-to-100 pipeline.
    """
    conn = MockAbletonConnection()
    recipe = ProductionRecipeEngine.build_zomboy_brostep_recipe()
    assert recipe.bpm == 145.0
    assert recipe.key == "F"
    assert len(recipe.tracks) == 8
    assert len(recipe.sections) == 6

    # Verify track roles
    roles = [t.role for t in recipe.tracks]
    assert "drums" in roles
    assert "growl" in roles
    assert "lead" in roles
    assert "bass" in roles
    assert "pad" in roles
    assert "master" in roles

    manifest = ProductionRecipeEngine.produce_zomboy_full_song_0_to_100(conn)
    assert manifest["status"] in ("SUCCESS", "SILENCE_WARNING")
    assert "arrangement_clips_verified" in manifest
    # Verify arrangement clips were recorded
    for t_idx in (2, 4, 5, 6, 10, 12, 15):
        assert t_idx in manifest["arrangement_clips_verified"]
        assert manifest["arrangement_clips_verified"][t_idx]["clip_count"] > 0




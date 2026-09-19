# tests/test_physical_sidechain_and_mastering.py
"""
Unit and Integration tests for:
- Physical Sidechain Routing (Kick -> Bass) integrated into ProductionRecipeEngine.
- 5-stage Native Mastering Chain (EQ Eight, Glue Compressor, Saturator, Utility, Limiter)
  integrated into ProductionRecipeEngine.
- Configurable activation and non-destructive execution.
"""

import pytest
from typing import Dict, Any, List

from engine.production.recipe_engine import (
    ProductionRecipeEngine,
    TrackBlueprint,
    RecipeSection,
    ProductionRecipe
)


class MockLiveMasteringConnection:
    """Mock connection that tracks devices, parameters, and sidechain routing."""

    def __init__(self):
        self.commands_sent: List[Dict[str, Any]] = []
        self.track_devices: Dict[int, List[Dict[str, str]]] = {
            2: [{"name": "Drum Rack"}],
            6: [{"name": "Vital"}],
            17: []  # Premaster / Master bus track
        }
        self.set_params: List[Dict[str, Any]] = []

    def send_command(self, cmd_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        self.commands_sent.append({"type": cmd_type, "params": params})

        if cmd_type == "get_session_info":
            return {"result": {"tempo": 128.0, "track_count": 18}}

        elif cmd_type == "get_track_info":
            t_idx = params.get("track_index", 0)
            devs = self.track_devices.get(t_idx, [{"name": "Serum 2"}])
            return {
                "result": {
                    "index": t_idx,
                    "name": f"Track {t_idx}",
                    "is_audio_track": False,
                    "is_midi_track": True,
                    "devices": devs,
                    "output_meter_level": 0.40,
                    "clip_slots": [{"has_clip": True}]
                }
            }

        elif cmd_type in ("load_instrument_or_effect", "load_browser_item"):
            t_idx = params.get("track_index", 0)
            uri = params.get("item_uri") or params.get("uri", "")
            d_name = "Device"
            if "Compressor" in uri and "Glue" not in uri:
                d_name = "Compressor"
            elif "Glue%20Compressor" in uri:
                d_name = "Glue Compressor"
            elif "EQ%20Eight" in uri:
                d_name = "EQ Eight"
            elif "Saturator" in uri:
                d_name = "Saturator"
            elif "Utility" in uri:
                d_name = "Utility"
            elif "Limiter" in uri:
                d_name = "Limiter"
            elif "FileId_5422" in uri or "808" in uri:
                d_name = "808 Core Kit"
            
            if t_idx not in self.track_devices:
                self.track_devices[t_idx] = []
            self.track_devices[t_idx].append({"name": d_name, "uri": uri})
            return {"status": "success", "result": {"loaded": True, "item_name": d_name}}

        elif cmd_type == "get_drum_rack_pads":
            return {
                "result": {
                    "active_pad_count": 16,
                    "pads": [{"note": 36 + i, "name": f"Pad {i}"} for i in range(16)]
                }
            }

        elif cmd_type == "get_arrangement_clips":
            return {
                "result": {
                    "track_index": params.get("track_index", 0),
                    "clip_count": 4,
                    "clips": [{"name": "Clip", "start_time": 0.0, "end_time": 16.0}]
                }
            }

        elif cmd_type == "set_device_parameter":
            self.set_params.append(params)
            return {"status": "success", "result": {"updated": True}}

        elif cmd_type == "execute_code":
            code = params.get("code", "")
            import re
            t_m = re.search(r"song\.tracks\[(\d+)\]", code)
            curr_t = int(t_m.group(1)) if t_m else 0
            for line in code.splitlines():
                p_m = re.search(r"devices\[(\d+)\]\.parameters\[(\d+)\]\.value\s*=\s*([0-9.]+)", line)
                if p_m:
                    self.set_params.append({
                        "track_index": curr_t,
                        "device_index": int(p_m.group(1)),
                        "parameter": int(p_m.group(2)),
                        "value": float(p_m.group(3))
                    })
            return {"status": "success", "result": "ok"}

        elif cmd_type in ("create_clip", "delete_clip", "add_notes_to_clip", "set_clip_name",
                          "create_cue_point", "duplicate_session_clip_to_arrangement",
                          "start_playback", "stop_playback", "set_current_song_time", "fire_clip",
                          "switch_to_arrangement_view"):
            return {"status": "success", "result": {}}

        return {"status": "success", "result": {}}


def test_recipe_engine_physical_sidechain_kick_to_bass():
    """Verifies that execute_physical_recipe detects Kick & Bass and configures native sidechain."""
    conn = MockLiveMasteringConnection()

    recipe = ProductionRecipe(
        title="Sidechain Test Song",
        genre_reference="EDM / Club",
        bpm=128.0,
        key="F Minor",
        scale="Minor",
        chord_progression=["i", "VI", "III", "VII"],
        tracks=[
            TrackBlueprint(
                track_index=2,
                name="Kick Drums",
                role="drums",
                instrument_name="Drum Rack",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 120}]
            ),
            TrackBlueprint(
                track_index=6,
                name="808 Sub Bass",
                role="bass",
                instrument_name="Vital",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 2.0, "velocity": 100}]
            )
        ],
        sections=[RecipeSection(name="1. Drop", start_bar=0, length_bars=4, active_roles=["drums", "bass"])],
        enable_sidechain=True,
        enable_mastering_chain=False,
        total_bars=4
    )

    manifest = ProductionRecipeEngine.execute_physical_recipe(conn, recipe)

    # 1. Verify sidechain manifest
    assert "sidechain" in manifest
    sc = manifest["sidechain"]
    assert sc["status"] == "SUCCESS"
    assert sc["bass_track_index"] == 6
    assert sc["kick_track_index"] == 2
    assert sc["sidechain_active"] is True

    # 2. Verify compressor was loaded onto Bass track (track 6)
    dev_names = [d["name"] for d in conn.track_devices.get(6, [])]
    assert "Compressor" in dev_names

    # 3. Verify sidechain parameterization (Attack=0.0, S/C On=1.0, etc.)
    bass_param_changes = [p for p in conn.set_params if p.get("track_index") == 6]
    assert len(bass_param_changes) >= 5
    param_dict = {p.get("parameter"): p.get("value") for p in bass_param_changes}
    assert param_dict.get(0) == 1.0   # Device On
    assert param_dict.get(20) == 1.0  # S/C On
    assert param_dict.get(4) == 0.0   # Attack (0.01 ms clamp)
    assert param_dict.get(2) == 0.75  # Ratio (4:1)


def test_recipe_engine_5_stage_mastering_chain():
    """Verifies that execute_physical_recipe deploys full native 5-stage mastering chain."""
    conn = MockLiveMasteringConnection()

    recipe = ProductionRecipe(
        title="Mastering Chain Test Song",
        genre_reference="Club Festival",
        bpm=128.0,
        key="G Minor",
        scale="Minor",
        chord_progression=["i", "iv", "v", "i"],
        tracks=[
            TrackBlueprint(
                track_index=2,
                name="Drums",
                role="drums",
                clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 120}]
            ),
            TrackBlueprint(
                track_index=17,
                name="Premaster Bus",
                role="master"
            )
        ],
        sections=[RecipeSection(name="1. Drop", start_bar=0, length_bars=4, active_roles=["all"])],
        enable_sidechain=False,
        enable_mastering_chain=True,
        master_bus_track_index=17,
        target_lufs=-8.0,
        total_bars=4
    )

    manifest = ProductionRecipeEngine.execute_physical_recipe(conn, recipe)

    # 1. Verify mastering chain manifest
    assert "mastering_chain" in manifest
    mc = manifest["mastering_chain"]
    assert mc["status"] == "SUCCESS"
    assert mc["track_index"] == 17
    assert mc["target_profile"] == "CLUB"
    assert mc["target_lufs"] == -9.0

    # 2. Verify all 5 devices were loaded onto track 17
    dev_names = [d["name"] for d in conn.track_devices.get(17, [])]
    assert "EQ Eight" in dev_names
    assert "Glue Compressor" in dev_names
    assert "Saturator" in dev_names
    assert "Utility" in dev_names
    assert "Limiter" in dev_names

    # 3. Verify parameters applied to mastering track
    m_params = [p for p in conn.set_params if p.get("track_index") == 17]
    assert len(m_params) > 10


def test_sidechain_and_mastering_disabled_flags():
    """Verifies that disabling flags bypasses steps cleanly without error."""
    conn = MockLiveMasteringConnection()

    recipe = ProductionRecipe(
        title="Bypass Test Song",
        genre_reference="Acoustic Folk",
        bpm=90.0,
        key="C Major",
        scale="Major",
        chord_progression=["I", "IV", "V", "I"],
        tracks=[
            TrackBlueprint(track_index=2, name="Kick", role="drums", clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 90}]),
            TrackBlueprint(track_index=6, name="Bass", role="bass", clip_notes=[{"pitch": 48, "start_time": 0.0, "duration": 1.0, "velocity": 90}])
        ],
        sections=[RecipeSection(name="1. Verse", start_bar=0, length_bars=4, active_roles=["drums", "bass"])],
        enable_sidechain=False,
        enable_mastering_chain=False,
        total_bars=4
    )

    manifest = ProductionRecipeEngine.execute_physical_recipe(conn, recipe)
    assert "sidechain" not in manifest
    assert "mastering_chain" not in manifest

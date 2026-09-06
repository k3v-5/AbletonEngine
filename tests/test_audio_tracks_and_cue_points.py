# tests/test_audio_tracks_and_cue_points.py
"""
Unit and Integration tests for:
- Procedural Audio Sample Generation (Vocal formants, foley bed, impact, riser).
- Audio Track Blueprint specification and sample resolution.
- Live Arrangement Cue Points (Locators) creation on section boundaries.
- Density Staging: selective Arrangement deployment based on active_roles.
- Vocal Staging & multitrack ducking coordination.
"""

import os
import wave
import pytest
from pathlib import Path
from typing import Dict, Any, List

from engine.audio.sample_generator import ProceduralSampleGenerator
from engine.production.recipe_engine import (
    ProductionRecipeEngine,
    TrackBlueprint,
    RecipeSection,
    ProductionRecipe
)


class MockLiveConnection:
    """Mock Ableton socket connection recording all commands sent."""

    def __init__(self):
        self.commands_sent: List[Dict[str, Any]] = []
        self.cue_points: List[Dict[str, Any]] = []
        self.arrangement_clips: List[Dict[str, Any]] = []
        self.warp_modes: Dict[int, int] = {}

    def send_command(self, cmd_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        self.commands_sent.append({"type": cmd_type, "params": params})

        if cmd_type == "get_session_info":
            return {"result": {"tempo": 120.0, "track_count": 18}}

        elif cmd_type == "get_track_info":
            t_idx = params.get("track_index", 0)
            is_audio = t_idx in (12, 15)
            return {
                "result": {
                    "index": t_idx,
                    "name": f"Track {t_idx}",
                    "is_audio_track": is_audio,
                    "is_midi_track": not is_audio,
                    "devices": [{"name": "Serum 2"}] if not is_audio else [],
                    "output_meter_level": 0.35,
                    "clip_slots": [{"has_clip": True}]
                }
            }

        elif cmd_type == "create_cue_point":
            self.cue_points.append(params)
            return {"status": "success", "action": "created", "name": params.get("name"), "time": params.get("time")}

        elif cmd_type == "create_audio_clip":
            return {"status": "success", "result": {"name": "Audio Clip", "length": 16.0, "is_audio_clip": True}}

        elif cmd_type == "set_clip_warp_mode":
            t_idx = params.get("track_index", 0)
            m = params.get("mode", 4)
            self.warp_modes[t_idx] = m
            return {"status": "success", "result": {"warp_mode": m, "warping": True}}

        elif cmd_type == "duplicate_session_clip_to_arrangement":
            self.arrangement_clips.append(params)
            return {"status": "success", "result": {"success": True}}

        elif cmd_type == "get_arrangement_clips":
            t_idx = params.get("track_index", 0)
            matching = [c for c in self.arrangement_clips if c.get("track_index") == t_idx]
            return {"status": "success", "result": {"track_index": t_idx, "clip_count": len(matching) if matching else 1, "clips": matching}}

        elif cmd_type == "get_drum_rack_pads":
            return {"status": "success", "result": {"active_pad_count": 16, "pads": []}}

        elif cmd_type == "create_arrangement_automation_envelope":
            return {"status": "success", "result": {"envelope_injected": True}}

        return {"status": "success", "result": {}}


def test_procedural_sample_generator_vocal_and_foley(tmp_path):
    """Verifies procedural synthesis of vocal formant WAV and foley bed."""
    vocal_path = str(tmp_path / "test_vocal.wav")
    foley_path = str(tmp_path / "test_foley.wav")

    res_vocal = ProceduralSampleGenerator.generate_sample("vocal", output_path=vocal_path, duration_sec=1.5)
    assert os.path.exists(res_vocal)
    assert os.path.getsize(res_vocal) > 1000

    with wave.open(res_vocal, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 44100
        assert wf.getnframes() == int(44100 * 1.5)

    res_foley = ProceduralSampleGenerator.generate_sample("foley", output_path=foley_path, duration_sec=1.0)
    assert os.path.exists(res_foley)
    with wave.open(res_foley, "rb") as wf:
        assert wf.getnframes() == 44100


def test_track_blueprint_audio_attributes_and_resolution(tmp_path):
    """Verifies TrackBlueprint with is_audio=True and automatic sample resolution."""
    tb = TrackBlueprint(
        track_index=12,
        name="Lead Vocal",
        role="vocal",
        is_audio=True,
        warp_mode="complex",
        clip_gain=0.92,
        pitch_coarse=-2,
        procedural_sample_type="vocal"
    )
    assert tb.is_audio is True
    assert tb.warp_mode == "complex"
    assert tb.clip_gain == 0.92
    assert tb.pitch_coarse == -2

    # Resolve sample path
    sample_file = ProductionRecipeEngine.resolve_audio_sample(tb)
    assert os.path.exists(sample_file)
    assert sample_file.endswith(".wav")


def test_execute_physical_recipe_cue_points_and_density_staging():
    """
    Verifies that execute_physical_recipe:
    1. Instantiates physical Cue Points in Live for every section.
    2. Enforces density staging (only duplicating clips when track role is active in that section).
    3. Handles audio tracks and sets complex warp mode.
    4. Coordinates vocal staging when vocal role is present.
    """
    mock_conn = MockLiveConnection()

    tracks = [
        TrackBlueprint(
            track_index=4,
            name="Serum Lead",
            role="lead",
            instrument_name="Serum 2",
            clip_notes=[{"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 100}],
            is_audio=False
        ),
        TrackBlueprint(
            track_index=6,
            name="Sub Bass",
            role="bass",
            instrument_name="Vital",
            clip_notes=[{"pitch": 36, "start_time": 0.0, "duration": 2.0, "velocity": 110}],
            is_audio=False
        ),
        TrackBlueprint(
            track_index=12,
            name="Lead Vocal Audio",
            role="vocal",
            is_audio=True,
            warp_mode="complex",
            clip_gain=0.88,
            pitch_coarse=0,
            procedural_sample_type="vocal"
        )
    ]

    # 4 Sections with distinct active roles
    sections = [
        RecipeSection(name="1. Intro", start_bar=0, length_bars=4, active_roles=["lead"]),
        RecipeSection(name="2. Verse", start_bar=4, length_bars=4, active_roles=["bass", "vocal"]),
        RecipeSection(name="3. Chorus", start_bar=8, length_bars=4, active_roles=["all"]),
        RecipeSection(name="4. Outro", start_bar=12, length_bars=4, active_roles=["lead"])
    ]

    recipe = ProductionRecipe(
        title="Test Density & Audio Production",
        genre_reference="Commercial Trap / Pop",
        bpm=130.0,
        key="C Minor",
        scale="Minor",
        chord_progression=["i", "VI", "III", "VII"],
        tracks=tracks,
        sections=sections,
        total_bars=16
    )

    manifest = ProductionRecipeEngine.execute_physical_recipe(mock_conn, recipe)

    # 1. Verify Cue Points
    cue_commands = [c for c in mock_conn.commands_sent if c["type"] == "create_cue_point"]
    assert len(cue_commands) == 4
    cue_names = [c["params"]["name"] for c in cue_commands]
    cue_times = [c["params"]["time"] for c in cue_commands]
    assert cue_names == ["1. Intro", "2. Verse", "3. Chorus", "4. Outro"]
    assert cue_times == [0.0, 16.0, 32.0, 48.0]

    # 2. Verify Audio Clip Loading on Track 12
    audio_clip_cmds = [c for c in mock_conn.commands_sent if c["type"] == "create_audio_clip"]
    assert len(audio_clip_cmds) == 1
    assert audio_clip_cmds[0]["params"]["track_index"] == 12
    assert os.path.exists(audio_clip_cmds[0]["params"]["path"])

    # 3. Verify Warp Mode set to Complex (4)
    assert mock_conn.warp_modes.get(12) == 4

    # 4. Verify Density Staging (Arrangement musical clip placement per track)
    # Track 4 (Lead): Active in Intro (bar 0=beat 0), Chorus (bar 8=beat 32), Outro (bar 12=beat 48). Musical clip ONLY when active!
    lead_musical_clips = [c for c in mock_conn.arrangement_clips if c["track_index"] == 4 and c.get("clip_index") == 0]
    lead_musical_times = [c["destination_time"] for c in lead_musical_clips]
    assert 0.0 in lead_musical_times   # Intro (active)
    assert 16.0 not in lead_musical_times  # Verse (MUSICAL CLIP MUST BE ABSENT)
    assert 32.0 in lead_musical_times  # Chorus (active)
    assert 48.0 in lead_musical_times  # Outro (active)

    # Track 6 (Bass): Active in Verse (bar 4=beat 16) and Chorus (bar 8=beat 32). Musical clip ONLY when active!
    bass_musical_clips = [c for c in mock_conn.arrangement_clips if c["track_index"] == 6 and c.get("clip_index") == 0]
    bass_musical_times = [c["destination_time"] for c in bass_musical_clips]
    assert 0.0 not in bass_musical_times   # Intro (MUST BE ABSENT)
    assert 16.0 in bass_musical_times      # Verse (active)
    assert 32.0 in bass_musical_times      # Chorus (active)
    assert 48.0 not in bass_musical_times  # Outro (MUST BE ABSENT)

    # Track 12 (Vocal Audio): Active in Verse and Chorus. Silent in Intro and Outro!
    vocal_clips = [c for c in mock_conn.arrangement_clips if c["track_index"] == 12]
    vocal_times = [c["destination_time"] for c in vocal_clips]
    assert 0.0 not in vocal_times  # Intro (SILENT)
    assert 16.0 in vocal_times     # Verse
    assert 32.0 in vocal_times     # Chorus
    assert 48.0 not in vocal_times # Outro (SILENT)

    # 5. Verify Vocal Staging Coordination in Manifest
    assert "vocal_staging" in manifest
    assert manifest["vocal_staging"]["status"] == "SUCCESS"
    assert "vocal_staging_applied" in manifest

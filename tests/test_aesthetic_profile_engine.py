# tests/test_aesthetic_profile_engine.py
"""
Unit and integration tests for AestheticProfileEngine:
- Zero default chain assumption policy
- Standardized structured queries for unknown genres
- Learning and persistence to state/learned/aesthetic_profiles.json
- Mandatory vs Optional effect classification
- Instrument decision documentation and retrieval
- CopilotGuidedSession Phase 5 integration
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from engine.fx.aesthetic_profile_engine import (
    AestheticProfileEngine,
    AestheticGenreProfile,
    RoleFXProfile,
    InstrumentDecision
)
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.adapters.mock_adapter import MockAbletonAdapter


@pytest.fixture
def temp_profiles_file(tmp_path):
    return tmp_path / "learned_profiles.json"


def test_seed_profiles_initialization(temp_profiles_file):
    """Validates that seed profiles (trap, edm, techno) are automatically available."""
    engine = AestheticProfileEngine(profiles_path=temp_profiles_file)
    assert engine.has_profile("trap")
    assert engine.has_profile("edm")
    assert engine.has_profile("techno")

    trap_prof = engine.get_profile("trap")
    assert trap_prof is not None
    assert "DRUMS" in trap_prof.roles
    assert "EQ Eight" in trap_prof.roles["DRUMS"].mandatory_effects
    assert "Saturator" in trap_prof.roles["DRUMS"].optional_effects


def test_unknown_genre_detection_and_query_schema(temp_profiles_file):
    """Validates that an unprofiled genre generates the standardized query schema."""
    engine = AestheticProfileEngine(profiles_path=temp_profiles_file)
    assert not engine.has_profile("hyperpop_cyberpunk")

    query = engine.build_standardized_genre_query("hyperpop_cyberpunk")
    assert query["status"] == "AESTHETIC_PROFILE_REQUIRED"
    assert "schema_expected" in query
    assert "DRUMS" in query["schema_expected"]
    assert "mandatory" in query["schema_expected"]["DRUMS"]
    assert "optional" in query["schema_expected"]["DRUMS"]
    assert "hyperpop_cyberpunk" in query["question"].lower()


def test_register_and_persist_new_genre_profile(temp_profiles_file):
    """Validates that receiving a new genre configuration registers and persists it to disk."""
    engine = AestheticProfileEngine(profiles_path=temp_profiles_file)

    input_json = {
        "display_name": "Hyperpop Cyberpunk",
        "aesthetic_notes": "Glitchy, distorted, heavy bitcrush and bright hyper-compressed vocals.",
        "roles": {
            "DRUMS": {
                "mandatory": ["EQ Eight", "Redux", "Glue Compressor"],
                "optional": ["Saturator", "Overdrive"]
            },
            "BASS": {
                "mandatory": ["EQ Eight", "Utility"],
                "optional": ["Saturator", "Overdrive"]
            },
            "LEAD": {
                "mandatory": ["EQ Eight", "Compressor"],
                "optional": ["Delay", "ValhallaVintageVerb", "Redux"]
            },
            "VOCALS": {
                "mandatory": ["EQ Eight", "Auto-Tune Artist", "Compressor"],
                "optional": ["ValhallaVintageVerb", "MicroShift"]
            }
        }
    }

    parsed = engine.parse_standardized_genre_input("hyperpop_cyberpunk", input_json)
    assert parsed is not None
    assert engine.has_profile("hyperpop_cyberpunk")
    assert temp_profiles_file.exists()

    # Verify reloading from disk preserves the learned profile
    engine2 = AestheticProfileEngine(profiles_path=temp_profiles_file)
    assert engine2.has_profile("hyperpop_cyberpunk")
    loaded = engine2.get_profile("hyperpop_cyberpunk")
    assert "Redux" in loaded.roles["DRUMS"].mandatory_effects
    assert "Auto-Tune Artist" in loaded.roles["VOCALS"].mandatory_effects
    assert "Overdrive" in loaded.roles["BASS"].optional_effects


def test_document_and_retrieve_novel_instrument_decision(temp_profiles_file):
    """Validates documenting decisions on new instruments and retrieving them later."""
    engine = AestheticProfileEngine(profiles_path=temp_profiles_file)

    decision = engine.document_instrument_decision(
        genre="trap",
        instrument_name="Moog Sub 37 Lead Pluck",
        role="LEAD",
        effects_added=["EQ Eight", "Saturator", "ValhallaVintageVerb"],
        configurations={"Drive": 0.45, "Decay": 1.2},
        reason="Warm analog bite with subtle room diffusion."
    )

    assert decision.instrument_name == "Moog Sub 37 Lead Pluck"
    assert "ValhallaVintageVerb" in decision.effects_added
    assert temp_profiles_file.exists()

    # Retrieve decision
    retrieved = engine.get_instrument_decision("trap", "Moog Sub 37 Lead Pluck")
    assert retrieved is not None
    assert retrieved.effects_added == ["EQ Eight", "Saturator", "ValhallaVintageVerb"]

    # Verify query prompt for this instrument reflects the past decision
    query = engine.build_track_fx_selection_query(
        track={"name": "Sub 37 Pluck", "role": "LEAD", "instrument": "Moog Sub 37 Lead Pluck"},
        genre="trap",
        track_index=2,
        total_tracks=6
    )
    assert "Decisión Histórica Documentada" in query["question"]
    assert "Moog Sub 37 Lead Pluck" in query["question"]


def test_track_fx_query_never_assumes_default_chains(temp_profiles_file):
    """Validates that track FX query enforces zero-default policy and clearly asks for choice."""
    engine = AestheticProfileEngine(profiles_path=temp_profiles_file)

    query = engine.build_track_fx_selection_query(
        track={"name": "Custom 808", "role": "BASS", "instrument": "SubLab XL"},
        genre="trap",
        track_index=1,
        total_tracks=5
    )
    assert query["status"] == "TRACK_FX_SELECTION_REQUIRED"
    assert "Cero Cadenas por Defecto" in query["question"]
    assert "Efectos Obligatorios" in query["question"]
    assert "Efectos Opcionales Disponibles" in query["question"]

    # Custom chain parsing
    custom_choice = engine.parse_track_fx_selection(
        user_input="Cadena: EQ Eight, Saturator, ValhallaVintageVerb",
        genre="trap",
        role="BASS",
        instrument="SubLab XL"
    )
    assert "EQ Eight" in custom_choice
    assert "Saturator" in custom_choice
    assert "ValhallaVintageVerb" in custom_choice


def test_copilot_phase_5_handles_new_genre_learning():
    """Integration test: CopilotGuidedSession pauses for unprofiled genre and registers it."""
    import uuid
    test_genre = f"test_genre_{uuid.uuid4().hex[:8]}"
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    session.data["genre"] = test_genre
    session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS", "instrument": "808 Core Kit"},
        {"index": 1, "name": "Bass", "role": "BASS", "instrument": "Vital Audio"}
    ]
    session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
    session.data["phase_index"] = 5
    session.data["current_fx_track_ptr"] = 0
    session.data["current_fx_dev_ptr"] = 0

    try:
        # 1. First step should detect unprofiled genre and request definition
        res_req = session.step(conn=adapter, user_input="")
        assert res_req.get("status") == "AESTHETIC_PROFILE_REQUIRED"
        assert "NUEVO GÉNERO DETECTADO" in res_req.get("question", "")

        # 2. Provide structured profile definition
        genre_def = json.dumps({
            "roles": {
                "DRUMS": {"mandatory": ["EQ Eight", "Glue Compressor"], "optional": ["Saturator"]},
                "BASS": {"mandatory": ["EQ Eight", "Utility"], "optional": ["Saturator", "Compressor"]}
            }
        })
        res_learned = session.step(conn=adapter, user_input=genre_def)
        assert session.data.get("aesthetic_profile_learned") == test_genre
        assert "pending_genre_aesthetic_profile" not in session.data
        # Now it proceeds into track effects
        assert "Paso 5 de 7" in res_learned.get("question", "")
    finally:
        # Clean up dynamic genre from disk
        engine = AestheticProfileEngine()
        if test_genre in engine._profiles:
            del engine._profiles[test_genre]
            engine.save_to_disk()

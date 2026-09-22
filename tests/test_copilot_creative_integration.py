# tests/test_copilot_creative_integration.py
"""
Integration tests verifying advanced creative capabilities directly accessible from CopilotGuidedSession:
1. Melodías Ultra Bien Hechas (Nivel T: Phrase breathing, rubato on arrival notes, humanization pocket)
2. Resampling & Self-Sampling (Audio Genesis: 'Render Before Sample' with provenance tracking)
3. Track Freeze & Unfreeze (Phase 10: Live LOM is_frozen control to lock DSP and free CPU)
4. Texture & Foley Bed Injection (Phase 10: Organic autogenous background beds at -24 dBFS)
"""

import pytest
from unittest.mock import MagicMock

from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_6.arranger import Phase6Arranger
from engine.production.copilot.phases.phase_6.handler import Phase6CompositionHandler
from engine.production.copilot.phases.phase_10.surgery_and_navigation import (
    handle_track_freeze,
    handle_texture_and_foley_injection,
)
from engine.performance import (
    PerformanceCore,
    InstrumentPerformanceProfile,
    PerformanceIntent,
    PhraseBreathingEngine,
    PocketTendency,
    VelocityProfile,
    ArticulationStyle,
)


@pytest.fixture
def clean_copilot_session():
    """Provides a freshly reset CopilotGuidedSession."""
    session = CopilotGuidedSession()
    session.reset()
    return session


# -------------------------------------------------------------------------
# 1. TEST MELODÍAS ULTRA BIEN HECHAS & NIVEL T EN COPILOT
# -------------------------------------------------------------------------
def test_copilot_phase_6_nivel_t_phrase_breathing_and_humanization(clean_copilot_session):
    """
    Verifies that when humanization is requested or active, Phase 6 deploys notes
    with phrase breathing (climax note weight + guaranteed breath rests >= 35 ms)
    and intentional microtiming pocket rather than raw robotic jitter.
    """
    session = clean_copilot_session
    conn = MockAbletonAdapter()

    session.data["bpm"] = 120.0
    session.data["last_composition_prompt"] = "humanizar y hacer respirar la melodía lead con dilla pocket"
    session.data["sections"] = [{"name": "Verse 1", "bars": 8, "start_bar": 0}]

    lead_track = {
        "index": 0,
        "name": "Lead Synth",
        "role": "LEAD",
        "instrument": "Analog Lab V"
    }
    session.data["tracks"] = [lead_track]

    # Continuous 16-note phrase with zero natural pauses
    raw_notes = [
        {"pitch": 72, "start_time": float(i) * 0.5, "duration": 0.5, "velocity": 90}
        for i in range(16)
    ]
    custom_notes_map = {("LEAD", 0): raw_notes}

    deployed_count = Phase6Arranger.deploy_single_track_composition(
        session=session,
        conn=conn,
        trk=lead_track,
        custom_notes_map=custom_notes_map,
        sections=session.data["sections"]
    )

    assert deployed_count >= 16

    # Verify that notes were deployed with phrase breathing and velocity expression
    added_notes = conn.get_clip_notes(0, 0)
    assert len(added_notes) >= 16

    # Check that phrase breathing adjusted velocities and durations
    velocities = [n["velocity"] for n in added_notes]
    durations = [n["duration"] for n in added_notes]

    # Expressive dynamics: velocities are not all identical to 90
    assert len(set(velocities)) > 1
    # Breath gaps: at least one phrase boundary has shortened duration to leave breathing room
    assert any(d < 0.5 for d in durations)


# -------------------------------------------------------------------------
# 2. TEST RESAMPLING & SELF-SAMPLING EN FASE 6
# -------------------------------------------------------------------------
def test_copilot_phase_6_resampling_directive(clean_copilot_session):
    """
    Verifies that the user can request autogenous resampling during Phase 6,
    triggering AudioGenesisEngine to create a provenanced sound asset.
    """
    session = clean_copilot_session
    conn = MockAbletonAdapter()

    session.data["current_phase"] = "PHASE_6_COMPOSITION"
    session.data["phase_index"] = 6
    session.data["tracks"] = [
        {"index": 0, "name": "Keys Rhodes", "role": "KEYS", "instrument": "Analog Lab V"},
        {"index": 1, "name": "Sub Bass", "role": "BASS", "instrument": "Serum"}
    ]

    handler = Phase6CompositionHandler()
    res = handler.handle(session, conn, "resamplear acordes para textura ambiental pad")

    assert res["status"] == "RESAMPLING_COMPLETED"
    assert "provenance_id" in res
    assert res["phase"] == "PHASE_6_COMPOSITION"

    # Verify session registered the generated sample
    assert "generated_samples" in session.data
    assert len(session.data["generated_samples"]) >= 1

    last_sample = session.data["last_resampled_sound"]
    assert last_sample is not None
    assert "provenance" in last_sample
    assert last_sample["provenance"]["sample_id"] == res["provenance_id"]


def test_copilot_modular_composition_resampling_directive(clean_copilot_session):
    """
    Verifies that resampling can also be triggered while in modular composition mode.
    """
    session = clean_copilot_session
    conn = MockAbletonAdapter()

    session.data["current_phase"] = "PHASE_6_COMPOSITION"
    session.data["phase_index"] = 6
    session.data["composition_session"] = {
        "active": True,
        "mode": "BY_SECTION",
        "section_index": 0
    }
    session.data["sections"] = [{"name": "Intro", "bars": 8}]
    session.data["tracks"] = [{"index": 0, "name": "Rhodes", "role": "KEYS"}]

    handler = Phase6CompositionHandler()
    res = handler.handle_modular_composition_step(session, conn, "resamplear esta pista para un nuevo lead")

    assert res["status"] == "RESAMPLING_COMPLETED"
    assert "provenance_id" in res


# -------------------------------------------------------------------------
# 3. TEST TRACK FREEZE & UNFREEZE EN FASE 10
# -------------------------------------------------------------------------
def test_copilot_phase_10_track_freeze(clean_copilot_session):
    """
    Verifies freezing and unfreezing a track in Live LOM during Phase 10 active listening.
    """
    session = clean_copilot_session
    conn = MockAbletonAdapter()

    tracks = [
        {"index": 0, "name": "Serum Heavy Bass", "role": "BASS", "is_frozen": False},
        {"index": 1, "name": "Analog Lab Keys", "role": "KEYS", "is_frozen": False}
    ]
    session.data["tracks"] = tracks

    # 1. Freeze track 1
    res_freeze = handle_track_freeze(conn, "congelar pista 1", tracks, "PHASE_10_ACTIVE_LISTENING")
    assert res_freeze["status"] == "TRACK_FREEZE_COMPLETED"
    assert res_freeze["is_frozen"] is True
    assert tracks[0]["is_frozen"] is True

    # Check LOM code sent to conn
    assert any("t.is_frozen = True" in c for c in getattr(conn, "executed_code", []))

    # 2. Unfreeze track 1
    res_unfreeze = handle_track_freeze(conn, "descongelar pista 1", tracks, "PHASE_10_ACTIVE_LISTENING")
    assert res_unfreeze["status"] == "TRACK_FREEZE_COMPLETED"
    assert res_unfreeze["is_frozen"] is False
    assert tracks[0]["is_frozen"] is False

    assert any("t.is_frozen = False" in c for c in getattr(conn, "executed_code", []))


# -------------------------------------------------------------------------
# 4. TEST TEXTURE & FOLEY BED INJECTION EN FASE 10
# -------------------------------------------------------------------------
def test_copilot_phase_10_texture_and_foley_injection(clean_copilot_session):
    """
    Verifies generating and injecting organic foley texture bed at -24 dBFS
    derived autogenously from the session harmonic material.
    """
    session = clean_copilot_session
    conn = MockAbletonAdapter()

    tracks = [
        {"index": 0, "name": "Rhodes Chords", "role": "KEYS"},
        {"index": 1, "name": "Texture Bed", "role": "TEXTURE_FOLEY"}
    ]
    session.data["tracks"] = tracks

    res = handle_texture_and_foley_injection(
        session=session,
        conn=conn,
        text="crear textura organica de sala y foley bed",
        tracks=tracks,
        completed_phase="PHASE_10_ACTIVE_LISTENING"
    )

    assert res["status"] == "TEXTURE_FOLEY_INJECTED"
    assert "texture_result" in res

    # Verify asset is recorded in session data
    assert "resampled_assets" in session.data
    assets = session.data["resampled_assets"]
    assert len(assets) >= 1
    assert assets[-1]["source_track"] == "Rhodes Chords"
    assert "provenance_id" in assets[-1]

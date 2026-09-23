# tests/test_pre_vocal_panning.py
"""
Unit and integration tests for Pre-Vocal Instrument Panning Evaluator:
Ensures instrument stereo field is evaluated and panned to avoid masking / collisions
and keep the center strictly clear for the vocal stage.
"""

import pytest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.mix.spatial_panning import InstrumentPanningEvaluator
from engine.production.copilot.guided_session import CopilotGuidedSession


@pytest.fixture
def mock_adapter():
    adapter = MockAbletonAdapter()
    while len(adapter.tracks) < 16:
        idx = len(adapter.tracks)
        adapter.tracks.append({
            "name": f"Track {idx}",
            "volume": 0.85,
            "panning": 0.0,
            "mute": False,
            "solo": False,
            "arm": False,
            "devices": []
        })
    return adapter


@pytest.fixture
def clean_session():
    gs = CopilotGuidedSession()
    gs.reset()
    return gs


def test_instrument_panning_evaluator_direct(mock_adapter):
    """Tests acoustic role classification, masking conflict detection and pan layout."""
    tracks = [
        {"index": 0, "name": "[DRUMS] 808 Core Kit", "role": "DRUMS", "panning": 0.0},
        {"index": 1, "name": "[BASS] Sub 808", "role": "BASS", "panning": 0.0},
        {"index": 2, "name": "[KEYS] Rhodes Chords", "role": "KEYS", "panning": 0.0},
        {"index": 3, "name": "[LEAD] Lead Synth Solo", "role": "LEAD", "panning": 0.0},
        {"index": 4, "name": "[PERC] Trap Hats", "role": "HI_HATS", "panning": 0.0},
        {"index": 12, "name": "[VOCALS] Lead Vocal", "role": "VOCALS", "panning": 0.0}
    ]

    audit = InstrumentPanningEvaluator.evaluate_session_panning(tracks, conn=mock_adapter)
    assert audit["status"] == "PANNING_AUDIT_COMPLETED"
    assert audit["has_masking_risk"] is True
    assert len(audit["conflicts"]) >= 2
    assert audit["center_clumping_tracks_count"] >= 3

    # Check that Kick, Sub, Vocals are Center
    directives_map = {d["track_index"]: d for d in audit["directives"]}
    assert directives_map[0]["recommended_pan"] == 0.0
    assert directives_map[1]["recommended_pan"] == 0.0
    assert directives_map[12]["recommended_pan"] == 0.0

    # Check complementary slotting: Keys L, Lead R, Hats R
    assert directives_map[2]["recommended_pan"] < 0  # Left (e.g. -0.24)
    assert directives_map[3]["recommended_pan"] > 0  # Right (e.g. +0.24)
    assert directives_map[4]["recommended_pan"] > 0  # Right (e.g. +0.16)

    # Test applying plan to Live adapter
    apply_res = InstrumentPanningEvaluator.apply_panning_plan(mock_adapter, audit["directives"])
    assert apply_res["status"] == "SUCCESS"
    assert apply_res["applied_count"] == 6

    # Verify adapter track states
    assert mock_adapter.tracks[2]["panning"] == directives_map[2]["recommended_pan"]
    assert mock_adapter.tracks[3]["panning"] == directives_map[3]["recommended_pan"]
    assert mock_adapter.tracks[12]["panning"] == 0.0


def test_pre_vocal_panning_intercept_in_vocal_workflow(clean_session, mock_adapter):
    """
    Validates that when the user triggers the vocal stage, if instruments are centered,
    the engine pauses, evaluates panning, and prompts the assistant with anti-masking options.
    """
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["tracks"] = [
        {"index": 0, "name": "[DRUMS] Core Kit", "role": "DRUMS", "panning": 0.0},
        {"index": 1, "name": "[BASS] Sub 808", "role": "BASS", "panning": 0.0},
        {"index": 2, "name": "[KEYS] Piano", "role": "KEYS", "panning": 0.0},
        {"index": 3, "name": "[LEAD] Synth Lead", "role": "LEAD", "panning": 0.0},
        {"index": 4, "name": "[PERC] Hats", "role": "HI_HATS", "panning": 0.0},
        {"index": 12, "name": "[VOCALS] Lead Vocal", "role": "VOCALS", "is_audio_track": True, "panning": 0.0}
    ]
    clean_session.data["panning_evaluated"] = False
    clean_session._save_state()

    # Producer asks to start vocal work
    res1 = clean_session.step(conn=mock_adapter, user_input="ya grabe la toma de voz, cortar frases")

    # Engine must intercept before vocal processing
    assert res1["status"] == "AWAITING_PRE_VOCAL_PANNING_DECISION"
    assert "EVALUACIÓN DE PANEO ESTÉREO" in res1["current_step"]
    assert "Decisión Técnica Requerida" in res1["question"]
    assert "Opción A" in res1["question"]
    assert "Opción B" in res1["question"]
    assert clean_session.data.get("awaiting_pre_vocal_panning") is True
    assert clean_session.data.get("pending_vocal_action") == "ya grabe la toma de voz, cortar frases"

    # Producer chooses Opción A (Apply recommended anti-overlap panning)
    res2 = clean_session.step(conn=mock_adapter, user_input="Opción A")

    # Engine should have applied panning to Live tracks
    assert clean_session.data.get("panning_evaluated") is True
    assert clean_session.data.get("awaiting_pre_vocal_panning") is False
    assert mock_adapter.tracks[2]["panning"] == -0.24  # Keys panned Left
    assert mock_adapter.tracks[3]["panning"] == 0.24   # Lead panned Right
    assert mock_adapter.tracks[12]["panning"] == 0.0  # Vocals pure Center

    # And it seamlessly progressed into the vocal workflow
    assert "Paneo anti-solapamiento aplicado" in res2.get("action_taken", "")


def test_pre_vocal_panning_bypass(clean_session, mock_adapter):
    """Validates that selecting Bypass keeps track pannings intact and proceeds."""
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["tracks"] = [
        {"index": 0, "name": "[DRUMS] Core Kit", "role": "DRUMS", "panning": 0.0},
        {"index": 1, "name": "[BASS] Sub 808", "role": "BASS", "panning": 0.0},
        {"index": 2, "name": "[KEYS] Piano", "role": "KEYS", "panning": 0.0},
        {"index": 3, "name": "[LEAD] Synth Lead", "role": "LEAD", "panning": 0.0},
        {"index": 12, "name": "[VOCALS] Lead Vocal", "role": "VOCALS", "is_audio_track": True, "panning": 0.0}
    ]
    clean_session.data["panning_evaluated"] = False
    clean_session._save_state()

    # Intercept
    clean_session.step(conn=mock_adapter, user_input="grabar voz")
    assert clean_session.data.get("awaiting_pre_vocal_panning") is True

    # User chooses Bypass
    res_byp = clean_session.step(conn=mock_adapter, user_input="Bypass")
    assert clean_session.data.get("panning_evaluated") is True
    assert clean_session.data.get("awaiting_pre_vocal_panning") is False
    assert "omitido (Bypass)" in res_byp.get("action_taken", "")


def test_phase_8_auto_panning_application(clean_session, mock_adapter):
    """Validates that in Phase 8 (Vocal Ducking), selecting Option A applies instrument panning."""
    clean_session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
    clean_session.data["phase_index"] = 8
    clean_session.data["tracks"] = [
        {"index": 0, "name": "[DRUMS] Core Kit", "role": "DRUMS", "panning": 0.0},
        {"index": 1, "name": "[BASS] Sub 808", "role": "BASS", "panning": 0.0},
        {"index": 2, "name": "[KEYS] Piano", "role": "KEYS", "panning": 0.0},
        {"index": 3, "name": "[LEAD] Synth Lead", "role": "LEAD", "panning": 0.0},
        {"index": 12, "name": "[VOCALS] Lead Vocal", "role": "VOCALS", "is_audio_track": True, "panning": 0.0}
    ]
    clean_session.data["panning_evaluated"] = False
    clean_session._save_state()

    res = clean_session.step(conn=mock_adapter, user_input="Opción A")
    assert res["phase"] == "PHASE_9_MIX_MASTER"
    assert clean_session.data.get("panning_evaluated") is True
    # Keys and Lead should be panned
    assert mock_adapter.tracks[2]["panning"] == -0.24
    assert mock_adapter.tracks[3]["panning"] == 0.24


def test_direct_panning_evaluation_command(clean_session, mock_adapter):
    """Validates direct natural language command to evaluate or adjust panning."""
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Kick", "role": "DRUMS", "panning": 0.0},
        {"index": 2, "name": "Rhodes", "role": "KEYS", "panning": 0.0},
        {"index": 3, "name": "Guitar", "role": "LEAD", "panning": 0.0}
    ]
    clean_session._save_state()
    res = clean_session.step(conn=mock_adapter, user_input="evaluar separacion estereo y paneo")
    assert res["status"] == "AWAITING_PRE_VOCAL_PANNING_DECISION"
    assert "summary_table" in res["panning_audit"]


def test_specialized_roles_anti_masking_panning(mock_adapter):
    """Validates anti-masking complementary slotting and center lock for all 6 new roles."""
    tracks = [
        {"index": 0, "name": "Dembow Rhythm", "role": "DEMBOW", "panning": 0.0},
        {"index": 1, "name": "Sub 808 Deep", "role": "808_BASS", "panning": 0.0},
        {"index": 2, "name": "Fender Precision Bass", "role": "ELECTRIC_BASS", "panning": 0.0},
        {"index": 3, "name": "Rhodes Chords", "role": "KEYS", "panning": 0.0},
        {"index": 4, "name": "Strat Rhythm Guitar", "role": "RHYTHM_GUITAR", "panning": 0.0},
        {"index": 5, "name": "Analog Lead", "role": "LEAD", "panning": 0.0},
        {"index": 6, "name": "Guitar Solo Lead", "role": "LEAD_GUITAR", "panning": 0.0},
        {"index": 7, "name": "Backing Harmonies", "role": "BACKING_VOCALS", "panning": 0.0},
        {"index": 12, "name": "Lead Vocal Master", "role": "LEAD_VOCAL", "panning": 0.0},
    ]

    audit = InstrumentPanningEvaluator.evaluate_session_panning(tracks, conn=mock_adapter)
    assert audit["status"] == "PANNING_AUDIT_COMPLETED"
    assert audit["has_masking_risk"] is True

    directives = {d["track_index"]: d for d in audit["directives"]}

    # Center-locked anchors (mono <120Hz & primary lead)
    assert directives[0]["recommended_pan"] == 0.0   # Dembow
    assert directives[1]["recommended_pan"] == 0.0   # 808
    assert directives[2]["recommended_pan"] == 0.0   # Electric Bass
    assert directives[12]["recommended_pan"] == 0.0  # Lead Vocal

    # Opposing harmonic pockets (Keys Left vs Rhythm Guitar Right)
    assert directives[3]["recommended_pan"] < 0  # Keys ~ -0.24 (24L)
    assert directives[4]["recommended_pan"] > 0  # Rhythm Guitar ~ +0.32 (32R)

    # Opposing melodic pockets (Lead Right vs Lead Guitar Left)
    assert directives[5]["recommended_pan"] > 0  # Synth Lead ~ +0.24 (24R)
    assert directives[6]["recommended_pan"] < 0  # Lead Guitar ~ -0.30 (30L)

    # Wide peripheral backing vocal pocket
    assert abs(directives[7]["recommended_pan"]) >= 0.35  # ~ 40L or 40R

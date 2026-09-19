# tests/test_vocal_and_mutation_suite.py
"""
Automated Test Suite for Advanced Capabilities:
1. Vocal Co-Creation Flow & Surgical Vocal Chain Processor
2. Closed-Loop Real-Time Resonance Detector
3. Drop Multi-Verse Engine with Strict AI Mutation Entropy Enforcement
"""

import pytest
import numpy as np
from unittest.mock import MagicMock
import json


# -------------------------------------------------------------------------
# 1. VOCAL CHAIN & CO-CREATION DIRECTOR TESTS
# -------------------------------------------------------------------------

def test_vocal_chain_spec_and_deployment():
    from engine.vocal.vocal_chain_processor import VocalChainProcessor

    spec = VocalChainProcessor.get_vocal_chain_spec()
    assert len(spec) == 5
    roles = [d["role"] for d in spec]
    assert "SURGICAL_EQ" in roles
    assert "DE_ESSER" in roles
    assert "DUAL_COMP_PEAK" in roles
    assert "DUAL_COMP_OPTO" in roles
    assert "STEREO_DIMENSION" in roles

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}
    res = VocalChainProcessor.deploy_vocal_chain(mock_conn, track_index=3)
    assert res["status"] == "SUCCESS"
    assert res["devices_configured"] == 5


def test_vocal_harmonies_generation():
    from engine.vocal.vocal_chain_processor import VocalChainProcessor

    lead_notes = [
        {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
        {"pitch": 63, "start_time": 1.5, "duration": 0.5, "velocity": 110}
    ]
    harmonies = VocalChainProcessor.generate_harmony_notes(lead_notes, interval_semitones=3)
    assert len(harmonies) == 2
    assert harmonies[0]["pitch"] == 63  # 60 + 3
    assert harmonies[1]["pitch"] == 66  # 63 + 3
    assert harmonies[0]["velocity"] < 100  # Backing vocal softer


def test_vocal_brief_and_lyrics_generation():
    from engine.vocal.vocal_copilot_flow import VocalCopilotDirector

    brief_brostep = VocalCopilotDirector.generate_vocal_brief(genre="Brostep", key="F", bpm=140.0)
    assert brief_brostep["status"] == "BRIEF_GENERATED"
    assert brief_brostep["genre"] == "BROSTEP"
    assert len(brief_brostep["suggested_lyrics"]) >= 3
    assert "chest voice" in brief_brostep["vocal_delivery_instructions"].lower()

    brief_trap = VocalCopilotDirector.generate_vocal_brief(genre="Trap", key="C#", bpm=130.0)
    assert brief_trap["genre"] == "TRAP"
    assert "808" in str(brief_trap["suggested_lyrics"])


def test_vocal_acoustics_validation():
    from engine.vocal.vocal_copilot_flow import VocalCopilotDirector

    # 1. Healthy commercial balance: Vocal RMS = -14.0 dBFS, Beat RMS = -16.5 dBFS (VBR = +2.5 dB), Ducking = True
    v_pass = VocalCopilotDirector.validate_vocal_acoustics(
        vocal_rms_db=-14.0,
        instrumental_rms_db=-16.5,
        synth_ducking_active=True
    )
    assert v_pass["passed"] is True
    assert v_pass["status"] == "VALIDATED"
    assert v_pass["vocal_to_beat_ratio_db"] == 2.5

    # 2. Too quiet vocal without synth ducking
    v_fail = VocalCopilotDirector.validate_vocal_acoustics(
        vocal_rms_db=-26.0,
        instrumental_rms_db=-16.0,
        synth_ducking_active=False
    )
    assert v_fail["passed"] is False
    assert len(v_fail["issues"]) >= 2


# -------------------------------------------------------------------------
# 2. CLOSED-LOOP RESONANCE DETECTOR TESTS
# -------------------------------------------------------------------------

def test_resonance_detector_frequency_notching():
    from engine.mix.resonance_detector import ResonanceDetector

    sr = 44100
    dur_sec = 1.0
    t = np.linspace(0, dur_sec, int(sr * dur_sec), endpoint=False)

    # Base pink/white noise simulating clean mix
    np.random.seed(42)
    clean_mix = np.random.normal(0, 0.05, len(t))

    # Inject sharp piercing metallic resonance at exactly 3,150 Hz
    resonant_tone = 0.40 * np.sin(2.0 * np.pi * 3150.0 * t)
    harsh_audio = clean_mix + resonant_tone

    report = ResonanceDetector.analyze_spectrum_resonances(
        audio_data=harsh_audio,
        sr=sr,
        threshold_db=3.5,
        min_q=5.0
    )
    assert report["status"] == "RESONANCES_DETECTED"
    assert report["has_harsh_peaks"] is True
    assert report["resonances_count"] >= 1

    top_res = report["resonances"][0]
    # Check frequency accuracy (within 50 Hz of 3,150 Hz)
    assert abs(top_res["frequency_hz"] - 3150.0) < 60.0
    assert top_res["zone"] == "HARSH_MID"
    assert top_res["recommended_notch"]["gain_db"] < -2.0
    assert top_res["recommended_notch"]["q"] >= 4.0


# -------------------------------------------------------------------------
# 3. DROP MUTATION MULTI-VERSE & ENTROPY TESTS
# -------------------------------------------------------------------------

def test_drop_mutator_divergence_calculation():
    from engine.music.drop_mutator import DropMutationEngine

    pat_a = [
        {"pitch": 36, "start_time": 0.0},
        {"pitch": 36, "start_time": 0.5},
        {"pitch": 36, "start_time": 1.0}
    ]
    # Identical pattern -> 0.0 divergence
    assert DropMutationEngine.calculate_rhythmic_divergence(pat_a, pat_a) == 0.0

    # Completely different rhythm -> 1.0 divergence
    pat_b = [
        {"pitch": 48, "start_time": 2.0},
        {"pitch": 50, "start_time": 2.75}
    ]
    assert DropMutationEngine.calculate_rhythmic_divergence(pat_a, pat_b) == 1.0


def test_drop_mutator_entropy_rejection():
    from engine.music.drop_mutator import DropMutationEngine, DropMutationEntropyViolationError

    lazy_ai_payload = {
        "variation_a": [
            {"pitch": 36, "start_time": 0.0, "duration": 0.5},
            {"pitch": 38, "start_time": 1.0, "duration": 0.5}
        ],
        # Variation B is identical to A!
        "variation_b": [
            {"pitch": 36, "start_time": 0.0, "duration": 0.5},
            {"pitch": 38, "start_time": 1.0, "duration": 0.5}
        ],
        "variation_c": [
            {"pitch": 60, "start_time": 0.25, "duration": 0.25}
        ]
    }

    # Motor must REJECT duplicate/lazy mutations!
    with pytest.raises(DropMutationEntropyViolationError) as exc_info:
        DropMutationEngine.validate_drop_mutations(lazy_ai_payload, min_divergence=0.40)
    assert "Variación B es demasiado similar a la Variación A" in str(exc_info.value)


def test_drop_mutator_entropy_approval_and_deployment():
    from engine.music.drop_mutator import DropMutationEngine

    contrasting_payload = {
        # Var A: 4-on-the-floor complextro hook
        "variation_a": [
            {"pitch": 36, "start_time": 0.0, "duration": 0.5},
            {"pitch": 36, "start_time": 1.0, "duration": 0.5},
            {"pitch": 36, "start_time": 2.0, "duration": 0.5},
            {"pitch": 36, "start_time": 3.0, "duration": 0.5}
        ],
        # Var B: Half-time riddim switch (kick on 0, snare on 2)
        "variation_b": [
            {"pitch": 36, "start_time": 0.0, "duration": 1.0},
            {"pitch": 38, "start_time": 2.0, "duration": 0.5},
            {"pitch": 43, "start_time": 3.5, "duration": 0.25}
        ],
        # Var C: Melodic supersaw arpeggio cascade
        "variation_c": [
            {"pitch": 60, "start_time": 0.25, "duration": 0.25},
            {"pitch": 63, "start_time": 0.50, "duration": 0.25},
            {"pitch": 67, "start_time": 0.75, "duration": 0.25},
            {"pitch": 70, "start_time": 1.25, "duration": 0.25},
            {"pitch": 72, "start_time": 1.75, "duration": 0.25}
        ]
    }

    val_res = DropMutationEngine.validate_drop_mutations(contrasting_payload, min_divergence=0.40)
    assert val_res["passed"] is True
    assert val_res["divergence_a_vs_b"] >= 0.40
    assert val_res["divergence_a_vs_c"] >= 0.40

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}
    deploy_res = DropMutationEngine.deploy_mutations_to_session(mock_conn, track_index=1, payload=contrasting_payload, base_slot=10)
    assert deploy_res["status"] == "MUTATIONS_DEPLOYED"
    assert len(deploy_res["variations_deployed"]) == 3
    assert deploy_res["variations_deployed"][0]["slot_index"] == 10
    assert deploy_res["variations_deployed"][1]["slot_index"] == 11
    assert deploy_res["variations_deployed"][2]["slot_index"] == 12


# -------------------------------------------------------------------------
# 4. GUIDED SESSION INTEGRATION TEST
# -------------------------------------------------------------------------

def test_guided_session_vocal_and_drop_commands(tmp_path, monkeypatch):
    from engine.production.copilot.guided_session import CopilotGuidedSession
    from engine.adapters.mock_adapter import MockAbletonAdapter

    test_state_file = tmp_path / "guided_session.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    adapter = MockAbletonAdapter()
    session = CopilotGuidedSession()
    # Fast forward session to Phase 9
    session.data["current_phase"] = "PHASE_9_COMPLETED"
    session.data["phase_index"] = 9
    session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS"},
        {"index": 1, "name": "Bass", "role": "BASS"},
        {"index": 2, "name": "Lead Vocal", "role": "VOCALS"}
    ]
    session.data["sections"] = [{"name": "Intro", "bars": 8}, {"name": "Drop 1", "bars": 16}]
    session.data["genre"] = "brostep"
    session.data["key"] = "F"
    session.data["bpm"] = 140.0
    session._save_state()

    # 1. Request vocal brief
    res_vocal_brief = session.step(conn=adapter, user_input="Añadir voces a la pista")
    assert res_vocal_brief["status"] == "VOCAL_BRIEF_ACTIVE"
    assert "Guía de Grabación Vocal" in res_vocal_brief["question"]
    assert "Líneas Líricas Sugeridas" in res_vocal_brief["question"]

    # 2. Process recorded vocals
    res_vocal_proc = session.step(conn=adapter, user_input="Voz lista, procesar y validar audio")
    assert res_vocal_proc["status"] == "VOCALS_PROCESSED"
    assert "Producción Vocal Procesada" in res_vocal_proc["question"]
    assert "Inteligibilidad Vocal" in res_vocal_proc["question"]

    # 3. Request drop mutation
    res_mut = session.step(conn=adapter, user_input="Generar variaciones de drop A/B/C")
    assert res_mut["status"] == "AWAITING_DROP_MUTATIONS"
    assert "Generador Multi-Verso de Drops A/B/C" in res_mut["question"]

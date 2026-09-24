# tests/test_copilot_refinements_audit.py
"""
Unit and integration tests verifying the 4 key architecture corrections:
1. Phase 2: Dynamic section suggestions and flexible NLP parsing without rigid template mandates.
2. Phase 5: Removal of lazy 'Cadena Express (Recomendada)' shortcuts in favor of intentional effect curation.
3. Phase 6: Strict assistant policy: zero autonomous/procedural note generation when none provided.
4. Point 4: Top & Tail hygiene: beat 0.0 micro-fade-in and dynamic outro fade to -inf dB at bar 80 / final boundary.
"""
import pytest
import numpy as np
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.arrangement.top_tail_guard import TopTailGuard
from engine.production.copilot.phases.phase_2_sections import Phase2SectionsHandler
from engine.production.copilot.phases.phase_6.arranger import Phase6Arranger


def test_phase_2_nlp_and_suggestion_flexibility():
    """Point 1: Verifies that Phase 2 does not impose a rigid template and parses NLP sections."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    # Step 1: Scaffolding
    session.step(conn=adapter, user_input="Opción A")

    # Step 2 prompt check: should offer suggestions, not force Option A/B
    p2_prompt = Phase2SectionsHandler().prompt(session)
    assert "Sugerencia Adaptativa" in p2_prompt["question"]
    assert "Flexibilidad Total (Cero Imposición Rígida)" in p2_prompt["question"]
    assert "Aprobar sugerencia" in p2_prompt["question"]

    # Step 2 handle check: custom conversational NLP sections
    res = session.step(
        conn=adapter,
        user_input="Quiero una estructura personalizada: Intro 8, Verso 16, Coro 16, Puente 8, Outro 8 en Fa Menor"
    )
    assert res["phase"] == "PHASE_3_INSTRUMENTS"
    assert session.data["key"] == "F"
    assert session.data["scale"] == "Minor"
    assert session.data["total_bars"] == 56
    assert len(session.data["sections"]) == 5
    sec_names = [s["name"] for s in session.data["sections"]]
    assert sec_names == ["Intro", "Verso", "Coro", "Puente", "Outro"]


def test_phase_2_approve_suggestion():
    """Point 1: Verifies approving the dynamic genre suggestion."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()
    session.data["genre"] = "trap"
    session.step(conn=adapter, user_input="Opción A")

    res = session.step(conn=adapter, user_input="Aprobar sugerencia en Fa Menor")
    assert res["phase"] == "PHASE_3_INSTRUMENTS"
    assert session.data["total_bars"] == 80
    assert len(session.data["sections"]) == 8


def test_phase_5_no_lazy_cadena_express_shortcut():
    """Point 2: Verifies that Phase 5 eliminates Cadena Express shortcut recommendations."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()
    session.step(conn=adapter, user_input="Opción A")
    session.step(conn=adapter, user_input="Opción B en Fa Menor")
    # Advance through Phase 3 and 4
    for _ in range(5):
        session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        session.step(conn=adapter, user_input="Opción 1")

    # Now in Phase 5
    p5_res = session.step(conn=adapter, user_input="")
    assert "Cadena Express (Recomendada)" not in p5_res["question"]
    assert "o escribe 'cadena express'" not in p5_res.get("instructions_for_ai", "")
    assert "Decisión deliberada por procesador" in p5_res["question"]


def test_phase_6_zero_autonomous_note_generation():
    """Point 3: Verifies that without user notes, the engine NEVER writes algorithmic notes."""
    session = CopilotGuidedSession()
    session.reset()
    session.data["tracks"] = [
        {"index": 0, "name": "Sub Bass", "role": "BASS"},
        {"index": 1, "name": "Lead", "role": "LEAD"}
    ]
    session.data["sections"] = [
        {"name": "Intro", "bars": 8, "start_bar": 0},
        {"name": "Drop", "bars": 16, "start_bar": 8}
    ]
    session.data["allow_autonomous_note_generation"] = False

    adapter = MockAbletonAdapter()
    # Deploy single track without any custom notes
    notes_written = Phase6Arranger.deploy_single_track_composition(
        session=session,
        conn=adapter,
        trk=session.data["tracks"][0],
        custom_notes_map={},
        sections=session.data["sections"]
    )
    # Notes count MUST be zero: engine strictly assists, prepares empty clip, never writes notes autonomously
    assert notes_written == 0
    assert session.data["tracks"][0]["notes_count"] == 0


def test_top_tail_pre_roll_and_outro_fade_bar_80():
    """Point 4: Verifies beat 0.0 micro-fade-in and bar 80 outro fade to -inf dB."""
    # 1. Pre-roll points check
    points_top = TopTailGuard.generate_pre_roll_gate_points(downbeat_beat=0.0)
    assert points_top[0]["time"] == 0.0
    assert points_top[0]["value"] == 0.0  # Must be -inf dB at sample 0
    assert points_top[-1]["value"] == 0.85  # Opens smoothly
    assert points_top[1]["time"] > 0.0  # Smooth micro-ramp, not colapsed at 0.0

    # 2. Outro points check for 80-bar arrangement (beat 320.0)
    adapter = MockAbletonAdapter()
    session_data = {
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Verso 1", "bars": 16},
            {"name": "Drop 1", "bars": 16},
            {"name": "Puente", "bars": 16},
            {"name": "Drop 2", "bars": 16},
            {"name": "Outro", "bars": 8}
        ],
        "tracks": [
            {"index": 0, "name": "Lush Pad", "role": "PAD"},
            {"index": 1, "name": "Bass", "role": "BASS"}
        ]
    }
    # Total bars = 8 + 16 + 16 + 16 + 16 + 8 = 80 bars = 320 beats
    res = TopTailGuard.apply_top_and_tail_guards(
        conn=adapter,
        master_track_index=0,
        total_bars=64.0,  # Should be overridden by sections (80.0)
        fade_bars=2.0,
        session_data=session_data
    )
    assert res["total_bars"] == 80.0
    outro_fade = res["outro_fade"]
    assert outro_fade["end_beat"] == 320.0
    assert outro_fade["start_beat"] == 312.0
    assert outro_fade["points"][-1]["value"] == 0.0  # Absolute zero at end of bar 80

    # 3. Audio Auditor compliance test
    # Simulate 80-bar audio buffer with pre-roll silence and complete outro decay to -inf dB
    sr = 44100
    dur = 2.0  # short buffer for fast test
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, dur, int(sr * dur)))
    # Pre-roll silence
    audio[:int(sr * 0.05)] = 0.0
    # Micro fade in
    audio[int(sr * 0.05):int(sr * 0.10)] *= np.linspace(0, 1, int(sr * 0.05))
    # Outro fade out
    audio[int(sr * 1.5):int(sr * 1.9)] *= np.linspace(1, 0, int(sr * 0.4))
    # Final tail silence (-inf dB)
    audio[int(sr * 1.9):] = 0.0

    audit = TopTailGuard.audit_top_and_tail_audio(audio, sr=sr, pre_roll_duration_sec=0.02, tail_duration_sec=0.05)
    assert audit["compliant"] is True
    assert audit["pre_roll_clean"] is True
    assert audit["tail_faded_clean"] is True

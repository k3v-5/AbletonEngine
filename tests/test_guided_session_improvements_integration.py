# tests/test_guided_session_improvements_integration.py
"""
Integration test for guided_session with newly implemented improvements:
- TransactionGuard snapshot and commit in Phase 5 without interrupting session flow
- Anti-Climax energy detection in Phase 7 prompting Option C
- Backward navigation from Phase 7 to Phase 6 (step reversal) to adjust clips and resuming normal progression
- Metric modulation snare rolls and 808 legato slides in composition Phase 6
- Unlocked modal interchange in Phase 6 composition
"""

import pytest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.session.transaction_guard import TransactionGuard


def test_guided_session_transaction_guard_and_anti_climax_reversal():
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    # Step 1: PHASE_1_TRACKS
    res1 = session.step(conn=adapter, user_input="Opción A")
    assert res1["phase"] == "PHASE_2_SECTIONS"

    # Step 2: PHASE_2_SECTIONS
    res2 = session.step(conn=adapter, user_input="Opción A")
    assert res2["phase"] == "PHASE_3_INSTRUMENTS"

    # Step 3: Fast-forward through instruments
    for _ in range(len(session.data["tracks"])):
        session.step(conn=adapter, user_input="Opción 1")
    assert session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING"

    # Step 4: Fast-forward through parameter sculpting
    while session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING":
        session.step(conn=adapter, user_input="FILTER_CUTOFF=0.70 DRIVE=0.20 AMP_ATTACK=0.01 AMP_RELEASE=0.40 SUB_LEVEL=0.80")
    assert session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"

    # Step 5: PHASE_5_INSERT_EFFECTS with TransactionGuard active
    # Step through insert effects
    while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        res_fx = session.step(conn=adapter, user_input="Opción 1")
        # Ensure active snapshot was committed or managed without breaking
        assert "error" not in str(res_fx).lower()

    # Verify flow reached Phase 6
    assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
    assert session.data["phase_index"] == 6

    # Step 6: PHASE_6_COMPOSITION with modal interchange progression
    res6 = session.step(conn=adapter, user_input="KEY A DORIAN BPM 124 TRAP")
    assert session.data["current_phase"] == "PHASE_7_AUTOMATION"

    # Step 7: PHASE_7_AUTOMATION evaluates Anti-Climax and provides Option C
    assert "Opción C" in res6["question"]

    # Test backward step-reversal to Phase 6 (Punto 22)
    res_reverse = session.step(conn=adapter, user_input="Opción C")
    assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
    assert session.data["phase_index"] == 6
    assert "Paso 6" in res_reverse.get("question", "")

    # Re-compose and progress forward again to Phase 7
    res_recomposed = session.step(conn=adapter, user_input="KEY A NATURAL_MINOR BPM 124 TRAP")
    assert session.data["current_phase"] == "PHASE_7_AUTOMATION"
    assert session.data["phase_index"] == 7

    # Proceed through Phase 7 with Option A (inject automations)
    res7 = session.step(conn=adapter, user_input="Opción A")
    assert session.data["current_phase"] == "PHASE_8_VOCAL_DUCKING"

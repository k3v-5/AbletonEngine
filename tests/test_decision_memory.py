"""
Tests for DecisionMemory in PIE.
Verifies contextual retrieval, linking, invalidation, superseding,
and the fundamental invariant: historical matches are CANDIDATE-ONLY and NEVER auto-executable.
"""
from engine.production.models import ProductionDecision
from engine.production.memory import DecisionMemory, MemoryStatus


def test_decision_memory_record_and_get():
    memory = DecisionMemory(project_id="test_mem")
    decision = ProductionDecision(
        decision_id="dec_master_01",
        intent_id="intent_01",
        domain="master",
        target="Master",
        decision_type="LIMITER_ADJUST",
        reason="Preserve inter-sample headroom",
        confidence=0.92,
        selected_action={"ceiling_db": -0.5, "gain_db": 1.2}
    )

    mem_id = memory.record(
        decision=decision,
        context={
            "genre": "Techno",
            "tempo": 130.0,
            "key": "Fm",
            "delivery_target": "STREAMING"
        }
    )

    assert mem_id.startswith("mem_")
    record = memory.get(mem_id)
    assert record is not None
    assert record["decision_id"] == "dec_master_01"
    assert record["domain"] == "master"
    assert record["context"]["genre"] == "Techno"
    assert record["confidence"] == 0.92

    # Invariants on stored record
    assert record["is_candidate_only"] is True
    assert record["auto_executable"] is False
    assert record["status"] == MemoryStatus.VALID


def test_decision_memory_candidate_only_invariant_on_search():
    memory = DecisionMemory(project_id="test_invariant")
    d1 = ProductionDecision(
        decision_id="d1",
        intent_id="intent_01",
        domain="master",
        target="Master",
        decision_type="EQ_HIGH_SHELF",
        reason="Add air at 10kHz",
        confidence=0.88,
        selected_action={"gain": 0.5}
    )
    d2 = ProductionDecision(
        decision_id="d2",
        intent_id="intent_02",
        domain="mix",
        target="Bass",
        decision_type="SIDECHAIN_COMP",
        reason="Duck bass during kick",
        confidence=0.95,
        selected_action={"ratio": 4.0}
    )

    memory.record(d1, {"genre": "House", "target": "Master"})
    memory.record(d2, {"genre": "House", "target": "Bass"})

    # Search query
    candidates = memory.search(query_context={"genre": "House", "target": "Master"}, domain="master")
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand["decision_id"] == "d1"

    # Strict invariant verification: Candidate ONLY, NO auto-execution
    assert cand["is_candidate_only"] is True
    assert cand["auto_executable"] is False
    assert "match_score" in cand
    assert cand["match_score"] > 0.5


def test_decision_memory_invalidation_and_superseding():
    memory = DecisionMemory(project_id="test_invalidation")
    d1 = ProductionDecision(
        decision_id="d1",
        intent_id="intent_01",
        domain="master",
        target="Master",
        decision_type="CLIPPING",
        reason="Soft clip master",
        confidence=0.85
    )
    d2 = ProductionDecision(
        decision_id="d2",
        intent_id="intent_02",
        domain="master",
        target="Master",
        decision_type="LIMITER",
        reason="Use transparent limiter instead",
        confidence=0.95
    )

    m1_id = memory.record(d1, {"genre": "Ambient"})
    m2_id = memory.record(d2, {"genre": "Ambient"})

    # Both valid initially
    assert len(memory.search({"genre": "Ambient"})) == 2

    # Invalidate d1
    memory.invalidate(m1_id, reason="Caused audible distortion on delicate transients")
    rec1 = memory.get(m1_id)
    assert rec1["status"] == MemoryStatus.INVALIDATED
    assert "audible distortion" in rec1["invalidation_reason"]

    # Invalidated item must not appear in search results
    search_after_invalidation = memory.search({"genre": "Ambient"})
    assert len(search_after_invalidation) == 1
    assert search_after_invalidation[0]["memory_id"] == m2_id

    # Re-validate d1
    memory.validate(m1_id)
    assert memory.get(m1_id)["status"] == MemoryStatus.VALID
    assert len(memory.search({"genre": "Ambient"})) == 2

    # Supersede d1 with d2
    memory.supersede(m1_id, m2_id)
    assert memory.get(m1_id)["status"] == MemoryStatus.SUPERSEDED
    assert memory.get(m1_id)["superseded_by"] == m2_id

    # Superseded item must not appear in search results
    search_after_superseded = memory.search({"genre": "Ambient"})
    assert len(search_after_superseded) == 1
    assert search_after_superseded[0]["memory_id"] == m2_id


def test_decision_memory_linking_and_serialization():
    memory = DecisionMemory(project_id="test_linking")
    d1 = ProductionDecision(
        decision_id="d_mix_kick",
        intent_id="intent_01",
        domain="mix",
        target="Kick",
        decision_type="HPF",
        reason="Remove sub-bass rumble"
    )
    d2 = ProductionDecision(
        decision_id="d_mix_bass",
        intent_id="intent_02",
        domain="mix",
        target="Bass",
        decision_type="SIDECHAIN",
        reason="Duck on kick hit"
    )

    m1_id = memory.record(d1)
    m2_id = memory.record(d2)

    # Link decisions
    memory.link(m1_id, "d_mix_bass")
    related = memory.get_related("d_mix_kick")
    assert len(related) == 1
    assert related[0]["decision_id"] == "d_mix_bass"

    # Serialization roundtrip
    data = memory.to_dict()
    restored = DecisionMemory.from_dict(data)
    assert restored.project_id == "test_linking"
    assert len(restored._records) == 2
    assert restored.get_related("d_mix_kick")[0]["decision_id"] == "d_mix_bass"

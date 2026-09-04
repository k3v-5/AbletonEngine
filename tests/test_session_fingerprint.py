"""
Tests for SessionFingerprint and Scoped vs Global Hash Invariants (Document 10).
Verifies Cases A through E:
- Case A: Same state -> Identical fingerprint
- Case B: Relevant change -> Different fingerprint
- Case C: Irrelevant change outside scope -> Identical fingerprint
- Case D: Dictionary ordering invariance -> Identical fingerprint
- Case E: Algorithm versioning
"""
import json
import hashlib
import pytest

from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode, DeviceNode
from engine.production.context import ProductionContext
from engine.production.models import SessionFingerprint


def test_case_a_same_state_identical_fingerprint():
    """Caso A: El mismo estado produce exactamente el mismo fingerprint."""
    graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    t_guitar = TrackNode(id="track_guitar", name="Guitar", ableton_index=1, type="audio", volume=0.75)
    graph.add_track(t_master)
    graph.add_track(t_guitar)

    ctx1 = ProductionContext(shadow_graph=graph, project_id="proj_1")
    ctx2 = ProductionContext(shadow_graph=graph, project_id="proj_1")

    fp1 = ctx1.compute_session_fingerprint(relevant_entities=["Guitar"])
    fp2 = ctx2.compute_session_fingerprint(relevant_entities=["Guitar"])

    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex string length


def test_case_b_relevant_change_invalidates_fingerprint():
    """Caso B: Una modificación en un elemento relevante DEBE invalidar el fingerprint."""
    graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    t_guitar = TrackNode(id="track_guitar", name="Guitar", ableton_index=1, type="audio", volume=0.75)
    graph.add_track(t_master)
    graph.add_track(t_guitar)

    context = ProductionContext(shadow_graph=graph)

    # Scoped to Guitar
    fp_before = context.compute_session_fingerprint(relevant_entities=["Guitar"])

    # Modificar parámetro relevante (volumen de Guitar)
    t_guitar.volume = 0.80
    graph.increment_version()

    fp_after = context.compute_session_fingerprint(relevant_entities=["Guitar"])

    assert fp_before != fp_after
    assert context.is_stale_for_plan(fp_before, relevant_entities=["Guitar"]) is True


def test_case_c_irrelevant_change_preserves_scoped_fingerprint():
    """Caso C: Una modificación en un elemento fuera del alcance NO DEBE invalidar el plan."""
    graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    t_guitar = TrackNode(id="track_guitar", name="Guitar", ableton_index=1, type="audio", volume=0.75)
    t_pad = TrackNode(id="track_pad", name="Pad", ableton_index=2, type="audio", volume=0.85)
    graph.add_track(t_master)
    graph.add_track(t_guitar)
    graph.add_track(t_pad)

    context = ProductionContext(shadow_graph=graph)

    # Plan sólo involucra a Guitar
    fp_scoped_before = context.compute_session_fingerprint(relevant_entities=["Guitar"])
    fp_global_before = context.compute_session_fingerprint()

    # Modificar elemento irrelevante (volumen de Pad de 0.85 a 0.70)
    t_pad.volume = 0.70
    graph.increment_version()

    fp_scoped_after = context.compute_session_fingerprint(relevant_entities=["Guitar"])
    fp_global_after = context.compute_session_fingerprint()

    # El fingerprint relevante NO DEBE CAMBIAR
    assert fp_scoped_before == fp_scoped_after
    assert context.is_stale_for_plan(fp_scoped_before, relevant_entities=["Guitar"]) is False

    # El fingerprint global SÍ cambia
    assert fp_global_before != fp_global_after


def test_case_d_dictionary_ordering_determinism():
    """Caso D: La serialización JSON canónica debe ser inmune al orden arbitrario de claves."""
    payload_1 = {"z_key": 10, "a_key": "val", "nested": {"m": True, "b": False}}
    payload_2 = {"a_key": "val", "z_key": 10, "nested": {"b": False, "m": True}}

    canonical_1 = json.dumps(payload_1, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    canonical_2 = json.dumps(payload_2, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    assert canonical_1 == canonical_2
    hash_1 = hashlib.sha256(canonical_1.encode("utf-8")).hexdigest()
    hash_2 = hashlib.sha256(canonical_2.encode("utf-8")).hexdigest()
    assert hash_1 == hash_2


def test_case_e_fingerprint_model_contract():
    """Caso E: SessionFingerprint model contract y algorithm versioning."""
    fp = SessionFingerprint(
        value="a" * 64,
        algorithm="SHA-256",
        algorithm_version="1.0.0",
        scope="PLAN_RELEVANT",
        details={"entities": ["Guitar"]}
    )
    assert fp.algorithm == "SHA-256"
    assert fp.algorithm_version == "1.0.0"
    assert fp.scope == "PLAN_RELEVANT"
    assert fp.source_version == "PIE-1.0"
    assert fp.details["entities"] == ["Guitar"]

    d = fp.to_dict()
    assert d["value"] == "a" * 64
    assert d["algorithm_version"] == "1.0.0"

    restored = SessionFingerprint.from_dict(d)
    assert restored.value == fp.value
    assert restored.algorithm_version == fp.algorithm_version

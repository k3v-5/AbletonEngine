"""
Tests for ProductionContext in PIE.
Verifies scoped fingerprinting, relevant vs irrelevant change detection,
and BS.1770-5 measurement capture.
"""
import numpy as np
import pytest
from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode, DeviceNode
from engine.production.context import ProductionContext
from engine.production.models import (
    ProductionContextSnapshot,
    SessionFingerprint,
    TrackRef,
    DeviceRef,
    ParameterRef,
)


def test_production_context_scoped_fingerprint():
    graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    t_kick = TrackNode(id="track_kick", name="Kick", ableton_index=1, type="midi", volume=0.75)
    t_vocal = TrackNode(id="track_vocal", name="Vocal", ableton_index=2, type="audio", volume=0.70)

    graph.add_track(t_master)
    graph.add_track(t_kick)
    graph.add_track(t_vocal)

    context = ProductionContext(shadow_graph=graph)

    # Initial scoped fingerprint for Master
    fp_master_1 = context.compute_session_fingerprint(relevant_entities=["Master"])

    # 1. Irrelevant change: modify Vocal track volume
    t_vocal.volume = 0.60
    graph.increment_version()

    fp_master_2 = context.compute_session_fingerprint(relevant_entities=["Master"])

    # Scoped fingerprint for Master must NOT change!
    assert fp_master_1 == fp_master_2
    assert context.is_stale_for_plan(fp_master_1, relevant_entities=["Master"]) is False

    # Global fingerprint DOES change
    fp_global = context.compute_session_fingerprint()
    assert fp_global != fp_master_1

    # 2. Relevant change: modify Master track
    t_master.volume = 0.90
    graph.increment_version()

    fp_master_3 = context.compute_session_fingerprint(relevant_entities=["Master"])
    # Scoped fingerprint for Master MUST change!
    assert fp_master_3 != fp_master_1
    assert context.is_stale_for_plan(fp_master_1, relevant_entities=["Master"]) is True


def test_production_context_measurements():
    graph = SessionShadowGraph()
    context = ProductionContext(shadow_graph=graph, loudness_profile="STREAMING")

    # Offline / simulated measurement
    offline_meas = context.capture_measurements(target_name="Master")
    assert "integrated_lufs" in offline_meas
    assert "true_peak_dbtp" in offline_meas
    assert offline_meas["standard"] == "ITU-R BS.1770-5"

    # Real DSP audio measurement
    sr = 48000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sine = 0.2 * np.sin(2 * np.pi * 1000 * t)
    audio = np.stack([sine, sine], axis=1)

    real_meas = context.capture_measurements(audio_buffer=audio, sample_rate=sr, target_name="Master")
    assert real_meas["integrated_lufs"] < -10.0
    assert real_meas["true_peak_dbtp"] < 0.0
    assert "ITU-R BS.1770-5" in real_meas["standard"]


def test_production_context_capture_and_snapshot_immutability():
    graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    t_bass = TrackNode(id="track_bass", name="Bass", ableton_index=1, type="audio", volume=0.75)
    graph.add_track(t_master)
    graph.add_track(t_bass)

    context = ProductionContext(shadow_graph=graph, project_id="test_proj")
    snap = context.capture(relevant_entities=["Bass"])

    assert isinstance(snap, ProductionContextSnapshot)
    assert snap.project_id == "test_proj"
    assert snap.session_id == "test_proj"
    assert snap.session_fingerprint is not None
    assert len(snap.tracks) == 2
    assert "Bass" in snap.relevant_object_ids

    # Immutability verification: snapshot cannot be modified
    with pytest.raises(Exception):
        snap.project_id = "altered_proj"

    # to_dict roundtrip
    d = snap.to_dict()
    assert d["project_id"] == "test_proj"
    restored = ProductionContextSnapshot.from_dict(d)
    assert restored.project_id == snap.project_id
    assert restored.session_fingerprint == snap.session_fingerprint


def test_production_context_reference_contracts():
    graph = SessionShadowGraph()
    t_synth = TrackNode(id="track_synth", name="Synth", ableton_index=1, type="midi", volume=0.80)
    dev = DeviceNode(
        id="dev_eq8",
        track_id="track_synth",
        ableton_track_index=1,
        ableton_device_index=0,
        name="EQ Eight",
        class_name="Eq8",
        type="audio_effect",
        parameters_cache={"Gain": 2.5, "Freq": 1000.0}
    )
    t_synth.devices = {"dev_eq8": dev}
    graph.add_track(t_synth)

    context = ProductionContext(shadow_graph=graph)

    # get_track_ref
    t_ref = context.get_track_ref("Synth")
    assert isinstance(t_ref, TrackRef)
    assert t_ref.name == "Synth"
    assert t_ref.volume == 0.80
    assert len(t_ref.devices) == 1

    # get_device_ref
    d_ref = context.get_device_ref("Synth", "EQ Eight")
    assert isinstance(d_ref, DeviceRef)
    assert d_ref.name == "EQ Eight"
    assert len(d_ref.parameters) == 2
    param_names = [p.name for p in d_ref.parameters]
    assert "Gain" in param_names
    assert "Freq" in param_names


def test_production_context_get_fingerprint():
    graph = SessionShadowGraph()
    t_master = TrackNode(id="track_master", name="Master", ableton_index=0, type="master", volume=0.85)
    graph.add_track(t_master)

    context = ProductionContext(shadow_graph=graph)
    fp = context.get_fingerprint(relevant_entities=["Master"])

    assert isinstance(fp, SessionFingerprint)
    assert len(fp.value) == 64
    assert fp.algorithm == "SHA-256"
    assert fp.algorithm_version == "1.0.0"
    assert fp.scope == "PLAN_RELEVANT"
    assert fp.source_version == "PIE-1.0"


def test_production_context_locks_detection():
    graph = SessionShadowGraph()
    t_drum = TrackNode(id="track_drum", name="Drums", ableton_index=1, type="audio", volume=0.80)
    graph.add_track(t_drum)
    graph.lock_object("track_drum", reason="Locked drum bus")

    context = ProductionContext(shadow_graph=graph)

    assert context.get_locked_state("Drums") is True
    assert context.get_locked_state("track_drum") is True
    locks = context.get_locks()
    assert "track_drum" in locks
    assert locks["track_drum"]["locked"] is True
    assert "drum" in locks["track_drum"]["reason"].lower()

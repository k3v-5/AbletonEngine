# tests/test_production_completeness.py
import pytest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.completeness import (
    ProductionCompletenessGate,
    CompletenessViolationType,
    ViolationSeverity,
    CompletenessReport,
)
from engine.arrangement.models.song import Song
from engine.arrangement.models.section import Section, SectionType
from engine.arrangement.compiler import ArrangementCompiler


def test_role_deduction():
    gate = ProductionCompletenessGate
    assert gate.deduce_role_from_track("Chroma_Drums_MIDI") == "DRUM_KIT"
    assert gate.deduce_role_from_track("Chroma_808_Bass") == "SUB_BASS"
    assert gate.deduce_role_from_track("Piano_Chords") == "PIANO"
    assert gate.deduce_role_from_track("Lead_Synth_1") == "LEAD"
    assert gate.deduce_role_from_track("Pad_Atmosphere") == "PAD"


def test_detect_silent_midi_track():
    adapter = MockAbletonAdapter()
    # Track 0: Kick with Drum Buss (has device)
    # Add a track with clips but NO device
    adapter.tracks.append({
        "index": 2,
        "name": "Chroma_808_Bass",
        "is_audio_track": False,
        "is_midi_track": True,
        "mute": False,
        "solo": False,
        "arm": False,
        "volume": 0.85,
        "panning": 0.0,
        "clip_slots": [
            {"index": 0, "has_clip": True, "clip": {"name": "808_Drop", "length": 16.0, "is_playing": False, "is_recording": False}}
        ],
        "devices": []  # SILENT!
    })

    # Run audit without auto-remediation
    report = ProductionCompletenessGate.audit_session(adapter, auto_remediate=False, target_genre="trap")
    
    assert report.silent_tracks_detected >= 1
    assert any(v.violation_type == CompletenessViolationType.SILENT_TRACK for v in report.violations)
    assert report.status == "FAIL"


def test_auto_remediation_heals_silent_track():
    adapter = MockAbletonAdapter()
    adapter.tracks.append({
        "index": 2,
        "name": "Chroma_808_Bass",
        "is_audio_track": False,
        "is_midi_track": True,
        "mute": False,
        "solo": False,
        "arm": False,
        "volume": 0.85,
        "panning": 0.0,
        "clip_slots": [
            {"index": 0, "has_clip": True, "clip": {"name": "808_Drop", "length": 16.0, "is_playing": False, "is_recording": False}}
        ],
        "devices": []  # SILENT!
    })

    # Run audit WITH auto-remediation
    report = ProductionCompletenessGate.audit_session(adapter, auto_remediate=True, target_genre="trap")
    
    assert report.status in ["AUTO_REMEDIATED", "PASS"]
    assert len(report.remediations) >= 1
    rem = report.remediations[0]
    assert rem.track_index == 2
    assert rem.success is True
    # Verify the device was actually loaded on the mock track
    assert len(adapter.tracks[2]["devices"]) >= 1


def test_compiler_ensure_sound_sources():
    adapter = MockAbletonAdapter()
    from engine import ProductionEngine
    eng = ProductionEngine(adapter=adapter)
    eng.synchronizer.reconcile()

    # Ensure track 0 and 1 have 0 devices initially
    adapter.tracks[0]["devices"] = []
    adapter.tracks[1]["devices"] = []

    compiler = ArrangementCompiler(eng)

    song = Song(
        name="Completeness_Test_Song",
        genre="trap",
        tempo=138.0,
        key="F",
        scale="natural_minor",
        sections=[
            Section(name="Intro", section_type=SectionType.INTRO, start_bar=0, bars=8, energy=0.3),
            Section(name="Drop", section_type=SectionType.DROP, start_bar=8, bars=16, energy=0.9),
        ]
    )

    res = compiler.compile(song, preview=False, ensure_sound_sources=True)
    assert res["status"] == "compiled_success"
    # Ensure instruments were loaded
    assert len(res["instruments_loaded"]) >= 1
    loaded_idx = res["instruments_loaded"][0]["track_index"]
    # Check that the track now has devices loaded
    assert len(adapter.tracks[loaded_idx]["devices"]) >= 1

# tests/test_instrumentation_phase3.py
"""
Test Suite for Phase 3: Instrumentation, VSTs & Universal Sound Design.
Validates:
1. InstalledPluginScanner: Host VST3/VST scanning, semantic role classification, recommendations.
2. AuthenticSampleDrumRackEngine: Local FL Studio sample library indexing, authentic .wav verification, 8-pad kit construction.
3. SemanticTimbreMorphEngine: Section-based 96-bar dynamic morphing, LPF cutoff sweeps, saturation warmth, envelope breakpoints.
4. ExecutiveCopilotEngine Phase 3 Integration: Discovery and execution of DEC-P3-01 to DEC-P3-07 decisions.
"""

import pytest
import os
from engine.instruments.installed_scanner import (
    InstalledPluginScanner, ScannedPlugin, PluginCategory
)
from engine.sound.drum_rack.authentic_builder import (
    AuthenticSampleDrumRackEngine, AuthenticDrumKitSpec, AuthenticDrumPad
)
from engine.sound.macros.semantic_morph import (
    SemanticTimbreMorphEngine, TimbreMacroState, SectionMorphPoint
)
from engine.production.copilot.stepper import (
    ExecutiveCopilotEngine, ProductionPhase, DecisionStatus
)


class TestInstalledPluginScanner:
    """Tests for dynamic VST3 / VST host discovery and semantic classification."""

    def test_scanner_initialization_and_defaults(self):
        scanner = InstalledPluginScanner()
        assert len(scanner.scan_paths) >= 3
        summary = scanner.get_catalog_summary()
        assert summary["status"] == "SUCCESS"
        assert summary["total_discovered"] > 0
        assert summary["vst3_count"] > 0
        assert summary["native_count"] >= 4

    def test_role_classification_coverage(self):
        scanner = InstalledPluginScanner()
        summary = scanner.get_catalog_summary()
        roles = summary["roles"]
        for required_role in ["KEYS", "BASS", "LEAD", "DRUMS", "VOCALS", "FX"]:
            assert required_role in roles
            assert len(roles[required_role]) > 0

    def test_vst_recommendations_per_role(self):
        scanner = InstalledPluginScanner()
        
        keys_rec = scanner.recommend_for_role("KEYS")
        assert keys_rec is not None
        assert "analog lab" in keys_rec.name.lower() or "drift" in keys_rec.name.lower()

        bass_rec = scanner.recommend_for_role("BASS")
        assert bass_rec is not None
        assert "serum" in bass_rec.name.lower() or "bloom" in bass_rec.name.lower() or "drift" in bass_rec.name.lower() or "sublab" in bass_rec.name.lower()

        lead_rec = scanner.recommend_for_role("LEAD")
        assert lead_rec is not None

        vocal_rec = scanner.recommend_for_role("VOCALS")
        assert vocal_rec is not None


class TestAuthenticSampleDrumRackEngine:
    """Tests for authentic local drum sample indexing, validation, and kit building."""

    def test_library_indexing(self):
        engine = AuthenticSampleDrumRackEngine()
        engine.build_sample_index(max_files_per_root=500)
        assert len(engine._sample_index.get("all", [])) > 0

    def test_authentic_sample_resolution(self):
        engine = AuthenticSampleDrumRackEngine()
        sample = engine.find_best_sample("KICK", ["ANAYI.wav", "ASESINO.wav", "kick"])
        assert sample is not None
        assert os.path.exists(sample)
        assert sample.lower().endswith((".wav", ".flac", ".aif"))
        assert os.path.getsize(sample) > 500

    def test_complete_8pad_kit_construction(self):
        engine = AuthenticSampleDrumRackEngine()
        kit = engine.build_kit_spec("Test_Tyler_Kit", "neo_soul_trap")
        assert kit.name == "Test_Tyler_Kit"
        assert len(kit.pads) == 8

        # Verify standard notes are present: C1 (36), D1 (38), D#1 (39), F#1 (42), A#1 (46), C#1 (37), C#2 (49), F#2 (54)
        for note in [36, 38, 39, 42, 46, 37, 49, 54]:
            assert note in kit.pads
            pad = kit.pads[note]
            assert pad.verified is True
            assert os.path.exists(pad.sample_path)
            assert pad.filesize_bytes > 500

    def test_kit_serialization(self):
        engine = AuthenticSampleDrumRackEngine()
        kit = engine.build_kit_spec()
        d = kit.to_dict()
        assert d["total_pads"] == 8
        assert 36 in d["pads"]
        assert d["pads"][36]["role"] == "KICK"


class TestSemanticTimbreMorphEngine:
    """Tests for 96-bar dynamic timbre macros and automation envelope generation."""

    def test_section_morph_roadmap(self):
        plan = SemanticTimbreMorphEngine.get_section_morph_plan()
        assert len(plan) == 8
        assert plan[0].section_name == "Intro"
        assert plan[0].start_bar == 0
        assert plan[-1].section_name == "Outro"
        assert plan[-1].end_bar == 96
        assert plan[-1].end_beat == 384.0

    def test_frequency_and_brightness_mapping(self):
        # 0.0 brightness -> 300 Hz
        hz_min = SemanticTimbreMorphEngine.brightness_to_filter_hz(0.0)
        assert abs(hz_min - 300.0) < 1.0

        # 1.0 brightness -> 20000 Hz
        hz_max = SemanticTimbreMorphEngine.brightness_to_filter_hz(1.0)
        assert abs(hz_max - 20000.0) < 1.0

        # Normalized mapping
        norm_min = SemanticTimbreMorphEngine.frequency_to_normalized(20.0)
        assert abs(norm_min - 0.0) < 0.01
        norm_max = SemanticTimbreMorphEngine.frequency_to_normalized(20000.0)
        assert abs(norm_max - 1.0) < 0.01

    def test_warmth_to_saturator_drive(self):
        drive_0 = SemanticTimbreMorphEngine.warmth_to_saturator_drive(0.0)
        assert drive_0 == 0.0
        drive_full = SemanticTimbreMorphEngine.warmth_to_saturator_drive(1.0)
        assert drive_full == 6.0
        drive_mid = SemanticTimbreMorphEngine.warmth_to_saturator_drive(0.5)
        assert drive_mid == 3.0

    def test_brightness_envelope_points(self):
        pts = SemanticTimbreMorphEngine.generate_brightness_envelope("CHORDS")
        assert len(pts) >= 16
        # Pre-chorus sweep starts at bar 24 (beat 96.0) and ends near bar 32 (beat 128.0)
        sweep_pts = [p for p in pts if 96.0 <= p[0] <= 128.0]
        assert len(sweep_pts) >= 2

    def test_full_automation_manifest(self):
        manifest = SemanticTimbreMorphEngine.generate_full_automation_manifest()
        assert manifest["status"] == "SUCCESS"
        assert manifest["total_bars"] == 96
        assert len(manifest["sections"]) == 8


class TestCopilotPhase3Integration:
    """Tests for ExecutiveCopilotEngine discovering and executing Phase 3 decisions."""

    def test_copilot_discovers_phase3_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0, "devices": []},
            {"name": "Snare & Clap", "track_index": 1, "devices": []},
            {"name": "Hi-Hats", "track_index": 2, "devices": []},
            {"name": "Perc & Foley", "track_index": 3, "devices": []},
            {"name": "808 Sub Bass", "track_index": 4, "devices": []},
            {"name": "Rhodes Piano", "track_index": 5, "devices": []},
            {"name": "Lead Synth", "track_index": 6, "devices": []},
            {"name": "Vocal Chops", "track_index": 7, "devices": []},
        ]
        state = copilot.inspect_session(tracks=mock_tracks)
        pending_ids = [d.id for d in state.pending_decisions]

        # Verify Phase 3 decisions registered
        assert "DEC-P3-01-HOST-VST-SCAN" in pending_ids
        assert any(d.startswith("DEC-P3-02-AUTHENTIC-DRUM-RACK") for d in pending_ids)
        assert any(d.startswith("DEC-P3-03-BASS-INSTRUMENT-LOAD") for d in pending_ids)
        assert any(d.startswith("DEC-P3-04-KEYS-INSTRUMENT-LOAD") for d in pending_ids)
        assert any(d.startswith("DEC-P3-05-LEAD-INSTRUMENT-LOAD") for d in pending_ids)
        assert any(d.startswith("DEC-P3-06-VOCAL-SAMPLER-LOAD") for d in pending_ids)
        assert "DEC-P3-07-ENERGY-TIMBRE-MORPH" in pending_ids

        # Verify phase enum
        for d in state.pending_decisions:
            if d.id.startswith("DEC-P3"):
                assert d.phase == ProductionPhase.PHASE_3_SOUND_DESIGN

    def test_copilot_executes_phase3_vst_scan_decision(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "808 Sub Bass", "track_index": 1},
            {"name": "Rhodes Piano", "track_index": 2},
            {"name": "Lead Synth", "track_index": 3},
            {"name": "Vocal Chops", "track_index": 4},
        ]
        copilot.inspect_session(tracks=mock_tracks)
        
        # Execute VST scan
        res = copilot.execute_decision("DEC-P3-01-HOST-VST-SCAN", choice="YES")
        assert res["status"] == "success"
        assert res["action"] == "APPLIED"
        assert "DEC-P3-01-HOST-VST-SCAN" in copilot.resolved_decisions

    def test_copilot_executes_phase3_timbre_morph_decision(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "808 Sub Bass", "track_index": 1},
            {"name": "Rhodes Piano", "track_index": 2},
        ]
        copilot.inspect_session(tracks=mock_tracks)

        res = copilot.execute_decision("DEC-P3-07-ENERGY-TIMBRE-MORPH", choice="YES")
        assert res["status"] == "success"
        assert res["action"] == "APPLIED"
        assert "DEC-P3-07-ENERGY-TIMBRE-MORPH" in copilot.resolved_decisions

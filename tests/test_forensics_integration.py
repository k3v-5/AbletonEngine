"""
End-to-End Integration Tests for Audio Forensics Engine (PIE Phase 7).
Validates full single-track and multitrack pipelines, cryptographic sealing,
atomic persistence, markdown reporting, and MCP tools.
"""
import pytest
import os
import json
import tempfile
import numpy as np

from engine.forensics import (
    AudioForensicsEngine,
    ForensicsStorage,
    ForensicReportGenerator,
    AnalysisConfig,
    ForensicEventType,
    Severity,
)
from engine.production.graph import ProductionGraph


class TestForensicsIntegration:

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as td:
            storage = ForensicsStorage(base_dir=td)
            yield storage

    def test_end_to_end_track_analysis(self, temp_storage):
        engine = AudioForensicsEngine(storage=temp_storage)
        graph = ProductionGraph(project_id="integration_test_proj")

        sr = 44100
        duration_s = 1.0
        n_samples = int(sr * duration_s)
        t = np.linspace(0, duration_s, n_samples, endpoint=False)

        # Build audio containing:
        # 1. Background signal
        audio = 0.2 * np.sin(2 * np.pi * 300.0 * t)
        # 2. DC offset +0.015
        audio += 0.015
        # 3. Clipping peak at 0.5s
        audio[int(0.5 * sr):int(0.5 * sr) + 10] = 1.0
        # 4. Resonant burst at 3000 Hz from 0.2s to 0.4s
        r_start = int(0.2 * sr)
        r_end = int(0.4 * sr)
        audio[r_start:r_end] += 0.6 * np.sin(2 * np.pi * 3000.0 * t[r_start:r_end])

        stereo = np.stack([audio, audio], axis=0)

        report = engine.analyze_track(
            audio=stereo,
            sample_rate=sr,
            track_id="lead_vocal_bus",
            production_graph=graph,
            save_report=True
        )

        assert report.report_id.startswith("rep_forensic_lead_vocal_bus")
        assert report.duration_seconds == 1.0
        assert report.channels == 2
        assert len(report.events) >= 2
        assert len(report.hypotheses) >= 2
        assert report.deterministic_hash != ""

        # Verify atomic disk persistence and integrity reload
        loaded_report = temp_storage.load_report(report.report_id, verify_hash=True)
        assert loaded_report.report_id == report.report_id
        assert loaded_report.deterministic_hash == report.deterministic_hash
        assert len(loaded_report.events) == len(report.events)

        # Verify markdown generation
        md = ForensicReportGenerator.generate_markdown_summary(loaded_report)
        assert "# Audio Forensic Diagnostic Report" in md
        assert report.deterministic_hash in md

        # Verify ProductionGraph nodes
        assert len(graph.nodes) >= 4

    def test_multitrack_analysis_pipeline(self, temp_storage):
        engine = AudioForensicsEngine(storage=temp_storage)
        sr = 44100
        t = np.linspace(0, 1.0, 44100, endpoint=False)

        # Kick and Sub clash at 55 Hz
        kick = np.zeros(44100)
        kick[10000:20000] = 0.8 * np.sin(2 * np.pi * 55.0 * t[10000:20000])

        sub = np.zeros(44100)
        sub[8000:22000] = 0.7 * np.sin(2 * np.pi * 55.0 * t[8000:22000])

        stems = {"Kick": kick, "Sub_808": sub}
        # Mixbus audio containing clipping
        mixbus = kick + sub
        mixbus[15000:15020] = 1.0

        report = engine.analyze_multitrack(
            stems=stems,
            sample_rate=sr,
            mixbus_audio=mixbus,
            save_report=True
        )

        assert report.report_id.startswith("rep_forensic_multitrack")
        assert len(report.events) >= 1
        # Check that masking between Kick and Sub_808 was detected
        event_types = [e.event_type for e in report.events]
        assert ForensicEventType.MASKING.value in event_types or "MASKING" in event_types

    def test_mcp_forensics_tools(self, monkeypatch):
        from server import forensics_analyze, forensics_report, forensics_events, forensics_explain

        # 1. Analyze fallback buffer
        res_json = forensics_analyze(ctx=None, track_id="Master", preset="default")
        data = json.loads(res_json)
        assert data["status"] == "SUCCESS"
        rep_id = data["report_id"]
        assert data["deterministic_hash"] != ""

        # 2. Get report JSON
        rep_json = forensics_report(ctx=None, report_id=rep_id, format="json")
        rep_data = json.loads(rep_json)
        assert rep_data["report_id"] == rep_id

        # 3. Get report Markdown
        rep_md = forensics_report(ctx=None, report_id=rep_id, format="markdown")
        assert "# Audio Forensic Diagnostic Report" in rep_md

        # 4. Query events
        ev_json = forensics_events(ctx=None, report_id=rep_id)
        ev_data = json.loads(ev_json)
        assert "events" in ev_data

        # 5. Explain non-existent event returns graceful error
        exp_json = forensics_explain(ctx=None, report_id=rep_id, event_id="non_existent_ev")
        exp_data = json.loads(exp_json)
        assert "error" in exp_data

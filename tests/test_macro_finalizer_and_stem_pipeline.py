# tests/test_macro_finalizer_and_stem_pipeline.py
import os
import math
import tempfile
import pytest
from typing import Dict, Any, List

from engine.production.copilot.recipes import MacroProductionRecipes
from engine.audio.stem_bouncer import StemBouncer, StemDefinition
from engine.audio.stem_audit import StemAuditor, PhaseCorrelationStatus


class MockSessionConnection:
    def __init__(self, tracks: List[Dict[str, Any]]):
        self.tracks = tracks
        self.commands = []

    def send_command(self, cmd: str, params: Dict[str, Any] = None) -> Any:
        params = params or {}
        self.commands.append((cmd, params))
        
        if cmd == "get_session_info":
            return {"tempo": 138.0, "num_tracks": len(self.tracks)}
            
        if cmd == "get_track_info":
            t_idx = params.get("track_index", 0)
            if 0 <= t_idx < len(self.tracks):
                return self.tracks[t_idx]
            return {"error": "Track out of range"}
            
        if cmd == "load_instrument_or_effect":
            t_idx = params.get("track_index", 0)
            uri = params.get("uri", "")
            d_name = "Compressor" if "Compressor" in uri else "Device"
            if 0 <= t_idx < len(self.tracks):
                if "devices" not in self.tracks[t_idx]:
                    self.tracks[t_idx]["devices"] = []
                self.tracks[t_idx]["devices"].append({"name": d_name})
            return {"status": "ok", "device_index": 0}
            
        if cmd == "get_device_parameters":
            return {
                "parameters": [
                    {"name": "Device On", "value": 1.0, "index": 0},
                    {"name": "S/C On", "value": 1.0, "index": 20},
                    {"name": "Stereo Width", "value": 1.0, "index": 4},
                    {"name": "Bass Mono", "value": 1.0, "index": 6},
                    {"name": "Bass Freq", "value": 0.38, "index": 7},
                ]
            }
            
        if cmd == "set_device_parameter":
            return {"status": "ok"}
            
        if cmd == "set_track_volume":
            return {"status": "ok"}
            
        if cmd == "set_track_mute":
            return {"status": "ok"}
            
        if cmd == "create_arrangement_automation_envelope":
            return {"status": "ok"}
            
        return {"status": "ok"}


def test_macro_finalize_dynamic_discovery_and_pipeline():
    tracks = [
        {"index": 0, "name": "Kick Drum Rack", "devices": []},
        {"index": 1, "name": "808 Sub Bassline", "devices": [{"name": "Compressor"}]},
        {"index": 2, "name": "Rhodes Chords Piano", "devices": []},
        {"index": 3, "name": "Lead Vocal Audio", "devices": []},
        {"index": 4, "name": "Premaster Bus Track", "devices": []},
    ]
    conn = MockSessionConnection(tracks)
    
    res = MacroProductionRecipes.finalize_mix_and_master(
        conn=conn,
        target_profile="STREAMING",
        pre_drop_bar=33.0
    )
    
    assert res["status"] == "SUCCESS"
    assert res["target_profile"] == "STREAMING"
    assert res["readiness_verdict"] == "READY"
    assert res["pre_drop_vacuum_points"] > 0
    
    # Verify dynamic track discovery
    discovered = res["tracks_discovered"]
    assert discovered["kick"] == 0
    assert discovered["bass"] == 1
    assert discovered["vocal"] == 3
    assert discovered["premaster"] == 4
    assert 2 in discovered["harmony"]
    
    # Verify execution steps
    assert "pre_drop_vacuum_injected" in res["steps_executed"]
    assert "vocal_staging_applied" in res["steps_executed"]
    assert "sidechain_configured" in res["steps_executed"]
    assert "mastering_chain_applied" in res["steps_executed"]
    
    # Verify sidechain & master details
    assert res["sidechain"] is not None
    assert res["mastering_chain"] is not None
    assert res["vocal_staging"] is not None


def test_macro_finalize_flag_toggles():
    tracks = [
        {"index": 0, "name": "Drums"},
        {"index": 1, "name": "Bass"},
    ]
    conn = MockSessionConnection(tracks)
    
    res = MacroProductionRecipes.finalize_mix_and_master(
        conn=conn,
        target_profile="CLUB",
        pre_drop_bar=17.0,
        enable_sidechain=False,
        enable_vocal_staging=False,
        enable_master_chain=False
    )
    
    assert res["status"] == "SUCCESS"
    assert res["target_profile"] == "CLUB"
    assert res["sidechain"] is None
    assert res["mastering_chain"] is None
    assert res["vocal_staging"] is None
    assert "sidechain_configured" not in res["steps_executed"]
    assert "mastering_chain_applied" not in res["steps_executed"]


def test_stem_bouncer_canonical_grouping_and_isolation():
    with tempfile.TemporaryDirectory() as tmpdir:
        bouncer = StemBouncer(export_dir=tmpdir)
        tracks = [
            {"index": 0, "name": "Kick & Snare Drums"},
            {"index": 1, "name": "HiHats & Percs"},
            {"index": 2, "name": "808 Reese Sub Bass"},
            {"index": 3, "name": "Grand Piano Chords"},
            {"index": 4, "name": "Vital Synth Lead Melody"},
            {"index": 5, "name": "Lead Vocal Hook"},
            {"index": 6, "name": "Transition Noise Sweep Riser"},
            {"index": 7, "name": "Ambient Soundscape Layer"}
        ]
        
        plan = bouncer.create_export_plan(tracks, bpm=130.0, start_bar=1.0, end_bar=33.0)
        assert plan.bpm == 130.0
        assert plan.total_bars == 32.0
        
        stems_by_id = {s.stem_id: s for s in plan.stems}
        assert "01_Drums" in stems_by_id
        assert stems_by_id["01_Drums"].track_indices == [0, 1]
        assert "02_Bass" in stems_by_id
        assert stems_by_id["02_Bass"].track_indices == [2]
        assert "03_Keys" in stems_by_id
        assert stems_by_id["03_Keys"].track_indices == [3]
        assert "04_Lead" in stems_by_id
        assert stems_by_id["04_Lead"].track_indices == [4]
        assert "05_Vocals" in stems_by_id
        assert stems_by_id["05_Vocals"].track_indices == [5]
        assert "06_FX" in stems_by_id
        assert stems_by_id["06_FX"].track_indices == [6]
        assert "07_Other" in stems_by_id
        assert stems_by_id["07_Other"].track_indices == [7]
        assert "00_Master" in stems_by_id
        
        # Test isolation pass and reset
        conn = MockSessionConnection(tracks)
        all_indices = [t["index"] for t in tracks]
        iso_res = bouncer.execute_stem_isolation_pass(conn, stems_by_id["01_Drums"], all_indices)
        assert iso_res["status"] == "ISOLATED"
        assert iso_res["active_tracks"] == [0, 1]
        
        # Verify mute commands were dispatched
        mute_cmds = [c for c in conn.commands if c[0] == "set_track_mute"]
        assert len(mute_cmds) == len(all_indices)
        
        reset_ok = bouncer.reset_session_mutes(conn, all_indices)
        assert reset_ok is True


def test_stem_auditor_phase_cross_correlation_forensics():
    # Coherent in-phase
    sig_1 = [0.8 * math.sin(2.0 * math.pi * 60.0 * (i / 48000.0)) for i in range(1200)]
    sig_2 = [0.7 * math.sin(2.0 * math.pi * 60.0 * (i / 48000.0)) for i in range(1200)]
    audit_coh = StemAuditor.audit_stem_phase(sig_1, sig_2, "Kick", "Bass")
    assert audit_coh["status"] == PhaseCorrelationStatus.COHERENT.value
    assert audit_coh["correlation_coefficient"] > 0.95
    
    # Destructive out-of-phase
    sig_inv = [-x for x in sig_1]
    audit_inv = StemAuditor.audit_stem_phase(sig_1, sig_inv, "Kick", "Bass")
    assert audit_inv["status"] == PhaseCorrelationStatus.DESTRUCTIVE_CANCEL.value
    assert audit_inv["correlation_coefficient"] < -0.95
    assert "CRITICAL" in audit_inv["recommendation"]


def test_stem_auditor_headroom_and_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracks = [
            {"index": 0, "name": "Kick Drums"},
            {"index": 1, "name": "808 Bass"},
            {"index": 2, "name": "Lead Synth"},
        ]
        
        # Audio buffers: safe headroom
        audio_buffers = {
            "01_Drums": [0.4 * math.sin(i * 0.05) for i in range(1000)],
            "02_Bass": [0.35 * math.sin(i * 0.05) for i in range(1000)],
            "04_Lead": [0.3 * math.sin(i * 0.1) for i in range(1000)],
            "00_Master": [0.6 * math.sin(i * 0.05) for i in range(1000)],
        }
        
        res = StemAuditor.orchestrate_stem_export_and_audit(
            tracks=tracks,
            export_dir=tmpdir,
            bpm=128.0,
            start_bar=1.0,
            end_bar=17.0,
            audio_buffers=audio_buffers
        )
        
        assert res.ready_for_distribution is True
        assert len(res.stem_metrics) > 0
        for m in res.stem_metrics:
            assert m.headroom_safe is True
            assert m.true_peak_dbtp <= -1.0
            
        assert len(res.phase_correlations) == 1
        assert res.phase_correlations[0]["status"] == PhaseCorrelationStatus.COHERENT.value


def test_export_and_audit_stems_adapter_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracks = [
            {"index": 0, "name": "Kick Drums"},
            {"index": 1, "name": "808 Bass"},
        ]
        conn = MockSessionConnection(tracks)
        
        res = StemAuditor.apply_stem_audit_adapter(
            conn=conn,
            export_dir=tmpdir,
            start_bar=1.0,
            end_bar=33.0
        )
        
        assert res["status"] == "success"
        assert res["ready_for_distribution"] is True
        assert res["stems_count"] >= 2
        assert os.path.exists(res["audit_manifest_path"])

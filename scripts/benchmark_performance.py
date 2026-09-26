#!/usr/bin/env python3
"""
AbletonEngine Performance Benchmark Harness
============================================
Measures and records wall-clock latency across critical engine operations:
  a) Module import/startup overhead (cold imports in isolated subprocesses)
  b) Scanner & Library lookups (InstalledPluginScanner, DecentSampler, DrumRack)
  c) Core Session execution (Full 9-phase CopilotGuidedSession walkthrough)
  d) Session Doctor execution (Diagnosis scan & triage on sample session)
  e) Audio DSP / LUFS validation (K-weighting, True Peak, Block LUFS)
  f) Pytest test suite execution runtimes (lufs, doctor, governance, guided_session)

Supports saving results to JSON, comparison mode (--compare) with percentage
speedups and Markdown export for OPTIMIZATION_REPORT.md.
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _run_subprocess_cold_import(module_name: str) -> Tuple[float, bool, str]:
    """Measures cold import latency of a module in an isolated subprocess."""
    code = (
        "import time, sys; "
        "t0 = time.perf_counter(); "
        f"import {module_name}; "
        "t1 = time.perf_counter(); "
        "print(f'{t1 - t0:.6f}')"
    )
    cmd = [sys.executable, "-c", code]
    try:
        t_start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        t_wall = time.perf_counter() - t_start
        if proc.returncode == 0:
            lines = [ln.strip() for ln in proc.stdout.strip().splitlines() if ln.strip()]
            for line in reversed(lines):
                try:
                    return float(line), True, ""
                except ValueError:
                    continue
            return t_wall, True, ""
        else:
            return t_wall, False, proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 60.0, False, "Timeout expired (60s)"
    except Exception as e:
        return 0.0, False, str(e)


# -----------------------------------------------------------------------------
# Section A: Import Overhead
# -----------------------------------------------------------------------------
def benchmark_imports() -> Dict[str, Any]:
    print("\n[1/6] Benchmarking Module Import & Startup Overhead (Cold Subprocesses)...")
    modules_to_test = [
        ("import_server", "server", "Server Entrypoint & Adapter Setup"),
        ("import_sound_engine", "engine.sound.engine", "SoundEngine Core Interface"),
        ("import_guided_session", "engine.production.copilot.guided_session", "CopilotGuidedSession Wizard"),
        ("import_session_doctor", "engine.production.doctor.session_doctor", "CopilotSessionDoctor Diagnostic"),
        ("import_loudness_analyzer", "engine.mix.loudness_analyzer", "LoudnessAnalyzer Audio DSP"),
    ]

    results = {}
    total_import_time = 0.0

    for metric_key, mod_name, label in modules_to_test:
        sec, success, err = _run_subprocess_cold_import(mod_name)
        total_import_time += sec
        status = "OK" if success else f"FAIL ({err[:30]}...)"
        print(f"  - {label} (`import {mod_name}`): {sec:.4f}s [{status}]")
        results[metric_key] = {
            "name": f"Import {mod_name}",
            "label": label,
            "seconds": round(sec, 6),
            "milliseconds": round(sec * 1000, 2),
            "success": success,
            "error": err if not success else None,
        }

    results["total_cold_imports"] = {
        "name": "Total Cold Imports",
        "label": "Sum of cold imports",
        "seconds": round(total_import_time, 6),
        "milliseconds": round(total_import_time * 1000, 2),
        "success": True,
    }
    return results


# -----------------------------------------------------------------------------
# Section B: Scanner & Library Lookups
# -----------------------------------------------------------------------------
def benchmark_scanners() -> Dict[str, Any]:
    print("\n[2/6] Benchmarking Filesystem Scanners & Library Lookups...")
    results = {}

    # 1. InstalledPluginScanner
    try:
        from engine.instruments.installed_scanner import InstalledPluginScanner
        scanner = InstalledPluginScanner()
        t0 = time.perf_counter()
        plugs = scanner.scan(force_rescan=True)
        t_vst = time.perf_counter() - t0
        print(f"  - InstalledPluginScanner.scan(force_rescan=True): {t_vst:.4f}s ({len(plugs)} plugins found)")
        results["vst_scanner_scan"] = {
            "name": "InstalledPluginScanner.scan",
            "label": "VST/VST3 Directory Scan & Signature Matching",
            "seconds": round(t_vst, 6),
            "milliseconds": round(t_vst * 1000, 2),
            "items_count": len(plugs),
            "success": True,
        }
    except Exception as e:
        print(f"  - InstalledPluginScanner.scan: FAILED ({e})")
        results["vst_scanner_scan"] = {"success": False, "error": str(e), "seconds": 0.0}

    # 2. DecentSamplerLibraryManager.scan_libraries
    try:
        from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
        t0 = time.perf_counter()
        ds_libs = DecentSamplerLibraryManager.scan_libraries(require_valid=False)
        t_ds_scan = time.perf_counter() - t0
        print(f"  - DecentSamplerLibraryManager.scan_libraries(): {t_ds_scan:.4f}s ({len(ds_libs)} libraries scanned)")
        results["decent_sampler_scan_libraries"] = {
            "name": "DecentSamplerLibraryManager.scan_libraries",
            "label": "Decent Sampler Directory Audit & Preset Validation",
            "seconds": round(t_ds_scan, 6),
            "milliseconds": round(t_ds_scan * 1000, 2),
            "items_count": len(ds_libs),
            "success": True,
        }
    except Exception as e:
        print(f"  - DecentSamplerLibraryManager.scan_libraries: FAILED ({e})")
        results["decent_sampler_scan_libraries"] = {"success": False, "error": str(e), "seconds": 0.0}

    # 3. DecentSamplerLibraryManager.get_libraries_for_role (6 roles)
    try:
        from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
        roles = ["KEYS", "BASS", "LEAD", "PAD", "DRUMS", "VOCALS"]
        t0 = time.perf_counter()
        role_counts = {}
        for r in roles:
            matched = DecentSamplerLibraryManager.get_libraries_for_role(r)
            role_counts[r] = len(matched)
        t_ds_roles = time.perf_counter() - t0
        print(f"  - DecentSamplerLibraryManager.get_libraries_for_role (6 roles): {t_ds_roles:.4f}s (avg {t_ds_roles/len(roles):.4f}s/role)")
        results["decent_sampler_roles_lookup"] = {
            "name": "DecentSamplerLibraryManager.get_libraries_for_role (6 roles)",
            "label": "Decent Sampler Multi-Role Filter Sweeps",
            "seconds": round(t_ds_roles, 6),
            "milliseconds": round(t_ds_roles * 1000, 2),
            "roles_evaluated": len(roles),
            "avg_per_role_ms": round((t_ds_roles / len(roles)) * 1000, 2),
            "success": True,
        }
    except Exception as e:
        print(f"  - DecentSamplerLibraryManager.get_libraries_for_role: FAILED ({e})")
        results["decent_sampler_roles_lookup"] = {"success": False, "error": str(e), "seconds": 0.0}

    # 4. AuthenticSampleDrumRackEngine.build_sample_index
    try:
        from engine.sound.drum_rack.authentic_builder import AuthenticSampleDrumRackEngine
        drum_engine = AuthenticSampleDrumRackEngine()
        t0 = time.perf_counter()
        drum_engine.build_sample_index()
        t_drums = time.perf_counter() - t0
        samples_count = len(drum_engine._sample_index.get("all", []))
        print(f"  - AuthenticSampleDrumRackEngine.build_sample_index(): {t_drums:.4f}s ({samples_count} samples indexed)")
        results["drum_rack_build_sample_index"] = {
            "name": "AuthenticSampleDrumRackEngine.build_sample_index",
            "label": "Drum Rack Sample Library Indexing & Fallback Generation",
            "seconds": round(t_drums, 6),
            "milliseconds": round(t_drums * 1000, 2),
            "samples_count": samples_count,
            "success": True,
        }
    except Exception as e:
        print(f"  - AuthenticSampleDrumRackEngine.build_sample_index: FAILED ({e})")
        results["drum_rack_build_sample_index"] = {"success": False, "error": str(e), "seconds": 0.0}

    # Total scanner operations
    total_scanners = sum(v.get("seconds", 0.0) for v in results.values())
    results["total_scanner_operations"] = {
        "name": "Total Scanner Operations",
        "label": "Cumulative scanning and library traversal time",
        "seconds": round(total_scanners, 6),
        "milliseconds": round(total_scanners * 1000, 2),
        "success": True,
    }
    return results


# -----------------------------------------------------------------------------
# Section C: Core Session Execution (CopilotGuidedSession)
# -----------------------------------------------------------------------------
def benchmark_guided_session() -> Dict[str, Any]:
    print("\n[3/6] Benchmarking Core Guided Session (9-Phase Walkthrough)...")
    results = {}

    import numpy as np
    import soundfile as sf
    from engine.adapters.mock_adapter import MockAbletonAdapter
    from engine.production.copilot.guided_session import CopilotGuidedSession

    # Prepare compliant test wav for Phase 9 Mix/Master offline validation
    mcp_dir = Path.home() / ".mcp_analysis"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    test_wav = mcp_dir / "benchmark_phase9_master.wav"

    sr = 44100
    dur = 5.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    sig = 0.28 * np.sin(2 * np.pi * 440.0 * t)
    stereo = np.vstack([sig, sig])
    sf.write(str(test_wav), stereo.T, sr)

    adapter = MockAbletonAdapter()
    session = CopilotGuidedSession()
    session.reset()

    comp_payload = {
        "bpm": 120.0,
        "key": "F",
        "scale": "natural_minor",
        "genre": "trap",
        "composition": {
            "0": {"all": [{"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 127}]},
            "DRUMS": {"all": [{"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 100}]},
            "KEYS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "PAD": {"all": [{"pitch": 65, "start_time": 0.0, "duration": 4.0, "velocity": 80}]},
            "BASS": {"all": [{"pitch": 29, "start_time": 0.0, "duration": 0.5, "velocity": 120}]},
            "LEAD": {"all": [{"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}]},
        },
    }

    t_total_start = time.perf_counter()

    # Phase 1: Scaffolding
    t0 = time.perf_counter()
    session.step(conn=adapter, user_input="Opción A")
    t_p1 = time.perf_counter() - t0

    # Phase 2: Sections
    t0 = time.perf_counter()
    session.step(conn=adapter, user_input="Opción B")
    t_p2 = time.perf_counter() - t0

    # Phase 3: Instruments (5 tracks)
    t0 = time.perf_counter()
    for _ in range(5):
        session.step(conn=adapter, user_input="Opción 1")
    t_p3 = time.perf_counter() - t0

    # Phase 4: Param Sculpting (5 tracks)
    t0 = time.perf_counter()
    for _ in range(5):
        session.step(conn=adapter, user_input="Opción 1")
    t_p4 = time.perf_counter() - t0

    # Phase 5: Insert Effects
    t0 = time.perf_counter()
    while session.data.get("current_phase") == "PHASE_5_INSERT_EFFECTS":
        session.step(conn=adapter, user_input="Opción 1")
    t_p5 = time.perf_counter() - t0

    # Phase 6: Composition
    t0 = time.perf_counter()
    session.step(conn=adapter, user_input=f"```json\n{json.dumps(comp_payload)}\n```")
    t_p6 = time.perf_counter() - t0

    # Phase 7: Automation
    t0 = time.perf_counter()
    session.step(conn=adapter, user_input="Opción 1")
    t_p7 = time.perf_counter() - t0

    # Phase 8: Vocal Ducking
    t0 = time.perf_counter()
    session.step(conn=adapter, user_input="Opción A")
    t_p8 = time.perf_counter() - t0

    # Phase 9: Mix & Master
    t0 = time.perf_counter()
    res9 = session.step(conn=adapter, user_input="Club a -8.5 LUFS")
    t_p9 = time.perf_counter() - t0

    t_total_session = time.perf_counter() - t_total_start

    print(f"  - Phase 1 (Scaffolding): {t_p1:.4f}s")
    print(f"  - Phase 2 (Sections): {t_p2:.4f}s")
    print(f"  - Phase 3 (Instruments x5): {t_p3:.4f}s")
    print(f"  - Phase 4 (Param Sculpting x5): {t_p4:.4f}s")
    print(f"  - Phase 5 (Insert Effects): {t_p5:.4f}s")
    print(f"  - Phase 6 (Composition): {t_p6:.4f}s")
    print(f"  - Phase 7 (Automation): {t_p7:.4f}s")
    print(f"  - Phase 8 (Vocal Ducking): {t_p8:.4f}s")
    print(f"  - Phase 9 (Mix & Master): {t_p9:.4f}s [status: {res9.get('status', 'UNKNOWN')}]")
    print(f"  => Total Guided Session (Phases 1-9): {t_total_session:.4f}s")

    phase_metrics = [
        ("phase_1_scaffolding", "Phase 1: Scaffolding", t_p1),
        ("phase_2_sections", "Phase 2: Sections", t_p2),
        ("phase_3_instruments", "Phase 3: Instruments (5 tracks)", t_p3),
        ("phase_4_param_sculpting", "Phase 4: Synthesis Sculpting (5 tracks)", t_p4),
        ("phase_5_insert_effects", "Phase 5: Insert Effects Chains", t_p5),
        ("phase_6_composition", "Phase 6: Composition MIDI Generation", t_p6),
        ("phase_7_automation", "Phase 7: Dynamic Automation Injection", t_p7),
        ("phase_8_vocal_ducking", "Phase 8: Vocal Ducking Calibration", t_p8),
        ("phase_9_mix_master", "Phase 9: Mix, Master & LUFS Gatekeeper", t_p9),
    ]

    for key, label, val in phase_metrics:
        results[key] = {
            "name": label,
            "label": label,
            "seconds": round(val, 6),
            "milliseconds": round(val * 1000, 2),
            "success": True,
        }

    results["total_guided_session_walkthrough"] = {
        "name": "Total Guided Session Walkthrough",
        "label": "Full 9-Phase End-to-End Guided Session Progression",
        "seconds": round(t_total_session, 6),
        "milliseconds": round(t_total_session * 1000, 2),
        "is_complete": session.data.get("is_complete", False),
        "certified_status": res9.get("status"),
        "success": True,
    }
    return results


# -----------------------------------------------------------------------------
# Section D: Session Doctor Execution
# -----------------------------------------------------------------------------
def benchmark_session_doctor() -> Dict[str, Any]:
    print("\n[4/6] Benchmarking Session Doctor (Diagnosis & Triage)...")
    results = {}

    from engine.production.doctor.session_doctor import CopilotSessionDoctor

    class MockDoctorLiveConnection:
        def __init__(self):
            self.tracks = [
                {
                    "name": "Kick Hot",
                    "track_index": 0,
                    "volume": 0.95,
                    "panning": 0.0,
                    "is_muted": False,
                    "clips": [{"clip_index": 0, "name": "Kick Loop", "notes_count": 16, "length": 16.0}],
                    "devices": [{"name": "EQ Eight"}, {"name": "EQ Eight"}],  # Duplicate EQ
                },
                {
                    "name": "Ghost Synth",
                    "track_index": 1,
                    "volume": 0.75,
                    "panning": 0.0,
                    "is_muted": False,
                    "clips": [],  # Orphan track
                    "devices": [],
                },
                {
                    "name": "Sub Bassline",
                    "track_index": 2,
                    "volume": 0.75,
                    "panning": 0.0,
                    "is_muted": True,  # Muted active track
                    "clips": [{"clip_index": 0, "name": "Sub", "notes_count": 16, "length": 8.0}],
                    "devices": [{"name": "Wavetable"}],  # Missing Channel EQ
                },
                {
                    "name": "Dead Clip Track",
                    "track_index": 3,
                    "volume": 0.75,
                    "panning": 0.0,
                    "is_muted": False,
                    "clips": [{"clip_index": 0, "name": "Silent", "notes_count": 0, "length": 4.0}],
                    "devices": [{"name": "Simpler"}],
                },
            ]
            self.master = {
                "volume": 0.92,
                "panning": 0.0,
                "devices": [{"name": "EQ Eight"}],  # Unmastered bus
            }

        def send_command(self, cmd: str, params: Optional[dict] = None) -> dict:
            params = params or {}
            if cmd == "get_session_info":
                return {
                    "track_count": len(self.tracks),
                    "num_tracks": len(self.tracks),
                    "tempo": 128.0,
                    "master_track": self.master,
                }
            if cmd == "get_track_info":
                t_idx = params.get("track_index", 0)
                if 0 <= t_idx < len(self.tracks):
                    return self.tracks[t_idx]
            return {"status": "ok"}

    state_tmp = PROJECT_ROOT / "state" / "benchmark_doctor_temp.json"
    doctor = CopilotSessionDoctor(state_file=state_tmp)
    conn = MockDoctorLiveConnection()

    # 1. Full Diagnostic Scan
    t0 = time.perf_counter()
    diag_res = doctor.step(conn, reset=True)
    t_diag = time.perf_counter() - t0

    issues_count = len(doctor.data.get("issues_queue", []))
    status = diag_res.get("status", "UNKNOWN")
    print(f"  - CopilotSessionDoctor.step(reset=True): {t_diag:.4f}s ({issues_count} issues detected, status: {status})")

    # 2. Interactive Triage Step
    t0 = time.perf_counter()
    triage_res = doctor.step(conn, user_input="Opción 1")
    t_triage = time.perf_counter() - t0
    print(f"  - CopilotSessionDoctor.step(user_input): {t_triage:.4f}s (triage action)")

    # Clean up temp state
    try:
        if state_tmp.exists():
            state_tmp.unlink()
    except Exception:
        pass

    results["doctor_diagnostic_scan"] = {
        "name": "CopilotSessionDoctor Diagnostic Scan",
        "label": "Full Session Health & Invariant Audit",
        "seconds": round(t_diag, 6),
        "milliseconds": round(t_diag * 1000, 2),
        "issues_detected": issues_count,
        "success": True,
    }
    results["doctor_triage_step"] = {
        "name": "CopilotSessionDoctor Triage Step",
        "label": "Interactive Doctor Repair Decision & State Commit",
        "seconds": round(t_triage, 6),
        "milliseconds": round(t_triage * 1000, 2),
        "success": True,
    }
    results["total_doctor_operations"] = {
        "name": "Total Doctor Operations",
        "label": "Combined diagnosis and repair time",
        "seconds": round(t_diag + t_triage, 6),
        "milliseconds": round((t_diag + t_triage) * 1000, 2),
        "success": True,
    }
    return results


# -----------------------------------------------------------------------------
# Section E: Audio DSP / LUFS Validation
# -----------------------------------------------------------------------------
def benchmark_audio_dsp(repeats: int = 3) -> Dict[str, Any]:
    print(f"\n[5/6] Benchmarking Audio DSP & LUFS Validation ({repeats} iterations per metric)...")
    results = {}

    import numpy as np
    from engine.mix.loudness_analyzer import LoudnessAnalyzer

    # Generate a deterministic 5.0-second stereo audio buffer (44.1 kHz, 2 channels)
    sr = 44100
    duration_s = 5.0
    np.random.seed(42)
    audio = np.random.uniform(-0.5, 0.5, (2, int(sr * duration_s))).astype(np.float64)

    # 1. K-weighting filter (_apply_k_weighting)
    kw_times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        _ = LoudnessAnalyzer._apply_k_weighting(audio.copy(), sr)
        kw_times.append(time.perf_counter() - t0)

    mean_kw = float(np.mean(kw_times))
    min_kw = float(np.min(kw_times))
    print(f"  - LoudnessAnalyzer._apply_k_weighting (5s audio): mean={mean_kw:.4f}s, min={min_kw:.4f}s")
    results["dsp_k_weighting_5s"] = {
        "name": "LoudnessAnalyzer._apply_k_weighting (5s audio)",
        "label": "ITU-R BS.1770-5 K-weighting Biquad Filtering (220.5k samples)",
        "seconds": round(mean_kw, 6),
        "milliseconds": round(mean_kw * 1000, 2),
        "min_seconds": round(min_kw, 6),
        "repeats": repeats,
        "success": True,
    }

    # 2. True Peak calculation (calculate_true_peak)
    tp_times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        _ = LoudnessAnalyzer.calculate_true_peak(audio, oversample_factor=4)
        tp_times.append(time.perf_counter() - t0)

    mean_tp = float(np.mean(tp_times))
    min_tp = float(np.min(tp_times))
    print(f"  - LoudnessAnalyzer.calculate_true_peak (4x oversample): mean={mean_tp:.4f}s, min={min_tp:.4f}s")
    results["dsp_true_peak_5s"] = {
        "name": "LoudnessAnalyzer.calculate_true_peak (4x oversample)",
        "label": "Annex 2 4x Sinc Oversampling True Peak Detection",
        "seconds": round(mean_tp, 6),
        "milliseconds": round(mean_tp * 1000, 2),
        "min_seconds": round(min_tp, 6),
        "repeats": repeats,
        "success": True,
    }

    # 3. Full Integrated LUFS with block gating (calculate_lufs_with_blocks)
    lufs_times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        _ = LoudnessAnalyzer.calculate_lufs_with_blocks(audio, sr)
        lufs_times.append(time.perf_counter() - t0)

    mean_lufs = float(np.mean(lufs_times))
    min_lufs = float(np.min(lufs_times))
    print(f"  - LoudnessAnalyzer.calculate_lufs_with_blocks (5s audio): mean={mean_lufs:.4f}s, min={min_lufs:.4f}s")
    results["dsp_calculate_lufs_with_blocks_5s"] = {
        "name": "LoudnessAnalyzer.calculate_lufs_with_blocks",
        "label": "BS.1770-5 Gated Loudness & Short-Term LUFS Integration",
        "seconds": round(mean_lufs, 6),
        "milliseconds": round(mean_lufs * 1000, 2),
        "min_seconds": round(min_lufs, 6),
        "repeats": repeats,
        "success": True,
    }

    total_dsp = mean_kw + mean_tp + mean_lufs
    results["total_audio_dsp"] = {
        "name": "Total Audio DSP Pipeline (5s audio)",
        "label": "Combined filtering, peak detection, and loudness integration",
        "seconds": round(total_dsp, 6),
        "milliseconds": round(total_dsp * 1000, 2),
        "success": True,
    }
    return results


# -----------------------------------------------------------------------------
# Section F: Pytest Test Suite Execution Runtimes
# -----------------------------------------------------------------------------
def benchmark_pytest_suites() -> Dict[str, Any]:
    print("\n[6/6] Benchmarking Pytest Test Suite Runtimes...")
    suites = [
        ("pytest_lufs_validation_gate", "tests/test_lufs_validation_gate.py", "LUFS Validation Gate Tests (7 tests)"),
        ("pytest_session_doctor", "tests/test_session_doctor.py", "Session Doctor Diagnostics Tests (15 tests)"),
        ("pytest_governance", "tests/governance/", "Governance & Cryptographic Ledger Tests (67 tests)"),
        ("pytest_guided_session", "tests/test_guided_session.py", "Guided Session Core Workflow Tests (32 tests)"),
    ]

    results = {}
    total_pytest_time = 0.0

    for metric_key, test_path, label in suites:
        print(f"  - Running `pytest {test_path}` ({label})...", flush=True)
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-q"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        t_run = time.perf_counter() - t0
        total_pytest_time += t_run

        passed = proc.returncode == 0
        last_line = ""
        for line in reversed(proc.stdout.strip().splitlines()):
            if "passed" in line or "failed" in line:
                last_line = line.strip()
                break

        status_str = f"PASSED ({last_line})" if passed else f"FAILED (code {proc.returncode})"
        print(f"    => {t_run:.2f}s [{status_str}]")

        results[metric_key] = {
            "name": f"pytest {test_path}",
            "label": label,
            "path": test_path,
            "seconds": round(t_run, 4),
            "milliseconds": round(t_run * 1000, 2),
            "exit_code": proc.returncode,
            "summary": last_line,
            "success": passed,
        }

    results["total_pytest_runtime"] = {
        "name": "Total Pytest Runtime",
        "label": "Cumulative execution time for 4 primary test suites (121 tests)",
        "seconds": round(total_pytest_time, 4),
        "milliseconds": round(total_pytest_time * 1000, 2),
        "success": True,
    }
    return results


# -----------------------------------------------------------------------------
# Comparison & Report Generator
# -----------------------------------------------------------------------------
def compare_benchmarks(
    baseline_data: Dict[str, Any],
    current_data: Dict[str, Any],
    as_markdown: bool = False,
) -> str:
    """Compares baseline vs current benchmarks and outputs formatted table."""
    base_metrics = baseline_data.get("metrics", {})
    curr_metrics = current_data.get("metrics", {})

    categories = [
        ("imports", "1. Module Import & Startup Overhead"),
        ("scanners", "2. Scanner & Library Lookups"),
        ("session", "3. Core Guided Session Execution"),
        ("doctor", "4. Session Doctor Execution"),
        ("dsp", "5. Audio DSP & LUFS Validation"),
        ("pytest", "6. Pytest Test Suite Runtimes"),
    ]

    rows = []
    for cat_key, cat_title in categories:
        b_cat = base_metrics.get(cat_key, {})
        c_cat = curr_metrics.get(cat_key, {})
        keys = list(dict.fromkeys(list(b_cat.keys()) + list(c_cat.keys())))

        for k in keys:
            b_item = b_cat.get(k, {})
            c_item = c_cat.get(k, {})
            name = c_item.get("name") or b_item.get("name") or k
            b_sec = b_item.get("seconds")
            c_sec = c_item.get("seconds")

            if b_sec is not None and c_sec is not None:
                delta = c_sec - b_sec
                speedup_pct = ((b_sec - c_sec) / b_sec * 100.0) if b_sec > 0 else 0.0
                ratio = (b_sec / c_sec) if c_sec > 0 else float("inf")
                rows.append((cat_title, name, b_sec, c_sec, delta, speedup_pct, ratio))
            elif b_sec is not None:
                rows.append((cat_title, name, b_sec, 0.0, 0.0, 0.0, 1.0))
            elif c_sec is not None:
                rows.append((cat_title, name, 0.0, c_sec, 0.0, 0.0, 1.0))

    if as_markdown:
        out = []
        out.append("| Subsystem / Operation | Baseline (s) | Optimized (s) | Delta (s) | Speedup (%) | Factor |")
        out.append("|:---|---:|---:|---:|---:|---:|")
        last_cat = None
        for cat, name, b_s, c_s, delta, pct, rat in rows:
            if cat != last_cat:
                out.append(f"| **{cat}** | | | | | |")
                last_cat = cat
            delta_str = f"{delta:+.4f}s"
            pct_str = f"{pct:+.1f}%" if pct != 0.0 else "0.0%"
            rat_str = f"{rat:.2f}x" if rat < 1000 else f"{rat:.1f}x"
            out.append(f"| {name} | {b_s:.4f}s | {c_s:.4f}s | {delta_str} | {pct_str} | {rat_str} |")
        return "\n".join(out)
    else:
        out = []
        out.append("=" * 110)
        out.append(f"{'PERFORMANCE COMPARISON REPORT: BASELINE vs OPTIMIZED':^110}")
        out.append("=" * 110)
        header = f"{'Benchmark Metric':<46} | {'Baseline':>10} | {'Current':>10} | {'Delta':>11} | {'Speedup':>9} | {'Factor':>8}"
        out.append(header)
        out.append("-" * 110)
        last_cat = None
        for cat, name, b_s, c_s, delta, pct, rat in rows:
            if cat != last_cat:
                out.append(f"\n[{cat}]")
                last_cat = cat
            delta_str = f"{delta:+.4f}s"
            pct_str = f"{pct:+.1f}%" if pct != 0.0 else "0.0%"
            rat_str = f"{rat:.2f}x" if rat < 1000 else f"{rat:.1f}x"
            out.append(f"{name:<46} | {b_s:>9.4f}s | {c_s:>9.4f}s | {delta_str:>11} | {pct_str:>9} | {rat_str:>8}")
        out.append("=" * 110)
        return "\n".join(out)


# -----------------------------------------------------------------------------
# Main Runner
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="AbletonEngine Comprehensive Performance Benchmark Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="scripts/benchmark_baseline.json",
        help="Path to save benchmark JSON output (default: scripts/benchmark_baseline.json)",
    )
    parser.add_argument(
        "--compare",
        "-c",
        type=str,
        default=None,
        help="Compare current benchmark against an existing baseline JSON file",
    )
    parser.add_argument(
        "--compare-only",
        nargs=2,
        metavar=("BASELINE_JSON", "CURRENT_JSON"),
        help="Compare two already recorded JSON files without re-running tests",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip long-running pytest suites (useful for rapid micro-benchmarking)",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Comma-separated categories to run: imports, scanners, session, doctor, dsp, pytest",
    )
    parser.add_argument(
        "--markdown",
        nargs="?",
        const=True,
        default=False,
        help="Output comparison table in GitHub Markdown format (optionally specify file path to write to)",
    )
    parser.add_argument(
        "--dsp-repeats",
        type=int,
        default=3,
        help="Number of iterations for DSP micro-benchmarks (default: 3)",
    )

    args = parser.parse_args()

    # Handle compare-only mode
    if args.compare_only:
        p_base = Path(args.compare_only[0])
        p_curr = Path(args.compare_only[1])
        if not p_base.exists():
            sys.exit(f"Error: Baseline file not found: {p_base}")
        if not p_curr.exists():
            sys.exit(f"Error: Current file not found: {p_curr}")
        base_data = json.loads(p_base.read_text(encoding="utf-8"))
        curr_data = json.loads(p_curr.read_text(encoding="utf-8"))
        as_md = bool(args.markdown)
        report = compare_benchmarks(base_data, curr_data, as_markdown=as_md)
        print(report)
        if isinstance(args.markdown, str) and args.markdown.lower() not in ("true", "1"):
            md_path = PROJECT_ROOT / args.markdown
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(report, encoding="utf-8")
            print(f"Markdown comparison report saved to: {md_path.resolve()}")
        return

    selected_categories = set(args.only.split(",")) if args.only else {"imports", "scanners", "session", "doctor", "dsp", "pytest"}
    if args.skip_pytest and "pytest" in selected_categories:
        selected_categories.remove("pytest")

    print("=" * 80)
    print("AbletonEngine Performance Benchmark Harness")
    print(f"Platform: {platform.platform()} | Python {platform.python_version()}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Target Output: {args.output}")
    print(f"Selected Categories: {', '.join(sorted(selected_categories))}")
    print("=" * 80)

    t_global_start = time.perf_counter()
    metrics: Dict[str, Any] = {}

    if "imports" in selected_categories:
        metrics["imports"] = benchmark_imports()
    if "scanners" in selected_categories:
        metrics["scanners"] = benchmark_scanners()
    if "session" in selected_categories:
        metrics["session"] = benchmark_guided_session()
    if "doctor" in selected_categories:
        metrics["doctor"] = benchmark_session_doctor()
    if "dsp" in selected_categories:
        metrics["dsp"] = benchmark_audio_dsp(repeats=args.dsp_repeats)
    if "pytest" in selected_categories:
        metrics["pytest"] = benchmark_pytest_suites()

    t_global_end = time.perf_counter()
    total_wall_clock = t_global_end - t_global_start

    print("\n" + "=" * 80)
    print(f"Benchmark Run Completed in {total_wall_clock:.2f}s ({total_wall_clock/60:.2f} min)")
    print("=" * 80)

    # Package benchmark payload
    payload = {
        "metadata": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cwd": str(PROJECT_ROOT),
        },
        "summary": {
            "total_wall_clock_seconds": round(total_wall_clock, 4),
            "categories_evaluated": sorted(list(selected_categories)),
        },
        "metrics": metrics,
    }

    # Save to output file
    out_path = PROJECT_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Benchmark results successfully saved to: {out_path.resolve()}")

    # Compare against baseline if requested
    if args.compare:
        comp_path = PROJECT_ROOT / args.compare
        if not comp_path.exists():
            print(f"\nWarning: Comparison baseline file not found: {comp_path}")
        else:
            base_data = json.loads(comp_path.read_text(encoding="utf-8"))
            as_md = bool(args.markdown)
            report = compare_benchmarks(base_data, payload, as_markdown=as_md)
            print("\n" + report)
            if isinstance(args.markdown, str) and args.markdown.lower() not in ("true", "1"):
                md_path = PROJECT_ROOT / args.markdown
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(report, encoding="utf-8")
                print(f"Markdown comparison report saved to: {md_path.resolve()}")


if __name__ == "__main__":
    main()

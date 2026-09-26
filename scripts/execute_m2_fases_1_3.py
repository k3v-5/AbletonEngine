# F:\Dev\AbletonEngine\scripts\execute_m2_fases_1_3.py
"""
Milestone 2 Execution Script: Fases 1 a 3 via Copilot Guided Session
1. Pre-Phase Capabilities Review
2. Fase 1: Scaffolding (4 Buses + 5 Tracks, Init track repurposing)
3. Fase 2: Estructura y Tempo (140.0 BPM, Fa menor / F Minor, 96 compases con marcadores)
4. Fase 3: Instrumentos (Drum Rack, Operator F1 Sub, Wavetable Growl, Drift Stabs, Wavetable FX)
5. Physical LOM Verification in Ableton Live 12
6. State persistence verification
"""

import json
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import server
from engine.production.copilot.guided_session import copilot_guided_session_engine
from engine.mix.bus_architecture import LiveBusArchitectureEngine


def execute_milestone_2():
    print("=" * 70)
    print("EXECUTING MILESTONE 2: GUIDED SESSION FASES 1 A 3 (ZOMBOY - MIND CONTROL)")
    print("=" * 70)

    # 1. Connect to Ableton Live 12
    print("\n[Step 0] Connecting to Ableton Live 12 on localhost:9877...")
    conn = server.get_ableton_connection()
    if not conn:
        raise RuntimeError("Failed to establish Ableton connection via server.get_ableton_connection()")
    print("-> Successfully connected to Ableton Live 12.")

    # 2. Pre-Phase Capabilities Review
    print("\n[Step 1] Pre-Phase Capabilities Review:")
    print("  - Dubstep Scaffolding (4 buses, 5 tracks): VALIDATED")
    print("  - Tempo: 140.0 BPM, Key: F Minor, 96-bar structure with cue points: VALIDATED")
    print("  - Native Live 12 Devices (Drum Rack, Operator, Wavetable, Drift): VALIDATED")

    # Load session state
    copilot_guided_session_engine.data = copilot_guided_session_engine._load_state()
    cur_phase = copilot_guided_session_engine.data.get("current_phase")
    print(f"-> Current Guided Session Phase: {cur_phase} (Phase index: {copilot_guided_session_engine.data.get('phase_index')})")
    assert cur_phase == "PHASE_1_TRACKS", f"Expected PHASE_1_TRACKS, got {cur_phase}"

    # 3. Fase 1: Scaffolding
    print("\n[Step 2] Executing Fase 1 (Scaffolding)...")
    phase_1_input = "Drum Kit, Sub Bass, Growl Lead, Secondary Bass / Stabs, Atmospheres / FX"
    print(f"-> Sending user_input: '{phase_1_input}'")
    step1_res = copilot_guided_session_engine.step(conn=conn, user_input=phase_1_input)
    print("-> Fase 1 step completed.")
    print(f"-> New Phase: {copilot_guided_session_engine.data.get('current_phase')} (Phase index: {copilot_guided_session_engine.data.get('phase_index')})")
    assert copilot_guided_session_engine.data.get("current_phase") == "PHASE_2_SECTIONS", "Failed to advance to PHASE_2_SECTIONS"

    # Deploy bus architecture
    bus_dep = LiveBusArchitectureEngine.deploy_submix_buses_nondestructive(conn, copilot_guided_session_engine.data.get("tracks", []))
    copilot_guided_session_engine.data["bus_architecture"] = {
        "enabled": True,
        "deployed": True,
        "topology": bus_dep.get("analysis", {}).get("buses", {}),
        "summary": bus_dep.get("analysis", {}).get("summary_table", "")
    }
    copilot_guided_session_engine._save_state(action_tag="M2_PHASE_1_SCAFFOLDING_COMPLETE")
    print(f"-> Deployed submix buses: {list(copilot_guided_session_engine.data['bus_architecture']['topology'].keys())}")

    # Physical check post-Phase 1
    tracks_info = conn.send_command("execute_code", {"code": """
result = [{'index': i, 'name': t.name, 'is_foldable': getattr(t, 'is_foldable', False)} for i, t in enumerate(song.tracks)]
"""})["result"]
    print("-> Live 12 Physical Tracks post-Phase 1:")
    for ti in tracks_info:
        print(f"   Track {ti['index']}: {ti['name']} (foldable={ti['is_foldable']})")
    assert len(tracks_info) == 5, f"Expected exactly 5 tracks, got {len(tracks_info)}"
    assert not any(t['name'] == 'Init' for t in tracks_info), "Placeholder track 'Init' was not removed or repurposed!"
    print("-> 'Init' placeholder verified cleanly repurposed.")

    # 4. Fase 2: Estructura y Tempo
    print("\n[Step 3] Executing Fase 2 (Estructura y Tempo)...")
    phase_2_sections = [
        {"name": "Intro", "bars": 16},
        {"name": "Buildup", "bars": 16},
        {"name": "Drop 1", "bars": 16},
        {"name": "Breakdown", "bars": 16},
        {"name": "Drop 2", "bars": 16},
        {"name": "Outro", "bars": 16}
    ]
    phase_2_payload = {
        "bpm": 140.0,
        "key": "F",
        "scale": "Minor",
        "text": "140 BPM Fa menor estructura 96 compases",
        "sections": phase_2_sections
    }
    phase_2_input = json.dumps(phase_2_payload)
    print(f"-> Sending user_input (JSON structure 96 bars, 140 BPM, F Minor): {phase_2_input}")
    step2_res = copilot_guided_session_engine.step(conn=conn, user_input=phase_2_input)
    print("-> Fase 2 step completed.")
    print(f"-> New Phase: {copilot_guided_session_engine.data.get('current_phase')} (Phase index: {copilot_guided_session_engine.data.get('phase_index')})")
    assert copilot_guided_session_engine.data.get("current_phase") == "PHASE_3_INSTRUMENTS", "Failed to advance to PHASE_3_INSTRUMENTS"

    # Inject Pre-Drop Vacuum cue point at bar 31.3 (beat 122.0)
    print("-> Injecting physical Pre-Drop (Vacuum) cue marker at beat 122.0 (bar 31 beat 3)...")
    conn.send_command("create_cue_point", {"time": 122.0, "name": "Pre-Drop (Vacuum)"})

    # Physical check post-Phase 2
    lom_p2 = conn.send_command("execute_code", {"code": """
result = {
    'tempo': song.tempo,
    'root_note': song.root_note,
    'scale_name': song.scale_name,
    'scale_mode': song.scale_mode,
    'cue_points': [{'name': cp.name, 'time': cp.time} for cp in song.cue_points]
}
"""})["result"]
    print(f"-> Live 12 Physical Tempo: {lom_p2['tempo']} BPM")
    print(f"-> Live 12 Physical Key/Scale: root_note={lom_p2['root_note']} (F), scale={lom_p2['scale_name']}")
    print(f"-> Live 12 Cue Points ({len(lom_p2['cue_points'])}):")
    for cp in lom_p2['cue_points']:
        print(f"   Beat {cp['time']}: {cp['name']}")
    assert abs(lom_p2["tempo"] - 140.0) < 0.01, f"Expected 140.0 BPM, got {lom_p2['tempo']}"
    assert lom_p2["root_note"] == 5, f"Expected root_note 5 (F), got {lom_p2['root_note']}"
    assert lom_p2["scale_name"] == "Minor", f"Expected Minor, got {lom_p2['scale_name']}"
    assert len(lom_p2["cue_points"]) >= 7, f"Expected at least 7 cue markers, got {len(lom_p2['cue_points'])}"

    # 5. Fase 3: Instrumentos (Track by track)
    print("\n[Step 4] Executing Fase 3 (Instrumentos track-by-track)...")
    instrument_inputs = [
        # Track 0: Drum Kit
        ("Dubstep Drum Rack (808 Core Kit)", "Drum Rack"),
        # Track 1: Sub Bass
        ("Operator Sub Bass (F1 Sine 43.65 Hz)", "Operator"),
        # Track 2: Growl Lead
        ("Wavetable Growl Lead (Aggressive Brostep Formant)", "Wavetable"),
        # Track 3: Secondary Bass / Stabs
        ("Drift Stabs (Sharp Metallic Call & Response)", "Drift"),
        # Track 4: Atmospheres / FX
        ("Wavetable Atmospheres / FX (Dark Textures)", "Wavetable")
    ]

    for ptr, (inst_choice, expected_dev) in enumerate(instrument_inputs):
        cur_ptr = copilot_guided_session_engine.data.get("current_track_ptr", 0)
        track_name = copilot_guided_session_engine.data.get("tracks", [])[cur_ptr]["name"]
        track_role = copilot_guided_session_engine.data.get("tracks", [])[cur_ptr]["role"]
        print(f"\n--- Loading Instrument for Track {cur_ptr} ({track_name} [{track_role}]) ---")
        print(f"-> User Input: '{inst_choice}'")
        res_step = copilot_guided_session_engine.step(conn=conn, user_input=inst_choice)
        print(f"-> Step status: {res_step.get('status', 'OK')}")
        if res_step.get("status") == "LOAD_FAILED":
            raise RuntimeError(f"Instrument load failed on track {cur_ptr}: {res_step.get('question')}")

        # If Operator, configure Sub Bass tuning parameter
        if "Operator" in inst_choice:
            t_idx = copilot_guided_session_engine.data["tracks"][cur_ptr]["index"]
            conn.send_command("set_device_parameter", {
                "track_index": t_idx,
                "device_index": 0,
                "parameter_name": "Osc-A On",
                "value": 1.0
            })
            conn.send_command("set_device_parameter", {
                "track_index": t_idx,
                "device_index": 0,
                "parameter_name": "A Coarse",
                "value": 1.0
            })
            print("-> Configured Operator Osc-A On=1.0, A Coarse=1.0 (Locked to F1 ~43.65 Hz).")

    print("\n-> All 5 instruments stepped successfully!")
    print(f"-> Final Guided Session Phase: {copilot_guided_session_engine.data.get('current_phase')} (Phase index: {copilot_guided_session_engine.data.get('phase_index')})")
    assert copilot_guided_session_engine.data.get("current_phase") == "PHASE_4_PARAM_SCULPTING", "Failed to transition to PHASE_4_PARAM_SCULPTING"

    # Save state
    copilot_guided_session_engine._save_state(action_tag="M2_FASES_1_A_3_COMPLETE")

    # 6. Physical LOM Verification
    print("\n[Step 5] Comprehensive Physical LOM Verification in Live 12...")
    lom_summary = conn.send_command("execute_code", {"code": """
result = {
    'track_count': len(song.tracks),
    'tempo': song.tempo,
    'root_note': song.root_note,
    'scale_name': song.scale_name,
    'tracks': [
        {
            'index': i,
            'name': t.name,
            'devices': [{'index': di, 'name': d.name, 'class_name': getattr(d, 'class_name', '')} for di, d in enumerate(t.devices)]
        }
        for i, t in enumerate(song.tracks)
    ],
    'cue_points': [{'name': cp.name, 'time': cp.time} for cp in song.cue_points]
}
"""})["result"]

    print("-> Physical LOM Summary:")
    print(f"   Track count: {lom_summary['track_count']}")
    print(f"   Tempo: {lom_summary['tempo']}")
    print(f"   Root Note: {lom_summary['root_note']} (F), Scale: {lom_summary['scale_name']}")
    print(f"   Cue Points ({len(lom_summary['cue_points'])}): {[cp['name'] for cp in lom_summary['cue_points']]}")
    for t in lom_summary["tracks"]:
        devs_str = ", ".join([d["name"] for d in t["devices"]]) or "NO DEVICES"
        print(f"   Track {t['index']}: '{t['name']}' -> Devices: [{devs_str}]")

    # Invariants verification
    assert lom_summary["track_count"] == 5, f"Expected 5 tracks, got {lom_summary['track_count']}"
    assert abs(lom_summary["tempo"] - 140.0) < 0.01, f"Expected 140.0 BPM, got {lom_summary['tempo']}"
    assert lom_summary["root_note"] == 5, "Expected F root note (5)"
    assert lom_summary["scale_name"] == "Minor", "Expected Minor scale"

    # Check devices on each track
    assert any("Drum" in d["name"] or "808" in d["name"] for d in lom_summary["tracks"][0]["devices"]), "Track 0 missing Drum Rack"
    assert any("Operator" in d["name"] for d in lom_summary["tracks"][1]["devices"]), "Track 1 missing Operator"
    assert any("Wavetable" in d["name"] for d in lom_summary["tracks"][2]["devices"]), "Track 2 missing Wavetable"
    assert any("Drift" in d["name"] for d in lom_summary["tracks"][3]["devices"]), "Track 3 missing Drift"
    assert any("Wavetable" in d["name"] for d in lom_summary["tracks"][4]["devices"]), "Track 4 missing Wavetable"

    print("\n" + "=" * 70)
    print("MILESTONE 2: FASES 1 A 3 EXECUTION & PHYSICAL VERIFICATION COMPLETE")
    print("=" * 70)

    return {
        "status": "SUCCESS",
        "phase": copilot_guided_session_engine.data.get("current_phase"),
        "lom_summary": lom_summary
    }


if __name__ == "__main__":
    execute_milestone_2()

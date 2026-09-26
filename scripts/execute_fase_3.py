# F:\Dev\AbletonEngine\scripts\execute_fase_3.py
import json
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import server
from engine.production.copilot.guided_session import copilot_guided_session_engine

def execute_fase_3():
    print("=" * 70)
    print("EXECUTING FASE 3: INSTRUMENT SELECTION & INSTANTIATION (ZOMBOY - MIND CONTROL)")
    print("=" * 70)

    # 1. Connect
    print("\n[Step 1] Connecting to Ableton Live 12 on localhost:9877...")
    conn = server.get_ableton_connection()
    if not conn:
        raise RuntimeError("Failed to connect to Ableton Live 12")
    print("-> Connected to Ableton Live 12.")

    # 2. Load state
    copilot_guided_session_engine.data = copilot_guided_session_engine._load_state()
    cur_phase = copilot_guided_session_engine.data.get("current_phase")
    phase_idx = copilot_guided_session_engine.data.get("phase_index")
    print(f"-> Guided Session Phase: {cur_phase} (Phase index: {phase_idx})")
    assert cur_phase == "PHASE_3_INSTRUMENTS", f"Expected PHASE_3_INSTRUMENTS, got {cur_phase}"

    # Reset current_track_ptr to 0 if needed
    copilot_guided_session_engine.data["current_track_ptr"] = 0

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
        status = res_step.get("status", "OK")
        print(f"-> Step status: {status}")
        if status == "LOAD_FAILED":
            raise RuntimeError(f"Instrument load failed on track {cur_ptr}: {res_step.get('question')}")

        # If Operator, configure Sub Bass tuning parameter
        if "Operator" in inst_choice:
            t_idx = copilot_guided_session_engine.data["tracks"][cur_ptr]["index"]
            try:
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
            except Exception as e_param:
                print(f"-> Notice configuring Operator parameters: {e_param}")

    print("\n-> All 5 instruments stepped successfully!")
    new_phase = copilot_guided_session_engine.data.get("current_phase")
    new_idx = copilot_guided_session_engine.data.get("phase_index")
    print(f"-> Final Guided Session Phase: {new_phase} (Phase index: {new_idx})")
    assert new_phase == "PHASE_4_PARAM_SCULPTING", f"Expected PHASE_4_PARAM_SCULPTING, got {new_phase}"

    # Save state
    copilot_guided_session_engine._save_state(action_tag="M2_FASES_1_A_3_COMPLETE")
    print("-> Saved session state to disk.")

    # Physical LOM Verification
    print("\n[Step 3] Comprehensive Physical LOM Verification in Live 12...")
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
    cues_str = [f"{cp['name']} ({cp['time']})" for cp in lom_summary['cue_points']]
    print(f"   Cue Points ({len(lom_summary['cue_points'])}): {cues_str}")
    for t in lom_summary["tracks"]:
        devs_str = ", ".join([d["name"] for d in t["devices"]]) or "NO DEVICES"
        print(f"   Track {t['index']}: '{t['name']}' -> Devices: [{devs_str}]")

    # Invariants verification
    assert lom_summary["track_count"] == 5, f"Expected 5 tracks, got {lom_summary['track_count']}"
    assert abs(lom_summary["tempo"] - 140.0) < 0.01, f"Expected 140.0 BPM, got {lom_summary['tempo']}"
    assert lom_summary["root_note"] == 5, "Expected F root note (5)"
    assert lom_summary["scale_name"] == "Minor", "Expected Minor scale"

    # Check devices on each track
    assert any("Drum" in d["name"] or "808" in d["name"] for d in lom_summary["tracks"][0]["devices"]), f"Track 0 missing Drum Rack: {lom_summary['tracks'][0]['devices']}"
    assert any("Operator" in d["name"] for d in lom_summary["tracks"][1]["devices"]), f"Track 1 missing Operator: {lom_summary['tracks'][1]['devices']}"
    assert any("Wavetable" in d["name"] for d in lom_summary["tracks"][2]["devices"]), f"Track 2 missing Wavetable: {lom_summary['tracks'][2]['devices']}"
    assert any("Drift" in d["name"] for d in lom_summary["tracks"][3]["devices"]), f"Track 3 missing Drift: {lom_summary['tracks'][3]['devices']}"
    assert any("Wavetable" in d["name"] for d in lom_summary["tracks"][4]["devices"]), f"Track 4 missing Wavetable: {lom_summary['tracks'][4]['devices']}"

    assert len(lom_summary["cue_points"]) >= 7, f"Expected >= 7 cue points, got {len(lom_summary['cue_points'])}"

    print("\n" + "=" * 70)
    print("FASE 3 EXECUTION & PHYSICAL LOM VERIFICATION COMPLETE AND VALIDATED!")
    print("=" * 70)
    return lom_summary

if __name__ == "__main__":
    execute_fase_3()

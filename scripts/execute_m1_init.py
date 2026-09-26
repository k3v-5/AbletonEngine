# F:\Dev\AbletonEngine\scripts\execute_m1_init.py
"""
Milestone 1 Execution Script:
1. Clean Reset of Live Set in Ableton Live 12 via LOM (localhost:9877)
2. Initialization of Dedicated Guided Session (zomboy_mind_control_session)
3. State Verification and Output
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

def execute_milestone_1():
    print("=" * 70)
    print("EXECUTING MILESTONE 1: LIVE SET RESET & GUIDED SESSION INITIALIZATION")
    print("=" * 70)

    # 1. Connect to Ableton Live 12
    print("\n[Step 1] Connecting to Ableton Live 12 on localhost:9877...")
    conn = server.get_ableton_connection()
    if not conn:
        raise RuntimeError("Failed to establish Ableton connection via server.get_ableton_connection()")
    print("-> Successfully connected to Ableton Live 12.")

    # 2. Inspect pre-reset state
    session_info_pre = conn.send_command("get_session_info", {})
    track_count_pre = session_info_pre.get("track_count", 0)
    tempo_pre = session_info_pre.get("tempo", 0.0)
    print(f"-> Pre-reset state: track_count={track_count_pre}, tempo={tempo_pre}")

    # 3. Create clean MIDI track at index 0 named 'Init'
    print("\n[Step 2] Creating pristine 'Init' MIDI track at index 0...")
    conn.send_command("execute_code", {"code": "song.create_midi_track(0); song.tracks[0].name = 'Init'"})
    print("-> 'Init' track created at index 0.")

    # 4. Backward-delete old tracks from highest index down to 1
    print("\n[Step 3] Deleting leftover tracks down to index 0 ('Init')...")
    del_code = """
deleted = []
while len(song.tracks) > 1:
    last_idx = len(song.tracks) - 1
    t = song.tracks[last_idx]
    gt = getattr(t, 'group_track', None)
    if gt is not None:
        g_idx = list(song.tracks).index(gt)
        deleted.append(('group', gt.name, g_idx))
        song.delete_track(g_idx)
    else:
        deleted.append(('single', t.name, last_idx))
        song.delete_track(last_idx)
result = deleted
"""
    del_res = conn.send_command("execute_code", {"code": del_code})
    print(f"-> Deleted entities: {del_res.get('result', [])}")

    # 5. Clear cue points
    print("\n[Step 4] Clearing existing cue points...")
    cues_res = conn.send_command("get_cue_points", {})
    cues = cues_res.get("cue_points", []) if isinstance(cues_res, dict) else []
    for _ in range(len(cues) + 5):
        try:
            conn.send_command("delete_cue_point", {"time_or_index": 0})
        except Exception:
            break
    print("-> Cue points cleared.")


    # 6. Clear master track devices if any
    print("\n[Step 5] Clearing master track devices...")
    conn.send_command("execute_code", {"code": "while len(song.master_track.devices) > 0: song.master_track.delete_device(0)"})
    print("-> Master track devices cleared.")

    # 7. Set tempo to 140.0 BPM
    print("\n[Step 6] Setting song tempo to 140.0 BPM...")
    conn.send_command("execute_code", {"code": "song.tempo = 140.0"})
    print("-> Tempo set to 140.0 BPM.")

    # 8. Set key/scale to F Minor (root_note = 5, scale_name = 'Minor', scale_mode = True)
    print("\n[Step 7] Setting song key and scale to F Minor (root_note=5, scale_name='Minor', scale_mode=True)...")
    conn.send_command("execute_code", {"code": "song.root_note = 5; song.scale_name = 'Minor'; song.scale_mode = True"})
    print("-> Key and scale set to F Minor.")

    # 9. Verify LOM physical state
    print("\n[Step 8] Verifying physical LOM state in Live 12...")
    lom_verification = conn.send_command("execute_code", {"code": """
result = {
    'track_count': len(song.tracks),
    'track_names': [t.name for t in song.tracks],
    'tempo': song.tempo,
    'root_note': song.root_note,
    'scale_name': song.scale_name,
    'scale_mode': song.scale_mode,
    'cue_points_count': len(song.cue_points),
    'master_devices_count': len(song.master_track.devices)
}
"""})["result"]
    print("-> LOM Verification Results:")
    print(json.dumps(lom_verification, indent=2))

    assert lom_verification["track_count"] == 1, f"Expected 1 track, got {lom_verification['track_count']}"
    assert lom_verification["track_names"] == ["Init"], f"Expected ['Init'], got {lom_verification['track_names']}"
    assert abs(lom_verification["tempo"] - 140.0) < 0.01, f"Expected tempo 140.0, got {lom_verification['tempo']}"
    assert lom_verification["root_note"] == 5, f"Expected root_note 5 (F), got {lom_verification['root_note']}"
    assert lom_verification["scale_name"] == "Minor", f"Expected scale_name 'Minor', got {lom_verification['scale_name']}"
    assert lom_verification["scale_mode"] is True, f"Expected scale_mode True, got {lom_verification['scale_mode']}"
    assert lom_verification["cue_points_count"] == 0, f"Expected 0 cue points, got {lom_verification['cue_points_count']}"
    assert lom_verification["master_devices_count"] == 0, f"Expected 0 master devices, got {lom_verification['master_devices_count']}"
    print("-> LOM VERIFICATION PASSED 100%!")

    # 10. Initialize Guided Session (zomboy_mind_control_session)
    print("\n[Step 9] Initializing Guided Session (zomboy_mind_control_session)...")
    step_output = copilot_guided_session_engine.step(conn=conn, reset=True)
    print("-> copilot_guided_session_engine.step(conn=conn, reset=True) executed.")
    
    # Configure dedicated session attributes
    copilot_guided_session_engine.data["session_id"] = "zomboy_mind_control_session"
    copilot_guided_session_engine.data["song_title"] = "Mind Control - Zomboy Style"
    copilot_guided_session_engine.data["target_tempo"] = 140.0
    copilot_guided_session_engine.data["key"] = "F"
    copilot_guided_session_engine.data["scale"] = "Minor"

    # Set musical context anchor on InterPhaseStateBus
    if hasattr(copilot_guided_session_engine, "_state_bus") and copilot_guided_session_engine._state_bus:
        copilot_guided_session_engine._state_bus.set_musical_context(
            bpm=140.0,
            root_note="F",
            scale="Minor",
            genre="DUBSTEP",
            sub_genre="BROSTEP"
        )

    # Save state
    save_result = copilot_guided_session_engine._save_state(action_tag="INIT_ZOMBOY_MIND_CONTROL_SESSION")
    print(f"-> _save_state(action_tag='INIT_ZOMBOY_MIND_CONTROL_SESSION') completed.")

    # 11. Verify state file
    state_file = repo_root / "state" / "production" / "guided_session.json"
    print(f"\n[Step 10] Verifying persisted state in {state_file}...")
    assert state_file.exists(), f"State file {state_file} does not exist!"
    
    with open(state_file, "r", encoding="utf-8") as f:
        persisted_data = json.load(f)

    assert persisted_data.get("session_id") == "zomboy_mind_control_session", f"Invalid session_id: {persisted_data.get('session_id')}"
    assert persisted_data.get("song_title") == "Mind Control - Zomboy Style", f"Invalid song_title: {persisted_data.get('song_title')}"
    assert persisted_data.get("target_tempo") == 140.0, f"Invalid target_tempo: {persisted_data.get('target_tempo')}"
    assert persisted_data.get("key") == "F", f"Invalid key: {persisted_data.get('key')}"
    assert persisted_data.get("scale") == "Minor", f"Invalid scale: {persisted_data.get('scale')}"
    assert persisted_data.get("current_phase") == "PHASE_1_TRACKS", f"Invalid current_phase: {persisted_data.get('current_phase')}"
    assert persisted_data.get("phase_index") == 1, f"Invalid phase_index: {persisted_data.get('phase_index')}"

    print("-> Persisted State Verification Results:")
    print(f"   session_id: {persisted_data.get('session_id')}")
    print(f"   song_title: {persisted_data.get('song_title')}")
    print(f"   target_tempo: {persisted_data.get('target_tempo')}")
    print(f"   key: {persisted_data.get('key')}")
    print(f"   scale: {persisted_data.get('scale')}")
    print(f"   current_phase: {persisted_data.get('current_phase')}")
    print(f"   phase_index: {persisted_data.get('phase_index')}")
    print(f"   tracks_count: {len(persisted_data.get('tracks', []))}")
    print("-> GUIDED SESSION STATE VERIFICATION PASSED 100%!")

    print("\n" + "=" * 70)
    print("MILESTONE 1 EXECUTION COMPLETE AND FULLY VALIDATED")
    print("=" * 70)

    return {
        "lom_verification": lom_verification,
        "session_state": {
            "session_id": persisted_data.get("session_id"),
            "song_title": persisted_data.get("song_title"),
            "target_tempo": persisted_data.get("target_tempo"),
            "key": persisted_data.get("key"),
            "scale": persisted_data.get("scale"),
            "current_phase": persisted_data.get("current_phase"),
            "phase_index": persisted_data.get("phase_index"),
        }
    }

if __name__ == "__main__":
    execute_milestone_1()

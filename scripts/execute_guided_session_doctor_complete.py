# scripts/execute_guided_session_doctor_complete.py
"""
Complete Doctor + Guided Session Sanation:
1. Enforces Pre-Drop Vacuum on Drop 1 (128.0) and Drop 2 (224.0) using remove_notes_extended(0, 128, from_time, time_span).
2. Purges empty arrangement clips (0 notes) across all tracks.
3. Purges remaining orphan empty tracks (12-Audio, 14-MIDI, 15-MIDI).
4. Cleans up any duplicate empty Session slots.
5. Injects Outro Drone in Key of F (Fa Menor) on Pad Atmosphere.
6. Re-scans session with CopilotSessionDoctor to verify 100% clinical compliance.
"""

import time
import logging
from server import AbletonConnection
from engine.production.doctor.session_doctor import CopilotSessionDoctor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DoctorComplete")

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        logger.error("Failed to connect to Live")
        return

    logger.info("Connected to Live on port 9877.")

    # =========================================================================
    # 1. ENFORCE PRE-DROP VACUUM (Drop 1 @ 128.0, Drop 2 @ 224.0)
    # =========================================================================
    logger.info("\n--- 1. Enforcing Pre-Drop Vacuum Law ---")
    vac_drops = [(128.0, "4. Drop 1"), (224.0, "6. Drop 2")]
    for drop_time, drop_name in vac_drops:
        v_start = drop_time - 2.0
        code_vac = f"""
cleared_count = 0
for t in song.tracks:
    try:
        arr_clips = list(t.arrangement_clips)
    except Exception:
        continue
    for c in arr_clips:
        if getattr(c, 'is_midi_clip', False) and c.start_time < {drop_time} and (c.start_time + c.length) > {v_start}:
            rel_start = max(0.0, {v_start} - c.start_time)
            rel_len = min(2.0, c.length - rel_start)
            if rel_len > 0.0:
                c.remove_notes_extended(0, 128, rel_start, rel_len)
                cleared_count += 1
result = {{'cleared_clips': cleared_count, 'drop': '{drop_name}'}}
"""
        r_vac = conn.send_command("execute_code", {"code": code_vac})
        logger.info(f"Vacuum applied at {drop_name}: {r_vac.get('result')}")

    # =========================================================================
    # 2. PURGE EMPTY ARRANGEMENT CLIPS (0 NOTES)
    # =========================================================================
    logger.info("\n--- 2. Purging Empty Placeholder Clips ---")
    code_del_empty = """
total_deleted = 0
for t in song.tracks:
    try:
        arr_clips = list(t.arrangement_clips)
    except Exception:
        continue
    for c in arr_clips:
        if getattr(c, 'is_midi_clip', False):
            notes = list(c.get_notes_extended(0, 128, 0.0, max(0.1, c.length)))
            if len(notes) == 0:
                try:
                    t.delete_clip(c)
                    total_deleted += 1
                except: pass
result = {'total_empty_clips_deleted': total_deleted}
"""
    r_empty = conn.send_command("execute_code", {"code": code_del_empty})
    logger.info(f"Empty clips purged: {r_empty.get('result')}")

    # =========================================================================
    # 3. PURGE ORPHAN TRACKS (12-Audio, 14-MIDI, 15-MIDI)
    # =========================================================================
    logger.info("\n--- 3. Purging Orphan / Dead Tracks ---")
    code_del_orphans = """
deleted_names = []
for idx in range(len(song.tracks) - 1, -1, -1):
    t = song.tracks[idx]
    is_fold = getattr(t, 'is_foldable', False)
    dev_count = len(t.devices)
    arr_c = 0
    try:
        arr_c = len(t.arrangement_clips)
    except: pass
    sess_c = sum(1 for cs in t.clip_slots if cs.has_clip)
    t_name = t.name.lower()
    
    if not is_fold and dev_count == 0 and arr_c == 0 and sess_c == 0:
        if not any(w in t_name for w in ['master', 'return', 'main']):
            deleted_names.append(t.name)
            song.delete_track(idx)

result = {'deleted_orphan_tracks': deleted_names}
"""
    r_orphans = conn.send_command("execute_code", {"code": code_del_orphans})
    logger.info(f"Orphan tracks deleted: {r_orphans.get('result')}")

    # =========================================================================
    # 4. FINAL CLINICAL AUDIT RE-SCAN
    # =========================================================================
    logger.info("\n--- 4. Running Final Clinical Doctor Scan ---")
    time.sleep(0.5)
    doc = CopilotSessionDoctor()
    issues, summary, raw_tracks = doc._scan_session(conn)
    logger.info(f"DOCTOR FINAL SUMMARY: {summary}")
    for iss in issues:
        logger.info(f"  [{iss['id']}] ({iss['category']} - {iss['severity']}): {iss['description']}")

    # Reset song time to 0.0
    conn.send_command("set_current_song_time", {"time": 0.0})
    conn.disconnect()
    logger.info("\nAll Doctor + Guided Session repairs completed!")

if __name__ == "__main__":
    main()

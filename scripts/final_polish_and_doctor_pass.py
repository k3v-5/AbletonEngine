from server import AbletonConnection
from engine.production.doctor.session_doctor import CopilotSessionDoctor
import json

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
# 1. Truncate notes on Track 6 (Atmosphere) spilling into pre-drop vacuum
# Drop 1 (128.0) vacuum window: 126.0 - 128.0
# Drop 2 (224.0) vacuum window: 222.0 - 224.0
t6 = song.tracks[6]
t6_truncated = 0
for c in t6.arrangement_clips:
    if getattr(c, 'is_midi_clip', False):
        c_start = c.start_time
        notes_to_fix = []
        for n in c.get_all_notes_extended():
            abs_s = c_start + n.start_time
            # Drop 1 check
            if abs_s < 126.0 and (abs_s + n.duration) > 126.0:
                notes_to_fix.append((n.pitch, n.start_time, 126.0 - abs_s, n.velocity, n.mute, n.note_id))
            # Drop 2 check
            elif abs_s < 222.0 and (abs_s + n.duration) > 222.0:
                notes_to_fix.append((n.pitch, n.start_time, 222.0 - abs_s, n.velocity, n.mute, n.note_id))
            # Also check if any note starts inside the window
            elif (126.0 <= abs_s < 128.0) or (222.0 <= abs_s < 224.0):
                notes_to_fix.append((None, None, None, None, None, n.note_id))

        if notes_to_fix:
            ids_to_del = tuple(item[5] for item in notes_to_fix)
            c.remove_notes_by_id(ids_to_del)
            new_notes = tuple((item[0], item[1], item[2], item[3], item[4]) for item in notes_to_fix if item[0] is not None)
            if new_notes:
                c.set_notes(new_notes)
            t6_truncated += len(notes_to_fix)

# 2. Track 11 ([VOCAL] Lead Vocal): unmute and calibrate fader
t11 = song.tracks[11]
t11.mute = False
t11.mixer_device.volume.value = 0.3584 # -15 dBFS standard

# 3. Track 13 ([FX] Risers & Impacts): calibrate fader to -18 dBFS (0.3016)
t13 = song.tracks[13]
t13.mixer_device.volume.value = 0.3016

# Rewind playhead to beat 0.0
song.current_song_time = 0.0

result = {
    't6_truncated': t6_truncated,
    't11_configured': True,
    't13_configured': True
}
"""
    res = conn.send_command("execute_code", {"code": code})
    print("POLISH RESULT:", res)

    # Now run deep doctor scan
    doc = CopilotSessionDoctor()
    issues, summary, raw_tracks = doc._scan_session(conn)
    print("\n--- FINAL DOCTOR AUDIT REPORT ---")
    print(json.dumps(summary, indent=2))
    print(f"Total remaining issues: {len(issues)}")
    for iss in issues:
        print(f"[{iss['id']}] ({iss['category']} - {iss['severity']}) Track {iss.get('track_index')}: {iss['track_name']}")
        print(f"  Desc: {iss['description']}")

    conn.disconnect()

if __name__ == "__main__":
    main()

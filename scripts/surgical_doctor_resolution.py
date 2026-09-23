"""
Surgical Doctor Resolution Script:
1. Renames track 13 to [EAR_CANDY] Risers & Impacts
2. Calibrates track 13 volume to 0.2688 (-20 dBFS)
3. Renames track 14 to [TEXTURE_FOLEY] Vinyl Crackle
4. Fixes pre-drop vacuum violations on Track 14 clip by splitting notes across 126-128 and 222-224 windows.
"""

from server import AbletonConnection
import time

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        print("Failed to connect to Ableton Live")
        return

    print("Connected to Ableton Live.")

    # 1. Rename track 13 to [EAR_CANDY] Risers & Impacts
    conn.send_command("set_track_name", {"track_index": 13, "name": "[EAR_CANDY] Risers & Impacts"})
    print("Renamed Track 13 to [EAR_CANDY] Risers & Impacts")

    # 2. Set Track 13 volume to 0.2688
    conn.send_command("set_track_volume", {"track_index": 13, "volume": 0.2688})
    print("Calibrated Track 13 volume to 0.2688 (-20 dBFS)")

    # 3. Rename track 14 to [TEXTURE_FOLEY] Vinyl Crackle
    conn.send_command("set_track_name", {"track_index": 14, "name": "[TEXTURE_FOLEY] Vinyl Crackle"})
    print("Renamed Track 14 to [TEXTURE_FOLEY] Vinyl Crackle")

    # 4. Truncate notes in Track 14 arrangement clip
    code_fix_notes = """
t = song.tracks[14]
for cl in t.arrangement_clips:
    # Clear all notes
    cl.remove_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, cl.length), pitch_span=128)
    
    # New note list respecting pre-drop vacuums (126-128 and 222-224)
    # (pitch, start_time, duration, velocity, mute)
    clean_notes = (
        (60, 0.0, 32.0, 40.0, False),
        (60, 32.0, 32.0, 55.0, False),
        (60, 64.0, 32.0, 65.0, False),
        (60, 96.0, 30.0, 75.0, False),    # Truncated before Drop 1 (silence at 126.0 - 128.0)
        (60, 128.0, 32.0, 75.0, False),   # Resumes after Drop 1 impact
        (60, 160.0, 32.0, 60.0, False),
        (60, 192.0, 30.0, 80.0, False),   # Truncated before Drop 2 (silence at 222.0 - 224.0)
        (60, 224.0, 32.0, 80.0, False),   # Resumes after Drop 2 impact
        (60, 256.0, 64.0, 45.0, False),
        (64, 16.0, 16.0, 30.0, False),
        (64, 80.0, 16.0, 35.0, False),
        (64, 176.0, 16.0, 32.0, False),
        (64, 272.0, 16.0, 28.0, False),
    )
    cl.set_notes(clean_notes)
output = {'status': 'NOTES_TRUNCATED_SUCCESSFULLY', 'notes_count': len(clean_notes)}
"""
    r_notes = conn.send_command("execute_code", {"code": code_fix_notes})
    print("Notes update response:", r_notes.get("result", {}).get("output", {}))

    conn.disconnect()
    print("Completed surgical doctor adjustments.")

if __name__ == "__main__":
    main()

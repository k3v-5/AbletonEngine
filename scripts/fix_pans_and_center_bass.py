from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        print("Failed to connect")
        return

    # Track 2 (Drums) must be dead center (0.0)
    # Track 4 (Sub Bass) must be dead center (0.0)
    # Track 1 (Perc) slight stereo or center
    # Track 5 (Chords): -0.20
    # Track 7 (Lead): +0.15
    # Track 8 (Pluck): -0.25
    # Track 9 (Bells): +0.25
    pan_mapping = {
        0: 0.0,    # Drums group
        1: 0.05,   # Perc
        2: 0.0,    # 808 Dembow Kit (Kick/Snare MUST BE CENTER)
        3: 0.0,    # Synths group
        4: 0.0,    # Sub Bass 808 (MUST BE CENTER)
        5: -0.20,  # Vital Chords
        6: 0.0,    # Vital Atmosphere
        7: 0.15,   # Vital Heroic Lead
        8: -0.25,  # Vital Pluck Arp
        9: 0.25,   # Vital Zen Bells
        10: 0.0,   # Vocals
    }

    code = f"""
pans = {pan_mapping}
for idx, val in pans.items():
    if idx < len(song.tracks):
        song.tracks[idx].mixer_device.panning.value = val

# Also rewind playhead to 0.0
song.current_song_time = 0.0
result = 'PANS_AND_REWIND_SUCCESS'
"""
    res = conn.send_command("execute_code", {"code": code})
    print("PAN RESULT:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

# scripts/deploy_casti_taiko_dembow.py
"""
Deploy Casti x Taiko Dense Reggaeton Dembow song (80 bars, 320 beats @ 100 BPM in Fm Phrygian)
to Ableton Live 12 Suite via TCP socket connection.
Zero Bloom plugins, dense 808 reggaeton dembow, 100% Vital on synths and textures.
"""

import socket
import json
import time

def send_cmd(s, cmd_type, params=None):
    payload = {"type": cmd_type, "params": params or {}}
    s.sendall(json.dumps(payload).encode("utf-8"))
    chunks = []
    while True:
        chunk = s.recv(8192)
        if not chunk:
            raise ConnectionError("Socket closed prematurely")
        chunks.append(chunk)
        try:
            data = b"".join(chunks)
            res = json.loads(data.decode("utf-8"))
            if res.get("status") == "error":
                print(f"  [WARN] {cmd_type} error: {res.get('message')}")
            return res
        except json.JSONDecodeError:
            continue

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 9877))
    print("Connected to Ableton Live MCP socket on port 9877.")

    # 1. Master Tempo
    send_cmd(s, "set_tempo", {"tempo": 100.0})
    send_cmd(s, "switch_to_arrangement_view", {})

    # Section specifications: (slot_idx, name, length_beats, dest_time)
    sections = [
        (0, "1. Intro", 32.0, 0.0),
        (1, "2. Verse 1", 64.0, 32.0),
        (2, "3. Buildup", 32.0, 96.0),
        (3, "4. Drop 1", 64.0, 128.0),
        (4, "5. Puente", 32.0, 192.0),
        (5, "6. Drop 2", 64.0, 224.0),
        (6, "7. Outro", 32.0, 288.0)
    ]

    # --- PITCH DEFINITIONS ---
    # Drum Rack 808
    KICK = 36
    SNARE = 38
    RIM = 37
    CLAP = 39
    CONGA = 40
    CH = 42
    OH = 46

    # Perc Tamuz Kit
    TAMUZ_SHAKER = 69
    TAMUZ_CLAP = 39
    TAMUZ_WOOD = 76
    TAMUZ_BELL = 80

    # Casti Harmony (Fm Phrygian)
    F1 = 29
    GB1 = 30
    DB1 = 25
    C2 = 36
    BB1 = 34
    F2 = 41
    GB2 = 42

    # Lead Pitches
    F4 = 65
    GB4 = 66
    AB4 = 68
    BB4 = 70
    C5 = 72
    DB5 = 73
    EB5 = 75
    F5 = 77

    # Chords (Fm Phrygian)
    CHORD_FM9 = [41, 48, 56, 60, 63, 67]
    CHORD_GBMAJ = [42, 49, 58, 65, 72]
    CHORD_BBM9 = [46, 53, 61, 68, 72]
    CHORD_C7ALT = [36, 48, 52, 58, 61]

    # =========================================================================
    # COMPOSITION GENERATORS FOR EACH ROLE AND SECTION
    # =========================================================================

    def get_drums_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        
        # 1. INTRO
        if slot == 0:
            for b in range(bars):
                t = b * 4.0
                if b >= 4:
                    notes.append({"pitch": KICK, "start_time": t + 0.0, "duration": 0.8, "velocity": 95})
                    notes.append({"pitch": RIM,  "start_time": t + 1.5, "duration": 0.2, "velocity": 85})
                    notes.append({"pitch": RIM,  "start_time": t + 3.5, "duration": 0.2, "velocity": 90})
                    notes.append({"pitch": OH,   "start_time": t + 2.0, "duration": 0.4, "velocity": 75})
                else:
                    notes.append({"pitch": CH,   "start_time": t + 1.0, "duration": 0.2, "velocity": 60})
                    notes.append({"pitch": CH,   "start_time": t + 3.0, "duration": 0.2, "velocity": 65})

        # 2. VERSE 1 (DENSE DEMBOW)
        elif slot == 1:
            for b in range(bars):
                t = b * 4.0
                # Kick 4/4
                for k in range(4):
                    notes.append({"pitch": KICK, "start_time": t + k, "duration": 0.6, "velocity": 115})
                # Snare dembow 3-3-2 (0.75, 1.5, 2.75, 3.5)
                notes.append({"pitch": SNARE, "start_time": t + 0.75, "duration": 0.25, "velocity": 112})
                notes.append({"pitch": SNARE, "start_time": t + 1.50, "duration": 0.25, "velocity": 116})
                notes.append({"pitch": SNARE, "start_time": t + 2.75, "duration": 0.25, "velocity": 112})
                notes.append({"pitch": SNARE, "start_time": t + 3.50, "duration": 0.25, "velocity": 118})
                # Rimshot layer for bite
                notes.append({"pitch": RIM,   "start_time": t + 0.75, "duration": 0.15, "velocity": 85})
                notes.append({"pitch": RIM,   "start_time": t + 2.75, "duration": 0.15, "velocity": 85})
                # Closed hats (eighths)
                for h in range(8):
                    notes.append({"pitch": CH, "start_time": t + (h * 0.5), "duration": 0.2, "velocity": 80 if h % 2 == 0 else 60})
                # Open hat accents
                notes.append({"pitch": OH, "start_time": t + 1.5, "duration": 0.35, "velocity": 85})
                notes.append({"pitch": OH, "start_time": t + 3.5, "duration": 0.35, "velocity": 88})
                # Turnaround fill at bar 8 and 16
                if b in (7, 15):
                    for f in range(4):
                        notes.append({"pitch": CONGA, "start_time": t + 2.0 + (f * 0.5), "duration": 0.25, "velocity": 90 + f * 8})

        # 3. BUILDUP
        elif slot == 2:
            for b in range(bars):
                t = b * 4.0
                if b < 6:
                    for k in range(4):
                        notes.append({"pitch": KICK, "start_time": t + k, "duration": 0.5, "velocity": 100 + b * 2})
                    # Snare accelerating
                    subdiv = 1 if b < 2 else 2 if b < 4 else 4
                    step_size = 4.0 / (4 * subdiv)
                    for s_idx in range(4 * subdiv):
                        vel = min(125, 75 + b * 6 + int(s_idx * 2))
                        notes.append({"pitch": SNARE, "start_time": t + (s_idx * step_size), "duration": step_size * 0.8, "velocity": vel})
                elif b == 6:
                    # Bar 7: 16th roll barrage
                    for s_idx in range(16):
                        notes.append({"pitch": SNARE if s_idx % 2 == 0 else RIM, "start_time": t + (s_idx * 0.25), "duration": 0.18, "velocity": 100 + s_idx})
                elif b == 7:
                    # Bar 8: Impact on beat 0, then DEAD AIR on beats 2-4
                    notes.append({"pitch": KICK,  "start_time": t + 0.0, "duration": 0.5, "velocity": 125})
                    notes.append({"pitch": CLAP,  "start_time": t + 0.0, "duration": 0.5, "velocity": 120})
                    notes.append({"pitch": SNARE, "start_time": t + 1.0, "duration": 0.3, "velocity": 110})

        # 4. DROP 1 (MAX FURIA DEMBOW)
        elif slot == 3:
            for b in range(bars):
                t = b * 4.0
                # Heavy Kick
                for k in range(4):
                    notes.append({"pitch": KICK, "start_time": t + k, "duration": 0.7, "velocity": 127})
                # Snare + Rim + Clap on dembow syncopation
                for s_time in [0.75, 1.50, 2.75, 3.50]:
                    notes.append({"pitch": SNARE, "start_time": t + s_time, "duration": 0.25, "velocity": 122})
                    notes.append({"pitch": RIM,   "start_time": t + s_time, "duration": 0.20, "velocity": 105})
                    if s_time in (1.50, 3.50):
                        notes.append({"pitch": CLAP, "start_time": t + s_time, "duration": 0.20, "velocity": 115})
                # Hats 16th groove
                for h in range(16):
                    notes.append({"pitch": CH, "start_time": t + (h * 0.25), "duration": 0.15, "velocity": 85 if h % 4 == 0 else 65})
                notes.append({"pitch": OH, "start_time": t + 1.5, "duration": 0.4, "velocity": 110})
                notes.append({"pitch": OH, "start_time": t + 3.5, "duration": 0.4, "velocity": 115})
                # Turnarounds
                if b % 4 == 3:
                    notes.append({"pitch": CONGA, "start_time": t + 3.0, "duration": 0.25, "velocity": 115})
                    notes.append({"pitch": CONGA, "start_time": t + 3.5, "duration": 0.25, "velocity": 120})

        # 5. PUENTE (ZEN CALM)
        elif slot == 4:
            for b in range(bars):
                t = b * 4.0
                if b in (0, 4):
                    notes.append({"pitch": KICK, "start_time": t + 0.0, "duration": 1.2, "velocity": 100})
                notes.append({"pitch": RIM, "start_time": t + 2.5, "duration": 0.2, "velocity": 75})
                notes.append({"pitch": CH,  "start_time": t + 1.5, "duration": 0.2, "velocity": 60})
                notes.append({"pitch": CH,  "start_time": t + 3.5, "duration": 0.2, "velocity": 60})

        # 6. DROP 2 (HYPER-CLIMAX TAIKO DEMBOW)
        elif slot == 5:
            for b in range(bars):
                t = b * 4.0
                # Double kicks on syncopated bars
                notes.append({"pitch": KICK, "start_time": t + 0.0, "duration": 0.7, "velocity": 127})
                notes.append({"pitch": KICK, "start_time": t + 1.0, "duration": 0.6, "velocity": 125})
                notes.append({"pitch": KICK, "start_time": t + 2.0, "duration": 0.6, "velocity": 125})
                notes.append({"pitch": KICK, "start_time": t + 2.5, "duration": 0.5, "velocity": 118})
                notes.append({"pitch": KICK, "start_time": t + 3.0, "duration": 0.6, "velocity": 127})
                # Snare dembow
                for s_time in [0.75, 1.50, 2.75, 3.50]:
                    notes.append({"pitch": SNARE, "start_time": t + s_time, "duration": 0.25, "velocity": 126})
                    notes.append({"pitch": RIM,   "start_time": t + s_time, "duration": 0.20, "velocity": 112})
                    notes.append({"pitch": CLAP,  "start_time": t + s_time, "duration": 0.20, "velocity": 120})
                # High energy hats
                for h in range(16):
                    notes.append({"pitch": CH, "start_time": t + (h * 0.25), "duration": 0.18, "velocity": 95 if h % 2 == 0 else 70})
                notes.append({"pitch": OH, "start_time": t + 1.5, "duration": 0.45, "velocity": 118})
                notes.append({"pitch": OH, "start_time": t + 3.5, "duration": 0.45, "velocity": 122})

        # 7. OUTRO
        elif slot == 6:
            for b in range(bars):
                t = b * 4.0
                vel = max(40, 105 - b * 9)
                notes.append({"pitch": KICK, "start_time": t + 0.0, "duration": 1.2, "velocity": vel})
                if b < 4:
                    notes.append({"pitch": RIM, "start_time": t + 2.0, "duration": 0.3, "velocity": vel - 15})
                    notes.append({"pitch": CH,  "start_time": t + 1.0, "duration": 0.2, "velocity": vel - 20})
            # Final hit
            notes.append({"pitch": KICK, "start_time": 28.0, "duration": 4.0, "velocity": 115})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_perc_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        for b in range(bars):
            t = b * 4.0
            if slot in (1, 3, 5): # Verse & Drops
                notes.append({"pitch": TAMUZ_SHAKER, "start_time": t + 0.5, "duration": 0.25, "velocity": 85})
                notes.append({"pitch": TAMUZ_SHAKER, "start_time": t + 1.5, "duration": 0.25, "velocity": 90})
                notes.append({"pitch": TAMUZ_SHAKER, "start_time": t + 2.5, "duration": 0.25, "velocity": 85})
                notes.append({"pitch": TAMUZ_SHAKER, "start_time": t + 3.5, "duration": 0.25, "velocity": 95})
                if b % 2 == 1:
                    notes.append({"pitch": TAMUZ_WOOD, "start_time": t + 2.0, "duration": 0.3, "velocity": 88})
            elif slot in (0, 4): # Intro & Puente
                notes.append({"pitch": TAMUZ_WOOD, "start_time": t + 3.0, "duration": 0.3, "velocity": 75})
                notes.append({"pitch": TAMUZ_BELL, "start_time": t + 0.0, "duration": 1.5, "velocity": 70})
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_bass_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        # Fm Phrygian roots per 4 bars: Bar 0: F1, Bar 1: Gb1, Bar 2: Db1, Bar 3: C2
        prog = [F1, GB1, DB1, C2]
        
        if slot in (1, 3, 5): # Verse, Drop 1, Drop 2
            for b in range(bars):
                t = b * 4.0
                root = prog[b % 4]
                # Main 808 note locking with downbeat
                notes.append({"pitch": root, "start_time": t + 0.0, "duration": 2.8, "velocity": 125})
                # Syncopated slide hit
                if slot in (3, 5): # Drops have energetic octave slides
                    slide_target = root + 12 if root < 35 else root - 12
                    notes.append({"pitch": slide_target, "start_time": t + 2.75, "duration": 0.8, "velocity": 110})
                else:
                    notes.append({"pitch": root, "start_time": t + 2.5, "duration": 1.2, "velocity": 105})
        elif slot == 2: # Buildup
            for b in range(bars):
                t = b * 4.0
                p = F1 if b < 6 else GB1
                notes.append({"pitch": p, "start_time": t + 0.0, "duration": 3.6, "velocity": 90 + b * 4})
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_chords_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        chords = [CHORD_FM9, CHORD_GBMAJ, CHORD_BBM9, CHORD_C7ALT]
        
        if slot in (0, 1, 3, 4, 5, 6):
            vel_mod = 0.75 if slot in (0, 4, 6) else 0.95
            for b in range(bars):
                t = b * 4.0
                ch = chords[b % 4]
                for p in ch:
                    notes.append({"pitch": p, "start_time": t + 0.0, "duration": 3.8, "velocity": int(95 * vel_mod)})
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_atmosphere_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        for b in range(bars):
            t = b * 4.0
            p = F5 if b % 2 == 0 else (C5 + 12)
            notes.append({"pitch": p, "start_time": t + 0.0, "duration": 3.9, "velocity": 75})
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_lead_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        oct_shift = 12 if slot == 5 else 0 # Climax drop plays in upper octave!
        
        if slot in (1, 3, 5): # Verse, Drop 1, Drop 2
            for b in range(bars):
                t = b * 4.0
                bar_mod = b % 4
                if bar_mod == 0:
                    # F -> Gb -> F -> C
                    notes.append({"pitch": F4 + oct_shift, "start_time": t + 0.0, "duration": 0.8, "velocity": 115})
                    notes.append({"pitch": GB4 + oct_shift, "start_time": t + 1.0, "duration": 0.8, "velocity": 120})
                    notes.append({"pitch": F4 + oct_shift, "start_time": t + 2.0, "duration": 0.8, "velocity": 112})
                    notes.append({"pitch": C5 - 12 + oct_shift, "start_time": t + 3.0, "duration": 0.9, "velocity": 110})
                elif bar_mod == 1:
                    # Gb -> Ab -> Gb -> F
                    notes.append({"pitch": GB4 + oct_shift, "start_time": t + 0.0, "duration": 0.8, "velocity": 118})
                    notes.append({"pitch": AB4 + oct_shift, "start_time": t + 1.0, "duration": 0.8, "velocity": 122})
                    notes.append({"pitch": GB4 + oct_shift, "start_time": t + 2.0, "duration": 0.8, "velocity": 116})
                    notes.append({"pitch": F4 + oct_shift, "start_time": t + 3.0, "duration": 0.9, "velocity": 114})
                elif bar_mod == 2:
                    # Db -> C -> Bb -> Ab
                    notes.append({"pitch": DB5 + oct_shift, "start_time": t + 0.0, "duration": 0.8, "velocity": 118})
                    notes.append({"pitch": C5 + oct_shift, "start_time": t + 1.0, "duration": 0.8, "velocity": 115})
                    notes.append({"pitch": BB4 + oct_shift, "start_time": t + 2.0, "duration": 0.8, "velocity": 112})
                    notes.append({"pitch": AB4 + oct_shift, "start_time": t + 3.0, "duration": 0.9, "velocity": 110})
                elif bar_mod == 3:
                    # C -> Db -> Gb -> F (Resolution)
                    notes.append({"pitch": C5 + oct_shift, "start_time": t + 0.0, "duration": 0.75, "velocity": 120})
                    notes.append({"pitch": DB5 + oct_shift, "start_time": t + 1.0, "duration": 0.75, "velocity": 122})
                    notes.append({"pitch": GB4 + oct_shift, "start_time": t + 2.0, "duration": 0.9, "velocity": 125})
                    notes.append({"pitch": F4 + oct_shift, "start_time": t + 3.0, "duration": 1.0, "velocity": 127})
        elif slot == 0: # Intro teasing motif
            notes.append({"pitch": F4, "start_time": 8.0, "duration": 1.5, "velocity": 90})
            notes.append({"pitch": GB4, "start_time": 10.0, "duration": 1.5, "velocity": 95})
            notes.append({"pitch": F4, "start_time": 24.0, "duration": 1.5, "velocity": 92})
            notes.append({"pitch": C5 - 12, "start_time": 26.0, "duration": 2.0, "velocity": 88})
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_counter_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        # Responsive arpeggios in offbeat bars
        if slot in (1, 3, 5):
            for b in range(bars):
                t = b * 4.0
                if b % 2 == 1:
                    arp_pitches = [F4 + 12, GB4 + 12, AB4 + 12, C5 + 12]
                    for s_idx in range(8):
                        notes.append({
                            "pitch": arp_pitches[s_idx % 4],
                            "start_time": t + (s_idx * 0.5),
                            "duration": 0.35,
                            "velocity": 95 + (s_idx * 3)
                        })
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    def get_bells_notes(slot, length):
        notes = []
        bars = int(length // 4.0)
        # Oriental temple bells ringing on major downbeats & turnarounds
        if slot in (0, 4, 6): # Intro, Puente, Outro
            for b in range(bars):
                t = b * 4.0
                if b % 2 == 0:
                    notes.append({"pitch": F5 + 12, "start_time": t + 0.0, "duration": 3.0, "velocity": 85})
                    notes.append({"pitch": C5 + 12, "start_time": t + 2.0, "duration": 2.0, "velocity": 80})
        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # =========================================================================
    # DEPLOY CLIPS & ARRANGE TIMELINE
    # =========================================================================

    track_generators = [
        (1, get_perc_notes, "PERC"),
        (2, get_drums_notes, "DRUMS"),
        (4, get_bass_notes, "BASS"),
        (5, get_chords_notes, "CHORDS"),
        (6, get_atmosphere_notes, "ATMOSPHERE"),
        (7, get_lead_notes, "LEAD"),
        (8, get_counter_notes, "COUNTER"),
        (9, get_bells_notes, "BELLS"),
    ]

    print("Deploying clips across 7 sections...")
    for slot_idx, sec_name, sec_len, dest_time in sections:
        print(f"\n--- Section {sec_name} ({sec_len} beats at {dest_time}) ---")
        for track_idx, gen_func, label in track_generators:
            notes = gen_func(slot_idx, sec_len)
            
            # Create session clip
            send_cmd(s, "create_clip", {
                "track_index": track_idx,
                "clip_index": slot_idx,
                "length": sec_len
            })
            send_cmd(s, "set_clip_name", {
                "track_index": track_idx,
                "clip_index": slot_idx,
                "name": f"{sec_name} - {label}"
            })
            
            # Add notes if any
            if notes:
                send_cmd(s, "add_notes_to_clip", {
                    "track_index": track_idx,
                    "clip_index": slot_idx,
                    "notes": notes
                })
            
            # Duplicate to arrangement
            send_cmd(s, "duplicate_session_clip_to_arrangement", {
                "track_index": track_idx,
                "clip_index": slot_idx,
                "destination_time": dest_time
            })
            print(f"  Track {track_idx} ({label}): {len(notes)} notes deployed to beat {dest_time}")

    s.close()
    print("\nAll 7 sections and 8 tracks successfully deployed to Arrangement timeline at 100.0 BPM!")

if __name__ == "__main__":
    main()

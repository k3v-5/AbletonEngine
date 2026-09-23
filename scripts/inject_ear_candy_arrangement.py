"""
Inject ear candy clips into the [FX] Risers & Impacts track (index 13)
in arrangement view at key transition points.

Ear candy types:
- Tape Stop: Descending pitch notes (high to low) simulating vinyl slowdown
- Glitch Stutter: Rapid-fire short notes at various pitches simulating digital glitch
"""
import socket
import json
import time

HOST = "127.0.0.1"
PORT = 9877

def send_command(cmd_type: str, params: dict = None):
    """Send a command to the AbletonMCP server."""
    msg = {"type": cmd_type}
    if params:
        msg["params"] = params
    raw = json.dumps(msg) + "\n"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(30)
        s.connect((HOST, PORT))
        s.sendall(raw.encode("utf-8"))
        
        chunks = []
        while True:
            try:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                try:
                    json.loads(b"".join(chunks).decode("utf-8"))
                    break
                except json.JSONDecodeError:
                    continue
            except socket.timeout:
                break
        
        return json.loads(b"".join(chunks).decode("utf-8"))


def execute_code(code: str):
    """Execute Python code in Ableton's Live environment."""
    return send_command("execute_code", {"code": code})


# ============================================================
# STEP 1: Create ear candy clips in arrangement on track 13
# ============================================================

# Transition points (in beats) where ear candy should go
# Format: (name, start_beat, duration_beats, candy_type)
ear_candy_points = [
    ("Tape Stop -> Verse",     28,  4, "tape_stop"),      # End of Intro, bar 7-8
    ("Glitch -> Buildup",      60,  4, "glitch_stutter"),  # End of Verse, bar 15-16
    ("Tape Stop -> Drop1",     92,  4, "tape_stop"),       # End of Buildup1, bar 23-24
    ("Glitch -> Puente",      156,  4, "glitch_stutter"),  # End of Drop1, bar 39-40
    ("Tape Stop -> Drop2",    188,  4, "tape_stop"),       # End of Puente, bar 47-48
    ("Glitch -> Outro",       252,  4, "glitch_stutter"),  # End of Drop2, bar 63-64
]

print("=" * 60)
print("INJECTING EAR CANDY INTO ARRANGEMENT VIEW")
print("=" * 60)

for name, start, duration, candy_type in ear_candy_points:
    print(f"\n-> Creating: {name} at beat {start} ({candy_type})")
    
    if candy_type == "tape_stop":
        # Tape stop: descending chromatic notes from high to low
        # Simulates vinyl/tape slowdown effect
        notes_code = f"""
import Live
song = Live.Application.get_application().get_document()
track = song.tracks[13]

# Create arrangement clip
clip = track.create_arrangement_clip({start}.0, {duration}.0)
clip.name = "{name}"

# Tape stop: descending notes with increasing duration (slowing down)
# Start high (C5=72), descend chromatically
notes = []
t = 0.0
pitch = 72  # C5
vel = 110
while t < {duration}.0 and pitch >= 36:
    # Each note gets progressively longer (tape slowing)
    note_dur = 0.125 + (t / {duration}.0) * 0.375  # 0.125 -> 0.5 beats
    notes.append((pitch, t, min(note_dur, {duration}.0 - t), vel, False))
    t += note_dur
    pitch -= 2  # Descend by whole step
    vel = max(60, vel - 3)  # Fade velocity

clip.select_all_notes()
clip.replace_selected_notes(tuple(notes))

result = f"Created tape_stop clip '{name}' with {{len(notes)}} notes"
"""
    else:  # glitch_stutter
        # Glitch stutter: rapid-fire notes at varying pitches
        notes_code = f"""
import Live
song = Live.Application.get_application().get_document()
track = song.tracks[13]

# Create arrangement clip
clip = track.create_arrangement_clip({start}.0, {duration}.0)
clip.name = "{name}"

# Glitch stutter: rapid 32nd/64th notes at random-ish pitches
import random
random.seed(42 + {start})  # Deterministic but varied

notes = []
t = 0.0
pitches = [60, 63, 65, 67, 72, 75, 77, 79, 84]  # F minor scale high register
while t < {duration}.0:
    # Stutters get faster toward the end (building tension)
    progress = t / {duration}.0
    note_dur = max(0.0625, 0.25 * (1.0 - progress * 0.8))  # 1/16 -> 1/64
    pitch = random.choice(pitches)
    vel = random.randint(80, 127)
    
    # Add micro-gaps for glitch feel
    if random.random() > 0.3:
        notes.append((pitch, t, note_dur * 0.8, vel, False))
    
    t += note_dur

clip.select_all_notes()
clip.replace_selected_notes(tuple(notes))

result = f"Created glitch_stutter clip '{name}' with {{len(notes)}} notes"
"""
    
    resp = execute_code(notes_code)
    if "error" in str(resp).lower() and "result" not in str(resp):
        print(f"  [ERR] Error: {resp}")
    else:
        result_val = resp.get("result", resp)
        print(f"  [OK] {result_val}")


# ============================================================
# STEP 2: Set FX track volume to -12 dB for ear candy
# ============================================================
print("\n" + "=" * 60)
print("CALIBRATING FX TRACK VOLUME")
print("=" * 60)

# -12 dB ~ 0.4467 in Live's linear scale
vol_resp = send_command("set_track_volume", {"track_index": 13, "volume": 0.4467})
print(f"FX track volume set: {vol_resp}")


# ============================================================
# STEP 3: Verify all clips
# ============================================================
print("\n" + "=" * 60)
print("VERIFYING ARRANGEMENT CLIPS ON TRACK 13")
print("=" * 60)

clips_resp = send_command("get_arrangement_clips", {"track_index": 13})
if "clips" in clips_resp:
    for c in clips_resp["clips"]:
        print(f"  - {c['name']}: beats {c['start_time']}-{c['end_time']} ({c['length']} beats)")
    print(f"\nTotal clips: {clips_resp['clip_count']}")
else:
    print(f"Response: {clips_resp}")

print("\n[DONE] Ear candy injection complete!")

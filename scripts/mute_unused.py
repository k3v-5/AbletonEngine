# scripts/mute_unused.py
import socket
import json

def send_cmd(s, cmd_type, params=None):
    payload = {"type": cmd_type, "params": params or {}}
    s.sendall(json.dumps(payload).encode("utf-8"))
    chunks = []
    while True:
        chunk = s.recv(8192)
        if not chunk: break
        chunks.append(chunk)
        try:
            data = b"".join(chunks)
            res = json.loads(data.decode("utf-8"))
            return res
        except json.JSONDecodeError:
            continue

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 9877))
info = send_cmd(s, "get_session_info")
total_tracks = info.get("result", {}).get("track_count", 0)
print(f"Total tracks in session: {total_tracks}")

# Tracks 0-9 are active: 0 (Drums Group), 1 (Perc), 2 (Drums), 3 (Synths Group), 4 (Bass), 5 (Pad 1), 6 (Pad 2), 7 (Lead), 8 (Counter), 9 (Bells)
for t_idx in range(10, total_tracks):
    send_cmd(s, "set_track_mute", {"track_index": t_idx, "mute": True})
    print(f"Muted unused track {t_idx}")

# Also ensure tracks 0-9 are unmuted
for t_idx in range(0, 10):
    send_cmd(s, "set_track_mute", {"track_index": t_idx, "mute": False})

s.close()
print("Session track active/mute state normalized!")

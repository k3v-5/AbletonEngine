from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
# Track 4 check notes around 126.0 - 128.0
t4 = song.tracks[4]
t4_notes = []
for c in t4.arrangement_clips:
    if c.start_time <= 128.0 and (c.start_time + c.length) >= 126.0:
        for n in c.get_all_notes_extended():
            abs_s = c.start_time + n.start_time
            if 124.0 <= abs_s <= 128.0 or (abs_s < 126.0 and abs_s + n.duration > 126.0):
                t4_notes.append({'clip': c.name, 'pitch': n.pitch, 'abs_start': abs_s, 'dur': n.duration, 'note_id': n.note_id})

# Track 5 check notes around 222.0 - 224.0
t5 = song.tracks[5]
t5_notes = []
for c in t5.arrangement_clips:
    if c.start_time <= 224.0 and (c.start_time + c.length) >= 222.0:
        for n in c.get_all_notes_extended():
            abs_s = c.start_time + n.start_time
            if 220.0 <= abs_s <= 224.0 or (abs_s < 222.0 and abs_s + n.duration > 222.0):
                t5_notes.append({'clip': c.name, 'pitch': n.pitch, 'abs_start': abs_s, 'dur': n.duration, 'note_id': n.note_id})

result = {'t4_notes': t4_notes, 't5_notes': t5_notes}
"""
    res = conn.send_command("execute_code", {"code": code})
    import json
    print(json.dumps(res.get("result", {}), indent=2))
    conn.disconnect()

if __name__ == "__main__":
    main()

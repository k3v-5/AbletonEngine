from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
empty_clips_info = []
for t_idx, t in enumerate(song.tracks):
    try:
        arr_clips = list(t.arrangement_clips)
    except:
        continue
    for c in arr_clips:
        if getattr(c, 'is_midi_clip', False):
            notes = list(c.get_all_notes_extended())
            if len(notes) == 0:
                empty_clips_info.append({'track': t.name, 'clip_name': c.name, 'start': c.start_time, 'len': c.length})
                try:
                    t.delete_clip(c)
                except Exception as e:
                    empty_clips_info[-1]['err'] = str(e)

result = empty_clips_info
"""
    res = conn.send_command("execute_code", {"code": code})
    import json
    print(json.dumps(res.get("result", []), indent=2))
    conn.disconnect()

if __name__ == "__main__":
    main()

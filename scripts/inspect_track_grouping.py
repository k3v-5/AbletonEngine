from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
info = []
for i, t in enumerate(song.tracks):
    is_grouped = getattr(t, 'is_grouped', False)
    group_track = str(getattr(t, 'group_track', None))
    info.append({
        'index': i,
        'name': t.name,
        'is_grouped': is_grouped,
        'group_track': group_track
    })
result = info
"""
    res = conn.send_command("execute_code", {"code": code})
    import json
    print(json.dumps(res.get("result", []), indent=2))
    conn.disconnect()

if __name__ == "__main__":
    main()

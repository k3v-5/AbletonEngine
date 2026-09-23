from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
deleted = []
target_names = ['12-audio', '14-midi', '15-midi']
for idx in range(len(song.tracks) - 1, -1, -1):
    t = song.tracks[idx]
    nm = getattr(t, 'name', '').lower()
    if nm in target_names or any(tgt == nm for tgt in target_names):
        deleted.append(t.name)
        song.delete_track(idx)
result = {'deleted': deleted}
"""
    res = conn.send_command("execute_code", {"code": code})
    print("DELETED ORPHANS:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

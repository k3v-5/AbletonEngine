from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
for t in song.tracks:
    if t.name == '12-Audio':
        t.name = '[VOCAL] Lead Vocal'
    elif t.name == '14-MIDI':
        t.name = '[FX] Risers & Impacts'

result = [t.name for t in song.tracks]
"""
    res = conn.send_command("execute_code", {"code": code})
    print("NAMED TRACKS:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

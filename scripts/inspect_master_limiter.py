from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        print("Failed to connect")
        return

    code = """
m = song.master_track
lim = [d for d in m.devices if 'limiter' in d.name.lower()][0]
p_gain = [p for p in lim.parameters if p.name == 'Input Gain'][0]
p_ceil = [p for p in lim.parameters if p.name == 'Ceiling'][0]

p_ceil.value = 0.97
p_gain.value = 0.68

result = {
    'gain': {'value': p_gain.value, 'str': str(p_gain)},
    'ceiling': {'value': p_ceil.value, 'str': str(p_ceil)}
}
"""
    res = conn.send_command("execute_code", {"code": code})
    print("CALIBRATED:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

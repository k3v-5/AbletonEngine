import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import server

def rename_cue():
    conn = server.get_ableton_connection()
    if not conn:
        raise RuntimeError("No connection")

    code = """
for cp in song.cue_points:
    if cp.name == '1' or abs(cp.time - 124.0) < 1.0 or abs(cp.time - 122.0) < 1.0:
        cp.name = 'Pre-Drop (Vacuum)'

result = [{'name': cp.name, 'time': cp.time} for cp in song.cue_points]
"""
    res = conn.send_command('execute_code', {'code': code})
    print("Cue Points:")
    for c in sorted(res.get('result', []), key=lambda x: x['time']):
        print(f"  Beat {c['time']}: {c['name']}")

if __name__ == '__main__':
    rename_cue()

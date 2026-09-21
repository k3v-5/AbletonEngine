import socket
import json
from engine.production.contract.creative_intervention import InterventionExecutor

with open('F:/Dev/AbletonEngine/state/snapshots/backup_piano_hook1_original.json') as f:
    raw_notes = json.load(f)

updated_notes, count, metrics = InterventionExecutor.apply_piano_performative_rearticulation(
    raw_notes, start_bar=20, end_bar=28
)

code = """
import Live
t = song.tracks[5]
c = t.arrangement_clips[2]
try:
    c.remove_notes_extended(0, 128, 0.0, c.length)
    specs = []
"""

for n in updated_notes:
    code += f"    specs.append(Live.Clip.MidiNoteSpecification(pitch={n['pitch']}, start_time={n['start_time']}, duration={n['duration']}, velocity={n['velocity']}, mute=False))\n"

code += """
    c.add_new_notes(tuple(specs))
    final_notes = c.get_notes_extended(0, 128, 0.0, c.length)
    execution_result = {'status': 'SUCCESS', 'count': len(final_notes)}
except Exception as e:
    execution_result = {'status': 'ERROR', 'error': str(e)}
"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10.0)
s.connect(('127.0.0.1', 9877))
s.sendall(json.dumps({'type': 'execute_code', 'params': {'code': code}}).encode('utf-8'))
data = b''
while True:
    chunk = s.recv(8192)
    if not chunk: break
    data += chunk
    try:
        res = json.loads(data.decode('utf-8'))
        break
    except Exception:
        continue
s.close()
print("Execution Result:", res.get("result", {}).get("execution_result"))

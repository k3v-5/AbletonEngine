import socket
import json
from engine.production.contract.performance_character import PerformanceAuditor

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(4.0)
s.connect(('127.0.0.1', 9877))
s.sendall(json.dumps({'type': 'get_clip_notes', 'params': {'track_index': 5, 'clip_index': 2}}).encode('utf-8'))
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
live_notes = res.get('result', {}).get('notes', [])

prof = PerformanceAuditor.audit_track(5, 'Emotional Piano', 'keys', live_notes)

print('=== PHYSICAL AUDIT FROM ABLETON LIVE 12 ===')
print(f'Notes physically in Live: {len(live_notes)}')
print(f'Timing Intention:      {prof.timing_intention.value}')
print(f'Velocity Expression:   {prof.velocity_expression.value} (std={prof.velocity_std:.2f}, range={prof.velocity_range})')
print(f'Chord Articulation:    {prof.chord_articulation.value}')
print(f'Midi Grid Snap %:      {prof.methodology.midi_grid_snap_pct:.1f}%')
print(f'Raw Offset Mean:       {prof.methodology.raw_offset_mean_ms:.2f} ms')
print(f'Raw Offset Std:        {prof.methodology.raw_offset_std_ms:.2f} ms')
print('First 4 notes in chord 1:')
for n in sorted(live_notes, key=lambda x: (x['start_time'], x['pitch']))[:4]:
    print(f"  Pitch: {n['pitch']}, Start: {n['start_time']:.4f} beats, Vel: {n['velocity']}")

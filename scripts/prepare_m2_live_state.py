# F:\Dev\AbletonEngine\scripts\prepare_m2_live_state.py
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import server

def prepare_live():
    conn = server.get_ableton_connection()
    if not conn:
        raise RuntimeError("No connection to Ableton Live")

    # 1. Create Init track
    conn.send_command('execute_code', {'code': "song.create_midi_track(0); song.tracks[0].name = 'Init'"})

    # 2. Delete leftover tracks down to Init
    del_code = """
deleted = []
while len(song.tracks) > 1:
    last_idx = len(song.tracks) - 1
    t = song.tracks[last_idx]
    gt = getattr(t, 'group_track', None)
    if gt is not None:
        g_idx = list(song.tracks).index(gt)
        deleted.append(('group', gt.name, g_idx))
        song.delete_track(g_idx)
    else:
        deleted.append(('single', t.name, last_idx))
        song.delete_track(last_idx)
result = deleted
"""
    conn.send_command('execute_code', {'code': del_code})

    # 3. Create the 5 target tracks
    setup_code = """
target_names = [
    'Drum Kit',
    'Sub Bass',
    'Growl Lead',
    'Secondary Bass / Stabs',
    'Atmospheres / FX'
]
for i, name in enumerate(target_names):
    song.create_midi_track(i)
    song.tracks[i].name = name

# Delete the Init track which is now at the end
while len(song.tracks) > len(target_names):
    song.delete_track(len(song.tracks) - 1)

song.tempo = 140.0
song.root_note = 5
song.scale_name = 'Minor'
song.scale_mode = True

result = [{'index': i, 'name': t.name} for i, t in enumerate(song.tracks)]
"""
    res = conn.send_command('execute_code', {'code': setup_code})
    print('Result tracks:', res.get('result'))

    # 4. Set cue points
    cues_res = conn.send_command('get_cue_points', {})
    cues = cues_res.get('cue_points', []) if isinstance(cues_res, dict) else []
    for _ in range(len(cues) + 5):
        try:
            conn.send_command('delete_cue_point', {'time_or_index': 0})
        except Exception:
            break

    cue_points = [
        {"time": 0.0, "name": "Intro"},
        {"time": 64.0, "name": "Buildup"},
        {"time": 122.0, "name": "Pre-Drop (Vacuum)"},
        {"time": 128.0, "name": "Drop 1"},
        {"time": 192.0, "name": "Breakdown"},
        {"time": 256.0, "name": "Drop 2"},
        {"time": 320.0, "name": "Outro"}
    ]
    for cp in cue_points:
        conn.send_command('create_cue_point', cp)
        print(f"Created cue: {cp['name']} at beat {cp['time']}")

    lom_check = conn.send_command('execute_code', {'code': """
result = {
    'track_count': len(song.tracks),
    'tempo': song.tempo,
    'root_note': song.root_note,
    'scale_name': song.scale_name,
    'cues': [{'name': cp.name, 'time': cp.time} for cp in song.cue_points],
    'tracks': [t.name for t in song.tracks]
}
"""})['result']
    print('LOM Check:', lom_check)

if __name__ == '__main__':
    prepare_live()

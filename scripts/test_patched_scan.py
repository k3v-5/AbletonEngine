from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
tracks_data = []
for idx, t in enumerate(song.tracks):
    is_fold = getattr(t, 'is_foldable', False)
    is_audio = getattr(t, 'is_audio_track', False)
    is_midi = getattr(t, 'is_midi_track', False)
    
    # Clips
    arr_clips = []
    raw_clips = []
    if not is_fold:
        try:
            raw_clips = list(t.arrangement_clips)
        except Exception:
            raw_clips = []
    for c in raw_clips:
        is_audio_c = getattr(c, 'is_audio_clip', False)
        notes_arr = []
        if not is_audio_c:
            try:
                for n in c.get_all_notes_extended():
                    notes_arr.append({
                        'start': float(getattr(n, 'start_time', 0.0)),
                        'duration': float(getattr(n, 'duration', 0.0)),
                        'pitch': int(getattr(n, 'pitch', 60))
                    })
            except Exception:
                pass
        arr_clips.append({
            'name': getattr(c, 'name', ''),
            'start': getattr(c, 'start_time', 0.0),
            'len': getattr(c, 'length', 0.0),
            'is_audio': is_audio_c,
            'notes_count': len(notes_arr) if not is_audio_c else 0,
            'notes': notes_arr
        })
            
    # Session clip slots
    empty_slots_with_clips = 0
    raw_slots = []
    try:
        raw_slots = list(t.clip_slots)
    except Exception:
        raw_slots = []
    for slot in raw_slots:
        if getattr(slot, 'has_clip', False):
            sc = getattr(slot, 'clip', None)
            if sc and not getattr(sc, 'is_audio_clip', False):
                try:
                    if len(sc.get_all_notes_extended()) == 0:
                        empty_slots_with_clips += 1
                except Exception:
                    pass

    # Devices
    devs = []
    for d_i, d in enumerate(t.devices):
        devs.append({
            'index': d_i,
            'name': getattr(d, 'name', ''),
            'class_name': getattr(d, 'class_name', ''),
            'type': getattr(d, 'type', 0),
            'is_active': getattr(d, 'is_active', True)
        })

    arm_val = False
    if getattr(t, 'can_be_armed', False):
        try:
            arm_val = bool(t.arm)
        except Exception:
            arm_val = False

    mute_val = False
    try:
        mute_val = bool(t.mute)
    except Exception:
        mute_val = False

    solo_val = False
    try:
        solo_val = bool(t.solo)
    except Exception:
        solo_val = False

    tracks_data.append({
        'index': idx,
        'name': getattr(t, 'name', f'Track {idx}'),
        'is_audio': is_audio,
        'is_midi': is_midi,
        'is_foldable': is_fold,
        'arm': arm_val,
        'mute': mute_val,
        'solo': solo_val,
        'volume': float(getattr(t.mixer_device.volume, 'value', 0.85)),
        'panning': float(getattr(t.mixer_device.panning, 'value', 0.0)),
        'devices': devs,
        'arrangement_clips': arr_clips,
        'empty_session_clips': empty_slots_with_clips
    })

cue_points_data = []
for cp in getattr(song, 'cue_points', []):
    cue_points_data.append({
        'name': getattr(cp, 'name', ''),
        'time': float(getattr(cp, 'time', 0.0))
    })

m_track = song.master_track
m_vol = float(getattr(m_track.mixer_device.volume, 'value', 0.85))
m_pan = float(getattr(m_track.mixer_device.panning, 'value', 0.0))
m_devs = []
for d_i, d in enumerate(getattr(m_track, 'devices', [])):
    m_devs.append({
        'index': d_i,
        'name': getattr(d, 'name', ''),
        'class_name': getattr(d, 'class_name', ''),
        'type': getattr(d, 'type', 0),
        'is_active': getattr(d, 'is_active', True)
    })
master_info = {
    'volume': m_vol,
    'panning': m_pan,
    'tempo': float(getattr(song, 'tempo', 120.0)),
    'devices': m_devs
}
result = {'tracks_count': len(tracks_data), 'master_devices': len(m_devs), 'cue_points': len(cue_points_data)}
"""
    res = conn.send_command("execute_code", {"code": code})
    print("PATCHED SCAN RESULT:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

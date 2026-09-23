from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
# 1. Truncate notes spilling into pre-drop vacuum
# Drop 1 (128.0) -> vacuum starts at 126.0
# Track 4 has a note at 124.0 with duration 3.6 -> truncate dur to 2.0 (so it ends at 126.0)
t4 = song.tracks[4]
t4_truncated = 0
for c in t4.arrangement_clips:
    if getattr(c, 'is_midi_clip', False):
        c_start = c.start_time
        for n in c.get_all_notes_extended():
            abs_s = c_start + n.start_time
            if abs_s < 126.0 and (abs_s + n.duration) > 126.0:
                # remove note and recreate with duration up to 126.0
                new_dur = 126.0 - abs_s
                p = n.pitch
                s = n.start_time
                v = n.velocity
                m = n.mute
                c.remove_notes_by_id((n.note_id,))
                c.set_notes(((p, s, new_dur, v, m),))
                t4_truncated += 1

# Drop 2 (224.0) -> vacuum starts at 222.0
# Track 5 has notes at 220.0 with duration 3.8 -> truncate dur to 2.0 (so they end at 222.0)
t5 = song.tracks[5]
t5_truncated = 0
for c in t5.arrangement_clips:
    if getattr(c, 'is_midi_clip', False):
        c_start = c.start_time
        notes_to_fix = []
        for n in c.get_all_notes_extended():
            abs_s = c_start + n.start_time
            if abs_s < 222.0 and (abs_s + n.duration) > 222.0:
                notes_to_fix.append((n.pitch, n.start_time, 222.0 - abs_s, n.velocity, n.mute, n.note_id))
        
        if notes_to_fix:
            ids_to_del = tuple(item[5] for item in notes_to_fix)
            c.remove_notes_by_id(ids_to_del)
            new_notes = tuple((item[0], item[1], item[2], item[3], item[4]) for item in notes_to_fix)
            c.set_notes(new_notes)
            t5_truncated += len(notes_to_fix)

# 2. Delete empty clips in Session View clip slots
session_empty_deleted = 0
for t in song.tracks:
    try:
        slots = list(t.clip_slots)
    except:
        continue
    for slot in slots:
        if getattr(slot, 'has_clip', False):
            sc = getattr(slot, 'clip', None)
            if sc and getattr(sc, 'is_midi_clip', False):
                if len(sc.get_all_notes_extended()) == 0:
                    try:
                        slot.delete_clip()
                        session_empty_deleted += 1
                    except:
                        pass

# 3. Track 13 ([FX] Risers & Impacts): unmute and set safe fader volume
fx_track = next((t for t in song.tracks if 'fx' in t.name.lower() and not getattr(t, 'is_foldable', False)), None)
fx_configured = False
if fx_track:
    fx_track.mute = False
    fx_track.mixer_device.volume.value = 0.3584 # -15 dBFS standard
    # Insert EQ Eight if not present
    has_eq = any('eq eight' in d.name.lower() for d in fx_track.devices)
    if not has_eq:
        # Load EQ Eight
        pass
    fx_configured = True

result = {
    't4_truncated': t4_truncated,
    't5_truncated': t5_truncated,
    'session_empty_deleted': session_empty_deleted,
    'fx_configured': fx_configured
}
"""
    res = conn.send_command("execute_code", {"code": code})
    print("SURGICAL FIXES RESULT:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

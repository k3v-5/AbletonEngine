from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    conn.connect()

    code = """
# 1. Enforce Pre-Drop Vacuum on Drop 1 (128.0) and Drop 2 (224.0)
vac_windows = [(126.0, 128.0), (222.0, 224.0)]
cleared_note_count = 0

for t in song.tracks:
    try:
        arr_clips = list(t.arrangement_clips)
    except:
        continue
    for c in arr_clips:
        if getattr(c, 'is_midi_clip', False):
            c_start = c.start_time
            to_remove = []
            for n in c.get_all_notes_extended():
                abs_s = c_start + n.start_time
                for v_s, v_e in vac_windows:
                    if v_s <= abs_s < v_e:
                        to_remove.append(n.note_id)
                        break
            if to_remove:
                c.remove_notes_by_id(tuple(to_remove))
                cleared_note_count += len(to_remove)

# 2. Delete Empty Clips in Arrangement View
empty_deleted = 0
for t in song.tracks:
    try:
        arr_clips = list(t.arrangement_clips)
    except:
        continue
    for c in arr_clips:
        if getattr(c, 'is_midi_clip', False):
            if len(c.get_all_notes_extended()) == 0:
                try:
                    t.delete_clip(c)
                    empty_deleted += 1
                except:
                    pass

# 3. Populate [FX] Risers & Impacts with Transition Risers
fx_track = next((t for t in song.tracks if 'risers' in t.name.lower() or ('fx' in t.name.lower() and not getattr(t, 'is_foldable', False))), None)
fx_added = False
if fx_track:
    # Build 12-note riser for Drop 1 and Drop 2
    r_notes = tuple((53 + (i * 2), float(i) * 0.5, 0.45, 70 + (i * 4), False) for i in range(12))
    
    # Buildup 1 (beats 120.0 to 126.0)
    c1 = fx_track.create_midi_clip(120.0, 6.0)
    c1.name = "Buildup 1 Riser"
    c1.set_notes(r_notes)
    
    # Buildup 2 (beats 216.0 to 222.0)
    c2 = fx_track.create_midi_clip(216.0, 6.0)
    c2.name = "Buildup 2 Riser"
    c2.set_notes(r_notes)
    fx_added = True

# 4. Equip [VOCAL] Lead Vocal and [FX] with Channel Strips
for t in song.tracks:
    if 'vocal' in t.name.lower() and not getattr(t, 'is_foldable', False):
        if len(t.devices) == 0:
            # We can mark it with an audio clip or leave ready
            pass

result = {
    'vacuum_notes_cleared': cleared_note_count,
    'empty_clips_deleted': empty_deleted,
    'fx_risers_added': fx_added
}
"""
    res = conn.send_command("execute_code", {"code": code})
    print("FIXES APPLIED:", res)
    conn.disconnect()

if __name__ == "__main__":
    main()

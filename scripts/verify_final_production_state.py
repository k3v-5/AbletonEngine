from server import AbletonConnection

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        print("Failed to connect")
        return

    code = """
tracks_summary = []
for t_idx, t in enumerate(song.tracks):
    devs = [d.name for d in t.devices]
    clips_count = sum(1 for cs in t.clip_slots if cs.has_clip)
    vol = t.mixer_device.volume.value
    pan = t.mixer_device.panning.value
    tracks_summary.append({
        'index': t_idx,
        'name': t.name,
        'devices': devs,
        'clips': clips_count,
        'volume': vol,
        'panning': pan
    })

m_devs = [d.name for d in song.master_track.devices]
result = {
    'tracks': tracks_summary,
    'master_devices': m_devs,
    'tempo': song.tempo,
    'cue_points': [c.name for c in song.cue_points]
}
"""
    res = conn.send_command("execute_code", {"code": code})
    import json
    print(json.dumps(res.get("result", {}), indent=2))
    conn.disconnect()

if __name__ == "__main__":
    main()

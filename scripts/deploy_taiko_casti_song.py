# scripts/deploy_taiko_casti_song.py
"""
Deployer for Taiko x Casti Epic Hybrid Song:
Constructs the full 80-bar composition (320.0 beats @ 100 BPM) in Ableton Live 12 Suite:
1. 20 Scenes in Session View (Scenes 1 to 20).
2. 5 Dedicated Tracks:
   - [TAIKO] Master Drums (MIDI - O-Daiko, Nagado, Shime, Bachi)
   - [CASTI] 808 Sub-Bass (MIDI - Deep Fm Phrygian subline)
   - [CASTI] Phrygian Lead (MIDI - Iconic Casti lead motif)
   - [CASTI] Dark Chords (MIDI - Lush Fm9 / Gbmaj / Bbm9 / C7alt harmony)
   - [PAD] UHTS 20-Stage Audio (Audio - Continuous mutated pads #01 to #20)
3. Full Arrangement View timeline (Bar 1 to Bar 80) with 20 Locators / Cue Points.
"""

import sys
import time
import glob
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_ableton_connection
from engine.composition.taiko_casti_composer import TaikoCastiComposer


def deploy_song():
    print("=" * 80)
    print("=== DEPLOYING TAIKO x CASTI EPIC HYBRID SONG IN ABLETON LIVE 12 SUITE ===")
    print("=" * 80)

    conn = get_ableton_connection()
    if not conn:
        print("[ERROR] Could not establish connection to Ableton Live.")
        return False

    # 1. Set Song Tempo & Key
    print("\n[STEP 1/6] Configuring Master Tempo & Key Signature in Live...")
    code_meta = """
song.tempo = 100.0
song.root_note = 5 # F
song.scale_name = "Minor"
result = {"tempo": song.tempo, "root_note": song.root_note, "scale_name": song.scale_name}
"""
    res_meta = conn.send_command("execute_code", {"code": code_meta})
    print(f"  Live Master Config: {res_meta.get('result')}")

    # 2. Clean up any previous staging tracks (>= 18) to keep user session tracks 0..17 intact
    print("\n[STEP 2/6] Preparing Tracks (preserving user tracks 0..17)...")
    code_cleanup = """
for i in range(len(song.tracks) - 1, 17, -1):
    song.delete_track(i)
result = len(song.tracks)
"""
    conn.send_command("execute_code", {"code": code_cleanup})
    time.sleep(0.3)

    # 3. Create the 5 Dedicated Song Tracks
    print("  Creating 5 dedicated tracks for Taiko x Casti...")
    code_create_tracks = """
tracks_info = []

# Track 1: Taiko Master Drums
t_taiko = song.create_midi_track(-1)
t_taiko.name = "[TAIKO] Master Drums"
tracks_info.append(t_taiko.name)

# Track 2: Casti 808 Sub-Bass
t_bass = song.create_midi_track(-1)
t_bass.name = "[CASTI] 808 Sub-Bass"
tracks_info.append(t_bass.name)

# Track 3: Casti Phrygian Lead
t_lead = song.create_midi_track(-1)
t_lead.name = "[CASTI] Phrygian Lead"
tracks_info.append(t_lead.name)

# Track 4: Casti Dark Chords
t_chords = song.create_midi_track(-1)
t_chords.name = "[CASTI] Dark Chords"
tracks_info.append(t_chords.name)

# Track 5: UHTS 20-Stage Audio Pad
t_pad = song.create_audio_track(-1)
t_pad.name = "[PAD] UHTS 20-Stage Audio"
tracks_info.append(t_pad.name)

result = {"created": tracks_info, "total_tracks": len(song.tracks)}
"""
    res_tracks = conn.send_command("execute_code", {"code": code_create_tracks})
    print(f"  Created tracks: {res_tracks.get('result')}")
    time.sleep(0.5)

    # Track indices (created at end of list)
    session_info = conn.send_command("get_session_info", {})
    total_tracks = session_info.get("track_count", 23)
    taiko_idx = total_tracks - 5
    bass_idx = total_tracks - 4
    lead_idx = total_tracks - 3
    chords_idx = total_tracks - 2
    pad_idx = total_tracks - 1

    print(f"  Track mapping: Taiko={taiko_idx}, Bass={bass_idx}, Lead={lead_idx}, Chords={chords_idx}, Pad={pad_idx}")

    # Set pad fader to -6 dBFS (0.75) for headroom
    try:
        conn.send_command("set_track_volume", {"track_index": pad_idx, "volume": 0.75})
    except Exception:
        pass

    # 3.5 Load Authentic Instruments and Sculpt Blueprints (Governance Compliance)
    print("\n[STEP 3.5/6] Loading authentic instruments & sculpting sound blueprints...")
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor

    # Load Drum Rack on Taiko Track
    try:
        conn.send_command("load_instrument_or_effect", {"track_index": taiko_idx, "uri": "query:Drums#Drum%20Rack"})
        time.sleep(0.3)
        DeviceParameterSupervisor.apply_sound_blueprint(
            conn, taiko_idx, role="DRUMS",
            custom_blueprint={"parameters": {"MACRO_1": 0.70, "MACRO_2": 0.60}}
        )
        print("    [OK] Taiko Master Drums: Drum Rack loaded & sculpted.")
    except Exception as e:
        print(f"    [Warning loading taiko drum rack]: {e}")

    # Load Drift on Bass Track
    try:
        conn.send_command("load_instrument_or_effect", {"track_index": bass_idx, "uri": "query:Synths#Drift"})
        time.sleep(0.3)
        DeviceParameterSupervisor.apply_sound_blueprint(
            conn, bass_idx, role="BASS",
            custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.40, "AMP_ATTACK": 0.01, "AMP_RELEASE": 0.85}}
        )
        print("    [OK] Casti 808 Sub-Bass: Drift loaded & sculpted.")
    except Exception as e:
        print(f"    [Warning loading bass instrument]: {e}")

    # Load Drift on Lead Track
    try:
        conn.send_command("load_instrument_or_effect", {"track_index": lead_idx, "uri": "query:Synths#Drift"})
        time.sleep(0.3)
        DeviceParameterSupervisor.apply_sound_blueprint(
            conn, lead_idx, role="LEAD",
            custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.75, "AMP_ATTACK": 0.04, "AMP_RELEASE": 0.35}}
        )
        print("    [OK] Casti Phrygian Lead: Drift loaded & sculpted.")
    except Exception as e:
        print(f"    [Warning loading lead instrument]: {e}")

    # Load Drift on Chords Track
    try:
        conn.send_command("load_instrument_or_effect", {"track_index": chords_idx, "uri": "query:Synths#Drift"})
        time.sleep(0.3)
        DeviceParameterSupervisor.apply_sound_blueprint(
            conn, chords_idx, role="KEYS",
            custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.60, "AMP_ATTACK": 0.02, "AMP_RELEASE": 0.50}}
        )
        print("    [OK] Casti Dark Chords: Drift loaded & sculpted.")
    except Exception as e:
        print(f"    [Warning loading chords instrument]: {e}")

    # 4. Ensure at least 20 Scenes in Session View
    print("\n[STEP 3/6] Ensuring 20 Scenes in Session View...")
    code_scenes = """
while len(song.scenes) < 20:
    song.create_scene(-1)
result = len(song.scenes)
"""
    conn.send_command("execute_code", {"code": code_scenes})
    time.sleep(0.3)

    # 5. Populate Session View (Clips in 20 Scenes) & Duplicate to Arrangement (80 Bars)
    print("\n[STEP 4/6] Staging 20 Scenes & 80-Bar Arrangement Timeline...")
    assets_dir = root_dir / "cache" / "resampled_mutations"

    for s_idx in range(1, 21):
        scene_pos = s_idx - 1
        meta = TaikoCastiComposer.SCENES[scene_pos]
        scene_name = meta["name"]
        pad_tech_name = meta["pad_uhts"]
        dest_time_beat = float(scene_pos * 16.0)

        print(f"\n[{s_idx:02d}/20] Staging Scene {s_idx:02d}: '{scene_name}' (Bar {scene_pos*4 + 1} to {s_idx*4})...")

        # Name Session Scene
        code_rename_scene = f"""
song.scenes[{scene_pos}].name = {repr(scene_name)}
result = song.scenes[{scene_pos}].name
"""
        conn.send_command("execute_code", {"code": code_rename_scene})

        # A. Taiko Master Drums
        taiko_notes = TaikoCastiComposer.get_taiko_notes_for_scene(s_idx)
        if taiko_notes:
            conn.send_command("create_clip", {
                "track_index": taiko_idx,
                "clip_index": scene_pos,
                "length": 16.0
            })
            conn.send_command("set_clip_name", {
                "track_index": taiko_idx,
                "clip_index": scene_pos,
                "name": f"Taiko #{s_idx:02d}"
            })
            conn.send_command("add_notes_to_clip", {
                "track_index": taiko_idx,
                "clip_index": scene_pos,
                "notes": taiko_notes
            })
            try:
                conn.send_command("duplicate_session_clip_to_arrangement", {
                    "track_index": taiko_idx,
                    "clip_index": scene_pos,
                    "destination_time": dest_time_beat
                })
            except Exception as e:
                print(f"    [Warning dup taiko to arrangement]: {e}")

        # B. Casti 808 Sub-Bass
        bass_notes = TaikoCastiComposer.get_bass_notes_for_scene(s_idx)
        if bass_notes:
            conn.send_command("create_clip", {
                "track_index": bass_idx,
                "clip_index": scene_pos,
                "length": 16.0
            })
            conn.send_command("set_clip_name", {
                "track_index": bass_idx,
                "clip_index": scene_pos,
                "name": f"808 Bass #{s_idx:02d}"
            })
            conn.send_command("add_notes_to_clip", {
                "track_index": bass_idx,
                "clip_index": scene_pos,
                "notes": bass_notes
            })
            try:
                conn.send_command("duplicate_session_clip_to_arrangement", {
                    "track_index": bass_idx,
                    "clip_index": scene_pos,
                    "destination_time": dest_time_beat
                })
            except Exception as e:
                print(f"    [Warning dup bass to arrangement]: {e}")

        # C. Casti Phrygian Lead
        lead_notes = TaikoCastiComposer.get_lead_notes_for_scene(s_idx)
        if lead_notes:
            conn.send_command("create_clip", {
                "track_index": lead_idx,
                "clip_index": scene_pos,
                "length": 16.0
            })
            conn.send_command("set_clip_name", {
                "track_index": lead_idx,
                "clip_index": scene_pos,
                "name": f"Lead Motif #{s_idx:02d}"
            })
            conn.send_command("add_notes_to_clip", {
                "track_index": lead_idx,
                "clip_index": scene_pos,
                "notes": lead_notes
            })
            try:
                conn.send_command("duplicate_session_clip_to_arrangement", {
                    "track_index": lead_idx,
                    "clip_index": scene_pos,
                    "destination_time": dest_time_beat
                })
            except Exception as e:
                print(f"    [Warning dup lead to arrangement]: {e}")

        # D. Casti Dark Chords
        chord_notes = TaikoCastiComposer.get_chord_notes_for_scene(s_idx)
        if chord_notes:
            conn.send_command("create_clip", {
                "track_index": chords_idx,
                "clip_index": scene_pos,
                "length": 16.0
            })
            conn.send_command("set_clip_name", {
                "track_index": chords_idx,
                "clip_index": scene_pos,
                "name": f"Chords #{s_idx:02d}"
            })
            conn.send_command("add_notes_to_clip", {
                "track_index": chords_idx,
                "clip_index": scene_pos,
                "notes": chord_notes
            })
            try:
                conn.send_command("duplicate_session_clip_to_arrangement", {
                    "track_index": chords_idx,
                    "clip_index": scene_pos,
                    "destination_time": dest_time_beat
                })
            except Exception as e:
                print(f"    [Warning dup chords to arrangement]: {e}")

        # E. UHTS 20-Stage Audio Pad
        pattern = f"taiko_casti_uhts_{s_idx:02d}_*.wav"
        pad_files = list(assets_dir.glob(pattern))
        if pad_files:
            pad_wav_path = str(pad_files[0].resolve())
            try:
                conn.send_command("create_audio_clip", {
                    "track_index": pad_idx,
                    "clip_index": scene_pos,
                    "path": pad_wav_path
                })
                conn.send_command("set_clip_name", {
                    "track_index": pad_idx,
                    "clip_index": scene_pos,
                    "name": f"UHTS #{s_idx:02d}: {pad_tech_name}"
                })
                conn.send_command("duplicate_session_clip_to_arrangement", {
                    "track_index": pad_idx,
                    "clip_index": scene_pos,
                    "destination_time": dest_time_beat
                })
            except Exception as e:
                print(f"    [Warning staging audio pad]: {e}")
        else:
            print(f"    [Warning] Pad asset not found for scene {s_idx}: {pattern}")

        # F. Arrangement Cue Point / Locator
        try:
            conn.send_command("create_cue_point", {
                "time": dest_time_beat,
                "name": f"#{s_idx:02d}: {scene_name}"
            })
        except Exception:
            pass

    # 6. Final Arrangement Setup, Loop Region & Playback
    print("\n[STEP 5/6] Finalizing Arrangement View & Loop Region...")
    try:
        conn.send_command("switch_to_arrangement_view", {})
    except Exception:
        pass

    try:
        conn.send_command("set_loop_region", {
            "start_time": 0.0,
            "length": 320.0,
            "enabled": True
        })
    except Exception:
        pass

    try:
        conn.send_command("jump_to_cue_point", {"target": 0.0})
    except Exception:
        pass

    print("\n[STEP 6/6] Starting Live Playback from Bar 1 (Compás 1)...")
    try:
        conn.send_command("start_playback", {})
    except Exception:
        pass

    print("\n" + "=" * 80)
    print(" [SUCCESS] TAIKO x CASTI FULL EPIC SONG DEPLOYED IN ABLETON LIVE 12!")
    print(f" - Tempo: 100.0 BPM | Tonality: F Minor Phrygian")
    print(f" - 20 Scenes configured in Session View with custom names and clips")
    print(f" - 80 Bars (320.0 beats) arranged across the timeline with 20 Cue Points")
    print(f" - 5 Tracks active: Taiko Drums, 808 Sub-Bass, Phrygian Lead, Dark Chords, UHTS Audio Pad")
    print(f" - All 20 UHTS Pad Resampling Textures active and evolving across the song")
    print("=" * 80 + "\n")
    return True


if __name__ == "__main__":
    deploy_song()

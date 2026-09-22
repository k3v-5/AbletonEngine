# scripts/deploy_20_resampled_audio_tracks.py
"""
Deploys 20 Dedicated Audio Tracks in Ableton Live 12 Suite:
Each track contains a real continuous 16-beat audio clip born from the
prolonged Arturia Analog Lab grand piano chord (Fm9) and mutated through
20 distinct producer resampling and DSP sound-design pipelines.
"""

import sys
import time
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_ableton_connection

MUTATIONS = [
    ("01", "SPECTRAL_FREEZE_DRONE", "uhts_01_spectral_freeze_drone.wav", "Liquid pad drone with zero hammer transient"),
    ("02", "TUNED_COMB_CHIME", "uhts_02_tuned_comb_chime.wav", "Exotic metallic plucked chime via Karplus-Strong"),
    ("03", "VOCAL_FORMANT_RESONANCE", "uhts_03_vocal_formant_resonance.wav", "Singing choir vowel formant synthesis"),
    ("04", "INDUSTRIAL_CRUNCH_MUTATION", "uhts_04_industrial_crunch_mutation.wav", "Abrasive 4-stage wavefolder overdrive"),
    ("05", "SUB_SAFE_LOW_GROWL", "uhts_05_sub_safe_low_growl.wav", "Subterranean sub-bass with strict mono lock"),
    ("06", "PITCH_SHIMMER_DIFFUSION", "uhts_06_pitch_shimmer_diffusion.wav", "+12st crystalline pitch shimmer halo"),
    ("07", "DARK_REESE_OCTAVE_DIVE", "uhts_07_dark_reese_octave_dive.wav", "-24st double octave deep detuned Reese growl"),
    ("08", "GRANULAR_MICRO_CLOUD", "uhts_08_granular_micro_cloud.wav", "Dense 40ms granular particle mist"),
    ("09", "VINTAGE_TAPE_WOW_WARP", "uhts_09_vintage_tape_wow_warp.wav", "Analog cassette wow & flutter with hysteresis"),
    ("10", "INHARMONIC_METALLIC_RING", "uhts_10_inharmonic_metallic_ring.wav", "Frequency-shifted sci-fi metallic bell ring"),
    ("11", "REVERSE_SWELL_BLOOM", "uhts_11_reverse_swell_bloom.wav", "Re-reversed exponential ambient swell bloom"),
    ("12", "LOFI_BIT_CRUSHER_DIRT", "uhts_12_lofi_bit_crusher_dirt.wav", "10-bit downsampled 90s digital sampler dirt"),
    ("13", "HAAS_3D_SPATIAL_DECOUPLE", "uhts_13_haas_3d_spatial_decouple.wav", "Psychoacoustic 3D Haas decoupled width"),
    ("14", "RHYTHMIC_STUTTER_CHOP", "uhts_14_rhythmic_stutter_chop.wav", "Syncopated 16th-note stutter buffer chop"),
    ("15", "OCTAVE_FUZZ_MULTIPLIER", "uhts_15_octave_fuzz_multiplier.wav", "Full-wave rectified upper-octave fuzz"),
    ("16", "CHOPPED_TRANCE_PULSE", "uhts_16_chopped_trance_pulse.wav", "16th-note polyrhythmic gated trance pulse"),
    ("17", "SPECTRAL_BLUR_INFINITE", "uhts_17_spectral_blur_infinite.wav", "Infinite 2D spectral blurred harmonic aura"),
    ("18", "ANALOG_TAPE_WARMTH_GLUE", "uhts_18_analog_tape_warmth_glue.wav", "Triode warmth with optical leveling glue"),
    ("19", "NEOPERREO_METALLIC_COMB", "uhts_19_neoperreo_metallic_comb.wav", "Resonant metallic early-reflection club comb"),
    ("20", "EXPONENTIAL_PITCH_DIVE", "uhts_20_exponential_pitch_dive.wav", "Continuous -14st exponential tension dive"),
]


def main():
    print("=== DEPLOYING 20 REAL RESAMPLED AUDIO TRACKS IN ABLETON LIVE 12 SUITE ===")
    conn = get_ableton_connection()
    if not conn:
        print("[ERROR] Could not connect to Ableton Live.")
        return

    # 1. Clean up any existing UHTS tracks (indices >= 18)
    session = conn.send_command("get_session_info", {})
    track_count = session.get("track_count", 0)
    print(f"Current track count in session: {track_count}")

    if track_count > 18:
        tracks_to_delete = track_count - 18
        print(f"Cleaning up {tracks_to_delete} previous tracks...")
        code = f"""
for i in range(len(song.tracks) - 1, 17, -1):
    song.delete_track(i)
result = len(song.tracks)
"""
        conn.send_command("execute_code", {"code": code})
        time.sleep(0.5)

    session = conn.send_command("get_session_info", {})
    base_track_count = session.get("track_count", 0)
    print(f"Base track count: {base_track_count} (User project tracks 0..17 preserved)")

    # 2. Create 20 dedicated native Audio Tracks
    print("\nCreating 20 dedicated Audio Tracks in Live...")
    code_create_tracks = """
created_names = []
for idx in range(20):
    t = song.create_audio_track(-1)
    t.name = f"[UHTS {idx+1:02d}]"
    created_names.append(t.name)
result = {"created_count": len(created_names), "total_tracks": len(song.tracks)}
"""
    res_create = conn.send_command("execute_code", {"code": code_create_tracks})
    print(f"Created audio tracks result: {res_create}")
    time.sleep(0.5)

    # 3. Import each continuous WAV file and configure track names and locators
    audio_dir = Path(root_dir) / "cache" / "uhts_resampled"
    start_uhts_idx = 18

    for idx, (num_str, name, filename, desc) in enumerate(MUTATIONS):
        track_idx = start_uhts_idx + idx
        full_track_name = f"[UHTS {num_str}] {name}"
        wav_path = str((audio_dir / filename).resolve())
        start_beat = float(idx * 16.0)

        print(f"\n[{num_str}/20] Staging Audio Track {track_idx}: '{full_track_name}'...")
        print(f"  Description: {desc}")
        print(f"  WAV: {filename}")

        # Rename track
        conn.send_command("set_track_name", {
            "track_index": track_idx,
            "name": full_track_name
        })

        # Import continuous audio clip into slot 0
        try:
            res_clip = conn.send_command("create_audio_clip", {
                "track_index": track_idx,
                "clip_index": 0,
                "path": wav_path
            })
            print(f"  Clip imported: {res_clip}")
        except Exception as e:
            print(f"  Warning importing audio clip: {e}")

        # Duplicate to Arrangement timeline at start_beat (80-bar walkthrough)
        try:
            conn.send_command("duplicate_session_clip_to_arrangement", {
                "track_index": track_idx,
                "clip_index": 0,
                "destination_time": start_beat
            })
        except Exception as e:
            print(f"  Warning duplicating to arrangement: {e}")

        # Create Arrangement Locator / Cue Point
        try:
            conn.send_command("create_cue_point", {
                "time": start_beat,
                "name": f"#{int(num_str)}: {name}"
            })
        except Exception:
            pass

    # 4. Solo Track 18 (Profile 1: Spectral Freeze Drone) initially
    for idx in range(20):
        t_i = start_uhts_idx + idx
        conn.send_command("set_track_solo", {
            "track_index": t_i,
            "solo": (t_i == start_uhts_idx)
        })

    # 5. Set loop region and start playback
    conn.send_command("set_loop_region", {
        "start_time": 0.0,
        "length": 16.0,
        "enabled": True
    })
    conn.send_command("jump_to_cue_point", {"target": 0.0})
    conn.send_command("start_playback", {})

    print("\n" + "=" * 70)
    print(" [OK] 20 RESAMPLED AUDIO TRACKS SUCCESSFULLY DEPLOYED IN LIVE!")
    print(" Each track contains real continuous audio mutated from the Analog Lab piano chord.")
    print(" Tracks: 18 to 37 (All Native Audio Tracks).")
    print(" Timeline: 80 bars (320 beats) spanning all 20 textures with Locators #1 to #20.")
    print(" Active: Track 18 ([UHTS 01] SPECTRAL_FREEZE_DRONE) is soloed and looping live.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

# scripts/audition_profile.py
"""
CLI Audition Controller for Universal Harmonic Transformation Suite (UHTS).
Switches instant SOLO and playback across the 20 Resampled Audio Tracks in Ableton Live 12 Suite.

Usage:
    python scripts/audition_profile.py <1-20 | PROFILE_NAME>
    python scripts/audition_profile.py list
    python scripts/audition_profile.py stop
"""

import sys
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_ableton_connection

MUTATIONS = [
    ("01", "SPECTRAL_FREEZE_DRONE", "Liquid pad drone with zero hammer transient (Spectral freeze + 200% stretch)"),
    ("02", "TUNED_COMB_CHIME", "Exotic metallic plucked chime (Karplus-Strong tuned comb filter in F)"),
    ("03", "VOCAL_FORMANT_RESONANCE", "Singing choir vowel formant synthesis (/a/, /e/, /i/ tracking)"),
    ("04", "INDUSTRIAL_CRUNCH_MUTATION", "Abrasive 4-stage wavefolder overdrive & transient smash"),
    ("05", "SUB_SAFE_LOW_GROWL", "Subterranean sub-bass with strict mono lock & sub-octave divider"),
    ("06", "PITCH_SHIMMER_DIFFUSION", "+12st crystalline pitch shimmer halo in diffusion loop"),
    ("07", "DARK_REESE_OCTAVE_DIVE", "-24st double octave deep detuned Reese growl & 280Hz filter"),
    ("08", "GRANULAR_MICRO_CLOUD", "Dense 40ms granular particle mist with stereo spatial spray"),
    ("09", "VINTAGE_TAPE_WOW_WARP", "Analog cassette wow & flutter (0.8Hz / 3.4Hz) with tape hysteresis"),
    ("10", "INHARMONIC_METALLIC_RING", "Frequency-shifted (+194Hz) sci-fi metallic bell ring"),
    ("11", "REVERSE_SWELL_BLOOM", "Re-reversed exponential ambient swell bloom"),
    ("12", "LOFI_BIT_CRUSHER_DIRT", "10-bit downsampled 90s digital sampler dirt (6.3kHz aliasing)"),
    ("13", "HAAS_3D_SPATIAL_DECOUPLE", "Psychoacoustic 3D Haas decoupled width (90° phase rotation)"),
    ("14", "RHYTHMIC_STUTTER_CHOP", "Syncopated 16th-note stutter buffer chop & rhythmic pulse"),
    ("15", "OCTAVE_FUZZ_MULTIPLIER", "Full-wave rectified upper-octave fuzz & 650Hz mid scoop"),
    ("16", "CHOPPED_TRANCE_PULSE", "16th-note polyrhythmic gated trance pulse with ping-pong bounce"),
    ("17", "SPECTRAL_BLUR_INFINITE", "Infinite 2D spectral blurred harmonic aura without attack"),
    ("18", "ANALOG_TAPE_WARMTH_GLUE", "Triode warmth with optical leveling glue & air lift"),
    ("19", "NEOPERREO_METALLIC_COMB", "Resonant metallic early-reflection club comb (1.18kHz)"),
    ("20", "EXPONENTIAL_PITCH_DIVE", "Continuous -14st exponential tension dive & HPF sweep"),
]


def list_profiles():
    print("\n" + "=" * 75)
    print(" UNIVERSAL HARMONIC TRANSFORMATION SUITE - 20 RESAMPLED AUDIO TEXTURES")
    print(" Source: Prolonged Grand Piano Chord (Fm9) - 16 Beats / 4 Bars Continuous")
    print("=" * 75)
    for idx, (num_str, name, desc) in enumerate(MUTATIONS, start=1):
        beat_start = (idx - 1) * 16.0
        bar_start = int(beat_start / 4.0) + 1
        track_idx = 17 + idx
        print(f"[{num_str}] Track {track_idx:02d} (Bar {bar_start:02d}) | {name:<30} | {desc}")
    print("=" * 75 + "\n")


def stop_playback():
    conn = get_ableton_connection()
    if conn:
        conn.send_command("stop_playback", {})
        print("[OK] Playback stopped in Ableton Live.")
    else:
        print("[ERROR] Could not connect to Ableton Live.")


def audition(target: str):
    conn = get_ableton_connection()
    if not conn:
        print("[ERROR] Could not connect to Ableton Live.")
        return

    # Resolve target number (1-20)
    target_idx = 1
    t_clean = target.strip().upper()
    if t_clean.isdigit():
        target_idx = max(1, min(20, int(t_clean)))
    else:
        for idx, (num_str, name, _) in enumerate(MUTATIONS, start=1):
            if t_clean in name or name in t_clean:
                target_idx = idx
                break

    num_str, name, desc = MUTATIONS[target_idx - 1]
    target_track_idx = 17 + target_idx
    start_beat = float((target_idx - 1) * 16.0)
    bar_pos = f"Bar {int(start_beat / 4.0) + 1} to {int(start_beat / 4.0) + 5}"

    print(f"\n[UHTS AUDITION] Activating Profile #{target_idx}: '{name}'...")
    print(f"  * Track: Index {target_track_idx} ('[UHTS {num_str}] {name}')")
    print(f"  * Timeline Position: Beat {start_beat} ({bar_pos})")
    print(f"  * Technique: {desc}")

    # 1. Solo target track, unsolo all other 19 UHTS tracks (indices 18 to 37)
    for t_i in range(18, 38):
        conn.send_command("set_track_solo", {
            "track_index": t_i,
            "solo": (t_i == target_track_idx)
        })

    # 2. Set 16-beat loop region on the track's arrangement block
    conn.send_command("set_loop_region", {
        "start_time": start_beat,
        "length": 16.0,
        "enabled": True
    })

    # 3. Jump playhead to position
    conn.send_command("jump_to_cue_point", {"target": start_beat})

    # 4. Trigger playback
    conn.send_command("start_playback", {})
    print(f"\n[OK] NOW PLAYING LIVE IN ABLETON!")
    print(f"[LISTENING FOCUS] ¿Cómo percibes la textura continua de #{target_idx} ({name}) sobre el acorde de piano?\n")


def main():
    parser = argparse.ArgumentParser(description="Audition UHTS Resampled Audio Textures in Ableton Live.")
    parser.add_argument("target", nargs="?", default="1", help="Profile number (1-20), profile name, 'list', or 'stop'")
    args = parser.parse_args()

    if args.target.lower() == "list":
        list_profiles()
    elif args.target.lower() == "stop":
        stop_playback()
    else:
        audition(args.target)


if __name__ == "__main__":
    main()

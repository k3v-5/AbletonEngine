# scripts/audition_profile.py
"""
CLI Audition Controller for Universal Harmonic Transformation Suite (UHTS)
Allows instant playback, looping, and device chain deployment for any of the 20 profiles in Ableton Live 12 Suite.

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

from server import get_ableton_connection, audition_harmonic_profile
from engine.sound_design.harmonic_transformation_suite import (
    HarmonicTransformationSuite,
    HarmonicProfile,
)


def list_profiles():
    print("\n" + "=" * 65)
    print(" UNIVERSAL HARMONIC TRANSFORMATION SUITE - 20 PROFILES")
    print("=" * 65)
    for idx, p in enumerate(HarmonicProfile, start=1):
        cfg = HarmonicTransformationSuite.get_config(p)
        beat_start = (idx - 1) * 16.0
        bar_start = int(beat_start / 4.0) + 1
        print(f"[{idx:02d}] {p.value:<30} (Bar {bar_start:02d}) | Drive: {cfg.drive_db:4.1f}dB | Formant: {cfg.formant_freq_hz:5.0f}Hz | OTT: {int(cfg.ott_depth*100):2d}%")
    print("=" * 65 + "\n")


def stop_playback():
    conn = get_ableton_connection()
    if conn:
        conn.send_command("stop_playback", {})
        print("[OK] Playback stopped in Ableton Live.")
    else:
        print("[ERROR] Could not connect to Ableton Live.")


def main():
    parser = argparse.ArgumentParser(description="Audition UHTS profiles in Ableton Live 12 Suite.")
    parser.add_argument("target", nargs="?", default="1", help="Profile number (1-20), profile name, 'list', or 'stop'")
    parser.add_argument("--track", type=int, default=None, help="Target track index (defaults to UHTS Showcase track)")
    parser.add_argument("--no-loop", action="store_true", help="Disable 16-beat looping")
    parser.add_argument("--no-play", action="store_true", help="Do not trigger playback automatically")

    args = parser.parse_args()

    if args.target.lower() == "list":
        list_profiles()
        return

    if args.target.lower() == "stop":
        stop_playback()
        return

    print(f"\n[UHTS AUDITION] Preparing audition for profile '{args.target}'...")
    res = audition_harmonic_profile(
        profile_target=args.target,
        track_index=args.track,
        loop=not args.no_loop,
        auto_play=not args.no_play
    )

    if res.get("status") == "success":
        print("[OK] AUDITION ACTIVE IN LIVE!")
        print(f"  * Profile: #{res['profile_number']} - {res['profile_name']}")
        print(f"  * Timeline Position: Beat {res['arrangement_beat']} ({res['bar_position']})")
        print(f"  * Track: Index {res['track_index']}")
        print(f"  * Loaded Physical Chain: {', '.join(res['loaded_devices'])}")
        cfg = res["acoustic_config"]
        print(f"  * Settings: Drive={cfg['drive_db']}dB ({cfg['curve_type']}), Formant={cfg['formant_freq_hz']}Hz (Q={cfg['formant_q']}), OTT={int(cfg['ott_depth']*100)}%, Space={int(cfg['space_wet']*100)}%")
        print(f"\n[LISTENING FOCUS] {res['feedback_prompt']}\n")
    else:
        print(f"[ERROR] Error during audition: {res.get('message')}")


if __name__ == "__main__":
    main()

# scripts/deploy_uhts_showcase_live.py
"""
Deploys the UHTS 20-Profile Showcase Environment in Ableton Live 12 Suite:
1. Creates dedicated track: '[UHTS SHOWCASE] Profile Audition'.
2. Generates 20 custom 4-bar clips (Fm Phrygian) across an 80-bar timeline.
3. Inserts 20 Locators (Cue Points) at each 16-beat boundary:
   #1: PAD_ATMOSPHERE, #2: METALLIC_WAVEFOLDER, ... #20: PITCH_DIVE_TENSION_RISER.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_ableton_connection
from engine.sound_design.harmonic_transformation_suite import (
    HarmonicTransformationSuite,
    HarmonicProfile,
)

def get_profile_notes(profile: HarmonicProfile) -> list:
    """Returns specialized musical notes in Fm Phrygian tailored to the profile's acoustic role."""
    p_val = profile.value.lower()
    
    # Bass / Sub growl profiles
    if "bass" in p_val or "growl" in p_val:
        return [
            {"pitch": 41, "start_time": 0.0, "duration": 3.75, "velocity": 110},  # F1
            {"pitch": 42, "start_time": 4.0, "duration": 3.75, "velocity": 115},  # Gb1 (Phrygian tension)
            {"pitch": 41, "start_time": 8.0, "duration": 3.75, "velocity": 110},  # F1
            {"pitch": 48, "start_time": 12.0, "duration": 3.5, "velocity": 112},  # C2
        ]
    
    # Lead / Wavefolder / Fuzz / Bell profiles
    elif "wavefolder" in p_val or "fuzz" in p_val or "bell" in p_val or "lead" in p_val:
        notes = []
        lead_pitches = [65, 66, 68, 72, 68, 66, 65, 60]  # F3, Gb3, Ab3, C4, Ab3, Gb3, F3, C3
        for idx, p in enumerate(lead_pitches):
            notes.append({"pitch": p, "start_time": float(idx * 2.0), "duration": 1.5, "velocity": 105})
        return notes
        
    # Percussion / Snare / Bit crusher / Crunch
    elif "snare" in p_val or "crunch" in p_val or "bit_crusher" in p_val:
        notes = []
        for beat in [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0]:
            notes.append({"pitch": 60, "start_time": beat, "duration": 0.5, "velocity": 115})
            notes.append({"pitch": 66, "start_time": beat + 1.0, "duration": 0.5, "velocity": 100})
        return notes
        
    # Vocal / Chop profiles
    elif "vocal" in p_val or "chop" in p_val:
        notes = []
        for b in range(16):
            p = 65 if b % 4 != 3 else 66
            notes.append({"pitch": p, "start_time": float(b), "duration": 0.75, "velocity": 98})
        return notes
        
    # Tension riser
    elif "riser" in p_val or "dive" in p_val:
        notes = []
        for b in range(16):
            pitch = 60 + b
            notes.append({"pitch": pitch, "start_time": float(b), "duration": 0.9, "velocity": min(127, 70 + b * 3)})
        return notes
        
    # Default Pad / Atmosphere / Shimmer / Tape / Drone / Gate / Freeze / Warmth
    else:
        return [
            # Bar 0-1: Fm9 (F, Ab, C, Eb, G)
            {"pitch": 65, "start_time": 0.0, "duration": 7.5, "velocity": 85},  # F3
            {"pitch": 68, "start_time": 0.0, "duration": 7.5, "velocity": 85},  # Ab3
            {"pitch": 72, "start_time": 0.0, "duration": 7.5, "velocity": 88},  # C4
            {"pitch": 75, "start_time": 0.0, "duration": 7.5, "velocity": 82},  # Eb4
            # Bar 2-3: Gbmaj7 (Gb, Bb, Db, F) - Phrygian tension chord
            {"pitch": 66, "start_time": 8.0, "duration": 7.5, "velocity": 90},  # Gb3
            {"pitch": 70, "start_time": 8.0, "duration": 7.5, "velocity": 88},  # Bb3
            {"pitch": 73, "start_time": 8.0, "duration": 7.5, "velocity": 88},  # Db4
            {"pitch": 77, "start_time": 8.0, "duration": 7.5, "velocity": 92},  # F4
        ]

def main():
    print("=== Deploying UHTS 20-Profile Showcase in Ableton Live ===")
    conn = get_ableton_connection()
    if not conn:
        print("Error: Could not connect to Ableton Live.")
        return

    session = conn.send_command("get_session_info", {})
    track_count = session.get("track_count", 0)
    print(f"Current track count in Live: {track_count}")

    # Check if showcase track exists
    showcase_track_idx = None
    for idx in range(track_count):
        t_info = conn.send_command("get_track_info", {"track_index": idx})
        t_name = t_info.get("name", "")
        if "UHTS SHOWCASE" in t_name:
            showcase_track_idx = idx
            print(f"Found existing showcase track at index {idx}: '{t_name}'")
            break

    # If not found, create a new MIDI track
    if showcase_track_idx is None:
        print("Creating new MIDI track for UHTS Showcase...")
        res = conn.send_command("create_midi_track", {})
        # Track is added at the end
        showcase_track_idx = track_count
        time.sleep(0.3)
        conn.send_command("set_track_name", {
            "track_index": showcase_track_idx,
            "name": "[UHTS SHOWCASE] Profile Audition"
        })
        # Load instrument: Drift
        try:
            conn.send_command("load_browser_item", {
                "track_index": showcase_track_idx,
                "item_uri": "query:Synths#Drift"
            })
        except Exception as e:
            print(f"Warning loading Drift: {e}")
        time.sleep(0.5)
    else:
        # Verify instrument on existing showcase track
        info = conn.send_command("get_track_info", {"track_index": showcase_track_idx})
        if not info.get("devices"):
            try:
                conn.send_command("load_browser_item", {
                    "track_index": showcase_track_idx,
                    "item_uri": "query:Synths#Drift"
                })
            except Exception as e:
                print(f"Warning loading Drift: {e}")

    print(f"Target Showcase Track: Index {showcase_track_idx}")

    # Deploy 20 sections of 4 bars (16 beats each)
    profiles = list(HarmonicProfile)
    for idx, profile in enumerate(profiles):
        locator_num = idx + 1
        start_beat = float(idx * 16.0)
        locator_name = f"#{locator_num}: {profile.value}"
        print(f"[{locator_num}/20] Staging '{locator_name}' at beat {start_beat}...")

        # 1. Create clip in session slot 0 for staging
        try:
            conn.send_command("delete_clip", {"track_index": showcase_track_idx, "clip_index": 0})
        except Exception:
            pass
        conn.send_command("create_clip", {
            "track_index": showcase_track_idx,
            "clip_index": 0,
            "length": 16.0
        })
        
        # 2. Add tailored notes
        notes = get_profile_notes(profile)
        conn.send_command("add_notes_to_clip", {
            "track_index": showcase_track_idx,
            "clip_index": 0,
            "notes": notes
        })

        # 3. Set clip name
        try:
            conn.send_command("set_clip_name", {
                "track_index": showcase_track_idx,
                "clip_index": 0,
                "name": locator_name
            })
        except Exception:
            pass

        # 4. Duplicate to arrangement timeline
        conn.send_command("duplicate_session_clip_to_arrangement", {
            "track_index": showcase_track_idx,
            "clip_index": 0,
            "destination_time": start_beat
        })

        # 5. Insert arrangement Locator / Cue Point
        try:
            conn.send_command("create_cue_point", {
                "time": start_beat,
                "name": locator_name
            })
        except Exception as e:
            print(f"  Note on cue point: {e}")

    print("\n=== UHTS 20-Profile Showcase Deployed Successfully in Live! ===")
    print("Timeline: 80 bars (320 beats) spanning all 20 profiles with Locators #1 to #20.")

if __name__ == "__main__":
    main()

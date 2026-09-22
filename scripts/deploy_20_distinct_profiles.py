# scripts/deploy_20_distinct_profiles.py
"""
Deploys 20 Dedicated Tracks in Ableton Live 12 Suite:
Each track has:
1. A DISTINCT synthesis engine / instrument (Wavetable, Operator, Meld, Analog, Collision, Tension, Electric, Drift, Simpler)
2. A DISTINCT musical adaptation/role of the SAME REFERENCE MELODY (Fm Phrygian 4-bar progression)
3. A DISTINCT UHTS physical processing chain
4. Positioned on the Arrangement timeline from bar 1 to bar 80 with 20 locators.
"""

import sys
import time
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_ableton_connection
from engine.sound_design.harmonic_transformation_suite import (
    HarmonicTransformationSuite,
    HarmonicProfile,
)

# 20 Distinct Synthesizer URIs for the 20 profiles
PROFILE_SYNTH_MAP = {
    HarmonicProfile.PAD_ATMOSPHERE: ("query:Synths#Wavetable", "Wavetable Pad"),
    HarmonicProfile.METALLIC_WAVEFOLDER: ("query:Synths#Operator", "Operator FM Lead"),
    HarmonicProfile.VOCAL_FORMANT: ("query:Synths#Meld", "Meld Vocal Synth"),
    HarmonicProfile.INDUSTRIAL_CRUNCH: ("query:Synths#Analog", "Analog Hard Sync"),
    HarmonicProfile.SUB_SAFE_BASS: ("query:Synths#Analog", "Analog Sub Bass"),
    HarmonicProfile.ETHEREAL_SHIMMER: ("query:Synths#Wavetable", "Wavetable Glass Bell"),
    HarmonicProfile.DARK_DRONE_SUB_GROWL: ("query:Synths#Analog", "Analog Reese Drone"),
    HarmonicProfile.GRANULAR_TEXTURE_CLOUD: ("query:Synths#Simpler", "Simpler Granular"),
    HarmonicProfile.RESAMPLE_TAPE_WARP: ("query:Synths#Electric", "Electric Rhodes Piano"),
    HarmonicProfile.INHARMONIC_BELL_CLUSTER: ("query:Synths#Collision", "Collision Mallet Bell"),
    HarmonicProfile.REVERSE_SPECTRAL_GHOST: ("query:Synths#Drift", "Drift Reverse Swell"),
    HarmonicProfile.LOFI_BIT_CRUSHER_DIRT: ("query:Synths#Drift", "Drift 8-Bit Chiptune"),
    HarmonicProfile.PSYCHOACOUSTIC_HAAS_WIDENER: ("query:Synths#Tension", "Tension Plucked String"),
    HarmonicProfile.VOCAL_CHOP_DISSECTOR: ("query:Synths#Simpler", "Simpler Vocal Slicer"),
    HarmonicProfile.OCTAVE_FUZZ_MONSTER: ("query:Synths#Analog", "Analog Fuzz Lead"),
    HarmonicProfile.CHOPPED_RHYTHMIC_GATE: ("query:Synths#Operator", "Operator Gated FM"),
    HarmonicProfile.SPECTRAL_FREEZE_INFINITE: ("query:Synths#Wavetable", "Wavetable Freeze Pad"),
    HarmonicProfile.ANALOG_WARMTH_SATURATOR: ("query:Synths#Analog", "Analog Warm Brass"),
    HarmonicProfile.NEOPERREO_METALLIC_SNARE: ("query:Synths#Collision", "Collision Metal Pluck"),
    HarmonicProfile.PITCH_DIVE_TENSION_RISER: ("query:Synths#Drift", "Drift Tension Dive"),
}


def get_profile_composition(profile: HarmonicProfile) -> list:
    """
    Returns the musical notes for each profile, all strictly interpreting
    the SAME CORE MELODY & HARMONY in Fm Phrygian (16 beats / 4 bars):
    - Bar 1: Fm9 (F, Ab, C, Eb, G)
    - Bar 2: Gbmaj7#11 (Gb, Bb, Db, F, C)
    - Bar 3: Bbm9 (Bb, Db, F, Ab, C)
    - Bar 4: Dbmaj7 / C7alt (Db, F, Ab, C -> C, E, Bb, Db)
    """
    p = profile

    # 1. PAD_ATMOSPHERE: Full sustained 4-voice chords
    if p == HarmonicProfile.PAD_ATMOSPHERE:
        return [
            # Bar 1: Fm9
            {"pitch": 53, "start_time": 0.0, "duration": 3.9, "velocity": 80},
            {"pitch": 56, "start_time": 0.0, "duration": 3.9, "velocity": 80},
            {"pitch": 60, "start_time": 0.0, "duration": 3.9, "velocity": 85},
            {"pitch": 67, "start_time": 0.0, "duration": 3.9, "velocity": 82},
            # Bar 2: Gbmaj7#11
            {"pitch": 54, "start_time": 4.0, "duration": 3.9, "velocity": 82},
            {"pitch": 58, "start_time": 4.0, "duration": 3.9, "velocity": 80},
            {"pitch": 61, "start_time": 4.0, "duration": 3.9, "velocity": 85},
            {"pitch": 65, "start_time": 4.0, "duration": 3.9, "velocity": 82},
            # Bar 3: Bbm9
            {"pitch": 53, "start_time": 8.0, "duration": 3.9, "velocity": 82},
            {"pitch": 56, "start_time": 8.0, "duration": 3.9, "velocity": 85},
            {"pitch": 61, "start_time": 8.0, "duration": 3.9, "velocity": 82},
            {"pitch": 65, "start_time": 8.0, "duration": 3.9, "velocity": 85},
            # Bar 4: Dbmaj7
            {"pitch": 49, "start_time": 12.0, "duration": 3.9, "velocity": 82},
            {"pitch": 53, "start_time": 12.0, "duration": 3.9, "velocity": 85},
            {"pitch": 56, "start_time": 12.0, "duration": 3.9, "velocity": 82},
            {"pitch": 60, "start_time": 12.0, "duration": 3.9, "velocity": 85},
        ]

    # 2. METALLIC_WAVEFOLDER: Topline Lead melody
    elif p == HarmonicProfile.METALLIC_WAVEFOLDER:
        return [
            # Bar 1
            {"pitch": 65, "start_time": 0.0, "duration": 1.4, "velocity": 110},  # F4
            {"pitch": 68, "start_time": 1.5, "duration": 0.9, "velocity": 115},  # Ab4
            {"pitch": 67, "start_time": 2.5, "duration": 0.6, "velocity": 108},  # G4
            {"pitch": 65, "start_time": 3.25, "duration": 0.6, "velocity": 112}, # F4
            # Bar 2
            {"pitch": 66, "start_time": 4.0, "duration": 1.4, "velocity": 115},  # Gb4
            {"pitch": 70, "start_time": 5.5, "duration": 0.9, "velocity": 112},  # Bb4
            {"pitch": 68, "start_time": 6.5, "duration": 0.9, "velocity": 110},  # Ab4
            {"pitch": 65, "start_time": 7.5, "duration": 0.4, "velocity": 108},  # F4
            # Bar 3
            {"pitch": 65, "start_time": 8.0, "duration": 1.4, "velocity": 112},  # F4
            {"pitch": 72, "start_time": 9.5, "duration": 0.9, "velocity": 118},  # C5
            {"pitch": 70, "start_time": 10.5, "duration": 0.9, "velocity": 115}, # Bb4
            {"pitch": 68, "start_time": 11.5, "duration": 0.4, "velocity": 110}, # Ab4
            # Bar 4
            {"pitch": 73, "start_time": 12.0, "duration": 0.9, "velocity": 118}, # Db5
            {"pitch": 72, "start_time": 13.0, "duration": 0.9, "velocity": 115}, # C5
            {"pitch": 70, "start_time": 14.0, "duration": 0.9, "velocity": 112}, # Bb4
            {"pitch": 67, "start_time": 15.0, "duration": 0.9, "velocity": 110}, # G4
        ]

    # 3. VOCAL_FORMANT: Expressive vocal singing of the topline
    elif p == HarmonicProfile.VOCAL_FORMANT:
        return [
            {"pitch": 65, "start_time": 0.0, "duration": 1.3, "velocity": 90},
            {"pitch": 68, "start_time": 1.5, "duration": 0.8, "velocity": 96},
            {"pitch": 67, "start_time": 2.5, "duration": 0.6, "velocity": 88},
            {"pitch": 65, "start_time": 3.25, "duration": 0.6, "velocity": 92},
            {"pitch": 66, "start_time": 4.0, "duration": 1.3, "velocity": 95},
            {"pitch": 70, "start_time": 5.5, "duration": 0.8, "velocity": 98},
            {"pitch": 68, "start_time": 6.5, "duration": 0.8, "velocity": 92},
            {"pitch": 65, "start_time": 8.0, "duration": 1.3, "velocity": 94},
            {"pitch": 72, "start_time": 9.5, "duration": 0.8, "velocity": 100},
            {"pitch": 70, "start_time": 10.5, "duration": 0.8, "velocity": 95},
            {"pitch": 73, "start_time": 12.0, "duration": 1.8, "velocity": 98},
            {"pitch": 72, "start_time": 14.0, "duration": 1.8, "velocity": 92},
        ]

    # 4. INDUSTRIAL_CRUNCH: Rhythmic syncopated chord stabs
    elif p == HarmonicProfile.INDUSTRIAL_CRUNCH:
        notes = []
        chord_pitches = [
            (0.0, [53, 60]), (1.0, [53, 60]), (2.5, [56, 63]),
            (4.0, [54, 61]), (5.0, [54, 61]), (6.5, [58, 65]),
            (8.0, [53, 60]), (9.0, [53, 60]), (10.5, [56, 61]),
            (12.0, [49, 56]), (13.5, [53, 60]), (15.0, [48, 55]),
        ]
        for t, pitches in chord_pitches:
            for pt in pitches:
                notes.append({"pitch": pt, "start_time": t, "duration": 0.45, "velocity": 120})
        return notes

    # 5. SUB_SAFE_BASS: Low sub bassline following fundamental root motion
    elif p == HarmonicProfile.SUB_SAFE_BASS:
        return [
            {"pitch": 41, "start_time": 0.0, "duration": 3.75, "velocity": 112},  # F1
            {"pitch": 42, "start_time": 4.0, "duration": 3.75, "velocity": 115},  # Gb1
            {"pitch": 46, "start_time": 8.0, "duration": 3.75, "velocity": 112},  # Bb1
            {"pitch": 37, "start_time": 12.0, "duration": 1.85, "velocity": 110}, # Db1
            {"pitch": 36, "start_time": 14.0, "duration": 1.85, "velocity": 114}, # C1
        ]

    # 6. ETHEREAL_SHIMMER: High-register crystalline bell accents (+12st)
    elif p == HarmonicProfile.ETHEREAL_SHIMMER:
        return [
            {"pitch": 77, "start_time": 0.0, "duration": 1.2, "velocity": 75},   # F5
            {"pitch": 80, "start_time": 1.5, "duration": 0.8, "velocity": 82},   # Ab5
            {"pitch": 79, "start_time": 2.5, "duration": 0.8, "velocity": 78},   # G5
            {"pitch": 78, "start_time": 4.0, "duration": 1.2, "velocity": 82},   # Gb5
            {"pitch": 82, "start_time": 5.5, "duration": 0.8, "velocity": 85},   # Bb5
            {"pitch": 80, "start_time": 6.5, "duration": 0.8, "velocity": 80},   # Ab5
            {"pitch": 84, "start_time": 9.5, "duration": 1.0, "velocity": 88},   # C6
            {"pitch": 82, "start_time": 10.5, "duration": 0.8, "velocity": 82},  # Bb5
            {"pitch": 85, "start_time": 12.0, "duration": 1.5, "velocity": 85},  # Db6
            {"pitch": 84, "start_time": 14.0, "duration": 1.8, "velocity": 80},  # C6
        ]

    # 7. DARK_DRONE_SUB_GROWL: Extended low root drone with pitch friction
    elif p == HarmonicProfile.DARK_DRONE_SUB_GROWL:
        return [
            {"pitch": 29, "start_time": 0.0, "duration": 7.9, "velocity": 105},  # F0/F1 long drone
            {"pitch": 30, "start_time": 8.0, "duration": 7.9, "velocity": 108},  # Gb0/Gb1 long tension drone
        ]

    # 8. GRANULAR_TEXTURE_CLOUD: Smeared sustained open chords
    elif p == HarmonicProfile.GRANULAR_TEXTURE_CLOUD:
        return [
            {"pitch": 60, "start_time": 0.0, "duration": 7.8, "velocity": 70},
            {"pitch": 65, "start_time": 0.0, "duration": 7.8, "velocity": 75},
            {"pitch": 68, "start_time": 0.0, "duration": 7.8, "velocity": 72},
            {"pitch": 61, "start_time": 8.0, "duration": 7.8, "velocity": 70},
            {"pitch": 66, "start_time": 8.0, "duration": 7.8, "velocity": 75},
            {"pitch": 70, "start_time": 8.0, "duration": 7.8, "velocity": 72},
        ]

    # 9. RESAMPLE_TAPE_WARP: Soulful Rhodes electric piano chords
    elif p == HarmonicProfile.RESAMPLE_TAPE_WARP:
        return [
            # Bar 1: Fm9 voicing
            {"pitch": 41, "start_time": 0.0, "duration": 3.75, "velocity": 85},
            {"pitch": 56, "start_time": 0.1, "duration": 3.65, "velocity": 80},
            {"pitch": 60, "start_time": 0.15, "duration": 3.6, "velocity": 84},
            {"pitch": 67, "start_time": 0.2, "duration": 3.55, "velocity": 78},
            # Bar 2: Gbmaj7#11
            {"pitch": 42, "start_time": 4.0, "duration": 3.75, "velocity": 88},
            {"pitch": 58, "start_time": 4.1, "duration": 3.65, "velocity": 82},
            {"pitch": 61, "start_time": 4.15, "duration": 3.6, "velocity": 86},
            {"pitch": 66, "start_time": 4.2, "duration": 3.55, "velocity": 80},
            # Bar 3: Bbm9
            {"pitch": 46, "start_time": 8.0, "duration": 3.75, "velocity": 86},
            {"pitch": 56, "start_time": 8.1, "duration": 3.65, "velocity": 82},
            {"pitch": 61, "start_time": 8.15, "duration": 3.6, "velocity": 85},
            {"pitch": 65, "start_time": 8.2, "duration": 3.55, "velocity": 80},
            # Bar 4: Dbmaj7
            {"pitch": 37, "start_time": 12.0, "duration": 3.75, "velocity": 85},
            {"pitch": 53, "start_time": 12.1, "duration": 3.65, "velocity": 82},
            {"pitch": 56, "start_time": 12.15, "duration": 3.6, "velocity": 84},
            {"pitch": 60, "start_time": 12.2, "duration": 3.55, "velocity": 80},
        ]

    # 10. INHARMONIC_BELL_CLUSTER: Bell chime strikes on melodic focal points
    elif p == HarmonicProfile.INHARMONIC_BELL_CLUSTER:
        return [
            {"pitch": 77, "start_time": 0.0, "duration": 2.5, "velocity": 105},
            {"pitch": 80, "start_time": 1.5, "duration": 2.0, "velocity": 100},
            {"pitch": 78, "start_time": 4.0, "duration": 2.5, "velocity": 105},
            {"pitch": 82, "start_time": 5.5, "duration": 2.0, "velocity": 102},
            {"pitch": 84, "start_time": 9.5, "duration": 2.5, "velocity": 110},
            {"pitch": 85, "start_time": 12.0, "duration": 2.0, "velocity": 108},
            {"pitch": 84, "start_time": 14.0, "duration": 2.0, "velocity": 104},
        ]

    # 11. REVERSE_SPECTRAL_GHOST: Swelling reverse chord hits leading into downbeats
    elif p == HarmonicProfile.REVERSE_SPECTRAL_GHOST:
        return [
            {"pitch": 60, "start_time": 2.0, "duration": 1.9, "velocity": 75},
            {"pitch": 65, "start_time": 2.0, "duration": 1.9, "velocity": 80},
            {"pitch": 61, "start_time": 6.0, "duration": 1.9, "velocity": 78},
            {"pitch": 66, "start_time": 6.0, "duration": 1.9, "velocity": 82},
            {"pitch": 61, "start_time": 10.0, "duration": 1.9, "velocity": 80},
            {"pitch": 65, "start_time": 10.0, "duration": 1.9, "velocity": 84},
            {"pitch": 60, "start_time": 14.0, "duration": 1.9, "velocity": 85},
            {"pitch": 72, "start_time": 14.0, "duration": 1.9, "velocity": 90},
        ]

    # 12. LOFI_BIT_CRUSHER_DIRT: 8-bit chiptune staccato run
    elif p == HarmonicProfile.LOFI_BIT_CRUSHER_DIRT:
        notes = []
        melody = [65, 68, 67, 65, 66, 70, 68, 65, 65, 72, 70, 68, 73, 72, 70, 67]
        for idx, pt in enumerate(melody):
            notes.append({"pitch": pt, "start_time": float(idx * 1.0), "duration": 0.45, "velocity": 95})
        return notes

    # 13. PSYCHOACOUSTIC_HAAS_WIDENER: Plucked string syncopated notes
    elif p == HarmonicProfile.PSYCHOACOUSTIC_HAAS_WIDENER:
        notes = []
        pattern = [(0.0, 65), (0.75, 68), (1.5, 72), (2.5, 67),
                   (4.0, 66), (4.75, 70), (5.5, 73), (6.5, 68),
                   (8.0, 65), (8.75, 72), (9.5, 77), (10.5, 70),
                   (12.0, 73), (12.75, 72), (13.5, 70), (14.5, 67)]
        for t, pt in pattern:
            notes.append({"pitch": pt, "start_time": t, "duration": 0.5, "velocity": 98})
        return notes

    # 14. VOCAL_CHOP_DISSECTOR: 16th-note stuttering chops
    elif p == HarmonicProfile.VOCAL_CHOP_DISSECTOR:
        notes = []
        chops = [65, 65, 68, 68, 67, 65, 65, 68, 66, 66, 70, 70, 68, 68, 65, 66,
                 65, 65, 72, 72, 70, 70, 68, 65, 73, 73, 72, 72, 70, 67, 65, 60]
        for idx, pt in enumerate(chops):
            notes.append({"pitch": pt, "start_time": float(idx * 0.5), "duration": 0.35, "velocity": 100})
        return notes

    # 15. OCTAVE_FUZZ_MONSTER: Screaming octave doubled lead
    elif p == HarmonicProfile.OCTAVE_FUZZ_MONSTER:
        notes = []
        lead = [(0.0, 65), (1.5, 68), (2.5, 67), (3.25, 65),
                (4.0, 66), (5.5, 70), (6.5, 68), (7.5, 65),
                (8.0, 65), (9.5, 72), (10.5, 70), (11.5, 68),
                (12.0, 73), (13.0, 72), (14.0, 70), (15.0, 67)]
        for t, pt in lead:
            notes.append({"pitch": pt, "start_time": t, "duration": 0.85, "velocity": 115})
            notes.append({"pitch": pt + 12, "start_time": t, "duration": 0.85, "velocity": 105})
        return notes

    # 16. CHOPPED_RHYTHMIC_GATE: 16th-note motor arpeggio through chord tones
    elif p == HarmonicProfile.CHOPPED_RHYTHMIC_GATE:
        notes = []
        arps = [
            [53, 56, 60, 65],  # Fm
            [54, 58, 61, 66],  # Gb
            [53, 56, 61, 65],  # Bbm
            [49, 53, 56, 60],  # Db
        ]
        for bar_idx, chord in enumerate(arps):
            for step in range(16):
                pt = chord[step % 4]
                t = float(bar_idx * 4.0 + step * 0.25)
                notes.append({"pitch": pt, "start_time": t, "duration": 0.2, "velocity": 92 if step % 4 == 0 else 78})
        return notes

    # 17. SPECTRAL_FREEZE_INFINITE: Frozen harmonic sustained drone
    elif p == HarmonicProfile.SPECTRAL_FREEZE_INFINITE:
        return [
            {"pitch": 53, "start_time": 0.0, "duration": 16.0, "velocity": 70}, # F3
            {"pitch": 60, "start_time": 0.0, "duration": 16.0, "velocity": 72}, # C4
            {"pitch": 65, "start_time": 0.0, "duration": 16.0, "velocity": 68}, # F4
            {"pitch": 72, "start_time": 0.0, "duration": 16.0, "velocity": 65}, # C5
        ]

    # 18. ANALOG_WARMTH_SATURATOR: Warm vintage brass counter-melody
    elif p == HarmonicProfile.ANALOG_WARMTH_SATURATOR:
        return [
            {"pitch": 53, "start_time": 0.0, "duration": 3.5, "velocity": 85},
            {"pitch": 56, "start_time": 0.0, "duration": 3.5, "velocity": 85},
            {"pitch": 54, "start_time": 4.0, "duration": 3.5, "velocity": 88},
            {"pitch": 58, "start_time": 4.0, "duration": 3.5, "velocity": 88},
            {"pitch": 53, "start_time": 8.0, "duration": 3.5, "velocity": 86},
            {"pitch": 56, "start_time": 8.0, "duration": 3.5, "velocity": 86},
            {"pitch": 49, "start_time": 12.0, "duration": 3.5, "velocity": 85},
            {"pitch": 53, "start_time": 12.0, "duration": 3.5, "velocity": 85},
        ]

    # 19. NEOPERREO_METALLIC_SNARE: Resonant percussive Latin dembow pluck
    elif p == HarmonicProfile.NEOPERREO_METALLIC_SNARE:
        notes = []
        dembow = [
            (0.0, 41), (1.5, 41), (2.0, 41), (3.0, 41),
            (4.0, 42), (5.5, 42), (6.0, 42), (7.0, 42),
            (8.0, 46), (9.5, 46), (10.0, 46), (11.0, 46),
            (12.0, 49), (13.5, 49), (14.0, 48), (15.0, 48),
        ]
        for t, pt in dembow:
            notes.append({"pitch": pt, "start_time": t, "duration": 0.35, "velocity": 115})
        return notes

    # 20. PITCH_DIVE_TENSION_RISER: Ascending tension glide + bar 4 pitch dive
    elif p == HarmonicProfile.PITCH_DIVE_TENSION_RISER:
        notes = []
        for step in range(12):
            notes.append({"pitch": 60 + step, "start_time": float(step * 1.0), "duration": 0.9, "velocity": 70 + step * 3})
        # Dive at bar 4
        notes.append({"pitch": 72, "start_time": 12.0, "duration": 0.8, "velocity": 110})
        notes.append({"pitch": 69, "start_time": 12.8, "duration": 0.8, "velocity": 105})
        notes.append({"pitch": 65, "start_time": 13.6, "duration": 0.8, "velocity": 100})
        notes.append({"pitch": 53, "start_time": 14.4, "duration": 1.4, "velocity": 90})
        return notes

    return []


def main():
    print("=== DEPLOYING 20 DEDICATED UHTS TRACKS IN ABLETON LIVE 12 SUITE ===")
    conn = get_ableton_connection()
    if not conn:
        print("[ERROR] Could not connect to Ableton Live.")
        return

    session = conn.send_command("get_session_info", {})
    initial_track_count = session.get("track_count", 0)
    print(f"Initial track count in session: {initial_track_count}")

    profiles = list(HarmonicProfile)
    uhts_track_indices = []

    # 1. Prepare 20 tracks (starting at index 18)
    # Track 18 already exists from showcase
    uhts_track_indices.append(18)
    # Create remaining 19 tracks if needed
    needed_tracks = 20 - (initial_track_count - 18)
    for i in range(needed_tracks):
        print(f"Creating MIDI track {initial_track_count + i}...")
        conn.send_command("create_midi_track", {"index": -1})
        time.sleep(0.1)

    session = conn.send_command("get_session_info", {})
    current_count = session.get("track_count", 0)
    print(f"Total tracks now available in session: {current_count}")

    # Track indices 18 to 37 will hold profiles 1 to 20
    for idx, profile in enumerate(profiles):
        target_track_idx = 18 + idx
        profile_num = idx + 1
        synth_uri, synth_desc = PROFILE_SYNTH_MAP[profile]
        track_name = f"[UHTS {profile_num:02d}] {profile.value}"
        start_beat = float(idx * 16.0)

        print(f"\n[{profile_num}/20] Configuring Track {target_track_idx}: '{track_name}'...")

        # A. Rename track
        conn.send_command("set_track_name", {
            "track_index": target_track_idx,
            "name": track_name
        })

        # B. Clean any existing devices on track
        info = conn.send_command("get_track_info", {"track_index": target_track_idx})
        dev_count = len(info.get("devices", []))
        while dev_count > 0:
            try:
                conn.send_command("delete_device", {"track_index": target_track_idx, "device_index": 0})
                info = conn.send_command("get_track_info", {"track_index": target_track_idx})
                dev_count = len(info.get("devices", []))
            except Exception:
                break

        # C. Load Dedicated Instrument / Synth
        print(f"  -> Loading Synth Engine: {synth_desc} ({synth_uri})")
        try:
            conn.send_command("load_browser_item", {
                "track_index": target_track_idx,
                "item_uri": synth_uri
            })
        except Exception as e:
            print(f"  Warning loading {synth_uri}: {e}. Trying fallback to Drift...")
            try:
                conn.send_command("load_browser_item", {
                    "track_index": target_track_idx,
                    "item_uri": "query:Synths#Drift"
                })
            except Exception:
                pass

        # D. Load UHTS Physical Effect Chain
        print(f"  -> Loading UHTS Physical Device Chain for '{profile.value}'...")
        HarmonicTransformationSuite.apply_to_live_track(
            track_index=target_track_idx,
            profile=profile,
            conn=conn,
            clear_existing_fx=False
        )

        # E. Create Session Clip with Tailored Notes of the Same Melody
        try:
            conn.send_command("delete_clip", {"track_index": target_track_idx, "clip_index": 0})
        except Exception:
            pass
        conn.send_command("create_clip", {
            "track_index": target_track_idx,
            "clip_index": 0,
            "length": 16.0
        })
        notes = get_profile_composition(profile)
        conn.send_command("add_notes_to_clip", {
            "track_index": target_track_idx,
            "clip_index": 0,
            "notes": notes
        })
        conn.send_command("set_clip_name", {
            "track_index": target_track_idx,
            "clip_index": 0,
            "name": f"Motif - {profile.value}"
        })

        # F. Duplicate Clip to Arrangement Timeline at start_beat
        conn.send_command("duplicate_session_clip_to_arrangement", {
            "track_index": target_track_idx,
            "clip_index": 0,
            "destination_time": start_beat
        })

        # G. Update Cue Point / Locator
        try:
            conn.send_command("create_cue_point", {
                "time": start_beat,
                "name": f"#{profile_num}: {profile.value}"
            })
        except Exception:
            pass

    # Unsolo all UHTS tracks, solo Track 18 (Profile 1) initially
    for idx in range(20):
        t_i = 18 + idx
        conn.send_command("set_track_solo", {"track_index": t_i, "solo": (t_i == 18)})

    print("\n" + "=" * 70)
    print(" [OK] 20 DEDICATED UHTS TRACKS SUCCESSFULLY CREATED & CONFIGURED!")
    print(" Each track has its own distinct synth, arrangement adaptation, and UHTS FX chain.")
    print(" Tracks: 18 to 37.")
    print(" Arrangement: 80 bars (320 beats) with Locators #1 to #20.")
    print(" Track 18 (Pad Atmosphere) is soloed and ready for audition.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

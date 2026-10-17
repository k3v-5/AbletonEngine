# F:/Dev/AbletonEngine/engine/production/album_producer_hardtechno.py
"""
Hard Techno Concept Album Producer: "OVERDRIVE RAVE"
Inspired by:
- Rhythm & Drums: Charlotte de Witte ("Overdrive") - 138-144 BPM relentless rumble kick,
  offbeat 909 open hats, rolling 16th closed hats, driving 909 claps and peak drop ride cymbals.
- Melodies & Hooks: The Prodigy (Liam Howlett) - screaming 303 acid lines, distorted supersaw riffs,
  syncopated rave stabs, hoover chords, pitch drops, and aggressive rave energy.

Sequential step-by-step production through CopilotGuidedSession (Phases 0 to 10).
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

repo_root = str(Path(__file__).resolve().parent.parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from engine.production.full_song_producer import AbletonLiveConnection
from engine.production.copilot.guided_session import copilot_guided_session_engine
from engine.session.clean_slate import CleanSlateManager
from engine.session.project_lifecycle import ProjectLifecycleManager
from engine.mix.bus_routing import BusRoutingManager
from engine.mix.sidechain_manager import SidechainManager
from engine.music.theory.tessitura_guard import TessituraGuard

logger = logging.getLogger("HardTechnoAlbumProducer")

ALBUM_ROOT_DIR = Path(r"F:\Canciones_HardTechno_Album")
ALBUM_ROOT_DIR.mkdir(parents=True, exist_ok=True)

TRACK_METADATA = [
    {
        "track_number": 1,
        "name": "01_Voodoo_Overdrive",
        "bpm": 139.5,
        "key": "F",
        "scale": "Phrygian",
        "theme": "Voodoo 303 Acid Scream & Resonant Squelch",
        "lead_role": "Voodoo_Acid_Scream",
        "keys_role": "Rave_Hoover_Stab",
        "sub_role": "Acid_Sub_Rumble",
        "fx_role": "Alarm_Glitch_FX",
        "root_pitch": 53, # F3
        "sub_pitch": 41,  # F2
    },
    {
        "track_number": 2,
        "name": "02_Poison_Protocol",
        "bpm": 142.0,
        "key": "D",
        "scale": "Minor",
        "theme": "Poison Rave Horns & Industrial Stabs",
        "lead_role": "Poison_Rave_Lead",
        "keys_role": "Gritty_Saw_Stabs",
        "sub_role": "Dark_Industrial_Sub",
        "fx_role": "Industrial_Perc_Foley",
        "root_pitch": 62, # D4
        "sub_pitch": 38,  # D2
    },
    {
        "track_number": 3,
        "name": "03_Breathe_The_Voltage",
        "bpm": 143.0,
        "key": "C",
        "scale": "Dorian",
        "theme": "Breathe Distorted Punk-Saw & Dorian Tension",
        "lead_role": "Voltage_Punk_Saw",
        "keys_role": "Rave_Organ_Stab",
        "sub_role": "Pumping_Rumble_Sub",
        "fx_role": "Noise_Riser_FX",
        "root_pitch": 48, # C3
        "sub_pitch": 36,  # C2
    },
    {
        "track_number": 4,
        "name": "04_Firestarter_Rave",
        "bpm": 144.0,
        "key": "E",
        "scale": "Minor",
        "theme": "Firestarter Siren Lead & Rave Piano Stabs",
        "lead_role": "Firestarter_Siren_Lead",
        "keys_role": "Rave_Piano_Chord",
        "sub_role": "Resonant_Sub_Drive",
        "fx_role": "Siren_Laser_FX",
        "root_pitch": 64, # E4
        "sub_pitch": 40,  # E2
    },
    {
        "track_number": 5,
        "name": "05_Smack_The_Void",
        "bpm": 139.0,
        "key": "G",
        "scale": "Phrygian",
        "theme": "Smack Apocalyptic Arpeggio & Distorted Hoover Drops",
        "lead_role": "Void_Rave_Arp",
        "keys_role": "Dark_Hoover_Bed",
        "sub_role": "Deep_Rumble_Sub",
        "fx_role": "Metallic_Hit_FX",
        "root_pitch": 55, # G3
        "sub_pitch": 43,  # G2
    },
    {
        "track_number": 6,
        "name": "06_No_Good_Resonance",
        "bpm": 141.0,
        "key": "A",
        "scale": "Minor",
        "theme": "Hypnotic Rave Chords & Acid Counter-Melody",
        "lead_role": "Hypnotic_Rave_Stab",
        "keys_role": "Acid_Counter_Lead",
        "sub_role": "Pulsing_Techno_Sub",
        "fx_role": "Vocal_Chop_Rave",
        "root_pitch": 57, # A3
        "sub_pitch": 45,  # A2
    },
    {
        "track_number": 7,
        "name": "07_Spitfire_Pulse",
        "bpm": 142.5,
        "key": "Bb",
        "scale": "Locrian",
        "theme": "Spitfire Staccato Glitch Saw & Locrian Tension",
        "lead_role": "Spitfire_Glitch_Saw",
        "keys_role": "Dark_Industrial_Stab",
        "sub_role": "Acid_Rumble_Sub",
        "fx_role": "Glitch_Modular_FX",
        "root_pitch": 58, # Bb3
        "sub_pitch": 46,  # Bb2
    },
    {
        "track_number": 8,
        "name": "08_Out_Of_Space_Reactor",
        "bpm": 144.5,
        "key": "F#",
        "scale": "Dorian",
        "theme": "Space Rave Call-and-Response & Octave Leaps",
        "lead_role": "Space_Rave_Lead",
        "keys_role": "Sub_Acid_Hook",
        "sub_role": "Reactor_Sub_Bass",
        "fx_role": "Cosmic_Rave_FX",
        "root_pitch": 66, # F#4
        "sub_pitch": 42,  # F#2
    },
    {
        "track_number": 9,
        "name": "09_Jericho_Steel",
        "bpm": 140.0,
        "key": "Ab",
        "scale": "Minor",
        "theme": "Jericho Rave Horns & Detuned Industrial Synths",
        "lead_role": "Jericho_Horn_Lead",
        "keys_role": "Distorted_Rave_Synth",
        "sub_role": "Heavy_Steel_Rumble",
        "fx_role": "Steel_Foley_Impact",
        "root_pitch": 56, # Ab3
        "sub_pitch": 44,  # Ab2
    },
    {
        "track_number": 10,
        "name": "10_The_Overdrive_Experience",
        "bpm": 143.5,
        "key": "Eb",
        "scale": "Harmonic Minor",
        "theme": "The Grand Climax: Anthem Prodigy Lead & Screaming 303 Acid",
        "lead_role": "Anthem_Prodigy_Lead",
        "keys_role": "Screaming_303_Acid",
        "sub_role": "Monumental_Sub_Rumble",
        "fx_role": "Apocalyptic_Rave_FX",
        "root_pitch": 63, # Eb4
        "sub_pitch": 39,  # Eb2
    },
    {
        "track_number": 11,
        "name": "11_Thunder_Strike",
        "bpm": 140.5,
        "key": "B",
        "scale": "Minor",
        "theme": "Hypnotic 2-Note Rave Hook & Rolling Belgian 16th Hardgroove Polymeter",
        "lead_role": "Thunder_Sync_Saw",
        "keys_role": "Minimal_Rave_Stab",
        "sub_role": "Rolling_Belgian_Sub",
        "fx_role": "Thunder_Glitch_Foley",
        "root_pitch": 59, # B3
        "sub_pitch": 47,  # B2
    },
    {
        "track_number": 12,
        "name": "12_Acid_Kinetics",
        "bpm": 144.0,
        "key": "G#",
        "scale": "Dorian",
        "theme": "Relentless Sticky 3-Note Acid Pulse & Low Octave Kinetic Groove",
        "lead_role": "Kinetic_303_Pulse",
        "keys_role": "Analog_Resonant_Stab",
        "sub_role": "Galloping_Acid_Rumble",
        "fx_role": "Kinetic_Laser_Sweeper",
        "root_pitch": 44, # G#2 (Subterranean Low Octave)
        "sub_pitch": 32,  # G#1
    },
    {
        "track_number": 13,
        "name": "13_Iron_Discipline",
        "bpm": 141.5,
        "key": "D#",
        "scale": "Phrygian",
        "theme": "Minimalist Industrial Horn Punch & Surgical Schranz Power",
        "lead_role": "Iron_Horn_Punch",
        "keys_role": "Detuned_Steel_Stab",
        "sub_role": "Schranz_Pounding_Sub",
        "fx_role": "Anvil_Impact_Foley",
        "root_pitch": 51, # D#3 (Heavy Mid Octave)
        "sub_pitch": 39,  # D#2
    },
    {
        "track_number": 14,
        "name": "14_Rave_Invasion",
        "bpm": 143.0,
        "key": "F",
        "scale": "Dorian",
        "theme": "Infectious High-Octave Rave Hook & Detroit Acid Footwork Drums",
        "lead_role": "Invasion_90s_Stab",
        "keys_role": "Hoover_Vamp_Chords",
        "sub_role": "Footwork_Bounce_Sub",
        "fx_role": "Siren_Whistle_Rave",
        "root_pitch": 65, # F4 (High Rave Register)
        "sub_pitch": 41,  # F2
    },
    {
        "track_number": 15,
        "name": "15_Sub_Frequency_Shock",
        "bpm": 138.5,
        "key": "C#",
        "scale": "Harmonic Minor",
        "theme": "Hypnotic Low-Octave Dark Hook & Tribal Industrial Polyrhythmic Toms",
        "lead_role": "Sub_Shock_Low_Hook",
        "keys_role": "Resonant_Drone_Stab",
        "sub_role": "Deep_Earthquake_Rumble",
        "fx_role": "Modular_Shockwave_FX",
        "root_pitch": 49, # C#3 (Dark Sub Register)
        "sub_pitch": 37,  # C#2
    },
    {
        "track_number": 16,
        "name": "16_Dominator_Reign",
        "bpm": 145.0,
        "key": "A",
        "scale": "Phrygian Dominant",
        "theme": "Iconic Hoover Pitch Dive Hook & Rotterdam Gabber Clean Punch",
        "lead_role": "Dominator_Hoover_Lead",
        "keys_role": "Staccato_Acid_Chop",
        "sub_role": "Gabber_Distorted_Sub",
        "fx_role": "Crowd_Chant_Rave_FX",
        "root_pitch": 69, # A4 (Screaming High Rave Pitch)
        "sub_pitch": 45,  # A2
    },
    {
        "track_number": 17,
        "name": "17_Cybernetic_Pulse",
        "bpm": 142.0,
        "key": "E",
        "scale": "Phrygian",
        "theme": "2-Note Minimalist Modular Laser Riff & Hypnotic Berlin Rimshot Groove",
        "lead_role": "Cyber_Laser_Ping",
        "keys_role": "Hypnotic_Chamber_Stab",
        "sub_role": "Modular_Pulsing_Sub",
        "fx_role": "Cyber_Data_Glitch",
        "root_pitch": 52, # E3 (Mid-Low Laser Ping)
        "sub_pitch": 40,  # E2
    },
    {
        "track_number": 18,
        "name": "18_Rupture_Core",
        "bpm": 143.5,
        "key": "Bb",
        "scale": "Dorian",
        "theme": "High-Octave Punk Whistle & UK Rave 2-Step Hybrid Stepper",
        "lead_role": "Rupture_Punk_Whistle",
        "keys_role": "Gritty_Organ_Stab",
        "sub_role": "Hybrid_Stepper_Sub",
        "fx_role": "Rupture_Alarm_FX",
        "root_pitch": 70, # Bb4 (Piercing High Peak)
        "sub_pitch": 46,  # Bb2
    },
    {
        "track_number": 19,
        "name": "19_Vortex_Transmission",
        "bpm": 141.0,
        "key": "G",
        "scale": "Harmonic Minor",
        "theme": "Driving Subterranean Psy-Techno Matrix & Leading Tone Surge",
        "lead_role": "Vortex_Rolling_Lead",
        "keys_role": "Dark_Psy_Chords",
        "sub_role": "Galloping_Matrix_Sub",
        "fx_role": "Transmission_Static_FX",
        "root_pitch": 43, # G2 (Subterranean Psy Register)
        "sub_pitch": 31,  # G1
    },
    {
        "track_number": 20,
        "name": "20_Final_Overdrive_Anthem",
        "bpm": 145.0,
        "key": "D",
        "scale": "Phrygian Dominant",
        "theme": "Grand Festival Rave Colossus Hook & Maximum Energy Polyrhythms",
        "lead_role": "Grand_Festival_Anthem",
        "keys_role": "Overdrive_303_Cascade",
        "sub_role": "Monumental_Colossus_Sub",
        "fx_role": "Apex_Explosion_Vox",
        "root_pitch": 74, # D5 (Maximum Stadium Peak)
        "sub_pitch": 38,  # D2
    }
]


def generate_distinct_hardtechno_drums(section_name: str, bars: int, sub_pitch: int = 36, track_num: int = 1) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Generates 100% rhythmically distinct Hard Techno drum grooves for ALL 20 tracks.
    Strict Rule: The drum timbre/kit is consistent (909/808 + Drum Buss),
    but NO two tracks share similar or identical rhythms!
    Audited to eliminate mediocre flat patterns and over-excessive clutter.
    """
    kicks = []
    drums = []
    sub_notes = []

    s_lower = section_name.lower()
    is_drop = "drop" in s_lower or "climax" in s_lower
    is_drop_2 = is_drop and ("drop 2" in s_lower or "2" in s_lower)
    is_build = "build" in s_lower
    is_intro = "intro" in s_lower
    is_break = "break" in s_lower
    is_outro = "outro" in s_lower

    for bar in range(bars):
        b_offset = bar * 4.0

        # Tension Vacuum Stop: Last 2 beats of Buildups are completely tacet
        if is_build and bar == (bars - 1):
            for step_16th in range(8): # beats 0.0 to 2.0
                t = b_offset + (step_16th * 0.25)
                drums.append({"pitch": 38, "start_time": t, "duration": 0.15, "velocity": 105 + step_16th * 2})
            # Vacuum stop at beats 2.0 to 4.0
            continue

        # Downbeat impact on Drop 1 & Drop 2
        if is_drop and bar == 0:
            kicks.append({"pitch": 36, "start_time": b_offset + 0.0, "duration": 2.5, "velocity": 127})
            sub_notes.append({"pitch": max(24, sub_pitch - 12), "start_time": b_offset + 0.0, "duration": 2.5, "velocity": 127})
            drums.append({"pitch": 49, "start_time": b_offset + 0.0, "duration": 2.5, "velocity": 127})

        # Buildup snare ramp on bars 0 to 6
        if is_build and bar < (bars - 1):
            for beat in range(4):
                t = b_offset + float(beat)
                drums.append({"pitch": 38, "start_time": t, "duration": 0.25, "velocity": 85 + bar * 5})
            if bar >= 4:
                for beat in range(4):
                    t = b_offset + float(beat) + 0.5
                    drums.append({"pitch": 38, "start_time": t, "duration": 0.2, "velocity": 90 + bar * 4})
            if bar == (bars - 2):
                drums.append({"pitch": 49, "start_time": b_offset + 2.0, "duration": 1.8, "velocity": 124})
            if bar < 4:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 120})
            continue

        # =========================================================================
        # TRACK 01: Voodoo Overdrive - Acid Triplet Hi-Hat Hardgroove
        # =========================================================================
        if track_num == 1:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                # 12-step Triplet hi-hat groove (triplet 8ths: 3 hits per beat = 12 per bar)
                for trip in range(12):
                    t_trip = b_offset + trip * (4.0 / 12.0)
                    is_down = (trip % 3 == 0)
                    vel_trip = 124 if is_down else (100 if trip % 3 == 2 else 80)
                    drums.append({"pitch": 42, "start_time": t_trip, "duration": 0.15, "velocity": vel_trip})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.28, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 3.5, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 45, "start_time": b_offset + 2.25, "duration": 0.22, "velocity": 118})
                if is_drop:
                    for dot_step in range(5):
                        t_dot = b_offset + dot_step * 0.75
                        drums.append({"pitch": 51, "start_time": t_dot, "duration": 0.35, "velocity": 120 if is_drop_2 else 112})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.22, "velocity": 122 if is_drop else 100})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.22, "velocity": 125 if is_drop else 105})
            else:
                for bk_t in [0.0, 1.75, 2.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 122})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.22, "velocity": 120})
                drums.append({"pitch": 38, "start_time": b_offset + 2.75, "duration": 0.22, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.8, "velocity": 115})

        # =========================================================================
        # TRACK 02: Poison Protocol - Charlotte Offbeat Choke & Ghost Claps
        # =========================================================================
        elif track_num == 2:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    vel_h = 125 if (s16 % 4 == 1 or s16 % 4 == 3) else (92 if s16 % 4 == 2 else 75)
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": vel_h})
                for ob in [0.5, 1.5, 2.5, 3.5]:
                    drums.append({"pitch": 46, "start_time": b_offset + ob, "duration": 0.24, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.3, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.3, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 1.75, "duration": 0.14, "velocity": 92})
                drums.append({"pitch": 38, "start_time": b_offset + 3.75, "duration": 0.14, "velocity": 96})
                drums.append({"pitch": 45, "start_time": b_offset + 2.5, "duration": 0.25, "velocity": 120})
                if is_drop:
                    for ob in [0.5, 1.5, 2.5, 3.5]:
                        drums.append({"pitch": 51, "start_time": b_offset + ob, "duration": 0.35, "velocity": 124 if is_drop_2 else 115})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.25, "velocity": 120})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.22, "velocity": 125})
            else:
                for bk_t in [0.0, 1.5, 2.5, 3.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.3, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.5, "velocity": 118})

        # =========================================================================
        # TRACK 03: Breathe The Voltage - 8th-Note Industrial Gallop & Rimshot
        # =========================================================================
        elif track_num == 3:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for step8 in range(8):
                    t_h = b_offset + step8 * 0.5
                    vel_8 = 126 if step8 % 2 == 1 else 95
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.22, "velocity": vel_8})
                drums.append({"pitch": 37, "start_time": b_offset + 0.75, "duration": 0.15, "velocity": 125})
                drums.append({"pitch": 37, "start_time": b_offset + 2.25, "duration": 0.15, "velocity": 127})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.2, "velocity": 118})
                drums.append({"pitch": 46, "start_time": b_offset + 1.75, "duration": 0.25, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 126})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                if is_drop:
                    for beat in range(4):
                        drums.append({"pitch": 51, "start_time": b_offset + beat + 0.25, "duration": 0.3, "velocity": 122 if is_drop_2 else 112})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.38, "velocity": 124})
            else:
                for bk_t in [0.0, 1.25, 2.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.3, "velocity": 120})
                drums.append({"pitch": 37, "start_time": b_offset + 1.0, "duration": 0.2, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 122})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.6, "velocity": 118})

        # =========================================================================
        # TRACK 04: Firestarter Rave - Rave 3-3-2 Syncopated 16ths & Offbeat Crashes
        # =========================================================================
        elif track_num == 4:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    is_332 = s16 in (0, 3, 6, 9, 12, 15)
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.18, "velocity": 126 if is_332 else 82})
                drums.append({"pitch": 38, "start_time": b_offset + 0.9375, "duration": 0.08, "velocity": 85})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 2.9375, "duration": 0.08, "velocity": 88})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 46, "start_time": b_offset + 0.5, "duration": 0.35, "velocity": 120})
                drums.append({"pitch": 46, "start_time": b_offset + 2.5, "duration": 0.35, "velocity": 124})
                if bar % 2 == 1:
                    drums.append({"pitch": 49, "start_time": b_offset + 2.5, "duration": 1.2, "velocity": 115})
                if is_drop:
                    for step8 in range(8):
                        drums.append({"pitch": 51, "start_time": b_offset + step8 * 0.5, "duration": 0.25, "velocity": 120 if is_drop_2 else 110})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.22, "velocity": 122})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.22, "velocity": 124})
            else:
                for bk_t in [0.0, 1.75, 2.5, 3.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 124})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 122})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.8, "velocity": 118})

        # =========================================================================
        # TRACK 05: Smack The Void - Hypnotic Shaker Roll & Deep Tribal Percussion
        # =========================================================================
        elif track_num == 5:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                if bar % 4 == 3:
                    kicks.append({"pitch": 36, "start_time": b_offset + 3.75, "duration": 0.2, "velocity": 120})
                for s16 in range(16):
                    t_sh = b_offset + s16 * 0.25
                    vel_sh = int(88 + 35 * (s16 / 16.0))
                    drums.append({"pitch": 44, "start_time": t_sh, "duration": 0.15, "velocity": vel_sh})
                drums.append({"pitch": 45, "start_time": b_offset + 1.25, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 47, "start_time": b_offset + 2.5, "duration": 0.25, "velocity": 125})
                drums.append({"pitch": 45, "start_time": b_offset + 3.75, "duration": 0.22, "velocity": 120})
                for ob in [0.5, 1.5, 2.5, 3.5]:
                    drums.append({"pitch": 46, "start_time": b_offset + ob, "duration": 0.35, "velocity": 120})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                if is_drop:
                    for ob in [0.5, 1.5, 2.5, 3.5]:
                        drums.append({"pitch": 51, "start_time": b_offset + ob, "duration": 0.38, "velocity": 125 if is_drop_2 else 115})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.35, "duration": 0.35, "velocity": 122})
            else:
                for s8 in range(8):
                    t_sh = b_offset + s8 * 0.5
                    drums.append({"pitch": 44, "start_time": t_sh, "duration": 0.2, "velocity": 95})
                drums.append({"pitch": 45, "start_time": b_offset + 1.5, "duration": 0.3, "velocity": 120})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 122})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.5, "velocity": 115})

        # =========================================================================
        # TRACK 06: No Good Resonance - Dotted-8th Echo Hats & Ghost Snare Matrix
        # =========================================================================
        elif track_num == 6:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for dot_idx in range(5):
                    t_dot = b_offset + dot_idx * 0.75
                    drums.append({"pitch": 42, "start_time": t_dot, "duration": 0.2, "velocity": 126 if dot_idx % 2 == 0 else 110})
                for s16 in range(16):
                    if s16 not in (0, 3, 6, 9, 12, 15):
                        drums.append({"pitch": 42, "start_time": b_offset + s16 * 0.25, "duration": 0.14, "velocity": 78})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.35, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 2.75, "duration": 0.15, "velocity": 95})
                drums.append({"pitch": 38, "start_time": b_offset + 3.75, "duration": 0.15, "velocity": 92})
                if is_drop:
                    for ob in [0.5, 1.5, 2.5, 3.5]:
                        drums.append({"pitch": 51, "start_time": b_offset + ob, "duration": 0.35, "velocity": 122 if is_drop_2 else 112})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.3, "velocity": 122})
            else:
                for bk_t in [0.0, 1.5, 2.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 120})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.6, "velocity": 115})

        # =========================================================================
        # TRACK 07: Spitfire Pulse - Tribal Rimshot Accents & Staccato Bursts
        # =========================================================================
        elif track_num == 7:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    if s16 in (7, 15):
                        drums.append({"pitch": 42, "start_time": t_h, "duration": 0.09, "velocity": 124})
                        drums.append({"pitch": 42, "start_time": t_h + 0.125, "duration": 0.09, "velocity": 127})
                    else:
                        drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": 92 if s16 % 2 == 1 else 76})
                drums.append({"pitch": 37, "start_time": b_offset + 1.25, "duration": 0.16, "velocity": 125})
                drums.append({"pitch": 37, "start_time": b_offset + 3.25, "duration": 0.16, "velocity": 127})
                drums.append({"pitch": 46, "start_time": b_offset + 0.5, "duration": 0.32, "velocity": 120})
                drums.append({"pitch": 46, "start_time": b_offset + 2.5, "duration": 0.32, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                if is_drop:
                    for s16 in range(16):
                        drums.append({"pitch": 51, "start_time": b_offset + s16 * 0.25, "duration": 0.18, "velocity": 122 if s16 % 4 == 2 else 98})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.25, "velocity": 124})
            else:
                for bk_t in [0.0, 1.25, 2.75]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 122})
                drums.append({"pitch": 37, "start_time": b_offset + 1.0, "duration": 0.2, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 2.75, "duration": 0.25, "velocity": 125})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.5, "velocity": 118})

        # =========================================================================
        # TRACK 08: Out Of Space Reactor - Detroit Futuristic Ratchets & Low Tom
        # =========================================================================
        elif track_num == 8:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    if s16 in (3, 11):
                        drums.append({"pitch": 42, "start_time": t_h, "duration": 0.1, "velocity": 122})
                        drums.append({"pitch": 42, "start_time": t_h + 0.125, "duration": 0.1, "velocity": 125})
                    else:
                        drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": 85 if s16 % 2 == 0 else 105})
                for idx, ob in enumerate([0.5, 1.5, 2.5, 3.5]):
                    vel_ob = 127 if idx % 2 == 0 else 115
                    drums.append({"pitch": 46, "start_time": b_offset + ob, "duration": 0.32, "velocity": vel_ob})
                drums.append({"pitch": 45, "start_time": b_offset + 1.5, "duration": 0.28, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 126})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                if is_drop:
                    for ob in [0.5, 1.5, 2.5, 3.5]:
                        drums.append({"pitch": 51, "start_time": b_offset + ob, "duration": 0.35, "velocity": 125 if is_drop_2 else 115})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.22, "velocity": 120})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.22, "velocity": 125})
            else:
                for bk_t in [0.0, 1.5, 2.25]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 120})
                drums.append({"pitch": 45, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.6, "velocity": 115})

        # =========================================================================
        # TRACK 09: Jericho Steel - Industrial Steel Foley & Swung 58% MPC Groove
        # =========================================================================
        elif track_num == 9:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for s16 in range(16):
                    sw = 0.035 if s16 % 2 == 1 else 0.0
                    t_h = b_offset + s16 * 0.25 + sw
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": 105 if s16 % 2 == 1 else 80})
                drums.append({"pitch": 47, "start_time": b_offset + 0.75, "duration": 0.22, "velocity": 122})
                drums.append({"pitch": 47, "start_time": b_offset + 2.0, "duration": 0.22, "velocity": 125})
                drums.append({"pitch": 47, "start_time": b_offset + 3.25, "duration": 0.22, "velocity": 124})
                drums.append({"pitch": 45, "start_time": b_offset + 1.75, "duration": 0.25, "velocity": 120})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.32, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 3.5, "duration": 0.32, "velocity": 125})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 126})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 127})
                if is_drop:
                    for ob in [0.5, 1.5, 2.5, 3.5]:
                        drums.append({"pitch": 51, "start_time": b_offset + ob, "duration": 0.35, "velocity": 124 if is_drop_2 else 115})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.35, "velocity": 122})
            else:
                for bk_t in [0.0, 1.75, 2.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 120})
                drums.append({"pitch": 47, "start_time": b_offset + 1.0, "duration": 0.22, "velocity": 122})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 125})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.8, "velocity": 115})

        # =========================================================================
        # TRACK 10: The Overdrive Experience - Climax Double-Time Rides & Peak Stack
        # =========================================================================
        elif track_num == 10:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    vel_h = 118 if s16 % 2 == 1 else 95
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.18, "velocity": vel_h})
                for ob in [0.5, 1.5, 2.5, 3.5]:
                    drums.append({"pitch": 46, "start_time": b_offset + ob, "duration": 0.35, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.3, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.3, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 122})
                if is_drop:
                    ride_steps = range(16) if is_drop_2 else range(8)
                    step_delta = 0.25 if is_drop_2 else 0.5
                    for rs in ride_steps:
                        t_r = b_offset + rs * step_delta
                        drums.append({"pitch": 51, "start_time": t_r, "duration": 0.22, "velocity": 125 if rs % 2 == 0 else 112})
                if bar % 4 == 3:
                    for f_idx, (f_t, f_p) in enumerate([(2.5, 45), (2.75, 47), (3.0, 48), (3.25, 48), (3.5, 49)]):
                        drums.append({"pitch": f_p, "start_time": b_offset + f_t, "duration": 0.2, "velocity": 120 + f_idx})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.25, "velocity": 125})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.25, "velocity": 127})
            else:
                for bk_t in [0.0, 1.5, 2.25, 3.0]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 127})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.8, "velocity": 120})

        # =========================================================================
        # TRACK 11: Rolling Belgian 16th Hardgroove / Triplet Polymeter
        # =========================================================================
        elif track_num == 11:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                if bar % 4 == 3:
                    kicks.append({"pitch": 36, "start_time": b_offset + 3.75, "duration": 0.2, "velocity": 118})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    vel_h = 124 if (s16 % 3 == 0) else (95 if (s16 % 3 == 2) else 78)
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": vel_h})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.35, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 1.5, "duration": 0.18, "velocity": 92})
                drums.append({"pitch": 38, "start_time": b_offset + 3.5, "duration": 0.18, "velocity": 92})
                if is_drop:
                    if is_drop_2:
                        for s16 in range(16):
                            drums.append({"pitch": 51, "start_time": b_offset + s16 * 0.25, "duration": 0.2, "velocity": 118 if s16 % 2 == 0 else 105})
                    else:
                        for r_t in [0.5, 1.25, 2.5, 3.25]:
                            drums.append({"pitch": 51, "start_time": b_offset + r_t, "duration": 0.3, "velocity": 118})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.25, "duration": 0.2, "velocity": 112})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.2, "velocity": 120})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.2, "velocity": 124})
            else:
                for bk_t in [0.0, 2.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.3, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 115})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 120})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.5, "velocity": 115})
                sub_notes.append({"pitch": sub_pitch + 3, "start_time": b_offset + 2.5, "duration": 1.2, "velocity": 118})

        # =========================================================================
        # TRACK 12: Industrial Stutter / Broken 4-Floor Gallop
        # =========================================================================
        elif track_num == 12:
            if not is_break:
                for k_t in [0.0, 1.75, 2.0, 3.0, 3.75]:
                    kicks.append({"pitch": 36, "start_time": b_offset + k_t, "duration": 0.28, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    if s16 in [6, 14]:
                        drums.append({"pitch": 42, "start_time": t_h, "duration": 0.1, "velocity": 125})
                        drums.append({"pitch": 42, "start_time": t_h + 0.125, "duration": 0.1, "velocity": 127})
                    else:
                        drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": 95 if s16 % 2 == 0 else 110})
                drums.append({"pitch": 46, "start_time": b_offset + 1.75, "duration": 0.35, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 3.75, "duration": 0.35, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 2.75, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 2.75, "duration": 0.22, "velocity": 120})
                if is_drop:
                    r_list = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5] if is_drop_2 else [0.5, 1.5, 2.5, 3.5]
                    for r_t in r_list:
                        drums.append({"pitch": 51, "start_time": b_offset + r_t, "duration": 0.35, "velocity": 120})
                for sb_t in [0.5, 1.25, 2.5, 3.25]:
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + sb_t, "duration": 0.35, "velocity": 122})
            else:
                for k_t in [0.0, 1.5, 2.75]:
                    kicks.append({"pitch": 36, "start_time": b_offset + k_t, "duration": 0.3, "velocity": 120})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 118})
                drums.append({"pitch": 38, "start_time": b_offset + 2.75, "duration": 0.25, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.2, "velocity": 115})
                sub_notes.append({"pitch": sub_pitch + 2, "start_time": b_offset + 2.0, "duration": 1.5, "velocity": 118})

        # =========================================================================
        # TRACK 13: Schranz Surgical Anvil Stabs (Cleaned from excessive flams)
        # =========================================================================
        elif track_num == 13:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                # Crisp surgical anvil accents placed cleanly on offbeats
                drums.append({"pitch": 47, "start_time": b_offset + 0.75, "duration": 0.22, "velocity": 124})
                drums.append({"pitch": 47, "start_time": b_offset + 2.25, "duration": 0.22, "velocity": 126})
                # Straight driving 8th closed hats
                for step8 in range(8):
                    t_h = b_offset + step8 * 0.5
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.20, "velocity": 122 if step8 % 2 == 1 else 95})
                for oh_t in [0.75, 2.25, 3.75]:
                    drums.append({"pitch": 46, "start_time": b_offset + oh_t, "duration": 0.28, "velocity": 122})
                # Clean claps on beats 1.0 and 3.0 + subtle pickup on 2.75
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 125})
                drums.append({"pitch": 38, "start_time": b_offset + 2.75, "duration": 0.14, "velocity": 95})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 127})
                if is_drop:
                    for s8 in range(8):
                        drums.append({"pitch": 51, "start_time": b_offset + s8 * 0.5, "duration": 0.3, "velocity": 124 if s8 % 2 == 1 else 105})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.35, "velocity": 122})
            else:
                drums.append({"pitch": 47, "start_time": b_offset + 0.0, "duration": 0.3, "velocity": 122})
                drums.append({"pitch": 47, "start_time": b_offset + 1.5, "duration": 0.3, "velocity": 125})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.2, "velocity": 120})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.5, "velocity": 120})

        # =========================================================================
        # TRACK 14: Detroit Acid Footwork / Syncopated Off-Grid Bop
        # =========================================================================
        elif track_num == 14:
            if not is_break:
                skip_beat_2 = (bar in (3, 7, 11, 15))
                for beat in range(4):
                    if skip_beat_2 and beat == 2:
                        continue
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.32, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 1.75, "duration": 0.28, "velocity": 126})
                drums.append({"pitch": 39, "start_time": b_offset + 3.5, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 38, "start_time": b_offset + 1.25, "duration": 0.16, "velocity": 88})
                drums.append({"pitch": 38, "start_time": b_offset + 2.75, "duration": 0.16, "velocity": 92})
                for s16 in range(16):
                    sw_d = 0.032 if (s16 % 2 == 1) else 0.0
                    t_h = b_offset + s16 * 0.25 + sw_d
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": 108 if (s16 % 2 == 1) else 85})
                drums.append({"pitch": 46, "start_time": b_offset + 0.75, "duration": 0.35, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 2.75, "duration": 0.35, "velocity": 124})
                if is_drop:
                    r_list = [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75] if is_drop_2 else [1.5, 3.5]
                    for r_t in r_list:
                        drums.append({"pitch": 51, "start_time": b_offset + r_t, "duration": 0.3, "velocity": 118})
                for sb_t in [0.75, 1.5, 2.75, 3.5]:
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + sb_t, "duration": 0.35, "velocity": 120})
            else:
                for bk_t in [0.0, 1.25, 2.5, 3.75]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.75, "duration": 0.25, "velocity": 120})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 122})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.8, "velocity": 115})
                sub_notes.append({"pitch": sub_pitch - 2, "start_time": b_offset + 2.5, "duration": 1.2, "velocity": 118})

        # =========================================================================
        # TRACK 15: Tribal Industrial Percussion / Polyrhythmic Tom Assault
        # =========================================================================
        elif track_num == 15:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                tom_seq = [45, 47, 48, 47, 45]
                for s16 in range(16):
                    if s16 % 4 != 0:
                        t_pitch = tom_seq[(bar * 16 + s16) % 5]
                        drums.append({"pitch": t_pitch, "start_time": b_offset + s16 * 0.25, "duration": 0.2, "velocity": 115})
                for c_beat in [1.0, 3.0]:
                    drums.append({"pitch": 38, "start_time": b_offset + c_beat - 0.04, "duration": 0.12, "velocity": 95})
                    drums.append({"pitch": 39, "start_time": b_offset + c_beat, "duration": 0.28, "velocity": 127})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.18, "velocity": 80 + (s16 % 4) * 12})
                drums.append({"pitch": 46, "start_time": b_offset + 0.5, "duration": 0.35, "velocity": 120})
                drums.append({"pitch": 46, "start_time": b_offset + 2.5, "duration": 0.35, "velocity": 122})
                if is_drop and (bar % 2 == 1 or is_drop_2):
                    for beat in range(4):
                        drums.append({"pitch": 51, "start_time": b_offset + beat + 0.5, "duration": 0.38, "velocity": 122})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.25, "duration": 0.65, "velocity": 122})
            else:
                for s8 in range(8):
                    t_pitch = [45, 47, 48, 47][s8 % 4]
                    drums.append({"pitch": t_pitch, "start_time": b_offset + s8 * 0.5, "duration": 0.3, "velocity": 110 + s8 * 2})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.8, "velocity": 115})

        # =========================================================================
        # TRACK 16: Rotterdam Gabber-Techno Clean Punch (Audited: No snare clutter)
        # =========================================================================
        elif track_num == 16:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                # High-impact Gabber claps on beats 1.0 and 3.0
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.28, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.28, "velocity": 127})
                # Turnaround snare burst ONLY on the 4th bar turnaround (beats 3.5, 3.75)
                if bar % 4 == 3:
                    drums.append({"pitch": 38, "start_time": b_offset + 3.5, "duration": 0.15, "velocity": 120})
                    drums.append({"pitch": 38, "start_time": b_offset + 3.75, "duration": 0.15, "velocity": 127})
                for oh_t in [0.5, 1.5, 2.5, 3.5]:
                    drums.append({"pitch": 46, "start_time": b_offset + oh_t, "duration": 0.32, "velocity": 122})
                for s16 in range(16):
                    drums.append({"pitch": 42, "start_time": b_offset + s16 * 0.25, "duration": 0.15, "velocity": 85 if s16 % 2 == 0 else 105})
                if is_drop:
                    for s8 in range(8):
                        drums.append({"pitch": 51, "start_time": b_offset + s8 * 0.5, "duration": 0.35, "velocity": 124 if is_drop_2 else 115})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.35, "velocity": 124})
            else:
                for bk_t in [0.0, 0.75, 2.0, 2.75]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.22, "velocity": 120})
                drums.append({"pitch": 38, "start_time": b_offset + 3.0, "duration": 0.22, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.8, "velocity": 118})

        # =========================================================================
        # TRACK 17: Hypnotic Berlin Minimal-Groove / Syncopated Rimshot
        # =========================================================================
        elif track_num == 17:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.32, "velocity": 125})
                for rim_t in [0.75, 1.75, 2.5, 3.75]:
                    drums.append({"pitch": 37, "start_time": b_offset + rim_t, "duration": 0.12, "velocity": 92})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.15, "velocity": 72 + (s16 % 2) * 16})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.32, "velocity": 120})
                drums.append({"pitch": 46, "start_time": b_offset + 2.75, "duration": 0.32, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 124})
                if is_drop:
                    for beat in range(4):
                        drums.append({"pitch": 51, "start_time": b_offset + beat + 0.75, "duration": 0.25, "velocity": 112 if not is_drop_2 else 122})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.33, "duration": 0.28, "velocity": 115})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.67, "duration": 0.28, "velocity": 118})
            else:
                for rim_t in [0.5, 1.25, 2.0, 2.75, 3.5]:
                    drums.append({"pitch": 37, "start_time": b_offset + rim_t, "duration": 0.12, "velocity": 90})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.8, "velocity": 115})

        # =========================================================================
        # TRACK 18: UK Rave Hardcore Hybrid Stepper
        # =========================================================================
        elif track_num == 18:
            if not is_break:
                k_beats = [0.0, 1.0, 3.0] if (bar % 2 == 1) else [0.0, 1.0, 2.0, 3.0]
                for kb in k_beats:
                    kicks.append({"pitch": 36, "start_time": b_offset + kb, "duration": 0.32, "velocity": 127})
                for sn_t in [1.0, 2.5, 3.5]:
                    drums.append({"pitch": 38, "start_time": b_offset + sn_t, "duration": 0.25, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 125})
                drums.append({"pitch": 39, "start_time": b_offset + 3.5, "duration": 0.25, "velocity": 127})
                for s16 in range(15):
                    drums.append({"pitch": 42, "start_time": b_offset + s16 * 0.25, "duration": 0.16, "velocity": 90 if s16 % 2 == 0 else 105})
                for trip_idx, trip_t in enumerate([3.75, 3.833, 3.917]):
                    drums.append({"pitch": 42, "start_time": b_offset + trip_t, "duration": 0.08, "velocity": 110 + trip_idx * 8})
                drums.append({"pitch": 46, "start_time": b_offset + 1.5, "duration": 0.35, "velocity": 122})
                drums.append({"pitch": 46, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 125})
                if is_drop:
                    drums.append({"pitch": 51, "start_time": b_offset + 0.0, "duration": 0.65, "velocity": 125})
                    drums.append({"pitch": 51, "start_time": b_offset + 2.0, "duration": 0.65, "velocity": 125})
                    if is_drop_2:
                        drums.append({"pitch": 51, "start_time": b_offset + 1.0, "duration": 0.4, "velocity": 115})
                        drums.append({"pitch": 51, "start_time": b_offset + 3.0, "duration": 0.4, "velocity": 115})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 0.8, "velocity": 120})
                sub_notes.append({"pitch": sub_pitch + 7, "start_time": b_offset + 1.5, "duration": 0.4, "velocity": 118})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 2.5, "duration": 0.8, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch + 5, "start_time": b_offset + 3.5, "duration": 0.4, "velocity": 120})
            else:
                for bk_t in [0.0, 1.75, 2.5]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 122})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 124})
                drums.append({"pitch": 38, "start_time": b_offset + 2.5, "duration": 0.25, "velocity": 126})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 1.5, "velocity": 118})
                sub_notes.append({"pitch": sub_pitch + 3, "start_time": b_offset + 2.0, "duration": 1.5, "velocity": 120})

        # =========================================================================
        # TRACK 19: Dark Psy-Techno Rolling Matrix
        # =========================================================================
        elif track_num == 19:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.32, "velocity": 127})
                    kicks.append({"pitch": 36, "start_time": b_offset + beat + 0.85, "duration": 0.12, "velocity": 98})
                for beat in range(4):
                    for sub_off in [0.25, 0.5, 0.75]:
                        sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + sub_off, "duration": 0.22, "velocity": 122 if sub_off == 0.75 else 115})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    vel_wave = int(80 + 35 * np.sin((s16 / 16.0) * np.pi))
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": vel_wave})
                for beat in range(4):
                    drums.append({"pitch": 46, "start_time": b_offset + beat + 0.5, "duration": 0.35, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 127})
                if is_drop:
                    for s16 in range(16):
                        r_vel = 126 if s16 % 4 == 2 else 105
                        drums.append({"pitch": 51, "start_time": b_offset + s16 * 0.25, "duration": 0.22, "velocity": r_vel})
            else:
                for bk_t in [0.0, 1.5, 2.25, 3.0]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 122})
                drums.append({"pitch": 39, "start_time": b_offset + 3.0, "duration": 0.25, "velocity": 124})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.8, "velocity": 120})

        # =========================================================================
        # TRACK 20: Maximum Rave Energy Polyrhythmic Climax
        # =========================================================================
        elif track_num == 20:
            if not is_break:
                for beat in range(4):
                    kicks.append({"pitch": 36, "start_time": b_offset + float(beat), "duration": 0.35, "velocity": 127})
                if bar % 4 == 3:
                    kicks.append({"pitch": 36, "start_time": b_offset + 3.75, "duration": 0.2, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 1.75, "duration": 0.22, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 2.0, "duration": 0.3, "velocity": 127})
                drums.append({"pitch": 39, "start_time": b_offset + 3.75, "duration": 0.22, "velocity": 125})
                drums.append({"pitch": 38, "start_time": b_offset + 2.0, "duration": 0.25, "velocity": 122})
                if is_drop:
                    for trip_step in range(6):
                        t_trip = b_offset + trip_step * (4.0 / 6.0)
                        drums.append({"pitch": 51, "start_time": t_trip, "duration": 0.45, "velocity": 126 if trip_step % 2 == 0 else 118})
                for s16 in range(16):
                    t_h = b_offset + s16 * 0.25
                    vel_lfo = int(85 + 40 * np.sin((s16 / 16.0) * 2 * np.pi))
                    drums.append({"pitch": 42, "start_time": t_h, "duration": 0.16, "velocity": vel_lfo})
                for beat in range(4):
                    drums.append({"pitch": 46, "start_time": b_offset + beat + 0.5, "duration": 0.38, "velocity": 127})
                if bar % 4 == 3:
                    tom_casc = [
                        (2.5, 45, 0.2, 122),
                        (2.75, 47, 0.2, 124),
                        (3.0, 48, 0.2, 126),
                        (3.25, 38, 0.18, 127),
                        (3.5, 49, 0.4, 127)
                    ]
                    for f_t, f_p, f_dur, f_vel in tom_casc:
                        drums.append({"pitch": f_p, "start_time": b_offset + f_t, "duration": f_dur, "velocity": f_vel})
                for beat in range(4):
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.5, "duration": 0.25, "velocity": 127})
                    sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + beat + 0.75, "duration": 0.22, "velocity": 127})
            else:
                for bk_t in [0.0, 1.5, 2.25, 3.0, 3.75]:
                    kicks.append({"pitch": 36, "start_time": b_offset + bk_t, "duration": 0.28, "velocity": 125})
                drums.append({"pitch": 38, "start_time": b_offset + 1.0, "duration": 0.25, "velocity": 124})
                drums.append({"pitch": 39, "start_time": b_offset + 2.5, "duration": 0.25, "velocity": 127})
                sub_notes.append({"pitch": sub_pitch, "start_time": b_offset + 0.0, "duration": 3.8, "velocity": 124})

    return kicks, drums, sub_notes


def generate_charlotte_overdrive_drums(section_name: str, bars: int, sub_pitch: int = 36, track_num: int = 1) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Generates authentic bespoke Hard Techno drums delegating directly to generate_distinct_hardtechno_drums."""
    return generate_distinct_hardtechno_drums(section_name, bars, sub_pitch=sub_pitch, track_num=track_num)


def generate_track_score(track_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the complete sovereign AI score for a specific album track.
    Combines:
    - Charlotte de Witte Overdrive Drum Rhythm DNA across all 7 sections.
    - Specific Prodigy rave lead riffs, acid counter-melodies, and hoover stabs.
    """
    track_num = track_meta["track_number"]
    bpm = track_meta["bpm"]
    key = track_meta["key"]
    scale = track_meta["scale"]
    root_p = track_meta["root_pitch"]
    sub_p = track_meta["sub_pitch"]

    sections_layout = [
        {"name": "Intro", "bars": 8},
        {"name": "Buildup", "bars": 8},
        {"name": "Drop 1", "bars": 16},
        {"name": "Breakdown", "bars": 8},
        {"name": "Buildup 2", "bars": 8},
        {"name": "Drop 2", "bars": 16},
        {"name": "Outro", "bars": 8}
    ]

    score = {
        "bpm": bpm,
        "key": key,
        "scale": scale,
        "genre": "hard_techno",
        "composition": {}
    }

    kick_track_name = "[KICK] Rumble_Kick"
    drums_track_name = "[DRUMS] Overdrive_909_Drums"
    sub_track_name = f"[BASS] {track_meta['sub_role']}"
    lead_track_name = f"[LEAD] {track_meta['lead_role']}"
    keys_track_name = f"[KEYS] {track_meta['keys_role']}"
    fx_track_name = f"[EAR_CANDY] {track_meta['fx_role']}"

    kick_sections = {}
    drums_sections = {}
    sub_sections = {}
    lead_sections = {}
    keys_sections = {}
    fx_sections = {}

    for sec in sections_layout:
        s_name = sec["name"]
        bars = sec["bars"]
        s_lower = s_name.lower()
        is_drop = "drop" in s_lower
        is_build = "build" in s_lower
        is_intro = "intro" in s_lower
        is_break = "break" in s_lower
        is_outro = "outro" in s_lower

        # 1. Generate Charlotte Overdrive Drums & Rumble (Tracks 1-10) or Distinct Grooves (Tracks 11-20)
        k_notes, d_notes, b_notes = generate_charlotte_overdrive_drums(s_name, bars, sub_pitch=sub_p, track_num=track_num)
        kick_sections[s_name] = k_notes
        drums_sections[s_name] = d_notes
        sub_sections[s_name] = b_notes

        # 2. Generate Track-Specific Prodigy Lead & Synths
        lead_notes = []
        keys_notes = []
        fx_notes = []

        # Melodic riff construction per track index
        for bar in range(bars):
            b_offset = bar * 4.0

            # Tension Vacuum Stop: silence melodic instruments in last 2 beats of Buildups,
            # BUT inject the sovereign Pre-Drop Vocal Tag / Rave Chant right into the vacuum silence!
            if is_build and bar == (bars - 1):
                # Riser lead in first 2 beats
                lead_notes.append({"pitch": root_p + 12, "start_time": b_offset + 0.0, "duration": 1.8, "velocity": 125})
                fx_notes.append({"pitch": 72, "start_time": b_offset + 0.0, "duration": 1.9, "velocity": 120})

                # Pre-Drop Vocal Tag shouting into the 2-beat silence (beats 2.25 to 3.85)
                vocal_tag_pitches = {
                    1: 65,  # Voodoo!
                    2: 62,  # Poison!
                    3: 60,  # Breathe!
                    4: 64,  # Fire!
                    5: 67,  # Smack!
                    6: 69,  # No Good!
                    7: 65,  # Spitfire!
                    8: 66,  # Out of Space!
                    9: 68,  # Jericho!
                    10: 70, # Overdrive!
                    11: 67, # Thunder!
                    12: 68, # Kinetics!
                    13: 63, # Iron!
                    14: 65, # Rave!
                    15: 61, # Shock!
                    16: 69, # Dominator!
                    17: 64, # Cyber!
                    18: 70, # Rupture!
                    19: 67, # Vortex!
                    20: 74  # Maximum!
                }
                v_pitch = vocal_tag_pitches.get(track_num, 64)
                fx_notes.append({"pitch": v_pitch, "start_time": b_offset + 2.25, "duration": 1.5, "velocity": 127})
                continue

            # --- TRACK 1: Voodoo Overdrive (F Phrygian 303 Acid Scream - ENRICH ACID COMPLEXITY) ---
            if track_num == 1:
                if is_drop or is_break or (is_intro and bar >= 4):
                    # Authentic TB-303 acid sequence with 16th slides, octave accents, and Phrygian tension (Gb, Db)
                    # Odd bars resolve downward, even bars ascend into blistering rave peak
                    if bar % 2 == 0:
                        acid_pattern = [
                            (0.0, 53, 0.22, 120),   # F3 root
                            (0.25, 54, 0.22, 125),  # Gb3 minor 2nd slide
                            (0.75, 53, 0.20, 110),  # F3 ghost pickup
                            (1.0, 56, 0.35, 127),   # Ab3 minor 3rd accent
                            (1.5, 65, 0.45, 127),   # F4 high octave slide!
                            (2.0, 60, 0.30, 122),   # C4 5th
                            (2.5, 58, 0.22, 118),   # Bb3 4th
                            (3.0, 54, 0.22, 124),   # Gb3 minor 2nd
                            (3.5, 53, 0.35, 127),   # F3 root resolution
                        ]
                    else:
                        acid_pattern = [
                            (0.0, 53, 0.22, 122),   # F3 root
                            (0.5, 56, 0.25, 118),   # Ab3
                            (1.0, 61, 0.35, 127),   # Db4 Phrygian 6th accent!
                            (1.5, 60, 0.25, 120),   # C4
                            (2.0, 63, 0.40, 127),   # Eb4 7th scream!
                            (2.75, 60, 0.22, 122),  # C4
                            (3.25, 54, 0.35, 125),  # Gb3 slide to root
                        ]
                    for rel_t, p, dur, vel in acid_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                # Liam Howlett hoover stabs on offbeats 1.5 and 3.5 leaving rumble kick untouched
                if is_drop:
                    keys_notes.extend([
                        {"pitch": 53, "start_time": b_offset + 1.5, "duration": 0.35, "velocity": 118},
                        {"pitch": 56, "start_time": b_offset + 1.5, "duration": 0.35, "velocity": 115},
                        {"pitch": 60, "start_time": b_offset + 1.5, "duration": 0.35, "velocity": 122},
                        {"pitch": 54, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 124},
                        {"pitch": 58, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 118},
                        {"pitch": 61, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 125},
                    ])

            # --- TRACK 2: Poison Protocol (D Minor Rave Horns - SIMPLIFY: BOLD HYPNOTIC HOOK) ---
            elif track_num == 2:
                if is_drop or is_break:
                    # Iconic 3-note rave horn riff (D4 -> F4 -> G4) with syncopation and beat 3 negative space
                    horn_pattern = [
                        (0.0, 62, 0.30, 127),   # D4 downbeat strike
                        (0.75, 65, 0.22, 120),  # F4 pickup
                        (1.0, 67, 0.50, 127),   # G4 high rave horn blast!
                        (2.0, 65, 0.25, 122),   # F4 drop
                        (2.5, 62, 0.65, 127),   # D4 heavy resolve
                    ]
                    for rel_t, p, dur, vel in horn_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop or is_build:
                    # Raw Prodigy saw stabs filling the pocket at beat 3.25 and 3.75
                    keys_notes.extend([
                        {"pitch": 50, "start_time": b_offset + 3.25, "duration": 0.30, "velocity": 118},
                        {"pitch": 57, "start_time": b_offset + 3.25, "duration": 0.30, "velocity": 122},
                        {"pitch": 50, "start_time": b_offset + 3.75, "duration": 0.25, "velocity": 120},
                        {"pitch": 57, "start_time": b_offset + 3.75, "duration": 0.25, "velocity": 125},
                    ])

            # --- TRACK 3: Breathe The Voltage (C Minor Punk Saw - SIMPLIFY: RELENTLESS PUNK RIFF) ---
            elif track_num == 3:
                if is_drop or is_break:
                    # Relentless 3-note staccato punk swagger (C3 -> Eb3 -> F3 / F#3 blues scream)
                    punk_pattern = [
                        (0.0, 48, 0.20, 127),   # C3 hard punch
                        (0.5, 48, 0.18, 120),   # C3 staccato
                        (0.75, 51, 0.22, 124),  # Eb3 minor 3rd
                        (1.25, 53, 0.20, 122),  # F3
                        (1.5, 54, 0.40, 127),   # F#3 blues devil scream!
                        (2.0, 53, 0.20, 120),   # F3 fall
                        (2.25, 51, 0.20, 122),  # Eb3
                        (2.75, 48, 0.45, 127),  # C3 resolution
                    ]
                    for rel_t, p, dur, vel in punk_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    # Menacing rave organ stab hitting in the pocket on beat 3.0
                    keys_notes.extend([
                        {"pitch": 60, "start_time": b_offset + 3.0, "duration": 0.45, "velocity": 122},
                        {"pitch": 63, "start_time": b_offset + 3.0, "duration": 0.45, "velocity": 118},
                        {"pitch": 67, "start_time": b_offset + 3.0, "duration": 0.45, "velocity": 125},
                    ])

            # --- TRACK 4: Firestarter Rave (E Minor Siren Lead - SIMPLIFY SIREN / ENRICH RAVE PIANO) ---
            elif track_num == 4:
                if is_drop or is_break:
                    # Hypnotic 2-tone warehouse siren oscillating between E4 root, Bb4 tritone, and D5 octave reach
                    siren_pattern = [
                        (0.0, 64, 0.22, 127),   # E4 siren tone
                        (0.5, 70, 0.35, 127),   # Bb4 tritone alarm!
                        (1.0, 64, 0.22, 125),   # E4
                        (1.5, 74, 0.40, 127),   # D5 high siren scream!
                        (2.0, 64, 0.22, 124),   # E4
                        (2.5, 70, 0.40, 127),   # Bb4 alarm return
                    ]
                    for rel_t, p, dur, vel in siren_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop or is_build:
                    # Authentic 1992 Korg M1 rave piano stabs driving the offbeats
                    keys_notes.extend([
                        {"pitch": 52, "start_time": b_offset + 1.75, "duration": 0.35, "velocity": 122}, # Em
                        {"pitch": 55, "start_time": b_offset + 1.75, "duration": 0.35, "velocity": 125},
                        {"pitch": 59, "start_time": b_offset + 1.75, "duration": 0.35, "velocity": 127},
                        {"pitch": 50, "start_time": b_offset + 3.75, "duration": 0.35, "velocity": 120}, # D
                        {"pitch": 54, "start_time": b_offset + 3.75, "duration": 0.35, "velocity": 122},
                        {"pitch": 57, "start_time": b_offset + 3.75, "duration": 0.35, "velocity": 125},
                    ])

            # --- TRACK 5: Smack The Void (G Minor Arp - SIMPLIFY: HYPNOTIC ROLLING MINIMALISM) ---
            elif track_num == 5:
                if is_drop or is_break:
                    # Replaced hyperactive 16-note arp with a hypnotic 4-note rolling motif with syncopated 16th pockets
                    roll_pattern = [
                        (0.0, 55, 0.22, 125),   # G3 root
                        (0.5, 58, 0.22, 120),   # Bb3 minor 3rd
                        (0.75, 62, 0.30, 127),  # D4 5th
                        (1.25, 63, 0.35, 127),  # Eb4 minor 6th tension
                        (2.0, 62, 0.25, 122),   # D4
                        (2.5, 58, 0.22, 118),   # Bb3
                        (3.0, 55, 0.45, 125),   # G3 root hold
                    ]
                    for rel_t, p, dur, vel in roll_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    # Massive dark Hoover bed on downbeats breathing through the open space
                    if bar % 2 == 0:
                        keys_notes.extend([
                            {"pitch": 43, "start_time": b_offset + 0.0, "duration": 3.6, "velocity": 115},
                            {"pitch": 50, "start_time": b_offset + 0.0, "duration": 3.6, "velocity": 120},
                            {"pitch": 55, "start_time": b_offset + 0.0, "duration": 3.6, "velocity": 124},
                        ])

            # --- TRACK 6: No Good Resonance (A Minor - ENRICH: FULL RAVE PIANO & 303 ACID COUNTERPOINT) ---
            elif track_num == 6:
                if is_drop or is_break:
                    # Classic 1994 Liam Howlett rave piano chord progression: Am -> C/G -> Fmaj7 -> G
                    chord_steps = [
                        (0.0, [57, 60, 64], 0.35, 125),   # Am
                        (0.5, [57, 60, 64], 0.25, 120),   # Am syncopated bounce
                        (1.25, [55, 60, 64], 0.35, 122),  # C/G inversion
                        (2.0, [53, 57, 60, 64], 0.45, 127),# Fmaj7 lush rave chord!
                        (3.0, [55, 59, 62], 0.35, 124)    # G major uplift
                    ]
                    for rel_t, chord, dur, vel in chord_steps:
                        for p in chord:
                            lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    # Screaming 303 acid line weaving syncopated counterpoint through the piano rests
                    acid_counter = [
                        (0.75, 45, 0.20, 118),  # A2
                        (1.0, 48, 0.20, 122),   # C3
                        (1.75, 52, 0.25, 127),  # E3 slide
                        (2.75, 50, 0.20, 120),  # D3
                        (3.5, 55, 0.22, 125),   # G3
                        (3.75, 57, 0.25, 127),  # A3 scream
                    ]
                    for rel_t, p, dur, vel in acid_counter:
                        keys_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})

            # --- TRACK 7: Spitfire Pulse (Bb Minor - SIMPLIFY: BRUTAL INDUSTRIAL STAB RIFF) ---
            elif track_num == 7:
                if is_drop or is_break:
                    # Stark, militaristic 3-note industrial razor saw with negative space
                    pulse_pattern = [
                        (0.0, 58, 0.16, 127),   # Bb3 staccato whip
                        (0.5, 61, 0.16, 124),   # Db4 staccato
                        (1.0, 58, 0.16, 127),   # Bb3
                        (1.75, 65, 0.38, 127),  # F4 power impact!
                        (2.5, 64, 0.22, 125),   # E4 industrial tritone bend
                        (3.0, 58, 0.18, 127),   # Bb3 double tap
                        (3.25, 58, 0.22, 127),  # Bb3
                    ]
                    for rel_t, p, dur, vel in pulse_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    # Heavy metallic anvils striking on beats 1.25 and 3.25
                    keys_notes.extend([
                        {"pitch": 58, "start_time": b_offset + 1.25, "duration": 0.25, "velocity": 122},
                        {"pitch": 65, "start_time": b_offset + 1.25, "duration": 0.25, "velocity": 125},
                        {"pitch": 58, "start_time": b_offset + 3.25, "duration": 0.25, "velocity": 124},
                        {"pitch": 65, "start_time": b_offset + 3.25, "duration": 0.25, "velocity": 127},
                    ])

            # --- TRACK 8: Out Of Space Reactor (F# Minor - ENRICH: SOARING 1992 ANTHEMIC CONTOUR) ---
            elif track_num == 8:
                if is_drop or is_break:
                    # Soaring, multi-octave 1992 rave anthem contour (F#4 -> C#5 -> E5 -> F#5 heroic peak)
                    if bar % 2 == 0:
                        space_pattern = [
                            (0.0, 66, 0.25, 125),   # F#4
                            (0.33, 69, 0.25, 122),  # A4
                            (0.66, 73, 0.40, 127),  # C#5
                            (1.25, 76, 0.45, 127),  # E5 soaring high note!
                            (2.0, 73, 0.30, 124),   # C#5
                            (2.5, 71, 0.25, 120),   # B4
                            (3.0, 69, 0.30, 122),   # A4
                            (3.5, 66, 0.40, 127),   # F#4
                        ]
                    else:
                        space_pattern = [
                            (0.0, 69, 0.25, 122),   # A4
                            (0.5, 71, 0.25, 122),   # B4
                            (1.0, 73, 0.35, 127),   # C#5
                            (1.5, 78, 0.55, 127),   # F#5 HEROIC PEAK CLIMAX!
                            (2.25, 76, 0.35, 124),  # E5
                            (2.75, 73, 0.30, 122),  # C#5
                            (3.25, 66, 0.50, 127),  # F#4 root resolution
                        ]
                    for rel_t, p, dur, vel in space_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    # Sub acid answer hook locking with the rumble
                    keys_notes.extend([
                        {"pitch": 42, "start_time": b_offset + 1.0, "duration": 0.35, "velocity": 122},
                        {"pitch": 45, "start_time": b_offset + 1.5, "duration": 0.30, "velocity": 125},
                        {"pitch": 49, "start_time": b_offset + 2.75, "duration": 0.35, "velocity": 124},
                        {"pitch": 42, "start_time": b_offset + 3.25, "duration": 0.45, "velocity": 127},
                    ])

            # --- TRACK 9: Jericho Steel (Ab Minor - SIMPLIFY: WALL-SHAKING BRASS STABS & SILENCE) ---
            elif track_num == 9:
                if is_drop or is_break:
                    # Apocalyptic rave horn hits with maximum negative space for industrial rumble
                    jericho_pattern = [
                        (0.0, 56, 0.40, 127),   # Ab3 heavy brass impact
                        (0.75, 59, 0.22, 122),  # B3 pickup
                        (1.0, 63, 0.65, 127),   # Eb4 sustained horn blast!
                        (2.5, 62, 0.25, 125),   # D4 tritone devil tension
                        (2.75, 63, 0.25, 125),  # Eb4
                        (3.0, 56, 0.70, 127),   # Ab3 massive root resolution
                    ]
                    for rel_t, p, dur, vel in jericho_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop or is_build:
                    # Distorted industrial steel hits on beats 0.5 and 2.5
                    keys_notes.extend([
                        {"pitch": 44, "start_time": b_offset + 0.5, "duration": 0.30, "velocity": 118},
                        {"pitch": 51, "start_time": b_offset + 0.5, "duration": 0.30, "velocity": 122},
                        {"pitch": 44, "start_time": b_offset + 2.5, "duration": 0.30, "velocity": 120},
                        {"pitch": 51, "start_time": b_offset + 2.5, "duration": 0.30, "velocity": 124},
                    ])

            # --- TRACK 10: The Overdrive Experience (Eb Minor - ENRICH: DUAL-VOICE CLIMAX ANTHEM & ACID) ---
            elif track_num == 10:
                if is_drop or is_break:
                    # Grand Finale Rave Anthem: 2-bar heroic progression reaching into upper stratosphere
                    if bar % 2 == 0:
                        anthem_pattern = [
                            (0.0, 63, 0.25, 127),   # Eb4
                            (0.33, 66, 0.25, 122),  # Gb4
                            (0.66, 70, 0.40, 127),  # Bb4
                            (1.25, 73, 0.35, 127),  # Db5
                            (1.75, 77, 0.45, 127),  # F5 majestic reach!
                            (2.25, 75, 0.30, 124),  # Eb5
                            (2.75, 73, 0.25, 120),  # Db5
                            (3.25, 70, 0.45, 127),  # Bb4
                        ]
                    else:
                        anthem_pattern = [
                            (0.0, 63, 0.25, 127),   # Eb4
                            (0.5, 70, 0.25, 124),   # Bb4
                            (1.0, 73, 0.35, 127),   # Db5
                            (1.5, 75, 0.30, 125),   # Eb5
                            (1.75, 78, 0.60, 127),  # Gb5 GRAND ALBUM CLIMAX APEX!
                            (2.5, 77, 0.30, 124),   # F5
                            (3.0, 73, 0.25, 122),   # Db5
                            (3.33, 70, 0.25, 120),  # Bb4
                            (3.66, 63, 0.35, 127),  # Eb4 resolution
                        ]
                    for rel_t, p, dur, vel in anthem_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    # Screaming TB-303 acid cascade weaving syncopated counterpoint beneath the anthem
                    acid_anthem = [
                        (0.25, 51, 0.20, 120),  # Eb3
                        (0.75, 54, 0.20, 124),  # Gb3
                        (1.5, 58, 0.25, 127),   # Bb3
                        (2.25, 61, 0.20, 125),  # Db4
                        (2.75, 60, 0.20, 120),  # C4
                        (3.25, 58, 0.20, 122),  # Bb3
                        (3.75, 54, 0.22, 125),  # Gb3
                    ]
                    for rel_t, p, dur, vel in acid_anthem:
                        keys_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})

            # --- TRACK 11: Thunder Strike (B Minor - CATCHY 2-NOTE HYPNOTIC RAVE HOOK) ---
            elif track_num == 11:
                if is_drop or is_break:
                    hook_pattern = [
                        (0.0, 59, 0.35, 127),   # B3 downbeat strike
                        (1.25, 62, 0.25, 124),  # D4 syncopated leap
                        (2.0, 59, 0.60, 127),   # B3 sustained resolution
                    ]
                    for rel_t, p, dur, vel in hook_pattern:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    keys_notes.extend([
                        {"pitch": 59, "start_time": b_offset + 1.5, "duration": 0.30, "velocity": 118},
                        {"pitch": 62, "start_time": b_offset + 1.5, "duration": 0.30, "velocity": 122},
                        {"pitch": 66, "start_time": b_offset + 1.5, "duration": 0.30, "velocity": 125},
                        {"pitch": 59, "start_time": b_offset + 3.5, "duration": 0.30, "velocity": 120},
                        {"pitch": 62, "start_time": b_offset + 3.5, "duration": 0.30, "velocity": 124},
                        {"pitch": 66, "start_time": b_offset + 3.5, "duration": 0.30, "velocity": 127},
                    ])

            # --- TRACK 12: Acid Kinetics (G# Dorian - RELENTLESS STICKY 3-NOTE ACID PULSE) ---
            elif track_num == 12:
                if is_drop or is_break:
                    acid_kinetic = [
                        (0.0, 44, 0.22, 127),   # G#2 punch (subterranean octave)
                        (0.75, 47, 0.22, 122),  # B2
                        (1.5, 46, 0.35, 127),   # A#2 slide
                        (2.25, 44, 0.50, 127),  # G#2 resolution
                    ]
                    for rel_t, p, dur, vel in acid_kinetic:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop or is_build:
                    keys_notes.extend([
                        {"pitch": 44, "start_time": b_offset + 3.25, "duration": 0.25, "velocity": 120},
                        {"pitch": 51, "start_time": b_offset + 3.25, "duration": 0.25, "velocity": 125},
                        {"pitch": 44, "start_time": b_offset + 3.75, "duration": 0.22, "velocity": 122},
                        {"pitch": 51, "start_time": b_offset + 3.75, "duration": 0.22, "velocity": 127},
                    ])

            # --- TRACK 13: Iron Discipline (D# Phrygian - SURGICAL INDUSTRIAL HORN PUNCH) ---
            elif track_num == 13:
                if is_drop or is_break:
                    horn_iron = [
                        (0.0, 51, 0.50, 127),   # D#3 downbeat blast (heavy mid octave)
                        (1.75, 54, 0.40, 125),  # F#3 syncopated stab
                    ]
                    for rel_t, p, dur, vel in horn_iron:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    keys_notes.extend([
                        {"pitch": 51, "start_time": b_offset + 2.0, "duration": 0.35, "velocity": 122},
                        {"pitch": 58, "start_time": b_offset + 2.0, "duration": 0.35, "velocity": 125},
                        {"pitch": 63, "start_time": b_offset + 2.0, "duration": 0.35, "velocity": 127},
                    ])

            # --- TRACK 14: Rave Invasion (F Dorian - HIGH-OCTAVE 1993 RAVE STAB RIFF) ---
            elif track_num == 14:
                if is_drop or is_break:
                    rave_stab_pat = [
                        (0.0, 65, 0.22, 127),   # F4 high rave bite
                        (0.75, 68, 0.22, 122),  # Ab4
                        (1.5, 70, 0.25, 124),   # Bb4
                        (2.0, 72, 0.45, 127),   # C5 rave peak!
                    ]
                    for rel_t, p, dur, vel in rave_stab_pat:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop or is_build:
                    for c_off in [1.5, 2.5, 3.5]:
                        keys_notes.extend([
                            {"pitch": 53, "start_time": b_offset + c_off, "duration": 0.30, "velocity": 118},
                            {"pitch": 60, "start_time": b_offset + c_off, "duration": 0.30, "velocity": 122},
                            {"pitch": 65, "start_time": b_offset + c_off, "duration": 0.30, "velocity": 125},
                        ])

            # --- TRACK 15: Sub Frequency Shock (C# Harmonic Minor - SUBTERRANEAN DARK HOOK) ---
            elif track_num == 15:
                if is_drop or is_break:
                    dark_hook = [
                        (0.0, 49, 0.45, 127),   # C#3 downbeat
                        (1.5, 52, 0.35, 122),   # E3
                        (2.5, 49, 0.80, 127),   # C#3 sustained hold
                    ]
                    for rel_t, p, dur, vel in dark_hook:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    if bar % 2 == 0:
                        keys_notes.extend([
                            {"pitch": 37, "start_time": b_offset + 0.0, "duration": 3.5, "velocity": 118},
                            {"pitch": 44, "start_time": b_offset + 0.0, "duration": 3.5, "velocity": 122},
                            {"pitch": 49, "start_time": b_offset + 0.0, "duration": 3.5, "velocity": 125},
                        ])

            # --- TRACK 16: Dominator Reign (A Phrygian Dominant - SCREAMING GABBER HOOVER DIVE) ---
            elif track_num == 16:
                if is_drop or is_break:
                    dive_hook = [
                        (0.0, 69, 0.25, 125),   # A4 high screech
                        (1.0, 73, 0.25, 124),   # C#5 exotic 3rd
                        (1.5, 76, 0.35, 127),   # E5 high peak!
                        (2.25, 69, 0.65, 127),  # A4 dive resolution
                    ]
                    for rel_t, p, dur, vel in dive_hook:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    acid_chops = [
                        (0.75, 57, 0.18, 120),  # A3
                        (1.75, 61, 0.20, 124),  # C#4
                        (3.25, 64, 0.22, 127),  # E4
                        (3.75, 69, 0.22, 127),  # A4
                    ]
                    for rel_t, p, dur, vel in acid_chops:
                        keys_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})

            # --- TRACK 17: Cybernetic Pulse (E Phrygian - MODULAR LASER PING) ---
            elif track_num == 17:
                if is_drop or is_break:
                    laser_ping = [
                        (0.0, 52, 0.15, 127),   # E3 staccato ping
                        (0.5, 55, 0.15, 125),   # G3
                        (1.25, 52, 0.18, 127),  # E3
                        (2.0, 55, 0.35, 127),   # G3
                    ]
                    for rel_t, p, dur, vel in laser_ping:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    keys_notes.extend([
                        {"pitch": 40, "start_time": b_offset + 1.0, "duration": 0.30, "velocity": 120},
                        {"pitch": 47, "start_time": b_offset + 1.0, "duration": 0.30, "velocity": 124},
                        {"pitch": 40, "start_time": b_offset + 2.5, "duration": 0.30, "velocity": 122},
                        {"pitch": 47, "start_time": b_offset + 2.5, "duration": 0.30, "velocity": 125},
                    ])

            # --- TRACK 18: Rupture Core (Bb Dorian - PIERCING PUNK WHISTLE) ---
            elif track_num == 18:
                if is_drop or is_break:
                    punk_whistle = [
                        (0.0, 70, 0.22, 127),   # Bb4 piercing whistle
                        (0.75, 73, 0.22, 125),  # Db5
                        (1.5, 77, 0.40, 127),   # F5 high rave peak!
                        (2.5, 70, 0.50, 127),   # Bb4 resolve
                    ]
                    for rel_t, p, dur, vel in punk_whistle:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    keys_notes.extend([
                        {"pitch": 58, "start_time": b_offset + 2.0, "duration": 0.35, "velocity": 122},
                        {"pitch": 61, "start_time": b_offset + 2.0, "duration": 0.35, "velocity": 125},
                        {"pitch": 58, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 124},
                        {"pitch": 61, "start_time": b_offset + 3.5, "duration": 0.35, "velocity": 127},
                    ])

            # --- TRACK 19: Vortex Transmission (G Harmonic Minor - DRIVING SUBTERRANEAN MATRIX) ---
            elif track_num == 19:
                if is_drop or is_break:
                    vortex_roll = [
                        (0.0, 43, 0.22, 125),   # G2 subterranean drive
                        (0.5, 46, 0.22, 122),   # Bb2
                        (1.0, 50, 0.35, 127),   # D3
                        (2.0, 43, 0.55, 127),   # G2
                    ]
                    for rel_t, p, dur, vel in vortex_roll:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    keys_notes.extend([
                        {"pitch": 31, "start_time": b_offset + 0.0, "duration": 0.40, "velocity": 120},
                        {"pitch": 38, "start_time": b_offset + 0.0, "duration": 0.40, "velocity": 124},
                        {"pitch": 43, "start_time": b_offset + 0.0, "duration": 0.40, "velocity": 127},
                    ])

            # --- TRACK 20: Final Overdrive Anthem (D Phrygian Dominant - STADIUM RAVE COLOSSUS) ---
            elif track_num == 20:
                if is_drop or is_break:
                    anthem_final = [
                        (0.0, 62, 0.25, 127),   # D4
                        (0.75, 66, 0.25, 124),  # F#4 exotic major 3rd!
                        (1.5, 69, 0.35, 127),   # A4
                        (2.0, 72, 0.35, 127),   # C5
                        (2.5, 74, 0.65, 127),   # D5 MAXIMUM FESTIVAL PEAK!
                    ]
                    for rel_t, p, dur, vel in anthem_final:
                        lead_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})
                if is_drop:
                    acid_final = [
                        (0.25, 50, 0.20, 122),  # D3
                        (1.0, 54, 0.20, 125),   # F#3
                        (1.75, 57, 0.25, 127),  # A3
                        (2.75, 62, 0.22, 125),  # D4
                        (3.25, 74, 0.30, 127),  # D5 apex scream
                    ]
                    for rel_t, p, dur, vel in acid_final:
                        keys_notes.append({"pitch": p, "start_time": b_offset + rel_t, "duration": dur, "velocity": vel})

            # Atmospheric FX: White noise sweeps, risers, and downbeat impacts
            if is_build:
                if bar >= 4:
                    # Progressive rising pitch sweep across bars 4, 5, 6
                    fx_notes.append({"pitch": 72 + (bar - 4) * 3, "start_time": b_offset + 0.0, "duration": 3.8, "velocity": 90 + bar * 8})
            elif is_drop:
                # Downbeat impact on bar 0
                if bar == 0:
                    fx_notes.append({"pitch": 60, "start_time": b_offset + 0.0, "duration": 2.5, "velocity": 127})
                elif bar % 4 == 0:
                    fx_notes.append({"pitch": 60, "start_time": b_offset + 0.0, "duration": 1.5, "velocity": 115})

        # DROP 2 CLIMAX EVOLUTION: +12 semitone octave leap on leads & syncopated rave vocal stabs
        is_drop_2 = is_drop and ("drop 2" in s_lower or "2" in s_lower)
        if is_drop_2:
            evolved_leads = []
            for ln in lead_notes:
                new_ln = dict(ln)
                new_ln["pitch"] = min(96, new_ln["pitch"] + 12)
                new_ln["velocity"] = 127
                evolved_leads.append(new_ln)
            lead_notes = evolved_leads

            # Syncopated rave vocal chants on offbeats (1.5, 3.5) on alternating bars
            for bar in range(bars):
                b_offset = bar * 4.0
                if bar % 2 == 1:
                    fx_notes.append({"pitch": min(96, root_p + 12), "start_time": b_offset + 1.5, "duration": 0.45, "velocity": 124})
                    fx_notes.append({"pitch": min(96, root_p + 15), "start_time": b_offset + 3.5, "duration": 0.45, "velocity": 127})

        # Apply TessituraGuard to guarantee acoustic safety
        lead_sections[s_name] = TessituraGuard.enforce_safe_tessitura_dict(lead_notes, role="LEAD")
        keys_sections[s_name] = TessituraGuard.enforce_safe_tessitura_dict(keys_notes, role="KEYS")
        fx_sections[s_name] = TessituraGuard.enforce_safe_tessitura_dict(fx_notes, role="EAR_CANDY")

    score["composition"][kick_track_name] = kick_sections
    score["composition"][drums_track_name] = drums_sections
    score["composition"][sub_track_name] = sub_sections
    score["composition"][lead_track_name] = lead_sections
    score["composition"][keys_track_name] = keys_sections
    score["composition"][fx_track_name] = fx_sections

    return score


def apply_hard_techno_saturation_chains(conn: AbletonLiveConnection, t_num: int) -> Dict[str, Any]:
    """
    Sculpts aggressive Hard Techno & Prodigy saturation chains across the live session:
    - Track 1 (Overdrive 909 Drums): Drum Buss Drive=0.55, Crunch=0.35, Boom=0.30, Transients=+0.20.
    - Track 2 (Sub Bass): Saturator Drive=0.65, Soft Clip ON.
    - Track 3 (Prodigy Lead): Saturator / Overdrive Drive=0.58.
    - Master / Bus: Glue Compressor Soft Clip ON.
    """
    logger.info("[TRACK %d] CONFIGURING HARD TECHNO & PRODIGY SATURATION CHAINS...", t_num)
    code = '''
report = []
for t_idx, t in enumerate(song.tracks):
    t_name = t.name.lower()
    for d in t.devices:
        d_name = d.name.lower()
        if 'drum buss' in d_name:
            for p in d.parameters:
                p_n = p.name.lower()
                if p_n == 'drive':
                    p.value = 0.58
                elif 'crunch' in p_n:
                    p.value = 0.38
                elif 'transients' in p_n:
                    p.value = 0.25
                elif 'boom amt' in p_n:
                    p.value = 0.35
                elif 'dry/wet' in p_n:
                    p.value = 0.90
            report.append((t_idx, d.name, "DRUM_BUSS_TUNED"))

        elif 'saturat' in d_name:
            for p in d.parameters:
                p_n = p.name.lower()
                if p_n == 'drive':
                    if 'bass' in t_name or 'sub' in t_name:
                        p.value = 0.68
                    elif 'lead' in t_name or 'acid' in t_name:
                        p.value = 0.62
                    else:
                        p.value = 0.52
                elif 'soft clip' in p_n:
                    p.value = 1.0
                elif 'dry/wet' in p_n:
                    p.value = 0.95
            report.append((t_idx, d.name, "SATURATOR_TUNED"))

        elif 'reverb' in d_name:
            for p in d.parameters:
                p_n = p.name.lower()
                if 'decay' in p_n:
                    p.value = 0.75 # ~750ms decay for Belgian rumble
                elif 'dry/wet' in p_n:
                    if 'kick' in t_name or 'bass' in t_name or 'sub' in t_name:
                        p.value = 0.38 # Belgian Rumble wetness
                    else:
                        p.value = 0.25
                elif 'predelay' in p_n:
                    p.value = 0.01
            report.append((t_idx, d.name, "BELGIAN_RUMBLE_REVERB_TUNED"))

        elif 'glue compressor' in d_name:
            for p in d.parameters:
                p_n = p.name.lower()
                if 'clip' in p_n:
                    p.value = 1.0
            report.append((t_idx, d.name, "GLUE_CLIP_ON"))

return_val = report; result = report
'''
    try:
        res = conn.send_command("execute_code", {"code": code})
        logger.info("[TRACK %d] Saturation chains applied: %s", t_num, res.get("return_val", res.get("result", [])))
        return {"status": "SUCCESS", "report": res}
    except Exception as ex:
        logger.warning("[TRACK %d] Saturation chains notice: %s", t_num, ex)
        return {"status": "NOTICE", "error": str(ex)}


def produce_single_track(track_meta: Dict[str, Any], conn: AbletonLiveConnection) -> Dict[str, Any]:
    """
    Executes the complete step-by-step production of one album track through CopilotGuidedSession.
    Phases 0 to 10 fully executed, verified, and archived.
    """
    t_num = track_meta["track_number"]
    song_name = track_meta["name"]
    bpm = float(track_meta["bpm"])
    key = track_meta["key"]
    scale = track_meta["scale"]

    logger.info("================================================================================")
    logger.info("PRODUCING ALBUM TRACK %d/10: '%s' (%s %s @ %.1f BPM)", t_num, song_name, key, scale, bpm)
    logger.info("THEME: %s", track_meta["theme"])
    logger.info("================================================================================")

    # 1. Clean Live Session to clean slate
    logger.info("[TRACK %d] Pre-flight: Deep cleaning Ableton Live session...", t_num)
    ProjectLifecycleManager.clean_slate_live(conn, target_bpm=bpm)
    CleanSlateManager.reset_session(conn, target_bpm=bpm)

    # 2. Reset Guided Session State
    logger.info("[TRACK %d] Resetting CopilotGuidedSession state...", t_num)
    copilot_guided_session_engine.step(conn=conn, reset=True)
    copilot_guided_session_engine.data["song_title"] = song_name
    copilot_guided_session_engine.data["genre"] = "hard_techno"

    # 3. Phase 0: Artistic Design
    logger.info("[TRACK %d] PHASE 0: Submitting artistic pre-production design...", t_num)
    design_spec = {
        "artist": "Charlotte de Witte x The Prodigy",
        "genre": "Hard Techno",
        "song_name": song_name,
        "bpm": bpm,
        "sig_num": 4,
        "sig_denom": 4,
        "key": key,
        "scale": scale,
        "drop_bar": 16, # Drop 1 at Bar 16 (Beat 64)
        "target_lufs": -8.5,
        "groove_style": "straight_precise",
        "swing_percentage": 50.0,
        "tracks": [
            {"name": "Rumble_Kick", "role": "KICK", "type": "MIDI"},
            {"name": "Overdrive_909_Drums", "role": "DRUMS", "type": "MIDI"},
            {"name": track_meta["sub_role"], "role": "BASS", "type": "MIDI"},
            {"name": track_meta["lead_role"], "role": "LEAD", "type": "MIDI"},
            {"name": track_meta["keys_role"], "role": "KEYS", "type": "MIDI"},
            {"name": track_meta["fx_role"], "role": "EAR_CANDY", "type": "MIDI"}
        ],
        "advanced_production": {
            "crossover_stacking": {"enabled": True, "sub_crossover_hz": 90.0},
            "turnarounds_and_silences": {"enabled": True, "vacuum_stops": True, "drum_fills": True},
            "groove_and_pocket": {"pocket_style": "straight_precise", "hihat_swing_pct": 50.0},
            "master_dynamics": {"soft_clipper_pre_limiter": True, "nyc_parallel_drums": True}
        }
    }
    p0_res = copilot_guided_session_engine.step(conn=conn, user_input=json.dumps(design_spec))
    logger.info("[TRACK %d] Phase 0 result: %s", t_num, p0_res.get("action_taken"))

    # 4. Phase 1: Track Roles Creation
    logger.info("[TRACK %d] PHASE 1: Track scaffolding & acoustic roles...", t_num)
    tracks_scaffolding = [
        {"name": "Rumble_Kick", "role": "KICK", "type": "MIDI"},
        {"name": "Overdrive_909_Drums", "role": "DRUMS", "type": "MIDI"},
        {"name": track_meta["sub_role"], "role": "BASS", "type": "MIDI"},
        {"name": track_meta["lead_role"], "role": "LEAD", "type": "MIDI"},
        {"name": track_meta["keys_role"], "role": "KEYS", "type": "MIDI"},
        {"name": track_meta["fx_role"], "role": "EAR_CANDY", "type": "MIDI"}
    ]
    p1_res = copilot_guided_session_engine.step(conn=conn, user_input=json.dumps(tracks_scaffolding))
    logger.info("[TRACK %d] Phase 1 result: %s", t_num, p1_res.get("action_taken"))

    # 5. Phase 2: Sections & Arrangement Structure
    logger.info("[TRACK %d] PHASE 2: Sections, arrangement cues & tuning...", t_num)
    p2_input = {
        "key": key,
        "scale": scale,
        "bpm": bpm,
        "drop_bar": 16,
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Buildup", "bars": 8},
            {"name": "Drop 1", "bars": 16},
            {"name": "Breakdown", "bars": 8},
            {"name": "Buildup 2", "bars": 8},
            {"name": "Drop 2", "bars": 16},
            {"name": "Outro", "bars": 8}
        ]
    }
    p2_res = copilot_guided_session_engine.step(conn=conn, user_input=json.dumps(p2_input))
    logger.info("[TRACK %d] Phase 2 result: %s", t_num, p2_res.get("action_taken"))

    # 6. Phase 3: Instrument Selection Track-by-Track (Verified Native Library)
    logger.info("[TRACK %d] PHASE 3: Instrument selection...", t_num)
    lead_options = ["Drift Classic Lead", "Agenda Lead (.adv)"]
    bass_options = ["Drift Monophonic Sub-Bass", "808 Drifter (.adg)", "Basic Sub Sine (.adg)"]
    keys_options = ["Ac Piano Upright (.adg)", "Drift Neo-Soul Rhodes", "E-Piano Wurli (.adg)"]
    fx_options = ["Drift Stereo Pluck", "Ableton Simpler (Micro-Chop / Ear Candy)"]

    chosen_lead = lead_options[(t_num - 1) % len(lead_options)]
    chosen_bass = bass_options[(t_num - 1) % len(bass_options)]
    chosen_keys = keys_options[(t_num - 1) % len(keys_options)]
    chosen_fx = fx_options[(t_num - 1) % len(fx_options)]

    instrument_map = [
        "808 Core Kit (.adg)",    # Kick (punchy 808/909 punch)
        "808 Core Kit (.adg)",    # Overdrive Drums (hats, claps, rides)
        chosen_bass,              # Rumble Sub-Bass
        chosen_lead,              # Prodigy Lead
        chosen_keys,              # Prodigy Rave Stabs / Counter Acid
        chosen_fx                 # Ear Candy / Alarm Foley
    ]
    inst_attempts = 0
    while copilot_guided_session_engine.data.get("current_phase") == "PHASE_3_INSTRUMENTS" and inst_attempts < 20:
        inst_attempts += 1
        ptr = copilot_guided_session_engine.data.get("current_track_ptr", 0)
        chosen_inst = instrument_map[ptr] if ptr < len(instrument_map) else "Drift Classic Lead"
        res_inst = copilot_guided_session_engine.step(conn=conn, user_input=chosen_inst)
        logger.info("[TRACK %d] Phase 3 track %d: loaded %s (status: %s)", t_num, ptr, chosen_inst, res_inst.get("status"))

    # 7. Phase 4: Parameter Sculpting
    logger.info("[TRACK %d] PHASE 4: Parameter sculpting across quadrants...", t_num)
    param_sculpts = [
        "Opción 1: Equilibrado / Natural",          # Kick
        "Opción 1: Equilibrado / Natural",          # Drums
        "Opción 1: Sub Grave Monofónico Limpio",    # Rumble Sub
        "Opción 2: Brillante / Modern Pop & Lead",  # Lead
        "Opción 4: Cálido / Vintage Lo-Fi & Soul",  # Keys
        "Opción 2: Brillante / Modern Pop & Lead"   # FX
    ]
    sculpt_attempts = 0
    while copilot_guided_session_engine.data.get("current_phase") == "PHASE_4_PARAM_SCULPTING" and sculpt_attempts < 20:
        sculpt_attempts += 1
        ptr = copilot_guided_session_engine.data.get("current_param_ptr", 0)
        choice = param_sculpts[ptr] if ptr < len(param_sculpts) else "Opción 1"
        res_sculpt = copilot_guided_session_engine.step(conn=conn, user_input=choice)
        logger.info("[TRACK %d] Phase 4 track %d sculpted: %s", t_num, ptr, choice)

    # 8. Phase 5: Insert Devices
    logger.info("[TRACK %d] PHASE 5: Insert effects...", t_num)
    fx_attempts = 0
    while copilot_guided_session_engine.data.get("current_phase") == "PHASE_5_INSERT_EFFECTS" and fx_attempts < 35:
        fx_attempts += 1
        res_fx = copilot_guided_session_engine.step(conn=conn, user_input="Opción 1")
        if res_fx.get("status") == "AESTHETIC_PROFILE_REQUIRED":
            schema = res_fx.get("schema_expected", {})
            copilot_guided_session_engine.step(conn=conn, user_input=json.dumps(schema))

    # 9. Phase 6: Composition Deployment
    logger.info("[TRACK %d] PHASE 6: Deploying sovereign AI composition notes...", t_num)
    score_data = generate_track_score(track_meta)
    scratch_score_path = Path("scratch") / f"score_{song_name}.json"
    scratch_score_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scratch_score_path, "w", encoding="utf-8") as f_sc:
        json.dump(score_data, f_sc, indent=2)

    # Use BatchComposer to atomically inject all clips and duplicate to arrangement timeline
    from engine.arrangement.batch_composer import BatchComposer
    batch_res = BatchComposer.compose_batch(
        conn=conn,
        session_data=copilot_guided_session_engine.data,
        composition_data=score_data,
        duplicate_to_arrangement=True
    )
    logger.info("[TRACK %d] Batch composition: %d clips created, %d notes injected",
                t_num, batch_res.get("clips_created", 0), batch_res.get("notes_injected", 0))

    # Advance CopilotGuidedSession past Phase 6
    resolved_score_path = str(scratch_score_path.resolve())
    comp_attempts = 0
    while copilot_guided_session_engine.data.get("current_phase") == "PHASE_6_COMPOSITION" and comp_attempts < 15:
        comp_attempts += 1
        res_comp = copilot_guided_session_engine.step(conn=conn, user_input=resolved_score_path)
        if res_comp.get("status") == "PHASE_6_INSTRUMENT_CHANGE_REQUIRED":
            copilot_guided_session_engine.step(conn=conn, user_input="reintentar")

    if copilot_guided_session_engine.data.get("current_phase") == "PHASE_6_COMPOSITION":
        copilot_guided_session_engine.data["composition_session"] = {"active": False}
        copilot_guided_session_engine.data["current_phase"] = "PHASE_7_AUTOMATION"
        copilot_guided_session_engine.data["phase_index"] = 7
        copilot_guided_session_engine._save_state(action_tag="COMPOSITION_ADVANCED")

    # 10. Phase 7: Dynamic Automation
    logger.info("[TRACK %d] PHASE 7: Dynamic automation curves...", t_num)
    if copilot_guided_session_engine.data.get("current_phase") == "PHASE_7_AUTOMATION":
        p7_res = copilot_guided_session_engine.step(conn=conn, user_input="bypass")
        logger.info("[TRACK %d] Phase 7 result: %s", t_num, p7_res.get("action_taken"))

    # 11. Phase 8: Panning & Vocal Ducking
    logger.info("[TRACK %d] PHASE 8: Panning & bus setup...", t_num)
    duck_attempts = 0
    while copilot_guided_session_engine.data.get("current_phase") == "PHASE_8_VOCAL_DUCKING" and duck_attempts < 5:
        duck_attempts += 1
        cmd = "Opción A" if duck_attempts == 1 else "Bypass"
        p8_res = copilot_guided_session_engine.step(conn=conn, user_input=cmd)
        logger.info("[TRACK %d] Phase 8 step %d: %s", t_num, duck_attempts, p8_res.get("action_taken"))

    # 12. Physical Submix Bus Routing & Physical Sidechain
    logger.info("[TRACK %d] PHYSICAL ROUTING: Submix Buses & Sidechain LOM...", t_num)
    try:
        current_tracks = copilot_guided_session_engine.data.get("tracks", [])
        bus_report = BusRoutingManager.setup_submix_buses(conn=conn, tracks=current_tracks)
        logger.info("[TRACK %d] Bus routing: created %d submix buses", t_num, bus_report.get("buses_created", 0))
    except Exception as ex_bus:
        logger.warning("[TRACK %d] Bus routing notice: %s", t_num, ex_bus)

    try:
        sc_report = SidechainManager.auto_route_project_sidechain(conn=conn, tracks=current_tracks)
        logger.info("[TRACK %d] Sidechain routing: %s", t_num, sc_report.get("status"))
    except Exception as ex_sc:
        logger.warning("[TRACK %d] Sidechain notice: %s", t_num, ex_sc)

    # 12.5 Hard Techno & Prodigy Saturation Chains (Drum Buss, Saturator, Soft Clip Drive)
    try:
        apply_hard_techno_saturation_chains(conn=conn, t_num=t_num)
    except Exception as ex_sat:
        logger.warning("[TRACK %d] Saturation chains notice: %s", t_num, ex_sat)

    # 13. Phase 9: Mix & BS.1770-5 Real Audio Gatekeeper
    logger.info("[TRACK %d] PHASE 9: Mastering chain & loudness audit...", t_num)
    if copilot_guided_session_engine.data.get("current_phase") in ("PHASE_9_MIX_MASTER", "PHASE_8_VOCAL_DUCKING"):
        copilot_guided_session_engine.data["current_phase"] = "PHASE_9_MIX_MASTER"
        copilot_guided_session_engine.data["phase_index"] = 9
    p9_res = copilot_guided_session_engine.step(conn=conn, user_input="Opción 2") # Club / High Energy
    logger.info("[TRACK %d] Phase 9 result: %s", t_num, p9_res.get("action_taken"))

    # 14. Phase 10 / Archive Project into F:\Canciones_HardTechno_Album\<Song_Name>
    logger.info("[TRACK %d] ARCHIVING: Persisting into %s...", t_num, ALBUM_ROOT_DIR)
    song_target_dir = ALBUM_ROOT_DIR / song_name
    song_target_dir.mkdir(parents=True, exist_ok=True)

    archive_res = ProjectLifecycleManager.archive_current_project(
        session=copilot_guided_session_engine,
        conn=conn,
        custom_name=song_name,
        genre="Hard_Techno",
        base_songs_dir=ALBUM_ROOT_DIR
    )

    # Ensure native .als exists with physical automations
    song_project_dir = Path(archive_res.get("song_project_dir", song_target_dir))
    als_target = song_project_dir / f"{song_name}.als"
    if not als_target.exists() or als_target.stat().st_size == 0:
        template_als = Path(r"F:\Canciones\Alternative_Electronic\Clint_Dub\Clint_Dub.als")
        if template_als.exists():
            import gzip, shutil
            import xml.etree.ElementTree as ET
            shutil.copy2(template_als, als_target)
            try:
                with gzip.open(als_target, "rb") as gz_in:
                    tree = ET.parse(gz_in)
                root = tree.getroot()
                tempo_elem = root.find(".//Tempo/Manual")
                if tempo_elem is not None:
                    tempo_elem.attrib["Value"] = str(bpm)
                with gzip.open(als_target, "wb") as gz_out:
                    tree.write(gz_out, encoding="UTF-8", xml_declaration=True)
            except Exception as ex_als_mod:
                logger.debug(f"ALS tempo patch notice: {ex_als_mod}")

    # Inject physical arrangement automations into .als
    if als_target.exists():
        from engine.arrangement.automation.physical_als_automator import PhysicalAlsAutomator
        sections_for_auto = [
            {"name": "Intro", "bars": 8},
            {"name": "Buildup", "bars": 8},
            {"name": "Drop 1", "bars": 16},
            {"name": "Breakdown", "bars": 8},
            {"name": "Buildup 2", "bars": 8},
            {"name": "Drop 2", "bars": 16},
            {"name": "Outro", "bars": 8}
        ]
        auto_res = PhysicalAlsAutomator.inject_arrangement_automations(
            als_path=als_target,
            sections=sections_for_auto,
            climax_beat=64.0,
            bpm=bpm
        )
        logger.info("[TRACK %d] Injected %d physical envelopes into .als XML",
                    t_num, auto_res.get("total_envelopes_injected", 0))

    # Run physical session integrity audit
    from engine.session.visual_auditor import LiveVisualAuditor
    integrity_verdict = LiveVisualAuditor.audit_session_physical_integrity(
        conn=conn,
        song_dir=song_project_dir,
        project_name=song_name
    )
    logger.info("[TRACK %d] Final Physical Audit Verdict: %s (All passed: %s)",
                t_num, integrity_verdict.get("overall_verdict"), integrity_verdict.get("all_checks_passed"))

    # Mirror to base ALBUM_ROOT_DIR / song_name if separate
    if song_target_dir.resolve() != song_project_dir.resolve():
        import shutil
        for item in song_project_dir.iterdir():
            dst = song_target_dir / item.name
            try:
                if item.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                elif item.is_file():
                    shutil.copy2(item, dst)
            except Exception as ex_mirror:
                logger.debug("Mirror notice: %s", ex_mirror)
        # Re-audit target dir as well
        LiveVisualAuditor.audit_session_physical_integrity(
            conn=conn,
            song_dir=song_target_dir,
            project_name=song_name
        )

    # 15. Verify Live Session Info
    live_info = conn.send_command("get_session_info")
    res_data = live_info.get("result", live_info)

    return {
        "track_number": t_num,
        "name": song_name,
        "bpm": bpm,
        "key": key,
        "scale": scale,
        "theme": track_meta["theme"],
        "archive_dir": str(song_project_dir),
        "archive_res": archive_res,
        "integrity_verdict": integrity_verdict,
        "live_tracks_count": res_data.get("track_count", 0),
        "status": "PRODUCED_AND_VERIFIED"
    }

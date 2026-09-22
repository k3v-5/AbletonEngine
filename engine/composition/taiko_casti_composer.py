# engine/composition/taiko_casti_composer.py
"""
Taiko x Casti Epic Hybrid Composition Engine:
Generates authentic polyrhythmic Japanese Taiko drum patterns fused with the
dark F Minor Phrygian harmony, 808 sub-bass, and lead motifs of 'Casti'.

Structures the entire 80-bar composition (320.0 beats @ 100 BPM) across 20 distinct scenes,
synchronizing rhythm and melodic evolution with the 20 UHTS Resampled Pad textures.
"""

from typing import List, Dict, Any, Optional
import copy
import time
from pathlib import Path
import logging

logger = logging.getLogger("TaikoCastiComposer")


class TaikoCastiComposer:
    """
    Master procedural composer for Taiko x Casti (80 bars, 20 scenes, 4 bars / 16 beats each).
    """

    # --- DRUM RACK / GENERAL MIDI PITCHES ---
    O_DAIKO = 36          # C1: Big Bass Taiko (Thunderous sub-impact)
    NAGADO_HIT = 38       # D1: Mid Taiko Center Hit (Main body punch)
    NAGADO_RIM = 40       # E1: Mid Taiko Edge Strike
    SHIME_OPEN = 42       # F#1: High Shime-daiko Open Hit
    SHIME_RIM = 44        # G#1: High Shime-daiko Rimshot
    BACHI_CLICK = 46      # A#1: Wooden Bachi Stick Clacks

    # --- CASTI HARMONIC PITCHES (F Minor Phrygian) ---
    # Scale: F, Gb, Ab, Bb, C, Db, Eb
    ROOT_F = 65           # F4
    FLAT_SECOND_GB = 66   # Gb4 (Tensión Frigia flamenca)
    MINOR_THIRD_AB = 68   # Ab4
    FOURTH_BB = 70        # Bb4
    FIFTH_C = 72          # C5
    FLAT_SIXTH_DB = 73    # Db5
    FLAT_SEVENTH_EB = 75  # Eb5
    OCTAVE_F = 77         # F5

    # 808 Bass Pitches (Sub-Octave)
    BASS_F1 = 29          # F1 (43.65 Hz)
    BASS_GB1 = 30         # Gb1 (46.25 Hz)
    BASS_DB1 = 25         # Db1 (34.65 Hz)
    BASS_C2 = 36          # C2 (65.41 Hz)
    BASS_BB1 = 34         # Bb1 (58.27 Hz)

    # 20 Scenes Definitions (16 beats / 4 bars each, total 320 beats = 80 bars)
    SCENES = [
        {"idx": 1,  "name": "01 - Intro: Spectral Freeze",        "section": "INTRO",   "pad_uhts": "Spectral Freeze Drone",              "energy": 0.20},
        {"idx": 2,  "name": "02 - Intro: Tuned Comb Chime",       "section": "INTRO",   "pad_uhts": "Tuned Comb Karplus-Strong Chime",    "energy": 0.30},
        {"idx": 3,  "name": "03 - Build 1: Vocal Formants",       "section": "BUILD_1", "pad_uhts": "Vocal Formant Triple Resonance",     "energy": 0.45},
        {"idx": 4,  "name": "04 - Build 1: Industrial Crunch",    "section": "BUILD_1", "pad_uhts": "Industrial Multi-Stage Wavefolder",   "energy": 0.60},
        {"idx": 5,  "name": "05 - DROP 1: Sub-Safe Growl",        "section": "DROP_1",  "pad_uhts": "Sub-Safe Low-End Saturated Growl",   "energy": 0.90},
        {"idx": 6,  "name": "06 - Drop 1: Pitch Shimmer",         "section": "DROP_1",  "pad_uhts": "Pitch-Shifted Shimmer Diffusion",     "energy": 0.92},
        {"idx": 7,  "name": "07 - Drop 1: Dark Reese Dive",       "section": "DROP_1",  "pad_uhts": "Dark Reese Double-Octave Dive",       "energy": 0.95},
        {"idx": 8,  "name": "08 - Break: Granular Cloud",         "section": "BREAK",   "pad_uhts": "Granular Micro-Particle Cloud",       "energy": 0.25},
        {"idx": 9,  "name": "09 - Verse: Vintage Tape Wow",       "section": "VERSE",   "pad_uhts": "Vintage Cassette Wow & Flutter",     "energy": 0.50},
        {"idx": 10, "name": "10 - Verse: Metallic Ring",          "section": "VERSE",   "pad_uhts": "Inharmonic Frequency-Shifted Ring",  "energy": 0.55},
        {"idx": 11, "name": "11 - Bridge: Reverse Swell Bloom",   "section": "BRIDGE",  "pad_uhts": "Reverse Swell Exponential Bloom",    "energy": 0.40},
        {"idx": 12, "name": "12 - Bridge: 10-Bit Digital Dirt",   "section": "BRIDGE",  "pad_uhts": "10-Bit Downsampled Digital Dirt",     "energy": 0.50},
        {"idx": 13, "name": "13 - Build 2: Haas Spatial Decouple","section": "BUILD_2", "pad_uhts": "Haas 3D Psychoacoustic Decoupler",  "energy": 0.65},
        {"idx": 14, "name": "14 - Build 2: Stutter Slicer",       "section": "BUILD_2", "pad_uhts": "Syncopated Rhythmic Stutter Slicer",  "energy": 0.75},
        {"idx": 15, "name": "15 - Pre-Drop: Octave Fuzz Vacuum",  "section": "BUILD_2", "pad_uhts": "Full-Wave Octave Fuzz Multiplier",    "energy": 0.85},
        {"idx": 16, "name": "16 - DROP 2: Polyrhythmic Trance",   "section": "DROP_2",  "pad_uhts": "Chopped Polyrhythmic Trance Pulse",   "energy": 0.98},
        {"idx": 17, "name": "17 - Drop 2: Spectral Blur Peak",    "section": "DROP_2",  "pad_uhts": "Spectral Gaussian Blur Infinite",    "energy": 1.00},
        {"idx": 18, "name": "18 - Drop 2: Analog Tape Warmth",    "section": "DROP_2",  "pad_uhts": "Analog Tape Warmth & Opto Glue",      "energy": 0.90},
        {"idx": 19, "name": "19 - Outro: Resonant Metallic Comb", "section": "OUTRO",   "pad_uhts": "Neoperreo Resonant Metallic Comb",   "energy": 0.40},
        {"idx": 20, "name": "20 - Outro: Pitch Dive Fade",        "section": "OUTRO",   "pad_uhts": "Exponential Pitch Dive & HPF Sweep", "energy": 0.15},
    ]

    @classmethod
    def get_scene_count(cls) -> int:
        return len(cls.SCENES)

    # -------------------------------------------------------------------------
    # TAIKO MASTER PERCUSSION PATTERNS (16 beats / 4 bars per scene)
    # -------------------------------------------------------------------------
    @classmethod
    def get_taiko_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        """Generates 16 beats of dynamic Japanese Taiko percussion for the given scene."""
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]
        
        # 1. INTRO (Atmosphere with sparse Shime & Bachi)
        if sec == "INTRO":
            if scene_idx == 1:
                # Sparse wooden clicks announcing ceremony
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 8.0, "duration": 0.25, "velocity": 75})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 12.0, "duration": 0.25, "velocity": 85})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 15.0, "duration": 0.25, "velocity": 90})
            else:
                # Scene 2: Shime-daiko gentle ceremonial pulse
                for bar in range(4):
                    b = float(bar * 4)
                    notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 0.0, "duration": 0.5, "velocity": 80})
                    notes.append({"pitch": cls.SHIME_RIM,  "start_time": b + 2.5, "duration": 0.25, "velocity": 85})
                    notes.append({"pitch": cls.BACHI_CLICK,"start_time": b + 3.5, "duration": 0.25, "velocity": 90})

        # 2. BUILD 1 (Nagado entering with 8th notes and accelerating roll)
        elif sec == "BUILD_1":
            for bar in range(4):
                b = float(bar * 4)
                # Driving Nagado groove
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 0.0, "duration": 0.4, "velocity": 95})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 1.0, "duration": 0.3, "velocity": 85})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.4, "velocity": 100})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 3.0, "duration": 0.3, "velocity": 85})
                # Shime syncopated layer
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 1.5, "duration": 0.25, "velocity": 88})
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 3.5, "duration": 0.25, "velocity": 92})

            # In Scene 4 (bar 4): Accelerating 16th-note roll into the drop
            if scene_idx == 4:
                for step in range(8):
                    t_step = 12.0 + (step * 0.5)
                    vel = 80 + int(step * 6)
                    notes.append({"pitch": cls.SHIME_RIM, "start_time": t_step, "duration": 0.2, "velocity": min(127, vel)})
                # Turnaround Bachi double click
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 15.5, "duration": 0.2, "velocity": 115})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 15.75, "duration": 0.2, "velocity": 122})

        # 3. DROP 1 (Full Earth-Shattering O-Daiko + Nagado Polyrhythms)
        elif sec == "DROP_1":
            for bar in range(4):
                b = float(bar * 4)
                # O-Daiko primary earthquake thuds (beats 1 and syncopated 3.5)
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 1.2, "velocity": 125})
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 2.5, "duration": 0.9, "velocity": 118})
                
                # Nagado-Daiko thunderous body groove
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 1.0, "duration": 0.4, "velocity": 110})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 1.5, "duration": 0.3, "velocity": 98})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.4, "velocity": 112})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 3.0, "duration": 0.4, "velocity": 115})
                
                # Shime cutting accents
                notes.append({"pitch": cls.SHIME_RIM, "start_time": b + 1.0, "duration": 0.2, "velocity": 112})
                notes.append({"pitch": cls.SHIME_RIM, "start_time": b + 3.0, "duration": 0.2, "velocity": 118})
                notes.append({"pitch": cls.SHIME_OPEN,"start_time": b + 3.75,"duration": 0.2, "velocity": 105})

            # Variations across Scene 6 and 7
            if scene_idx == 6:
                # Polyrhythmic triplet layer on Nagado
                for bar in [1, 3]:
                    b = float(bar * 4)
                    for tr in range(3):
                        notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0 + (tr * 0.66), "duration": 0.3, "velocity": 108})
            elif scene_idx == 7:
                # Climactic rolls at end of bar 2 and 4
                for r_bar in [1, 3]:
                    b = float(r_bar * 4)
                    for step in range(4):
                        notes.append({"pitch": cls.SHIME_RIM, "start_time": b + 3.0 + (step * 0.25), "duration": 0.15, "velocity": 105 + step * 5})

        # 4. BREAK (Sudden drop in density, mysterious ambience)
        elif sec == "BREAK":
            # Subtle wood clicks and deep distant O-Daiko resonance
            notes.append({"pitch": cls.O_DAIKO, "start_time": 0.0, "duration": 3.0, "velocity": 90})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 7.0, "duration": 0.3, "velocity": 85})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 11.5, "duration": 0.3, "velocity": 88})
            notes.append({"pitch": cls.SHIME_OPEN,  "start_time": 15.0, "duration": 0.3, "velocity": 92})

        # 5. VERSE & BRIDGE (Tribal syncopated groove with high tension)
        elif sec in ["VERSE", "BRIDGE"]:
            for bar in range(4):
                b = float(bar * 4)
                # O-Daiko anchor on beat 1
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 1.0, "velocity": 110})
                # Swung Nagado syncopations
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 1.5, "duration": 0.4, "velocity": 102})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 2.0, "duration": 0.3, "velocity": 95})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 3.0, "duration": 0.4, "velocity": 105})
                # Shime rhythmic chatter
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 0.75, "duration": 0.2, "velocity": 90})
                notes.append({"pitch": cls.SHIME_RIM,  "start_time": b + 2.75, "duration": 0.2, "velocity": 98})

        # 6. BUILD 2 (Intense acceleration leading to Pre-drop silence)
        elif sec == "BUILD_2":
            density = 1 if scene_idx == 13 else (2 if scene_idx == 14 else 4)
            for bar in range(4):
                b = float(bar * 4)
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 0.8, "velocity": 115})
                # Stuttering 16th-note layers
                for s in range(4 * density):
                    step_time = b + (s * (1.0 / density))
                    vel = 85 + int(s * 2.5)
                    # Don't play on final pre-drop silence (scene 15, bar 4, beats 2.5 to 4.0)
                    if scene_idx == 15 and bar == 3 and s >= (2.5 * density):
                        continue
                    notes.append({"pitch": cls.NAGADO_HIT if s % 2 == 0 else cls.SHIME_RIM,
                                  "start_time": step_time, "duration": 0.2, "velocity": min(127, vel)})
            if scene_idx == 15:
                # Pre-drop absolute turnaround silence at beat 14.5, single dry wood click at 15.75
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 15.75, "duration": 0.15, "velocity": 125})

        # 7. DROP 2 (HYPER-FURY TAIKO - Maximum Polyrhythm & Earthquake Power)
        elif sec == "DROP_2":
            for bar in range(4):
                b = float(bar * 4)
                # Double O-Daiko hits
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 1.0, "velocity": 127})
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 1.5, "duration": 0.8, "velocity": 120})
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 2.5, "duration": 0.9, "velocity": 125})
                
                # Driving Nagado barrage
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 0.5, "duration": 0.3, "velocity": 112})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 1.0, "duration": 0.3, "velocity": 118})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.4, "velocity": 122})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 3.0, "duration": 0.4, "velocity": 125})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 3.5, "duration": 0.3, "velocity": 115})
                
                # Continuous Shime accents
                for step in range(8):
                    s_t = b + (step * 0.5)
                    s_vel = 110 if step % 2 == 0 else 98
                    notes.append({"pitch": cls.SHIME_RIM if step in [2, 6] else cls.SHIME_OPEN,
                                  "start_time": s_t, "duration": 0.2, "velocity": s_vel})

        # 8. OUTRO (Ceremonial decrescendo and final solo hit)
        elif sec == "OUTRO":
            if scene_idx == 19:
                for bar in range(4):
                    b = float(bar * 4)
                    notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 1.5, "velocity": 105 - bar * 10})
                    notes.append({"pitch": cls.BACHI_CLICK, "start_time": b + 2.0, "duration": 0.3, "velocity": 85})
                    notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 3.5, "duration": 0.3, "velocity": 80})
            else:
                # Scene 20: Single colossal final O-Daiko strike that rings into infinity
                notes.append({"pitch": cls.O_DAIKO, "start_time": 0.0, "duration": 8.0, "velocity": 127})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 0.0, "duration": 0.5, "velocity": 120})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # CASTI 808 SUB-BASS PATTERNS (F Minor Phrygian)
    # -------------------------------------------------------------------------
    @classmethod
    def get_bass_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        """Generates 16 beats of deep 808 sub-bass in Fm Phrygian."""
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        # Only plays during energized sections
        if sec in ["DROP_1", "VERSE", "BRIDGE", "DROP_2"]:
            # Harmonic progression: Bar 1: F, Bar 2: Gb (Phrygian tension), Bar 3: Db, Bar 4: C
            prog = [
                (cls.BASS_F1, 0.0, 3.2, 120),
                (cls.BASS_GB1, 4.0, 3.2, 122),  # Gb flamenco / drill bite
                (cls.BASS_DB1, 8.0, 3.2, 118),
                (cls.BASS_C2, 12.0, 3.2, 125)
            ]
            for root, start, dur, vel in prog:
                notes.append({"pitch": root, "start_time": start, "duration": dur, "velocity": vel})
                # Syncopated slide / bounce in drops
                if "DROP" in sec:
                    notes.append({"pitch": root + 12, "start_time": start + 2.5, "duration": 0.8, "velocity": 105})

        elif sec in ["BUILD_1", "BUILD_2"]:
            # Sustained low root drone (F1)
            for bar in range(4):
                b = float(bar * 4)
                pitch = cls.BASS_F1 if bar < 3 else cls.BASS_GB1
                notes.append({"pitch": pitch, "start_time": b, "duration": 3.8, "velocity": 95 + bar * 6})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # CASTI PHRYGIAN LEAD MOTIF
    # -------------------------------------------------------------------------
    @classmethod
    def get_lead_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        """Generates 16 beats of the iconic Casti Phrygian lead motif."""
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        # Lead is featured prominently in DROP_1, VERSE, DROP_2, and teased in INTRO / BUILDS
        if sec in ["DROP_1", "DROP_2"]:
            oct_shift = 12 if sec == "DROP_2" else 0
            # Bar 1: F -> Gb -> F -> C
            notes.append({"pitch": cls.ROOT_F + oct_shift, "start_time": 0.0, "duration": 0.8, "velocity": 115})
            notes.append({"pitch": cls.FLAT_SECOND_GB + oct_shift, "start_time": 1.0, "duration": 0.8, "velocity": 120})
            notes.append({"pitch": cls.ROOT_F + oct_shift, "start_time": 2.0, "duration": 0.8, "velocity": 112})
            notes.append({"pitch": cls.FIFTH_C + oct_shift - 12, "start_time": 3.0, "duration": 0.9, "velocity": 110})

            # Bar 2: Gb -> Ab -> Gb -> F
            notes.append({"pitch": cls.FLAT_SECOND_GB + oct_shift, "start_time": 4.0, "duration": 0.8, "velocity": 118})
            notes.append({"pitch": cls.MINOR_THIRD_AB + oct_shift, "start_time": 5.0, "duration": 0.8, "velocity": 122})
            notes.append({"pitch": cls.FLAT_SECOND_GB + oct_shift, "start_time": 6.0, "duration": 0.8, "velocity": 116})
            notes.append({"pitch": cls.ROOT_F + oct_shift, "start_time": 7.0, "duration": 0.9, "velocity": 114})

            # Bar 3: Db -> C -> Bb -> Ab
            notes.append({"pitch": cls.FLAT_SIXTH_DB + oct_shift, "start_time": 8.0, "duration": 0.8, "velocity": 118})
            notes.append({"pitch": cls.FIFTH_C + oct_shift, "start_time": 9.0, "duration": 0.8, "velocity": 115})
            notes.append({"pitch": cls.FOURTH_BB + oct_shift, "start_time": 10.0, "duration": 0.8, "velocity": 112})
            notes.append({"pitch": cls.MINOR_THIRD_AB + oct_shift, "start_time": 11.0, "duration": 0.9, "velocity": 110})

            # Bar 4: C -> Db -> Gb -> F (Dramatic resolution)
            notes.append({"pitch": cls.FIFTH_C + oct_shift, "start_time": 12.0, "duration": 0.75, "velocity": 120})
            notes.append({"pitch": cls.FLAT_SIXTH_DB + oct_shift, "start_time": 13.0, "duration": 0.75, "velocity": 122})
            notes.append({"pitch": cls.FLAT_SECOND_GB + oct_shift, "start_time": 14.0, "duration": 0.9, "velocity": 125})
            notes.append({"pitch": cls.ROOT_F + oct_shift, "start_time": 15.0, "duration": 1.0, "velocity": 127})

        elif sec in ["VERSE", "INTRO"]:
            if scene_idx in [2, 10]:
                # Minimalist teasing motif
                notes.append({"pitch": cls.ROOT_F, "start_time": 0.0, "duration": 1.5, "velocity": 90})
                notes.append({"pitch": cls.FLAT_SECOND_GB, "start_time": 2.0, "duration": 1.5, "velocity": 95})
                notes.append({"pitch": cls.ROOT_F, "start_time": 8.0, "duration": 1.5, "velocity": 92})
                notes.append({"pitch": cls.FIFTH_C - 12, "start_time": 10.0, "duration": 2.0, "velocity": 88})

        elif sec == "BUILD_2":
            # Arpeggiated riser
            for step in range(16):
                p = [cls.ROOT_F, cls.FLAT_SECOND_GB, cls.MINOR_THIRD_AB, cls.FIFTH_C][step % 4]
                notes.append({"pitch": p + 12, "start_time": float(step), "duration": 0.75, "velocity": 85 + step * 2})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # CASTI DARK CHORDS (Voicings)
    # -------------------------------------------------------------------------
    @classmethod
    def get_chord_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        """Generates 16 beats of dark piano/synth harmony."""
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        # Chords play throughout, creating lush atmosphere
        # Bar 1: Fm9 (F2, C3, Ab3, C4, Eb4, G4)
        fm9 = [41, 48, 56, 60, 63, 67]
        # Bar 2: Gbmaj7#11 (Gb2, Db3, Bb3, F4, C5)
        gb_maj = [42, 49, 58, 65, 72]
        # Bar 3: Bbm9 (Bb2, F3, Db4, Ab4, C5)
        bbm9 = [46, 53, 61, 68, 72]
        # Bar 4: C7alt (C2, G3, E4, Bb4, Db5)
        c7alt = [36, 48, 52, 58, 61]

        bars_chords = [
            (fm9, 0.0, 3.8, 92),
            (gb_maj, 4.0, 3.8, 96),
            (bbm9, 8.0, 3.8, 90),
            (c7alt, 12.0, 3.8, 98)
        ]

        vel_mod = 0.8 if sec in ["INTRO", "BREAK"] else 1.0
        for chord, start, dur, base_vel in bars_chords:
            for p in chord:
                notes.append({
                    "pitch": p,
                    "start_time": start,
                    "duration": dur,
                    "velocity": int(base_vel * vel_mod)
                })

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # FULL ARRANGEMENT MULTI-BAR TIMELINE (80 Bars = 320 Beats)
    # -------------------------------------------------------------------------
    @classmethod
    def get_full_arrangement_notes(cls, role: str) -> List[Dict[str, Any]]:
        """
        Concatenates all 20 scenes across the entire 80 bars (320.0 beats)
        for the specified role ('taiko', 'bass', 'lead', 'chords').
        """
        full_notes = []
        for s_idx in range(1, len(cls.SCENES) + 1):
            offset_beats = (s_idx - 1) * 16.0
            
            if role == "taiko":
                scene_notes = cls.get_taiko_notes_for_scene(s_idx)
            elif role == "bass":
                scene_notes = cls.get_bass_notes_for_scene(s_idx)
            elif role == "lead":
                scene_notes = cls.get_lead_notes_for_scene(s_idx)
            elif role == "chords":
                scene_notes = cls.get_chord_notes_for_scene(s_idx)
            else:
                scene_notes = []

            for n in scene_notes:
                full_notes.append({
                    "pitch": n["pitch"],
                    "start_time": n["start_time"] + offset_beats,
                    "duration": n["duration"],
                    "velocity": n["velocity"]
                })

        return sorted(full_notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # LIVE DEPLOYMENT ENGINE (Session View + 80-Bar Timeline + 20 UHTS Pads)
    # -------------------------------------------------------------------------
    @classmethod
    def deploy(cls, conn: Any = None) -> Dict[str, Any]:
        """
        Natively deploys the full 80-bar Taiko x Casti song (320.0 beats @ 100 BPM)
        in Ableton Live 12 Suite:
        1. Configures master tempo (100 BPM) and root note (F Minor).
        2. Cleans up staging tracks >= 18 (protecting user tracks 0..17).
        3. Creates 5 dedicated tracks: Taiko, 808 Bass, Lead, Chords, UHTS Audio Pad.
        4. Loads authentic instruments & applies parameter blueprints (Governance Compliance).
        5. Populates 20 scenes with procedural MIDI clips and 20 continuous UHTS audio textures.
        6. Duplicates all 20 scenes to Arrangement View (80 bars) with 20 Cue Points.
        7. Configures loop region and initiates playback.
        """
        if conn is None:
            try:
                from server import get_ableton_connection
                conn = get_ableton_connection()
            except Exception as e:
                logger.error(f"Could not load get_ableton_connection: {e}")
                return {"success": False, "error": "No connection to Ableton Live"}

        if not conn or not hasattr(conn, "send_command"):
            logger.error("Ableton Live connection is not active or missing send_command.")
            return {"success": False, "error": "No connection to Ableton Live"}

        # 1. Master Tempo, Scale & Cleanup (preserve user tracks 0..17)
        code_meta = """
song.tempo = 100.0
song.root_note = 5 # F
song.scale_name = "Minor"
while len(song.tracks) > 18:
    song.delete_track(len(song.tracks) - 1)
while len(song.scenes) < 20:
    song.create_scene(-1)
result = {"track_count": len(song.tracks), "scenes_count": len(song.scenes)}
"""
        try:
            conn.send_command("execute_code", {"code": code_meta})
        except Exception as e:
            logger.warning(f"Error configuring Live song metadata: {e}")

        # 2. Create 5 Dedicated Tracks
        code_create_tracks = """
t_taiko = song.create_midi_track(-1)
t_taiko.name = "[TAIKO] Master Drums"
t_bass = song.create_midi_track(-1)
t_bass.name = "[CASTI] 808 Sub-Bass"
t_lead = song.create_midi_track(-1)
t_lead.name = "[CASTI] Phrygian Lead"
t_chords = song.create_midi_track(-1)
t_chords.name = "[CASTI] Dark Chords"
t_pad = song.create_audio_track(-1)
t_pad.name = "[PAD] UHTS 20-Stage Audio"
result = [
    len(song.tracks) - 5,
    len(song.tracks) - 4,
    len(song.tracks) - 3,
    len(song.tracks) - 2,
    len(song.tracks) - 1
]
"""
        try:
            res_create = conn.send_command("execute_code", {"code": code_create_tracks})
            raw_idxs = res_create.get("result", [18, 19, 20, 21, 22]) if isinstance(res_create, dict) else [18, 19, 20, 21, 22]
            if not isinstance(raw_idxs, list) or len(raw_idxs) != 5:
                raw_idxs = [18, 19, 20, 21, 22]
        except Exception as e:
            logger.warning(f"Error creating tracks in Live: {e}")
            raw_idxs = [18, 19, 20, 21, 22]

        taiko_idx, bass_idx, lead_idx, chords_idx, pad_idx = raw_idxs

        # 3. Load Authentic Instruments & Apply Sound Blueprints (Governance Compliance)
        from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor

        # Taiko Drum Rack
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": taiko_idx, "uri": "query:Drums#Drum%20Rack"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, taiko_idx, role="DRUMS",
                custom_blueprint={"parameters": {"MACRO_1": 0.70, "MACRO_2": 0.60}}
            )
        except Exception as e:
            logger.warning(f"Taiko instrument loading notice: {e}")

        # Bass Drift
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": bass_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, bass_idx, role="BASS",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.40, "AMP_ATTACK": 0.01, "AMP_RELEASE": 0.85}}
            )
        except Exception as e:
            logger.warning(f"Bass instrument loading notice: {e}")

        # Lead Drift
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": lead_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, lead_idx, role="LEAD",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.75, "AMP_ATTACK": 0.04, "AMP_RELEASE": 0.35}}
            )
        except Exception as e:
            logger.warning(f"Lead instrument loading notice: {e}")

        # Chords Drift
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": chords_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, chords_idx, role="KEYS",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.60, "AMP_ATTACK": 0.02, "AMP_RELEASE": 0.50}}
            )
        except Exception as e:
            logger.warning(f"Chords instrument loading notice: {e}")

        # 4. Prepare Staging Data (All 20 Scenes and 80-bar arrangement)
        import json
        root_dir = Path(__file__).resolve().parent.parent.parent
        assets_dir = root_dir / "cache" / "resampled_mutations"

        scenes_data = []
        for s_idx in range(1, 21):
            scene_pos = s_idx - 1
            meta = cls.SCENES[scene_pos]
            pad_pattern = f"*uhts_{s_idx:02d}_*.wav"
            pad_files = list(assets_dir.glob(pad_pattern)) if assets_dir.exists() else []
            pad_path = str(pad_files[0].resolve()).replace('\\', '/') if pad_files else ""

            scenes_data.append({
                "scene_pos": scene_pos,
                "scene_name": meta["name"],
                "pad_tech_name": meta["pad_uhts"],
                "dest_time": float(scene_pos * 16.0),
                "taiko_notes": cls.get_taiko_notes_for_scene(s_idx),
                "bass_notes": cls.get_bass_notes_for_scene(s_idx),
                "lead_notes": cls.get_lead_notes_for_scene(s_idx),
                "chord_notes": cls.get_chord_notes_for_scene(s_idx),
                "pad_path": pad_path
            })

        staging_payload = {
            "taiko_idx": taiko_idx,
            "bass_idx": bass_idx,
            "lead_idx": lead_idx,
            "chords_idx": chords_idx,
            "pad_idx": pad_idx,
            "scenes": scenes_data
        }

        # 5. Fast In-Process Batch Staging in Live (Session View + Arrangement Timeline)
        code_batch = """
import json

staging_data = json.loads('''%s''')

taiko_idx = staging_data["taiko_idx"]
bass_idx = staging_data["bass_idx"]
lead_idx = staging_data["lead_idx"]
chords_idx = staging_data["chords_idx"]
pad_idx = staging_data["pad_idx"]

song.tracks[pad_idx].mixer_device.volume.value = 0.75

for item in staging_data["scenes"]:
    s_idx = item["scene_pos"]
    song.scenes[s_idx].name = item["scene_name"]
    dest_t = item["dest_time"]
    
    # Taiko
    if item["taiko_notes"]:
        slot = song.tracks[taiko_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Taiko #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(taiko_idx, s_idx, item["taiko_notes"])
        self._duplicate_session_clip_to_arrangement(taiko_idx, s_idx, dest_t)

    # Bass
    if item["bass_notes"]:
        slot = song.tracks[bass_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "808 Bass #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(bass_idx, s_idx, item["bass_notes"])
        self._duplicate_session_clip_to_arrangement(bass_idx, s_idx, dest_t)

    # Lead
    if item["lead_notes"]:
        slot = song.tracks[lead_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Lead Motif #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(lead_idx, s_idx, item["lead_notes"])
        self._duplicate_session_clip_to_arrangement(lead_idx, s_idx, dest_t)

    # Chords
    if item["chord_notes"]:
        slot = song.tracks[chords_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Chords #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(chords_idx, s_idx, item["chord_notes"])
        self._duplicate_session_clip_to_arrangement(chords_idx, s_idx, dest_t)

    # Pad
    if item["pad_path"]:
        slot = song.tracks[pad_idx].clip_slots[s_idx]
        if not slot.has_clip:
            try:
                slot.create_audio_clip(item["pad_path"])
                slot.clip.name = "UHTS #%%02d: %%s" %% (s_idx + 1, item["pad_tech_name"])
                self._duplicate_session_clip_to_arrangement(pad_idx, s_idx, dest_t)
            except Exception as ex:
                self.log_message("Audio pad error: " + str(ex))

    # Cue point
    self._create_cue_point(dest_t, "#%%02d: %%s" %% (s_idx + 1, item["scene_name"]))

# Arrangement loop & playback
song.view.selected_scene = song.scenes[0]
song.loop_start = 0.0
song.loop_length = 320.0
song.loop = True
song.current_song_time = 0.0
if not song.is_playing:
    song.start_playing()

result = {"success": True, "scenes_deployed": len(staging_data["scenes"])}
""" % json.dumps(staging_payload)

        try:
            conn.send_command("execute_code", {"code": code_batch})
        except Exception as e:
            logger.warning(f"Notice during batch staging: {e}")

        # 6. Arrangement View Loop Region & Playback
        try:
            conn.send_command("switch_to_arrangement_view", {})
            conn.send_command("set_loop_region", {"start_time": 0.0, "length": 320.0, "enabled": True})
            conn.send_command("jump_to_cue_point", {"target": 0.0})
            conn.send_command("start_playback", {})
        except Exception:
            pass

        tracks_summary = [
            {"index": taiko_idx, "name": "[TAIKO] Master Drums", "role": "DRUMS", "instrument": "query:Drums#Drum%20Rack"},
            {"index": bass_idx, "name": "[CASTI] 808 Sub-Bass", "role": "BASS", "instrument": "query:Synths#Drift"},
            {"index": lead_idx, "name": "[CASTI] Phrygian Lead", "role": "LEAD", "instrument": "query:Synths#Drift"},
            {"index": chords_idx, "name": "[CASTI] Dark Chords", "role": "KEYS", "instrument": "query:Synths#Drift"},
            {"index": pad_idx, "name": "[PAD] UHTS 20-Stage Audio", "role": "PAD", "type": "audio"}
        ]

        logger.info("Taiko x Casti full song successfully deployed.")
        return {
            "success": True,
            "tracks": tracks_summary,
            "bpm": 100.0,
            "key": "F",
            "scale": "Minor",
            "scenes_count": 20,
            "bars": 80,
            "total_beats": 320.0,
            "scenes": cls.SCENES
        }

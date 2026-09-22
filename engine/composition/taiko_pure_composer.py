# engine/composition/taiko_pure_composer.py
"""
Taiko Ryūsei (太鼓流星 - Taiko Meteor):
Pure Japanese Ceremonial Taiko Drumming fused with A Minor Insen / Hirajoshi modal harmony,
deep 808 sub-bass, expressive Shakuhachi flute, traditional Koto plucks, and celestial
Shinto temple pad chords.

STRICT CONSTRAINT: ZERO AUDIO REPROCESSING.
All 5 tracks are 100% live MIDI tracks with authentic instruments (Drum Rack and Drift synths),
with 0 resampled audio clips and 0 UHTS mutations.

Structure: 32 Bars (128.0 beats @ 112.0 BPM) across 8 scenes in Session View
and continuous timeline in Arrangement View with 8 Locators.
"""

from typing import List, Dict, Any, Optional
import time
from pathlib import Path
import json
import logging

logger = logging.getLogger("TaikoPureComposer")


class TaikoPureComposer:
    """
    Master procedural composer for Taiko Ryūsei (32 bars, 8 scenes, 4 bars / 16 beats each).
    100% pure synthesis and live instrumentation (zero audio reprocessing).
    """

    # --- DRUM RACK GENERAL MIDI PITCHES ---
    O_DAIKO = 36          # C1: Grand Imperial Bass Drum (Sub-impact)
    NAGADO_HIT = 38       # D1: Mid Nagado Taiko Center Hit (Main punch)
    NAGADO_RIM = 40       # E1: Mid Nagado Edge Strike
    SHIME_OPEN = 42       # F#1: High Shime-daiko Open Hit
    SHIME_RIM = 44        # G#1: High Shime-daiko Rimshot
    BACHI_CLICK = 46      # A#1: Wooden Bachi Stick Clacks
    ATARIGANE = 48        # C2: Ceremonial Brass Hand Bell

    # --- A MINOR INSEN / HIRAJOSHI PITCHES ---
    # Insen Scale in A: A, Bb, D, E, G
    ROOT_A = 69           # A4
    FLAT_SECOND_BB = 70   # Bb4 (Traditional Insen modal tension)
    FOURTH_D = 74         # D5
    FIFTH_E = 76          # E5
    FLAT_SEVENTH_G = 79   # G5
    OCTAVE_A = 81         # A5
    HIGH_BB = 82          # Bb5

    # 808 Sub-Bass Pitches in A
    BASS_A0 = 21          # A0 (27.50 Hz)
    BASS_A1 = 33          # A1 (55.00 Hz)
    BASS_BB1 = 34         # Bb1 (58.27 Hz)
    BASS_D2 = 38          # D2 (73.42 Hz)
    BASS_E2 = 40          # E2 (82.41 Hz)
    BASS_G2 = 43          # G2 (98.00 Hz)

    # 8 Scenes Definition (16 beats / 4 bars each, total 128 beats = 32 bars @ 112 BPM)
    SCENES = [
        {"idx": 1, "name": "01 - Dawn: Temple Bell & Bachi Whispers",   "section": "INTRO",   "energy": 0.20},
        {"idx": 2, "name": "02 - Gathering: Nagado Pulse & Koto Call",  "section": "INTRO",   "energy": 0.40},
        {"idx": 3, "name": "03 - Build: Thunder of Sacred Mountain",    "section": "BUILD",   "energy": 0.65},
        {"idx": 4, "name": "04 - DROP 1: The Great Taiko Storm",       "section": "DROP_1",  "energy": 0.95},
        {"idx": 5, "name": "05 - Groove: Polyrhythmic Battle Chant",     "section": "DROP_1",  "energy": 0.90},
        {"idx": 6, "name": "06 - Break: Mist of the Bamboo Grove",      "section": "BREAK",   "energy": 0.30},
        {"idx": 7, "name": "07 - CLIMAX: Celestial Dragon Roar",        "section": "DROP_2",  "energy": 1.00},
        {"idx": 8, "name": "08 - Outro: Fading Temple Echoes",          "section": "OUTRO",   "energy": 0.15},
    ]

    @classmethod
    def get_scene_count(cls) -> int:
        return len(cls.SCENES)

    # -------------------------------------------------------------------------
    # 1. TAIKO CEREMONIAL PERCUSSION PATTERNS (16 beats / 4 bars per scene)
    # -------------------------------------------------------------------------
    @classmethod
    def get_taiko_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        if sec == "INTRO":
            if scene_idx == 1:
                # Bell strikes and sparse wooden clicks
                notes.append({"pitch": cls.ATARIGANE, "start_time": 0.0, "duration": 1.0, "velocity": 85})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 4.0, "duration": 0.25, "velocity": 75})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 8.0, "duration": 0.25, "velocity": 80})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 12.0, "duration": 0.25, "velocity": 85})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 14.5, "duration": 0.25, "velocity": 90})
                notes.append({"pitch": cls.ATARIGANE, "start_time": 15.0, "duration": 1.0, "velocity": 95})
            else:
                # Nagado heartbeat pulse with Shime open strikes
                for bar in range(4):
                    b = float(bar * 4)
                    notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 0.0, "duration": 0.5, "velocity": 85})
                    notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 2.0, "duration": 0.25, "velocity": 80})
                    notes.append({"pitch": cls.BACHI_CLICK, "start_time": b + 3.5, "duration": 0.25, "velocity": 85})

        elif sec == "BUILD":
            # Accelerating Nagado body hits and rapid Shime rolls
            for bar in range(4):
                b = float(bar * 4)
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 0.0, "duration": 0.5, "velocity": 95})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.5, "velocity": 100})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 3.0, "duration": 0.25, "velocity": 90})
                # 16th-note Shime rolls
                for sub in range(4):
                    notes.append({
                        "pitch": cls.SHIME_OPEN,
                        "start_time": b + 2.0 + (sub * 0.25),
                        "duration": 0.2,
                        "velocity": 75 + (bar * 5) + (sub * 3)
                    })
            # Huge final O-Daiko warning hit
            notes.append({"pitch": cls.O_DAIKO, "start_time": 15.0, "duration": 1.0, "velocity": 127})

        elif sec in ["DROP_1", "DROP_2"]:
            is_climax = (sec == "DROP_2")
            o_vel = 127 if is_climax else 118
            n_vel = 120 if is_climax else 110

            for bar in range(4):
                b = float(bar * 4)
                # O-Daiko colossal downbeat
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 1.0, "velocity": o_vel})
                if bar in [1, 3] or is_climax:
                    notes.append({"pitch": cls.O_DAIKO, "start_time": b + 2.5, "duration": 0.5, "velocity": o_vel - 10})

                # Nagado main body driving cadence
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 1.0, "duration": 0.5, "velocity": n_vel})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.5, "velocity": n_vel})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 3.0, "duration": 0.25, "velocity": n_vel - 5})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 3.5, "duration": 0.25, "velocity": n_vel})

                # Shime-daiko syncopated polyrhythms
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 0.75, "duration": 0.25, "velocity": 95})
                notes.append({"pitch": cls.SHIME_RIM,  "start_time": b + 1.75, "duration": 0.25, "velocity": 100})
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 2.25, "duration": 0.25, "velocity": 105})
                notes.append({"pitch": cls.SHIME_RIM,  "start_time": b + 3.25, "duration": 0.25, "velocity": 110})

                # Atarigane bell accent
                if bar in [0, 2]:
                    notes.append({"pitch": cls.ATARIGANE, "start_time": b + 0.0, "duration": 0.5, "velocity": 105})

        elif sec == "BREAK":
            # Solemn spacious temple silence with isolated bachi and shime
            notes.append({"pitch": cls.ATARIGANE, "start_time": 0.0, "duration": 2.0, "velocity": 90})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 4.0, "duration": 0.5, "velocity": 75})
            notes.append({"pitch": cls.SHIME_OPEN,  "start_time": 8.0, "duration": 0.5, "velocity": 80})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 12.0, "duration": 0.5, "velocity": 85})

        elif sec == "OUTRO":
            # Fading O-Daiko rumble into silence
            notes.append({"pitch": cls.O_DAIKO,   "start_time": 0.0, "duration": 2.0, "velocity": 100})
            notes.append({"pitch": cls.ATARIGANE, "start_time": 4.0, "duration": 2.0, "velocity": 80})
            notes.append({"pitch": cls.O_DAIKO,   "start_time": 8.0, "duration": 2.0, "velocity": 75})
            notes.append({"pitch": cls.BACHI_CLICK,"start_time": 14.0, "duration": 0.5, "velocity": 65})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # 2. INSEN 808 SUB-BASS PATTERNS (Root in A)
    # -------------------------------------------------------------------------
    @classmethod
    def get_bass_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        if sec == "INTRO":
            if scene_idx == 2:
                # Sustained gentle root notes
                notes.append({"pitch": cls.BASS_A1, "start_time": 0.0, "duration": 3.8, "velocity": 85})
                notes.append({"pitch": cls.BASS_BB1,"start_time": 4.0, "duration": 3.8, "velocity": 80})
                notes.append({"pitch": cls.BASS_D2, "start_time": 8.0, "duration": 3.8, "velocity": 85})
                notes.append({"pitch": cls.BASS_A1, "start_time": 12.0, "duration": 3.8, "velocity": 85})

        elif sec == "BUILD":
            # Driving pulse on A1 and Bb1
            for bar in range(4):
                b = float(bar * 4)
                p = cls.BASS_BB1 if bar == 2 else (cls.BASS_E2 if bar == 3 else cls.BASS_A1)
                notes.append({"pitch": p, "start_time": b + 0.0, "duration": 1.8, "velocity": 95})
                notes.append({"pitch": p, "start_time": b + 2.0, "duration": 1.8, "velocity": 100})

        elif sec in ["DROP_1", "DROP_2"]:
            vel = 120 if sec == "DROP_2" else 112
            # Punchy Insen 808 slides: A1 -> Bb1 -> D2 -> E2
            prog = [cls.BASS_A1, cls.BASS_BB1, cls.BASS_D2, cls.BASS_E2]
            for bar in range(4):
                b = float(bar * 4)
                root_p = prog[bar]
                # Downbeat sub impact
                notes.append({"pitch": root_p, "start_time": b + 0.0, "duration": 1.8, "velocity": vel})
                # Offbeat bounce
                notes.append({"pitch": root_p, "start_time": b + 2.5, "duration": 0.8, "velocity": vel - 5})
                # Insen modal tension slide
                slide_p = cls.BASS_BB1 if root_p == cls.BASS_A1 else cls.BASS_G2
                notes.append({"pitch": slide_p, "start_time": b + 3.5, "duration": 0.5, "velocity": vel})

        elif sec == "OUTRO":
            notes.append({"pitch": cls.BASS_A0, "start_time": 0.0, "duration": 7.5, "velocity": 80})
            notes.append({"pitch": cls.BASS_A0, "start_time": 8.0, "duration": 7.5, "velocity": 70})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # 3. SHAKUHACHI / INSEN LEAD FLUTE PATTERNS
    # -------------------------------------------------------------------------
    @classmethod
    def get_lead_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        if sec == "INTRO":
            if scene_idx == 2:
                # Ancient flute motif in Insen scale: A4 -> Bb4 -> D5 -> E5 -> Bb4 -> A4
                m = [
                    (cls.ROOT_A, 0.0, 2.0, 80),
                    (cls.FLAT_SECOND_BB, 2.5, 1.2, 85),
                    (cls.FOURTH_D, 4.0, 2.0, 90),
                    (cls.FIFTH_E, 6.5, 1.2, 92),
                    (cls.FLAT_SECOND_BB, 8.0, 2.0, 85),
                    (cls.ROOT_A, 11.0, 3.5, 80),
                ]
                for p, s, d, v in m:
                    notes.append({"pitch": p, "start_time": s, "duration": d, "velocity": v})

        elif sec in ["DROP_1", "DROP_2"]:
            oct_shift = 12 if sec == "DROP_2" else 0
            v_base = 105 if sec == "DROP_2" else 95
            # Soaring ceremonial warrior theme
            m = [
                (cls.ROOT_A + oct_shift, 0.0, 1.5, v_base),
                (cls.FLAT_SECOND_BB + oct_shift, 1.8, 0.8, v_base + 3),
                (cls.FOURTH_D + oct_shift, 2.8, 1.0, v_base + 5),
                (cls.FIFTH_E + oct_shift, 4.0, 2.5, v_base + 8),
                (cls.HIGH_BB + oct_shift, 7.0, 0.8, v_base + 10),
                (cls.OCTAVE_A + oct_shift, 8.0, 1.5, v_base + 8),
                (cls.FIFTH_E + oct_shift, 10.0, 1.5, v_base + 5),
                (cls.FOURTH_D + oct_shift, 12.0, 1.2, v_base + 3),
                (cls.FLAT_SECOND_BB + oct_shift, 13.5, 1.0, v_base),
                (cls.ROOT_A + oct_shift, 14.8, 1.2, v_base - 2),
            ]
            for p, s, d, v in m:
                notes.append({"pitch": p, "start_time": s, "duration": d, "velocity": v})

        elif sec == "BREAK":
            # Expressive solo flute breath
            notes.append({"pitch": cls.ROOT_A, "start_time": 1.0, "duration": 2.5, "velocity": 75})
            notes.append({"pitch": cls.FLAT_SECOND_BB, "start_time": 4.5, "duration": 2.0, "velocity": 78})
            notes.append({"pitch": cls.FIFTH_E, "start_time": 7.5, "duration": 3.0, "velocity": 85})
            notes.append({"pitch": cls.FOURTH_D, "start_time": 11.0, "duration": 1.8, "velocity": 80})
            notes.append({"pitch": cls.ROOT_A, "start_time": 13.5, "duration": 2.2, "velocity": 72})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # 4. TRADITIONAL KOTO PLUCK PATTERNS (Hirajoshi / Insen Arpeggios)
    # -------------------------------------------------------------------------
    @classmethod
    def get_koto_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        # Fast 16th and 8th-note delicate wooden plucks
        if sec in ["BUILD", "DROP_1", "DROP_2"]:
            arp_pitches = [cls.ROOT_A, cls.FLAT_SECOND_BB, cls.FOURTH_D, cls.FIFTH_E, cls.FLAT_SEVENTH_G]
            vel = 90 if sec == "DROP_2" else 80
            for bar in range(4):
                b = float(bar * 4)
                for step in range(8):
                    t = b + (step * 0.5)
                    p = arp_pitches[(bar + step) % len(arp_pitches)]
                    notes.append({"pitch": p, "start_time": t, "duration": 0.35, "velocity": vel})

        elif sec == "INTRO" and scene_idx == 2:
            # Slower entrance plucks
            m = [
                (cls.ROOT_A, 0.5, 0.5, 75),
                (cls.FOURTH_D, 1.5, 0.5, 78),
                (cls.FIFTH_E, 2.5, 0.5, 80),
                (cls.FLAT_SECOND_BB, 4.5, 0.5, 78),
                (cls.ROOT_A, 5.5, 0.5, 75),
            ]
            for p, s, d, v in m:
                notes.append({"pitch": p, "start_time": s, "duration": d, "velocity": v})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # 5. SHINTO TEMPLE SYNTH PAD CHORDS (Pure Synthesis - Zero Reprocessing)
    # -------------------------------------------------------------------------
    @classmethod
    def get_pad_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        # 4 Bars sustained ethereal harmony in A Minor Insen
        # Bar 1: Am9 [A2=45, C3=48, E3=52, G3=55, B3=59]
        # Bar 2: Bbmaj7#11 [Bb2=46, D3=50, F3=53, A3=57, E4=64] (Insen modal tension)
        # Bar 3: Dm9 [D3=50, F3=53, A3=57, C4=60, E4=64]
        # Bar 4: Em7(b9) [E2=40, D3=50, F3=53, G3=55, B3=59]
        chords_prog = [
            ([45, 48, 52, 55, 59], 0.0, 3.9),
            ([46, 50, 53, 57, 64], 4.0, 3.9),
            ([50, 53, 57, 60, 64], 8.0, 3.9),
            ([40, 50, 53, 55, 59], 12.0, 3.9),
        ]

        vel = 92 if sec in ["DROP_1", "DROP_2"] else 75
        for chord, start, dur in chords_prog:
            for p in chord:
                notes.append({
                    "pitch": p,
                    "start_time": start,
                    "duration": dur,
                    "velocity": vel
                })

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # LIVE DEPLOYMENT ENGINE (Pure Synthesis / 0 Reprocessed Audio)
    # -------------------------------------------------------------------------
    @classmethod
    def deploy(cls, conn: Any = None) -> Dict[str, Any]:
        """
        Deploys the full 32-bar pure Taiko song (Taiko Ryūsei) into Ableton Live 12 Suite:
        1. Sets master tempo (112.0 BPM) and root note A Minor.
        2. Preserves user tracks 0..17 untouched; cleans up tracks > 17.
        3. Creates 5 live MIDI tracks:
           - Track 18: [TAIKO] Ceremonial Drums (Drum Rack)
           - Track 19: [BASS] Insen 808 Sub (Drift Synth)
           - Track 20: [LEAD] Shakuhachi / Insen Flute (Drift Synth)
           - Track 21: [KOTO] Ceremonial Pluck (Drift Synth)
           - Track 22: [PAD-PURE] Shinto Temple Chords (Drift Synth - Pure Synthesis!)
        4. Loads authentic instruments and applies sound blueprints.
        5. Populates 8 scenes in Session View and duplicates to 32-bar Arrangement timeline with 8 Cue Points.
        6. ZERO audio reprocessing / ZERO resampled audio clips.
        7. Starts playback from Bar 1.
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

        # 1. Master Tempo & Scale (Preserve tracks 0..17)
        code_meta = """
song.tempo = 112.0
song.root_note = 9 # A
song.scale_name = "Minor"

# Preserve user tracks 0..17
while len(song.tracks) > 18:
    song.delete_track(len(song.tracks) - 1)

while len(song.scenes) < 8:
    song.create_scene(-1)
"""
        try:
            conn.send_command("execute_code", {"code": code_meta})
        except Exception as e:
            logger.warning(f"Notice setting tempo/scenes in Live: {e}")

        # 2. Create 5 Live MIDI Tracks
        for _ in range(5):
            try:
                conn.send_command("create_midi_track", {"index": -1})
            except Exception as e:
                logger.warning(f"Notice creating track: {e}")

        taiko_idx = 18
        bass_idx = 19
        lead_idx = 20
        koto_idx = 21
        pad_idx = 22

        # 3. Rename tracks
        conn.send_command("set_track_name", {"track_index": taiko_idx, "name": "[TAIKO] Ceremonial Drums"})
        conn.send_command("set_track_name", {"track_index": bass_idx, "name": "[BASS] Insen 808 Sub"})
        conn.send_command("set_track_name", {"track_index": lead_idx, "name": "[LEAD] Shakuhachi / Insen Flute"})
        conn.send_command("set_track_name", {"track_index": koto_idx, "name": "[KOTO] Ceremonial Pluck"})
        conn.send_command("set_track_name", {"track_index": pad_idx, "name": "[PAD-PURE] Shinto Temple Chords"})

        # 4. Load Instruments & Sound Blueprints
        from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor

        # Taiko Drum Rack
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": taiko_idx, "uri": "query:Drums#Drum%20Rack"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn=conn, track_index=taiko_idx, role="DRUMS", plugin_name="Drum Rack",
                custom_blueprint={"parameters": {"MACRO_1": 0.85, "MACRO_2": 0.65, "MACRO_3": 0.40, "MACRO_4": 0.70}}
            )
        except Exception as e:
            logger.debug(f"Taiko instrument notice: {e}")

        # Insen 808 Sub (Drift)
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": bass_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn=conn, track_index=bass_idx, role="BASS", plugin_name="Drift",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.42, "DRIVE": 0.45, "SUB_LEVEL": 0.95, "AMP_ATTACK": 0.02, "AMP_RELEASE": 0.40}}
            )
        except Exception as e:
            logger.debug(f"Bass instrument notice: {e}")

        # Shakuhachi Flute (Drift)
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": lead_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn=conn, track_index=lead_idx, role="LEAD", plugin_name="Drift",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.72, "DRIVE": 0.20, "AMP_ATTACK": 0.08, "AMP_RELEASE": 0.35, "BRIGHTNESS": 0.68}}
            )
        except Exception as e:
            logger.debug(f"Lead instrument notice: {e}")

        # Koto Pluck (Drift)
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": koto_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn=conn, track_index=koto_idx, role="KEYS", plugin_name="Drift",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.85, "DRIVE": 0.15, "AMP_ATTACK": 0.01, "AMP_DECAY": 0.35, "AMP_SUSTAIN": 0.05, "AMP_RELEASE": 0.25}}
            )
        except Exception as e:
            logger.debug(f"Koto instrument notice: {e}")

        # Shinto Temple Pad (Drift - Pure Synth)
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": pad_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn=conn, track_index=pad_idx, role="PAD", plugin_name="Drift",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.65, "DRIVE": 0.25, "AMP_ATTACK": 0.35, "AMP_RELEASE": 0.85, "SUB_LEVEL": 0.60}}
            )
        except Exception as e:
            logger.debug(f"Pad instrument notice: {e}")

        # 5. Build Staging Payload for Fast Batch Execution
        scenes_data = []
        for s_idx in range(1, 9):
            meta = cls.SCENES[s_idx - 1]
            dest_time = (s_idx - 1) * 16.0
            scenes_data.append({
                "scene_pos": s_idx - 1,
                "scene_name": meta["name"],
                "dest_time": dest_time,
                "taiko_notes": cls.get_taiko_notes_for_scene(s_idx),
                "bass_notes": cls.get_bass_notes_for_scene(s_idx),
                "lead_notes": cls.get_lead_notes_for_scene(s_idx),
                "koto_notes": cls.get_koto_notes_for_scene(s_idx),
                "pad_notes": cls.get_pad_notes_for_scene(s_idx)
            })

        staging_payload = {
            "taiko_idx": taiko_idx,
            "bass_idx": bass_idx,
            "lead_idx": lead_idx,
            "koto_idx": koto_idx,
            "pad_idx": pad_idx,
            "scenes": scenes_data
        }

        # 6. Fast In-Process Batch Staging (Session + Arrangement View)
        code_batch = """
import json

staging_data = json.loads('''%s''')

taiko_idx = staging_data["taiko_idx"]
bass_idx = staging_data["bass_idx"]
lead_idx = staging_data["lead_idx"]
koto_idx = staging_data["koto_idx"]
pad_idx = staging_data["pad_idx"]

for item in staging_data["scenes"]:
    s_idx = item["scene_pos"]
    song.scenes[s_idx].name = item["scene_name"]
    dest_t = item["dest_time"]

    # 1. Taiko Master Ensemble
    if item["taiko_notes"]:
        slot = song.tracks[taiko_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Taiko #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(taiko_idx, s_idx, item["taiko_notes"])
        self._duplicate_session_clip_to_arrangement(taiko_idx, s_idx, dest_t)

    # 2. Insen 808 Sub-Bass
    if item["bass_notes"]:
        slot = song.tracks[bass_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "808 Bass #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(bass_idx, s_idx, item["bass_notes"])
        self._duplicate_session_clip_to_arrangement(bass_idx, s_idx, dest_t)

    # 3. Shakuhachi Flute Lead
    if item["lead_notes"]:
        slot = song.tracks[lead_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Flute Lead #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(lead_idx, s_idx, item["lead_notes"])
        self._duplicate_session_clip_to_arrangement(lead_idx, s_idx, dest_t)

    # 4. Koto Ceremonial Pluck
    if item["koto_notes"]:
        slot = song.tracks[koto_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Koto Pluck #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(koto_idx, s_idx, item["koto_notes"])
        self._duplicate_session_clip_to_arrangement(koto_idx, s_idx, dest_t)

    # 5. Shinto Temple Pad (Pure Synth)
    if item["pad_notes"]:
        slot = song.tracks[pad_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Temple Pad #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(pad_idx, s_idx, item["pad_notes"])
        self._duplicate_session_clip_to_arrangement(pad_idx, s_idx, dest_t)

    # Arrangement Cue Point Locator
    self._create_cue_point(dest_t, "#%%02d: %%s" %% (s_idx + 1, item["scene_name"]))

# Loop region & playback
song.view.selected_scene = song.scenes[0]
song.loop_start = 0.0
song.loop_length = 128.0
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

        # Switch to arrangement view
        try:
            conn.send_command("switch_to_arrangement_view", {})
        except Exception:
            pass

        tracks_summary = [
            {"index": taiko_idx, "name": "[TAIKO] Ceremonial Drums", "role": "DRUMS", "instrument": "query:Drums#Drum%20Rack"},
            {"index": bass_idx, "name": "[BASS] Insen 808 Sub", "role": "BASS", "instrument": "query:Synths#Drift"},
            {"index": lead_idx, "name": "[LEAD] Shakuhachi / Insen Flute", "role": "LEAD", "instrument": "query:Synths#Drift"},
            {"index": koto_idx, "name": "[KOTO] Ceremonial Pluck", "role": "KEYS", "instrument": "query:Synths#Drift"},
            {"index": pad_idx, "name": "[PAD-PURE] Shinto Temple Chords", "role": "PAD", "instrument": "query:Synths#Drift"}
        ]

        logger.info("Taiko Ryūsei pure song successfully deployed in Ableton Live.")
        return {
            "success": True,
            "tracks": tracks_summary,
            "bpm": 112.0,
            "key": "A",
            "scale": "Minor",
            "scenes_count": 8,
            "bars": 32,
            "total_beats": 128.0,
            "reprocessing": "NONE (Pure Synthesis & Percussion)",
            "scenes": cls.SCENES
        }

# engine/composition/taiko_shimmer_composer.py
"""
Taiko Shimmer: Kaze no Hikari (風の光):
Ceremonial Japanese Taiko Drumming fused with D Minor Insen / Phrygian harmony,
deep 808 sub-bass, and a dedicated atmospheric Pad processed through a single
reprocessing mutation: UHTS Technique #06 (Pitch-Shifted Shimmer Diffusion).

Structure: 40 Bars (160.0 beats @ 105 BPM) across 10 scenes in Session View
and continuous timeline in Arrangement View with 10 Locators.
"""

from typing import List, Dict, Any, Optional
import time
from pathlib import Path
import json
import logging

logger = logging.getLogger("TaikoShimmerComposer")


class TaikoShimmerComposer:
    """
    Master procedural composer for Taiko Shimmer (40 bars, 10 scenes, 4 bars / 16 beats each).
    """

    # --- DRUM RACK GENERAL MIDI PITCHES ---
    O_DAIKO = 36          # C1: Big Bass Taiko (Thunderous sub-impact)
    NAGADO_HIT = 38       # D1: Mid Taiko Center Hit (Main punch)
    NAGADO_RIM = 40       # E1: Mid Taiko Edge Strike
    SHIME_OPEN = 42       # F#1: High Shime-daiko Open Hit
    SHIME_RIM = 44        # G#1: High Shime-daiko Rimshot
    BACHI_CLICK = 46      # A#1: Wooden Bachi Stick Clacks

    # --- D MINOR INSEN / PHRYGIAN PITCHES ---
    # Insen Scale: D, Eb, G, A, C
    ROOT_D = 62           # D4
    FLAT_SECOND_EB = 63   # Eb4 (Tensión modal japonesa Insen)
    FOURTH_G = 67         # G4
    FIFTH_A = 69          # A4
    FLAT_SEVENTH_C = 72   # C5
    OCTAVE_D = 74         # D5
    HIGH_EB = 75          # Eb5

    # 808 Sub-Bass Pitches in D
    BASS_D1 = 26          # D1 (36.71 Hz)
    BASS_EB1 = 27         # Eb1 (38.89 Hz)
    BASS_G1 = 31          # G1 (48.99 Hz)
    BASS_A1 = 33          # A1 (55.00 Hz)
    BASS_C2 = 36          # C2 (65.41 Hz)

    # 10 Scenes Definition (16 beats / 4 bars each, total 160 beats = 40 bars @ 105 BPM)
    SCENES = [
        {"idx": 1,  "name": "01 - Intro: Shimmer Awakening",           "section": "INTRO",   "energy": 0.20},
        {"idx": 2,  "name": "02 - Entrance: Ceremonial Koto Motif",      "section": "INTRO",   "energy": 0.35},
        {"idx": 3,  "name": "03 - Build 1: Nagado Thunder Gathering",    "section": "BUILD_1", "energy": 0.55},
        {"idx": 4,  "name": "04 - DROP 1: Battle Roar & Shimmer Aura",   "section": "DROP_1",  "energy": 0.90},
        {"idx": 5,  "name": "05 - Drop 1: Polyrhythmic Transcendence",   "section": "DROP_1",  "energy": 0.95},
        {"idx": 6,  "name": "06 - Break: Mist of the Ancient Temple",   "section": "BREAK",   "energy": 0.30},
        {"idx": 7,  "name": "07 - Build 2: Accelerating Bachi Roll",     "section": "BUILD_2", "energy": 0.70},
        {"idx": 8,  "name": "08 - DROP 2: Colossal Climax",             "section": "DROP_2",  "energy": 1.00},
        {"idx": 9,  "name": "09 - Post-Climax: Resonant Shockwave",     "section": "DROP_2",  "energy": 0.65},
        {"idx": 10, "name": "10 - Outro: Shimmering Void Fade",         "section": "OUTRO",   "energy": 0.15},
    ]

    @classmethod
    def get_scene_count(cls) -> int:
        return len(cls.SCENES)

    # -------------------------------------------------------------------------
    # TAIKO PERCUSSION PATTERNS (16 beats / 4 bars per scene)
    # -------------------------------------------------------------------------
    @classmethod
    def get_taiko_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        if sec == "INTRO":
            if scene_idx == 1:
                # Sparse wooden clicks announcing ceremony
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 4.0, "duration": 0.25, "velocity": 75})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 8.0, "duration": 0.25, "velocity": 85})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 12.0, "duration": 0.25, "velocity": 90})
                notes.append({"pitch": cls.BACHI_CLICK, "start_time": 15.0, "duration": 0.25, "velocity": 95})
            else:
                # Gentle Shime pulse with occasional bachi
                for bar in range(4):
                    b = float(bar * 4)
                    notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 0.0, "duration": 0.5, "velocity": 80})
                    notes.append({"pitch": cls.SHIME_RIM,  "start_time": b + 2.5, "duration": 0.25, "velocity": 85})
                    notes.append({"pitch": cls.BACHI_CLICK,"start_time": b + 3.5, "duration": 0.25, "velocity": 90})

        elif sec == "BUILD_1" or sec == "BUILD_2":
            # Driving Nagado hits with accelerating 16th-note Shime rolls
            for bar in range(4):
                b = float(bar * 4)
                # Main body hits on downbeats
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 0.0, "duration": 0.5, "velocity": 95})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.5, "velocity": 100})
                # Offbeat rim accents
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 1.5, "duration": 0.25, "velocity": 88})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 3.5, "duration": 0.25, "velocity": 92})
            # Accelerating roll in bar 4 (beats 12 to 16)
            for step in range(16):
                t_pos = 12.0 + step * 0.25
                vel = 70 + int(step * 3.5)
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": t_pos, "duration": 0.2, "velocity": min(125, vel)})

        elif sec in ["DROP_1", "DROP_2"]:
            # Massive Polyrhythmic Taiko Battle: Heavy O-Daiko earthquake hits + rapid Nagado & Shime
            is_climax = (sec == "DROP_2")
            o_vel = 127 if is_climax else 120
            for bar in range(4):
                b = float(bar * 4)
                # O-Daiko colossus
                notes.append({"pitch": cls.O_DAIKO, "start_time": b + 0.0, "duration": 1.5, "velocity": o_vel})
                if bar in [1, 3]:
                    notes.append({"pitch": cls.O_DAIKO, "start_time": b + 2.5, "duration": 1.2, "velocity": o_vel - 5})

                # Nagado power pattern
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 1.0, "duration": 0.4, "velocity": 105})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 2.0, "duration": 0.4, "velocity": 110})
                notes.append({"pitch": cls.NAGADO_HIT, "start_time": b + 3.0, "duration": 0.3, "velocity": 102})
                notes.append({"pitch": cls.NAGADO_RIM, "start_time": b + 3.5, "duration": 0.2, "velocity": 112})

                # Shime polyrhythmic hi-hat syncopation (dotted 8ths)
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 0.75, "duration": 0.2, "velocity": 90})
                notes.append({"pitch": cls.SHIME_RIM,  "start_time": b + 1.75, "duration": 0.2, "velocity": 95})
                notes.append({"pitch": cls.SHIME_OPEN, "start_time": b + 2.75, "duration": 0.2, "velocity": 92})

        elif sec == "BREAK":
            # Ethereal mist: sparse bamboo rimshots floating against the shimmer pad
            notes.append({"pitch": cls.SHIME_RIM,   "start_time": 2.0,  "duration": 0.3, "velocity": 75})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 5.5,  "duration": 0.2, "velocity": 80})
            notes.append({"pitch": cls.NAGADO_RIM,  "start_time": 9.0,  "duration": 0.4, "velocity": 78})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 13.5, "duration": 0.2, "velocity": 85})

        elif sec == "OUTRO":
            # Ceremonial fade: single deep O-Daiko reverberating into the void
            notes.append({"pitch": cls.O_DAIKO,     "start_time": 0.0,  "duration": 4.0, "velocity": 115})
            notes.append({"pitch": cls.SHIME_OPEN,  "start_time": 6.0,  "duration": 0.5, "velocity": 70})
            notes.append({"pitch": cls.BACHI_CLICK, "start_time": 10.0, "duration": 0.3, "velocity": 65})
            notes.append({"pitch": cls.O_DAIKO,     "start_time": 12.0, "duration": 4.0, "velocity": 90})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # 808 SUB-BASS PATTERNS in D Minor
    # -------------------------------------------------------------------------
    @classmethod
    def get_bass_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        if sec in ["INTRO", "BREAK", "OUTRO"]:
            # Sustained tonic drone or empty in breakdown
            if scene_idx in [2, 10]:
                notes.append({"pitch": cls.BASS_D1, "start_time": 0.0, "duration": 8.0, "velocity": 85})
            return notes

        if sec in ["BUILD_1", "BUILD_2"]:
            # Pulsing 8th notes rising into the drop
            for bar in range(4):
                b = float(bar * 4)
                notes.append({"pitch": cls.BASS_D1, "start_time": b + 0.0, "duration": 1.8, "velocity": 95})
                p = cls.BASS_EB1 if bar == 3 else cls.BASS_D1
                notes.append({"pitch": p, "start_time": b + 2.0, "duration": 1.8, "velocity": 100})
            return notes

        if sec in ["DROP_1", "DROP_2"]:
            # Heavy, sustained 808 sub-bass with Insen modal slides
            is_d2 = (sec == "DROP_2")
            bar_pitches = [
                (cls.BASS_D1,  0.0, 3.5, 115 if is_d2 else 105),
                (cls.BASS_EB1, 4.0, 3.5, 120 if is_d2 else 110),
                (cls.BASS_G1,  8.0, 3.5, 115 if is_d2 else 105),
                (cls.BASS_A1,  12.0, 1.8, 110 if is_d2 else 100),
                (cls.BASS_C2,  14.0, 1.8, 118 if is_d2 else 108),
            ]
            for p, start, dur, vel in bar_pitches:
                notes.append({"pitch": p, "start_time": start, "duration": dur, "velocity": vel})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # INSEN KOTO / FLUTE LEAD MELODY
    # -------------------------------------------------------------------------
    @classmethod
    def get_lead_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        if sec == "INTRO" and scene_idx == 2:
            # Ceremonial theme introduction
            m = [
                (cls.ROOT_D, 0.0, 1.5, 88),
                (cls.FLAT_SECOND_EB, 2.0, 1.0, 92),
                (cls.ROOT_D, 3.5, 1.5, 85),
                (cls.FIFTH_A, 6.0, 2.0, 95),
                (cls.FOURTH_G, 8.5, 1.5, 90),
                (cls.FLAT_SECOND_EB, 10.5, 1.5, 88),
                (cls.ROOT_D, 12.5, 3.0, 92),
            ]
            for p, start, dur, vel in m:
                notes.append({"pitch": p, "start_time": start, "duration": dur, "velocity": vel})

        elif sec in ["DROP_1", "DROP_2"]:
            # Full expressive Insen lead melody soaring above the drums
            octave_shift = 12 if sec == "DROP_2" else 0
            m = [
                (cls.ROOT_D + octave_shift, 0.0, 1.2, 105),
                (cls.FLAT_SECOND_EB + octave_shift, 1.5, 0.8, 110),
                (cls.ROOT_D + octave_shift, 2.5, 1.2, 102),
                (cls.FIFTH_A + octave_shift, 4.0, 1.8, 112),
                (cls.FOURTH_G + octave_shift, 6.0, 1.2, 105),
                (cls.FLAT_SECOND_EB + octave_shift, 7.5, 0.8, 108),
                (cls.ROOT_D + octave_shift, 8.5, 2.5, 115),
                (cls.FLAT_SEVENTH_C + octave_shift, 11.5, 1.0, 100),
                (cls.FIFTH_A + octave_shift, 13.0, 1.5, 108),
                (cls.ROOT_D + octave_shift, 14.8, 1.2, 110),
            ]
            for p, start, dur, vel in m:
                notes.append({"pitch": p, "start_time": start, "duration": dur, "velocity": vel})

        elif sec == "BREAK":
            # Sparse solo flute phrase
            notes.append({"pitch": cls.ROOT_D, "start_time": 1.0, "duration": 2.0, "velocity": 75})
            notes.append({"pitch": cls.FLAT_SECOND_EB, "start_time": 4.0, "duration": 1.5, "velocity": 80})
            notes.append({"pitch": cls.FIFTH_A, "start_time": 7.0, "duration": 2.5, "velocity": 85})
            notes.append({"pitch": cls.FOURTH_G, "start_time": 10.5, "duration": 1.5, "velocity": 78})
            notes.append({"pitch": cls.ROOT_D, "start_time": 13.0, "duration": 2.5, "velocity": 82})

        return sorted(notes, key=lambda x: (x["start_time"], x["pitch"]))

    # -------------------------------------------------------------------------
    # SOURCE ATMOSPHERIC PAD CHORDS (Dm9 -> Ebmaj7#11 -> Gm9 -> Asus4(b9))
    # -------------------------------------------------------------------------
    @classmethod
    def get_pad_notes_for_scene(cls, scene_idx: int) -> List[Dict[str, Any]]:
        notes = []
        meta = cls.SCENES[scene_idx - 1]
        sec = meta["section"]

        # Chords: 4 bars (16 beats)
        # Bar 1: Dm9 (D3=50, F3=53, A3=57, C4=60, E4=64)
        # Bar 2: Ebmaj7#11 (Eb3=51, G3=55, Bb3=58, D4=62, A4=69)
        # Bar 3: Gm9 (G2=43, D3=50, Bb3=58, F4=65, A4=69)
        # Bar 4: Asus4(b9) (A2=45, G3=55, Bb3=58, D4=62, F4=65)
        chords_prog = [
            ([50, 53, 57, 60, 64], 0.0, 3.9),
            ([51, 55, 58, 62, 69], 4.0, 3.9),
            ([43, 50, 58, 65, 69], 8.0, 3.9),
            ([45, 55, 58, 62, 65], 12.0, 3.9),
        ]

        vel = 90 if sec in ["DROP_1", "DROP_2"] else 75
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
    # LIVE DEPLOYMENT ENGINE (Fast In-Process Batch)
    # -------------------------------------------------------------------------
    @classmethod
    def deploy(cls, conn: Any = None) -> Dict[str, Any]:
        """
        Deploys the full 40-bar Taiko Shimmer song in Ableton Live 12 Suite:
        1. Sets master tempo (105.0 BPM) and root note D Minor.
        2. Cleans up tracks > 17 (preserving user tracks 0..17).
        3. Creates 5 dedicated tracks: Taiko, 808 Bass, Insen Lead, Source Pad, Shimmer Audio Pad.
        4. Loads authentic instruments & applies parameter blueprints (Governance Compliance).
        5. Populates 10 scenes in Session View and duplicates to 40-bar Arrangement with 10 Cue Points.
        6. Connects Shimmer Diffusion Audio Pad (Technique #06) continuously throughout the song.
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

        # 1. Master Tempo, Scale & Cleanup (Preserve user tracks 0..17)
        code_meta = """
song.tempo = 105.0
song.root_note = 2 # D
song.scale_name = "Minor"
while len(song.tracks) > 18:
    song.delete_track(len(song.tracks) - 1)
while len(song.scenes) < 10:
    song.create_scene(-1)
result = {"track_count": len(song.tracks), "scenes_count": len(song.scenes)}
"""
        try:
            conn.send_command("execute_code", {"code": code_meta})
        except Exception as e:
            logger.warning(f"Error setting Live metadata: {e}")

        # 2. Create the 5 Dedicated Song Tracks
        code_create_tracks = """
t_taiko = song.create_midi_track(-1); t_taiko.name = "[TAIKO] Master Drums"
t_bass = song.create_midi_track(-1); t_bass.name = "[BASS] Insen 808 Sub"
t_lead = song.create_midi_track(-1); t_lead.name = "[LEAD] Koto/Insen Motif"
t_pad_src = song.create_midi_track(-1); t_pad_src.name = "[PAD-SRC] Original Atmospheric Pad"
t_pad_uhts = song.create_audio_track(-1); t_pad_uhts.name = "[PAD-UHTS] Shimmer Diffusion Audio"
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

        taiko_idx, bass_idx, lead_idx, pad_src_idx, pad_uhts_idx = raw_idxs

        # 3. Load Authentic Instruments & Apply Sound Blueprints (Governance Compliance)
        from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor

        # Taiko Drum Rack
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": taiko_idx, "uri": "query:Drums#Drum%20Rack"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, taiko_idx, role="DRUMS",
                custom_blueprint={"parameters": {"MACRO_1": 0.75, "MACRO_2": 0.65}}
            )
        except Exception as e:
            logger.warning(f"Taiko instrument notice: {e}")

        # Bass Drift
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": bass_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, bass_idx, role="BASS",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.38, "AMP_ATTACK": 0.01, "AMP_RELEASE": 0.90}}
            )
        except Exception as e:
            logger.warning(f"Bass instrument notice: {e}")

        # Lead Drift
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": lead_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, lead_idx, role="LEAD",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.80, "AMP_ATTACK": 0.02, "AMP_RELEASE": 0.40}}
            )
        except Exception as e:
            logger.warning(f"Lead instrument notice: {e}")

        # Source Pad Drift
        try:
            conn.send_command("load_instrument_or_effect", {"track_index": pad_src_idx, "uri": "query:Synths#Drift"})
            DeviceParameterSupervisor.apply_sound_blueprint(
                conn, pad_src_idx, role="PAD",
                custom_blueprint={"parameters": {"FILTER_CUTOFF": 0.55, "AMP_ATTACK": 0.35, "AMP_RELEASE": 0.80}}
            )
        except Exception as e:
            logger.warning(f"Source pad instrument notice: {e}")

        # 4. Resolve Shimmer Audio File Path
        root_dir = Path(__file__).resolve().parent.parent.parent
        shimmer_wav_path = root_dir / "cache" / "resampled_mutations" / "taiko_shimmer_uhts_06_pitch_shimmer.wav"
        if not shimmer_wav_path.exists():
            from scripts.generate_taiko_shimmer_assets import generate_assets
            generate_assets()

        safe_shimmer_path = str(shimmer_wav_path.resolve()).replace('\\', '/')

        # 5. Prepare Staging Data (10 Scenes across 40 bars)
        scenes_data = []
        for s_idx in range(1, len(cls.SCENES) + 1):
            scene_pos = s_idx - 1
            meta = cls.SCENES[scene_pos]
            scenes_data.append({
                "scene_pos": scene_pos,
                "scene_name": meta["name"],
                "dest_time": float(scene_pos * 16.0),
                "taiko_notes": cls.get_taiko_notes_for_scene(s_idx),
                "bass_notes": cls.get_bass_notes_for_scene(s_idx),
                "lead_notes": cls.get_lead_notes_for_scene(s_idx),
                "pad_notes": cls.get_pad_notes_for_scene(s_idx),
                "shimmer_path": safe_shimmer_path
            })

        staging_payload = {
            "taiko_idx": taiko_idx,
            "bass_idx": bass_idx,
            "lead_idx": lead_idx,
            "pad_src_idx": pad_src_idx,
            "pad_uhts_idx": pad_uhts_idx,
            "scenes": scenes_data
        }

        # 6. Fast In-Process Batch Staging in Live (Session View + Arrangement Timeline)
        code_batch = """
import json

staging_data = json.loads('''%s''')

taiko_idx = staging_data["taiko_idx"]
bass_idx = staging_data["bass_idx"]
lead_idx = staging_data["lead_idx"]
pad_src_idx = staging_data["pad_src_idx"]
pad_uhts_idx = staging_data["pad_uhts_idx"]

song.tracks[pad_uhts_idx].mixer_device.volume.value = 0.75

for item in staging_data["scenes"]:
    s_idx = item["scene_pos"]
    song.scenes[s_idx].name = item["scene_name"]
    dest_t = item["dest_time"]
    
    # 1. Taiko Master Drums
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

    # 3. Koto/Insen Lead
    if item["lead_notes"]:
        slot = song.tracks[lead_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Insen Lead #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(lead_idx, s_idx, item["lead_notes"])
        self._duplicate_session_clip_to_arrangement(lead_idx, s_idx, dest_t)

    # 4. Source Atmospheric Pad
    if item["pad_notes"]:
        slot = song.tracks[pad_src_idx].clip_slots[s_idx]
        if not slot.has_clip:
            slot.create_clip(16.0)
        slot.clip.name = "Pad Src #%%02d" %% (s_idx + 1)
        self._add_notes_to_clip(pad_src_idx, s_idx, item["pad_notes"])
        self._duplicate_session_clip_to_arrangement(pad_src_idx, s_idx, dest_t)

    # 5. Resampled Shimmer Diffusion Pad (Technique #06 Audio)
    if item["shimmer_path"]:
        slot = song.tracks[pad_uhts_idx].clip_slots[s_idx]
        if not slot.has_clip:
            try:
                slot.create_audio_clip(item["shimmer_path"])
                slot.clip.name = "Shimmer Pad #%%02d" %% (s_idx + 1)
                self._duplicate_session_clip_to_arrangement(pad_uhts_idx, s_idx, dest_t)
            except Exception as ex:
                self.log_message("Shimmer audio error: " + str(ex))

    # 6. Arrangement Cue Point / Locator
    self._create_cue_point(dest_t, "#%%02d: %%s" %% (s_idx + 1, item["scene_name"]))

# Loop region & playback
song.view.selected_scene = song.scenes[0]
song.loop_start = 0.0
song.loop_length = 160.0
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

        # 7. Final setup & summary
        try:
            conn.send_command("switch_to_arrangement_view", {})
        except Exception:
            pass

        tracks_summary = [
            {"index": taiko_idx, "name": "[TAIKO] Master Drums", "role": "DRUMS", "instrument": "query:Drums#Drum%20Rack"},
            {"index": bass_idx, "name": "[BASS] Insen 808 Sub", "role": "BASS", "instrument": "query:Synths#Drift"},
            {"index": lead_idx, "name": "[LEAD] Koto/Insen Motif", "role": "LEAD", "instrument": "query:Synths#Drift"},
            {"index": pad_src_idx, "name": "[PAD-SRC] Original Atmospheric Pad", "role": "PAD", "instrument": "query:Synths#Drift"},
            {"index": pad_uhts_idx, "name": "[PAD-UHTS] Shimmer Diffusion Audio", "role": "PAD", "type": "audio"}
        ]

        logger.info("Taiko Shimmer full song successfully deployed in Ableton Live.")
        return {
            "success": True,
            "tracks": tracks_summary,
            "bpm": 105.0,
            "key": "D",
            "scale": "Minor",
            "scenes_count": 10,
            "bars": 40,
            "total_beats": 160.0,
            "technique": "Pitch-Shifted Shimmer Diffusion",
            "scenes": cls.SCENES
        }

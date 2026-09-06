# engine/arrangement/arrangement_composer.py
"""
Arrangement Composer & Multi-Section Timeline Orchestrator:
Orchestrates a complete 5-section musical song directly onto Ableton Live's Arrangement timeline.
Enforces structural progression: Intro -> Verse -> Pre-Drop (with 1-bar vacuum drop) -> Drop / Chorus -> Outro.
Creates cue points, generates unique musical patterns per section and role, duplicates clips to their
exact beat locations, and switches Live to Arrangement view.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("ArrangementComposer")


class ArrangementSection:
    """Specification of an arrangement section."""
    def __init__(
        self,
        name: str,
        section_type: str,
        start_beat: float,
        length_beats: float,
        energy: float,
        description: str
    ):
        self.name = name
        self.section_type = section_type
        self.start_beat = start_beat
        self.length_beats = length_beats
        self.energy = energy
        self.description = description


class ArrangementComposer:
    """Builds and deploys complete multi-section arrangements to Ableton Live."""

    SECTIONS = [
        ArrangementSection("1. INTRO", "INTRO", 0.0, 32.0, 0.35, "Atmospheric chords, ethereal pad, vocal chop FX. No kick/sub."),
        ArrangementSection("2. VERSE", "VERSE", 32.0, 32.0, 0.60, "808 Hi-Hats, offbeat claps, sustained 808 root notes, comping chords, teaser lead."),
        ArrangementSection("3. PRE-DROP", "PRE_DROP", 64.0, 16.0, 0.85, "Accelerating snare roll (1/8 -> 1/16), riser sweep, 1-bar silence drop vacuum at bar 20."),
        ArrangementSection("4. DROP", "DROP", 80.0, 32.0, 1.00, "Full 808 kick, sliding 808 sub, cutting main hook lead, vocal hook chants, stereo chords."),
        ArrangementSection("5. OUTRO", "OUTRO", 112.0, 16.0, 0.30, "Half-time drums, resolving sustained chord, lingering pad tail, downlifter FX.")
    ]

    TOTAL_BEATS = 128.0  # 32 bars

    @classmethod
    def compose_and_deploy(
        cls,
        conn: Any,
        track_mapping: Dict[str, int],
        tempo: float = 140.0,
        genre: str = "Trap / Phonk"
    ) -> Dict[str, Any]:
        """
        Executes full arrangement composition:
        1. Sets project tempo.
        2. Places cue points for all 5 sections.
        3. Generates 5 distinct musical clips per track (one per section).
        4. Injects notes into Session clips.
        5. Duplicates each clip to its destination time in the Arrangement timeline.
        6. Switches Live to Arrangement view and resets playhead to 0.0.
        """
        if conn is None or not hasattr(conn, "send_command"):
            logger.info("Mock arrangement composition (no live connection)")
            return {
                "status": "MOCK_SUCCESS",
                "total_beats": cls.TOTAL_BEATS,
                "sections": len(cls.SECTIONS),
                "clips_placed": len(track_mapping) * len(cls.SECTIONS)
            }

        logger.info(f"Iniciando composicion de Arrangement ({len(cls.SECTIONS)} secciones, {cls.TOTAL_BEATS} beats)")

        # 1. Set tempo
        try:
            conn.send_command("set_tempo", {"tempo": float(tempo)})
        except Exception as e:
            logger.warning(f"Could not set tempo: {e}")

        # 2. Place Cue Points on Arrangement Timeline
        cue_results = []
        for sec in cls.SECTIONS:
            try:
                res = conn.send_command("create_cue_point", {
                    "time": float(sec.start_beat),
                    "name": sec.name
                })
                cue_results.append(res)
            except Exception as e:
                logger.warning(f"Could not create cue point '{sec.name}': {e}")

        # 3. Generate and deploy notes per section and track
        deployed_clips = []
        for sec_idx, sec in enumerate(cls.SECTIONS):
            logger.info(f"  Seccion {sec.name} (beats {sec.start_beat} a {sec.start_beat + sec.length_beats}) - Energia: {sec.energy}")

            for role, track_idx in track_mapping.items():
                notes = cls._generate_section_notes(role, sec)
                if not notes:
                    # Silence in this section for this role (e.g. Intro for drums/sub)
                    continue

                clip_name = f"[{sec.name.split('.')[1].strip()}] {role.capitalize()}"

                # Create clip in session slot sec_idx
                try:
                    conn.send_command("create_clip", {
                        "track_index": track_idx,
                        "clip_index": sec_idx,
                        "length": float(sec.length_beats)
                    })
                    conn.send_command("set_clip_name", {
                        "track_index": track_idx,
                        "clip_index": sec_idx,
                        "name": clip_name
                    })
                    conn.send_command("add_notes_to_clip", {
                        "track_index": track_idx,
                        "clip_index": sec_idx,
                        "notes": notes
                    })

                    # Duplicate clip to Arrangement timeline at sec.start_beat
                    dup_res = conn.send_command("duplicate_session_clip_to_arrangement", {
                        "track_index": track_idx,
                        "clip_index": sec_idx,
                        "destination_time": float(sec.start_beat)
                    })

                    deployed_clips.append({
                        "section": sec.name,
                        "role": role,
                        "track_index": track_idx,
                        "start_beat": sec.start_beat,
                        "length_beats": sec.length_beats,
                        "note_count": len(notes)
                    })
                except Exception as e:
                    logger.error(f"Failed deploying clip for {role} in {sec.name}: {e}")

        # 4. Switch Live to Arrangement View
        try:
            conn.send_command("switch_to_arrangement_view")
            conn.send_command("set_current_song_time", {"time_val": 0.0})
        except Exception as e:
            logger.warning(f"Failed switching to Arrangement view: {e}")

        return {
            "status": "ARRANGEMENT_COMPOSED",
            "tempo": tempo,
            "total_beats": cls.TOTAL_BEATS,
            "total_bars": int(cls.TOTAL_BEATS / 4.0),
            "sections_count": len(cls.SECTIONS),
            "clips_deployed": len(deployed_clips),
            "details": deployed_clips
        }

    @classmethod
    def _generate_section_notes(cls, role: str, sec: ArrangementSection) -> List[Dict[str, Any]]:
        """Generates tailored musical notes for a role in a specific section."""
        role_upper = role.upper()
        sec_type = sec.section_type
        length = sec.length_beats

        if "DRUM" in role_upper:
            return cls._drums_pattern(sec_type, length)
        elif "BASS" in role_upper or "SUB" in role_upper:
            return cls._sub_bass_pattern(sec_type, length)
        elif "CHORD" in role_upper or "KEY" in role_upper:
            return cls._chords_pattern(sec_type, length)
        elif "LEAD" in role_upper:
            return cls._lead_pattern(sec_type, length)
        elif "VOCAL" in role_upper:
            return cls._vocals_pattern(sec_type, length)
        elif "PAD" in role_upper:
            return cls._pad_pattern(sec_type, length)
        elif "FX" in role_upper:
            return cls._fx_pattern(sec_type, length)
        else:
            return []

    # =========================================================================
    # RHYTHMIC & MELODIC GENERATORS PER SECTION
    # =========================================================================

    @staticmethod
    def _drums_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates dynamic drum patterns for 808 Kit (Kick=36, Snare=38, Clap=39, Hat=42, OpenHat=46)."""
        notes = []
        if sec_type == "INTRO":
            # Very sparse: gentle hi-hat tick every 2 beats
            for b in range(0, int(length), 2):
                notes.append({"pitch": 42, "start_time": float(b), "duration": 0.1, "velocity": 45})
            return notes

        elif sec_type == "VERSE":
            # Trap verse: 8th note hi-hats with 16th roll at end of 4th bar; Snare/Clap on 2 & 4
            for bar in range(int(length / 4.0)):
                bar_start = bar * 4.0
                # Claps on beat 2 and 4
                notes.append({"pitch": 39, "start_time": bar_start + 1.0, "duration": 0.2, "velocity": 90})
                notes.append({"pitch": 39, "start_time": bar_start + 3.0, "duration": 0.2, "velocity": 95})
                # Hi-hats: 8th notes
                for h in range(8):
                    t = bar_start + h * 0.5
                    vel = 80 if h % 2 == 0 else 60
                    notes.append({"pitch": 42, "start_time": t, "duration": 0.15, "velocity": vel})
                # Occasional soft kick on beat 1 of odd bars
                if bar % 2 == 0:
                    notes.append({"pitch": 36, "start_time": bar_start, "duration": 0.25, "velocity": 85})
            return notes

        elif sec_type == "PRE_DROP":
            # Accelerated snare roll: 8th notes bars 1-2 (beats 0-8), 16th notes bar 3 (beats 8-12), SILENCE bar 4 (beats 12-16)
            for h in range(16):
                t = h * 0.5
                vel = 65 + int(h * 2.0)
                notes.append({"pitch": 38, "start_time": t, "duration": 0.18, "velocity": vel})
            for s in range(16):
                t = 8.0 + s * 0.25
                vel = 90 + int(s * 1.8)
                notes.append({"pitch": 38, "start_time": t, "duration": 0.10, "velocity": min(120, vel)})
                if s % 2 == 0:
                    notes.append({"pitch": 39, "start_time": t, "duration": 0.10, "velocity": min(115, vel - 5)})
            # Bar 4 (beats 12.0 to 16.0): ABSOLUTE SILENCE - The 1-bar vacuum drop cut!
            return notes

        elif sec_type == "DROP":
            # Explosive 808 Trap beat! Full heavy kick syncopation, hard snares, triplet hat rolls
            kick_offsets = [0.0, 0.75, 1.5, 2.75, 3.25]
            for bar in range(int(length / 4.0)):
                bar_start = bar * 4.0
                for ko in kick_offsets:
                    notes.append({"pitch": 36, "start_time": bar_start + ko, "duration": 0.35, "velocity": 115})
                notes.append({"pitch": 38, "start_time": bar_start + 1.0, "duration": 0.25, "velocity": 118})
                notes.append({"pitch": 39, "start_time": bar_start + 1.0, "duration": 0.25, "velocity": 110})
                notes.append({"pitch": 38, "start_time": bar_start + 3.0, "duration": 0.25, "velocity": 120})
                notes.append({"pitch": 39, "start_time": bar_start + 3.0, "duration": 0.25, "velocity": 115})
                notes.append({"pitch": 46, "start_time": bar_start + 0.5, "duration": 0.25, "velocity": 95})
                notes.append({"pitch": 46, "start_time": bar_start + 2.5, "duration": 0.25, "velocity": 95})
                for h in range(16):
                    t = bar_start + h * 0.25
                    vel = 90 if h % 4 == 0 else 70
                    notes.append({"pitch": 42, "start_time": t, "duration": 0.12, "velocity": vel})
            return notes

        elif sec_type == "OUTRO":
            # Half-time fading drums
            for bar in range(int(length / 4.0)):
                bar_start = bar * 4.0
                notes.append({"pitch": 36, "start_time": bar_start, "duration": 0.3, "velocity": max(30, 85 - bar * 10)})
                notes.append({"pitch": 38, "start_time": bar_start + 2.0, "duration": 0.2, "velocity": max(30, 80 - bar * 10)})
                for h in range(4):
                    notes.append({"pitch": 42, "start_time": bar_start + h * 1.0, "duration": 0.15, "velocity": max(20, 60 - bar * 8)})
            return notes

        return []

    @staticmethod
    def _sub_bass_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates 808 Sub Bass notes (C#1=37, A0=33, B0=35, G#0=32)."""
        notes = []
        if sec_type == "INTRO":
            return []

        elif sec_type == "VERSE":
            roots = [37, 33, 35, 32]
            for i, r in enumerate(roots * 2):
                t = i * 4.0
                if t + 4.0 <= length:
                    notes.append({"pitch": r, "start_time": t, "duration": 3.75, "velocity": 90})
            return notes

        elif sec_type == "PRE_DROP":
            for b in range(12):
                p = 37 if b < 8 else 40
                notes.append({"pitch": p, "start_time": float(b), "duration": 0.75, "velocity": 85 + b * 2})
            return notes

        elif sec_type == "DROP":
            pattern = [
                (0.0, 37, 0.7, 115), (0.75, 37, 0.7, 110), (1.5, 37, 1.1, 118), (2.75, 49, 0.45, 120), (3.25, 37, 0.7, 112),
                (4.0, 33, 0.7, 115), (4.75, 33, 0.7, 110), (5.5, 33, 1.1, 118), (6.75, 35, 1.2, 120),
                (8.0, 35, 0.7, 115), (8.75, 35, 0.7, 110), (9.5, 35, 1.1, 118), (10.75, 47, 0.45, 120), (11.25, 35, 0.7, 112),
                (12.0, 32, 0.7, 115), (12.75, 32, 0.7, 110), (13.5, 32, 1.1, 118), (14.75, 37, 1.2, 122)
            ]
            for bar_block in range(2):
                block_offset = bar_block * 16.0
                for start, pitch, dur, vel in pattern:
                    if block_offset + start < length:
                        notes.append({"pitch": pitch, "start_time": block_offset + start, "duration": dur, "velocity": vel})
            return notes

        elif sec_type == "OUTRO":
            notes.append({"pitch": 37, "start_time": 0.0, "duration": 12.0, "velocity": 85})
            return notes

        return []

    @staticmethod
    def _chords_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates chord progressions (C#m - A - B - G#m)."""
        progression = [
            [49, 52, 56, 61],  # C#m9
            [45, 49, 52, 57],  # Amaj7
            [47, 51, 54, 59],  # Bsus
            [44, 47, 51, 56]   # G#m
        ]
        notes = []

        if sec_type == "INTRO":
            for i, chord in enumerate(progression * 2):
                t = i * 4.0
                if t + 4.0 <= length:
                    for p in chord:
                        notes.append({"pitch": p, "start_time": t, "duration": 3.8, "velocity": 75})
            return notes

        elif sec_type == "VERSE":
            for i, chord in enumerate(progression * 2):
                t = i * 4.0
                if t + 4.0 <= length:
                    for stab in [0.5, 1.5, 2.5, 3.5]:
                        for p in chord:
                            notes.append({"pitch": p, "start_time": t + stab, "duration": 0.35, "velocity": 70})
            return notes

        elif sec_type == "PRE_DROP":
            for bar in range(3):
                chord = progression[bar % len(progression)]
                t = bar * 4.0
                for p in chord:
                    notes.append({"pitch": p, "start_time": t, "duration": 3.75, "velocity": 70 + bar * 10})
            return notes

        elif sec_type == "DROP":
            for i, chord in enumerate(progression * 2):
                t = i * 4.0
                if t + 4.0 <= length:
                    for stab in [0.0, 0.75, 1.5, 2.5, 3.25]:
                        for p in chord:
                            notes.append({"pitch": p, "start_time": t + stab, "duration": 0.4, "velocity": 85})
            return notes

        elif sec_type == "OUTRO":
            for p in progression[0]:
                notes.append({"pitch": p, "start_time": 0.0, "duration": 14.0, "velocity": 70})
            return notes

        return []

    @staticmethod
    def _lead_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates cutting Lead Hook melodies (C# Minor)."""
        notes = []
        if sec_type == "INTRO":
            return []

        elif sec_type == "VERSE":
            teaser = [
                (0.0, 61, 0.4, 80), (0.5, 63, 0.4, 82), (1.0, 64, 0.8, 85),
                (2.0, 68, 0.5, 88), (2.75, 64, 0.5, 82), (3.5, 61, 1.2, 85)
            ]
            for block in range(int(length / 8.0)):
                t_offset = block * 8.0
                for start, p, dur, vel in teaser:
                    notes.append({"pitch": p, "start_time": t_offset + start, "duration": dur, "velocity": vel})
            return notes

        elif sec_type == "PRE_DROP":
            arp = [61, 64, 66, 68, 71, 73, 76, 78]
            for i in range(24):
                t = i * 0.5
                p = arp[i % len(arp)] + (12 if i >= 16 else 0)
                notes.append({"pitch": p, "start_time": t, "duration": 0.35, "velocity": 75 + i})
            return notes

        elif sec_type == "DROP":
            hook = [
                (0.0, 73, 0.45, 105), (0.5, 73, 0.45, 100), (1.0, 71, 0.45, 102), (1.5, 68, 0.8, 108),
                (2.5, 66, 0.45, 98), (3.0, 68, 0.9, 105),
                (4.0, 73, 0.45, 105), (4.5, 76, 0.45, 110), (5.0, 73, 0.45, 105), (5.5, 71, 0.8, 102),
                (6.5, 68, 0.9, 100), (7.5, 64, 0.5, 95),
                (8.0, 73, 0.45, 105), (8.5, 73, 0.45, 100), (9.0, 71, 0.45, 102), (9.5, 68, 0.8, 108),
                (10.5, 71, 0.45, 105), (11.0, 73, 0.9, 112),
                (12.0, 76, 0.45, 115), (12.5, 75, 0.45, 110), (13.0, 73, 0.45, 108), (13.5, 71, 0.8, 105),
                (14.5, 68, 0.9, 100), (15.5, 61, 0.5, 95)
            ]
            for block in range(2):
                b_offset = block * 16.0
                for start, p, dur, vel in hook:
                    if b_offset + start < length:
                        notes.append({"pitch": p, "start_time": b_offset + start, "duration": dur, "velocity": vel})
            return notes

        elif sec_type == "OUTRO":
            notes.append({"pitch": 73, "start_time": 0.0, "duration": 1.2, "velocity": 75})
            notes.append({"pitch": 68, "start_time": 2.0, "duration": 1.5, "velocity": 65})
            notes.append({"pitch": 61, "start_time": 4.0, "duration": 4.0, "velocity": 55})
            return notes

        return []

    @staticmethod
    def _vocals_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates rhythmic vocal chop triggers."""
        notes = []
        if sec_type == "INTRO":
            notes.append({"pitch": 64, "start_time": 0.0, "duration": 2.5, "velocity": 70})
            notes.append({"pitch": 61, "start_time": 16.0, "duration": 2.5, "velocity": 72})
            return notes

        elif sec_type == "VERSE":
            for bar in range(0, int(length / 4.0), 2):
                notes.append({"pitch": 64, "start_time": bar * 4.0 + 2.5, "duration": 0.6, "velocity": 80})
            return notes

        elif sec_type == "PRE_DROP":
            for i in range(12):
                notes.append({"pitch": 60 + (i % 4), "start_time": float(i), "duration": 0.4, "velocity": 75 + i * 2})
            return notes

        elif sec_type == "DROP":
            for bar in range(int(length / 4.0)):
                bar_start = bar * 4.0
                notes.append({"pitch": 64, "start_time": bar_start + 0.5, "duration": 0.5, "velocity": 95})
                notes.append({"pitch": 61, "start_time": bar_start + 2.5, "duration": 0.5, "velocity": 98})
            return notes

        elif sec_type == "OUTRO":
            notes.append({"pitch": 61, "start_time": 0.0, "duration": 3.0, "velocity": 65})
            return notes

        return []

    @staticmethod
    def _pad_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates ethereal atmospheric pad layers."""
        notes = []
        if sec_type in ["INTRO", "VERSE", "DROP"]:
            for bar in range(0, int(length / 4.0), 4):
                t = bar * 4.0
                dur = min(15.5, length - t)
                notes.append({"pitch": 49, "start_time": t, "duration": dur, "velocity": 65})
                notes.append({"pitch": 56, "start_time": t, "duration": dur, "velocity": 65})
            return notes
        elif sec_type == "PRE_DROP":
            notes.append({"pitch": 49, "start_time": 0.0, "duration": 11.5, "velocity": 85})
            notes.append({"pitch": 56, "start_time": 0.0, "duration": 11.5, "velocity": 85})
            return notes
        elif sec_type == "OUTRO":
            notes.append({"pitch": 49, "start_time": 0.0, "duration": 14.0, "velocity": 60})
            return notes
        return []

    @staticmethod
    def _fx_pattern(sec_type: str, length: float) -> List[Dict[str, Any]]:
        """Generates FX triggers (Pitch 60=Riser, 62=Impact, 64=Downlifter)."""
        notes = []
        if sec_type == "INTRO":
            notes.append({"pitch": 60, "start_time": 28.0, "duration": 4.0, "velocity": 80})
            return notes
        elif sec_type == "PRE_DROP":
            notes.append({"pitch": 60, "start_time": 0.0, "duration": 12.0, "velocity": 105})
            return notes
        elif sec_type == "DROP":
            notes.append({"pitch": 62, "start_time": 0.0, "duration": 4.0, "velocity": 115})
            notes.append({"pitch": 62, "start_time": 16.0, "duration": 4.0, "velocity": 110})
            return notes
        elif sec_type == "OUTRO":
            notes.append({"pitch": 64, "start_time": 0.0, "duration": 8.0, "velocity": 85})
            return notes
        return []

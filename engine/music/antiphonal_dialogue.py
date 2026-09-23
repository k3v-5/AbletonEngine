# engine/music/antiphonal_dialogue.py
"""
Antiphonal Dialogue Engine (Multitrack Call & Response Orchestrator):
Coordinates multi-instrument musical dialogue across the arrangement.
Detects melodic calls and rest windows from the focal track (Lead Vocal or Main Lead)
and dynamically generates rotational, non-overlapping responses distributed across
acoustically eligible responder tracks (Keys stabs, Counter-Leads, Brass hits, Plucks, Bass licks).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set
import math
import logging

from engine.music.models import NoteEvent

logger = logging.getLogger("AntiphonalDialogueEngine")


@dataclass
class DialogueResponseConfig:
    track_index: int
    role: str
    instrument_name: str
    response_type: str        # "CHORD_STAB", "MELODIC_COUNTERPOINT", "BRASS_ACCENT", "TEXTURE_PLUCK", "BASS_LICK"
    pitch_range: Tuple[int, int]
    max_duration_beats: float
    preferred_density: int    # Number of notes per response (1 to 4)


class AntiphonalDialogueEngine:
    """
    Orchestrates multitrack Call & Response across arrangement sections.
    Operates strictly via the ROTATIONAL dialogue policy across acoustically eligible tracks.
    """

    # Acoustically eligible roles for call-and-response interactions
    ELIGIBLE_RESPONDER_ROLES: Dict[str, Dict[str, Any]] = {
        "KEYS": {
            "response_type": "CHORD_STAB",
            "pitch_range": (55, 76),
            "max_duration": 1.5,
            "density": 3,
            "description": "Stabs armónicos rítmicos complementarios"
        },
        "PIANO": {
            "response_type": "CHORD_STAB",
            "pitch_range": (53, 76),
            "max_duration": 1.5,
            "density": 3,
            "description": "Respuestas de acordes y arpegios rápidos"
        },
        "RHODES": {
            "response_type": "CHORD_STAB",
            "pitch_range": (55, 74),
            "max_duration": 1.5,
            "density": 2,
            "description": "Stabs cálidos sincopados"
        },
        "LEAD": {
            "response_type": "MELODIC_COUNTERPOINT",
            "pitch_range": (64, 86),
            "max_duration": 2.0,
            "density": 4,
            "description": "Contramelodía melódica y riffs agudos"
        },
        "SYNTH": {
            "response_type": "MELODIC_COUNTERPOINT",
            "pitch_range": (60, 84),
            "max_duration": 1.5,
            "density": 3,
            "description": "Riffs de sintetizador y arpegios"
        },
        "GUITAR": {
            "response_type": "MELODIC_COUNTERPOINT",
            "pitch_range": (55, 79),
            "max_duration": 1.75,
            "density": 3,
            "description": "Licks de guitarra y rasgueos de respuesta"
        },
        "BRASS": {
            "response_type": "BRASS_ACCENT",
            "pitch_range": (57, 81),
            "max_duration": 1.0,
            "density": 2,
            "description": "Golpes punzantes de metales y acentos"
        },
        "STRINGS": {
            "response_type": "SWELL_ACCENT",
            "pitch_range": (60, 84),
            "max_duration": 2.0,
            "density": 2,
            "description": "Frases cortas de cuerda y staccatos"
        },
        "PLUCK": {
            "response_type": "TEXTURE_PLUCK",
            "pitch_range": (65, 88),
            "max_duration": 1.0,
            "density": 4,
            "description": "Cascadas de plucks y campanas"
        },
        "BASS": {
            "response_type": "BASS_LICK",
            "pitch_range": (36, 55),
            "max_duration": 1.0,
            "density": 2,
            "description": "Licks melódicos y slides de bajo en remates"
        }
    }

    # Ineligible roles that MUST NOT participate in Call & Response dialogue
    INELIGIBLE_ROLES: Set[str] = {
        "DRUMS", "KICK", "SNARE", "HIHAT", "PERCUSSION", "CLAP",
        "SUB", "SUB_BASS", "808_SUB", "FX", "RISER"
    }

    @classmethod
    def filter_eligible_responders(
        cls,
        tracks: List[Dict[str, Any]],
        focal_track_index: int
    ) -> List[DialogueResponseConfig]:
        """
        Audits tracks and extracts only acoustically eligible response instruments,
        filtering out drums, sub-bass foundation, and the focal track itself.
        """
        eligible = []
        for trk in tracks:
            t_idx = trk.get("index", 0)
            if t_idx == focal_track_index:
                continue

            role = str(trk.get("role", "")).upper()
            name = str(trk.get("name", "")).upper()

            # Check explicit ineligibility
            if any(ir in role or ir in name for ir in cls.INELIGIBLE_ROLES):
                continue

            # Identify matching role profile
            matched_role = None
            for e_role in cls.ELIGIBLE_RESPONDER_ROLES:
                if e_role in role or e_role in name:
                    matched_role = e_role
                    break

            if not matched_role:
                # Secondary detection based on name
                if any(w in name for w in ("KEY", "PIANO", "CHORD")):
                    matched_role = "KEYS"
                elif any(w in name for w in ("LEAD", "SYNTH", "SOLO")):
                    matched_role = "LEAD"
                elif any(w in name for w in ("BRASS", "HORN")):
                    matched_role = "BRASS"
                elif any(w in name for w in ("PLUCK", "BELL")):
                    matched_role = "PLUCK"
                elif any(w in name for w in ("GUITAR", "STRUM")):
                    matched_role = "GUITAR"

            if matched_role:
                cfg = cls.ELIGIBLE_RESPONDER_ROLES[matched_role]
                eligible.append(DialogueResponseConfig(
                    track_index=t_idx,
                    role=matched_role,
                    instrument_name=trk.get("name", f"Track {t_idx}"),
                    response_type=cfg["response_type"],
                    pitch_range=cfg["pitch_range"],
                    max_duration_beats=cfg["max_duration"],
                    preferred_density=cfg["density"]
                ))

        return eligible

    @classmethod
    def detect_focal_rest_windows(
        cls,
        focal_notes: List[Dict[str, Any]],
        total_beats: float,
        min_rest_beats: float = 1.0,
        guard_margin_beats: float = 0.05
    ) -> List[Dict[str, float]]:
        """
        Analyzes the focal melodic track notes and identifies precise rest pockets
        (pauses between phrases) where responder instruments can safely converse.
        """
        if not focal_notes:
            # If focal track is entirely silent or not populated, create default phrase rests
            bars = max(1, int(total_beats / 4.0))
            rests = []
            for b in range(0, bars, 2):
                # Rest on beats 3 and 4 of every 2nd bar
                r_start = float((b + 1) * 4.0 + 2.0)
                r_end = float((b + 2) * 4.0)
                if r_end <= total_beats:
                    rests.append({
                        "start_beat": r_start + guard_margin_beats,
                        "end_beat": r_end - guard_margin_beats,
                        "duration": (r_end - r_start) - (2 * guard_margin_beats)
                    })
            return rests

        sorted_notes = sorted(
            focal_notes,
            key=lambda n: float(n.get("start_time", n.get("start", 0.0)))
        )

        rest_windows = []
        # Check initial rest before first note
        first_st = float(sorted_notes[0].get("start_time", sorted_notes[0].get("start", 0.0)))
        if first_st >= min_rest_beats:
            rest_windows.append({
                "start_beat": round(guard_margin_beats, 3),
                "end_beat": round(first_st - guard_margin_beats, 3),
                "duration": round(first_st - (2 * guard_margin_beats), 3)
            })

        for i in range(len(sorted_notes) - 1):
            curr_n = sorted_notes[i]
            next_n = sorted_notes[i + 1]

            c_st = float(curr_n.get("start_time", curr_n.get("start", 0.0)))
            c_dur = float(curr_n.get("duration", 1.0))
            c_end = c_st + c_dur

            n_st = float(next_n.get("start_time", next_n.get("start", 0.0)))

            gap = n_st - c_end
            if gap >= min_rest_beats:
                rest_windows.append({
                    "start_beat": round(c_end + guard_margin_beats, 3),
                    "end_beat": round(n_st - guard_margin_beats, 3),
                    "duration": round(gap - (2 * guard_margin_beats), 3)
                })

        # Check rest after last note up to section end
        last_n = sorted_notes[-1]
        last_st = float(last_n.get("start_time", last_n.get("start", 0.0)))
        last_end = last_st + float(last_n.get("duration", 1.0))
        if (total_beats - last_end) >= min_rest_beats:
            rest_windows.append({
                "start_beat": round(last_end + guard_margin_beats, 3),
                "end_beat": round(total_beats - guard_margin_beats, 3),
                "duration": round(total_beats - last_end - (2 * guard_margin_beats), 3)
            })

        return rest_windows

    @classmethod
    def generate_antiphonal_motif(
        cls,
        responder_cfg: DialogueResponseConfig,
        window: Dict[str, float],
        scale_pitches: List[int],
        root_pitch: int = 60,
        complexity_level: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generates a tailored response motif based on the responder's acoustic profile,
        confined strictly within window['start_beat'] and window['end_beat'].
        """
        w_start = window["start_beat"]
        w_dur = window["duration"]
        p_low, p_high = responder_cfg.pitch_range

        # Filter valid scale pitches within range
        valid_pitches = [p for p in scale_pitches if p_low <= p <= p_high]
        if not valid_pitches:
            valid_pitches = [root_pitch]

        response_type = responder_cfg.response_type
        notes = []

        if response_type == "CHORD_STAB":
            # 2 to 3-voice harmonic stab (e.g. root + 3rd + 5th or 7th)
            triad = valid_pitches[:3] if len(valid_pitches) >= 3 else [valid_pitches[0]]
            stab_dur = min(0.5, w_dur * 0.45)
            # Syncopated start: slightly off the downbeat of the window
            t_offset = 0.25 if w_dur > 1.25 else 0.0
            for p in triad:
                notes.append({
                    "pitch": int(p),
                    "start_time": round(w_start + t_offset, 3),
                    "duration": round(stab_dur, 3),
                    "velocity": 95,
                    "mute": False
                })
            # Second trailing stab if window allows
            if w_dur >= 1.5 and complexity_level >= 2:
                for p in triad:
                    notes.append({
                        "pitch": int(p),
                        "start_time": round(w_start + t_offset + 0.75, 3),
                        "duration": round(stab_dur * 0.8, 3),
                        "velocity": 85,
                        "mute": False
                    })

        elif response_type in ("MELODIC_COUNTERPOINT", "TEXTURE_PLUCK"):
            # Cascading run of 2-4 melodic notes
            note_count = min(responder_cfg.preferred_density, max(2, int(w_dur / 0.5)))
            step_dur = min(0.375, (w_dur * 0.85) / note_count)
            # Melodic contour (descending or wave)
            sampled_pitches = valid_pitches[-note_count:] if len(valid_pitches) >= note_count else (valid_pitches * 2)[:note_count]
            if len(sampled_pitches) > 1:
                sampled_pitches = list(reversed(sampled_pitches))  # Classic resolving descent

            for idx, p in enumerate(sampled_pitches):
                notes.append({
                    "pitch": int(p),
                    "start_time": round(w_start + (idx * step_dur), 3),
                    "duration": round(step_dur * 0.85, 3),
                    "velocity": 90 - (idx * 4),
                    "mute": False
                })

        elif response_type == "BRASS_ACCENT":
            # Punchy staccato hit
            hit_dur = 0.25
            root_p = valid_pitches[len(valid_pitches) // 2]
            fifth_p = root_p + 7 if (root_p + 7) <= p_high else root_p - 5
            for p in (root_p, fifth_p):
                notes.append({
                    "pitch": int(p),
                    "start_time": round(w_start + 0.25, 3),
                    "duration": round(hit_dur, 3),
                    "velocity": 110,
                    "mute": False
                })

        elif response_type == "BASS_LICK":
            # Syncopated slide in low register
            lick_count = min(2, len(valid_pitches))
            lick_pitches = valid_pitches[:lick_count]
            step_dur = 0.25
            for idx, p in enumerate(lick_pitches):
                notes.append({
                    "pitch": int(p),
                    "start_time": round(w_start + (idx * step_dur), 3),
                    "duration": round(step_dur * 0.9, 3),
                    "velocity": 105,
                    "mute": False
                })
        else:
            # General fallback: single clean response note
            notes.append({
                "pitch": int(valid_pitches[0]),
                "start_time": round(w_start, 3),
                "duration": round(min(1.0, w_dur * 0.8), 3),
                "velocity": 90,
                "mute": False
            })

        return notes

    @classmethod
    def orchestrate_rotational_dialogue(
        cls,
        tracks: List[Dict[str, Any]],
        focal_track_index: int,
        focal_notes: List[Dict[str, Any]],
        total_beats: float,
        scale_root_pitch: int = 60,
        scale_intervals: Optional[List[int]] = None,
        complexity_level: int = 3
    ) -> Dict[str, Any]:
        """
        Executes the user-approved ROTATIONAL Call & Response policy:
        1. Filters tracks to identify only acoustically eligible response instruments.
        2. Detects focal rest windows.
        3. Rotates sequentially through eligible responders (Turn 1 -> Track A, Turn 2 -> Track B, etc.).
        4. Injects non-overlapping notes partitioned by track.
        """
        if scale_intervals is None:
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # Major default

        # Build full MIDI pitch gamut for the scale across octaves 2 to 7
        scale_pitches = []
        for octave in range(2, 8):
            base = octave * 12
            for interval in scale_intervals:
                p = base + interval
                if 24 <= p <= 108:
                    scale_pitches.append(p)

        eligible_responders = cls.filter_eligible_responders(tracks, focal_track_index)
        if not eligible_responders:
            logger.warning("No eligible response instruments found for Antiphonal Dialogue.")
            return {
                "status": "NO_ELIGIBLE_RESPONDERS",
                "policy": "ROTATIONAL",
                "focal_track_index": focal_track_index,
                "dialogue_matrix": {},
                "total_responses": 0,
                "summary": "No se encontraron pistas armónicas/melódicas secundarias elegibles."
            }

        rest_windows = cls.detect_focal_rest_windows(focal_notes, total_beats)
        dialogue_matrix: Dict[int, List[Dict[str, Any]]] = {
            r.track_index: [] for r in eligible_responders
        }

        total_responses = 0
        rotation_idx = 0
        dialogue_events = []

        for window in rest_windows:
            if window["duration"] < 0.75:
                continue

            responder = eligible_responders[rotation_idx % len(eligible_responders)]
            response_notes = cls.generate_antiphonal_motif(
                responder_cfg=responder,
                window=window,
                scale_pitches=scale_pitches,
                root_pitch=scale_root_pitch,
                complexity_level=complexity_level
            )

            if response_notes:
                dialogue_matrix[responder.track_index].extend(response_notes)
                total_responses += 1
                dialogue_events.append({
                    "window_start": window["start_beat"],
                    "window_end": window["end_beat"],
                    "responder_track": responder.track_index,
                    "responder_name": responder.instrument_name,
                    "responder_role": responder.role,
                    "response_type": responder.response_type,
                    "note_count": len(response_notes)
                })
                # Advance strictly to next instrument in rotation
                rotation_idx += 1

        summary_lines = [
            f"• **Pista Focal (Líder):** Track {focal_track_index}",
            f"• **Instrumentos Elegibles en Rotación:** {', '.join([r.instrument_name for r in eligible_responders])}",
            f"• **Ventanas de Pausa Detectadas:** {len(rest_windows)}",
            f"• **Total de Respuestas Antifonales Desplegadas:** {total_responses}"
        ]

        return {
            "status": "SUCCESS",
            "policy": "ROTATIONAL",
            "focal_track_index": focal_track_index,
            "eligible_responders_count": len(eligible_responders),
            "eligible_responders": [r.__dict__ for r in eligible_responders],
            "dialogue_matrix": dialogue_matrix,
            "dialogue_events": dialogue_events,
            "total_responses": total_responses,
            "summary": "\n".join(summary_lines)
        }

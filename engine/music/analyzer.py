"""
engine/music/analyzer.py
MusicAnalyzer: Analyzes Live session tracks, cue points, and MIDI clips
to abstract a complete intermediate SongState representation.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from .song_state import SongState, MusicalSection, MelodicState, LyricBlueprint, ProsodicConstraint

logger = logging.getLogger(__name__)

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def pitch_to_name(pitch: int) -> str:
    """Converts MIDI pitch number (e.g. 60) to scientific pitch name (e.g. 'C4')."""
    p_cl = pitch % 12
    octv = (pitch // 12) - 1
    return f"{PITCH_NAMES[p_cl]}{octv}"


class MusicAnalyzer:
    """Extracts high-level musical abstractions from Ableton Live project data."""

    @classmethod
    def analyze_melody_clip(cls, notes: List[Dict[str, Any]], track_name: str = "Lead") -> MelodicState:
        """Analyzes a list of MIDI notes to extract range, contour, and density."""
        if not notes:
            return MelodicState(track_name=track_name, notes_count=0)

        pitches = [int(n.get("pitch", 60)) for n in notes]
        min_p = min(pitches)
        max_p = max(pitches)
        range_str = f"{pitch_to_name(min_p)}-{pitch_to_name(max_p)}"

        # Density: notes per bar
        total_time = max(float(n.get("start_time", 0.0)) + float(n.get("duration", 1.0)) for n in notes)
        bars_count = max(1.0, total_time / 4.0)
        density = min(1.0, len(notes) / (bars_count * 8.0))

        # Contour analysis: compare first third vs last third average pitch
        sorted_notes = sorted(notes, key=lambda x: float(x.get("start_time", 0.0)))
        n_third = max(1, len(sorted_notes) // 3)
        first_avg = sum(n["pitch"] for n in sorted_notes[:n_third]) / n_third
        last_avg = sum(n["pitch"] for n in sorted_notes[-n_third:]) / n_third

        if last_avg - first_avg > 3:
            contour = "ascending"
        elif first_avg - last_avg > 3:
            contour = "descending"
        else:
            contour = "wave"

        # Hook detection: high repetition / density in upper register
        is_hook = (max_p >= 69 and density > 0.40)

        return MelodicState(
            track_name=track_name,
            pitch_range=range_str,
            lowest_pitch=min_p,
            highest_pitch=max_p,
            density=density,
            rhythmic_style="syncopated" if density > 0.35 else "straight",
            contour=contour,
            hook=is_hook,
            notes_count=len(notes)
        )

    @classmethod
    def extract_prosodic_constraints(cls, notes: List[Dict[str, Any]], section_bars: Tuple[int, int]) -> LyricBlueprint:
        """
        Groups melodic notes into musical phrases separated by rests (> 0.75 beats)
        and derives strict syllable and stress constraints.
        """
        sorted_notes = sorted(notes, key=lambda x: float(x.get("start_time", 0.0)))
        phrases: List[List[Dict[str, Any]]] = []
        current_phrase: List[Dict[str, Any]] = []

        last_end = 0.0
        for n in sorted_notes:
            st = float(n.get("start_time", 0.0))
            dur = float(n.get("duration", 0.5))
            if current_phrase and (st - last_end >= 0.75):
                phrases.append(current_phrase)
                current_phrase = [n]
            else:
                current_phrase.append(n)
            last_end = st + dur

        if current_phrase:
            phrases.append(current_phrase)

        constraints: List[ProsodicConstraint] = []
        syllables_list: List[int] = []

        for p_idx, phrase_notes in enumerate(phrases):
            syl_count = len(phrase_notes)
            syllables_list.append(syl_count)

            # Find peak note in phrase
            peak_note = max(phrase_notes, key=lambda x: int(x.get("pitch", 0)))
            peak_idx = phrase_notes.index(peak_note) + 1  # 1-indexed syllable

            # Detect notes on strong beats (beats 0.0 and 2.0 within bar -> 1st and 3rd beats)
            stressed = []
            for i, n in enumerate(phrase_notes):
                beat_in_bar = float(n.get("start_time", 0.0)) % 4.0
                if abs(beat_in_bar - 0.0) < 0.25 or abs(beat_in_bar - 2.0) < 0.25:
                    stressed.append(i + 1)

            constraints.append(ProsodicConstraint(
                phrase_index=p_idx + 1,
                bars=section_bars,
                target_syllables=syl_count,
                stressed_syllables=stressed,
                highest_note_pitch=int(peak_note.get("pitch", 60)),
                highest_note_syllable_idx=peak_idx,
                preferred_vowels_on_peak=["a", "o", "e"] if peak_note.get("pitch", 60) >= 69 else ["a", "e", "i", "o", "u"],
                phrase_type="emotional_peak" if peak_note.get("pitch", 60) >= 71 else "narrative"
            ))

        return LyricBlueprint(
            section_name="Analyzed Section",
            bars=section_bars,
            rhyme_scheme="AABB" if len(phrases) == 4 else "ABAB",
            phrases_count=len(phrases),
            syllables_per_phrase=syllables_list,
            narrative_role="main_hook" if any(c.phrase_type == "emotional_peak" for c in constraints) else "situation",
            emotional_theme="longing",
            prosodic_constraints=constraints
        )

    @classmethod
    def analyze_session(cls, conn: Any, title: str = "Ableton Production") -> SongState:
        """
        Builds a full SongState by querying session tempo, locators, and tracks from Live.
        """
        # 1. Session info
        s_info = conn.send_command("get_session_info", {})
        s_data = s_info.get("result", s_info)
        tempo = float(s_data.get("tempo", 120.0))

        # 2. Locators / Cue points
        cue_res = conn.send_command("get_cue_points", {})
        c_data = cue_res.get("result", cue_res) if isinstance(cue_res, dict) else {}
        cues = c_data.get("cue_points", []) if isinstance(c_data, dict) else []

        sections: List[MusicalSection] = []
        for i, cue in enumerate(cues):
            name = cue.get("name", f"Section {i+1}")
            st_beat = float(cue.get("time", 0.0))
            st_bar = int(st_beat / 4.0)

            end_beat = float(cues[i+1].get("time", st_beat + 32.0)) if i + 1 < len(cues) else st_beat + 32.0
            end_bar = int(end_beat / 4.0)

            # Determine mood and energy
            energy = 0.90 if any(h in name.lower() for h in ["drop", "climax"]) else (
                0.35 if any(l in name.lower() for l in ["intro", "outro", "vacuum"]) else 0.65
            )
            mood = "cathartic" if energy > 0.8 else ("intimate" if energy < 0.4 else "tension")

            sections.append(MusicalSection(
                name=name,
                bars=(st_bar, end_bar),
                energy=energy,
                mood=mood,
                narrative_role="central_message" if energy > 0.8 else "introduce_situation"
            ))

        if not sections:
            sections.append(MusicalSection(name="Main", bars=(0, 32), energy=0.60))

        # 3. Installed tracks
        track_count = int(s_data.get("track_count", 0))
        tracks_installed = []
        for t_idx in range(min(track_count, 18)):
            try:
                t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                t_data = t_info.get("result", t_info)
                t_name = t_data.get("name")
                if t_name:
                    tracks_installed.append(t_name)
            except Exception:
                pass

        return SongState(
            title=title,
            tempo=tempo,
            key="F",
            scale="minor",
            meter="4/4",
            sections=sections,
            tracks_installed=tracks_installed,
            overall_energy_curve=[s.energy for s in sections]
        )

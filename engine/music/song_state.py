"""
engine/music/song_state.py
Authoritative Intermediate Musical Representation (Musical OS Layer).

Provides the unified schema that decouples high-level creative AI intent
from low-level Ableton DAW implementation:
- Nivel 1: Estado Técnico (Pistas, Plugins, Racks, Automatizaciones en Live).
- Nivel 2: Estado Musical (SongState: Tempo, Armonía, Rango Melódico, Densidad, Energía).
- Nivel 3: Estado Narrativo & Prosódico (Mood, Tensión, LyricBlueprint, Acentuación).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class ProsodicConstraint:
    """Constraints imposed by a melodic line onto prospective lyric text."""
    phrase_index: int
    bars: Tuple[int, int]
    target_syllables: int
    stressed_syllables: List[int] = field(default_factory=list)  # 1-indexed (e.g. [2, 6])
    highest_note_pitch: Optional[int] = None                     # MIDI pitch (e.g. 73 for C#5)
    highest_note_syllable_idx: Optional[int] = None              # Which syllable falls on peak
    preferred_vowels_on_peak: List[str] = field(default_factory=lambda: ["a", "o", "e"]) # Open vowels
    phrase_type: str = "emotional_peak"                          # 'intimate', 'rising', 'emotional_peak', 'resolution'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phrase_index": self.phrase_index,
            "bars": list(self.bars),
            "target_syllables": self.target_syllables,
            "stressed_syllables": self.stressed_syllables,
            "highest_note_pitch": self.highest_note_pitch,
            "highest_note_syllable_idx": self.highest_note_syllable_idx,
            "preferred_vowels_on_peak": self.preferred_vowels_on_peak,
            "phrase_type": self.phrase_type
        }


@dataclass
class LyricBlueprint:
    """Complete lyric generation specification for a musical section."""
    section_name: str
    bars: Tuple[int, int]
    rhyme_scheme: str = "AABB"                                   # 'AABB', 'ABAB', 'ABCB', etc.
    phrases_count: int = 4
    syllables_per_phrase: List[int] = field(default_factory=list)
    narrative_role: str = "main_hook"                            # 'atmosphere', 'situation', 'tension', 'hook', 'resolution'
    emotional_theme: str = "longing"                             # 'nostalgia', 'euphoria', 'vulnerability', 'defiance'
    prosodic_constraints: List[ProsodicConstraint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "bars": list(self.bars),
            "rhyme_scheme": self.rhyme_scheme,
            "phrases_count": self.phrases_count,
            "syllables_per_phrase": self.syllables_per_phrase,
            "narrative_role": self.narrative_role,
            "emotional_theme": self.emotional_theme,
            "prosodic_constraints": [p.to_dict() for p in self.prosodic_constraints]
        }


@dataclass
class MelodicState:
    """Melodic characteristics of a musical section."""
    track_name: str = "Lead"
    pitch_range: str = "C#4-A4"
    lowest_pitch: int = 61
    highest_pitch: int = 69
    density: float = 0.35                                        # 0.0 (sparse) to 1.0 (busy)
    rhythmic_style: str = "syncopated"                           # 'straight', 'syncopated', 'triplet', 'legato'
    contour: str = "ascending"                                   # 'ascending', 'descending', 'arch', 'wave', 'static'
    hook: bool = False
    notes_count: int = 16

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_name": self.track_name,
            "pitch_range": self.pitch_range,
            "lowest_pitch": self.lowest_pitch,
            "highest_pitch": self.highest_pitch,
            "density": round(self.density, 2),
            "rhythmic_style": self.rhythmic_style,
            "contour": self.contour,
            "hook": self.hook,
            "notes_count": self.notes_count
        }


@dataclass
class MusicalSection:
    """High-level semantic definition of a song section."""
    name: str
    bars: Tuple[int, int]
    energy: float = 0.50                                         # 0.0 to 1.0
    harmony: List[str] = field(default_factory=list)             # e.g. ["F#m", "D", "A", "E"]
    melodic_density: float = 0.30
    melody: Optional[MelodicState] = None
    mood: str = "intimate"
    narrative_role: str = "introduce_situation"
    lyric_blueprint: Optional[LyricBlueprint] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "bars": list(self.bars),
            "energy": round(self.energy, 2),
            "harmony": self.harmony,
            "melodic_density": round(self.melodic_density, 2),
            "mood": self.mood,
            "narrative_role": self.narrative_role
        }
        if self.melody:
            d["melody"] = self.melody.to_dict()
        if self.lyric_blueprint:
            d["lyric_blueprint"] = self.lyric_blueprint.to_dict()
        return d


@dataclass
class SongState:
    """
    Authoritative Intermediate Representation of the Complete Song.
    Acts as the source of truth between LLM and Ableton Live.
    """
    title: str = "Untitled Project"
    tempo: float = 120.0
    key: str = "C"
    scale: str = "minor"
    meter: str = "4/4"
    style_tags: List[str] = field(default_factory=lambda: ["electronic", "alternative"])
    sections: List[MusicalSection] = field(default_factory=list)
    tracks_installed: List[str] = field(default_factory=list)
    overall_energy_curve: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song": {
                "title": self.title,
                "tempo": self.tempo,
                "key": f"{self.key} {self.scale}",
                "meter": self.meter,
                "style": self.style_tags
            },
            "sections": [s.to_dict() for s in self.sections],
            "tracks_installed": self.tracks_installed,
            "overall_energy_curve": [round(e, 2) for e in self.overall_energy_curve]
        }

    def to_llm_prompt_summary(self) -> str:
        """
        Formats a clean, token-efficient summary for LLM context injection.
        Gives the LLM the exact musical reality without overwhelming it with DAW trivia.
        """
        lines = [
            f"=== SONG STATE: '{self.title}' ===",
            f"Tempo: {self.tempo} BPM | Key: {self.key} {self.scale} | Meter: {self.meter}",
            f"Style: {', '.join(self.style_tags)}",
            "\n--- SECTIONS & MUSICAL ARCHITECTURE ---"
        ]
        for s in self.sections:
            lines.append(f"• [{s.name}] Bars {s.bars[0]}-{s.bars[1]} | Energy: {s.energy:.2f} | Mood: {s.mood}")
            if s.harmony:
                lines.append(f"  Harmony: {' -> '.join(s.harmony)}")
            if s.melody:
                lines.append(
                    f"  Melody: Range {s.melody.pitch_range}, Style {s.melody.rhythmic_style}, "
                    f"Contour {s.melody.contour}{' (HOOK)' if s.melody.hook else ''}"
                )
            if s.lyric_blueprint:
                lb = s.lyric_blueprint
                lines.append(
                    f"  Lyrics: {lb.phrases_count} phrases, Rhyme {lb.rhyme_scheme}, "
                    f"Syllables {lb.syllables_per_phrase}, Role: {lb.narrative_role}"
                )
        return "\n".join(lines)

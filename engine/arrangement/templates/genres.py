# engine/arrangement/templates/genres.py
from dataclasses import dataclass, field
from typing import Dict, Any, List
from engine.arrangement.models.section import Section
from engine.arrangement.templates.structures import StructureLibrary

@dataclass
class GenreArrangementProfile:
    genre: str
    default_tempo: float
    typical_structure: str
    preferred_phrase_bars: int
    drop_count: int
    density_budgets: Dict[str, float]
    humanization_levels: Dict[str, float]
    role_priorities: List[str]

GENRE_ARRANGEMENT_PROFILES: Dict[str, GenreArrangementProfile] = {
    "melodic_techno": GenreArrangementProfile(
        genre="melodic_techno",
        default_tempo=126.0,
        typical_structure="progressive",
        preferred_phrase_bars=16,
        drop_count=2,
        density_budgets={"intro": 0.35, "build": 0.65, "drop": 0.90, "breakdown": 0.40, "outro": 0.30},
        humanization_levels={"drums": 0.25, "bass": 0.20, "lead": 0.40, "chords": 0.45},
        role_priorities=["kick", "bass", "lead", "chords", "hihat_closed", "percussion", "pad", "arp"]
    ),
    "peak_time_techno": GenreArrangementProfile(
        genre="peak_time_techno",
        default_tempo=132.0,
        typical_structure="club",
        preferred_phrase_bars=16,
        drop_count=2,
        density_budgets={"intro": 0.40, "build": 0.75, "drop": 0.95, "breakdown": 0.35, "outro": 0.35},
        humanization_levels={"drums": 0.15, "bass": 0.15, "lead": 0.25, "chords": 0.20},
        role_priorities=["kick", "sub_bass", "rumble", "snare", "clap", "hihat_open", "lead"]
    ),
    "deep_house": GenreArrangementProfile(
        genre="deep_house",
        default_tempo=122.0,
        typical_structure="progressive",
        preferred_phrase_bars=16,
        drop_count=2,
        density_budgets={"intro": 0.40, "build": 0.60, "drop": 0.80, "breakdown": 0.45, "outro": 0.35},
        humanization_levels={"drums": 0.35, "bass": 0.30, "chords": 0.50, "lead": 0.45},
        role_priorities=["kick", "bass", "chords", "hihat_closed", "vocal", "pad"]
    ),
    "synthwave": GenreArrangementProfile(
        genre="synthwave",
        default_tempo=115.0,
        typical_structure="radio",
        preferred_phrase_bars=8,
        drop_count=2,
        density_budgets={"intro": 0.30, "build": 0.65, "drop": 0.85, "breakdown": 0.40, "outro": 0.30},
        humanization_levels={"drums": 0.20, "bass": 0.20, "lead": 0.35, "chords": 0.40},
        role_priorities=["kick", "snare", "bass", "arp", "lead", "pad"]
    )
}

class GenreTemplates:
    PROFILES = GENRE_ARRANGEMENT_PROFILES

    @classmethod
    def get_genre_template(cls, genre: str = "melodic_techno") -> List[Section]:
        clean_genre = str(genre).lower().strip()
        profile = cls.PROFILES.get(clean_genre, cls.PROFILES["melodic_techno"])
        return StructureLibrary.get_template(profile.typical_structure)


def get_genre_profile(genre: str = "melodic_techno") -> GenreArrangementProfile:
    return GENRE_ARRANGEMENT_PROFILES.get(str(genre).lower().strip(), GENRE_ARRANGEMENT_PROFILES["melodic_techno"])

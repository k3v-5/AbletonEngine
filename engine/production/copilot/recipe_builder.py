# engine/production/copilot/recipe_builder.py
"""
Copilot Production Recipe Builder (Single Responsibility Principle - SRP):
Builds ProductionRecipe blueprints from guided session data dictionaries.
"""

from typing import Any, Dict
from engine.production.recipe_engine import ProductionRecipe, RecipeSection, TrackBlueprint


class CopilotRecipeBuilder:
    """Constructs validated ProductionRecipe instances from session state."""

    @classmethod
    def build_recipe_from_session(cls, session: Any) -> ProductionRecipe:
        """Assembles a ProductionRecipe from a CopilotGuidedSession instance or session data dict."""
        data = session.data if hasattr(session, "data") else session
        tracks = data.get("tracks", [])
        sections = data.get("sections", [])
        key = data.get("key", "F")
        scale = data.get("scale", "natural_minor")
        bpm = float(data.get("bpm", 120.0))

        recipe_tracks = []
        for trk in tracks:
            recipe_tracks.append(TrackBlueprint(
                track_index=trk.get("index", 0),
                name=trk.get("name", "Track"),
                role=str(trk.get("role", "instrument")).lower(),
                instrument_name=trk.get("instrument", trk.get("name", "Instrument"))
            ))

        recipe_sections = []
        current_bar = 0
        for idx, s in enumerate(sections):
            s_name = s.get("name", f"Section {idx+1}")
            s_bars = int(s.get("bars", 8))
            recipe_sections.append(RecipeSection(
                name=s_name,
                start_bar=current_bar,
                length_bars=s_bars,
                active_roles=[t.role for t in recipe_tracks]
            ))
            current_bar += s_bars

        genre_ref = data.get("genre", "Modern Production")
        user_chords = data.get("chord_progression")
        if not user_chords:
            genre_lower = str(genre_ref).lower()
            is_minor = "minor" in scale.lower()
            if any(w in genre_lower for w in ["dubstep", "riddim", "brostep", "metal", "dnb", "drum_and_bass", "techno", "ambient"]):
                user_chords = [f"{key}m"] if is_minor else [f"{key}"]
            else:
                user_chords = [f"{key}m"] if is_minor else [f"{key}"]

        return ProductionRecipe(
            title=data.get("title", "Copilot Guided Production"),
            genre_reference=genre_ref,
            key=key,
            scale=scale,
            chord_progression=user_chords,
            bpm=bpm,
            tracks=recipe_tracks,
            sections=recipe_sections
        )

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

        return ProductionRecipe(
            title="Copilot Guided Production",
            genre_reference="Modern Production",
            key=key,
            scale=scale,
            chord_progression=["Fm", "Db", "Ab", "Eb"],
            bpm=bpm,
            tracks=recipe_tracks,
            sections=recipe_sections
        )

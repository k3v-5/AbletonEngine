# engine/production/copilot/phases/phase_6/recipes.py
"""
Phase 6 Recipe Builder:
Builds a production recipe instance from current Copilot session state.
"""
from typing import Any
from engine.production.recipe_engine import ProductionRecipe, RecipeSection, TrackBlueprint


class Phase6RecipeBuilder:
    """Constructs ProductionRecipe blueprints from guided session data."""

    @staticmethod
    def build_recipe_from_session(session: Any) -> ProductionRecipe:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        key = session.data.get("key", "F")
        scale = session.data.get("scale", "natural_minor")
        bpm = float(session.data.get("bpm", 120.0))

        recipe_tracks = []
        for trk in tracks:
            recipe_tracks.append(TrackBlueprint(
                track_index=trk["index"],
                name=trk["name"],
                role=trk["role"].lower(),
                instrument_name=trk.get("instrument", trk["name"])
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

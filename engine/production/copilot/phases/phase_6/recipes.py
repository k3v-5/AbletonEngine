# engine/production/copilot/phases/phase_6/recipes.py
"""
Phase 6 Recipe Builder:
Builds a production recipe instance from current Copilot session state.
"""
from typing import Any
from engine.production.recipe_engine import ProductionRecipe
from engine.production.copilot.recipe_builder import CopilotRecipeBuilder


class Phase6RecipeBuilder:
    """Constructs ProductionRecipe blueprints from guided session data."""

    @staticmethod
    def build_recipe_from_session(session: Any) -> ProductionRecipe:
        return CopilotRecipeBuilder.build_recipe_from_session(session)


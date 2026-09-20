# engine/production/copilot/phases/phase_6_composition.py
"""
Phase 6: Multi-section harmonic, rhythmic, and melodic composition in arrangement timeline.
Facade module maintaining 100% backward compatibility for Phase6CompositionHandler.
Implementation refactored into modular subpackage engine.production.copilot.phases.phase_6.
"""
from engine.production.copilot.phases.phase_6.handler import Phase6CompositionHandler
from engine.production.copilot.phases.phase_6.parser import Phase6Parser
from engine.production.copilot.phases.phase_6.gatekeepers import Phase6Gatekeepers
from engine.production.copilot.phases.phase_6.arranger import Phase6Arranger
from engine.production.copilot.phases.phase_6.prompts import Phase6Prompts
from engine.production.copilot.phases.phase_6.recipes import Phase6RecipeBuilder

__all__ = [
    "Phase6CompositionHandler",
    "Phase6Parser",
    "Phase6Gatekeepers",
    "Phase6Arranger",
    "Phase6Prompts",
    "Phase6RecipeBuilder",
]

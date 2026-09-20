# engine/production/copilot/phases/phase_6/__init__.py
"""
Phase 6: Multi-section harmonic, rhythmic, and melodic composition package.
Modularized components:
- parser: AI composition JSON/file parser and note finder
- gatekeepers: explicit composition, completeness, outro synth continuity, pre-drop vacuum
- arranger: arrangement stamping, single track deployer, governance retry
- prompts: interactive prompt builder
- recipes: recipe blueprint builder
- handler: Phase6CompositionHandler facade
"""
from .handler import Phase6CompositionHandler
from .parser import Phase6Parser
from .gatekeepers import Phase6Gatekeepers
from .arranger import Phase6Arranger
from .prompts import Phase6Prompts
from .recipes import Phase6RecipeBuilder
from .turnaround_engine import TurnaroundEngine

__all__ = [
    "Phase6CompositionHandler",
    "Phase6Parser",
    "Phase6Gatekeepers",
    "Phase6Arranger",
    "Phase6Prompts",
    "Phase6RecipeBuilder",
    "TurnaroundEngine",
]

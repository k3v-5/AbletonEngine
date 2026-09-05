"""
Ableton Production Intelligence Engine - Fase 3: Arrangement Engine.
Song Structure, Energy, Sections, Transitions, Roles, and Multi-Drop Evolution.
"""
from .models.section import Section, SectionType
from .models.song import Song
from .energy.dimensions import EnergyDimensions
from .energy.curve import EnergyCurve, EnergyCurveGenerator
from .templates.structures import StructureLibrary
from .templates.genres import GenreTemplates
from .roles.matrix import RoleMatrix, SectionRoleMap, RoleSlot, STANDARD_ROLES
from .roles.orchestrator import RoleOrchestrator
from .transitions.models import TransitionDescriptor, TransitionType
from .transitions.pre_drop import PreDropGenerator
from .transitions.engine import TransitionEngine
from .transitions.automation import TransitionAutomationEngine, AutomationCurveType
from .drops.engine import DropDifferentiationEngine
from .narrative.arc import NarrativeArc
from .variation.planner import VariationPlanner, VariationDirective
from .variation.motifs import MotifEvolutionManager
from .density import DensityController
from .linter.comparison import SectionComparator
from .linter.linter import ArrangementLinter, LintIssue
from .scoring import ArrangementScorer
from .locking import ArrangementLockManager
from .compiler import ArrangementCompiler
from .generator import ArrangementGenerator

__all__ = [
    "Section", "SectionType", "Song",
    "EnergyDimensions", "EnergyCurve", "EnergyCurveGenerator",
    "StructureLibrary", "GenreTemplates",
    "RoleMatrix", "SectionRoleMap", "RoleSlot", "STANDARD_ROLES",
    "RoleOrchestrator",
    "TransitionDescriptor", "TransitionType", "PreDropGenerator", "TransitionEngine",
    "TransitionAutomationEngine", "AutomationCurveType",
    "DropDifferentiationEngine", "NarrativeArc",
    "VariationPlanner", "VariationDirective", "MotifEvolutionManager",
    "DensityController",
    "SectionComparator", "ArrangementLinter", "LintIssue",
    "ArrangementScorer", "ArrangementLockManager",
    "ArrangementCompiler", "ArrangementGenerator"
]

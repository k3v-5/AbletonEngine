# engine/production/copilot/phases/__init__.py
"""
Modular Phase Handlers for Copilot Guided Session.
Encapsulates each stage of interactive music production into dedicated, testable handlers.
"""

from .base import BasePhaseHandler
from .phase_1_tracks import Phase1TracksHandler
from .phase_2_sections import Phase2SectionsHandler

__all__ = [
    "BasePhaseHandler",
    "Phase1TracksHandler",
    "Phase2SectionsHandler",
]

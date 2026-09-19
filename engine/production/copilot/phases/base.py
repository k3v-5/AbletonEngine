# engine/production/copilot/phases/base.py
"""
Base Abstract Phase Handler Interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePhaseHandler(ABC):
    """Abstract interface for a music production phase handler."""

    @abstractmethod
    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        """Generates the interactive prompt and choices for this phase."""
        pass

    @abstractmethod
    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Processes the user's decision, applies DAW mutations, and transitions state."""
        pass

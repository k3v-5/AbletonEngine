# engine/core/protocols.py
"""
Core Typing Protocols (Interface Segregation Principle - ISP):
Defines lightweight, decoupled structural interfaces for remote DAW communication,
phase handlers, session state inspection, and audio analysis.
"""

from typing import Protocol, runtime_checkable, Dict, Any, Optional, List


@runtime_checkable
class CommandSenderProtocol(Protocol):
    """Protocol for components capable of dispatching remote commands to Ableton Live."""

    def send_command(
        self,
        command_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Dispatches an atomic command with parameters to the DAW Remote Script."""
        ...


@runtime_checkable
class AbletonConnectionProtocol(CommandSenderProtocol, Protocol):
    """Protocol representing a full connection to Ableton Live (Mock or Live Socket)."""

    def is_connected(self) -> bool:
        """Returns True if the connection to Ableton Live is healthy and active."""
        ...


@runtime_checkable
class PhaseHandlerProtocol(Protocol):
    """Protocol representing a structured conversational phase handler."""

    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        """Renders the conversational step and decision options for the user/AI."""
        ...

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Processes the decision, applies DAW actions, and updates phase state."""
        ...


@runtime_checkable
class SessionStateProtocol(Protocol):
    """Protocol for inspecting and persisting session state."""

    data: Dict[str, Any]

    def _save_state(self) -> None:
        """Persists the session data to disk."""
        ...


@runtime_checkable
class TrackResolverProtocol(Protocol):
    """Protocol for resolving physical DAW track indices from metadata entities."""

    @classmethod
    def resolve_track_index(cls, conn: Any, trk: Dict[str, Any]) -> int:
        """Resolves the physical DAW track index without index drift."""
        ...


@runtime_checkable
class InterceptHandlerProtocol(Protocol):
    """Protocol for global user-input intercept handlers (Chain of Responsibility & SRP/OCP)."""

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        """Determines if this handler can handle the given user input."""
        ...

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        """Handles user input if relevant; returns response dict or None."""
        ...

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        """Legacy compatibility adapter for direct intercept calls."""
        ...


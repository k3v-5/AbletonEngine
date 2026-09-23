# engine/production/copilot/phase_registry.py
"""
Phase Registry and Polymorphic Dispatcher (Open/Closed Principle - OCP & Dependency Inversion - DIP):
Central repository and resolver for music production phase handlers.
Allows new phases, alternative strategies, or test doubles to be registered
without modifying the core CopilotGuidedSession state machine.
"""

from typing import Dict, Any, Optional, Type
import logging
from engine.production.copilot.phases.base import BasePhaseHandler

logger = logging.getLogger("PhaseRegistry")


class PhaseRegistry:
    """
    Registry of phase handlers decoupling CopilotGuidedSession from concrete phase implementations.
    Supports lazy instantiation to prevent import cycles and overhead.
    """

    def __init__(self, register_defaults: bool = True):
        self._handlers: Dict[str, BasePhaseHandler] = {}
        self._factories: Dict[str, Any] = {}
        if register_defaults:
            self._register_default_phases()

    def register(self, phase_name: str, handler: BasePhaseHandler) -> None:
        """Registers an instantiated phase handler for a phase name."""
        self._handlers[phase_name] = handler
        self._factories.pop(phase_name, None)

    def register_lazy(self, phase_name: str, factory_callable: Any) -> None:
        """Registers a factory callable that creates the handler on demand."""
        self._factories[phase_name] = factory_callable
        self._handlers.pop(phase_name, None)

    def get(self, phase_name: str) -> Optional[BasePhaseHandler]:
        """Resolves the handler for a given phase name, instantiating lazily if needed."""
        if phase_name in self._handlers:
            return self._handlers[phase_name]

        if phase_name in self._factories:
            try:
                handler = self._factories[phase_name]()
                self._handlers[phase_name] = handler
                return handler
            except Exception as e:
                logger.error(f"Error instantiating phase handler for '{phase_name}': {e}")
                return None

        # Alias mappings for transitional phases
        if phase_name in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER"):
            return self.get("PHASE_9_MIX_MASTER_CANONICAL")
        if phase_name in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED"):
            return self.get("PHASE_10_COMPLETED_CANONICAL")

        return None

    def has_phase(self, phase_name: str) -> bool:
        """Checks if a handler exists for the given phase."""
        return (
            phase_name in self._handlers
            or phase_name in self._factories
            or phase_name in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER", "PHASE_9_COMPLETED", "PHASE_10_COMPLETED")
        )

    def dispatch_prompt(self, phase_name: str, session: Any, **kwargs) -> Dict[str, Any]:
        """Polymorphically dispatches prompt generation to the appropriate phase handler."""
        handler = self.get(phase_name)
        if handler is None:
            return {
                "status": "ERROR",
                "message": f"Fase desconocida o sin handler registrado: {phase_name}",
                "phase": phase_name
            }
        return handler.prompt(session, **kwargs)

    def dispatch_handle(self, phase_name: str, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Polymorphically dispatches user input handling to the appropriate phase handler."""
        handler = self.get(phase_name)
        if handler is None:
            return {
                "status": "ERROR",
                "message": f"Fase desconocida o sin handler registrado: {phase_name}",
                "phase": phase_name
            }
        return handler.handle(session, conn, user_input)

    def _register_default_phases(self) -> None:
        """Registers lazy factories for all 10 canonical production phases."""

        def _p1():
            from .phases.phase_1_tracks import Phase1TracksHandler
            return Phase1TracksHandler()

        def _p2():
            from .phases.phase_2_sections import Phase2SectionsHandler
            return Phase2SectionsHandler()

        def _p3():
            from .phases.phase_3_instruments import Phase3InstrumentsHandler
            return Phase3InstrumentsHandler()

        def _p4():
            from .phases.phase_4_param_sculpting import Phase4ParamSculptingHandler
            return Phase4ParamSculptingHandler()

        def _p5():
            from .phases.phase_5_insert_effects import Phase5InsertEffectsHandler
            return Phase5InsertEffectsHandler()

        def _p6():
            from .phases.phase_6.handler import Phase6CompositionHandler
            return Phase6CompositionHandler()

        def _p7():
            from .phases.phase_7_automation import Phase7AutomationHandler
            return Phase7AutomationHandler()

        def _p8():
            from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
            return Phase8VocalDuckingHandler()

        def _p9():
            from .phases.phase_9_export import Phase9ExportHandler
            return Phase9ExportHandler()

        def _p10():
            from .phases.phase_10.handler import Phase10ListenersHandler
            return Phase10ListenersHandler()

        self.register_lazy("PHASE_1_TRACKS", _p1)
        self.register_lazy("PHASE_2_SECTIONS", _p2)
        self.register_lazy("PHASE_3_INSTRUMENTS", _p3)
        self.register_lazy("PHASE_4_PARAM_SCULPTING", _p4)
        self.register_lazy("PHASE_5_INSERT_EFFECTS", _p5)
        self.register_lazy("PHASE_6_COMPOSITION", _p6)
        self.register_lazy("PHASE_7_AUTOMATION", _p7)
        self.register_lazy("PHASE_8_VOCAL_DUCKING", _p8)
        self.register_lazy("PHASE_9_MIX_MASTER_CANONICAL", _p9)
        self.register_lazy("PHASE_9_MIX_MASTER", _p9)
        self.register_lazy("PHASE_8_MIX_MASTER", _p9)
        self.register_lazy("PHASE_10_COMPLETED_CANONICAL", _p10)
        self.register_lazy("PHASE_10_COMPLETED", _p10)
        self.register_lazy("PHASE_9_COMPLETED", _p10)


# Default singleton instance for standard use
default_phase_registry = PhaseRegistry()

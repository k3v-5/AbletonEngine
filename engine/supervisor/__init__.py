# engine/supervisor/__init__.py
"""
Ableton Production Supervisor & Hard Quality Gates:
Inverts control so the engine is the authoritative quality gatekeeper,
monitoring physical liveness, verifying parameter exposure, and guiding mastering.
"""

from .failure_diagnostics import (
    FailureCategory,
    DiagnosticSeverity,
    DiagnosticFinding,
    FailureDiagnostics
)
from .acoustic_probe import (
    AcousticSilenceError,
    AcousticProbe
)
from .gatekeeper import (
    ProductionPhase,
    GateValidationError,
    GateResult,
    Gatekeeper
)

__all__ = [
    "FailureCategory",
    "DiagnosticSeverity",
    "DiagnosticFinding",
    "FailureDiagnostics",
    "AcousticSilenceError",
    "AcousticProbe",
    "ProductionPhase",
    "GateValidationError",
    "GateResult",
    "Gatekeeper"
]

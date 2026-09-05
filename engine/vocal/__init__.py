# engine/vocal/__init__.py
from .pipeline import (
    VocalStyle,
    VocalChainStage,
    VocalProductionProfile,
    VocalProductionEngine
)
from .chopper import (
    VocalChopStyle,
    VocalChopNote,
    VocalChopperEngine
)

__all__ = [
    "VocalStyle",
    "VocalChainStage",
    "VocalProductionProfile",
    "VocalProductionEngine",
    "VocalChopStyle",
    "VocalChopNote",
    "VocalChopperEngine"
]

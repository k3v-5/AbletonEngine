# engine/instruments/plugins/__init__.py
from .models import PluginSemanticRole, PluginProfile, ParameterSpec, NormalizedParameterResult
from .registry import PluginRegistry
from .normalizer import VSTParameterNormalizer

__all__ = [
    "PluginSemanticRole",
    "PluginProfile",
    "ParameterSpec",
    "NormalizedParameterResult",
    "PluginRegistry",
    "VSTParameterNormalizer"
]

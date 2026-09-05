# engine/sound/vital/__init__.py
"""
Vital Patch Synthesis Module for Ableton Production Intelligence Engine (PIE).
"""

from engine.sound.vital.models import (
    VitalPresetSpec,
    VitalPresetStyle,
    VitalOscillatorSpec,
    VitalFilterSpec,
    VitalEnvelopeSpec,
    VitalLfoSpec,
    VitalEffectsSpec,
    VitalModulationRouting
)
from engine.sound.vital.builder import VitalPatchBuilder
from engine.sound.vital.file_manager import VitalPresetManager

__all__ = [
    "VitalPresetSpec",
    "VitalPresetStyle",
    "VitalOscillatorSpec",
    "VitalFilterSpec",
    "VitalEnvelopeSpec",
    "VitalLfoSpec",
    "VitalEffectsSpec",
    "VitalModulationRouting",
    "VitalPatchBuilder",
    "VitalPresetManager"
]

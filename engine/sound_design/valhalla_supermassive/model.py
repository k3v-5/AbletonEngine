# engine/sound_design/valhalla_supermassive/model.py
"""
Valhalla Supermassive Data Model.

Represents the complete state of a Valhalla Supermassive instance
in pure Python, decoupled from XML formatting.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import copy

from .schema import ValhallaSupermassiveSchema


@dataclass
class SupermassiveModel:
    """Complete parameter state of Valhalla Supermassive."""

    preset_name: str = "Default"
    plugin_version: str = ValhallaSupermassiveSchema.DEFAULT_VERSION

    # Audio & Time Parameters (all normalized floats in [0.0, 1.0])
    mix: float = 1.0
    delay_sync: float = 0.25         # 0.0 = ms, 0.25 = straight note, 0.5 = dotted, 0.75 = triplet
    delay_note: float = 0.285714298  # 1/8 note
    delay_ms: float = 0.5
    delay_warp: float = 0.5
    clear: float = 0.0
    feedback: float = 0.5
    density: float = 0.5
    width: float = 1.0
    low_cut: float = 0.0
    high_cut: float = 1.0
    mod_rate: float = 0.5
    mod_depth: float = 0.5
    mode: float = 0.0                # Gemini (0 / 21)

    # Internal reserved registers
    reserved1: float = 0.0
    reserved2: float = 0.0
    reserved3: float = 0.0
    reserved4: float = 0.0

    @property
    def mode_name(self) -> str:
        """Return the current mode as human-readable string."""
        return ValhallaSupermassiveSchema.float_to_mode(self.mode)

    @property
    def mode_index(self) -> int:
        """Return current mode index [0, 21]."""
        return ValhallaSupermassiveSchema.float_to_mode_index(self.mode)

    def set_mode(self, mode: str) -> None:
        """Set mode by canonical mode name (e.g. 'Andromeda', 'Lyra', etc.)."""
        self.mode = ValhallaSupermassiveSchema.mode_to_float(mode)

    def set_sync(self, sync_type: str) -> None:
        """Set delay sync type ('ms', 'synced', 'dotted', 'triplet')."""
        normalized = sync_type.strip().lower()
        if normalized in ValhallaSupermassiveSchema.SYNC_MODES:
            self.delay_sync = ValhallaSupermassiveSchema.SYNC_MODES[normalized]
        else:
            raise ValueError(
                f"Unknown sync type '{sync_type}'. "
                f"Valid: {list(ValhallaSupermassiveSchema.SYNC_MODES.keys())}"
            )

    def set_delay_note(self, division: str) -> None:
        """Set delay note division (e.g. '1/8', '1/4', '1/16')."""
        if division in ValhallaSupermassiveSchema.NOTE_DIVISIONS:
            self.delay_note = ValhallaSupermassiveSchema.NOTE_DIVISIONS[division]
        else:
            raise ValueError(
                f"Unknown note division '{division}'. "
                f"Valid: {list(ValhallaSupermassiveSchema.NOTE_DIVISIONS.keys())}"
            )

    def to_xml_attribs(self) -> Dict[str, str]:
        """Generate attribute dictionary matching exact XML case."""
        return {
            "pluginVersion": self.plugin_version,
            "presetName": self.preset_name,
            "Mix": f"{self.mix:.9g}",
            "DelaySync": f"{self.delay_sync:.9g}",
            "DelayNote": f"{self.delay_note:.9g}",
            "Delay_Ms": f"{self.delay_ms:.9g}",
            "DelayWarp": f"{self.delay_warp:.9g}",
            "Clear": f"{self.clear:.9g}",
            "Feedback": f"{self.feedback:.9g}",
            "Density": f"{self.density:.9g}",
            "Width": f"{self.width:.9g}",
            "LowCut": f"{self.low_cut:.9g}",
            "HighCut": f"{self.high_cut:.9g}",
            "ModRate": f"{self.mod_rate:.9g}",
            "ModDepth": f"{self.mod_depth:.9g}",
            "Mode": f"{self.mode:.9g}",
            "Reserved1": f"{self.reserved1:.9g}",
            "Reserved2": f"{self.reserved2:.9g}",
            "Reserved3": f"{self.reserved3:.9g}",
            "Reserved4": f"{self.reserved4:.9g}",
        }

    def copy(self) -> "SupermassiveModel":
        """Return a deep copy of this model."""
        return copy.deepcopy(self)

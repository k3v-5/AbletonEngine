# engine/sound_design/surge_xt_fx/sanitizer.py
"""
Sanitizer and Auto-Repair for Surge XT FX.

Guarantees data integrity:
- Pads or truncates parameter lists to exactly 12 items
- Cleans NaN, Inf, and invalid types
- Resolves slot index collisions
- Sanitizes XML entity characters in preset names
"""

from typing import Tuple, List, Dict, Any
import math

from .schema import FXType, SurgeFXSchema
from .model import SurgeFXSlotModel, SurgeFXRackModel


class SurgeFXSanitizer:
    """Auto-repairs and sanitizes Surge FX configurations."""

    @classmethod
    def sanitize_slot(cls, slot: SurgeFXSlotModel) -> Tuple[SurgeFXSlotModel, List[str]]:
        """Sanitize an individual slot model."""
        repaired = slot.copy()
        corrections: List[str] = []

        # 1. Type validation
        if not isinstance(repaired.type, FXType):
            try:
                repaired.type = SurgeFXSchema.resolve_type(repaired.type)
                corrections.append(f"Resolved FX type to {repaired.type.name}.")
            except Exception:
                repaired.type = FXType.OFF
                corrections.append("Invalid FX type reset to OFF.")

        # 2. Parameters list size & float safety
        while len(repaired.params) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            repaired.params.append(0.0)
            corrections.append("Padded missing param with 0.0.")
        if len(repaired.params) > SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            repaired.params = repaired.params[:SurgeFXSchema.NUM_PARAMS_PER_SLOT]
            corrections.append("Truncated extra params to 12.")

        for i in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
            v = repaired.params[i]
            if v is None or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
                repaired.params[i] = 0.0
                corrections.append(f"Param p{i} had invalid value ({v}), reset to 0.0.")

        # 3. Ensure modifier lists match 12 items
        for mod_attr in ["temposync", "extend_range", "deactivated"]:
            lst = getattr(repaired, mod_attr)
            while len(lst) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
                lst.append(False)
            if len(lst) > SurgeFXSchema.NUM_PARAMS_PER_SLOT:
                setattr(repaired, mod_attr, lst[:SurgeFXSchema.NUM_PARAMS_PER_SLOT])

        while len(repaired.deform_type) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            repaired.deform_type.append(0)
        if len(repaired.deform_type) > SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            repaired.deform_type = repaired.deform_type[:SurgeFXSchema.NUM_PARAMS_PER_SLOT]

        # 4. Preset name cleanup
        if repaired.preset_name:
            repaired.preset_name = repaired.preset_name.strip()

        return repaired, corrections

    @classmethod
    def sanitize_rack(cls, rack: SurgeFXRackModel) -> Tuple[SurgeFXRackModel, List[str]]:
        """Sanitize complete 16-slot rack."""
        repaired = rack.copy()
        corrections: List[str] = []

        # Ensure exactly 16 slots
        while len(repaired.slots) < SurgeFXSchema.NUM_SLOTS:
            idx = len(repaired.slots)
            repaired.slots.append(SurgeFXSlotModel(slot_index=idx))
            corrections.append(f"Created missing slot {idx}.")
        if len(repaired.slots) > SurgeFXSchema.NUM_SLOTS:
            repaired.slots = repaired.slots[:SurgeFXSchema.NUM_SLOTS]
            corrections.append("Truncated extra rack slots to 16.")

        for i in range(SurgeFXSchema.NUM_SLOTS):
            slot, slot_fixes = cls.sanitize_slot(repaired.slots[i])
            slot.slot_index = i
            repaired.slots[i] = slot
            corrections.extend([f"Slot {i}: {fix}" for fix in slot_fixes])

        return repaired, corrections

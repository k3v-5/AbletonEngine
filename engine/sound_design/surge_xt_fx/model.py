# engine/sound_design/surge_xt_fx/model.py
"""
Surge XT FX Data Model.

Domain model representing:
- SurgeFXSlotModel: Individual effect processor (type, p0..p11, metadata)
- SurgeFXRackModel: 16-slot multi-FX rack grid spanning Scene A, B, Send, and Global
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple
import copy

from .schema import FXType, FXChain, FXBypass, SurgeFXSchema


@dataclass
class SurgeFXSlotModel:
    """Represents a single FX slot unit in Surge XT."""

    slot_index: int = 0
    type: FXType = FXType.OFF
    preset_name: str = ""
    params: List[float] = field(default_factory=lambda: [0.0] * SurgeFXSchema.NUM_PARAMS_PER_SLOT)
    temposync: List[bool] = field(default_factory=lambda: [False] * SurgeFXSchema.NUM_PARAMS_PER_SLOT)
    extend_range: List[bool] = field(default_factory=lambda: [False] * SurgeFXSchema.NUM_PARAMS_PER_SLOT)
    deactivated: List[bool] = field(default_factory=lambda: [False] * SurgeFXSchema.NUM_PARAMS_PER_SLOT)
    deform_type: List[int] = field(default_factory=lambda: [0] * SurgeFXSchema.NUM_PARAMS_PER_SLOT)
    filename: str = ""
    bypass: bool = False

    def __post_init__(self):
        # Ensure correct list lengths
        if len(self.params) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            self.params.extend([0.0] * (SurgeFXSchema.NUM_PARAMS_PER_SLOT - len(self.params)))
        if len(self.temposync) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            self.temposync.extend([False] * (SurgeFXSchema.NUM_PARAMS_PER_SLOT - len(self.temposync)))
        if len(self.extend_range) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            self.extend_range.extend([False] * (SurgeFXSchema.NUM_PARAMS_PER_SLOT - len(self.extend_range)))
        if len(self.deactivated) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            self.deactivated.extend([False] * (SurgeFXSchema.NUM_PARAMS_PER_SLOT - len(self.deactivated)))
        if len(self.deform_type) < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            self.deform_type.extend([0] * (SurgeFXSchema.NUM_PARAMS_PER_SLOT - len(self.deform_type)))

    @property
    def type_name(self) -> str:
        """Return readable effect name."""
        return SurgeFXSchema.FX_TYPE_SPECS.get(self.type, {}).get("name", "Unknown")

    @property
    def is_active(self) -> bool:
        """True if effect is assigned and not bypassed."""
        return self.type != FXType.OFF and not self.bypass

    def set_param(
        self,
        index: int,
        value: float,
        temposync: bool = False,
        extend: bool = False,
        deactivate: bool = False,
        deform: int = 0,
    ) -> None:
        """Set parameter value and optional modifiers."""
        if not 0 <= index < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            raise IndexError(f"Surge FX param index {index} out of range [0, 11].")
        self.params[index] = float(value)
        self.temposync[index] = bool(temposync)
        self.extend_range[index] = bool(extend)
        self.deactivated[index] = bool(deactivate)
        self.deform_type[index] = int(deform)

    def get_param(self, index: int) -> float:
        """Get parameter float value."""
        if not 0 <= index < SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            raise IndexError(f"Surge FX param index {index} out of range [0, 11].")
        return self.params[index]

    def copy(self) -> "SurgeFXSlotModel":
        """Return deep copy of slot model."""
        return copy.deepcopy(self)


@dataclass
class SurgeFXRackModel:
    """Represents the complete 16-slot multi-FX rack in Surge XT."""

    name: str = "Surge XT Rack"
    slots: List[SurgeFXSlotModel] = field(default_factory=list)
    bypass_mode: FXBypass = FXBypass.ALL_FX

    def __post_init__(self):
        if not self.slots:
            self.slots = [SurgeFXSlotModel(slot_index=i) for i in range(SurgeFXSchema.NUM_SLOTS)]
        elif len(self.slots) < SurgeFXSchema.NUM_SLOTS:
            start = len(self.slots)
            for i in range(start, SurgeFXSchema.NUM_SLOTS):
                self.slots.append(SurgeFXSlotModel(slot_index=i))

    def get_slot(self, slot_idx: int) -> SurgeFXSlotModel:
        """Retrieve slot by index [0, 15]."""
        if not 0 <= slot_idx < SurgeFXSchema.NUM_SLOTS:
            raise IndexError(f"Slot index {slot_idx} out of bounds [0, 15].")
        return self.slots[slot_idx]

    def set_slot(self, slot_idx: int, slot: SurgeFXSlotModel) -> None:
        """Set slot at index [0, 15]."""
        if not 0 <= slot_idx < SurgeFXSchema.NUM_SLOTS:
            raise IndexError(f"Slot index {slot_idx} out of bounds [0, 15].")
        slot.slot_index = slot_idx
        self.slots[slot_idx] = slot

    def get_chain_slots(self, chain: FXChain) -> List[SurgeFXSlotModel]:
        """Get the 4 slots belonging to a specific chain."""
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[chain]
        return [self.slots[i] for i in indices]

    def get_active_slots(self) -> List[SurgeFXSlotModel]:
        """Return all enabled, non-bypassed slots."""
        return [s for s in self.slots if s.is_active]

    def to_daw_param_map(self) -> Dict[str, float]:
        """
        Generate mapping of Ableton Live / DAW automation parameter names
        to float values for all 16 slots.
        Example keys: 'FX A1 Type', 'FX A1 Param 1', ...
        """
        params: Dict[str, float] = {}
        for s_idx, slot in enumerate(self.slots):
            slot_name = SurgeFXSchema.SLOT_NAMES[s_idx]
            # Type param
            params[f"{slot_name} Type"] = float(int(slot.type))
            # 12 slot params
            for p_idx in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
                params[f"{slot_name} Param {p_idx + 1}"] = slot.params[p_idx]
        return params

    def to_lom_command_list(self, only_active: bool = True) -> List[Tuple[str, float]]:
        """
        Generate list of (parameter_name, float_value) tuples for direct
        Live LOM injection via 'set_device_parameter'.
        Includes both canonical slot names (e.g. 'A Insert FX 1 Type') and short aliases
        (e.g. 'FX A1 Type') for active slots.
        """
        commands: List[Tuple[str, float]] = []
        for s_idx, slot in enumerate(self.slots):
            if only_active and not slot.is_active:
                continue
            slot_name = SurgeFXSchema.SLOT_NAMES[s_idx]

            # Short alias mapping e.g. "A Insert FX 1" -> "FX A1"
            short_prefix = None
            if "A Insert FX" in slot_name:
                num = slot_name.split()[-1]
                short_prefix = f"FX A{num}"
            elif "B Insert FX" in slot_name:
                num = slot_name.split()[-1]
                short_prefix = f"FX B{num}"

            # Type parameter
            type_val = float(int(slot.type))
            commands.append((f"{slot_name} Type", type_val))
            if short_prefix:
                commands.append((f"{short_prefix} Type", type_val))

            # 12 slot parameters
            for p_idx in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
                p_val = slot.params[p_idx]
                commands.append((f"{slot_name} Param {p_idx + 1}", p_val))
                if short_prefix:
                    commands.append((f"{short_prefix} Param {p_idx + 1}", p_val))

        return commands

    def copy(self) -> "SurgeFXRackModel":
        """Return deep copy of rack model."""
        return copy.deepcopy(self)

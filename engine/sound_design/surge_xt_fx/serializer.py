# engine/sound_design/surge_xt_fx/serializer.py
"""
Serializer and Parser for Surge XT Effects Presets (.srgfx, .srgfxchain).

Directly produces and ingests authentic Surge XT XML preset formats:
1. Single FX Preset (.srgfx): <single-fx streaming_version="30"> <snapshot ... /> </single-fx>
2. Chain FX Preset (.srgfxchain): <chain-fx streaming_version="30"> <snapshot ...> <fx ... /> </snapshot> </chain-fx>
"""

from typing import List, Tuple, Optional, Union
import xml.etree.ElementTree as ET
from pathlib import Path
import os

from .schema import FXType, FXChain, SurgeFXSchema
from .model import SurgeFXSlotModel, SurgeFXRackModel
from .sanitizer import SurgeFXSanitizer


class SurgeFXSerializer:
    """Handles serialization and deserialization of Surge XT FX formats."""

    @classmethod
    def get_user_fx_presets_dir(cls) -> Path:
        """Standard Surge XT user FX presets directory: ~/Documents/Surge XT/FX Presets/"""
        docs = Path(os.path.expanduser("~")) / "Documents"
        return docs / "Surge XT" / "FX Presets"

    @classmethod
    def get_user_chain_presets_dir(cls) -> Path:
        """Standard Surge XT user FX chain directory: ~/Documents/Surge XT/FX Chains/"""
        docs = Path(os.path.expanduser("~")) / "Documents"
        return docs / "Surge XT" / "FX Chains"

    @classmethod
    def to_single_fx_xml(cls, slot: SurgeFXSlotModel, sanitize: bool = True) -> str:
        """Serialize a SurgeFXSlotModel to .srgfx XML string."""
        target = slot
        if sanitize:
            target, _ = SurgeFXSanitizer.sanitize_slot(slot)

        name = target.preset_name or SurgeFXSchema.FX_TYPE_SPECS.get(target.type, {}).get("name", "Preset")
        type_id = int(target.type)

        lines = [
            f'<single-fx streaming_version="{SurgeFXSchema.STREAMING_VERSION}">',
            f'  <snapshot name="{name}"',
            f'     type="{type_id}"',
        ]

        for i in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
            lines.append(f'     p{i}="{target.params[i]:.9g}"')
            if target.temposync[i]:
                lines.append(f'     p{i}_temposync="1"')
            if target.extend_range[i]:
                lines.append(f'     p{i}_extend_range="1"')
            if target.deactivated[i]:
                lines.append(f'     p{i}_deactivated="1"')
            if target.deform_type[i] > 0:
                lines.append(f'     p{i}_deform_type="{target.deform_type[i]}"')

        if target.filename:
            lines.append(f'     filename="{target.filename}"')

        lines.append('  />')
        lines.append('</single-fx>\n')
        return "\n".join(lines)

    @classmethod
    def from_single_fx_xml(cls, xml_text: str) -> SurgeFXSlotModel:
        """Parse .srgfx XML string into SurgeFXSlotModel."""
        root = ET.fromstring(xml_text.strip())
        if root.tag != "single-fx":
            raise ValueError(f"Invalid root tag '{root.tag}'; expected '<single-fx>'.")

        snapshot = root.find("snapshot")
        if snapshot is None:
            raise ValueError("Missing '<snapshot>' element in single-fx XML.")

        slot = SurgeFXSlotModel()
        attrib = snapshot.attrib

        slot.preset_name = attrib.get("name", "")
        if "type" in attrib:
            slot.type = FXType(int(attrib["type"]))

        for i in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
            p_key = f"p{i}"
            if p_key in attrib:
                slot.params[i] = float(attrib[p_key])
            if f"{p_key}_temposync" in attrib:
                slot.temposync[i] = attrib[f"{p_key}_temposync"] == "1"
            if f"{p_key}_extend_range" in attrib:
                slot.extend_range[i] = attrib[f"{p_key}_extend_range"] == "1"
            if f"{p_key}_deactivated" in attrib:
                slot.deactivated[i] = attrib[f"{p_key}_deactivated"] == "1"
            if f"{p_key}_deform_type" in attrib:
                slot.deform_type[i] = int(attrib[f"{p_key}_deform_type"])

        if "filename" in attrib:
            slot.filename = attrib["filename"]

        return slot

    @classmethod
    def to_chain_fx_xml(
        cls, chain_name: str, slots: List[SurgeFXSlotModel], sanitize: bool = True
    ) -> str:
        """Serialize a 4-slot chain to .srgfxchain XML string."""
        chain_slots = slots[:SurgeFXSchema.SLOTS_PER_CHAIN]
        while len(chain_slots) < SurgeFXSchema.SLOTS_PER_CHAIN:
            chain_slots.append(SurgeFXSlotModel(slot_index=len(chain_slots)))

        lines = [
            f'<chain-fx streaming_version="{SurgeFXSchema.STREAMING_VERSION}">',
            f'  <snapshot name="{chain_name}">',
        ]

        for slot_idx, slot in enumerate(chain_slots):
            target = slot
            if sanitize:
                target, _ = SurgeFXSanitizer.sanitize_slot(slot)

            type_id = int(target.type)
            pn = target.preset_name

            lines.append(f'    <fx slot="{slot_idx}"')
            lines.append(f'       type="{type_id}"')
            lines.append(f'       preset_name="{pn}"')

            if target.type != FXType.OFF:
                for i in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
                    lines.append(f'       p{i}="{target.params[i]:.9g}"')
                    if target.temposync[i]:
                        lines.append(f'       p{i}_temposync="1"')
                    if target.extend_range[i]:
                        lines.append(f'       p{i}_extend_range="1"')
                    if target.deactivated[i]:
                        lines.append(f'       p{i}_deactivated="1"')
                    if target.deform_type[i] > 0:
                        lines.append(f'       p{i}_deform_type="{target.deform_type[i]}"')

                if target.filename:
                    lines.append(f'       filename="{target.filename}"')

            lines.append('    />')

        lines.append('  </snapshot>')
        lines.append('</chain-fx>\n')
        return "\n".join(lines)

    @classmethod
    def from_chain_fx_xml(cls, xml_text: str) -> Tuple[str, List[SurgeFXSlotModel]]:
        """Parse .srgfxchain XML string into (chain_name, list_of_4_slots)."""
        root = ET.fromstring(xml_text.strip())
        if root.tag != "chain-fx":
            raise ValueError(f"Invalid root tag '{root.tag}'; expected '<chain-fx>'.")

        snapshot = root.find("snapshot")
        if snapshot is None:
            raise ValueError("Missing '<snapshot>' element in chain-fx XML.")

        chain_name = snapshot.attrib.get("name", "Untitled Chain")
        slots = [SurgeFXSlotModel(slot_index=i) for i in range(SurgeFXSchema.SLOTS_PER_CHAIN)]

        for fx_elem in snapshot.findall("fx"):
            if "slot" not in fx_elem.attrib:
                continue
            slot_idx = int(fx_elem.attrib["slot"])
            if not 0 <= slot_idx < SurgeFXSchema.SLOTS_PER_CHAIN:
                continue

            slot = slots[slot_idx]
            attrib = fx_elem.attrib
            if "type" in attrib:
                slot.type = FXType(int(attrib["type"]))
            slot.preset_name = attrib.get("preset_name", "")

            for i in range(SurgeFXSchema.NUM_PARAMS_PER_SLOT):
                p_key = f"p{i}"
                if p_key in attrib:
                    slot.params[i] = float(attrib[p_key])
                if f"{p_key}_temposync" in attrib:
                    slot.temposync[i] = attrib[f"{p_key}_temposync"] == "1"
                if f"{p_key}_extend_range" in attrib:
                    slot.extend_range[i] = attrib[f"{p_key}_extend_range"] == "1"
                if f"{p_key}_deactivated" in attrib:
                    slot.deactivated[i] = attrib[f"{p_key}_deactivated"] == "1"
                if f"{p_key}_deform_type" in attrib:
                    slot.deform_type[i] = int(attrib[f"{p_key}_deform_type"])

            if "filename" in attrib:
                slot.filename = attrib["filename"]

        return chain_name, slots

    @classmethod
    def save_single_fx_file(
        cls, slot: SurgeFXSlotModel, destination_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Save a single FX preset to disk as .srgfx."""
        if destination_path is None:
            type_short = SurgeFXSchema.FX_TYPE_SPECS.get(slot.type, {}).get("short", "Other")
            name = slot.preset_name or "Preset"
            dest = cls.get_user_fx_presets_dir() / type_short / f"{name}.srgfx"
        else:
            dest = Path(destination_path)
            if dest.suffix != ".srgfx":
                dest = dest.with_suffix(".srgfx")

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cls.to_single_fx_xml(slot), encoding="utf-8")
        return dest

    @classmethod
    def save_chain_fx_file(
        cls, chain_name: str, slots: List[SurgeFXSlotModel], destination_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Save an FX chain preset to disk as .srgfxchain."""
        if destination_path is None:
            dest = cls.get_user_chain_presets_dir() / f"{chain_name}.srgfxchain"
        else:
            dest = Path(destination_path)
            if dest.suffix != ".srgfxchain":
                dest = dest.with_suffix(".srgfxchain")

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(cls.to_chain_fx_xml(chain_name, slots), encoding="utf-8")
        return dest

    @classmethod
    def save_chain_file(
        cls,
        rack_or_name: Union[SurgeFXRackModel, str],
        category: Optional[str] = None,
        slots: Optional[List[SurgeFXSlotModel]] = None,
        destination_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Ergonomic wrapper supporting SurgeFXRackModel or (chain_name, slots)."""
        if isinstance(rack_or_name, SurgeFXRackModel):
            chain_name = rack_or_name.name
            chain_slots = rack_or_name.get_chain_slots(FXChain.SCENE_A)
            if destination_path is None:
                base_dir = cls.get_user_chain_presets_dir()
                if category:
                    base_dir = base_dir / category
                destination_path = base_dir / f"{chain_name}.srgfxchain"
            return cls.save_chain_fx_file(chain_name, chain_slots, destination_path=destination_path)
        else:
            chain_name = str(rack_or_name)
            chain_slots = slots or []
            if destination_path is None:
                base_dir = cls.get_user_chain_presets_dir()
                if category:
                    base_dir = base_dir / category
                destination_path = base_dir / f"{chain_name}.srgfxchain"
            return cls.save_chain_fx_file(chain_name, chain_slots, destination_path=destination_path)

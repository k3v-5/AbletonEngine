# engine/sound_design/surge_xt_fx/validator.py
"""
Multi-Tier Validator for Surge XT Effects.

Evaluates single FX presets (.srgfx), chain presets (.srgfxchain),
or Python SurgeFXSlotModel / SurgeFXRackModel instances across three distinct tiers:
- Tier 1: XML Syntax & Surge XT Schema Specification (streaming_version, single-fx, chain-fx)
- Tier 2: DSP Range Bounds & Slot Topology (16 slots, 12 params per slot, type [0..31])
- Tier 3: Acoustic Policies & Gain-Staging (anti-clipping, anti-resonance)
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

from .schema import FXType, FXChain, FXBypass, SurgeFXSchema
from .model import SurgeFXSlotModel, SurgeFXRackModel
from .policies import SurgeFXSafetyPolicy


class SurgeFXValidationError(ValueError):
    """Raised when strict validation fails on a Surge XT FX preset or rack."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "Surge XT FX Validation Failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


@dataclass
class SurgeFXValidationReport:
    """Detailed multi-tier audit report for Surge XT FX."""
    is_valid: bool = True
    format_errors: List[str] = field(default_factory=list)        # Tier 1
    consistency_errors: List[str] = field(default_factory=list)   # Tier 2
    policy_warnings: List[str] = field(default_factory=list)      # Tier 3
    corrections: List[str] = field(default_factory=list)

    @property
    def all_errors(self) -> List[str]:
        return self.format_errors + self.consistency_errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.all_errors),
            "format_error_count": len(self.format_errors),
            "consistency_error_count": len(self.consistency_errors),
            "policy_warning_count": len(self.policy_warnings),
            "format_errors": self.format_errors,
            "consistency_errors": self.consistency_errors,
            "policy_warnings": self.policy_warnings,
            "corrections": self.corrections,
        }


class SurgeFXValidator:
    """Validator for Surge XT FX models and XML files."""

    @classmethod
    def validate_slot(cls, slot: SurgeFXSlotModel, strict: bool = False) -> SurgeFXValidationReport:
        """Validate an individual FX slot."""
        report = SurgeFXValidationReport()

        # Tier 1: Check type bounds
        if not isinstance(slot.type, (FXType, int)):
            report.format_errors.append(
                f"Tier 1: Invalid slot FX type '{slot.type}' (expected FXType or int)."
            )
        elif int(slot.type) < 0 or int(slot.type) >= len(SurgeFXSchema.FX_TYPE_SPECS):
            report.format_errors.append(
                f"Tier 1: FX type id {int(slot.type)} out of valid range [0, {len(SurgeFXSchema.FX_TYPE_SPECS) - 1}]."
            )

        # Tier 2: Check parameter count
        if len(slot.params) != SurgeFXSchema.NUM_PARAMS_PER_SLOT:
            report.consistency_errors.append(
                f"Tier 2: Slot has {len(slot.params)} parameters; expected exactly {SurgeFXSchema.NUM_PARAMS_PER_SLOT}."
            )

        # Check all params are numbers
        for idx, p in enumerate(slot.params):
            if not isinstance(p, (int, float)):
                report.consistency_errors.append(
                    f"Tier 2: Param p{idx} value '{p}' is not a valid number."
                )

        # Tier 3: Acoustic policy
        report.policy_warnings.extend(SurgeFXSafetyPolicy.audit_slot(slot))

        if report.all_errors:
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)

        return report

    @classmethod
    def validate_rack(cls, rack: SurgeFXRackModel, strict: bool = False) -> SurgeFXValidationReport:
        """Validate complete 16-slot rack."""
        report = SurgeFXValidationReport()

        if len(rack.slots) != SurgeFXSchema.NUM_SLOTS:
            report.consistency_errors.append(
                f"Tier 2: Rack has {len(rack.slots)} slots; expected exactly {SurgeFXSchema.NUM_SLOTS}."
            )

        for slot in rack.slots:
            sub_report = cls.validate_slot(slot, strict=False)
            report.format_errors.extend(sub_report.format_errors)
            report.consistency_errors.extend(sub_report.consistency_errors)

        # Rack-level policy warnings
        report.policy_warnings.extend(SurgeFXSafetyPolicy.audit_rack(rack))

        if report.all_errors:
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)

        return report

    @classmethod
    def validate_single_fx_xml(cls, xml_text: str, strict: bool = False) -> SurgeFXValidationReport:
        """Validate raw XML of a single-fx preset (.srgfx)."""
        report = SurgeFXValidationReport()

        cleaned = xml_text.strip()
        if not cleaned:
            report.format_errors.append("Tier 1: XML string is empty.")
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)
            return report

        try:
            root = ET.fromstring(cleaned)
        except ET.ParseError as e:
            report.format_errors.append(f"Tier 1: XML parse error: {e}")
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)
            return report

        # Tier 1: Check root
        if root.tag != "single-fx":
            report.format_errors.append(
                f"Tier 1: Invalid root element '<{root.tag}>'. Expected '<single-fx>'."
            )

        # Check snapshot element
        snapshot = root.find("snapshot")
        if snapshot is None:
            report.format_errors.append("Tier 1: Missing child element '<snapshot>' under '<single-fx>'.")
        else:
            if "type" not in snapshot.attrib:
                report.format_errors.append("Tier 1: Missing 'type' attribute on '<snapshot>'.")
            else:
                try:
                    t_val = int(snapshot.attrib["type"])
                    if not 0 <= t_val < len(SurgeFXSchema.FX_TYPE_SPECS):
                        report.consistency_errors.append(
                            f"Tier 2: Type {t_val} out of valid range [0, {len(SurgeFXSchema.FX_TYPE_SPECS) - 1}]."
                        )
                except ValueError:
                    report.format_errors.append(
                        f"Tier 1: 'type' attribute '{snapshot.attrib['type']}' is not an integer."
                    )

        if report.all_errors:
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)

        return report

    @classmethod
    def validate_chain_fx_xml(cls, xml_text: str, strict: bool = False) -> SurgeFXValidationReport:
        """Validate raw XML of an FX chain preset (.srgfxchain)."""
        report = SurgeFXValidationReport()

        cleaned = xml_text.strip()
        if not cleaned:
            report.format_errors.append("Tier 1: XML string is empty.")
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)
            return report

        try:
            root = ET.fromstring(cleaned)
        except ET.ParseError as e:
            report.format_errors.append(f"Tier 1: XML parse error: {e}")
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)
            return report

        if root.tag != "chain-fx":
            report.format_errors.append(
                f"Tier 1: Invalid root element '<{root.tag}>'. Expected '<chain-fx>'."
            )

        snapshot = root.find("snapshot")
        if snapshot is None:
            report.format_errors.append("Tier 1: Missing child element '<snapshot>' under '<chain-fx>'.")
        else:
            fx_elems = snapshot.findall("fx")
            for elem in fx_elems:
                if "slot" not in elem.attrib:
                    report.format_errors.append("Tier 1: '<fx>' element missing required 'slot' attribute.")
                else:
                    try:
                        s_idx = int(elem.attrib["slot"])
                        if not 0 <= s_idx < SurgeFXSchema.SLOTS_PER_CHAIN:
                            report.consistency_errors.append(
                                f"Tier 2: Chain slot {s_idx} out of range [0, {SurgeFXSchema.SLOTS_PER_CHAIN - 1}]."
                            )
                    except ValueError:
                        report.format_errors.append("Tier 1: 'slot' attribute is not an integer.")

        if report.all_errors:
            report.is_valid = False
            if strict:
                raise SurgeFXValidationError(report.all_errors)

        return report

# engine/sound_design/valhalla_supermassive/validator.py
"""
Multi-Tier Validator for Valhalla Supermassive.

Evaluates preset XML or SupermassiveModel across three distinct tiers:
- Tier 1: Format Specification (element tags, canonical case attributes, token types)
- Tier 2: Physical Parameter Bounds ([0.0, 1.0] range, discrete steps)
- Tier 3: Acoustic Safety Policies (runaway feedback, mud accumulation)
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

from .schema import ValhallaSupermassiveSchema
from .model import SupermassiveModel
from .policies import SupermassiveSafetyPolicy


class ValhallaValidationError(ValueError):
    """Raised when strict validation fails on a Valhalla Supermassive preset."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "Valhalla Supermassive Validation Failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


@dataclass
class ValhallaValidationReport:
    """Detailed multi-tier audit report for Valhalla Supermassive."""
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


class ValhallaSupermassiveValidator:
    """
    Validates SupermassiveModel instances or raw XML strings against the 3-tier rules.
    """

    @classmethod
    def validate(cls, target: Union[SupermassiveModel, str], strict: bool = False) -> ValhallaValidationReport:
        """Unified entry point validating either SupermassiveModel or XML string."""
        if isinstance(target, str):
            return cls.validate_xml(target, strict=strict)
        return cls.validate_model(target, strict=strict)

    @classmethod
    def validate_model(cls, model: SupermassiveModel, strict: bool = False) -> ValhallaValidationReport:
        """Audit a SupermassiveModel instance across all 3 tiers."""
        report = ValhallaValidationReport()

        # Tier 1: Check required metadata
        if not model.preset_name or not model.preset_name.strip():
            report.format_errors.append("Tier 1: presetName cannot be empty.")
        if not model.plugin_version or not model.plugin_version.strip():
            report.format_errors.append("Tier 1: pluginVersion cannot be empty.")

        # Tier 2: Check parameter bounds
        params_to_check = {
            "mix": model.mix,
            "delay_sync": model.delay_sync,
            "delay_note": model.delay_note,
            "delay_ms": model.delay_ms,
            "delay_warp": model.delay_warp,
            "clear": model.clear,
            "feedback": model.feedback,
            "density": model.density,
            "width": model.width,
            "low_cut": model.low_cut,
            "high_cut": model.high_cut,
            "mod_rate": model.mod_rate,
            "mod_depth": model.mod_depth,
            "mode": model.mode,
            "reserved1": model.reserved1,
            "reserved2": model.reserved2,
            "reserved3": model.reserved3,
            "reserved4": model.reserved4,
        }

        for param_name, val in params_to_check.items():
            if not isinstance(val, (int, float)):
                report.consistency_errors.append(
                    f"Tier 2: Parameter '{param_name}' must be a float, got {type(val).__name__} ({val})."
                )
            elif val < 0.0 or val > 1.0:
                report.consistency_errors.append(
                    f"Tier 2: Parameter '{param_name}' value {val} out of valid normalized range [0.0, 1.0]."
                )

        # Tier 3: Acoustic Policies
        policy_warnings = SupermassiveSafetyPolicy.audit_model(model)
        report.policy_warnings.extend(policy_warnings)

        if report.all_errors:
            report.is_valid = False
            if strict:
                raise ValhallaValidationError(report.all_errors)

        return report

    @classmethod
    def validate_xml_string(cls, xml_text: str, strict: bool = False) -> ValhallaValidationReport:
        """Audit raw XML string (as found in .vpreset or clipboard)."""
        report = ValhallaValidationReport()

        cleaned = xml_text.strip()
        if not cleaned:
            report.format_errors.append("Tier 1: XML string is empty.")
            report.is_valid = False
            if strict:
                raise ValhallaValidationError(report.all_errors)
            return report

        try:
            root = ET.fromstring(cleaned)
        except ET.ParseError as e:
            report.format_errors.append(f"Tier 1: Malformed XML syntax: {e}")
            report.is_valid = False
            if strict:
                raise ValhallaValidationError(report.all_errors)
            return report

        # Tier 1: Check root element tag
        if root.tag != ValhallaSupermassiveSchema.PLUGIN_NAME:
            report.format_errors.append(
                f"Tier 1: Invalid root element '<{root.tag}>'. Expected '<{ValhallaSupermassiveSchema.PLUGIN_NAME}>'."
            )

        # Tier 1: Check required attributes existence
        expected_attribs = set(ValhallaSupermassiveSchema.PARAMETER_SPECS.keys())
        expected_attribs.add("pluginVersion")
        expected_attribs.add("presetName")

        missing = expected_attribs - set(root.attrib.keys())
        if missing:
            report.format_errors.append(
                f"Tier 1: Missing expected XML attributes: {sorted(list(missing))}."
            )

        # Tier 2: Check float conversion and range for all parameters
        for attr, (min_v, max_v, _) in ValhallaSupermassiveSchema.PARAMETER_SPECS.items():
            if attr in root.attrib:
                val_str = root.attrib[attr]
                try:
                    f_val = float(val_str)
                    if f_val < min_v or f_val > max_v:
                        report.consistency_errors.append(
                            f"Tier 2: Attribute '{attr}' value {f_val} is outside [{min_v}, {max_v}]."
                        )
                except ValueError:
                    report.consistency_errors.append(
                        f"Tier 2: Attribute '{attr}' value '{val_str}' cannot be parsed as float."
                    )

        # Tier 3: Parse into model to check acoustic safety
        if not report.format_errors and not report.consistency_errors:
            try:
                from .serializer import ValhallaSupermassiveSerializer
                model = ValhallaSupermassiveSerializer.from_xml_element(root)
                report.policy_warnings.extend(SupermassiveSafetyPolicy.audit_model(model))
            except Exception as e:
                report.consistency_errors.append(f"Tier 2: Failed to build model from XML: {e}")

        if report.all_errors:
            report.is_valid = False
            if strict:
                raise ValhallaValidationError(report.all_errors)

        return report

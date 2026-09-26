# engine/sound_design/decent_sampler/validator.py
"""
3-Tier Validator for Decent Sampler Instruments.

Evaluates instruments across three distinct tiers:
- Tier 1: Decent Sampler Format Specification (XML tags, canonical tokens, types)
- Tier 2: Structural Consistency & Safety (loNote <= rootNote <= hiNote, loVel <= hiVel)
- Tier 3: Audio & Musical Policies (anti-click envelopes, CPU tail management)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
from pathlib import Path

from .schema import DecentSamplerSchema
from .model import InstrumentModel, GroupModel, SampleZoneModel, EffectModel, BindingModel
from .policies import AudioSafetyPolicy, ResourcePolicy


class ValidationError(ValueError):
    """Raised when strict validation fails on a Decent Sampler instrument."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "Decent Sampler Instrument Validation Failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


@dataclass
class ValidationReport:
    """Detailed multi-tier audit report."""
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


class DecentSamplerValidator:
    """
    Validates InstrumentModel instances or raw XML trees against the 3-tier hierarchy.
    """

    @classmethod
    def validate_model(cls, instrument: InstrumentModel, strict: bool = False) -> ValidationReport:
        """Audits an InstrumentModel across all three validation tiers."""
        report = ValidationReport()

        # ====================================================================
        # TIER 1: FORMAT SPECIFICATION (Tags, Types, Canonical Names)
        # ====================================================================
        if not instrument.groups:
            report.format_errors.append("Instrument must contain at least one <groups> element.")

        total_samples = instrument.total_samples()
        if total_samples == 0:
            report.format_errors.append("Instrument must contain at least one <sample> zone.")

        # Validate Effects
        for idx, effect in enumerate(instrument.effects):
            cls._audit_effect_format(effect, f"instrument.effects[{idx}]", report, level="instrument")

        for g_idx, group in enumerate(instrument.groups):
            for e_idx, effect in enumerate(group.effects):
                cls._audit_effect_format(effect, f"group[{g_idx}].effects[{e_idx}]", report, level="group")

        # Validate Controls & Bindings
        for c_idx, control in enumerate(instrument.ui.controls):
            for b_idx, binding in enumerate(control.bindings):
                cls._audit_binding_format(binding, f"control[{c_idx}].bindings[{b_idx}]", report)

        # ====================================================================
        # TIER 2: STRUCTURAL CONSISTENCY & SAFETY
        # ====================================================================
        for g_idx, group in enumerate(instrument.groups):
            for s_idx, sample in enumerate(group.samples):
                ctx = f"group[{g_idx}].sample[{s_idx}] ({sample.path})"

                # Path portability check
                if "\\" in sample.path:
                    report.consistency_errors.append(
                        f"{ctx}: Path contains Windows backslashes ('\\'). Must use standard forward slashes ('/')."
                    )
                if Path(sample.path).is_absolute() or (len(sample.path) > 1 and sample.path[1] == ":"):
                    report.consistency_errors.append(
                        f"{ctx}: Absolute path detected ('{sample.path}'). Paths must be relative for portability."
                    )

                # Note hierarchy check: 0 <= lo <= root <= hi <= 127
                if not (DecentSamplerSchema.NOTE_MIN <= sample.root_note <= DecentSamplerSchema.NOTE_MAX):
                    report.consistency_errors.append(
                        f"{ctx}: rootNote {sample.root_note} is out of MIDI bounds (0-127)."
                    )
                if sample.lo_note > sample.hi_note:
                    report.consistency_errors.append(
                        f"{ctx}: Inverted note bounds (loNote={sample.lo_note} > hiNote={sample.hi_note})."
                    )
                if not (sample.lo_note <= sample.root_note <= sample.hi_note):
                    report.consistency_errors.append(
                        f"{ctx}: rootNote {sample.root_note} must be between loNote {sample.lo_note} and hiNote {sample.hi_note}."
                    )

                # Velocity hierarchy check: 0 <= lo <= hi <= 127
                if sample.lo_vel > sample.hi_vel:
                    report.consistency_errors.append(
                        f"{ctx}: Inverted velocity bounds (loVel={sample.lo_vel} > hiVel={sample.hi_vel})."
                    )

                # Round-robin consistency
                if sample.seq_position > sample.seq_length:
                    report.consistency_errors.append(
                        f"{ctx}: seqPosition ({sample.seq_position}) exceeds seqLength ({sample.seq_length})."
                    )

        # ====================================================================
        # TIER 3: AUDIO & RESOURCE POLICIES (Heuristics & Best Practices)
        # ====================================================================
        for g_idx, group in enumerate(instrument.groups):
            # Envelope safety
            env_issues = AudioSafetyPolicy.audit_envelope(group.attack, group.release)
            for issue in env_issues:
                report.policy_warnings.append(f"group[{g_idx}]: {issue}")

            # Tail effect placement
            for effect in group.effects:
                eff_warnings = ResourcePolicy.audit_effect_placement(effect.type, "group")
                for w in eff_warnings:
                    report.policy_warnings.append(f"group[{g_idx}]: {w}")

        report.is_valid = len(report.all_errors) == 0

        if strict and not report.is_valid:
            raise ValidationError(report.all_errors)

        return report

    @classmethod
    def _audit_effect_format(cls, effect: EffectModel, context: str, report: ValidationReport, level: str) -> None:
        """Audits an effect against schema canonical rules."""
        if effect.type != effect.type.lower():
            report.format_errors.append(
                f"{context}: Effect type '{effect.type}' must be canonical lowercase (e.g. '{effect.type.lower()}')."
            )

        canonical = effect.type.lower()
        if canonical not in DecentSamplerSchema.CANONICAL_EFFECT_TYPES:
            report.format_errors.append(
                f"{context}: Unrecognized effect type '{effect.type}'. Must be one of {sorted(list(DecentSamplerSchema.CANONICAL_EFFECT_TYPES))}."
            )

        if level == "group" and canonical in DecentSamplerSchema.GLOBAL_ONLY_EFFECTS:
            report.consistency_errors.append(
                f"{context}: Effect '{canonical}' is unsupported at the group level by Decent Sampler."
            )

    @classmethod
    def _audit_binding_format(cls, binding: BindingModel, context: str, report: ValidationReport) -> None:
        """Audits a binding element against schema rules."""
        if binding.type not in DecentSamplerSchema.VALID_BINDING_TYPES:
            report.format_errors.append(
                f"{context}: Invalid binding type '{binding.type}'."
            )
        if binding.level not in DecentSamplerSchema.VALID_BINDING_LEVELS:
            report.format_errors.append(
                f"{context}: Invalid binding level '{binding.level}'."
            )
        if binding.parameter not in DecentSamplerSchema.VALID_BINDING_PARAMETERS:
            report.format_errors.append(
                f"{context}: Unrecognized parameter token '{binding.parameter}'."
            )
        if binding.translation not in DecentSamplerSchema.VALID_TRANSLATION_MODES:
            report.format_errors.append(
                f"{context}: Invalid translation mode '{binding.translation}'."
            )

    @classmethod
    def validate_xml(cls, xml_content: str, strict: bool = False, lenient: bool = True) -> ValidationReport:
        """Parses and validates a raw XML string representation."""
        report = ValidationReport()
        if lenient:
            from .serializer import DSPresetSerializer
            xml_content, corrections = DSPresetSerializer.clean_xml_content(xml_content)
            for c in corrections:
                report.corrections.append(c)
                report.policy_warnings.append(f"JUCE-Tolerant Sanitization: {c}")

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            report.format_errors.append(f"XML Parse Failure: {str(e)}")
            report.is_valid = False
            if strict:
                raise ValidationError(report.all_errors)
            return report

        if root.tag != DecentSamplerSchema.ROOT_TAG:
            report.format_errors.append(
                f"Root XML tag must be <{DecentSamplerSchema.ROOT_TAG}>, found <{root.tag}>."
            )

        # Ensure <groups> exists
        groups_elem = root.find("groups")
        if groups_elem is None:
            report.format_errors.append("Root element missing required <groups> container.")
        else:
            sample_count = len(groups_elem.findall(".//sample"))
            if sample_count == 0:
                report.format_errors.append("No <sample> elements found under <groups>.")

        # Check effects lowercase invariant in XML
        for eff in root.findall(".//effect"):
            eff_type = eff.get("type", "")
            if eff_type != eff_type.lower():
                report.format_errors.append(
                    f"Effect element has non-lowercase type='{eff_type}'. Must be '{eff_type.lower()}'."
                )

        # Check sample paths in XML
        for s in root.findall(".//sample"):
            path_val = s.get("path", "")
            if "\\" in path_val:
                report.consistency_errors.append(
                    f"Sample path '{path_val}' contains Windows backslashes. Must use forward slashes."
                )

        report.is_valid = len(report.all_errors) == 0
        if strict and not report.is_valid:
            raise ValidationError(report.all_errors)

        return report

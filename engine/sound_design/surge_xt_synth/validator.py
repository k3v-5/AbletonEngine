# engine/sound_design/surge_xt_synth/validator.py
"""
Surge XT Synthesizer 3-Tier Validator.

Tier 1: Range & Type Bounds (All normalized floats in [0.0, 1.0], pitch limits, unison [1..16]).
Tier 2: Physical & Signal Flow Integrity (Active oscillator count, anti-click release floor).
Tier 3: Acoustic Policy (Resonance runaway protection, gain-staging headroom, sub-bass phase clarity).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .model import SurgeSynthPatchModel
from .schema import SurgeXTSynthSchema


class SurgeSynthValidationError(Exception):
    """Raised when Surge XT Synthesizer patch validation fails in strict mode."""
    pass


@dataclass
class SurgeSynthValidationReport:
    """Detailed diagnostic report of 3-tier validation for Surge XT Synthesizer."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tier1_passed: bool = True
    tier2_passed: bool = True
    tier3_passed: bool = True

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            msg = "Surge XT Synth Validation Failed:\n" + "\n".join(f" - [ERROR] {e}" for e in self.errors)
            raise SurgeSynthValidationError(msg)


class SurgeSynthValidator:
    """Performs rigorous 3-tier validation for Surge XT Synthesizer patches."""

    @classmethod
    def validate_patch(
        cls,
        patch: SurgeSynthPatchModel,
        role: Optional[str] = None,
        strict: bool = False
    ) -> SurgeSynthValidationReport:
        report = SurgeSynthValidationReport(is_valid=True)

        # -------------------------------------------------------------
        # TIER 1: Range & Type Bounds
        # -------------------------------------------------------------
        # Master & Unison
        if not (0.0 <= patch.volume <= 1.0):
            report.errors.append(f"Tier 1: Master volume={patch.volume} must be in [0.0, 1.0].")
            report.tier1_passed = False

        if not isinstance(patch.unison_count, int) or not (SurgeXTSynthSchema.UNISON_MIN_VOICES <= patch.unison_count <= SurgeXTSynthSchema.UNISON_MAX_VOICES):
            report.errors.append(f"Tier 1: unison_count={patch.unison_count} must be an integer in [{SurgeXTSynthSchema.UNISON_MIN_VOICES}, {SurgeXTSynthSchema.UNISON_MAX_VOICES}].")
            report.tier1_passed = False

        if not (0.0 <= patch.unison_detune <= 1.0):
            report.errors.append(f"Tier 1: unison_detune={patch.unison_detune} must be in [0.0, 1.0].")
            report.tier1_passed = False

        # Oscillators bounds
        for osc in patch.oscillators:
            if osc.osc_type not in SurgeXTSynthSchema.OSCILLATOR_TYPES:
                report.errors.append(f"Tier 1: Osc {osc.slot} has invalid type '{osc.osc_type}'. Must be one of {SurgeXTSynthSchema.OSCILLATOR_TYPES}.")
                report.tier1_passed = False

            if not (SurgeXTSynthSchema.OCTAVE_MIN <= osc.octave <= SurgeXTSynthSchema.OCTAVE_MAX):
                report.errors.append(f"Tier 1: Osc {osc.slot} octave={osc.octave} outside [{SurgeXTSynthSchema.OCTAVE_MIN}, {SurgeXTSynthSchema.OCTAVE_MAX}].")
                report.tier1_passed = False

            if not (SurgeXTSynthSchema.SEMITONE_MIN <= osc.semitone <= SurgeXTSynthSchema.SEMITONE_MAX):
                report.errors.append(f"Tier 1: Osc {osc.slot} semitone={osc.semitone} outside [{SurgeXTSynthSchema.SEMITONE_MIN}, {SurgeXTSynthSchema.SEMITONE_MAX}].")
                report.tier1_passed = False

            if not (-100.0 <= osc.cent <= 100.0):
                report.errors.append(f"Tier 1: Osc {osc.slot} cent={osc.cent} outside [-100.0, 100.0].")
                report.tier1_passed = False

            if not (0.0 <= osc.level <= 1.0):
                report.errors.append(f"Tier 1: Osc {osc.slot} level={osc.level} must be in [0.0, 1.0].")
                report.tier1_passed = False

        # Filters bounds
        for f in [patch.filter1, patch.filter2]:
            if f.filter_type not in SurgeXTSynthSchema.FILTER_TYPES:
                report.errors.append(f"Tier 1: Filter {f.unit} has invalid type '{f.filter_type}'.")
                report.tier1_passed = False

            for p_name, p_val in [("cutoff", f.cutoff), ("resonance", f.resonance), ("drive", f.drive)]:
                if not (0.0 <= p_val <= 1.0):
                    report.errors.append(f"Tier 1: Filter {f.unit} {p_name}={p_val} must be in [0.0, 1.0].")
                    report.tier1_passed = False

        # Envelopes bounds
        for env in [patch.amp_envelope, patch.filter_envelope]:
            for p_name, p_val in [("attack", env.attack), ("decay", env.decay), ("sustain", env.sustain), ("release", env.release)]:
                if not (0.0 <= p_val <= 1.0):
                    report.errors.append(f"Tier 1: {env.name} Envelope {p_name}={p_val} must be in [0.0, 1.0].")
                    report.tier1_passed = False

        # -------------------------------------------------------------
        # TIER 2: Physical & Signal Flow Integrity
        # -------------------------------------------------------------
        # Ensure at least one active, unmuted oscillator with level > 0
        active_oscs = [osc for osc in patch.oscillators if not osc.mute and osc.level > 0.0]
        if not active_oscs:
            report.errors.append("Tier 2: Dead patch detected. All oscillators are muted or have zero level. Synthesizer would be completely silent.")
            report.tier2_passed = False

        # Anti-click envelope release floor
        if patch.amp_envelope.release < SurgeXTSynthSchema.MIN_RELEASE_SEC:
            report.errors.append(
                f"Tier 2: Amp envelope release ({patch.amp_envelope.release}s) is below safety floor ({SurgeXTSynthSchema.MIN_RELEASE_SEC}s). "
                "Causes harsh digital zero-crossing clicks on note-off."
            )
            report.tier2_passed = False

        if not patch.patch_name or not str(patch.patch_name).strip():
            report.errors.append("Tier 2: patch_name cannot be empty.")
            report.tier2_passed = False

        # -------------------------------------------------------------
        # TIER 3: Acoustic Policy & Studio Guardrails
        # -------------------------------------------------------------
        norm_role = str(role).strip().upper() if role else None

        # Filter runaway self-oscillation protection
        for f in [patch.filter1, patch.filter2]:
            if f.resonance > 0.95:
                report.warnings.append(
                    f"Tier 3 Policy: Filter {f.unit} resonance ({f.resonance}) > 0.95. "
                    "Extreme self-oscillation risk: could produce painful digital sine piercing."
                )

        # Gain staging headroom check
        high_level_oscs = [osc for osc in active_oscs if osc.level > 0.70]
        if len(high_level_oscs) >= 2 and patch.unison_count >= 4 and patch.volume > 0.85:
            report.warnings.append(
                f"Tier 3 Policy: {len(high_level_oscs)} loud oscillators with {patch.unison_count} unison voices at volume={patch.volume}. "
                "Risk of internal DSP saturation clipping before the track fader."
            )

        # Sub-bass mono integrity
        if norm_role == "BASS" and patch.unison_count > 4 and patch.unison_detune > 0.40:
            report.warnings.append(
                f"Tier 3 Policy: Bass patch has {patch.unison_count} unison voices with high detune ({patch.unison_detune}). "
                "Risk of phase cancellation in sub frequencies below 100 Hz."
            )

        report.is_valid = len(report.errors) == 0
        if strict:
            report.raise_if_invalid()

        return report

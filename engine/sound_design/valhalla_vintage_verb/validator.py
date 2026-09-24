# engine/sound_design/valhalla_vintage_verb/validator.py
"""
Valhalla VintageVerb 3-Tier Validator.

Tier 1: Range & Schema Bounds (All parameters normalized strictly in [0.0, 1.0]).
Tier 2: Physical & Spectral Consistency (LowCut < HighCut, valid algorithms and eras).
Tier 3: Acoustic Policy (Mud prevention, runaway feedback and metallic ring protection).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .model import VintageVerbModel
from .schema import ValhallaVintageVerbSchema, VintageVerbColor


class VintageVerbValidationError(Exception):
    """Raised when Valhalla VintageVerb validation fails in strict mode."""
    pass


@dataclass
class VintageVerbValidationReport:
    """Detailed diagnostic report of 3-tier validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tier1_passed: bool = True
    tier2_passed: bool = True
    tier3_passed: bool = True

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            msg = "Valhalla VintageVerb Validation Failed:\n" + "\n".join(f" - [ERROR] {e}" for e in self.errors)
            raise VintageVerbValidationError(msg)


class ValhallaVintageVerbValidator:
    """Performs rigorous 3-tier validation for Valhalla VintageVerb configurations."""

    @classmethod
    def validate(
        cls,
        model: VintageVerbModel,
        role: Optional[str] = None,
        strict: bool = False
    ) -> VintageVerbValidationReport:
        report = VintageVerbValidationReport(is_valid=True)

        # -------------------------------------------------------------
        # TIER 1: Range & Schema Bounds [0.0, 1.0]
        # -------------------------------------------------------------
        continuous_params = [
            ("Mix", model.mix),
            ("PreDelay", model.predelay),
            ("Decay", model.decay),
            ("Size", model.size),
            ("Attack", model.attack),
            ("BassMult", model.bass_mult),
            ("BassXover", model.bass_xover),
            ("HighShelf", model.high_shelf),
            ("HighCut", model.high_cut),
            ("LowCut", model.low_cut),
            ("EarlyDiffusion", model.early_diffusion),
            ("LateDiffusion", model.late_diffusion),
            ("ModRate", model.mod_rate),
            ("ModDepth", model.mod_depth),
            ("Mode", model.mode),
            ("ColorMode", model.color_mode),
        ]

        for p_name, p_val in continuous_params:
            if not isinstance(p_val, (int, float)):
                report.errors.append(f"Tier 1: Parameter '{p_name}' must be a float, got {type(p_val).__name__} ({p_val}).")
                report.tier1_passed = False
            elif p_val < 0.0 or p_val > 1.0:
                report.errors.append(f"Tier 1: Parameter '{p_name}'={p_val} is out of normalized bounds [0.0, 1.0].")
                report.tier1_passed = False

        if model.mode_name not in ValhallaVintageVerbSchema.MODES:
            report.errors.append(f"Tier 1: Unknown algorithmic mode '{model.mode_name}'. Must be one of {ValhallaVintageVerbSchema.NUM_MODES} valid modes.")
            report.tier1_passed = False

        # -------------------------------------------------------------
        # TIER 2: Physical & Spectral Consistency
        # -------------------------------------------------------------
        # LowCut vs HighCut spectral inversion check
        if model.low_cut >= model.high_cut:
            report.errors.append(
                f"Tier 2: Spectral inversion detected: LowCut ({model.low_cut}) >= HighCut ({model.high_cut}). "
                "This completely silences or destroys the reverb frequency spectrum."
            )
            report.tier2_passed = False

        if not model.preset_name or not str(model.preset_name).strip():
            report.errors.append("Tier 2: preset_name cannot be empty.")
            report.tier2_passed = False

        # -------------------------------------------------------------
        # TIER 3: Acoustic Policy & Studio Guardrails
        # -------------------------------------------------------------
        norm_role = str(role).strip().upper() if role else None

        # Anti-mud rule: Drums, Percussion and Bass must have adequate LowCut
        if norm_role in ("DRUMS", "PERCUSSION", "BASS"):
            if model.low_cut < 0.05:
                report.warnings.append(
                    f"Tier 3 Policy: LowCut={model.low_cut} on role '{norm_role}' is below 0.05. "
                    "Risk of low-frequency mud and muddying the kick/bass relationship."
                )

        # Nonlin mode recommendations
        if model.mode_name == "Nonlin":
            if model.decay > 0.60:
                report.warnings.append(
                    "Tier 3 Policy: 'Nonlin' mode with Decay > 0.60 may sound unnaturally gated or stretched."
                )
        else:
            # Extreme size vs decay sanity
            if model.decay > 0.85 and model.size < 0.15:
                report.warnings.append(
                    f"Tier 3 Policy: Massive decay ({model.decay_seconds}s) inside tiny room size ({model.size}) "
                    "creates unnatural metallic flutter and resonant build-up."
                )

        # Wrap up validation status
        report.is_valid = len(report.errors) == 0
        if strict:
            report.raise_if_invalid()

        return report

# engine/sound_design/vital_design_validator.py
"""
Vital Design Validator & Diagnostic Reporter.

Audits granular sound design specifications submitted by AI or user scripts.
Provides clear, actionable diagnostic feedback on invalid parameters, suggests
corrections, and offers both strict and resilient auto-correcting modes.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import difflib
import logging

logger = logging.getLogger("VitalDesignValidator")


class VitalValidationError(ValueError):
    """Raised when strict validation fails on a Vital sound design specification."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "Vital Sound Design Specification Failed Validation:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


@dataclass
class ValidationReport:
    """Detailed audit report containing diagnostics, warnings, corrections, and sanitized spec."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    sanitized_spec: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "correction_count": len(self.corrections),
            "errors": self.errors,
            "warnings": self.warnings,
            "corrections": self.corrections
        }


class VitalDesignValidator:
    """
    Validates granular specifications for Vital Synth sound generation.
    Checks oscillators, filters, modulations, LFOs, and effects against physical and DSP constraints.
    """

    VALID_WAVEFORMS: Set[str] = {
        "SINE", "SAW", "TRIANGLE", "PULSE", "SQUARE", "FM",
        "VOCAL_FORMANT_A", "VOCAL_FORMANT_E", "VOCAL_FORMANT_I",
        "VOCAL_FORMANT_O", "VOCAL_FORMANT_U",
        "ANALOG_WARM", "CHEBYSHEV", "HARMONIC_SERIES", "WHITE_NOISE",
        "METALLIC", "BELL", "NOISE", "DIRTY_SAW", "SUPERSAW", "SUB_SINE"
    }

    VALID_FILTER_MODELS: Set[str] = {
        "ANALOG_12", "ANALOG_24", "DIRTY", "LADDER", "DIODE_303", "COMB", "FORMANT", "DIGITAL"
    }

    VALID_FILTER_MODES: Set[str] = {
        "LOW_PASS", "BAND_PASS", "HIGH_PASS", "NOTCH"
    }

    VALID_SAMPLER_TYPES: Set[str] = {
        "WHITE_NOISE", "PINK", "VINYL", "CLICK", "TRANSIENT"
    }

    VALID_MOD_SOURCES: Set[str] = {
        "LFO_1", "LFO_2", "LFO_3", "LFO_4",
        "ENV_1", "ENV_2", "ENV_3",
        "RANDOM_S_H", "RANDOM_PERLIN",
        "MACRO_1", "MACRO_2", "MACRO_3", "MACRO_4"
    }

    VALID_MOD_DESTINATIONS: Set[str] = {
        "FILTER_CUTOFF", "FILTER_RESONANCE", "FILTER_DRIVE",
        "WAVETABLE_FRAME", "OSC_1_FRAME", "OSC_2_FRAME", "OSC_3_FRAME",
        "OSC_1_PITCH", "OSC_2_PITCH", "OSC_3_PITCH", "OSC_PITCH",
        "OSC_1_LEVEL", "OSC_2_LEVEL", "OSC_3_LEVEL",
        "OSC_1_DETUNE", "OSC_2_DETUNE", "OSC_3_DETUNE",
        "DISTORTION_DRIVE", "REVERB_MIX", "DELAY_MIX", "DELAY_FEEDBACK", "CHORUS_MIX", "PAN", "VOLUME"
    }

    VALID_LFO_SHAPES: Set[str] = {
        "SINE", "TRIANGLE", "SAW_DOWN", "SAW_UP", "SQUARE",
        "STEPPED_RANDOM", "WOBBLE_GROWL", "RAMP_UP", "RAMP_DOWN"
    }

    VALID_LFO_RATES: Set[str] = {
        "1/64", "1/32", "1/16", "1/8", "1/4", "1/2",
        "1_BAR", "2_BARS", "4_BARS", "8_BARS",
        "TRIPLET_1/16", "TRIPLET_1/8", "TRIPLET_1/4",
        "DOTTED_1/16", "DOTTED_1/8", "DOTTED_1/4"
    }

    CUTOFF_DESCRIPTORS: Dict[str, float] = {
        "DEEP_SUB": 40.0,
        "SUB_BASS": 55.0,
        "SUB": 90.0,
        "LOW_MID": 350.0,
        "MID": 1000.0,
        "HIGH_MID": 3200.0,
        "BRIGHT": 7500.0,
        "AIR": 14000.0,
        "OPEN": 19000.0
    }

    @classmethod
    def validate_specification(
        cls,
        spec: Dict[str, Any],
        strict: bool = False
    ) -> ValidationReport:
        """
        Validates the entire sound design specification.

        Args:
            spec: The dictionary submitted by the AI or user.
            strict: If True, raises VitalValidationError on any error.
                    If False, applies safe auto-corrections and reports them.

        Returns:
            ValidationReport with diagnostics and sanitized spec.
        """
        report = ValidationReport()
        sanitized: Dict[str, Any] = {}

        if not isinstance(spec, dict):
            report.is_valid = False
            report.errors.append(f"Specification must be a dictionary, got {type(spec).__name__}.")
            if strict:
                raise VitalValidationError(report.errors)
            return report

        # 1. Validate Oscillators
        sanitized["oscillators"] = cls._validate_oscillators(spec.get("oscillators", {}), report)

        # 2. Validate Filter
        sanitized["filter"] = cls._validate_filter(spec.get("filter", {}), report)

        # 3. Validate Modulations
        sanitized["modulations"] = cls._validate_modulations(spec.get("modulations", []), report)

        # 4. Validate Envelopes
        sanitized["envelopes"] = cls._validate_envelopes(spec.get("envelopes", {}), report)

        # 5. Validate Effects
        sanitized["effects"] = cls._validate_effects(spec.get("effects", {}), report)

        # 6. Validate Sampler / Noise Layer
        if "sampler" in spec:
            sanitized["sampler"] = cls._validate_sampler(spec.get("sampler", {}), report)

        # 7. Validate Variation and Seed
        sanitized["variation"] = cls._validate_variation(spec.get("variation", 0.0), report)
        sanitized["seed"] = spec.get("seed", None)

        # Determine overall validity
        if report.errors:
            report.is_valid = False
            if strict:
                raise VitalValidationError(report.errors)

        report.sanitized_spec = sanitized
        return report

    @classmethod
    def _validate_oscillators(cls, osc_dict: Any, report: ValidationReport) -> Dict[str, Any]:
        """Validates oscillator specifications for osc_1, osc_2, osc_3."""
        sanitized_oscs: Dict[str, Any] = {}

        if not isinstance(osc_dict, dict):
            report.warnings.append(f"'oscillators' should be a dict, got {type(osc_dict).__name__}. Using default setup.")
            osc_dict = {"osc_1": {"waveform": "SAW"}}

        if not osc_dict:
            # Default fallback
            osc_dict = {"osc_1": {"waveform": "SAW"}}

        for osc_name in ("osc_1", "osc_2", "osc_3"):
            if osc_name not in osc_dict:
                continue

            cfg = osc_dict[osc_name]
            if not isinstance(cfg, dict):
                report.errors.append(f"'{osc_name}' must be a dict with oscillator properties.")
                continue

            clean_cfg: Dict[str, Any] = {}

            # Waveform
            raw_wave = str(cfg.get("waveform", "SAW")).upper().strip()
            if raw_wave not in cls.VALID_WAVEFORMS:
                close = difflib.get_close_matches(raw_wave, list(cls.VALID_WAVEFORMS), n=1)
                suggestion = close[0] if close else "SAW"
                report.warnings.append(
                    f"'{osc_name}.waveform' '{raw_wave}' is unrecognized. "
                    f"Auto-corrected to '{suggestion}'."
                )
                report.corrections.append(f"Replaced invalid waveform '{raw_wave}' with '{suggestion}' in {osc_name}.")
                clean_cfg["waveform"] = suggestion
            else:
                clean_cfg["waveform"] = raw_wave

            # Octave & Semitones
            octave = cfg.get("octave", 0)
            if not isinstance(octave, (int, float)) or not (-4 <= octave <= 4):
                clamped_oct = max(-4, min(4, int(octave) if isinstance(octave, (int, float)) else 0))
                report.warnings.append(f"'{osc_name}.octave' {octave} outside [-4..4]. Clamped to {clamped_oct}.")
                clean_cfg["octave"] = clamped_oct
            else:
                clean_cfg["octave"] = int(octave)

            semitones = cfg.get("semitones", 0)
            if isinstance(semitones, (int, float)):
                clean_cfg["semitones"] = max(-48, min(48, int(semitones)))

            # Detune Cents
            cents = cfg.get("detune_cents", 0.0)
            if isinstance(cents, (int, float)):
                clean_cfg["detune_cents"] = max(-100.0, min(100.0, float(cents)))

            # Unison Voices
            unison = cfg.get("unison", cfg.get("unison_voices", 1))
            if not isinstance(unison, (int, float)) or not (1 <= unison <= 16):
                clamped_uni = max(1, min(16, int(unison) if isinstance(unison, (int, float)) else 1))
                report.warnings.append(f"'{osc_name}.unison' {unison} outside [1..16]. Clamped to {clamped_uni}.")
                clean_cfg["unison"] = clamped_uni
            else:
                clean_cfg["unison"] = int(unison)

            # Level & Pan
            lvl = cfg.get("level", 0.707)
            clean_cfg["level"] = max(0.0, min(1.0, float(lvl) if isinstance(lvl, (int, float)) else 0.707))

            pan = cfg.get("pan", 0.0)
            clean_cfg["pan"] = max(-1.0, min(1.0, float(pan) if isinstance(pan, (int, float)) else 0.0))

            # FM specific parameters
            if "FM" in clean_cfg["waveform"]:
                clean_cfg["fm_carrier"] = max(0.25, min(16.0, float(cfg.get("fm_carrier", 1.0))))
                clean_cfg["fm_mod"] = max(0.25, min(16.0, float(cfg.get("fm_mod", 2.0))))
                clean_cfg["fm_index"] = max(0.0, min(10.0, float(cfg.get("fm_index", 1.5))))

            sanitized_oscs[osc_name] = clean_cfg

        # Ensure at least one oscillator is configured
        if not sanitized_oscs:
            sanitized_oscs["osc_1"] = {"waveform": "SAW", "octave": 0, "unison": 1, "level": 0.707}
            report.warnings.append("No valid oscillators were configured. Defaulted to single SAW on osc_1.")

        return sanitized_oscs

    @classmethod
    def _validate_filter(cls, flt_dict: Any, report: ValidationReport) -> Dict[str, Any]:
        """Validates filter model, mode, cutoff frequency, and resonance."""
        clean_flt: Dict[str, Any] = {}

        if not isinstance(flt_dict, dict):
            flt_dict = {}

        # Model
        raw_model = str(flt_dict.get("model", "ANALOG_12")).upper().strip()
        if raw_model not in cls.VALID_FILTER_MODELS:
            close = difflib.get_close_matches(raw_model, list(cls.VALID_FILTER_MODELS), n=1)
            suggestion = close[0] if close else "ANALOG_12"
            report.warnings.append(
                f"Filter model '{raw_model}' is unrecognized. "
                f"Valid models: {sorted(list(cls.VALID_FILTER_MODELS))}. Auto-corrected to '{suggestion}'."
            )
            report.corrections.append(f"Corrected filter model to '{suggestion}'.")
            clean_flt["model"] = suggestion
        else:
            clean_flt["model"] = raw_model

        # Mode
        raw_mode = str(flt_dict.get("mode", "LOW_PASS")).upper().strip()
        if raw_mode not in cls.VALID_FILTER_MODES:
            clean_flt["mode"] = "LOW_PASS"
            report.warnings.append(f"Filter mode '{raw_mode}' unknown. Defaulted to 'LOW_PASS'.")
        else:
            clean_flt["mode"] = raw_mode

        # Cutoff Frequency (Hz or descriptor)
        raw_cutoff = flt_dict.get("cutoff_hz", flt_dict.get("cutoff", 2500.0))
        if isinstance(raw_cutoff, str):
            desc_upper = raw_cutoff.upper().strip()
            if desc_upper in cls.CUTOFF_DESCRIPTORS:
                clean_flt["cutoff_hz"] = cls.CUTOFF_DESCRIPTORS[desc_upper]
            else:
                report.warnings.append(f"Cutoff descriptor '{raw_cutoff}' unknown. Defaulted to 2500 Hz.")
                clean_flt["cutoff_hz"] = 2500.0
        elif isinstance(raw_cutoff, (int, float)):
            val = float(raw_cutoff)
            if val < 20.0:
                report.warnings.append(f"Cutoff frequency {val} Hz is subsonic (<20 Hz). Clamped to 45.0 Hz to prevent silence.")
                report.corrections.append("Clamped subsonic cutoff to 45.0 Hz.")
                clean_flt["cutoff_hz"] = 45.0
            elif val > 20000.0:
                clean_flt["cutoff_hz"] = 20000.0
            else:
                clean_flt["cutoff_hz"] = val
        else:
            clean_flt["cutoff_hz"] = 2500.0

        # Resonance
        res = flt_dict.get("resonance", 0.25)
        if isinstance(res, (int, float)):
            f_res = float(res)
            if f_res > 0.75:
                report.warnings.append(
                    f"Resonance {f_res:.2f} is dangerously high (>0.75, acoustic howl risk). "
                    "Clamped to safe maximum 0.65."
                )
                report.corrections.append("Clamped high resonance to 0.65.")
                clean_flt["resonance"] = 0.65
            else:
                clean_flt["resonance"] = max(0.0, f_res)
        else:
            clean_flt["resonance"] = 0.25

        # Drive
        drive = flt_dict.get("drive", 0.0)
        clean_flt["drive"] = max(0.0, min(1.0, float(drive) if isinstance(drive, (int, float)) else 0.0))

        return clean_flt

    @classmethod
    def _validate_modulations(cls, mod_list: Any, report: ValidationReport) -> List[Dict[str, Any]]:
        """Validates routing matrix connections, rates, and amounts."""
        clean_mods: List[Dict[str, Any]] = []

        if not isinstance(mod_list, list):
            return clean_mods

        for i, mod in enumerate(mod_list):
            if not isinstance(mod, dict):
                report.warnings.append(f"Modulation entry #{i} must be a dict.")
                continue

            src = str(mod.get("source", "")).upper().strip()
            dest = str(mod.get("destination", "")).upper().strip()

            if src not in cls.VALID_MOD_SOURCES:
                close = difflib.get_close_matches(src, list(cls.VALID_MOD_SOURCES), n=1)
                suggestion = close[0] if close else "LFO_1"
                report.warnings.append(f"Modulation source '{src}' in entry #{i} is invalid. Corrected to '{suggestion}'.")
                src = suggestion

            if dest not in cls.VALID_MOD_DESTINATIONS:
                close = difflib.get_close_matches(dest, list(cls.VALID_MOD_DESTINATIONS), n=1)
                suggestion = close[0] if close else "FILTER_CUTOFF"
                report.warnings.append(f"Modulation destination '{dest}' in entry #{i} is invalid. Corrected to '{suggestion}'.")
                dest = suggestion

            amt = mod.get("amount", 0.5)
            amt_val = max(-1.0, min(1.0, float(amt) if isinstance(amt, (int, float)) else 0.5))

            # Shape and Rate for LFO sources
            shape = str(mod.get("shape", "TRIANGLE")).upper().strip()
            if shape not in cls.VALID_LFO_SHAPES:
                shape = "TRIANGLE"

            rate = str(mod.get("rate", "1/8")).upper().strip()
            if rate not in cls.VALID_LFO_RATES:
                rate = "1/8"

            clean_mods.append({
                "source": src,
                "destination": dest,
                "amount": amt_val,
                "shape": shape,
                "rate": rate
            })

        return clean_mods

    @classmethod
    def _validate_envelopes(cls, env_dict: Any, report: ValidationReport) -> Dict[str, Any]:
        """Validates ADSR envelope parameters."""
        clean_env: Dict[str, Any] = {}
        if not isinstance(env_dict, dict):
            return clean_env

        for k in ("attack", "decay", "sustain", "release"):
            if k in env_dict:
                v = env_dict[k]
                if isinstance(v, (int, float)):
                    clean_env[k] = max(0.0, float(v))

        return clean_env

    @classmethod
    def _validate_effects(cls, fx_dict: Any, report: ValidationReport) -> Dict[str, Any]:
        """Validates effect parameters."""
        if not isinstance(fx_dict, dict):
            return {}
        return fx_dict

    @classmethod
    def _validate_variation(cls, var_val: Any, report: ValidationReport) -> float:
        """Validates stochastic variation factor."""
        if not isinstance(var_val, (int, float)):
            return 0.0
        return max(0.0, min(1.0, float(var_val)))

    @classmethod
    def _validate_sampler(cls, samp_dict: Any, report: ValidationReport) -> Dict[str, Any]:
        """Validates internal sampler/noise layer configuration."""
        if not isinstance(samp_dict, dict):
            return {}

        clean_samp: Dict[str, Any] = {}
        clean_samp["on"] = bool(samp_dict.get("on", True))

        raw_type = str(samp_dict.get("sample_type", "WHITE_NOISE")).upper().strip()
        if raw_type not in cls.VALID_SAMPLER_TYPES:
            close = difflib.get_close_matches(raw_type, list(cls.VALID_SAMPLER_TYPES), n=1)
            suggestion = close[0] if close else "WHITE_NOISE"
            report.warnings.append(
                f"Sampler type '{raw_type}' unrecognized. Auto-corrected to '{suggestion}'."
            )
            clean_samp["sample_type"] = suggestion
        else:
            clean_samp["sample_type"] = raw_type

        lvl = samp_dict.get("level", 0.3)
        clean_samp["level"] = max(0.0, min(1.0, float(lvl) if isinstance(lvl, (int, float)) else 0.3))
        clean_samp["loop"] = bool(samp_dict.get("loop", True))

        return clean_samp

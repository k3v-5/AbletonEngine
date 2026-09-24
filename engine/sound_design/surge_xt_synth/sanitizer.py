# engine/sound_design/surge_xt_synth/sanitizer.py
"""
Surge XT Synthesizer Sanitizer.

Auto-corrects out-of-bound parameters, resolves fuzzy oscillator and filter aliases,
enforces anti-click envelope floors, and ensures zero dead-patch scenarios.
"""

from typing import Dict, Any, Optional

from .model import SurgeSynthPatchModel, SurgeSynthOscillatorModel
from .schema import (
    SurgeXTSynthSchema,
    SurgeOscillatorType,
    SurgeFilterType,
    SurgeFilterSubtype,
    SurgeFilterConfig
)


class SurgeSynthSanitizer:
    """Sanitizes Surge XT Synthesizer patches to guarantee acoustic integrity and schema validity."""

    OSC_ALIASES: Dict[str, str] = {
        "classic": SurgeOscillatorType.CLASSIC.value,
        "analog": SurgeOscillatorType.CLASSIC.value,
        "saw": SurgeOscillatorType.CLASSIC.value,
        "square": SurgeOscillatorType.CLASSIC.value,
        "sub": SurgeOscillatorType.CLASSIC.value,
        "modern": SurgeOscillatorType.MODERN.value,
        "dpw": SurgeOscillatorType.MODERN.value,
        "wavetable": SurgeOscillatorType.WAVETABLE.value,
        "wt": SurgeOscillatorType.WAVETABLE.value,
        "sine": SurgeOscillatorType.SINE.value,
        "fm": SurgeOscillatorType.FM2.value,
        "fm2": SurgeOscillatorType.FM2.value,
        "fm3": SurgeOscillatorType.FM3.value,
        "string": SurgeOscillatorType.STRING.value,
        "pluck": SurgeOscillatorType.STRING.value,
        "physical": SurgeOscillatorType.STRING.value,
        "twist": SurgeOscillatorType.TWIST.value,
        "plaits": SurgeOscillatorType.TWIST.value,
        "mutable": SurgeOscillatorType.TWIST.value,
        "alias": SurgeOscillatorType.ALIAS.value,
        "chiptune": SurgeOscillatorType.ALIAS.value,
        "8bit": SurgeOscillatorType.ALIAS.value,
        "audioin": SurgeOscillatorType.AUDIO_IN.value,
        "input": SurgeOscillatorType.AUDIO_IN.value,
    }

    FILTER_ALIASES: Dict[str, str] = {
        "ladder": SurgeFilterType.LADDER_LP.value,
        "moog": SurgeFilterType.LADDER_LP.value,
        "k35": SurgeFilterType.K35_LP.value,
        "ms20": SurgeFilterType.K35_LP.value,
        "diode": SurgeFilterType.DIODE_LP.value,
        "303": SurgeFilterType.DIODE_LP.value,
        "obxd": SurgeFilterType.OBXD_LP.value,
        "oberheim": SurgeFilterType.OBXD_LP.value,
        "tripole": SurgeFilterType.TRIPOLE.value,
        "chow": SurgeFilterType.TRIPOLE.value,
        "comb": SurgeFilterType.COMB_POS.value,
        "comb+": SurgeFilterType.COMB_POS.value,
        "comb-": SurgeFilterType.COMB_NEG.value,
        "lp12": SurgeFilterType.LOWPASS_12.value,
        "lp24": SurgeFilterType.LOWPASS_24.value,
        "hp12": SurgeFilterType.HIGHPASS_12.value,
        "hp24": SurgeFilterType.HIGHPASS_24.value,
        "bp12": SurgeFilterType.BANDPASS_12.value,
        "bp24": SurgeFilterType.BANDPASS_24.value,
        "notch": SurgeFilterType.NOTCH.value,
    }

    @classmethod
    def resolve_oscillator_type(cls, name: str) -> str:
        """Resolves fuzzy oscillator name to canonical type."""
        clean = name.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        if clean in cls.OSC_ALIASES:
            return cls.OSC_ALIASES[clean]
        for canonical in SurgeXTSynthSchema.OSCILLATOR_TYPES:
            if canonical.lower() == clean:
                return canonical
        return SurgeOscillatorType.CLASSIC.value

    @classmethod
    def resolve_filter_type(cls, name: str) -> str:
        """Resolves fuzzy filter name to canonical type."""
        clean = name.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        if clean in cls.FILTER_ALIASES:
            return cls.FILTER_ALIASES[clean]
        for canonical in SurgeXTSynthSchema.FILTER_TYPES:
            if canonical.lower().replace(" ", "") == clean:
                return canonical
        return SurgeFilterType.LADDER_LP.value

    @classmethod
    def sanitize_patch(cls, patch: SurgeSynthPatchModel, role: Optional[str] = None) -> SurgeSynthPatchModel:
        """Sanitizes patch in place to guarantee validity."""
        # 1. Master controls
        patch.volume = max(0.0, min(1.0, float(patch.volume)))
        patch.unison_count = max(SurgeXTSynthSchema.UNISON_MIN_VOICES, min(SurgeXTSynthSchema.UNISON_MAX_VOICES, int(patch.unison_count)))
        patch.unison_detune = max(0.0, min(1.0, float(patch.unison_detune)))

        # 2. Oscillators
        active_oscs = []
        for osc in patch.oscillators:
            osc.osc_type = cls.resolve_oscillator_type(osc.osc_type)
            osc.octave = max(SurgeXTSynthSchema.OCTAVE_MIN, min(SurgeXTSynthSchema.OCTAVE_MAX, int(osc.octave)))
            osc.semitone = max(SurgeXTSynthSchema.SEMITONE_MIN, min(SurgeXTSynthSchema.SEMITONE_MAX, int(osc.semitone)))
            osc.cent = max(-100.0, min(100.0, float(osc.cent)))
            osc.level = max(0.0, min(1.0, float(osc.level)))
            osc.pan = max(-1.0, min(1.0, float(osc.pan)))
            if not osc.mute and osc.level > 0.0:
                active_oscs.append(osc)

        # Resurrect dead patch if all oscillators are silent
        if not active_oscs and patch.oscillators:
            patch.oscillators[0].mute = False
            patch.oscillators[0].level = 0.85

        # 3. Filters
        for f in [patch.filter1, patch.filter2]:
            f.filter_type = cls.resolve_filter_type(f.filter_type)
            f.cutoff = max(0.0, min(1.0, float(f.cutoff)))
            f.resonance = max(0.0, min(0.95, float(f.resonance)))  # Safety limit 0.95
            f.drive = max(0.0, min(1.0, float(f.drive)))

        # 4. Envelopes
        for env in [patch.amp_envelope, patch.filter_envelope]:
            env.attack = max(0.0, min(1.0, float(env.attack)))
            env.decay = max(0.0, min(1.0, float(env.decay)))
            env.sustain = max(0.0, min(1.0, float(env.sustain)))
            env.release = max(SurgeXTSynthSchema.MIN_RELEASE_SEC, min(1.0, float(env.release)))

        # Role-based policy adjustments
        norm_role = str(role).strip().upper() if role else None
        if norm_role == "BASS":
            # For bass, constrain extreme unison detune to protect sub-bass mono power
            patch.unison_count = min(4, patch.unison_count)
            patch.unison_detune = min(0.35, patch.unison_detune)

        if not patch.patch_name or not str(patch.patch_name).strip():
            patch.patch_name = "SurgeXT_Patch"

        return patch

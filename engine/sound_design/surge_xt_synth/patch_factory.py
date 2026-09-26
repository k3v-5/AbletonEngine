# engine/sound_design/surge_xt_synth/patch_factory.py
"""
Surge XT Synthesizer Patch Factory.

Constructs acoustically calibrated, studio-grade synthesizer patches
tailored for specific musical roles (BASS, LEAD, KEYS, PAD, PLUCK, 808, FX)
with zero manual guesswork and full parameter validation.
"""

from typing import Dict, Any, Optional

from .model import (
    SurgeSynthPatchModel,
    SurgeSynthOscillatorModel,
    SurgeSynthFilterModel,
    SurgeSynthEnvelopeModel
)
from .schema import (
    SurgeXTSynthSchema,
    SurgeOscillatorType,
    SurgeFilterType,
    SurgeFilterSubtype,
    SurgeFilterConfig
)
from .sanitizer import SurgeSynthSanitizer
from .validator import SurgeSynthValidator


class SurgeSynthPatchFactory:
    """Factory creating role-specific synthesized patches for Surge XT."""

    @classmethod
    def build_bass_reese_patch(
        cls,
        patch_name: str = "Bass_Reese",
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> SurgeSynthPatchModel:
        """Constructs a thick, analog-modeled Reese bass with sub-oscillator and Moog ladder filtering."""
        applied = applied_params or {}

        patch = SurgeSynthPatchModel(
            patch_name=patch_name,
            category="Bass",
            volume=0.82,
            unison_count=2,
            unison_detune=0.18,
            oscillators=[
                SurgeSynthOscillatorModel(slot=1, osc_type=SurgeOscillatorType.CLASSIC.value, octave=-1, level=0.85, param1=0.0), # Saw
                SurgeSynthOscillatorModel(slot=2, osc_type=SurgeOscillatorType.CLASSIC.value, octave=-1, cent=7.5, level=0.85, param1=0.0), # Detuned Saw
                SurgeSynthOscillatorModel(slot=3, osc_type=SurgeOscillatorType.SINE.value, octave=-2, level=0.75, route="Direct Out"), # Sub-bass bypasses filter
            ],
            filter1=SurgeSynthFilterModel(unit=1, filter_type=SurgeFilterType.LADDER_LP.value, cutoff=0.45, resonance=0.22, drive=0.15),
            amp_envelope=SurgeSynthEnvelopeModel(name="Amp", attack=0.005, decay=0.45, sustain=0.85, release=0.20),
            filter_envelope=SurgeSynthEnvelopeModel(name="Filter", attack=0.01, decay=0.30, sustain=0.40, release=0.15),
        )

        cls._apply_overrides(patch, applied)
        return SurgeSynthSanitizer.sanitize_patch(patch, role="BASS")

    @classmethod
    def build_pluck_fm_patch(
        cls,
        patch_name: str = "Keys_FM_Pluck",
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> SurgeSynthPatchModel:
        """Constructs a crystal-clear FM pluck with fast decay and snappy K35 filter."""
        applied = applied_params or {}

        patch = SurgeSynthPatchModel(
            patch_name=patch_name,
            category="Keys",
            volume=0.85,
            unison_count=1,
            oscillators=[
                SurgeSynthOscillatorModel(slot=1, osc_type=SurgeOscillatorType.FM2.value, octave=0, level=0.90, param1=0.60, param2=0.40),
                SurgeSynthOscillatorModel(slot=2, osc_type=SurgeOscillatorType.CLASSIC.value, octave=0, cent=4.0, level=0.45, param2=0.50), # Square bite
                SurgeSynthOscillatorModel(slot=3, osc_type=SurgeOscillatorType.CLASSIC.value, mute=True, level=0.0),
            ],
            filter1=SurgeSynthFilterModel(unit=1, filter_type=SurgeFilterType.K35_LP.value, cutoff=0.62, resonance=0.38, drive=0.05),
            amp_envelope=SurgeSynthEnvelopeModel(name="Amp", attack=0.002, decay=0.32, sustain=0.00, release=0.18),
            filter_envelope=SurgeSynthEnvelopeModel(name="Filter", attack=0.002, decay=0.22, sustain=0.15, release=0.15),
        )

        cls._apply_overrides(patch, applied)
        return SurgeSynthSanitizer.sanitize_patch(patch, role="KEYS")

    @classmethod
    def build_lead_supersaw_patch(
        cls,
        patch_name: str = "Lead_Supersaw",
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> SurgeSynthPatchModel:
        """Constructs a cutting 7-voice stereo supersaw lead with Diode saturation."""
        applied = applied_params or {}

        patch = SurgeSynthPatchModel(
            patch_name=patch_name,
            category="Lead",
            volume=0.80,
            unison_count=7,
            unison_detune=0.42,
            oscillators=[
                SurgeSynthOscillatorModel(slot=1, osc_type=SurgeOscillatorType.MODERN.value, octave=0, level=0.88),
                SurgeSynthOscillatorModel(slot=2, osc_type=SurgeOscillatorType.MODERN.value, octave=0, cent=5.0, level=0.88),
                SurgeSynthOscillatorModel(slot=3, osc_type=SurgeOscillatorType.CLASSIC.value, octave=-1, level=0.50), # Center body
            ],
            filter1=SurgeSynthFilterModel(unit=1, filter_type=SurgeFilterType.DIODE_LP.value, cutoff=0.82, resonance=0.25, drive=0.12),
            amp_envelope=SurgeSynthEnvelopeModel(name="Amp", attack=0.01, decay=0.40, sustain=0.75, release=0.28),
            filter_envelope=SurgeSynthEnvelopeModel(name="Filter", attack=0.015, decay=0.35, sustain=0.50, release=0.20),
        )

        cls._apply_overrides(patch, applied)
        return SurgeSynthSanitizer.sanitize_patch(patch, role="LEAD")

    @classmethod
    def build_pad_lush_patch(
        cls,
        patch_name: str = "Pad_Lush_String",
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> SurgeSynthPatchModel:
        """Constructs an evolving physical-modeled string pad with warm Oberheim filter and slow attack."""
        applied = applied_params or {}

        patch = SurgeSynthPatchModel(
            patch_name=patch_name,
            category="Pad",
            volume=0.78,
            unison_count=4,
            unison_detune=0.32,
            oscillators=[
                SurgeSynthOscillatorModel(slot=1, osc_type=SurgeOscillatorType.STRING.value, octave=0, level=0.82, param1=0.65), # Physical pluck/string
                SurgeSynthOscillatorModel(slot=2, osc_type=SurgeOscillatorType.WAVETABLE.value, octave=0, cent=-4.0, level=0.78, param1=0.45),
                SurgeSynthOscillatorModel(slot=3, osc_type=SurgeOscillatorType.SINE.value, octave=-1, level=0.40),
            ],
            filter1=SurgeSynthFilterModel(unit=1, filter_type=SurgeFilterType.OBXD_LP.value, cutoff=0.56, resonance=0.15, drive=0.00),
            amp_envelope=SurgeSynthEnvelopeModel(name="Amp", attack=0.42, decay=0.85, sustain=0.82, release=0.65),
            filter_envelope=SurgeSynthEnvelopeModel(name="Filter", attack=0.55, decay=0.90, sustain=0.65, release=0.50),
        )

        cls._apply_overrides(patch, applied)
        return SurgeSynthSanitizer.sanitize_patch(patch, role="PAD")

    @classmethod
    def build_808_sub_patch(
        cls,
        patch_name: str = "Bass_808_Sub",
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> SurgeSynthPatchModel:
        """Constructs a hard-hitting 808 sub bass with pitch drop transient and drive."""
        applied = applied_params or {}

        patch = SurgeSynthPatchModel(
            patch_name=patch_name,
            category="Bass",
            volume=0.88,
            unison_count=1,
            oscillators=[
                SurgeSynthOscillatorModel(slot=1, osc_type=SurgeOscillatorType.SINE.value, octave=-2, level=0.95),
                SurgeSynthOscillatorModel(slot=2, osc_type=SurgeOscillatorType.CLASSIC.value, octave=-1, level=0.35, param1=0.25), # Subtle harmonic bite
                SurgeSynthOscillatorModel(slot=3, osc_type=SurgeOscillatorType.CLASSIC.value, mute=True, level=0.0),
            ],
            filter1=SurgeSynthFilterModel(unit=1, filter_type=SurgeFilterType.LADDER_LP.value, cutoff=0.38, resonance=0.10, drive=0.28),
            amp_envelope=SurgeSynthEnvelopeModel(name="Amp", attack=0.002, decay=0.85, sustain=0.25, release=0.35),
            filter_envelope=SurgeSynthEnvelopeModel(name="Filter", attack=0.001, decay=0.08, sustain=0.00, release=0.10), # Fast pitch drop
        )

        cls._apply_overrides(patch, applied)
        return SurgeSynthSanitizer.sanitize_patch(patch, role="BASS")

    @classmethod
    def create_role_patch(
        cls,
        role: str,
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None,
        track_name: Optional[str] = None
    ) -> SurgeSynthPatchModel:
        """
        Dynamically selects and molds the optimal synthesizer patch for the role.
        """
        norm_role = str(role).strip().upper()
        p_name = track_name or f"Surge_{norm_role}"

        if norm_role in ("BASS", "SUB_BASS"):
            # Check if 808 style requested
            applied = applied_params or {}
            style_str = str(applied.get("style", "")).lower()
            if "808" in style_str or "trap" in style_str:
                return cls.build_808_sub_patch(p_name, bpm, applied)
            return cls.build_bass_reese_patch(p_name, bpm, applied)

        elif norm_role in ("KEYS", "PIANO", "PLUCK"):
            return cls.build_pluck_fm_patch(p_name, bpm, applied_params)

        elif norm_role in ("LEAD", "SYNTH", "SOLO"):
            return cls.build_lead_supersaw_patch(p_name, bpm, applied_params)

        elif norm_role in ("PAD", "STRINGS", "AMBIENT"):
            return cls.build_pad_lush_patch(p_name, bpm, applied_params)

        else:
            # Versatile hybrid default
            return cls.build_pluck_fm_patch(p_name, bpm, applied_params)

    @classmethod
    def _apply_overrides(cls, patch: SurgeSynthPatchModel, applied: Dict[str, Any]) -> None:
        """Applies generic parameter overrides from user or copilot session."""
        if "Cutoff" in applied or "cutoff" in applied:
            patch.filter1.cutoff = float(applied.get("Cutoff", applied.get("cutoff", patch.filter1.cutoff)))
        if "Resonance" in applied or "resonance" in applied:
            patch.filter1.resonance = float(applied.get("Resonance", applied.get("resonance", patch.filter1.resonance)))
        if "Volume" in applied or "volume" in applied:
            patch.volume = float(applied.get("Volume", applied.get("volume", patch.volume)))
        if "UnisonCount" in applied or "unison_count" in applied:
            patch.unison_count = int(applied.get("UnisonCount", applied.get("unison_count", patch.unison_count)))
        if "Attack" in applied or "attack" in applied:
            patch.amp_envelope.attack = float(applied.get("Attack", applied.get("attack", patch.amp_envelope.attack)))
        if "Release" in applied or "release" in applied:
            patch.amp_envelope.release = float(applied.get("Release", applied.get("release", patch.amp_envelope.release)))

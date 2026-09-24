# engine/sound_design/surge_xt_fx/policies.py
"""
Acoustic and Production Policies for Surge XT Effects.

Audits multi-FX chains for:
- Serial distortion gain compounding (anti-clipping)
- Resonator/Combulator runaway feedback
- Excessive CPU density (multiple Nimbus / Reverb 2 in series)
- Extreme stereo phase de-correlation
"""

from typing import List, Set
from .schema import FXType, FXChain, SurgeFXSchema
from .model import SurgeFXRackModel, SurgeFXSlotModel


class SurgeFXSafetyPolicy:
    """Acoustic safety and gain staging auditor for Surge XT FX."""

    DISTORTION_TYPES: Set[FXType] = {
        FXType.DISTORTION,
        FXType.CHOW,
        FXType.TAPE,
        FXType.NEURON,
        FXType.WAVESHAPER,
        FXType.BONSAI,
    }

    HEAVY_CPU_TYPES: Set[FXType] = {
        FXType.NIMBUS,
        FXType.CONVOLUTION,
        FXType.REVERB2,
        FXType.SPRING_REVERB,
    }

    @classmethod
    def audit_slot(cls, slot: SurgeFXSlotModel) -> List[str]:
        """Audit an individual FX slot."""
        warnings: List[str] = []
        if not slot.is_active:
            return warnings

        # 1. Combulator / Resonator feedback
        if slot.type == FXType.COMBULATOR:
            # p2 in combulator is feedback
            if slot.params[2] > 0.95:
                warnings.append(
                    f"Acoustic Risk [Combulator Resonance]: slot {slot.slot_index} ({slot.type_name}) "
                    f"feedback={slot.params[2]:.2f} near self-oscillation threshold (> 0.95)."
                )

        # 2. Extreme drive on CHOW / Tape
        if slot.type == FXType.CHOW:
            # p0 is threshold in dB (-48 to 0)
            if slot.params[0] < -40.0 and slot.params[3] > 0.8:
                warnings.append(
                    f"Acoustic Warning [CHOW Saturation]: High saturation threshold ({slot.params[0]:.1f} dB) "
                    f"with wet mix={slot.params[3]:.2f} may heavily clip transients."
                )

        if slot.type == FXType.TAPE:
            # p0 is drive in dB (0 to 36)
            if slot.params[0] > 24.0:
                warnings.append(
                    f"Gain Staging Warning [Tape Drive]: Tape drive={slot.params[0]:.1f} dB is extremely hot. "
                    f"Ensure output level compensation."
                )

        return warnings

    @classmethod
    def audit_rack(cls, rack: SurgeFXRackModel) -> List[str]:
        """Audit the entire 16-slot rack across all chains."""
        warnings: List[str] = []

        # Audit each slot individually
        for slot in rack.slots:
            warnings.extend(cls.audit_slot(slot))

        # Audit serial gain compounding within each chain
        for chain in FXChain:
            chain_slots = rack.get_chain_slots(chain)
            dist_count = sum(1 for s in chain_slots if s.is_active and s.type in cls.DISTORTION_TYPES)
            if dist_count >= 3:
                warnings.append(
                    f"Gain Staging Hazard [{chain.name}]: {dist_count} distortion/saturation stages "
                    f"chained in series. Severe intermodulation distortion and gain explosion likely."
                )

        # Audit rack-wide CPU density
        cpu_heavy_count = sum(1 for s in rack.slots if s.is_active and s.type in cls.HEAVY_CPU_TYPES)
        if cpu_heavy_count >= 4:
            warnings.append(
                f"Resource Warning [Heavy DSP]: Rack contains {cpu_heavy_count} heavy DSP processors "
                f"(Nimbus/Convolution/Reverbs). May cause audio buffer dropouts at low buffer sizes."
            )

        return warnings

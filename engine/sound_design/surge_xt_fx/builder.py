# engine/sound_design/surge_xt_fx/builder.py
"""
High-Level Multi-FX Rack Builder & Archetypes for Surge XT Effects.

Provides fluent builders and production-ready sound design presets:
- Analog Tape Bus (CHOW + ChowTape + M/S width)
- Granular Shimmer Cloud (Nimbus pitch shimmer + Reverb 2)
- Vintage Lo-Fi Chain (Tape wow/flutter + Bandpass EQ + BBD Ensemble)
- Ambient Drone Space (Floaty Delay + Reverb 2 + Slow Phaser)
"""

from typing import List, Optional, Dict, Any
from .schema import FXType, FXChain, FXBypass, SurgeFXSchema
from .model import SurgeFXSlotModel, SurgeFXRackModel
from .sanitizer import SurgeFXSanitizer


class SurgeFXSlotBuilder:
    """Builder for individual Surge FX slot."""

    def __init__(self, slot_index: int = 0, fx_type: FXType = FXType.OFF, name: str = ""):
        self._slot = SurgeFXSlotModel(slot_index=slot_index, type=fx_type, preset_name=name)

    def with_params(self, params: List[float]) -> "SurgeFXSlotBuilder":
        for i, val in enumerate(params[:SurgeFXSchema.NUM_PARAMS_PER_SLOT]):
            self._slot.params[i] = float(val)
        return self

    def with_param(
        self,
        index: int,
        value: float,
        temposync: bool = False,
        extend: bool = False,
        deactivate: bool = False,
        deform: int = 0,
    ) -> "SurgeFXSlotBuilder":
        self._slot.set_param(index, value, temposync, extend, deactivate, deform)
        return self

    def with_filename(self, filename: str) -> "SurgeFXSlotBuilder":
        self._slot.filename = filename
        return self

    def build(self, sanitize: bool = True) -> SurgeFXSlotModel:
        if sanitize:
            sanitized, _ = SurgeFXSanitizer.sanitize_slot(self._slot)
            return sanitized
        return self._slot.copy()


class SurgeFXRackBuilder:
    """Fluent rack builder for configuring the 16-slot Surge XT multi-FX matrix."""

    def __init__(self, rack_name: Optional[str] = None, name: Optional[str] = None):
        r_name = name or rack_name or "Surge FX Rack"
        self._rack = SurgeFXRackModel(name=r_name)

    def with_slot(self, slot_index: int, slot: SurgeFXSlotModel) -> "SurgeFXRackBuilder":
        self._rack.set_slot(slot_index, slot)
        return self

    def with_chain(self, chain: FXChain, slots: List[SurgeFXSlotModel]) -> "SurgeFXRackBuilder":
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[chain]
        for idx, slot_model in zip(indices, slots[:SurgeFXSchema.SLOTS_PER_CHAIN]):
            self._rack.set_slot(idx, slot_model)
        return self

    def with_bypass_mode(self, mode: FXBypass) -> "SurgeFXRackBuilder":
        self._rack.bypass_mode = mode
        return self

    def add_tape_slot(
        self, chain: FXChain = FXChain.SCENE_A, slot: int = 0, drive: float = 6.0, mix: float = 0.85
    ) -> "SurgeFXRackBuilder":
        slot_idx = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[chain][slot]
        tape_slot = (
            SurgeFXSlotBuilder(slot_idx, FXType.TAPE, "Tape Saturation")
            .with_param(0, drive)
            .with_param(11, mix)
            .build()
        )
        return self.with_slot(slot_idx, tape_slot)

    def build(self, sanitize: bool = True) -> SurgeFXRackModel:
        if sanitize:
            sanitized, _ = SurgeFXSanitizer.sanitize_rack(self._rack)
            return sanitized
        return self._rack.copy()


SurgeFXBuilder = SurgeFXRackBuilder


class SurgeFXArchetypes:
    """Pre-configured multi-FX racks and chain archetypes for AI sound design."""

    @staticmethod
    def create_analog_tape_bus() -> SurgeFXRackModel:
        """
        Master/Bus analog tape saturator and stereo polisher.
        Slots used: Global FX 1..4 (slots 6, 7, 14, 15).
        """
        builder = SurgeFXRackBuilder("Analog Tape Master Bus")

        # Slot 1 (Global 1): CHOW Half-Wave Rectifier
        chow = (
            SurgeFXSlotBuilder(6, FXType.CHOW, "Warm Saturation")
            .with_param(0, -18.0)  # Threshold -18dB
            .with_param(1, 5.0)    # Ratio
            .with_param(2, 0.0)    # Normal polarity
            .with_param(3, 0.65)   # 65% Wet Mix
            .build()
        )

        # Slot 2 (Global 2): Tape (ChowTape magnetic modeling)
        tape = (
            SurgeFXSlotBuilder(7, FXType.TAPE, "15 IPS Studer Style")
            .with_param(0, 6.0)    # Drive +6dB
            .with_param(1, 0.40)   # Saturation
            .with_param(2, 0.50)   # Bias
            .with_param(3, 15.0)   # Speed (15 IPS)
            .with_param(7, 0.15)   # Degrade depth (subtle)
            .with_param(10, 0.70)  # Tone
            .with_param(11, 0.85)  # Output Mix
            .build()
        )

        # Slot 3 (Global 3): EQ (3-Band parametric polish)
        eq = (
            SurgeFXSlotBuilder(14, FXType.EQ, "Bus Sweetener EQ")
            .with_param(0, -1.0)   # Low Gain -1dB
            .with_param(1, 80.0)   # Low Freq
            .with_param(2, 0.5)    # Mid Gain
            .with_param(3, 2500.0) # Mid Freq
            .with_param(5, 1.5)    # High Shelf +1.5dB Air
            .with_param(6, 12000.0)# High Freq
            .build()
        )

        # Slot 4 (Global 4): Mid-Side Tool
        ms = (
            SurgeFXSlotBuilder(15, FXType.MID_SIDE, "Stereo Enhancer")
            .with_param(0, 1.0)    # Mid gain
            .with_param(1, 1.08)   # Side gain (gentle 108% stereo widening)
            .build()
        )

        builder.with_slot(6, chow)
        builder.with_slot(7, tape)
        builder.with_slot(14, eq)
        builder.with_slot(15, ms)
        return builder.build()

    @staticmethod
    def create_granular_shimmer_rack() -> SurgeFXRackModel:
        """
        Ambient granular shimmer rack using Nimbus (Clouds) + Reverb 2.
        Slots used: Send FX 1..4 (slots 4, 5, 12, 13).
        """
        builder = SurgeFXRackBuilder("Granular Shimmer Rack")

        # Slot 1 (Send 1): Nimbus (+12st pitch shimmer cloud)
        nimbus = (
            SurgeFXSlotBuilder(4, FXType.NIMBUS, "Octave Shimmer Granular")
            .with_param(0, 1.0)    # Mode 1 (Pitch Shifting)
            .with_param(1, 0.50)   # Grain Position
            .with_param(2, 0.45)   # Grain Size
            .with_param(3, 12.0)   # Pitch +12 semitones
            .with_param(4, 0.70)   # Density
            .with_param(5, 0.60)   # Texture / Diffusion
            .with_param(6, 0.80)   # Wet Mix
            .with_param(7, 1.0)    # Stereo Spread
            .with_param(8, 0.50)   # Feedback
            .with_param(9, 0.60)   # Internal Reverb
            .build()
        )

        # Slot 2 (Send 2): Reverb 2 (Lush diffuse decay)
        reverb = (
            SurgeFXSlotBuilder(5, FXType.REVERB2, "Cosmic Tail")
            .with_param(0, 0.75)   # Decay
            .with_param(1, 0.05)   # Pre-delay
            .with_param(2, 0.15)   # Low Cut
            .with_param(3, 0.70)   # High Cut
            .with_param(5, 0.85)   # Room Size
            .with_param(6, 0.80)   # Diffusion
            .with_param(7, 1.0)    # 100% Wet (Send)
            .build()
        )

        # Slot 3 (Send 3): 4-Voice Chorus (Thick dimensional movement)
        chorus = (
            SurgeFXSlotBuilder(12, FXType.CHORUS, "Wide Motion Chorus")
            .with_param(0, 0.35)   # Rate
            .with_param(1, 0.60)   # Depth
            .with_param(2, 0.50)   # Feedback
            .with_param(3, 0.80)   # Mix
            .build()
        )

        # Slot 4 (Send 4): Conditioner (Gentle limiting & de-harshing)
        conditioner = (
            SurgeFXSlotBuilder(13, FXType.CONDITIONER, "Dynamics Safety")
            .with_param(0, 0.0)    # Gate off
            .with_param(3, 0.75)   # Limiter active
            .build()
        )

        builder.with_slot(4, nimbus)
        builder.with_slot(5, reverb)
        builder.with_slot(12, chorus)
        builder.with_slot(13, conditioner)
        return builder.build()

    @staticmethod
    def create_vintage_lofi_chain() -> List[SurgeFXSlotModel]:
        """
        4-slot chain for vintage lo-fi tape degradation, vinyl tone, and BBD chorus.
        Suitable for Scene A or Scene B insert chain.
        """
        # Slot 0: Tape degradation
        s0 = (
            SurgeFXSlotBuilder(0, FXType.TAPE, "Worn Cassette")
            .with_param(0, 8.0)    # Drive +8dB
            .with_param(1, 0.55)   # Saturation
            .with_param(3, 7.5)    # 7.5 IPS low speed
            .with_param(7, 0.60)   # Degrade depth (pronounced flutter)
            .with_param(8, 0.45)   # Degrade amount
            .with_param(9, 0.50)   # Degrade variance (random dropouts)
            .with_param(10, 0.40)  # Darker tone
            .build()
        )

        # Slot 1: Bandpass telephone EQ
        s1 = (
            SurgeFXSlotBuilder(1, FXType.EQ, "Lo-Fi Bandpass")
            .with_param(0, -6.0)   # Low Cut
            .with_param(1, 350.0)  # 350 Hz Highpass
            .with_param(2, 2.0)    # Mid poke
            .with_param(3, 1800.0) # 1.8 kHz
            .with_param(5, -8.0)   # High Cut
            .with_param(6, 4500.0) # 4.5 kHz Lowpass
            .build()
        )

        # Slot 2: Vintage BBD Ensemble
        s2 = (
            SurgeFXSlotBuilder(2, FXType.ENSEMBLE, "Warm BBD Chorus")
            .with_param(0, 0.25)   # Slow rate
            .with_param(1, 0.50)   # Depth
            .with_param(3, 0.60)   # Mix
            .build()
        )

        # Slot 3: Floaty Delay
        s3 = (
            SurgeFXSlotBuilder(3, FXType.FLOATY_DELAY, "Ethereal Lo-Fi Repeats")
            .with_param(0, 0.35)   # Delay time
            .with_param(2, 0.40)   # Feedback
            .with_param(9, 0.30)   # 30% Wet Mix
            .build()
        )

        return [s0, s1, s2, s3]

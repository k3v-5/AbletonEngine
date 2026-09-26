# engine/sound_design/surge_xt_fx/rack_factory.py
"""
Surge XT Multi-Slot Sound Design Rack Factory.

Generates production-grade 3-to-4 slot multi-FX chains per musical role:
- DRUMS: Tape saturation (ChowTape) -> Exciter -> Conditioner (bus compression glue).
- BASS: CHOW (warm mid saturation) -> EQ (sub shaping) -> Conditioner -> Mid/Side (mono sub).
- KEYS: Vintage Ensemble (BBD) -> Tape flutter/warmth -> Presence EQ -> Mid/Side width.
- PAD: Nimbus Granular Cloud -> Lush Reverb 2 -> Conditioner -> Stereo Width.
- LEAD: CHOW overdrive -> Tape saturation -> Floaty Delay / Flanger.
- STRINGS: Ensemble BBD -> Airwindows / Tone EQ -> Reverb 2.
- VOCALS: Conditioner (gate/de-ess) -> Tape saturation -> Exciter air -> Mid/Side vocal focus.
- FX: Nimbus granular mangler -> Combulator -> Reverb 2 -> Delay.
"""

from typing import Dict, Any, List, Optional, Union
import logging

from .schema import FXType, FXChain, FXBypass, SurgeFXSchema
from .model import SurgeFXSlotModel, SurgeFXRackModel
from .builder import SurgeFXSlotBuilder, SurgeFXRackBuilder
from .validator import SurgeFXValidator

logger = logging.getLogger("SurgeFXRackFactory")


class SurgeFXRackFactory:
    """Factory for constructing tailored multi-slot Surge XT FX chains."""

    @classmethod
    def build_bass_power_rack(
        cls,
        bpm: float = 120.0,
        drive: float = 0.25,
        mono_sub: bool = True,
        rack_name: str = "Bass_Power_Rack"
    ) -> SurgeFXRackModel:
        """
        4-Slot Bass Channel Strip:
        Slot 1: CHOW Half-Wave Saturation (generates audible mid harmonics)
        Slot 2: 3-Band Parametric EQ (tight sub cut @ 30Hz, punch boost @ 80Hz)
        Slot 3: Conditioner (fast optical leveling & dynamics control)
        Slot 4: Mid-Side Tool (forces mono below 120Hz, keeps mix clean in club PAs)
        """
        builder = SurgeFXRackBuilder(rack_name=rack_name)
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SCENE_A]

        # Slot 1 (Scene A1): CHOW
        s1 = (
            SurgeFXSlotBuilder(slot_index=indices[0], fx_type=FXType.CHOW, name="Bass_ChowSat")
            .with_param(0, -18.0 + (drive * 8.0))   # Threshold (-18dB to -10dB)
            .with_param(1, 3.5 + (drive * 2.5))     # Ratio
            .with_param(2, 0.0)                     # Normal polarity
            .with_param(3, 0.70)                    # Mix
            .build()
        )

        # Slot 2 (Scene A2): EQ
        s2 = (
            SurgeFXSlotBuilder(slot_index=indices[1], fx_type=FXType.EQ, name="Bass_SculptEQ")
            .with_param(0, 1.2)     # Low shelf +1.2dB sub weight
            .with_param(1, 65.0)    # Low freq 65Hz
            .with_param(2, -1.5)    # Mid notch -1.5dB (boxiness cleanup)
            .with_param(3, 350.0)   # Mid freq 350Hz
            .with_param(5, -2.0)    # High shelf cut (anti-fizz)
            .with_param(6, 4500.0)  # High freq 4.5kHz
            .build()
        )

        # Slot 3 (Scene A3): Conditioner
        s3 = (
            SurgeFXSlotBuilder(slot_index=indices[2], fx_type=FXType.CONDITIONER, name="Bass_Dynamics")
            .with_param(0, 0.0)     # Input trim
            .with_param(1, -16.0)   # Comp threshold
            .with_param(2, 3.0)     # Comp ratio 3:1
            .with_param(3, 10.0)    # Attack 10ms
            .with_param(4, 180.0)   # Release 180ms
            .with_param(11, 0.85)   # Mix
            .build()
        )

        # Slot 4 (Scene A4): Mid-Side Tool
        s4 = (
            SurgeFXSlotBuilder(slot_index=indices[3], fx_type=FXType.MID_SIDE, name="Bass_MonoSub")
            .with_param(0, 1.0)     # Mid gain (solid center)
            .with_param(1, 0.80 if mono_sub else 1.0) # Side gain attenuation
            .build()
        )

        builder.with_chain(FXChain.SCENE_A, [s1, s2, s3, s4])
        return builder.build()

    @classmethod
    def build_drum_glue_rack(
        cls,
        bpm: float = 120.0,
        drive: float = 0.30,
        punch: bool = True,
        rack_name: str = "Drum_Glue_Rack"
    ) -> SurgeFXRackModel:
        """
        3-Slot Drum Bus Punch & Glue:
        Slot 1: ChowTape (15 IPS Studer-style magnetic compression & transient rounding)
        Slot 2: Exciter (harmonic presence & top-end air for cymbals/snare crack)
        Slot 3: Conditioner (VCA bus compressor emulation for groove cohesion)
        """
        builder = SurgeFXRackBuilder(rack_name=rack_name)
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SCENE_A]

        # Slot 1 (Scene A1): Tape Saturation
        tape_drive_db = 4.0 + (drive * 8.0) # +4dB to +12dB
        s1 = (
            SurgeFXSlotBuilder(slot_index=indices[0], fx_type=FXType.TAPE, name="Drum_TapeGlue")
            .with_param(0, tape_drive_db)
            .with_param(1, 0.45)   # Saturation
            .with_param(2, 0.50)   # Bias
            .with_param(3, 15.0)   # 15 IPS speed
            .with_param(7, 0.10)   # Degradation
            .with_param(10, 0.65)  # Tone
            .with_param(11, 0.80)  # Mix
            .build()
        )

        # Slot 2 (Scene A2): Exciter
        s2 = (
            SurgeFXSlotBuilder(slot_index=indices[1], fx_type=FXType.EXCITER, name="Drum_TopAir")
            .with_param(0, 0.25)    # Exciter amount
            .with_param(1, 3500.0)  # Crossover frequency 3.5kHz
            .with_param(2, 0.40)    # Harmonics balance
            .with_param(3, 0.60)    # Wet mix
            .build()
        )

        # Slot 3 (Scene A3): Conditioner (Bus Glue)
        s3 = (
            SurgeFXSlotBuilder(slot_index=indices[2], fx_type=FXType.CONDITIONER, name="Drum_BusComp")
            .with_param(0, 0.0)     # Trim
            .with_param(1, -14.0)   # Threshold
            .with_param(2, 2.5 if punch else 4.0) # Ratio 2.5:1
            .with_param(3, 30.0)    # Attack 30ms (lets kick transient punch through)
            .with_param(4, 120.0)   # Auto/BPM-synced release
            .with_param(11, 0.75)   # Parallel glue mix
            .build()
        )

        # Slot 4 (Scene A4): Off
        s4 = SurgeFXSlotBuilder(slot_index=indices[3], fx_type=FXType.OFF).build()

        builder.with_chain(FXChain.SCENE_A, [s1, s2, s3, s4])
        return builder.build()

    @classmethod
    def build_keys_vintage_rack(
        cls,
        bpm: float = 120.0,
        modulation: bool = True,
        rack_name: str = "Keys_Vintage_Rack"
    ) -> SurgeFXRackModel:
        """
        4-Slot Keys & Electric Piano Warmth:
        Slot 1: BBD Ensemble (lush analog bucket-brigade stereo movement)
        Slot 2: Tape (subtle wow/flutter & warm magnetic saturation)
        Slot 3: EQ (cleans 300Hz mud & adds 3kHz bell presence)
        Slot 4: Mid-Side Tool (subtle 110% stereo widening)
        """
        builder = SurgeFXRackBuilder(rack_name=rack_name)
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SCENE_A]

        # Slot 1: Ensemble
        s1 = (
            SurgeFXSlotBuilder(slot_index=indices[0], fx_type=FXType.ENSEMBLE, name="Keys_BBDEnsemble")
            .with_param(0, 0.35)   # Depth
            .with_param(1, 0.20, temposync=True) # Rate
            .with_param(2, 0.55)   # Mix
            .build()
        )

        # Slot 2: Tape
        s2 = (
            SurgeFXSlotBuilder(slot_index=indices[1], fx_type=FXType.TAPE, name="Keys_TapeWarmth")
            .with_param(0, 3.5)    # Drive +3.5dB
            .with_param(1, 0.30)   # Saturation
            .with_param(2, 0.50)   # Bias
            .with_param(3, 7.5)    # 7.5 IPS for vintage lofi character
            .with_param(7, 0.20)   # Subtle flutter
            .with_param(10, 0.60)  # Tone
            .with_param(11, 0.70)  # Mix
            .build()
        )

        # Slot 3: EQ
        s3 = (
            SurgeFXSlotBuilder(slot_index=indices[2], fx_type=FXType.EQ, name="Keys_SweetEQ")
            .with_param(0, -1.0)   # Low cut -1dB
            .with_param(1, 120.0)  # Low freq 120Hz
            .with_param(2, -1.8)   # Mid notch -1.8dB
            .with_param(3, 380.0)  # Mud freq 380Hz
            .with_param(5, 1.4)    # High shelf +1.4dB
            .with_param(6, 3200.0) # Bell presence
            .build()
        )

        # Slot 4: Mid-Side
        s4 = (
            SurgeFXSlotBuilder(slot_index=indices[3], fx_type=FXType.MID_SIDE, name="Keys_StereoAir")
            .with_param(0, 1.0)    # Mid
            .with_param(1, 1.10)   # Side +10% width
            .build()
        )

        builder.with_chain(FXChain.SCENE_A, [s1, s2, s3, s4])
        return builder.build()

    @classmethod
    def build_ambient_pad_rack(
        cls,
        bpm: float = 120.0,
        cloud: bool = True,
        rack_name: str = "Ambient_Pad_Rack"
    ) -> SurgeFXRackModel:
        """
        3-Slot Ambient Granular Cloud:
        Slot 1: Nimbus Granular Texture (Clouds pitch-shifting granular wash)
        Slot 2: 4-Voice Chorus (stereo diffusion)
        Slot 3: Reverb 2 (modern high-density algorithmic tail)
        """
        builder = SurgeFXRackBuilder(rack_name=rack_name)
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SCENE_A]

        # Slot 1: Nimbus
        s1 = (
            SurgeFXSlotBuilder(slot_index=indices[0], fx_type=FXType.NIMBUS, name="Pad_GranularCloud")
            .with_param(0, 1.0)    # Mode: Pitch shift (+12st)
            .with_param(1, 0.65)   # Density
            .with_param(2, 0.60)   # Grain size
            .with_param(3, 0.50)   # Texture
            .with_param(4, 0.45)   # Wet mix
            .build()
        )

        # Slot 2: Chorus
        s2 = (
            SurgeFXSlotBuilder(slot_index=indices[1], fx_type=FXType.CHORUS, name="Pad_DiffusionChorus")
            .with_param(0, 0.25, temposync=True) # Rate
            .with_param(1, 0.40)   # Depth
            .with_param(2, 4.0)    # 4 voices
            .with_param(3, 0.30)   # Feedback
            .with_param(11, 0.50)  # Mix
            .build()
        )

        # Slot 3: Reverb 2
        s3 = (
            SurgeFXSlotBuilder(slot_index=indices[2], fx_type=FXType.REVERB2, name="Pad_LushSpace")
            .with_param(0, 0.70)   # Decay time
            .with_param(1, 0.04)   # Pre-delay
            .with_param(2, 0.15)   # Low cut
            .with_param(3, 0.75)   # High cut
            .with_param(7, 0.40)   # Wet mix
            .with_param(8, 1.0)    # Stereo width
            .build()
        )

        s4 = SurgeFXSlotBuilder(slot_index=indices[3], fx_type=FXType.OFF).build()

        builder.with_chain(FXChain.SCENE_A, [s1, s2, s3, s4])
        return builder.build()

    @classmethod
    def build_lead_overdrive_rack(
        cls,
        bpm: float = 120.0,
        drive: float = 0.35,
        rack_name: str = "Lead_Overdrive_Rack"
    ) -> SurgeFXRackModel:
        """
        3-Slot Lead Synth / Guitar Presence:
        Slot 1: CHOW Half-Wave Drive (aggressive harmonic richness)
        Slot 2: Tape (rounds harsh square-wave edges)
        Slot 3: Floaty Delay (rhythmic ambient bounces without clashing)
        """
        builder = SurgeFXRackBuilder(rack_name=rack_name)
        indices = SurgeFXSchema.CHAIN_TO_SLOT_INDICES[FXChain.SCENE_A]

        # Slot 1: CHOW Overdrive
        s1 = (
            SurgeFXSlotBuilder(slot_index=indices[0], fx_type=FXType.CHOW, name="Lead_ChowDrive")
            .with_param(0, -12.0 + (drive * 6.0))
            .with_param(1, 4.5)
            .with_param(3, 0.60)
            .build()
        )

        # Slot 2: Tape
        s2 = (
            SurgeFXSlotBuilder(slot_index=indices[1], fx_type=FXType.TAPE, name="Lead_TapeSmooth")
            .with_param(0, 5.0)
            .with_param(1, 0.35)
            .with_param(3, 15.0)
            .with_param(10, 0.65)
            .with_param(11, 0.75)
            .build()
        )

        # Slot 3: Floaty Delay
        s3 = (
            SurgeFXSlotBuilder(slot_index=indices[2], fx_type=FXType.FLOATY_DELAY, name="Lead_FloatyDelay")
            .with_param(0, 0.375, temposync=True) # 3/8 delay
            .with_param(1, 0.35)   # Feedback
            .with_param(2, 0.0)    # Pitch shift
            .with_param(3, 0.35)   # Wet mix
            .build()
        )

        s4 = SurgeFXSlotBuilder(slot_index=indices[3], fx_type=FXType.OFF).build()

        builder.with_chain(FXChain.SCENE_A, [s1, s2, s3, s4])
        return builder.build()

    @classmethod
    def create_role_rack(
        cls,
        role: str,
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None,
        track_name: str = "Track"
    ) -> SurgeFXRackModel:
        """
        Dynamically selects and molds a high-tier multi-slot Surge XT FX rack
        based on musical track role and user-applied parameters.
        """
        applied = applied_params or {}
        norm_role = str(role).strip().upper()
        drive_val = float(applied.get("FX A1 Drive", applied.get("Drive", 0.28)))

        rack_name = f"{track_name}_{norm_role}_SurgeRack"

        if norm_role in ("DRUMS", "PERCUSSION", "TOP_LOOP"):
            rack = cls.build_drum_glue_rack(bpm=bpm, drive=drive_val, rack_name=rack_name)
        elif norm_role in ("BASS", "808", "SUB"):
            rack = cls.build_bass_power_rack(bpm=bpm, drive=drive_val, rack_name=rack_name)
        elif norm_role in ("KEYS", "E_PIANO", "PIANO", "GUITAR"):
            rack = cls.build_keys_vintage_rack(bpm=bpm, rack_name=rack_name)
        elif norm_role in ("PAD", "TEXTURE_FOLEY", "FOLEY"):
            rack = cls.build_ambient_pad_rack(bpm=bpm, rack_name=rack_name)
        elif norm_role in ("LEAD", "COUNTER_LEAD", "SYNTH", "ARPS"):
            rack = cls.build_lead_overdrive_rack(bpm=bpm, drive=drive_val, rack_name=rack_name)
        else:
            # Universal warm bus fallback
            rack = cls.build_keys_vintage_rack(bpm=bpm, rack_name=rack_name)

        # Allow user overrides on Slot 1 Drive/Mix if explicitly molded
        if "FX A1 Mix" in applied:
            slot0 = rack.get_slot(0)
            slot0.params[3 if slot0.type == FXType.CHOW else 11] = float(applied["FX A1 Mix"])

        return rack

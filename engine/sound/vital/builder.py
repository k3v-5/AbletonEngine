# engine/sound/vital/builder.py
"""
Procedural Patch Synthesis Builder for Vital (.vital)
Produces fully articulated VitalPresetSpec instances for Bass, 808, Keys, Leads, Pads, and Custom.
"""

from typing import Dict, Any, Optional
from engine.sound.vital.models import (
    VitalPresetSpec,
    VitalPresetStyle,
    VitalOscillatorSpec,
    VitalFilterSpec,
    VitalEnvelopeSpec,
    VitalLfoSpec,
    VitalEffectsSpec,
    VitalModulationRouting
)

class VitalPatchBuilder:
    """Procedural sound designer creating tailored Vital synthesizers patches."""

    @staticmethod
    def build_reese_bass(
        sub_weight: float = 0.8,
        detune_amount: float = 3.5,
        filter_cutoff: float = 72.0,
        drive: float = 6.0,
        name: str = "PIE_Heavy_Reese"
    ) -> VitalPresetSpec:
        """
        Builds a modern heavy Reese Bass with stereo detuned saw saws,
        clean direct sub-oscillator, warm analog saturation, and macro controls.
        """
        osc1 = VitalOscillatorSpec(
            on=True,
            wave_frame=0.0,
            level=0.75,
            transpose=0,
            unison_voices=5,
            unison_detune=float(detune_amount),
            unison_blend=0.85,
            destination=1  # Filter 1
        )
        osc2 = VitalOscillatorSpec(
            on=True,
            wave_frame=64.0,
            level=0.60,
            transpose=-12,
            unison_voices=7,
            unison_detune=float(detune_amount * 1.15),
            unison_blend=0.80,
            destination=1  # Filter 1
        )
        # Sub oscillator direct out to keep mono fundamental solid
        osc3 = VitalOscillatorSpec(
            on=True,
            wave_frame=0.0,
            level=float(sub_weight),
            transpose=-24,
            unison_voices=1,
            destination=3  # Direct Out
        )
        
        filter1 = VitalFilterSpec(
            on=True,
            model=0,  # Analog
            style=1,  # 24dB
            cutoff=float(filter_cutoff),
            resonance=0.22,
            drive=float(drive),
            blend=0.0  # Lowpass
        )
        
        env1 = VitalEnvelopeSpec(
            attack=0.005,
            decay=0.8,
            sustain=0.75,
            release=0.25
        )
        
        lfo1 = VitalLfoSpec(
            sync=True,
            tempo=6,  # 1/4 note subtle pulse
            smooth_time=-6.0
        )
        
        fx = VitalEffectsSpec(
            distortion_on=True,
            distortion_drive=float(drive),
            distortion_type=0,  # Soft clip
            distortion_mix=0.85,
            chorus_on=True,
            chorus_dry_wet=0.25,
            compressor_on=True,
            compressor_band_gain=3.0
        )
        
        mods = [
            VitalModulationRouting(source="macro_control_1", destination="filter_1_cutoff", amount=0.4),
            VitalModulationRouting(source="macro_control_2", destination="distortion_drive", amount=0.5),
            VitalModulationRouting(source="macro_control_3", destination="osc_1_unison_detune", amount=0.6),
            VitalModulationRouting(source="macro_control_4", destination="osc_3_level", amount=0.4),
            VitalModulationRouting(source="lfo_1", destination="filter_1_cutoff", amount=0.15)
        ]
        
        return VitalPresetSpec(
            preset_name=name,
            author="Ableton PIE Engine",
            comments="Procedural Heavy Reese Bass with direct sub routing and analog drive",
            preset_style=VitalPresetStyle.BASS,
            macro1="CUTOFF",
            macro2="DRIVE",
            macro3="DETUNE",
            macro4="SUB LVL",
            oscillators=[osc1, osc2, osc3],
            filters=[filter1],
            envelopes=[env1],
            lfos=[lfo1],
            effects=fx,
            modulations=mods
        )

    @staticmethod
    def build_hard_808(
        distortion_drive: float = 12.0,
        glide_time: float = 0.08,
        pitch_decay: float = 0.04,
        name: str = "PIE_Carnage_808"
    ) -> VitalPresetSpec:
        """
        Builds an aggressive modern 808 with transient punch pitch envelope,
        hard clipping saturation, and portamento glide.
        """
        osc1 = VitalOscillatorSpec(
            on=True,
            wave_frame=0.0,
            level=0.88,
            transpose=-24,
            unison_voices=1,
            destination=1
        )
        osc2 = VitalOscillatorSpec(
            on=True,
            wave_frame=128.0,
            level=0.35,
            transpose=0,
            unison_voices=1,
            destination=1
        )
        
        filter1 = VitalFilterSpec(
            on=True,
            model=1,  # Dirty
            style=1,  # 24dB
            cutoff=68.0,
            drive=float(distortion_drive / 2.0),
            blend=0.0
        )
        
        amp_env = VitalEnvelopeSpec(
            attack=0.002,
            decay=1.6,
            sustain=0.0,
            release=0.18,
            decay_power=-3.0
        )
        
        pitch_env = VitalEnvelopeSpec(
            attack=0.001,
            decay=float(pitch_decay),
            sustain=0.0,
            release=0.02,
            decay_power=-5.0
        )
        
        fx = VitalEffectsSpec(
            distortion_on=True,
            distortion_drive=float(distortion_drive),
            distortion_type=1,  # Hard clip
            distortion_mix=1.0,
            compressor_on=True,
            compressor_band_gain=4.5
        )
        
        mods = [
            VitalModulationRouting(source="env_2", destination="osc_1_transpose", amount=0.35),
            VitalModulationRouting(source="macro_control_1", destination="env_2_decay", amount=0.5),
            VitalModulationRouting(source="macro_control_2", destination="distortion_drive", amount=0.6),
            VitalModulationRouting(source="macro_control_3", destination="portamento_time", amount=0.7),
            VitalModulationRouting(source="macro_control_4", destination="env_1_decay", amount=0.4)
        ]
        
        settings = {
            "portamento_time": float(glide_time),
            "portamento_slope": 0.0,
            "legato": 1.0
        }
        
        return VitalPresetSpec(
            preset_name=name,
            author="Ableton PIE Engine",
            comments="Procedural Hard 808 with pitch punch and hard clipping",
            preset_style=VitalPresetStyle.BASS,
            macro1="PUNCH",
            macro2="DISTORT",
            macro3="GLIDE",
            macro4="DECAY",
            oscillators=[osc1, osc2],
            filters=[filter1],
            envelopes=[amp_env, pitch_env],
            effects=fx,
            modulations=mods,
            settings=settings
        )

    @staticmethod
    def build_neo_soul_keys(
        warmth: float = 0.7,
        tremolo_rate: float = 4.0,
        chorus_depth: float = 0.35,
        name: str = "PIE_Warm_Rhodes"
    ) -> VitalPresetSpec:
        """
        Builds a lush warm electric piano / neo soul keys patch
        with subtle tremolo, lush chorus, and vintage character.
        """
        osc1 = VitalOscillatorSpec(
            on=True,
            wave_frame=36.0,
            level=0.75,
            transpose=0,
            unison_voices=1,
            destination=1
        )
        osc2 = VitalOscillatorSpec(
            on=True,
            wave_frame=12.0,
            level=0.28,
            transpose=12,
            unison_voices=1,
            destination=1
        )
        
        cutoff_val = 60.0 + float(warmth) * 35.0
        filter1 = VitalFilterSpec(
            on=True,
            model=0,  # Analog
            style=0,  # 12dB
            cutoff=cutoff_val,
            resonance=0.12,
            blend=0.0
        )
        
        env1 = VitalEnvelopeSpec(
            attack=0.015,
            decay=1.4,
            sustain=0.45,
            release=0.38
        )
        
        lfo1 = VitalLfoSpec(
            sync=False,
            frequency=float(tremolo_rate),
            waveform_name="Sine"
        )
        
        fx = VitalEffectsSpec(
            chorus_on=True,
            chorus_dry_wet=float(chorus_depth),
            chorus_voices=4,
            delay_on=True,
            delay_dry_wet=0.20,
            delay_tempo=7,  # 1/8
            delay_style=2,  # Ping Pong
            reverb_on=True,
            reverb_dry_wet=0.28,
            reverb_decay_time=2.2
        )
        
        mods = [
            VitalModulationRouting(source="macro_control_1", destination="filter_1_cutoff", amount=0.5),
            VitalModulationRouting(source="macro_control_2", destination="lfo_1_frequency", amount=0.6),
            VitalModulationRouting(source="macro_control_3", destination="chorus_dry_wet", amount=0.5),
            VitalModulationRouting(source="macro_control_4", destination="reverb_dry_wet", amount=0.5),
            VitalModulationRouting(source="lfo_1", destination="osc_1_level", amount=0.15)
        ]
        
        return VitalPresetSpec(
            preset_name=name,
            author="Ableton PIE Engine",
            comments="Neo-Soul Electric Piano with vintage tremolo and space",
            preset_style=VitalPresetStyle.KEYS,
            macro1="WARMTH",
            macro2="TREMOLO",
            macro3="CHORUS",
            macro4="SPACE",
            oscillators=[osc1, osc2],
            filters=[filter1],
            envelopes=[env1],
            lfos=[lfo1],
            effects=fx,
            modulations=mods
        )

    @staticmethod
    def build_lead_hook(
        brightness: float = 0.8,
        portamento: float = 0.05,
        ping_pong_delay: float = 0.3,
        name: str = "PIE_Euphoric_Lead"
    ) -> VitalPresetSpec:
        """
        Builds a cutting synth lead with 7-voice unison spread,
        dynamic cutoff envelope, and stereo ping pong delay.
        """
        osc1 = VitalOscillatorSpec(
            on=True,
            wave_frame=0.0,
            level=0.72,
            transpose=0,
            unison_voices=7,
            unison_detune=2.4,
            destination=1
        )
        osc2 = VitalOscillatorSpec(
            on=True,
            wave_frame=128.0,
            level=0.50,
            transpose=12,
            unison_voices=3,
            unison_detune=1.5,
            destination=1
        )
        
        cutoff_val = 70.0 + float(brightness) * 45.0
        filter1 = VitalFilterSpec(
            on=True,
            model=2,  # Ladder
            style=1,  # 24dB
            cutoff=cutoff_val,
            resonance=0.28,
            drive=3.0,
            blend=0.0
        )
        
        env1 = VitalEnvelopeSpec(
            attack=0.006,
            decay=0.6,
            sustain=0.82,
            release=0.3
        )
        
        fx = VitalEffectsSpec(
            distortion_on=True,
            distortion_drive=4.5,
            distortion_type=0,
            delay_on=True,
            delay_dry_wet=float(ping_pong_delay),
            delay_tempo=7,
            delay_style=2,  # Ping Pong
            reverb_on=True,
            reverb_dry_wet=0.26,
            reverb_decay_time=2.4
        )
        
        mods = [
            VitalModulationRouting(source="macro_control_1", destination="filter_1_cutoff", amount=0.5),
            VitalModulationRouting(source="macro_control_2", destination="delay_dry_wet", amount=0.6),
            VitalModulationRouting(source="macro_control_3", destination="reverb_dry_wet", amount=0.5),
            VitalModulationRouting(source="macro_control_4", destination="portamento_time", amount=0.7)
        ]
        
        settings = {
            "portamento_time": float(portamento),
            "legato": 1.0
        }
        
        return VitalPresetSpec(
            preset_name=name,
            author="Ableton PIE Engine",
            comments="Euphoric Lead Hook with 7-voice supersaw and ping-pong delay",
            preset_style=VitalPresetStyle.LEAD,
            macro1="BRIGHT",
            macro2="DELAY",
            macro3="REVERB",
            macro4="GLIDE",
            oscillators=[osc1, osc2],
            filters=[filter1],
            envelopes=[env1],
            effects=fx,
            modulations=mods,
            settings=settings
        )

    @staticmethod
    def build_custom(spec_dict: Dict[str, Any]) -> VitalPresetSpec:
        """
        Builds a custom Vital patch from a dictionary specification or prompt synthesis.
        """
        name = spec_dict.get("name", "PIE_Custom_Patch")
        style_str = spec_dict.get("style", "Experimental")
        try:
            style = VitalPresetStyle(style_str)
        except Exception:
            style = VitalPresetStyle.EXPERIMENTAL
            
        osc1_unison = int(spec_dict.get("osc1_unison", 1))
        osc1_detune = float(spec_dict.get("osc1_detune", 2.0))
        cutoff = float(spec_dict.get("cutoff", 85.0))
        drive = float(spec_dict.get("drive", 0.0))
        
        osc1 = VitalOscillatorSpec(
            on=True,
            level=float(spec_dict.get("osc1_level", 0.707)),
            transpose=int(spec_dict.get("osc1_transpose", 0)),
            unison_voices=osc1_unison,
            unison_detune=osc1_detune
        )
        
        filter1 = VitalFilterSpec(
            on=True,
            cutoff=cutoff,
            drive=drive,
            resonance=float(spec_dict.get("resonance", 0.0))
        )
        
        fx = VitalEffectsSpec(
            distortion_on=drive > 1.0,
            distortion_drive=drive,
            delay_on=bool(spec_dict.get("delay", False)),
            reverb_on=bool(spec_dict.get("reverb", False))
        )
        
        return VitalPresetSpec(
            preset_name=name,
            author=spec_dict.get("author", "Ableton PIE Engine"),
            comments=spec_dict.get("comments", "Procedurally synthesized custom patch"),
            preset_style=style,
            macro1=spec_dict.get("macro1", "MACRO 1"),
            macro2=spec_dict.get("macro2", "MACRO 2"),
            macro3=spec_dict.get("macro3", "MACRO 3"),
            macro4=spec_dict.get("macro4", "MACRO 4"),
            oscillators=[osc1],
            filters=[filter1],
            effects=fx
        )

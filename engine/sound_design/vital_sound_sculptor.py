# engine/sound_design/vital_sound_sculptor.py
"""
Vital Sound Sculptor.

Translates high-level sonic directives (brightness, warmth/drive, punch,
sustain, space, stereo width, and movement) into bounded, musical parameter
transformations on a cloned Vital preset.

Implements the 7 Elite Acoustic Principles discovered via forensic reverse engineering of KSHMR presets:
1. Clean Headroom Wavetable discipline (Basic Shapes / pure harmonics).
2. The 7-Voice Roland JP-8000 Unison Sweet Spot (~1.95 detune).
3. The Zero-Delay Anti-Clutter Rule (delay kept OFF inside synth; reverb pre-low cut at 25.0).
4. Mid-Range Focused Distortion (Soft Clip with distortion_filter_cutoff = 80.0 / 830 Hz).
5. Transient Laser Pitch-Punch (35ms logarithmic env_2 drop into osc transpose via Macro 1).
6. Subtle White Noise Air Layering (14-18% level, loop mode for analog top-end sheen).
7. Logarithmic Decay Power Invariant (env_1_decay_power = -2.0, sustain = 1.0 for sidechain pumping).
"""

from typing import Dict, Any, Optional
import copy
import logging

from engine.sound_design.vital_parameter_schema import VitalParameterSchema
from engine.sound_design.vital_wavetable_synth import WavetableSynthesizer

logger = logging.getLogger("VitalSoundSculptor")


class VitalSoundSculptor:
    """
    Transforms Vital preset parameters according to macro-acoustic dimensions,
    strictly abiding by the 7 commercial production principles of KSHMR.
    """

    @classmethod
    def sculpt_preset(
        cls,
        base_preset: Dict[str, Any],
        directives: Dict[str, Any],
        preset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Applies a dictionary of high-level directives to sculpt a new sound.

        Supported Directives:
            - brightness (0.0 - 1.0): Warm/dark -> ultra-bright/piercing + White Noise air.
            - warmth_drive (0.0 - 1.0): Clean/pure -> analog saturated tube with 80.0 mid-focus.
            - punch (0.0 - 1.0): Soft attack -> snappy click + 35ms laser pitch-drop on Macro 1.
            - decay_sustain (0.0 - 1.0): Short pluck -> 100% sustain for DAW sidechain pumping.
            - space_dimension (0.0 - 1.0): Bone-dry -> lush reverb (zero internal delay to protect mix).
            - stereo_width (0.0 - 1.0): Mono -> 7-voice JP-8000 supersaw + octave stacking.
            - movement (0.0 - 1.0): Static tone -> rhythmic LFO wavetable & filter modulation.
            - custom_wavetable (str): "FM", "VOCAL", "ANALOG", "BASIC_SHAPES" to inject.
            - is_bass (bool): If True, strictly protects mono low-end and prevents reverb mud.
            - delay (bool): Explicitly enables internal delay if desired (defaults to False).
            - ott (bool): Explicitly forces multiband OTT compression.
        """
        patch = copy.deepcopy(base_preset)
        settings = patch.get("settings", {})

        if preset_name:
            patch["preset_name"] = preset_name
            patch["comments"] = f"Sculpted by AbletonEngine AI ({preset_name})"

        is_bass = directives.get("is_bass", False)
        if not is_bass:
            style_str = (patch.get("preset_style") or "").upper()
            is_bass = "BASS" in style_str or "808" in style_str or "SUB" in style_str

        # 1. Principle 1: Wavetable Selection & Clean Harmonic Backbone
        if "custom_wavetable" in directives and directives["custom_wavetable"]:
            wt_type = str(directives["custom_wavetable"]).upper()
            new_wt = WavetableSynthesizer.build_morphing_wavetable(wt_type)
            if "wavetables" in settings and isinstance(settings["wavetables"], list):
                if len(settings["wavetables"]) > 0:
                    settings["wavetables"][0] = new_wt
                else:
                    settings["wavetables"].append(new_wt)

        # 2. Principle 6: Brightness & Subtle White Noise Air Layering
        brightness_val = float(directives.get("brightness", 0.5))
        cls._apply_brightness(settings, brightness_val, is_bass=is_bass)

        # 3. Principle 4: Mid-Range Focused Distortion (80.0 Cutoff Rule)
        warmth_val = float(directives.get("warmth_drive", 0.3))
        cls._apply_warmth_drive(settings, warmth_val)

        # 4. Principle 5: Transient Laser Pitch-Punch (35ms Drop)
        punch_val = float(directives.get("punch", 0.5))
        cls._apply_punch(settings, patch, punch_val)

        # 5. Principle 7: Logarithmic Envelopes & Sustain Calibration
        decay_val = float(directives.get("decay_sustain", 0.6))
        cls._apply_decay_sustain(settings, decay_val)

        # Support explicit ADSR envelope overrides for ambient pads, drones, or tight clicks
        if "attack" in directives:
            settings["env_1_attack"] = max(0.001, min(15.0, float(directives["attack"])))
        if "decay" in directives:
            settings["env_1_decay"] = max(0.02, min(15.0, float(directives["decay"])))
        if "sustain" in directives:
            settings["env_1_sustain"] = max(0.0, min(1.0, float(directives["sustain"])))
        if "release" in directives:
            settings["env_1_release"] = max(0.01, min(15.0, float(directives["release"])))

        # 6. Principle 3: Zero-Delay Anti-Clutter & Pre-Filtered Reverb
        space_val = float(directives.get("space_dimension", 0.3))
        enable_delay = directives.get("delay", False)
        cls._apply_space_dimension(settings, space_val, is_bass=is_bass, force_delay=enable_delay)

        # 7. Principle 2: 7-Voice JP-8000 Unison Sweet Spot & Harmonic Stacking
        width_val = float(directives.get("stereo_width", 0.5))
        cls._apply_stereo_width(settings, width_val, is_bass=is_bass)
        if not is_bass and width_val > 0.55:
            cls._apply_harmonic_octave_stacking(settings, width_val)

        # 8. Movement and LFO Modulation
        if "movement" in directives:
            cls._apply_movement(settings, float(directives["movement"]))

        # 9. Multiband Compressor / OTT Stage (Calibrated to KSHMR Averages)
        force_ott = directives.get("ott", False)
        if force_ott or warmth_val > 0.40 or brightness_val > 0.65:
            cls._apply_multiband_compression(settings, warmth_val)

        # 10. Dynamic 3-Band EQ Stage
        if brightness_val > 0.50 or is_bass:
            cls._apply_eq(settings, brightness_val, warmth_val, is_bass=is_bass)

        # 11. Acoustic Integrity Gatekeeper (Non-negotiable invariants)
        settings = VitalParameterSchema.enforce_anti_silence_invariants(settings)
        patch["settings"] = settings

        return patch

    @classmethod
    def _apply_brightness(cls, settings: Dict[str, Any], val: float, is_bass: bool = False) -> None:
        """
        Scales filter cutoff safely between 42.0 and 126.0.
        If brightness is high (>0.65) and not bass, injects subtle White Noise air (Principle 6).
        """
        b = max(0.0, min(1.0, val))
        target_cutoff = 42.0 + (b ** 1.3) * (126.0 - 42.0)
        settings["filter_1_cutoff"] = target_cutoff
        settings["filter_1_resonance"] = 0.10 + b * 0.30

        if b > 0.85:
            settings["filter_1_mix"] = 1.0

        # Principle 6: Subtle White Noise Air Layering (14% - 18% level, loop mode)
        if b > 0.65 and not is_bass:
            noise_sample = WavetableSynthesizer.generate_sampler_buffer("WHITE_NOISE", duration_sec=1.0)
            settings["sample"] = noise_sample
            settings["sample_on"] = 1.0
            settings["sample_level"] = 0.14 + (b - 0.65) * 0.12  # Clamped between 0.14 and 0.18
            settings["sample_loop"] = 1.0
            settings["sample_destination"] = 3.0  # Direct to FX rack (bypasses filter)

    @classmethod
    def _apply_warmth_drive(cls, settings: Dict[str, Any], val: float) -> None:
        """
        Principle 4: Mid-Range Focused Distortion.
        Uses Soft Clip (type 0.0) with distortion_filter_cutoff = 80.0 (~830 Hz)
        to saturate the body without high-end fizz.
        """
        w = max(0.0, min(1.0, val))
        if w > 0.15:
            settings["distortion_on"] = 1.0
            settings["distortion_type"] = 0.0  # Soft Clip
            settings["distortion_filter_cutoff"] = 80.0  # The KSHMR mid-focus rule
            settings["distortion_filter_blend"] = 0.0
            # Drive range: +2.0 dB up to +18.0 dB (sweet spot)
            drive_db = 2.0 + (w * 16.0)
            settings["distortion_drive"] = drive_db
            settings["distortion_mix"] = min(1.0, 0.40 + w * 0.60)
            settings["filter_1_drive"] = w * 4.0
        else:
            settings["distortion_on"] = 0.0
            settings["filter_1_drive"] = 0.0

    @classmethod
    def _apply_punch(cls, settings: Dict[str, Any], patch: Dict[str, Any], val: float) -> None:
        """
        Principle 5: Transient Laser Pitch-Punch.
        Shapes attack envelope and configures a 35ms logarithmic env_2 drop into oscillator pitch.
        """
        p = max(0.0, min(1.0, val))
        attack_sec = 0.050 * (1.0 - p) + 0.001
        settings["env_1_attack"] = attack_sec

        # KSHMR Laser Pitch-Punch: env_2 (35ms, decay_power -2.0) -> macro_control_1 -> osc transpose
        if p > 0.50:
            settings["env_2_attack"] = 0.0
            settings["env_2_decay"] = 0.035  # Exactly 35ms
            settings["env_2_sustain"] = 0.0
            settings["env_2_decay_power"] = -2.0
            settings["macro_control_1"] = 0.0
            patch["macro1"] = "PUNCH DROP"

            mod_list = settings.get("modulations", [])
            pitch_mod_amt = 0.09 + (p - 0.50) * 0.08  # 0.09 to 0.13

            # Slot 0: env_2 -> macro_control_1
            if len(mod_list) > 0:
                mod_list[0] = {"source": "env_2", "destination": "macro_control_1"}
                settings["modulation_1_amount"] = 1.0
            # Slot 1: macro_control_1 -> osc_1_transpose
            if len(mod_list) > 1:
                mod_list[1] = {"source": "macro_control_1", "destination": "osc_1_transpose"}
                settings["modulation_2_amount"] = pitch_mod_amt
            # Slot 2: macro_control_1 -> osc_2_transpose
            if len(mod_list) > 2:
                mod_list[2] = {"source": "macro_control_1", "destination": "osc_2_transpose"}
                settings["modulation_3_amount"] = pitch_mod_amt
            # Slot 3: macro_control_1 -> osc_3_transpose
            if len(mod_list) > 3:
                mod_list[3] = {"source": "macro_control_1", "destination": "osc_3_transpose"}
                settings["modulation_4_amount"] = pitch_mod_amt

    @classmethod
    def _apply_decay_sustain(cls, settings: Dict[str, Any], val: float) -> None:
        """
        Principle 7: Logarithmic Envelopes (decay_power = -2.0) and Sustain.
        Sustain defaults to 1.0 for leads/chords to allow clean DAW sidechain pumping.
        """
        d = max(0.0, min(1.0, val))
        settings["env_1_decay_power"] = -2.0
        settings["env_1_release_power"] = -2.0

        if d < 0.30:
            # Pluck mode
            settings["env_1_sustain"] = 0.0
            decay_sec = 0.18 + (d / 0.30) * 0.30
            settings["env_1_decay"] = decay_sec
            settings["env_1_release"] = 0.15
        elif d < 0.60:
            # Semi-sustained
            settings["env_1_sustain"] = 0.70
            settings["env_1_decay"] = 0.80
            settings["env_1_release"] = 0.40
        else:
            # Full 100% Sustain for massive festival wall of sound (sidechain friendly)
            settings["env_1_sustain"] = 1.0
            settings["env_1_decay"] = 1.00
            settings["env_1_release"] = 0.55

    @classmethod
    def _apply_space_dimension(
        cls,
        settings: Dict[str, Any],
        val: float,
        is_bass: bool = False,
        force_delay: bool = False
    ) -> None:
        """
        Principle 3: The Zero-Delay Anti-Clutter Rule.
        Delay is kept OFF by default to keep the mix pristine (delays are processed via DAW sends).
        Reverb uses pre_low_cutoff at 25.0 to protect sub frequencies.
        """
        s = max(0.0, min(1.0, val))

        # Always protect sub-bass from reverb mud
        settings["reverb_pre_low_cutoff"] = 45.0 if is_bass else 25.0

        if is_bass:
            if s > 0.45:
                settings["reverb_on"] = 1.0
                settings["reverb_dry_wet"] = min(0.15, s * 0.18)
                settings["reverb_size"] = 0.40
            else:
                settings["reverb_on"] = 0.0
            settings["delay_on"] = 0.0
            return

        # Polyphonic / Lead instruments
        if s > 0.10:
            settings["reverb_on"] = 1.0
            settings["reverb_dry_wet"] = 0.15 + s * 0.35  # Average ~0.35
            settings["reverb_size"] = 0.45 + s * 0.40     # Average ~0.65
            settings["reverb_decay_time"] = -1.0 + s * 3.5
        else:
            settings["reverb_on"] = 0.0

        # Principle 3: Delay OFF by default, unless explicitly requested
        if force_delay or s > 0.85:
            settings["delay_on"] = 1.0
            settings["delay_dry_wet"] = 0.20
            settings["delay_feedback"] = 0.45
            settings["delay_filter_cutoff"] = 70.0
        else:
            settings["delay_on"] = 0.0

    @classmethod
    def _apply_stereo_width(cls, settings: Dict[str, Any], val: float, is_bass: bool = False) -> None:
        """
        Principle 2: The 7-Voice JP-8000 Unison Sweet Spot (~1.95 detune).
        Provides a rock-solid mono core with wide side stereo without phase blur.
        """
        w = max(0.0, min(1.0, val))

        if is_bass:
            settings["osc_1_unison_voices"] = 1.0
            settings["osc_1_unison_detune"] = 0.0
            settings["polyphony"] = 1.0
            return

        if w < 0.20:
            # Focused mono / dual
            settings["osc_1_unison_voices"] = 1.0
            settings["osc_1_unison_detune"] = 0.0
        elif w < 0.45:
            # 4 voices
            settings["osc_1_unison_voices"] = 4.0
            settings["osc_1_unison_detune"] = 1.20
        elif w < 0.85:
            # Principle 2: The 7-Voice Sweet Spot (JP-8000)
            settings["osc_1_unison_voices"] = 7.0
            settings["osc_1_unison_detune"] = 1.80 + (w - 0.45) * 0.60  # Centers around 1.95
            settings["osc_1_detune_power"] = 1.5
        else:
            # 16-Voice Extreme
            settings["osc_1_unison_voices"] = 16.0
            settings["osc_1_unison_detune"] = 2.50

    @classmethod
    def _apply_harmonic_octave_stacking(cls, settings: Dict[str, Any], width_val: float) -> None:
        """
        Stacking calibrated to KSHMR voice balances:
        Osc 1: Fundamental 0 st (7 voices)
        Osc 2: Upper octave +12 st (5-7 voices, detune 0.14)
        Osc 3: Sub/Body fundamental 0 st (1-3 voices centered)
        """
        # Osc 2: Upper octave (+12 semitones)
        settings["osc_2_on"] = 1.0
        settings["osc_2_level"] = 0.52
        settings["osc_2_transpose"] = 12.0
        settings["osc_2_unison_voices"] = 5.0 if width_val < 0.75 else 7.0
        settings["osc_2_unison_detune"] = 1.40

        # Osc 3: Body / Fundamental layer (0 semitones, tight focus)
        settings["osc_3_on"] = 1.0
        settings["osc_3_level"] = 0.48
        settings["osc_3_transpose"] = 0.0
        settings["osc_3_unison_voices"] = 1.0 if width_val < 0.75 else 3.0
        settings["osc_3_unison_detune"] = 0.50
        settings["osc_3_destination"] = 1.0

    @classmethod
    def _apply_multiband_compression(cls, settings: Dict[str, Any], warmth_val: float) -> None:
        """
        Applies Vital's native OTT multiband compression calibrated to KSHMR averages:
        Mix ~25-30% (lets dry transient punch through while gluing tails),
        Band gain ~13.3 dB, High gain ~16.9 dB.
        """
        settings["compressor_on"] = 1.0
        settings["compressor_mix"] = min(0.35, 0.22 + warmth_val * 0.15)  # KSHMR avg is 0.24
        settings["compressor_attack"] = 0.15
        settings["compressor_release"] = 0.20
        settings["compressor_band_gain"] = 13.5
        settings["compressor_high_gain"] = 16.9
        settings["compressor_low_gain"] = 13.0

    @classmethod
    def _apply_eq(cls, settings: Dict[str, Any], brightness_val: float, warmth_val: float, is_bass: bool = False) -> None:
        """Applies 3-band EQ shaping for mix clarity and presence."""
        settings["eq_on"] = 1.0
        if is_bass:
            settings["eq_low_cutoff"] = 35.0
            settings["eq_low_gain"] = min(3.0, 1.0 + warmth_val * 2.0)
            settings["eq_high_cutoff"] = 85.0
            settings["eq_high_gain"] = -4.0
        else:
            settings["eq_low_cutoff"] = 42.0   # Clean low cut below ~160 Hz
            settings["eq_low_gain"] = -6.0
            settings["eq_high_cutoff"] = 98.0  # Sparkle above 7 kHz
            settings["eq_high_gain"] = min(3.5, 1.5 + (brightness_val - 0.5) * 3.5)

    @classmethod
    def _apply_movement(cls, settings: Dict[str, Any], val: float) -> None:
        """Modulates wavetable frame or filter with LFO 1."""
        m = max(0.0, min(1.0, val))
        if m > 0.15:
            tempo_step = 7.0 + (m * 4.0)
            settings["lfo_1_tempo"] = round(tempo_step)
            settings["lfo_1_sync"] = 1.0
            settings["osc_1_wave_frame"] = m * 200.0

            modulations = settings.get("modulations", [])
            if isinstance(modulations, list) and len(modulations) > 4:
                modulations[4] = {
                    "source": "lfo_1",
                    "destination": "filter_1_cutoff",
                    "amount": m * 0.40,
                    "bipolar": 0.0,
                    "bypass": 0.0,
                    "power": 0.0,
                    "stereo": 0.0
                }
                settings["modulation_5_amount"] = m * 0.40

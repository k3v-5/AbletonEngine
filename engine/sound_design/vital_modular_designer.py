# engine/sound_design/vital_modular_designer.py
"""
Vital Modular Designer.

Materializes granular specifications (custom waveforms, specialized filter models
like Diode 303/Comb, LFO shapes like Sample & Hold, and modulation routing matrices)
into a production-grade .vital preset with organic analog variation.
"""

from typing import Dict, Any, List, Optional
import copy
import math
import random
import logging

from engine.sound_design.vital_parameter_schema import VitalParameterSchema
from engine.sound_design.vital_wavetable_synth import WavetableSynthesizer

logger = logging.getLogger("VitalModularDesigner")


class VitalModularDesigner:
    """
    Granular synthesizer architect for Vital.
    Converts sanitized component specifications into physical Vital DSP parameters.
    """

    # Filter model mapping to Vital internal float constants
    FILTER_MODEL_MAP: Dict[str, float] = {
        "ANALOG_12": 0.0,
        "ANALOG_24": 0.0,
        "DIRTY": 1.0,
        "LADDER": 2.0,
        "DIGITAL": 3.0,
        "DIODE_303": 4.0,
        "FORMANT": 5.0,
        "COMB": 6.0
    }

    # Filter mode mapping: 0.0=LowPass, 1.0=BandPass, 2.0=HighPass
    FILTER_MODE_MAP: Dict[str, float] = {
        "LOW_PASS": 0.0,
        "BAND_PASS": 1.0,
        "HIGH_PASS": 2.0,
        "NOTCH": 1.0
    }

    # LFO tempo sync mapping (Vital internal logarithmic tempo scale)
    LFO_RATE_MAP: Dict[str, float] = {
        "1/64": 13.0,
        "1/32": 12.0,
        "1/16": 11.0,
        "1/8": 9.0,
        "1/4": 7.0,
        "1/2": 6.0,
        "1_BAR": 5.0,
        "2_BARS": 4.0,
        "4_BARS": 3.0,
        "8_BARS": 2.0,
        "TRIPLET_1/16": 11.5,
        "TRIPLET_1/8": 9.5,
        "TRIPLET_1/4": 7.5
    }

    DESTINATION_MAP: Dict[str, str] = {
        "FILTER_CUTOFF": "filter_1_cutoff",
        "FILTER_RESONANCE": "filter_1_resonance",
        "FILTER_DRIVE": "filter_1_drive",
        "WAVETABLE_FRAME": "osc_1_wave_frame",
        "OSC_1_FRAME": "osc_1_wave_frame",
        "OSC_2_FRAME": "osc_2_wave_frame",
        "OSC_3_FRAME": "osc_3_wave_frame",
        "OSC_1_PITCH": "osc_1_transpose",
        "OSC_2_PITCH": "osc_2_transpose",
        "OSC_3_PITCH": "osc_3_transpose",
        "OSC_PITCH": "osc_1_transpose",
        "OSC_1_LEVEL": "osc_1_level",
        "OSC_2_LEVEL": "osc_2_level",
        "OSC_3_LEVEL": "osc_3_level",
        "OSC_1_DETUNE": "osc_1_tune",
        "OSC_2_DETUNE": "osc_2_tune",
        "OSC_3_DETUNE": "osc_3_tune",
        "DISTORTION_DRIVE": "distortion_drive",
        "REVERB_MIX": "reverb_dry_wet",
        "DELAY_MIX": "delay_dry_wet",
        "DELAY_FEEDBACK": "delay_feedback",
        "CHORUS_MIX": "chorus_dry_wet",
        "PAN": "osc_1_pan",
        "VOLUME": "volume"
    }

    @classmethod
    def hz_to_midi_pitch(cls, hz: float) -> float:
        """Converts frequency in Hz to Vital MIDI pitch note (0.0 .. 128.0)."""
        safe_hz = max(10.0, min(22000.0, float(hz)))
        # formula: 69 + 12 * log2(hz / 440.0)
        midi_note = 69.0 + 12.0 * math.log2(safe_hz / 440.0)
        return max(18.0, min(128.0, midi_note))

    @classmethod
    def design_preset(
        cls,
        base_preset: Dict[str, Any],
        sanitized_spec: Dict[str, Any],
        preset_name: str = "Custom_Modular_Sound"
    ) -> Dict[str, Any]:
        """
        Materializes the granular specification onto a cloned preset archetype.
        """
        patch = copy.deepcopy(base_preset)
        patch["preset_name"] = preset_name
        patch["comments"] = f"Modular sound design synthesized by AbletonEngine AI ({preset_name})"

        settings = patch.get("settings", {})
        rng = random.Random(sanitized_spec.get("seed")) if sanitized_spec.get("seed") is not None else random

        variation = float(sanitized_spec.get("variation", 0.0))

        # 1. Apply Oscillators
        cls._apply_oscillators(settings, sanitized_spec.get("oscillators", {}), variation, rng)

        # 2. Apply Filter (Model, Mode, Cutoff, Resonance)
        cls._apply_filter(settings, sanitized_spec.get("filter", {}), variation, rng)

        # 3. Apply Modulations & Custom LFO Shapes
        cls._apply_modulations(settings, sanitized_spec.get("modulations", []), variation, rng)

        # 4. Apply Envelopes if specified
        cls._apply_envelopes(settings, sanitized_spec.get("envelopes", {}))

        # 5. Apply Sampler / Noise Layer if specified
        if "sampler" in sanitized_spec:
            cls._apply_sampler(settings, sanitized_spec["sampler"])

        # 6. Apply Effects if specified
        cls._apply_effects(settings, sanitized_spec.get("effects", {}))

        # 7. Final Gatekeeper Check
        settings = VitalParameterSchema.enforce_anti_silence_invariants(settings)
        patch["settings"] = settings

        return patch

    @classmethod
    def _apply_oscillators(
        cls,
        settings: Dict[str, Any],
        oscs_spec: Dict[str, Any],
        variation: float,
        rng: random.Random
    ) -> None:
        """Configures and synthesizes waveforms for osc_1, osc_2, osc_3."""
        # Ensure wavetables container exists
        if "wavetables" not in settings or not isinstance(settings["wavetables"], list):
            settings["wavetables"] = []

        while len(settings["wavetables"]) < 3:
            settings["wavetables"].append(WavetableSynthesizer.build_morphing_wavetable("BASIC_SHAPES"))

        for i, osc_key in enumerate(("osc_1", "osc_2", "osc_3"), start=1):
            if osc_key not in oscs_spec:
                # If not explicitly specified, keep current state or turn off if secondary
                if i > 1 and f"{osc_key}_on" in settings:
                    settings[f"{osc_key}_on"] = 0.0
                continue

            cfg = oscs_spec[osc_key]
            settings[f"{osc_key}_on"] = 1.0

            # Synthesize custom wavetable based on waveform request
            wave_type = cfg.get("waveform", "SAW").upper()
            wt_structure = cls._synthesize_waveform_for_osc(wave_type, cfg)
            settings["wavetables"][i - 1] = wt_structure

            # Octave & Semitones & Detune
            octave = int(cfg.get("octave", 0))
            semitones = int(cfg.get("semitones", 0))
            transpose = octave * 12 + semitones
            settings[f"{osc_key}_transpose"] = float(transpose)

            # Detune cents + Organic Variation Drift
            cents = float(cfg.get("detune_cents", 0.0))
            if variation > 0.0:
                # Analog pitch drift (+- 2 cents scaled by variation)
                cents += rng.gauss(0, 2.0 * variation)

            settings[f"{osc_key}_tune"] = cents / 100.0

            # Unison & Detune
            unison = int(cfg.get("unison", 1))
            settings[f"{osc_key}_unison_voices"] = float(unison)

            detune_val = float(cfg.get("unison_detune", 0.15))
            if unison > 1:
                settings[f"{osc_key}_unison_detune"] = max(0.01, min(5.0, detune_val * 3.0))
            else:
                settings[f"{osc_key}_unison_detune"] = 0.0

            # Level & Pan
            settings[f"{osc_key}_level"] = float(cfg.get("level", 0.707))
            settings[f"{osc_key}_pan"] = float(cfg.get("pan", 0.0))

            # Phase Mode
            phase_mode = str(cfg.get("phase_mode", "RANDOM")).upper()
            if "LOCKED_90" in phase_mode:
                settings[f"{osc_key}_random_phase"] = 0.0
                settings[f"{osc_key}_phase"] = 0.25
            elif "LOCKED" in phase_mode:
                settings[f"{osc_key}_random_phase"] = 0.0
                settings[f"{osc_key}_phase"] = 0.0
            else:
                settings[f"{osc_key}_random_phase"] = 1.0

    @classmethod
    def _synthesize_waveform_for_osc(cls, wave_type: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Generates appropriate single or multi-frame wavetable structure."""
        if "SINE" in wave_type:
            kf = [{"position": 0, "wave_data": WavetableSynthesizer.generate_sine()}]
            return WavetableSynthesizer.build_wavetable_structure("Pure Sine", kf)

        elif "TRIANGLE" in wave_type:
            kf = [{"position": 0, "wave_data": WavetableSynthesizer.generate_triangle()}]
            return WavetableSynthesizer.build_wavetable_structure("Pure Triangle", kf)

        elif "PULSE" in wave_type or "SQUARE" in wave_type:
            pw = float(cfg.get("pulse_width", 0.5))
            kf = [{"position": 0, "wave_data": WavetableSynthesizer.generate_pulse(pw)}]
            return WavetableSynthesizer.build_wavetable_structure(f"Pulse {int(pw*100)}%", kf)

        elif "FM" in wave_type:
            c = float(cfg.get("fm_carrier", 1.0))
            m = float(cfg.get("fm_mod", 2.0))
            idx = float(cfg.get("fm_index", 2.0))
            kf = [
                {"position": 0, "wave_data": WavetableSynthesizer.generate_sine()},
                {"position": 128, "wave_data": WavetableSynthesizer.generate_fm(c, m, idx * 0.5)},
                {"position": 256, "wave_data": WavetableSynthesizer.generate_fm(c, m, idx)}
            ]
            return WavetableSynthesizer.build_wavetable_structure(f"FM {c}:{m}", kf)

        elif "VOCAL" in wave_type:
            # Extract vowel letter
            vowel = wave_type.split("_")[-1] if "_" in wave_type else "A"
            if vowel not in ("A", "E", "I", "O", "U"):
                vowel = "A"
            kf = [{"position": 0, "wave_data": WavetableSynthesizer.generate_formant_vocal(vowel)}]
            return WavetableSynthesizer.build_wavetable_structure(f"Vocal Formant {vowel}", kf)

        elif "ANALOG" in wave_type or "CHEBYSHEV" in wave_type:
            kf = [
                {"position": 0, "wave_data": WavetableSynthesizer.generate_chebyshev_warmth(order=2, drive=0.6)},
                {"position": 256, "wave_data": WavetableSynthesizer.generate_chebyshev_warmth(order=3, drive=0.85)}
            ]
            return WavetableSynthesizer.build_wavetable_structure("Analog Chebyshev", kf)

        elif "METALLIC" in wave_type or "BELL" in wave_type:
            # Inharmonic bell partials
            weights = [1.0, 0.0, 0.7, 0.0, 0.5, 0.0, 0.0, 0.4, 0.2]
            kf = [
                {"position": 0, "wave_data": WavetableSynthesizer.generate_harmonic_additive(weights)},
                {"position": 256, "wave_data": WavetableSynthesizer.generate_fm(1.0, 3.5, 3.0)}
            ]
            return WavetableSynthesizer.build_wavetable_structure("Metallic Bell", kf)

        elif "NOISE" in wave_type:
            # High-entropy random cycle
            floats = [random.uniform(-1.0, 1.0) for _ in range(2048)]
            kf = [{"position": 0, "wave_data": WavetableSynthesizer.encode_wave_floats(floats)}]
            return WavetableSynthesizer.build_wavetable_structure("White Noise Table", kf)

        elif "DIRTY" in wave_type or "SUPERSAW" in wave_type:
            kf = [
                {"position": 0, "wave_data": WavetableSynthesizer.generate_saw()},
                {"position": 256, "wave_data": WavetableSynthesizer.generate_chebyshev_warmth(order=3, drive=0.9)}
            ]
            return WavetableSynthesizer.build_wavetable_structure("Dirty Saturated Saw", kf)

        else:
            # Standard Saw or Saw morph
            kf = [{"position": 0, "wave_data": WavetableSynthesizer.generate_saw()}]
            return WavetableSynthesizer.build_wavetable_structure("Analog Saw", kf)

    @classmethod
    def _apply_filter(
        cls,
        settings: Dict[str, Any],
        flt_spec: Dict[str, Any],
        variation: float,
        rng: random.Random
    ) -> None:
        """Applies specialized filter model (Diode, Comb, Dirty, etc.), mode, and frequency."""
        settings["filter_1_on"] = 1.0

        # Model
        model_name = flt_spec.get("model", "ANALOG_12").upper()
        settings["filter_1_model"] = cls.FILTER_MODEL_MAP.get(model_name, 0.0)
        settings["filter_1_style"] = 1.0 if "24" in model_name else 0.0

        # Mode (Low pass, Band pass, High pass)
        mode_name = flt_spec.get("mode", "LOW_PASS").upper()
        settings["filter_1_blend"] = cls.FILTER_MODE_MAP.get(mode_name, 0.0)

        # Cutoff frequency
        cutoff_hz = float(flt_spec.get("cutoff_hz", 2500.0))
        midi_cutoff = cls.hz_to_midi_pitch(cutoff_hz)

        # Organic variation: slight component tolerance drift (+- 1.5 MIDI notes)
        if variation > 0.0:
            midi_cutoff += rng.gauss(0, 1.5 * variation)
            midi_cutoff = max(18.0, min(128.0, midi_cutoff))

        settings["filter_1_cutoff"] = midi_cutoff

        # Resonance & Drive
        res = float(flt_spec.get("resonance", 0.25))
        settings["filter_1_resonance"] = min(0.70, res)

        drive = float(flt_spec.get("drive", 0.0))
        settings["filter_1_drive"] = drive * 12.0
        settings["filter_1_mix"] = 1.0

    @classmethod
    def _apply_modulations(
        cls,
        settings: Dict[str, Any],
        mod_specs: List[Dict[str, Any]],
        variation: float,
        rng: random.Random
    ) -> None:
        """Configures LFO shapes and connects matrix routes."""
        if not mod_specs:
            return

        mod_list = settings.get("modulations", [])
        while len(mod_list) < len(mod_specs) + 4:
            mod_list.append({"destination": "", "source": ""})

        lfos = settings.get("lfos", [])

        for i, mod in enumerate(mod_specs):
            src = mod.get("source", "LFO_1").lower()
            dest_key = mod.get("destination", "FILTER_CUTOFF")
            dest = cls.DESTINATION_MAP.get(dest_key, "filter_1_cutoff")
            amt = float(mod.get("amount", 0.5))

            slot_idx = i + 1  # 1-indexed for parameter names
            mod_list[i] = {"source": src, "destination": dest}
            settings[f"modulation_{slot_idx}_amount"] = amt

            # Configure LFO if source is LFO
            if src.startswith("lfo_"):
                lfo_num = src.split("_")[-1]
                rate_str = mod.get("rate", "1/8")
                tempo_val = cls.LFO_RATE_MAP.get(rate_str, 9.0)
                settings[f"{src}_tempo"] = tempo_val
                settings[f"{src}_sync"] = 1.0

                # LFO Shape configuration
                shape = mod.get("shape", "TRIANGLE").upper()
                lfo_idx = int(lfo_num) - 1
                if 0 <= lfo_idx < len(lfos):
                    cls._configure_lfo_shape(lfos[lfo_idx], shape, rng if variation > 0 else None)

    @classmethod
    def _configure_lfo_shape(cls, lfo_obj: Dict[str, Any], shape: str, rng: Optional[random.Random]) -> None:
        """Injects discrete coordinate points into Vital's LFO curve structure."""
        if not isinstance(lfo_obj, dict):
            return

        if "STEPPED_RANDOM" in shape:
            # Sample & Hold 8-step pattern
            points = []
            powers = []
            step_w = 1.0 / 8.0
            for s in range(8):
                y = (rng.random() if rng else ((s * 7) % 10) / 10.0)
                points.extend([s * step_w, y, (s + 1) * step_w, y])
                powers.extend([0.0, 0.0])
            lfo_obj["num_points"] = 16
            lfo_obj["points"] = points
            lfo_obj["powers"] = powers
            lfo_obj["name"] = "Sample & Hold"

        elif "SAW_DOWN" in shape or "RAMP_DOWN" in shape:
            lfo_obj["num_points"] = 2
            lfo_obj["points"] = [0.0, 1.0, 1.0, 0.0]
            lfo_obj["powers"] = [0.0, 0.0]
            lfo_obj["name"] = "Ramp Down"

        elif "SAW_UP" in shape or "RAMP_UP" in shape:
            lfo_obj["num_points"] = 2
            lfo_obj["points"] = [0.0, 0.0, 1.0, 1.0]
            lfo_obj["powers"] = [0.0, 0.0]
            lfo_obj["name"] = "Ramp Up"

        elif "SQUARE" in shape:
            lfo_obj["num_points"] = 4
            lfo_obj["points"] = [0.0, 1.0, 0.5, 1.0, 0.501, 0.0, 1.0, 0.0]
            lfo_obj["powers"] = [0.0, 0.0, 0.0, 0.0]
            lfo_obj["name"] = "Square"

        else:
            # Standard Triangle
            lfo_obj["num_points"] = 3
            lfo_obj["points"] = [0.0, 0.0, 0.5, 1.0, 1.0, 0.0]
            lfo_obj["powers"] = [0.0, 0.0, 0.0]
            lfo_obj["name"] = "Triangle"

        # Rigorous Vital invariant: len(powers) MUST strictly equal num_points
        np = int(lfo_obj.get("num_points", 0))
        pws = lfo_obj.setdefault("powers", [])
        if len(pws) < np:
            pws.extend([0.0] * (np - len(pws)))
        elif len(pws) > np:
            lfo_obj["powers"] = pws[:np]

    @classmethod
    def _apply_envelopes(cls, settings: Dict[str, Any], env_spec: Dict[str, Any]) -> None:
        """Applies custom ADSR values allowing fast clicks/percussion and expansive pads."""
        if "attack" in env_spec:
            settings["env_1_attack"] = max(0.001, float(env_spec["attack"]))
        if "decay" in env_spec:
            settings["env_1_decay"] = max(0.02, float(env_spec["decay"]))
        if "sustain" in env_spec:
            settings["env_1_sustain"] = max(0.0, min(1.0, float(env_spec["sustain"])))
        if "release" in env_spec:
            settings["env_1_release"] = max(0.01, float(env_spec["release"]))

    @classmethod
    def _apply_sampler(cls, settings: Dict[str, Any], samp_spec: Dict[str, Any]) -> None:
        """Configures Vital's internal Sampler buffer with algorithmic audio."""
        if not samp_spec or not samp_spec.get("on", True):
            return
        settings["sample_on"] = 1.0
        sample_type = str(samp_spec.get("sample_type", "WHITE_NOISE")).upper()
        settings["sample"] = WavetableSynthesizer.generate_sampler_buffer(sample_type, duration_sec=1.0)
        settings["sample_level"] = float(samp_spec.get("level", 0.3))
        settings["sample_loop"] = 1.0 if samp_spec.get("loop", True) else 0.0

    @classmethod
    def _apply_effects(cls, settings: Dict[str, Any], fx_spec: Dict[str, Any]) -> None:
        """Applies distortion, reverb, delay, chorus, compression, and EQ."""
        if not isinstance(fx_spec, dict):
            return

        if "distortion" in fx_spec:
            dist = fx_spec["distortion"]
            settings["distortion_on"] = 1.0 if dist.get("on", True) else 0.0
            settings["distortion_filter_cutoff"] = 80.0
            if "drive_db" in dist:
                settings["distortion_drive"] = float(dist["drive_db"])

        if "reverb" in fx_spec:
            rev = fx_spec["reverb"]
            settings["reverb_on"] = 1.0 if rev.get("on", True) else 0.0
            settings["reverb_pre_low_cutoff"] = 25.0
            if "mix" in rev:
                settings["reverb_dry_wet"] = float(rev["mix"])

        if "delay" in fx_spec:
            dly = fx_spec["delay"]
            settings["delay_on"] = 1.0 if dly.get("on", True) else 0.0
            if "mix" in dly:
                settings["delay_dry_wet"] = float(dly["mix"])
            if "feedback" in dly:
                settings["delay_feedback"] = float(dly["feedback"])
            if "tempo" in dly:
                settings["delay_tempo"] = float(dly["tempo"])

        if "chorus" in fx_spec:
            cho = fx_spec["chorus"]
            settings["chorus_on"] = 1.0 if cho.get("on", True) else 0.0
            if "mix" in cho:
                settings["chorus_dry_wet"] = float(cho["mix"])

        if "compressor" in fx_spec or "ott" in fx_spec:
            comp = fx_spec.get("compressor", fx_spec.get("ott", {}))
            settings["compressor_on"] = 1.0 if comp.get("on", True) else 0.0
            if "mix" in comp:
                settings["compressor_mix"] = float(comp["mix"])

        if "eq" in fx_spec:
            eq = fx_spec["eq"]
            settings["eq_on"] = 1.0 if eq.get("on", True) else 0.0
            if "low_gain" in eq:
                settings["eq_low_gain"] = float(eq["low_gain"])
            if "high_gain" in eq:
                settings["eq_high_gain"] = float(eq["high_gain"])

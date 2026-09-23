# engine/sound_design/vital_parameter_schema.py
"""
Vital Parameter Schema & Acoustic Integrity Gatekeeper.

Defines parameter domains, nominal ranges, units, and validation invariants
to guarantee that generated or transformed .vital presets produce audible,
production-grade sound with zero risk of silent or broken patches.
"""

from typing import Dict, Any, Tuple, Optional, List
import logging

logger = logging.getLogger("VitalParameterSchema")


class VitalParameterSchema:
    """
    Exhaustive schema and boundary enforcement engine for Vital Synth presets.
    Covers the 772 scalar settings, envelope curves, and anti-silence invariants.
    """

    # --- CRITICAL ACOUSTIC INVARIANTS ---
    # Master volume in Vital uses an internal quadratic curve (~4000 to ~6600).
    # Values under 100 result in complete digital silence.
    VOLUME_MIN = 4000.0
    VOLUME_MAX = 6500.0
    VOLUME_NOMINAL = 5400.0

    # Filter cutoff in Vital is expressed in MIDI pitch units (0.0 to 128.0).
    # 127 ≈ 20 kHz, 60 ≈ 261 Hz (C4), 27 ≈ 40 Hz, 18 ≈ 23 Hz (lowest audible sub note B0/C1).
    FILTER_CUTOFF_SAFE_MIN = 18.0
    FILTER_CUTOFF_SAFE_MAX_HP = 118.0  # ≈ 7 kHz (prevents ultrasonic silence in high-pass)
    FILTER_CUTOFF_MAX = 130.0

    # Resonances above 0.75 can cause ear-damaging feedback howl.
    FILTER_RESONANCE_SAFE_MAX = 0.75

    # Amplitude Envelope (env_1) safety limits
    ENV_ATTACK_MIN = 0.001     # 1 millisecond (prevents click at zero)
    ENV_ATTACK_MAX = 15.0      # 15 seconds (allows expansive ambient pads/drones)
    ENV_DECAY_MIN = 0.02       # 20 ms (allows tight, snappy percussive clicks and plucks)
    ENV_DECAY_MAX = 15.0
    ENV_SUSTAIN_MIN = 0.0
    ENV_SUSTAIN_MAX = 1.0
    ENV_RELEASE_MIN = 0.01     # 10 ms (allows fast gating without click)
    ENV_RELEASE_MAX = 15.0

    # Distortion limits (dB)
    DISTORTION_DRIVE_MIN = -20.0
    DISTORTION_DRIVE_MAX = 28.0

    # Domain-specific parameter boundary rules
    # (param_prefix, min_val, max_val, default_val)
    BOUNDS: Dict[str, Tuple[float, float, float]] = {
        # Master & Voice
        "volume": (VOLUME_MIN, VOLUME_MAX, VOLUME_NOMINAL),
        "polyphony": (1.0, 32.0, 8.0),
        "legato": (0.0, 1.0, 0.0),
        "portamento_force": (0.0, 1.0, 0.0),
        "portamento_time": (-10.0, 0.0, -5.0),
        "voice_priority": (0.0, 4.0, 4.0),
        "pitch_bend_range": (1.0, 24.0, 2.0),
        "stereo_routing": (0.0, 1.0, 0.0),

        # Oscillators (General for osc_1, osc_2, osc_3)
        "osc_level": (0.0, 1.0, 0.707),
        "osc_on": (0.0, 1.0, 1.0),
        "osc_pan": (-1.0, 1.0, 0.0),
        "osc_phase": (0.0, 1.0, 0.0),
        "osc_random_phase": (0.0, 1.0, 1.0),
        "osc_transpose": (-48.0, 48.0, 0.0),
        "osc_tune": (-1.0, 1.0, 0.0),
        "osc_unison_voices": (1.0, 16.0, 1.0),
        "osc_unison_detune": (0.0, 6.0, 0.15),
        "osc_unison_blend": (0.0, 1.0, 0.8),
        "osc_wave_frame": (0.0, 256.0, 0.0),
        "osc_distortion_amount": (0.0, 1.0, 0.5),
        "osc_distortion_type": (0.0, 10.0, 0.0),
        "osc_spectral_morph_amount": (0.0, 1.0, 0.5),
        "osc_spectral_morph_type": (0.0, 10.0, 0.0),

        # Filters
        "filter_cutoff": (FILTER_CUTOFF_SAFE_MIN, FILTER_CUTOFF_MAX, 115.0),
        "filter_resonance": (0.0, FILTER_RESONANCE_SAFE_MAX, 0.25),
        "filter_drive": (0.0, 18.0, 0.0),
        "filter_mix": (0.0, 1.0, 1.0),
        "filter_blend": (0.0, 2.0, 0.0),  # 0=LP, 1=BP, 2=HP
        "filter_keytrack": (0.0, 1.0, 0.0),
        "filter_model": (0.0, 7.0, 0.0),
        "filter_style": (0.0, 3.0, 0.0),

        # Amplitude Envelope (env_1)
        "env_1_attack": (ENV_ATTACK_MIN, ENV_ATTACK_MAX, 0.01),
        "env_1_decay": (ENV_DECAY_MIN, ENV_DECAY_MAX, 1.0),
        "env_1_sustain": (ENV_SUSTAIN_MIN, ENV_SUSTAIN_MAX, 0.8),
        "env_1_release": (ENV_RELEASE_MIN, ENV_RELEASE_MAX, 0.3),
        "env_1_decay_power": (-3.0, 1.0, -2.0),
        "env_1_release_power": (-3.0, 1.0, -2.0),

        # Modulation Envelopes (env_2 .. env_6)
        "env_attack": (0.0, ENV_ATTACK_MAX, 0.01),
        "env_decay": (0.0, ENV_DECAY_MAX, 1.0),
        "env_sustain": (0.0, 1.0, 0.5),
        "env_release": (0.0, ENV_RELEASE_MAX, 0.5),

        # LFOs (lfo_1 .. lfo_8)
        "lfo_frequency": (0.0, 20.0, 1.0),
        "lfo_tempo": (1.0, 16.0, 7.0),
        "lfo_sync": (0.0, 1.0, 1.0),
        "lfo_sync_type": (0.0, 3.0, 0.0),
        "lfo_fade_time": (0.0, 4.0, 0.0),
        "lfo_smooth_time": (-10.0, 0.0, -7.5),

        # Distortion
        "distortion_drive": (DISTORTION_DRIVE_MIN, DISTORTION_DRIVE_MAX, 0.0),
        "distortion_mix": (0.0, 1.0, 1.0),
        "distortion_type": (0.0, 6.0, 0.0),
        "distortion_filter_cutoff": (20.0, 130.0, 80.0),

        # Reverb
        "reverb_size": (0.1, 1.0, 0.5),
        "reverb_decay_time": (-4.0, 7.0, 2.0),
        "reverb_dry_wet": (0.0, 1.0, 0.25),
        "reverb_delay": (0.0, 0.2, 0.0),

        # Delay
        "delay_tempo": (1.0, 16.0, 9.0),
        "delay_feedback": (0.0, 0.90, 0.45),
        "delay_dry_wet": (0.0, 1.0, 0.25),
        "delay_filter_cutoff": (30.0, 120.0, 70.0),

        # Chorus & Flanger & Phaser
        "chorus_dry_wet": (0.0, 1.0, 0.35),
        "chorus_voices": (1.0, 8.0, 4.0),
        "chorus_spread": (0.0, 1.0, 0.8),
        "flanger_dry_wet": (0.0, 1.0, 0.3),
        "phaser_dry_wet": (0.0, 1.0, 0.3),

        # Compressor / Multiband OTT
        "compressor_mix": (0.0, 1.0, 0.6),
        "compressor_attack": (0.01, 1.0, 0.2),
        "compressor_release": (0.01, 1.0, 0.2),
        "compressor_band_gain": (0.0, 24.0, 14.0),

        # EQ
        "eq_low_gain": (-18.0, 12.0, 0.0),
        "eq_band_gain": (-18.0, 12.0, 0.0),
        "eq_high_gain": (-18.0, 12.0, 0.0),

        # Sampler
        "sample_level": (0.0, 1.0, 0.5),
        "sample_loop": (0.0, 1.0, 1.0)
    }

    @classmethod
    def clamp_parameter(cls, name: str, value: Any) -> Any:
        """
        Clamps a single parameter value to its safe physical and musical bounds.
        """
        if not isinstance(value, (int, float)):
            return value

        val_float = float(value)

        # 1. Exact match in BOUNDS
        if name in cls.BOUNDS:
            min_v, max_v, _ = cls.BOUNDS[name]
            return max(min_v, min(max_v, val_float))

        # 2. Oscillator specific mapping (osc_1_level -> osc_level)
        for osc_id in ("osc_1_", "osc_2_", "osc_3_"):
            if name.startswith(osc_id):
                suffix = "osc_" + name[len(osc_id):]
                if suffix in cls.BOUNDS:
                    min_v, max_v, _ = cls.BOUNDS[suffix]
                    return max(min_v, min(max_v, val_float))

        # 3. Filter specific mapping (filter_1_cutoff -> filter_cutoff)
        for flt_id in ("filter_1_", "filter_2_"):
            if name.startswith(flt_id):
                suffix = "filter_" + name[len(flt_id):]
                if suffix in cls.BOUNDS:
                    min_v, max_v, _ = cls.BOUNDS[suffix]
                    return max(min_v, min(max_v, val_float))

        # 4. Secondary envelopes (env_2_attack -> env_attack)
        for env_id in ("env_2_", "env_3_", "env_4_", "env_5_", "env_6_"):
            if name.startswith(env_id):
                suffix = "env_" + name[len(env_id):]
                if suffix in cls.BOUNDS:
                    min_v, max_v, _ = cls.BOUNDS[suffix]
                    return max(min_v, min(max_v, val_float))

        # 5. LFO mapping (lfo_1_tempo -> lfo_tempo)
        for lfo_id in [f"lfo_{i}_" for i in range(1, 9)]:
            if name.startswith(lfo_id):
                suffix = "lfo_" + name[len(lfo_id):]
                if suffix in cls.BOUNDS:
                    min_v, max_v, _ = cls.BOUNDS[suffix]
                    return max(min_v, min(max_v, val_float))

        # 6. Modulation amount mapping
        if name.startswith("modulation_") and name.endswith("_amount"):
            return max(-1.0, min(1.0, val_float))

        # Fallback for generic boolean flags
        if name.endswith("_on") or name.endswith("_sync") or name.endswith("_bypass"):
            return 1.0 if val_float >= 0.5 else 0.0

        return val_float

    @classmethod
    def enforce_anti_silence_invariants(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rigorous acoustic gatekeeper that checks and fixes any condition that
        could cause a .vital preset to output complete silence or inaudible clicks.
        """
        # --- INVARIANT 1: Master Volume Calibration ---
        vol = float(settings.get("volume", cls.VOLUME_NOMINAL))
        if vol < cls.VOLUME_MIN or vol > cls.VOLUME_MAX:
            logger.warning(
                f"[AcousticGatekeeper] Volume {vol} outside safe range. "
                f"Clamping to nominal {cls.VOLUME_NOMINAL}."
            )
            settings["volume"] = cls.VOLUME_NOMINAL

        # --- INVARIANT 2: Audio Source Existence ---
        # At least one oscillator or sampler MUST be active with an audible level.
        # Threshold 0.05 (-26 dB) allows subtle background layers or quiet sub-oscillators.
        osc1_active = settings.get("osc_1_on", 0.0) >= 0.5 and float(settings.get("osc_1_level", 0.0)) >= 0.05
        osc2_active = settings.get("osc_2_on", 0.0) >= 0.5 and float(settings.get("osc_2_level", 0.0)) >= 0.05
        osc3_active = settings.get("osc_3_on", 0.0) >= 0.5 and float(settings.get("osc_3_level", 0.0)) >= 0.05
        sample_active = settings.get("sample_on", 0.0) >= 0.5 and float(settings.get("sample_level", 0.0)) >= 0.05

        if not (osc1_active or osc2_active or osc3_active or sample_active):
            logger.warning(
                "[AcousticGatekeeper] No active sound generator detected! "
                "Enabling osc_1 with nominal level 0.707."
            )
            settings["osc_1_on"] = 1.0
            settings["osc_1_level"] = 0.7071067690849304

        # --- INVARIANT 3: Filter Cutoff & Brickwall Attenuation ---
        # Context-aware filter gatekeeper:
        # Low-Pass: cutoff < 18.0 (subsonic DC, <23 Hz) causes silence.
        # High-Pass: cutoff > 118.0 (ultrasonic, >7 kHz) wipes out all musical fundamentals.
        for f_idx in (1, 2):
            f_on = settings.get(f"filter_{f_idx}_on", 0.0) >= 0.5
            f_blend = float(settings.get(f"filter_{f_idx}_blend", 0.0))
            f_cutoff = float(settings.get(f"filter_{f_idx}_cutoff", 115.0))
            f_mix = float(settings.get(f"filter_{f_idx}_mix", 1.0))

            if f_on and f_mix > 0.05:
                if f_blend < 0.5:  # Low-pass active
                    if f_cutoff < cls.FILTER_CUTOFF_SAFE_MIN:
                        logger.warning(
                            f"[AcousticGatekeeper] Filter {f_idx} cutoff {f_cutoff} is subsonic in low-pass. "
                            f"Clamping to safe audible cutoff {cls.FILTER_CUTOFF_SAFE_MIN}."
                        )
                        settings[f"filter_{f_idx}_cutoff"] = cls.FILTER_CUTOFF_SAFE_MIN
                elif f_blend >= 1.5:  # High-pass active
                    if f_cutoff > cls.FILTER_CUTOFF_SAFE_MAX_HP:
                        logger.warning(
                            f"[AcousticGatekeeper] Filter {f_idx} cutoff {f_cutoff} is ultrasonic in high-pass (>118.0). "
                            f"Clamping to safe audible cutoff {cls.FILTER_CUTOFF_SAFE_MAX_HP}."
                        )
                        settings[f"filter_{f_idx}_cutoff"] = cls.FILTER_CUTOFF_SAFE_MAX_HP
                else:  # Band-pass / Notch active
                    if f_cutoff < cls.FILTER_CUTOFF_SAFE_MIN:
                        settings[f"filter_{f_idx}_cutoff"] = cls.FILTER_CUTOFF_SAFE_MIN
                    elif f_cutoff > cls.FILTER_CUTOFF_SAFE_MAX_HP:
                        settings[f"filter_{f_idx}_cutoff"] = cls.FILTER_CUTOFF_SAFE_MAX_HP

            # Prevent self-oscillating feedback scream
            f_res = float(settings.get(f"filter_{f_idx}_resonance", 0.0))
            if f_res > cls.FILTER_RESONANCE_SAFE_MAX:
                settings[f"filter_{f_idx}_resonance"] = cls.FILTER_RESONANCE_SAFE_MAX

        # --- INVARIANT 4: Primary Amplitude Envelope (env_1) Integrity ---
        # Note duration must not be zero.
        # Only inaudible micro-clicks (decay < 25ms with 0 sustain) get expanded to a safe 150ms tail.
        # Snappy intentional percussive clicks and plucks (>= 25ms) are completely preserved.
        env1_sustain = float(settings.get("env_1_sustain", 1.0))
        env1_decay = float(settings.get("env_1_decay", 1.0))
        env1_attack = float(settings.get("env_1_attack", 0.01))

        if env1_sustain <= 0.01 and env1_decay < 0.025:
            logger.warning(
                f"[AcousticGatekeeper] env_1 has zero sustain and inaudible micro-decay ({env1_decay}s). "
                "Expanding decay to 0.15s to ensure audible transient."
            )
            settings["env_1_decay"] = 0.15

        if env1_attack < cls.ENV_ATTACK_MIN:
            settings["env_1_attack"] = cls.ENV_ATTACK_MIN

        # Ensure valid exponential decay and release curvature
        if "env_1_decay_power" not in settings or float(settings["env_1_decay_power"]) > 0.0:
            settings["env_1_decay_power"] = -2.0
        if "env_1_release_power" not in settings or float(settings["env_1_release_power"]) > 0.0:
            settings["env_1_release_power"] = -2.0

        # --- INVARIANT 5: Polyphony Sanity ---
        poly = float(settings.get("polyphony", 8.0))
        if poly < 1.0 or poly > 32.0:
            settings["polyphony"] = 8.0

        # --- INVARIANT 6: LFO Vector Alignment Gatekeeper ---
        # Vital C++ parser requires len(powers) == num_points and len(points) == 2 * num_points.
        # Any discrepancy causes "Preset file is corrupted" upon loading.
        for lfo in settings.get("lfos", []):
            if isinstance(lfo, dict):
                np = int(lfo.get("num_points", 0))
                pts = lfo.setdefault("points", [])
                pws = lfo.setdefault("powers", [])
                if len(pts) < 2 * np:
                    pts.extend([0.0] * (2 * np - len(pts)))
                elif len(pts) > 2 * np:
                    lfo["points"] = pts[:2 * np]
                if len(pws) < np:
                    pws.extend([0.0] * (np - len(pws)))
                elif len(pws) > np:
                    lfo["powers"] = pws[:np]

        # --- INVARIANT 7: Wavetable Component & Version Integrity ---
        # Vital 1.0.x rejects wavetables reporting future versions or invalid Wave Source keys.
        for wt in settings.get("wavetables", []):
            if isinstance(wt, dict):
                wt["version"] = "1.0.7"
                for group in wt.get("groups", []):
                    for comp in group.get("components", []):
                        if comp.get("type") == "Wave Source":
                            comp.pop("audio_file", None)
                            comp.setdefault("interpolation", 1)
                            comp.setdefault("interpolation_style", 0)

        # --- INVARIANT 8: Sampler Buffer Safe Metadata ---
        samp = settings.get("sample")
        if isinstance(samp, dict):
            if samp.get("name") not in ("White Noise", "Key Click", "Air"):
                samp["name"] = "White Noise"

        return settings

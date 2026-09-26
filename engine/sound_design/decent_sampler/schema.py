# engine/sound_design/decent_sampler/schema.py
"""
Level 1: Decent Sampler Format Specification & Canonical Schema.

Defines the exact XML specification for Decent Sampler presets (.dspreset)
conforming to version 1.33.0+. Covers recognized elements, valid attribute names,
data types, canonical lowercase tokens, and physical boundary constraints.
"""

from typing import Dict, Set, Tuple, Any, List, Optional, Union
from dataclasses import dataclass
import math
import re


class DecentSamplerSchema:
    """
    Formal schema specification for the Decent Sampler (.dspreset) XML format.
    Does not encode opinionated engine policies; focuses strictly on what the
    Decent Sampler plugin recognizes, accepts, and requires.
    """

    # --- FORMAT METADATA ---
    MIN_SUPPORTED_VERSION = "1.0.0"
    CURRENT_SPEC_VERSION = "1.33.0"
    ROOT_TAG = "DecentSampler"

    # --- PHYSICAL / MIDI BOUNDS ---
    NOTE_MIN = 0
    NOTE_MAX = 127
    VELOCITY_MIN = 0
    VELOCITY_MAX = 127
    PAN_MIN = -100.0
    PAN_MAX = 100.0
    TUNING_SEMITONES_MIN = -36.0
    TUNING_SEMITONES_MAX = 36.0
    FREQUENCY_MIN_HZ = 20.0
    FREQUENCY_MAX_HZ = 22000.0

    # --- CANONICAL EFFECT TYPES (STRICTLY LOWERCASE) ---
    # Decent Sampler C++ parser requires exact canonical lowercase identifiers.
    CANONICAL_EFFECT_TYPES: Set[str] = {
        "lowpass",
        "lowpass_1pl",
        "highpass",
        "bandpass",
        "notch",
        "peak",
        "gain",
        "reverb",
        "delay",
        "chorus",
        "phaser",
        "convolution",
        "pitch_shift",
        "wave_folder",
        "wave_shaper",
        "stereo_simulator",
        "bit_crusher",
        "compressor",
        "stutter",
    }

    # Effects that Decent Sampler supports strictly at the global (instrument) level
    GLOBAL_ONLY_EFFECTS: Set[str] = {"reverb", "delay"}

    # Effects permitted at the group level
    GROUP_COMPATIBLE_EFFECTS: Set[str] = {
        "lowpass",
        "lowpass_1pl",
        "highpass",
        "bandpass",
        "gain",
        "chorus",
        "wave_folder",
        "wave_shaper",
    }

    # --- RECOGNIZED ELEMENTS & VALID ATTRIBUTES ---
    ELEMENT_ATTRIBUTES: Dict[str, Set[str]] = {
        "DecentSampler": {
            "minVersion",
            "pluginVersion",
            "volume",
            "globalVolume",
            "globalPan",
            "globalTuning",
            "glideTime",
            "glideMode",
        },
        "ui": {
            "width",
            "height",
            "bgImage",
            "layoutMode",
        },
        "tab": {
            "name",
        },
        "labeled-knob": {
            "x",
            "y",
            "width",
            "height",
            "label",
            "type",
            "valueType",
            "minValue",
            "maxValue",
            "value",
            "defaultValue",
            "textColor",
            "textSize",
            "trackForegroundColor",
            "trackBackgroundColor",
            "style",
            "tags",
        },
        "control": {
            "x",
            "y",
            "width",
            "height",
            "type",
            "valueType",
            "minValue",
            "maxValue",
            "value",
            "defaultValue",
            "tags",
        },
        "button": {
            "x",
            "y",
            "width",
            "height",
            "style",
            "value",
            "tags",
        },
        "state": {
            "name",
        },
        "menu": {
            "x",
            "y",
            "width",
            "height",
            "value",
            "tags",
        },
        "option": {
            "name",
            "value",
        },
        "xyPad": {
            "x",
            "y",
            "width",
            "height",
        },
        "keyboard": {
            "visible",
            "height",
        },
        "color": {
            "loNote",
            "hiNote",
            "color",
        },
        "groups": {
            "volume",
            "globalVolume",
            "globalPan",
            "globalTuning",
            "glideTime",
            "glideMode",
            "attack",
            "decay",
            "sustain",
            "release",
            "attackCurve",
            "decayCurve",
            "releaseCurve",
            "seqMode",
            "seqLength",
            "playbackMode",
            "ampVelTrack",
        },
        "group": {
            "tags",
            "enabled",
            "volume",
            "groupVolume",
            "pan",
            "groupPan",
            "groupTuning",
            "ampVelTrack",
            "pitchKeyTrack",
            "glideTime",
            "glideMode",
            "ampEnvEnabled",
            "attack",
            "decay",
            "sustain",
            "release",
            "attackCurve",
            "decayCurve",
            "releaseCurve",
            "seqMode",
            "seqPosition",
            "seqLength",
            "trigger",
            "silencedByTags",
            "silencingMode",
            "silencingDecay",
            "playbackMode",
            "loNote",
            "hiNote",
            "loVel",
            "hiVel",
        },
        "sample": {
            "path",
            "rootNote",
            "loNote",
            "hiNote",
            "loVel",
            "hiVel",
            "start",
            "end",
            "tuning",
            "volume",
            "pan",
            "pitchKeyTrack",
            "trigger",
            "releaseTriggerDecay",
            "loopEnabled",
            "loopStart",
            "loopEnd",
            "loopCrossfade",
            "loopCrossfadeMode",
            "tags",
            "seqMode",
            "seqPosition",
            "seqLength",
            "silencedByTags",
            "silencingMode",
            "silencingDecay",
            "playbackMode",
            "delay",
            "delayUnit",
            "retriggerEnabled",
            "retriggerInterval",
            "retriggerIntervalUnit",
            "attack",
            "decay",
            "sustain",
            "release",
            "attackCurve",
            "decayCurve",
            "releaseCurve",
            "ampEnvEnabled",
        },
        "effects": set(),
        "effect": {
            "type",
            "tags",
            "enabled",
            # Common filter params
            "frequency",
            "resonance",
            "q",
            "gain",
            # Reverb params
            "roomSize",
            "damping",
            "wetLevel",
            # Delay params
            "delayTime",
            "delayTimeFormat",
            "feedback",
            "stereoOffset",
            # Chorus params
            "mix",
            "modDepth",
            "modRate",
            # Phaser params
            "centerFrequency",
            # Convolution
            "irFile",
            # Pitch shift
            "pitchShift",
            # Distortion / wave folding
            "drive",
            "threshold",
            "driveBoost",
            "outputLevel",
            "highQuality",
            # Stereo simulator
            "algorithm",
            "width",
            # Bit crusher
            "bitDepth",
            "sampleRateReduction",
            # Compressor
            "ratio",
            "attack",
            "release",
            "inputGain",
            "outputGain",
            "autoBypass",
            # Stutter
            "amount",
            # Gain
            "level",
            "levelUnit",
        },
        "modulators": set(),
        "lfo": {
            "shape",
            "frequency",
            "frequencyFormat",
            "modAmount",
            "delayTime",
            "scope",
            "modBehavior",
            "tags",
        },
        "envelope": {
            "attack",
            "decay",
            "sustain",
            "release",
            "attackCurve",
            "decayCurve",
            "releaseCurve",
            "modAmount",
            "scope",
            "modBehavior",
            "tags",
        },
        "binding": {
            "type",
            "level",
            "position",
            "groupIndex",
            "effectIndex",
            "controlIndex",
            "modulatorIndex",
            "tags",
            "groupTags",
            "sampleTags",
            "effectTags",
            "modulatorTags",
            "controlTags",
            "identifier",
            "parameter",
            "translation",
            "translationOutputMin",
            "translationOutputMax",
            "translationReversed",
            "translationTable",
            "translationValue",
            "triggerOnLoad",
            "factor",
            "enabled",
        },
    }

    # --- BINDING SPECIFICATION ---
    VALID_BINDING_TYPES: Set[str] = {
        "amp",
        "general",
        "effect",
        "control",
        "note",
        "note_binding",
        "velocity_binding",
        "button_state_binding",
        "keyboard_color",
        "modulator",
        "note_sequence",
        "arpeggiator",
    }

    VALID_BINDING_LEVELS: Set[str] = {
        "ui",
        "instrument",
        "group",
        "sample",
        "oscillator",
        "tag",
        "midi",
    }

    VALID_TRANSLATION_MODES: Set[str] = {
        "linear",
        "table",
        "fixed_value",
    }

    VALID_BINDING_PARAMETERS: Set[str] = {
        # Amplitude / Master
        "AMP_VOLUME",
        "GLOBAL_TUNING",
        "PAN",
        "AMP_VEL_TRACK",
        "GROUP_TUNING",
        "OUTPUT_1_VOLUME",
        "OUTPUT_2_VOLUME",
        # Envelope
        "ENV_ATTACK",
        "ENV_ATTACK_CURVE",
        "ENV_DECAY",
        "ENV_DECAY_CURVE",
        "ENV_SUSTAIN",
        "ENV_RELEASE",
        "ENV_RELEASE_CURVE",
        "AMP_ENV_ENABLED",
        # Glide
        "GLIDE_TIME",
        "GLIDE_MODE",
        # Group / Sample
        "ENABLED",
        "LO_NOTE",
        "HI_NOTE",
        "LO_VEL",
        "HI_VEL",
        "ROOT_NOTE",
        "SAMPLE_START",
        "SAMPLE_END",
        "LOOP_START",
        "LOOP_END",
        "SILENCING_DECAY",
        "SILENCING_MODE",
        "PITCH_KEY_TRACK",
        # Effects
        "FX_FILTER_FREQUENCY",
        "FX_FILTER_RESONANCE",
        "FX_REVERB_WET_LEVEL",
        "FX_REVERB_ROOM_SIZE",
        "FX_REVERB_DAMPING",
        "FX_DELAY_TIME",
        "FX_DELAY_FEEDBACK",
        "FX_DELAY_WET_LEVEL",
        "FX_CHORUS_MIX",
        "FX_CHORUS_MOD_DEPTH",
        "FX_CHORUS_MOD_RATE",
        "FX_PHASER_MIX",
        "FX_PHASER_FEEDBACK",
        "FX_PHASER_CENTER_FREQUENCY",
        "FX_CONVOLUTION_MIX",
        "FX_PITCH_SHIFT",
        "FX_PITCH_SHIFT_MIX",
        "FX_DRIVE",
        "FX_THRESHOLD",
        "FX_DRIVE_BOOST",
        "FX_OUTPUT_LEVEL",
        "FX_WIDTH",
        "FX_BIT_DEPTH",
        "FX_SAMPLE_RATE_REDUCTION",
        "FX_MIX",
        "FX_RATIO",
        "FX_ATTACK",
        "FX_RELEASE",
        "FX_INPUT_GAIN",
        "FX_OUTPUT_GAIN",
        "FX_STUTTER_AMOUNT",
        # UI controls
        "VALUE",
        "TEXT",
        "TEXT_COLOR",
        "BG_COLOR",
    }

    # --- MODULATOR OPTIONS ---
    VALID_LFO_SHAPES: Set[str] = {"sine", "square", "saw"}
    VALID_MOD_SCOPES: Set[str] = {"global", "voice"}
    VALID_MOD_BEHAVIORS: Set[str] = {"set", "modulate", "multiply", "add"}
    VALID_FREQUENCY_FORMATS: Set[str] = {"hz", "musical_time"}

    # --- ROUND ROBIN & TRIGGER OPTIONS ---
    VALID_SEQ_MODES: Set[str] = {"round_robin", "random", "true_random", "always"}
    VALID_TRIGGERS: Set[str] = {"attack", "release", "first", "legato", "continuous"}
    VALID_GLIDE_MODES: Set[str] = {"always", "legato", "off"}
    VALID_PLAYBACK_MODES: Set[str] = {"auto", "memory", "disk_streaming"}
    VALID_LOOP_CROSSFADE_MODES: Set[str] = {"linear", "equal_power"}
    VALID_SILENCING_MODES: Set[str] = {"fast", "normal"}
    VALID_AUDIO_EXTENSIONS: Set[str] = {".wav", ".aif", ".aiff", ".flac"}

    # --- INDUSTRY STANDARD CALIBRATION TABLES ---
    # Proven 7-point logarithmic frequency curve for lowpass filter cutoffs (33Hz -> 22kHz)
    DEFAULT_LOG_FILTER_TABLE: str = (
        "0,33;0.3,150;0.4,450;0.5,1100;0.7,4100;0.9,11000;1.0001,22000"
    )

    @classmethod
    def db_to_gain(cls, db_val: float) -> float:
        """Converts decibels to linear amplitude gain factor (0dB -> 1.0)."""
        return round(10.0 ** (db_val / 20.0), 6)

    @classmethod
    def gain_to_db(cls, gain_val: float) -> float:
        """Converts linear amplitude gain factor to decibels (1.0 -> 0dB)."""
        safe_gain = max(gain_val, 1e-6)
        return round(20.0 * math.log10(safe_gain), 2)

    @classmethod
    def parse_volume_string(cls, val: Union[str, float, int, None]) -> float:
        """
        Parses volume values specified either as a linear float factor (1.0)
        or with decibels suffix ('2dB', '0dB', '-6dB').
        Tolerates newlines or minor corruption in third-party files.
        """
        if val is None:
            return 1.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        if not val_str:
            return 1.0

        # Check for decibels suffix
        if "db" in val_str.lower():
            # Extract first numeric sequence (handles '3\n  aadB' gracefully)
            m = re.search(r"[-+]?\d*\.?\d+", val_str)
            if m:
                db_num = float(m.group(0))
                return cls.db_to_gain(db_num)
            return 1.0

        try:
            return float(val_str)
        except ValueError:
            return 1.0


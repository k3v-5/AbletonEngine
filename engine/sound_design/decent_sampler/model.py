# engine/sound_design/decent_sampler/model.py
"""
Intermediate Representation (IR): Pure Python Domain Model for Decent Sampler.

Decouples sound design decisions, sample mapping planning, and musical logic
from XML generation and parsing.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import copy


@dataclass
class BindingModel:
    """Represents a <binding> between UI controls / modulators and engine parameters."""
    type: str = "amp"                  # amp, effect, general, control, etc.
    level: str = "instrument"          # instrument, group, sample, ui, tag
    parameter: str = "AMP_VOLUME"      # Engine parameter token
    position: Optional[int] = None     # 0-based target index
    group_index: Optional[int] = None
    effect_index: Optional[int] = None
    control_index: Optional[int] = None
    tags: Optional[str] = None         # Target tag(s)
    translation: str = "linear"        # linear, table, fixed_value
    translation_output_min: Optional[float] = None
    translation_output_max: Optional[float] = None
    translation_reversed: bool = False
    translation_table: Optional[str] = None
    translation_value: Optional[str] = None
    trigger_on_load: bool = True
    factor: float = 1.0
    enabled: bool = True


@dataclass
class ControlModel:
    """Represents a UI widget (<labeled-knob>, <button>, <menu>)."""
    control_type: str = "labeled-knob"  # labeled-knob, button, menu, etc.
    label: str = "Volume"
    x: int = 0
    y: int = 0
    width: int = 90
    height: int = 90
    min_value: float = 0.0
    max_value: float = 1.0
    value: float = 1.0
    default_value: float = 1.0
    text_color: str = "FFFFFFFF"       # AARRGGBB hex
    text_size: Optional[int] = None
    track_foreground_color: Optional[str] = None  # AARRGGBB hex
    track_background_color: Optional[str] = None  # AARRGGBB hex
    type: str = "float"                           # percent, float, integer
    value_type: str = "linear"         # linear, decibels, musical_time, etc.
    bindings: List[BindingModel] = field(default_factory=list)


@dataclass
class UIModel:
    """Represents the visual interface (<ui>) container."""
    width: int = 812
    height: int = 375
    bg_image: Optional[str] = None
    layout_mode: str = "relative"
    controls: List[ControlModel] = field(default_factory=list)


@dataclass
class EffectModel:
    """Represents an audio DSP processor (<effect>)."""
    type: str = "lowpass"              # Canonical lowercase type
    tags: Optional[str] = None
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModulatorModel:
    """Represents an LFO or auxiliary envelope (<lfo>, <envelope>)."""
    mod_type: str = "lfo"              # lfo, envelope
    shape: str = "sine"
    frequency: float = 1.0
    frequency_format: str = "hz"       # hz, musical_time
    mod_amount: float = 1.0
    delay_time: float = 0.0
    scope: str = "global"              # global, voice
    mod_behavior: str = "set"          # set, modulate, multiply, add
    tags: Optional[str] = None
    # Envelope specific
    attack: float = 0.01
    decay: float = 1.0
    sustain: float = 1.0
    release: float = 0.3
    attack_curve: int = -100
    decay_curve: int = 100
    release_curve: int = 100
    bindings: List[BindingModel] = field(default_factory=list)


@dataclass
class SampleZoneModel:
    """Represents an individual playable sample zone (<sample>)."""
    path: str = ""                     # Relative audio file path
    root_note: int = 60                # MIDI note (0-127)
    lo_note: int = 0
    hi_note: int = 127
    lo_vel: int = 0
    hi_vel: int = 127
    start: int = 0
    end: Optional[int] = None
    tuning: float = 0.0                # Fine-tuning in semitones
    volume: float = 1.0                # Linear gain or dB string
    pan: float = 0.0                   # -100 to 100
    pitch_key_track: float = 1.0       # 1.0 = normal 1 semitone/key
    trigger: str = "attack"            # attack, release, first, legato
    release_trigger_decay: float = 0.0
    loop_enabled: bool = False
    loop_start: int = 0
    loop_end: Optional[int] = None
    loop_crossfade: int = 0
    loop_crossfade_mode: str = "equal_power"
    tags: Optional[str] = None
    seq_mode: str = "always"           # round_robin, random, true_random, always
    seq_position: int = 1
    seq_length: int = 1
    silenced_by_tags: Optional[str] = None
    silencing_mode: str = "fast"
    silencing_decay: float = 0.0
    playback_mode: str = "auto"
    delay: float = 0.0
    delay_unit: str = "seconds"


@dataclass
class GroupModel:
    """Represents a sample collection (<group>) sharing settings and voice logic."""
    name: str = "Default Group"
    tags: Optional[str] = None
    enabled: bool = True
    volume: float = 1.0
    pan: float = 0.0
    group_tuning: float = 0.0
    amp_vel_track: float = 1.0
    pitch_key_track: float = 1.0
    glide_time: float = 0.0
    glide_mode: str = "legato"
    amp_env_enabled: bool = True
    attack: float = 0.001
    decay: float = 1.0
    sustain: float = 1.0
    release: float = 0.3
    attack_curve: int = -100
    decay_curve: int = 100
    release_curve: int = 100
    seq_mode: str = "always"
    seq_position: int = 1
    seq_length: int = 1
    silenced_by_tags: Optional[str] = None
    silencing_mode: str = "fast"
    silencing_decay: float = 0.0
    playback_mode: str = "auto"
    samples: List[SampleZoneModel] = field(default_factory=list)
    effects: List[EffectModel] = field(default_factory=list)

    def add_sample(self, sample: SampleZoneModel) -> "GroupModel":
        self.samples.append(sample)
        return self


@dataclass
class InstrumentModel:
    """
    Root Domain Model representing a complete Decent Sampler instrument preset.
    Pure Python data structure, independent of XML serialization.
    """
    name: str = "Untitled Instrument"
    min_version: str = "1.0.0"
    plugin_version: str = "1"
    volume: float = 1.0
    global_pan: float = 0.0
    global_tuning: float = 0.0
    glide_time: float = 0.0
    glide_mode: str = "legato"
    ui: UIModel = field(default_factory=UIModel)
    groups: List[GroupModel] = field(default_factory=list)
    effects: List[EffectModel] = field(default_factory=list)
    modulators: List[ModulatorModel] = field(default_factory=list)

    def add_group(self, group: GroupModel) -> "InstrumentModel":
        self.groups.append(group)
        return self

    def add_effect(self, effect: EffectModel) -> "InstrumentModel":
        self.effects.append(effect)
        return self

    def add_modulator(self, modulator: ModulatorModel) -> "InstrumentModel":
        self.modulators.append(modulator)
        return self

    def add_control(self, control: ControlModel) -> "InstrumentModel":
        self.ui.controls.append(control)
        return self

    def total_samples(self) -> int:
        return sum(len(g.samples) for g in self.groups)

    def clone(self) -> "InstrumentModel":
        return copy.deepcopy(self)

"""
AbletonEngine Production Knowledge Base.
Full 20-module encyclopedic knowledge ported and optimized for Ableton Live 12 Suite and VST3 ecosystem.
"""

from engine.knowledge.constants import Genre, SEMITONE_TO_NAME, midi_to_note
from engine.knowledge.composition.scales import (
    SCALE_INTERVALS, SCALE_DESCRIPTIONS, GENRE_SCALE_RECOMMENDATIONS,
    MOOD_SCALE_MAP, COMMON_KEYS, get_scale_notes, get_scale_notes_range, format_scale_info,
)
from engine.knowledge.composition.chords import (
    PROGRESSION_DEFINITIONS, get_progression_chords, progression_to_midi_notes,
    format_progression_info, list_progressions,
)
from engine.knowledge.composition.drum_patterns import (
    PATTERNS, VELOCITY_GUIDE, SWING_VALUES, pattern_to_midi_notes,
    list_patterns, format_velocity_guide, get_patterns_for_bpm, check_bpm_compatibility,
)
from engine.knowledge.composition.basslines import (
    BASS_TYPES, BASS_PROCESSING_CHAIN, BASS_GOLDEN_RULES, BASS_TRICKS,
    generate_bassline_notes, format_bass_type_info, format_processing_chain,
    format_growl_guide, format_golden_rules, list_distortion_plugins,
)
from engine.knowledge.arrangement.song_structures import (
    STRUCTURES, TRANSITIONS, QUICK_START_10_STEPS, get_structure, get_quick_start,
)
from engine.knowledge.producers.producers import (
    get_producer_profile, list_producers,
)
from engine.knowledge.sampling.sampling import (
    get_chopping_guide, get_sampling_workflow, get_drum_machine_emulation,
    get_sample_processing_chain, SAMPLING_SOURCES,
)
from engine.knowledge.plugins.serum2 import (
    get_patch_recipe, get_genre_sounds, get_fx_chain as get_serum_fx,
    get_sound_design_tips, get_wavetable_guide, list_patches as list_serum_patches,
)
from engine.knowledge.plugins.fabfilter import (
    get_eq_preset, get_compressor_preset, get_fabfilter_chain,
    get_saturn_guide, format_plugin_info as fabfilter_info,
)
from engine.knowledge.plugins.ozone12 import (
    get_mastering_chain as get_ozone_chain, get_module_guide as get_ozone_module,
    get_quick_master, get_lufs_targets as get_ozone_lufs, list_ozone_modules,
)
from engine.knowledge.plugins.rx11 import (
    get_cleanup_chain, get_module_guide as get_rx_module,
    get_repair_workflow, list_rx_modules,
)
from engine.knowledge.plugins.autotune import (
    get_autotune_settings, get_vocal_tuning_workflow, get_key_detection_guide,
)
from engine.knowledge.plugins.cymatics import (
    get_cymatics_chain, get_plugin_guide as get_cymatics_guide, list_cymatics_presets,
)
from engine.knowledge.plugins.plugin_chains import (
    get_chain, get_mix_levels, get_mastering_chain, get_eq_guide,
    get_send_config, get_gain_staging_guide, get_mixer_template,
    get_lufs_targets, get_workflow, get_soundtoys_guide, PLUGIN_CHAINS,
)
from engine.knowledge.plugins.vocal_chains import (
    get_vocal_chain, get_vocal_tricks, get_vocal_checklist,
)
from engine.knowledge.plugins.mixing_advanced import (
    get_mixing_workflow, get_bus_setup, get_mixing_checklist,
)

__all__ = [
    "Genre", "SEMITONE_TO_NAME", "midi_to_note",
    "get_scale_notes", "get_progression_chords", "pattern_to_midi_notes",
    "generate_bassline_notes", "get_structure", "get_producer_profile",
    "get_chopping_guide", "get_patch_recipe", "get_eq_preset",
    "get_compressor_preset", "get_ozone_chain", "get_cleanup_chain",
    "get_autotune_settings", "get_cymatics_chain", "get_chain",
    "get_vocal_chain", "get_mixing_workflow", "PLUGIN_CHAINS",
]

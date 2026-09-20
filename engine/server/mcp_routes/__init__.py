"""
MCP Route modules for AbletonEngine server.
"""

from .copilot_routes import (
    handle_copilot_get_status,
    handle_copilot_review_decisions,
    handle_copilot_execute_decision,
    handle_copilot_preflight_check,
    handle_copilot_auto_produce,
    handle_copilot_guided_session,
    handle_copilot_session_doctor,
)
from .mix_master_routes import (
    handle_setup_full_mastering_chain,
    handle_apply_adaptive_deesser,
    handle_mix_apply_frequency_slotting,
    handle_mix_audit_phase_and_mono_compatibility,
    handle_mix_apply_vocal_lead_fader_riding,
    handle_mix_apply_multitrack_sidechain_ducking,
    handle_mix_audit_psychoacoustic_masking,
)
from .sound_design_routes import (
    handle_get_producer_info,
    handle_get_serum_patch,
    handle_get_fabfilter_preset,
    handle_get_vocal_chain_guide,
    handle_audio_semantic_sample_match,
    handle_audio_deconstruct_reference,
    handle_audio_transcribe_to_midi,
)

__all__ = [
    "handle_copilot_get_status",
    "handle_copilot_review_decisions",
    "handle_copilot_execute_decision",
    "handle_copilot_preflight_check",
    "handle_copilot_auto_produce",
    "handle_copilot_guided_session",
    "handle_copilot_session_doctor",
    "handle_setup_full_mastering_chain",
    "handle_apply_adaptive_deesser",
    "handle_mix_apply_frequency_slotting",
    "handle_mix_audit_phase_and_mono_compatibility",
    "handle_mix_apply_vocal_lead_fader_riding",
    "handle_mix_apply_multitrack_sidechain_ducking",
    "handle_mix_audit_psychoacoustic_masking",
    "handle_get_producer_info",
    "handle_get_serum_patch",
    "handle_get_fabfilter_preset",
    "handle_get_vocal_chain_guide",
    "handle_audio_semantic_sample_match",
    "handle_audio_deconstruct_reference",
    "handle_audio_transcribe_to_midi",
]

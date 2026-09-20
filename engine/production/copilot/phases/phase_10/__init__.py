"""
Phase 10 package: Active Listening, Transport Navigation, Clip Micro-Surgery,
Vocal Production / Chops, Instrument Swap Re-validation, and Forensic Stem Export.
"""

from .handler import Phase10ListenersHandler
from .instrument_swap import (
    initiate_instrument_swap_flow,
    prompt_instrument_swap_preset,
    handle_instrument_swap_step,
    execute_instrument_swap_reaudit,
)
from .stem_coordinator import audit_and_prepare_stems
from .vocal_pipeline import handle_vocal_pipeline
from .drop_mutator import handle_drop_mutator
from .surgery_and_navigation import (
    handle_clip_surgery,
    handle_master_gain_boost,
    handle_low_mid_resonance_clean,
    handle_top_and_tail_guard,
    handle_transport_navigation,
    handle_session_tweaks,
)
from .music_director import MusicDirector

__all__ = [
    "MusicDirector",
    "Phase10ListenersHandler",
    "initiate_instrument_swap_flow",
    "prompt_instrument_swap_preset",
    "handle_instrument_swap_step",
    "execute_instrument_swap_reaudit",
    "audit_and_prepare_stems",
    "handle_vocal_pipeline",
    "handle_drop_mutator",
    "handle_clip_surgery",
    "handle_master_gain_boost",
    "handle_low_mid_resonance_clean",
    "handle_top_and_tail_guard",
    "handle_transport_navigation",
    "handle_session_tweaks",
]

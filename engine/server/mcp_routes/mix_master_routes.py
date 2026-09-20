"""
Mix and Master MCP Routes:
Handlers for mastering chains, adaptive de-essers, frequency slotting,
phase alignment, and psychoacoustic masking audits.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("AbletonMCPServer.MixMasterRoutes")


def handle_setup_full_mastering_chain(
    get_connection: Callable[[], Any],
    track_index: int = 12,
    target_profile: str = "STREAMING"
) -> dict:
    """Deploys the complete 5-device native mastering chain in Ableton Live."""
    try:
        from engine.mastering.live_master_chain import LiveMasterChainEngine
        conn = get_connection()
        return LiveMasterChainEngine.setup_live_mastering_chain(conn, track_index=track_index, target_profile=target_profile)
    except Exception as e:
        logger.error(f"Error in setup_full_mastering_chain: {e}")
        return {"status": "error", "message": str(e)}


def handle_apply_adaptive_deesser(
    get_connection: Callable[[], Any],
    track_index: int,
    target_sibilance_freq: float = 6800.0,
    threshold: float = 0.65
) -> dict:
    """Deploys a surgical adaptive De-Esser on a track in Ableton Live."""
    try:
        from engine.vocal.adaptive_deesser import AdaptiveDeEsserEngine
        conn = get_connection()
        return AdaptiveDeEsserEngine.deploy_adaptive_deesser(
            conn=conn,
            track_index=track_index,
            target_sibilance_freq=target_sibilance_freq,
            threshold=threshold
        )
    except Exception as e:
        logger.error(f"Error in apply_adaptive_deesser: {e}")
        return {"status": "error", "message": str(e)}


def handle_mix_apply_frequency_slotting() -> dict:
    """Applies multitrack complementary frequency slotting and HPF filtering."""
    try:
        from engine.mix.frequency_slotting import FrequencySlottingEngine
        return FrequencySlottingEngine.generate_full_session_slotting_plan()
    except Exception as e:
        logger.error(f"Error in mix_apply_frequency_slotting: {e}")
        return {"status": "error", "message": str(e)}


def handle_mix_audit_phase_and_mono_compatibility() -> dict:
    """Audits Pearson phase correlation coefficients and mono collapse."""
    try:
        from engine.mix.phase_alignment import PhaseAlignmentEngine
        return PhaseAlignmentEngine.generate_phase_audit_report()
    except Exception as e:
        logger.error(f"Error in mix_audit_phase_and_mono_compatibility: {e}")
        return {"status": "error", "message": str(e)}


def handle_mix_apply_vocal_lead_fader_riding(role: str = "vocal", crossfade_beats: float = 2.0) -> dict:
    """Computes section-aware dynamic fader riding automation curves."""
    try:
        from engine.mix.fader_rider import VocalLeadFaderRider
        return VocalLeadFaderRider.get_fader_riding_manifest()
    except Exception as e:
        logger.error(f"Error in mix_apply_vocal_lead_fader_riding: {e}")
        return {"status": "error", "message": str(e)}


def handle_mix_apply_multitrack_sidechain_ducking() -> dict:
    """Coordinates physical sidechain compression routing and envelope ducking."""
    try:
        from engine.mix.multitrack_sidechain import MultiTrackSidechainCoordinator
        return MultiTrackSidechainCoordinator.get_multitrack_sidechain_matrix()
    except Exception as e:
        logger.error(f"Error in mix_apply_multitrack_sidechain_ducking: {e}")
        return {"status": "error", "message": str(e)}


def handle_mix_audit_psychoacoustic_masking(
    masker_audio_path: str,
    target_audio_path: str,
    masker_role: str = "DRUMS",
    target_role: str = "BASS"
) -> dict:
    """Audits psychoacoustic masking between interacting stems."""
    try:
        from engine.mix.psychoacoustic_masking import PsychoacousticMaskingAuditor
        return PsychoacousticMaskingAuditor.audit_masking(
            masker_audio_path=masker_audio_path,
            target_audio_path=target_audio_path,
            masker_role=masker_role,
            target_role=target_role
        )
    except Exception as e:
        logger.error(f"Error in mix_audit_psychoacoustic_masking: {e}")
        return {"status": "error", "message": str(e)}

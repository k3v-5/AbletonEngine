"""
Sound Design and Preset MCP Routes:
Handlers for synth patches, FabFilter presets, producer profiles,
vocal chain guides, semantic sample matching, and reference audio transcription.
"""

import math
import glob
import logging
from typing import Optional, List, Callable, Any

logger = logging.getLogger("AbletonMCPServer.SoundDesignRoutes")


def handle_get_producer_info(producer_name: str) -> dict:
    """Get signature production blueprint, drum selection, swing, and hardware emulation."""
    try:
        from engine.knowledge.producers.producers import get_producer_profile
        profile = get_producer_profile(producer_name)
        return {"status": "success", "profile": profile}
    except Exception as e:
        logger.error(f"Error in get_producer_info: {e}")
        return {"status": "error", "message": str(e)}


def handle_get_serum_patch(patch_name: str) -> dict:
    """Get step-by-step synthesis patch recipe for Serum 2."""
    try:
        from engine.knowledge.plugins.serum2 import get_patch_recipe
        recipe = get_patch_recipe(patch_name)
        return {"status": "success", "recipe": recipe}
    except Exception as e:
        logger.error(f"Error in get_serum_patch: {e}")
        return {"status": "error", "message": str(e)}


def handle_get_fabfilter_preset(plugin: str, element: str) -> dict:
    """Get surgical presets for FabFilter Pro-Q 4, Pro-C 3, or Saturn 2 by instrument element."""
    try:
        from engine.knowledge.plugins.fabfilter import get_eq_preset, get_compressor_preset
        p_lower = plugin.lower()
        if "eq" in p_lower or "q" in p_lower:
            res = get_eq_preset(element)
        else:
            res = get_compressor_preset(element)
        return {"status": "success", "preset": res}
    except Exception as e:
        logger.error(f"Error in get_fabfilter_preset: {e}")
        return {"status": "error", "message": str(e)}


def handle_get_vocal_chain_guide(style: str = "trap_lead") -> dict:
    """Get complete 10-slot vocal chain order with Auto-Tune Pro, RX 11, EQ, and dynamics settings."""
    try:
        from engine.knowledge.plugins.vocal_chains import get_vocal_chain
        chain = get_vocal_chain(style)
        return {"status": "success", "vocal_chain": chain}
    except Exception as e:
        logger.error(f"Error in get_vocal_chain_guide: {e}")
        return {"status": "error", "message": str(e)}


def handle_audio_semantic_sample_match(prompt: str, sample_paths: Optional[List[str]] = None, top_k: int = 5) -> dict:
    """Matches natural language intent to audio samples using physical 6D acoustic signatures."""
    try:
        from engine.audio.semantic_sample_matcher import AcousticFeatureExtractor, SemanticSampleMatcher
        paths = sample_paths or []
        if not paths:
            paths = glob.glob(r"F:\Dev\AbletonEngine\**\*.wav", recursive=True)[:30]
        
        signatures = {}
        for p in paths:
            sig = AcousticFeatureExtractor.extract_from_file(p)
            if sig:
                signatures[p] = sig
                
        results = SemanticSampleMatcher.rank_candidates(prompt, signatures, top_k=top_k)
        return {"status": "success", "prompt": prompt, "matches": results}
    except Exception as e:
        logger.error(f"Error in audio_semantic_sample_match: {e}")
        return {"status": "error", "message": str(e)}


def handle_audio_deconstruct_reference(audio_path: str, prefer_neural: bool = True, bpm: float = 120.0) -> dict:
    """Separates reference track into stems and extracts arrangement energy profile."""
    try:
        from engine.audio.deconstruction.neural_separator import HybridStemSeparator
        sep = HybridStemSeparator()
        stems = sep.separate(audio_path, prefer_neural=prefer_neural)
        profile = sep.profile_arrangement_energy(stems, tempo_bpm=bpm)
        return {
            "status": "success",
            "stems": {k: v.to_dict() for k, v in stems.items()},
            "arrangement_profile": profile
        }
    except Exception as e:
        logger.error(f"Error in audio_deconstruct_reference: {e}")
        return {"status": "error", "message": str(e)}


def handle_audio_transcribe_to_midi(
    get_connection: Callable[[], Any],
    audio_path: str,
    track_index: Optional[int] = None,
    tempo_bpm: float = 120.0
) -> dict:
    """Transcribes monophonic audio recording into expressive MIDI notes."""
    try:
        from engine.audio.deconstruction.expressive_transcriber import ExpressiveAudioTranscriber
        transcriber = ExpressiveAudioTranscriber()
        events = transcriber.transcribe_file(audio_path, tempo_bpm=tempo_bpm)
        
        if track_index is not None:
            conn = get_connection()
            if conn and hasattr(conn, "send_command") and events:
                clip_notes = [
                    {"pitch": e.pitch, "start_time": e.start_time_beats, "duration": e.duration_beats, "velocity": e.velocity, "mute": False}
                    for e in events
                ]
                total_beats = max(4.0, math.ceil(max(e.start_time_beats + e.duration_beats for e in events) / 4.0) * 4.0)
                conn.send_command("create_clip", {"track_index": track_index, "clip_index": 0, "length": total_beats})
                conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": 0, "notes": clip_notes})
                
        return {
            "status": "success",
            "notes_count": len(events),
            "events": [e.to_dict() for e in events[:20]]
        }
    except Exception as e:
        logger.error(f"Error in audio_transcribe_to_midi: {e}")
        return {"status": "error", "message": str(e)}

"""
Physical Sidechain Routing Weaver:
Connects Kick source track to Bass target track Compressor in Live with calibrated
threshold, ratio, attack, and release parameters.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("RecipeEngine.SidechainWeaver")


def configure_physical_sidechain(conn: Any, recipe: Any, manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Routinely locates Kick and Bass tracks from recipe blueprints and configures
    physical Sidechain on the Bass compressor.
    """
    if not getattr(recipe, "enable_sidechain", True):
        return None

    kick_tracks = [t for t in recipe.tracks if "drum" in t.role.lower() or "kick" in t.name.lower() or "drum" in t.name.lower()]
    bass_tracks = [t for t in recipe.tracks if "bass" in t.role.lower() or "sub" in t.role.lower() or "808" in t.role.lower() or "bass" in t.name.lower()]
    if not (kick_tracks and bass_tracks):
        return None

    b_track = bass_tracks[0]
    k_track = kick_tracks[0]
    logger.info(f"\n--- Fase Sidechain Físico: Enrutando Pista {k_track.track_index} ({k_track.name}) -> Pista {b_track.track_index} ({b_track.name}) ---")
    try:
        from engine.mix.sidechain_manager import SidechainManager
        sc_res = SidechainManager.configure_sidechain(
            conn=conn,
            bass_track_index=b_track.track_index,
            kick_track_index=k_track.track_index,
            threshold=0.55,
            ratio=0.75,
            attack=0.0,
            release=0.16
        )
        manifest["sidechain"] = sc_res
        logger.info(f"  -> Sidechain físico configurado con éxito: {sc_res.get('routing_summary', '')}")
        return sc_res
    except Exception as e:
        logger.warning(f"Aviso al configurar sidechain físico Kick->Bass: {e}")
        return None

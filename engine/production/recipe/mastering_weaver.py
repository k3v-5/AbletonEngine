"""
Mastering Chain Deployment Weaver:
Installs native 5-stage mastering chain on the designated master / premaster track
calibrated for the recipe's target LUFS profile.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("RecipeEngine.MasteringWeaver")


def configure_mastering_chain(conn: Any, recipe: Any, manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Deploys native 5-stage mastering chain on master bus track.
    """
    if not getattr(recipe, "enable_mastering_chain", True):
        return None

    m_track_candidates = [t for t in recipe.tracks if "master" in t.role.lower() or "premaster" in t.name.lower() or "master" in t.name.lower()]
    target_m_idx = getattr(recipe, "master_bus_track_index", None)
    if target_m_idx is None and m_track_candidates:
        target_m_idx = m_track_candidates[0].track_index

    if target_m_idx is None:
        return None

    logger.info(f"\n--- Fase Masterización: Desplegando Cadena Nativa de 5 Etapas en Pista {target_m_idx} ---")
    try:
        from engine.mastering.live_master_chain import LiveMasterChainEngine
        prof = "STREAMING"
        if getattr(recipe, "target_lufs", -7.0) >= -8.0:
            prof = "CLUB"
        elif getattr(recipe, "target_lufs", -7.0) <= -13.0:
            prof = "STREAMING"
        m_res = LiveMasterChainEngine.setup_live_mastering_chain(
            conn=conn,
            track_index=target_m_idx,
            target_profile=prof
        )
        manifest["mastering_chain"] = m_res
        logger.info(f"  -> Cadena de masterización instalada: {m_res.get('devices_installed', [])}")
        return m_res
    except Exception as e:
        logger.warning(f"Aviso al desplegar cadena nativa de masterización: {e}")
        return None

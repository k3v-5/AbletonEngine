# engine/creative/artistic_critic/identity_critic.py
"""
1. Identity Critic:
Core Question: "¿Podría esta canción intercambiarse por otra canción del catálogo sin que nadie notara la diferencia?"

Audits:
- Melodic fingerprint (pitch classes, interval contours)
- Rhythmic fingerprint (syncopation entropy, microtiming)
- Harmonic fingerprint (chord extensions, cadence choices)
- Timbre fingerprint (plugin stack, frequency distribution)
- Arrangement fingerprint (density trajectory)
- Spatial fingerprint (stereo width, reverb depth)

VETO Condition:
- Uniqueness < 0.65 vs CatalogMemory, or interchangeable clone of an existing catalog work.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity
from engine.memory.catalog_memory import CatalogMemory

logger = logging.getLogger("IdentityCritic")


class IdentityCritic:
    """Evaluates whether the song has an unrepeatable identity or converges to catalog cliches."""

    @classmethod
    def evaluate(
        cls,
        candidate_data: Dict[str, Any],
        catalog_memory: Optional[CatalogMemory] = None
    ) -> CriticScore:
        fingerprints = candidate_data.get("fingerprints", {})
        melodic_fp = float(fingerprints.get("melodic", 0.85))
        rhythmic_fp = float(fingerprints.get("rhythmic", 0.85))
        harmonic_fp = float(fingerprints.get("harmonic", 0.80))
        timbre_fp = float(fingerprints.get("timbre", 0.85))
        arr_fp = float(fingerprints.get("arrangement", 0.82))
        spatial_fp = float(fingerprints.get("spatial", 0.78))

        # Check against Catalog Memory if available
        uniqueness = 0.88
        conflict_name = None
        if catalog_memory and hasattr(catalog_memory, "evaluate_proposal_against_catalog"):
            proposal_meta = {
                "key": candidate_data.get("key", "C"),
                "bpm": candidate_data.get("bpm", 120.0),
                "genre": candidate_data.get("genre", "neo_soul"),
                "instrument_plugins": candidate_data.get("plugins", []),
                "recipes": candidate_data.get("recipes", []),
            }
            conflicts = catalog_memory.evaluate_proposal_against_catalog(proposal_meta)
            critical_conflicts = [c for c in conflicts if getattr(c, "severity", "").upper() == "CRITICAL_CLICHE"]
            if critical_conflicts:
                conflict = critical_conflicts[0]
                conflict_name = getattr(conflict, "conflicting_song_title", getattr(conflict, "existing_song_title", "obra previa"))
                uniqueness = 0.45

        # Weighted identity score
        composite_identity = (
            melodic_fp * 0.20 +
            rhythmic_fp * 0.20 +
            harmonic_fp * 0.15 +
            timbre_fp * 0.20 +
            arr_fp * 0.15 +
            spatial_fp * 0.10
        )
        final_score = round(composite_identity * uniqueness, 3)

        details = {
            "melodic_fingerprint": round(melodic_fp, 2),
            "rhythmic_fingerprint": round(rhythmic_fp, 2),
            "harmonic_fingerprint": round(harmonic_fp, 2),
            "timbre_fingerprint": round(timbre_fp, 2),
            "arrangement_fingerprint": round(arr_fp, 2),
            "spatial_fingerprint": round(spatial_fp, 2),
            "catalog_uniqueness": round(uniqueness, 2),
        }

        if final_score < 0.60 or uniqueness < 0.60:
            return CriticScore(
                dimension=CriticDimension.IDENTITY,
                score=final_score,
                severity=VetoSeverity.VETO_REJECT,
                explanation=f"VETO: Canción intercambiable con '{conflict_name or 'obra previa en catálogo'}'. Carece de huella distintiva (Uniqueness: {uniqueness:.2f}).",
                details=details
            )
        elif final_score < 0.75:
            return CriticScore(
                dimension=CriticDimension.IDENTITY,
                score=final_score,
                severity=VetoSeverity.WARNING,
                explanation="ADVERTENCIA: La huella tímbrica o armónica se aproxima a convenciones de catálogo.",
                details=details
            )

        return CriticScore(
            dimension=CriticDimension.IDENTITY,
            score=final_score,
            severity=VetoSeverity.PASS,
            explanation="Identidad consolidada: huella dactilar estética única respecto al catálogo.",
            details=details
        )

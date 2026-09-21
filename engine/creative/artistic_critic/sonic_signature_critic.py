# engine/creative/artistic_critic/sonic_signature_critic.py
"""
6. Sonic Signature Critic:
Core Question: "¿Hay algún sonido que solamente pueda pertenecer a ESTA canción?"

Musical Requirement:
Every song must possess at least ONE unique, unrepeatable sonic signature
born from intentional sound design, resampling, granular processing, or custom chains.

Examples:
- "Reverse Rhodes ghost + distorted transient + filtered vinyl tail"
- "Pitched acoustic percussion + granular vocal fragment + mono synth body"

VETO Condition:
- No unique sonic signature declared, or all instruments are purely generic stock presets.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging

from .critic_verdict import CriticScore, CriticDimension, VetoSeverity
from engine.creative.artistic_intent import ArtisticIntent

logger = logging.getLogger("SonicSignatureCritic")


class SonicSignatureCritic:
    """Demands a distinctive, bespoke sonic fingerprint unique to this musical work."""

    @classmethod
    def evaluate(
        cls,
        candidate_data: Dict[str, Any],
        intent: Optional[ArtisticIntent] = None
    ) -> CriticScore:
        signature = candidate_data.get("sonic_signature") or candidate_data.get("signature_sound")
        has_custom_sound_design = bool(candidate_data.get("has_custom_sound_design", False))
        is_all_stock = bool(candidate_data.get("all_stock_presets", False))

        details = {
            "declared_signature": signature,
            "has_custom_sound_design": has_custom_sound_design,
            "is_all_stock": is_all_stock,
        }

        # 1. Total absence of sonic signature or all stock presets: VETO
        if is_all_stock or (not signature and not has_custom_sound_design):
            return CriticScore(
                dimension=CriticDimension.SONIC_SIGNATURE,
                score=0.20,
                severity=VetoSeverity.VETO_REJECT,
                explanation="VETO: Ausencia de firma sonora. La canción solo utiliza presets genéricos de fábrica sin ningún diseño sonoro que le pertenezca exclusivamente.",
                details=details
            )

        # 2. Signature present but vague/short
        sig_str = str(signature or "").strip()
        if len(sig_str) < 10 and not has_custom_sound_design:
            return CriticScore(
                dimension=CriticDimension.SONIC_SIGNATURE,
                score=0.65,
                severity=VetoSeverity.WARNING,
                explanation="ADVERTENCIA: La firma sonora es débil o poco específica. Requiere mayor desarrollo tímbrico.",
                details=details
            )

        # 3. Authentic unique signature confirmed
        score = 0.95 if has_custom_sound_design and len(sig_str) >= 15 else 0.88
        return CriticScore(
            dimension=CriticDimension.SONIC_SIGNATURE,
            score=score,
            severity=VetoSeverity.PASS,
            explanation=f"Firma sonora única confirmada: '{sig_str or 'Bespoke Resampled Layer'}'.",
            details=details
        )

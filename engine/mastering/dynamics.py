"""
Dynamic Preservation Engine.
Monitors crest factor, dynamic range, and transient health to prevent squashing.
"""
from typing import Dict, Any


class DynamicPreservationEngine:
    """Calculates dynamic preservation score and loudness efficiency."""

    @classmethod
    def evaluate_dynamics(cls, pre_crest: float, post_crest: float,
                          pre_lufs: float, post_lufs: float) -> Dict[str, Any]:
        crest_loss = max(0.0, pre_crest - post_crest)
        lufs_gain = max(0.0, post_lufs - pre_lufs)

        # Dynamic preservation score (100 = perfect preservation)
        # Losing >3 dB crest factor is severe damage
        preservation_score = max(0.0, 100.0 - (crest_loss * 20.0))

        # Loudness efficiency: LUFS gained per dB of crest factor lost
        efficiency = round(lufs_gain / (crest_loss + 1e-6), 2)

        dynamic_damage = bool(crest_loss > 3.0 or post_crest < 6.5)

        return {
            "dynamic_preservation_score": round(preservation_score, 1),
            "crest_loss_db": round(crest_loss, 2),
            "lufs_gain_db": round(lufs_gain, 2),
            "loudness_efficiency": efficiency,
            "dynamic_damage_detected": dynamic_damage
        }

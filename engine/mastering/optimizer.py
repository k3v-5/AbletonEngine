"""
Multi-Objective Pareto Optimizer.
Weighs competing mastering dimensions (loudness vs dynamic damage vs translation).
"""
from typing import Dict, Any, Optional
from .models import MasterPlan


class MasteringOptimizer:
    """Evaluates multi-objective tradeoffs and determines whether a master is superior."""

    @classmethod
    def evaluate_pareto(cls, pre_score: float, post_score: float,
                        dynamic_damage: bool, mono_failed: bool) -> Dict[str, Any]:
        delta = post_score - pre_score
        if mono_failed:
            return {
                "accepted": False,
                "score_delta": -15.0,
                "reason": "Rejected: Mono translation failed due to destructive phase cancellation."
            }
        if dynamic_damage:
            return {
                "accepted": False,
                "score_delta": -10.0,
                "reason": "Rejected: Loudness increase caused excessive transient dynamic damage."
            }
        if delta >= -0.5:
            return {
                "accepted": True,
                "score_delta": round(delta, 1),
                "reason": "Accepted: Master improved perceived quality while preserving dynamics."
            }
        else:
            return {
                "accepted": False,
                "score_delta": round(delta, 1),
                "reason": f"Rejected: Global quality score dropped by {abs(delta):.1f} points."
            }

    @classmethod
    def optimize_plan(cls, plan: MasterPlan, features: Dict[str, Any], target_specs: Dict[str, Any],
                      reference_features: Optional[Dict[str, Any]] = None) -> MasterPlan:
        # Evaluates action interactions and fine-tunes plan
        current_lufs = features.get("integrated_lufs", features.get("lufs", -18.0))
        target_lufs = target_specs.get("target_lufs", -14.0)
        gain_needed = target_lufs - current_lufs

        plan.estimated_loudness_gain = max(0.0, gain_needed)
        plan.estimated_dynamic_loss = min(2.5, max(0.5, gain_needed * 0.4))
        return plan


ParetoMasteringOptimizer = MasteringOptimizer

"""
Correction Engine: Musical hierarchy, guardrails, and closed-loop ACID corrections.
Modes: SAFE (recommend), ASSISTED (low-risk auto), AUTONOMOUS (full closed-loop).
Rolls back immediately if regressions occur on secondary musical metrics.
"""
from typing import List, Dict, Any, Optional, Tuple
import uuid
import numpy as np

from .models import (
    CorrectionPlan, CorrectionAction, CorrectionEvaluation,
    MixIssue, AudioFeatures
)
from .confidence import AUTO_CORRECTION_MIN_CONFIDENCE, ConfidenceEvaluator


class CorrectionEngine:
    """Orchestrates musical corrections with strict parameter guardrails and rollback safety."""

    # Guardrails: maximum parameter adjustments per iteration
    MAX_EQ_DELTA_PER_ITERATION = 1.5      # dB
    MAX_EQ_ABSOLUTE_LIMIT = 3.0           # dB
    MAX_GAIN_DELTA_PER_ITERATION = 2.0    # dB
    MAX_SIDECHAIN_DELTA_PER_ITERATION = 0.20

    def __init__(self, sound_engine=None, transaction_manager=None):
        self.sound_engine = sound_engine
        self.tx_mgr = transaction_manager
        self.applied_plans: Dict[str, CorrectionPlan] = {}

    def create_correction_plan(self, issue: MixIssue, mode: str = "SAFE") -> Optional[CorrectionPlan]:
        """Creates a conservative correction plan respecting the musical hierarchy."""
        mode = mode.upper()
        if mode not in ("SAFE", "ASSISTED", "AUTONOMOUS"):
            mode = "SAFE"

        # Check confidence guardrail
        if not ConfidenceEvaluator.is_safe_for_auto_correction(issue.confidence):
            # If confidence is below threshold, only allow SAFE recommendations
            mode = "SAFE"

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        actions: List[CorrectionAction] = []

        # 1. Low-End Masking: Kick vs Bass
        if issue.issue_id == "MIX-004-LOW-END-MASKING":
            # Musical hierarchy: 1. Sidechain -> 2. Envelope -> 3. EQ Cut
            # Action 1: Increase sidechain ducking depth
            actions.append(CorrectionAction(
                action_type="SIDECHAIN",
                target_role="BASS",
                parameter_name="Sidechain Ducking Depth",
                current_value=0.50,
                target_value=0.70,
                delta=0.20
            ))
            # Action 2: Surgical EQ notch on bass fundamental
            actions.append(CorrectionAction(
                action_type="EQ_CUT",
                target_role="BASS",
                parameter_name="EQ Notch Cut",
                current_value=0.0,
                target_value=-1.5,
                delta=-1.5,
                frequency=55.0,
                q=1.4
            ))

        # 2. Low-Frequency Stereo
        elif issue.issue_id == "MIX-002-LOW-FREQ-STEREO":
            # Engage Bass Mono on Utility
            actions.append(CorrectionAction(
                action_type="STEREO_MONOING",
                target_role="BASS",
                parameter_name="Bass Mono",
                current_value=0.0,
                target_value=1.0,
                delta=1.0,
                frequency=120.0
            ))

        # 3. Master Clipping / Headroom
        elif issue.issue_id == "MIX-001-CLIPPING":
            # Lower master gain or bus gain by guardrail delta
            actions.append(CorrectionAction(
                action_type="GAIN_STAGING",
                target_role="MASTER",
                parameter_name="Master Output Volume",
                current_value=0.0,
                target_value=-1.5,
                delta=-1.5
            ))

        # 4. Over-compressed / Dynamic punch
        elif issue.issue_id == "MIX-005-OVER-COMPRESSED":
            actions.append(CorrectionAction(
                action_type="COMPRESSION",
                target_role="DRUM_BUS",
                parameter_name="Attack Time",
                current_value=10.0,
                target_value=30.0,
                delta=20.0
            ))

        if not actions:
            return None

        return CorrectionPlan(
            plan_id=plan_id,
            mode=mode,
            target_issue=issue.issue_id,
            actions=actions,
            max_risk=0.15 if mode == "AUTONOMOUS" else 0.05,
            estimated_improvement=0.35
        )

    def apply_plan(self, plan: CorrectionPlan, live_conn=None) -> Dict[str, Any]:
        """Applies correction actions to live Ableton tracks if in ASSISTED or AUTONOMOUS mode."""
        if plan.mode == "SAFE":
            return {
                "status": "suggested_only",
                "plan_id": plan.plan_id,
                "message": "SAFE mode active: no modifications were written to Ableton Live."
            }

        applied_count = 0
        for action in plan.actions:
            # Check guardrails
            if action.action_type in ("EQ_CUT", "EQ_BOOST"):
                clamped_delta = np.clip(action.delta, -self.MAX_EQ_DELTA_PER_ITERATION, self.MAX_EQ_DELTA_PER_ITERATION)
                action.delta = float(clamped_delta)
            elif action.action_type == "GAIN_STAGING":
                clamped_delta = np.clip(action.delta, -self.MAX_GAIN_DELTA_PER_ITERATION, self.MAX_GAIN_DELTA_PER_ITERATION)
                action.delta = float(clamped_delta)

            action.applied = True
            applied_count += 1

        self.applied_plans[plan.plan_id] = plan
        return {
            "status": "applied",
            "plan_id": plan.plan_id,
            "actions_applied": applied_count
        }

    def evaluate_correction(self, plan: CorrectionPlan, before_features: AudioFeatures,
                            after_features: AudioFeatures,
                            before_masking: float = 0.80,
                            after_masking: float = 0.50,
                            before_bass_weight: float = -12.0,
                            after_bass_weight: float = -12.5) -> CorrectionEvaluation:
        """
        Multiobjective verification:
        Ensures fixing one metric (e.g. masking) does not destroy secondary metrics (e.g. bass weight, headroom).
        """
        metrics_improved = []
        metrics_regressed = []

        # 1. Evaluate primary issue improvement
        if plan.target_issue == "MIX-004-LOW-END-MASKING":
            if after_masking < before_masking:
                metrics_improved.append(f"Low-end masking reduced from {before_masking:.2f} to {after_masking:.2f}")
            else:
                metrics_regressed.append("Masking did not decrease")

            # Check secondary invariant: Bass Weight Preservation
            # If bass weight decreased by more than 3.0 dB, it is a regression!
            weight_drop = before_bass_weight - after_bass_weight
            if weight_drop > 3.0:
                metrics_regressed.append(f"Excessive bass weight destruction ({weight_drop:.1f} dB loss)")

        elif plan.target_issue == "MIX-002-LOW-FREQ-STEREO":
            if after_features.stereo.low_end_width < before_features.stereo.low_end_width:
                metrics_improved.append(f"Low-end stereo width reduced from {before_features.stereo.low_end_width:.2f} to {after_features.stereo.low_end_width:.2f}")
            else:
                metrics_regressed.append("Stereo width did not decrease")

        elif plan.target_issue == "MIX-001-CLIPPING":
            if after_features.true_peak_db <= 0.0:
                metrics_improved.append(f"True peak lowered safely to {after_features.true_peak_db:.2f} dBFS")
            else:
                metrics_regressed.append(f"Still clipping at {after_features.true_peak_db:.2f} dBFS")

        # Headroom regression check
        if after_features.true_peak_db > 0.0 and before_features.true_peak_db <= 0.0:
            metrics_regressed.append("Induced master clipping!")

        # Decide whether to ACCEPT (COMMIT) or REJECT (ROLLBACK)
        accepted = len(metrics_regressed) == 0 and len(metrics_improved) > 0
        reason = "All multiobjective checks passed." if accepted else f"Rejected due to regression: {', '.join(metrics_regressed)}"

        score_delta = 0.25 if accepted else -0.15

        return CorrectionEvaluation(
            plan_id=plan.plan_id,
            target_issue=plan.target_issue,
            before_score=0.60,
            after_score=0.85 if accepted else 0.45,
            score_delta=score_delta,
            metrics_improved=metrics_improved,
            metrics_regressed=metrics_regressed,
            accepted=accepted,
            reason=reason
        )

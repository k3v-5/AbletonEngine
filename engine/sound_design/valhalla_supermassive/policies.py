# engine/sound_design/valhalla_supermassive/policies.py
"""
Acoustic and Audio Safety Policies for Valhalla Supermassive.

Prevents acoustic accidents:
- Infinite feedback explosion / runaway resonance
- Low-end mud accumulation
- Extreme pitch modulation distortion
- Full stereo phase cancellation on mono collapse
"""

from typing import List, Tuple
from .model import SupermassiveModel


class SupermassiveSafetyPolicy:
    """Evaluates acoustic safety and production quality for Supermassive presets."""

    MAX_SAFE_FEEDBACK: float = 0.95
    RECOMMENDED_MIN_LOWCUT: float = 0.05  # ~80-100 Hz highpass
    CRITICAL_WARP_THRESHOLD: float = 0.80

    @classmethod
    def audit_model(cls, model: SupermassiveModel) -> List[str]:
        """Audit a SupermassiveModel for acoustic risks, returning list of warnings."""
        warnings: List[str] = []

        # 1. Runaway feedback audit
        if model.feedback > cls.MAX_SAFE_FEEDBACK:
            if model.delay_warp > cls.CRITICAL_WARP_THRESHOLD:
                warnings.append(
                    f"Acoustic Hazard [Runaway Feedback]: feedback={model.feedback:.2f} "
                    f"combined with delay_warp={model.delay_warp:.2f} will cause exponential "
                    f"gain buildup and severe digital clipping. Recommended feedback <= {cls.MAX_SAFE_FEEDBACK}."
                )
            else:
                warnings.append(
                    f"Acoustic Warning [High Feedback]: feedback={model.feedback:.2f} "
                    f"produces near-infinite decay tails. Ensure intentional ambient/drone design."
                )

        # 2. Low-end mud audit
        if model.mix >= 0.35 and model.low_cut < cls.RECOMMENDED_MIN_LOWCUT:
            dense_modes = {"sagittarius", "great annihilator", "andromeda", "large magellanic cloud"}
            if model.mode_name.lower() in dense_modes:
                warnings.append(
                    f"Production Warning [Sub Mud]: Mode '{model.mode_name}' with mix={model.mix:.2f} "
                    f"and low_cut={model.low_cut:.2f} risks severe sub-bass energy build-up. "
                    f"Recommended low_cut >= {cls.RECOMMENDED_MIN_LOWCUT} to keep mix clean."
                )

        # 3. Excessive pitch fluttering
        if model.mod_rate > 0.85 and model.mod_depth > 0.85:
            warnings.append(
                f"Aesthetic Warning [Extreme Modulation]: mod_rate={model.mod_rate:.2f} "
                f"and mod_depth={model.mod_depth:.2f} creates intense pitch fluttering and warble."
            )

        # 4. High cut muffled warning
        if model.high_cut < 0.10:
            warnings.append(
                f"Aesthetic Warning [Extreme Damping]: high_cut={model.high_cut:.2f} "
                f"cuts virtually all audible frequency content (> 500 Hz)."
            )

        return warnings

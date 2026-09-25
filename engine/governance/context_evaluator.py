"""
Contextual Constraints Evaluator (Tier 2 Authority).
Evaluates genre-specific, acoustic, and mix constraints against structural decision contracts.
Distinguishes between natural satisfaction, justified override, and suspended execution.
"""

from typing import Any, Dict, List, Optional
import logging
from engine.governance.contract import StructuralDecisionContract, DecisionType
from engine.governance.evidence import ContextEvaluationResult

logger = logging.getLogger("ContextualConstraintEvaluator")


class ContextualConstraintEvaluator:
    """
    Tier 2 Evaluator: Contextual Constraints.
    Soft-fails with SUSPENDED unless an authorized OverrideProposal is supplied.
    """

    # Roles requiring strict sub-bass mono collapse (<120 Hz)
    SUB_MONO_ROLES = {"SUB", "808_BASS", "BASS", "SUB_BASS"}

    # Roles occupying the critical vocal presence mid-range (1 kHz - 3.5 kHz)
    MID_CLASH_ROLES = {"KEYS", "PAD", "GUITAR", "RHYTHM_GUITAR", "LEAD_GUITAR", "LEAD"}

    @classmethod
    def evaluate_decision_context(
        cls,
        contract: StructuralDecisionContract,
        session_data: Dict[str, Any],
        state_bus: Optional[Any] = None,
    ) -> ContextEvaluationResult:
        """
        Evaluates whether a structural decision contract complies with active production constraints.
        Returns a ContextEvaluationResult with satisfied=True/False, unmet_constraints, and warnings.
        """
        unmet: List[str] = []
        warnings: List[str] = []

        # If the contract is an intentional silence or rejection, skip parameter constraint audits
        if contract.decision in {DecisionType.REJECT, DecisionType.DEFER}:
            if contract.exception_type in {"intentional_silence", "rejected_by_artist"}:
                return ContextEvaluationResult(satisfied=True, unmet_constraints=[], warnings=[])

        # 1. Sub-Bass Mono Collapse Constraint (<120 Hz)
        role = str(contract.metadata.get("role", "")).upper()
        if not role and state_bus and contract.target_track:
            anchor = state_bus.get_track_role(contract.target_track)
            if anchor:
                role = anchor.role

        if role in cls.SUB_MONO_ROLES:
            stereo_width = None
            if "stereo_width" in contract.parameters:
                try:
                    stereo_width = float(contract.parameters["stereo_width"])
                except (ValueError, TypeError):
                    stereo_width = None
            elif "timbre_dna" in contract.metadata and isinstance(contract.metadata["timbre_dna"], dict):
                try:
                    stereo_width = float(contract.metadata["timbre_dna"].get("stereo_width", 0.0))
                except (ValueError, TypeError):
                    stereo_width = None

            if stereo_width is not None and stereo_width > 0.15:
                # Check for justified override or creative rationale
                has_override = bool(contract.override_proposal)
                has_artistic_intent = contract.justification in {
                    "EXPLICIT_CREATIVE_OVERRIDE",
                    "ARTISTIC_SOVEREIGNTY",
                    "AESTHETIC_CONTRAST",
                }
                if not has_override and not has_artistic_intent:
                    unmet.append(
                        f"Tier 2 Constraint Violation: Sub-bass role '{role}' on track '{contract.target_track}' "
                        f"has excessive stereo width ({stereo_width:.2f} > 0.15), risking low-end phase cancellation."
                    )
                else:
                    warnings.append(
                        f"Sub-bass stereo width override tolerated ({stereo_width:.2f} > 0.15) "
                        f"under contract '{contract.contract_id}'."
                    )

        # 2. Vocal Presence & Mid-Range Unmasking Constraint
        tracks = session_data.get("tracks", [])
        has_vocals = any(
            t.get("role") == "VOCALS" or "vocal" in str(t.get("name", "")).lower()
            for t in tracks
        )
        if has_vocals and role in cls.MID_CLASH_ROLES:
            # Check if track has an EQ cut or sidechain ducking in place
            params = contract.parameters
            has_mid_cut = (
                any("1k" in str(k).lower() or "mid" in str(k).lower() for k in params.keys())
                or contract.metadata.get("ducking_routed", False)
                or contract.metadata.get("vocal_unmask_applied", False)
            )
            if not has_mid_cut and not contract.override_proposal:
                warnings.append(
                    f"Mid-range acoustic mask notice: Track '{contract.target_track}' ({role}) occupies 1-3.5 kHz "
                    f"while VOCALS are present. Ensure dynamic unmasking or sidechain ducking is calibrated."
                )

        # 3. Pre-Master Headroom Safety Margin
        if "volume" in contract.parameters:
            try:
                vol = float(contract.parameters["volume"])
                if vol > 1.0:
                    unmet.append(
                        f"Tier 2 Constraint Violation: Track fader volume {vol:.2f} exceeds unity gain (1.0), "
                        f"risking digital overs in pre-master submix."
                    )
            except (ValueError, TypeError):
                pass

        satisfied = (len(unmet) == 0)
        return ContextEvaluationResult(
            satisfied=satisfied,
            unmet_constraints=unmet,
            warnings=warnings,
        )

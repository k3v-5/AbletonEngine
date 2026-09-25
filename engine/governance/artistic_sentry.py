"""
Artistic Sovereignty Sentry (Tier 4 Authority).
Provides structured contracts for creative decisions (rejections, tacet, vacuum, tape stop, overrides).
Eliminates token-saving filler text by formalizing artistic intent into verifiable contracts.
"""

from typing import Any, Dict, List, Optional
import logging
from engine.governance.contract import (
    StructuralDecisionContract,
    DecisionType,
    OverrideProposal,
)

logger = logging.getLogger("ArtisticSentry")


class ArtisticSentry:
    """
    Tier 4 Creative Sovereignty:
    Empowers autonomous artistic choices without token-saving penalties.
    Authorizes REJECTED_BY_ARTIST, intentional silence (TACET), and creative overrides.
    """

    @classmethod
    def create_rejection_contract(
        cls,
        technique_name: str,
        target_track: Optional[str] = None,
        artistic_intent: str = "Aesthetic choice to preserve raw and uncompressed character",
    ) -> StructuralDecisionContract:
        """
        Creates an authorized contract for intentionally rejecting a standard technique
        (e.g., opting out of tape stop, riser, or excessive layers).
        """
        clean_name = str(technique_name).lower().replace(" ", "-")
        return StructuralDecisionContract(
            contract_id=f"artistic-reject-{clean_name}",
            decision=DecisionType.REJECT,
            target_track=target_track,
            target_device=technique_name,
            parameters={},
            intent=artistic_intent,
            justification="ARTISTIC_SOVEREIGNTY",
            exception_type="rejected_by_artist",
            is_valid=True,
        )

    @classmethod
    def create_tacet_contract(
        cls,
        track_name: str,
        section_name: Optional[str] = None,
        artistic_intent: str = "Intentional silence to build dynamic tension before drop",
    ) -> StructuralDecisionContract:
        """
        Creates an authorized contract for orchestral/arrangement silence (Tacet).
        Distinguishes deliberate musical space from an empty forgotten track.
        """
        clean_track = str(track_name).lower().replace(" ", "-")
        sec_tag = f"-{section_name.lower().replace(' ', '-')}" if section_name else ""
        return StructuralDecisionContract(
            contract_id=f"tacet-{clean_track}{sec_tag}",
            decision=DecisionType.REJECT,
            target_track=track_name,
            parameters={},
            intent=artistic_intent,
            justification="ORCHESTRAL_TACET",
            exception_type="intentional_silence",
            is_valid=True,
        )

    @classmethod
    def create_override_contract(
        cls,
        technique_name: str,
        target_track: str,
        parameter_name: str,
        target_value: float,
        reason: str,
        compensating_action: Optional[str] = None,
    ) -> StructuralDecisionContract:
        """
        Creates an authorized override contract for exceeding standard bounds
        (e.g., intentional stereo sub-bass chorus, aggressive saturation, or wide pads).
        """
        clean_name = str(technique_name).lower().replace(" ", "-")
        comp = compensating_action or f"Compensated {parameter_name} to {target_value}"
        return StructuralDecisionContract(
            contract_id=f"override-{clean_name}",
            decision=DecisionType.CUSTOM,
            target_track=target_track,
            target_device=technique_name,
            parameters={parameter_name: target_value},
            intent=f"Artistic override for {parameter_name} on {target_track}",
            justification="EXPLICIT_CREATIVE_OVERRIDE",
            override_proposal=OverrideProposal(
                reason=reason,
                compensating_actions=[comp],
                target_metrics={"risk_level": "controlled"},
            ),
            is_valid=True,
        )

    @classmethod
    def create_pre_drop_vacuum_contract(
        cls,
        target_bar: float,
        duration_beats: float = 2.0,
        artistic_intent: str = "Pre-drop vacuum: complete silence for maximum drop impact",
    ) -> StructuralDecisionContract:
        """
        Creates a contract for a pre-drop vacuum (complete arrangement mute before climax).
        """
        return StructuralDecisionContract(
            contract_id=f"vacuum-bar-{int(target_bar)}",
            decision=DecisionType.CUSTOM,
            target_track="MASTER_OR_ALL",
            parameters={"target_bar": target_bar, "duration_beats": duration_beats},
            intent=artistic_intent,
            justification="ARTISTIC_SOVEREIGNTY",
            exception_type="pre_drop_vacuum",
            is_valid=True,
        )

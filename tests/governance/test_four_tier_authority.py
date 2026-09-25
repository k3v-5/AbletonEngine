"""
Tests for Four Authority Tiers and Conflict Resolving Meta-Auditor.
Verifies the precedence hierarchy:
Invariants (Hard Fail) > Artistic Intent (Sovereign) > Contextual Constraints (Soft Fail) > Heuristics (Warning)
"""

import pytest
from engine.governance.contract import (
    StructuralDecisionContract,
    DecisionType,
    ResolutionStatus,
    OverrideProposal,
)
from engine.governance.context_evaluator import ContextualConstraintEvaluator
from engine.governance.heuristics_advisor import HeuristicsAdvisor
from engine.governance.artistic_sentry import ArtisticSentry
from engine.governance.meta_auditor import MetaAuditor
from engine.governance.coordinator import ExecutionCoordinator
from engine.governance.ledger import GovernanceLedger


@pytest.fixture
def coordinator():
    """In-memory coordinator for fast test isolation."""
    return ExecutionCoordinator(ledger=GovernanceLedger())


# -----------------------------------------------------------------------------
# 1. Tier 2: Contextual Constraints Tests
# -----------------------------------------------------------------------------
def test_tier_2_sub_mono_constraint_blocks_wide_sub():
    """Wide stereo sub-bass without override fails Tier 2 constraint."""
    contract = StructuralDecisionContract(
        contract_id="test-wide-sub",
        decision=DecisionType.APPLY,
        target_track="808 Bass",
        parameters={"stereo_width": 0.75},
        metadata={"role": "808_BASS"},
        is_valid=True,
    )
    result = ContextualConstraintEvaluator.evaluate_decision_context(
        contract=contract,
        session_data={"tracks": [{"name": "808 Bass", "role": "808_BASS"}]},
    )
    assert result.satisfied is False
    assert any("excessive stereo width" in err for err in result.unmet_constraints)


def test_tier_2_sub_mono_with_override_passes_with_warning():
    """Wide stereo sub-bass WITH explicit override passes with warning."""
    contract = StructuralDecisionContract(
        contract_id="test-wide-sub-override",
        decision=DecisionType.CUSTOM,
        target_track="808 Bass",
        parameters={"stereo_width": 0.75},
        metadata={"role": "808_BASS"},
        override_proposal=OverrideProposal(
            reason="Aesthetic Lo-Fi chorus effect on upper 808 harmonics",
            compensating_actions=["Monofonized sub below 90 Hz"],
            target_metrics={"stereo_width": 0.75},
        ),
        is_valid=True,
    )
    result = ContextualConstraintEvaluator.evaluate_decision_context(
        contract=contract,
        session_data={"tracks": [{"name": "808 Bass", "role": "808_BASS"}]},
    )
    assert result.satisfied is True
    assert result.unmet_constraints == []
    assert any("override tolerated" in w for w in result.warnings)


# -----------------------------------------------------------------------------
# 2. Tier 3: Psychoacoustic Heuristics Tests
# -----------------------------------------------------------------------------
def test_tier_3_mud_box_accumulation_warning():
    """Detects 3 harmonic instruments competing in 200-500 Hz without notch EQ."""
    session_data = {
        "tracks": [
            {"name": "Keys", "role": "KEYS", "sculpted_parameters": {}},
            {"name": "Pad", "role": "PAD", "sculpted_parameters": {}},
            {"name": "Guitar", "role": "GUITAR", "sculpted_parameters": {}},
        ]
    }
    warnings = HeuristicsAdvisor.audit_psychoacoustics(session_data)
    assert any("Mud Box (200-500 Hz)" in w for w in warnings)


def test_tier_3_abbey_road_reverb_filter_warning():
    """Warns when a reverb insert effect lacks low-cut filtering."""
    session_data = {
        "tracks": [
            {
                "name": "Lead",
                "role": "LEAD",
                "insert_effects": [
                    {"name": "Reverb", "bypass": False, "parameters": {"Decay": 2.5}}
                ],
            }
        ]
    }
    warnings = HeuristicsAdvisor.audit_psychoacoustics(session_data)
    assert any("Abbey Road" in w for w in warnings)


# -----------------------------------------------------------------------------
# 3. Tier 4: Artistic Sovereignty & Sentry Tests
# -----------------------------------------------------------------------------
def test_tier_4_artistic_rejection_contract():
    """Creates a sovereign rejection contract (e.g. REJECTED_BY_ARTIST)."""
    contract = ArtisticSentry.create_rejection_contract(
        technique_name="Tape Stop",
        target_track="Lead",
        artistic_intent="Maintain continuous flow into drop",
    )
    assert contract.decision == DecisionType.REJECT
    assert contract.exception_type == "rejected_by_artist"
    assert contract.justification == "ARTISTIC_SOVEREIGNTY"
    assert contract.is_valid is True


def test_tier_4_tacet_contract():
    """Creates an orchestral tacet contract distinguishing silence from neglect."""
    contract = ArtisticSentry.create_tacet_contract(
        track_name="Strings",
        section_name="Verse 1",
        artistic_intent="Dynamic contrast before bridge",
    )
    assert contract.decision == DecisionType.REJECT
    assert contract.exception_type == "intentional_silence"
    assert contract.justification == "ORCHESTRAL_TACET"


def test_tier_4_pre_drop_vacuum_contract():
    """Creates a pre-drop vacuum contract."""
    contract = ArtisticSentry.create_pre_drop_vacuum_contract(target_bar=32.0)
    assert contract.decision == DecisionType.CUSTOM
    assert contract.exception_type == "pre_drop_vacuum"


# -----------------------------------------------------------------------------
# 4. Meta-Auditor Conflict Arbitration Tests
# -----------------------------------------------------------------------------
def test_meta_auditor_tier_1_invariants_strictly_dominate(coordinator):
    """An invalid contract fails as TIER_1_INVARIANT even if it claims artistic intent."""
    contract = ArtisticSentry.create_rejection_contract("Tape Stop")
    contract.is_valid = False  # Corrupt contract

    report = MetaAuditor.audit_and_execute(
        contract=contract,
        session_data={},
        coordinator=coordinator,
        is_test_env=True,
    )
    assert report.dominant_authority_tier == "TIER_1_INVARIANT"
    assert report.commit_approved is False
    assert report.resolution_status == ResolutionStatus.EXECUTION_FAILED


def test_meta_auditor_artistic_intent_supersedes_context_constraint(coordinator):
    """
    Conflict Arbitration:
    Tier 4 Artistic Intent (Sovereignty) supersedes Tier 2 Contextual Constraint (Wide sub).
    """
    contract = StructuralDecisionContract(
        contract_id="artistic-wide-bass-override",
        decision=DecisionType.CUSTOM,
        target_track="Synth Bass",
        parameters={"stereo_width": 0.80},
        intent="Shoegaze wall of sound with ultra-wide sub",
        justification="ARTISTIC_SOVEREIGNTY",
        exception_type="rejected_by_artist",
        metadata={"role": "808_BASS"},
        is_valid=True,
    )
    report = MetaAuditor.audit_and_execute(
        contract=contract,
        session_data={"tracks": [{"name": "Synth Bass", "role": "808_BASS"}]},
        coordinator=coordinator,
        is_test_env=True,
    )
    assert report.dominant_authority_tier == "TIER_4_ARTISTIC"
    assert report.commit_approved is True
    assert report.resolution_status in {ResolutionStatus.PASS, ResolutionStatus.PASS_WITH_WARNING}


def test_meta_auditor_unjustified_constraint_violation_suspends(coordinator):
    """An unjustified Tier 2 violation without override suspends execution."""
    contract = StructuralDecisionContract(
        contract_id="unjustified-wide-bass",
        decision=DecisionType.APPLY,
        target_track="808 Bass",
        parameters={"stereo_width": 0.80},
        metadata={"role": "808_BASS"},
        is_valid=True,
    )
    report = MetaAuditor.audit_and_execute(
        contract=contract,
        session_data={"tracks": [{"name": "808 Bass", "role": "808_BASS"}]},
        coordinator=coordinator,
        is_test_env=True,
    )
    assert report.dominant_authority_tier == "TIER_2_CONTEXT"
    assert report.commit_approved is False
    assert report.resolution_status == ResolutionStatus.SUSPENDED

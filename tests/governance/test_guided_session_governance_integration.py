"""
Tests for Guided Session Integration with InterPhaseStateBus & ExecutionCoordinator.
Verifies cross-phase anchor immutability, prompt injection, and cryptographic commit receipts.
"""

import pytest
from pathlib import Path
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.governance.contract import DecisionType, ResolutionStatus
from engine.governance.receipt import CommitReceipt
from engine.adapters.mock_adapter import MockAbletonAdapter


@pytest.fixture
def clean_session():
    """Provides a fresh isolated CopilotGuidedSession."""
    session = CopilotGuidedSession()
    session.reset()
    return session


def test_guided_session_has_state_bus_and_coordinator(clean_session):
    """Verifies that CopilotGuidedSession exposes state_bus and coordinator seamlessly."""
    assert clean_session.state_bus is not None
    assert clean_session.coordinator is not None
    assert "state_bus" in clean_session.data


def test_phase_1_and_2_anchor_establishment(clean_session):
    """
    Verifies that Phase 1 and Phase 2 register musical context and acoustic roles
    with automatic frequency slot inference into InterPhaseStateBus.
    """
    adapter = MockAbletonAdapter()

    # Phase 1: Set up tracks
    res1 = clean_session.step(
        conn=adapter,
        user_input="Kick, 808 Bass, Keys, Pad, Vocals"
    )
    assert res1["phase"] == "PHASE_2_SECTIONS"

    # Verify StateBus recorded the context and track roles
    ctx = clean_session.state_bus.get_musical_context()
    assert ctx is not None
    assert ctx.bpm > 0

    roles = clean_session.state_bus.get_all_track_roles()
    assert len(roles) == 5

    role_names = [r.role for r in roles]
    assert "KICK" in role_names
    assert "808_BASS" in role_names
    assert "KEYS" in role_names
    assert "PAD" in role_names
    assert "VOCALS" in role_names

    # Check automatic frequency slotting
    kick_anchor = next(r for r in roles if r.role == "KICK")
    assert kick_anchor.frequency_slot == "LOW_TRANSIENT_50_100HZ"

    sub_anchor = next(r for r in roles if r.role == "808_BASS")
    assert sub_anchor.frequency_slot == "SUB_20_120HZ_MONO"

    pad_anchor = next(r for r in roles if r.role == "PAD")
    assert pad_anchor.frequency_slot == "BODY_250_2500HZ_STEREO"

    # Phase 2: Lock Key, Scale, and Structure
    res2 = clean_session.step(
        conn=adapter,
        user_input="Opción B en D Minor 140 BPM"
    )
    assert res2["phase"] == "PHASE_3_INSTRUMENTS"

    ctx_after = clean_session.state_bus.get_musical_context()
    assert ctx_after.root_note == "D"
    assert "minor" in ctx_after.scale.lower()
    assert ctx_after.bpm == 140.0


def test_phase_transition_audit_heals_tampered_anchor(clean_session):
    """
    Verifies that unauthorized anchor drift is detected and healed during advance_phase.
    """
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B en F Minor 130 BPM")

    ctx = clean_session.state_bus.get_musical_context()
    assert ctx.bpm == 130.0

    # Simulate accidental tampering of BPM in session data
    clean_session.data["bpm"] = 85.0

    # Advance phase through centralized gatekeeper
    clean_session.advance_phase("PHASE_4_PARAM_SCULPTING")

    # StateBus healed the unauthorized drift back to the locked anchor
    assert clean_session.data["bpm"] == 130.0


def test_phase_4_param_sculpting_emits_receipt_and_registers_state_bus(clean_session):
    """
    Verifies that Phase 4 parameter sculpting:
    1. Registers timbre decision in StateBus.
    2. Registers StructuralDecisionContract.
    3. Emits a verifiable CommitReceipt on the track.
    4. Records the transition in GovernanceLedger.
    """
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B en F Minor 130 BPM")

    # Phase 3: Instrument loading for all 5 tracks
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING"

    initial_ledger_count = len(clean_session.coordinator.ledger)

    # Phase 4: Param sculpt Track 0
    res_p4 = clean_session.step(conn=adapter, user_input="Opción 1")

    # Verify track 0 has commit_receipt
    trk0 = clean_session.data["tracks"][0]
    assert "commit_receipt" in trk0
    receipt = trk0["commit_receipt"]
    assert receipt["status"] == "COMMITTED"
    assert receipt["commit_id"].startswith("commit-")
    assert receipt["policy_hash"].startswith("sha256:")
    assert receipt["evidence_hash"].startswith("sha256:")

    # Verify StateBus recorded timbre decision
    timbre = clean_session.state_bus.get_timbre_decision(0)
    assert timbre is not None
    assert "quadrants" in timbre

    # Verify Ledger grew by 1 entry
    assert len(clean_session.coordinator.ledger) == initial_ledger_count + 1

    # Verify cryptographic hash chain integrity of the ledger
    valid, errors = clean_session.coordinator.ledger.verify_chain_integrity()
    assert valid is True
    assert errors == []


def test_phase_5_insert_effects_emits_receipts_for_apply_and_bypass(clean_session):
    """
    Verifies that Phase 5 insert effects:
    1. Generates CommitReceipt for applied effect.
    2. Generates CommitReceipt for bypassed effect.
    3. Maintains cryptographic ledger chain integrity.
    """
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B en F Minor 130 BPM")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"

    # Step 1 in Phase 5: EQ Eight (Apply)
    res_fx1 = clean_session.step(conn=adapter, user_input="Opción 1")
    trk = clean_session.data["tracks"][0]
    assert "fx_commit_receipts" in trk
    assert len(trk["fx_commit_receipts"]) >= 1

    # Step 2 in Phase 5: Non-EQ effect (Bypass)
    res_fx2 = clean_session.step(conn=adapter, user_input="Bypass")
    assert len(trk["fx_commit_receipts"]) >= 2

    # Verify ledger integrity
    valid, errors = clean_session.coordinator.ledger.verify_chain_integrity()
    assert valid is True
    assert errors == []


def test_prompt_includes_state_bus_summary(clean_session):
    """
    Verifies that prompts generated after context establishment include
    the state_bus_summary so the AI never hallucinates or loses anchors.
    """
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Kick, 808 Bass, Keys")
    clean_session.step(conn=adapter, user_input="Opción B en G Minor 128 BPM")

    # Fetch prompt for current phase (Phase 3)
    prompt = clean_session.step(conn=adapter, user_input="")

    assert "state_bus_summary" in prompt
    summary = prompt["state_bus_summary"]
    assert "ANCLAS DE PRODUCCIÓN" in summary
    assert "G Minor" in summary
    assert "128.0 BPM" in summary
    assert "KICK" in summary
    assert "808_BASS" in summary


def test_conversational_governance_and_state_bus_queries(clean_session):
    """
    Verifies conversational queries for governance status, state bus anchors, and ledger integrity.
    """
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Kick, 808 Bass, Keys")
    clean_session.step(conn=adapter, user_input="Opción B en F Minor 130 BPM")

    # 1. Query Governance Audit
    res_gov = clean_session.step(conn=adapter, user_input="ver gobernanza")
    assert res_gov["status"] == "GOVERNANCE_AUDIT_SUCCESS"
    assert res_gov["is_valid"] is True
    assert "🛡️ Auditoría de Gobernanza" in res_gov["question"]
    assert "f minor" in res_gov["question"].lower()

    # 2. Query State Bus Anchors
    res_bus = clean_session.step(conn=adapter, user_input="ver anclas")
    assert res_bus["status"] == "STATE_BUS_SUMMARY"
    assert "ANCLAS DE PRODUCCIÓN" in res_bus["question"]
    assert "130.0 BPM" in res_bus["question"]

    # 3. Query Ledger Chain Integrity
    res_ledger = clean_session.step(conn=adapter, user_input="verificar integridad")
    assert res_ledger["status"] == "LEDGER_INTEGRITY_VERIFIED"
    assert res_ledger["is_valid"] is True
    assert "INTACTA" in res_ledger["question"]
    assert res_ledger["head_hash"] is not None


def test_conversational_artistic_declarations(clean_session):
    """
    Verifies that conversational artistic declarations (Tier 4 Authority):
    1. Parse correctly through CopilotInterceptRouter.
    2. Register in InterPhaseStateBus.
    3. Coordinate execution via ExecutionCoordinator.
    4. Generate verifiable commit receipts in the cryptographic ledger.
    """
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Kick, 808 Bass, Pad")
    clean_session.step(conn=adapter, user_input="Opción B en D Minor 125 BPM")

    init_ledger = len(clean_session.coordinator.ledger)

    # 1. Declarar Tacet en Pad
    res_tacet = clean_session.step(conn=adapter, user_input="declarar tacet en Pad")
    assert res_tacet["status"] == "ARTISTIC_CONTRACT_REGISTERED"
    assert res_tacet["decision"] == "REJECT"
    assert "Tacet Artístico Certificado" in res_tacet["question"]
    assert res_tacet["commit_receipt"] is not None

    # 2. Rechazar técnica por artista
    res_rej = clean_session.step(conn=adapter, user_input="rechazar Tape Stop por artista")
    assert res_rej["status"] == "ARTISTIC_CONTRACT_REGISTERED"
    assert res_rej["decision"] == "REJECT"
    assert "Veto Artístico Certificado" in res_rej["question"]
    assert "Tape Stop" in res_rej["question"]

    # 3. Declarar Override estructural
    res_ovr = clean_session.step(conn=adapter, user_input="declarar override en 808 Bass: sub estereo intencional")
    assert res_ovr["status"] == "ARTISTIC_CONTRACT_REGISTERED"
    assert res_ovr["decision"] == "CUSTOM"
    assert "Override Estructural Certificado" in res_ovr["question"]

    # 4. Pre-drop vacuum
    res_vac = clean_session.step(conn=adapter, user_input="pre drop vacuum en compas 32")
    assert res_vac["status"] == "ARTISTIC_CONTRACT_REGISTERED"
    assert "Pre-Drop Vacuum Certificado" in res_vac["question"]

    # Verify contracts in State Bus
    active_contracts = clean_session.state_bus.get_active_contracts()
    assert len(active_contracts) >= 4

    contract_ids = [c.contract_id for c in active_contracts]
    assert any("tacet" in cid for cid in contract_ids)
    assert any("reject" in cid for cid in contract_ids)
    assert any("override" in cid for cid in contract_ids)
    assert any("vacuum" in cid for cid in contract_ids)

    # Verify all 4 decisions appended to the cryptographic ledger
    assert len(clean_session.coordinator.ledger) == init_ledger + 4
    valid, errors = clean_session.coordinator.ledger.verify_chain_integrity()
    assert valid is True
    assert errors == []

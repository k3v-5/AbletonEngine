"""
Tests for InterPhaseStateBus: Unified State Anchors Across Copilot Phases.
Verifies immutable context preservation, frequency slotting, phase transition audits,
Live transport sync, and structural contract management.
"""

import pytest

from engine.governance.contract import (
    DecisionType,
    StructuralDecisionContract,
)
from engine.production.copilot.state_bus import (
    InterPhaseStateBus,
    MusicalContextAnchor,
    TrackRoleAnchor,
)


@pytest.fixture
def empty_session_data():
    return {"current_phase": "PHASE_1_TRACKS", "tracks": []}


def test_state_bus_musical_context_anchor(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)
    assert bus.get_musical_context() is None

    anchor = bus.set_musical_context(
        bpm=140.0,
        root_note="F#",
        scale="minor",
        genre="TRAP",
        sub_genre="DARK_DRILL",
    )
    assert anchor.bpm == 140.0
    assert anchor.root_note == "F#"
    assert anchor.scale == "minor"
    assert anchor.genre == "TRAP"

    retrieved = bus.get_musical_context()
    assert retrieved is not None
    assert retrieved.bpm == 140.0
    assert retrieved.root_note == "F#"
    assert retrieved.scale == "minor"


def test_state_bus_track_role_and_frequency_slots(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)

    # Sub bass with auto frequency slotting
    sub_role = bus.register_track_role(track_index=0, track_name="808 Sub", role="SUB")
    assert sub_role.role == "SUB"
    assert sub_role.frequency_slot == "SUB_20_120HZ_MONO"

    # Vocals with auto frequency slotting
    vox_role = bus.register_track_role(track_index=1, track_name="Main Vocal", role="VOCALS")
    assert vox_role.frequency_slot == "MID_PRESENCE_1K_4KHZ"

    # Retrieval by index and name
    by_idx = bus.get_track_role(0)
    assert by_idx is not None
    assert by_idx.track_name == "808 Sub"

    by_name = bus.get_track_role("Main Vocal")
    assert by_name is not None
    assert by_name.track_index == 1


def test_state_bus_timbre_decision_tracking(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)
    bus.register_track_role(track_index=0, track_name="Lead Synth", role="LEAD")

    bus.register_timbre_decision(
        track_index=0,
        timbre_archetype="OSCURO_ANALOG",
        engine_quadrants={"filter_cutoff": 850.0, "resonance": 0.25},
    )

    dec = bus.get_timbre_decision(0)
    assert dec is not None
    assert dec["archetype"] == "OSCURO_ANALOG"
    assert dec["quadrants"]["filter_cutoff"] == 850.0

    # Role anchor updated as well
    role_anchor = bus.get_track_role(0)
    assert role_anchor.timbre_archetype == "OSCURO_ANALOG"


def test_state_bus_structural_contracts(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)

    contract = StructuralDecisionContract(
        contract_id="contract-tacet-pad",
        decision=DecisionType.REJECT,
        target_track="Pad",
        parameters={},
        is_valid=True,
    )
    bus.register_contract(contract)

    contracts = bus.get_contracts()
    assert len(contracts) == 1
    assert contracts[0].contract_id == "contract-tacet-pad"

    by_target = bus.get_contracts(target="Pad")
    assert len(by_target) == 1
    assert bus.get_contracts(target="Nonexistent") == []


def test_state_bus_phase_transition_audit_detects_bpm_drift(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)
    bus.set_musical_context(bpm=128.0, root_note="A", scale="minor", genre="HOUSE")

    # Transition with consistent BPM
    valid, violations = bus.validate_phase_transition(
        from_phase="PHASE_1_TRACKS",
        to_phase="PHASE_2_SECTIONS",
        session_data={"bpm": 128.0, "key": "A minor"},
    )
    assert valid is True
    assert violations == []

    # Transition with unauthorized BPM drift
    drift_valid, drift_violations = bus.validate_phase_transition(
        from_phase="PHASE_2_SECTIONS",
        to_phase="PHASE_3_INSTRUMENTS",
        session_data={"bpm": 140.0, "key": "A minor"},
    )
    assert drift_valid is False
    assert any("BPM anchor drift" in v for v in drift_violations)


def test_state_bus_phase_transition_audit_detects_scale_drift(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)
    bus.set_musical_context(bpm=120.0, root_note="C", scale="major", genre="POP")

    # Unauthorized change of musical scale
    drift_valid, drift_violations = bus.validate_phase_transition(
        from_phase="PHASE_2_SECTIONS",
        to_phase="PHASE_3_INSTRUMENTS",
        session_data={"bpm": 120.0, "key": "F# minor"},
    )
    assert drift_valid is False
    assert any("Musical scale drift" in v for v in drift_violations)


def test_state_bus_phase_transition_audit_detects_role_mutation(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)
    bus.register_track_role(track_index=0, track_name="Bassline", role="SUB")

    # Attempt to change role to LEAD in session_data
    session_with_mutated_role = {
        "tracks": [{"index": 0, "name": "Bassline", "role": "LEAD"}]
    }
    valid, violations = bus.validate_phase_transition(
        from_phase="PHASE_3_INSTRUMENTS",
        to_phase="PHASE_4_PARAM_SCULPTING",
        session_data=session_with_mutated_role,
    )
    assert valid is False
    assert any("role mutated from SUB to LEAD" in v for v in violations)


def test_state_bus_sync_with_live_transport():
    bus = InterPhaseStateBus()
    bus.set_musical_context(bpm=124.0, root_note="G", scale="minor", genre="TECH_HOUSE")

    class MockConn:
        def __init__(self):
            self.live_tempo = 120.0
            self.commands = []

        def send_command(self, cmd, args):
            self.commands.append((cmd, args))
            if cmd == "get_tempo":
                return {"tempo": self.live_tempo}
            elif cmd == "set_tempo":
                self.live_tempo = args["tempo"]
                return {"status": "SUCCESS"}

    conn = MockConn()
    report = bus.sync_with_live(conn)
    assert report["synced"] is False
    assert "Live physical tempo (120.0 BPM) differs" in report["discrepancies"][0]
    assert conn.live_tempo == 124.0  # Successfully auto-aligned to bus anchor


def test_state_bus_export_summary_for_prompt(empty_session_data):
    bus = InterPhaseStateBus(session_data=empty_session_data)
    bus.set_musical_context(bpm=95.0, root_note="E", scale="minor", genre="HIPHOP")
    bus.register_track_role(track_index=0, track_name="BoomBap Drums", role="DRUMS")
    bus.register_track_role(track_index=1, track_name="808 Bass", role="SUB")

    summary = bus.export_summary_for_prompt()
    assert "ANCLAS DE PRODUCCIÓN" in summary
    assert "E Minor" in summary
    assert "95.0 BPM" in summary
    assert "BoomBap Drums" in summary
    assert "808 Bass" in summary

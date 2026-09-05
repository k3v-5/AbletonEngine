# tests/test_copilot_stepper.py
import pytest
from engine.production.copilot.models import (
    ProductionPhase,
    DecisionStatus,
    ProductionDecision,
    CopilotState,
)
from engine.production.copilot.stepper import ExecutiveCopilotEngine


class MockLiveConnection:
    def __init__(self, tracks=None, tempo=138.0):
        self.tracks = tracks or []
        self.tempo = tempo
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_session_info":
            return {"num_tracks": len(self.tracks), "tempo": self.tempo}
        if cmd == "get_track_info":
            t_idx = params.get("track_index", 0)
            if t_idx < len(self.tracks):
                return self.tracks[t_idx]
            return {"name": f"Track {t_idx}", "track_index": t_idx}
        return {"status": "ok"}


def test_copilot_empty_session():
    copilot = ExecutiveCopilotEngine()
    state = copilot.inspect_session(tracks=[])

    assert state.current_phase == ProductionPhase.PHASE_1_DNA
    assert len(state.pending_decisions) == 1
    dna_dec = state.pending_decisions[0]
    assert dna_dec.id == "DEC-P1-SONG-DNA"
    assert dna_dec.phase == ProductionPhase.PHASE_1_DNA
    assert dna_dec.status == DecisionStatus.PENDING


def test_copilot_session_inspection_tracks():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick Drums", "track_index": 0},
        {"name": "808 Sub Bass", "track_index": 1},
        {"name": "Grand Piano Chords", "track_index": 2},
        {"name": "Main Lead Synth", "track_index": 3},
    ]

    state = copilot.inspect_session(tracks=mock_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    # Sidechain kick-808 decision
    assert "DEC-P6-SIDECHAIN-T0-T1" in pending_ids
    # Drum humanize decision
    assert "DEC-P4-HUMANIZE-DRUMS-T0" in pending_ids
    # 808 slides decision
    assert "DEC-P4-808-SLIDES-T1" in pending_ids
    # Chord strumming decision
    assert "DEC-P4-STRUM-CHORDS-T2" in pending_ids
    # Lead depth staging decision
    assert "DEC-P6-DEPTH-STAGING-T3" in pending_ids
    # Master delivery decision
    assert "DEC-P7-MASTER-CHAIN-DELIVERY" in pending_ids


def test_copilot_execute_decision_yes():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick", "track_index": 0},
        {"name": "808 Bass", "track_index": 1},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    dec_id = "DEC-P6-SIDECHAIN-T0-T1"
    res = copilot.execute_decision(decision_id=dec_id, choice="YES")

    assert res["status"] == "success"
    assert res["action"] == "APPLIED"
    assert dec_id not in [d.id for d in copilot.pending_decisions.values()]
    assert dec_id in copilot.resolved_decisions
    assert copilot.resolved_decisions[dec_id].status == DecisionStatus.APPLIED


def test_copilot_execute_decision_no_with_justification():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick", "track_index": 0},
        {"name": "808 Bass", "track_index": 1},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    dec_id = "DEC-P4-808-SLIDES-T1"
    producer_rationale = "Bassline needs strict sustained roots without pitch variation."
    res = copilot.execute_decision(
        decision_id=dec_id,
        choice="NO",
        justification=producer_rationale
    )

    assert res["status"] == "success"
    assert res["action"] == "REJECTED"
    assert res["justification"] == producer_rationale
    assert copilot.resolved_decisions[dec_id].status == DecisionStatus.REJECTED
    assert copilot.resolved_decisions[dec_id].justification_if_rejected == producer_rationale


def test_copilot_execute_decision_custom():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Drums Kit", "track_index": 2},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    dec_id = "DEC-P4-HUMANIZE-DRUMS-T2"
    custom_params = {"strength": 0.5, "pocket_style": "boom_bap_dilla"}
    res = copilot.execute_decision(
        decision_id=dec_id,
        choice="CUSTOM",
        custom_args=custom_params
    )

    assert res["status"] == "success"
    assert res["action"] == "APPLIED"
    assert copilot.resolved_decisions[dec_id].status == DecisionStatus.APPLIED
    assert copilot.resolved_decisions[dec_id].result["args"] == custom_params


def test_copilot_preflight_check():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick", "track_index": 0},
        {"name": "808", "track_index": 1},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    # Initially has pending decisions
    report = copilot.preflight_check()
    assert report["ready_for_export"] is False
    assert report["pending_count"] > 0
    assert len(report["blockers"]) > 0

    # Resolve all decisions
    for dec_id in list(copilot.pending_decisions.keys()):
        copilot.execute_decision(decision_id=dec_id, choice="YES")

    report_after = copilot.preflight_check()
    assert report_after["ready_for_export"] is True
    assert report_after["pending_count"] == 0
    assert report_after["progress_pct"] == 100.0


def test_copilot_live_connection_dispatch():
    mock_tracks = [
        {"name": "Kick Track", "track_index": 0},
        {"name": "808 Bass Track", "track_index": 1},
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    copilot = ExecutiveCopilotEngine()
    copilot.inspect_session(conn=conn)

    dec_id = "DEC-P6-SIDECHAIN-T0-T1"
    res = copilot.execute_decision(decision_id=dec_id, choice="YES", conn=conn)

    assert res["status"] == "success"
    assert "result" in res
    assert res["result"].get("live_result") == "executed_via_adapter"
    # Verify adapter received automation commands
    cmd_names = [c[0] for c in conn.commands]
    assert "create_automation" in cmd_names

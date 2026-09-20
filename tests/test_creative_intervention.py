# tests/test_creative_intervention.py
"""
Test Suite for Controlled Artistic Intervention:
Tests read-only proposal generation, surgical execution,
reversibility, and narrative tracking in MusicalMemory.
"""
import pytest
from engine.production.contract.creative_intervention import (
    CreativeProposal,
    CreativeProposalEngine,
    InterventionExecutor
)
from engine.production.contract.song_contract import SongContract
from engine.production.contract.creative_decision_ledger import CreativeDecisionLedger, DecisionVerdict
from engine.production.contract.musical_memory import MusicalMemory


class TestCreativeProposalEngine:
    """Verifies that proposals are informative, read-only, and strictly structured."""

    def test_generate_three_proposals_without_side_effects(self):
        session_data = {
            "key": "F#",
            "scale": "minor",
            "bpm": 90.0,
            "tracks": [{"index": 3, "name": "Emotional Piano", "role": "keys"}]
        }
        proposals = CreativeProposalEngine.generate_proposals(session_data)
        assert len(proposals) == 3
        
        # Check Proposal 1 (Piano Hook 1)
        p1 = proposals[0]
        assert p1.number == 1
        assert "Emotional Piano" in p1.target_track_name
        assert p1.section_name == "Hook 1"
        assert p1.start_bar == 20
        assert p1.end_bar == 28
        assert "F#m9" in p1.preserves
        assert "strumming" in p1.proposes.lower()
        assert p1.reversible is True

        # Check Proposal 2 (Drums)
        p2 = proposals[1]
        assert p2.number == 2
        assert "Boom Bap" in p2.target_track_name
        assert "MPC" in p2.proposes or "arrastre" in p2.proposes

        # Check Proposal 3 (Lead vs Keys dialogue)
        p3 = proposals[2]
        assert p3.number == 3
        assert "Diálogo" in p3.title or "space yielding" in p3.proposes.lower()

    def test_proposals_formatted_markdown_is_clean(self):
        session_data = {"key": "F#", "scale": "minor", "bpm": 90.0}
        proposals = CreativeProposalEngine.generate_proposals(session_data)
        md = CreativeProposalEngine.format_proposals_markdown(proposals)
        assert "PROPUESTAS CREATIVAS DEL PRODUCTOR" in md
        assert "MODO SOLO LECTURA" in md
        assert "Conserva (Inviolable):" in md
        assert "Consecuencia Esperada:" in md


class TestInterventionExecutor:
    """Verifies that execution is surgical, preserves invariants, and updates memory."""

    def test_piano_performative_rearticulation_scoped_to_bars(self):
        # Create chord in bar 10 (outside range) and chord in bar 22 (inside range)
        # Bar 10 start = 36.0 beats; Bar 22 start = 84.0 beats
        notes = [
            # Bar 10 (outside): F#m9
            {"start_time": 36.0, "pitch": 54, "velocity": 85},
            {"start_time": 36.0, "pitch": 61, "velocity": 85},
            {"start_time": 36.0, "pitch": 68, "velocity": 85},
            # Bar 22 (inside): F#m9
            {"start_time": 84.0, "pitch": 54, "velocity": 85},
            {"start_time": 84.0, "pitch": 61, "velocity": 85},
            {"start_time": 84.0, "pitch": 68, "velocity": 85},
        ]

        updated, count, metrics = InterventionExecutor.apply_piano_performative_rearticulation(
            notes=notes,
            start_bar=20,
            end_bar=28,
            bpm=90.0
        )

        assert count == 3  # Only the 3 notes in bar 22 were modified!
        # Check that bar 10 notes are identical
        bar_10_notes = [n for n in updated if n["start_time"] == 36.0]
        assert len(bar_10_notes) == 3
        for n in bar_10_notes:
            assert n["velocity"] == 85

        # Check that bar 22 notes have strum spread and velocity contour
        bar_22_notes = [n for n in updated if float(n["start_time"]) >= 84.0]
        assert len(bar_22_notes) == 3
        # Notes should have spread start_time
        start_times = [float(n["start_time"]) for n in bar_22_notes]
        assert start_times[0] < start_times[1] < start_times[2]
        # Pitches must be 100% preserved
        pitches = [n["pitch"] for n in bar_22_notes]
        assert pitches == [54, 61, 68]

    def test_execute_proposal_records_decision_and_updates_musical_memory(self):
        contract = SongContract.scaffold_from_session_state({"bpm": 90.0, "key": "F#", "scale": "minor"})
        decision_ledger = CreativeDecisionLedger()

        proposals = CreativeProposalEngine.generate_proposals({"bpm": 90.0, "key": "F#", "scale": "minor"})
        p1 = proposals[0]

        # 4 notes in bar 20
        test_notes = [
            {"start_time": 76.0, "pitch": 54, "velocity": 85},
            {"start_time": 76.0, "pitch": 61, "velocity": 85},
            {"start_time": 76.0, "pitch": 65, "velocity": 85},
            {"start_time": 76.0, "pitch": 68, "velocity": 85},
        ]

        result = InterventionExecutor.execute_proposal(
            proposal=p1,
            notes=test_notes,
            conn=None,
            contract=contract,
            decision_ledger=decision_ledger
        )

        assert result["status"] == "INTERVENTION_EXECUTED"
        assert result["modified_notes_count"] == 4

        # Verify decision recorded in CreativeDecisionLedger
        assert len(decision_ledger.decisions) == 1
        record = list(decision_ledger.decisions.values())[0]
        assert record.target_element == "Emotional Piano"
        assert record.verdict == DecisionVerdict.DELIBERATE_RETURN

        # Verify narrative milestone in MusicalMemory
        milestone = contract.musical_memory.get_milestone(f"INTERVENTION_{p1.id}")
        assert milestone is not None
        assert "expressive live performer" in milestone.what_it_means_now

        # Verify re-audit verdict
        re_audit = result["re_audit"]
        assert "EXITOSO" in re_audit["verdict"]
        assert "100% PRESERVED" in re_audit["preserved_invariants"]["harmonic_integrity"]

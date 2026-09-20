# tests/test_song_contract_and_omissions.py
"""
Test Suite: SongContract, EvidenceLedger, SongIntentMemory, and OmissionAudit.
Verifies the tripartite obligation lifecycle, cross-phase persistence, physical evidence
verification, hard phase omission gatekeepers, and creative continuity checks.
"""
import pytest
from unittest.mock import MagicMock
from engine.production.contract import (
    SongContract,
    TripartiteObligation,
    ObligationCategory,
    ObligationStatus,
    SongIntentMemory,
    EmotionalAxis,
    SonicThesis,
    EvidenceLedger,
    OmissionAuditor,
    OmissionReport,
)


class TestSongContractTripartiteDiscipline:
    """Verifies that Intent, Implementation, and Evidence remain strictly decoupled."""

    def test_obligation_lifecycle(self):
        ob = TripartiteObligation(
            id="KICK_COMPOSITION",
            title="Arrangement Kick Pattern",
            category=ObligationCategory.PRODUCTION,
            due_phase="PHASE_6_COMPOSITION",
            is_critical=True,
            intent={"pocket": "unquantized_boom_bap", "bars": 64}
        )
        assert ob.status == ObligationStatus.PENDING
        assert ob.evidence == {}

        # 1. State generated in memory
        ob.mark_implemented({"notes_count": 121, "clips_scheduled": 6})
        assert ob.status == ObligationStatus.IMPLEMENTED
        assert ob.implementation["notes_count"] == 121

        # 2. Evidence queried from DAW
        evidence_lom = {"clip_count": 6, "first_clip_beat": 0.0, "track_name": "[KICK] 808 Core Kit"}
        ob.mark_verified(evidence_lom)
        assert ob.status == ObligationStatus.VERIFIED
        assert ob.evidence == evidence_lom
        assert ob.last_verified_at is not None

    def test_serialization_and_deserialization(self):
        contract = SongContract(
            song_id="tyler_track_01",
            title="Tyler Neo Soul F# Minor",
            intent_memory=SongIntentMemory.create_for_style(genre="rap/neo-soul", artist="Tyler, The Creator", key="F#", scale="minor", bpm=90.0)
        )
        ob = contract.register_obligation(
            id="BASS_SUB_GLIDES",
            title="808 Sub Glides in Chorus",
            category=ObligationCategory.PRODUCTION,
            due_phase="PHASE_6_COMPOSITION",
            is_critical=True,
            intent={"glide_notes": 8}
        )
        ob.mark_implemented({"glide_pitches": [30, 42]})
        ob.mark_verified({"glides_active": True})

        d = contract.to_dict()
        restored = SongContract.from_dict(d)

        assert restored.song_id == "tyler_track_01"
        assert restored.title == "Tyler Neo Soul F# Minor"
        assert "BASS_SUB_GLIDES" in restored.obligations
        restored_ob = restored.obligations["BASS_SUB_GLIDES"]
        assert restored_ob.status == ObligationStatus.VERIFIED
        assert restored_ob.implementation["glide_pitches"] == [30, 42]
        assert restored_ob.intent["glide_notes"] == 8


class TestSongIntentMemory:
    """Verifies creative continuity, aesthetic anchors, and forbidden drift detection."""

    def test_forbidden_drift_detection(self):
        intent = SongIntentMemory.create_for_style("rap/neo-soul", "Tyler, The Creator")
        
        # Safe description
        warnings_safe = intent.check_forbidden_drift("Añadir compresión analógica y saturación cálida en los teclados")
        assert len(warnings_safe) == 0

        # Unsafe description with EDM clichés
        warnings_drift = intent.check_forbidden_drift("Insertar un white noise riser de 16 compases para crear un edm build")
        assert len(warnings_drift) >= 1
        assert any("EDM" in w for w in warnings_drift)

    def test_emotional_axis_mapping(self):
        axis = EmotionalAxis(start="intimate", middle="uneasy", peak="expansive", ending="unresolved")
        assert axis.get_for_section("Intro") == "intimate"
        assert axis.get_for_section("Verse 1") == "intimate"
        assert axis.get_for_section("Bridge") == "uneasy"
        assert axis.get_for_section("Hook 3") == "expansive"
        assert axis.get_for_section("Outro") == "unresolved"


class TestOmissionAuditAndGating:
    """Simulates the real production scenario where Kick was forgotten after a failure."""

    def test_kick_failure_scenario_hard_blocks_phase_transition(self):
        session_data = {
            "key": "F#",
            "scale": "minor",
            "bpm": 90.0,
            "genre": "rap/neo-soul",
            "tracks": [
                {
                    "index": 1,
                    "name": "Kick",
                    "role": "KICK",
                    "deployment_failed": True,
                    "deployment_error": "Silent track error",
                    "notes_count": 0
                },
                {
                    "index": 2,
                    "name": "Drums",
                    "role": "DRUMS",
                    "deployment_failed": False,
                    "notes_count": 80
                }
            ],
            "sections": [
                {"name": "Intro", "bars": 4, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 4}
            ]
        }
        contract = SongContract.scaffold_from_session_state(session_data)

        # Mock connection where Kick has 0 clips
        conn = MagicMock()
        def mock_send(cmd, params=None):
            params = params or {}
            if cmd == "get_session_info":
                return {"tempo": 90.0, "track_count": 5}
            if cmd == "get_cue_points":
                return {"cue_points": [{"name": "Intro", "time": 0.0}, {"name": "Verse 1", "time": 16.0}]}
            if cmd == "get_track_info":
                t_idx = params.get("track_index", 0)
                return {"index": t_idx, "name": f"Track {t_idx}", "devices": [{"name": "808 Core Kit", "class_name": "DrumGroupDevice"}]}
            if cmd == "get_arrangement_clips":
                t_idx = params.get("track_index", 0)
                if t_idx == 1:
                    return {"track_index": 1, "clips": []}  # 0 clips on Kick!
                return {"track_index": 2, "clips": [{"start_time": 16.0, "length": 64.0}]}
            return {}

        conn.send_command.side_effect = mock_send

        # Execute omission audit for Phase 6
        report = OmissionAuditor.audit_phase_readiness(contract, session_data, conn, "PHASE_6_COMPOSITION")

        # Must be HARD-BLOCKED!
        assert report.can_advance is False
        assert report.failed_count >= 1
        assert "Kick" in str(report.failed_obligations) or "COMPOSITION_1_KICK" in str(report.failed_obligations)
        assert report.block_reason is not None
        assert "bloqueada" in report.block_reason.lower() or "fallida" in report.block_reason.lower()

        # Markdown report must contain the failure warning
        md = report.format_markdown_report()
        assert "BLOQUEO POR OMISIÓN" in md
        assert "Obligaciones Fallidas" in md

    def test_repaired_kick_permits_phase_advance(self):
        session_data = {
            "key": "F#",
            "scale": "minor",
            "bpm": 90.0,
            "genre": "rap/neo-soul",
            "tracks": [
                {
                    "index": 1,
                    "name": "Kick",
                    "role": "KICK",
                    "deployment_failed": False,
                    "notes_count": 121,
                    "sculpted_parameters": {"FILTER_CUTOFF": 0.65}
                }
            ],
            "sections": [
                {"name": "Intro", "bars": 4, "start_bar": 0}
            ]
        }
        contract = SongContract.scaffold_from_session_state(session_data)

        # Mock connection where Kick has verified clips
        conn = MagicMock()
        def mock_send(cmd, params=None):
            params = params or {}
            if cmd == "get_session_info":
                return {"tempo": 90.0, "track_count": 2}
            if cmd == "get_cue_points":
                return {"cue_points": [{"name": "Intro", "time": 0.0}]}
            if cmd == "get_track_info":
                return {"index": 1, "name": "Kick", "devices": [{"name": "808 Core Kit", "class_name": "DrumGroupDevice"}]}
            if cmd == "get_arrangement_clips":
                return {"track_index": 1, "clips": [{"start_time": 0.0, "length": 16.0}]}
            return {}

        conn.send_command.side_effect = mock_send

        # Audit phase 6
        report = OmissionAuditor.audit_phase_readiness(contract, session_data, conn, "PHASE_6_COMPOSITION")

        # All critical obligations up to Phase 6 satisfied
        assert report.can_advance is True
        assert report.failed_count == 0
        md = report.format_markdown_report()
        assert "PASS: LISTO PARA AVANZAR" in md


class TestCopilotGuidedSessionContractCommands:
    """Verifies conversational query dispatch in CopilotGuidedSession."""

    def test_contract_query_dispatch(self):
        from engine.production.copilot.guided_session import CopilotGuidedSession
        session = CopilotGuidedSession()
        
        # Test "ver contrato"
        res_contract = session.step(conn=None, user_input="ver contrato")
        assert res_contract.get("status") == "SONG_CONTRACT_SUMMARY"
        assert "Contrato de Producción" in res_contract.get("message", "")

        # Test "intencion creativa"
        res_intent = session.step(conn=None, user_input="intencion creativa")
        assert res_intent.get("status") == "SONG_INTENT_SUMMARY"
        assert "Tesis Sonora" in res_intent.get("message", "")

        # Test "auditoria de omisiones"
        res_omission = session.step(conn=None, user_input="auditoria de omisiones")
        assert res_omission.get("status") == "OMISSION_AUDIT_COMPLETED"
        assert "Auditoría de Omisiones" in res_omission.get("message", "")

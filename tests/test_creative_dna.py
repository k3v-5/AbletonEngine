import pytest
from unittest.mock import MagicMock
from engine.creative.models import (
    SongCreativeDNA,
    SonicWorld,
    AestheticMood,
    ReferenceProfile,
    HarmonicDNA,
    ModalFlavor,
    TrackRoleAllocation,
    ArrangementBlueprint,
    ArrangementSectionBlueprint
)
from engine.creative.dna_engine import CreativeDirectionEngine
from engine.production.copilot.stepper import ExecutiveCopilotEngine
from engine.production.copilot.models import ProductionPhase


class TestCreativeDNAModels:
    def test_sonic_world_defaults(self):
        sw = SonicWorld()
        assert sw.mood == AestheticMood.NEO_SOUL_GROOVE
        assert sw.harmonic_warmth == 0.70
        assert sw.foley_texture == "vinyl_dust"

    def test_harmonic_dna_defaults(self):
        hd = HarmonicDNA()
        assert hd.key_root == "F"
        assert hd.scale == "natural_minor"
        assert ModalFlavor.DORIAN in hd.secondary_modes
        assert hd.allow_modal_interchange is True

    def test_song_creative_dna_serialization(self):
        dna = CreativeDirectionEngine.formulate_creative_brief(
            title="Bones Groove Pt 3",
            artist="Tyler & JID Tribute",
            genre="hip_hop_neo_soul"
        )
        data = dna.to_dict()
        assert data["title"] == "Bones Groove Pt 3"
        assert data["artist"] == "Tyler & JID Tribute"
        assert data["genre"] == "hip_hop_neo_soul"
        assert "sonic_world" in data
        assert "reference_profile" in data
        assert "harmonic_dna" in data
        assert "track_scaffold" in data
        assert len(data["track_scaffold"]) == 8
        assert "arrangement_blueprint" in data
        assert data["arrangement_blueprint"]["total_bars"] == 96
        assert len(data["arrangement_blueprint"]["sections"]) == 8


class TestCreativeDirectionEngine:
    def test_get_available_reference_profiles(self):
        profiles = CreativeDirectionEngine.get_available_reference_profiles()
        assert "tyler_jid_neo_soul_trap" in profiles
        assert "atlanta_dark_trap" in profiles
        assert "melodic_neo_soul" in profiles
        assert profiles["tyler_jid_neo_soul_trap"]["groove_signature"] == "dilla_swing"

    def test_build_default_track_scaffold(self):
        scaffold = CreativeDirectionEngine.build_default_track_scaffold()
        assert len(scaffold) == 8
        roles = [t.role for t in scaffold]
        assert "KICK" in roles
        assert "BASS" in roles
        assert "SNARE" in roles
        assert "HATS" in roles
        assert "CHORDS" in roles
        assert "LEAD" in roles
        assert "VOCAL_HOOK" in roles
        assert "FOLEY" in roles

        # Verify frequency reservations exist
        for t in scaffold:
            assert len(t.frequency_reservation) > 0
            assert t.track_color.startswith("#")

    def test_build_default_arrangement_blueprint(self):
        arr = CreativeDirectionEngine.build_default_arrangement_blueprint(total_bars=96, tempo_bpm=142.0)
        assert arr.total_bars == 96
        assert arr.tempo_bpm == 142.0
        assert len(arr.sections) == 8
        assert arr.sections[0].name == "Intro"
        assert arr.sections[-1].name == "Outro"
        assert arr.sections[3].name == "Chorus"
        assert arr.sections[3].target_energy == 0.90
        assert arr.sections[6].name == "Final Chorus"
        assert arr.sections[6].target_energy == 1.00

    def test_scaffold_live_project_mock(self):
        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = lambda cmd, args: {
            "status": "success",
            "result": {"track_count": 0, "tracks": []}
        }

        dna = CreativeDirectionEngine.formulate_creative_brief(
            title="Test Track",
            artist="Test Artist",
            genre="trap"
        )
        res = CreativeDirectionEngine.scaffold_live_project(mock_conn, dna, create_cues=True)

        assert res["status"] == "SUCCESS"
        assert len(res["tracks_created"]) == 8
        assert len(res["cues_created"]) == 8
        assert mock_conn.send_command.called


class TestCopilotPhase1Integration:
    def test_copilot_discovers_phase1_decisions(self):
        copilot = ExecutiveCopilotEngine()
        # Mock empty session (0 tracks)
        state = copilot.inspect_session(conn=None, tracks=[])

        decision_ids = [d.id for d in state.pending_decisions]
        assert "DEC-P1-01-CREATIVE-MOOD" in decision_ids
        assert "DEC-P1-02-HARMONIC-DNA" in decision_ids
        assert "DEC-P1-03-TRACK-SCAFFOLD" in decision_ids
        assert "DEC-P1-04-ENERGY-ROADMAP" in decision_ids

        for d in state.pending_decisions:
            if d.id.startswith("DEC-P1"):
                assert d.phase == ProductionPhase.PHASE_1_DNA
                assert len(d.action_tool) > 0

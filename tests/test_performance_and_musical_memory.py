# tests/test_performance_and_musical_memory.py
"""
Test Suite for Performance Character (Level E), Interaction Consequence (Level F),
Timing Methodology Separation, and Musical Narrative Memory.
"""
import pytest
from engine.production.contract.performance_character import (
    PerformanceAuditor,
    TimingIntention,
    VelocityExpression,
    ChordArticulation,
    TrackPerformanceProfile,
)
from engine.production.contract.interaction_audit import (
    InteractionAuditor,
    InteractionPosture,
    SpaceYieldingDiagnostic,
    RhythmicInterlockingDiagnostic,
)
from engine.production.contract.musical_memory import (
    MusicalMemory,
    NarrativeMilestone,
)
from engine.production.contract.creative_xray import CreativeXRay
from engine.production.contract.song_contract import SongContract


class TestTimingMethodologyAndPerformanceCharacter:
    """Verifies that Level E audit differentiates timing layers and avoids coercive scoring."""

    def test_grid_snapped_drum_audit(self):
        # 16 notes snapped exactly to 1/16 beats (0.0, 0.25, 0.5, 0.75...)
        notes = [{"start_time": i * 0.25, "pitch": 36, "velocity": 95} for i in range(16)]
        profile = PerformanceAuditor.audit_track(
            track_index=0,
            track_name="Boom Bap Kit",
            role="drums",
            notes=notes,
            assigned_groove=None,
            groove_amount=0.0
        )
        assert profile.methodology.midi_grid_snap_pct >= 99.0
        assert profile.timing_intention == TimingIntention.MACHINE_LOCKED
        assert profile.velocity_expression == VelocityExpression.MECHANICAL_FLAT
        assert "rejilla matemática" in profile.artistic_dilemma
        assert "MPC/SP-1200" in profile.artistic_dilemma

    def test_ableton_groove_pool_separation(self):
        # Even if MIDI notes are visually at 0.0, an assigned Ableton Groove must be recognized
        notes = [{"start_time": i * 0.25, "pitch": 38, "velocity": 90} for i in range(8)]
        profile = PerformanceAuditor.audit_track(
            track_index=1,
            track_name="Live Hats",
            role="drums",
            notes=notes,
            assigned_groove="MPC 16 Swing-65.agr",
            groove_amount=0.65
        )
        assert profile.methodology.assigned_groove == "MPC 16 Swing-65.agr"
        assert profile.methodology.groove_amount == 0.65
        assert profile.timing_intention == TimingIntention.GROOVE_MAPPED

    def test_velocity_expression_piano_phrased(self):
        # Highly phrased dynamic contour (velocities between 45 and 110)
        notes = [
            {"start_time": 0.0, "pitch": 60, "velocity": 45},
            {"start_time": 1.0, "pitch": 64, "velocity": 75},
            {"start_time": 2.0, "pitch": 67, "velocity": 95},
            {"start_time": 3.0, "pitch": 71, "velocity": 110},
        ]
        profile = PerformanceAuditor.audit_track(
            track_index=3,
            track_name="Emotional Piano",
            role="keys",
            notes=notes
        )
        assert profile.velocity_expression == VelocityExpression.CONTOUR_PHRASED
        assert profile.velocity_std >= 12.0

    def test_strings_pad_bed_classification(self):
        # Narrow velocity range typical of orchestral pad beds
        notes = [{"start_time": i * 4.0, "pitch": 55, "velocity": 74} for i in range(4)]
        profile = PerformanceAuditor.audit_track(
            track_index=4,
            track_name="Omnisphere Strings",
            role="strings",
            notes=notes
        )
        assert profile.velocity_expression == VelocityExpression.PAD_BED
        assert profile.methodology.transient_profile == "SLOW_ENVELOPE"


class TestInteractionAndConsequenceAudit:
    """Verifies that Level F audits whether tracks listen to each other."""

    def test_space_yielding_dialogue(self):
        # Lead speaks in bars 0 and 2 (beats 80-84 and 88-92)
        lead_notes = [
            {"start_time": 80.5, "pitch": 72},
            {"start_time": 88.5, "pitch": 74},
        ]
        # Accompaniment yields space: 1 note during lead bars, 8 notes during free bars
        acc_notes = [
            {"start_time": 81.0, "pitch": 60},  # in lead bar
            {"start_time": 84.0, "pitch": 60},  # in free bar
            {"start_time": 85.0, "pitch": 62},  # in free bar
            {"start_time": 86.0, "pitch": 64},  # in free bar
            {"start_time": 87.0, "pitch": 65},  # in free bar
        ]
        diag = InteractionAuditor.audit_space_yielding(
            lead_track_name="Analog Lab Lead",
            lead_notes=lead_notes,
            acc_track_name="Emotional Piano",
            acc_notes=acc_notes,
            section_name="Hook 1",
            start_beat=80.0,
            end_beat=96.0
        )
        assert diag.posture == InteractionPosture.ACTIVE_DIALOGUE
        assert diag.yielding_ratio < 0.65

    def test_rhythmic_interlocking_kick_bass(self):
        # Kick strikes on beat 0 and 2
        kick_notes = [{"start_time": 0.0}, {"start_time": 2.0}]
        # Bass syncopates on beat 0.75, 1.5, 2.75 (only 1 simultaneous on 0.0)
        bass_notes = [{"start_time": 0.0}, {"start_time": 0.75}, {"start_time": 1.5}, {"start_time": 2.75}]
        diag = InteractionAuditor.audit_rhythmic_interlocking(kick_notes, bass_notes)
        assert diag.posture == InteractionPosture.INTERLOCKED_POCKET
        assert diag.syncopated_interlocks >= 2

    def test_sectional_causality_awareness(self):
        reactions = InteractionAuditor.audit_sectional_reactions({"bpm": 90})
        assert len(reactions) >= 2
        kick_silenced = [r for r in reactions if r.trigger_action == "KICK_SILENCED"][0]
        assert kick_silenced.is_causally_aware is True
        assert any("SubLab" in t for t in kick_silenced.reacting_tracks)


class TestMusicalMemoryNarrativeAxis:
    """Verifies that MusicalMemory links historical precedent, current reality, and future expectation."""

    def test_record_and_query_narrative_context(self):
        mem = MusicalMemory(song_id="test_song")
        mem.record_milestone(
            milestone_id="TEST_KICK_DROP",
            element="Kick 808",
            section="Hook 2",
            action="SILENCED",
            what_happened_before="Active in Verse 1 and Hook 1",
            what_it_means_now="Weightlessness and harmonic expansion",
            what_could_happen_next="Prepares total vacuum in Bridge",
            interdependent_reactions=["SubLab carried bass alone"],
            artistic_intent="Dynamic tension"
        )

        queried = mem.query_narrative_context("Kick", "Hook 2")
        assert queried is not None
        assert queried.action == "SILENCED"
        assert "Weightlessness" in queried.what_it_means_now
        assert "Bridge" in queried.what_could_happen_next

    def test_serialization_cycle(self):
        scaffold = MusicalMemory.scaffold_for_neo_soul("neo_soul_42")
        d = scaffold.to_dict()
        restored = MusicalMemory.from_dict(d)
        assert restored.song_id == "neo_soul_42"
        assert len(restored.milestones) == 3
        m_hook3 = restored.get_milestone("HOOK_3_RETURN")
        assert m_hook3 is not None
        assert "16 compases" in m_hook3.what_happened_before


class TestFullCreativeXRayIntegration:
    """Verifies that CreativeXRay synthesizes all 6 levels into a unified perceptual mirror."""

    def test_xray_output_contains_levels_e_f_and_musical_memory(self):
        session_data = {
            "genre": "rap/neo-soul",
            "key": "F#",
            "scale": "minor",
            "bpm": 90.0,
            "tracks": [
                {"index": 0, "name": "Boom Bap Kit", "role": "drums", "notes": [{"start_time": 0.0, "velocity": 90}]},
                {"index": 1, "name": "SubLab XL", "role": "bass", "notes": [{"start_time": 0.5, "velocity": 95}]},
                {"index": 2, "name": "Emotional Piano", "role": "keys", "notes": [{"start_time": 0.0, "velocity": 85}]},
            ],
            "sections": [
                {"name": "Verse 1", "bars": 16, "start_bar": 0},
                {"name": "Hook 1", "bars": 8, "start_bar": 16},
            ]
        }
        contract = SongContract.scaffold_from_session_state(session_data)
        xray = CreativeXRay.generate_xray(session_data, contract=contract)

        md = xray["markdown_report"]
        assert "NIVEL E: CARÁCTER INTERPRETATIVO" in md
        assert "NIVEL F: INTERACCIÓN Y CAUSALIDAD" in md
        assert "MEMORIA MUSICAL NARRATIVA" in md
        assert "performance_character" in xray
        assert "interaction_consequence" in xray
        assert "musical_memory" in xray

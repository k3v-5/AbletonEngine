"""
Test Suite: Live Creative Controller, Reversible Actuation, and Online Validation Monitor (Fase 7)
Verifies:
1. Shadow mode passive observation without Live mutation.
2. Limited actuation with decision_id and TransactionGuard snapshots.
3. Transactional rollback upon degraded coherence/identity feeding CreativeRegretTracker.
4. Telemetry feeding Yield, Mechanism Interaction Graph, and Innovation Half-Life.
5. OnlineValidationMonitor computing HHI, rollback rate, and simulation-reality gap (JSD).
6. Full integration with CopilotGuidedSession via conversational NLP commands.
"""

import pytest
from unittest.mock import MagicMock

from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.creative.corpus_territory import CorpusTerritory
from engine.creative.creative_yield import CreativeYieldTracker
from engine.creative.mechanism_interaction_graph import MechanismInteractionGraph
from engine.creative.creative_regret import CreativeRegretTracker
from engine.creative.innovation_half_life import InnovationHalfLifeTracker
from engine.creative.online_validation_monitor import OnlineValidationMonitor
from engine.creative.live_creative_controller import LiveCreativeController, OperationalMode
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.sound.timbre_dna import TimbreDNA


@pytest.fixture
def mock_conn():
    return MockAbletonAdapter()


@pytest.fixture
def clean_controller():
    territory = CorpusTerritory(storage_path="")
    territory.clear()
    yield_tracker = CreativeYieldTracker(storage_path="")
    interaction_graph = MechanismInteractionGraph(storage_path="")
    regret_tracker = CreativeRegretTracker(storage_path="")
    lifecycle_tracker = InnovationHalfLifeTracker(storage_path="")
    monitor = OnlineValidationMonitor()

    return LiveCreativeController(
        territory=territory,
        yield_tracker=yield_tracker,
        interaction_graph=interaction_graph,
        regret_tracker=regret_tracker,
        lifecycle_tracker=lifecycle_tracker,
        monitor=monitor,
        default_mode=OperationalMode.SHADOW
    )


@pytest.fixture
def sample_session_data():
    return {
        "name": "LiveSession_01",
        "genre": "melodic_techno",
        "bpm": 124.0,
        "tonal_center": "F#",
        "mode": "Minor",
        "tracks": [
            {"role": "LEAD", "name": "Lead Synth", "timbre_dna": TimbreDNA(brightness=0.65, roughness=0.35).to_dict()},
            {"role": "DRUMS", "name": "Drum Kit", "notes_count": 32},
            {"role": "BASS", "name": "Rolling Bass", "timbre_dna": TimbreDNA(brightness=0.30, roughness=0.50).to_dict()},
            {"role": "TEXTURE_FOLEY", "name": "Foley Bed"}
        ],
        "spatial_energy_curve": [{"stereo_width": 0.20}, {"stereo_width": 1.25}],
        "sections": [
            {"name": "intro", "bars": 8, "energy": 0.3},
            {"name": "drop", "bars": 16, "energy": 0.9, "is_pre_drop_transition": True}
        ],
        "applied_mechanisms": ["polyrhythm_3_16", "foley_texture"]
    }


class TestShadowModeAndObservation:
    def test_shadow_mode_computes_metrics_without_mutating_live(self, clean_controller, sample_session_data, mock_conn):
        assert clean_controller.mode == OperationalMode.SHADOW

        # Record shadow observation
        obs = clean_controller.record_shadow_observation(
            sample_session_data,
            actual_action="MANUAL_CHORD_RECORDED",
            conn=mock_conn
        )

        assert obs["operational_mode"] == "SHADOW"
        assert "decision_id" in obs
        assert obs["decision_id"].startswith("dec_shadow_")
        assert "governor_evaluation" in obs
        assert obs["governor_evaluation"]["governor_mode"] in ("EVOLVE", "EXPLORE", "ANCHOR")
        assert len(clean_controller.shadow_observations) == 1

        # Verify monitor was updated with shadow record
        assert clean_controller.monitor.total_actuations == 1
        assert clean_controller.monitor.rollbacks_count == 0


class TestLimitedActuationAndTransactionalRollback:
    def test_limited_actuation_applies_low_risk_mutation_with_decision_id(self, clean_controller, sample_session_data, mock_conn):
        clean_controller.set_mode("LIMITED_ACTUATION")
        assert clean_controller.mode == OperationalMode.LIMITED_ACTUATION

        session_mock = type("MockSession", (), {"data": dict(sample_session_data)})()

        def successful_mutation(sess, conn):
            # Improves contrast without degrading identity
            sess.data["tracks"][0]["timbre_dna"]["brightness"] = 0.72
            return {"applied": "timbre_brightness_lift"}

        res = clean_controller.execute_limited_actuation(
            session=session_mock,
            conn=mock_conn,
            candidate_key="A",
            techniques_to_apply=["polyrhythm_3_16", "foley_texture"],
            mutation_callback=successful_mutation
        )

        assert res["status"] == "ACTUATION_COMMITTED"
        assert res["decision_id"].startswith("dec_live_")
        assert res["delta"] >= -0.01
        assert len(clean_controller.decision_history) == 1

        # Learning subsystems updated
        rec = clean_controller.yield_tracker.records.get("polyrhythm_3_16")
        assert rec is not None
        assert rec.total_invocations >= 1
        assert clean_controller.regret_tracker.get_regret_rate() == 0.0

    def test_transactional_rollback_on_degraded_coherence(self, clean_controller, sample_session_data, mock_conn):
        clean_controller.set_mode("LIMITED_ACTUATION")

        session_mock = type("MockSession", (), {"data": dict(sample_session_data), "_save_state": MagicMock()})()

        def destructive_mutation(sess, conn):
            # Breaks identity and coherence drastically
            sess.data["tracks"] = []
            sess.data["sections"] = []
            return {"applied": "wipe_tracks"}

        res = clean_controller.execute_limited_actuation(
            session=session_mock,
            conn=mock_conn,
            candidate_key="E",
            techniques_to_apply=["destructive_chaos_glitch"],
            mutation_callback=destructive_mutation
        )

        assert res["status"] == "ACTUATION_ROLLED_BACK_BY_GUARDRAIL"
        assert res["decision_id"].startswith("dec_live_")
        assert "destructive_chaos_glitch" in res["techniques_rejected"]
        assert res["rollback"]["rolled_back"] is True

        # Regret tracker recorded the failed intervention!
        assert clean_controller.regret_tracker.get_regret_rate("destructive_chaos_glitch") == 1.0
        assert len(clean_controller.regret_tracker.events) == 1


class TestOnlineValidationMonitor:
    def test_monitor_computes_hhi_and_simulation_gap(self):
        monitor = OnlineValidationMonitor()

        # Simulate a realistic distribution: mostly EVOLVE, some EXPLORE, rare ANCHOR
        techniques = ["foley_texture", "polyrhythm_3_16", "sub_glide", "stereo_widening", "pre_drop_vacuum"]
        for i in range(100):
            mode = "EVOLVE" if i < 65 else ("EXPLORE" if i < 98 else "ANCHOR")
            tech = techniques[i % len(techniques)]
            is_rb = (i == 42 or i == 87)
            monitor.record_decision(
                decision_id=f"dec_{i}",
                mode=mode,
                techniques_applied=[tech],
                was_rolled_back=is_rb,
                delta_score=-0.1 if is_rb else 0.05
            )

        hhi = monitor.calculate_herfindahl_index()
        assert hhi < 0.22  # Balanced distribution across 5 techniques
        assert monitor.get_rollback_rate() == 0.02

        gap_jsd = monitor.calculate_simulation_reality_gap()
        assert gap_jsd < 0.05  # Very close to simulated benchmark (65% EVOLVE / 34% EXPLORE / 1% ANCHOR)

        rep = monitor.generate_report()
        assert rep["status"] == "ONLINE_MONITOR_HEALTHY"
        assert rep["total_actuations"] == 100
        assert rep["is_monopoly_risk"] is False


class TestMemoryCommitAndLifecycles:
    def test_commit_session_to_memory(self, clean_controller, sample_session_data):
        pt = clean_controller.commit_session_to_memory(sample_session_data, auto_save=False)
        assert isinstance(pt.session_id, str)
        assert len(clean_controller.territory.points) == 1
        assert "polyrhythm_3_16" in clean_controller.lifecycle_tracker.lifecycles

        dash = clean_controller.get_telemetry_dashboard()
        assert dash["corpus_territory_total_songs"] == 1
        assert dash["active_clusters_count"] >= 1


class TestGuidedSessionIntegration:
    def test_guided_session_nlp_commands(self, mock_conn):
        session = CopilotGuidedSession()
        session.reset()

        # 1. Switch to Shadow Mode via NLP
        res_shadow = session.step(conn=mock_conn, user_input="activar modo sombra")
        assert res_shadow["status"] == "CREATIVE_MODE_UPDATED"
        assert res_shadow["mode"] == "SHADOW"
        assert "Modo Sombra Activado" in res_shadow["message"]

        # 2. Switch to Limited Actuation via NLP
        res_act = session.step(conn=mock_conn, user_input="actuacion limitada")
        assert res_act["status"] == "CREATIVE_MODE_UPDATED"
        assert res_act["mode"] == "LIMITED_ACTUATION"
        assert "Actuación Limitada Activada" in res_act["message"]

        # 3. Request Creative Telemetry Audit via NLP
        res_audit = session.step(conn=mock_conn, user_input="auditoria creativa")
        assert res_audit["status"] == "CREATIVE_AUDIT_COMPLETED"
        assert "Auditoría Creativa Online" in res_audit["message"]
        assert "Índice HHI" in res_audit["message"]
        assert "Brecha Simulación-Realidad" in res_audit["message"]

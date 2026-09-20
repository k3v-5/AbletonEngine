"""
Test Suite: Fase 6 — Creative Validation, Ablation & Long-Horizon Dynamics
Verifies:
1. Innovation Half-Life Tracker (Lifecycle states, saturation, fallow periods, resurgence)
2. Creative Ablation Harness (Entropy, Jensen-Shannon divergence, causal impact)
3. Long-Horizon Simulator (Vectorized headless simulation, Herfindahl index, meta-cliche detection)
4. Seed Invariance Auditor (Path-dependency, hysteresis, escape velocity from initial bias)
"""

import pytest
from engine.creative.innovation_half_life import InnovationHalfLifeTracker, TechniqueLifecycle
from engine.creative.creative_ablation import (
    CreativeAblationHarness, AblationConfig, calculate_shannon_entropy,
    calculate_jensen_shannon_divergence
)
from engine.creative.long_horizon_simulator import LongHorizonSimulator
from engine.creative.seed_invariance import SeedInvarianceAuditor


# ==============================================================================
# 1. Innovation Half-Life Tests
# ==============================================================================

class TestInnovationHalfLife:
    def test_record_session_and_lifecycle(self):
        tracker = InnovationHalfLifeTracker(storage_path="")
        for i in range(5):
            tracker.record_session(session_index=i + 1, techniques_applied=["foley_texture"], yields={"foley_texture": 0.85})

        lc = tracker.lifecycles.get("foley_texture")
        assert lc is not None
        assert lc.total_usages == 5
        assert lc.average_yield == 0.85
        assert lc.peak_session > 0

    def test_saturation_and_quarantine(self):
        tracker = InnovationHalfLifeTracker(storage_path="")
        # Apply technique heavily across 25 sessions with declining yield
        for i in range(25):
            tracker.record_session(session_index=i + 1, techniques_applied=["overused_flanger"], yields={"overused_flanger": 0.20})

        lc = tracker.lifecycles.get("overused_flanger")
        assert lc.current_status == "SATURATING"
        assert lc.saturation_session is not None
        assert tracker.should_quarantine("overused_flanger") is True

    def test_dormancy_and_resurgence(self):
        tracker = InnovationHalfLifeTracker(storage_path="", fallow_period=10)
        # 1. Settle in saturation
        for i in range(20):
            tracker.record_session(session_index=i + 1, techniques_applied=["acid_lead"], yields={"acid_lead": 0.25})

        # 2. Rest technique for 15 sessions (only apply other techniques)
        for i in range(20, 36):
            tracker.record_session(session_index=i + 1, techniques_applied=["organic_shaker"])

        lc = tracker.lifecycles.get("acid_lead")
        assert lc.current_status == "DORMANT"
        assert tracker.is_eligible_for_resurgence("acid_lead") is True

        # 3. Re-introduce after dormancy
        tracker.record_session(session_index=37, techniques_applied=["acid_lead"], yields={"acid_lead": 0.90})
        assert lc.current_status == "RESURGENT"
        assert len(lc.resurgence_sessions) == 1

    def test_half_life_calculation(self):
        lc = TechniqueLifecycle(
            technique_name="test_tech",
            peak_session=10,
            peak_frequency=0.60,
            occurrences=[1, 2, 5, 8, 9, 10, 11, 15, 25, 40]
        )
        # Occurrences thin out dramatically after session 10
        hl = lc.half_life_sessions
        assert hl is not None
        assert hl > 0


# ==============================================================================
# 2. Creative Ablation Harness Tests
# ==============================================================================

class TestCreativeAblation:
    def test_entropy_and_js_divergence_math(self):
        # Uniform distribution should have max entropy (~1.0)
        uniform_counts = {f"t_{i}": 10 for i in range(10)}
        h_uniform = calculate_shannon_entropy(uniform_counts)
        assert 0.98 <= h_uniform <= 1.0

        # Monopoly distribution should have lower entropy
        monopoly_counts = {"t_0": 90, "t_1": 5, "t_2": 5}
        h_monopoly = calculate_shannon_entropy(monopoly_counts)
        assert h_monopoly < 0.60

        # Identical distributions have JSD = 0
        dist_a = {"t1": 0.5, "t2": 0.5}
        assert calculate_jensen_shannon_divergence(dist_a, dist_a) == 0.0

        # Completely disjoint distributions have JSD > 0.80
        dist_b = {"t3": 0.5, "t4": 0.5}
        assert calculate_jensen_shannon_divergence(dist_a, dist_b) > 0.80

    def test_run_cohort_ablation(self):
        res_baseline = CreativeAblationHarness.run_cohort(AblationConfig("BASELINE"), count=15, base_seed=42)
        assert res_baseline.total_sessions == 15
        assert res_baseline.shannon_entropy > 0.70
        assert res_baseline.average_territorial_dispersion > 0.0

    def test_full_ablation_study(self):
        study = CreativeAblationHarness.run_ablation_study(cohort_size=15, base_seed=42)
        assert study["status"] == "ABLATION_STUDY_COMPLETED"
        assert study["total_conditions_tested"] == 7
        assert len(study["comparisons"]) == 7
        verdicts = [c["causal_verdict"] for c in study["comparisons"]]
        assert "BASELINE_REFERENCE" in verdicts


# ==============================================================================
# 3. Long-Horizon Simulator Tests
# ==============================================================================

class TestLongHorizonSimulator:
    def test_periodic_limit_cycle_detector(self):
        # A synthetic sequence with strict period 3
        periodic_seq = ["EXPLORE", "EVOLVE", "ANCHOR"] * 25
        is_periodic, period = LongHorizonSimulator._detect_periodic_limit_cycle(periodic_seq)
        assert is_periodic is True
        assert period == 3

        # An aperiodic / chaotic sequence
        import random
        rng = random.Random(99)
        aperiodic_seq = [rng.choice(["EXPLORE", "EVOLVE", "ANCHOR"]) for _ in range(120)]
        is_periodic_ap, _ = LongHorizonSimulator._detect_periodic_limit_cycle(aperiodic_seq)
        assert is_periodic_ap is False

    def test_long_horizon_simulation_run(self):
        sim = LongHorizonSimulator.run_simulation(n_sessions=120, window_size=40, seed=42)
        assert sim["status"] == "LONG_HORIZON_SIMULATION_COMPLETED"
        assert sim["total_sessions"] == 120
        assert sim["discovered_territories_count"] >= 2
        assert len(sim["window_snapshots"]) == 3
        for w in sim["window_snapshots"]:
            assert w["herfindahl_index"] < 0.25  # No severe monopoly
        assert sim["asymptotic_verdict"] in ("HEALTHY_OPEN_ENDED_EVOLUTION", "STABLE_MULTI_TERRITORY_ATTRACTOR")


# ==============================================================================
# 4. Seed Invariance & Path-Dependency Tests
# ==============================================================================

class TestSeedInvariance:
    def test_seed_invariance_study(self):
        invariance = SeedInvarianceAuditor.run_invariance_study(generations_per_cohort=25, base_seed=42)
        assert invariance["status"] == "SEED_INVARIANCE_AUDITED"
        assert invariance["escape_ratio_from_bias"] >= 0.50
        assert invariance["path_dependency_ratio"] <= 0.50
        assert invariance["verdict"] in ("RESILIENT_INDEPENDENCE", "MODERATE_HYSTERESIS")

"""
Tests for VerificationMatrix in PIE.
Verifies multi-variable acoustic evaluation, primary target tolerances,
and strict regression detection (True Peak, Limiter GR, Phase, Dynamic Range).
"""
from engine.production.verification import VerificationMatrix


def test_verification_matrix_success():
    vm = VerificationMatrix(max_true_peak_dbtp=-0.3, max_limiter_gr_db=2.5)

    before = {"integrated_lufs": -18.0, "true_peak_dbtp": -1.5, "limiter_gr_db": 0.0, "lra": 6.0}
    after = {"integrated_lufs": -14.2, "true_peak_dbtp": -0.5, "limiter_gr_db": 1.2, "lra": 5.5}

    expected_delta = {"integrated_lufs": 3.8}
    res = vm.evaluate(before, after, expected_delta, primary_metric="integrated_lufs", tolerance=0.5)

    assert res.passed is True
    assert res.status == "PASS"
    assert len(res.regressions) == 0
    assert res.actual_delta["integrated_lufs"] == 3.8


def test_verification_matrix_true_peak_regression():
    vm = VerificationMatrix(max_true_peak_dbtp=-0.3)

    before = {"integrated_lufs": -18.0, "true_peak_dbtp": -1.5}
    # Inter-sample clipping: True Peak is +0.1 dBTP (violates -0.3 dBTP ceiling)
    after = {"integrated_lufs": -14.0, "true_peak_dbtp": 0.1}

    expected_delta = {"integrated_lufs": 4.0}
    res = vm.evaluate(before, after, expected_delta)

    assert res.passed is False
    assert res.status == "REGRESSION"
    assert any("True Peak regression" in r for r in res.regressions)


def test_verification_matrix_limiter_gr_regression():
    vm = VerificationMatrix(max_limiter_gr_db=2.5)

    before = {"integrated_lufs": -18.0, "true_peak_dbtp": -1.5, "limiter_gr_db": 0.0}
    # Excessive gain reduction: 3.5 dB > 2.5 dB
    after = {"integrated_lufs": -14.0, "true_peak_dbtp": -0.5, "limiter_gr_db": 3.5}

    expected_delta = {"integrated_lufs": 4.0}
    res = vm.evaluate(before, after, expected_delta)

    assert res.passed is False
    assert res.status == "REGRESSION"
    assert any("Limiter GR regression" in r for r in res.regressions)


def test_verification_matrix_phase_correlation_regression():
    vm = VerificationMatrix(min_phase_correlation=0.2)

    before = {"integrated_lufs": -18.0, "phase_correlation": 0.85}
    after = {"integrated_lufs": -14.0, "phase_correlation": -0.1}  # Phase cancellation!

    expected_delta = {"integrated_lufs": 4.0}
    res = vm.evaluate(before, after, expected_delta)

    assert res.passed is False
    assert res.status == "REGRESSION"
    assert any("Phase cancellation" in r for r in res.regressions)


def test_verification_matrix_dynamic_range_collapse():
    vm = VerificationMatrix()

    before = {"integrated_lufs": -18.0, "lra": 7.0}
    after = {"integrated_lufs": -14.0, "lra": 1.2}  # Dynamic range squashed below 2 LU

    expected_delta = {"integrated_lufs": 4.0}
    res = vm.evaluate(before, after, expected_delta)

    assert res.passed is False
    assert res.status == "REGRESSION"
    assert any("Dynamic range collapse" in r for r in res.regressions)


# =====================================================================
# Document 11 VerificationEngine Comprehensive Contract Tests
# =====================================================================

import tempfile
import os
import shutil
from engine.production.verification import (
    VerificationEngine,
    VerificationVerdict,
    MetricSnapshot,
    VerificationSnapshot,
    MetricExpectation,
    RegressionRule,
    VerificationReport,
)
from engine.production.serializer import ProductionStorage


def test_doc11_01_objective_met_verified():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -17.0, "true_peak_dbtp": -1.5, "phase_correlation": 0.8})
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -0.8, "phase_correlation": 0.78})

    expectations = [
        MetricExpectation(metric_name="integrated_lufs", expected_delta=3.0, tolerance=0.5, direction="INCREASE")
    ]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.VERIFIED
    assert report.passed is True
    assert report.objective_met is True
    assert report.regression_free is True
    assert report.confidence == 1.0
    assert report.deltas["integrated_lufs"].within_expectation is True


def test_doc11_02_objective_not_met_failed():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5})
    # Target delta was +4.0, actual is +0.2 -> fails objective
    after = engine.capture_snapshot({"integrated_lufs": -17.8, "true_peak_dbtp": -1.4})

    expectations = [
        MetricExpectation(metric_name="integrated_lufs", expected_delta=4.0, tolerance=0.5, direction="INCREASE")
    ]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.FAILED
    assert report.passed is False
    assert report.objective_met is False


def test_doc11_03_critical_true_peak_regression_rollback():
    engine = VerificationEngine(max_true_peak_dbtp=-0.3)
    before = engine.capture_snapshot({"integrated_lufs": -17.0, "true_peak_dbtp": -1.2})
    # Loudness target met, but True Peak clipped into positive realm (+0.2 dBTP)
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": 0.2})

    expectations = [
        MetricExpectation(metric_name="integrated_lufs", expected_delta=3.0, tolerance=0.5, direction="INCREASE")
    ]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.ROLLBACK_REQUIRED
    assert report.passed is False
    assert any("True Peak regression" in r for r in report.reasons)


def test_doc11_04_minor_secondary_degradation_warning():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -16.0, "crest_factor_db": 12.0})
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "crest_factor_db": 10.2})

    expectations = [
        MetricExpectation(metric_name="integrated_lufs", expected_delta=2.0, tolerance=0.5, direction="INCREASE")
    ]
    warning_rules = [
        RegressionRule(metric_name="crest_factor_db", min_delta=-1.5, severity="WARNING", description="Minor dynamic loss")
    ]
    report = engine.compare(before=before, after=after, expectations=expectations, regression_rules=warning_rules)

    assert report.verdict == VerificationVerdict.VERIFIED_WITH_WARNING
    assert report.passed is True
    assert len(report.warnings) > 0


def test_doc11_05_nan_inf_metric_invalid():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -16.0, "true_peak_dbtp": float("nan")})
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -1.0})

    expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=2.0)]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.INVALID
    assert report.passed is False
    assert any("invalid" in r.lower() or "nan" in r.lower() for r in report.reasons)


def test_doc11_06_algorithm_version_mismatch_invalid():
    engine = VerificationEngine()
    m_before = {"integrated_lufs": MetricSnapshot(metric_name="integrated_lufs", value=-16.0, algorithm_version="1.0.0")}
    m_after = {"integrated_lufs": MetricSnapshot(metric_name="integrated_lufs", value=-14.0, algorithm_version="1.1.0")}

    before = VerificationSnapshot(session_fingerprint="fp1", metrics=m_before)
    after = VerificationSnapshot(session_fingerprint="fp1", metrics=m_after)

    expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=2.0)]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.INVALID
    assert any("Algorithm version mismatch" in r for r in report.reasons)


def test_doc11_07_fingerprint_mismatch_invalid():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -16.0}, session_fingerprint="fp_alpha")
    after = engine.capture_snapshot(
        {"integrated_lufs": -14.0},
        session_fingerprint="fp_beta",
        metadata={"concurrent_modification": True}
    )

    expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=2.0)]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.INVALID
    assert any("Fingerprint mismatch" in r for r in report.reasons)


def test_doc11_08_verify_rollback_success():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5, "lra": 6.0})
    # After rollback, values are restored within tolerance (±0.02)
    post_rollback = engine.capture_snapshot({"integrated_lufs": -18.02, "true_peak_dbtp": -1.51, "lra": 6.01})

    report = engine.verify_rollback(before=before, post_rollback=post_rollback, tolerance=0.1)

    assert report.verdict == VerificationVerdict.VERIFIED
    assert report.passed is True
    assert report.objective_met is True


def test_doc11_09_verify_rollback_incomplete_failure():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5})
    # Post rollback state diverges significantly (integrated_lufs still -15.0)
    post_rollback = engine.capture_snapshot({"integrated_lufs": -15.0, "true_peak_dbtp": -0.8})

    report = engine.verify_rollback(before=before, post_rollback=post_rollback, tolerance=0.1)

    assert report.verdict in (VerificationVerdict.FAILED, VerificationVerdict.ROLLBACK_REQUIRED)
    assert report.passed is False
    assert any("ROLLBACK_INCOMPLETE" in r for r in report.reasons)


def test_doc11_10_determinism_identical_reports():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5})
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -0.8})
    expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=4.0)]

    report1 = engine.compare(before=before, after=after, expectations=expectations, decision_id="dec_fixed", verification_id="ver_fixed")
    for _ in range(10):
        rep = engine.compare(before=before, after=after, expectations=expectations, decision_id="dec_fixed", verification_id="ver_fixed")
        # Ensure timestamp invariance for strict hash comparison
        object.__setattr__(rep, "created_at", report1.created_at)
        assert rep.compute_hash() == report1.compute_hash()


def test_doc11_11_multivariable_scenario_rollback():
    # Multivariable case: Intelligibility improved, BUT True Peak clips
    engine = VerificationEngine(max_true_peak_dbtp=-0.5)
    before = engine.capture_snapshot({
        "vocal_intelligibility": 0.60,
        "true_peak_dbtp": -1.2,
        "stereo_correlation": 0.85
    })
    after = engine.capture_snapshot({
        "vocal_intelligibility": 0.80, # +0.20 met!
        "true_peak_dbtp": -0.1,        # True peak exceeds -0.5 ceiling -> CRITICAL!
        "stereo_correlation": 0.80
    })

    expectations = [
        MetricExpectation(metric_name="vocal_intelligibility", expected_delta=0.20, tolerance=0.05, direction="INCREASE")
    ]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.ROLLBACK_REQUIRED
    assert report.passed is False
    assert any("True Peak" in r for r in report.reasons)


def test_doc11_12_unexpected_side_effect():
    engine = VerificationEngine()
    before = engine.capture_snapshot({
        "integrated_lufs": -18.0,
        "true_peak_dbtp": -1.5,
        "sub_bass_energy": -24.0
    })
    # Action aimed at loudness, but sub_bass_energy unexpectedly spiked +2.5 dB
    after = engine.capture_snapshot({
        "integrated_lufs": -14.0,
        "true_peak_dbtp": -0.8,
        "sub_bass_energy": -21.5
    })

    expectations = [
        MetricExpectation(metric_name="integrated_lufs", expected_delta=4.0, tolerance=0.5, direction="INCREASE")
    ]
    report = engine.compare(before=before, after=after, expectations=expectations)

    assert report.verdict == VerificationVerdict.VERIFIED_WITH_WARNING
    assert any("sub_bass_energy" in s for s in report.unexpected_side_effects)


def test_doc11_13_no_op_evaluation():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -1.0})
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -1.0})

    # Case A: Intent was STABLE / NO_OP -> VERIFIED
    exp_stable = [MetricExpectation(metric_name="integrated_lufs", expected_delta=0.0, direction="STABLE")]
    rep_a = engine.compare(before=before, after=after, expectations=exp_stable)
    assert rep_a.verdict == VerificationVerdict.VERIFIED

    # Case B: Intent required change (+3.0) -> FAILED
    exp_change = [MetricExpectation(metric_name="integrated_lufs", expected_delta=3.0, direction="INCREASE")]
    rep_b = engine.compare(before=before, after=after, expectations=exp_change)
    assert rep_b.verdict == VerificationVerdict.FAILED


def test_doc11_14_policy_integration():
    engine = VerificationEngine()
    before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5})
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -0.8})

    expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=4.0)]
    # Policy check failed externally
    report = engine.compare(before=before, after=after, expectations=expectations, policy_compliant=False)

    assert report.verdict == VerificationVerdict.FAILED
    assert report.policy_compliant is False
    assert any("Policy compliance" in r for r in report.reasons)


def test_doc11_15_loudness_profile_integration():
    engine = VerificationEngine(max_true_peak_dbtp=-0.3)
    before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5})
    # Target True Peak under default -0.3 is fine (-0.7), but under profile ceiling of -1.0 it violates
    after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -0.7})

    profile = {"target_lufs": -14.0, "tolerance_lu": 0.5, "max_true_peak_dbtp": -1.0}
    expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=4.0)]
    report = engine.compare(before=before, after=after, expectations=expectations, profile=profile)

    assert report.verdict == VerificationVerdict.ROLLBACK_REQUIRED
    assert any("profile ceiling" in r for r in report.reasons)


def test_doc11_16_serialization_roundtrip():
    temp_dir = tempfile.mkdtemp()
    try:
        storage = ProductionStorage(base_dir=temp_dir)
        engine = VerificationEngine()

        before = engine.capture_snapshot({"integrated_lufs": -18.0, "true_peak_dbtp": -1.5})
        after = engine.capture_snapshot({"integrated_lufs": -14.0, "true_peak_dbtp": -0.8})
        expectations = [MetricExpectation(metric_name="integrated_lufs", expected_delta=4.0)]

        report = engine.compare(before=before, after=after, expectations=expectations)
        saved_path = storage.save_verification(report)
        assert os.path.exists(saved_path)

        loaded_rep = storage.load_verification(report.verification_id)
        assert loaded_rep is not None
        assert loaded_rep.verification_id == report.verification_id
        assert loaded_rep.verdict == report.verdict
        assert loaded_rep.report_hash == report.report_hash
        assert loaded_rep.confidence == report.confidence
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

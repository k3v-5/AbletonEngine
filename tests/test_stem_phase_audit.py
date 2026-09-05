# tests/test_stem_phase_audit.py
import pytest
import math
from engine.audio.stem_audit import (
    PhaseCorrelationStatus,
    StemAuditor,
)


class MockConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_session_info":
            return {"tempo": 130.0, "num_tracks": 2}
        if cmd == "get_track_info":
            return {"index": params.get("track_index", 0), "name": "Test Track"}
        return {"status": "ok"}


def test_pearson_correlation_identical_and_inverted():
    # In-phase signals: rho = 1.0
    sig_a = [math.sin(2.0 * math.pi * 50.0 * (i / 48000.0)) for i in range(1000)]
    sig_b = [math.sin(2.0 * math.pi * 50.0 * (i / 48000.0)) for i in range(1000)]
    rho_identical = StemAuditor.calculate_pearson_correlation(sig_a, sig_b)
    assert pytest.approx(rho_identical, 0.01) == 1.0

    # 180 degrees inverted phase signals: rho = -1.0
    sig_inv = [-x for x in sig_a]
    rho_inverted = StemAuditor.calculate_pearson_correlation(sig_a, sig_inv)
    assert pytest.approx(rho_inverted, 0.01) == -1.0


def test_audit_stem_phase_status():
    sig_a = [math.sin(i * 0.1) for i in range(500)]
    sig_b_opp = [-math.sin(i * 0.1) for i in range(500)]

    audit_res = StemAuditor.audit_stem_phase(sig_a, sig_b_opp, "Kick", "808")
    assert audit_res["status"] == PhaseCorrelationStatus.DESTRUCTIVE_CANCEL.value
    assert "CRITICAL" in audit_res["recommendation"]


def test_stem_loudness_headroom_safe():
    # Normal peak safe signal
    samples_safe = [0.5 * math.sin(i * 0.1) for i in range(1000)]
    metric = StemAuditor.audit_stem_loudness(samples_safe, "Keys")
    assert metric.true_peak_dbtp < -1.0
    assert metric.headroom_safe is True

    # Clipping signal (peak = 1.0 -> 0.0 dBTP)
    samples_clip = [1.0 * math.sin(i * 0.1) for i in range(1000)]
    metric_clip = StemAuditor.audit_stem_loudness(samples_clip, "Loud_Keys")
    assert metric_clip.true_peak_dbtp > -0.5
    assert metric_clip.headroom_safe is False


def test_apply_stem_audit_adapter():
    conn = MockConnection()
    res = StemAuditor.apply_stem_audit_adapter(conn=conn)
    assert res["status"] == "success"
    assert res["stems_count"] > 0
    assert "audit_manifest_path" in res

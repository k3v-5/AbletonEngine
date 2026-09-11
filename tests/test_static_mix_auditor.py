# tests/test_static_mix_auditor.py
import pytest
from engine.mix.static_auditor import StaticMixAuditor

def test_static_auditor_flags_master_and_channels():
    session = {
        "project": {"master_volume": 0.96},
        "tracks": [
            {"index": 0, "name": "Kick", "volume": 0.98, "mute": False, "devices": [1, 2, 3, 4, 5, 6]},
            {"index": 1, "name": "Ghost Track", "volume": 0.0, "mute": False, "devices": [1]},
            {"index": 2, "name": "Bass", "volume": 0.75, "mute": False, "devices": [1, 2]}
        ]
    }
    report = StaticMixAuditor.audit_session(session, genre="trap")
    assert not report["passed"]
    assert "master-clipping-risk" in report["global_flags"]
    assert any("fx-heavy" in t["flags"] for t in report["flagged_tracks"])
    assert any("silent-active" in t["flags"] for t in report["flagged_tracks"])
    assert any("near-clip-fader" in t["flags"] for t in report["flagged_tracks"])

def test_static_auditor_passes_clean_session():
    clean_session = {
        "project": {"master_volume": 0.85},
        "tracks": [
            {"index": 0, "name": "Kick", "volume": 0.80, "mute": False, "devices": [1, 2, 3]},
            {"index": 1, "name": "Bass", "volume": 0.75, "mute": False, "devices": [1, 2]}
        ]
    }
    report = StaticMixAuditor.audit_session(clean_session, genre="streaming")
    assert report["passed"]
    assert len(report["flagged_tracks"]) == 0

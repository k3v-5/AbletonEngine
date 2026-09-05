# tests/test_vocal_pipeline.py
import pytest
from engine.vocal.pipeline import VocalStyle, VocalProductionEngine

def test_vocal_profiles():
    engine = VocalProductionEngine()
    rap_profile = engine.get_vocal_profile(VocalStyle.MODERN_RAP)
    assert rap_profile.high_pass_hz == 100.0
    assert rap_profile.compressor_ratio == 4.0
    assert len(rap_profile.chain) == 4

    trap_profile = engine.get_vocal_profile("trap")
    assert trap_profile.style == VocalStyle.TRAP
    assert trap_profile.high_pass_hz == 120.0

def test_ducking_envelope_calculation():
    engine = VocalProductionEngine()
    
    # Vocal singing in bars 16-24 (beats 64-96)
    vocal_ranges = [(64.0, 96.0)]
    song_length = 128.0 # 32 bars
    
    envelope = engine.calculate_ducking_envelope(
        vocal_ranges_beats=vocal_ranges,
        song_length_beats=song_length,
        duck_amount_db=-2.5,
        attack_beats=0.5,
        release_beats=1.0,
        baseline_volume=0.85
    )
    
    assert len(envelope) >= 4
    # Check pre-vocal baseline
    assert envelope[0]["value"] == 0.85
    assert envelope[0]["time"] == 0.0

    # Find the ducked points
    ducked_pts = [p for p in envelope if 64.0 <= p["time"] <= 96.0]
    expected_ducked_val = 0.85 * (10.0 ** (-2.5 / 20.0))
    for dp in ducked_pts:
        assert dp["value"] == pytest.approx(expected_ducked_val, abs=0.01)

    # Post vocal recovery
    recovery_pts = [p for p in envelope if p["time"] >= 97.0]
    assert len(recovery_pts) > 0
    assert recovery_pts[-1]["value"] == 0.85

def test_ducking_envelope_invalid_db():
    engine = VocalProductionEngine()
    with pytest.raises(ValueError):
        engine.calculate_ducking_envelope([(10.0, 20.0)], 50.0, duck_amount_db=3.0)

def test_target_identification():
    engine = VocalProductionEngine()
    track_names = [
        "Main Drums",         # 0 (protected)
        "808 Sub Bass",       # 1 (protected)
        "Tyler Rhodes Chords",# 2 (target)
        "Synth Lead Hook",    # 3 (target)
        "Vocal Lead",         # 4 (protected)
        "Ambient Pad",        # 5 (target)
        "Master"              # 6 (protected)
    ]
    targets = engine.identify_ducking_targets(track_names)
    assert 2 in targets # Rhodes Chords
    assert 3 in targets # Synth Lead
    assert 5 in targets # Pad
    assert 0 not in targets # Drums
    assert 1 not in targets # 808
    assert 4 not in targets # Vocal

# tests/test_anti_cliche_guard.py
import pytest
from engine.supervisor.anti_cliche_guard import AntiClicheGuard
from engine.music.mutation_engine import MusicMutationEngine

def test_anti_cliche_rejects_flat_velocities():
    flat_notes = [{"pitch": 36, "start_time": float(i), "duration": 0.5, "velocity": 100} for i in range(8)]
    passed, reason, metrics = AntiClicheGuard.audit_midi_clip(flat_notes)
    assert not passed
    assert "FLAT_VELOCITIES_DETECTED" in reason

def test_anti_cliche_rejects_exact_loop_repetition():
    bar = [{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 100}, {"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 85}]
    four_bars = []
    for b in range(4):
        for n in bar:
            n_copy = dict(n)
            n_copy["start_time"] = n["start_time"] + (b * 4.0)
            four_bars.append(n_copy)
    passed, reason, _ = AntiClicheGuard.audit_midi_clip(four_bars)
    assert not passed
    assert "EXACT_LOOP_REPEAT_DETECTED" in reason

def test_mutation_engine_produces_passing_patterns():
    flat_notes = [{"pitch": 36, "start_time": float(i * 0.5), "duration": 0.25, "velocity": 100} for i in range(16)]
    mutated, rep = MusicMutationEngine.mutate_drum_pattern(flat_notes, groove="dilla_drunk", humanize_strength=0.35)
    passed, reason, metrics = AntiClicheGuard.audit_midi_clip(mutated)
    assert passed
    assert reason == "PASSED"
    assert metrics["velocity_std_dev"] >= 1.8

def test_audit_preset_sculpting():
    default_rec = {"Cutoff": 0.50, "Drive": 0.20, "Attack": 0.05}
    raw_applied = {"Cutoff": 0.50, "Drive": 0.20, "Attack": 0.05}
    passed_raw, reason_raw = AntiClicheGuard.audit_preset_sculpting(default_rec, raw_applied)
    assert not passed_raw
    assert "RAW_PRESET_CLICHE_DETECTED" in reason_raw

    sculpted = {"Cutoff": 0.65, "Drive": 0.35, "Attack": 0.05}
    passed_sculpted, reason_sculpted = AntiClicheGuard.audit_preset_sculpting(default_rec, sculpted)
    assert passed_sculpted

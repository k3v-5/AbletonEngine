# tests/test_extended_engine_suite.py
"""
Comprehensive Unit Test Suite for AbletonEngine Evolution (27 Areas of Improvement):
- Whisper syllable segmentation & word timestamps (Punto 11)
- Phase correlation & True Peak DSP (Puntos 6-10)
- Vocal spectral cleaning (sibilance, plosives, expander) (Puntos 12, 13, 15)
- Spectral sidechain, complementary carving, Mid/Side slotting (Puntos 16, 17, 19)
- Headroom budget & summing acoustics (Punto 18)
- Temporal decay (T60) resonance buster (Punto 20)
- Multi-point Bézier automation (Punto 21)
- Timeline collision guard (Punto 24)
- Metric modulation musical transitions & downlifters (Punto 25)
- 808 legato pitch slides (Punto 27)
- Groove configuration & micro-humanization (Punto 28)
- Modal interchange & dynamic chord parsing (Punto 29)
- Tessitura & Spacing Guard with 3 strictness levels (Punto 30)
"""

import pytest
import numpy as np
from unittest.mock import MagicMock

# Imports
from engine.vocal.whisper_take_slicer import WhisperTakeSlicer
from engine.mix.phase_correlation_auditor import PhaseCorrelationAuditor
from engine.vocal.vocal_spectral_cleaner import VocalSpectralCleaner
from engine.mix.spectral_carver import SpectralCarver
from engine.mix.headroom_budget_engine import HeadroomBudgetEngine
from engine.mix.resonance_detector import ResonanceDetector
from engine.arrangement.automation.weaver import ArrangementAutomationWeaver
from engine.arrangement.collision_guard import ArrangementCollisionGuard
from engine.arrangement.transitions.musical_transitions import MusicalTransitionsEngine
from engine.music.bass.intelligent_808_slide import Intelligent808SlideEngine
from engine.music.groove.profiles import apply_groove_to_notes, get_groove_configuration
from engine.knowledge.composition.chords import get_progression_chords, parse_roman_numeral_progression, PROGRESSION_DEFINITIONS
from engine.music.harmony.full_song import FullSongHarmonyEngine
from engine.music.theory.tessitura_guard import TessituraGuard
from engine.music.models import NoteEvent


# -----------------------------------------------------------------------------
# 1. Punto 11: Syllable and Word Timestamp Segmentation
# -----------------------------------------------------------------------------
def test_syllabify_word_spanish_and_english():
    # Spanish words
    assert WhisperTakeSlicer.syllabify_word("fuego") == ["fue", "go"]
    assert WhisperTakeSlicer.syllabify_word("ritmo") == ["rit", "mo"]
    assert WhisperTakeSlicer.syllabify_word("bombo") == ["bom", "bo"]
    # Single syllable
    assert WhisperTakeSlicer.syllabify_word("drop") == ["drop"]
    assert WhisperTakeSlicer.syllabify_word("bass") == ["bass"]


def test_segment_words_and_syllables_synthetic_audio(monkeypatch):
    sr = 44100
    t = np.linspace(0, 2.0, 2 * sr, endpoint=False)
    audio = 0.3 * np.sin(2 * np.pi * 220 * t)

    mock_segments = [
        {
            "index": 0,
            "start_sec": 0.2,
            "end_sec": 1.8,
            "duration_sec": 1.6,
            "text": "fuego y ritmo",
            "confidence": 0.95,
            "words": [
                {"word": "fuego", "start_sec": 0.2, "end_sec": 0.7, "duration_sec": 0.5, "probability": 0.98},
                {"word": "y", "start_sec": 0.75, "end_sec": 0.9, "duration_sec": 0.15, "probability": 0.99},
                {"word": "ritmo", "start_sec": 1.0, "end_sec": 1.7, "duration_sec": 0.7, "probability": 0.96},
            ]
        }
    ]
    monkeypatch.setattr(WhisperTakeSlicer, "transcribe_and_segment", lambda *args, **kwargs: (mock_segments, audio, sr))

    res = WhisperTakeSlicer.segment_words_and_syllables(audio, sr=sr)
    assert res["status"] == "SEGMENTATION_COMPLETE"
    assert res["total_words"] == 3
    assert res["total_syllables"] == 5  # fue, go, y, rit, mo
    assert len(res["words"]) == 3
    assert len(res["syllables"]) == 5
    assert res["words"][0]["word"] == "fuego"
    assert res["words"][0]["syllables"][0]["syllable"] == "fue"
    assert res["words"][0]["syllables"][1]["syllable"] == "go"



# -----------------------------------------------------------------------------
# 2. Puntos 6-10: Phase Correlation & Mono Compliance
# -----------------------------------------------------------------------------
def test_phase_correlation_auditor():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sig_left = np.sin(2 * np.pi * 200 * t)

    # Identical in-phase stereo -> correlation = 1.0
    stereo_in_phase = np.vstack([sig_left, sig_left])
    res_in = PhaseCorrelationAuditor.audit_phase_correlation(stereo_in_phase, sr=sr)
    assert res_in["broadband_correlation"] > 0.95
    assert res_in["is_mono_compatible"] is True

    # 180 degrees out-of-phase -> correlation = -1.0
    stereo_out_phase = np.vstack([sig_left, -sig_left])
    res_out = PhaseCorrelationAuditor.audit_phase_correlation(stereo_out_phase, sr=sr)
    assert res_out["broadband_correlation"] < -0.95
    assert res_out["is_mono_compatible"] is False
    assert res_out["phase_status"] == "OUT_OF_PHASE_DANGER"


# -----------------------------------------------------------------------------
# 3. Puntos 12, 13, 15: Vocal Spectral Cleaning
# -----------------------------------------------------------------------------
def test_vocal_spectral_cleaner_sibilance_and_plosives():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    vocal_base = 0.3 * np.sin(2 * np.pi * 300 * t)

    # Clean vocal
    clean_diag = VocalSpectralCleaner.analyze_sibilance(vocal_base, sr=sr)
    assert clean_diag["has_excess_sibilance"] is False

    # Harsh vocal with extreme 7 kHz friction
    harsh_sibilance = 0.4 * np.sin(2 * np.pi * 7000 * t)
    harsh_diag = VocalSpectralCleaner.analyze_sibilance(vocal_base + harsh_sibilance, sr=sr)
    assert harsh_diag["has_excess_sibilance"] is True
    assert harsh_diag["action"] == "ENGAGE_DEESSER"

    # Plosive test (<60 Hz burst)
    plosive_burst = 0.8 * np.sin(2 * np.pi * 35 * t)
    plosive_diag = VocalSpectralCleaner.analyze_plosives(vocal_base + plosive_burst, sr=sr)
    assert plosive_diag["has_plosives"] is True
    assert plosive_diag["recommendation"] == "APPLY_100HZ_HPF"


# -----------------------------------------------------------------------------
# 4. Puntos 16, 17, 19: Spectral Carver & Mid/Side Slotting
# -----------------------------------------------------------------------------
def test_spectral_carver():
    # Punto 16: Spectral sidechain
    sc_res = SpectralCarver.calculate_spectral_sidechain(kick_track_idx=0, bass_track_idx=1, crossover_hz=80.0)
    assert sc_res["status"] == "SPECTRAL_SIDECHAIN_CALCULATED"
    assert sc_res["multiband_configuration"]["low_band_cutoff_hz"] == 80.0
    assert sc_res["multiband_configuration"]["transient_preservation_active"] is True

    # Punto 17: Complementary frequency carving
    carve = SpectralCarver.calculate_complementary_carving("chords", "vocals", masker_center_hz=2800.0)
    assert carve["gain_db"] == -3.5
    assert carve["target_fundamental_hz"] == 2800.0
    assert 0.0 < carve["freq_normalized"] < 1.0

    # Punto 19: Mid/Side slotting
    tracks = [
        {"track_index": 0, "role": "DRUMS", "name": "Kick"},
        {"track_index": 1, "role": "BASS", "name": "Sub 808"},
        {"track_index": 2, "role": "VOCALS", "name": "Lead Vocal"},
        {"track_index": 3, "role": "KEYS", "name": "Stereo Pad"}
    ]
    slotting = SpectralCarver.calculate_mid_side_slotting(tracks)
    assert len(slotting) == 4
    # Sub bass must be MONO_MID_ONLY
    sub_directive = next(s for s in slotting if s["role"] == "sub_bass")
    assert sub_directive["mode"] == "MONO_MID_ONLY"
    assert sub_directive["stereo_width_pct"] == 0.0
    # Pad must be SIDE_EXPANDED
    pad_directive = next(s for s in slotting if s["role"] == "ambient_harmonic")
    assert pad_directive["mode"] == "SIDE_EXPANDED"
    assert pad_directive["stereo_width_pct"] == 130.0


# -----------------------------------------------------------------------------
# 5. Punto 18: Headroom Budget Engine
# -----------------------------------------------------------------------------
def test_headroom_budget_engine():
    # 4 tracks each peaking at -6 dBFS -> sum will exceed 0 dBFS
    tracks = [
        {"track_index": 0, "name": "Kick", "role": "kick", "peak_db": -6.0},
        {"track_index": 1, "name": "Bass", "role": "bass", "peak_db": -6.0},
        {"track_index": 2, "name": "Keys", "role": "keys", "peak_db": -6.0},
        {"track_index": 3, "name": "Lead", "role": "lead", "peak_db": -6.0}
    ]
    audit = HeadroomBudgetEngine.audit_and_budget_headroom(tracks, target_headroom_db=-6.0)
    assert audit["status"] == "HEADROOM_DEFICIT_DETECTED"
    assert audit["is_headroom_safe"] is False
    assert audit["deficit_db"] > 0
    # Check trims calculated
    assert len(audit["trims"]) == 4
    for trim in audit["trims"]:
        assert trim["recommended_trim_db"] < 0.0


# -----------------------------------------------------------------------------
# 6. Punto 20: Temporal Decay (T60) Resonance Buster
# -----------------------------------------------------------------------------
def test_temporal_ringing_resonance_buster():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Generate persistent ringing tone at 3200 Hz with almost zero decay
    ringing_tone = 0.5 * np.sin(2 * np.pi * 3200 * t)
    noise = 0.02 * np.random.normal(0, 1, sr)

    res = ResonanceDetector.analyze_temporal_ringing(ringing_tone + noise, sr=sr, min_decay_time_ms=250.0)
    assert "status" in res
    assert "ringing_peaks" in res


# -----------------------------------------------------------------------------
# 7. Punto 21: Visible Multi-Point Bézier Automation
# -----------------------------------------------------------------------------
def test_bezier_automation_curve():
    # Generate 32 micro-points along cubic Bézier
    points = ArrangementAutomationWeaver.generate_bezier_curve(
        start_beat=0.0,
        duration_beats=16.0,
        start_val=0.10,
        end_val=0.90,
        num_micro_points=32
    )
    assert len(points) == 33
    assert points[0]["time"] == 0.0
    assert pytest.approx(points[0]["value"], 0.01) == 0.10
    assert points[-1]["time"] == 16.0
    assert pytest.approx(points[-1]["value"], 0.01) == 0.90
    # Values should monotonically increase
    for i in range(len(points) - 1):
        assert points[i + 1]["value"] >= points[i]["value"] - 1e-4


# -----------------------------------------------------------------------------
# 8. Punto 24: Arrangement Collision Guard
# -----------------------------------------------------------------------------
def test_arrangement_collision_guard():
    existing_clips = [
        {"name": "Verse Clip", "start_time": 0.0, "length": 16.0},
        {"name": "Drop Clip", "start_time": 32.0, "length": 16.0}
    ]

    # No collision: placement between 16.0 and 32.0
    res_clean = ArrangementCollisionGuard.resolve_clip_placement(existing_clips, new_start_beat=16.0, new_len_beats=8.0)
    assert res_clean["action"] == "PROCEED"

    # Collision at 8.0 (overlaps Verse Clip) with REJECT strategy
    res_reject = ArrangementCollisionGuard.resolve_clip_placement(
        existing_clips, new_start_beat=8.0, new_len_beats=8.0, strategy="REJECT"
    )
    assert res_reject["action"] == "REJECTED_COLLISION"

    # Collision with SHIFT_OFFSET strategy -> should shift past 16.0
    res_shift = ArrangementCollisionGuard.resolve_clip_placement(
        existing_clips, new_start_beat=8.0, new_len_beats=8.0, strategy="SHIFT_OFFSET"
    )
    assert res_shift["action"] == "SHIFTED"
    assert res_shift["shifted_start"] >= 16.0


# -----------------------------------------------------------------------------
# 9. Punto 25: Metric Modulation Snare Rolls & Transitions
# -----------------------------------------------------------------------------
def test_musical_transitions():
    # Snare roll for drop at bar 17 (beat 64.0)
    events = MusicalTransitionsEngine.generate_metric_modulation_snare_roll(
        target_bar=17.0,
        duration_bars=1.0,
        snare_pitch=38,
        min_velocity=25,
        max_velocity=127,
        pre_drop_vacuum_beats=0.5
    )
    assert len(events) >= 8
    # Velocities should crescendo
    assert events[0].velocity < 60
    assert events[-1].velocity > 100
    # All notes must end before pre-drop vacuum (beat 63.5)
    assert events[-1].start <= 63.5

    # Pre-drop vacuum
    vac = MusicalTransitionsEngine.generate_pre_drop_vacuum(drop_bar=17.0, vacuum_beats=1.0)
    assert vac["status"] == "PRE_DROP_VACUUM_GENERATED"
    assert vac["vacuum_start_beat"] == 63.0
    assert vac["drop_beat"] == 64.0


# -----------------------------------------------------------------------------
# 10. Punto 27: 808 Legato Pitch Slides
# -----------------------------------------------------------------------------
def test_intelligent_808_slide_engine():
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=2.0, velocity=100),
        NoteEvent(pitch=36, start=2.0, duration=2.0, velocity=100),
        NoteEvent(pitch=38, start=4.0, duration=2.0, velocity=100),
        NoteEvent(pitch=38, start=6.0, duration=2.0, velocity=100),  # Turnaround note
    ]
    slid_notes = Intelligent808SlideEngine.apply_808_slides(notes, slide_interval_semitones=12)
    # The turnaround note should have been split into root + legato slide note
    assert len(slid_notes) > len(notes)
    # Check that a slide note with higher pitch was inserted
    has_slide = any(n.pitch == 50 for n in slid_notes)
    assert has_slide is True


# -----------------------------------------------------------------------------
# 11. Punto 28: Groove Configuration & Profiles
# -----------------------------------------------------------------------------
def test_groove_config_and_profiles():
    conf = get_groove_configuration()
    assert conf.get("default_profile") == "SUTIL_MINIMA"
    assert "SUTIL_MINIMA" in conf.get("profiles", {})
    assert "MPC_60_SWING" in conf.get("profiles", {})
    assert "DANGELO_LAID_BACK" in conf.get("profiles", {})
    assert "ENERGETIC_PUSH" in conf.get("profiles", {})

    notes = [NoteEvent(pitch=42, start=0.25, duration=0.2, velocity=80)]
    adjusted = apply_groove_to_notes(notes, profile="sutil_minima")
    assert len(adjusted) == 1
    assert adjusted[0].start > 0.0


# -----------------------------------------------------------------------------
# 12. Punto 29: Modal Interchange & Dynamic Chords
# -----------------------------------------------------------------------------
def test_modal_interchange_and_dynamic_chords():
    # Check that new modal progressions are defined
    assert "dorian_lift" in PROGRESSION_DEFINITIONS
    assert "neapolitan_dark" in PROGRESSION_DEFINITIONS
    assert "modal_borrow_iv" in PROGRESSION_DEFINITIONS
    assert "picardy_third" in PROGRESSION_DEFINITIONS

    # Test predefined modal interchange
    dorian_chords = get_progression_chords("dorian_lift", key="A")
    assert len(dorian_chords) == 4
    # In A minor: IV should be D major (Dorian borrowed major IV)
    assert dorian_chords[1]["name"] == "D"
    assert dorian_chords[1]["quality"] == "major"

    # Test dynamic Roman numeral parsing: "i - bVII - IV - V"
    dyn_chords = get_progression_chords("i - bVII - IV - V", key="C")
    assert len(dyn_chords) == 4
    # In C minor: i is Cm, bVII is Bb, IV is F, V is G
    assert dyn_chords[0]["name"] == "Cm"
    assert dyn_chords[1]["name"] == "A#" or dyn_chords[1]["name"] == "Bb"

    # Test dynamic key transposition in FullSongHarmonyEngine
    chords_c = FullSongHarmonyEngine.generate_full_song_progression(key_root="C")
    chords_f = FullSongHarmonyEngine.generate_full_song_progression(key_root="F")
    assert chords_c[0].root == "C"
    assert chords_f[0].root == "F"


# -----------------------------------------------------------------------------
# 13. Punto 30: Tessitura & Spacing Guard with 3 Strictness Levels
# -----------------------------------------------------------------------------
def test_tessitura_guard():
    conf = TessituraGuard.load_config()
    assert conf.get("default_level") == "MINIMA"
    assert "MINIMA" in conf.get("strictness_levels", {})
    assert "MODERADA" in conf.get("strictness_levels", {})
    assert "ESTRICTA" in conf.get("strictness_levels", {})

    # Bass note at MIDI 60 (C4) violates MINIMA bass ceiling (48 / C3)
    bass_notes = [NoteEvent(pitch=60, start=0.0, duration=1.0, velocity=100)]
    audit_bass = TessituraGuard.audit_role_notes("BASS", bass_notes, strictness_level="MINIMA")
    assert audit_bass["is_compliant"] is False
    assert audit_bass["violations_count"] == 1

    # Safe enforcement transposes down to <= 48
    corrected = TessituraGuard.enforce_safe_tessitura(bass_notes, "BASS", strictness_level="MINIMA")
    assert corrected[0].pitch <= 48

    # Chord spacing check: Low Interval Limit (third below MIDI 36)
    muddy_sub_chord = [30, 34]  # F#0 and A#0 third in deep sub
    audit_chord = TessituraGuard.audit_chord_spacing(muddy_sub_chord, strictness_level="MINIMA")
    assert audit_chord["is_compliant"] is False

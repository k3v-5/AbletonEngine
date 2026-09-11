# tests/test_ai_layers.py
"""
Unit and Integration Tests for the 5 Reliable AI Layers in AbletonEngine:
1. Semantic Sample Matcher (Acoustic 6D Signature & Intent Matching)
2. Hybrid Stem Separator & Arrangement Profiler (Meta Demucs + DSP Fallback)
3. Expressive Audio-to-MIDI Transcriber (F0 detection, pitch bends, velocity)
4. Full-Spectrum Psychoacoustic Masking Auditor (Zwicker 24 Bark critical bands)
5. Producer Style-Conditioned Groove & Pocket Engine (Micro-timing & velocity shaping)
"""

import math
import tempfile
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf

from engine.audio.semantic_sample_matcher import (
    AcousticFeatureExtractor,
    AcousticSignature,
    SemanticSampleMatcher
)
from engine.audio.deconstruction.neural_separator import HybridStemSeparator
from engine.audio.deconstruction.expressive_transcriber import (
    ExpressiveAudioTranscriber,
    ExpressiveNoteEvent
)
from engine.mix.psychoacoustic_masking import (
    PsychoacousticMaskingAuditor,
    PsychoacousticMaskingReport,
    BARK_BANDS_24
)
from engine.music.groove.pocket import GroovePocketEngine, PocketStyle
from engine.music.models import NoteEvent


# -------------------------------------------------------------------------
# 1. SEMANTIC SAMPLE MATCHER TESTS
# -------------------------------------------------------------------------
def test_acoustic_feature_extractor():
    sr = 44100
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Synthetic punchy kick: 80Hz -> 45Hz sub sweep, sharp exponential decay
    freq_sweep = np.linspace(80, 45, len(t))
    env_kick = np.exp(-t * 15.0)
    kick_audio = np.sin(2 * np.pi * freq_sweep * t) * env_kick

    sig_kick = AcousticFeatureExtractor.extract(kick_audio, sr)
    assert sig_kick.attack_time_ms < 10.0, "Kick attack should be fast"
    assert sig_kick.sub_energy_ratio > 0.40, "Kick should have significant low-end energy"
    assert sig_kick.crest_factor_db > 8.0, "Kick should have punchy crest factor"

    # Synthetic bright hi-hat: highpass noise, short decay
    noise = np.random.uniform(-1.0, 1.0, len(t))
    env_hat = np.exp(-t * 40.0)
    hat_audio = noise * env_hat
    sig_hat = AcousticFeatureExtractor.extract(hat_audio, sr)
    assert sig_hat.spectral_centroid_hz > 2000.0, "Hi-hat should have high spectral centroid"
    assert sig_hat.sub_energy_ratio < 0.15, "Hi-hat should have very little sub energy"


def test_semantic_sample_matcher_ranking():
    sr = 44100
    t = np.linspace(0, 0.4, int(sr * 0.4), endpoint=False)

    # Sample A: Boomy sub (pure 45 Hz sine, long decay)
    sub_audio = np.sin(2 * np.pi * 45.0 * t) * np.exp(-t * 3.0)
    sig_sub = AcousticFeatureExtractor.extract(sub_audio, sr)

    # Sample B: Punchy snappy snare (200Hz + noise, fast attack)
    snare_audio = (np.sin(2 * np.pi * 200.0 * t) + np.random.uniform(-0.5, 0.5, len(t))) * np.exp(-t * 25.0)
    sig_snare = AcousticFeatureExtractor.extract(snare_audio, sr)

    candidates = {
        "sample_sub_808": sig_sub,
        "sample_snappy_snare": sig_snare
    }

    # Query 1: Boomy sub
    rank_sub = SemanticSampleMatcher.rank_candidates("boomy deep subby 808", candidates)
    assert rank_sub[0]["id"] == "sample_sub_808", "Should rank sub first for boomy subby query"

    # Query 2: Snappy snare
    rank_snare = SemanticSampleMatcher.rank_candidates("crisp snappy punchy tight", candidates)
    assert rank_snare[0]["id"] == "sample_snappy_snare", "Should rank snare first for snappy query"


# -------------------------------------------------------------------------
# 2. HYBRID STEM SEPARATOR & ARRANGEMENT PROFILER TESTS
# -------------------------------------------------------------------------
def test_hybrid_stem_separator_and_profiler(tmp_path):
    sr = 44100
    duration = 4.0  # 4 seconds
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Compound test audio: Drums (50Hz bursts) + Vocals (1000Hz sine) + Stereo noise
    audio = np.zeros((len(t), 2), dtype=np.float32)
    # 50 Hz kick bursts
    audio[:, 0] += 0.5 * np.sin(2 * np.pi * 50.0 * t) * (np.sin(2 * np.pi * 2.0 * t) > 0.5)
    audio[:, 1] += 0.5 * np.sin(2 * np.pi * 50.0 * t) * (np.sin(2 * np.pi * 2.0 * t) > 0.5)
    # 1000 Hz vocal
    audio[:, 0] += 0.3 * np.sin(2 * np.pi * 1000.0 * t)
    audio[:, 1] += 0.3 * np.sin(2 * np.pi * 1000.0 * t)

    test_wav = tmp_path / "test_ref.wav"
    sf.write(str(test_wav), audio, sr)

    separator = HybridStemSeparator(output_dir=str(tmp_path / "stems"))
    # Separate (using DSP fallback or Demucs)
    stems = separator.separate(test_wav, prefer_neural=False)

    assert "drums" in stems
    assert "bass" in stems
    assert "vocals" in stems
    assert "other" in stems
    assert Path(stems["drums"].audio_path).exists()
    assert stems["drums"].duration_seconds >= 3.9

    # Test arrangement profiler
    profile = separator.profile_arrangement_energy(stems, tempo_bpm=120.0, bars_per_window=1)
    assert len(profile) >= 1
    assert "section_estimate" in profile[0]
    assert "energies_db" in profile[0]


# -------------------------------------------------------------------------
# 3. EXPRESSIVE AUDIO-TO-MIDI TRANSCRIBER TESTS
# -------------------------------------------------------------------------
def test_expressive_audio_transcriber(tmp_path):
    sr = 44100
    # Two distinct notes:
    # 0.0 to 0.8s: A4 (440 Hz -> MIDI 69)
    # 0.8 to 1.6s: C5 (523.25 Hz -> MIDI 72)
    t1 = np.linspace(0, 0.8, int(sr * 0.8), endpoint=False)
    t2 = np.linspace(0, 0.8, int(sr * 0.8), endpoint=False)

    note1 = np.sin(2 * np.pi * 440.0 * t1) * 0.7
    note2 = np.sin(2 * np.pi * 523.25 * t2) * 0.7
    full_audio = np.concatenate([note1, note2])

    test_wav = tmp_path / "melody.wav"
    sf.write(str(test_wav), full_audio, sr)

    transcriber = ExpressiveAudioTranscriber()
    events = transcriber.transcribe_file(test_wav, tempo_bpm=120.0)

    assert len(events) >= 1, "Transcriber should find at least 1 note event"
    pitches = [e.pitch for e in events]
    # Check that either 69 (A4) or 72 (C5) are transcribed
    assert (69 in pitches or 72 in pitches), f"Expected pitch 69 or 72 in transcribed notes, got {pitches}"
    for e in events:
        assert isinstance(e.pitch_bends_cents, list)
        assert e.velocity > 0


# -------------------------------------------------------------------------
# 4. PSYCHOACOUSTIC MASKING AUDITOR TESTS
# -------------------------------------------------------------------------
def test_psychoacoustic_masking_auditor():
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Test Case A: Heavy collision in Bark 1 (50 Hz)
    # Masker: loud 50 Hz kick (0 dBFS peak)
    masker_kick = np.sin(2 * np.pi * 50.0 * t) * 0.95
    # Target: quiet 50 Hz sub bass (-22 dBFS)
    target_bass = np.sin(2 * np.pi * 50.0 * t) * 0.08

    report_clash = PsychoacousticMaskingAuditor.audit_masking_conflict(
        masker_audio=masker_kick,
        target_audio=target_bass,
        sr=sr,
        masker_role="DRUMS",
        target_role="BASS"
    )

    assert report_clash.most_clashing_bark_band == 1, "Collision should be in Bark 1 (50 Hz)"
    assert report_clash.overall_masking_score > 0.05, "Should report significant masking"
    assert len(report_clash.recommended_eq_cuts) >= 1
    assert report_clash.recommended_eq_cuts[0]["center_freq_hz"] == 50.0

    # Test Case B: Clean separation (50 Hz kick vs 5000 Hz hi-hat)
    target_hihat = np.sin(2 * np.pi * 5000.0 * t) * 0.50
    report_clean = PsychoacousticMaskingAuditor.audit_masking_conflict(
        masker_audio=masker_kick,
        target_audio=target_hihat,
        sr=sr,
        masker_role="DRUMS",
        target_role="HIHAT"
    )

    assert report_clean.min_smr_db > 0.0 or len(report_clean.severely_masked_bands) == 0, \
        "5000 Hz hi-hat should not be masked by 50 Hz kick"


# -------------------------------------------------------------------------
# 5. GROOVE POCKET ENGINE TESTS
# -------------------------------------------------------------------------
def test_groove_pocket_engine():
    # Style mapping
    assert GroovePocketEngine.producer_to_pocket_style("J Dilla") == PocketStyle.NEO_SOUL_DILLA
    assert GroovePocketEngine.producer_to_pocket_style("Metro Boomin") == PocketStyle.ATLANTA_TRAP
    assert GroovePocketEngine.producer_to_pocket_style("Daft Punk") == PocketStyle.FRENCH_PUMP
    assert GroovePocketEngine.producer_to_pocket_style("Mike Dean") == PocketStyle.DARK_RAGE
    assert GroovePocketEngine.producer_to_pocket_style("Boom Bap") == PocketStyle.BOOM_BAP
    assert GroovePocketEngine.producer_to_pocket_style("Unknown") == PocketStyle.ORGANIC_HUMAN

    # Apply pocket to notes
    notes = [
        NoteEvent(pitch=36, start=0.0, duration=0.5, velocity=100),
        NoteEvent(pitch=38, start=1.0, duration=0.5, velocity=100),
        NoteEvent(pitch=42, start=1.5, duration=0.25, velocity=90)
    ]

    # J Dilla: Snare at beat 1.0 should receive delayed backbeat (+12ms offset)
    pocketed = GroovePocketEngine.apply_pocket_to_notes(
        notes=notes,
        role="snare",
        pocket_style=PocketStyle.NEO_SOUL_DILLA,
        tempo=120.0,
        strength=1.0,
        seed=123
    )

    assert len(pocketed) == len(notes)
    # The snare at beat 1.0 should be pushed back (> 1.0)
    assert pocketed[1].start > 1.0, f"Dilla snare should be laid-back, got {pocketed[1].start}"
    # Reproducible with same seed
    pocketed_again = GroovePocketEngine.apply_pocket_to_notes(
        notes=notes,
        role="snare",
        pocket_style=PocketStyle.NEO_SOUL_DILLA,
        tempo=120.0,
        strength=1.0,
        seed=123
    )
    assert pocketed[1].start == pocketed_again[1].start, "Pocket should be 100% deterministic with seed"

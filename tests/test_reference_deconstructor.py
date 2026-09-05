# tests/test_reference_deconstructor.py
"""
Unit tests for Audio Reference Deconstruction, Stem Separation, and MIDI Transcription.
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import soundfile as sf

from engine.audio.deconstruction.models import (
    StemCategory,
    DeconstructedStem,
    TranscribedNoteEvent,
    AudioTranscriptionResult
)
from engine.audio.deconstruction.separator import AudioStemSeparator
from engine.audio.deconstruction.transcriber import ReferenceTranscriber
from engine.audio.deconstruction.reconstructor import ReferenceReconstructor

@pytest.fixture
def synthetic_audio_track():
    """Generates a 3-second synthetic audio file with bass, drums, and harmonic synth."""
    sr = 44100
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # 1. Bass: 55 Hz (A1) sine wave
    bass = 0.5 * np.sin(2 * np.pi * 55.0 * t)
    
    # 2. Drums: Rhythmic transients at 120 BPM (0.5s intervals)
    drums = np.zeros_like(t)
    for beat_time in np.arange(0.0, duration, 0.5):
        idx = int(beat_time * sr)
        if idx + 2000 < len(drums):
            # Kick-like burst
            burst = np.sin(2 * np.pi * 80.0 * np.linspace(0, 0.05, 2000)) * np.exp(-np.linspace(0, 5, 2000))
            drums[idx : idx + 2000] += burst * 0.8
            
    # 3. Harmonics: C Major chord (C4=261.6Hz, E4=329.6Hz, G4=392.0Hz)
    chord = 0.2 * (np.sin(2 * np.pi * 261.6 * t) + np.sin(2 * np.pi * 329.6 * t) + np.sin(2 * np.pi * 392.0 * t))
    
    mixed = bass + drums + chord
    mixed = np.column_stack([mixed, mixed]).astype(np.float32)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
        
    sf.write(temp_path, mixed, sr)
    yield temp_path, sr, duration
    
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

def test_stem_separator(synthetic_audio_track):
    audio_path, sr, duration = synthetic_audio_track
    with tempfile.TemporaryDirectory() as tmpdir:
        separator = AudioStemSeparator(output_dir=tmpdir)
        stems = separator.separate(audio_path, base_name="test_ref")
        
        assert len(stems) == 4
        assert "drums" in stems
        assert "bass" in stems
        assert "vocals" in stems
        assert "other" in stems
        
        for name, stem in stems.items():
            assert os.path.exists(stem.audio_path)
            assert stem.sample_rate == sr
            assert stem.duration_seconds == pytest.approx(duration, abs=0.1)
            assert stem.peak_db <= 0.01  # Not clipping

def test_transcriber_tempo_and_key(synthetic_audio_track):
    audio_path, sr, duration = synthetic_audio_track
    with tempfile.TemporaryDirectory() as tmpdir:
        separator = AudioStemSeparator(output_dir=tmpdir)
        transcriber = ReferenceTranscriber(separator=separator)
        
        data, _ = sf.read(audio_path, always_2d=True)
        mono = 0.5 * (data[:, 0] + data[:, 1])
        
        tempo = transcriber.detect_tempo(mono, sr)
        assert 60.0 <= tempo <= 180.0
        
        key = transcriber.detect_key(mono, sr)
        assert isinstance(key, str)
        assert "Major" in key or "Minor" in key

def test_transcriber_full_pipeline(synthetic_audio_track):
    audio_path, sr, duration = synthetic_audio_track
    with tempfile.TemporaryDirectory() as tmpdir:
        separator = AudioStemSeparator(output_dir=tmpdir)
        transcriber = ReferenceTranscriber(separator=separator)
        
        result = transcriber.transcribe(audio_path, tempo=120.0, key="C Major")
        
        assert isinstance(result, AudioTranscriptionResult)
        assert result.detected_tempo == 120.0
        assert result.detected_key == "C Major"
        assert len(result.stems) == 4
        assert len(result.drum_notes) > 0
        assert result.drum_notes[0].pitch in (36, 38, 42)
        assert len(result.bass_notes) > 0
        # Synthetic bass was A1 (55Hz -> MIDI 33)
        assert any(abs(n.pitch - 33) <= 2 for n in result.bass_notes)

def test_reconstructor_plan_generation(synthetic_audio_track):
    audio_path, sr, duration = synthetic_audio_track
    with tempfile.TemporaryDirectory() as tmpdir:
        separator = AudioStemSeparator(output_dir=tmpdir)
        transcriber = ReferenceTranscriber(separator=separator)
        result = transcriber.transcribe(audio_path, tempo=120.0, key="A Minor")
        
        reconstructor = ReferenceReconstructor()
        plan = reconstructor.build_reconstruction_plan(result)
        
        assert plan["detected_tempo"] == 120.0
        assert plan["detected_key"] == "A Minor"
        assert len(plan["tracks"]) == 3
        assert plan["tracks"][0]["name"] == "Ref_Drums_MIDI"
        assert plan["tracks"][1]["name"] == "Ref_Bass_MIDI"
        assert plan["tracks"][2]["name"] == "Ref_Chords_MIDI"
        assert len(plan["stems"]) == 4

        # Verify offline reconstruction response
        offline_res = reconstructor.reconstruct(result)
        assert offline_res["status"] == "plan_generated_offline"
        assert "plan" in offline_res

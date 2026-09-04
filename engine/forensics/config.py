"""
Centralized Configuration & Standard Spectral Bands for Audio Forensics Engine.
"""
from typing import List, Tuple
from .models import AnalysisConfig


# 14 Standard Spectral Aggregation Bands (Section 14)
STANDARD_FREQUENCY_BANDS: List[Tuple[str, float, float]] = [
    ("SUB_LOW", 20.0, 40.0),
    ("SUB_MID", 40.0, 60.0),
    ("BASS_LOW", 60.0, 90.0),
    ("BASS_MID", 90.0, 120.0),
    ("BASS_HIGH", 120.0, 200.0),
    ("LOW_MIDS_1", 200.0, 320.0),
    ("LOW_MIDS_2", 320.0, 500.0),
    ("MIDS", 500.0, 1000.0),
    ("HIGH_MIDS_1", 1000.0, 2000.0),
    ("HIGH_MIDS_2", 2000.0, 3000.0),
    ("PRESENCE_1", 3000.0, 5000.0),
    ("PRESENCE_2", 5000.0, 8000.0),
    ("BRILLIANCE_1", 8000.0, 12000.0),
    ("BRILLIANCE_2", 12000.0, 20000.0)
]

DEFAULT_ANALYSIS_CONFIG = AnalysisConfig(
    fft_size=2048,
    hop_size=512,
    window="hann",
    min_frequency_hz=20.0,
    max_frequency_hz=20000.0,
    peak_threshold_db=-0.1,
    resonance_threshold_db=6.0,
    minimum_event_duration_ms=50.0,
    maximum_event_gap_ms=100.0,
    correlation_threshold=0.75,
    clipping_threshold_dbfs=-0.01,
    algorithm_version="1.0.0"
)

# Specialized presets for specific source types
VOCAL_FORENSICS_CONFIG = AnalysisConfig(
    fft_size=2048,
    hop_size=256,
    window="hann",
    min_frequency_hz=80.0,
    max_frequency_hz=16000.0,
    peak_threshold_db=-0.1,
    resonance_threshold_db=5.0,
    minimum_event_duration_ms=40.0,
    maximum_event_gap_ms=80.0,
    correlation_threshold=0.80,
    clipping_threshold_dbfs=-0.01,
    algorithm_version="1.0.0"
)

LOW_END_FORENSICS_CONFIG = AnalysisConfig(
    fft_size=4096,
    hop_size=1024,
    window="hann",
    min_frequency_hz=20.0,
    max_frequency_hz=500.0,
    peak_threshold_db=-0.1,
    resonance_threshold_db=4.5,
    minimum_event_duration_ms=60.0,
    maximum_event_gap_ms=120.0,
    correlation_threshold=0.70,
    clipping_threshold_dbfs=-0.01,
    algorithm_version="1.0.0"
)

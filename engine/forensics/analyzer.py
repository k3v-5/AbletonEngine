"""
Audio Forensics Master Engine Facade (PIE Phase 7).
Coordinates temporal, spectral, dynamic, and causal forensic diagnostics
for single audio streams and multitrack stems.
GUARANTEES: Deterministic, strictly READ-ONLY ($State_{before} \\equiv State_{after}$),
zero ML dependencies.
"""
from typing import Optional, Dict, Any, List, Sequence, Tuple
import numpy as np
import time
import uuid

from .models import (
    AnalysisConfig,
    AudioFrame,
    ForensicEvent,
    ForensicEventType,
    Severity,
    CausalHypothesis,
    TrackBaseline,
    ForensicReport,
)
from .config import DEFAULT_ANALYSIS_CONFIG
from .stft import STFTEngine
from .temporal import TemporalEngine
from .spectral import SpectralEngine
from .clipping import ClippingEngine
from .anomalies import AnomalyEngine
from .masking import MaskingEngine
from .correlation import CorrelationEngine
from .baseline import BaselineEngine
from .causality import CausalityEngine
from .report import ForensicReportGenerator
from .serializer import ForensicsStorage
from .exceptions import InvalidAudioError, InvalidAnalysisConfigError


class AudioForensicsEngine:
    """
    Comprehensive Audio Forensics Engine.
    Transitions PIE from global static metrics to exact time-frequency diagnostic localization.
    """

    def __init__(self, storage: Optional[ForensicsStorage] = None):
        self.storage = storage or ForensicsStorage()

    @staticmethod
    def _validate_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        if not isinstance(audio, np.ndarray):
            raise InvalidAudioError(f"Audio must be a numpy.ndarray, got {type(audio)}")
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        elif audio.ndim != 2:
            raise InvalidAudioError(f"Audio must have 1 or 2 dimensions, got shape {audio.shape}")
        if audio.shape[0] not in (1, 2):
            raise InvalidAudioError(f"Forensics supports 1 or 2 channels, got {audio.shape[0]}")
        if audio.size == 0:
            raise InvalidAudioError("Audio buffer cannot be empty.")
        if not np.all(np.isfinite(audio)):
            raise InvalidAudioError("Audio buffer contains non-finite values (NaN or Inf).")
        if sample_rate <= 0:
            raise InvalidAudioError(f"Sample rate must be positive, got {sample_rate}")
        return audio

    def analyze_track(
        self,
        audio: np.ndarray,
        sample_rate: int,
        track_id: str = "track_01",
        config: Optional[AnalysisConfig] = None,
        production_graph: Optional[Any] = None,
        project_id: str = "default_project",
        save_report: bool = True,
    ) -> ForensicReport:
        """
        Performs full forensic audit on a single audio track or mixbus.

        Steps:
        1. Input validation & defensive check.
        2. STFT time-frequency transform.
        3. Temporal frame feature extraction.
        4. Statistical baseline profile computation.
        5. Spectral resonance detection.
        6. Digital sample clipping & BS.1770-5 4x True Peak detection.
        7. Acoustic anomalies (DC offset, clicks, pops, dropouts, channel loss, phase).
        8. Causal hypothesis inference.
        9. Optional ProductionGraph lineage injection.
        10. Cryptographically sealed report generation and atomic persistence.
        """
        t0 = time.perf_counter()
        audio = self._validate_audio(audio, sample_rate)
        cfg = config or DEFAULT_ANALYSIS_CONFIG

        channels = audio.shape[0]
        duration_s = float(audio.shape[1] / sample_rate)

        # 1. STFT Transform
        stft_res = STFTEngine.compute_stft(audio, sample_rate, cfg)

        # 2. Temporal Frames
        frames = TemporalEngine.analyze_frames(audio, sample_rate, cfg)

        # 3. Track Baseline Profile
        baseline = BaselineEngine.compute_baseline(audio, sample_rate, frames, cfg, track_id=track_id)

        # 4. Spectral Resonances
        resonance_events = SpectralEngine.detect_resonances(stft_res, baseline=baseline, config=cfg)

        # 5. Clipping & Inter-Sample True Peak
        clipping_events = ClippingEngine.analyze(audio, sample_rate, config=cfg)

        # 6. Acoustic Anomalies
        anomaly_events = AnomalyEngine.analyze(audio, sample_rate, config=cfg)

        # Aggregate all detected events
        all_events = resonance_events + clipping_events + anomaly_events
        all_events.sort(key=lambda e: (e.start_time_seconds, e.event_type))

        # 7. Causal Inference
        hypotheses = CausalityEngine.generate_hypotheses_for_events(
            events=all_events,
            baseline=baseline,
            track_name=track_id
        )

        # 8. Optional Lineage Injection into ProductionGraph
        if production_graph is not None:
            CausalityEngine.inject_into_production_graph(
                graph=production_graph,
                events=all_events,
                hypotheses=hypotheses,
                project_id=project_id
            )

        elapsed = time.perf_counter() - t0
        report_id = f"rep_forensic_{track_id}_{int(t0)}"

        report = ForensicReportGenerator.create_report(
            report_id=report_id,
            sample_rate=sample_rate,
            duration_seconds=duration_s,
            channels=channels,
            frames_analyzed=len(frames),
            measurements_count=len(frames) + len(all_events),
            events=all_events,
            hypotheses=hypotheses,
            baseline=baseline,
            config=cfg,
            processing_time_seconds=elapsed,
            analysis_version=cfg.algorithm_version
        )

        if save_report and self.storage:
            self.storage.save_report(report)

        return report

    def analyze_multitrack(
        self,
        stems: Dict[str, np.ndarray],
        sample_rate: int,
        mixbus_audio: Optional[np.ndarray] = None,
        config: Optional[AnalysisConfig] = None,
        production_graph: Optional[Any] = None,
        project_id: str = "default_project",
        save_report: bool = True,
    ) -> ForensicReport:
        """
        Performs multitrack forensic audit across stems, detecting pairwise masking
        and attributing mixbus events to specific source tracks.
        """
        t0 = time.perf_counter()
        cfg = config or DEFAULT_ANALYSIS_CONFIG

        if not stems:
            raise InvalidAudioError("Multitrack stems dictionary cannot be empty.")

        # Determine reference duration and channels
        first_stem = next(iter(stems.values()))
        first_stem = self._validate_audio(first_stem, sample_rate)
        duration_s = float(first_stem.shape[1] / sample_rate)
        channels = first_stem.shape[0]

        all_events: List[ForensicEvent] = []

        # 1. Pairwise Dynamic Masking Analysis
        masking_events = MaskingEngine.analyze_multitrack(
            stems=stems,
            sample_rate=sample_rate,
            config=cfg,
            clash_threshold_db=6.0
        )
        all_events.extend(masking_events)

        # 2. Individual Stem Audits (Clipping / Anomalies / Resonances on each stem)
        for stem_name, stem_audio in stems.items():
            stem_audio_val = self._validate_audio(stem_audio, sample_rate)
            stem_clips = ClippingEngine.analyze(stem_audio_val, sample_rate, config=cfg)
            stem_anoms = AnomalyEngine.analyze(stem_audio_val, sample_rate, config=cfg)
            # Add stem name tag in details
            for ev in stem_clips + stem_anoms:
                details = dict(ev.details)
                details["source_stem"] = stem_name
                object.__setattr__(ev, "details", details)
            all_events.extend(stem_clips)
            all_events.extend(stem_anoms)

        # 3. If Mixbus audio is provided, analyze mixbus and attribute defects to stems
        if mixbus_audio is not None:
            mixbus_audio_val = self._validate_audio(mixbus_audio, sample_rate)
            mix_clips = ClippingEngine.analyze(mixbus_audio_val, sample_rate, config=cfg)
            for mc in mix_clips:
                attribs = CorrelationEngine.attribute_event_to_sources(mc, stems, sample_rate)
                if attribs:
                    top_stem, top_score, stats = attribs[0]
                    det = dict(mc.details)
                    det["attributed_stem"] = top_stem
                    det["attribution_score"] = top_score
                    det["attribution_ranking"] = [(s[0], s[1]) for s in attribs[:3]]
                    object.__setattr__(mc, "details", det)
                all_events.append(mc)

        all_events.sort(key=lambda e: (e.start_time_seconds, e.event_type))

        # 4. Multitrack Causal Hypotheses
        hypotheses = CausalityEngine.generate_hypotheses_for_events(
            events=all_events,
            track_name="Multitrack_Session"
        )

        # 5. Lineage Injection
        if production_graph is not None:
            CausalityEngine.inject_into_production_graph(
                graph=production_graph,
                events=all_events,
                hypotheses=hypotheses,
                project_id=project_id
            )

        elapsed = time.perf_counter() - t0
        report_id = f"rep_forensic_multitrack_{int(t0)}"

        report = ForensicReportGenerator.create_report(
            report_id=report_id,
            sample_rate=sample_rate,
            duration_seconds=duration_s,
            channels=channels,
            frames_analyzed=int(duration_s / (cfg.hop_size / sample_rate)),
            measurements_count=len(all_events),
            events=all_events,
            hypotheses=hypotheses,
            baseline=None,
            config=cfg,
            processing_time_seconds=elapsed,
            analysis_version=cfg.algorithm_version
        )

        if save_report and self.storage:
            self.storage.save_report(report)

        return report

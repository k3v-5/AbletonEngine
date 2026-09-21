# engine/creative/contextual_sonic_critic.py
"""
Contextual Sonic Critic (Nivel R):
Evaluates sound design mutations and self-sampling candidates in the physical context
of the song's arrangement, answering the core question:
'Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?'

Unlike isolated taste evaluation, the Contextual Sonic Critic compares the physical
render of a section BEFORE the intervention against the render AFTER inserting the mutation,
auditing 10 objective acoustic and psychoacoustic dimensions:

1. Groove & Pocket (Grid stability, low-end transient clarity, rhythmic feel)
2. Vocal Lead Clearance (Intelligibility corridor 1.0 - 3.5 kHz, masking detection)
3. Spectral Crowding & Mud (Low-mid mud zone 200 - 500 Hz, sub-bass clash)
4. Transient Sharpness & Punch (Crest factor preservation: Peak dBFS - RMS dBFS)
5. Energy Trajectory (Dynamic alignment with section narrative: Hook vs Verse vs Bridge)
6. Spatial Depth & Stereo Width (Mono correlation, width expansion without phase cancellation)
7. Identity Elevation (Unique timbre contribution vs generic stock filler)
8. Motif Resonance (Organic reinforcement of the core melodic/harmonic DNA)
9. Sectional Contrast (Textural and dynamic step from preceding sections)
10. Net Song Improvement (Delta Q: composite holistic quality delta)
"""

from __future__ import annotations
import os
import math
import wave
import struct
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

import numpy as np

from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("ContextualSonicCritic")


class ContextualDimension(str, Enum):
    """The 10 In-Situ Contextual Dimensions."""
    GROOVE = "groove"
    VOCAL_CLEARANCE = "vocal_clearance"
    SPECTRAL_CROWDING = "spectral_crowding"
    TRANSIENTS = "transients"
    ENERGY_TRAJECTORY = "energy_trajectory"
    SPACE_WIDTH = "space_width"
    IDENTITY = "identity"
    MOTIF_RESONANCE = "motif_resonance"
    SECTIONAL_CONTRAST = "sectional_contrast"
    NET_IMPROVEMENT = "net_improvement"


class ContextualVerdict(str, Enum):
    """Verdict on whether the staged mutation genuinely improves the song."""
    DEFINITIVE_IMPROVEMENT = "definitive_improvement"  # Delta Q >= +0.10, no fatal vetoes
    MARGINAL_BENEFIT = "marginal_benefit"              # 0.0 <= Delta Q < +0.10, no fatal vetoes
    DEGRADATION = "degradation"                        # Delta Q < 0.0 or any fatal veto


@dataclass
class AudioSectionAcousticSnapshot:
    """Acoustic and psychoacoustic profile of an audio section."""
    duration_sec: float = 0.0
    peak_dbfs: float = -96.0
    rms_dbfs: float = -96.0
    crest_factor_db: float = 0.0
    sub_energy_dbfs: float = -96.0        # 20 - 90 Hz
    bass_energy_dbfs: float = -96.0       # 90 - 200 Hz
    mud_energy_dbfs: float = -96.0        # 200 - 500 Hz (Mud Zone)
    mid_energy_dbfs: float = -96.0        # 500 - 1000 Hz
    vocal_corridor_dbfs: float = -96.0    # 1000 - 3500 Hz (Vocal Presence)
    high_mid_energy_dbfs: float = -96.0   # 3500 - 8000 Hz
    air_energy_dbfs: float = -96.0        # 8000 - 20000 Hz
    stereo_width: float = 0.0             # RMS(Side) / RMS(Mid)
    mono_correlation: float = 1.0         # -1.0 (anti-phase) to +1.0 (perfect mono)
    sub_mono_correlation: float = 1.0     # Correlation specifically for < 120 Hz
    raw_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_sec": round(self.duration_sec, 3),
            "peak_dbfs": round(self.peak_dbfs, 2),
            "rms_dbfs": round(self.rms_dbfs, 2),
            "crest_factor_db": round(self.crest_factor_db, 2),
            "sub_energy_dbfs": round(self.sub_energy_dbfs, 2),
            "bass_energy_dbfs": round(self.bass_energy_dbfs, 2),
            "mud_energy_dbfs": round(self.mud_energy_dbfs, 2),
            "mid_energy_dbfs": round(self.mid_energy_dbfs, 2),
            "vocal_corridor_dbfs": round(self.vocal_corridor_dbfs, 2),
            "high_mid_energy_dbfs": round(self.high_mid_energy_dbfs, 2),
            "air_energy_dbfs": round(self.air_energy_dbfs, 2),
            "stereo_width": round(self.stereo_width, 3),
            "mono_correlation": round(self.mono_correlation, 3),
            "sub_mono_correlation": round(self.sub_mono_correlation, 3),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioSectionAcousticSnapshot:
        return cls(
            duration_sec=float(data.get("duration_sec", 0.0)),
            peak_dbfs=float(data.get("peak_dbfs", -96.0)),
            rms_dbfs=float(data.get("rms_dbfs", -96.0)),
            crest_factor_db=float(data.get("crest_factor_db", 0.0)),
            sub_energy_dbfs=float(data.get("sub_energy_dbfs", -96.0)),
            bass_energy_dbfs=float(data.get("bass_energy_dbfs", -96.0)),
            mud_energy_dbfs=float(data.get("mud_energy_dbfs", -96.0)),
            mid_energy_dbfs=float(data.get("mid_energy_dbfs", -96.0)),
            vocal_corridor_dbfs=float(data.get("vocal_corridor_dbfs", -96.0)),
            high_mid_energy_dbfs=float(data.get("high_mid_energy_dbfs", -96.0)),
            air_energy_dbfs=float(data.get("air_energy_dbfs", -96.0)),
            stereo_width=float(data.get("stereo_width", 0.0)),
            mono_correlation=float(data.get("mono_correlation", 1.0)),
            sub_mono_correlation=float(data.get("sub_mono_correlation", 1.0)),
            raw_metrics=dict(data.get("raw_metrics", {}))
        )


@dataclass
class ContextualAcousticDeltas:
    """Acoustic deltas between staged section audio and baseline audio (Staged - Baseline)."""
    delta_rms_db: float
    delta_peak_db: float
    delta_crest_factor_db: float
    delta_vocal_corridor_db: float
    delta_mud_db: float
    delta_sub_db: float
    delta_stereo_width: float
    delta_mono_correlation: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta_rms_db": round(self.delta_rms_db, 2),
            "delta_peak_db": round(self.delta_peak_db, 2),
            "delta_crest_factor_db": round(self.delta_crest_factor_db, 2),
            "delta_vocal_corridor_db": round(self.delta_vocal_corridor_db, 2),
            "delta_mud_db": round(self.delta_mud_db, 2),
            "delta_sub_db": round(self.delta_sub_db, 2),
            "delta_stereo_width": round(self.delta_stereo_width, 3),
            "delta_mono_correlation": round(self.delta_mono_correlation, 3),
        }


@dataclass
class ContextualAuditReport:
    """
    Comprehensive in-situ contextual audit report answering:
    'Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?'
    """
    section_name: str
    target_role: str
    candidate_id: str
    distance_category: str
    distance_score: float
    baseline_metrics: AudioSectionAcousticSnapshot
    staged_metrics: AudioSectionAcousticSnapshot
    deltas: ContextualAcousticDeltas
    dimension_scores: Dict[str, float]
    net_improvement_score: float
    verdict: ContextualVerdict
    veto_flags: List[str]
    actionable_directive: str
    mixing_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "target_role": self.target_role,
            "candidate_id": self.candidate_id,
            "distance_category": self.distance_category,
            "distance_score": round(self.distance_score, 3),
            "baseline_metrics": self.baseline_metrics.to_dict(),
            "staged_metrics": self.staged_metrics.to_dict(),
            "deltas": self.deltas.to_dict(),
            "dimension_scores": {k: round(v, 3) for k, v in self.dimension_scores.items()},
            "net_improvement_score": round(self.net_improvement_score, 3),
            "verdict": self.verdict.value,
            "veto_flags": list(self.veto_flags),
            "actionable_directive": self.actionable_directive,
            "mixing_suggestions": list(self.mixing_suggestions),
        }


class ContextualSonicCritic:
    """
    In-Situ Sonic Critic for full song and section arrangements.
    Performs physical A/B audits across the 10 contextual dimensions.
    """

    # Veto thresholds
    MAX_ALLOWED_VOCAL_MASKING_DB = 2.2      # dB increase in 1.0 - 3.5 kHz without sidechain
    MAX_ALLOWED_MUD_BUILDUP_DB = 3.2        # dB increase in 200 - 500 Hz
    MIN_ALLOWED_MONO_CORRELATION = 0.05     # Below this is destructive anti-phase
    MIN_ALLOWED_SUB_MONO_CORRELATION = 0.70 # Sub must remain tight and centered
    MAX_ALLOWED_CREST_FACTOR_LOSS_DB = 3.5  # Transient destruction threshold

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # Physical Audio Signal Analysis
    # -------------------------------------------------------------------------
    def analyze_audio_signal(
        self,
        audio_input: Union[str, Path, np.ndarray, Dict[str, Any]],
        sample_rate: int = 44100
    ) -> AudioSectionAcousticSnapshot:
        """
        Analyzes audio input and extracts full acoustic and psychoacoustic metrics:
        - Accepts: WAV file path, numpy ndarray (mono or stereo), or pre-computed dict.
        """
        if isinstance(audio_input, dict):
            return AudioSectionAcousticSnapshot.from_dict(audio_input)

        # Load audio data as stereo float32 array in [-1.0, 1.0]
        stereo_audio, sr = self._load_audio_to_stereo(audio_input, sample_rate)
        n_samples = stereo_audio.shape[1]
        duration_sec = n_samples / float(sr) if sr > 0 else 0.0

        if n_samples == 0:
            return AudioSectionAcousticSnapshot(duration_sec=0.0)

        left = stereo_audio[0]
        right = stereo_audio[1]
        mono = 0.5 * (left + right)

        # 1. Peak & RMS
        peak_amp = float(np.max(np.abs(stereo_audio)))
        peak_dbfs = 20.0 * math.log10(max(1e-6, peak_amp))

        rms_amp = float(np.sqrt(np.mean(mono ** 2)))
        rms_dbfs = 20.0 * math.log10(max(1e-6, rms_amp))

        crest_factor_db = max(0.0, peak_dbfs - rms_dbfs)

        # 2. Mid / Side & Spatial Correlation
        mid = (left + right) / math.sqrt(2.0)
        side = (left - right) / math.sqrt(2.0)
        rms_mid = float(np.sqrt(np.mean(mid ** 2)))
        rms_side = float(np.sqrt(np.mean(side ** 2)))
        stereo_width = rms_side / max(1e-6, rms_mid)

        # Pearson correlation between Left and Right
        denom = (np.sqrt(np.sum(left ** 2)) * np.sqrt(np.sum(right ** 2)))
        if denom > 1e-9:
            mono_corr = float(np.sum(left * right) / denom)
        else:
            mono_corr = 1.0
        mono_corr = max(-1.0, min(1.0, mono_corr))

        # 3. Frequency Band Energy (FFT)
        freq_bands = self._calculate_frequency_bands(left, right, sr)

        # 4. Sub-Bass Mono Correlation (< 120 Hz)
        sub_mono_corr = self._calculate_sub_mono_correlation(left, right, sr)

        return AudioSectionAcousticSnapshot(
            duration_sec=duration_sec,
            peak_dbfs=peak_dbfs,
            rms_dbfs=rms_dbfs,
            crest_factor_db=crest_factor_db,
            sub_energy_dbfs=freq_bands["sub"],
            bass_energy_dbfs=freq_bands["bass"],
            mud_energy_dbfs=freq_bands["mud"],
            mid_energy_dbfs=freq_bands["mid"],
            vocal_corridor_dbfs=freq_bands["vocal"],
            high_mid_energy_dbfs=freq_bands["high_mid"],
            air_energy_dbfs=freq_bands["air"],
            stereo_width=stereo_width,
            mono_correlation=mono_corr,
            sub_mono_correlation=sub_mono_corr,
            raw_metrics={"sample_rate": sr, "samples": n_samples}
        )

    # -------------------------------------------------------------------------
    # Master Contextual Evaluation
    # -------------------------------------------------------------------------
    def evaluate_staged_sound_in_context(
        self,
        section_name: str,
        baseline_audio: Union[str, Path, np.ndarray, Dict[str, Any]],
        staged_audio: Union[str, Path, np.ndarray, Dict[str, Any]],
        song_dna: Optional[CompositionalDNA] = None,
        target_role: str = "pad_texture",
        candidate_id: str = "candidate_01",
        distance_score: float = 0.50,
        has_lead_vocal: Optional[bool] = None,
        sample_rate: int = 44100
    ) -> ContextualAuditReport:
        """
        Executes an in-situ audit comparing the section audio BEFORE and AFTER intervention:
        Answers: 'Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?'
        """
        # Step 1: Acoustic snapshots
        baseline = self.analyze_audio_signal(baseline_audio, sample_rate)
        staged = self.analyze_audio_signal(staged_audio, sample_rate)

        # Step 2: Compute physical deltas
        deltas = ContextualAcousticDeltas(
            delta_rms_db=staged.rms_dbfs - baseline.rms_dbfs,
            delta_peak_db=staged.peak_dbfs - baseline.peak_dbfs,
            delta_crest_factor_db=staged.crest_factor_db - baseline.crest_factor_db,
            delta_vocal_corridor_db=staged.vocal_corridor_dbfs - baseline.vocal_corridor_dbfs,
            delta_mud_db=staged.mud_energy_dbfs - baseline.mud_energy_dbfs,
            delta_sub_db=staged.sub_energy_dbfs - baseline.sub_energy_dbfs,
            delta_stereo_width=staged.stereo_width - baseline.stereo_width,
            delta_mono_correlation=staged.mono_correlation - baseline.mono_correlation
        )

        # Step 3: Determine section context & vocal presence
        sec_low = section_name.lower()
        if has_lead_vocal is None:
            has_lead_vocal = any(k in sec_low for k in ["hook", "chorus", "verse", "lead"])

        # Determine distance category
        distance_category = self._categorize_distance(distance_score)

        # Step 4: Evaluate the 10 Contextual Dimensions
        scores: Dict[str, float] = {}
        veto_flags: List[str] = []
        mixing_suggestions: List[str] = []

        # 1. Groove & Pocket
        scores[ContextualDimension.GROOVE.value] = self._score_groove(
            baseline, staged, deltas, target_role, veto_flags, mixing_suggestions
        )

        # 2. Vocal Lead Clearance
        scores[ContextualDimension.VOCAL_CLEARANCE.value] = self._score_vocal_clearance(
            baseline, staged, deltas, has_lead_vocal, target_role, veto_flags, mixing_suggestions
        )

        # 3. Spectral Crowding & Mud
        scores[ContextualDimension.SPECTRAL_CROWDING.value] = self._score_spectral_crowding(
            baseline, staged, deltas, target_role, veto_flags, mixing_suggestions
        )

        # 4. Transient Sharpness & Punch
        scores[ContextualDimension.TRANSIENTS.value] = self._score_transients(
            baseline, staged, deltas, target_role, veto_flags, mixing_suggestions
        )

        # 5. Energy Trajectory
        scores[ContextualDimension.ENERGY_TRAJECTORY.value] = self._score_energy_trajectory(
            deltas, section_name, mixing_suggestions
        )

        # 6. Spatial Depth & Stereo Width
        scores[ContextualDimension.SPACE_WIDTH.value] = self._score_space_width(
            baseline, staged, deltas, veto_flags, mixing_suggestions
        )

        # 7. Identity Elevation
        scores[ContextualDimension.IDENTITY.value] = self._score_identity(
            staged, distance_score, distance_category, song_dna
        )

        # 8. Motif Resonance
        scores[ContextualDimension.MOTIF_RESONANCE.value] = self._score_motif_resonance(
            distance_score, distance_category, song_dna
        )

        # 9. Sectional Contrast
        scores[ContextualDimension.SECTIONAL_CONTRAST.value] = self._score_sectional_contrast(
            deltas, staged, section_name
        )

        # 10. Net Song Improvement (Delta Q)
        net_q, verdict, directive = self._calculate_net_improvement_and_verdict(
            scores=scores,
            deltas=deltas,
            veto_flags=veto_flags,
            section_name=section_name,
            target_role=target_role,
            distance_category=distance_category,
            distance_score=distance_score,
            has_lead_vocal=has_lead_vocal
        )
        scores[ContextualDimension.NET_IMPROVEMENT.value] = net_q

        return ContextualAuditReport(
            section_name=section_name,
            target_role=target_role,
            candidate_id=candidate_id,
            distance_category=distance_category,
            distance_score=distance_score,
            baseline_metrics=baseline,
            staged_metrics=staged,
            deltas=deltas,
            dimension_scores=scores,
            net_improvement_score=net_q,
            verdict=verdict,
            veto_flags=veto_flags,
            actionable_directive=directive,
            mixing_suggestions=mixing_suggestions
        )

    # -------------------------------------------------------------------------
    # Dimension Scoring Implementations
    # -------------------------------------------------------------------------
    def _score_groove(
        self,
        baseline: AudioSectionAcousticSnapshot,
        staged: AudioSectionAcousticSnapshot,
        deltas: ContextualAcousticDeltas,
        target_role: str,
        veto_flags: List[str],
        suggestions: List[str]
    ) -> float:
        """Evaluates whether the addition locks with or disrupts the rhythmic pocket."""
        score = 0.50

        # Sub mono correlation loss when adding bass/pad
        if staged.sub_mono_correlation < self.MIN_ALLOWED_SUB_MONO_CORRELATION and target_role in ["bass", "pad_texture"]:
            score -= 0.30
            suggestions.append("Mono-colapsar frecuencias bajo 110 Hz para centrar el golpe de subgraves.")
        elif staged.sub_mono_correlation >= 0.85 and deltas.delta_rms_db > 0.3:
            score += 0.15

        # Rhythmic crest factor collapse
        if deltas.delta_crest_factor_db < -self.MAX_ALLOWED_CREST_FACTOR_LOSS_DB:
            score -= 0.30
            suggestions.append("Reducir compresión o nivel de capa de sostén; se está perdiendo la pegada de la base.")
        elif deltas.delta_crest_factor_db < -1.5:
            score -= 0.15
        elif target_role == "percussion" and deltas.delta_crest_factor_db >= -0.5:
            score += 0.25

        return round(max(0.10, min(1.0, score)), 3)

    def _score_vocal_clearance(
        self,
        baseline: AudioSectionAcousticSnapshot,
        staged: AudioSectionAcousticSnapshot,
        deltas: ContextualAcousticDeltas,
        has_lead_vocal: bool,
        target_role: str,
        veto_flags: List[str],
        suggestions: List[str]
    ) -> float:
        """Evaluates clarity in the crucial vocal intelligibility corridor (1.0 - 3.5 kHz)."""
        if not has_lead_vocal:
            return 0.50

        vocal_boost = deltas.delta_vocal_corridor_db

        if vocal_boost > self.MAX_ALLOWED_VOCAL_MASKING_DB:
            # Fatal Veto: Vocal is severely drowned by the instrument
            veto_flags.append("VOCAL_MASKING_EXCEEDED")
            suggestions.append(
                f"Veto acústico: La mutación invade el corredor vocal (+{vocal_boost:.1f} dB en 1.0–3.5 kHz). "
                "Insertar sidechain dinámico con la voz o dipping con campana de -3 dB en 2.2 kHz."
            )
            return 0.10

        elif vocal_boost > 1.2:
            suggestions.append(
                f"Advertencia de presencia: Aumento de +{vocal_boost:.1f} dB en rango vocal. Monitorear inteligibilidad lírica."
            )
            return 0.35

        elif vocal_boost <= 0.6 and deltas.delta_rms_db > 0.3:
            # Vocal is completely transparent while song gained energy
            return 0.90
        else:
            return 0.50

    def _score_spectral_crowding(
        self,
        baseline: AudioSectionAcousticSnapshot,
        staged: AudioSectionAcousticSnapshot,
        deltas: ContextualAcousticDeltas,
        target_role: str,
        veto_flags: List[str],
        suggestions: List[str]
    ) -> float:
        """Evaluates mud zone (200 - 500 Hz) and sub-bass headroom."""
        mud_boost = deltas.delta_mud_db
        score = 0.50

        if mud_boost > self.MAX_ALLOWED_MUD_BUILDUP_DB:
            veto_flags.append("MUD_ZONE_CONGESTION")
            suggestions.append(
                f"Veto espectral: Exceso de lodo acumulado (+{mud_boost:.1f} dB en 200–500 Hz). "
                "Aplicar filtro notch o high-pass filter inmediato."
            )
            return 0.10

        elif mud_boost > 1.8:
            score -= 0.20
            suggestions.append(f"Atenuar 1.5 dB en 300 Hz para evitar congestión en el rango medio-grave.")
        elif mud_boost <= 0.5 and deltas.delta_rms_db > 0.3:
            score += 0.15

        # Check sub-bass leak for non-bass roles
        if target_role not in ["bass"] and deltas.delta_sub_db > 1.5:
            score -= 0.20
            suggestions.append("Filtrar subgraves (corte HPF en 90 Hz) en elementos no destinados a bajo/bombo.")

        return round(max(0.10, min(1.0, score)), 3)

    def _score_transients(
        self,
        baseline: AudioSectionAcousticSnapshot,
        staged: AudioSectionAcousticSnapshot,
        deltas: ContextualAcousticDeltas,
        target_role: str,
        veto_flags: List[str],
        suggestions: List[str]
    ) -> float:
        """Evaluates crest factor preservation and drum punchiness."""
        loss = -deltas.delta_crest_factor_db

        if loss > self.MAX_ALLOWED_CREST_FACTOR_LOSS_DB:
            veto_flags.append("TRANSIENTS_CRUSHED")
            suggestions.append(
                f"Veto dinámico: Pérdida excesiva de factor de cresta (-{loss:.1f} dB). "
                "La mutación aplasta los transitorios de la batería. Revisar limitador o ataque del compresor."
            )
            return 0.10

        elif loss > 1.8:
            suggestions.append("Ligera pérdida de pegada en transitorios; atenuar nivel o acelerar ataque de capas.")
            return 0.35
        elif deltas.delta_crest_factor_db >= 0.0 and deltas.delta_rms_db > 0.3:
            return 0.65
        else:
            return 0.50

    def _score_energy_trajectory(
        self,
        deltas: ContextualAcousticDeltas,
        section_name: str,
        suggestions: List[str]
    ) -> float:
        """Evaluates whether energy delta conforms to narrative role (Hook vs Verse vs Bridge)."""
        sec_low = section_name.lower()
        d_rms = deltas.delta_rms_db

        if any(w in sec_low for w in ["hook", "chorus", "drop"]):
            # Hooks want energy lift (+0.5 to +3.0 dB)
            if 0.4 <= d_rms <= 3.2:
                return 0.90
            elif d_rms > 3.2:
                suggestions.append(f"El salto de volumen en el Hook es demasiado abrupto (+{d_rms:.1f} dB).")
                return 0.40
            elif d_rms <= 0.05:
                suggestions.append("El Hook requiere mayor impacto energético (la mutación no aportó suficiente pegada).")
                return 0.40
            else:
                return 0.55

        elif any(w in sec_low for w in ["verse", "intro"]):
            # Verses want intimacy or subtle support (-0.5 to +1.2 dB)
            if -0.5 <= d_rms <= 1.2:
                return 0.55
            elif d_rms > 1.2:
                suggestions.append("Demasiada energía para una estrofa; compite con la intimidad de la voz.")
                return 0.35
            else:
                return 0.50

        elif any(w in sec_low for w in ["bridge", "breakdown"]):
            # Breakdown wants spatial contrast without hyper-dense RMS
            if 0.2 <= d_rms <= 1.5 and deltas.delta_stereo_width > 0.0:
                return 0.70
            elif abs(d_rms) < 0.1:
                return 0.50
            return 0.55

        return 0.50

    def _score_space_width(
        self,
        baseline: AudioSectionAcousticSnapshot,
        staged: AudioSectionAcousticSnapshot,
        deltas: ContextualAcousticDeltas,
        veto_flags: List[str],
        suggestions: List[str]
    ) -> float:
        """Evaluates mono compatibility and immersive stereo width."""
        # Absolute fatal veto: anti-phase / stereo cancellation
        if staged.mono_correlation < self.MIN_ALLOWED_MONO_CORRELATION:
            veto_flags.append("MONO_PHASE_COLLAPSE")
            suggestions.append(
                f"Veto crítico de fase: Correlación mono {staged.mono_correlation:.2f} < {self.MIN_ALLOWED_MONO_CORRELATION}. "
                "El sonido sufrirá cancelación destructiva completa al reproducirse en dispositivos mono."
            )
            return 0.05

        score = 0.50
        if staged.mono_correlation < 0.35:
            score -= 0.25
            suggestions.append("Correlación mono baja (riesgo de desfase). Reducir ensanchamiento estéreo excesivo.")
        elif staged.mono_correlation >= 0.55 and deltas.delta_stereo_width > 0.05:
            score += 0.25

        return round(max(0.05, min(1.0, score)), 3)

    def _score_identity(
        self,
        staged: AudioSectionAcousticSnapshot,
        distance_score: float,
        distance_category: str,
        song_dna: Optional[CompositionalDNA]
    ) -> float:
        """Evaluates the timbral distinctiveness and signature of the sound."""
        if distance_category == "radical_discovery":
            return 0.75
        elif distance_category == "balanced_evolution":
            return 0.65
        else:
            return 0.55

    def _score_motif_resonance(
        self,
        distance_score: float,
        distance_category: str,
        song_dna: Optional[CompositionalDNA]
    ) -> float:
        """Evaluates how effectively the mutation reinforces thematic unity."""
        if distance_category == "subtle_recognizable_variation":
            return 0.75
        elif distance_category == "balanced_evolution":
            return 0.65
        else:
            return 0.50

    def _score_sectional_contrast(
        self,
        deltas: ContextualAcousticDeltas,
        staged: AudioSectionAcousticSnapshot,
        section_name: str
    ) -> float:
        """Evaluates textural differentiation added to the section."""
        if abs(deltas.delta_rms_db) > 0.3 or deltas.delta_stereo_width > 0.05:
            step = abs(deltas.delta_rms_db) * 0.10 + staged.stereo_width * 0.15
            return round(min(1.0, 0.55 + step), 3)
        return 0.50

    # -------------------------------------------------------------------------
    # Net Score and Directive Calculation
    # -------------------------------------------------------------------------
    def _calculate_net_improvement_and_verdict(
        self,
        scores: Dict[str, float],
        deltas: ContextualAcousticDeltas,
        veto_flags: List[str],
        section_name: str,
        target_role: str,
        distance_category: str,
        distance_score: float,
        has_lead_vocal: bool
    ) -> Tuple[float, ContextualVerdict, str]:
        """
        Calculates Net Improvement Delta Q and generates clear executive directive:
        Answers: 'Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?'
        """
        weights = {
            ContextualDimension.VOCAL_CLEARANCE.value: 0.22,
            ContextualDimension.SPECTRAL_CROWDING.value: 0.16,
            ContextualDimension.ENERGY_TRAJECTORY.value: 0.15,
            ContextualDimension.TRANSIENTS.value: 0.13,
            ContextualDimension.GROOVE.value: 0.11,
            ContextualDimension.SPACE_WIDTH.value: 0.09,
            ContextualDimension.IDENTITY.value: 0.06,
            ContextualDimension.MOTIF_RESONANCE.value: 0.04,
            ContextualDimension.SECTIONAL_CONTRAST.value: 0.04,
        }

        # Calculate raw composite delta from neutral 0.50
        raw_net = 0.0
        for dim, weight in weights.items():
            s = scores.get(dim, 0.50)
            # Map [0.0, 1.0] -> [-1.0, +1.0]
            raw_net += weight * ((s - 0.50) * 2.0)

        # Fatal vetoes override any positive score into degradation
        if veto_flags:
            net_q = round(min(-0.25, raw_net - 0.35), 3)
            verdict = ContextualVerdict.DEGRADATION

            directive_parts = []
            if "VOCAL_MASKING_EXCEEDED" in veto_flags:
                directive_parts.append(f"ahogar la voz principal (+{deltas.delta_vocal_corridor_db:.1f} dB en 1.0–3.5 kHz)")
            if "TRANSIENTS_CRUSHED" in veto_flags:
                directive_parts.append(f"aplastamiento de batería (-{-deltas.delta_crest_factor_db:.1f} dB de cresta)")
            if "MONO_PHASE_COLLAPSE" in veto_flags:
                directive_parts.append(f"Veto crítico de fase: colapso mono")
            if "MUD_ZONE_CONGESTION" in veto_flags:
                directive_parts.append(f"saturación de graves medios (+{deltas.delta_mud_db:.1f} dB en 200–500 Hz)")

            reasons_str = "; ".join(directive_parts) if directive_parts else ", ".join(veto_flags)
            directive = f"Rechazar o intervenir fader en {section_name} por incompatibilidad acústica: {reasons_str}."
            return net_q, verdict, directive

        # No fatal vetoes: evaluate net score
        net_q = round(raw_net, 3)

        if net_q >= 0.10:
            verdict = ContextualVerdict.DEFINITIVE_IMPROVEMENT
            role_title = target_role.replace("_", " ").title()

            if distance_category == "subtle_recognizable_variation":
                dist_note = f"Preserva el motivo con fidelidad (distancia {distance_score:.2f}) reforzando la memoria temática."
            elif distance_category == "radical_discovery":
                dist_note = f"Aporta metamorfosis audaz (distancia {distance_score:.2f}) elevando el impacto tímbrico."
            else:
                dist_note = f"Evolución balanceada (distancia {distance_score:.2f}) con parentesco orgánico."

            directive = (
                f"Aprobar e integrar {role_title} en {section_name} (ΔQ = +{net_q:.2f}): "
                f"Mejora neta confirmada. Eleva la energía en {deltas.delta_rms_db:+.1f} dB "
                f"manteniendo despejada la voz y conservando la pegada de la base. {dist_note}"
            )
        elif net_q >= 0.0:
            verdict = ContextualVerdict.MARGINAL_BENEFIT
            directive = (
                f"Beneficio marginal en {section_name} (ΔQ = +{net_q:.2f}): No genera problemas acústicos "
                "graves pero su aporte dinámico e identitario es sutil. Considerar automatización de paneo o filtro."
            )
        else:
            verdict = ContextualVerdict.DEGRADATION
            directive = (
                f"Rechazar en {section_name} (ΔQ = {net_q:.2f}): El balance global de la sección empeora ligeramente. "
                "No compensa la pérdida de espacio en la mezcla."
            )

        return net_q, verdict, directive

    # -------------------------------------------------------------------------
    # Helper Math & Audio Signal Utilities
    # -------------------------------------------------------------------------
    def _categorize_distance(self, distance: float) -> str:
        if distance < 0.25:
            return "subtle_recognizable_variation"
        elif distance > 0.88:
            return "radical_discovery"
        else:
            return "balanced_evolution"

    def _load_audio_to_stereo(
        self,
        audio_input: Union[str, Path, np.ndarray],
        sample_rate: int = 44100
    ) -> Tuple[np.ndarray, int]:
        """Loads WAV or numpy array into [2, N] float32 array in [-1.0, 1.0]."""
        if isinstance(audio_input, np.ndarray):
            arr = audio_input.astype(np.float32)
            if arr.ndim == 1:
                # Mono -> Duplicate to Stereo [2, N]
                return np.stack([arr, arr]), sample_rate
            elif arr.ndim == 2:
                if arr.shape[0] == 2:
                    return arr, sample_rate
                elif arr.shape[1] == 2:
                    return arr.T, sample_rate
                else:
                    m = arr.mean(axis=0)
                    return np.stack([m, m]), sample_rate
            return np.zeros((2, 1024), dtype=np.float32), sample_rate

        # It's a file path
        path = Path(audio_input)
        if not path.exists():
            logger.warning(f"Audio file '{path}' not found; returning silence.")
            return np.zeros((2, sample_rate), dtype=np.float32), sample_rate

        with wave.open(str(path), "rb") as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if sampwidth == 2:
            dtype = np.int16
            scale = 32768.0
        elif sampwidth == 4:
            dtype = np.int32
            scale = 2147483648.0
        else:
            dtype = np.uint8
            scale = 128.0

        flat_arr = np.frombuffer(raw_data, dtype=dtype).astype(np.float32) / scale

        if channels == 1:
            stereo = np.stack([flat_arr, flat_arr])
        else:
            stereo = flat_arr.reshape(-1, channels).T[:2]

        return stereo, sr

    def _calculate_frequency_bands(
        self,
        left: np.ndarray,
        right: np.ndarray,
        sample_rate: int
    ) -> Dict[str, float]:
        """Computes RMS energy in dBFS across key psychoacoustic frequency bands."""
        mono = 0.5 * (left + right)
        n = len(mono)
        if n < 16:
            return {b: -96.0 for b in ["sub", "bass", "mud", "mid", "vocal", "high_mid", "air"]}

        fft_vals = np.fft.rfft(mono)
        freqs = np.fft.rfftfreq(n, 1.0 / float(sample_rate))
        power = (np.abs(fft_vals) / n) ** 2

        bands = {
            "sub": (20.0, 90.0),
            "bass": (90.0, 200.0),
            "mud": (200.0, 500.0),
            "mid": (500.0, 1000.0),
            "vocal": (1000.0, 3500.0),
            "high_mid": (3500.0, 8000.0),
            "air": (8000.0, 20000.0),
        }

        results = {}
        for band_name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs < high)
            band_power = np.sum(power[mask])
            rms = math.sqrt(max(1e-12, float(band_power)))
            results[band_name] = 20.0 * math.log10(max(1e-6, rms))

        return results

    def _calculate_sub_mono_correlation(
        self,
        left: np.ndarray,
        right: np.ndarray,
        sample_rate: int
    ) -> float:
        """Computes stereo phase correlation strictly for frequencies under 120 Hz."""
        n = len(left)
        if n < 32:
            return 1.0

        fft_l = np.fft.rfft(left)
        fft_r = np.fft.rfft(right)
        freqs = np.fft.rfftfreq(n, 1.0 / float(sample_rate))

        sub_mask = freqs <= 120.0
        sub_l = np.fft.irfft(fft_l * sub_mask, n)
        sub_r = np.fft.irfft(fft_r * sub_mask, n)

        denom = np.sqrt(np.sum(sub_l ** 2)) * np.sqrt(np.sum(sub_r ** 2))
        if denom > 1e-9:
            corr = float(np.sum(sub_l * sub_r) / denom)
            return max(-1.0, min(1.0, corr))
        return 1.0

    # -------------------------------------------------------------------------
    # Physical Test Synthesis Utility
    # -------------------------------------------------------------------------
    @classmethod
    def synthesize_test_section(
        cls,
        section_name: str = "Hook 3",
        duration_sec: float = 1.0,
        sample_rate: int = 44100,
        has_vocal: bool = True,
        add_clean_pad: bool = False,
        add_vocal_clash: bool = False,
        add_phase_inversion: bool = False,
        add_mud_drone: bool = False,
        add_squash_limiting: bool = False
    ) -> np.ndarray:
        """
        Synthesizes deterministic physical audio arrays for testing in-situ critique.
        Returns stereo numpy array [2, N].
        """
        n_samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, n_samples, endpoint=False)

        # Base drums: Kick (60 Hz punch) + Hi-hat (10 kHz burst)
        kick_freq = 60.0 * np.exp(-t * 12.0)
        kick = 0.50 * np.sin(2.0 * np.pi * kick_freq * t) * np.exp(-t * 8.0)
        hihat = 0.15 * (np.random.rand(n_samples) * 2.0 - 1.0) * (np.sin(2.0 * np.pi * 10000.0 * t))

        # Base Bass: 100 Hz
        bass = 0.35 * np.sin(2.0 * np.pi * 100.0 * t)

        # Baseline Left and Right
        l = kick + bass + hihat
        r = kick + bass + hihat

        # Lead Vocal (2200 Hz tone + harmonics)
        if has_vocal:
            vocal_l = 0.40 * np.sin(2.0 * np.pi * 2200.0 * t)
            vocal_r = 0.40 * np.sin(2.0 * np.pi * 2200.0 * t)
            l += vocal_l
            r += vocal_r

        # Clean Staged Pad (650 Hz shimmer with stereo width)
        if add_clean_pad:
            pad_l = 0.25 * np.sin(2.0 * np.pi * 650.0 * t)
            pad_r = 0.25 * np.sin(2.0 * np.pi * 650.0 * t + math.pi / 4.0)  # Gentle stereo phase
            l += pad_l
            r += pad_r

        # Vocal Clash Synth (Huge 2200 Hz square wave)
        if add_vocal_clash:
            clash = 0.70 * np.sign(np.sin(2.0 * np.pi * 2200.0 * t))
            l += clash
            r += clash

        # Phase Inversion (Anti-phase: Right = -Left)
        if add_phase_inversion:
            r = -l

        # Mud Drone (Heavy 300 Hz accumulation)
        if add_mud_drone:
            mud = 0.85 * np.sin(2.0 * np.pi * 300.0 * t)
            l += mud
            r += mud

        # Squash limiting (Destroys crest factor)
        if add_squash_limiting:
            l = np.clip(l * 3.0, -0.6, 0.6)
            r = np.clip(r * 3.0, -0.6, 0.6)

        return np.stack([l.astype(np.float32), r.astype(np.float32)])

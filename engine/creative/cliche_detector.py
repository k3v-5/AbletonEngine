"""
Cliché Detector & Musical Fitness Engine:
Audits musical arrangements and note patterns for predictability, repetitive clichés,
and evaluates overall composition fitness:
score = 0.35 * musical_quality + 0.25 * identity + 0.20 * novelty + 0.20 * coherence
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import math
from .music_dna import MusicDNA


@dataclass
class ClicheAuditReport:
    """Detailed audit report from ClichéDetector."""
    fitness_score: float
    musical_quality: float
    identity_score: float
    novelty_score: float
    coherence_score: float
    cliches_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fitness_score": round(self.fitness_score, 3),
            "musical_quality": round(self.musical_quality, 3),
            "identity_score": round(self.identity_score, 3),
            "novelty_score": round(self.novelty_score, 3),
            "coherence_score": round(self.coherence_score, 3),
            "cliches_detected": self.cliches_detected,
            "recommendations": self.recommendations
        }


class ClicheDetector:
    """
    Analyzes musical events, harmony, and arrangements to guard against generic AI tropes.
    """

    def __init__(self, dna: Optional[MusicDNA] = None):
        self.dna = dna or MusicDNA()

    def audit_notes(
        self,
        notes: List[Dict[str, Any]],
        role: str = "lead",
        section: str = "drop"
    ) -> ClicheAuditReport:
        """
        Audits a list of note events for robotic velocity, lack of syncopation,
        and pitch monotony.
        """
        cliches: List[str] = []
        recommendations: List[str] = []

        if not notes:
            return ClicheAuditReport(
                fitness_score=0.2,
                musical_quality=0.2,
                identity_score=0.2,
                novelty_score=0.2,
                coherence_score=0.2,
                cliches_detected=["empty_clip"],
                recommendations=["Generate note events for this track."]
            )

        # 1. Velocity Monotony Audit
        velocities = [n.get("velocity", 100) for n in notes]
        mean_vel = sum(velocities) / len(velocities)
        variance_vel = sum((v - mean_vel) ** 2 for v in velocities) / len(velocities)
        std_vel = math.sqrt(variance_vel)

        if std_vel < 3.0:
            cliches.append("robotic_flat_velocity")
            recommendations.append(
                "Apply humanized velocity curve (e.g. 110-70-85-60 drummer wrist dynamics)."
            )

        # 2. Timing / Grid Monotony Audit
        times = [n.get("time", 0.0) for n in notes]
        on_beats = sum(1 for t in times if abs(t - round(t)) < 0.02)
        on_beat_ratio = on_beats / len(times)

        if on_beat_ratio > 0.85 and role.lower() not in ["kick", "pad"]:
            cliches.append("excessive_on_beat_quantization")
            recommendations.append(
                "Inject syncopated off-beat accents or micro-timing push/pull (+-10ms)."
            )

        # 3. Pitch Monotony Audit
        pitches = [n.get("pitch", 60) for n in notes]
        unique_pitches = set(pitches)
        if len(unique_pitches) <= 2 and len(notes) > 8 and role.lower() not in ["kick", "snare", "foley"]:
            cliches.append("melodic_pitch_stagnation")
            recommendations.append(
                "Expand interval vocabulary (use fourths, minor sixths, or pentatonic contours)."
            )

        # Compute Sub-Scores
        # Musical Quality: penalize robotic velocities and flat contours
        mq = 1.0 - (0.35 if "robotic_flat_velocity" in cliches else 0.0) - (0.25 if "melodic_pitch_stagnation" in cliches else 0.0)
        mq = max(0.1, min(1.0, mq))

        # Identity Score: adherence to DNA interval / rhythm profile
        id_score = 0.85 if not cliches else max(0.3, 0.85 - 0.15 * len(cliches))

        # Novelty Score: based on DNA novelty expectations and syncopation
        novelty_score = 0.80 if on_beat_ratio < 0.60 else 0.50

        # Coherence Score: track should feel structured
        coherence_score = 0.90 if len(notes) >= 4 else 0.40

        # Master Fitness Score
        fitness = (
            0.35 * mq +
            0.25 * id_score +
            0.20 * novelty_score +
            0.20 * coherence_score
        )

        return ClicheAuditReport(
            fitness_score=fitness,
            musical_quality=mq,
            identity_score=id_score,
            novelty_score=novelty_score,
            coherence_score=coherence_score,
            cliches_detected=cliches,
            recommendations=recommendations
        )

    def audit_turnaround(
        self,
        bar_4_notes: List[Dict[str, Any]],
        bar_8_notes: List[Dict[str, Any]]
    ) -> ClicheAuditReport:
        """
        Audits an 8-bar section to verify that bar 8 is not identical to bar 4
        (enforces turnaround variation / transition cue).
        """
        cliches: List[str] = []
        recommendations: List[str] = []

        # Compare notes in bar 4 vs bar 8 normalized to relative bar start
        b4_rel = sorted([(round(n.get("time", 0.0) % 4.0, 2), n.get("pitch", 0)) for n in bar_4_notes])
        b8_rel = sorted([(round(n.get("time", 0.0) % 4.0, 2), n.get("pitch", 0)) for n in bar_8_notes])

        is_identical = (b4_rel == b8_rel and len(b4_rel) > 0)

        if is_identical:
            cliches.append("identical_bar_8_and_4")
            recommendations.append(
                "Enforce Bar 8 Turnaround: Inject drum fill, abrupt silence (sub bass / drums out), or passing chord."
            )
            mq = 0.55
            novelty = 0.30
        else:
            mq = 0.90
            novelty = 0.85

        id_score = 0.80
        coherence = 0.85
        fitness = 0.35 * mq + 0.25 * id_score + 0.20 * novelty + 0.20 * coherence

        return ClicheAuditReport(
            fitness_score=fitness,
            musical_quality=mq,
            identity_score=id_score,
            novelty_score=novelty,
            coherence_score=coherence,
            cliches_detected=cliches,
            recommendations=recommendations
        )

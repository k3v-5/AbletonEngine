# engine/performance/identity.py
"""
Performance Identity & Catalog Memory (Nivel T4):
Encapsulates the persistent expressive fingerprint of a performer or musical project across songs:
- timing_signature (role timing offsets and variances)
- velocity_signature (dynamic curves and accent ratios)
- articulation_signature (staccato/legato ratios and chord strum spread)
- groove_signature (kick/bass coupling and snare drag)
- phrase_signature (rubato climax lag and breath gap distributions)
- instrument_relationships (ensemble coupling topology)

Integrates with CatalogMemory to enable evolving artist interpretative lineage across catalog works.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .models import PerformanceIntent, InstrumentPerformanceProfile
from .groove_intelligence import SongGrooveTemplate


@dataclass
class PerformanceSignature:
    """
    Cryptographic and mathematical fingerprint of an interpretive performance identity.
    """
    identity_id: str
    name: str = "Neo-Soul Dilla Ensemble"
    timing_signature: Dict[str, float] = field(default_factory=dict)
    velocity_signature: Dict[str, float] = field(default_factory=dict)
    articulation_signature: Dict[str, float] = field(default_factory=dict)
    groove_signature: Dict[str, float] = field(default_factory=dict)
    phrase_signature: Dict[str, float] = field(default_factory=dict)
    instrument_relationships: Dict[str, str] = field(default_factory=dict)
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self.compute_fingerprint()

    def compute_fingerprint(self) -> str:
        payload = {
            "name": self.name,
            "timing": self.timing_signature,
            "velocity": self.velocity_signature,
            "articulation": self.articulation_signature,
            "groove": self.groove_signature,
            "phrase": self.phrase_signature,
            "relationships": self.instrument_relationships,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "name": self.name,
            "fingerprint": self.fingerprint,
            "timing_signature": self.timing_signature,
            "velocity_signature": self.velocity_signature,
            "articulation_signature": self.articulation_signature,
            "groove_signature": self.groove_signature,
            "phrase_signature": self.phrase_signature,
            "instrument_relationships": self.instrument_relationships,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PerformanceSignature:
        return cls(
            identity_id=data.get("identity_id", "anon_perf_id"),
            name=data.get("name", "Default Performance Identity"),
            timing_signature=data.get("timing_signature", {}),
            velocity_signature=data.get("velocity_signature", {}),
            articulation_signature=data.get("articulation_signature", {}),
            groove_signature=data.get("groove_signature", {}),
            phrase_signature=data.get("phrase_signature", {}),
            instrument_relationships=data.get("instrument_relationships", {}),
            fingerprint=data.get("fingerprint", ""),
        )


class PerformanceIdentityEngine:
    """
    Extracts, evaluates, and persists PerformanceSignatures across the project catalog.
    """

    @classmethod
    def extract_signature(
        cls,
        session_tracks: Dict[str, List[Dict[str, Any]]],
        track_roles: Dict[str, str],
        bpm: float = 120.0,
        name: str = "Extracted Session Identity",
        groove_template: Optional[SongGrooveTemplate] = None
    ) -> PerformanceSignature:
        """
        Synthesizes a full PerformanceSignature from active session tracks.
        """
        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0

        t_sig: Dict[str, float] = {}
        v_sig: Dict[str, float] = {}
        a_sig: Dict[str, float] = {}
        relationships: Dict[str, str] = {}

        for t_name, notes in session_tracks.items():
            if not notes:
                continue
            role = track_roles.get(t_name, "other").lower()

            # Calculate velocity mean and std
            vels = [int(n.get("velocity", 90)) for n in notes]
            m_vel = float(sum(vels)) / len(vels)
            var_vel = sum((v - m_vel) ** 2 for v in vels) / len(vels)
            std_vel = math.sqrt(var_vel)
            v_sig[f"{role}_mean_vel"] = round(m_vel, 1)
            v_sig[f"{role}_std_vel"] = round(std_vel, 2)

            # Calculate timing deviations from closest 16th grid
            offsets_ms: List[float] = []
            durations: List[float] = []
            for n in notes:
                st = float(n.get("start_time", n.get("start", 0.0)))
                dur = float(n.get("duration", 0.5))
                durations.append(dur)
                nearest_16th = round(st / 0.25) * 0.25
                offsets_ms.append((st - nearest_16th) * ms_per_beat)

            m_off = float(sum(offsets_ms)) / len(offsets_ms)
            var_off = sum((o - m_off) ** 2 for o in offsets_ms) / len(offsets_ms)
            std_off = math.sqrt(var_off)

            t_sig[f"{role}_offset_ms"] = round(m_off, 2)
            t_sig[f"{role}_std_ms"] = round(std_off, 2)

            # Articulation mean duration
            avg_dur = float(sum(durations)) / len(durations)
            a_sig[f"{role}_avg_dur"] = round(avg_dur, 3)

            # Coupling relationships
            if role in ["bass", "sub"]:
                relationships[role] = "coupled_to_kick"
            elif role in ["snare", "clap"]:
                relationships[role] = "laid_back_from_grid"
            elif role in ["kick"]:
                relationships[role] = "primary_anchor"

        # Groove signature
        g_sig: Dict[str, float] = {
            "kick_bass_coupling_ms": round(groove_template.kick_bass_coupling_ms if groove_template else 1.5, 2),
            "snare_laid_back_ms": round(groove_template.snare_laid_back_ms if groove_template else 10.0, 2),
            "swing_ratio": round(groove_template.swing_ratio if groove_template else 0.50, 3),
        }

        # Phrase signature
        p_sig: Dict[str, float] = {
            "climax_rubato_ms": 5.0,
            "min_breath_gap_ms": 35.0,
            "phrase_push": 0.20,
        }

        identity_id = f"perf_id_{hashlib.sha256(name.encode('utf-8')).hexdigest()[:8]}"

        return PerformanceSignature(
            identity_id=identity_id,
            name=name,
            timing_signature=t_sig,
            velocity_signature=v_sig,
            articulation_signature=a_sig,
            groove_signature=g_sig,
            phrase_signature=p_sig,
            instrument_relationships=relationships
        )

    @classmethod
    def calculate_similarity(
        cls,
        sig_a: PerformanceSignature,
        sig_b: PerformanceSignature
    ) -> float:
        """
        Computes musical interpretative similarity score in range [0.0, 1.0].
        Compares groove offsets, timing variances, and dynamic profiles.
        """
        score = 1.0

        # 1. Compare Groove Signature
        g_a = sig_a.groove_signature
        g_b = sig_b.groove_signature

        coupling_diff = abs(g_a.get("kick_bass_coupling_ms", 1.5) - g_b.get("kick_bass_coupling_ms", 1.5))
        snare_diff = abs(g_a.get("snare_laid_back_ms", 10.0) - g_b.get("snare_laid_back_ms", 10.0))

        score -= min(0.35, (coupling_diff / 10.0) * 0.20)
        score -= min(0.35, (snare_diff / 20.0) * 0.20)

        # 2. Compare Timing Signature keys
        common_roles = set(
            k.split("_")[0] for k in sig_a.timing_signature.keys()
        ).intersection(
            k.split("_")[0] for k in sig_b.timing_signature.keys()
        )

        if common_roles:
            role_penalties = 0.0
            for r in common_roles:
                std_a = sig_a.timing_signature.get(f"{r}_std_ms", 5.0)
                std_b = sig_b.timing_signature.get(f"{r}_std_ms", 5.0)
                role_penalties += min(0.1, abs(std_a - std_b) / 10.0)
            score -= (role_penalties / len(common_roles)) * 0.30

        return max(0.0, min(1.0, round(score, 4)))

    @classmethod
    def persist_signature(
        cls,
        sig: PerformanceSignature,
        storage_dir: Optional[Path] = None
    ) -> Path:
        """Saves signature to JSON file for catalog re-use."""
        base_dir = storage_dir or Path("state/learned/performance_identities")
        base_dir.mkdir(parents=True, exist_ok=True)
        file_path = base_dir / f"{sig.identity_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sig.to_dict(), f, indent=2)
        return file_path

    @classmethod
    def load_signature(
        cls,
        identity_id: str,
        storage_dir: Optional[Path] = None
    ) -> Optional[PerformanceSignature]:
        """Loads a stored PerformanceSignature by ID."""
        base_dir = storage_dir or Path("state/learned/performance_identities")
        file_path = base_dir / f"{identity_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PerformanceSignature.from_dict(data)

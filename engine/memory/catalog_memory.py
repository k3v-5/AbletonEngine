# engine/memory/catalog_memory.py
"""
Catalog Memory & Cross-Song Identity (Phase O):
Tracks historical production decisions across the creator's entire song catalog.
Prevents the AI from unconsciously repeating 'favorite recipes':
e.g. If Song 1 and Song 2 both used Rhodes + vinyl texture + reverse vocal,
CatalogMemory detects the clash, sounds a CatalogRedundancyConflict alarm,
and suggests unmapped sonic and harmonic territory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Set
import datetime
import json
import logging
import os

logger = logging.getLogger("CatalogMemory")


class ConflictSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL_CLICHE = "CRITICAL_CLICHE"


@dataclass
class SongCatalogRecord:
    """Archival fingerprint of a previously produced song."""
    song_id: str
    title: str
    key_root: str = "C"
    key: Optional[str] = None
    scale: str = "minor"
    bpm: float = 120.0
    genre: str = "neo_soul"
    instrument_roles: Dict[str, str] = field(default_factory=dict)  # role -> plugin/timbre name
    instrument_plugins: List[str] = field(default_factory=list)
    sound_design_recipes: List[str] = field(default_factory=list)   # e.g. ["vinyl_dust", "reverse_vocal"]
    signature_gestures: List[str] = field(default_factory=list)     # e.g. ["pre_hook_vacuum_drop"]
    signature_textures: List[str] = field(default_factory=list)
    groove_style: str = "analog_human"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def __post_init__(self):
        if self.key is not None:
            self.key_root = self.key
        else:
            self.key = self.key_root

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "title": self.title,
            "key_root": self.key_root,
            "scale": self.scale,
            "bpm": round(self.bpm, 1),
            "instrument_roles": self.instrument_roles,
            "sound_design_recipes": self.sound_design_recipes,
            "signature_gestures": self.signature_gestures,
            "groove_style": self.groove_style,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SongCatalogRecord:
        return cls(
            song_id=data.get("song_id", ""),
            title=data.get("title", ""),
            key_root=data.get("key_root", "C"),
            scale=data.get("scale", "minor"),
            bpm=float(data.get("bpm", 120.0)),
            instrument_roles=data.get("instrument_roles", {}),
            sound_design_recipes=data.get("sound_design_recipes", []),
            signature_gestures=data.get("signature_gestures", []),
            groove_style=data.get("groove_style", "analog_human"),
            created_at=data.get("created_at", ""),
        )


@dataclass
class CatalogConflict:
    """Detailed clash report between a proposed work and previous catalog pieces."""
    severity: ConflictSeverity
    conflicting_song_id: str
    conflicting_song_title: str
    overlap_type: str  # "RECIPE_REDUNDANCY", "INSTRUMENTATION_CLICHE", "TONAL_POCKET_CLASH"
    overlapping_items: List[str]
    similarity_score: float
    warning_message: str
    suggested_alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "conflicting_song_id": self.conflicting_song_id,
            "conflicting_song_title": self.conflicting_song_title,
            "overlap_type": self.overlap_type,
            "overlapping_items": self.overlapping_items,
            "similarity_score": round(self.similarity_score, 2),
            "warning_message": self.warning_message,
            "suggested_alternatives": self.suggested_alternatives,
        }


class CatalogMemory:
    """
    Global memory repository overseeing cross-song artistic diversity.
    Enforces catalog uniqueness and discourages repetitive aesthetic crutches.
    """

    # Library of diversification substitutes when a formula is overused
    DIVERSIFICATION_ALTERNATIVES = {
        "rhodes": ["FM Crystal Electric Piano", "Muted Granular Electric Guitar", "Warm Analog Poly Brass", "Upright Felt Piano"],
        "vinyl_dust": ["Cassette Tape Hiss", "Organic Room Foliage Creaks", "Hydrophone Water Bubbles", "Magnetic Ribbon Hum"],
        "reverse_vocal": ["Resynthesized Flute Chops", "Granular Bell Shimmer", "Spectral Reverse Mallet", "Distorted Comb-Filtered Lead"],
        "sublab": ["Moog Ladder Filter Bass", "Oberheim SEM Saw Bass", "808 Distorted Saturator", "Double Bass Slap"],
        "808": ["Acoustic Upright Sub", "Drift Pulse Bass", "Modular FM Sub-Drop", "Analog Lab Taurus Sub"],
    }

    def __init__(self):
        self.records: List[SongCatalogRecord] = []

    @property
    def songs(self) -> List[SongCatalogRecord]:
        """Provides direct list access to catalog song records."""
        return self.records

    def register_song(self, record: SongCatalogRecord) -> None:
        """Adds a completed or in-progress song to the catalog memory."""
        # Replace if existing song_id
        self.records = [r for r in self.records if r.song_id != record.song_id]
        self.records.append(record)
        logger.info(f"Registered song '{record.title}' ({record.song_id}) in CatalogMemory. Total catalog size: {len(self.records)}")

    def register_completed_song(self, record: SongCatalogRecord) -> None:
        """Alias for register_song."""
        return self.register_song(record)

    def audit_proposal(
        self,
        proposed_instruments: Dict[str, str],
        proposed_recipes: List[str],
        key_root: str,
        bpm: float,
        current_song_id: Optional[str] = None
    ) -> List[CatalogConflict]:
        """
        Audits a proposed production concept against the historical catalog.
        Returns conflicts if the combination mimics an existing song too closely.
        """
        conflicts: List[CatalogConflict] = []

        for rec in self.records:
            if current_song_id and rec.song_id == current_song_id:
                continue

            # 1. Check Recipe Redundancy (e.g. Rhodes + vinyl + reverse vocal)
            common_recipes = set(proposed_recipes).intersection(set(rec.sound_design_recipes))
            recipe_similarity = len(common_recipes) / max(1, len(set(proposed_recipes).union(set(rec.sound_design_recipes))))

            # 2. Check Instrument Overlap
            proposed_plugins = {p.lower() for p in proposed_instruments.values()}
            rec_plugins = {p.lower() for p in rec.instrument_roles.values()}
            common_plugins = proposed_plugins.intersection(rec_plugins)
            plugin_similarity = len(common_plugins) / max(1, len(proposed_plugins.union(rec_plugins)))

            # 3. Check Tonal & Tempo Clustering
            tonal_match = (key_root.lower() == rec.key_root.lower())
            tempo_match = abs(bpm - rec.bpm) < 4.0

            # Composite Similarity Index
            composite_similarity = (recipe_similarity * 0.45) + (plugin_similarity * 0.40) + (0.15 if (tonal_match and tempo_match) else 0.0)

            if composite_similarity >= 0.50:
                overlapping_features = list(common_recipes) + [p for p in common_plugins]
                alternatives: List[str] = []
                for item in overlapping_features:
                    clean_item = item.lower().replace("_", " ")
                    for key, alts in self.DIVERSIFICATION_ALTERNATIVES.items():
                        if key in clean_item:
                            alternatives.extend(alts[:2])

                sev = ConflictSeverity.CRITICAL_CLICHE if composite_similarity >= 0.70 else ConflictSeverity.WARNING
                warning = (
                    f"Catalog Redundancy Conflict with '{rec.title}' ({rec.song_id}): "
                    f"{composite_similarity*100:.1f}% aesthetic overlap detected "
                    f"(common features: {', '.join(overlapping_features[:4])})."
                )

                conflicts.append(CatalogConflict(
                    severity=sev,
                    conflicting_song_id=rec.song_id,
                    conflicting_song_title=rec.title,
                    overlap_type="RECIPE_REDUNDANCY",
                    overlapping_items=overlapping_features,
                    similarity_score=composite_similarity,
                    warning_message=warning,
                    suggested_alternatives=list(set(alternatives))[:5]
                ))

        return conflicts

    def calculate_catalog_diversity_index(self) -> float:
        """
        Calculates catalog-wide timbral and harmonic dispersion.
        0.0 = completely monolithic / repetitive.
        1.0 = richly varied and diverse across keys, tempos, and instruments.
        """
        if len(self.records) <= 1:
            return 1.0  # Default pristine diversity for solitary piece

        all_keys = {r.key_root for r in self.records}
        all_instruments = {
            inst for r in self.records
            for inst in (list(r.instrument_roles.values()) + getattr(r, "instrument_plugins", []))
        }
        all_recipes = {rcp for r in self.records for rcp in r.sound_design_recipes}

        key_diversity = min(1.0, len(all_keys) / max(1, len(self.records)))
        inst_diversity = min(1.0, len(all_instruments) / max(1, (len(self.records) * 3)))
        recipe_diversity = min(1.0, len(all_recipes) / max(1, (len(self.records) * 2)))

        return round((key_diversity * 0.35) + (inst_diversity * 0.40) + (recipe_diversity * 0.25), 3)

    def calculate_diversity_index(self) -> float:
        """Alias for calculate_catalog_diversity_index."""
        return self.calculate_catalog_diversity_index()

    def evaluate_proposal_against_catalog(self, proposal: Dict[str, Any]) -> List[CatalogConflict]:
        """Convenience evaluation adapter for dictionary proposals."""
        plugins = proposal.get("instrument_plugins") or proposal.get("plugins", [])
        instruments = {f"role_{i}": str(p) for i, p in enumerate(plugins)}
        recipes = [str(r) for r in proposal.get("recipes", [])]
        key = str(proposal.get("key", "C"))
        bpm = float(proposal.get("bpm", 120.0))
        return self.audit_proposal(instruments, recipes, key, bpm)

    def audit_audio_provenance(self, song_id: str, provenance_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Audits audio provenance records for a song in the catalog.
        Verifies that no UNKNOWN audio exists and returns autogenous lineage metrics.
        """
        total = len(provenance_records)
        unprovenanced = [r for r in provenance_records if str(r.get("origin", "")).lower() == "unknown"]
        autogenous = [r for r in provenance_records if str(r.get("origin", "")).lower() in ("original_generated", "derived_from_song")]
        return {
            "song_id": song_id,
            "total_samples": total,
            "compliant": len(unprovenanced) == 0,
            "unprovenanced_count": len(unprovenanced),
            "autogenous_ratio": round(len(autogenous) / max(1, total), 3) if total > 0 else 1.0,
            "is_closed_ecosystem": len(unprovenanced) == 0 and len(autogenous) == total,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_songs": len(self.records),
            "catalog_diversity_index": self.calculate_catalog_diversity_index(),
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CatalogMemory:
        cat = cls()
        cat.records = [SongCatalogRecord.from_dict(r) for r in data.get("records", [])]
        return cat


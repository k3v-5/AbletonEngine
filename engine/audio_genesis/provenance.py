# engine/audio_genesis/provenance.py
"""
Audio Provenance Engine:
Enforces strict audio provenance and lineage tracking for all creative audio materials.

Rule 1: Source Policy
Each audio source must possess a verifiable SampleOrigin.
Audio marked as UNKNOWN has creative_usage = FORBIDDEN and deterministically
raises CreativeGovernanceError unless an explicit bypass is provided.

Every generated sample answers:
'¿De dónde salió este audio?' with a full genealogical trace:
Source (track, clip, bars, midi) -> Instrument -> Processing Chain -> Render Metadata -> Destination.
"""

from __future__ import annotations
import uuid
import datetime
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("AudioProvenanceEngine")


class SampleOrigin(str, Enum):
    """Classification of audio source origin."""
    ORIGINAL_GENERATED = "original_generated"  # Rendered directly from MIDI/instrument in this song
    DERIVED_FROM_SONG = "derived_from_song"    # Mutated/resampled from an existing provenanced render
    USER_IMPORTED = "user_imported"            # Explicitly imported by the human producer
    CATALOG_SAMPLE = "catalog_sample"          # Authorized sample from the verified catalog memory
    UNKNOWN = "unknown"                        # Unverified / arbitrary audio without lineage


class CreativeUsagePolicy(str, Enum):
    """Permission policy for using audio as raw creative material."""
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"


class CreativeGovernanceError(RuntimeError):
    """Raised when an unprovenanced or forbidden audio source is used creatively."""
    pass


@dataclass
class AudioSourceLocation:
    """Precise location of the musical source within the project."""
    source_type: str = "generated_render"  # generated_render, derived_render, user_imported, catalog_sample
    track: str = "Master"
    clip: str = "Main"
    bars: Tuple[int, int] = (1, 8)
    midi_source: bool = True
    midi_notes_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "track": self.track,
            "clip": self.clip,
            "bars": list(self.bars),
            "midi_source": self.midi_source,
            "midi_notes_hash": self.midi_notes_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioSourceLocation:
        bars_val = data.get("bars", [1, 8])
        return cls(
            source_type=data.get("source_type", "generated_render"),
            track=data.get("track", "Master"),
            clip=data.get("clip", "Main"),
            bars=(int(bars_val[0]), int(bars_val[1])),
            midi_source=bool(data.get("midi_source", True)),
            midi_notes_hash=data.get("midi_notes_hash"),
        )


@dataclass
class InstrumentProvenance:
    """Instrument and sound engine details generating the initial raw audio."""
    device: str = "Unknown Synth"
    preset: str = ""
    device_category: str = "synth"  # synth, keys, bass, drums, orchestral, sampler

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "preset": self.preset,
            "device_category": self.device_category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InstrumentProvenance:
        return cls(
            device=data.get("device", "Unknown Synth"),
            preset=data.get("preset", ""),
            device_category=data.get("device_category", "synth"),
        )


@dataclass
class ProcessingStep:
    """A discrete processing or transformation step applied to the audio."""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProcessingStep:
        return cls(
            name=data.get("name", "generic_process"),
            parameters=dict(data.get("parameters", {})),
        )


@dataclass
class RenderMetadata:
    """Physical acoustic attributes of the rendered audio material."""
    format: str = "wav"
    duration_sec: float = 2.0
    sample_rate: int = 44100
    channels: int = 2
    peak_dbfs: float = -6.0
    rms_dbfs: float = -18.0
    file_path: Optional[str] = None
    content_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "duration_sec": round(self.duration_sec, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "peak_dbfs": round(self.peak_dbfs, 2),
            "rms_dbfs": round(self.rms_dbfs, 2),
            "file_path": self.file_path,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RenderMetadata:
        return cls(
            format=data.get("format", "wav"),
            duration_sec=float(data.get("duration_sec", 2.0)),
            sample_rate=int(data.get("sample_rate", 44100)),
            channels=int(data.get("channels", 2)),
            peak_dbfs=float(data.get("peak_dbfs", -6.0)),
            rms_dbfs=float(data.get("rms_dbfs", -18.0)),
            file_path=data.get("file_path"),
            content_hash=data.get("content_hash", ""),
        )


@dataclass
class SampleProvenanceRecord:
    """
    Immutable birth certificate and genealogical dossier for an audio sample.
    Answers unequivocally: '¿De dónde salió este audio?'
    """
    sample_id: str
    origin: SampleOrigin
    source: AudioSourceLocation
    instrument: InstrumentProvenance
    processing: List[ProcessingStep] = field(default_factory=list)
    render: RenderMetadata = field(default_factory=RenderMetadata)
    destination: str = "Simpler"
    parent_sample_id: Optional[str] = None
    generation_depth: int = 0
    song_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def creative_usage(self) -> CreativeUsagePolicy:
        """Determines whether creative usage is permitted based on origin."""
        if self.origin == SampleOrigin.UNKNOWN:
            return CreativeUsagePolicy.FORBIDDEN
        return CreativeUsagePolicy.ALLOWED

    @property
    def is_autogenous(self) -> bool:
        """True if derived entirely from this song's own composition."""
        return self.origin in (SampleOrigin.ORIGINAL_GENERATED, SampleOrigin.DERIVED_FROM_SONG)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "origin": self.origin.value if isinstance(self.origin, SampleOrigin) else str(self.origin),
            "creative_usage": self.creative_usage.value,
            "source": self.source.to_dict(),
            "instrument": self.instrument.to_dict(),
            "processing": [p.to_dict() for p in self.processing],
            "render": self.render.to_dict(),
            "destination": self.destination,
            "parent_sample_id": self.parent_sample_id,
            "generation_depth": self.generation_depth,
            "song_id": self.song_id,
            "created_at": self.created_at,
            "is_autogenous": self.is_autogenous,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SampleProvenanceRecord:
        o_str = data.get("origin", "unknown")
        try:
            origin = SampleOrigin(o_str)
        except ValueError:
            origin = SampleOrigin.UNKNOWN

        return cls(
            sample_id=data.get("sample_id", f"sample_{str(uuid.uuid4())[:8]}"),
            origin=origin,
            source=AudioSourceLocation.from_dict(data.get("source", {})),
            instrument=InstrumentProvenance.from_dict(data.get("instrument", {})),
            processing=[ProcessingStep.from_dict(p) for p in data.get("processing", [])],
            render=RenderMetadata.from_dict(data.get("render", {})),
            destination=data.get("destination", "Simpler"),
            parent_sample_id=data.get("parent_sample_id"),
            generation_depth=int(data.get("generation_depth", 0)),
            song_id=data.get("song_id", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass
class GenealogicalNode:
    """A node in the genealogical ancestry tree."""
    record: SampleProvenanceRecord
    children: List[GenealogicalNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record": self.record.to_dict(),
            "children": [c.to_dict() for c in self.children],
        }


class AudioGenealogyTree:
    """Maintains and visualizes the complete ancestry tree of generated audio."""

    def __init__(self):
        self.records: Dict[str, SampleProvenanceRecord] = {}
        self.children_map: Dict[Optional[str], List[str]] = {}

    def add_record(self, record: SampleProvenanceRecord) -> None:
        self.records[record.sample_id] = record
        parent = record.parent_sample_id
        if parent not in self.children_map:
            self.children_map[parent] = []
        if record.sample_id not in self.children_map[parent]:
            self.children_map[parent].append(record.sample_id)

    def get_lineage(self, sample_id: str) -> List[SampleProvenanceRecord]:
        """Traces back ancestry from a sample to the original root."""
        lineage = []
        curr = self.records.get(sample_id)
        while curr:
            lineage.append(curr)
            curr = self.records.get(curr.parent_sample_id) if curr.parent_sample_id else None
        return list(reversed(lineage))

    def render_ascii_tree(self, sample_id: Optional[str] = None) -> str:
        """Renders an ASCII visualization of the genealogical tree."""
        roots = [sample_id] if sample_id and sample_id in self.records else self.children_map.get(None, [])
        if not roots:
            return "Empty Genealogy Tree."

        lines = ["ORIGINAL SONG GENESIS"]

        def _walk(sid: str, prefix: str, is_last: bool):
            rec = self.records.get(sid)
            if not rec:
                return
            branch = "└── " if is_last else "├── "
            desc = f"{rec.sample_id} [{rec.origin.value}] ({rec.source.track}) -> {rec.destination}"
            if rec.processing:
                procs = ", ".join(p.name for p in rec.processing)
                desc += f" | FX: [{procs}]"
            lines.append(prefix + branch + desc)

            children = self.children_map.get(sid, [])
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child_id in enumerate(children):
                _walk(child_id, new_prefix, i == len(children) - 1)

        for i, root_id in enumerate(roots):
            _walk(root_id, "│   ", i == len(roots) - 1)

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_count": len(self.records),
            "records": {k: v.to_dict() for k, v in self.records.items()},
        }


class AudioProvenanceEngine:
    """
    Central governance and tracking engine for audio provenance.
    Verifies that creative workflows never ingest unprovenanced audio.
    """

    def __init__(self):
        self.genealogy_tree = AudioGenealogyTree()
        self.records: Dict[str, SampleProvenanceRecord] = {}

    def register_sample(self, record: SampleProvenanceRecord) -> None:
        """Registers a newly rendered or mutated sample into provenance storage."""
        self.records[record.sample_id] = record
        self.genealogy_tree.add_record(record)
        logger.info(
            f"Registered provenance for {record.sample_id} [{record.origin.value}] "
            f"from {record.source.track} (depth={record.generation_depth})"
        )

    def validate_creative_usage(
        self,
        record: SampleProvenanceRecord,
        allow_external_override: bool = False
    ) -> bool:
        """
        Enforces Rule 1: UNKNOWN audio cannot be used as creative raw material.
        Raises CreativeGovernanceError if violated.
        """
        if record.origin == SampleOrigin.UNKNOWN and not allow_external_override:
            raise CreativeGovernanceError(
                f"Cannot use unprovenanced audio (origin={record.origin.value}, id={record.sample_id}) "
                f"as creative source. The engine never takes arbitrary audio without explicit provenance."
            )
        return True

    def get_provenance(self, sample_id: str) -> Optional[SampleProvenanceRecord]:
        return self.records.get(sample_id)

    def get_genealogy_tree(self) -> AudioGenealogyTree:
        return self.genealogy_tree

    def audit_session_samples(
        self,
        sample_records: List[SampleProvenanceRecord]
    ) -> Dict[str, Any]:
        """Audits a batch of samples to ensure 100% provenance compliance."""
        total = len(sample_records)
        unprovenanced = [s for s in sample_records if s.origin == SampleOrigin.UNKNOWN]
        autogenous = [s for s in sample_records if s.is_autogenous]
        user_imported = [s for s in sample_records if s.origin == SampleOrigin.USER_IMPORTED]
        catalog = [s for s in sample_records if s.origin == SampleOrigin.CATALOG_SAMPLE]

        return {
            "total_samples": total,
            "compliant_count": total - len(unprovenanced),
            "unprovenanced_violations": [s.sample_id for s in unprovenanced],
            "autogenous_ratio": round(len(autogenous) / max(1, total), 3),
            "is_fully_compliant": len(unprovenanced) == 0,
            "origins_distribution": {
                "autogenous": len(autogenous),
                "user_imported": len(user_imported),
                "catalog": len(catalog),
                "unknown": len(unprovenanced),
            }
        }

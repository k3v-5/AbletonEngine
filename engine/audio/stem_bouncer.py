# engine/audio/stem_bouncer.py
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("StemBouncer")

@dataclass
class StemDefinition:
    stem_id: str             # e.g. "01_Drums"
    display_name: str        # "Drums"
    track_indices: List[int] # Tracks that belong to this stem
    track_names: List[str]   # Track names
    output_filename: str     # "01_Drums.wav"

@dataclass
class StemExportPlan:
    export_directory: str
    bpm: float
    start_bar: float
    end_bar: float
    total_bars: float
    duration_seconds: float
    sample_rate: int = 48000
    bit_depth: int = 24
    stems: List[StemDefinition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "export_directory": self.export_directory,
            "bpm": self.bpm,
            "start_bar": self.start_bar,
            "end_bar": self.end_bar,
            "total_bars": self.total_bars,
            "duration_seconds": round(self.duration_seconds, 2),
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
            "stem_count": len(self.stems),
            "stems": [
                {
                    "stem_id": s.stem_id,
                    "display_name": s.display_name,
                    "track_indices": s.track_indices,
                    "track_names": s.track_names,
                    "output_filename": s.output_filename
                }
                for s in self.stems
            ]
        }

class StemBouncer:
    """
    Automated stems export coordinator for arrangement sessions in Ableton Live.
    Groups musical roles into clean stems (Drums, Bass, Keys, Leads, Vocals, FX, Master)
    and prepares safe bounce workflows and metadata manifests.
    """

    DEFAULT_EXPORTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "exports",
        "stems"
    )

    STEM_CATEGORIES = [
        ("01_Drums", "Drums", ["drum", "kick", "snare", "hat", "clap", "perc", "tom", "cymbal", "808 kit"]),
        ("02_Bass", "Bass", ["bass", "sub", "808", "reese", "low end"]),
        ("05_Vocals", "Vocals", ["vocal", "vox", "lead vox", "adlib", "backing", "choir"]),
        ("03_Keys", "Keys & Chords", ["keys", "chord", "piano", "rhodes", "epiano", "pad", "organ"]),
        ("04_Lead", "Leads & Synths", ["lead", "synth", "hook", "arp", "melody", "vital", "guitar"]),
        ("06_FX", "FX & Transitions", ["fx", "sweep", "riser", "impact", "noise", "transition", "crash"])
    ]

    def __init__(self, export_dir: Optional[str] = None):
        self.export_dir = export_dir or self.DEFAULT_EXPORTS_DIR

    def create_export_plan(
        self,
        tracks: List[Dict[str, Any]],
        bpm: float = 142.0,
        start_bar: float = 1.0,
        end_bar: float = 65.0,
        sample_rate: int = 48000,
        bit_depth: int = 24
    ) -> StemExportPlan:
        """
        Analyzes session tracks and automatically partitions them into standard musical stem groups.
        """
        total_bars = max(1.0, end_bar - start_bar)
        # Duration calculation: (bars * 4 beats/bar) / (bpm / 60)
        duration_seconds = (total_bars * 4.0 * 60.0) / bpm

        assigned_indices = set()
        stems = []

        for stem_id, display_name, keywords in self.STEM_CATEGORIES:
            stem_indices = []
            stem_names = []

            for t in tracks:
                t_idx = t.get("index", 0)
                t_name = t.get("name", "").lower()

                if t_idx in assigned_indices:
                    continue

                if any(kw in t_name for kw in keywords):
                    stem_indices.append(t_idx)
                    stem_names.append(t.get("name", f"Track {t_idx}"))
                    assigned_indices.add(t_idx)

            if stem_indices:
                stems.append(StemDefinition(
                    stem_id=stem_id,
                    display_name=display_name,
                    track_indices=stem_indices,
                    track_names=stem_names,
                    output_filename=f"{stem_id}.wav"
                ))

        # Any unassigned musical tracks get gathered into a Misc stem
        unassigned_indices = []
        unassigned_names = []
        for t in tracks:
            t_idx = t.get("index", 0)
            if t_idx not in assigned_indices and t.get("name", "").lower() != "master":
                unassigned_indices.append(t_idx)
                unassigned_names.append(t.get("name", f"Track {t_idx}"))

        if unassigned_indices:
            stems.append(StemDefinition(
                stem_id="07_Other",
                display_name="Other",
                track_indices=unassigned_indices,
                track_names=unassigned_names,
                output_filename="07_Other.wav"
            ))

        # Always add Master stem
        stems.append(StemDefinition(
            stem_id="00_Master",
            display_name="Full Mix Master",
            track_indices=[t.get("index", 0) for t in tracks],
            track_names=["Master Mix"],
            output_filename="00_Master.wav"
        ))

        return StemExportPlan(
            export_directory=self.export_dir,
            bpm=bpm,
            start_bar=start_bar,
            end_bar=end_bar,
            total_bars=total_bars,
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            stems=stems
        )

    def generate_manifest(self, plan: StemExportPlan) -> str:
        """
        Generates and saves the stem manifest JSON in the export directory.
        """
        os.makedirs(plan.export_directory, exist_ok=True)
        manifest_path = os.path.join(plan.export_directory, "manifest.json")
        data = {
            "version": "1.0",
            "timestamp": time.time(),
            "export_plan": plan.to_dict(),
            "status": "ready"
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return manifest_path

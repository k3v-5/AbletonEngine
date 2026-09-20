"""
Resampling Lab & Sound Genealogy Engine (Phase 6.5):
Implements intentional, structured destructive resampling:
MIDI -> Instrument -> Audio -> Transformation -> Audition / Analysis -> Keep/Reject -> GeneratedSource.
Registers the resampled material into the internal catalog with full lineage/genealogy.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import os
import logging
from pathlib import Path

from engine.sound.timbre_dna import TimbreDNA
from engine.instruments.browser_catalog import (
    SoundSourceOption,
    InstrumentSourceCategory,
    CURATED_SOURCES,
    LiveBrowserCatalogEngine
)
from engine.creative.music_identity import MusicIdentity

logger = logging.getLogger("ResamplingLab")


@dataclass
class GeneratedSource(SoundSourceOption):
    """
    Sound source generated dynamically via destructive resampling with full lineage.
    """
    origin_track_name: str = ""
    origin_section: str = ""
    transformations: List[str] = field(default_factory=list)
    lineage_id: str = ""
    dna: Optional[TimbreDNA] = None
    plugin_name: str = ""
    generation_depth: int = 1
    parent_source_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "origin_track_name": self.origin_track_name,
            "origin_section": self.origin_section,
            "transformations": self.transformations,
            "lineage_id": self.lineage_id,
            "plugin_name": self.plugin_name,
            "generation_depth": self.generation_depth,
            "parent_source_id": self.parent_source_id,
            "dna": self.dna.to_dict() if self.dna and hasattr(self.dna, "to_dict") else {}
        })
        return base




class ResamplingLab:
    """
    Executes intentional, non-random destructive audio transformations
    and registers them as first-class citizens in the instrument catalog.
    """

    TRANSFORMATION_RECIPES = {
        "ghost_lead_texture": [
            "render_stem",
            "reverse_audio",
            "pitch_shift_-12",
            "texture_stretch_180",
            "transient_extraction",
            "high_pass_filter_400hz",
            "reverb_diffusion"
        ],
        "sub_impact_rumble": [
            "render_stem",
            "pitch_shift_-24",
            "analog_saturation",
            "low_pass_filter_90hz",
            "sidechain_compression"
        ],
        "vocal_granular_cloud": [
            "render_stem",
            "time_stretch_220",
            "pitch_shift_+7",
            "chorus_ensemble",
            "shimmer_reverb"
        ],
        "percussive_glitch_accent": [
            "render_stem",
            "transient_chop",
            "reverse_even_slices",
            "bitcrush_12bit",
            "ping_pong_delay"
        ]
    }

    @classmethod
    def evaluate_resampling_opportunity(
        cls,
        role: str,
        section_name: str,
        musical_importance: str = "high"
    ) -> Optional[str]:
        """
        Determines whether a track in a given section is a high-value candidate for resampling.
        Avoids random noise; prioritizes lead motifs, vocal hooks, and primary chord beds.
        """
        r_upper = str(role).upper()
        s_low = str(section_name).lower()

        if r_upper in ("LEAD", "COUNTER_LEAD") and any(w in s_low for w in ["drop", "chorus", "verse"]):
            return "ghost_lead_texture"
        elif r_upper in ("VOCALS", "VOX") and any(w in s_low for w in ["hook", "verse", "drop"]):
            return "vocal_granular_cloud"
        elif r_upper in ("BASS", "KICK") and any(w in s_low for w in ["drop", "build"]):
            return "sub_impact_rumble"
        elif r_upper in ("DRUMS", "PERCUSSION") and any(w in s_low for w in ["break", "puente", "build"]):
            return "percussive_glitch_accent"
        return None

    @classmethod
    def process_and_register_source(
        cls,
        session_data: Dict[str, Any],
        source_track: Any = None,
        origin_section: Optional[str] = None,
        recipe_name: str = "ghost_lead_texture",
        target_role: Optional[str] = None,
        source_track_name: Optional[str] = None,
        section_name: Optional[str] = None
    ) -> GeneratedSource:

        """
        Executes transformation chain, generates a new musical object, logs genealogy,
        and registers it into CURATED_SOURCES and the active session.
        """
        # Resolve source_track flexibly (dict or str)
        if isinstance(source_track, str):
            t_name = source_track
            # try to find in session_data tracks
            found_t = next((t for t in session_data.get("tracks", []) if t.get("name") == source_track), None)
            t_role = found_t.get("role", "LEAD") if found_t else "LEAD"
        elif isinstance(source_track, dict):
            t_name = source_track.get("name", "Source")
            t_role = source_track.get("role", "LEAD")
        elif source_track_name:
            t_name = source_track_name
            found_t = next((t for t in session_data.get("tracks", []) if t.get("name") == source_track_name), None)
            t_role = found_t.get("role", "LEAD") if found_t else "LEAD"
        else:
            t_name = "Source"
            t_role = "LEAD"

        sec_name = origin_section or section_name or "Drop"
        assigned_role = target_role or ("TEXTURE_FOLEY" if "texture" in recipe_name or "cloud" in recipe_name else (
            "COUNTER_LEAD" if "lead" in recipe_name else "EAR_CANDY"
        ))

        transformations = cls.TRANSFORMATION_RECIPES.get(recipe_name, cls.TRANSFORMATION_RECIPES["ghost_lead_texture"])

        
        # Generate unique serial id
        existing_resamples = session_data.get("generated_sources", [])
        serial = len(existing_resamples) + 1
        gen_id = f"gen_source_{assigned_role.lower()}_{serial:03d}"
        display_name = f"Resampled {t_name} ({recipe_name.replace('_', ' ').title()})"

        # Resolve lineage depth: check if source is an already resampled GeneratedSource
        parent_source_id = t_name
        generation_depth = 1
        for es in existing_resamples:
            if es.get("id") == t_name or es.get("name") == t_name or es.get("origin_track_name") == t_name:
                parent_source_id = es.get("id", t_name)
                generation_depth = int(es.get("generation_depth", 1)) + 1
                break

        # Calculate evolved TimbreDNA based on transformations
        base_dna = TimbreDNA.from_role(t_role)
        if "pitch_shift_-12" in transformations:
            base_dna.brightness = max(0.1, base_dna.brightness - 0.30)
        if "pitch_shift_+7" in transformations:
            base_dna.brightness = min(0.95, base_dna.brightness + 0.20)
        if "texture_stretch_180" in transformations or "time_stretch_220" in transformations:
            base_dna.transient_strength = max(0.1, base_dna.transient_strength - 0.40)
            base_dna.movement = min(0.95, base_dna.movement + 0.35)
        if "reverb_diffusion" in transformations or "shimmer_reverb" in transformations:
            base_dna.stereo_width = min(0.98, base_dna.stereo_width + 0.30)

        gen_source = GeneratedSource(
            id=gen_id,
            name=display_name,
            role=assigned_role,
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri=f"query:GeneratedSources#{gen_id}",
            vendor="AbletonEngine / ResamplingLab",
            description=f"Generated from '{t_name}' in {sec_name} via {len(transformations)} transformations (depth={generation_depth}).",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.65, "STEREO_WIDTH": 0.85},
                "transformations": transformations
            },
            origin_track_name=t_name,
            origin_section=sec_name,
            transformations=transformations,
            lineage_id=f"parent:{parent_source_id}->{gen_id}",
            dna=base_dna,
            generation_depth=generation_depth,
            parent_source_id=parent_source_id
        )

        # 1. Register in CURATED_SOURCES so it is queryable by LiveBrowserCatalogEngine
        if assigned_role not in CURATED_SOURCES:
            CURATED_SOURCES[assigned_role] = []
        CURATED_SOURCES[assigned_role].insert(0, gen_source)

        # 2. Record in Session Data
        if "generated_sources" not in session_data:
            session_data["generated_sources"] = []
        session_data["generated_sources"].append(gen_source.to_dict())

        # 3. Record in MusicIdentity Genealogy Log
        ident_data = session_data.get("music_identity")
        if ident_data:
            ident = MusicIdentity.from_dict(ident_data)
            ident.record_genealogy(
                event_type="destructive_resample",
                source_id=parent_source_id,
                destination_id=gen_id,
                section=sec_name,
                transformations=transformations
            )
            session_data["music_identity"] = ident.to_dict()

        logger.info(f"Registered GeneratedSource '{display_name}' ({gen_id}, depth={generation_depth}) for role '{assigned_role}'.")
        return gen_source


class GenealogyTree:
    """
    Constructs and analyzes the evolutionary lineage tree of resampled materials.
    Measures survival rates and branch depth across the session.
    """

    @classmethod
    def build_tree(cls, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a hierarchical tree from session generated_sources and tracks.
        """
        gen_sources = session_data.get("generated_sources", [])
        tracks = session_data.get("tracks", [])
        active_source_names = {t.get("name") for t in tracks} | {t.get("source_id") for t in tracks}

        nodes: Dict[str, Dict[str, Any]] = {}
        roots: List[str] = []

        for s in gen_sources:
            s_id = s.get("id")
            parent = s.get("parent_source_id", s.get("origin_track_name", "Unknown"))
            depth = s.get("generation_depth", 1)
            survived = s.get("name") in active_source_names or s_id in active_source_names

            nodes[s_id] = {
                "id": s_id,
                "name": s.get("name"),
                "parent": parent,
                "depth": depth,
                "origin_section": s.get("origin_section"),
                "transformations": s.get("transformations", []),
                "survived": survived,
                "children": []
            }

        # Link children to parents
        for s_id, node in nodes.items():
            parent_id = node["parent"]
            if parent_id in nodes:
                nodes[parent_id]["children"].append(node)
            else:
                roots.append(s_id)

        return {
            "total_nodes": len(nodes),
            "root_ids": roots,
            "nodes": nodes
        }

    @classmethod
    def calculate_survival_rate(cls, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the percentage of GeneratedSources that survived into the final arrangement tracks.
        """
        gen_sources = session_data.get("generated_sources", [])
        if not gen_sources:
            return {
                "total_generated": 0,
                "survived_count": 0,
                "survival_rate": 0.0,
                "max_depth": 0
            }

        tree = cls.build_tree(session_data)
        nodes = tree["nodes"]
        survived_count = sum(1 for n in nodes.values() if n["survived"])
        total = len(nodes)
        max_depth = max((n["depth"] for n in nodes.values()), default=0)

        return {
            "total_generated": total,
            "survived_count": survived_count,
            "survival_rate": round(survived_count / total, 3) if total > 0 else 0.0,
            "max_depth": max_depth
        }

    @classmethod
    def render_ascii_tree(cls, session_data: Dict[str, Any]) -> str:
        """
        Renders an ASCII visualization of the sound evolutionary tree.
        """
        tree = cls.build_tree(session_data)
        nodes = tree["nodes"]
        lines: List[str] = ["Sound Evolutionary Tree:"]

        def _render_node(node: Dict[str, Any], prefix: str = "", is_last: bool = True):
            connector = "└── " if is_last else "├── "
            status = "[SURVIVED]" if node["survived"] else "[DISCARDED]"
            lines.append(f"{prefix}{connector}{node['name']} (depth={node['depth']}) {status}")
            child_prefix = prefix + ("    " if is_last else "│   ")
            children = node.get("children", [])
            for i, child in enumerate(children):
                _render_node(child, child_prefix, i == len(children) - 1)

        for r_id in tree["root_ids"]:
            root_node = nodes[r_id]
            lines.append(f"Host Origin: {root_node['parent']}")
            _render_node(root_node, prefix=" ", is_last=True)

        return "\n".join(lines)


# Top-level alias for convenience
RESAMPLING_RECIPES = ResamplingLab.TRANSFORMATION_RECIPES



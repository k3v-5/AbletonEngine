"""
Frequency Collision Graph and Spectral Occupancy Map.
Represents multi-role mixing as an interconnected spectral network.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import networkx as nx

from .models import Severity


@dataclass
class ConflictEdge:
    role_a: str
    role_b: str
    conflict_band: str
    frequency_overlap: float
    energy_overlap: float
    temporal_overlap: float
    severity: Severity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_a": self.role_a,
            "role_b": self.role_b,
            "conflict_band": self.conflict_band,
            "frequency_overlap": round(self.frequency_overlap, 3),
            "energy_overlap": round(self.energy_overlap, 3),
            "temporal_overlap": round(self.temporal_overlap, 3),
            "severity": self.severity.value
        }


class FrequencyConflictGraph:
    """Graph network tracking multi-role spectral and temporal clashes."""

    def __init__(self):
        self.graph = nx.Graph()

    def add_role_node(self, role: str, primary_band: str, energy_share: float) -> None:
        self.graph.add_node(role, primary_band=primary_band, energy_share=energy_share)

    def add_conflict(self, edge: ConflictEdge) -> None:
        self.graph.add_edge(
            edge.role_a,
            edge.role_b,
            conflict_band=edge.conflict_band,
            frequency_overlap=edge.frequency_overlap,
            energy_overlap=edge.energy_overlap,
            temporal_overlap=edge.temporal_overlap,
            severity=edge.severity
        )

    def get_conflicts_for_role(self, role: str) -> List[Dict[str, Any]]:
        if not self.graph.has_node(role):
            return []
        conflicts = []
        for nbr in self.graph.neighbors(role):
            edge_data = self.graph.get_edge_data(role, nbr)
            conflicts.append({
                "other_role": nbr,
                "conflict_band": edge_data["conflict_band"],
                "frequency_overlap": edge_data["frequency_overlap"],
                "severity": edge_data["severity"].value
            })
        return conflicts

    def to_dict(self) -> Dict[str, Any]:
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "role_a": u,
                "role_b": v,
                "conflict_band": data.get("conflict_band", "unknown"),
                "frequency_overlap": round(data.get("frequency_overlap", 0.0), 3),
                "severity": data.get("severity", Severity.INFO).value
            })
        return {
            "nodes": list(self.graph.nodes()),
            "edges": edges,
            "total_conflicts": len(edges)
        }


class SpectralOccupancyMap:
    """Maps spectral bands to occupying roles and energy distributions."""

    ROLE_TYPICAL_RANGES = {
        "SUB": (20.0, 70.0),
        "KICK": (35.0, 110.0),
        "BASS": (60.0, 250.0),
        "CHORDS": (150.0, 1500.0),
        "PAD": (200.0, 3000.0),
        "VOCAL": (300.0, 5000.0),
        "LEAD": (400.0, 8000.0),
        "DRUMS": (100.0, 16000.0),
        "FX": (500.0, 20000.0)
    }

    @classmethod
    def get_occupancy_map(cls, active_roles: List[str]) -> Dict[str, List[str]]:
        """Returns band -> list of active occupying roles."""
        bands = {
            "20-60Hz": [],
            "60-120Hz": [],
            "120-400Hz": [],
            "400-2kHz": [],
            "2k-8kHz": [],
            "8k-20kHz": []
        }
        for role in active_roles:
            r = role.upper()
            if r in ("SUB", "KICK"):
                bands["20-60Hz"].append(r)
            if r in ("KICK", "BASS"):
                bands["60-120Hz"].append(r)
            if r in ("BASS", "CHORDS", "PAD"):
                bands["120-400Hz"].append(r)
            if r in ("CHORDS", "PAD", "VOCAL", "LEAD"):
                bands["400-2kHz"].append(r)
            if r in ("VOCAL", "LEAD", "DRUMS"):
                bands["2k-8kHz"].append(r)
            if r in ("DRUMS", "FX", "LEAD"):
                bands["8k-20kHz"].append(r)
        return bands

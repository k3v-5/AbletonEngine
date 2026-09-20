"""
Territorial Corpus Space & Continuous Creative Map:
Projects generated music sessions into an n-dimensional continuous aesthetic territory.

Features:
1. TerritoryPoint: Multi-feature embedding vector (7D TimbreDNA, rhythm density, harmony, spatial breathing, tempo).
2. Continuous Distance Metric: Quantifies distance from candidate session to the historical corpus.
3. Creative Novelty Score: Evaluates whether a session occupies an unexplored region of creative space.
4. Territory Saturation Detector: Flags over-crowded aesthetic quadrants ("40 songs in this exact zone").
5. State Persistence: Stores and updates historical memory in state/learned/corpus_memory.json.
"""

import os
import json
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from engine.sound.timbre_dna import TimbreDNA

logger = logging.getLogger("CorpusTerritory")

DEFAULT_CORPUS_STORAGE_PATH = os.path.join("state", "learned", "corpus_memory.json")


@dataclass
class TerritoryPoint:
    """Multi-dimensional continuous representation of a song in the creative territory."""
    session_id: str
    genre: str
    bpm: float
    tonal_center: str
    mode: str
    timbre_vector: List[float]  # 7D: brightness, roughness, inharmonicity, stereo_width, transient, movement, instability
    rhythm_density: float       # Average drum notes per bar
    spatial_width_max: float
    spatial_width_min: float
    applied_mechanisms: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "genre": self.genre,
            "bpm": round(self.bpm, 2),
            "tonal_center": self.tonal_center,
            "mode": self.mode,
            "timbre_vector": [round(v, 4) for v in self.timbre_vector],
            "rhythm_density": round(self.rhythm_density, 3),
            "spatial_width_max": round(self.spatial_width_max, 3),
            "spatial_width_min": round(self.spatial_width_min, 3),
            "applied_mechanisms": self.applied_mechanisms,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerritoryPoint":
        return cls(
            session_id=str(data.get("session_id", "unknown")),
            genre=str(data.get("genre", "electronic")),
            bpm=float(data.get("bpm", 124.0)),
            tonal_center=str(data.get("tonal_center", "C")),
            mode=str(data.get("mode", "Minor")),
            timbre_vector=list(data.get("timbre_vector", [0.5] * 7)),
            rhythm_density=float(data.get("rhythm_density", 16.0)),
            spatial_width_max=float(data.get("spatial_width_max", 1.0)),
            spatial_width_min=float(data.get("spatial_width_min", 0.2)),
            applied_mechanisms=list(data.get("applied_mechanisms", [])),
            timestamp=float(data.get("timestamp", time.time()))
        )


@dataclass
class TerritoryCluster:
    """A distinct aesthetic cluster/territory discovered in creative space."""
    cluster_id: str
    name: str
    centroid_point: TerritoryPoint
    member_ids: List[str] = field(default_factory=list)
    radius: float = 0.25

    @property
    def total_songs(self) -> int:
        return len(self.member_ids)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "name": self.name,
            "centroid": self.centroid_point.to_dict(),
            "member_ids": self.member_ids,
            "total_songs": self.total_songs,
            "radius": round(self.radius, 4)
        }


def compute_centroid(points: List[TerritoryPoint], cluster_id: str = "cluster_0") -> TerritoryPoint:
    """Calculates representative centroid for a group of territory points."""
    if not points:
        raise ValueError("Cannot compute centroid of empty points list")

    genre_counts: Dict[str, int] = {}
    tonal_counts: Dict[str, int] = {}
    mode_counts: Dict[str, int] = {}
    for p in points:
        genre_counts[p.genre] = genre_counts.get(p.genre, 0) + 1
        tonal_counts[p.tonal_center] = tonal_counts.get(p.tonal_center, 0) + 1
        mode_counts[p.mode] = mode_counts.get(p.mode, 0) + 1

    dom_genre = max(genre_counts.items(), key=lambda x: x[1])[0]
    dom_tonal = max(tonal_counts.items(), key=lambda x: x[1])[0]
    dom_mode = max(mode_counts.items(), key=lambda x: x[1])[0]

    n = len(points)
    avg_bpm = sum(p.bpm for p in points) / n
    avg_rhythm = sum(p.rhythm_density for p in points) / n
    avg_spa_max = sum(p.spatial_width_max for p in points) / n
    avg_spa_min = sum(p.spatial_width_min for p in points) / n

    dim = len(points[0].timbre_vector)
    avg_timbre = [sum(p.timbre_vector[i] for p in points) / n for i in range(dim)]

    all_mechs = set()
    for p in points:
        all_mechs.update(p.applied_mechanisms)

    return TerritoryPoint(
        session_id=f"centroid_{cluster_id}",
        genre=dom_genre,
        bpm=round(avg_bpm, 1),
        tonal_center=dom_tonal,
        mode=dom_mode,
        timbre_vector=avg_timbre,
        rhythm_density=round(avg_rhythm, 3),
        spatial_width_max=round(avg_spa_max, 3),
        spatial_width_min=round(avg_spa_min, 3),
        applied_mechanisms=list(all_mechs)
    )


class CorpusTerritory:
    """
    Maintains a territorial map of all historical sessions produced by the engine.
    Calculates empirical distance, novelty scores, and saturation zones.
    """

    def __init__(self, storage_path: str = DEFAULT_CORPUS_STORAGE_PATH):
        self.storage_path = storage_path
        self.points: List[TerritoryPoint] = []
        self.load()

    def clear(self) -> None:
        """Clears in-memory points (useful for testing and reset)."""
        self.points.clear()

    @classmethod
    def extract_point_from_session(cls, session_data: Any) -> TerritoryPoint:
        """Extracts a TerritoryPoint from a session object or dictionary."""
        data = session_data.data if hasattr(session_data, "data") else (session_data if isinstance(session_data, dict) else {})

        session_id = data.get("song_title", data.get("name", f"session_{int(time.time())}"))
        genre = data.get("genre", "electronic")
        bpm = float(data.get("bpm", data.get("tempo", 124.0)))

        ident = data.get("music_identity", {})
        tonal_center = str(data.get("tonal_center", ident.get("tonal_center", "C")))
        mode = str(data.get("mode", ident.get("mode", "Minor")))

        # 1. Timbre Vector (7D)
        tracks = data.get("tracks", [])
        dna_list: List[TimbreDNA] = []
        if "timbre_motif" in ident and "dna" in ident["timbre_motif"]:
            dna_list.append(TimbreDNA.from_dict(ident["timbre_motif"]["dna"]))
        for t in tracks:
            if "timbre_dna" in t:
                dna_list.append(TimbreDNA.from_dict(t["timbre_dna"]))
            elif "role" in t:
                if hasattr(TimbreDNA, "from_role"):
                    dna_list.append(TimbreDNA.from_role(t["role"]))
                else:
                    from engine.sound.timbre_dna import TimbreRelationshipMatrix
                    dna_list.append(TimbreRelationshipMatrix.get_default_for_role(t["role"]))

        if dna_list:
            n = len(dna_list)
            avg_dna = [
                sum(d.brightness for d in dna_list) / n,
                sum(d.roughness for d in dna_list) / n,
                sum(d.inharmonicity for d in dna_list) / n,
                sum(d.stereo_width for d in dna_list) / n,
                sum(d.transient_strength for d in dna_list) / n,
                sum(d.movement for d in dna_list) / n,
                sum(d.pitch_instability for d in dna_list) / n
            ]
        else:
            avg_dna = [0.65, 0.35, 0.20, 0.75, 0.60, 0.45, 0.05]

        # 2. Rhythm Density
        drum_tracks = [t for t in tracks if str(t.get("role", "")).upper() in ("DRUMS", "KICK", "PERCUSSION", "SNARE")]
        total_drum_notes = sum(t.get("notes_count", len(t.get("notes", []))) for t in drum_tracks)
        sections = data.get("sections", [{"bars": 16}])
        total_bars = sum(s.get("bars", 8) for s in sections) or 16
        rhythm_density = total_drum_notes / max(1, total_bars)

        # 3. Spatial Width Range
        curve = data.get("spatial_energy_curve", [])
        widths = [
            pt.get("stereo_width", pt.get("profile", {}).get("stereo_width", 1.0))
            for pt in curve
        ] or [0.20, 1.20]
        spatial_min = min(widths)
        spatial_max = max(widths)

        # 4. Applied mechanisms
        mechanisms = list(data.get("applied_mechanisms", []))

        return TerritoryPoint(
            session_id=session_id,
            genre=genre,
            bpm=bpm,
            tonal_center=tonal_center,
            mode=mode,
            timbre_vector=avg_dna,
            rhythm_density=rhythm_density,
            spatial_width_max=spatial_max,
            spatial_width_min=spatial_min,
            applied_mechanisms=mechanisms
        )

    @classmethod
    def calculate_distance(cls, pt_a: TerritoryPoint, pt_b: TerritoryPoint) -> float:
        """
        Calculates normalized continuous Euclidean/Cosine distance between two territory points in [0.0, 1.0].
        Weights: Genre (0.15), Timbre (0.35), Rhythm (0.15), Harmony (0.15), Spatial (0.10), Tempo (0.10).
        """
        # 0. Genre distance
        genre_dist = 1.0 if pt_a.genre.lower().strip() != pt_b.genre.lower().strip() else 0.0

        # 1. Timbral distance (Euclidean 7D normalized by sqrt(7))
        tim_sum_sq = sum((v1 - v2) ** 2 for v1, v2 in zip(pt_a.timbre_vector, pt_b.timbre_vector))
        tim_dist = math.sqrt(tim_sum_sq) / math.sqrt(len(pt_a.timbre_vector))
        tim_dist = min(1.0, max(0.0, tim_dist))

        # 2. Rhythmic density distance
        max_density = max(pt_a.rhythm_density, pt_b.rhythm_density, 1.0)
        rhy_dist = min(1.0, abs(pt_a.rhythm_density - pt_b.rhythm_density) / max_density)

        # 3. Harmonic distance
        harm_dist = 0.0
        if pt_a.tonal_center.lower() != pt_b.tonal_center.lower():
            harm_dist += 0.60
        if pt_a.mode.lower() != pt_b.mode.lower():
            harm_dist += 0.40

        # 4. Spatial distance
        spa_diff = (abs(pt_a.spatial_width_max - pt_b.spatial_width_max) +
                    abs(pt_a.spatial_width_min - pt_b.spatial_width_min)) / 2.0
        spa_dist = min(1.0, spa_diff)

        # 5. Tempo distance
        bpm_dist = min(1.0, abs(pt_a.bpm - pt_b.bpm) / 60.0)

        # Composite distance with calibrated genre slotting (0.25)
        composite_distance = (
            (genre_dist * 0.25) +
            (tim_dist * 0.30) +
            (rhy_dist * 0.15) +
            (harm_dist * 0.15) +
            (spa_dist * 0.08) +
            (bpm_dist * 0.07)
        )
        return round(min(1.0, max(0.0, composite_distance)), 4)

    def add_session_to_territory(self, session_data: Any, auto_save: bool = False) -> TerritoryPoint:
        """Extracts and adds a session point to the territory memory."""
        point = self.extract_point_from_session(session_data)
        self.points.append(point)
        if auto_save:
            self.save()
        return point

    def calculate_corpus_distance(self, candidate_session: Any, k: int = 3) -> float:
        """
        Calculates distance from candidate session to the historical corpus.
        Returns novelty score in [0.0, 1.0].
        If corpus is empty, returns 1.0 (maximum novelty).
        Uses k-Nearest Neighbors (average distance to top k closest points).
        """
        if not self.points:
            return 1.0

        target_point = self.extract_point_from_session(candidate_session)
        distances = [self.calculate_distance(target_point, p) for p in self.points]
        distances.sort()

        # Average distance to top k closest neighbors
        top_k = distances[:min(k, len(distances))]
        avg_knn_dist = sum(top_k) / len(top_k)
        return round(min(1.0, max(0.0, avg_knn_dist)), 4)

    def detect_territory_saturation(
        self,
        candidate_session: Any,
        radius: float = 0.20,
        threshold_count: int = 4,
        recent_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Detects whether the candidate session lies within an over-saturated quadrant of the creative map.
        Uses a temporal window (default 40 sessions when corpus > 50) to prevent historical archives
        from triggering permanent false-positive saturation alarms at large scales.
        """
        target_point = self.extract_point_from_session(candidate_session)
        neighbors_in_radius: List[TerritoryPoint] = []

        window_size = recent_window if recent_window is not None else (40 if len(self.points) > 50 else None)
        search_points = self.points[-window_size:] if window_size else self.points

        for p in search_points:
            dist = self.calculate_distance(target_point, p)
            if dist <= radius and p.session_id != target_point.session_id:
                neighbors_in_radius.append(p)

        neighbor_count = len(neighbors_in_radius)
        is_saturated = neighbor_count >= threshold_count
        density_ratio = round(neighbor_count / max(1, len(search_points)), 3)

        warning = None
        recommendation = None
        if is_saturated:
            warning = (
                f"Saturación de territorio detectada: {neighbor_count} canciones previas residen a distancia <= {radius} "
                f"en este cuadrante estético ({target_point.genre}, {target_point.tonal_center} {target_point.mode}, {target_point.bpm} BPM)."
            )
            recommendation = (
                "Forzar desplazamiento territorial: modificar el centro tonal, variar la subdivisión de groove "
                "o desplazar el vector TimbreDNA (más rugosidad o movimiento) para poblar territorio virgen."
            )

        return {
            "is_saturated": is_saturated,
            "neighbor_count_in_radius": neighbor_count,
            "saturation_density_ratio": density_ratio,
            "radius_tested": radius,
            "threshold_count": threshold_count,
            "warning": warning,
            "recommendation": recommendation,
            "neighbor_ids": [n.session_id for n in neighbors_in_radius[:5]]
        }

    def get_territory_map_summary(self) -> Dict[str, Any]:
        """Returns statistical overview of the mapped creative space."""
        total = len(self.points)
        if total == 0:
            return {"status": "EMPTY_TERRITORY", "total_points": 0}

        genre_counts: Dict[str, int] = {}
        for p in self.points:
            genre_counts[p.genre] = genre_counts.get(p.genre, 0) + 1

        # Calculate average pairwise distance across sample
        sample = self.points[:min(20, total)]
        pair_dists = []
        for i in range(len(sample)):
            for j in range(i + 1, len(sample)):
                pair_dists.append(self.calculate_distance(sample[i], sample[j]))

        avg_dispersion = round(sum(pair_dists) / len(pair_dists), 3) if pair_dists else 0.0

        return {
            "status": "TERRITORY_MAPPED",
            "total_songs_in_territory": total,
            "genre_distribution": genre_counts,
            "average_territorial_dispersion": avg_dispersion,
            "dispersion_quality": "HIGH_EXPLORATION" if avg_dispersion >= 0.45 else "LOW_CLUSTER_CONVERGENCE"
        }

    def discover_territories(
        self,
        min_cluster_size: int = 2,
        max_radius: float = 0.30
    ) -> List[TerritoryCluster]:
        """
        Discovers aesthetic clusters in the historical session corpus.
        Groups points that are within max_radius distance into coherent territories.
        """
        if not self.points:
            return []

        clusters: List[TerritoryCluster] = []
        assigned = set()

        for idx, seed in enumerate(self.points):
            if seed.session_id in assigned:
                continue

            members = [seed]
            for candidate in self.points:
                if candidate.session_id == seed.session_id or candidate.session_id in assigned:
                    continue
                if self.calculate_distance(seed, candidate) <= max_radius:
                    members.append(candidate)

            if len(members) >= min_cluster_size:
                cluster_id = f"territory_{len(clusters) + 1}"
                centroid = compute_centroid(members, cluster_id=cluster_id)

                refined_members = [
                    p for p in members
                    if self.calculate_distance(p, centroid) <= max_radius * 1.35
                ]
                if len(refined_members) < min_cluster_size:
                    refined_members = members

                for m in refined_members:
                    assigned.add(m.session_id)

                cluster_name = (
                    f"Territory_{len(clusters) + 1}: {centroid.genre.capitalize()} "
                    f"{centroid.tonal_center} {centroid.mode} ({int(centroid.bpm)} BPM)"
                )
                max_d = max(self.calculate_distance(m, centroid) for m in refined_members) if refined_members else max_radius

                clusters.append(TerritoryCluster(
                    cluster_id=cluster_id,
                    name=cluster_name,
                    centroid_point=centroid,
                    member_ids=[m.session_id for m in refined_members],
                    radius=max_d
                ))

        unassigned_points = [p for p in self.points if p.session_id not in assigned]
        if min_cluster_size == 1:
            for p in unassigned_points:
                cid = f"territory_{len(clusters) + 1}"
                clusters.append(TerritoryCluster(
                    cluster_id=cid,
                    name=f"Territory_{len(clusters) + 1}: {p.genre.capitalize()} {p.tonal_center} {p.mode} ({int(p.bpm)} BPM)",
                    centroid_point=p,
                    member_ids=[p.session_id],
                    radius=0.10
                ))

        return clusters

    def find_closest_cluster(
        self,
        candidate_session: Any,
        clusters: Optional[List[TerritoryCluster]] = None
    ) -> Optional[Tuple[TerritoryCluster, float]]:
        """Finds closest aesthetic cluster to a given session."""
        cl_list = clusters if clusters is not None else self.discover_territories()
        if not cl_list:
            return None

        target_point = self.extract_point_from_session(candidate_session)
        best_cluster = None
        min_dist = float("inf")

        for cl in cl_list:
            dist = self.calculate_distance(target_point, cl.centroid_point)
            if dist < min_dist:
                min_dist = dist
                best_cluster = cl

        return (best_cluster, round(min_dist, 4)) if best_cluster else None

    def track_temporal_evolution(self, window_size: int = 5) -> Dict[str, Any]:
        """
        Measures temporal drift and expansion velocity of creative space over time.
        Compares the initial cohort of sessions with the latest cohort.
        """
        if len(self.points) < 2:
            return {
                "status": "INSUFFICIENT_HISTORY",
                "total_points": len(self.points),
                "centroid_drift": 0.0,
                "sequential_step_distance": 0.0,
                "evolutionary_velocity": "STABLE"
            }

        step_dists = [
            self.calculate_distance(self.points[i], self.points[i + 1])
            for i in range(len(self.points) - 1)
        ]
        avg_step = sum(step_dists) / len(step_dists)

        k = min(window_size, max(1, len(self.points) // 2))
        early_points = self.points[:k]
        late_points = self.points[-k:]

        early_centroid = compute_centroid(early_points, cluster_id="early")
        late_centroid = compute_centroid(late_points, cluster_id="late")
        drift = self.calculate_distance(early_centroid, late_centroid)

        if drift >= 0.25:
            velocity = "EXPANDING"
        elif drift >= 0.10:
            velocity = "EVOLVING"
        else:
            velocity = "CONVERGED"

        return {
            "status": "EVOLUTION_TRACKED",
            "total_points": len(self.points),
            "centroid_drift": round(drift, 4),
            "sequential_step_distance": round(avg_step, 4),
            "evolutionary_velocity": velocity
        }

    def detect_territorial_stagnation(
        self,
        window: int = 10,
        max_dwell_ratio: float = 0.70
    ) -> Dict[str, Any]:
        """
        Alerts if the engine has been producing too many consecutive songs in the exact same cluster.
        Prevents territorial stagnation / creative comfort zone.
        """
        recent_points = self.points[-window:]
        if len(self.points) < 8 or len(recent_points) < 6:
            return {
                "is_stagnant": False,
                "status": "INSUFFICIENT_HISTORY",
                "dwell_ratio": 0.0,
                "window_tested": len(self.points)
            }
        clusters = self.discover_territories(min_cluster_size=1)
        if not clusters:
            return {
                "is_stagnant": False,
                "status": "NO_CLUSTERS",
                "dwell_ratio": 0.0
            }

        cluster_counts: Dict[str, int] = {}
        for pt in recent_points:
            best_cl = None
            min_d = float("inf")
            for cl in clusters:
                d = self.calculate_distance(pt, cl.centroid_point)
                if d < min_d:
                    min_d = d
                    best_cl = cl
            if best_cl and min_d <= min(0.25, max(0.18, best_cl.radius * 1.25)):
                cluster_counts[best_cl.cluster_id] = cluster_counts.get(best_cl.cluster_id, 0) + 1

        if not cluster_counts:
            return {
                "is_stagnant": False,
                "status": "NO_CLUSTER_ASSIGNMENTS",
                "dwell_ratio": 0.0
            }

        dominant_cluster_id, dominant_count = max(cluster_counts.items(), key=lambda x: x[1])
        dwell_ratio = dominant_count / len(recent_points)
        is_stagnant = dwell_ratio >= max_dwell_ratio

        dominant_cluster = next((c for c in clusters if c.cluster_id == dominant_cluster_id), None)
        dominant_name = dominant_cluster.name if dominant_cluster else dominant_cluster_id

        warning = None
        recommendation = None
        if is_stagnant:
            warning = (
                f"Estancamiento territorial detectado: el motor ha permanecido {dwell_ratio * 100:.1f}% "
                f"de sus últimas {len(recent_points)} sesiones en '{dominant_name}'."
            )
            recommendation = (
                "Forzar desplazamiento estético: activar modo EXPLORE, seleccionar tempos contrastantes "
                "o transicionar a paletas tímbricas y escalas no exploradas."
            )

        return {
            "is_stagnant": is_stagnant,
            "dominant_cluster_id": dominant_cluster_id,
            "dominant_cluster_name": dominant_name,
            "dominant_session_count": dominant_count,
            "recent_sessions_window": len(recent_points),
            "dwell_ratio": round(dwell_ratio, 3),
            "max_dwell_ratio_threshold": max_dwell_ratio,
            "warning": warning,
            "recommendation": recommendation
        }

    def save(self, filepath: Optional[str] = None) -> None:
        """Persists the territory to JSON file."""
        target = filepath or self.storage_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = {
            "version": "1.0",
            "total_points": len(self.points),
            "updated_at": time.time(),
            "points": [p.to_dict() for p in self.points]
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.points)} territory points to {target}")

    def load(self, filepath: Optional[str] = None) -> None:
        """Loads territory points from JSON file if it exists."""
        target = filepath or self.storage_path
        if not os.path.exists(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.points = [TerritoryPoint.from_dict(d) for d in data.get("points", [])]
            logger.info(f"Loaded {len(self.points)} territory points from {target}")
        except Exception as e:
            logger.warning(f"Failed to load corpus territory from {target}: {e}")

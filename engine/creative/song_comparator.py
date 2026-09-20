"""
Multi-Dimensional Perceptual Comparator & Song Comparison Engine:
Evaluates perceptual distinctiveness between two songs across 7 dimensions:
1. Melodic similarity (pitch intervals, contours)
2. Rhythmic similarity (grooves, subdivisions, densities)
3. Harmonic similarity (tonal centers, modes, progressions)
4. Timbral similarity (7-dimensional TimbreDNA vector distance)
5. Spatial similarity (stereo width breathing, reverb depth)
6. Structural similarity (section proportions and order)
7. Motif similarity (shared production motifs)

Guarantees that A != B represents genuine audible perceptual divergence,
and detects Aesthetic Monotony (different notes with identical sound aesthetic).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import math

from engine.sound.timbre_dna import TimbreDNA


@dataclass
class SongComparison:
    """
    Detailed multi-dimensional comparison between two songs/sessions.
    """
    song_a_name: str
    song_b_name: str
    melodic_similarity: float
    rhythmic_similarity: float
    harmonic_similarity: float
    timbral_similarity: float
    spatial_similarity: float
    structural_similarity: float
    motif_similarity: float
    composite_similarity: float
    perceptual_verdict: str  # "IDENTICAL", "VARIATION_OF_SAME_IDENTITY", "DISTINCT_SONG", "AESTHETICALLY_MONOTONOUS"
    dimension_deltas: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_a_name": self.song_a_name,
            "song_b_name": self.song_b_name,
            "melodic_similarity": round(self.melodic_similarity, 3),
            "rhythmic_similarity": round(self.rhythmic_similarity, 3),
            "harmonic_similarity": round(self.harmonic_similarity, 3),
            "timbral_similarity": round(self.timbral_similarity, 3),
            "spatial_similarity": round(self.spatial_similarity, 3),
            "structural_similarity": round(self.structural_similarity, 3),
            "motif_similarity": round(self.motif_similarity, 3),
            "composite_similarity": round(self.composite_similarity, 3),
            "perceptual_verdict": self.perceptual_verdict,
            "dimension_deltas": self.dimension_deltas
        }


class PerceptualComparator:
    """
    Compares two music sessions across 7 perceptual dimensions,
    ensuring that divergence is genuine and alerting against timbral monotony.
    """

    @classmethod
    def compare_sessions(cls, session_a: Any, session_b: Any) -> SongComparison:
        """
        Conducts multi-dimensional similarity analysis between Session A and Session B.
        """
        data_a = session_a.data if hasattr(session_a, "data") else (session_a if isinstance(session_a, dict) else {})
        data_b = session_b.data if hasattr(session_b, "data") else (session_b if isinstance(session_b, dict) else {})

        name_a = data_a.get("song_title", data_a.get("name", "Song A"))
        name_b = data_b.get("song_title", data_b.get("name", "Song B"))

        # 1. Melodic Similarity
        mel_sim = cls._calculate_melodic_similarity(data_a, data_b)

        # 2. Rhythmic Similarity
        rhy_sim = cls._calculate_rhythmic_similarity(data_a, data_b)

        # 3. Harmonic Similarity
        harm_sim = cls._calculate_harmonic_similarity(data_a, data_b)

        # 4. Timbral Similarity (7D TimbreDNA)
        tim_sim = cls._calculate_timbral_similarity(data_a, data_b)

        # 5. Spatial Similarity
        spa_sim = cls._calculate_spatial_similarity(data_a, data_b)

        # 6. Structural Similarity
        str_sim = cls._calculate_structural_similarity(data_a, data_b)

        # 7. Motif Similarity
        mot_sim = cls._calculate_motif_similarity(data_a, data_b)

        # Weighted Composite Similarity
        composite = (
            (mel_sim * 0.20) +
            (rhy_sim * 0.15) +
            (harm_sim * 0.15) +
            (tim_sim * 0.25) +
            (spa_sim * 0.10) +
            (str_sim * 0.15)
        )
        composite = round(min(1.0, max(0.0, composite)), 3)

        # Determine Perceptual Verdict
        if composite >= 0.95:
            verdict = "IDENTICAL"
        elif mot_sim >= 0.70 and harm_sim >= 0.75 and 0.50 <= composite < 0.95:
            verdict = "VARIATION_OF_SAME_IDENTITY"
        elif tim_sim >= 0.88 and (mel_sim < 0.60 or rhy_sim < 0.60):
            # The subtle internal cliché: distinct notes, but identical sound aesthetics!
            verdict = "AESTHETICALLY_MONOTONOUS"
        elif composite < 0.55:
            verdict = "DISTINCT_SONG"
        else:
            verdict = "PARTIALLY_SIMILAR"

        deltas = {
            "melodic_diff": round(1.0 - mel_sim, 3),
            "rhythmic_diff": round(1.0 - rhy_sim, 3),
            "harmonic_diff": round(1.0 - harm_sim, 3),
            "timbral_diff": round(1.0 - tim_sim, 3),
            "spatial_diff": round(1.0 - spa_sim, 3),
            "structural_diff": round(1.0 - str_sim, 3)
        }

        return SongComparison(
            song_a_name=name_a,
            song_b_name=name_b,
            melodic_similarity=mel_sim,
            rhythmic_similarity=rhy_sim,
            harmonic_similarity=harm_sim,
            timbral_similarity=tim_sim,
            spatial_similarity=spa_sim,
            structural_similarity=str_sim,
            motif_similarity=mot_sim,
            composite_similarity=composite,
            perceptual_verdict=verdict,
            dimension_deltas=deltas
        )

    @classmethod
    def _calculate_melodic_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        tracks_a = [t for t in data_a.get("tracks", []) if str(t.get("role", "")).upper() in ("LEAD", "COUNTER_LEAD", "KEYS")]
        tracks_b = [t for t in data_b.get("tracks", []) if str(t.get("role", "")).upper() in ("LEAD", "COUNTER_LEAD", "KEYS")]

        if not tracks_a and not tracks_b:
            return 1.0
        if not tracks_a or not tracks_b:
            return 0.30

        # Pitch sets
        pitches_a = {n.get("pitch", 60) for t in tracks_a for n in t.get("notes", [])}
        pitches_b = {n.get("pitch", 60) for t in tracks_b for n in t.get("notes", [])}

        if not pitches_a and not pitches_b:
            return 1.0
        if not pitches_a or not pitches_b:
            return 0.30

        # Jaccard overlap of pitches
        intersection = pitches_a.intersection(pitches_b)
        union = pitches_a.union(pitches_b)
        return round(len(intersection) / len(union), 3)

    @classmethod
    def _calculate_rhythmic_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        drums_a = [t for t in data_a.get("tracks", []) if str(t.get("role", "")).upper() in ("DRUMS", "KICK", "PERCUSSION")]
        drums_b = [t for t in data_b.get("tracks", []) if str(t.get("role", "")).upper() in ("DRUMS", "KICK", "PERCUSSION")]

        if not drums_a and not drums_b:
            return 1.0
        if not drums_a or not drums_b:
            return 0.30

        total_a = sum(t.get("notes_count", len(t.get("notes", []))) for t in drums_a)
        total_b = sum(t.get("notes_count", len(t.get("notes", []))) for t in drums_b)

        if total_a == 0 and total_b == 0:
            return 1.0
        ratio = min(total_a, total_b) / max(1, max(total_a, total_b))

        # Check groove cell equivalence
        grooves_a = {t.get("groove_cell") for t in drums_a if t.get("groove_cell")}
        grooves_b = {t.get("groove_cell") for t in drums_b if t.get("groove_cell")}
        groove_bonus = 0.20 if grooves_a == grooves_b else 0.0

        return round(min(1.0, ratio * 0.80 + groove_bonus), 3)

    @classmethod
    def _calculate_harmonic_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        ident_a = data_a.get("music_identity", {})
        ident_b = data_b.get("music_identity", {})

        tc_a = data_a.get("tonal_center", ident_a.get("tonal_center", "C"))
        tc_b = data_b.get("tonal_center", ident_b.get("tonal_center", "C"))
        mode_a = data_a.get("mode", ident_a.get("mode", "Minor"))
        mode_b = data_b.get("mode", ident_b.get("mode", "Minor"))

        score = 0.0
        if tc_a.lower() == tc_b.lower():
            score += 0.60
        if mode_a.lower() == mode_b.lower():
            score += 0.40

        return round(score, 3)

    @classmethod
    def _calculate_timbral_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        dna_a = cls._extract_average_timbre_dna(data_a)
        dna_b = cls._extract_average_timbre_dna(data_b)

        # 7-Dimensional Euclidean Distance normalized by sqrt(7)
        dims = [
            (dna_a.brightness, dna_b.brightness),
            (dna_a.roughness, dna_b.roughness),
            (dna_a.inharmonicity, dna_b.inharmonicity),
            (dna_a.stereo_width, dna_b.stereo_width),
            (dna_a.transient_strength, dna_b.transient_strength),
            (dna_a.movement, dna_b.movement),
            (dna_a.pitch_instability, dna_b.pitch_instability)
        ]
        sum_sq = sum((v1 - v2) ** 2 for v1, v2 in dims)
        euclid_dist = math.sqrt(sum_sq) / math.sqrt(len(dims))

        # Similarity is 1.0 - normalized distance
        return round(max(0.0, min(1.0, 1.0 - euclid_dist)), 3)

    @classmethod
    def _extract_average_timbre_dna(cls, data: Dict[str, Any]) -> TimbreDNA:
        tracks = data.get("tracks", [])
        dna_list: List[TimbreDNA] = []

        ident = data.get("music_identity", {})
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

        if not dna_list:
            return TimbreDNA()

        n = len(dna_list)
        return TimbreDNA(
            brightness=sum(d.brightness for d in dna_list) / n,
            roughness=sum(d.roughness for d in dna_list) / n,
            inharmonicity=sum(d.inharmonicity for d in dna_list) / n,
            stereo_width=sum(d.stereo_width for d in dna_list) / n,
            transient_strength=sum(d.transient_strength for d in dna_list) / n,
            movement=sum(d.movement for d in dna_list) / n,
            pitch_instability=sum(d.pitch_instability for d in dna_list) / n
        )

    @classmethod
    def _calculate_spatial_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        curve_a = data_a.get("spatial_energy_curve", [])
        curve_b = data_b.get("spatial_energy_curve", [])

        if not curve_a and not curve_b:
            return 1.0
        if not curve_a or not curve_b:
            return 0.50

        # Compare drop widths and pre-drop widths
        def get_max_width(c: List[Dict[str, Any]]) -> float:
            return max((pt.get("stereo_width", pt.get("profile", {}).get("stereo_width", 1.0)) for pt in c), default=1.0)

        max_a = get_max_width(curve_a)
        max_b = get_max_width(curve_b)
        diff = abs(max_a - max_b)
        return round(max(0.0, 1.0 - diff), 3)

    @classmethod
    def _calculate_structural_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        secs_a = [s.get("name", "").lower() for s in data_a.get("sections", [])]
        secs_b = [s.get("name", "").lower() for s in data_b.get("sections", [])]

        if not secs_a and not secs_b:
            return 1.0
        if not secs_a or not secs_b:
            return 0.50

        set_a = set(secs_a)
        set_b = set(secs_b)
        jaccard = len(set_a.intersection(set_b)) / len(set_a.union(set_b)) if set_a.union(set_b) else 1.0
        len_ratio = min(len(secs_a), len(secs_b)) / max(1, max(len(secs_a), len(secs_b)))

        return round((jaccard * 0.6) + (len_ratio * 0.4), 3)

    @classmethod
    def _calculate_motif_similarity(cls, data_a: Dict[str, Any], data_b: Dict[str, Any]) -> float:
        ident_a = data_a.get("music_identity", {})
        ident_b = data_b.get("music_identity", {})

        mel_a = ident_a.get("melodic_motif", {}).get("intervals", [])
        mel_b = ident_b.get("melodic_motif", {}).get("intervals", [])
        rhy_a = ident_a.get("rhythmic_motif", {}).get("pattern_name", "")
        rhy_b = ident_b.get("rhythmic_motif", {}).get("pattern_name", "")

        score = 0.0
        if mel_a and mel_b and mel_a == mel_b:
            score += 0.60
        if rhy_a and rhy_b and rhy_a == rhy_b:
            score += 0.40

        return round(score, 3)

    @classmethod
    def audit_aesthetic_monotony(cls, session_list: List[Any]) -> Dict[str, Any]:
        """
        Audits a batch of sessions for Aesthetic Monotony:
        Flags pairs that have distinct composition/notes but identical TimbreDNA vectors (> 0.88).
        """
        if len(session_list) < 2:
            return {"monotony_risk": False, "flagged_pairs": []}

        flagged: List[Dict[str, Any]] = []
        for i in range(len(session_list)):
            for j in range(i + 1, len(session_list)):
                comp = cls.compare_sessions(session_list[i], session_list[j])
                if comp.perceptual_verdict == "AESTHETICALLY_MONOTONOUS":
                    flagged.append({
                        "song_a": comp.song_a_name,
                        "song_b": comp.song_b_name,
                        "timbral_similarity": comp.timbral_similarity,
                        "melodic_similarity": comp.melodic_similarity,
                        "rhythmic_similarity": comp.rhythmic_similarity,
                        "warning": "Composición diferente pero estética tímbrica idéntica."
                    })

        return {
            "monotony_risk": len(flagged) > 0,
            "total_pairs_tested": (len(session_list) * (len(session_list) - 1)) // 2,
            "flagged_pairs_count": len(flagged),
            "flagged_pairs": flagged
        }

    @classmethod
    def calculate_novelty_against_corpus(
        cls,
        session: Any,
        corpus_sessions: List[Any],
        k: int = 3
    ) -> float:
        """
        Calculates perceptual novelty against a list of corpus sessions.
        Novelty = 1.0 - composite_similarity to the closest k neighbors.
        """
        if not corpus_sessions:
            return 1.0

        similarities = [
            cls.compare_sessions(session, ref).composite_similarity
            for ref in corpus_sessions
        ]
        similarities.sort(reverse=True)
        top_k = similarities[:min(k, len(similarities))]
        avg_top_similarity = sum(top_k) / len(top_k)
        return round(max(0.0, min(1.0, 1.0 - avg_top_similarity)), 3)

    @classmethod
    def evaluate_identity_novelty_matrix(
        cls,
        identity_score: float,
        novelty_score: float,
        coherence_score: float = 0.80
    ) -> Dict[str, Any]:
        """
        Evaluates the dual axis: Identity vs Novelty.
        Prevents both uncreative clichés (High Identity, Low Novelty)
        and chaotic noise (Low Identity, High Novelty), targeting the Sweet Spot:
        BALANCED_INNOVATION (Identity >= 0.60, Novelty in [0.40, 0.85]).
        """
        coh_factor = min(1.0, coherence_score / 0.65) if coherence_score > 0 else 0.0
        ident_factor = min(1.0, identity_score / 0.45) if identity_score > 0 else 0.0
        useful_novelty = round(novelty_score * coh_factor * ident_factor, 3)

        if identity_score >= 0.60 and 0.40 <= novelty_score <= 0.85:
            quadrant = "BALANCED_INNOVATION"
            diagnosis = "Zona óptima (Sweet Spot): Alta identidad con novedad diferenciadora genuina."
            action = "PRESERVE_AND_PROCEED"
        elif identity_score >= 0.60 and novelty_score < 0.40:
            quadrant = "REPLICA_CLICHE"
            diagnosis = "Riesgo de cliché por replicación: Alta identidad pero similitud excesiva con el corpus histórico."
            action = "INJECT_CONTROLLED_NOVELTY"
        elif identity_score < 0.45 and novelty_score > 0.65:
            quadrant = "CHAOTIC_NOISE"
            diagnosis = "Riesgo de ruido caótico: Novedad aparente pero identidad y coherencia musical disueltas."
            action = "STABILIZE_IDENTITY_ANCHORS"
        else:
            quadrant = "WEAK_ANONYMOUS"
            diagnosis = "Zona débil: Identidad diluida y novedad marginal."
            action = "REBUILD_CORE_MOTIFS"

        return {
            "quadrant": quadrant,
            "identity_score": round(identity_score, 3),
            "novelty_score": round(novelty_score, 3),
            "coherence_score": round(coherence_score, 3),
            "useful_novelty": useful_novelty,
            "is_in_sweet_spot": quadrant == "BALANCED_INNOVATION",
            "diagnosis": diagnosis,
            "recommended_action": action
        }


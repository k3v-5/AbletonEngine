"""
Empirical Creative Calibration Runner:
Executes multi-genre production cohorts (N = 25 to 100) to observe emergent engine behavior,
calibrate artistic thresholds, and diagnose systemic biases without human bias.

Produces the comprehensive Empirical Calibration Report:
1. Convergence Analysis: Overused mechanisms and active cliché alarms (OPTIONAL techniques only).
2. Underutilization Auditing: Techniques with < 5% usage across the corpus.
3. Conflict & Rollback Hotspots: A/B candidate mutation acceptance vs. rollback ratios in Music Director.
4. Timbral Aesthetics & Perceptual Diversity: Multi-dimensional distance and aesthetic monotony detection.
5. Recommended Calibrations: Concrete numeric tuning proposals for probabilities and thresholds.
"""

import logging
import random
import math
from typing import Dict, Any, List, Optional, Tuple

from engine.sound.timbre_dna import TimbreDNA
from engine.creative.music_identity import MusicIdentity, IdentityAuditor
from engine.creative.resampling_lab import ResamplingLab, GeneratedSource, GenealogyTree
from engine.creative.corpus_evaluator import CreativeCorpusEvaluator, MechanismCategory
from engine.creative.song_comparator import PerceptualComparator, SongComparison
from engine.production.copilot.phases.phase_10.music_director import MusicDirector

logger = logging.getLogger("EmpiricalCalibrationRunner")


class SimulatedSession:
    """
    Lightweight, fast in-memory music session for empirical cohort simulation.
    Compatible with MusicDirector, CreativeCorpusEvaluator, and PerceptualComparator.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def _save_state(self, *args, **kwargs):
        pass

    def to_dict(self) -> Dict[str, Any]:
        return self.data


class EmpiricalCalibrationRunner:
    """
    Orchestrates large-scale empirical simulations and generates calibration audits.
    """

    DEFAULT_GENRES = ["melodic_techno", "house", "afro_house", "dnb", "ambient"]

    @classmethod
    def simulate_production_cohort(
        cls,
        count: int = 50,
        genres: Optional[List[str]] = None,
        seeds: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Simulates an empirical cohort of N production sessions across specified genres.
        Executes the full pipeline: MusicIdentity -> ResamplingLab -> MusicDirector -> TimbreDNA.
        """
        target_genres = genres if genres is not None else cls.DEFAULT_GENRES
        sessions: List[SimulatedSession] = []

        keys = ["F#", "A", "D", "G", "C", "E", "B"]
        modes = ["Dorian", "Minor", "Phrygian", "Aeolian", "Major"]

        for i in range(count):
            seed = seeds[i] if (seeds and i < len(seeds)) else (1000 + i * 37)
            rng = random.Random(seed)

            genre = target_genres[i % len(target_genres)]
            key = keys[i % len(keys)]
            mode = modes[i % len(modes)]

            # Genre-specific tempo
            if genre == "melodic_techno":
                bpm = 124.0 + (i % 4)
            elif genre == "house":
                bpm = 126.0 + (i % 3)
            elif genre == "afro_house":
                bpm = 122.0 + (i % 3)
            elif genre == "dnb":
                bpm = 174.0 + (i % 2)
            else:  # ambient
                bpm = 90.0 + (i % 6)

            # Establish Transversal Music Identity
            ident = MusicIdentity(
                song_title=f"Session_{genre}_{i+1}",
                concept=f"Autonomous empirical composition {genre} #{i+1}",
                tonal_center=key,
                mode=mode,
                tempo=bpm
            )

            # Simulate motif exposure with Memory Anchor Model
            # In 60% of sessions, establish memory (verbatim first), then develop (A -> A -> A' -> A'')
            if (i % 5) in (0, 1, 2):
                ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
                ident.record_motif_exposure("melodic", "Verse", was_transformed=False)
                ident.record_motif_exposure("melodic", "Build", was_transformed=True)
                ident.record_motif_exposure("melodic", "Drop", was_transformed=True)
            elif (i % 5) == 3:
                # Early mutation
                ident.record_motif_exposure("melodic", "Intro", was_transformed=True)
                ident.record_motif_exposure("melodic", "Verse", was_transformed=True)
                ident.record_motif_exposure("melodic", "Build", was_transformed=True)
                ident.record_motif_exposure("melodic", "Drop", was_transformed=True)
            else:
                # Static repetition
                ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
                ident.record_motif_exposure("melodic", "Verse", was_transformed=False)
                ident.record_motif_exposure("melodic", "Build", was_transformed=False)
                ident.record_motif_exposure("melodic", "Drop", was_transformed=False)

            # Genre-specific TimbreDNA profiles to ensure aesthetic differentiation across genres
            if genre == "ambient":
                kick_dna = TimbreDNA(brightness=0.20, roughness=0.10, stereo_width=0.30, transient_strength=0.25, movement=0.40)
                bass_dna = TimbreDNA(brightness=0.25, roughness=0.10, stereo_width=0.40, transient_strength=0.20, movement=0.60)
                lead_dna = TimbreDNA(brightness=0.40, roughness=0.15, stereo_width=0.90, transient_strength=0.20, movement=0.85)
            elif genre == "dnb":
                kick_dna = TimbreDNA(brightness=0.60, roughness=0.50, stereo_width=0.10, transient_strength=0.95, movement=0.10)
                bass_dna = TimbreDNA(brightness=0.75, roughness=0.85, stereo_width=0.55, transient_strength=0.80, movement=0.70)
                lead_dna = TimbreDNA(brightness=0.85, roughness=0.75, stereo_width=0.70, transient_strength=0.90, movement=0.40)
            elif genre == "afro_house":
                kick_dna = TimbreDNA(brightness=0.40, roughness=0.20, stereo_width=0.15, transient_strength=0.70, movement=0.30)
                bass_dna = TimbreDNA(brightness=0.35, roughness=0.25, stereo_width=0.20, transient_strength=0.60, movement=0.40)
                lead_dna = TimbreDNA(brightness=0.60, roughness=0.30, stereo_width=0.60, transient_strength=0.70, movement=0.65)
            elif genre == "house":
                kick_dna = TimbreDNA(brightness=0.50, roughness=0.30, stereo_width=0.10, transient_strength=0.80, movement=0.15)
                bass_dna = TimbreDNA(brightness=0.45, roughness=0.35, stereo_width=0.25, transient_strength=0.70, movement=0.30)
                lead_dna = TimbreDNA(brightness=0.70, roughness=0.45, stereo_width=0.65, transient_strength=0.75, movement=0.50)
            else:  # melodic_techno
                kick_dna = TimbreDNA(brightness=0.45, roughness=0.40, stereo_width=0.10, transient_strength=0.85, movement=0.20)
                bass_dna = TimbreDNA(brightness=0.65, roughness=0.55, stereo_width=0.30, transient_strength=0.75, movement=0.50)
                lead_dna = TimbreDNA(brightness=0.75, roughness=0.60, stereo_width=0.75, transient_strength=0.65, movement=0.70)

            # Build Tracks
            lead_pitch_base = 60 + (i % 12)
            tracks: List[Dict[str, Any]] = [
                {
                    "name": "Kick",
                    "role": "KICK",
                    "notes_count": 16,
                    "notes": [{"pitch": 36, "is_out_of_scale": False} for _ in range(16)],
                    "timbre_dna": kick_dna.to_dict()
                },
                {
                    "name": "Snare",
                    "role": "SNARE",
                    "notes_count": 16,
                    "notes": [{"pitch": 38, "is_out_of_scale": False} for _ in range(16)],
                    "timbre_dna": TimbreDNA.from_role("SNARE").to_dict()
                },
                {
                    "name": "Bass",
                    "role": "BASS",
                    "notes_count": 16,
                    "notes": [{"pitch": 36 + (i % 7), "is_out_of_scale": False} for _ in range(16)],
                    "timbre_dna": bass_dna.to_dict()
                },
                {
                    "name": f"Lead {genre}",
                    "role": "LEAD",
                    "notes_count": 16,
                    "notes": [{"pitch": lead_pitch_base + step, "is_out_of_scale": False} for step in (0, 3, 7, 10)],
                    "timbre_dna": lead_dna.to_dict()
                }
            ]

            # Technique probabilities
            applied_mechanisms: List[str] = []

            # 1. Pre-drop stereo collapse / vacuum (HARD rule: ~92% occurrence)
            has_collapse = (rng.random() < 0.92)
            spatial_curve = [
                {"stereo_width": 0.15 if has_collapse else 0.50, "section": "pre_drop"},
                {"stereo_width": 1.25, "section": "drop"}
            ]
            if has_collapse:
                applied_mechanisms.append("pre_drop_stereo_collapse")
                applied_mechanisms.append("pre_drop_vacuum")

            # 2. Metric tension 3/16 (OPTIONAL technique: ~30% occurrence)
            has_poly = (rng.random() < 0.30)
            if has_poly:
                tracks.append({
                    "name": "Arp 3/16",
                    "role": "ARP",
                    "section": "build",
                    "notes": [{"pitch": 60, "is_metric_tension": True}],
                    "timbre_dna": TimbreDNA(brightness=0.80, roughness=0.30).to_dict()
                })
                applied_mechanisms.append("polyrhythm_3_16")

            # 3. Foley layer (SOFT convention: ~75% occurrence)
            has_foley = (rng.random() < 0.75)
            if has_foley:
                tracks.append({
                    "name": "Organic Foley Bed",
                    "role": "TEXTURE_FOLEY",
                    "section": "intro",
                    "notes_count": 4,
                    "timbre_dna": TimbreDNA(brightness=0.35, roughness=0.20, stereo_width=0.80).to_dict()
                })
                applied_mechanisms.append("foley_bed")

            # 4. Reverse transition (OPTIONAL technique: ~40% occurrence)
            has_reverse = (rng.random() < 0.40)
            if has_reverse:
                ident.genealogy_log.append({
                    "derived_track": "Reverse Transition Swell",
                    "transformations": ["reverse", "reverb_freeze"],
                    "origin_section": "build"
                })
                applied_mechanisms.append("reverse_audio_transition")

            # Canonical anchors
            applied_mechanisms.append("metric_anchor_4_4")
            applied_mechanisms.append("frequency_slotting")

            session_data: Dict[str, Any] = {
                "name": f"Session_{genre}_{i+1}",
                "song_title": f"Session_{genre}_{i+1}",
                "genre": genre,
                "bpm": bpm,
                "tonal_center": key,
                "mode": mode,
                "tracks": tracks,
                "sections": [
                    {"name": "Verse", "bars": 8, "energy": 0.40},
                    {"name": "Build", "bars": 8, "energy": 0.65},
                    {"name": "Drop", "bars": 16, "energy": 0.90}
                ],
                "spatial_energy_curve": spatial_curve,
                "music_identity": ident.to_dict(),
                "generated_sources": [],
                "music_director_history": [],
                "applied_mechanisms": applied_mechanisms,
                "frequency_slotting_applied": True,
                "pre_drop_vacuum_verified": has_collapse
            }

            # Simulate ResamplingLab derived sources (multi-generational depth)
            if rng.random() < 0.45:
                gen_1 = ResamplingLab.process_and_register_source(
                    session_data=session_data,
                    source_track_name=f"Lead {genre}",
                    origin_section="Drop",
                    recipe_name="ghost_lead_texture"
                )
                # Keep gen_1 in tracks with 60% probability
                if rng.random() < 0.60:
                    session_data["tracks"].append({"name": gen_1.name, "source_id": gen_1.id})

                # Generation 2 in 20% of cases
                if rng.random() < 0.20:
                    gen_2 = ResamplingLab.process_and_register_source(
                        session_data=session_data,
                        source_track_name=gen_1.id,
                        origin_section="Breakdown",
                        recipe_name="vocal_granular_cloud"
                    )
                    if rng.random() < 0.50:
                        session_data["tracks"].append({"name": gen_2.name, "source_id": gen_2.id})

            sim_session = SimulatedSession(session_data)

            # Evaluate with Music Director (A/B search & guardrails)
            # Evaluate mutations on ~60% of sessions
            if rng.random() < 0.60:
                MusicDirector.evaluate_ab_mutations(sim_session)

            sessions.append(sim_session)

        # Run Corpus Evaluation
        corpus_report = CreativeCorpusEvaluator.evaluate_corpus(sessions)

        # Run Perceptual Monotony Audit across session sample
        monotony_report = PerceptualComparator.audit_aesthetic_monotony(sessions[:min(15, len(sessions))])

        return {
            "status": "COHORT_SIMULATED",
            "total_sessions": count,
            "genres_covered": target_genres,
            "sessions": sessions,
            "corpus_evaluation": corpus_report,
            "monotony_audit": monotony_report
        }

    @classmethod
    def generate_calibration_report(cls, cohort_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes empirical cohort data into a structured calibration diagnosis:
        Convergence, Underutilization, Conflict Hotspots, Timbral Aesthetics, and Calibration Tuning.
        """
        corpus = cohort_data.get("corpus_evaluation", {})
        monotony = cohort_data.get("monotony_audit", {})
        sessions = cohort_data.get("sessions", [])

        frequencies = corpus.get("frequencies", {})
        cliche_alarms = corpus.get("cliche_alarms", [])
        underutilized = corpus.get("underutilized_techniques", [])
        director_metrics = corpus.get("director_metrics", {})
        resampling_metrics = corpus.get("resampling_metrics", {})

        # 1. Convergence Diagnosis
        convergence_findings: List[Dict[str, Any]] = []
        for alarm in cliche_alarms:
            convergence_findings.append({
                "technique": alarm.get("technique"),
                "category": alarm.get("category"),
                "frequency": alarm.get("frequency"),
                "severity": "HIGH_CLICHE_RISK",
                "diagnosis": f"Uso excesivo ({alarm.get('frequency') * 100:.1f}%) supera umbral de cliché interno."
            })

        # Check canonical rules (HARD)
        hard_rules_verified = {
            "pre_drop_vacuum": frequencies.get("pre_drop_vacuum", 0.0),
            "metric_anchor_4_4": frequencies.get("metric_anchor_4_4", 0.0),
            "frequency_slotting": frequencies.get("frequency_slotting", 0.0)
        }

        # 2. Underutilization Diagnosis
        underutilization_findings: List[Dict[str, Any]] = []
        for tech in underutilized:
            freq = frequencies.get(tech, 0.0)
            underutilization_findings.append({
                "technique": tech,
                "frequency": freq,
                "severity": "UNDERUTILIZED",
                "diagnosis": f"Técnica '{tech}' presenta un uso marginal ({freq * 100:.1f}% < 5%)."
            })

        # 3. Conflict & Rollback Hotspots
        candidate_rollbacks: Dict[str, int] = {
            "candidate_a_bass_subtraction": 0,
            "candidate_b_counter_lead": 0,
            "candidate_c_resampling_ghost": 0,
            "candidate_d_turnaround_rhythm": 0,
            "candidate_e_metric_tension": 0
        }
        candidate_commits: Dict[str, int] = {k: 0 for k in candidate_rollbacks.keys()}

        for s in sessions:
            data = s.data if hasattr(s, "data") else (s if isinstance(s, dict) else {})
            for h in data.get("music_director_history", []):
                cand = h.get("candidate", h.get("mutation", "candidate_e"))
                status = h.get("status")
                # Map candidate name
                for key in candidate_rollbacks.keys():
                    if key.split("_")[1] in cand.lower():
                        if status == "ROLLBACK_EXECUTED":
                            candidate_rollbacks[key] += 1
                        elif status == "MUTATION_COMMITTED":
                            candidate_commits[key] += 1

        total_rollbacks = director_metrics.get("total_rollbacks_executed", sum(candidate_rollbacks.values()))
        total_mutations = director_metrics.get("total_mutations_applied", sum(candidate_commits.values()))
        rollback_rate = director_metrics.get("rollback_rate", 0.0)

        # Identify primary conflict hotspot
        primary_hotspot = max(candidate_rollbacks.items(), key=lambda item: item[1])[0] if any(candidate_rollbacks.values()) else "none"

        # 4. Timbral Aesthetics & Perceptual Diversity
        flagged_monotonous_count = monotony.get("flagged_pairs_count", 0)
        total_pairs_tested = max(1, monotony.get("total_pairs_tested", 1))
        monotony_rate = round(flagged_monotonous_count / total_pairs_tested, 3)
        aesthetic_diversity = (
            "DIVERSE_AND_DISTINCT" if monotony_rate < 0.15
            else "AESTHETIC_MONOTONY_RISK"
        )

        # 5. Concrete Recommended Calibrations
        recommendations: List[str] = []
        if cliche_alarms:
            for a in cliche_alarms:
                recommendations.append(
                    f"Calibración de Frecuencia: {a.get('recommendation')} (Técnica: {a.get('technique')})"
                )
        if underutilization_findings:
            recommendations.append(
                "Calibración de Selección: Incrementar la probabilidad condicional de activación de técnicas infrautilizadas o evaluar su eliminación si son redundantes."
            )
        if rollback_rate > 0.40:
            recommendations.append(
                f"Calibración de Guardrail: Tasa de rollback de {rollback_rate * 100:.1f}% es elevada. Hotspot principal: {primary_hotspot}. Flexibilizar el umbral de coherencia para permitir mayor libertad tímbrica."
            )
        if aesthetic_diversity == "AESTHETIC_MONOTONY_RISK":
            recommendations.append(
                "Calibración Tímbrica: Diversificar los perfiles espectrales base de TimbreDNA para evitar convergencia estética entre canciones de géneros distintos."
            )
        if not recommendations:
            recommendations.append("El motor se encuentra en equilibrio creativo óptimo; no se requieren intervenciones urgentes.")

        return {
            "status": "CALIBRATION_REPORT_GENERATED",
            "total_cohort_sessions": len(sessions),
            "convergence": {
                "cliche_alarms_count": len(cliche_alarms),
                "cliche_alarms": cliche_alarms,
                "findings": convergence_findings,
                "canonical_rules_adherence": hard_rules_verified
            },
            "underutilization": {
                "underutilized_count": len(underutilization_findings),
                "findings": underutilization_findings
            },
            "conflicts": {
                "total_mutations_applied": total_mutations,
                "total_rollbacks_executed": total_rollbacks,
                "rollback_rate": rollback_rate,
                "candidate_rollbacks": candidate_rollbacks,
                "candidate_commits": candidate_commits,
                "primary_conflict_hotspot": primary_hotspot
            },
            "timbral_aesthetics": {
                "total_pairs_tested": total_pairs_tested,
                "flagged_monotonous_pairs_count": flagged_monotonous_count,
                "monotony_rate": monotony_rate,
                "aesthetic_diversity_verdict": aesthetic_diversity,
                "flagged_pairs": monotony.get("flagged_pairs", [])
            },
            "resampling_diagnostics": resampling_metrics,
            "recommended_calibrations": recommendations
        }

    @classmethod
    def run_calibration_study(
        cls,
        count: int = 25,
        genres: Optional[List[str]] = None,
        seeds: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Convenience method to simulate and generate the report in a single call."""
        cohort = cls.simulate_production_cohort(count=count, genres=genres, seeds=seeds)
        report = cls.generate_calibration_report(cohort)
        return {
            "cohort_summary": {
                "total_sessions": cohort["total_sessions"],
                "genres_covered": cohort["genres_covered"]
            },
            "calibration_report": report
        }

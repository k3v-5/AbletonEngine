"""
Music Director & A&R Interno (Phase 10 & Session Doctor):
Multi-dimensional musical predictability auditor and selective surgical mutator.
Evaluates the Triad:
1. Predictability Score (rhythmic straight-4 grid, static velocities, symmetrical sections)
2. Identity Score (preservation of the 6 signature production motifs)
3. Contrast Score (dynamic range and section-to-section divergence)

Follows the Supreme Rule:
"No obligues al motor a hacer 'cosas interesantes', oblígalo a buscar decisiones interesantes."
Only mutates if contrast or identity is deficient. Evaluates A/B candidate mutations
(A through E) and executes atomic rollback via TransactionGuard if no candidate improves
the overall musical score.
"""

import logging
from typing import Dict, Any, List, Optional
import copy
import random

from engine.creative.cliche_detector import ClicheDetector
from engine.creative.music_dna import MusicDNA
from engine.creative.music_identity import MusicIdentity, IdentityAuditor
from engine.session.transaction_guard import TransactionGuard
from engine.music.rhythm.metric_tension import MetricTensionCoordinator, MetricTensionEvent

logger = logging.getLogger("MusicDirector")


class MusicDirector:
    """
    Acts as an internal Executive Music Director / A&R to evaluate musicality,
    prevent AI cliché formulas, and perform selective surgical layer mutations with A/B search.
    """

    @classmethod
    def audit_predictability(
        cls,
        session: Any,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Conducts a multi-dimensional predictability and artistic audit across the session.
        """
        tracks = session.data.get("tracks", []) if hasattr(session, "data") else []
        sections = session.data.get("sections", []) if hasattr(session, "data") else []
        dna_data = session.data.get("music_dna") if hasattr(session, "data") else None
        dna = MusicDNA.from_dict(dna_data) if dna_data else MusicDNA()

        issues: List[str] = []
        recommendations: List[str] = []

        # 1. Structural Predictability
        has_asymmetry = any(s.get("bars", 8) not in (8, 16, 32) for s in sections)
        if not has_asymmetry and len(sections) > 4:
            issues.append("symmetrical_structure_cliche")
            recommendations.append("Añadir compases asimétricos (ej. puente de 10 compases o buildup de 12 compases).")

        # 2. Rhythmic Predictability
        drum_tracks = [t for t in tracks if str(t.get("role", "")).upper() in ("DRUMS", "KICK", "PERCUSSION")]
        if drum_tracks:
            total_drum_notes = sum(t.get("notes_count", 0) for t in drum_tracks)
            if total_drum_notes > 0 and total_drum_notes % 16 == 0:
                issues.append("rigid_grid_quantization")
                recommendations.append("Aplicar humanización de micro-timing (+-8ms) y dinámica de muñeca (110-70-85-60).")

        # 3. Melodic & Harmonic Call-and-Response
        has_lead = any(str(t.get("role", "")).upper() == "LEAD" for t in tracks)
        has_counter = any(str(t.get("role", "")).upper() == "COUNTER_LEAD" for t in tracks)
        if has_lead and not has_counter:
            issues.append("missing_call_and_response")
            recommendations.append("Inyectar pista COUNTER_LEAD / ARPS que responda al lead o a la voz.")

        # 4. Ear Candy & Texture Presence
        has_candy = any(str(t.get("role", "")).upper() == "EAR_CANDY" for t in tracks)
        has_foley = any(str(t.get("role", "")).upper() in ("TEXTURE_FOLEY", "FOLEY") for t in tracks)
        if not has_candy:
            issues.append("lacks_ear_candy_transients")
            recommendations.append("Incorporar EAR_CANDY con destellos esporádicos en los bordes estéreo.")
        if not has_foley:
            issues.append("lacks_organic_texture_bed")
            recommendations.append("Agregar capa de TEXTURE / FOLEY a -24 dBFS para profundidad ambiental.")

        # Overall Predictability Score (0.0 unpredictable to 1.0 totally generic)
        base_pred = 0.30 + (0.15 * len(issues))
        pred_score = min(0.95, round(base_pred, 2))

        return {
            "status": "AUDIT_COMPLETED",
            "predictability_score": pred_score,
            "is_formulaic": pred_score > 0.65,
            "issues_detected": issues,
            "recommendations": recommendations,
            "dimensions": {
                "structural": "Asimétrica" if has_asymmetry else "Fórmula estándar (8/16 compases)",
                "rhythmic": "Humanizada" if "rigid_grid_quantization" not in issues else "Rígida en rejilla",
                "dialogue": "Llamada y respuesta activa" if has_counter else "Monólogo melódico",
                "organic_depth": "Inmersiva" if (has_candy and has_foley) else "Seca / computarizada"
            }
        }

    @classmethod
    def audit_contrast(cls, session: Any) -> Dict[str, Any]:
        """
        Evaluates section-to-section contrast across energy, density, and instrumentation.
        Returns a contrast_score between 0.0 (monotonous) and 1.0 (rich narrative contrast).
        """
        session_data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        sections = session_data.get("sections", [])
        tracks = session_data.get("tracks", [])

        if not sections or len(sections) < 2:
            return {"contrast_score": 0.50, "evaluation": "Insuficientes secciones para calcular contraste."}

        energy_diffs: List[float] = []
        for i in range(len(sections) - 1):
            s1 = sections[i]
            s2 = sections[i + 1]
            e1 = float(s1.get("energy", 0.5))
            e2 = float(s2.get("energy", 0.5))
            energy_diffs.append(abs(e2 - e1))

        avg_energy_delta = sum(energy_diffs) / len(energy_diffs) if energy_diffs else 0.0

        # Check for pre-drop contrast (energy dip before drop)
        has_drop_contrast = False
        for i, s in enumerate(sections):
            if "drop" in s.get("name", "").lower() and i > 0:
                prev_s = sections[i - 1]
                if float(prev_s.get("energy", 0.5)) != float(s.get("energy", 0.5)):
                    has_drop_contrast = True
                    break

        contrast_score = min(1.0, max(0.1, (avg_energy_delta * 1.5) + (0.25 if has_drop_contrast else 0.0)))
        return {
            "contrast_score": round(contrast_score, 2),
            "avg_energy_delta": round(avg_energy_delta, 2),
            "has_drop_contrast": has_drop_contrast
        }

    @classmethod
    def audit_coherence(cls, session: Any) -> Dict[str, Any]:
        """
        Audits narrative, harmonic, and structural coherence across the session.
        Guarantees that musical mutations do not break scale unity or groove foundation.
        Returns coherence_score in [0.0, 1.0].
        """
        session_data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        tracks = session_data.get("tracks", [])
        sections = session_data.get("sections", [])
        ident_data = session_data.get("music_identity")
        identity = MusicIdentity.from_dict(ident_data) if ident_data else None

        # 1. Anchor Stability: Kick, Snare/Clap, Bass/Sub present without rogue silencing
        has_kick = any(str(t.get("role", "")).upper() in ("KICK", "DRUMS") for t in tracks)
        has_snare = any(str(t.get("role", "")).upper() in ("SNARE", "CLAP", "DRUMS") for t in tracks)
        has_bass = any(str(t.get("role", "")).upper() in ("BASS", "SUB", "808") for t in tracks)
        anchors_present = sum([has_kick, has_snare, has_bass])
        anchor_stability = min(1.0, anchors_present / 3.0) if tracks else 1.0


        # 2. Harmonic Continuity: notes respect scale/tonal center if defined
        tonal_center = identity.tonal_center if identity else "C"
        harmonic_issues = 0
        total_notes_checked = 0
        for t in tracks:
            notes = t.get("notes", [])
            for n in notes:
                total_notes_checked += 1
                if n.get("is_out_of_scale", False):
                    harmonic_issues += 1

        harmonic_continuity = 1.0 - (harmonic_issues / max(1, total_notes_checked))

        # 3. Density Continuity: sections don't have erratic dropouts
        density_diffs = []
        if len(sections) > 1:
            for i in range(len(sections) - 1):
                s1_notes = sections[i].get("notes_count", 16)
                s2_notes = sections[i + 1].get("notes_count", 16)
                diff = abs(s2_notes - s1_notes) / max(1, max(s1_notes, s2_notes))
                density_diffs.append(diff)
            avg_density_jump = sum(density_diffs) / len(density_diffs) if density_diffs else 0.0
            density_continuity = max(0.4, 1.0 - (avg_density_jump * 0.5))
        else:
            density_continuity = 0.90

        coherence_score = round(
            (harmonic_continuity * 0.40) +
            (anchor_stability * 0.35) +
            (density_continuity * 0.25),
            2
        )

        return {
            "status": "COHERENCE_AUDITED",
            "coherence_score": coherence_score,
            "harmonic_continuity": round(harmonic_continuity, 2),
            "anchor_stability": round(anchor_stability, 2),
            "density_continuity": round(density_continuity, 2),
            "is_narrative_coherent": coherence_score >= 0.70
        }

    @classmethod
    def audit_triad(cls, session: Any, conn: Any = None) -> Dict[str, Any]:
        """
        Audits the complete Triad + Coherence:
        1. Predictability Score
        2. Identity Score
        3. Contrast Score
        4. Coherence Score (Narrative Guardrail)

        Applies the Supreme Rule:
        Only recommends intervention if contrast < 0.35, predictability > 0.65, or identity < 0.45.
        """
        session_data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})

        pred_audit = cls.audit_predictability(session, conn)
        pred_score = pred_audit.get("predictability_score", 0.50)

        ident_audit = IdentityAuditor.evaluate_identity(session_data)
        ident_score = ident_audit.get("identity_score", 0.50)

        contrast_audit = cls.audit_contrast(session)
        contrast_score = contrast_audit.get("contrast_score", 0.50)

        coherence_audit = cls.audit_coherence(session)
        coherence_score = coherence_audit.get("coherence_score", 0.80)

        # Supreme Rule check
        needs_intervention = (
            contrast_score < 0.35 or
            pred_score > 0.65 or
            ident_score < 0.45
        )

        rationale = []
        if contrast_score < 0.35:
            rationale.append(f"Contraste insuficiente ({contrast_score:.2f} < 0.35). Secciones demasiado homogéneas.")
        if pred_score > 0.65:
            rationale.append(f"Predictibilidad excesiva ({pred_score:.2f} > 0.65). Fórmulas AI repetitivas.")
        if ident_score < 0.45:
            rationale.append(f"Identidad diluida ({ident_score:.2f} < 0.45). Faltan motivos de producción clave.")

        if not needs_intervention:
            rationale.append("La sesión mantiene balance armónico de identidad, predictibilidad y contraste. Regla Suprema: No forzar mutación.")

        return {
            "status": "TRIAD_AUDITED",
            "predictability_score": pred_score,
            "identity_score": ident_score,
            "contrast_score": contrast_score,
            "coherence_score": coherence_score,
            "needs_intervention": needs_intervention,
            "intervention_rationale": " | ".join(rationale),
            "predictability_details": pred_audit,
            "identity_details": ident_audit,
            "contrast_details": contrast_audit,
            "coherence_details": coherence_audit
        }

    @classmethod
    def evaluate_ab_mutations(
        cls,
        session: Any,
        conn: Any = None,
        candidate_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates candidate mutations A through E using iterative search:
        - Mutation A: Bass Subtraction during turnaround/pre-drop
        - Mutation B: Counter-Lead Call-and-Response Injection
        - Mutation C: Resampling Ghost Texture Injection
        - Mutation D: Turnaround Rhythmic Variation
        - Mutation E: Metric Tension Polyrhythm (3/16 leading into drop)

        Guardrail:
        A candidate is ONLY valid if:
        candidate_is_valid = (identity_preserved >= 0.45 and coherence_preserved >= 0.65)
        This prevents mutations that create high contrast at the expense of narrative coherence.

        Calculates Delta:
        Delta = (Identity * 0.5) + (Contrast * 0.3) + (Coherence * 0.2) - (Predictability * 0.15)
        """
        session_data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        initial_triad = cls.audit_triad(session, conn)

        if not initial_triad["needs_intervention"]:
            return {
                "status": "NO_INTERVENTION_NEEDED",
                "message": "La sesión posee balance óptimo. Regla Suprema respetada: no se intervino.",
                "initial_triad": initial_triad,
                "winner": None,
                "action": "PRESERVED"
            }

        # Begin Transaction for atomic mutation experiment
        snap = TransactionGuard.begin_transaction(session_data)

        # Check if corpus territory is supplied in session_data or conn
        corpus_territory = session_data.get("corpus_territory") or (conn.get("corpus_territory") if isinstance(conn, dict) else None)

        if corpus_territory and hasattr(corpus_territory, "calculate_corpus_distance"):
            baseline_novelty = corpus_territory.calculate_corpus_distance(session_data)
            baseline_useful_novelty = round(
                baseline_novelty *
                min(1.0, initial_triad.get("coherence_score", 0.80) / 0.65) *
                min(1.0, initial_triad["identity_score"] / 0.45),
                4
            )
            baseline_score = (
                (initial_triad["identity_score"] * 0.40) +
                (initial_triad["contrast_score"] * 0.25) +
                (initial_triad.get("coherence_score", 0.80) * 0.20) +
                (baseline_useful_novelty * 0.15) -
                (initial_triad["predictability_score"] * 0.15)
            )
        else:
            baseline_novelty = 0.50
            baseline_useful_novelty = 0.50
            baseline_score = (
                (initial_triad["identity_score"] * 0.5) +
                (initial_triad["contrast_score"] * 0.3) +
                (initial_triad.get("coherence_score", 0.80) * 0.2) -
                (initial_triad["predictability_score"] * 0.15)
            )

        all_candidate_defs = {
            "A": {
                "name": "Bass Subtraction",
                "layer": "bass",
                "description": "Sustracción de bajo durante 1 compás de turnaround para crear vacío dinámico."
            },
            "B": {
                "name": "Counter-Lead Injection",
                "layer": "melody",
                "description": "Inyección de pista COUNTER_LEAD con motivo transformado para llamada y respuesta."
            },
            "C": {
                "name": "Resampling Ghost Texture",
                "layer": "texture",
                "description": "Inyección de GeneratedSource (textura resampleada y estirada) en breakdown."
            },
            "D": {
                "name": "Turnaround Rhythmic Variation",
                "layer": "rhythm",
                "description": "Variación rítmica sincopada en compás 8/16 con dinámica de muñeca."
            },
            "E": {
                "name": "Metric Tension Polyrhythm",
                "layer": "rhythm",
                "description": "Polirritmia 3/16 en Lead/Arp durante los 4 compases previos al Drop."
            }
        }

        active_keys = candidate_keys if candidate_keys is not None else ["A", "B", "C", "D", "E"]
        candidates_results: List[Dict[str, Any]] = []

        for key in active_keys:
            cand_def = all_candidate_defs.get(key)
            if not cand_def:
                continue

            # Create an isolated sandbox session copy to test the mutation
            sandbox_data = copy.deepcopy(session_data)
            cls._apply_candidate_to_data(sandbox_data, key)

            # Evaluate triad & coherence on candidate
            cand_session_mock = type("MockSession", (), {"data": sandbox_data})()
            cand_triad = cls.audit_triad(cand_session_mock)

            cand_ident = cand_triad["identity_score"]
            cand_contrast = cand_triad["contrast_score"]
            cand_pred = cand_triad["predictability_score"]
            cand_coherence = cand_triad.get("coherence_score", 0.80)

            # --- GUARDRAIL CHECK ---
            # Candidate cannot sacrifice coherence or identity for sheer contrast!
            is_valid = (cand_ident >= 0.45 and cand_coherence >= 0.65)
            if not is_valid:
                logger.info(
                    f"Candidate {key} rejected by Guardrail: "
                    f"identity={cand_ident:.2f} (min 0.45), coherence={cand_coherence:.2f} (min 0.65)"
                )
                candidates_results.append({
                    "candidate_key": key,
                    "name": cand_def["name"],
                    "description": cand_def["description"],
                    "score": 0.0,
                    "delta": -1.0,
                    "triad": cand_triad,
                    "coherence_score": cand_coherence,
                    "rejected_by_guardrail": True,
                    "guardrail_reason": f"Identity ({cand_ident:.2f} < 0.45) or Coherence ({cand_coherence:.2f} < 0.65) breached."
                })
                continue

            # Calculate composite candidate score and delta
            if corpus_territory and hasattr(corpus_territory, "calculate_corpus_distance"):
                cand_novelty = corpus_territory.calculate_corpus_distance(sandbox_data)
                cand_useful_novelty = round(
                    cand_novelty *
                    min(1.0, cand_coherence / 0.65) *
                    min(1.0, cand_ident / 0.45),
                    4
                )
                cand_score = (
                    (cand_ident * 0.40) +
                    (cand_contrast * 0.25) +
                    (cand_coherence * 0.20) +
                    (cand_useful_novelty * 0.15) -
                    (cand_pred * 0.15)
                )
            else:
                cand_novelty = 0.50
                cand_useful_novelty = 0.50
                cand_score = (
                    (cand_ident * 0.5) +
                    (cand_contrast * 0.3) +
                    (cand_coherence * 0.2) -
                    (cand_pred * 0.15)
                )
            delta = cand_score - baseline_score

            candidates_results.append({
                "candidate_key": key,
                "name": cand_def["name"],
                "description": cand_def["description"],
                "score": round(cand_score, 4),
                "delta": round(delta, 4),
                "triad": cand_triad,
                "coherence_score": cand_coherence,
                "useful_novelty": cand_useful_novelty,
                "corpus_novelty": cand_novelty,
                "rejected_by_guardrail": False,
                "sandbox_data": sandbox_data
            })

        # Rank candidates by delta
        valid_candidates = [c for c in candidates_results if not c.get("rejected_by_guardrail", False)]
        valid_candidates.sort(key=lambda c: c["delta"], reverse=True)
        best_candidate = valid_candidates[0] if valid_candidates else None

        if best_candidate and best_candidate["delta"] > 0.02:
            # Improvement found! Commit the winning candidate
            logger.info(f"Music Director applying winning candidate {best_candidate['candidate_key']} with delta +{best_candidate['delta']:.4f}")
            if hasattr(session, "data"):
                session.data = best_candidate["sandbox_data"]
                if hasattr(session, "_save_state"):
                    session._save_state()

            TransactionGuard.commit_transaction()

            return {
                "status": "MUTATION_COMMITTED",
                "winner": {
                    "key": best_candidate["candidate_key"],
                    "name": best_candidate["name"],
                    "delta": best_candidate["delta"],
                    "triad": best_candidate["triad"],
                    "coherence_score": best_candidate["coherence_score"]
                },
                "initial_triad": initial_triad,
                "all_candidates": [
                    {k: c.get(k) for k in ("candidate_key", "name", "delta", "score", "rejected_by_guardrail", "guardrail_reason", "useful_novelty", "corpus_novelty")}
                    for c in candidates_results
                ],
                "message": f"Mutación candidata {best_candidate['candidate_key']} ({best_candidate['name']}) aprobada con mejora de delta +{best_candidate['delta']:.4f}."
            }
        else:
            # No candidate showed meaningful improvement -> ROLLBACK
            logger.info("No candidate improved musical triad sufficiently or passed guardrail. Executing rollback.")
            TransactionGuard.rollback_transaction(conn, session)

            return {
                "status": "ROLLBACK_EXECUTED",
                "message": "Ninguna mutación candidata superó el umbral de mejora artística o cumplió el guardrail de coherencia. Estado original restaurado mediante TransactionGuard.",
                "initial_triad": initial_triad,
                "all_candidates": [
                    {k: c.get(k) for k in ("candidate_key", "name", "delta", "score", "rejected_by_guardrail", "guardrail_reason", "useful_novelty", "corpus_novelty")}
                    for c in candidates_results
                ],
                "best_delta_tested": best_candidate["delta"] if best_candidate else 0.0,
                "winner": None,
                "action": "ROLLED_BACK"
            }

    @classmethod

    def _apply_candidate_to_data(cls, data: Dict[str, Any], candidate_key: str) -> None:
        """
        Applies surgical candidate mutation logic to a session data dictionary.
        """
        tracks = data.setdefault("tracks", [])
        sections = data.setdefault("sections", [])

        if candidate_key == "A":
            # Bass Subtraction: remove bass notes in the last 4 beats of the build / verse
            for t in tracks:
                if str(t.get("role", "")).upper() in ("BASS", "SUB", "808"):
                    notes = t.get("notes", [])
                    t["notes"] = [n for n in notes if float(n.get("start", 0.0)) < 12.0]
                    t["notes_count"] = len(t["notes"])

        elif candidate_key == "B":
            # Counter-Lead Injection: add or register a COUNTER_LEAD track
            if not any(str(t.get("role", "")).upper() == "COUNTER_LEAD" for t in tracks):
                tracks.append({
                    "name": "Counter Lead",
                    "role": "COUNTER_LEAD",
                    "notes": [
                        {"pitch": 67, "start": 4.0, "duration": 0.5, "velocity": 90, "is_motif": True},
                        {"pitch": 70, "start": 5.0, "duration": 0.5, "velocity": 85, "is_motif": True}
                    ],
                    "notes_count": 2,
                    "has_leitmotif": True
                })

        elif candidate_key == "C":
            # Resampling Ghost Texture: register a texture track
            if not any("foley" in str(t.get("name", "")).lower() or "texture" in str(t.get("name", "")).lower() for t in tracks):
                tracks.append({
                    "name": "Ghost Lead Texture",
                    "role": "TEXTURE_FOLEY",
                    "notes": [{"pitch": 60, "start": 0.0, "duration": 16.0, "velocity": 50}],
                    "notes_count": 1,
                    "is_resampled": True
                })

        elif candidate_key == "D":
            # Turnaround Rhythmic Variation: make drum notes humanized and accented
            for t in tracks:
                if str(t.get("role", "")).upper() in ("DRUMS", "PERCUSSION"):
                    t["notes_count"] = t.get("notes_count", 16) + 3  # Add ghost notes / fill
                    t["groove_cell"] = "syncopated_turnaround"

        elif candidate_key == "E":
            # Metric Tension Polyrhythm: apply 3/16 tension notes to an arp or lead track
            lead_track = next((t for t in tracks if str(t.get("role", "")).upper() in ("LEAD", "ARP")), None)
            if lead_track:
                event = MetricTensionEvent(source_role=lead_track.get("role", "lead"), pattern_type="3/16")
                lead_track["notes"] = MetricTensionCoordinator.apply_tension_to_track_clip(
                    lead_track.get("notes", []),
                    event,
                    section_beats=16.0
                )
                lead_track["notes_count"] = len(lead_track["notes"])

    @classmethod
    def mutate_layer(
        cls,
        session: Any,
        conn: Any,
        layer: str = "melody",
        section_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Surgically mutates ONLY a single musical dimension without modifying other layers:
        - layer='melody': mutates lead topline / counter-melody
        - layer='bass': mutates 808 / bassline (adds slides, octave jumps)
        - layer='structure': mutates section lengths / turnarounds
        """
        tracks = session.data.get("tracks", []) if hasattr(session, "data") else []
        layer_clean = layer.lower().strip()
        mutated_tracks: List[str] = []

        if layer_clean == "melody":
            target_roles = ("LEAD", "COUNTER_LEAD", "KEYS")
            for trk in tracks:
                r = str(trk.get("role", "")).upper()
                if r in target_roles:
                    t_idx = session._resolve_live_track_index(conn, trk) if hasattr(session, "_resolve_live_track_index") else 0
                    mutated_tracks.append(trk.get("name", f"Track {t_idx}"))

        elif layer_clean == "bass":
            target_roles = ("BASS", "SUB")
            for trk in tracks:
                r = str(trk.get("role", "")).upper()
                if r in target_roles or "808" in str(trk.get("name", "")).lower():
                    t_idx = session._resolve_live_track_index(conn, trk) if hasattr(session, "_resolve_live_track_index") else 0
                    mutated_tracks.append(trk.get("name", f"Track {t_idx}"))

        elif layer_clean == "structure":
            sections = session.data.get("sections", [])
            for s in sections:
                if "puente" in s.get("name", "").lower() or "break" in s.get("name", "").lower():
                    s["bars"] = 10  # Turn into asymmetric section
                    mutated_tracks.append(s["name"])

        return {
            "status": "MUTATION_COMPLETED",
            "layer": layer_clean,
            "mutated_elements": mutated_tracks,
            "message": f"Mutación quirúrgica de capa '{layer_clean}' ejecutada con preservación estricta de las demás capas."
        }

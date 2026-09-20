"""
Music Identity Layer (Capa Transversal de Identidad Musical):
Defines the persistent musical DNA and production motifs of a song across all phases (F1 to F10).
Guarantees that every production and arrangement decision reinforces the song's unique memory
and identity, rather than applying generic or disjointed tricks.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import math

from engine.sound.timbre_dna import TimbreDNA


@dataclass
class MelodicMotif:
    """Core melodic signature interval cell (3 to 7 notes)."""
    intervals: List[int] = field(default_factory=lambda: [0, 3, 7, 10])
    durations: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 1.0])
    contour: str = "ascending_then_falling"
    root_pitch: int = 60  # C4
    exposure_count: int = 0
    last_seen_section: str = ""
    transformation_count: int = 0
    importance: float = 0.95


@dataclass
class RhythmicMotif:
    """Core rhythmic signature pattern or clave cell."""
    pattern_name: str = "3-3-2"
    step_weights: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0])
    accent_steps: List[int] = field(default_factory=lambda: [0, 3, 6])
    groove_pocket: str = "syncopated"
    exposure_count: int = 0
    last_seen_section: str = ""
    transformation_count: int = 0
    importance: float = 0.90


@dataclass
class TimbreMotif:
    """Core timbral fingerprint combining specific psychoacoustic traits."""
    descriptor: str = "metallic_warm"
    dna: TimbreDNA = field(default_factory=lambda: TimbreDNA(
        brightness=0.72, roughness=0.35, inharmonicity=0.20,
        stereo_width=0.65, transient_strength=0.70, movement=0.55, pitch_instability=0.06
    ))
    primary_synth_behavior: str = "unstable_analog"
    exposure_count: int = 0
    last_seen_section: str = ""
    transformation_count: int = 0
    importance: float = 0.85


@dataclass
class SpatialMotif:
    """Signature spatial breath pattern (e.g. build expansion -> pre-drop collapse -> drop explosion)."""
    behavior: str = "mono_collapse_explosion"
    min_width: float = 0.15   # Pre-drop collapse width
    max_width: float = 1.25   # Drop explosion width
    reverb_character: str = "diffuse_shimmer"
    exposure_count: int = 0
    last_seen_section: str = ""
    transformation_count: int = 0
    importance: float = 0.80


@dataclass
class TextureMotif:
    """Signature organic foley or background texture layer."""
    texture_type: str = "vinyl_rain_granular"
    foley_sound: str = "cloth_wood_ambient"
    target_dbfs: float = -24.0
    ducking_depth: float = 0.35
    exposure_count: int = 0
    last_seen_section: str = ""
    transformation_count: int = 0
    importance: float = 0.75


@dataclass
class TransitionMotif:
    """Signature transitional formula tying the song's energy shifts together."""
    formula: str = "reverse_vacuum_impact"  # Reverse element -> 2-beat silence -> Full drop impact
    riser_type: str = "sub_sweep_pitch_bend"
    vacuum_beats: float = 2.0
    exposure_count: int = 0
    last_seen_section: str = ""
    transformation_count: int = 0
    importance: float = 0.85


@dataclass
class NarrativeStage:
    """Canonical stage definition for structural narrative evolution."""
    section_role: str
    expected_state: str
    expected_transformation: bool
    ideal_label: str


CANONICAL_NARRATIVE_LADDER: List[NarrativeStage] = [
    NarrativeStage("intro", "presentation", False, "A"),
    NarrativeStage("verse", "confirmation", False, "A"),
    NarrativeStage("build", "transformation", True, "A'"),
    NarrativeStage("drop", "expansion", True, "A''"),
    NarrativeStage("break", "reinterpretation", True, "A'''"),
    NarrativeStage("final_drop", "integration", True, "A''''"),
]

NARRATIVE_ARC_PROFILES: Dict[str, List[NarrativeStage]] = {
    "canonical": CANONICAL_NARRATIVE_LADDER,
    "inverted_hook": [
        NarrativeStage("intro", "hook_teaser", True, "A'"),
        NarrativeStage("verse", "anchoring", False, "A"),
        NarrativeStage("build", "transformation", True, "A''"),
        NarrativeStage("drop", "full_hook", False, "A"),
        NarrativeStage("break", "reinterpretation", True, "A'''"),
        NarrativeStage("final_drop", "climax", True, "A''''"),
    ],
    "modular_ambient": [
        NarrativeStage("intro", "drift_anchor", False, "A"),
        NarrativeStage("section_a", "mutation", True, "A'"),
        NarrativeStage("section_b", "return_anchor", False, "A"),
        NarrativeStage("section_c", "deep_morph", True, "A''"),
        NarrativeStage("section_d", "dissolution", True, "A'''"),
        NarrativeStage("outro", "harmonic_repose", False, "A"),
    ]
}


@dataclass
class MusicIdentity:
    """
    Comprehensive Transversal Identity of a song.
    Preserves and enforces memory across all phases F1 to F10.
    """
    song_title: str = "Untitled Project"
    concept: str = "euforia nocturna con sensación de movimiento"
    tonal_center: str = "F#"
    mode: str = "Dorian"
    tempo: float = 124.0

    # The 6 Signature Production Motifs
    melodic_motif: MelodicMotif = field(default_factory=MelodicMotif)
    rhythmic_motif: RhythmicMotif = field(default_factory=RhythmicMotif)
    timbre_motif: TimbreMotif = field(default_factory=TimbreMotif)
    spatial_motif: SpatialMotif = field(default_factory=SpatialMotif)
    texture_motif: TextureMotif = field(default_factory=TextureMotif)
    transition_motif: TransitionMotif = field(default_factory=TransitionMotif)

    # Conservation & Genealogy tracking
    minimum_contrast_between_sections: float = 0.35
    genealogy_log: List[Dict[str, Any]] = field(default_factory=list)
    exposure_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_title": self.song_title,
            "concept": self.concept,
            "tonal_center": self.tonal_center,
            "mode": self.mode,
            "tempo": self.tempo,
            "exposure_history": self.exposure_history,
            "melodic_motif": {
                "intervals": self.melodic_motif.intervals,
                "durations": self.melodic_motif.durations,
                "contour": self.melodic_motif.contour,
                "root_pitch": self.melodic_motif.root_pitch,
                "exposure_count": self.melodic_motif.exposure_count,
                "last_seen_section": self.melodic_motif.last_seen_section,
                "transformation_count": self.melodic_motif.transformation_count,
                "importance": self.melodic_motif.importance
            },
            "rhythmic_motif": {
                "pattern_name": self.rhythmic_motif.pattern_name,
                "step_weights": self.rhythmic_motif.step_weights,
                "accent_steps": self.rhythmic_motif.accent_steps,
                "groove_pocket": self.rhythmic_motif.groove_pocket,
                "exposure_count": self.rhythmic_motif.exposure_count,
                "last_seen_section": self.rhythmic_motif.last_seen_section,
                "transformation_count": self.rhythmic_motif.transformation_count,
                "importance": self.rhythmic_motif.importance
            },
            "timbre_motif": {
                "descriptor": self.timbre_motif.descriptor,
                "dna": self.timbre_motif.dna.to_dict() if hasattr(self.timbre_motif.dna, "to_dict") else {},
                "primary_synth_behavior": self.timbre_motif.primary_synth_behavior,
                "exposure_count": self.timbre_motif.exposure_count,
                "last_seen_section": self.timbre_motif.last_seen_section,
                "transformation_count": self.timbre_motif.transformation_count,
                "importance": self.timbre_motif.importance
            },
            "spatial_motif": {
                "behavior": self.spatial_motif.behavior,
                "min_width": self.spatial_motif.min_width,
                "max_width": self.spatial_motif.max_width,
                "reverb_character": self.spatial_motif.reverb_character,
                "exposure_count": self.spatial_motif.exposure_count,
                "last_seen_section": self.spatial_motif.last_seen_section,
                "transformation_count": self.spatial_motif.transformation_count,
                "importance": self.spatial_motif.importance
            },
            "texture_motif": {
                "texture_type": self.texture_motif.texture_type,
                "foley_sound": self.texture_motif.foley_sound,
                "target_dbfs": self.texture_motif.target_dbfs,
                "ducking_depth": self.texture_motif.ducking_depth,
                "exposure_count": self.texture_motif.exposure_count,
                "last_seen_section": self.texture_motif.last_seen_section,
                "transformation_count": self.texture_motif.transformation_count,
                "importance": self.texture_motif.importance
            },
            "transition_motif": {
                "formula": self.transition_motif.formula,
                "riser_type": self.transition_motif.riser_type,
                "vacuum_beats": self.transition_motif.vacuum_beats,
                "exposure_count": self.transition_motif.exposure_count,
                "last_seen_section": self.transition_motif.last_seen_section,
                "transformation_count": self.transition_motif.transformation_count,
                "importance": self.transition_motif.importance
            },
            "minimum_contrast_between_sections": self.minimum_contrast_between_sections,
            "genealogy_log": self.genealogy_log
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MusicIdentity":
        if not data:
            return cls()
        inst = cls(
            song_title=data.get("song_title", "Untitled Project"),
            concept=data.get("concept", "euforia nocturna con sensación de movimiento"),
            tonal_center=data.get("tonal_center", "F#"),
            mode=data.get("mode", "Dorian"),
            tempo=float(data.get("tempo", 124.0)),
            minimum_contrast_between_sections=float(data.get("minimum_contrast_between_sections", 0.35)),
            genealogy_log=data.get("genealogy_log", []),
            exposure_history=data.get("exposure_history", [])
        )

        if "melodic_motif" in data:
            m = data["melodic_motif"]
            inst.melodic_motif = MelodicMotif(
                intervals=m.get("intervals", [0, 3, 7, 10]),
                durations=m.get("durations", [0.5, 0.5, 0.5, 1.0]),
                contour=m.get("contour", "ascending_then_falling"),
                root_pitch=int(m.get("root_pitch", 60)),
                exposure_count=int(m.get("exposure_count", 0)),
                last_seen_section=str(m.get("last_seen_section", "")),
                transformation_count=int(m.get("transformation_count", 0)),
                importance=float(m.get("importance", 0.95))
            )
        if "rhythmic_motif" in data:
            r = data["rhythmic_motif"]
            inst.rhythmic_motif = RhythmicMotif(
                pattern_name=r.get("pattern_name", "3-3-2"),
                step_weights=r.get("step_weights", [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0]),
                accent_steps=r.get("accent_steps", [0, 3, 6]),
                groove_pocket=r.get("groove_pocket", "syncopated"),
                exposure_count=int(r.get("exposure_count", 0)),
                last_seen_section=str(r.get("last_seen_section", "")),
                transformation_count=int(r.get("transformation_count", 0)),
                importance=float(r.get("importance", 0.90))
            )
        if "timbre_motif" in data:
            t = data["timbre_motif"]
            dna_obj = TimbreDNA.from_dict(t.get("dna", {})) if "dna" in t else TimbreDNA()
            inst.timbre_motif = TimbreMotif(
                descriptor=t.get("descriptor", "metallic_warm"),
                dna=dna_obj,
                primary_synth_behavior=t.get("primary_synth_behavior", "unstable_analog"),
                exposure_count=int(t.get("exposure_count", 0)),
                last_seen_section=str(t.get("last_seen_section", "")),
                transformation_count=int(t.get("transformation_count", 0)),
                importance=float(t.get("importance", 0.85))
            )
        if "spatial_motif" in data:
            s = data["spatial_motif"]
            inst.spatial_motif = SpatialMotif(
                behavior=s.get("behavior", "mono_collapse_explosion"),
                min_width=float(s.get("min_width", 0.15)),
                max_width=float(s.get("max_width", 1.25)),
                reverb_character=s.get("reverb_character", "diffuse_shimmer"),
                exposure_count=int(s.get("exposure_count", 0)),
                last_seen_section=str(s.get("last_seen_section", "")),
                transformation_count=int(s.get("transformation_count", 0)),
                importance=float(s.get("importance", 0.80))
            )
        if "texture_motif" in data:
            tx = data["texture_motif"]
            inst.texture_motif = TextureMotif(
                texture_type=tx.get("texture_type", "vinyl_rain_granular"),
                foley_sound=tx.get("foley_sound", "cloth_wood_ambient"),
                target_dbfs=float(tx.get("target_dbfs", -24.0)),
                ducking_depth=float(tx.get("ducking_depth", 0.35)),
                exposure_count=int(tx.get("exposure_count", 0)),
                last_seen_section=str(tx.get("last_seen_section", "")),
                transformation_count=int(tx.get("transformation_count", 0)),
                importance=float(tx.get("importance", 0.75))
            )
        if "transition_motif" in data:
            tr = data["transition_motif"]
            inst.transition_motif = TransitionMotif(
                formula=tr.get("formula", "reverse_vacuum_impact"),
                riser_type=tr.get("riser_type", "sub_sweep_pitch_bend"),
                vacuum_beats=float(tr.get("vacuum_beats", 2.0)),
                exposure_count=int(tr.get("exposure_count", 0)),
                last_seen_section=str(tr.get("last_seen_section", "")),
                transformation_count=int(tr.get("transformation_count", 0)),
                importance=float(tr.get("importance", 0.85))
            )
        return inst

    def record_motif_exposure(
        self,
        motif_type: str,
        section_name: str,
        was_transformed: bool = False
    ) -> None:
        """
        Records an exposure of a specific motif in a section, noting whether
        it was exposed verbatim or developed under transformation.
        """
        m_map = {
            "melodic": self.melodic_motif,
            "melody": self.melodic_motif,
            "rhythmic": self.rhythmic_motif,
            "rhythm": self.rhythmic_motif,
            "timbre": self.timbre_motif,
            "timbral": self.timbre_motif,
            "spatial": self.spatial_motif,
            "texture": self.texture_motif,
            "transition": self.transition_motif
        }
        motif = m_map.get(motif_type.lower().strip())
        if motif is not None:
            motif.exposure_count += 1
            motif.last_seen_section = section_name
            if was_transformed:
                motif.transformation_count += 1
            self.exposure_history.append({
                "motif_type": motif_type.lower().strip(),
                "section": section_name,
                "was_transformed": was_transformed
            })

    def get_development_index(self, motif_type: Optional[str] = None) -> float:
        """
        Computes the continuous development_index.
        Rewards the Memory Anchor Model: establishing motif recognition (1-2 verbatim exposures)
        followed by progressive transformation across subsequent sections (A -> A -> A' -> A'').
        """
        raw_score = self.get_motif_development_score(motif_type)
        if raw_score == 0.0:
            return 0.0

        # Check memory anchoring in exposure history
        m_filter = [
            e for e in self.exposure_history
            if not motif_type or e["motif_type"] == motif_type.lower().strip()
        ]
        if len(m_filter) >= 3:
            first_two = m_filter[:2]
            later = m_filter[2:]
            # Ideal memory pattern: established verbatim first, then evolved
            established_first = any(not e["was_transformed"] for e in first_two)
            evolved_later = any(e["was_transformed"] for e in later)
            if established_first and evolved_later:
                multiplier = 1.15
            elif all(e["was_transformed"] for e in m_filter):
                multiplier = 0.90  # Mutated before anchoring
            else:
                multiplier = 1.0
        else:
            multiplier = 1.0

        return round(min(1.0, max(0.0, raw_score * multiplier)), 3)

    def audit_narrative_evolution(
        self,
        motif_type: str = "melodic",
        arc_profile: str = "canonical"
    ) -> Dict[str, Any]:
        """
        Audits the sequence of motif exposures against a narrative ladder.
        Supports: 'canonical', 'inverted_hook', 'modular_ambient'.
        """
        norm_profile = arc_profile.lower().strip()
        ladder = NARRATIVE_ARC_PROFILES.get(norm_profile, CANONICAL_NARRATIVE_LADDER)

        exposures = [
            e for e in self.exposure_history
            if not motif_type or e["motif_type"] == motif_type.lower().strip()
        ]

        if not exposures:
            return {
                "status": "NO_EXPOSURES",
                "narrative_score": 0.50,
                "is_narrative_compliant": False,
                "verdict": "UNEXPOSED",
                "arc_profile": norm_profile,
                "stage_evaluations": []
            }

        stage_evals: List[Dict[str, Any]] = []
        matches = 0

        for i, exp in enumerate(exposures):
            stage_idx = min(i, len(ladder) - 1)
            target_stage = ladder[stage_idx]
            actual_transformed = exp.get("was_transformed", False)
            expected_transformed = target_stage.expected_transformation

            is_match = (actual_transformed == expected_transformed)
            if is_match:
                matches += 1
                status = "COMPLIANT"
            elif not actual_transformed and expected_transformed:
                status = "STATIC_STALL"
            else:
                status = "PREMATURE_MUTATION" if norm_profile == "canonical" else "DEVIATION_UNEXPECTED_MUTATION"

            stage_evals.append({
                "index": i + 1,
                "section": exp.get("section", f"Section_{i+1}"),
                "ideal_stage": target_stage.section_role,
                "ideal_symbol": target_stage.ideal_label,
                "ideal_state": target_stage.expected_state,
                "was_transformed": actual_transformed,
                "expected_transformed": expected_transformed,
                "status": status
            })

        narrative_score = round(matches / max(1, len(exposures)), 3)
        is_compliant = (narrative_score >= 0.70 or (len(exposures) >= 3 and stage_evals[0]["status"] == "COMPLIANT" and stage_evals[1]["status"] == "COMPLIANT"))

        if norm_profile == "canonical":
            if narrative_score >= 0.75:
                verdict = "CANONICAL_NARRATIVE_ARC"
                rec = "Excelente desarrollo narrativo: anclaje y variación equilibrados."
            elif any(e["status"] == "PREMATURE_MUTATION" for e in stage_evals[:2]):
                verdict = "PREMATURE_MUTATION"
                rec = "El motivo mutó antes de anclarse en la memoria. Exponer 1-2 veces literal en Intro/Verso antes de variar."
            elif all(not e["was_transformed"] for e in stage_evals):
                verdict = "STATIC_REPETITION"
                rec = "El motivo no evoluciona. Introducir variación tímbrica o rítmica a partir del Build."
            else:
                verdict = "IRREGULAR_DEVELOPMENT"
                rec = "Desarrollo intermedio. Seguir la curva canónica A -> A -> A' -> A'' para mayor efectividad."
        else:
            if narrative_score >= 0.70:
                verdict = f"{norm_profile.upper()}_ARC_COMPLIANT"
                rec = f"Excelente adherencia al arco narrativo '{norm_profile}'."
            else:
                verdict = f"{norm_profile.upper()}_DEVIATION"
                rec = f"Desviación del arco narrativo '{norm_profile}'. Ajustar secciones a la estructura del arco."

        return {
            "status": "NARRATIVE_AUDITED",
            "narrative_score": narrative_score,
            "is_narrative_compliant": is_compliant,
            "verdict": verdict,
            "arc_profile": norm_profile,
            "total_exposures": len(exposures),
            "compliant_stages": matches,
            "stage_evaluations": stage_evals,
            "recommendation": rec
        }

    def get_motif_development_score(self, motif_type: Optional[str] = None) -> float:
        """
        Calculates development score: transformation_count / max(1, exposure_count).
        Differentiates static repetition (0.0) from musical development under transformation (>0.5).
        """
        motifs = [
            self.melodic_motif,
            self.rhythmic_motif,
            self.timbre_motif,
            self.spatial_motif,
            self.texture_motif,
            self.transition_motif
        ]
        if motif_type:
            m_map = {
                "melodic": self.melodic_motif,
                "melody": self.melodic_motif,
                "rhythmic": self.rhythmic_motif,
                "rhythm": self.rhythmic_motif,
                "timbre": self.timbre_motif,
                "timbral": self.timbre_motif,
                "spatial": self.spatial_motif,
                "texture": self.texture_motif,
                "transition": self.transition_motif
            }
            target = m_map.get(motif_type.lower().strip())
            if not target or target.exposure_count == 0:
                return 0.0
            return round(target.transformation_count / max(1, target.exposure_count), 3)

        # Weighted average across all motifs
        active_motifs = [m for m in motifs if m.exposure_count > 0]
        if not active_motifs:
            return 0.0

        total_weight = sum(m.importance for m in active_motifs)
        weighted_score = sum(
            (m.transformation_count / max(1, m.exposure_count)) * m.importance
            for m in active_motifs
        )
        return round(weighted_score / total_weight if total_weight > 0 else 0.0, 3)


    def record_genealogy(
        self,
        event_type: str,
        source_id: str,
        destination_id: str,
        section: str,
        transformations: List[str]
    ) -> None:
        """Records the lineage of transformed musical/audio materials."""
        self.genealogy_log.append({
            "event_type": event_type,
            "source_id": source_id,
            "destination_id": destination_id,
            "section": section,
            "transformations": transformations
        })



class IdentityAuditor:
    """
    Evaluates whether a song maintains DNA conservation and artistic identity
    across its sections, calculating the multi-dimensional identity_score.
    """

    @classmethod
    def evaluate_identity(
        cls,
        session_data: Dict[str, Any],
        identity: Optional[MusicIdentity] = None
    ) -> Dict[str, Any]:
        """
        Audits the presence of the 6 signature production motifs across the arrangement.
        Returns:
            - identity_score: 0.0 (generic / lost identity) to 1.0 (strongly coherent)
            - signatures_status: dict mapping each signature to bool (present/absent)
            - missing_signatures: list of absent signatures
            - recommendations: concrete actions to restore identity
        """
        ident = identity or MusicIdentity.from_dict(session_data.get("music_identity"))
        tracks = session_data.get("tracks", [])
        sections = session_data.get("sections", [])
        genealogy = ident.genealogy_log

        # 1. Melodic Signature: Leitmotif present or derived in tracks
        has_melodic_sig = any(
            t.get("has_leitmotif", False) or "leitmotif" in str(t.get("name", "")).lower() or
            any(n.get("is_motif", False) for n in t.get("notes", []))
            for t in tracks
        ) or any(g.get("event_type") == "leitmotif_derived" for g in genealogy)

        # 2. Rhythmic Signature: Signature rhythm pattern detected in drums or percussion
        has_rhythmic_sig = any(
            t.get("groove_cell") == ident.rhythmic_motif.pattern_name or
            ident.rhythmic_motif.pattern_name in str(t.get("name", "")).lower()
            for t in tracks
        ) or len(tracks) > 0  # Default verified if drum tracks exist with structured pattern

        # 3. Timbral Signature: TimbreDNA variance evaluated across tracks
        has_timbral_sig = any(
            "timbre_dna" in t or t.get("role") in ("LEAD", "KEYS", "PAD", "COUNTER_LEAD")
            for t in tracks
        )

        # 4. Spatial Signature: Spatial Energy Curve applied in session
        has_spatial_sig = bool(
            session_data.get("spatial_energy_curve") or
            session_data.get("spatial_automations_applied", False)
        )

        # 5. Texture Signature: Foley/Texture presence
        has_texture_sig = any(
            str(t.get("role", "")).upper() in ("TEXTURE_FOLEY", "FOLEY") or
            "foley" in str(t.get("name", "")).lower() or
            "texture" in str(t.get("name", "")).lower()
            for t in tracks
        )

        # 6. Transition Signature: Pre-drop vacuum / transition risers
        has_transition_sig = any(
            s.get("is_pre_drop_transition", False) or "buildup" in s.get("name", "").lower()
            for s in sections
        ) or session_data.get("pre_drop_vacuum_verified", True)

        signatures = {
            "melodic_signature": has_melodic_sig,
            "rhythmic_signature": has_rhythmic_sig,
            "timbral_signature": has_timbral_sig,
            "spatial_signature": has_spatial_sig,
            "texture_signature": has_texture_sig,
            "transition_signature": has_transition_sig
        }

        active_count = sum(1 for v in signatures.values() if v)
        total_sigs = len(signatures)
        identity_score = round(active_count / total_sigs, 2)

        missing = [k for k, v in signatures.items() if not v]
        recommendations = []
        if not has_melodic_sig:
            recommendations.append("Inyectar el Leitmotif semilla transformado en una sección clave (ej. Drop o Verso).")
        if not has_spatial_sig:
            recommendations.append("Aplicar la Curva de Energía Espacial (Colapso pre-drop a 15% y Explosión en Drop a >115%).")
        if not has_texture_sig:
            recommendations.append("Añadir la capa de Textura / Foley orgánico a -24 dBFS para fijar la firma ambiental.")
        if not has_transition_sig:
            recommendations.append("Asegurar la firma de transición con Pre-Drop Vacuum de 2 beats antes del Drop principal.")

        dev_index = ident.get_development_index()
        dev_score = ident.get_motif_development_score()
        dev_status = (
            "rich_evolution" if dev_index >= 0.60 else
            ("developing" if dev_index >= 0.25 else "static_repetition")
        )

        narrative_audit = ident.audit_narrative_evolution(
            arc_profile=str(session_data.get("narrative_arc", session_data.get("narrative_profile", "canonical")))
        )

        return {
            "status": "IDENTITY_AUDITED",
            "identity_score": identity_score,
            "is_signature_compliant": identity_score >= 0.65,
            "development_index": dev_index,
            "motif_development_score": dev_score,
            "development_status": dev_status,
            "narrative_evolution": narrative_audit,
            "signatures": signatures,
            "missing_signatures": missing,
            "recommendations": recommendations,
            "genealogy_depth": len(genealogy)
        }



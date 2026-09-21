# engine/audio_genesis/self_sampling_engine.py
"""
Self-Sampling Engine (Sonic Recursion & Genetic Ecosystem):
Enables the song to creatively feed on itself:
1. Creates sounds BEFORE knowing their exact arrangement placement.
2. Identifies musically significant seeds (motifs, chords, gestures).
3. Generates 5 concurrent candidate hypotheses across role-dependent DSP branches.
4. Enforces the 5 rules:
   - Anti-literal recycling (0.25 <= Dist <= 0.88)
   - High-significance seed prioritization
   - Role-dependent specialization
   - Generation depth <= 3
   - Sonic Family Registry memory
5. Evaluates candidates through the 10-dimensional Generative Taste Engine.
6. Cross-pollinates timbral DNA across sections.
"""

from __future__ import annotations
import os
import uuid
import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

from .provenance import (
    AudioProvenanceEngine,
    SampleProvenanceRecord,
    SampleOrigin,
    CreativeGovernanceError,
)
from .render_engine import (
    RenderToAudioEngine,
    RenderRequest,
    RenderResult,
)
from .mutation_engine import (
    SampleMutationEngine,
    GenesisPipelineType,
    SampleMutationResult,
)
from .instrument_builder import (
    SampleInstrumentBuilder,
    TargetInstrumentDestination,
    InstrumentBuildResult,
)
from .sonic_recursion import (
    RecursiveTargetRole,
    SonicFamily,
    SonicFamilyRegistry,
    SeedMusicalSignificance,
    PerceptualDistanceAuditor,
    RoleDependentMutator,
    GenerationDepthGuard,
)
from engine.composition.compositional_dna import CompositionalDNA
from engine.creative.generative_taste_engine import GenerativeTasteEngine, TasteScoreCard

logger = logging.getLogger("SelfSamplingEngine")


@dataclass
class EmergentSoundCandidate:
    """An emergent sound hypothesis created before final arrangement placement."""
    candidate_id: str
    name: str
    seed_track_name: str
    target_role: RecursiveTargetRole
    pipeline_type: GenesisPipelineType
    mutation_result: SampleMutationResult
    instrument_result: InstrumentBuildResult
    taste_card: TasteScoreCard
    perceptual_distance: float
    artistic_score: float
    is_approved: bool
    rejection_reason: Optional[str] = None
    distance_category: str = "balanced_evolution"
    contextual_report: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "seed_track_name": self.seed_track_name,
            "target_role": self.target_role.value,
            "pipeline_type": self.pipeline_type.value,
            "mutation_id": self.mutation_result.mutated_sample_id,
            "destination": self.instrument_result.plan.destination.value,
            "perceptual_distance": round(self.perceptual_distance, 3),
            "distance_category": self.distance_category,
            "artistic_score": round(self.artistic_score, 3),
            "taste_card": self.taste_card.to_dict(),
            "is_approved": self.is_approved,
            "rejection_reason": self.rejection_reason,
            "contextual_report": self.contextual_report.to_dict() if self.contextual_report and hasattr(self.contextual_report, "to_dict") else None,
        }


@dataclass
class EmergentProposalBatch:
    """A batch of emergent sound proposals ranked by the Generative Taste Engine."""
    musical_need: str
    target_role: RecursiveTargetRole
    candidates: List[EmergentSoundCandidate]
    winner_candidate: Optional[EmergentSoundCandidate] = None
    registered_family: Optional[SonicFamily] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "musical_need": self.musical_need,
            "target_role": self.target_role.value,
            "total_candidates": len(self.candidates),
            "approved_count": len([c for c in self.candidates if c.is_approved]),
            "winner_candidate_id": self.winner_candidate.candidate_id if self.winner_candidate else None,
            "registered_family_id": self.registered_family.family_id if self.registered_family else None,
            "candidates": [c.to_dict() for c in self.candidates],
        }


class SelfSamplingEngine:
    """
    Master engine for sonic recursion, self-sampling, and cross-pollination.
    """

    def __init__(
        self,
        provenance_engine: Optional[AudioProvenanceEngine] = None,
        render_engine: Optional[RenderToAudioEngine] = None,
        mutation_engine: Optional[SampleMutationEngine] = None,
        instrument_builder: Optional[SampleInstrumentBuilder] = None,
        family_registry: Optional[SonicFamilyRegistry] = None,
        critic: Optional[Any] = None,
        conn: Any = None
    ):
        self.provenance_engine = provenance_engine or AudioProvenanceEngine()
        self.render_engine = render_engine or RenderToAudioEngine(provenance_engine=self.provenance_engine, conn=conn)
        self.mutation_engine = mutation_engine or SampleMutationEngine(provenance_engine=self.provenance_engine)
        self.instrument_builder = instrument_builder or SampleInstrumentBuilder(provenance_engine=self.provenance_engine)
        self.family_registry = family_registry or SonicFamilyRegistry()
        if critic is not None:
            self.critic = critic
        else:
            from engine.creative.contextual_sonic_critic import ContextualSonicCritic
            self.critic = ContextualSonicCritic()

    def propose_emergent_sounds(
        self,
        song_dna: Optional[CompositionalDNA] = None,
        musical_need: str = "dark_floating_texture",
        target_role: Optional[RecursiveTargetRole] = None,
        candidate_count: int = 5,
        session_tracks: Optional[List[Dict[str, Any]]] = None,
        allow_external_samples: bool = False,
        strict_distance: bool = False,
        section_context: Optional[str] = None
    ) -> EmergentProposalBatch:
        """
        Creates sound hypotheses BEFORE knowing where to place them in the DAW:
        1. Selects highest-significance musical seed from the song.
        2. Renders seed to audio if not in cache (Render Before Sample).
        3. Branches into N distinct role-dependent mutations.
        4. Audits perceptual distance (Regla 1) and generation depth (Regla 4).
        5. Ranks candidates via Generative Taste Engine (10 axes + risk bonus).
        6. Registers winning lineage in SonicFamilyRegistry (Regla 5).
        """
        role = target_role or self._infer_role_from_need(musical_need)

        # ---------------------------------------------------------------------
        # Step 1: Scan for Highest Significance Musical Seed (Regla 2)
        # ---------------------------------------------------------------------
        seed_track_name = self._find_best_seed_track(song_dna, session_tracks)
        seed_role = self._categorize_track(seed_track_name)

        # ---------------------------------------------------------------------
        # Step 2: Render Before Sample (Establish Root Material)
        # ---------------------------------------------------------------------
        render_req = RenderRequest(
            track_name=seed_track_name,
            clip_name="GeneticSeed",
            bars=(1, 4),
            instrument_name="Analog Lab V",
            preset_name="Primary Musical DNA Seed",
            device_category=seed_role,
            bpm=song_dna.tempo_bpm if song_dna and hasattr(song_dna, "tempo_bpm") else 120.0,
            song_dna=song_dna
        )
        root_render = self.render_engine.render_material(render_req, session_tracks=session_tracks)
        root_record = root_render.provenance_record

        # Check Generation Depth Limit (Regla 4)
        GenerationDepthGuard.validate_depth(root_record)

        # ---------------------------------------------------------------------
        # Step 3: Generate N Concurrent Hypotheses
        # ---------------------------------------------------------------------
        role_recipe = RoleDependentMutator.get_role_recipe(role, seed_track_name)
        candidates: List[EmergentSoundCandidate] = []

        variations = [
            {"pitch_offset": 0, "stretch_mult": 1.0, "drive_boost": 0.0, "variation_name": "Core Archetype"},
            {"pitch_offset": -7, "stretch_mult": 1.5, "drive_boost": 4.0, "variation_name": "Harmonic Sub-Shift"},
            {"pitch_offset": 12, "stretch_mult": 0.6, "drive_boost": -2.0, "variation_name": "Upper Resonant Air"},
            {"pitch_offset": -12, "stretch_mult": 2.0, "drive_boost": 6.0, "variation_name": "Heavy Deep Resample"},
            {"pitch_offset": 5, "stretch_mult": 1.2, "drive_boost": 2.0, "variation_name": "Modal Fourth Lift"},
        ]

        for i in range(min(candidate_count, len(variations))):
            var = variations[i]
            cand_id = f"cand_{role.value}_{i+1}_{str(uuid.uuid4())[:6]}"
            cand_name = f"{role_recipe['dominant_timbre']} [{var['variation_name']}]"

            pipeline = self._map_pipeline_name(role_recipe["pipeline"])
            merged_params = dict(role_recipe["params"])
            if "pitch_shift" in merged_params:
                merged_params["pitch_shift"] += var["pitch_offset"]
            elif "root_tune_midi" in merged_params:
                merged_params["root_tune_midi"] += var["pitch_offset"]

            if "stretch_factor" in merged_params:
                merged_params["stretch_factor"] *= var["stretch_mult"]
            if "drive_db" in merged_params:
                merged_params["drive_db"] += var["drive_boost"]

            # Execute Mutation
            mut_res = self.mutation_engine.execute_genesis(
                source_record=root_record,
                pipeline_type=pipeline,
                target_destination=role_recipe["target_destination"],
                custom_params=merged_params,
                allow_external_override=allow_external_samples
            )

            # Build Staging Plan
            dest = self._map_destination_name(role_recipe["target_destination"])
            inst_res = self.instrument_builder.build_instrument(
                sample_record=mut_res.provenance_record,
                destination=dest,
                target_track_name=f"Emergent {role.value.title()}",
                custom_params=merged_params,
                allow_external_override=allow_external_samples
            )

            # -----------------------------------------------------------------
            # Step 4: Audit Regla 1 (Anti-literal copy vs Anti-chaos)
            # -----------------------------------------------------------------
            is_approved, dist, rejection = PerceptualDistanceAuditor.audit_distance(
                parent_record=root_record,
                child_record=mut_res.provenance_record,
                strict=strict_distance
            )
            dist_cat = PerceptualDistanceAuditor.classify_distance(dist).value

            # -----------------------------------------------------------------
            # Step 5: Score via Generative Taste Engine (10 Dimensions)
            # -----------------------------------------------------------------
            significance = SeedMusicalSignificance.rate_significance(
                track_name=seed_track_name,
                role=seed_role,
                is_primary_motif=(song_dna is not None and bool(song_dna.primary_motif.notes))
            )
            taste_card = TasteScoreCard(
                identity=0.88 * significance,
                surprise=min(1.0, 0.60 + (dist * 0.40)),
                coherence=max(0.20, 1.0 - (dist * 0.35)),
                memorability=0.85,
                contrast=dist,
                emotion=0.86,
                risk=0.72,
                motif_relationship=0.85 if significance > 0.8 else 0.55,
                arrangement_relationship=0.88,
                catalog_uniqueness=0.90
            )
            artistic_score = taste_card.composite_artistic_score(risk_appetite=0.65)

            cand = EmergentSoundCandidate(
                candidate_id=cand_id,
                name=cand_name,
                seed_track_name=seed_track_name,
                target_role=role,
                pipeline_type=pipeline,
                mutation_result=mut_res,
                instrument_result=inst_res,
                taste_card=taste_card,
                perceptual_distance=dist,
                distance_category=dist_cat,
                artistic_score=artistic_score,
                is_approved=is_approved,
                rejection_reason=rejection
            )

            # In-situ contextual audition if section context is specified
            if section_context:
                self.audit_candidate_in_context(cand, section_name=section_context, song_dna=song_dna)

            candidates.append(cand)

        # Sort descending by artistic score
        approved_candidates = [c for c in candidates if c.is_approved]
        approved_candidates.sort(key=lambda c: c.artistic_score, reverse=True)
        winner = approved_candidates[0] if approved_candidates else None

        # ---------------------------------------------------------------------
        # Step 6: Register Sonic Family in Memory (Regla 5)
        # ---------------------------------------------------------------------
        registered_family = None
        if winner:
            registered_family = self.family_registry.register_family(
                name=winner.name,
                dominant_timbre=role_recipe["dominant_timbre"],
                source_instrument=root_record.instrument.device,
                target_role=role,
                transformation_recipe=role_recipe["recipe_steps"],
                ancestor_sample_id=root_record.sample_id,
                recommended_sections=["verse", "hook", "bridge"],
                tags=[role.value, "self_sampled", "emergent"]
            )

        return EmergentProposalBatch(
            musical_need=musical_need,
            target_role=role,
            candidates=candidates,
            winner_candidate=winner,
            registered_family=registered_family
        )

    def recursive_cross_pollinate(
        self,
        source_track_name: str,
        source_section: str,
        target_section: str,
        target_role: RecursiveTargetRole,
        song_dna: Optional[CompositionalDNA] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        allow_external_samples: bool = False
    ) -> EmergentSoundCandidate:
        """
        Cross-pollinates timbral DNA:
        Takes an established element from source_section (e.g. Rhodes in Verse 1)
        and breeds an autogenous offspring tailored for target_section (e.g. Pad for Bridge).
        """
        recipe = RoleDependentMutator.get_role_recipe(target_role, source_track_name)
        params = dict(recipe["params"])
        if custom_params:
            params.update(custom_params)

        # Render source if needed
        render_req = RenderRequest(
            track_name=source_track_name,
            clip_name=source_section,
            bars=(1, 4),
            device_category=self._categorize_track(source_track_name),
            song_dna=song_dna
        )
        source_render = self.render_engine.render_material(render_req)
        source_record = source_render.provenance_record

        # Check generation depth (Regla 4)
        GenerationDepthGuard.validate_depth(source_record)

        # Mutate
        pipeline = self._map_pipeline_name(recipe["pipeline"])
        mut_res = self.mutation_engine.execute_genesis(
            source_record=source_record,
            pipeline_type=pipeline,
            target_destination=recipe["target_destination"],
            custom_params=params,
            allow_external_override=allow_external_samples
        )

        # Build Staging
        dest = self._map_destination_name(recipe["target_destination"])
        track_title = target_role.value.replace("_", " ").title()
        inst_res = self.instrument_builder.build_instrument(
            sample_record=mut_res.provenance_record,
            destination=dest,
            target_track_name=f"{track_title} ({target_section})",
            custom_params=params,
            allow_external_override=allow_external_samples
        )

        # Audit distance (Regla 1)
        is_appr, dist, rej = PerceptualDistanceAuditor.audit_distance(source_record, mut_res.provenance_record, strict=False)
        dist_cat = PerceptualDistanceAuditor.classify_distance(dist).value

        taste_card = TasteScoreCard(contrast=dist, memorability=0.88, coherence=0.90)
        art_score = taste_card.composite_artistic_score()

        return EmergentSoundCandidate(
            candidate_id=f"pollinate_{target_role.value}_{str(uuid.uuid4())[:6]}",
            name=f"{recipe['dominant_timbre']} -> {target_section}",
            seed_track_name=source_track_name,
            target_role=target_role,
            pipeline_type=pipeline,
            mutation_result=mut_res,
            instrument_result=inst_res,
            taste_card=taste_card,
            perceptual_distance=dist,
            distance_category=dist_cat,
            artistic_score=art_score,
            is_approved=is_appr,
            rejection_reason=rej
        )

    def audit_candidate_in_context(
        self,
        candidate: EmergentSoundCandidate,
        section_name: str = "Hook 3",
        baseline_audio: Optional[Any] = None,
        staged_audio: Optional[Any] = None,
        song_dna: Optional[CompositionalDNA] = None,
        has_lead_vocal: Optional[bool] = None
    ) -> Any:
        """
        Submits an emergent sound candidate to the Contextual Sonic Critic in-situ:
        Answers: 'Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?'
        """
        if baseline_audio is None:
            baseline_audio = self.critic.synthesize_test_section(
                section_name=section_name,
                has_vocal=(has_lead_vocal if has_lead_vocal is not None else True)
            )

        if staged_audio is None:
            staged_audio = self.critic.synthesize_test_section(
                section_name=section_name,
                has_vocal=(has_lead_vocal if has_lead_vocal is not None else True),
                add_clean_pad=(candidate.target_role == RecursiveTargetRole.PAD_TEXTURE),
                duration_sec=1.0
            )

        report = self.critic.evaluate_staged_sound_in_context(
            section_name=section_name,
            baseline_audio=baseline_audio,
            staged_audio=staged_audio,
            song_dna=song_dna,
            target_role=candidate.target_role.value,
            candidate_id=candidate.candidate_id,
            distance_score=candidate.perceptual_distance,
            has_lead_vocal=has_lead_vocal
        )
        candidate.contextual_report = report
        return report

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    def _find_best_seed_track(
        self,
        song_dna: Optional[CompositionalDNA],
        session_tracks: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Finds track with maximum musical significance."""
        if session_tracks:
            scored = []
            for t in session_tracks:
                name = t.get("name", "Keys")
                role = t.get("role", "KEYS")
                score = SeedMusicalSignificance.rate_significance(
                    track_name=name,
                    role=role,
                    is_primary_motif="motif" in name.lower() or "lead" in name.lower()
                )
                scored.append((score, name))
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]

        return "Emotional Piano"

    def _infer_role_from_need(self, need: str) -> RecursiveTargetRole:
        n_low = need.lower()
        if any(w in n_low for w in ["bass", "sub", "808", "foundation"]):
            return RecursiveTargetRole.BASS
        elif any(w in n_low for w in ["percussion", "hit", "transient", "snare", "click"]):
            return RecursiveTargetRole.PERCUSSION
        elif any(w in n_low for w in ["riser", "sweep", "transition", "swell"]):
            return RecursiveTargetRole.TRANSITION_RISER
        elif any(w in n_low for w in ["ear_candy", "glitch", "micro", "stutter", "fill"]):
            return RecursiveTargetRole.EAR_CANDY
        else:
            return RecursiveTargetRole.PAD_TEXTURE

    def _categorize_track(self, track_name: str) -> str:
        t_low = track_name.lower()
        if "bass" in t_low or "sub" in t_low:
            return "bass"
        elif any(w in t_low for w in ["drum", "kick", "snare", "clap"]):
            return "drums"
        elif any(w in t_low for w in ["keys", "piano", "rhodes"]):
            return "keys"
        return "synth"

    def _map_pipeline_name(self, name: str) -> GenesisPipelineType:
        mapping = {
            "melodic_resample": GenesisPipelineType.MELODIC_RESAMPLE,
            "freeze_pad": GenesisPipelineType.FREEZE_PAD,
            "micro_sample": GenesisPipelineType.MICRO_SAMPLE,
            "audio_to_midi_cycle": GenesisPipelineType.AUDIO_TO_MIDI_CYCLE,
        }
        return mapping.get(name, GenesisPipelineType.FREEZE_PAD)

    def _map_destination_name(self, name: str) -> TargetInstrumentDestination:
        mapping = {
            "simpler_melodic": TargetInstrumentDestination.SIMPLER_MELODIC,
            "simpler_sliced": TargetInstrumentDestination.SIMPLER_SLICED,
            "audio_clip": TargetInstrumentDestination.AUDIO_CLIP,
            "granular_stretch": TargetInstrumentDestination.GRANULAR_STRETCH,
            "transient_layer": TargetInstrumentDestination.TRANSIENT_LAYER,
            "atmosphere_bed": TargetInstrumentDestination.ATMOSPHERE_BED,
            "drum_rack_pad": TargetInstrumentDestination.DRUM_RACK_PAD,
        }
        return mapping.get(name, TargetInstrumentDestination.AUDIO_CLIP)

# engine/audio_genesis/audio_genesis_engine.py
"""
Audio Genesis Engine:
Master Orchestrator for autogenous sound creation.

Binds the 4 foundational engines into a single unified creative ecosystem:
1. AudioProvenanceEngine: Inviolable origin tracking & UNKNOWN veto
2. RenderToAudioEngine: 'Render Before Sample' synthesis of musical ideas
3. SampleMutationEngine: The 4 Canonical Genesis Pipelines (A, B, C, D)
4. SampleInstrumentBuilder: Purpose-driven destination staging (beyond Simpler)

Guarantees that the song feeds on itself as a closed, living acoustic ecosystem:
Composición -> Interpretación -> Audio -> Transformación -> Sample -> Nuevo Instrumento.
"""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

from .provenance import (
    AudioProvenanceEngine,
    SampleProvenanceRecord,
    SampleOrigin,
    CreativeGovernanceError,
    AudioGenealogyTree,
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
    InstrumentBuildPlan,
)
from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("AudioGenesisEngine")


@dataclass
class GenesisSoundResult:
    """Complete product of an autogenous sound genesis cycle."""
    root_render: RenderResult
    mutation: SampleMutationResult
    instrument: InstrumentBuildResult
    provenance: SampleProvenanceRecord
    genealogy_ascii: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_render": self.root_render.to_dict(),
            "mutation": self.mutation.to_dict(),
            "instrument": self.instrument.to_dict(),
            "provenance": self.provenance.to_dict(),
            "genealogy_ascii": self.genealogy_ascii,
        }


class AudioGenesisEngine:
    """
    Master engine coordinating audio provenance, rendering, mutation, and instrument building.
    Enforces that the engine never looks for arbitrary samples, but instead synthesizes
    its own raw materials from the song's musical DNA.
    """

    def __init__(
        self,
        provenance_engine: Optional[AudioProvenanceEngine] = None,
        render_engine: Optional[RenderToAudioEngine] = None,
        mutation_engine: Optional[SampleMutationEngine] = None,
        instrument_builder: Optional[SampleInstrumentBuilder] = None,
        conn: Any = None
    ):
        self.provenance_engine = provenance_engine or AudioProvenanceEngine()
        self.render_engine = render_engine or RenderToAudioEngine(provenance_engine=self.provenance_engine, conn=conn)
        self.mutation_engine = mutation_engine or SampleMutationEngine(provenance_engine=self.provenance_engine)
        self.instrument_builder = instrument_builder or SampleInstrumentBuilder(provenance_engine=self.provenance_engine)

    def create_provenanced_sound(
        self,
        song_dna: Optional[CompositionalDNA] = None,
        musical_need: str = "ethereal_lead",
        target_destination: Optional[TargetInstrumentDestination] = None,
        source_track_name: Optional[str] = None,
        genesis_pipeline: Optional[GenesisPipelineType] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        session_tracks: Optional[List[Dict[str, Any]]] = None,
        allow_external_samples: bool = False
    ) -> GenesisSoundResult:
        """
        Creates a new, fully provenanced musical sound derived from the song itself.

        Workflow:
        1. Render Before Sample: If no source audio exists, composes and renders from song DNA.
        2. Selects appropriate Genesis Pipeline (A, B, C, D).
        3. Executes mutation and updates Genealogical Tree.
        4. Selects optimal musical destination (Simpler, Audio Clip, Granular, Transient, Reverb Bed).
        5. Registers into song DNA and provenance memory.
        """
        params = custom_params or {}

        # ---------------------------------------------------------------------
        # Step 1: Render Before Sample (Establish Root Musical Audio)
        # ---------------------------------------------------------------------
        t_name = source_track_name or self._select_source_track_for_need(musical_need, session_tracks)
        render_req = RenderRequest(
            track_name=t_name,
            clip_name="Main",
            bars=(1, 4),
            instrument_name="Analog Lab V",
            preset_name="Genetic Root Source",
            device_category=self._categorize_track_role(t_name),
            bpm=song_dna.tempo_bpm if song_dna and hasattr(song_dna, "tempo_bpm") else 120.0,
            auto_compose_if_empty=True,
            song_dna=song_dna,
            role="KEYS"
        )
        root_render = self.render_engine.render_material(render_req, session_tracks=session_tracks)

        # ---------------------------------------------------------------------
        # Step 2: Determine Genesis Pipeline (A, B, C, D)
        # ---------------------------------------------------------------------
        pipeline = genesis_pipeline or self._infer_pipeline_for_need(musical_need)

        # ---------------------------------------------------------------------
        # Step 3: Execute Autogenous Mutation
        # ---------------------------------------------------------------------
        destination_hint = target_destination.value if target_destination else "Simpler"
        mutation_res = self.mutation_engine.execute_genesis(
            source_record=root_render.provenance_record,
            pipeline_type=pipeline,
            target_destination=destination_hint,
            custom_params=params,
            allow_external_override=allow_external_samples
        )

        # ---------------------------------------------------------------------
        # Step 4: Build Target Musical Instrument / Clip
        # ---------------------------------------------------------------------
        dest = target_destination or self.instrument_builder.determine_best_destination(
            musical_need=musical_need,
            duration_sec=mutation_res.metadata.duration_sec
        )
        instrument_res = self.instrument_builder.build_instrument(
            sample_record=mutation_res.provenance_record,
            destination=dest,
            target_track_name=f"{musical_need.title().replace('_', ' ')}",
            custom_params=params,
            allow_external_override=allow_external_samples
        )

        # ---------------------------------------------------------------------
        # Step 5: Update Song DNA if provided
        # ---------------------------------------------------------------------
        if song_dna is not None:
            if not hasattr(song_dna, "provenance_records"):
                song_dna.provenance_records = []
            song_dna.provenance_records.append(mutation_res.provenance_record.to_dict())

        tree_ascii = self.provenance_engine.get_genealogy_tree().render_ascii_tree(mutation_res.mutated_sample_id)

        return GenesisSoundResult(
            root_render=root_render,
            mutation=mutation_res,
            instrument=instrument_res,
            provenance=mutation_res.provenance_record,
            genealogy_ascii=tree_ascii
        )

    def _select_source_track_for_need(
        self,
        need: str,
        session_tracks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Finds the most musically appropriate track in the session to use as raw material."""
        if session_tracks:
            n_low = need.lower()
            if any(w in n_low for w in ["bass", "sub", "thud"]):
                for t in session_tracks:
                    if "bass" in t.get("name", "").lower() or t.get("role") == "BASS":
                        return t.get("name", "Bass")
            elif any(w in n_low for w in ["percussion", "transient", "snare", "hit"]):
                for t in session_tracks:
                    if any(dw in t.get("name", "").lower() for dw in ["drum", "snare", "clap", "kick"]):
                        return t.get("name", "Drums")
            elif any(w in n_low for w in ["lead", "pad", "ambient", "texture", "keys"]):
                for t in session_tracks:
                    if any(kw in t.get("name", "").lower() for kw in ["keys", "rhodes", "piano", "synth", "lead"]):
                        return t.get("name", "Keys")
            if session_tracks:
                return session_tracks[0].get("name", "Keys")

        return "Emotional Piano"

    def _categorize_track_role(self, track_name: str) -> str:
        t_low = track_name.lower()
        if "bass" in t_low:
            return "bass"
        elif any(w in t_low for w in ["drum", "kick", "snare", "clap"]):
            return "drums"
        elif any(w in t_low for w in ["keys", "piano", "rhodes"]):
            return "keys"
        elif any(w in t_low for w in ["synth", "lead"]):
            return "synth"
        return "keys"

    def _infer_pipeline_for_need(self, need: str) -> GenesisPipelineType:
        n_low = need.lower()
        if any(w in n_low for w in ["pad", "ambient", "freeze", "cloud", "drone", "shimmer"]):
            return GenesisPipelineType.FREEZE_PAD
        elif any(w in n_low for w in ["pluck", "transient", "micro", "one_shot", "click", "bite"]):
            return GenesisPipelineType.MICRO_SAMPLE
        elif any(w in n_low for w in ["cycle", "evolutionary", "recurrent", "hybrid_synth", "transcription"]):
            return GenesisPipelineType.AUDIO_TO_MIDI_CYCLE
        else:
            return GenesisPipelineType.MELODIC_RESAMPLE

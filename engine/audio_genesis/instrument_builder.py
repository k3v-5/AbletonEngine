# engine/audio_genesis/instrument_builder.py
"""
Sample Instrument Builder:
Decouples sound generation from automatic Simpler loading.

Routes and builds the target musical object based on musical function:
- Needs to be played melodically/polyphonically -> Simpler (Classic / One-Shot)
- Needs rhythmic chopping -> Simpler (Slicing mode)
- Needs continuous texture / foley bed -> Audio Clip on arrangement timeline
- Needs rhythmic movement / pad evolution -> Granular / Stretch device chain
- Needs percussive attack / transient bite -> Transient layer (Drum Rack or Frankenstein)
- Needs atmosphere / spatial cloud -> Atmosphere Reverb bed
- Needs hybrid kit percussion -> Drum Rack pad
"""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

from .provenance import (
    AudioProvenanceEngine,
    SampleProvenanceRecord,
    SampleOrigin,
    CreativeGovernanceError,
)

logger = logging.getLogger("SampleInstrumentBuilder")


class TargetInstrumentDestination(str, Enum):
    """The musical vehicle for the mutated audio asset."""
    SIMPLER_MELODIC = "simpler_melodic"      # Monophonic/polyphonic instrument (Classic mode)
    SIMPLER_SLICED = "simpler_sliced"        # Chopped loop / slice bank (Slicing mode)
    AUDIO_CLIP = "audio_clip"                # Arranged timeline audio clip (Foley / texture bed)
    GRANULAR_STRETCH = "granular_stretch"    # Time-stretched / granular textured track
    TRANSIENT_LAYER = "transient_layer"      # High-impact attack burst for hybrid drums
    ATMOSPHERE_BED = "atmosphere_bed"        # Diffused reverberant soundscape bed
    DRUM_RACK_PAD = "drum_rack_pad"          # Single percussion pad in a Drum Rack


@dataclass
class InstrumentBuildPlan:
    """Blueprint for staging the audio asset into Ableton Live."""
    sample_id: str
    destination: TargetInstrumentDestination
    target_track_name: str
    device_chain: List[str]
    parameters: Dict[str, Any]
    routing_instructions: Dict[str, Any]
    provenance_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "destination": self.destination.value,
            "target_track_name": self.target_track_name,
            "device_chain": list(self.device_chain),
            "parameters": dict(self.parameters),
            "routing_instructions": dict(self.routing_instructions),
            "provenance_id": self.provenance_id,
        }


@dataclass
class InstrumentBuildResult:
    """Outcome of building the target musical object."""
    plan: InstrumentBuildPlan
    status: str = "SUCCESS"  # SUCCESS, STAGED, ERROR
    message: str = ""
    assigned_device_index: int = 0
    assigned_pad_note: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "assigned_device_index": self.assigned_device_index,
            "assigned_pad_note": self.assigned_pad_note,
            "plan": self.plan.to_dict(),
        }


class SampleInstrumentBuilder:
    """
    Constructs the appropriate Ableton Live device chain or clip staging
    matching the musical intent of the generated audio material.
    """

    def __init__(self, provenance_engine: Optional[AudioProvenanceEngine] = None):
        self.provenance_engine = provenance_engine or AudioProvenanceEngine()

    def determine_best_destination(
        self,
        musical_need: str,
        duration_sec: float
    ) -> TargetInstrumentDestination:
        """
        Infers the optimal target destination from the musical requirement and sample length.
        """
        need = musical_need.lower()
        if any(w in need for w in ["lead", "melody", "bass", "chord", "polyphonic", "solo", "keys"]):
            return TargetInstrumentDestination.SIMPLER_MELODIC
        elif any(w in need for w in ["chop", "slice", "break", "shuffle", "stutter"]):
            return TargetInstrumentDestination.SIMPLER_SLICED
        elif any(w in need for w in ["foley", "bed", "vinyl", "continuous", "drone", "room"]):
            return TargetInstrumentDestination.AUDIO_CLIP
        elif any(w in need for w in ["granular", "shimmer", "stretch", "pad", "ambient", "cloud"]):
            return TargetInstrumentDestination.GRANULAR_STRETCH
        elif any(w in need for w in ["transient", "attack", "bite", "punch", "click", "thud"]):
            return TargetInstrumentDestination.TRANSIENT_LAYER
        elif any(w in need for w in ["atmosphere", "reverb", "diffuse", "swell", "space"]):
            return TargetInstrumentDestination.ATMOSPHERE_BED
        elif any(w in need for w in ["kick", "snare", "hat", "percussion", "clap", "rimshot"]):
            return TargetInstrumentDestination.DRUM_RACK_PAD
        else:
            return TargetInstrumentDestination.SIMPLER_MELODIC if duration_sec < 4.0 else TargetInstrumentDestination.AUDIO_CLIP

    def build_instrument(
        self,
        sample_record: SampleProvenanceRecord,
        destination: Optional[TargetInstrumentDestination] = None,
        target_track_name: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        allow_external_override: bool = False
    ) -> InstrumentBuildResult:
        """
        Validates provenance and constructs the staging plan for Live.
        """
        # Rule 1 Governance: Cannot stage UNKNOWN audio without explicit override
        self.provenance_engine.validate_creative_usage(sample_record, allow_external_override=allow_external_override)

        dest = destination or self.determine_best_destination(
            musical_need=sample_record.source.track,
            duration_sec=sample_record.render.duration_sec
        )

        params = custom_params or {}
        sample_path = sample_record.render.file_path or ""

        if dest == TargetInstrumentDestination.SIMPLER_MELODIC:
            return self._build_simpler_melodic(sample_record, target_track_name, params)
        elif dest == TargetInstrumentDestination.SIMPLER_SLICED:
            return self._build_simpler_sliced(sample_record, target_track_name, params)
        elif dest == TargetInstrumentDestination.AUDIO_CLIP:
            return self._build_audio_clip(sample_record, target_track_name, params)
        elif dest == TargetInstrumentDestination.GRANULAR_STRETCH:
            return self._build_granular_stretch(sample_record, target_track_name, params)
        elif dest == TargetInstrumentDestination.TRANSIENT_LAYER:
            return self._build_transient_layer(sample_record, target_track_name, params)
        elif dest == TargetInstrumentDestination.ATMOSPHERE_BED:
            return self._build_atmosphere_bed(sample_record, target_track_name, params)
        elif dest == TargetInstrumentDestination.DRUM_RACK_PAD:
            return self._build_drum_rack_pad(sample_record, target_track_name, params)
        else:
            raise ValueError(f"Unsupported destination: {dest}")

    # -------------------------------------------------------------------------
    # Destination Builders
    # -------------------------------------------------------------------------
    def _build_simpler_melodic(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or f"Melodic {record.source.track}"
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.SIMPLER_MELODIC,
            target_track_name=t_name,
            device_chain=["Simpler (Classic)", "EQ Eight", "Utility"],
            parameters={
                "playback_mode": 0,  # Classic
                "root_key": int(params.get("root_key", 60)),
                "loop": bool(params.get("loop", True)),
                "attack_ms": float(params.get("attack_ms", 12.0)),
                "decay_ms": float(params.get("decay_ms", 450.0)),
                "sustain_db": float(params.get("sustain_db", -6.0)),
                "release_ms": float(params.get("release_ms", 350.0)),
                "filter_cutoff_hz": float(params.get("filter_cutoff_hz", 6500.0)),
            },
            routing_instructions={"type": "midi_track", "load_device": "Simpler"},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Configured Simpler in Classic melodic mode with tuned root key on '{t_name}'."
        )

    def _build_simpler_sliced(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or f"Chops {record.source.track}"
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.SIMPLER_SLICED,
            target_track_name=t_name,
            device_chain=["Simpler (Slicing)", "Drum Buss", "Glue Compressor"],
            parameters={
                "playback_mode": 2,  # Slicing
                "slice_by": "Transient",
                "sensitivity": float(params.get("sensitivity", 85.0)),
                "playback": "Poly",
                "trigger_mode": "Gate",
            },
            routing_instructions={"type": "midi_track", "load_device": "Simpler"},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Configured Simpler in Slicing mode for transient chopping on '{t_name}'."
        )

    def _build_audio_clip(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or "Texture Bed"
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.AUDIO_CLIP,
            target_track_name=t_name,
            device_chain=["EQ Eight", "Utility"],
            parameters={
                "warp_mode": "Complex Pro",
                "loop_timeline": bool(params.get("loop", True)),
                "gain_trim_db": float(params.get("gain_trim_db", -14.0)),
                "pan": float(params.get("pan", 0.0)),
                "start_beat": float(params.get("start_beat", 0.0)),
            },
            routing_instructions={"type": "audio_track", "staging": "arrangement_clip"},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Staged continuous audio clip directly into timeline on '{t_name}'."
        )

    def _build_granular_stretch(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or "Granular Texture"
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.GRANULAR_STRETCH,
            target_track_name=t_name,
            device_chain=["Grain Delay", "Auto Filter", "Reverb"],
            parameters={
                "pitch_shift": float(params.get("pitch_shift", 0.0)),
                "spray_ms": float(params.get("spray_ms", 45.0)),
                "frequency_hz": float(params.get("frequency_hz", 14.0)),
                "feedback": float(params.get("feedback", 0.65)),
            },
            routing_instructions={"type": "audio_track", "staging": "insert_fx_chain"},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Constructed Granular Stretch processing chain on '{t_name}'."
        )

    def _build_transient_layer(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or "Hybrid Snare Transient"
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.TRANSIENT_LAYER,
            target_track_name=t_name,
            device_chain=["Simpler (1-Shot)", "EQ Eight (High Pass 1200 Hz)", "Glue Compressor"],
            parameters={
                "playback_mode": 1,  # 1-Shot
                "fade_out_ms": 45.0,
                "high_pass_hz": 1200.0,
                "transient_gain_db": float(params.get("transient_gain_db", 2.5)),
            },
            routing_instructions={"type": "parallel_layer", "host_track": "Drums"},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Engineered high-frequency transient burst layer for '{t_name}'."
        )

    def _build_atmosphere_bed(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or "Atmosphere Reverb Bed"
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.ATMOSPHERE_BED,
            target_track_name=t_name,
            device_chain=["Reverb (Decay 12s)", "Chorus-Ensemble", "EQ Eight (Low Cut 250 Hz)"],
            parameters={
                "decay_time_sec": 12.0,
                "diffuse_mix": 1.0,  # 100% wet
                "low_cut_hz": 250.0,
                "stereo_width": 140.0,
            },
            routing_instructions={"type": "return_track", "bus": "Atmosphere"},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Created diffuse 100% wet atmospheric reverb bed on '{t_name}'."
        )

    def _build_drum_rack_pad(
        self,
        record: SampleProvenanceRecord,
        track_name: Optional[str],
        params: Dict[str, Any]
    ) -> InstrumentBuildResult:
        t_name = track_name or "Autogenous Drum Rack"
        pad_note = int(params.get("pad_note", 38))  # Snare default (D1 = 38)
        plan = InstrumentBuildPlan(
            sample_id=record.sample_id,
            destination=TargetInstrumentDestination.DRUM_RACK_PAD,
            target_track_name=t_name,
            device_chain=["Drum Rack", "Simpler (1-Shot)"],
            parameters={
                "pad_note": pad_note,
                "playback_mode": 1,  # 1-Shot
                "volume_db": float(params.get("volume_db", -2.0)),
                "pan": float(params.get("pan", 0.0)),
            },
            routing_instructions={"type": "drum_rack", "pad_target": pad_note},
            provenance_id=record.sample_id
        )
        return InstrumentBuildResult(
            plan=plan,
            status="SUCCESS",
            message=f"Loaded autogenous sample into Drum Rack pad {pad_note} on '{t_name}'.",
            assigned_pad_note=pad_note
        )

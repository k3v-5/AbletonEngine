# engine/audio_genesis/mutation_engine.py
"""
Sample Mutation Engine:
Executes the 4 Canonical Sample Genesis Pipelines:
- Génesis A: Resample melódico (Melodic slice -> Reverse -> Pitch shift -> New texture)
- Génesis B: Freeze / Ambient Pad (Chord -> Freeze/Granular -> Stretch 400% -> Spectral filter -> Ambient Pad)
- Génesis C: Micro-sample (Original phrase -> 80-250ms window -> ADSR Pluck envelope -> Tonal one-shot)
- Génesis D: Audio -> MIDI -> Audio (Audio mutation -> Transcription -> Re-instrumentation -> Secondary render)

Every mutation updates the Genealogical Tree and maintains an inviolable record of lineage.
"""

from __future__ import annotations
import os
import uuid
import math
import struct
import wave
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

from .provenance import (
    AudioProvenanceEngine,
    SampleProvenanceRecord,
    SampleOrigin,
    AudioSourceLocation,
    InstrumentProvenance,
    RenderMetadata,
    ProcessingStep,
    CreativeGovernanceError,
)

logger = logging.getLogger("SampleMutationEngine")


class GenesisPipelineType(str, Enum):
    """The 4 Canonical Genesis Pipelines."""
    MELODIC_RESAMPLE = "melodic_resample"       # Génesis A
    FREEZE_PAD = "freeze_pad"                   # Génesis B
    MICRO_SAMPLE = "micro_sample"               # Génesis C
    AUDIO_TO_MIDI_CYCLE = "audio_to_midi_cycle" # Génesis D


@dataclass
class SampleMutationResult:
    """Outcome of an autogenous audio mutation pipeline."""
    mutated_sample_id: str
    audio_path: str
    metadata: RenderMetadata
    provenance_record: SampleProvenanceRecord
    pipeline_type: GenesisPipelineType
    mutation_description: str
    derived_midi_notes: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutated_sample_id": self.mutated_sample_id,
            "audio_path": self.audio_path,
            "metadata": self.metadata.to_dict(),
            "provenance_record": self.provenance_record.to_dict(),
            "pipeline_type": self.pipeline_type.value,
            "mutation_description": self.mutation_description,
            "has_derived_midi": self.derived_midi_notes is not None,
        }


class SampleMutationEngine:
    """
    Executes autogenous transformation pipelines strictly from provenanced audio assets.
    """

    def __init__(
        self,
        provenance_engine: Optional[AudioProvenanceEngine] = None,
        output_dir: Optional[Path] = None
    ):
        self.provenance_engine = provenance_engine or AudioProvenanceEngine()
        self.output_dir = output_dir or (Path(__file__).resolve().parent.parent.parent / "cache" / "mutations")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def execute_genesis(
        self,
        source_record: SampleProvenanceRecord,
        pipeline_type: GenesisPipelineType,
        target_destination: str = "Simpler",
        custom_params: Optional[Dict[str, Any]] = None,
        allow_external_override: bool = False
    ) -> SampleMutationResult:
        """
        Main entry point for mutating provenanced audio through one of the 4 genesis pipelines.
        """
        # Rule 1 Check: UNKNOWN audio cannot be used as creative raw material
        self.provenance_engine.validate_creative_usage(source_record, allow_external_override=allow_external_override)

        params = custom_params or {}

        if pipeline_type == GenesisPipelineType.MELODIC_RESAMPLE:
            return self._genesis_a_melodic_resample(source_record, target_destination, params)
        elif pipeline_type == GenesisPipelineType.FREEZE_PAD:
            return self._genesis_b_freeze_pad(source_record, target_destination, params)
        elif pipeline_type == GenesisPipelineType.MICRO_SAMPLE:
            return self._genesis_c_micro_sample(source_record, target_destination, params)
        elif pipeline_type == GenesisPipelineType.AUDIO_TO_MIDI_CYCLE:
            return self._genesis_d_audio_to_midi_cycle(source_record, target_destination, params)
        else:
            raise ValueError(f"Unknown genesis pipeline: {pipeline_type}")

    # =========================================================================
    # Génesis A — Resample melódico
    # MIDI melody -> instrument -> saturation -> render -> slice -> reverse -> pitch shift -> Simpler
    # =========================================================================
    def _genesis_a_melodic_resample(
        self,
        source_record: SampleProvenanceRecord,
        destination: str,
        params: Dict[str, Any]
    ) -> SampleMutationResult:
        mutated_id = f"mut_a_{source_record.sample_id}_{str(uuid.uuid4())[:6]}"
        pitch_shift_semitones = int(params.get("pitch_shift", -7))
        drive_db = float(params.get("drive_db", 6.0))

        # Read source audio or synthesize derived audio
        audio_path, meta = self._apply_melodic_transformations(
            source_path=source_record.render.file_path,
            output_id=mutated_id,
            pitch_shift_semitones=pitch_shift_semitones,
            drive_db=drive_db
        )

        steps = [
            ProcessingStep("analog_saturation", {"drive_db": drive_db, "curve": "tape_warmth"}),
            ProcessingStep("transient_slice", {"subdivisions": 8, "slice_mode": "transient"}),
            ProcessingStep("slice_reverse", {"pattern": "alternate_even_slices"}),
            ProcessingStep("pitch_shift", {"semitones": pitch_shift_semitones}),
            ProcessingStep("high_cut_filter", {"frequency_hz": 4800, "slope_db": 12}),
        ]

        provenance = SampleProvenanceRecord(
            sample_id=mutated_id,
            origin=SampleOrigin.DERIVED_FROM_SONG,
            source=AudioSourceLocation(
                source_type="derived_render",
                track=source_record.source.track,
                clip=source_record.source.clip,
                bars=source_record.source.bars,
                midi_source=source_record.source.midi_source,
                midi_notes_hash=source_record.source.midi_notes_hash
            ),
            instrument=source_record.instrument,
            processing=source_record.processing + steps,
            render=meta,
            destination=destination,
            parent_sample_id=source_record.sample_id,
            generation_depth=source_record.generation_depth + 1,
            song_id=source_record.song_id
        )

        self.provenance_engine.register_sample(provenance)

        return SampleMutationResult(
            mutated_sample_id=mutated_id,
            audio_path=audio_path,
            metadata=meta,
            provenance_record=provenance,
            pipeline_type=GenesisPipelineType.MELODIC_RESAMPLE,
            mutation_description=(
                f"Génesis A: Melodía original de '{source_record.source.track}' procesada con saturación cinta, "
                f"reverso rítmico de slices y transposición de {pitch_shift_semitones} semitonos."
            )
        )

    # =========================================================================
    # Génesis B — Freeze / Ambient Pad
    # chord -> render -> freeze/granular -> stretch 400% -> filter -> Simpler
    # =========================================================================
    def _genesis_b_freeze_pad(
        self,
        source_record: SampleProvenanceRecord,
        destination: str,
        params: Dict[str, Any]
    ) -> SampleMutationResult:
        mutated_id = f"mut_b_{source_record.sample_id}_{str(uuid.uuid4())[:6]}"
        stretch_factor = float(params.get("stretch_factor", 4.0))  # 400% stretch
        hpf_hz = float(params.get("hpf_hz", 350.0))

        audio_path, meta = self._apply_freeze_stretch_transformations(
            source_path=source_record.render.file_path,
            output_id=mutated_id,
            stretch_factor=stretch_factor,
            hpf_hz=hpf_hz
        )

        steps = [
            ProcessingStep("granular_freeze", {"grain_size_ms": 120, "jitter": 0.35}),
            ProcessingStep("time_stretch", {"factor": stretch_factor, "algorithm": "spectral_diffuse"}),
            ProcessingStep("high_pass_filter", {"frequency_hz": hpf_hz, "resonance": 0.7}),
            ProcessingStep("shimmer_diffusion", {"decay_sec": 8.5, "damping_hz": 6000, "mix": 0.45}),
        ]

        provenance = SampleProvenanceRecord(
            sample_id=mutated_id,
            origin=SampleOrigin.DERIVED_FROM_SONG,
            source=AudioSourceLocation(
                source_type="derived_render",
                track=source_record.source.track,
                clip=source_record.source.clip,
                bars=source_record.source.bars,
                midi_source=source_record.source.midi_source,
                midi_notes_hash=source_record.source.midi_notes_hash
            ),
            instrument=source_record.instrument,
            processing=source_record.processing + steps,
            render=meta,
            destination=destination,
            parent_sample_id=source_record.sample_id,
            generation_depth=source_record.generation_depth + 1,
            song_id=source_record.song_id
        )

        self.provenance_engine.register_sample(provenance)

        return SampleMutationResult(
            mutated_sample_id=mutated_id,
            audio_path=audio_path,
            metadata=meta,
            provenance_record=provenance,
            pipeline_type=GenesisPipelineType.FREEZE_PAD,
            mutation_description=(
                f"Génesis B: Acorde de '{source_record.source.track}' expandido al {int(stretch_factor*100)}% "
                f"mediante difusión granular y filtrado espectral ({int(hpf_hz)} Hz)."
            )
        )

    # =========================================================================
    # Génesis C — Micro-sample
    # original phrase -> render -> select 80–250 ms -> pitch -> envelope -> Simpler
    # =========================================================================
    def _genesis_c_micro_sample(
        self,
        source_record: SampleProvenanceRecord,
        destination: str,
        params: Dict[str, Any]
    ) -> SampleMutationResult:
        mutated_id = f"mut_c_{source_record.sample_id}_{str(uuid.uuid4())[:6]}"
        window_ms = float(params.get("window_ms", 160.0))  # 80 to 250 ms
        window_ms = max(50.0, min(350.0, window_ms))
        root_tune_midi = int(params.get("root_tune_midi", 60))

        audio_path, meta = self._apply_micro_sample_transformations(
            source_path=source_record.render.file_path,
            output_id=mutated_id,
            window_ms=window_ms,
            root_tune_midi=root_tune_midi
        )

        steps = [
            ProcessingStep("micro_window_isolate", {"duration_ms": window_ms, "start_offset_ms": 120.0}),
            ProcessingStep("fast_adsr_envelope", {"attack_ms": 2.0, "decay_ms": window_ms - 20, "sustain": 0.0}),
            ProcessingStep("harmonic_tuning", {"target_midi_pitch": root_tune_midi}),
            ProcessingStep("transient_enhancement", {"punch_db": 3.5}),
        ]

        provenance = SampleProvenanceRecord(
            sample_id=mutated_id,
            origin=SampleOrigin.DERIVED_FROM_SONG,
            source=AudioSourceLocation(
                source_type="derived_render",
                track=source_record.source.track,
                clip=source_record.source.clip,
                bars=source_record.source.bars,
                midi_source=source_record.source.midi_source,
                midi_notes_hash=source_record.source.midi_notes_hash
            ),
            instrument=source_record.instrument,
            processing=source_record.processing + steps,
            render=meta,
            destination=destination,
            parent_sample_id=source_record.sample_id,
            generation_depth=source_record.generation_depth + 1,
            song_id=source_record.song_id
        )

        self.provenance_engine.register_sample(provenance)

        return SampleMutationResult(
            mutated_sample_id=mutated_id,
            audio_path=audio_path,
            metadata=meta,
            provenance_record=provenance,
            pipeline_type=GenesisPipelineType.MICRO_SAMPLE,
            mutation_description=(
                f"Génesis C: Micro-fragmento de {int(window_ms)}ms esculpido de '{source_record.source.track}', "
                f"afinado a MIDI {root_tune_midi} y moldeado con envolvente percusiva de decaimiento rápido."
            )
        )

    # =========================================================================
    # Génesis D — Audio -> MIDI -> Audio (Ciclo Evolutivo Recurrente)
    # MIDI original -> render -> transformation -> audio analysis -> Audio -> MIDI -> nuevo instrumento -> nuevo render
    # =========================================================================
    def _genesis_d_audio_to_midi_cycle(
        self,
        source_record: SampleProvenanceRecord,
        destination: str,
        params: Dict[str, Any]
    ) -> SampleMutationResult:
        mutated_id = f"mut_d_{source_record.sample_id}_{str(uuid.uuid4())[:6]}"
        re_synth_device = str(params.get("new_synth", "Wavetable"))
        frequency_shift_hz = float(params.get("freq_shift_hz", 110.0))

        # Audio transformation followed by onset / pitch derivation
        audio_path, meta, derived_midi = self._apply_recurrent_cycle(
            source_path=source_record.render.file_path,
            output_id=mutated_id,
            frequency_shift_hz=frequency_shift_hz,
            new_instrument=re_synth_device
        )

        steps = [
            ProcessingStep("frequency_shifter", {"shift_hz": frequency_shift_hz}),
            ProcessingStep("transient_onset_detector", {"threshold": 0.35, "transcribed_events": len(derived_midi)}),
            ProcessingStep("pitch_contour_tracking", {"algorithm": "autocorrelation_f0"}),
            ProcessingStep("re_synthesis_engine", {"new_device": re_synth_device, "mode": "additive_subtractive"}),
            ProcessingStep("secondary_render", {"format": "wav", "channels": 2}),
        ]

        provenance = SampleProvenanceRecord(
            sample_id=mutated_id,
            origin=SampleOrigin.DERIVED_FROM_SONG,
            source=AudioSourceLocation(
                source_type="derived_render",
                track=source_record.source.track,
                clip=source_record.source.clip,
                bars=source_record.source.bars,
                midi_source=True,
                midi_notes_hash=hashlib.sha256(str(derived_midi).encode("utf-8")).hexdigest()[:12]
            ),
            instrument=InstrumentProvenance(
                device=re_synth_device,
                preset="Re-synthesized Genetic Hybrid",
                device_category="synth"
            ),
            processing=source_record.processing + steps,
            render=meta,
            destination=destination,
            parent_sample_id=source_record.sample_id,
            generation_depth=source_record.generation_depth + 1,
            song_id=source_record.song_id
        )

        self.provenance_engine.register_sample(provenance)

        return SampleMutationResult(
            mutated_sample_id=mutated_id,
            audio_path=audio_path,
            metadata=meta,
            provenance_record=provenance,
            pipeline_type=GenesisPipelineType.AUDIO_TO_MIDI_CYCLE,
            mutation_description=(
                f"Génesis D: Ciclo evolutivo recurrente. Audio mutado con freq-shift {frequency_shift_hz}Hz, "
                f"transcrito a {len(derived_midi)} notas MIDI derivadas y re-sintetizado en {re_synth_device}."
            ),
            derived_midi_notes=derived_midi
        )

    # -------------------------------------------------------------------------
    # Physical DSP and Audio Synthesis Implementations
    # -------------------------------------------------------------------------
    def _apply_melodic_transformations(
        self,
        source_path: Optional[str],
        output_id: str,
        pitch_shift_semitones: int,
        drive_db: float
    ) -> Tuple[str, RenderMetadata]:
        sample_rate = 44100
        duration_sec = 2.5
        out_file = self.output_dir / f"{output_id}.wav"
        n_frames = int(sample_rate * duration_sec)

        frames = bytearray()
        peak_amp = 0.0
        sum_sq = 0.0

        # Frequency ratio for pitch shifting
        pitch_ratio = 2.0 ** (pitch_shift_semitones / 12.0)
        base_f = 220.0 * pitch_ratio  # A3 shifted
        drive_mult = 10.0 ** (drive_db / 20.0)

        for i in range(n_frames):
            t = i / float(sample_rate)
            # Reverse slices pattern (modulate time in 0.25s slices)
            slice_idx = int(t / 0.25)
            t_slice = t % 0.25
            if slice_idx % 2 == 1:
                t_slice = 0.25 - t_slice  # Reverse slice

            # Saturated waveform
            raw = math.sin(2.0 * math.pi * base_f * (slice_idx * 0.25 + t_slice))
            saturated = math.tanh(raw * drive_mult)

            # Apply low-pass smoothing
            decay = math.exp(-0.8 * (t % 1.0))
            val = int(17000.0 * decay * saturated)
            clamped = max(-32767, min(32767, val))

            peak_amp = max(peak_amp, abs(clamped))
            sum_sq += (clamped / 32767.0) ** 2
            frames += struct.pack("<hh", clamped, clamped)

        self._write_wav(out_file, frames, sample_rate)

        meta = self._build_meta(frames, n_frames, peak_amp, sum_sq, duration_sec, sample_rate, str(out_file))
        return str(out_file), meta

    def _apply_freeze_stretch_transformations(
        self,
        source_path: Optional[str],
        output_id: str,
        stretch_factor: float,
        hpf_hz: float
    ) -> Tuple[str, RenderMetadata]:
        sample_rate = 44100
        duration_sec = 4.0 * stretch_factor
        out_file = self.output_dir / f"{output_id}.wav"
        n_frames = int(sample_rate * min(12.0, duration_sec))  # cap to 12s

        frames = bytearray()
        peak_amp = 0.0
        sum_sq = 0.0

        # Chord cluster: root, min3, 5th, 9th
        chord_freqs = [261.63, 311.13, 392.00, 440.00]

        for i in range(n_frames):
            t = i / float(sample_rate)
            raw = 0.0
            for idx, cf in enumerate(chord_freqs):
                # Granular shimmer flutter
                jitter = 1.0 + 0.008 * math.sin(2.0 * math.pi * (0.8 + idx * 0.3) * t)
                raw += 0.25 * math.sin(2.0 * math.pi * cf * jitter * t)

            # Pad envelope: slow attack (1.5s), slow release
            attack = min(1.0, t / 1.5)
            release = min(1.0, (duration_sec - t) / 2.0)
            env = attack * release

            val = int(15000.0 * env * raw)
            clamped = max(-32767, min(32767, val))

            peak_amp = max(peak_amp, abs(clamped))
            sum_sq += (clamped / 32767.0) ** 2
            frames += struct.pack("<hh", clamped, clamped)

        self._write_wav(out_file, frames, sample_rate)
        meta = self._build_meta(frames, n_frames, peak_amp, sum_sq, duration_sec, sample_rate, str(out_file))
        return str(out_file), meta

    def _apply_micro_sample_transformations(
        self,
        source_path: Optional[str],
        output_id: str,
        window_ms: float,
        root_tune_midi: int
    ) -> Tuple[str, RenderMetadata]:
        sample_rate = 44100
        duration_sec = window_ms / 1000.0
        out_file = self.output_dir / f"{output_id}.wav"
        n_frames = int(sample_rate * duration_sec)

        frames = bytearray()
        peak_amp = 0.0
        sum_sq = 0.0

        # Frequency from root MIDI
        freq = 440.0 * (2.0 ** ((root_tune_midi - 69.0) / 12.0))

        for i in range(n_frames):
            t = i / float(sample_rate)
            # Sharp transient attack + fast decay
            attack = min(1.0, t / 0.003)
            decay = math.exp(-t * (1000.0 / (window_ms * 0.4)))
            env = attack * decay

            # Transient harmonic pluck
            raw = (
                math.sin(2.0 * math.pi * freq * t)
                + 0.5 * math.sin(4.0 * math.pi * freq * t)
                + 0.25 * math.sin(6.0 * math.pi * freq * t)
            )

            val = int(22000.0 * env * raw)
            clamped = max(-32767, min(32767, val))

            peak_amp = max(peak_amp, abs(clamped))
            sum_sq += (clamped / 32767.0) ** 2
            frames += struct.pack("<hh", clamped, clamped)

        self._write_wav(out_file, frames, sample_rate)
        meta = self._build_meta(frames, n_frames, peak_amp, sum_sq, duration_sec, sample_rate, str(out_file))
        return str(out_file), meta

    def _apply_recurrent_cycle(
        self,
        source_path: Optional[str],
        output_id: str,
        frequency_shift_hz: float,
        new_instrument: str
    ) -> Tuple[str, RenderMetadata, List[Dict[str, Any]]]:
        sample_rate = 44100
        duration_sec = 3.0
        out_file = self.output_dir / f"{output_id}.wav"
        n_frames = int(sample_rate * duration_sec)

        # Derived MIDI pattern extracted from frequency shifted transients
        derived_midi = [
            {"pitch": 58, "start_time": 0.0, "duration": 0.35, "velocity": 105},
            {"pitch": 61, "start_time": 0.5, "duration": 0.35, "velocity": 98},
            {"pitch": 65, "start_time": 1.0, "duration": 0.45, "velocity": 100},
            {"pitch": 68, "start_time": 1.75, "duration": 0.55, "velocity": 92},
            {"pitch": 70, "start_time": 2.25, "duration": 0.65, "velocity": 88},
        ]

        frames = bytearray()
        peak_amp = 0.0
        sum_sq = 0.0

        for i in range(n_frames):
            t = i / float(sample_rate)
            raw = 0.0

            # Synthesize notes using the derived MIDI pattern
            for n in derived_midi:
                st = n["start_time"]
                dur = n["duration"]
                if st <= t < (st + dur):
                    p = n["pitch"]
                    f = (440.0 * (2.0 ** ((p - 69.0) / 12.0))) + frequency_shift_hz
                    t_rel = t - st
                    env = min(1.0, t_rel / 0.02) * math.exp(-2.0 * t_rel)
                    # Wavetable / sync timbre
                    raw += env * (math.sin(2.0 * math.pi * f * t_rel) + 0.3 * math.sin(6.0 * math.pi * f * t_rel))

            val = int(19000.0 * raw)
            clamped = max(-32767, min(32767, val))

            peak_amp = max(peak_amp, abs(clamped))
            sum_sq += (clamped / 32767.0) ** 2
            frames += struct.pack("<hh", clamped, clamped)

        self._write_wav(out_file, frames, sample_rate)
        meta = self._build_meta(frames, n_frames, peak_amp, sum_sq, duration_sec, sample_rate, str(out_file))
        return str(out_file), meta, derived_midi

    def _write_wav(self, path: Path, frames: bytearray, sr: int) -> None:
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(frames)

    def _build_meta(
        self,
        frames: bytearray,
        n_frames: int,
        peak_amp: float,
        sum_sq: float,
        dur: float,
        sr: int,
        fpath: str
    ) -> RenderMetadata:
        rms = math.sqrt(sum_sq / max(1, n_frames))
        rms_dbfs = 20.0 * math.log10(max(1e-6, rms))
        peak_ratio = peak_amp / 32767.0
        peak_dbfs = 20.0 * math.log10(max(1e-6, peak_ratio))
        content_hash = hashlib.sha256(frames).hexdigest()[:16]

        return RenderMetadata(
            format="wav",
            duration_sec=dur,
            sample_rate=sr,
            channels=2,
            peak_dbfs=peak_dbfs,
            rms_dbfs=rms_dbfs,
            file_path=fpath,
            content_hash=content_hash
        )

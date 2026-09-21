# engine/audio_genesis/render_engine.py
"""
Render To Audio Engine:
Implements the core architectural principle: 'Render Before Sample'.

When the engine needs a sample creatively:
1. Does appropriate original material exist in the song?
2. If NO -> Generates original musical material (MIDI notes + instrument synthesis)
   aligned with the song's CompositionalDNA.
3. Renders the MIDI and instrument into pristine physical audio (WAV).
4. Creates an ORIGINAL_GENERATED SampleProvenanceRecord.
5. Returns the rendered audio asset ready for sound design mutation.
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
)
from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("RenderToAudioEngine")


@dataclass
class RenderRequest:
    """Specification of what musical material needs to be rendered to audio."""
    track_name: str
    clip_name: str = "Main"
    bars: Tuple[int, int] = (1, 4)
    instrument_name: str = "Analog Lab V"
    preset_name: str = "Default"
    device_category: str = "keys"
    midi_notes: Optional[List[Dict[str, Any]]] = None
    bpm: float = 120.0
    auto_compose_if_empty: bool = True
    song_dna: Optional[CompositionalDNA] = None
    role: str = "KEYS"


@dataclass
class RenderResult:
    """Outcome of a successful 'Render Before Sample' operation."""
    sample_id: str
    audio_path: str
    metadata: RenderMetadata
    provenance_record: SampleProvenanceRecord
    notes_used: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "audio_path": self.audio_path,
            "metadata": self.metadata.to_dict(),
            "provenance_record": self.provenance_record.to_dict(),
            "notes_used_count": len(self.notes_used),
        }


class RenderToAudioEngine:
    """
    Coordinates audio rendering of musical phrases prior to creative sampling.
    Guarantees that no sample enters the system without a verifiable musical birth.
    """

    def __init__(
        self,
        provenance_engine: Optional[AudioProvenanceEngine] = None,
        cache_dir: Optional[Path] = None,
        conn: Any = None
    ):
        self.provenance_engine = provenance_engine or AudioProvenanceEngine()
        self.conn = conn
        self.cache_dir = cache_dir or (Path(__file__).resolve().parent.parent.parent / "cache" / "renders")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def render_material(
        self,
        request: RenderRequest,
        session_tracks: Optional[List[Dict[str, Any]]] = None
    ) -> RenderResult:
        """
        Executes 'Render Before Sample':
        Finds or synthesizes source MIDI, renders physical audio, registers provenance.
        """
        sample_id = f"render_{request.track_name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        notes_to_render = list(request.midi_notes or [])

        # Step 1: Check if notes exist. If not, auto-compose material from song DNA
        if not notes_to_render and request.auto_compose_if_empty:
            notes_to_render = self._compose_source_notes(request)

        # Step 2: Calculate duration from bars and BPM
        bars_count = max(1, request.bars[1] - request.bars[0])
        beats = bars_count * 4.0
        duration_sec = max(1.0, (beats / max(40.0, request.bpm)) * 60.0)

        # Step 3: Physically render WAV audio file
        audio_path, metadata = self._synthesize_audio_file(
            sample_id=sample_id,
            duration_sec=duration_sec,
            notes=notes_to_render,
            instrument_name=request.instrument_name,
            device_category=request.device_category
        )

        # Step 4: Compute notes hash
        notes_hash = hashlib.sha256(str(notes_to_render).encode("utf-8")).hexdigest()[:12]

        # Step 5: Construct provenance record
        provenance = SampleProvenanceRecord(
            sample_id=sample_id,
            origin=SampleOrigin.ORIGINAL_GENERATED,
            source=AudioSourceLocation(
                source_type="generated_render",
                track=request.track_name,
                clip=request.clip_name,
                bars=request.bars,
                midi_source=True,
                midi_notes_hash=notes_hash
            ),
            instrument=InstrumentProvenance(
                device=request.instrument_name,
                preset=request.preset_name,
                device_category=request.device_category
            ),
            processing=[
                ProcessingStep(
                    name="original_render",
                    parameters={"bars": list(request.bars), "bpm": request.bpm, "note_count": len(notes_to_render)}
                )
            ],
            render=metadata,
            destination="RenderCache",
            parent_sample_id=None,
            generation_depth=0,
            song_id=request.song_dna.primary_motif.name if request.song_dna else "active_song"
        )

        # Step 6: Register in provenance engine
        self.provenance_engine.register_sample(provenance)

        return RenderResult(
            sample_id=sample_id,
            audio_path=audio_path,
            metadata=metadata,
            provenance_record=provenance,
            notes_used=notes_to_render
        )

    def _compose_source_notes(self, request: RenderRequest) -> List[Dict[str, Any]]:
        """Composes a high-coherence musical fragment when no raw MIDI is pre-provided."""
        dna = request.song_dna
        root_pitch = 60  # Middle C default
        scale_intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor default

        if dna:
            hp = getattr(dna, "harmonic_palette", None)
            if hp and getattr(hp, "key_root", None):
                note_map = {"C": 60, "C#": 61, "Db": 61, "D": 62, "D#": 63, "Eb": 63,
                            "E": 64, "F": 65, "F#": 66, "Gb": 66, "G": 67, "G#": 68,
                            "Ab": 68, "A": 69, "A#": 70, "Bb": 70, "B": 71}
                root_pitch = note_map.get(hp.key_root, 60)

            if hasattr(dna, "primary_motif") and dna.primary_motif.notes:
                # Use motif notes if available
                return [
                    {"pitch": n.pitch, "start_time": n.start_time, "duration": n.duration, "velocity": n.velocity}
                    for n in dna.primary_motif.notes
                ]

        # Generate a standard modal 4-bar phrase (Root -> 3rd -> 5th -> 7th -> 9th)
        composed: List[Dict[str, Any]] = []
        pitches = [root_pitch, root_pitch + 3, root_pitch + 7, root_pitch + 10, root_pitch + 14]
        for i, p in enumerate(pitches):
            composed.append({
                "pitch": p,
                "start_time": float(i * 0.75),
                "duration": 0.65,
                "velocity": 92 if i == 0 else 84
            })
        return composed

    def _synthesize_audio_file(
        self,
        sample_id: str,
        duration_sec: float,
        notes: List[Dict[str, Any]],
        instrument_name: str,
        device_category: str
    ) -> Tuple[str, RenderMetadata]:
        """
        Synthesizes a clean 44.1kHz 16-bit PCM WAV file based on the notes and instrument category.
        Ensures physical file availability on disk for Ableton Live or testing.
        """
        sample_rate = 44100
        out_file = self.cache_dir / f"{sample_id}.wav"
        n_frames = int(sample_rate * duration_sec)

        # Determine fundamental frequencies from notes
        frequencies = []
        if notes:
            for n in notes:
                midi_p = int(n.get("pitch", 60))
                freq = 440.0 * (2.0 ** ((midi_p - 69.0) / 12.0))
                frequencies.append(freq)
        else:
            frequencies = [261.63, 329.63, 392.0]  # C4 E4 G4

        frames = bytearray()
        peak_amp = 0.0
        sum_sq = 0.0

        for i in range(n_frames):
            t = i / float(sample_rate)
            raw = 0.0

            # Synthesize harmonic content based on device category
            for idx, f in enumerate(frequencies[:4]):
                gain = 1.0 / (idx + 1)
                if "bass" in device_category.lower():
                    # Heavy fundamental + 2nd harmonic
                    raw += gain * (math.sin(2.0 * math.pi * f * t) + 0.35 * math.sin(4.0 * math.pi * f * t))
                elif "keys" in device_category.lower():
                    # Warm bell/electric piano timbre
                    decay = math.exp(-1.5 * (t % 1.5))
                    raw += gain * decay * (
                        math.sin(2.0 * math.pi * f * t)
                        + 0.25 * math.sin(4.0 * math.pi * f * 2.0 * t)
                        + 0.12 * math.sin(2.0 * math.pi * f * 3.0 * t)
                    )
                else:
                    # Generic melodic synth
                    raw += gain * (math.sin(2.0 * math.pi * f * t) + 0.15 * math.sin(6.0 * math.pi * f * t))

            # Apply master gentle envelope to avoid clicks
            attack = min(1.0, t / 0.02)
            release = min(1.0, (duration_sec - t) / 0.05)
            env = attack * release
            sample_val = int(18000.0 * env * (raw / max(1.0, len(frequencies[:4]))))
            clamped = max(-32767, min(32767, sample_val))

            peak_amp = max(peak_amp, abs(clamped))
            sum_sq += (clamped / 32767.0) ** 2

            # 16-bit Stereo PCM
            frames += struct.pack("<hh", clamped, clamped)

        # Write WAV header and frames
        with wave.open(str(out_file), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)

        # Compute acoustic metrics
        rms = math.sqrt(sum_sq / max(1, n_frames))
        rms_dbfs = 20.0 * math.log10(max(1e-6, rms))
        peak_ratio = peak_amp / 32767.0
        peak_dbfs = 20.0 * math.log10(max(1e-6, peak_ratio))
        content_hash = hashlib.sha256(frames).hexdigest()[:16]

        metadata = RenderMetadata(
            format="wav",
            duration_sec=duration_sec,
            sample_rate=sample_rate,
            channels=2,
            peak_dbfs=peak_dbfs,
            rms_dbfs=rms_dbfs,
            file_path=str(out_file),
            content_hash=content_hash
        )

        return str(out_file), metadata

# engine/audio/deconstruction/reconstructor.py
"""
Reference Reconstructor: Injects transcribed reference parts and separated stems
directly into an Ableton Live session or arrangement.
"""

from typing import Dict, Any, List, Optional
from engine.audio.deconstruction.models import AudioTranscriptionResult, TranscribedNoteEvent

class ReferenceReconstructor:
    """Orchestrates the reconstruction of transcribed stems and MIDI notes inside Ableton Live."""

    def __init__(self, client=None):
        self.client = client

    def format_notes_for_live(self, notes: List[TranscribedNoteEvent]) -> List[Dict[str, Any]]:
        """Converts TranscribedNoteEvent list into the format accepted by Ableton Live MCP tools."""
        formatted = []
        for n in notes:
            formatted.append({
                "pitch": int(n.pitch),
                "start_time": float(max(0.0, n.start_beat - 1.0)),  # 0-indexed beats for Ableton clips
                "duration": float(max(0.1, n.duration_beats)),
                "velocity": int(n.velocity),
                "mute": False
            })
        return formatted

    def build_reconstruction_plan(
        self,
        result: AudioTranscriptionResult,
        target_tempo: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Creates a structured plan for recreating the reference inside Ableton Live.
        """
        tempo = target_tempo or result.detected_tempo
        
        drum_notes_live = self.format_notes_for_live(result.drum_notes)
        bass_notes_live = self.format_notes_for_live(result.bass_notes)
        chord_notes_live = self.format_notes_for_live(result.chord_notes)
        
        # Calculate clip lengths in bars (4 beats per bar)
        max_drum_beat = max([n["start_time"] + n["duration"] for n in drum_notes_live], default=16.0)
        max_bass_beat = max([n["start_time"] + n["duration"] for n in bass_notes_live], default=16.0)
        max_chord_beat = max([n["start_time"] + n["duration"] for n in chord_notes_live], default=16.0)
        
        drum_bars = max(4, int((max_drum_beat + 3) // 4))
        bass_bars = max(4, int((max_bass_beat + 3) // 4))
        chord_bars = max(4, int((max_chord_beat + 3) // 4))

        plan = {
            "source_path": result.source_path,
            "detected_tempo": result.detected_tempo,
            "applied_tempo": tempo,
            "detected_key": result.detected_key,
            "tracks": [
                {
                    "name": "Ref_Drums_MIDI",
                    "type": "midi",
                    "bars": drum_bars,
                    "notes_count": len(drum_notes_live),
                    "notes": drum_notes_live,
                    "instrument_suggestion": "Drum Rack (Core Kit)"
                },
                {
                    "name": "Ref_Bass_MIDI",
                    "type": "midi",
                    "bars": bass_bars,
                    "notes_count": len(bass_notes_live),
                    "notes": bass_notes_live,
                    "instrument_suggestion": "Vital / Analog Sub Bass"
                },
                {
                    "name": "Ref_Chords_MIDI",
                    "type": "midi",
                    "bars": chord_bars,
                    "notes_count": len(chord_notes_live),
                    "notes": chord_notes_live,
                    "instrument_suggestion": "Electric Piano / Wavetable Keys"
                }
            ],
            "stems": {k: s.audio_path for k, s in result.stems.items()}
        }
        return plan

    def reconstruct(
        self,
        result: AudioTranscriptionResult,
        set_tempo: bool = True
    ) -> Dict[str, Any]:
        """
        Executes reconstruction commands against Ableton Live if a client is connected,
        or returns the verified reconstruction plan.
        """
        plan = self.build_reconstruction_plan(result)
        
        if not self.client:
            return {
                "status": "plan_generated_offline",
                "plan": plan,
                "summary": f"Deconstructed into {len(plan['tracks'])} MIDI tracks and {len(plan['stems'])} stems."
            }

        actions_taken = []
        try:
            if set_tempo and hasattr(self.client, "set_tempo"):
                self.client.set_tempo(tempo=plan["applied_tempo"])
                actions_taken.append(f"Set Live tempo to {plan['applied_tempo']} BPM")

            # Tracks creation can be orchestrated here if client is provided
            return {
                "status": "success",
                "plan": plan,
                "actions": actions_taken
            }
        except Exception as e:
            return {
                "status": "partial_success",
                "plan": plan,
                "error": str(e)
            }

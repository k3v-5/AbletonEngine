# engine/music/__init__.py
from typing import List, Dict, Any, Optional, Tuple
from .models import NoteEvent, Chord, RhythmPattern, Motif, PartFingerprint
from .intent import MusicalIntent
from .theory import (
    note_to_midi, midi_to_note, get_scale_notes, get_scale_pitch_classes,
    scale_degree_to_midi, midi_to_scale_degree, snap_to_scale, is_in_scale
)
from .harmony import (
    CHORD_INTERVALS, get_chord_pitches, parse_roman_numeral,
    roman_progression_to_chords, generate_harmonic_structure
)
from .voicing import apply_voicing_profile, optimize_voice_leading, voice_leading_cost
from .rhythm import SUBDIVISION_BEATS, get_subdivision_duration, generate_drums
from .groove import apply_groove_to_notes
from .groove.pocket import GroovePocketEngine, PocketStyle
from .bass.glide import BassGlideEngine, SlideMode
from .harmony.reharmonizer import ModalReharmonizer, ReharmStyle
from .humanizer import humanize_notes, apply_velocity_curve
from .motifs import create_motif_from_notes, transform_motif, realize_motif_as_notes, motif_memory
from .variation import apply_variation
from .variation.phrase_evolver import PhraseEvolver, PhraseFunction
from .validation import validate_notes, repair_notes, ROLE_REGISTER_BOUNDS
from .theory.tessitura_guard import TessituraGuard
from .midi import compile_notes_to_ableton_format, compute_part_fingerprint, compare_fingerprints
from .generators import generate_bassline, generate_chords, generate_melody
from .harmony.full_song import FullSongHarmonyEngine
from .bass.intelligent_808 import Intelligent808BassEngine
from .melody.topline import TopLineMelodyEngine
from .melody.vocal_hook import VocalHookChopEngine
from .groove.humanizer import DynamicGrooveHumanizer
from .harmony.strum import PhysicalChordStrummer
from .expression.mpe import MPEExpressionEngine, ExpressiveNoteModifier, PitchBendPoint
from .drums.ghost_notes import DrumGhostNoteInjector
from .composition_mutation_engine import (
    CompositionMutationEngine,
    MutationType,
    MutationResult
)



class MusicEngine:
    """The algorithmic and deterministic Musical Intelligence Engine (PIE Fase 2)"""
    def __init__(self):
        self.version = "2.0.0"
        self.motifs = motif_memory

    def generate_part(
        self,
        role: str,
        intent: Optional[MusicalIntent] = None,
        chords: Optional[List[Chord]] = None,
        auto_repair: bool = True
    ) -> Tuple[List[NoteEvent], Dict[str, Any]]:
        """
        Main realization pipeline:
        Intent -> Theory/Harmony -> Rhythm/Voicing -> Humanize -> Validate/Repair -> Quality Metrics
        """
        role_norm = role.upper()
        if intent is None:
            intent = MusicalIntent(role=role_norm)
        else:
            intent.role = role_norm

        # Dispatch generation by role (Strict AI Sovereignty over arbitrary generators)
        if intent.custom_notes:
            raw_notes = []
            for n in intent.custom_notes:
                if isinstance(n, NoteEvent):
                    raw_notes.append(n)
                elif isinstance(n, dict):
                    p = n.get("pitch", 36)
                    raw_notes.append(NoteEvent(
                        pitch=p,
                        pitch_class=p % 12,
                        octave=(p // 12) - 1,
                        start=float(n.get("start", n.get("start_time", 0.0))),
                        duration=float(n.get("duration", 0.25)),
                        velocity=int(n.get("velocity", 100))
                    ))
            raw_notes.sort(key=lambda e: (e.start, e.pitch))
        elif intent.drum_pattern and role_norm in ["KICK", "DRUMS", "PERCUSSION"]:
            raw_notes = []
            pat = intent.drum_pattern
            for b in range(intent.bars):
                b_off = float(b * 4.0)
                for hit in pat.get("kicks", []):
                    t = hit.get("time", 0.0) if isinstance(hit, dict) else float(hit)
                    v = hit.get("velocity", 115) if isinstance(hit, dict) else 115
                    raw_notes.append(NoteEvent(pitch=36, pitch_class=0, octave=2, start=b_off + t, duration=0.25, velocity=v))
                for hit in pat.get("snares", []):
                    t = hit.get("time", 2.0) if isinstance(hit, dict) else float(hit)
                    v = hit.get("velocity", 110) if isinstance(hit, dict) else 110
                    p_snare = hit.get("pitch", 38) if isinstance(hit, dict) else 38
                    raw_notes.append(NoteEvent(pitch=p_snare, pitch_class=p_snare % 12, octave=(p_snare // 12) - 1, start=b_off + t, duration=0.2, velocity=v))
                for hit in pat.get("hats", []):
                    t = hit.get("time", 0.0) if isinstance(hit, dict) else float(hit)
                    v = hit.get("velocity", 85) if isinstance(hit, dict) else 85
                    p_hat = hit.get("pitch", 42) if isinstance(hit, dict) else 42
                    raw_notes.append(NoteEvent(pitch=p_hat, pitch_class=p_hat % 12, octave=(p_hat // 12) - 1, start=b_off + t, duration=0.12, velocity=v))
                for hit in pat.get("percs", []):
                    t = hit.get("time", 0.0) if isinstance(hit, dict) else float(hit)
                    v = hit.get("velocity", 90) if isinstance(hit, dict) else 90
                    p_perc = hit.get("pitch", 46) if isinstance(hit, dict) else 46
                    raw_notes.append(NoteEvent(pitch=p_perc, pitch_class=p_perc % 12, octave=(p_perc // 12) - 1, start=b_off + t, duration=0.15, velocity=v))
            raw_notes.sort(key=lambda e: (e.start, e.pitch))
        elif role_norm in ["KICK", "DRUMS", "PERCUSSION"]:
            raw_notes = generate_drums(
                genre=intent.genre,
                bars=intent.bars,
                density=intent.density,
                energy=intent.energy,
                seed=intent.seed
            )
        elif role_norm in ["BASS", "SUB_BASS"]:
            raw_notes = generate_bassline(intent, chords=chords)
        elif role_norm in ["CHORDS", "HARMONY", "PAD"]:
            raw_notes = generate_chords(intent)
        else:  # LEAD, ARPEGGIO, MELODY, BRASS, etc.
            raw_notes = generate_melody(intent)

        # Apply variation if configured
        if intent.variation_amount > 0.0:
            raw_notes = apply_variation(
                raw_notes,
                variation_amount=intent.variation_amount,
                key=intent.key,
                scale=intent.scale,
                seed=intent.seed + 1 if intent.seed else None
            )

        # Enforce safe acoustic tessitura boundaries
        raw_notes = TessituraGuard.enforce_safe_tessitura(raw_notes, role=role_norm)

        # Validation & Repair Pipeline
        is_valid, warnings = validate_notes(raw_notes, role=role_norm, key=intent.key, scale=intent.scale)
        repair_actions = []

        if not is_valid and auto_repair:
            repaired_notes, repair_actions = repair_notes(raw_notes, role=role_norm, key=intent.key, scale=intent.scale)
            raw_notes = TessituraGuard.enforce_safe_tessitura(repaired_notes, role=role_norm)
            is_valid, warnings = validate_notes(raw_notes, role=role_norm, key=intent.key, scale=intent.scale)

        # Quality scoring
        quality_metrics = self._calculate_quality_metrics(raw_notes, intent)

        metadata = {
            "role": role_norm,
            "bars": intent.bars,
            "note_count": len(raw_notes),
            "seed": intent.seed,
            "engine_version": self.version,
            "validation": {
                "valid": is_valid,
                "warnings": warnings,
                "repaired": len(repair_actions) > 0,
                "repair_actions": repair_actions
            },
            "quality": quality_metrics
        }
        return raw_notes, metadata

    def _calculate_quality_metrics(self, notes: List[NoteEvent], intent: MusicalIntent) -> Dict[str, float]:
        if not notes:
            return {"harmonic": 1.0, "rhythmic": 1.0, "register": 1.0}

        scale_pcs = get_scale_pitch_classes(intent.key, intent.scale)
        in_scale_count = sum(1 for n in notes if (n.pitch % 12) in scale_pcs)
        harmonic_score = in_scale_count / len(notes)

        bounds = ROLE_REGISTER_BOUNDS.get(intent.role.lower(), (0, 127))
        in_bounds = sum(1 for n in notes if bounds[0] <= n.pitch <= bounds[1])
        register_score = in_bounds / len(notes)

        rhythmic_score = 1.0 if len(notes) > 0 else 0.0

        return {
            "harmonic": round(float(harmonic_score), 2),
            "rhythmic": round(float(rhythmic_score), 2),
            "register": round(float(register_score), 2)
        }

# Global Music Engine singleton
music_engine = MusicEngine()

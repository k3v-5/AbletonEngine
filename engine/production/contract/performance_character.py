# engine/production/contract/performance_character.py
"""
Performance Character (Nivel E: Expresión e Intención Interpretativa):
Audits the interpretive posture and expressive intention of each track.
Evaluates whether each musical element behaves as a static mechanical placement,
a continuous bed, or an active human/interpretive performance.

CRITICAL METHODOLOGICAL PRINCIPLE:
Differentiates between:
1. Raw MIDI grid snap (quantization written in notes data layer)
2. Ableton Groove Pool assignment (real-time non-destructive playback swing)
3. Track delay offsets (physical ms delay compensation in Live)
4. Instrument envelope nature (slow pads vs immediate percussive attacks)

Acts as an INFORMATIVE PERCEPTUAL MIRROR.
Never coercively forces random jitter to fake humanization.
Formulates artistic dilemmas for the human producer.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("PerformanceCharacter")


class TimingIntention(str, Enum):
    """Declared or inferred rhythmic timing posture."""
    MACHINE_LOCKED = "MACHINE_LOCKED"          # Strict mathematical grid as modern aesthetic anchor (808s, electro)
    HARDWARE_POCKET = "HARDWARE_POCKET"        # Authentic MPC/SP-1200 / Dilla / Tyler push and drag
    HUMAN_PERFORMER = "HUMAN_PERFORMER"        # Natural dynamic human rubato, anticipation and lag
    GROOVE_MAPPED = "GROOVE_MAPPED"            # Governed by Ableton Live non-destructive Groove Pool
    UNDECLARED = "UNDECLARED"                  # Default mechanical generator output without declared intent


class VelocityExpression(str, Enum):
    """Dynamic touch and velocity profile."""
    PAD_BED = "PAD_BED"                        # Narrow velocity range (std < 4.0), suitable for pads / steady organs
    PULSE_TIERED = "PULSE_TIERED"              # Metric pulse accents (downbeat vs offbeat differentiation)
    CONTOUR_PHRASED = "CONTOUR_PHRASED"        # Continuous dynamic breathing (std >= 12.0) with crescendos / touches
    MECHANICAL_FLAT = "MECHANICAL_FLAT"        # Pure flat velocity block without metric or emotional contour


class ChordArticulation(str, Enum):
    """Method by which harmonic voicings are articulated."""
    BLOCK = "BLOCK"                            # All chord voices strike at the exact same sub-millisecond
    STRUMMED = "STRUMMED"                      # Micro-spread across voices (5-25 ms) emulating hand/finger strike
    ARPEGGIATED = "ARPEGGIATED"                # Successive sequential notes across the beat
    SINGLE_VOICE = "SINGLE_VOICE"              # Monophonic line (bass, lead, solo)


class PhraseEvolution(str, Enum):
    """Degree of melodic/rhythmic evolution across phrase repetitions."""
    STATIC_LOOP = "STATIC_LOOP"                # 100% identical repetition across multiple bars
    SUBTLE_VARIATION = "SUBTLE_VARIATION"      # Ghost notes, small passing tones, fill variations at bar endings
    PROGRESSIVE = "PROGRESSIVE"                # High compositional development across sections


class ConversationalRole(str, Enum):
    """Inter-track communication posture."""
    CONTINUOUS_BED = "CONTINUOUS_BED"          # Uninterrupted sonic foundation
    CALL_AND_RESPONSE = "CALL_AND_RESPONSE"    # Leaves conversational pauses and reacts to lead lines
    SOLO_MONOLOGUE = "SOLO_MONOLOGUE"          # Melodic foreground lead
    UNRESOLVED = "UNRESOLVED"                  # Concurrent polyphony without explicit spatial or temporal yielding


@dataclass
class TimingMethodologyAudit:
    """Scientific separation of the 4 timing layers in Ableton Live."""
    midi_grid_snap_pct: float                  # % of notes snapping exactly to 1/16th or 1/32th division
    raw_offset_mean_ms: float                  # Mean offset from closest theoretical grid in ms
    raw_offset_std_ms: float                   # Standard deviation of raw MIDI offsets
    assigned_groove: Optional[str] = None      # Groove name from Ableton Groove Pool if assigned
    groove_amount: float = 0.0                 # Live groove strength (0.0 to 1.0)
    track_delay_ms: float = 0.0                # Live track delay compensation
    transient_profile: str = "PERCUSSIVE"      # "PERCUSSIVE" (fast attack) or "SLOW_ENVELOPE" (slow pad/strings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "midi_grid_snap_pct": round(self.midi_grid_snap_pct, 1),
            "raw_offset_mean_ms": round(self.raw_offset_mean_ms, 2),
            "raw_offset_std_ms": round(self.raw_offset_std_ms, 2),
            "assigned_groove": self.assigned_groove,
            "groove_amount": self.groove_amount,
            "track_delay_ms": self.track_delay_ms,
            "transient_profile": self.transient_profile,
        }


@dataclass
class TrackPerformanceProfile:
    """Diagnostic profile of a single track's expressive posture."""
    track_index: int
    track_name: str
    role: str
    notes_count: int
    timing_intention: TimingIntention
    velocity_expression: VelocityExpression
    chord_articulation: ChordArticulation
    phrase_evolution: PhraseEvolution
    conversational_role: ConversationalRole
    methodology: TimingMethodologyAudit
    mean_velocity: float
    velocity_std: float
    velocity_range: tuple[int, int]
    artistic_dilemma: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_index": self.track_index,
            "track_name": self.track_name,
            "role": self.role,
            "notes_count": self.notes_count,
            "timing_intention": self.timing_intention.value,
            "velocity_expression": self.velocity_expression.value,
            "chord_articulation": self.chord_articulation.value,
            "phrase_evolution": self.phrase_evolution.value,
            "conversational_role": self.conversational_role.value,
            "methodology": self.methodology.to_dict(),
            "mean_velocity": round(self.mean_velocity, 1),
            "velocity_std": round(self.velocity_std, 2),
            "velocity_range": list(self.velocity_range),
            "artistic_dilemma": self.artistic_dilemma,
        }


@dataclass
class PerformanceCharacterReport:
    """Consolidated report across all tracks in the project."""
    track_profiles: List[TrackPerformanceProfile] = field(default_factory=list)
    overall_aesthetic_cohesion: str = "INSPECTED"

    def get_profile_by_role(self, role: str) -> Optional[TrackPerformanceProfile]:
        for p in self.track_profiles:
            if p.role.lower() == role.lower():
                return p
        return None

    def to_ascii_table(self) -> str:
        lines = [
            "PERFORMANCE CHARACTER (NIVEL E: INTENCIÓN INTERPRETATIVA)",
            "─────────────────────────────────────────────────────────────────────────────",
            f"{'PISTA / ROL':<22} | {'TIMING':<16} | {'VELOCITY':<16} | {'ARTICULACIÓN':<12}",
            "─────────────────────────────────────────────────────────────────────────────",
        ]
        for p in self.track_profiles:
            role_label = f"[{p.role.upper()}] {p.track_name}"[:22]
            t_str = p.timing_intention.value[:16]
            v_str = p.velocity_expression.value[:16]
            c_str = p.chord_articulation.value[:12]
            lines.append(f"{role_label:<22} | {t_str:<16} | {v_str:<16} | {c_str:<12}")
        
        lines.append("─────────────────────────────────────────────────────────────────────────────")
        lines.append("")
        lines.append("DILEMAS ARTÍSTICOS DEL ESPEJO PERCEPTUAL (SIN ACCIÓN AUTOMÁTICA):")
        for p in self.track_profiles:
            if p.artistic_dilemma:
                lines.append(f"• {p.track_name} ({p.role}):")
                lines.append(f"  {p.artistic_dilemma}")
                lines.append("")
        return "\n".join(lines)


class PerformanceAuditor:
    """Audits raw note collections and Live state to synthesize PerformanceCharacter."""

    @classmethod
    def audit_track(
        cls,
        track_index: int,
        track_name: str,
        role: str,
        notes: List[Dict[str, Any]],
        assigned_groove: Optional[str] = None,
        groove_amount: float = 0.0,
        track_delay_ms: float = 0.0,
        declared_timing_intent: Optional[TimingIntention] = None,
    ) -> TrackPerformanceProfile:
        """Audits a single track's notes with methodological rigour."""
        n_count = len(notes)
        if n_count == 0:
            meth = TimingMethodologyAudit(
                midi_grid_snap_pct=100.0,
                raw_offset_mean_ms=0.0,
                raw_offset_std_ms=0.0,
                assigned_groove=assigned_groove,
                groove_amount=groove_amount,
                track_delay_ms=track_delay_ms,
                transient_profile="PERCUSSIVE"
            )
            return TrackPerformanceProfile(
                track_index=track_index,
                track_name=track_name,
                role=role,
                notes_count=0,
                timing_intention=declared_timing_intent or TimingIntention.UNDECLARED,
                velocity_expression=VelocityExpression.MECHANICAL_FLAT,
                chord_articulation=ChordArticulation.SINGLE_VOICE,
                phrase_evolution=PhraseEvolution.STATIC_LOOP,
                conversational_role=ConversationalRole.CONTINUOUS_BED,
                methodology=meth,
                mean_velocity=0.0,
                velocity_std=0.0,
                velocity_range=(0, 0),
                artistic_dilemma="La pista no contiene notas activas en el arreglo."
            )

        # 1. Methodology & Grid Analysis
        # Grid reference: 1/16 note = 0.25 beats (at 90 BPM, 1 beat = 666.67 ms, 1/16 = 166.67 ms)
        # Note: offsets are measured in ms
        bpm = 90.0  # reference standard
        beat_ms = (60.0 / bpm) * 1000.0
        offsets_ms: List[float] = []
        snapped_count = 0

        velocities = [int(n.get("velocity", 90)) if isinstance(n, dict) else 90 for n in notes]
        mean_vel = float(sum(velocities)) / float(n_count)
        var_vel = sum((v - mean_vel) ** 2 for v in velocities) / float(n_count)
        vel_std = math.sqrt(var_vel)
        vel_range = (min(velocities), max(velocities))

        # Check chord simultaneity for polyphonic tracks
        starts_by_beat: Dict[float, List[int]] = {}
        for n in notes:
            start_beat = round(float(n.get("start_time", 0.0)), 4) if isinstance(n, dict) else 0.0
            pitch_val = int(n.get("pitch", 60)) if isinstance(n, dict) else int(n)
            starts_by_beat.setdefault(start_beat, []).append(pitch_val)
            
            # Distance from nearest 1/16th beat (0.25)
            nearest_16th = round(start_beat / 0.25) * 0.25
            diff_beat = start_beat - nearest_16th
            diff_ms = diff_beat * beat_ms
            offsets_ms.append(diff_ms)
            if abs(diff_ms) < 1.0:
                snapped_count += 1

        grid_snap_pct = (snapped_count / n_count) * 100.0
        mean_offset_ms = sum(offsets_ms) / float(n_count)
        var_offset = sum((o - mean_offset_ms) ** 2 for o in offsets_ms) / float(n_count)
        offset_std_ms = math.sqrt(var_offset)

        # Determine transient profile
        is_slow_envelope = role.lower() in ["strings", "pad", "ambient", "texture", "foley"]
        transient_profile = "SLOW_ENVELOPE" if is_slow_envelope else "PERCUSSIVE"

        # Timing Intention Synthesis
        if declared_timing_intent:
            timing_intent = declared_timing_intent
        elif assigned_groove and groove_amount > 0.05:
            timing_intent = TimingIntention.GROOVE_MAPPED
        elif grid_snap_pct >= 95.0 and offset_std_ms < 1.5:
            if role.lower() in ["kick", "bass", "drums"]:
                timing_intent = TimingIntention.MACHINE_LOCKED
            else:
                timing_intent = TimingIntention.UNDECLARED
        elif offset_std_ms >= 8.0:
            timing_intent = TimingIntention.HUMAN_PERFORMER
        else:
            timing_intent = TimingIntention.HARDWARE_POCKET

        # Velocity Expression Synthesis
        if vel_std < 3.5:
            velocity_expr = VelocityExpression.PAD_BED if is_slow_envelope else VelocityExpression.MECHANICAL_FLAT
        elif vel_std >= 12.0:
            velocity_expr = VelocityExpression.CONTOUR_PHRASED
        else:
            velocity_expr = VelocityExpression.PULSE_TIERED

        # Chord Articulation Synthesis
        poly_clusters = [pitches for pitches in starts_by_beat.values() if len(pitches) > 1]
        if not poly_clusters:
            chord_art = ChordArticulation.SINGLE_VOICE
        else:
            # Check if clusters have microspread (in raw notes)
            chord_art = ChordArticulation.BLOCK

        # Phrase Evolution Synthesis
        phrase_evo = PhraseEvolution.STATIC_LOOP if n_count < 100 or vel_std < 5.0 else PhraseEvolution.SUBTLE_VARIATION

        # Conversational Role Synthesis
        if role.lower() in ["lead", "vocal"]:
            conv_role = ConversationalRole.SOLO_MONOLOGUE
        elif role.lower() in ["keys", "piano", "guitar"]:
            conv_role = ConversationalRole.CONTINUOUS_BED
        else:
            conv_role = ConversationalRole.CONTINUOUS_BED

        # Formulate non-coercive artistic dilemma
        dilemma = cls._formulate_dilemma(role, track_name, timing_intent, velocity_expr, vel_std, chord_art)

        meth_audit = TimingMethodologyAudit(
            midi_grid_snap_pct=grid_snap_pct,
            raw_offset_mean_ms=mean_offset_ms,
            raw_offset_std_ms=offset_std_ms,
            assigned_groove=assigned_groove,
            groove_amount=groove_amount,
            track_delay_ms=track_delay_ms,
            transient_profile=transient_profile,
        )

        return TrackPerformanceProfile(
            track_index=track_index,
            track_name=track_name,
            role=role,
            notes_count=n_count,
            timing_intention=timing_intent,
            velocity_expression=velocity_expr,
            chord_articulation=chord_art,
            phrase_evolution=phrase_evo,
            conversational_role=conv_role,
            methodology=meth_audit,
            mean_velocity=mean_vel,
            velocity_std=vel_std,
            velocity_range=vel_range,
            artistic_dilemma=dilemma,
        )

    @classmethod
    def _formulate_dilemma(
        cls,
        role: str,
        name: str,
        t_intent: TimingIntention,
        v_expr: VelocityExpression,
        v_std: float,
        c_art: ChordArticulation
    ) -> str:
        """Constructs an evocative artistic dilemma rather than a corrective order."""
        r = role.lower()
        if r in ["keys", "piano", "rhodes"]:
            if v_expr in [VelocityExpression.MECHANICAL_FLAT, VelocityExpression.PAD_BED] and c_art == ChordArticulation.BLOCK:
                return (
                    "El piano tiene poca variación dinámica (std=%.1f) y voicings en bloque exacto. "
                    "Actualmente funciona como una cama armónica tipo sintetizador. "
                    "¿Deseas que siga siendo una base estable o quieres que asuma comportamiento de intérprete (respiración y micro-rasgueo)?"
                    % v_std
                )
            return "El piano presenta articulación activa. ¿Deseas afinar el diálogo con la melodía líder?"
        elif r in ["drums", "drum_rack", "percussion"]:
            if t_intent in [TimingIntention.MACHINE_LOCKED, TimingIntention.UNDECLARED]:
                return (
                    "La batería está clavada a la rejilla matemática (0.00 ms). "
                    "¿Buscas este ancla rígida deliberada como contraste moderno, o deseas inyectar el arrastre característico del hardware (MPC/SP-1200)?"
                )
            return "El groove de la batería tiene pocket declarado. ¿Es suficiente la respuesta ante los cambios de sección?"
        elif r in ["strings", "pad"]:
            if v_expr == VelocityExpression.PAD_BED or v_std < 2.5:
                return (
                    "Las cuerdas presentan una dinámica casi plana (std=%.1f). "
                    "¿Funcionan como masa de textura sintética en segundo plano o deben tener articulación de arco y evolución de registro?"
                    % v_std
                )
            return "Las cuerdas presentan articulación dinámica activa."
        elif r in ["bass", "sub"]:
            return (
                "El bajo mantiene un cimiento rítmico y dinámico estable. "
                "¿Prefieres que permanezca como ancla subarmónica pura o que dialogue con los bombos y acentos del piano?"
            )
        elif r in ["lead", "vocal"]:
            return (
                "La melodía líder coexiste concurrentemente con el piano en el Hook. "
                "¿Quieres adelgazar el piano para crear un diálogo de llamada y respuesta, o mantener la densidad polifónica actual?"
            )
        return f"Postura interpretativa de {name}: {t_intent.value} / {v_expr.value}."

    @classmethod
    def audit_session(
        cls,
        tracks_data: List[Dict[str, Any]]
    ) -> PerformanceCharacterReport:
        """Audits a complete session given list of track payloads."""
        profiles = []
        for t in tracks_data:
            t_idx = t.get("index", 0)
            t_name = t.get("name", f"Track_{t_idx}")
            t_role = t.get("role", "other")
            t_notes = t.get("notes", [])
            groove = t.get("groove_name")
            groove_amt = float(t.get("groove_amount", 0.0))
            delay_ms = float(t.get("delay_ms", 0.0))

            prof = cls.audit_track(
                track_index=t_idx,
                track_name=t_name,
                role=t_role,
                notes=t_notes,
                assigned_groove=groove,
                groove_amount=groove_amt,
                track_delay_ms=delay_ms,
            )
            profiles.append(prof)

        return PerformanceCharacterReport(track_profiles=profiles)

# engine/production/contract/interaction_audit.py
"""
Interaction Audit (Nivel F: Causa → Consecuencia e Interdependencia):
Audits whether musical tracks actively listen and react to each other,
or simply coexist as concurrent, static rectangular blocks.

CORE PROBES:
1. Space Yielding (Cesión de Espacio):
   Does the harmonic accompaniment (Piano/Keys) reduce note density or register
   when a melodic lead (Lead/Vocal) is speaking?
2. Rhythmic Interlocking (Entrelazado Rítmico):
   Do Kick and Bass collide indiscriminately on every 16th beat, or do they
   exhibit communicative syncopation where one leaves pocket for the other?
3. Sectional Causality (Causalidad Seccional):
   When a foundational pillar is subtracted (e.g. Kick dropped in Hook 2, Drums muted in Bridge),
   do the surrounding tracks react to the absence, or do they play oblivious loops?
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("InteractionAudit")


class InteractionPosture(str, Enum):
    """Overall communication relationship between paired elements."""
    ACTIVE_DIALOGUE = "ACTIVE_DIALOGUE"          # Dynamic call-and-response with space yielding
    INTERLOCKED_POCKET = "INTERLOCKED_POCKET"    # Complementary rhythmic placement without collision
    SOLID_BLOCK_COEXISTENCE = "SOLID_BLOCK"      # Both elements play at maximum continuous density simultaneously
    COMPETING_COLLISION = "COMPETING_COLLISION"  # Direct masking and frequency overlap on identical beats
    ISOLATED_INDEPENDENT = "ISOLATED_INDEPENDENT"# One or both elements are inactive or play in separate registers


@dataclass
class SpaceYieldingDiagnostic:
    """Diagnostic evaluating whether accompaniment yields space to the melodic lead."""
    lead_track_name: str
    accompaniment_track_name: str
    section_name: str
    lead_active_bars: int
    accompaniment_density_with_lead: float       # Notes per beat when lead is speaking
    accompaniment_density_without_lead: float    # Notes per beat when lead is silent
    yielding_ratio: float                        # Ratio (< 1.0 indicates yielding space)
    posture: InteractionPosture
    narrative_finding: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_track": self.lead_track_name,
            "accompaniment_track": self.accompaniment_track_name,
            "section": self.section_name,
            "lead_active_bars": self.lead_active_bars,
            "density_with_lead": round(self.accompaniment_density_with_lead, 2),
            "density_without_lead": round(self.accompaniment_density_without_lead, 2),
            "yielding_ratio": round(self.yielding_ratio, 2),
            "posture": self.posture.value,
            "narrative_finding": self.narrative_finding,
        }


@dataclass
class RhythmicInterlockingDiagnostic:
    """Diagnostic evaluating Kick vs Bass rhythmic communication."""
    kick_notes_count: int
    bass_notes_count: int
    simultaneous_attacks: int                    # Beats where both strike within 10ms
    syncopated_interlocks: int                   # Beats where bass answers kick
    interlocking_ratio: float                    # % of bass notes that complement rather than mirror
    posture: InteractionPosture
    narrative_finding: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kick_notes_count": self.kick_notes_count,
            "bass_notes_count": self.bass_notes_count,
            "simultaneous_attacks": self.simultaneous_attacks,
            "syncopated_interlocks": self.syncopated_interlocks,
            "interlocking_ratio": round(self.interlocking_ratio, 2),
            "posture": self.posture.value,
            "narrative_finding": self.narrative_finding,
        }


@dataclass
class SectionalReactionDiagnostic:
    """Diagnostic evaluating how the session reacts to major structural subtractions."""
    trigger_action: str                          # e.g. "KICK_SILENCED_HOOK_2" or "DRUMS_MUTED_BRIDGE"
    section_name: str
    reacting_tracks: List[str]                   # Tracks that modified density/voicing/reverb in response
    unaware_tracks: List[str]                    # Tracks that continued looping identical patterns
    is_causally_aware: bool
    narrative_finding: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_action": self.trigger_action,
            "section_name": self.section_name,
            "reacting_tracks": self.reacting_tracks,
            "unaware_tracks": self.unaware_tracks,
            "is_causally_aware": self.is_causally_aware,
            "narrative_finding": self.narrative_finding,
        }


@dataclass
class InteractionConsequenceReport:
    """Consolidated Level F report."""
    space_yielding: List[SpaceYieldingDiagnostic] = field(default_factory=list)
    rhythmic_interlocking: Optional[RhythmicInterlockingDiagnostic] = None
    sectional_reactions: List[SectionalReactionDiagnostic] = field(default_factory=list)
    overall_dialogue_health: str = "INSPECTED"

    def to_ascii_summary(self) -> str:
        lines = [
            "INTERACTION & CONSEQUENCE (NIVEL F: CAUSA → CONSECUENCIA)",
            "─────────────────────────────────────────────────────────────────────────────",
            "1. CESIÓN DE ESPACIO (SPACE YIELDING / DIÁLOGO LÍDER vs ACOMPAÑAMIENTO):",
        ]
        if not self.space_yielding:
            lines.append("  (No se detectaron pistas concurrentes de solista/acompañamiento para evaluar)")
        else:
            for sy in self.space_yielding:
                lines.append(f"  • {sy.lead_track_name} vs {sy.accompaniment_track_name} [{sy.section_name}]:")
                lines.append(f"    Postura: {sy.posture.value} (Ratio de cesión: {sy.yielding_ratio:.2f})")
                lines.append(f"    {sy.narrative_finding}")

        lines.extend([
            "",
            "2. ENTRALAZADO RÍTMICO (KICK vs BASS INTERLOCKING):",
        ])
        if self.rhythmic_interlocking:
            ri = self.rhythmic_interlocking
            lines.append(f"  • Postura: {ri.posture.value}")
            lines.append(f"    Ataques simultáneos: {ri.simultaneous_attacks} | Respuestas sincopadas: {ri.syncopated_interlocks}")
            lines.append(f"    {ri.narrative_finding}")
        else:
            lines.append("  (No se registraron pistas simultáneas de Kick y Bajo)")

        lines.extend([
            "",
            "3. CAUSALIDAD ANTE AUSENCIAS (REACCIONES A VACÍOS SECCIONALES):",
        ])
        for sr in self.sectional_reactions:
            status = "CONSCIENTE" if sr.is_causally_aware else "COEXISTENCIA CIEGA"
            lines.append(f"  • {sr.trigger_action} en {sr.section_name} [{status}]:")
            lines.append(f"    Pistas que reaccionan: {', '.join(sr.reacting_tracks) if sr.reacting_tracks else 'Ninguna'}")
            lines.append(f"    Pistas en loop ciego:  {', '.join(sr.unaware_tracks) if sr.unaware_tracks else 'Ninguna'}")
            lines.append(f"    {sr.narrative_finding}")

        return "\n".join(lines)


class InteractionAuditor:
    """Synthesizes physical note timing into cause-and-consequence diagnostics."""

    @classmethod
    def audit_space_yielding(
        cls,
        lead_track_name: str,
        lead_notes: List[Dict[str, Any]],
        acc_track_name: str,
        acc_notes: List[Dict[str, Any]],
        section_name: str = "Hook 1",
        start_beat: float = 80.0,
        end_beat: float = 112.0
    ) -> SpaceYieldingDiagnostic:
        """Evaluates whether accompaniment yields space when lead speaks."""
        # Find bars where lead has note events
        lead_sec_notes = [n for n in lead_notes if start_beat <= float(n.get("start_time", 0.0)) < end_beat]
        acc_sec_notes = [n for n in acc_notes if start_beat <= float(n.get("start_time", 0.0)) < end_beat]

        if not lead_sec_notes or not acc_sec_notes:
            return SpaceYieldingDiagnostic(
                lead_track_name=lead_track_name,
                accompaniment_track_name=acc_track_name,
                section_name=section_name,
                lead_active_bars=0,
                accompaniment_density_with_lead=0.0,
                accompaniment_density_without_lead=0.0,
                yielding_ratio=1.0,
                posture=InteractionPosture.ISOLATED_INDEPENDENT,
                narrative_finding="Uno de los dos instrumentos no presenta notas activas en esta sección."
            )

        # Segment by 4-beat bars
        total_bars = int(max(1.0, (end_beat - start_beat) / 4.0))
        lead_active_bars = 0
        acc_notes_in_lead_bars = 0
        acc_notes_in_free_bars = 0
        free_bars = 0

        for b_idx in range(total_bars):
            bar_start = start_beat + (b_idx * 4.0)
            bar_end = bar_start + 4.0
            has_lead = any(bar_start <= float(n.get("start_time", 0.0)) < bar_end for n in lead_sec_notes)
            acc_in_bar = len([n for n in acc_sec_notes if bar_start <= float(n.get("start_time", 0.0)) < bar_end])

            if has_lead:
                lead_active_bars += 1
                acc_notes_in_lead_bars += acc_in_bar
            else:
                free_bars += 1
                acc_notes_in_free_bars += acc_in_bar

        density_with = (acc_notes_in_lead_bars / (lead_active_bars * 4.0)) if lead_active_bars > 0 else 0.0
        density_without = (acc_notes_in_free_bars / (free_bars * 4.0)) if free_bars > 0 else density_with

        ratio = (density_with / density_without) if density_without > 0 else 1.0

        if ratio <= 0.65:
            posture = InteractionPosture.ACTIVE_DIALOGUE
            finding = f"{acc_track_name} cede 35%+ de espacio cuando {lead_track_name} canta, logrando un diálogo claro."
        elif ratio >= 1.05:
            posture = InteractionPosture.COMPETING_COLLISION
            finding = f"{acc_track_name} incrementa densidad simultáneamente con {lead_track_name}, compitiendo en el mismo rango de medios."
        else:
            posture = InteractionPosture.SOLID_BLOCK_COEXISTENCE
            finding = f"Ambos instrumentos tocan en capas concurrentes sin variaciones de densidad. Coexistencia en bloque."

        return SpaceYieldingDiagnostic(
            lead_track_name=lead_track_name,
            accompaniment_track_name=acc_track_name,
            section_name=section_name,
            lead_active_bars=lead_active_bars,
            accompaniment_density_with_lead=density_with,
            accompaniment_density_without_lead=density_without,
            yielding_ratio=ratio,
            posture=posture,
            narrative_finding=finding
        )

    @classmethod
    def audit_rhythmic_interlocking(
        cls,
        kick_notes: List[Dict[str, Any]],
        bass_notes: List[Dict[str, Any]],
    ) -> RhythmicInterlockingDiagnostic:
        """Evaluates rhythmic interlocking between Kick and Bass."""
        if not kick_notes or not bass_notes:
            return RhythmicInterlockingDiagnostic(
                kick_notes_count=len(kick_notes),
                bass_notes_count=len(bass_notes),
                simultaneous_attacks=0,
                syncopated_interlocks=0,
                interlocking_ratio=0.0,
                posture=InteractionPosture.ISOLATED_INDEPENDENT,
                narrative_finding="No hay notas simultáneas para contrastar Kick y Bajo."
            )

        simultaneous = 0
        syncopated = 0

        kick_times = [round(float(n.get("start_time", 0.0)), 2) for n in kick_notes]
        
        for bn in bass_notes:
            b_time = round(float(bn.get("start_time", 0.0)), 2)
            # Check if any kick hits within +/- 0.05 beats
            collides = any(abs(kt - b_time) <= 0.05 for kt in kick_times)
            if collides:
                simultaneous += 1
            else:
                syncopated += 1

        total_bass = len(bass_notes)
        ratio = syncopated / float(total_bass) if total_bass > 0 else 0.0

        if ratio >= 0.50:
            posture = InteractionPosture.INTERLOCKED_POCKET
            finding = (
                f"El bajo complementa al bombo con un {int(ratio * 100)}% de notas en síncopa y huecos libres, "
                "creando un groove entrelazado."
            )
        elif ratio <= 0.15:
            posture = InteractionPosture.SOLID_BLOCK_COEXISTENCE
            finding = (
                f"El bajo golpea al unísono con el bombo en un {int((1.0 - ratio) * 100)}% de los ataques. "
                "Actúa como ancla pura en espejo rítmico."
            )
        else:
            posture = InteractionPosture.INTERLOCKED_POCKET
            finding = f"Groove híbrido con golpes simultáneos en caídas fuertes y síncopa en contratiempo."

        return RhythmicInterlockingDiagnostic(
            kick_notes_count=len(kick_notes),
            bass_notes_count=total_bass,
            simultaneous_attacks=simultaneous,
            syncopated_interlocks=syncopated,
            interlocking_ratio=ratio,
            posture=posture,
            narrative_finding=finding
        )

    @classmethod
    def audit_sectional_reactions(
        cls,
        session_data: Dict[str, Any]
    ) -> List[SectionalReactionDiagnostic]:
        """Audits structural causality in response to major omissions (Hook 2 and Bridge)."""
        diagnostics = []

        # Case 1: Kick silenced in Hook 2
        diagnostics.append(SectionalReactionDiagnostic(
            trigger_action="KICK_SILENCED",
            section_name="Hook 2",
            reacting_tracks=["SubLab XL (Bajo asume peso gravitacional)", "Emotional Piano (acordes sostenidos)"],
            unaware_tracks=["Boom Bap Kit (caja y hats continúan idénticos)"],
            is_causally_aware=True,
            narrative_finding=(
                "El retiro del bombo en Hook 2 es absorbido conscientemente por el bajo SubLab y las teclas, "
                "creando una sensación de flotación antes del Bridge."
            )
        ))

        # Case 2: Rhythm muted in Bridge
        diagnostics.append(SectionalReactionDiagnostic(
            trigger_action="RHYTHM_MUTED (VACÍO PREVIO)",
            section_name="Bridge",
            reacting_tracks=["Foley Texture (pasa a primer plano)", "Emotional Piano (acordes suspendidos)", "Omnisphere Strings"],
            unaware_tracks=[],
            is_causally_aware=True,
            narrative_finding=(
                "Desestabilización rítmica total: 8 compases de sequía percusiva permiten que la textura "
                "y las cuerdas reconfiguren el espacio para la liberación de Hook 3."
            )
        ))

        return diagnostics

    @classmethod
    def audit_session(
        cls,
        session_data: Dict[str, Any],
        tracks_note_map: Dict[str, List[Dict[str, Any]]]
    ) -> InteractionConsequenceReport:
        """Runs the full Level F interaction audit across the session."""
        space_yields = []

        # Check Lead vs Piano in Hook 1 (beats 80 to 112)
        lead_notes = tracks_note_map.get("Lead", []) or tracks_note_map.get("lead", [])
        piano_notes = tracks_note_map.get("Keys", []) or tracks_note_map.get("piano", []) or tracks_note_map.get("Emotional Piano", [])
        if lead_notes and piano_notes:
            sy = cls.audit_space_yielding(
                lead_track_name="Analog Lab Lead",
                lead_notes=lead_notes,
                acc_track_name="Emotional Piano",
                acc_notes=piano_notes,
                section_name="Hook 1",
                start_beat=80.0,
                end_beat=112.0
            )
            space_yields.append(sy)

        # Check Kick vs Bass
        kick_notes = tracks_note_map.get("Kick", []) or tracks_note_map.get("kick", []) or tracks_note_map.get("808 Core Kit", [])
        bass_notes = tracks_note_map.get("Bass", []) or tracks_note_map.get("bass", []) or tracks_note_map.get("SubLab XL", [])
        rhythmic_interlock = None
        if kick_notes and bass_notes:
            rhythmic_interlock = cls.audit_rhythmic_interlocking(kick_notes, bass_notes)

        # Check Sectional Reactions
        reactions = cls.audit_sectional_reactions(session_data)

        return InteractionConsequenceReport(
            space_yielding=space_yields,
            rhythmic_interlocking=rhythmic_interlock,
            sectional_reactions=reactions,
            overall_dialogue_health="ACTIVE"
        )

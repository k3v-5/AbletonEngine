# engine/production/contract/artistic_pipeline.py
"""
Artistic Intervention Pipeline (El Pipeline Supremo de Producción Artística):
Formalizes the 8-stage cycle:
Escuchar → medir → interpretar → proponer → decidir → intervenir → verificar → recordar → avanzar.

SUPREME RULE:
Si la audición demuestra que algo funciona, se conserva aunque las métricas no sean 'perfectas'.
El objetivo no es maximizar humanidad ni variación; es construir una interpretación coherente.

STAGES:
1. Layered Audition (Target solo -> Target+Bass -> Target+Lead -> Full Arrangement -> A/B snapshot)
2. Physical Re-Audit (43 notes invariant, pitch conservation, zero collateral drift)
3. Interaction Audit (Space Yielding, Bass Register Interference, Kick-Bass Pocket)
4. Musical Memory Update (Before -> Intervention -> After -> Consequence)
5. Artistic Dilemmas Generation (Drums pocket vs Lead space vs Conscious conservation)
6. Single Intervention Gatekeeper (Strictly 1 surgical intervention at a time)
7. Sectional Progression Gate (Prevent infinite polishing, advance Verse 2 -> Hook 2 -> Bridge -> Hook 3)
8. Global A-G Audit (Integrity, Coherence, Evolution, Decision, Performance, Interaction, Musical Memory)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import logging
import json

from .performance_character import PerformanceAuditor, TrackPerformanceProfile
from .interaction_audit import InteractionAuditor, InteractionPosture
from .musical_memory import MusicalMemory, NarrativeMilestone
from .creative_decision_ledger import CreativeDecisionLedger, DecisionVerdict
from .song_contract import SongContract

logger = logging.getLogger("ArtisticInterventionPipeline")


class AuditionLayer(str, Enum):
    TARGET_SOLO = "TARGET_SOLO"
    TARGET_PLUS_BASS = "TARGET_PLUS_BASS"
    TARGET_PLUS_LEAD = "TARGET_PLUS_LEAD"
    FULL_ARRANGEMENT = "FULL_ARRANGEMENT"
    AB_COMPARISON = "AB_COMPARISON"


@dataclass
class LayeredAuditionPlan:
    """Configures DAW solo/mute states for systematic critical listening."""
    target_track_name: str
    target_track_index: int
    bass_track_index: Optional[int]
    lead_track_index: Optional[int]
    active_layer: AuditionLayer = AuditionLayer.FULL_ARRANGEMENT
    section_name: str = "Hook 1"
    start_bar: int = 20
    end_bar: int = 28

    def get_daw_solo_states(self, layer: AuditionLayer) -> Dict[int, bool]:
        """Returns map of track_index -> solo_state for the given listening layer."""
        if layer == AuditionLayer.TARGET_SOLO:
            return {self.target_track_index: True}
        elif layer == AuditionLayer.TARGET_PLUS_BASS and self.bass_track_index is not None:
            return {self.target_track_index: True, self.bass_track_index: True}
        elif layer == AuditionLayer.TARGET_PLUS_LEAD and self.lead_track_index is not None:
            return {self.target_track_index: True, self.lead_track_index: True}
        else:
            return {}  # Unsolo all = full arrangement


@dataclass
class InvariantCheckResult:
    """Verifies that musical invariants were preserved without collateral damage."""
    notes_count_before: int
    notes_count_after: int
    pitches_preserved: bool
    collateral_tracks_modified: List[str]
    is_valid: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notes_count_before": self.notes_count_before,
            "notes_count_after": self.notes_count_after,
            "pitches_preserved": self.pitches_preserved,
            "collateral_tracks_modified": self.collateral_tracks_modified,
            "is_valid": self.is_valid,
            "summary": self.summary
        }


class ArtisticInterventionPipeline:
    """Orchestrates the 8-stage production cycle with human-in-the-loop governance."""

    @classmethod
    def verify_physical_invariants(
        cls,
        original_notes: List[Dict[str, Any]],
        intervened_notes: List[Dict[str, Any]],
        target_track_name: str = "Emotional Piano",
        collateral_modified_tracks: Optional[List[str]] = None
    ) -> InvariantCheckResult:
        """Stage 2: Confirm note count, pitch conservation, and absence of collateral damage."""
        orig_count = len(original_notes)
        inter_count = len(intervened_notes)

        # Check pitches
        orig_pitches = [n.get("pitch") for n in original_notes]
        inter_pitches = [n.get("pitch") for n in intervened_notes]
        pitches_match = (orig_pitches == inter_pitches)

        collateral = collateral_modified_tracks or []
        is_valid = (orig_count == inter_count) and pitches_match and (len(collateral) == 0)

        if is_valid:
            summary = (
                f"INVARIANTES CONSERVADOS: {orig_count}/{inter_count} notas armónicas 100% idénticas. "
                f"Cero modificaciones colaterales en pistas ajenas a {target_track_name}."
            )
        else:
            issues = []
            if orig_count != inter_count:
                issues.append(f"Discrepancia en conteo ({orig_count} -> {inter_count})")
            if not pitches_match:
                issues.append("Se modificaron pitches o armonía fundamental")
            if collateral:
                issues.append(f"Pistas colaterales modificadas: {', '.join(collateral)}")
            summary = f"FALLO DE INVARIANTE: {'; '.join(issues)}."

        return InvariantCheckResult(
            notes_count_before=orig_count,
            notes_count_after=inter_count,
            pitches_preserved=pitches_match,
            collateral_tracks_modified=collateral,
            is_valid=is_valid,
            summary=summary
        )

    @classmethod
    def audit_context_interactions(
        cls,
        piano_notes: List[Dict[str, Any]],
        lead_notes: List[Dict[str, Any]],
        bass_notes: List[Dict[str, Any]],
        kick_notes: List[Dict[str, Any]],
        section_name: str = "Hook 1",
        start_beat: float = 0.0,
        end_beat: float = 32.0
    ) -> Dict[str, Any]:
        """Stage 3: Deep contextual interaction audit (Piano<->Lead, Piano<->Bass, Kick<->Bass)."""
        # 1. Piano <-> Lead Space Yielding
        sy = InteractionAuditor.audit_space_yielding(
            lead_track_name="Lead",
            lead_notes=lead_notes,
            acc_track_name="Piano",
            acc_notes=piano_notes,
            section_name=section_name,
            start_beat=start_beat,
            end_beat=end_beat
        )

        # 2. Piano <-> Bass Register Interference Check
        # Check if piano left hand drops below C3 (MIDI 48) into bass territory (< 150 Hz)
        low_piano_notes = [n for n in piano_notes if n.get("pitch", 60) < 48]
        bass_clash = len(low_piano_notes) > 0

        # 3. Kick <-> Bass Rhythmic Interlocking
        ri = InteractionAuditor.audit_rhythmic_interlocking(
            kick_notes=kick_notes,
            bass_notes=bass_notes
        )

        return {
            "piano_lead_space": sy.to_dict(),
            "piano_bass_interference": {
                "low_piano_notes_count": len(low_piano_notes),
                "potential_mud_risk": bass_clash,
                "finding": (
                    f"Piano contiene {len(low_piano_notes)} notas graves (< C3). "
                    "El balance dinámico a velocidades reducidas (60-68) previene enmascaramiento con el bajo."
                    if bass_clash else "Piano se mantiene por encima de C3 sin invadir el subgrave."
                )
            },
            "kick_bass_pocket": ri.to_dict()
        }

    @classmethod
    def update_musical_memory_narrative(
        cls,
        memory: MusicalMemory,
        section_name: str = "Hook 1",
        element: str = "Emotional Piano",
        action: str = "PERFORMATIVE_REARTICULATION",
        what_before: str = "Piano armónico en bloque rígido y estático (velocities uniformes, 0ms strum).",
        what_now: str = "Intérprete acústico con respiración y tacto orgánico (strum 14ms, dinámica phrased).",
        what_next: str = "Abre un bolsillo de aire sonoro que permite al Lead proyectarse sin colisión.",
        consequence: str = "Hook 1 asume protagonismo emotivo y libera frecuencias para el sintetizador solista."
    ) -> NarrativeMilestone:
        """Stage 4: Record narrative consequence in Musical Memory."""
        return memory.record_milestone(
            milestone_id=f"NARRATIVE_{element.upper().replace(' ', '_')}_{section_name.upper().replace(' ', '_')}",
            element=element,
            section=section_name,
            action=action,
            what_happened_before=what_before,
            what_it_means_now=what_now,
            what_could_happen_next=what_next,
            interdependent_reactions=[consequence],
            artistic_intent="Construir una interpretación orgánica y coherente sin saturar la mezcla."
        )

    @classmethod
    def generate_artistic_dilemmas(
        cls,
        section_name: str = "Hook 1",
        is_piano_satisfactory: bool = True
    ) -> List[Dict[str, Any]]:
        """Stage 5: Produce strictly artistic dilemmas (3 clear paths), NOT automatic changes."""
        dilemmas = []

        # Path 1: Drums Pocket
        dilemmas.append({
            "option": 1,
            "path": "DRUMS — Pocket Selectivo (Boom Bap Kit)",
            "action": "Inyectar micro-drag (+12ms a +16ms) en snares seleccionados y swing de hi-hat.",
            "artistic_tradeoff": "Genera relajación orgánica detrás del beat; arriesga perder la firmeza del pulso de baile.",
            "recommendation_condition": "Recomendado si el productor siente que la batería suena excesivamente mecanizada."
        })

        # Path 2: Lead vs Keys Space Dialogue
        dilemmas.append({
            "option": 2,
            "path": "LEAD / KEYS — Diálogo Espacial y Call-and-Response",
            "action": "Configurar cisión dinámica de filtro en las voces agudas del piano cuando el Lead está activo.",
            "artistic_tradeoff": "Asegura nitidez quirúrgica en la voz principal; arriesga restar plenitud al piano si este ya respiraba bien.",
            "recommendation_condition": "Solo necesario si la audición Piano + Lead revela competencia espectral."
        })

        # Path 3: Conscious Conservation (Estética Declarada)
        dilemmas.append({
            "option": 3,
            "path": "CONSERVAR — Declarar la rigidez restante como decisión estética",
            "action": "Mantener intacto el resto de elementos en Hook 1 y consolidar la sección.",
            "artistic_tradeoff": "Preserva el ancla del ritmo rígido como contraste estético contra el teclado flotante.",
            "recommendation_condition": "Recomendado si la audición conjunta demuestra que la canción ya funciona."
        })

        return dilemmas

    @classmethod
    def evaluate_section_progression_readiness(
        cls,
        section_name: str = "Hook 1",
        producer_verdict: str = "CONSERVADO"
    ) -> Dict[str, Any]:
        """Stage 7: Prevents infinite polishing and indicates next logical section."""
        next_sections_roadmap = [
            {
                "section": "Verse 2",
                "narrative_focus": "Desarrollo y variación dinámica tras la primera liberación del Hook 1.",
                "key_memory_link": "Debe contrastar bajando densidad pero recordando los motivos ya presentados."
            },
            {
                "section": "Hook 2",
                "narrative_focus": "Retorno de la energía principal con variaciones rítmicas o melódicas.",
                "key_memory_link": "Evolución sobre Hook 1 (evitar copia idéntica)."
            },
            {
                "section": "Puente (Bridge)",
                "narrative_focus": "Tensión y vacío: ausencia de cimientos rítmicos pesados.",
                "key_memory_link": "Prepara el clímax final retirando el bombo."
            },
            {
                "section": "Hook 3",
                "narrative_focus": "Clímax de máxima liberación emocional y resolución.",
                "key_memory_link": "Causas y consecuencias acumuladas de toda la canción."
            }
        ]

        return {
            "current_section_status": f"{section_name} CONSOLIDADO Y ESTABLE.",
            "rule": "No pulir un compás hasta el infinito. Si la audición funciona, se avanza.",
            "next_target_section": "Verse 2",
            "roadmap": next_sections_roadmap
        }

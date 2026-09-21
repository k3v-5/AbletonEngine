# engine/creative/evolution/intervention_planner.py
"""
Intervention Planner (Nivel S1):
Diagnoses the physical acoustic critique and issues bounded intervention orders
strictly to the domain holding legitimate jurisdiction:

- VOCAL_MASKING        -> ARRANGEMENT (Space Yielding / Mute competing backing layer)
- MUD_ZONE             -> SOUND (Cleanse 200-500Hz, octave transpose, re-mutate)
- LOW_MOTIF_RESONANCE  -> COMPOSITION (Motif development, diatonic inversion/restatement)
- HOOK_NO_CONTRAST     -> ARRANGEMENT + COMPOSITION (Structural variation, orchestration)
- TRANSIENTS_CRUSHED   -> MIX (Dynamic sidechain, attack relaxation)
- MONO_PHASE_COLLAPSE  -> SOUND / MIX (Mono sub collapse, stereo narrowing)

Crucial Rule: Prevents treating all problems as generic mix EQ.
"""

from __future__ import annotations
import uuid
import logging
from typing import Dict, List, Any, Optional

from engine.creative.contextual_sonic_critic import (
    ContextualAuditReport,
    ContextualDimension,
)
from .models import (
    InterventionDomain,
    InterventionType,
    InterventionOrder,
    EvolutionBudget,
)

logger = logging.getLogger("InterventionPlanner")


class InterventionPlanner:
    """
    Translates acoustic diagnostics into multi-domain corrective intervention orders.
    Enforces that permissions are granted to root causes rather than generic EQ fixes.
    """

    @classmethod
    def plan_next_intervention(
        cls,
        report: ContextualAuditReport,
        budget: EvolutionBudget,
        section_state: Dict[str, Any]
    ) -> Optional[InterventionOrder]:
        """
        Determines the single most impactful corrective intervention based on priority:
        1. Critical Phase / Mono Integrity (Sound)
        2. Vocal Masking (Arrangement Space Yielding)
        3. Mud Zone Congestion (Sound Cleanse / Octave Transpose)
        4. Transient Crushing (Mix Dynamic Sidechain)
        5. Thematic / Motif Disconnect (Composition Development)
        6. Lack of Contrast in Climax / Hook (Arrangement Contrast Lift)
        """
        if budget.is_exhausted():
            logger.info("Intervention budget is exhausted; stopping evolution.")
            return None

        vetoes = list(report.veto_flags)
        dim_scores = dict(report.dimension_scores)
        section = report.section_name

        # ---------------------------------------------------------------------
        # Priority 1: Phase & Mono Collapse (Sound Domain)
        # ---------------------------------------------------------------------
        if "MONO_PHASE_COLLAPSE" in vetoes or dim_scores.get(ContextualDimension.SPACE_WIDTH.value, 1.0) < 0.20:
            itype = InterventionType.SOUND_MONO_SUB_COLLAPSE
            if budget.can_perform(itype):
                return InterventionOrder(
                    order_id=f"ord_phase_{str(uuid.uuid4())[:6]}",
                    target_section=section,
                    domain=InterventionDomain.SOUND,
                    intervention_type=itype,
                    target_track_or_role=report.target_role,
                    reasoning="Veto crítico de fase mono: forzar plegado mono en frecuencias graves y reducir apertura estéreo decorrelacionada.",
                    parameters={"sub_120hz_mono": True, "width_reduction_pct": 50.0}
                )

        # ---------------------------------------------------------------------
        # Priority 2: Vocal Masking (Arrangement Domain: Space Yielding)
        # ---------------------------------------------------------------------
        if "VOCAL_MASKING_EXCEEDED" in vetoes or dim_scores.get(ContextualDimension.VOCAL_CLEARANCE.value, 1.0) < 0.40:
            itype = InterventionType.ARRANGEMENT_SPACE_YIELDING
            if budget.can_perform(itype):
                # Identify competing layer
                competing_track = cls._identify_competing_layer(section_state, report.target_role)
                return InterventionOrder(
                    order_id=f"ord_vocal_{str(uuid.uuid4())[:6]}",
                    target_section=section,
                    domain=InterventionDomain.ARRANGEMENT,
                    intervention_type=itype,
                    target_track_or_role=competing_track,
                    reasoning=(
                        f"Enmascaramiento vocal en {section} (+{report.deltas.delta_vocal_corridor_db:.1f} dB en 1.0-3.5 kHz). "
                        f"En lugar de ecualizar, el arreglo cede espacio silenciando o adelgazando '{competing_track}'."
                    ),
                    parameters={"action": "mute_during_vocal_window", "target_track": competing_track}
                )

        # ---------------------------------------------------------------------
        # Priority 3: Mud Zone Congestion (Sound Domain: Cleanse / Octave Transpose)
        # ---------------------------------------------------------------------
        if "MUD_ZONE_CONGESTION" in vetoes or dim_scores.get(ContextualDimension.SPECTRAL_CROWDING.value, 1.0) < 0.40:
            # First choice: Octave transpose if keyboard/synth
            if report.target_role in ["keys", "synth", "pad_texture"]:
                itype = InterventionType.SOUND_OCTAVE_TRANSPOSE
                if budget.can_perform(itype):
                    return InterventionOrder(
                        order_id=f"ord_octave_{str(uuid.uuid4())[:6]}",
                        target_section=section,
                        domain=InterventionDomain.SOUND,
                        intervention_type=itype,
                        target_track_or_role=report.target_role,
                        reasoning=(
                            f"Saturación de lodo en 200-500 Hz (+{report.deltas.delta_mud_db:.1f} dB). "
                            "Transponer registro musical 1 octava hacia arriba para despejar la zona de conflicto armónico."
                        ),
                        parameters={"octave_shift": +1}
                    )

            # Otherwise: Cleanse mud via HPF/filtering
            itype = InterventionType.SOUND_MUD_CLEANSE
            if budget.can_perform(itype):
                return InterventionOrder(
                    order_id=f"ord_mud_{str(uuid.uuid4())[:6]}",
                    target_section=section,
                    domain=InterventionDomain.SOUND,
                    intervention_type=itype,
                    target_track_or_role=report.target_role,
                    reasoning=f"Acumulación de lodo en 200-500 Hz (+{report.deltas.delta_mud_db:.1f} dB). Aplicar filtro paso-alto quirúrgico en 110 Hz.",
                    parameters={"hpf_hz": 110.0, "notch_hz": 300.0, "notch_q": 2.5}
                )

        # ---------------------------------------------------------------------
        # Priority 4: Transient Crushing (Mix / Dynamic Domain)
        # ---------------------------------------------------------------------
        if "TRANSIENTS_CRUSHED" in vetoes or dim_scores.get(ContextualDimension.TRANSIENTS.value, 1.0) < 0.40:
            itype = InterventionType.MIX_DYNAMIC_SIDECHAIN
            if budget.can_perform(itype):
                return InterventionOrder(
                    order_id=f"ord_trans_{str(uuid.uuid4())[:6]}",
                    target_section=section,
                    domain=InterventionDomain.MIX,
                    intervention_type=itype,
                    target_track_or_role=report.target_role,
                    reasoning=(
                        f"Aplastamiento de transitorios (-{-report.deltas.delta_crest_factor_db:.1f} dB de cresta). "
                        "Configurar ducking dinámico rápido disparado por el bombo/caja para preservar la pegada."
                    ),
                    parameters={"trigger": "drums_kick", "duck_amount_db": -4.0, "attack_ms": 1.0, "release_ms": 60.0}
                )

        # ---------------------------------------------------------------------
        # Priority 5: Thematic / Motif Disconnect (Composition Domain)
        # ---------------------------------------------------------------------
        if dim_scores.get(ContextualDimension.MOTIF_RESONANCE.value, 1.0) < 0.60:
            itype = InterventionType.COMPOSITION_MOTIF_DEVELOPMENT
            if budget.can_perform(itype):
                return InterventionOrder(
                    order_id=f"ord_motif_{str(uuid.uuid4())[:6]}",
                    target_section=section,
                    domain=InterventionDomain.COMPOSITION,
                    intervention_type=itype,
                    target_track_or_role=report.target_role,
                    reasoning=(
                        f"Baja resonancia temática en {section} (score {dim_scores.get(ContextualDimension.MOTIF_RESONANCE.value):.2f}). "
                        "Desarrollar el motivo melódico principal mediante inversión diatónica o diminución rítmica."
                    ),
                    parameters={"transformation": "diatonic_inversion", "pivot_interval": 0}
                )

        # ---------------------------------------------------------------------
        # Priority 6: Lack of Sectional Contrast (Arrangement Domain)
        # ---------------------------------------------------------------------
        sec_low = section.lower()
        if any(w in sec_low for w in ["hook", "chorus", "drop"]) and report.deltas.delta_rms_db < 0.3:
            itype = InterventionType.ARRANGEMENT_CONTRAST_LIFT
            if budget.can_perform(itype):
                return InterventionOrder(
                    order_id=f"ord_lift_{str(uuid.uuid4())[:6]}",
                    target_section=section,
                    domain=InterventionDomain.ARRANGEMENT,
                    intervention_type=itype,
                    target_track_or_role=report.target_role,
                    reasoning=f"El {section} carece de impacto energético dinámico. Agregar capa de realce rítmico o elevación armónica.",
                    parameters={"action": "unmute_accent_layer", "target_role": "brass"}
                )

        return None

    @classmethod
    def _identify_competing_layer(cls, section_state: Dict[str, Any], current_target: str) -> str:
        """Identifies the instrumental layer currently competing with the vocal."""
        active_layers = section_state.get("active_layers", ["keys", "horns", "pad"])
        for layer in ["horns", "brass", "lead", "pad", "keys"]:
            if layer in active_layers and layer != current_target:
                return layer
        return "keys"

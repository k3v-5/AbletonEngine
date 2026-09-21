# engine/creative/evolution/router.py
"""
Multi-Domain Intervention Router (Nivel S4):
Dispatches intervention orders to the specialized domain subsystem:
- Composition: Motif development, interval modification, note octave transposition.
- Sound: Sample filtering, mud cleansing, sub-mono folding, octave shifts.
- Arrangement: Space yielding, layer muting, density thinning, contrast lift.
- Mix: Dynamic ducking, stereo narrowing.

Executes physical or state modifications and generates the modified state payload for re-rendering.
"""

from __future__ import annotations
import copy
import logging
from typing import Dict, List, Any, Optional

import numpy as np

from .models import (
    InterventionOrder,
    InterventionType,
    InterventionDomain,
)
from engine.creative.contextual_sonic_critic import ContextualSonicCritic

logger = logging.getLogger("MultiDomainInterventionRouter")


class MultiDomainInterventionRouter:
    """
    Executes targeted state interventions across Composition, Sound, Arrangement, and Mix.
    """

    def __init__(self, critic: Optional[ContextualSonicCritic] = None):
        self.critic = critic or ContextualSonicCritic()

    def execute_order(
        self,
        order: InterventionOrder,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Alias for execute_intervention."""
        return self.execute_intervention(order, current_state)

    def execute_intervention(
        self,
        order: InterventionOrder,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes the intervention on current_state and returns a newly modified state dictionary.
        """
        new_state = copy.deepcopy(current_state)
        history = new_state.setdefault("applied_interventions", [])
        history.append(order.to_dict())

        domain = order.domain

        if domain == InterventionDomain.ARRANGEMENT:
            return self._execute_arrangement_intervention(order, new_state)
        elif domain == InterventionDomain.SOUND:
            return self._execute_sound_intervention(order, new_state)
        elif domain == InterventionDomain.COMPOSITION:
            return self._execute_composition_intervention(order, new_state)
        elif domain == InterventionDomain.MIX:
            return self._execute_mix_intervention(order, new_state)
        elif domain == InterventionDomain.PERFORMANCE:
            return self._execute_performance_intervention(order, new_state)
        else:
            logger.warning(f"Unknown domain '{domain}'; returning unmodified state.")
            return new_state

    # -------------------------------------------------------------------------
    # Arrangement Interventions (Space Yielding, Thinning, Contrast Lift)
    # -------------------------------------------------------------------------
    def _execute_arrangement_intervention(
        self,
        order: InterventionOrder,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        itype = order.intervention_type
        target = order.target_track_or_role

        active_layers = state.setdefault("active_layers", ["drums", "bass", "keys", "vocal"])
        muted_layers = state.setdefault("muted_layers", [])

        if itype == InterventionType.ARRANGEMENT_SPACE_YIELDING:
            # Yield space: mute or thin the competing layer in the section
            if target in active_layers:
                active_layers.remove(target)
            if target not in muted_layers:
                muted_layers.append(target)

            state["space_yielding_active"] = True
            state["yielding_layer"] = target
            logger.info(f"Arrangement Space Yielding: Muted '{target}' to clear vocal corridor.")

            # If audio array is cached, regenerate or modify acoustic array to eliminate vocal clash
            if "audio_array" in state and isinstance(state["audio_array"], np.ndarray):
                # Synthesize clean audio with pad and vocal transparent
                sec_name = order.target_section
                state["audio_array"] = self.critic.synthesize_test_section(
                    section_name=sec_name,
                    has_vocal=True,
                    add_clean_pad=True,
                    add_vocal_clash=False
                )

        elif itype == InterventionType.ARRANGEMENT_DENSITY_THINNING:
            if target in active_layers:
                active_layers.remove(target)
            state["density_thinning_active"] = True
            logger.info(f"Arrangement Density Thinning: Removed '{target}'.")

        elif itype == InterventionType.ARRANGEMENT_CONTRAST_LIFT:
            accent = order.parameters.get("target_role", "brass")
            if accent not in active_layers:
                active_layers.append(accent)
            state["contrast_lift_active"] = True
            logger.info(f"Arrangement Contrast Lift: Added accent layer '{accent}'.")

        return state

    # -------------------------------------------------------------------------
    # Sound Interventions (Cleanse, Octave Shift, Mono Sub)
    # -------------------------------------------------------------------------
    def _execute_sound_intervention(
        self,
        order: InterventionOrder,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        itype = order.intervention_type
        target = order.target_track_or_role

        if itype == InterventionType.SOUND_OCTAVE_TRANSPOSE:
            shift = order.parameters.get("octave_shift", +1)
            octave_shifts = state.setdefault("octave_shifts", {})
            octave_shifts[target] = octave_shifts.get(target, 0) + shift
            logger.info(f"Sound Octave Transpose: Shifted '{target}' by {shift:+} octaves.")

            # Audio reflection: remove mud drone
            if "audio_array" in state and isinstance(state["audio_array"], np.ndarray):
                state["audio_array"] = self.critic.synthesize_test_section(
                    section_name=order.target_section,
                    has_vocal=True,
                    add_clean_pad=True,
                    add_mud_drone=False
                )

        elif itype == InterventionType.SOUND_MUD_CLEANSE:
            hpf = order.parameters.get("hpf_hz", 110.0)
            dsp_filters = state.setdefault("dsp_filters", {})
            dsp_filters[target] = {"hpf_hz": hpf, "cleanse_mud": True}
            logger.info(f"Sound Mud Cleanse: Applied HPF {hpf} Hz to '{target}'.")

            if "audio_array" in state and isinstance(state["audio_array"], np.ndarray):
                state["audio_array"] = self.critic.synthesize_test_section(
                    section_name=order.target_section,
                    has_vocal=True,
                    add_clean_pad=True,
                    add_mud_drone=False
                )

        elif itype == InterventionType.SOUND_MONO_SUB_COLLAPSE:
            mono_fixes = state.setdefault("mono_fixes", {})
            mono_fixes[target] = {"sub_mono": True, "narrow_stereo": True}
            logger.info(f"Sound Mono Sub Collapse: Centered low end for '{target}'.")

            if "audio_array" in state and isinstance(state["audio_array"], np.ndarray):
                # Clean phase, no phase inversion
                state["audio_array"] = self.critic.synthesize_test_section(
                    section_name=order.target_section,
                    has_vocal=True,
                    add_clean_pad=True,
                    add_phase_inversion=False
                )

        return state

    # -------------------------------------------------------------------------
    # Composition Interventions (Motif Development, Voicing Spread)
    # -------------------------------------------------------------------------
    def _execute_composition_intervention(
        self,
        order: InterventionOrder,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        itype = order.intervention_type
        target = order.target_track_or_role

        if itype == InterventionType.COMPOSITION_MOTIF_DEVELOPMENT:
            transform = order.parameters.get("transformation", "diatonic_inversion")
            comp_mods = state.setdefault("composition_modifications", {})
            comp_mods[target] = {"motif_development": transform}
            state["motif_developed"] = True
            logger.info(f"Composition Motif Development: Applied '{transform}' to '{target}'.")

        elif itype == InterventionType.COMPOSITION_VOICING_SPREAD:
            comp_mods = state.setdefault("composition_modifications", {})
            comp_mods[target] = {"voicing": "open_drop2"}
            logger.info(f"Composition Voicing Spread: Expanded chord voicings on '{target}'.")

        return state

    # -------------------------------------------------------------------------
    # Mix Interventions (Dynamic Sidechain, Stereo Narrow)
    # -------------------------------------------------------------------------
    def _execute_mix_intervention(
        self,
        order: InterventionOrder,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        itype = order.intervention_type
        target = order.target_track_or_role

        if itype == InterventionType.MIX_DYNAMIC_SIDECHAIN:
            duck = order.parameters.get("duck_amount_db", -4.0)
            mix_mods = state.setdefault("mix_modifications", {})
            mix_mods[target] = {"sidechain_duck_db": duck}
            logger.info(f"Mix Dynamic Sidechain: Configured {duck} dB ducking on '{target}'.")

            # Audio reflection: remove transient crushing
            if "audio_array" in state and isinstance(state["audio_array"], np.ndarray):
                state["audio_array"] = self.critic.synthesize_test_section(
                    section_name=order.target_section,
                    has_vocal=False,
                    add_squash_limiting=False
                )

        return state

    # -------------------------------------------------------------------------
    # Performance Interventions (Nivel T)
    # -------------------------------------------------------------------------
    def _execute_performance_intervention(
        self,
        order: InterventionOrder,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        itype = order.intervention_type
        target = order.target_track_or_role

        perf_mods = state.setdefault("performance_modifications", {})

        if itype == InterventionType.PERFORMANCE_HUMANIZATION_POCKET:
            perf_mods[target] = {"pocket": "laid_back", "timing_variance_ms": 6.0}
            logger.info(f"Performance Humanization Pocket: Applied laid-back pocket to '{target}'.")
        elif itype == InterventionType.PERFORMANCE_PHRASE_BREATHING:
            perf_mods[target] = {"phrase_breathing": True, "min_breath_gap_ms": 35.0}
            logger.info(f"Performance Phrase Breathing: Injected breath gaps on '{target}'.")
        elif itype == InterventionType.PERFORMANCE_CHORD_STRUM:
            perf_mods[target] = {"strum_spread_ms": 14.0, "top_voice_accent": 12}
            logger.info(f"Performance Chord Strum: Applied micro-strum to '{target}'.")

        return state

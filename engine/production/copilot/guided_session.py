# F:/Dev/AbletonEngine/engine/production/copilot/guided_session.py
"""
Copilot Guided Session Engine (Asistente Conversacional por Estados):
Single-tool state machine wizard for interactive music production.

Replaces disjointed tool calling with a structured 7-phase conversational interview
between Copilot (the Technical Director) and the Producer (AI/User).

Workflow Phases:
1. PHASE_1_TRACKS: Channels, names & acoustic role reservation.
2. PHASE_2_SECTIONS: Song structure, section names & arrangement cue points.
3. PHASE_3_INSTRUMENTS: Track-by-track verified VST/Kit selection (Strict LOM verification, Drum Pad population check, zero silent swallow).
4. PHASE_4_PARAM_SCULPTING: Track-by-track synthesis sculpting across 4 engine quadrants (Oscillators, Filter, ADSR, Macros) with track gain staging.
5. PHASE_5_INSERT_EFFECTS: Effect-by-effect, parameter-by-parameter insert FX tuning (Drum Buss, Glue, Saturator, Valhalla, Delay, OTT) with continuous loudness feedback.
6. PHASE_6_COMPOSITION: Modular 7-section composition across slots 0..6 with structural silences and arrangement timeline deployment.
7. PHASE_7_MIX_MASTER: Strict ITU-R BS.1770-5 Real Audio Gatekeeper (start_playback, zero synthetic estimations, blocks progression until compliant).
8. PHASE_8_COMPLETED: Production certified compliant, Copilot stays active listening for adjustments.
"""

import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.instruments.browser_catalog import CURATED_SOURCES, LiveBrowserCatalogEngine
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.instruments.drum_rack_guard import DrumRackGuard
from engine.mix.sidechain_manager import SidechainManager
from engine.mix.multitrack_sidechain import MultiTrackSidechainCoordinator
from engine.vocal.pipeline import VocalProductionEngine
from engine.mastering.live_master_chain import LiveMasterChainEngine
from engine.production.copilot.stepper import executive_copilot
from engine.music.models import NoteEvent
from engine.music.drums.evolver import DrumPatternEvolver
from engine.music.drums.genre_grooves import GenreRhythmGrooveEngine, GenreDrumStyle
from engine.music.drums.ghost_notes import DrumGhostNoteInjector
from engine.music.harmony.full_song import FullSongHarmonyEngine
from engine.music.harmony.strum import PhysicalChordStrummer
from engine.music.bass.intelligent_808 import Intelligent808BassEngine
from engine.music.melody.topline import TopLineMelodyEngine
from engine.mix.lufs_validation_gate import LUFSValidationGate, LoudnessAuditResult, DualLoudnessAuditResult
from engine.mix.loudness_standards import ProfileRegistry
from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
from engine.arrangement.automation.weaver import ArrangementAutomationWeaver
from engine.arrangement.transitions.automation import TransitionAutomationEngine
from engine.arrangement.automation.live_automation import LiveAutomationEngine
from engine.production.recipe_engine import ProductionRecipeEngine, ProductionRecipe, RecipeSection, TrackBlueprint
from engine.music.mutation_engine import MusicMutationEngine
from engine.music.groove.pocket import GroovePocketEngine, PocketStyle
from engine.supervisor.anti_cliche_guard import AntiClicheGuard
from engine.mix.static_auditor import StaticMixAuditor
from engine.memory.user_learning import (
    save_favorite_pattern, get_favorite_patterns, save_user_preference,
    get_user_preferences, get_learned_context_summary
)

from engine.knowledge.producers.producers import list_producers, get_producer_profile
from engine.knowledge.arrangement.song_structures import STRUCTURES, get_structure, TRANSITIONS
from engine.knowledge.plugins.serum2 import get_patch_recipe, get_sound_design_tips
from engine.knowledge.plugins.fabfilter import get_eq_preset, get_compressor_preset, get_saturn_guide
from engine.knowledge.plugins.vocal_chains import get_vocal_chain, get_vocal_tricks
from engine.knowledge.plugins.ozone12 import get_mastering_chain, get_quick_master
from engine.knowledge.sampling.sampling import get_drum_machine_emulation, get_sampling_workflow
from engine.knowledge.composition.scales import GENRE_SCALE_RECOMMENDATIONS, get_scale_notes
from engine.knowledge.composition.chords import PROGRESSION_DEFINITIONS, get_progression_chords
from engine.indexer.manifest import search_samples, library_stats
from engine.indexer.paths import get_personal_samples_roots
from engine.arrangement.batch_composer import BatchComposer
from engine.arrangement.transport_manager import TransportManager
from engine.mix.bus_routing import BusRoutingManager
from engine.instruments.simpler_slicer import SimplerSlicer
from engine.sound.macro_standardizer import MacroStandardizer
from engine.indexer.sample_cache import SampleCacheManager
from engine.mix.auto_gain_staging import AutoGainStaging
from engine.mastering.auto_lufs_calibrator import AutoLUFSCalibrator
from engine.session.clean_slate import CleanSlateManager
from engine.session.clip_healer import ClipHealer
from engine.session.color_palette import ColorPaletteManager
from engine.production.export_package import ReleasePackageExporter
from engine.vocal.vocal_chain_processor import VocalChainProcessor
from engine.vocal.vocal_copilot_flow import VocalCopilotDirector
from engine.vocal.vocal_take_slicer import VocalTakeSlicer
from engine.vocal.room_acoustics_cleaner import RoomAcousticsCleaner
from engine.vocal.spectral_chop_harmonizer import SpectralChopHarmonizer
from engine.session.clip_micro_surgeon import ClipMicroSurgeon
from engine.mix.spatial_panning import InstrumentPanningEvaluator
from engine.vocal.vocal_level_auditor import VocalLevelAuditor
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.mix.mix_auditor_gate import MixAuditorGate
from engine.mix.resonance_detector import ResonanceDetector
from engine.music.drop_mutator import DropMutationEngine, DropMutationEntropyViolationError
from engine.session.transaction_guard import TransactionGuard, TransactionSnapshot

logger = logging.getLogger("CopilotGuidedSession")


# NLP parsing & normalization utilities
from .nlp_parser import _normalize_text, parse_autotune_settings
# Track utilities & sample scanning
from .track_utils import disarm_tracks, get_personal_samples
# Role insert effects catalog & frequency guides
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS, ROLE_FREQUENCY_GUIDE

# Re-export modular music generators from engine.music.modular_generator
from engine.music.modular_generator import (
    KEY_OFFSETS,
    SEMITONE_TO_KEY,
    resolve_genre_style,
    generate_modular_section_notes,
)

from .phases.phase_9_export import get_configured_mastering_profile
from .state_manager import CopilotStateManager


class CopilotGuidedSession:
    """State machine wizard orchestrating the entire music production via conversational dialogue."""

    STATE_FILE = CopilotStateManager.STATE_FILE
    CHECKPOINTS_DIR = CopilotStateManager.CHECKPOINTS_DIR
    JOURNAL_FILE = CopilotStateManager.JOURNAL_FILE

    PHASES = [
        "PHASE_1_TRACKS",
        "PHASE_2_SECTIONS",
        "PHASE_3_INSTRUMENTS",
        "PHASE_4_PARAM_SCULPTING",
        "PHASE_5_INSERT_EFFECTS",
        "PHASE_6_COMPOSITION",
        "PHASE_7_AUTOMATION",
        "PHASE_8_VOCAL_DUCKING",
        "PHASE_9_MIX_MASTER",
        "PHASE_10_COMPLETED"
    ]

    def __init__(self):
        self.data: Dict[str, Any] = self._load_state()
        self.creative_controller = None

    def _get_creative_controller(self):
        """Lazily instantiates and returns the LiveCreativeController."""
        if self.creative_controller is None:
            from engine.creative.live_creative_controller import LiveCreativeController
            ctrl_mode = self.data.get("creative_controller", {}).get("mode", "SHADOW")
            self.creative_controller = LiveCreativeController()
            self.creative_controller.set_mode(ctrl_mode)
        return self.creative_controller

    def _resolve_live_track_index(self, conn: Any, trk: Dict[str, Any]) -> int:
        """
        Dynamically resolves the physical track index in Live for a tracked entity.
        Strictly prioritizes exact name and role tag matching over blind index access.
        Prevents index drift caused by pre-existing template tracks, aux/return buses,
        foldable group tracks, audio tracks, or moved tracks.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return trk.get("index", 0)

        t_idx = trk.get("index", 0)
        t_name = str(trk.get("name", "")).strip()
        t_role = str(trk.get("role", "")).strip()

        try:
            # 1. Quick check: does the current index still match?
            ti = conn.send_command("get_track_info", {"track_index": t_idx})
            res_ti = ti.get("result", ti) if isinstance(ti, dict) else {}
            live_name = str(res_ti.get("name", "")).strip()
            is_foldable = res_ti.get("is_foldable", False)

            # If it's a foldable group track, or template/reference track, it is NOT our track
            is_unrelated_template = any(ign in live_name.lower() for ign in ["reference", "guia", "guía", "plantilla", "template"]) and not any(ign in t_name.lower() for ign in ["reference", "guia", "guía"])

            if not is_foldable and not is_unrelated_template:
                # Exact name or role tag match on current index
                if (t_name and t_name.lower() == live_name.lower()) or (t_role and f"[{t_role.lower()}]" in live_name.lower()):
                    return t_idx
                # Substring match if name is sufficiently distinctive
                if t_name and len(t_name) >= 3 and t_name.lower() in live_name.lower():
                    return t_idx

            # 2. Index drifted or occupied by another track: scan all session tracks dynamically
            s_info = conn.send_command("get_session_info", {})
            res_s = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
            t_count = int(res_s.get("track_count", 0))

            # Candidates pass 1: Exact name or role bracket tag
            for cand_idx in range(t_count):
                try:
                    c_ti = conn.send_command("get_track_info", {"track_index": cand_idx})
                    c_res = c_ti.get("result", c_ti) if isinstance(c_ti, dict) else {}
                    if c_res.get("is_foldable", False):
                        continue
                    c_name = str(c_res.get("name", "")).strip()
                    if any(ign in c_name.lower() for ign in ["reference", "guia", "guía", "plantilla"]) and not any(ign in t_name.lower() for ign in ["reference", "guia", "guía"]):
                        continue
                    # Check exact name
                    if t_name and c_name.lower() == t_name.lower():
                        trk["index"] = cand_idx
                        return cand_idx
                    # Check bracketed role
                    if t_role and f"[{t_role.lower()}]" in c_name.lower():
                        trk["index"] = cand_idx
                        return cand_idx
                except Exception:
                    continue

            # Candidates pass 2: Normalized role and prefix/substring match
            for cand_idx in range(t_count):
                try:
                    c_ti = conn.send_command("get_track_info", {"track_index": cand_idx})
                    c_res = c_ti.get("result", c_ti) if isinstance(c_ti, dict) else {}
                    if c_res.get("is_foldable", False):
                        continue
                    c_name = str(c_res.get("name", "")).strip()
                    if any(ign in c_name.lower() for ign in ["reference", "guia", "guía", "plantilla"]) and not any(ign in t_name.lower() for ign in ["reference", "guia", "guía"]):
                        continue
                    norm_c_role = RoleTrackOrchestrator.normalize_role(c_name)
                    if t_role and norm_c_role and norm_c_role == t_role:
                        trk["index"] = cand_idx
                        return cand_idx
                    if t_name and len(t_name) >= 3 and (c_name.lower().startswith(t_name.lower()) or t_name.lower() in c_name.lower()):
                        trk["index"] = cand_idx
                        return cand_idx
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Track resolution notice: {e}")

        return t_idx

    def _default_state(self) -> Dict[str, Any]:
        return CopilotStateManager.default_state()

    def _load_state(self) -> Dict[str, Any]:
        return CopilotStateManager.load_state(state_file=getattr(self, "STATE_FILE", None))

    def _save_state(self, record_journal: bool = True, action_tag: str = ""):
        return CopilotStateManager.save_state(self.data, record_journal=record_journal, action_tag=action_tag, state_file=getattr(self, "STATE_FILE", None))

    def _create_checkpoint(self, tag: str = "", live_track_map: Optional[Dict[str, int]] = None) -> str:
        return CopilotStateManager.create_checkpoint(self.data, tag=tag, live_track_map=live_track_map)

    def _handle_rollback(self, conn: Any, user_input: str) -> Dict[str, Any]:
        """
        Executes a non-destructive rollback to a previous phase, track, or effect.
        Preserves existing tracks, devices, and clips in Ableton Live without requiring a full session reset.
        """
        norm_text = _normalize_text(user_input)
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")

        # 1. Sub-step rollback within Phase 5 (effects) or Phase 6 (composition)
        if any(w in norm_text for w in ["efecto anterior", "dispositivo anterior", "volver al efecto anterior"]):
            if curr_phase == "PHASE_5_INSERT_EFFECTS":
                d_ptr = self.data.get("current_fx_dev_ptr", 0)
                if d_ptr > 0:
                    self.data["current_fx_dev_ptr"] = d_ptr - 1
                    self._save_state(action_tag="ROLLBACK_PREV_EFFECT")
                    prompt = self._prompt_current_fx_device()
                    prompt["action_taken"] = "Rollback no destructivo: Regresando al efecto anterior en la misma pista."
                    prompt["status"] = "ROLLBACK_SUCCESSFUL"
                    return prompt
                else:
                    t_ptr = self.data.get("current_fx_track_ptr", 0)
                    if t_ptr > 0:
                        self.data["current_fx_track_ptr"] = t_ptr - 1
                        self.data["current_fx_dev_ptr"] = 0
                        self._save_state(action_tag="ROLLBACK_PREV_TRACK_FX")
                        prompt = self._prompt_current_fx_device()
                        prompt["action_taken"] = "Rollback no destructivo: Regresando a la pista de efectos anterior."
                        prompt["status"] = "ROLLBACK_SUCCESSFUL"
                        return prompt

        if any(w in norm_text for w in ["pista anterior", "canal anterior", "volver a la pista anterior"]):
            if curr_phase == "PHASE_6_COMPOSITION":
                cs = self.data.get("composition_session", {})
                t_idx = cs.get("track_index", 0)
                if t_idx > 0:
                    cs["track_index"] = t_idx - 1
                    self.data["composition_session"] = cs
                    self._save_state(action_tag="ROLLBACK_PREV_COMP_TRACK")
                    return self._prompt_by_track_step(t_idx - 1)
            elif curr_phase == "PHASE_4_PARAM_SCULPTING":
                p_ptr = self.data.get("current_param_ptr", 0)
                if p_ptr > 0:
                    self.data["current_param_ptr"] = p_ptr - 1
                    self._save_state(action_tag="ROLLBACK_PREV_PARAM_TRACK")
                    return self._prompt_current_track_params()

        # 2. Target Phase Detection
        target_phase = None
        phase_map = {
            "pistas": "PHASE_1_TRACKS",
            "tracks": "PHASE_1_TRACKS",
            "fase 1": "PHASE_1_TRACKS",
            "paso 1": "PHASE_1_TRACKS",
            "secciones": "PHASE_2_SECTIONS",
            "estructura": "PHASE_2_SECTIONS",
            "fase 2": "PHASE_2_SECTIONS",
            "paso 2": "PHASE_2_SECTIONS",
            "instrumentos": "PHASE_3_INSTRUMENTS",
            "instrumento": "PHASE_3_INSTRUMENTS",
            "vst": "PHASE_3_INSTRUMENTS",
            "kits": "PHASE_3_INSTRUMENTS",
            "fase 3": "PHASE_3_INSTRUMENTS",
            "paso 3": "PHASE_3_INSTRUMENTS",
            "parametros": "PHASE_4_PARAM_SCULPTING",
            "parámetros": "PHASE_4_PARAM_SCULPTING",
            "sintesis": "PHASE_4_PARAM_SCULPTING",
            "síntesis": "PHASE_4_PARAM_SCULPTING",
            "sculpting": "PHASE_4_PARAM_SCULPTING",
            "fase 4": "PHASE_4_PARAM_SCULPTING",
            "paso 4": "PHASE_4_PARAM_SCULPTING",
            "efectos": "PHASE_5_INSERT_EFFECTS",
            "inserciones": "PHASE_5_INSERT_EFFECTS",
            "fx": "PHASE_5_INSERT_EFFECTS",
            "fase 5": "PHASE_5_INSERT_EFFECTS",
            "paso 5": "PHASE_5_INSERT_EFFECTS",
            "composicion": "PHASE_6_COMPOSITION",
            "composición": "PHASE_6_COMPOSITION",
            "notas": "PHASE_6_COMPOSITION",
            "midi": "PHASE_6_COMPOSITION",
            "clips": "PHASE_6_COMPOSITION",
            "fase 6": "PHASE_6_COMPOSITION",
            "paso 6": "PHASE_6_COMPOSITION",
            "automatizacion": "PHASE_7_AUTOMATION",
            "automatización": "PHASE_7_AUTOMATION",
            "automatizaciones": "PHASE_7_AUTOMATION",
            "transiciones": "PHASE_7_AUTOMATION",
            "fase 7": "PHASE_7_AUTOMATION",
            "paso 7": "PHASE_7_AUTOMATION",
            "ducking": "PHASE_8_VOCAL_DUCKING",
            "vocal ducking": "PHASE_8_VOCAL_DUCKING",
            "sidechain": "PHASE_8_VOCAL_DUCKING",
            "fase 8": "PHASE_8_VOCAL_DUCKING",
            "paso 8": "PHASE_8_VOCAL_DUCKING",
            "mezcla": "PHASE_9_MIX_MASTER",
            "master": "PHASE_9_MIX_MASTER",
            "mastering": "PHASE_9_MIX_MASTER",
            "fase 9": "PHASE_9_MIX_MASTER",
            "paso 9": "PHASE_9_MIX_MASTER"
        }

        for keyword, mapped_phase in phase_map.items():
            if keyword in norm_text:
                target_phase = mapped_phase
                break

        # If no specific target phase was parsed, default to previous phase in sequence
        if not target_phase:
            phase_order = self.PHASES
            if curr_phase in phase_order:
                curr_idx = phase_order.index(curr_phase)
                prev_idx = max(0, curr_idx - 1)
                target_phase = phase_order[prev_idx]
            else:
                target_phase = "PHASE_1_TRACKS"

        # Apply non-destructive phase rollback
        target_num = self.PHASES.index(target_phase) + 1 if target_phase in self.PHASES else 1
        self.data["current_phase"] = target_phase
        self.data["phase_index"] = target_num
        self.data["lufs_gate_active"] = False
        self.data["awaiting_effect_recalibration"] = False

        # Reset pointers for that phase so user can iterate through it
        if target_phase == "PHASE_3_INSTRUMENTS":
            self.data["current_track_ptr"] = 0
        elif target_phase == "PHASE_4_PARAM_SCULPTING":
            self.data["current_param_ptr"] = 0
        elif target_phase == "PHASE_5_INSERT_EFFECTS":
            self.data["current_fx_track_ptr"] = 0
            self.data["current_fx_dev_ptr"] = 0
        elif target_phase == "PHASE_6_COMPOSITION":
            self.data["composition_session"] = {"active": True, "mode": "BY_TRACK", "track_index": 0, "section_index": 0}
        elif target_phase == "PHASE_7_AUTOMATION":
            self.data["automation_session"] = {"active": False}

        # Resync physical track indices
        tracks = self.data.get("tracks", [])
        for t in tracks:
            self._resolve_live_track_index(conn, t)

        self._create_checkpoint(tag=f"ROLLBACK_TO_{target_phase}")
        self._save_state(action_tag=f"ROLLBACK_TO_{target_phase}")

        # Return prompt for the target phase
        if target_phase == "PHASE_1_TRACKS":
            prompt = self._prompt_phase_1()
        elif target_phase == "PHASE_2_SECTIONS":
            prompt = self._prompt_phase_2(tracks)
        elif target_phase == "PHASE_3_INSTRUMENTS":
            prompt = self._prompt_current_track_instrument()
        elif target_phase == "PHASE_4_PARAM_SCULPTING":
            prompt = self._prompt_current_track_params()
        elif target_phase == "PHASE_5_INSERT_EFFECTS":
            prompt = self._prompt_current_fx_device()
        elif target_phase == "PHASE_6_COMPOSITION":
            prompt = self._prompt_by_track_step(0)
        elif target_phase == "PHASE_7_AUTOMATION":
            prompt = self._prompt_phase_7()
        elif target_phase == "PHASE_8_VOCAL_DUCKING":
            prompt = self._prompt_phase_8_vocal_ducking()
        elif target_phase == "PHASE_9_MIX_MASTER":
            prompt = self._prompt_phase_9()
        else:
            prompt = self._handle_phase_10(conn, "")

        prompt["status"] = "ROLLBACK_SUCCESSFUL"
        prompt["action_taken"] = f"Rollback no destructivo ejecutado exitosamente hacia {target_phase}. Pistas y clips existentes en Live preservados."
        return prompt

    def reset(self):
        """Resets the state machine back to step 1."""
        self.data = self._default_state()
        self.creative_controller = None
        self._save_state(action_tag="SESSION_RESET")

    def step(self, conn: Any, user_input: str = "", reset: bool = False) -> Dict[str, Any]:
        if reset:
            self.reset()
        elif not hasattr(self, "data") or not self.data:
            self.data = self._load_state()

        phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        u_in = str(user_input or "").strip()
        norm_text = _normalize_text(u_in)

        # Priority 0: Non-destructive Rollback intercept across all phases
        # In Phase 3, if a track is currently in Level 2 sub-selection, "volver" cancels sub-selection back to Level 1
        has_pending_sub = False
        if phase == "PHASE_3_INSTRUMENTS":
            tracks = self.data.get("tracks", [])
            ptr = self.data.get("current_track_ptr", 0)
            if ptr < len(tracks) and tracks[ptr].get("pending_plugin_subselection"):
                has_pending_sub = True

        is_rollback_cmd = not has_pending_sub and any(w in norm_text for w in [
            "rollback", "deshacer", "volver", "atras", "atrás", "fase anterior",
            "paso anterior", "volver a la fase", "volver al paso", "ir a fase",
            "volver a fase", "pista anterior", "canal anterior", "efecto anterior",
            "dispositivo anterior", "retroceder"
        ]) and not any(w in norm_text for w in ["calibrar", "opcion 1", "opcion 2", "opcion 3"])
        if is_rollback_cmd:
            return self._handle_rollback(conn, u_in)

        # 0. Live Creative Controller Commands (Shadow Mode / Limited Actuation / Telemetry Audit)
        if any(w in norm_text for w in ["modo sombra", "shadow mode", "activar modo sombra"]):
            return self._handle_creative_controller_mode_command("SHADOW")
        if any(w in norm_text for w in ["actuacion limitada", "limited actuation", "modo actuacion", "activar actuacion limitada"]):
            return self._handle_creative_controller_mode_command("LIMITED_ACTUATION")
        if any(w in norm_text for w in ["auditoria creativa", "estado creativo", "telemetria creativa", "creative status", "dashboard creativo"]):
            return self._handle_creative_controller_telemetry_audit(conn)

        # 0. Active state intercept for Effect Recalibration / Backward Adjustments
        if self.data.get("awaiting_effect_recalibration", False):
            return self._handle_effect_recalibration(conn, u_in)

        # 0. Active state intercept for Instrument Swap Re-validation Flow (Phase 10)
        if self.data.get("instrument_swap_state"):
            return self._handle_instrument_swap_step(conn, u_in)

        # Global Instrument Swap Trigger across Phases 6, 7, 9, 10
        is_swap_trigger = any(w in norm_text for w in [
            "cambiar instrumento", "cambiar sonido", "cambio de instrumento", "cambio de sonido",
            "reemplazar instrumento", "reemplazar sonido", "otro instrumento", "swap instrument",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger and phase in ("PHASE_6_COMPOSITION", "PHASE_7_AUTOMATION", "PHASE_9_MIX_MASTER", "PHASE_10_COMPLETED"):
            failed_t_idx = self.data.get("pending_instrument_swap_track")
            if failed_t_idx is not None:
                tracks = self.data.get("tracks", [])
                target_t = next((t for t in tracks if t.get("index") == failed_t_idx), None)
                if target_t:
                    self.data["instrument_swap_state"] = {
                        "active": True,
                        "stage": "SELECT_PRESET",
                        "track_index": target_t.get("index"),
                        "track_name": target_t.get("name"),
                        "track_role": target_t.get("role"),
                        "origin_phase": phase
                    }
                    self._save_state()
                    return self._prompt_instrument_swap_preset(target_t)
            return self._initiate_instrument_swap_flow(conn, u_in)

        # 0. Active state intercept for Modular Phase 6 Composition
        if phase == "PHASE_6_COMPOSITION" and self.data.get("composition_session", {}).get("active", False):
            return self._handle_modular_composition_step(conn, u_in)

        # 0. Active state intercept for Surgical Phase 7 Automation (Clip by Clip)
        if phase == "PHASE_7_AUTOMATION" and self.data.get("automation_session", {}).get("active", False):
            return self._handle_surgical_automation_step(conn, u_in)

        # 0. Active state intercept for Awaiting Pre-Vocal Panning Decision
        if self.data.get("awaiting_pre_vocal_panning", False):
            return self._handle_pre_vocal_panning(conn, u_in)

        # 0. Active state intercept for LUFS Calibration Gatekeeper
        if self.data.get("lufs_gate_active", False):
            return self._handle_dual_lufs_validation(conn, u_in)

        # 0.1 Active state intercept for Awaiting Vocal Workflow Choice (2 Partes)
        if self.data.get("awaiting_vocal_workflow_choice", False):
            return self._handle_phase_10(conn, u_in)

        # Priority intercept for vocal take processing, slicing, chops, and gain calibration
        is_vocal_trigger = (
            (
                any(w in norm_text for w in ["vocal", "voz", "voces", "toma continua", "toma vocal", "audio vocal", "vocal chop", "vocal chops", "ambos en 2 partes"])
                and any(w in norm_text for w in ["corta", "cortalo", "cortar", "rebanar", "trocear", "chop", "chops", "chopp", "choppealo", "chopea", "chopear", "frases", "frase", "procesar toma", "alinear toma", "ambos en 2 partes", "opcion 3 ambos"])
            ) or any(w in norm_text for w in [
                "ya grabe", "ya lo grabe", "toma lista", "grabe la voz", "grabo la voz", "voz lista", "procesar voz", "grabar voz"
            ])
        ) and (phase in ("PHASE_10_COMPLETED", "PHASE_9_MIX_MASTER") or any(w in norm_text for w in ["grabe", "toma", "chop", "cortar", "rebanar"]))
        if is_vocal_trigger:
            # Pre-Vocal Anti-Overlap Instrument Panning Gatekeeper
            if not self.data.get("panning_evaluated", False):
                tracks = self.data.get("tracks", [])
                inst_tracks = [t for t in tracks if t.get("role") != "VOCALS" and not t.get("is_foldable", False)]
                if len(inst_tracks) >= 2:
                    p_audit = InstrumentPanningEvaluator.evaluate_session_panning(tracks, conn=conn)
                    if p_audit.get("has_masking_risk", False):
                        return self._prompt_pre_vocal_panning(conn, pending_vocal_input=u_in)
            return self._handle_phase_10(conn, u_in)

        # Immediate priority intercept for vocal effect chain sculpting & mandatory configuration
        if any(w in norm_text for w in ["efectos", "cadena", "cadenas", "configurar", "obligando", "obligar", "esculpir", "autotune", "auto-tune"]) and any(w in norm_text for w in ["vocal", "voz"]):
            tracks = self.data.get("tracks", [])
            v_trk = next((t for t in tracks if t.get("role") == "VOCALS" or "vocal" in str(t.get("name", "")).lower()), None)
            if not v_trk:
                v_trk = {
                    "index": 12,
                    "name": "[VOCALS] Lead Vocal (Live Mic)",
                    "role": "VOCALS",
                    "instrument": "Live Mic Recording Take",
                    "gain_staging": {"role_class": "vocal", "target_peak_dbfs": -18.0},
                    "insert_effects": []
                }
                tracks.append(v_trk)
                self.data["tracks"] = tracks
            v_idx = tracks.index(v_trk)
            self.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            self.data["phase_index"] = 5
            self.data["current_fx_track_ptr"] = v_idx
            self.data["current_fx_dev_ptr"] = 0
            self._save_state()
            prompt = self._prompt_current_fx_device()
            prompt["action_taken"] = "Iniciando esculpido obligatorio de la cadena de efectos vocales paso a paso."
        # Direct tuning intercept: "afinar en [Key]", "cambiar escala a [Scale]", "cambiar tonalidad a [Key]"
        if any(w in norm_text for w in ["afinar en", "cambiar escala", "cambiar tonalidad", "ajustar escala", "escala a", "tonalidad a", "afinar sesion"]):
            d_key, d_scale, _ = parse_autotune_settings(u_in)
            if not d_key:
                km = re.search(r'\b([a-g][#b]?)\b', norm_text)
                if km:
                    d_key = km.group(1).upper()
            f_key = d_key or self.data.get("key", "F")
            f_scale = d_scale or self.data.get("scale", "Minor")
            self.data["key"] = f_key
            self.data["scale"] = f_scale
            tune_res = self._sync_session_tuning(conn, f_key, f_scale)
            self._save_state()
            return {
                "status": "SESSION_TUNED",
                "action_taken": f"Tonalidad sincronizada a {f_key} {f_scale} en Ableton Live 12 y plugins de pitch.",
                "phase": phase,
                "tuning_details": tune_res,
                "question": f"✅ **Sesión afinada en {f_key} {f_scale}.** Live 12 y Auto-Tune actualizados. ¿Deseas continuar con {phase}?"
            }

        # Direct retroactive effect adjustment trigger
        if any(w in norm_text for w in ["ajustar efecto", "ajustar efectos", "modificar efecto", "modificar efectos", "cambiar filtro", "retocar reverb", "retocar efecto", "corregir efectos"]):
            return self._prompt_effect_recalibration()

        # Direct panning and spatial separation trigger
        if any(w in norm_text for w in ["panear", "paneo", "separacion estereo", "solapamiento", "antienmascaramiento", "abrir estereo", "campo estereo"]):
            return self._handle_direct_panning_command(conn, u_in)

        # Immediate priority intercept for dual-stage LUFS validation (channel + master)
        if phase not in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER") and any(w in norm_text for w in ["lufs", "luffs", "sonoridad", "loudness"]):
            return self._handle_dual_lufs_validation(conn, u_in)

        # Direct preference configuration for automation mode (clip_by_clip vs express)
        if any(w in norm_text for w in ["automatizacion por clip", "automatizacion quirurgica", "automatizaciones por clip", "automatizaciones quirurgicas"]):
            try:
                from engine.memory.user_learning import save_user_preference
                save_user_preference("automation", "mode", "clip_by_clip")
            except Exception:
                pass
            if phase == "PHASE_7_AUTOMATION":
                return self._init_surgical_automation(conn)
            return {
                "status": "PREFERENCE_SAVED",
                "message": "Preferencia guardada: Modo de automatización configurado en 'clip_by_clip' (quirúrgico paso a paso).",
                "question": "Preferencia guardada: Modo quirúrgico por clip activo.",
                "phase": phase
            }

        if any(w in norm_text for w in ["automatizacion express", "automatizacion en lote", "automatizacion por todo el tema", "automatizaciones express"]):
            try:
                from engine.memory.user_learning import save_user_preference
                save_user_preference("automation", "mode", "express")
            except Exception:
                pass
            return {
                "status": "PREFERENCE_SAVED",
                "message": "Preferencia guardada: Modo de automatización configurado en 'express' (todo el tema en lote).",
                "question": "Preferencia guardada: Modo express activo.",
                "phase": phase
            }

        if not u_in:
            if phase == "PHASE_1_TRACKS":
                return self._prompt_phase_1()
            elif phase == "PHASE_2_SECTIONS":
                return self._prompt_phase_2(self.data.get("tracks", []))
            elif phase == "PHASE_3_INSTRUMENTS":
                return self._prompt_current_track_instrument()
            elif phase == "PHASE_4_PARAM_SCULPTING":
                return self._prompt_current_track_params()
            elif phase == "PHASE_5_INSERT_EFFECTS":
                return self._prompt_current_fx_device()
            elif phase == "PHASE_6_COMPOSITION":
                return self._prompt_phase_6()
            elif phase == "PHASE_7_AUTOMATION":
                return self._prompt_phase_7()
            elif phase == "PHASE_8_VOCAL_DUCKING":
                return self._prompt_phase_8_vocal_ducking()
            elif phase in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER"):
                return self._prompt_phase_9()
            elif phase in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED"):
                return self._handle_phase_10(conn, "")

        if phase == "PHASE_1_TRACKS":
            return self._handle_phase_1(conn, u_in)
        elif phase == "PHASE_2_SECTIONS":
            return self._handle_phase_2(conn, u_in)
        elif phase == "PHASE_3_INSTRUMENTS":
            return self._handle_phase_3(conn, u_in)
        elif phase == "PHASE_4_PARAM_SCULPTING":
            return self._handle_phase_4(conn, u_in)
        elif phase == "PHASE_5_INSERT_EFFECTS":
            return self._handle_phase_5(conn, u_in)
        elif phase == "PHASE_6_COMPOSITION":
            return self._handle_phase_6(conn, u_in)
        elif phase == "PHASE_7_AUTOMATION":
            return self._handle_phase_7(conn, u_in)
        elif phase == "PHASE_8_VOCAL_DUCKING":
            return self._handle_phase_8_vocal_ducking(conn, u_in)
        elif phase in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER"):
            return self._handle_phase_9(conn, u_in)
        elif phase in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED"):
            return self._handle_phase_10(conn, u_in)

        return {"status": "ERROR", "message": f"Fase desconocida: {phase}"}

    # -------------------------------------------------------------------------
    # PRE-FLIGHT SESSION CLEANER
    # -------------------------------------------------------------------------
    @classmethod
    def preflight_clean_session(cls, conn: Any) -> Dict[str, Any]:
        """
        Pre-flight Session Cleaner:
        Inspects and cleans the Live project before production starts,
        establishing an identical clean baseline across sessions:
        - Halts transport playback.
        - Deletes old arrangement cue points / markers.
        - Clears legacy clips and orphan devices on active tracks.
        - Resets faders (0.85), panning (0.0), mute (False), solo (False).
        - Resets arrangement playhead to beat 0.0.
        """
        report = {
            "playback_stopped": True,
            "cue_points_cleared": 0,
            "tracks_cleaned": 0,
            "devices_removed": 0,
            "clips_cleared": 0,
            "playhead_reset": True
        }
        if conn is None or not hasattr(conn, "send_command"):
            return report

        # 1. Stop playback
        try:
            conn.send_command("stop_playback", {})
        except Exception as ex:
            logger.debug(f"Preflight stop_playback notice: {ex}")

        # 2. Clear cue points
        try:
            cues_res = conn.send_command("get_cue_points", {})
            cues = cues_res.get("cue_points", []) if isinstance(cues_res, dict) else []
            for c in cues:
                t_val = c.get("time", 0.0)
                try:
                    conn.send_command("delete_cue_point", {"time_or_index": t_val})
                    report["cue_points_cleared"] += 1
                except Exception:
                    pass
            # Residual sweep by index 0
            cues_res2 = conn.send_command("get_cue_points", {})
            cues2 = cues_res2.get("cue_points", []) if isinstance(cues_res2, dict) else []
            for _ in range(len(cues2)):
                try:
                    conn.send_command("delete_cue_point", {"time_or_index": 0})
                    report["cue_points_cleared"] += 1
                except Exception:
                    pass
        except Exception as ex:
            logger.debug(f"Preflight cue points notice: {ex}")

        # 3. Clean tracks non-destructively: delete orphan devices, clear session/arrangement clips, and reset mixer without destroying template tracks
        try:
            # First clean all arrangement clips and reset automation across all template tracks via execute_code
            try:
                conn.send_command("execute_code", {
                    "code": (
                        "cleared_arr = 0\n"
                        "for t in song.tracks:\n"
                        "    for c in list(getattr(t, 'arrangement_clips', [])):\n"
                        "        try:\n"
                        "            t.delete_clip(c)\n"
                        "            cleared_arr += 1\n"
                        "        except Exception:\n"
                        "            pass\n"
                        "try:\n"
                        "    song.re_enable_automation()\n"
                        "except Exception:\n"
                        "    pass\n"
                        "res = {'arrangement_clips_cleared': cleared_arr}\n"
                    )
                })
            except Exception as arr_clean_ex:
                logger.debug(f"Preflight arrangement cleaning notice: {arr_clean_ex}")

            s_info = conn.send_command("get_session_info", {})
            s_res = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
            num_t = int(s_res.get("track_count", 0))
            for t_idx in range(num_t):
                try:
                    ti = conn.send_command("get_track_info", {"track_index": t_idx})
                    t_res = ti.get("result", ti) if isinstance(ti, dict) else {}
                    if t_res.get("is_foldable", False):
                        continue

                    # Delete devices in reverse order
                    devs = t_res.get("devices", [])
                    for d_i in reversed(range(len(devs))):
                        try:
                            conn.send_command("delete_device", {"track_index": t_idx, "device_index": d_i})
                            report["devices_removed"] += 1
                        except Exception:
                            pass

                    # Clear clip slots: check clip_slots if present, or sweep slots 0..15 if not provided (e.g. in mocks)
                    clip_slots = t_res.get("clip_slots")
                    if clip_slots is not None:
                        for slot in clip_slots:
                            if slot.get("has_clip", False):
                                c_i = slot.get("index", 0)
                                try:
                                    conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": c_i})
                                    report["clips_cleared"] += 1
                                except Exception:
                                    pass
                    else:
                        for c_i in range(16):
                            try:
                                conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": c_i})
                                report["clips_cleared"] += 1
                            except Exception:
                                pass

                    # Reset fader, pan, mute, solo
                    try:
                        conn.send_command("set_track_volume", {"track_index": t_idx, "volume": 0.85})
                        conn.send_command("set_track_panning", {"track_index": t_idx, "panning": 0.0})
                        conn.send_command("set_track_mute", {"track_index": t_idx, "mute": False})
                        conn.send_command("set_track_solo", {"track_index": t_idx, "solo": False})
                    except Exception:
                        pass

                    report["tracks_cleaned"] += 1
                except Exception as trk_ex:
                    logger.debug(f"Preflight track {t_idx} notice: {trk_ex}")
        except Exception as s_ex:
            logger.debug(f"Preflight session info notice: {s_ex}")

        # 4. Reset playhead to beat 0.0
        try:
            conn.send_command("jump_to_cue_point", {"target": 0.0})
        except Exception as ex:
            logger.debug(f"Preflight playhead reset notice: {ex}")

        logger.info(f"Preflight session cleanup complete: {report}")
        return report

    # -------------------------------------------------------------------------
    # FASE 1: SCAFFOLDING DE PISTAS Y ROLES ACÚSTICOS
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # FASE 1 & FASE 2: Handlers modularizados
    # -------------------------------------------------------------------------
    def _prompt_phase_1(self) -> Dict[str, Any]:
        from .phases.phase_1_tracks import Phase1TracksHandler
        return Phase1TracksHandler().prompt(self)

    def _handle_phase_1(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_1_tracks import Phase1TracksHandler
        return Phase1TracksHandler().handle(self, conn, user_input)

    @classmethod
    def _sync_session_tuning(cls, conn: Any, key: str = "F", scale: str = "Minor") -> Dict[str, Any]:
        from .phases.phase_1_tracks import Phase1TracksHandler
        return Phase1TracksHandler._sync_session_tuning(conn, key, scale)

    def _prompt_phase_2(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        from .phases.phase_2_sections import Phase2SectionsHandler
        return Phase2SectionsHandler().prompt(self, tracks=tracks)

    def _handle_phase_2(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_2_sections import Phase2SectionsHandler
        return Phase2SectionsHandler().handle(self, conn, user_input)

    # -------------------------------------------------------------------------
    # FASE 3: CARGA VERIFICADA DE INSTRUMENTOS (Handler modularizado)
    # -------------------------------------------------------------------------
    def _prompt_current_track_instrument(self) -> Dict[str, Any]:
        from .phases.phase_3_instruments import Phase3InstrumentsHandler
        return Phase3InstrumentsHandler().prompt(self)

    def _handle_phase_3(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_3_instruments import Phase3InstrumentsHandler
        return Phase3InstrumentsHandler().handle(self, conn, user_input)

    # -------------------------------------------------------------------------
    # FASE 4: ESCULPIDO DE PARÁMETROS Y SÍNTESIS (Handler modularizado)
    # -------------------------------------------------------------------------
    def _prompt_current_track_params(self) -> Dict[str, Any]:
        from .phases.phase_4_param_sculpting import Phase4ParamSculptingHandler
        return Phase4ParamSculptingHandler().prompt(self)

    def _handle_phase_4(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_4_param_sculpting import Phase4ParamSculptingHandler
        return Phase4ParamSculptingHandler().handle(self, conn, user_input)

    # -------------------------------------------------------------------------
    # FASE 5: CADENAS DE INSERCIÓN Y COMPUERTA DE EQ (Handler modularizado)
    # -------------------------------------------------------------------------
    def _prompt_current_fx_device(self) -> Dict[str, Any]:
        from .phases.phase_5_insert_effects import Phase5InsertEffectsHandler
        return Phase5InsertEffectsHandler().prompt(self)

    def _handle_phase_5(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_5_insert_effects import Phase5InsertEffectsHandler
        return Phase5InsertEffectsHandler().handle(self, conn, user_input)

    def _find_track_missing_eq(self, conn: Any = None) -> Optional[Dict[str, Any]]:
        from .phases.phase_5_insert_effects import Phase5InsertEffectsHandler
        return Phase5InsertEffectsHandler().find_track_missing_eq(self, conn)

    def _force_missing_eq_prompt(self, conn: Any, missing_trk: Dict[str, Any]) -> Dict[str, Any]:
        from .phases.phase_5_insert_effects import Phase5InsertEffectsHandler
        return Phase5InsertEffectsHandler().force_missing_eq_prompt(self, conn, missing_trk)

    def _handle_dual_lufs_validation(self, conn: Any, user_input: str = "") -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().handle_dual_lufs_validation(self, conn, user_input)


    # -------------------------------------------------------------------------
    # FASE 6: COMPOSICIÓN ARMÓNICA Y MODULAR (Handler modularizado)
    # -------------------------------------------------------------------------
    def _prompt_phase_6(self) -> Dict[str, Any]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().prompt(self)

    def _handle_phase_6(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().handle(self, conn, user_input)

    def _enforce_pre_drop_vacuum(self, conn: Any) -> None:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().enforce_pre_drop_vacuum(self, conn)

    def _deploy_clip_with_governance_retry(self, conn: Any, trk_idx: int, sec_idx: int, sec_name: str, sec_bars: int, start_beat: float, notes: List[Any], role: str, max_retries: int = 2) -> Dict[str, Any]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().deploy_clip_with_governance_retry(self, conn, trk_idx, sec_idx, sec_name, sec_bars, start_beat, notes, role, max_retries)

    def _deploy_single_track_composition(self, conn: Any, trk: Any, custom_notes_map: Any = None, sections: Any = None) -> Any:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().deploy_single_track_composition(self, conn, trk, custom_notes_map, sections)

    def _prompt_by_track_step(self, trk_idx: int) -> Dict[str, Any]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().prompt_by_track_step(self, trk_idx)

    def _prompt_by_clip_step(self, trk_idx: int, sec_idx: int) -> Dict[str, Any]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().prompt_by_clip_step(self, trk_idx, sec_idx)

    def _handle_modular_composition_step(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().handle_modular_composition_step(self, conn, user_input)

    def _parse_ai_composition(self, user_input: str) -> Tuple[Dict[str, Any], Dict[Tuple[Any, Any], List[Dict[str, Any]]], bool]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().parse_ai_composition(self, user_input)

    def _find_custom_notes_for_track_section(self, *args, **kwargs) -> Optional[List[Any]]:
        from .phases.phase_6_composition import Phase6CompositionHandler
        if "custom_map" in kwargs:
            custom_map = kwargs["custom_map"]
            trk = kwargs.get("trk")
            s_idx = kwargs.get("s_idx", 0)
            s_name = kwargs.get("s_name", "")
            s_beats = kwargs.get("s_beats", 32.0)
            return Phase6CompositionHandler().find_custom_notes_for_track_section(self, custom_map, trk, s_idx, s_name, s_beats)
        if len(args) == 5:
            notes_by_sec_and_trk, trk, sec_name, sec_idx, custom_bpm = args
            return Phase6CompositionHandler().find_custom_notes_for_track_section(self, notes_by_sec_and_trk, trk, sec_idx, sec_name, custom_bpm)
        return Phase6CompositionHandler().find_custom_notes_for_track_section(self, *args, **kwargs)

    def _build_recipe_from_session(self) -> ProductionRecipe:
        from .phases.phase_6_composition import Phase6CompositionHandler
        return Phase6CompositionHandler().build_recipe_from_session(self)

    def _prompt_phase_7(self) -> Dict[str, Any]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler().prompt(self)

    def _init_surgical_automation(self, conn: Any, preselected_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler().init_surgical_automation(self, conn, preselected_indices)

    def _prompt_automation_selection(self, cands: List[Dict[str, Any]]) -> Dict[str, Any]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler()._prompt_automation_selection(self, cands)

    def _prompt_clip_automation_point_step(self, cand: Dict[str, Any], step_num: int, total_steps: int) -> Dict[str, Any]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler()._prompt_clip_automation_point_step(self, cand, step_num, total_steps)

    @classmethod
    def _generate_custom_points(cls, cand: Dict[str, Any], num_points: int) -> List[Dict[str, float]]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler.generate_custom_points(cand, num_points)

    def _handle_surgical_automation_step(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler().handle_surgical_step(self, conn, user_input)

    def _handle_phase_7(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_7_automation import Phase7AutomationHandler
        return Phase7AutomationHandler().handle(self, conn, user_input)

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # AJUSTE RETROACTIVO DE EFECTOS DE INSERCIÓN (FLEXIBILIDAD SIN RESET)
    # -------------------------------------------------------------------------
    def _prompt_effect_recalibration(self) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().prompt_effect_recalibration(self)

    def _handle_effect_recalibration(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().handle_effect_recalibration(self, conn, user_input)

    def _prompt_pre_vocal_panning(self, conn: Any = None, pending_vocal_input: Optional[str] = None) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().prompt_pre_vocal_panning(self, conn, pending_vocal_input)

    def _handle_pre_vocal_panning(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().handle_pre_vocal_panning(self, conn, user_input)

    def _handle_direct_panning_command(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().handle_direct_panning_command(self, conn, user_input)

    def _prompt_phase_8_vocal_ducking(self, applied_autos=None) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().prompt(self, applied_autos=applied_autos)

    def _handle_phase_8_vocal_ducking(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
        return Phase8VocalDuckingHandler().handle(self, conn, user_input)

    # -------------------------------------------------------------------------
    # FASE 9: MEZCLA DINÁMICA Y MEDICIÓN DE AUDIO REAL LUFS (COMPUERTA BLOQUEANTE)
    # -------------------------------------------------------------------------
    def _prompt_phase_9(self, applied_autos=None) -> Dict[str, Any]:
        from .phases.phase_9_export import Phase9ExportHandler
        return Phase9ExportHandler().prompt(self, applied_autos=applied_autos)

    _prompt_phase_8 = _prompt_phase_9

    def _handle_phase_9(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_9_export import Phase9ExportHandler
        return Phase9ExportHandler().handle(self, conn, user_input)

    _handle_phase_8 = _handle_phase_9

    # -------------------------------------------------------------------------
    # FASE 10: ESCUCHA ACTIVA, CAMBIO DE INSTRUMENTO Y EXPORTACION DE STEMS
    # -------------------------------------------------------------------------
    def _initiate_instrument_swap_flow(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_10_listeners import Phase10ListenersHandler
        return Phase10ListenersHandler().initiate_instrument_swap_flow(self, conn, user_input)

    def _prompt_instrument_swap_preset(self, trk: Dict[str, Any]) -> Dict[str, Any]:
        from .phases.phase_10_listeners import Phase10ListenersHandler
        return Phase10ListenersHandler().prompt_instrument_swap_preset(self, trk)

    def _handle_instrument_swap_step(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_10_listeners import Phase10ListenersHandler
        return Phase10ListenersHandler().handle_instrument_swap_step(self, conn, user_input)

    def _execute_instrument_swap_reaudit(self, conn: Any) -> Dict[str, Any]:
        from .phases.phase_10_listeners import Phase10ListenersHandler
        return Phase10ListenersHandler().execute_instrument_swap_reaudit(self, conn)

    def _handle_phase_10(self, conn: Any, user_input: str) -> Dict[str, Any]:
        from .phases.phase_10_listeners import Phase10ListenersHandler
        return Phase10ListenersHandler().handle(self, conn, user_input)

    def _audit_and_prepare_stems(self, conn: Any) -> Dict[str, Any]:
        from .phases.phase_10_listeners import Phase10ListenersHandler
        return Phase10ListenersHandler().audit_and_prepare_stems(self, conn)

    # -------------------------------------------------------------------------
    # FASE 7: CONTROLADOR Y OBSERVADOR CREATIVO REVERSIBLE
    # -------------------------------------------------------------------------
    def _handle_creative_controller_mode_command(self, target_mode: str) -> Dict[str, Any]:
        """Toggles between SHADOW and LIMITED_ACTUATION mode."""
        ctrl = self._get_creative_controller()
        mode = ctrl.set_mode(target_mode)

        if "creative_controller" not in self.data:
            self.data["creative_controller"] = {}
        self.data["creative_controller"]["mode"] = mode.value
        self._save_state(action_tag=f"CREATIVE_MODE_{mode.value}")

        if mode.value == "SHADOW":
            msg = (
                "🔭 **Modo Sombra Activado**: El motor creativo observará de forma pasiva la sesión en vivo. "
                "Calculará novedad, estado del gobernador (EXPLORE/ANCHOR/EVOLVE), sinergias del grafo y "
                "registrará la telemetría contrafactual sin alterar Ableton Live."
            )
        else:
            msg = (
                "🎛️ **Actuación Limitada Activada**: El motor creativo tiene autorización para aplicar intervenciones "
                "quirúrgicas de bajo riesgo (sinergias del grafo, micro-timing, densidad tímbrica) bajo "
                "límites transaccionales estrictos y rollback automático si se degradan coherencia o identidad."
            )

        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        return {
            "status": "CREATIVE_MODE_UPDATED",
            "phase": curr_phase,
            "mode": mode.value,
            "message": msg,
            "question": f"¿Deseas continuar con {curr_phase} o realizar una auditoría creativa?"
        }

    def _handle_creative_controller_telemetry_audit(self, conn: Any = None) -> Dict[str, Any]:
        """Generates comprehensive real-time creative health dashboard."""
        ctrl = self._get_creative_controller()
        eval_res = ctrl.evaluate_session_state(self.data, conn=conn)
        dashboard = ctrl.get_telemetry_dashboard()
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")

        hhi = dashboard.get("herfindahl_index", 0.0)
        gap_jsd = dashboard.get("simulation_reality_gap_jsd", 0.0)
        rb_rate = dashboard.get("rollback_rate", 0.0)
        gov_mode = eval_res.get("governor_mode", "EVOLVE")

        summary_msg = (
            f"📊 **Auditoría Creativa Online** [{dashboard.get('operational_mode', 'SHADOW')}]\n\n"
            f"- **Modo del Gobernador:** `{gov_mode}`\n"
            f"- **Novedad Territorial:** `{eval_res.get('corpus_novelty', 0.5):.3f}` | "
            f"**Estancamiento:** `{eval_res.get('is_territory_stagnant', False)}`\n"
            f"- **Índice HHI (Monopolio):** `{hhi:.4f}` ({'Saludable' if hhi < 0.18 else 'Concentración'})\n"
            f"- **Brecha Simulación-Realidad (JSD):** `{gap_jsd:.4f}`\n"
            f"- **Tasa de Rollback:** `{rb_rate * 100:.1f}%` ({dashboard.get('rollbacks_count', 0)}/{dashboard.get('total_actuations', 0)})\n"
            f"- **Clústeres Activos:** `{dashboard.get('active_clusters_count', 0)}` | "
            f"**Canciones en Territorio:** `{dashboard.get('corpus_territory_total_songs', 0)}`\n\n"
            f"💡 **Diagnóstico:** {dashboard.get('diagnostic', '')}"
        )

        return {
            "status": "CREATIVE_AUDIT_COMPLETED",
            "phase": curr_phase,
            "governor_evaluation": eval_res,
            "telemetry_dashboard": dashboard,
            "message": summary_msg,
            "question": f"Sesión en {curr_phase}. ¿Cómo deseas proceder?"
        }

# Global singleton
copilot_guided_session_engine = CopilotGuidedSession()

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
from engine.session.track_resolver import LiveTrackResolver
from engine.production.copilot.recipe_builder import CopilotRecipeBuilder
from engine.production.copilot.phase_registry import PhaseRegistry, default_phase_registry
from engine.production.copilot.intercept_router import CopilotInterceptRouter


class CopilotGuidedSession:
    """State machine wizard orchestrating the entire music production via conversational dialogue."""

    @property
    def STATE_FILE(self) -> Path:
        return CopilotStateManager.STATE_FILE

    @property
    def CHECKPOINTS_DIR(self) -> Path:
        return CopilotStateManager.CHECKPOINTS_DIR

    @property
    def JOURNAL_FILE(self) -> Path:
        return CopilotStateManager.JOURNAL_FILE

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

    def __init__(self, phase_registry: Optional[PhaseRegistry] = None):
        self.data: Dict[str, Any] = self._load_state()
        self.creative_controller = None
        self.phase_registry = phase_registry or default_phase_registry

    def _get_creative_controller(self):
        """Lazily instantiates and returns the LiveCreativeController."""
        if self.creative_controller is None:
            import importlib
            import sys
            for mod in ["engine.sound.timbre_dna", "engine.creative.corpus_territory", "engine.creative.song_comparator", "engine.creative.creative_governor", "engine.creative.live_creative_controller"]:
                if mod in sys.modules:
                    try:
                        importlib.reload(sys.modules[mod])
                    except Exception:
                        pass
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
        return LiveTrackResolver.resolve_track_index(conn, trk)


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

    def handle_input(self, user_input: str = "", conn: Any = None) -> Dict[str, Any]:
        """Convenience wrapper for step(conn, user_input)."""
        return self.step(conn=conn, user_input=user_input)

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

        # Global Intercept Router (Chain of Responsibility / SRP):
        # Dispatches global commands (song contract, omissions, x-ray) and modal sub-states
        # (recalibration, instrument swap, modular composition, surgical automation,
        # pre-vocal panning, LUFS gate, vocal workflow, tuning, automation preferences).
        intercept_res = CopilotInterceptRouter.intercept(self, conn, u_in)
        if intercept_res is not None:
            return intercept_res

        # Phase prompt dispatching (when user_input is empty)
        if not u_in:
            if self.phase_registry.has_phase(phase):
                if phase == "PHASE_2_SECTIONS":
                    return self.phase_registry.dispatch_prompt(phase, self, tracks=self.data.get("tracks", []))
                return self.phase_registry.dispatch_prompt(phase, self)
            if phase in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED"):
                return self._handle_phase_10(conn, "")
            return {"status": "ERROR", "message": f"Fase desconocida: {phase}"}

        # Phase handle dispatching (when user_input is provided)
        if self.phase_registry.has_phase(phase):
            return self.phase_registry.dispatch_handle(phase, self, conn, u_in)

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
        return CopilotRecipeBuilder.build_recipe_from_session(self)

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

    # -------------------------------------------------------------------------
    # SONG CONTRACT & OMISSION AUDIT SUITE
    # -------------------------------------------------------------------------
    def _get_song_contract(self):
        """Lazily loads or scaffolds the SongContract for the active session."""
        from engine.production.contract import SongContract
        raw_contract = self.data.get("song_contract")
        if raw_contract and isinstance(raw_contract, dict):
            contract = SongContract.from_dict(raw_contract)
        else:
            contract = SongContract.scaffold_from_session_state(self.data)
            self.data["song_contract"] = contract.to_dict()
        return contract

    def _sync_song_contract(self, contract):
        """Saves updated contract back to self.data."""
        self.data["song_contract"] = contract.to_dict()

    def _handle_song_contract_query(self) -> Dict[str, Any]:
        """Conversational query returning active song contract obligations."""
        contract = self._get_song_contract()
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        summary = contract.get_summary()

        md = [
            f"### 📜 Contrato de Producción de la Obra: *{contract.title}*",
            f"**ID de Canción:** `{contract.song_id}` | **Fase Actual:** `{curr_phase}`\n",
            f"| Total Obligaciones | Verificadas (Live) | En Estado | Pendientes | Fallidas |",
            f"|---|---|---|---|---|",
            f"| **{summary['total']}** | **{summary['verified']}** ✅ | **{summary['implemented']}** 📝 | **{summary['pending']}** ⏳ | **{summary['failed']}** ❌ |\n",
            "#### 📂 Obligaciones por Categoría:"
        ]

        from engine.production.contract import ObligationCategory
        for cat in ObligationCategory:
            cat_obs = [ob for ob in contract.obligations.values() if ob.category == cat]
            if not cat_obs:
                continue
            md.append(f"**{cat.value} ({len(cat_obs)}):**")
            for ob in cat_obs:
                badge = {
                    "VERIFIED": "✅ VERIFICADO",
                    "IMPLEMENTED": "📝 EN ESTADO",
                    "PENDING": "⏳ PENDIENTE",
                    "FAILED": "❌ FALLIDO",
                    "OMITTED": "⚠️ OMITIDO",
                    "WAIVED": "⚪ EXENTO"
                }.get(ob.status.value, str(ob.status.value))
                fail_note = f" *(Fallo: {ob.failure_reason})*" if ob.failure_reason else ""
                md.append(f"- [{badge}] **{ob.title}** (Vence: `{ob.due_phase}`){fail_note}")
            md.append("")

        return {
            "status": "SONG_CONTRACT_SUMMARY",
            "phase": curr_phase,
            "contract": contract.to_dict(),
            "message": "\n".join(md),
            "question": f"Contrato activo ({summary['verified']}/{summary['total']} verificadas). ¿Cómo deseas proceder?"
        }

    def _handle_omission_audit_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query executing an active omission audit against Ableton Live."""
        from engine.production.contract import OmissionAuditor
        contract = self._get_song_contract()
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        report = OmissionAuditor.audit_phase_readiness(contract, self.data, conn, curr_phase)
        self._sync_song_contract(contract)
        self._save_state(action_tag="MANUAL_OMISSION_AUDIT")

        return {
            "status": "OMISSION_AUDIT_COMPLETED",
            "phase": curr_phase,
            "can_advance": report.can_advance,
            "omission_report": report.to_dict(),
            "message": report.format_markdown_report(),
            "question": f"Auditoría de omisiones para {curr_phase} completada. ¿Cómo deseas proceder?"
        }

    def _handle_song_intent_query(self) -> Dict[str, Any]:
        """Conversational query returning the artistic intent memory."""
        contract = self._get_song_contract()
        intent = contract.intent_memory
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")

        md = [
            f"### 🎯 Memoria de Intención Creativa (`SongIntentMemory`)",
            f"- **Tesis Sonora:** *\"{intent.thesis.statement}\"*",
            f"- **Género / Estilo:** `{intent.thesis.genre}` (Referencia: `{intent.thesis.reference_artist}`)",
            f"- **Tonalidad & Tempo:** `{intent.thesis.key} {intent.thesis.scale}` a `{intent.thesis.bpm} BPM`\n",
            "#### ⚓ Anclas de Identidad Sonora (Innegociables):",
            *[f"- {a}" for a in intent.identity_anchors],
            "\n#### 🚫 Derivas Prohibidas (Anti-Patrones):",
            *[f"- {d}" for d in intent.forbidden_drift],
            "\n#### 📈 Objetivos de Evolución Estructural:",
            *[f"- **{e.get('id', 'EVOL')}** ({e.get('source')} $\\to$ {e.get('target')}): {e.get('expected')}" for e in intent.evolution_targets],
            "\n#### ❓ Preguntas Creativas Abiertas:",
            *[f"- {q}" for q in intent.unresolved_questions]
        ]

        return {
            "status": "SONG_INTENT_SUMMARY",
            "phase": curr_phase,
            "intent_memory": intent.to_dict(),
            "message": "\n".join(md),
            "question": f"Tesis sonora: '{intent.thesis.statement}'. ¿Deseas continuar con {curr_phase}?"
        }

    def validate_phase_readiness(self, conn: Any, target_phase: str) -> Optional[Dict[str, Any]]:
        """
        Gating check: verifies if current phase obligations are satisfied before advancing.
        Returns None if phase can advance, or a blocking response dict if blocked by omission.
        """
        from engine.production.contract import OmissionAuditor
        contract = self._get_song_contract()
        report = OmissionAuditor.audit_phase_readiness(contract, self.data, conn, target_phase)
        self._sync_song_contract(contract)
        self._save_state(action_tag=f"OMISSION_AUDIT_{target_phase}")

        if not report.can_advance:
            return {
                "status": "PHASE_BLOCKED_BY_OMISSION",
                "phase": target_phase,
                "current_step": f"{target_phase} DETENIDA POR OMISIÓN CRÍTICA",
                "action_taken": f"Bloqueo de fase: {report.block_reason}",
                "question": report.format_markdown_report(),
                "instructions_for_ai": "Resuelve la obligación fallida o ejecuta la reparación sugerida antes de continuar.",
                "omission_report": report.to_dict()
            }
        return None

    def _handle_creative_xray_query(self, conn: Any = None) -> Dict[str, Any]:
        """Generates full 4-level Creative X-Ray diagnostic across Integrity, Coherence, Evolution, and Decision."""
        from engine.production.contract.creative_xray import CreativeXRay
        contract = self._get_song_contract()
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        xray_res = CreativeXRay.generate_xray(self.data, conn=conn, contract=contract)

        return {
            "status": "CREATIVE_XRAY_GENERATED",
            "phase": curr_phase,
            "xray": xray_res,
            "message": xray_res.get("markdown_report", ""),
            "question": "¿Cómo interpretas estos hallazgos y qué decisión creativa prefieres tomar?"
        }

    def _handle_emotional_arc_query(self) -> Dict[str, Any]:
        """Conversational query returning the orchestrated emotional trajectory across song sections."""
        from engine.arrangement.emotional_arc import EmotionalArcDirector
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        genre = self.data.get("genre", "trap")
        key = self.data.get("key", "F")
        scale = self.data.get("scale", "natural_minor")
        sections = self.data.get("sections", [])

        inferred_emotion = EmotionalArcDirector.infer_emotion(genre=genre, key=key, scale=scale)
        arc = self.data.get("emotional_arc")
        if not arc or len(arc) != len(sections):
            arc = EmotionalArcDirector.orchestrate_arc(
                sections=sections,
                genre=genre,
                emotion=inferred_emotion,
                key=key,
                scale=scale
            )
            self.data["emotion"] = inferred_emotion.value
            self.data["emotional_arc"] = arc
            self._save_state(action_tag="EMOTIONAL_ARC_EVALUATED")

        profile = EmotionalArcDirector.EMOTIONAL_PROFILES.get(inferred_emotion, {})
        md = [
            f"### 🎭 Director de Arco Emocional y Dinámica Macro",
            f"- **Tonalidad & Escala:** `{key} {scale}` | **Género:** `{genre.capitalize()}`",
            f"- **Emoción Inferida:** `{profile.get('name', inferred_emotion.value)}` ({inferred_emotion.value})",
            f"- **Tesis Emocional:** {profile.get('description', '')}\n",
            "| Sección | Compases | Energía (%) | Dispositivo de Tensión | Retención de Inercia Rítmica |",
            "| :--- | :---: | :---: | :--- | :--- |"
        ]
        for sec in arc:
            s_name = sec.get("name", "Sección")
            s_bars = sec.get("bars", 8)
            s_energy = int(float(sec.get("target_energy", 0.5)) * 100)
            s_tension = sec.get("tension_device", "STANDARD")
            s_inertia = ", ".join(sec.get("inertia_keep_roles", [])) or "—"
            md.append(f"| **{s_name}** | {s_bars} | {s_energy}% | `{s_tension}` | {s_inertia} |")

        md.append("\n💡 *Regla de Éxito Comercial: El Verso 2 no colapsa la inercia rítmica, conservando elementos del Coro/Drop.*")

        return {
            "status": "EMOTIONAL_ARC_SUMMARY",
            "phase": curr_phase,
            "emotion": inferred_emotion.value,
            "emotional_arc": arc,
            "message": "\n".join(md),
            "question": f"Arco emocional '{inferred_emotion.value}' orquestado. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_bus_architecture_query(self) -> Dict[str, Any]:
        """Conversational query returning non-destructive submaster stem bus routing."""
        from engine.mix.bus_architecture import LiveBusArchitectureEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        bus_plan = self.data.get("bus_architecture")
        if not bus_plan or not bus_plan.get("buses"):
            bus_plan = LiveBusArchitectureEngine.analyze_topology(tracks)
            self.data["bus_architecture"] = bus_plan
            self._save_state(action_tag="BUS_TOPOLOGY_ANALYZED")

        md = [
            "### 🎛️ Arquitectura de Buses Submaster (Stem Submixes)",
            "Enrutamiento comercial no destructivo para cohesión de mezcla y pegamento dinámico:\n",
            bus_plan.get("summary_table", ""),
            "\n🔒 *Garantía de Invariante: Ninguna pista, clip o efecto de usuario es alterado ni sobreescrito.*"
        ]

        return {
            "status": "BUS_ARCHITECTURE_SUMMARY",
            "phase": curr_phase,
            "bus_architecture": bus_plan,
            "message": "\n".join(md),
            "question": f"Matriz de submaster con {bus_plan.get('active_buses_count', 0)} buses activos. ¿Cómo deseas proceder?"
        }

    def _handle_hook_evaluation_query(self) -> Dict[str, Any]:
        """Conversational query auditing melodic hook memorability and commercial compliance."""
        from engine.music.melody.hook_contour import HookContourEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        notes = self.data.get("hook_architecture", {}).get("notes", [])
        if not notes:
            key = self.data.get("key", "F")
            scale = self.data.get("scale", "natural_minor")
            notes = HookContourEngine.generate_hook_motif(key_root=key, scale=scale)
            if "hook_architecture" not in self.data:
                self.data["hook_architecture"] = {}
            self.data["hook_architecture"]["notes"] = [n.to_dict() if hasattr(n, "to_dict") else dict(n.__dict__) for n in notes]

        from engine.music.models import NoteEvent
        note_objs = [n if isinstance(n, NoteEvent) else NoteEvent(**n) for n in notes]
        report = HookContourEngine.evaluate_hook(note_objs)

        md = [
            f"### 🪝 Auditoría de Psicología Melódica y Hook Theory (`HookContourEngine`)",
            f"- **Puntuación Hook Factor:** **{report.score:.1f} / 100** {'⭐ (Comercial Hit)' if report.is_valid_commercial_hook else '⚠️ (Requiere Pulido)'}",
            f"- **Contorno Geométrico:** `{report.detected_contour.value}`",
            f"- **Rango Vocal:** `{report.vocal_range_semitones}` semitonos (Límite máximo: 18)",
            f"- **Violaciones Salto-Paso:** `{report.leap_step_violations}`",
            f"- **Respiración y Silencios:** `{'Sí (Frases humanas)' if report.has_breathing_space else 'No (Sin pausas)'}`",
            f"- **Simetría de Motivos:** `{int(report.motif_symmetry_ratio * 100)}%`\n"
        ]
        if report.recommendations:
            md.append("#### 💡 Recomendaciones de Retención:")
            for rec in report.recommendations:
                md.append(f"- {rec}")

        return {
            "status": "HOOK_EVALUATION_REPORT",
            "phase": curr_phase,
            "hook_report": report.to_dict(),
            "message": "\n".join(md),
            "question": f"Hook Factor: {report.score:.1f}/100. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_ear_candy_query(self) -> Dict[str, Any]:
        """Conversational query returning organic ear candy timeline and micro-gestures."""
        from engine.arrangement.transitions.ear_candy import SmartEarCandyEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        sections = self.data.get("sections", [])
        tot_bars = self.data.get("total_bars", 64)
        density = self.data.get("ear_candy", {}).get("density_level", 2)

        events = SmartEarCandyEngine.generate_ear_candy_package(
            sections=sections,
            total_bars=tot_bars,
            density_level=density
        )
        self.data["ear_candy"] = {
            "density_level": density,
            "events": [e.to_dict() for e in events]
        }
        self._save_state(action_tag="EAR_CANDY_SCHEDULED")

        summary_md = SmartEarCandyEngine.render_markdown_summary(events, density_level=density)
        return {
            "status": "EAR_CANDY_SUMMARY",
            "phase": curr_phase,
            "density_level": density,
            "events_count": len(events),
            "ear_candy": self.data["ear_candy"],
            "message": summary_md,
            "question": f"Ear candy programado con densidad {density}/5 ({len(events)} micro-eventos). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_space_ducking_query(self) -> Dict[str, Any]:
        """Conversational query returning ducked reverbs and delays status."""
        from engine.mix.space_ducking import DynamicSpaceDucker, SpaceDuckingMode
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        mode_str = self.data.get("space_ducking", {}).get("mode", "COMMERCIAL_STANDARD")
        try:
            mode = SpaceDuckingMode(mode_str)
        except Exception:
            mode = SpaceDuckingMode.COMMERCIAL_STANDARD

        recipe = DynamicSpaceDucker.get_recipe(mode)
        summary_md = DynamicSpaceDucker.render_markdown_summary(recipe)
        return {
            "status": "SPACE_DUCKING_SUMMARY",
            "phase": curr_phase,
            "mode": mode.value,
            "recipe": recipe,
            "message": summary_md,
            "question": f"Space Ducking activo en modo '{mode.value}' (-{abs(recipe['duck_amount_db'])} dB). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_modal_harmony_query(self) -> Dict[str, Any]:
        """Conversational query returning modal borrowing and smooth voice leading analysis."""
        from engine.music.harmony.modal_voice_leading import ModalVoiceLeadingEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        key = self.data.get("key", "F")
        scale = self.data.get("scale", "natural_minor")

        voiced_chords = ModalVoiceLeadingEngine.enrich_progression_with_borrowing(
            key_root=key,
            scale=scale,
            inject_emotional_borrowing=True
        )
        self.data["modal_voice_leading"] = {
            "key": key,
            "scale": scale,
            "chords": [c.to_dict() for c in voiced_chords]
        }
        self._save_state(action_tag="MODAL_HARMONY_EVALUATED")

        summary_md = ModalVoiceLeadingEngine.render_markdown_summary(voiced_chords, key=key, scale=scale)
        return {
            "status": "MODAL_HARMONY_SUMMARY",
            "phase": curr_phase,
            "chords": [c.to_dict() for c in voiced_chords],
            "message": summary_md,
            "question": f"Progresión modal optimizada en {key} {scale}. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_metric_modulation_query(self) -> Dict[str, Any]:
        """Conversational query returning active micro-rhythmic metric modulation setup."""
        from engine.music.groove.metric_modulation import MetricModulationEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        level = self.data.get("metric_modulation", {}).get("level", 2)
        summary_md = MetricModulationEngine.render_markdown_summary(level)

        return {
            "status": "METRIC_MODULATION_SUMMARY",
            "phase": curr_phase,
            "level": level,
            "config": MetricModulationEngine.get_config(level),
            "message": summary_md,
            "question": f"Modulación métrica configurada en Nivel {level}/5. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_antiphonal_dialogue_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning rotational Call & Response dialogue architecture."""
        from engine.music.antiphonal_dialogue import AntiphonalDialogueEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])

        dialogue = self.data.get("antiphonal_dialogue")
        if not dialogue:
            focal_trk = next((t for t in tracks if str(t.get("role", "")).upper() in ("VOCALS", "VOCAL", "VOX", "LEAD", "SYNTH_LEAD")), None)
            f_idx = focal_trk.get("index", 0) if focal_trk else 0
            f_notes = focal_trk.get("notes", []) if focal_trk else []
            if not f_notes:
                f_notes = [
                    {"pitch": 64, "start_time": 0.0, "duration": 1.5, "velocity": 100},
                    {"pitch": 67, "start_time": 2.0, "duration": 1.5, "velocity": 105},
                    {"pitch": 65, "start_time": 4.0, "duration": 1.5, "velocity": 98}
                ]
            dialogue = AntiphonalDialogueEngine.orchestrate_rotational_dialogue(
                tracks=tracks,
                focal_track_index=f_idx,
                focal_notes=f_notes,
                total_beats=32.0,
                scale_root_pitch=60
            )
            self.data["antiphonal_dialogue"] = dialogue
            self._save_state(action_tag="ANTIPHONAL_DIALOGUE_EVALUATED")

        summary_md = (
            "🗣️ **Arquitectura de Interacción Call & Response (Antiphonal Dialogue)**\n\n"
            f"• **Política de Diálogo:** `{dialogue.get('policy', 'ROTATIONAL')}` (Rotación estricta secuencial)\n"
            f"• **Pista Focal (Líder):** Pista {dialogue.get('focal_track_index', 0)}\n"
            f"• **Instrumentos Elegibles en Rotación:** {dialogue.get('eligible_responders_count', len(dialogue.get('eligible_responders', [])))}\n"
            f"• **Total de Respuestas Antifonales:** {dialogue.get('total_responses', 0)}\n"
            "• **Garantía Anti-Colisión:** Margen de seguridad $\\ge 0.05$ beats ante notas líderes."
        )
        return {
            "status": "ANTIPHONAL_DIALOGUE_SUMMARY",
            "phase": curr_phase,
            "policy": dialogue.get("policy", "ROTATIONAL"),
            "total_responses": dialogue.get("total_responses", 0),
            "antiphonal_dialogue": dialogue,
            "message": summary_md,
            "question": f"Call & Response antifonal configurado ({dialogue.get('total_responses', 0)} respuestas). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_phase_correlation_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning low-end phase and polarity correlation audit."""
        from engine.mix.phase_correlation_sentinel import PhaseCorrelationSentinel
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        phase_audit = PhaseCorrelationSentinel.audit_kick_bass_coherence(tracks, conn=conn)
        self.data["phase_correlation"] = phase_audit
        self._save_state(action_tag="PHASE_CORRELATION_AUDITED")

        summary_md = (
            "🎛️ **Auditoría de Alineación de Fase y Polaridad Low-End (Phase Correlation Sentinel)**\n\n"
            f"• **Pista Kick:** Pista {phase_audit.get('kick_track_index', 'N/A')}\n"
            f"• **Pista Bass:** Pista {phase_audit.get('bass_track_index', 'N/A')}\n"
            f"• **Coeficiente de Correlación (ρ):** `{phase_audit.get('correlation_coefficient', 1.0):.2f}`\n"
            f"• **Diagnóstico:** `{phase_audit.get('status', 'OK')}`\n"
            f"• **Inversión de Polaridad (180°):** `{'REQUERIDA' if phase_audit.get('directives', {}).get('invert_polarity_180') else 'No necesaria'}`\n"
            f"• **Micro-Delay:** `{phase_audit.get('directives', {}).get('delay_ms', 0.0):.2f} ms`\n"
            f"• **Bass Mono (<120 Hz):** `{'ACTIVO' if phase_audit.get('directives', {}).get('bass_mono_enabled') else 'Inactivo'}`"
        )
        return {
            "status": "PHASE_CORRELATION_SUMMARY",
            "phase": curr_phase,
            "audit": phase_audit,
            "message": summary_md,
            "question": f"Alineación de fase auditada (ρ = {phase_audit.get('correlation_coefficient', 1.0):.2f}). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_resonance_carver_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning dynamic resonance carving & anti-masking audit."""
        from engine.mix.smart_resonance_carver import SmartResonanceCarver
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        carve_audit = SmartResonanceCarver.audit_session_resonances(tracks, conn=conn)
        self.data["smart_resonance_carver"] = carve_audit
        self._save_state(action_tag="RESONANCE_CARVER_AUDITED")

        clashes = carve_audit.get("detected_clashes", [])
        clash_lines = [f"• `{c.get('pair')}` ({c.get('center_freq_hz')} Hz): {c.get('remedy')}" for c in clashes] if clashes else ["• No se detectaron colisiones de enmascaramiento críticas."]

        summary_md = (
            "🔬 **Ecualización Dinámica Anti-Enmascaramiento en Tiempo Real (Smart Resonance Carver)**\n\n"
            f"• **Pistas Auditadas:** {len(tracks)}\n"
            f"• **Puntos de Conflicto Espectral:** {len(clashes)}\n"
            + "\n".join(clash_lines)
        )
        return {
            "status": "RESONANCE_CARVER_SUMMARY",
            "phase": curr_phase,
            "audit": carve_audit,
            "clashes_count": len(clashes),
            "message": summary_md,
            "question": f"Tallado anti-enmascaramiento evaluado ({len(clashes)} colisiones). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_crossover_stacking_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning psychoacoustic 3-band crossover layer architecture."""
        from engine.sound.crossover_stacking import MultiLayerCrossoverStacker
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        target_trk = next((t for t in tracks if str(t.get("role", "")).upper() in ("BASS", "SYNTH", "KEYS", "LEAD")), None)
        trk_name = target_trk.get("name", "Synth Layer") if target_trk else "Bass/Synth"
        split_plan = MultiLayerCrossoverStacker.create_crossover_split(source_track_name=trk_name)
        self.data["crossover_stacking"] = split_plan
        self._save_state(action_tag="CROSSOVER_STACKING_EVALUATED")

        summary_md = (
            "🎚️ **Separación de Capas por Crossover Psicoacústico (Multi-Layer Crossover Stacker)**\n\n"
            f"• **Pista Fuente:** `{trk_name}`\n"
            "• **Capa Sub (<90 Hz):** Mono absoluto, limpieza de fase, compresión pesada.\n"
            "• **Capa Body (90 - 1200 Hz):** Stereo width 0.35, saturación armónica analógica.\n"
            "• **Capa Air (>1200 Hz):** Stereo width 0.95, micro-modulación estéreo y brillo dimensional."
        )
        return {
            "status": "CROSSOVER_STACKING_SUMMARY",
            "phase": curr_phase,
            "split_plan": split_plan,
            "message": summary_md,
            "question": f"Crossover psicoacústico de 3 capas configurado en '{trk_name}'. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_vocal_harmonies_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning intelligent vocal harmony and wide stereo spread stack."""
        from engine.music.vocal_harmony import VocalHarmonyEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        harmonies = self.data.get("vocal_harmonies")
        if not harmonies:
            harmonies = VocalHarmonyEngine.generate_vocal_harmony_stack(
                lead_notes=[
                    {"pitch": 64, "start_time": 0.0, "duration": 1.5, "velocity": 100},
                    {"pitch": 67, "start_time": 2.0, "duration": 1.5, "velocity": 105},
                    {"pitch": 65, "start_time": 4.0, "duration": 1.5, "velocity": 98}
                ],
                scale_root_pitch=60,
                bpm=float(self.data.get("bpm", 120.0))
            )
            self.data["vocal_harmonies"] = harmonies
            self._save_state(action_tag="VOCAL_HARMONIES_EVALUATED")

        summary_md = (
            "🎤 **Generador de Armonías y Coros Estéreo Inteligentes (Vocal Harmony Engine)**\n\n"
            f"• **High Harmony:** +3 / +4 semitonos diatónicos paneados al `60L`.\n"
            f"• **Low Harmony:** -3 / -4 semitonos diatónicos paneados al `60R`.\n"
            f"• **Total Notas de Armonía:** {harmonies.get('total_harmony_notes', 0)}\n"
            "• **Humanización de Micro-Timing:** Jitter anti-comb filtering de 8 ms."
        )
        return {
            "status": "VOCAL_HARMONY_SUMMARY",
            "phase": curr_phase,
            "harmonies": harmonies,
            "message": summary_md,
            "question": f"Armonías vocales generadas ({harmonies.get('total_harmony_notes', 0)} notas). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_drum_fills_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning adaptive high-fidelity drum fill details."""
        from engine.music.drums.adaptive_fill import AdaptiveDrumFillGenerator
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        fills = self.data.get("adaptive_drum_fills")
        if not fills:
            fills = AdaptiveDrumFillGenerator.generate_turnaround_fill(
                section_length_beats=32.0,
                fill_duration_beats=4.0,
                genre=self.data.get("genre", "pop"),
                bpm=float(self.data.get("bpm", 120.0))
            )
            self.data["adaptive_drum_fills"] = fills
            self._save_state(action_tag="ADAPTIVE_DRUM_FILLS_EVALUATED")

        summary_md = (
            "🥁 **Motor de Fills y Redobles Frecuencialmente Adaptativos (Adaptive Drum Fills)**\n\n"
            f"• **Estilo Aplicado:** `{fills.get('style_applied', 'POP')}`\n"
            f"• **Duración:** {fills.get('duration_beats', 4.0)} beats en compás de turnaround\n"
            f"• **Total de Notas de Redoble:** {fills.get('note_count', 0)}\n"
            f"• **Estructura:** 4 capas (Toms afinados 41-48, Snare flams/rolls, Címbalos/Splash)\n"
            "• **Kick Dropout:** Silencio de bombo en beats 3-4 para evitar enmascaramiento."
        )
        return {
            "status": "ADAPTIVE_DRUM_FILLS_SUMMARY",
            "phase": curr_phase,
            "fills": fills,
            "message": summary_md,
            "question": f"Redoble adaptativo de 4 capas configurado ({fills.get('note_count', 0)} notas). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_micro_stutter_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning tape stop curve and glitch micro-stutter envelopes."""
        from engine.arrangement.transitions.micro_stutter import MicroStutterEngine
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tape_stop = self.data.get("tape_stop")
        if not tape_stop:
            tape_stop = MicroStutterEngine.generate_tape_stop_envelope(
                pre_drop_beat=32.0,
                stop_duration_beats=2.0,
                pitch_drop_semitones=-24.0,
                curve_shape="EXPONENTIAL",
                preserve_drum_fills=True
            )
            self.data["tape_stop"] = tape_stop
            self._save_state(action_tag="TAPE_STOP_EVALUATED")

        summary_md = (
            "📼 **Generador de Micro-Edits Glitch y Tape Stops (Micro Stutter Engine)**\n\n"
            f"• **Tape Stop en Pre-Drop:** Curva exponencial de {tape_stop.get('stop_duration_beats', 2.0)} beats\n"
            f"• **Caída de Tono:** `{tape_stop.get('pitch_drop_semitones', -24.0)} semitonos`\n"
            f"• **Alcance de Procesamiento:** `Opción A (Music Bus Exclusivo)`\n"
            "• **Batería y Fills:** 100% limpios y secos en primer plano durante la caída."
        )
        return {
            "status": "MICRO_STUTTER_SUMMARY",
            "phase": curr_phase,
            "tape_stop": tape_stop,
            "message": summary_md,
            "question": f"Tape Stop pre-drop configurado en Music Bus (-24st, fills limpios). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_metric_displacement_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning off-beat metric displacement status."""
        from engine.music.groove.metric_displacement import OffBeatMetricDisplacer
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        disp_data = self.data.get("metric_displacement")
        if not disp_data:
            target_trk = next((t for t in tracks if any(el in str(t.get("role", "")).upper() for el in OffBeatMetricDisplacer.ELIGIBLE_ROLES)), None)
            notes = target_trk.get("notes", []) if target_trk else [
                {"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 100},
                {"pitch": 36, "start_time": 4.0, "duration": 1.0, "velocity": 100},
                {"pitch": 38, "start_time": 8.0, "duration": 1.0, "velocity": 100}
            ]
            role = target_trk.get("role", "BASS") if target_trk else "BASS"
            disp_res = OffBeatMetricDisplacer.apply_metric_displacement(notes, role=role, displacement_level=2)
            disp_data = {"status": "APPLIED", "tracks": [{"track": role, "role": role, "bars": disp_res.get("displaced_bars", [2]), "shift": 0.25}]}
            self.data["metric_displacement"] = disp_data
            summary_md = OffBeatMetricDisplacer.render_markdown_summary(disp_res)
        else:
            summary_md = (
                "🕺 **Motor de Acentos de Contratiempo y Desplazamiento Métrico (Metric Displacer)**\n\n"
                f"• **Pistas Sincopadas:** {len(disp_data.get('tracks', []))}\n"
                "• **Patrón:** Desplazamiento micro-rítmico (+0.25 beats) en compases 2 y 6 para añadir rebote orgánico."
            )

        return {
            "status": "METRIC_DISPLACEMENT_SUMMARY",
            "phase": curr_phase,
            "metric_displacement": disp_data,
            "message": summary_md,
            "question": f"Desplazamiento métrico evaluado. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_z_plane_depth_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning 3D Z-plane psychoacoustic depth distribution."""
        from engine.mix.z_plane_depth import ZPlaneDepthArchitect
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        depth_audit = ZPlaneDepthArchitect.evaluate_session_depth(tracks)
        self.data["z_plane_depth"] = depth_audit
        summary_md = ZPlaneDepthArchitect.render_markdown_summary(depth_audit)

        return {
            "status": "Z_PLANE_DEPTH_SUMMARY",
            "phase": curr_phase,
            "z_plane_depth": depth_audit,
            "message": summary_md,
            "question": f"Profundidad en eje Z evaluada ({len(depth_audit.get('depth_distribution', {}).get('FOREGROUND', []))} foreground, {len(depth_audit.get('depth_distribution', {}).get('BACKGROUND', []))} background). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_sub_stereo_morph_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning dynamic sub-to-stereo drop expansion envelope."""
        from engine.sound.sub_stereo_morpher import DynamicSubToStereoMorpher
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        drop_sec = next((s for s in self.data.get("sections", []) if any(w in str(s.get("name", "")).lower() for w in ["drop", "climax", "coro"])), None)
        drop_start = float(drop_sec.get("start_bar", 0) * 4.0) if drop_sec else 32.0

        morph = self.data.get("sub_stereo_morph")
        if not morph:
            morph = DynamicSubToStereoMorpher.generate_drop_expansion_envelope(
                drop_start_beat=drop_start,
                pre_drop_duration_beats=4.0,
                drop_stereo_width=1.35
            )
            self.data["sub_stereo_morph"] = morph

        summary_md = DynamicSubToStereoMorpher.render_markdown_summary(morph)
        return {
            "status": "SUB_STEREO_MORPH_SUMMARY",
            "phase": curr_phase,
            "sub_stereo_morph": morph,
            "message": summary_md,
            "question": f"Apertura sub-a-estéreo configurada (ancho en drop: {morph.get('drop_stereo_width', 1.35)}). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_foley_bed_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning atmospheric foley bed prescription."""
        from engine.arrangement.textures.foley_bed import AtmosphericFoleyBedGenerator
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        genre = str(self.data.get("genre", "pop"))

        foley = self.data.get("foley_bed")
        if not foley:
            foley = AtmosphericFoleyBedGenerator.generate_foley_bed_prescription(
                genre=genre,
                target_level_dbfs=-30.0
            )
            self.data["foley_bed"] = foley

        summary_md = AtmosphericFoleyBedGenerator.render_markdown_summary(foley)
        return {
            "status": "FOLEY_BED_SUMMARY",
            "phase": curr_phase,
            "foley_bed": foley,
            "message": summary_md,
            "question": f"Cama foley '{foley.get('preset', 'VINYL_WARMTH')}' calibrada a {foley.get('target_level_dbfs', -30.0)} dBFS. ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_crest_factor_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning pre-master crest factor & headroom audit."""
        from engine.mix.crest_factor_optimizer import PreMasterCrestFactorOptimizer
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        tracks = self.data.get("tracks", [])
        crest_audit = PreMasterCrestFactorOptimizer.audit_session_crest_factors(tracks, conn=conn)
        self.data["crest_factor_audit"] = crest_audit
        summary_md = PreMasterCrestFactorOptimizer.render_markdown_summary(crest_audit)

        return {
            "status": "CREST_FACTOR_SUMMARY",
            "phase": curr_phase,
            "crest_factor_audit": crest_audit,
            "message": summary_md,
            "question": f"Factor de cresta auditado (Pico max: {crest_audit.get('max_track_crest_factor', 0.0):.1f} dB, Soft-clipping: {crest_audit.get('clip_instances', 0)} pistas). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_hihat_mutation_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning evolutionary hi-hat mutation status."""
        from engine.music.drums.hihat_mutator import EvolutionaryHiHatMutator
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        genre = str(self.data.get("genre", "trap"))
        hh_data = self.data.get("hihat_mutations")
        if not hh_data:
            # Generate demonstration 8-bar pattern
            demo_notes = []
            for b in range(32):
                demo_notes.append({"pitch": 42, "start_time": float(b), "duration": 0.25, "velocity": 85})
            hh_data = EvolutionaryHiHatMutator.mutate_hihat_pattern(
                notes=demo_notes,
                bars=8,
                genre=genre,
                intensity=0.6
            )
            self.data["hihat_mutations"] = hh_data

        summary_md = EvolutionaryHiHatMutator.render_markdown_summary(hh_data)
        return {
            "status": "HIHAT_MUTATION_SUMMARY",
            "phase": curr_phase,
            "hihat_mutations": hh_data,
            "message": summary_md,
            "question": f"Mutación de Hi-Hats activa ({len(hh_data.get('mutations_applied', []))} mutaciones en 8 compases). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_pedal_suspension_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning harmonic pedal points and suspended chords status."""
        from engine.music.harmony.pedal_suspension import PedalPointSuspensionWeaver
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        pedal_data = self.data.get("pedal_suspensions")
        if not pedal_data:
            pedal_data = PedalPointSuspensionWeaver.weave_pedal_point_progression(
                chords_or_notes=[],
                pedal_pitch=36,
                section_name="pre_chorus",
                suspension_type="AUTO"
            )
            self.data["pedal_suspensions"] = pedal_data

        summary_md = PedalPointSuspensionWeaver.render_markdown_summary(pedal_data)
        return {
            "status": "PEDAL_SUSPENSION_SUMMARY",
            "phase": curr_phase,
            "pedal_suspensions": pedal_data,
            "message": summary_md,
            "question": f"Tensión armónica pedal configurada (Tensión: {int(pedal_data.get('harmonic_tension_score', 0.8) * 100)}%). ¿Deseas continuar con {curr_phase}?"
        }

    def _handle_underwater_sweep_query(self, conn: Any = None) -> Dict[str, Any]:
        """Conversational query returning underwater / radio acoustic sweep transition curves."""
        from engine.arrangement.transitions.underwater_sweep import UnderwaterRadioSweepGenerator
        curr_phase = self.data.get("current_phase", "PHASE_1_TRACKS")
        drop_sec = next((s for s in self.data.get("sections", []) if any(w in str(s.get("name", "")).lower() for w in ["drop", "climax", "coro"])), None)
        drop_start = float(drop_sec.get("start_bar", 0) * 4.0) if drop_sec else 32.0

        sweep = self.data.get("underwater_sweep")
        if not sweep:
            sweep = UnderwaterRadioSweepGenerator.generate_underwater_sweep(
                drop_start_beat=drop_start,
                duration_beats=4.0,
                mode="UNDERWATER"
            )
            self.data["underwater_sweep"] = sweep

        summary_md = UnderwaterRadioSweepGenerator.render_markdown_summary(sweep)
        return {
            "status": "UNDERWATER_SWEEP_SUMMARY",
            "phase": curr_phase,
            "underwater_sweep": sweep,
            "message": summary_md,
            "question": f"Filtro underwater pre-drop configurado ({sweep.get('mode', 'UNDERWATER')}, min {sweep.get('min_cutoff_hz')} Hz). ¿Deseas continuar con {curr_phase}?"
        }


# Global singleton
copilot_guided_session_engine = CopilotGuidedSession()

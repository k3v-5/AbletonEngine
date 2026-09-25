# engine/production/copilot/intercept_router.py
"""
Copilot Global Intercept Router (Chain of Responsibility & SOLID Architecture):
Deconstructs global keyword commands, multi-phase triggers, and active modal sub-states
into cohesive, single-responsibility handlers adhering strictly to SRP, OCP, LSP, ISP, and DIP.
"""

from typing import Dict, Any, Optional, List
import re
import logging
from engine.production.copilot.nlp_parser import _normalize_text, parse_autotune_settings
from engine.core.protocols import InterceptHandlerProtocol

logger = logging.getLogger("CopilotInterceptRouter")


# ---------------------------------------------------------------------------
# 1. Governance, Authority & Cryptographic Ledger Handler (SRP: Governance)
# ---------------------------------------------------------------------------
class GovernanceInterceptHandler:
    """Handles Four-Tier Authority, State Bus inspection, and Ledger integrity audits."""

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        if any(w in norm_text for w in [
            "ver gobernanza", "auditoria de gobernanza", "auditoria gobernanza",
            "governance audit", "estado de gobernanza", "verificar gobernanza"
        ]):
            return True
        if any(w in norm_text for w in [
            "ver anclas", "ver state bus", "anclas de estado", "state bus",
            "anclas de produccion", "anclas de producción", "ver anclas de produccion"
        ]):
            return True
        if any(w in norm_text for w in [
            "ver ledger", "verificar ledger", "auditar ledger", "verificar integridad",
            "integridad ledger", "cadena de ledger", "ledger audit"
        ]):
            return True
        if any(w in norm_text for w in ["declarar tacet", "tacet en", "silencio intencional"]):
            return True
        if any(w in norm_text for w in ["rechazar", "rechazado"]) and any(
            w in norm_text for w in ["por artista", "como artista", "decision artistica", "decisión artística"]
        ):
            return True
        if any(w in norm_text for w in ["declarar override", "override estructural"]):
            return True
        if any(w in norm_text for w in [
            "pre drop vacuum", "pre-drop vacuum", "vacio pre drop", "vacío pre drop", "silencio pre drop"
        ]):
            return True
        return False

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        if any(w in norm_text for w in [
            "ver gobernanza", "auditoria de gobernanza", "auditoria gobernanza",
            "governance audit", "estado de gobernanza", "verificar gobernanza"
        ]):
            return session._handle_governance_audit_query()

        if any(w in norm_text for w in [
            "ver anclas", "ver state bus", "anclas de estado", "state bus",
            "anclas de produccion", "anclas de producción", "ver anclas de produccion"
        ]):
            return session._handle_state_bus_query()

        if any(w in norm_text for w in [
            "ver ledger", "verificar ledger", "auditar ledger", "verificar integridad",
            "integridad ledger", "cadena de ledger", "ledger audit"
        ]):
            return session._handle_ledger_integrity_query()

        if any(w in norm_text for w in ["declarar tacet", "tacet en", "silencio intencional"]):
            return session._handle_artistic_contract_declaration(user_input, contract_type="tacet")

        if any(w in norm_text for w in ["rechazar", "rechazado"]):
            return session._handle_artistic_contract_declaration(user_input, contract_type="reject")

        if any(w in norm_text for w in ["declarar override", "override estructural"]):
            return session._handle_artistic_contract_declaration(user_input, contract_type="override")

        if any(w in norm_text for w in ["pre drop vacuum", "pre-drop vacuum", "vacio pre drop", "vacío pre drop", "silencio pre drop"]):
            return session._handle_artistic_contract_declaration(user_input, contract_type="vacuum")

        return None

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        norm = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else ""
        return self.handle(norm, user_input, session, conn, phase) if self.can_handle(norm, user_input, session, phase) else None


# ---------------------------------------------------------------------------
# 2. Sound Design & Library Configuration Handler (SRP: Sound Design)
# ---------------------------------------------------------------------------
class SoundDesignInterceptHandler:
    """Handles sound design modes (Legacy vs Advanced) and Decent Sampler library path configurations."""

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        if any(w in norm_text for w in [
            "activar sound design avanzado", "activar modo sound design avanzado",
            "sound design avanzado", "modo sound design avanzado"
        ]):
            return True
        if any(w in norm_text for w in [
            "modo sound design clasico", "modo sound design clásico",
            "sound design clasico", "sound design clásico",
            "modo sound design legacy", "sound design legacy"
        ]):
            return True
        if any(w in norm_text for w in ["estado sound design", "estado de sound design", "ver sound design"]):
            return True
        if any(w in norm_text for w in [
            "ver librerias decent sampler", "listar librerias decent sampler",
            "librerias decent sampler", "decent sampler librerias", "ver librerias"
        ]):
            return True
        if re.search(
            r"(?:cambiar|configurar|setear|actualizar|definir)\s+(?:la\s+)?(?:carpeta|ruta|directorio)\s+(?:de\s+)?(?:librerias|muestras|sonidos|decent\s*sampler)?\s+(?:a|en|por)?\s*[:=]?\s*([a-zA-Z]:[\\/][^\n\r]+|\/[^\n\r]+|~[\\/][^\n\r]+)",
            user_input, re.IGNORECASE
        ) or re.search(
            r"(?:carpeta|ruta|directorio)\s+(?:de\s+)?(?:librerias|decent\s*sampler)?\s*[:=]\s*([a-zA-Z]:[\\/][^\n\r]+|\/[^\n\r]+|~[\\/][^\n\r]+)",
            user_input, re.IGNORECASE
        ):
            return True
        return False

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        # Sound Design Mode Intercepts
        if any(w in norm_text for w in [
            "activar sound design avanzado", "activar modo sound design avanzado",
            "sound design avanzado", "modo sound design avanzado"
        ]):
            session.set_sound_design_mode("ADVANCED")
            return {
                "status": "SOUND_DESIGN_MODE_UPDATED",
                "mode": "ADVANCED",
                "action_taken": "Modo de sound design avanzado activado para la sesión.",
                "message": "Modo de sound design avanzado activado."
            }

        if any(w in norm_text for w in [
            "modo sound design clasico", "modo sound design clásico",
            "sound design clasico", "sound design clásico",
            "modo sound design legacy", "sound design legacy"
        ]):
            session.set_sound_design_mode("LEGACY")
            return {
                "status": "SOUND_DESIGN_MODE_UPDATED",
                "mode": "LEGACY",
                "action_taken": "Modo de sound design clásico (legacy) restaurado.",
                "message": "Modo de sound design clásico restaurado."
            }

        if any(w in norm_text for w in ["estado sound design", "estado de sound design", "ver sound design"]):
            curr_mode = session.get_sound_design_mode()
            return {
                "status": "SOUND_DESIGN_CONFIG_STATUS",
                "mode": curr_mode,
                "action_taken": f"Consulta de estado: el modo de sound design actual es {curr_mode}.",
                "message": f"Modo de sound design actual: {curr_mode}"
            }

        # Decent Sampler Library Directory Configuration & Query Commands
        if any(w in norm_text for w in [
            "ver librerias decent sampler", "listar librerias decent sampler",
            "librerias decent sampler", "decent sampler librerias", "ver librerias"
        ]):
            from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
            root = DecentSamplerLibraryManager.get_library_root()
            libs = DecentSamplerLibraryManager.scan_libraries(require_valid=False)
            valid_libs = [l for l in libs if l.is_valid]
            invalid_libs = [l for l in libs if not l.is_valid]
            
            lines = [f"📁 **Carpeta de librerías Decent Sampler:** `{root}`\n"]
            lines.append(f"✅ **Librerías Válidas ({len(valid_libs)}):**")
            for vl in valid_libs:
                lines.append(f"  • **{vl.name}** [{vl.role_hint}] ({vl.sample_count} samples)")
            if invalid_libs:
                lines.append(f"\n⚠️ **Librerías Descartadas / Corruptas ({len(invalid_libs)}):**")
                for il in invalid_libs:
                    err_summary = "; ".join(il.validation_errors[:2])
                    lines.append(f"  • *{il.name}*: {err_summary}")
            
            return {
                "status": "SUCCESS",
                "action_taken": f"Consulta de librerías Decent Sampler ({len(valid_libs)} válidas en {root}).",
                "question": "\n".join(lines),
                "phase": phase
            }

        m_set_lib = re.search(
            r"(?:cambiar|configurar|setear|actualizar|definir)\s+(?:la\s+)?(?:carpeta|ruta|directorio)\s+(?:de\s+)?(?:librerias|muestras|sonidos|decent\s*sampler)?\s+(?:a|en|por)?\s*[:=]?\s*([a-zA-Z]:[\\/][^\n\r]+|\/[^\n\r]+|~[\\/][^\n\r]+)",
            user_input, re.IGNORECASE
        ) or re.search(
            r"(?:carpeta|ruta|directorio)\s+(?:de\s+)?(?:librerias|decent\s*sampler)?\s*[:=]\s*([a-zA-Z]:[\\/][^\n\r]+|\/[^\n\r]+|~[\\/][^\n\r]+)",
            user_input, re.IGNORECASE
        )
        if m_set_lib:
            candidate_path = m_set_lib.group(1).strip().strip('"').strip("'")
            from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
            try:
                new_root = DecentSamplerLibraryManager.set_library_root(candidate_path)
                all_scanned = DecentSamplerLibraryManager.scan_libraries(require_valid=False)
                val_scanned = [l for l in all_scanned if l.is_valid]
                inv_scanned = [l for l in all_scanned if not l.is_valid]
                
                resp_lines = [
                    f"✅ **Carpeta de librerías Decent Sampler actualizada exitosamente:**\n`{new_root}`\n",
                    f"🔍 **Auditoría Pre-Flight completada:**",
                    f"• Librerías certificadas y listas para usar: **{len(val_scanned)}**"
                ]
                for vl in val_scanned:
                    resp_lines.append(f"  - 🎹 **{vl.name}** [{vl.role_hint}]: {vl.sample_count} muestras.")
                if inv_scanned:
                    resp_lines.append(f"• Carpetas descartadas por corrupción o sin muestras válidas: **{len(inv_scanned)}**")
                
                resp_lines.append(f"\n💡 *Esta ruta se ha guardado en la configuración persistente (`state/engine_settings.json`).*")
                
                return {
                    "status": "LIBRARY_ROOT_UPDATED",
                    "action_taken": f"Carpeta principal de Decent Sampler actualizada a {new_root} ({len(val_scanned)} librerías válidas).",
                    "question": "\n".join(resp_lines),
                    "new_library_root": str(new_root),
                    "valid_libraries_count": len(val_scanned),
                    "phase": phase
                }
            except Exception as ex_set:
                return {
                    "status": "ERROR",
                    "action_taken": f"Error al cambiar carpeta de librerías: {ex_set}",
                    "question": (
                        f"⚠️ **Error al configurar carpeta de librerías:**\n\n"
                        f"{str(ex_set)}\n\n"
                        f"Por favor verifica que la ruta exista en tu disco y sea accesible."
                    ),
                    "phase": phase
                }

        return None

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        norm = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else ""
        return self.handle(norm, user_input, session, conn, phase) if self.can_handle(norm, user_input, session, phase) else None


# ---------------------------------------------------------------------------
# 3. Procedural Composition Handler (SRP: Procedural & Exotic Compositions)
# ---------------------------------------------------------------------------
class ProceduralCompositionInterceptHandler:
    """Handles Taiko orchestrations (Taiko Pure, Taiko Shimmer) and exotic procedural compositions."""

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        if "taiko" in norm_text:
            is_pure = any(w in norm_text for w in [
                "no quiero que reproceses", "sin reprocesamiento", "cero reprocesamiento",
                "taiko puro", "pure taiko"
            ]) or ("reproces" in norm_text and any(neg in norm_text for neg in ["no", "cero", "sin", "ningun", "ningún"]))
            is_shimmer = any(w in norm_text for w in [
                "un solo efecto", "solo efecto", "single effect", "shimmer", "un solo efecto de procesamiento"
            ])
            return is_pure or is_shimmer
        return False

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        if "taiko" in norm_text:
            if any(w in norm_text for w in [
                "no quiero que reproceses", "sin reprocesamiento", "cero reprocesamiento",
                "taiko puro", "pure taiko"
            ]) or ("reproces" in norm_text and any(neg in norm_text for neg in ["no", "cero", "sin", "ningun", "ningún"])):
                from engine.composition.taiko_pure_composer import TaikoPureComposer
                deploy_res = TaikoPureComposer.deploy(conn)
                session.data["current_phase"] = "PHASE_6_COMPOSITION"
                session.data["phase_index"] = 6
                session.data["bpm"] = 112.0
                session.data["key"] = "A"
                session.data["scale"] = "Minor"
                session.data["tracks"] = deploy_res.get("tracks", [])
                session.data["resampling_session"] = {
                    "active": False,
                    "mode": "NO_REPROCESSING",
                    "reason": "Pure synthesis and live instrumentation with zero audio reprocessing requested by producer."
                }
                session._save_state(action_tag="TAIKO_PURE_ORCHESTRATED")
                return {
                    "status": "TAIKO_PURE_ORCHESTRATED",
                    "phase": "PHASE_6_COMPOSITION",
                    "phase_index": 6,
                    "bpm": 112.0,
                    "tonality": "A Minor Insen",
                    "bars": 32,
                    "scenes_count": 8,
                    "reprocessing": "NONE",
                    "tracks": session.data["tracks"],
                    "action_taken": "Taiko Ryūsei (Puro, 0 reprocesamiento de audio) desplegado en Live."
                }

            if any(w in norm_text for w in [
                "un solo efecto", "solo efecto", "single effect", "shimmer", "un solo efecto de procesamiento"
            ]):
                from engine.composition.taiko_shimmer_composer import TaikoShimmerComposer
                deploy_res = TaikoShimmerComposer.deploy(conn)
                session.data["current_phase"] = "PHASE_11_AUDIO_RESAMPLING"
                session.data["phase_index"] = 11
                session.data["bpm"] = 105.0
                session.data["key"] = "D"
                session.data["scale"] = "Minor"
                session.data["tracks"] = deploy_res.get("tracks", [])
                session.data["sections"] = deploy_res.get("scenes", [f"Scene {i+1}" for i in range(10)])
                session.data["resampling_session"] = {
                    "active": True,
                    "mode": "SINGLE_TECHNIQUE_PAD",
                    "technique_index": 6,
                    "technique": "Pitch-Shifted Shimmer Diffusion"
                }
                session._save_state(action_tag="TAIKO_SHIMMER_ORCHESTRATED")
                return {
                    "status": "TAIKO_SHIMMER_ORCHESTRATED",
                    "phase": "PHASE_11_AUDIO_RESAMPLING",
                    "phase_index": 11,
                    "bpm": 105.0,
                    "tonality": "D Minor Insen",
                    "bars": 40,
                    "scenes_count": 10,
                    "tracks": session.data["tracks"],
                    "action_taken": "Taiko Shimmer (Kaze no Hikari con Shimmer Diffusion #06) desplegado en Live."
                }
        return None

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        norm = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else ""
        return self.handle(norm, user_input, session, conn, phase) if self.can_handle(norm, user_input, session, phase) else None


# ---------------------------------------------------------------------------
# 4. Creative Continuity & Omission Audit Handler (SRP: Creative Anchors)
# ---------------------------------------------------------------------------
class CreativeContinuityInterceptHandler:
    """Handles 26 cross-phase creative invariants, omission audits, acoustic sentinels, and diagnostic queries."""

    QUERY_TRIGGERS: List[Dict[str, Any]] = [
        {"keywords": ["ver contrato", "contrato de la cancion", "contrato de la obra", "mostrar contrato", "obligaciones", "song contract"], "handler": "_handle_song_contract_query", "needs_conn": False},
        {"keywords": ["auditoria de omisiones", "auditoria omisiones", "omisiones", "que falta", "que se olvido", "obligaciones pendientes", "omission audit"], "handler": "_handle_omission_audit_query", "needs_conn": True},
        {"keywords": ["intencion creativa", "tesis sonora", "eje emocional", "anclas de identidad", "song intent"], "handler": "_handle_song_intent_query", "needs_conn": False},
        {"keywords": ["creative x-ray", "creative xray", "radiografia creativa", "radiografía creativa", "xray", "x-ray", "espejo perceptual"], "handler": "_handle_creative_xray_query", "needs_conn": True},
        {"keywords": ["ver arco emocional", "arco emocional", "dynamic tension", "tension macro", "retencion de inercia", "curva emocional"], "handler": "_handle_emotional_arc_query", "needs_conn": False},
        {"keywords": ["ver arquitectura de buses", "arquitectura de buses", "buses submaster", "submaster buses", "buses de mezcla", "stem buses", "ver buses"], "handler": "_handle_bus_architecture_query", "needs_conn": False},
        {"keywords": ["evaluar gancho", "analizar gancho", "ver gancho", "hook factor", "hook theory", "contorno melodico", "retencion melodica"], "handler": "_handle_hook_evaluation_query", "needs_conn": False},
        {"keywords": ["inyectar ear candy", "ear candy", "micro transiciones", "gestos de ear candy", "ver ear candy"], "handler": "_handle_ear_candy_query", "needs_conn": False},
        {"keywords": ["reverbs duckeados", "space ducking", "delays duckeados", "ducking de reverb", "ver space ducking"], "handler": "_handle_space_ducking_query", "needs_conn": False},
        {"keywords": ["intercambio modal", "prestamos modales", "voice leading", "acordes prestados", "conduccion de voces"], "handler": "_handle_modal_harmony_query", "needs_conn": False},
        {"keywords": ["modulacion metrica", "polirritmias", "metric modulation", "subdivisiones metricas", "rolls metricos"], "handler": "_handle_metric_modulation_query", "needs_conn": False},
        {"keywords": ["call and response", "antiphonal dialogue", "dialogo antifonal", "llamada y respuesta", "ver call and response", "ver dialogo antifonal"], "handler": "_handle_antiphonal_dialogue_query", "needs_conn": True},
        {"keywords": ["alinear fase", "phase correlation", "correlacion de fase", "polaridad low end", "phase alignment", "ver fase", "alineacion de fase"], "handler": "_handle_phase_correlation_query", "needs_conn": True},
        {"keywords": ["anti enmascaramiento", "anti-enmascaramiento", "resonance carver", "tallado dinamico", "carving", "ver enmascaramiento", "ecualizacion dinamica"], "handler": "_handle_resonance_carver_query", "needs_conn": True},
        {"keywords": ["crossover", "crossover stacker", "separacion de capas", "tres bandas", "multibanda psicoacustico", "ver crossover"], "handler": "_handle_crossover_stacking_query", "needs_conn": True},
        {"keywords": ["armonias vocales", "vocal harmonies", "coros estereo", "generar armonias", "voces dobles", "ver armonias"], "handler": "_handle_vocal_harmonies_query", "needs_conn": True},
        {"keywords": ["ver fills", "redobles adaptativos", "drum fills", "redobles de bateria", "turnaround fill", "redobles"], "handler": "_handle_drum_fills_query", "needs_conn": True},
        {"keywords": ["tape stop", "micro-edits", "micro edits", "stutter glitch", "parada de cinta", "ver tape stop"], "handler": "_handle_micro_stutter_query", "needs_conn": True},
        {"keywords": ["desplazamiento metrico", "offbeat displacement", "contratiempo", "sincopa contratiempo", "ver desplazamiento"], "handler": "_handle_metric_displacement_query", "needs_conn": True},
        {"keywords": ["profundidad z", "plano z", "eje z", "z plane depth", "ver profundidad z", "escala z"], "handler": "_handle_z_plane_depth_query", "needs_conn": True},
        {"keywords": ["apertura de bajo", "sub to stereo", "sub-to-stereo", "morfologia sub", "sub a estereo", "ver apertura sub"], "handler": "_handle_sub_stereo_morph_query", "needs_conn": True},
        {"keywords": ["textura foley", "foley bed", "foley subliminal", "capa foley", "ruido vinilo", "ver foley"], "handler": "_handle_foley_bed_query", "needs_conn": True},
        {"keywords": ["factor de cresta", "crest factor", "optimizador de headroom", "headroom pre master", "ver factor de cresta"], "handler": "_handle_crest_factor_query", "needs_conn": True},
        {"keywords": ["mutacion hi hats", "mutacion hi-hats", "hi-hat mutator", "rolls estocasticos", "mutacion hihat", "ver hi hats"], "handler": "_handle_hihat_mutation_query", "needs_conn": True},
        {"keywords": ["nota pedal", "pedal point", "tension armonica pedal", "suspensiones", "acordes sus", "ver nota pedal"], "handler": "_handle_pedal_suspension_query", "needs_conn": False},
        {"keywords": ["filtro underwater", "underwater sweep", "ruptura acustica", "filtro radio", "transicion underwater", "ver underwater"], "handler": "_handle_underwater_sweep_query", "needs_conn": True},
    ]

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        return any(any(kw in norm_text for kw in entry["keywords"]) for entry in self.QUERY_TRIGGERS)

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        for entry in self.QUERY_TRIGGERS:
            if any(kw in norm_text for kw in entry["keywords"]):
                method_name = entry["handler"]
                if hasattr(session, method_name):
                    method = getattr(session, method_name)
                    return method(conn) if entry["needs_conn"] else method()
        return None

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        norm = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else ""
        return self.handle(norm, user_input, session, conn, phase) if self.can_handle(norm, user_input, session, phase) else None


# ---------------------------------------------------------------------------
# 5. Active Sub-State Intercept Handler (SRP: Modal Sub-Step Progression)
# ---------------------------------------------------------------------------
class ActiveSubStateInterceptHandler:
    """Manages modal sub-steps requiring persistent user feedback or multi-turn dialogues."""

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        sdata = getattr(session, "data", {})
        if sdata.get("awaiting_effect_recalibration", False):
            return True
        if sdata.get("instrument_swap_state"):
            return True
        # Global swap trigger in Phases 6, 7, 9, 10
        is_swap_trigger = any(w in norm_text for w in [
            "cambiar instrumento", "cambiar sonido", "cambio de instrumento", "cambio de sonido",
            "reemplazar instrumento", "reemplazar sonido", "otro instrumento", "swap instrument",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger and phase in ("PHASE_6_COMPOSITION", "PHASE_7_AUTOMATION", "PHASE_9_MIX_MASTER", "PHASE_10_COMPLETED"):
            return True
        # Modular Phase 6 Composition active sub-state
        if phase == "PHASE_6_COMPOSITION" and sdata.get("composition_session", {}).get("active", False):
            return True
        # Surgical Phase 7 Automation active sub-state
        if phase == "PHASE_7_AUTOMATION" and sdata.get("automation_session", {}).get("active", False):
            return True
        # Pre-vocal panning decision
        if sdata.get("awaiting_pre_vocal_panning", False):
            return True
        # LUFS Calibration Gatekeeper active sub-state
        if sdata.get("lufs_gate_active", False):
            return True
        # Vocal workflow choice active sub-state
        if sdata.get("awaiting_vocal_workflow_choice", False):
            return True
        # Phase 11 Audio Resampling trigger
        is_resampling_trigger = any(w in norm_text for w in [
            "resamplear", "resampling", "reprocesar", "catalogo de reprocesamiento",
            "catálogo de reprocesamiento", "resintesis", "resíntesis", "uhts"
        ])
        if is_resampling_trigger and phase in ("PHASE_10_COMPLETED", "PHASE_9_COMPLETED"):
            return True
        return False

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        sdata = session.data

        if sdata.get("awaiting_effect_recalibration", False):
            return session._handle_effect_recalibration(conn, user_input)

        if sdata.get("instrument_swap_state"):
            return session._handle_instrument_swap_step(conn, user_input)

        # Global Instrument Swap Trigger across Phases 6, 7, 9, 10
        is_swap_trigger = any(w in norm_text for w in [
            "cambiar instrumento", "cambiar sonido", "cambio de instrumento", "cambio de sonido",
            "reemplazar instrumento", "reemplazar sonido", "otro instrumento", "swap instrument",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger and phase in ("PHASE_6_COMPOSITION", "PHASE_7_AUTOMATION", "PHASE_9_MIX_MASTER", "PHASE_10_COMPLETED"):
            failed_t_idx = sdata.get("pending_instrument_swap_track")
            if failed_t_idx is not None:
                tracks = sdata.get("tracks", [])
                target_t = next((t for t in tracks if t.get("index") == failed_t_idx), None)
                if target_t:
                    sdata["instrument_swap_state"] = {
                        "active": True,
                        "stage": "SELECT_PRESET",
                        "track_index": target_t.get("index"),
                        "track_name": target_t.get("name"),
                        "track_role": target_t.get("role"),
                        "origin_phase": phase
                    }
                    session._save_state()
                    return session._prompt_instrument_swap_preset(target_t)
            return session._initiate_instrument_swap_flow(conn, user_input)

        # Active state for Modular Phase 6 Composition
        if phase == "PHASE_6_COMPOSITION" and sdata.get("composition_session", {}).get("active", False):
            return session._handle_modular_composition_step(conn, user_input)

        # Active state for Surgical Phase 7 Automation (Clip by Clip)
        if phase == "PHASE_7_AUTOMATION" and sdata.get("automation_session", {}).get("active", False):
            return session._handle_surgical_automation_step(conn, user_input)

        # Active state for Awaiting Pre-Vocal Panning Decision
        if sdata.get("awaiting_pre_vocal_panning", False):
            return session._handle_pre_vocal_panning(conn, user_input)

        # Active state for LUFS Calibration Gatekeeper
        if sdata.get("lufs_gate_active", False):
            return session._handle_dual_lufs_validation(conn, user_input)

        # Active state for Awaiting Vocal Workflow Choice (2 Partes)
        if sdata.get("awaiting_vocal_workflow_choice", False):
            return session._handle_phase_10(conn, user_input)

        # Trigger for Phase 11 Audio Resampling & Reprocessing Catalog from Phase 10
        is_resampling_trigger = any(w in norm_text for w in [
            "resamplear", "resampling", "reprocesar", "catalogo de reprocesamiento",
            "catálogo de reprocesamiento", "resintesis", "resíntesis", "uhts"
        ])
        if is_resampling_trigger and phase in ("PHASE_10_COMPLETED", "PHASE_9_COMPLETED"):
            sdata["current_phase"] = "PHASE_11_AUDIO_RESAMPLING"
            sdata["phase_index"] = 11
            session._save_state(action_tag="ENTER_PHASE_11")
            from engine.production.copilot.phases.phase_11_resampling import Phase11ResamplingHandler
            handler = Phase11ResamplingHandler()
            return handler.prompt(session, conn=conn)

        return None

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        norm = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else ""
        return self.handle(norm, user_input, session, conn, phase) if self.can_handle(norm, user_input, session, phase) else None


# ---------------------------------------------------------------------------
# 6. Vocal & Mix Action Intercept Handler (SRP: Direct Production Actions)
# ---------------------------------------------------------------------------
class VocalAndMixActionInterceptHandler:
    """Handles vocal chops, vocal channel sculpting, direct tuning, panning, and LUFS calibration."""

    def can_handle(self, norm_text: str, user_input: str, session: Any, phase: str) -> bool:
        # Vocal take processing trigger
        is_vocal_trigger = (
            (
                any(w in norm_text for w in ["vocal", "voz", "voces", "toma continua", "toma vocal", "audio vocal", "vocal chop", "vocal chops", "ambos en 2 partes"])
                and any(w in norm_text for w in ["corta", "cortalo", "cortar", "rebanar", "trocear", "chop", "chops", "chopp", "choppealo", "chopea", "chopear", "frases", "frase", "procesar toma", "alinear toma", "ambos en 2 partes", "opcion 3 ambos"])
            ) or any(w in norm_text for w in [
                "ya grabe", "ya lo grabe", "toma lista", "grabe la voz", "grabo la voz", "voz lista", "procesar voz", "grabar voz"
            ])
        ) and (phase in ("PHASE_10_COMPLETED", "PHASE_9_MIX_MASTER") or any(w in norm_text for w in ["grabe", "toma", "chop", "cortar", "rebanar"]))
        if is_vocal_trigger:
            return True

        # Vocal effect chain sculpting
        if any(w in norm_text for w in ["efectos", "cadena", "cadenas", "configurar", "obligando", "obligar", "esculpir", "autotune", "auto-tune"]) and any(w in norm_text for w in ["vocal", "voz"]):
            return True

        # Direct tuning intercept
        if any(w in norm_text for w in ["afinar en", "cambiar escala", "cambiar tonalidad", "ajustar escala", "escala a", "tonalidad a", "afinar sesion"]):
            return True

        # Direct retroactive effect adjustment trigger
        if any(w in norm_text for w in ["ajustar efecto", "ajustar efectos", "modificar efecto", "modificar efectos", "cambiar filtro", "retocar reverb", "retocar efecto", "corregir efectos"]):
            return True

        # Direct panning and spatial separation trigger
        if any(w in norm_text for w in ["panear", "paneo", "separacion estereo", "solapamiento", "antienmascaramiento", "abrir estereo", "campo estereo"]):
            return True

        # Out-of-phase LUFS validation trigger
        if phase not in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER") and any(w in norm_text for w in ["lufs", "luffs", "sonoridad", "loudness"]):
            return True

        # Automation preferences
        if any(w in norm_text for w in ["automatizacion por clip", "automatizacion quirurgica", "automatizaciones por clip", "automatizaciones quirurgicas"]):
            return True
        if any(w in norm_text for w in ["automatizacion express", "automatizacion en lote", "automatizacion por todo el tema", "automatizaciones express"]):
            return True

        return False

    def handle(self, norm_text: str, user_input: str, session: Any, conn: Any, phase: str) -> Optional[Dict[str, Any]]:
        # 1. Priority intercept for vocal take processing, slicing, chops, and gain calibration
        is_vocal_trigger = (
            (
                any(w in norm_text for w in ["vocal", "voz", "voces", "toma continua", "toma vocal", "audio vocal", "vocal chop", "vocal chops", "ambos en 2 partes"])
                and any(w in norm_text for w in ["corta", "cortalo", "cortar", "rebanar", "trocear", "chop", "chops", "chopp", "choppealo", "chopea", "chopear", "frases", "frase", "procesar toma", "alinear toma", "ambos en 2 partes", "opcion 3 ambos"])
            ) or any(w in norm_text for w in [
                "ya grabe", "ya lo grabe", "toma lista", "grabe la voz", "grabo la voz", "voz lista", "procesar voz", "grabar voz"
            ])
        ) and (phase in ("PHASE_10_COMPLETED", "PHASE_9_MIX_MASTER") or any(w in norm_text for w in ["grabe", "toma", "chop", "cortar", "rebanar"]))
        if is_vocal_trigger:
            if not session.data.get("panning_evaluated", False):
                tracks = session.data.get("tracks", [])
                inst_tracks = [t for t in tracks if t.get("role") != "VOCALS" and not t.get("is_foldable", False)]
                if len(inst_tracks) >= 2:
                    from engine.mix.spatial_panning import InstrumentPanningEvaluator
                    p_audit = InstrumentPanningEvaluator.evaluate_session_panning(tracks, conn=conn)
                    if p_audit.get("has_masking_risk", False):
                        return session._prompt_pre_vocal_panning(conn, pending_vocal_input=user_input)
            return session._handle_phase_10(conn, user_input)

        # 2. Vocal effect chain sculpting & mandatory configuration
        if any(w in norm_text for w in ["efectos", "cadena", "cadenas", "configurar", "obligando", "obligar", "esculpir", "autotune", "auto-tune"]) and any(w in norm_text for w in ["vocal", "voz"]):
            tracks = session.data.get("tracks", [])
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
                session.data["tracks"] = tracks
            v_idx = tracks.index(v_trk)
            session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            session.data["phase_index"] = 5
            session.data["current_fx_track_ptr"] = v_idx
            session.data["current_fx_dev_ptr"] = 0
            session._save_state()
            prompt = session._prompt_current_fx_device()
            prompt["action_taken"] = "Iniciando esculpido obligatorio de la cadena de efectos vocales paso a paso."
            return prompt

        # 3. Direct tuning intercept
        if any(w in norm_text for w in ["afinar en", "cambiar escala", "cambiar tonalidad", "ajustar escala", "escala a", "tonalidad a", "afinar sesion"]):
            d_key, d_scale, _ = parse_autotune_settings(user_input)
            if not d_key:
                km = re.search(r'\b([a-g][#b]?)\b', norm_text)
                if km:
                    d_key = km.group(1).upper()
            f_key = d_key or session.data.get("key", "F")
            f_scale = d_scale or session.data.get("scale", "Minor")
            session.data["key"] = f_key
            session.data["scale"] = f_scale
            tune_res = session._sync_session_tuning(conn, f_key, f_scale)
            session._save_state()
            return {
                "status": "SESSION_TUNED",
                "action_taken": f"Tonalidad sincronizada a {f_key} {f_scale} en Ableton Live 12 y plugins de pitch.",
                "phase": phase,
                "tuning_details": tune_res,
                "question": f"✅ **Sesión afinada en {f_key} {f_scale}.** Live 12 y Auto-Tune actualizados. ¿Deseas continuar con {phase}?"
            }

        # 4. Direct retroactive effect adjustment trigger
        if any(w in norm_text for w in ["ajustar efecto", "ajustar efectos", "modificar efecto", "modificar efectos", "cambiar filtro", "retocar reverb", "retocar efecto", "corregir efectos"]):
            return session._prompt_effect_recalibration()

        # 5. Direct panning and spatial separation trigger
        if any(w in norm_text for w in ["panear", "paneo", "separacion estereo", "solapamiento", "antienmascaramiento", "abrir estereo", "campo estereo"]):
            return session._handle_direct_panning_command(conn, user_input)

        # 6. Immediate priority intercept for dual-stage LUFS validation (channel + master)
        if phase not in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER") and any(w in norm_text for w in ["lufs", "luffs", "sonoridad", "loudness"]):
            return session._handle_dual_lufs_validation(conn, user_input)

        # 7. Direct preference configuration for automation mode (clip_by_clip vs express)
        if any(w in norm_text for w in ["automatizacion por clip", "automatizacion quirurgica", "automatizaciones por clip", "automatizaciones quirurgicas"]):
            try:
                from engine.memory.user_learning import save_user_preference
                save_user_preference("automation", "mode", "clip_by_clip")
            except Exception:
                pass
            if phase == "PHASE_7_AUTOMATION":
                return session._init_surgical_automation(conn)
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

        return None

    def handle_intercept(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        norm = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else ""
        return self.handle(norm, user_input, session, conn, phase) if self.can_handle(norm, user_input, session, phase) else None


# ---------------------------------------------------------------------------
# 7. Intercept Handler Registry (OCP & DIP: Extensible Handler Pipeline)
# ---------------------------------------------------------------------------
class InterceptHandlerRegistry:
    """Maintains prioritized registry of intercept handlers conforming to InterceptHandlerProtocol."""

    def __init__(self):
        self._handlers: List[Any] = [
            GovernanceInterceptHandler(),
            SoundDesignInterceptHandler(),
            ProceduralCompositionInterceptHandler(),
            CreativeContinuityInterceptHandler(),
            ActiveSubStateInterceptHandler(),
            VocalAndMixActionInterceptHandler(),
        ]

    def get_handlers(self) -> List[Any]:
        return list(self._handlers)

    def register_handler(self, handler: Any, index: Optional[int] = None) -> None:
        """Dynamically registers an intercept handler (Open/Closed Principle - OCP)."""
        if index is not None:
            self._handlers.insert(index, handler)
        else:
            self._handlers.append(handler)

    def dispatch(self, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        """Dispatches user input sequentially through registered handlers."""
        norm_text = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS") if hasattr(session, "data") else "PHASE_1_TRACKS"

        for handler in self._handlers:
            if hasattr(handler, "can_handle") and handler.can_handle(norm_text, user_input, session, phase):
                res = handler.handle(norm_text, user_input, session, conn, phase)
                if res is not None:
                    return res
        return None

    _instance: Optional["InterceptHandlerRegistry"] = None

    @classmethod
    def default(cls) -> "InterceptHandlerRegistry":
        if cls._instance is None:
            cls._instance = InterceptHandlerRegistry()
        return cls._instance


# ---------------------------------------------------------------------------
# 8. High-Level Facade (Backward Compatibility & LSP)
# ---------------------------------------------------------------------------
class CopilotInterceptRouter:
    """Evaluates user input against global cross-phase triggers and modal sub-step states."""

    registry = InterceptHandlerRegistry.default()

    @classmethod
    def intercept(cls, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        """Processes global commands or active sub-step intercepts via the handler pipeline."""
        return cls.registry.dispatch(session, conn, user_input)

    @classmethod
    def register_handler(cls, handler: Any, index: Optional[int] = None) -> None:
        """Extensibility point to attach specialized handlers at runtime."""
        cls.registry.register_handler(handler, index=index)

# engine/production/copilot/intercept_router.py
"""
Copilot Global Intercept Router (Chain of Responsibility & Single Responsibility Principle - SRP):
Separates global keyword commands, multi-phase triggers, and active modal sub-states
from standard sequential phase progression in CopilotGuidedSession.
"""

from typing import Dict, Any, Optional
import re
import logging
from engine.production.copilot.nlp_parser import _normalize_text, parse_autotune_settings

logger = logging.getLogger("CopilotInterceptRouter")


class CopilotInterceptRouter:
    """Evaluates user input against global cross-phase triggers and modal sub-step states."""

    @classmethod
    def intercept(cls, session: Any, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Processes global commands or active sub-step intercepts.
        Returns a response dict if intercepted, or None to continue normal phase dispatch.
        """
        norm_text = _normalize_text(user_input)
        phase = session.data.get("current_phase", "PHASE_1_TRACKS")

        # 1. Creative Continuity & Omission Audit Queries
        if any(w in norm_text for w in ["ver contrato", "contrato de la cancion", "contrato de la obra", "mostrar contrato", "obligaciones", "song contract"]):
            return session._handle_song_contract_query()

        if any(w in norm_text for w in ["auditoria de omisiones", "auditoria omisiones", "omisiones", "que falta", "que se olvido", "obligaciones pendientes", "omission audit"]):
            return session._handle_omission_audit_query(conn)

        if any(w in norm_text for w in ["intencion creativa", "tesis sonora", "eje emocional", "anclas de identidad", "song intent"]):
            return session._handle_song_intent_query()

        if any(w in norm_text for w in ["creative x-ray", "creative xray", "radiografia creativa", "radiografía creativa", "xray", "x-ray", "espejo perceptual"]):
            return session._handle_creative_xray_query(conn)

        # Emotional Arc Director Query
        if any(w in norm_text for w in ["ver arco emocional", "arco emocional", "dynamic tension", "tension macro", "retencion de inercia", "curva emocional"]):
            return session._handle_emotional_arc_query()

        # Bus Submaster Architecture Query
        if any(w in norm_text for w in ["ver arquitectura de buses", "arquitectura de buses", "buses submaster", "submaster buses", "buses de mezcla", "stem buses", "ver buses"]):
            return session._handle_bus_architecture_query()

        # Hook Theory & Hook Factor Query
        if any(w in norm_text for w in ["evaluar gancho", "analizar gancho", "ver gancho", "hook factor", "hook theory", "contorno melodico", "retencion melodica"]):
            return session._handle_hook_evaluation_query()

        # Smart Ear Candy & Micro-Transitions Query
        if any(w in norm_text for w in ["inyectar ear candy", "ear candy", "micro transiciones", "gestos de ear candy", "ver ear candy"]):
            return session._handle_ear_candy_query()

        # Dynamic Space Ducking (Reverbs & Delays Duckeados con Bloom) Query
        if any(w in norm_text for w in ["reverbs duckeados", "space ducking", "delays duckeados", "ducking de reverb", "ver space ducking"]):
            return session._handle_space_ducking_query()

        # Modal Interchange & Voice Leading Query
        if any(w in norm_text for w in ["intercambio modal", "prestamos modales", "voice leading", "acordes prestados", "conduccion de voces"]):
            return session._handle_modal_harmony_query()

        # Micro-Rhythmic Metric Modulation & Polyrhythms Query
        if any(w in norm_text for w in ["modulacion metrica", "polirritmias", "metric modulation", "subdivisiones metricas", "rolls metricos"]):
            return session._handle_metric_modulation_query()

        # Antiphonal Dialogue & Core Call & Response Query
        if any(w in norm_text for w in ["call and response", "antiphonal dialogue", "dialogo antifonal", "llamada y respuesta", "ver call and response", "ver dialogo antifonal"]):
            return session._handle_antiphonal_dialogue_query(conn)

        # Low-End Phase & Polarity Correlation Sentinel Query
        if any(w in norm_text for w in ["alinear fase", "phase correlation", "correlacion de fase", "polaridad low end", "phase alignment", "ver fase", "alineacion de fase"]):
            return session._handle_phase_correlation_query(conn)

        # Smart Resonance Anti-Masking Carver Query
        if any(w in norm_text for w in ["anti enmascaramiento", "anti-enmascaramiento", "resonance carver", "tallado dinamico", "carving", "ver enmascaramiento", "ecualizacion dinamica"]):
            return session._handle_resonance_carver_query(conn)

        # Psychoacoustic Crossover Multi-Layer Stacker Query
        if any(w in norm_text for w in ["crossover", "crossover stacker", "separacion de capas", "tres bandas", "multibanda psicoacustico", "ver crossover"]):
            return session._handle_crossover_stacking_query(conn)

        # Vocal Harmony & Stereo Spread Engine Query
        if any(w in norm_text for w in ["armonias vocales", "vocal harmonies", "coros estereo", "generar armonias", "voces dobles", "ver armonias"]):
            return session._handle_vocal_harmonies_query(conn)

        # High-Fidelity Adaptive Drum Fills Query
        if any(w in norm_text for w in ["ver fills", "redobles adaptativos", "drum fills", "redobles de bateria", "turnaround fill", "redobles"]):
            return session._handle_drum_fills_query(conn)

        # Micro-Edits Glitch & Tape Stop Query
        if any(w in norm_text for w in ["tape stop", "micro-edits", "micro edits", "stutter glitch", "parada de cinta", "ver tape stop"]):
            return session._handle_micro_stutter_query(conn)

        # Off-Beat Metric Displacer Query
        if any(w in norm_text for w in ["desplazamiento metrico", "offbeat displacement", "contratiempo", "sincopa contratiempo", "ver desplazamiento"]):
            return session._handle_metric_displacement_query(conn)

        # Z-Plane Psychoacoustic Depth Query
        if any(w in norm_text for w in ["profundidad z", "plano z", "eje z", "z plane depth", "ver profundidad z", "escala z"]):
            return session._handle_z_plane_depth_query(conn)

        # Dynamic Sub-to-Stereo Morpher Query
        if any(w in norm_text for w in ["apertura de bajo", "sub to stereo", "sub-to-stereo", "morfologia sub", "sub a estereo", "ver apertura sub"]):
            return session._handle_sub_stereo_morph_query(conn)

        # Atmospheric Foley Bed Generator Query
        if any(w in norm_text for w in ["textura foley", "foley bed", "foley subliminal", "capa foley", "ruido vinilo", "ver foley"]):
            return session._handle_foley_bed_query(conn)

        # Pre-Master Crest Factor & Headroom Optimizer Query
        if any(w in norm_text for w in ["factor de cresta", "crest factor", "optimizador de headroom", "headroom pre master", "ver factor de cresta"]):
            return session._handle_crest_factor_query(conn)

        # Evolutionary Hi-Hat Mutator Query
        if any(w in norm_text for w in ["mutacion hi hats", "mutacion hi-hats", "hi-hat mutator", "rolls estocasticos", "mutacion hihat", "ver hi hats"]):
            return session._handle_hihat_mutation_query(conn)

        # Harmonic Pedal Point & Suspension Weaver Query
        if any(w in norm_text for w in ["nota pedal", "pedal point", "tension armonica pedal", "suspensiones", "acordes sus", "ver nota pedal"]):
            return session._handle_pedal_suspension_query(conn)

        # Underwater & Radio Acoustic Sweep Transition Query
        if any(w in norm_text for w in ["filtro underwater", "underwater sweep", "ruptura acustica", "filtro radio", "transicion underwater", "ver underwater"]):
            return session._handle_underwater_sweep_query(conn)

        # 2. Active sub-states (Awaiting Recalibration, Swap, Pre-Vocal Panning, LUFS, etc.)
        if session.data.get("awaiting_effect_recalibration", False):
            return session._handle_effect_recalibration(conn, user_input)

        if session.data.get("instrument_swap_state"):
            return session._handle_instrument_swap_step(conn, user_input)

        # Global Instrument Swap Trigger across Phases 6, 7, 9, 10
        is_swap_trigger = any(w in norm_text for w in [
            "cambiar instrumento", "cambiar sonido", "cambio de instrumento", "cambio de sonido",
            "reemplazar instrumento", "reemplazar sonido", "otro instrumento", "swap instrument",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger and phase in ("PHASE_6_COMPOSITION", "PHASE_7_AUTOMATION", "PHASE_9_MIX_MASTER", "PHASE_10_COMPLETED"):
            failed_t_idx = session.data.get("pending_instrument_swap_track")
            if failed_t_idx is not None:
                tracks = session.data.get("tracks", [])
                target_t = next((t for t in tracks if t.get("index") == failed_t_idx), None)
                if target_t:
                    session.data["instrument_swap_state"] = {
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
        if phase == "PHASE_6_COMPOSITION" and session.data.get("composition_session", {}).get("active", False):
            return session._handle_modular_composition_step(conn, user_input)

        # Active state for Surgical Phase 7 Automation (Clip by Clip)
        if phase == "PHASE_7_AUTOMATION" and session.data.get("automation_session", {}).get("active", False):
            return session._handle_surgical_automation_step(conn, user_input)

        # Active state for Awaiting Pre-Vocal Panning Decision
        if session.data.get("awaiting_pre_vocal_panning", False):
            return session._handle_pre_vocal_panning(conn, user_input)

        # Active state for LUFS Calibration Gatekeeper
        if session.data.get("lufs_gate_active", False):
            return session._handle_dual_lufs_validation(conn, user_input)

        # Active state for Awaiting Vocal Workflow Choice (2 Partes)
        if session.data.get("awaiting_vocal_workflow_choice", False):
            return session._handle_phase_10(conn, user_input)

        # 3. Priority intercept for vocal take processing, slicing, chops, and gain calibration
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

        # 4. Vocal effect chain sculpting & mandatory configuration
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

        # 5. Direct tuning intercept
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

        # 6. Direct retroactive effect adjustment trigger
        if any(w in norm_text for w in ["ajustar efecto", "ajustar efectos", "modificar efecto", "modificar efectos", "cambiar filtro", "retocar reverb", "retocar efecto", "corregir efectos"]):
            return session._prompt_effect_recalibration()

        # 7. Direct panning and spatial separation trigger
        if any(w in norm_text for w in ["panear", "paneo", "separacion estereo", "solapamiento", "antienmascaramiento", "abrir estereo", "campo estereo"]):
            return session._handle_direct_panning_command(conn, user_input)

        # 8. Immediate priority intercept for dual-stage LUFS validation (channel + master)
        if phase not in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER") and any(w in norm_text for w in ["lufs", "luffs", "sonoridad", "loudness"]):
            return session._handle_dual_lufs_validation(conn, user_input)

        # 9. Direct preference configuration for automation mode (clip_by_clip vs express)
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

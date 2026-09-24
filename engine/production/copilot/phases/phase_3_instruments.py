# engine/production/copilot/phases/phase_3_instruments.py
"""
Phase 3: Verified instrument loading, two-level hierarchical plugin selection,
SubLab XL prioritization, and Drum Rack verification.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.production.copilot.track_utils import get_personal_samples
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.instruments.browser_catalog import LiveBrowserCatalogEngine, InstrumentSourceCategory
from engine.instruments.drum_rack_guard import DrumRackGuard

logger = logging.getLogger("Phase3Instruments")

class Phase3InstrumentsHandler(BasePhaseHandler):
    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_current_track_instrument(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_3(session, conn, user_input)

    def _prompt_current_track_instrument(self, session: Any) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        ptr = session.data.get("current_track_ptr", 0)
    
        if ptr >= len(tracks):
            session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
            session.data["phase_index"] = 4
            session.data["current_param_ptr"] = 0
            session._save_state()
            return session._prompt_current_track_params()
    
        trk = tracks[ptr]
        t_idx = trk["index"]
        t_name = trk["name"]
        role = trk["role"]
        is_audio = trk.get("is_audio", False) or role == "VOCALS"
        is_fx_audio = (role == "FX" and is_audio) or trk.get("is_fx_audio", False)
    
        # Audio FX Track / Parallel Bus Routing Selection
        if is_fx_audio:
            routing_candidates = []
            for other_t in tracks:
                if other_t.get("index") != t_idx:
                    routing_candidates.append(f"  • Pista {other_t.get('index')}: **{other_t.get('name')}** (Rol: `{other_t.get('role')}`)")
            routing_block = "\n".join(routing_candidates) if routing_candidates else "  • Sin otras pistas registradas (se mantendrá entrada externa)."
    
            opts_text = [
                "  1. 🌀 **Cableguys ShaperBox 3** (Modulación Rítmica Multiefecto): Curvas de volumen (ducking/stutter), paneo y filtros rítmicos sincronizados al tempo militar.",
                "  2. 🔥 **Output Thermal** (Saturación y Distorsión Multibanda): Armónicos industriales abrasivos y crunch agresivo con macros dinámicos.",
                "  3. 🌌 **Valhalla DSP ValhallaVintageVerb** (Espacio Algorítmico): Espacialidad profunda, colas de reverb densas y reflexiones ambientales estéreo.",
                "  4. 📼 **FabFilter Saturn 2** (Saturación de Válvulas y Cinta): Distorsión armónica multibanda para dar calidez o mordida analógica.",
                "  5. 🎛️ **Ableton Native Audio Effects** (Saturator / Dynamic Tube / Echo / Redux): Cadenas de procesamiento nativo ultraligeras de latencia cero."
            ]
            options_block = "\n".join(opts_text)
    
            return {
                "current_step": f"PASO 3 DE 7: CONFIGURACIÓN DE PISTA DE EFECTO DE AUDIO (PISTA {ptr + 1} DE {len(tracks)})",
                "action_taken": f"Configurando bus de efecto de audio Pista {t_idx}: {t_name} ({role}).",
                "question": (
                    f"🎛️ **Paso 3 de 7: Efecto de Audio y Ruteo de Entrada para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                    f"Esta pista funcionará como **canal de efecto de audio / bus de retorno** en Ableton Live.\n\n"
                    f"**Efectos de Audio Disponibles:**\n"
                    f"{options_block}\n\n"
                    f"**Pistas Fuentes Disponibles para Ruteo de Entrada:**\n"
                    f"{routing_block}\n\n"
                    f"💡 *El motor cargará el plugin, configurará el ruteo interno (`input_routing_type`) y activará la monitorización en tiempo real (`In`) para que el procesamiento sea audible de inmediato.*\n\n"
                    f"• *Indica el efecto y la pista de origen (ej: 'ShaperBox 3 desde Lead', 'Opción 1 con entrada de Drums', o 'Thermal desde Bass').*"
                ),
                "instructions_for_ai": f"Especifica el efecto de audio y la pista de origen para el ruteo de entrada en {t_name}.",
                "target_track": t_idx,
                "role": role,
                "is_audio": True,
                "is_fx_audio": True,
                "phase": "PHASE_3_INSTRUMENTS"
            }
    
        # Audio / Vocal Track Take Selection
        if is_audio and role == "VOCALS" and not trk.get("chopping_mode"):
            p_samples = get_personal_samples("vocal")
            v_samples = [s for s in p_samples if "vocal" in str(s.get("folder", "")).lower() or "vocales" in str(s.get("folder", "")).lower() or any(k in str(s.get("name", "")).lower() for k in ["duki", "vocal", "vox", "kanye", "bts"])]
            sample_names_sample = ", ".join([s["name"] for s in v_samples[:3]]) if v_samples else "duki.mp3, bts.mp3"
    
            opts_text = [
                "  1. 🎙️ **Grabar mi propia voz en vivo (Live Tracking & Mic In)** (Recomendada): Prepara el canal para grabación física con micrófono: arma la pista en Live (`arm = True`), activa monitorización de baja latencia (`Auto`) e inserta cadena de tracking limpia (`EQ Eight` corte pasa-altos en 90 Hz + `Compressor` suave de captura). La grabación será troceada automáticamente con Whisper en la fase de composición.",
                f"  2. 📁 **Cargar toma existente de mi librería personal**: Importa un archivo de audio o a capella desde tu carpeta (`{sample_names_sample}`).",
                "  3. 🔪 **Modo Chopping / Simpler Vocal**: Convierte frases o samples vocales en rebanadas para tocarlas rítmicamente con teclado MIDI."
            ]
    
            options_block = "\n".join(opts_text)
            return {
                "current_step": f"PASO 3 DE 7: ASIGNACIÓN DE MODO VOCAL (PISTA {ptr + 1} DE {len(tracks)})",
                "action_taken": f"Configurando canal vocal Pista {t_idx}: {t_name} ({role}).",
                "question": (
                    f"🎙️ **Paso 3 de 7: Configuración de Voz / Grabación para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                    f"¿Cómo deseas producir la voz en esta pista?\n\n"
                    f"{options_block}\n\n"
                    f"• *Responde 'Opción 1' o 'Grabar voz' para armar la pista para tu micrófono y trocear la grabación.*\n"
                    f"• *Responde 'Opción 2' o el nombre de un archivo para importar una toma existente.*\n"
                    f"• *Responde 'Opción 3' o 'Chopping' para rebanar frases vocales en Simpler.*"
                ),
                "instructions_for_ai": f"Indica la opción de flujo vocal para {t_name} (Opción 1: Grabar voz en vivo, Opción 2: Cargar toma, Opción 3: Chopping).",
                "target_track": t_idx,
                "role": role,
                "is_audio": True,
                "phase": "PHASE_3_INSTRUMENTS"
            }
    
        # Multi-preset sub-selection mode (Level 2: Presets of Analog Lab V / Omnisphere + Clean default option)
        pending_plugin = trk.get("pending_plugin_subselection")
        if pending_plugin:
            sub_options = LiveBrowserCatalogEngine.get_plugin_presets_for_role(pending_plugin, role)
            sub_opts_text = []
            for s_idx, s_opt in enumerate(sub_options, 1):
                is_clean = "(Default / Plugin limpio)" in s_opt.name
                icon = "🎛️" if is_clean else "📁"
                sub_opts_text.append(f"  {s_idx}. {icon} **{s_opt.name}**: {s_opt.description}")
    
            sub_block = "\n".join(sub_opts_text)
            return {
                "current_step": f"PASO 3 DE 7: SUB-SELECCIÓN DE PRESETS ({pending_plugin}) (PISTA {ptr + 1} DE {len(tracks)})",
                "action_taken": f"Seleccionando preset o versión limpia de {pending_plugin} para Pista {t_idx}: {t_name} ({role}).",
                "question": (
                    f"🎹 **Paso 3 de 7 (Sub-nivel): Presets de {pending_plugin} para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                    f"Has seleccionado **{pending_plugin}**. Elige un preset específico de tu librería o la opción limpia/default:\n\n"
                    f"{sub_block}\n\n"
                    f"• *Responde con el número de opción o nombre del preset (ej: 'Opción 1', 'Opción {len(sub_options)}').*\n"
                    f"• *Si eliges 'Default / Plugin limpio', se cargará el VST3 base crudo y el motor te preguntará por parámetros y macros en la Fase 4 para esculpir el sonido.*\n"
                    f"• *O responde 'Volver' para regresar a la lista principal de plugins.*"
                ),
                "instructions_for_ai": f"Indica el preset o la opción limpia de {pending_plugin} para {t_name}.",
                "target_track": t_idx,
                "role": role,
                "pending_plugin_subselection": pending_plugin,
                "phase": "PHASE_3_INSTRUMENTS",
                "is_subselection": True
            }
    
        # Dynamically retrieve verified sources filtering out uninstalled VSTs (Level 1: Strictly Plugins)
        lookup_role = "GUITAR" if ("guitar" in t_name.lower() or "acustic" in t_name.lower() or "flamenc" in t_name.lower()) else (
            "PERCUSSION" if ("perc" in t_name.lower() or "palma" in t_name.lower() or "clap" in t_name.lower()) else role
        )
        cat_options = LiveBrowserCatalogEngine.get_available_sources_for_role(lookup_role, filter_installed=True)
        opts_text = []
        if cat_options:
            display_limit = min(7, len(cat_options))
            for idx, opt in enumerate(cat_options[:display_limit], 1):
                cat_val = opt.category.value if hasattr(opt.category, "value") else str(opt.category)
                tag = "🔥 VST3 Terceros" if cat_val == "vst3" else "🎛️ Nativo Live"
                opts_text.append(f"  {idx}. **{opt.name}** [{tag}]: {opt.description}")
        else:
            opts_text = [
                f"  1. **Core Library {role}** (Nativo Live 12)",
                f"  2. **Preset Analógico {role}** (Sintetizador verificado)"
            ]
    
        # Inyectar recetas quirúrgicas y emulaciones de la Base de Conocimiento
        kb_notes = []
        if role == "DRUMS":
            kb_notes.append("  💡 **Emulaciones Hardware:** SP-1200 (12-bit punch), MPC 3000 (pocket swing), TR-808/909.")
            kb_notes.append("  💡 **Sample Indexer en Parquet:** Búsqueda activa disponible en tu librería local.")
        elif role in ["BASS", "SUB"]:
            kb_notes.append("  💡 **Prioridad de Bajos:** SubLab XL (#1), Serum 2, Massive X, Massive, Cyclop.")
        elif role in ["LEAD", "SYNTH"]:
            kb_notes.append("  💡 **Receta Quirúrgica Serum 2:** `hyperpop_lead` (Sync wavetable, Portamento 35ms) o `supersaw_lead` (7 unisons).")
        elif role in ["PAD", "STRINGS"]:
            kb_notes.append("  💡 **Receta Quirúrgica Serum 2:** `analog_warm_pad` (PWM, LFO en cutoff, Reverb hall estéreo).")
        
        if kb_notes:
            opts_text.append("\n**Recetas de la Base de Conocimiento:**\n" + "\n".join(kb_notes))
    
        # Autonomous Chopping Mode (Synthesis & Internal Transformation)
        chop_idx = (min(7, len(cat_options)) if cat_options else 2) + 1
        opts_text.append(
            f"\n  {chop_idx}. 🔪 **Modo Chopping Autónomo** (Ableton Simpler con generación interna y transformación por síntesis aditiva/FM y remuestreo mutado)"
        )
    
        options_block = "\n".join(opts_text)
    
        return {
            "current_step": f"PASO 3 DE 7: CARGA DE INSTRUMENTO / KIT (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Seleccionando fuente sonora física para Pista {t_idx}: {t_name} ({role}).",
            "question": (
                f"🎹 **Paso 3 de 7: Instrumento / Kit para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                f"¿Qué generador sonoro o kit deseas cargar en esta pista?\n\n"
                f"*Instrumentos y plugins verificados (prioridad a sintetizadores de terceros, nativos al final):*\n"
                f"{options_block}\n\n"
                f"• *Responde con el número de opción o nombre de plugin (ej: 'Opción 1', 'SubLab XL', 'Serum 2').*\n"
                f"• *Si eliges Analog Lab V, Omnisphere o Decent Sampler, el asistente abrirá el sub-menú de presets o librerías auditadas y la opción de plugin limpio default.*\n"
                f"• *O selecciona el Modo Chopping Autónomo escribiendo 'Opción {chop_idx}' o 'Modo Chopping' (sintetiza una fuente armónica única, la procesa y rebanará en Simpler sin usar librerías externas).*"
            ),
            "instructions_for_ai": f"Indica la opción de instrumento o kit para {t_name}.",
            "target_track": t_idx,
            "role": role,
            "phase": "PHASE_3_INSTRUMENTS"
        }
    
    def _handle_phase_3(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        ptr = session.data.get("current_track_ptr", 0)
    
        if ptr >= len(tracks):
            session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
            session.data["phase_index"] = 4
            session.data["current_param_ptr"] = 0
            session._save_state()
            return session._prompt_current_track_params()
    
        trk = tracks[ptr]
        t_idx = session._resolve_live_track_index(conn, trk)
        role = trk["role"]
        t_name = trk.get("name", "")
        u_clean = _normalize_text(user_input)
    
        is_audio = trk.get("is_audio", False) or role == "VOCALS"
        is_fx_audio = (role == "FX" and is_audio) or trk.get("is_fx_audio", False)
        wants_chopping = any(w in u_clean for w in ["chopping", "chop", "cortar", "rebanar", "simpler", "opcion 3", "3."]) or u_clean == "3"
    
        # Audio FX Track / Parallel Bus Routing Branch
        if is_fx_audio:
            chosen_fx_name = "Cableguys ShaperBox 3"
            chosen_fx_uri = "query:Plugins#VST3:Cableguys:ShaperBox%203"
    
            if any(w in u_clean for w in ["thermal", "output", "opcion 2", "2."]) or u_clean == "2":
                chosen_fx_name = "Output Thermal"
                chosen_fx_uri = "query:Plugins#VST3:Output:Thermal"
            elif any(w in u_clean for w in ["valhalla", "reverb", "opcion 3", "3."]) or u_clean == "3":
                chosen_fx_name = "Valhalla DSP ValhallaVintageVerb"
                chosen_fx_uri = "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"
            elif any(w in u_clean for w in ["saturn", "fabfilter", "opcion 4", "4."]) or u_clean == "4":
                chosen_fx_name = "FabFilter Saturn 2"
                chosen_fx_uri = "query:Plugins#VST3:FabFilter:Saturn%202"
            elif any(w in u_clean for w in ["saturator", "nativo", "opcion 5", "5."]) or u_clean == "5":
                chosen_fx_name = "Ableton Saturator"
                chosen_fx_uri = "query:AudioFx#Saturator"
            elif "echo" in u_clean:
                chosen_fx_name = "Ableton Echo"
                chosen_fx_uri = "query:AudioFx#Echo"
            elif "redux" in u_clean:
                chosen_fx_name = "Ableton Redux"
                chosen_fx_uri = "query:AudioFx#Redux"
            elif "shaperbox" in u_clean or "shaper" in u_clean or "opcion 1" in u_clean or u_clean == "1":
                chosen_fx_name = "Cableguys ShaperBox 3"
                chosen_fx_uri = "query:Plugins#VST3:Cableguys:ShaperBox%203"
    
            # Resolve source track for input routing
            target_source_name = None
            for other_t in tracks:
                if other_t.get("index") != t_idx:
                    ot_role = str(other_t.get("role", "")).lower()
                    ot_name = str(other_t.get("name", "")).lower()
                    if ot_role in u_clean or ot_name in u_clean:
                        target_source_name = other_t.get("name")
                        break
                    for token in ot_name.replace("[", "").replace("]", "").replace("(", "").replace(")", "").split():
                        if len(token) > 2 and token in u_clean:
                            target_source_name = other_t.get("name")
                            break
                    if target_source_name:
                        break
    
            if not target_source_name:
                for cand_role in ["LEAD", "DRUMS", "BRASS", "KEYS", "BASS"]:
                    for other_t in tracks:
                        if other_t.get("index") != t_idx and other_t.get("role") == cand_role:
                            target_source_name = other_t.get("name")
                            break
                    if target_source_name:
                        break
            if not target_source_name and tracks:
                for other_t in tracks:
                    if other_t.get("index") != t_idx:
                        target_source_name = other_t.get("name")
                        break
    
            actual_routed_to = None
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    conn.send_command("load_browser_item", {
                        "track_index": t_idx,
                        "item_uri": chosen_fx_uri
                    })
                except Exception as ex_fx_load:
                    logger.warning(f"Notice loading audio FX device on track {t_idx}: {ex_fx_load}")
    
                if target_source_name:
                    clean_source_query = target_source_name.lower().replace("[", "").replace("]", "").strip()
                    code_route = f"""
t = song.tracks[{t_idx}]
t.current_monitoring_state = 0
target_q = "{clean_source_query}"
matched_rt = None
for rt in getattr(t, 'available_input_routing_types', []):
    dn = rt.display_name.lower()
    if target_q in dn:
        matched_rt = rt
        break
if not matched_rt:
    for w in target_q.split():
        if len(w) > 2:
            for rt in getattr(t, 'available_input_routing_types', []):
                if w in rt.display_name.lower():
                    matched_rt = rt
                    break
            if matched_rt:
                break
if matched_rt:
    t.input_routing_type = matched_rt
    res = {{'status': 'success', 'routed_to': matched_rt.display_name, 'monitoring': t.current_monitoring_state}}
else:
    res = {{'status': 'not_found', 'available': [rt.display_name for rt in getattr(t, 'available_input_routing_types', [])]}}
"""
                    try:
                        r_res = conn.send_command("execute_code", {"code": code_route})
                        r_data = r_res.get("result", r_res) if isinstance(r_res, dict) else {}
                        inner_res = r_data.get("res", {})
                        if inner_res.get("status") == "success":
                            actual_routed_to = inner_res.get("routed_to")
                    except Exception as ex_route:
                        logger.warning(f"Audio FX routing notice for track {t_idx}: {ex_route}")
    
                short_fx = chosen_fx_name.split()[-1]
                short_src = target_source_name.replace("[", "").replace("]", "") if target_source_name else "Bus"
                try:
                    conn.send_command("set_track_name", {
                        "track_index": t_idx,
                        "name": f"[{role}] {short_fx} ({short_src})"
                    })
                except Exception:
                    pass
    
            trk["instrument"] = f"{chosen_fx_name} (In: {actual_routed_to or target_source_name})"
            trk["effect_loaded"] = chosen_fx_name
            trk["input_routing"] = actual_routed_to or target_source_name
            trk["monitoring_state"] = "In"
            trk["is_audio"] = True
            trk["is_fx_audio"] = True
    
            session.data["current_track_ptr"] = ptr + 1
            session._save_state()
    
            if session.data["current_track_ptr"] < len(tracks):
                return session._prompt_current_track_instrument()
            else:
                session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
                session.data["phase_index"] = 4
                session.data["current_param_ptr"] = 0
                session._save_state()
                return session._prompt_current_track_params()
    
        # Audio Track / Vocal Take Loading Branch
        if is_audio and role == "VOCALS" and not wants_chopping:
            p_samples = get_personal_samples("vocal")
            v_samples = [s for s in p_samples if "vocal" in str(s.get("folder", "")).lower() or "vocales" in str(s.get("folder", "")).lower() or any(k in str(s.get("name", "")).lower() for k in ["duki", "vocal", "vox", "kanye", "bts"])]
    
            # Check if user explicitly selected Option 2 (Import external take from library)
            wants_import = any(w in u_clean for w in ["opcion 2", "2.", "importar", "cargar toma", "archivo", "libreria"]) or u_clean == "2"
            chosen_sample = None
            if not wants_import:
                for vs in v_samples:
                    vs_name = vs["name"].lower()
                    vs_base = vs_name.rsplit(".", 1)[0]
                    if vs_base in u_clean or vs_name in u_clean:
                        wants_import = True
                        chosen_sample = vs
                        break
    
            if wants_import:
                # Option 2: Import external take
                if not chosen_sample:
                    for vs in v_samples:
                        vs_name = vs["name"].lower()
                        vs_base = vs_name.rsplit(".", 1)[0]
                        if vs_base in u_clean or vs_name in u_clean or any(p in u_clean for p in vs_base.replace("-", " ").replace("_", " ").split() if len(p) > 2):
                            chosen_sample = vs
                            break
                if not chosen_sample and v_samples:
                    duki_cand = [vs for vs in v_samples if "duki" in vs["name"].lower() and "duki2" not in vs["name"].lower()]
                    chosen_sample = duki_cand[0] if duki_cand else v_samples[0]
    
                v_path = chosen_sample["path"] if chosen_sample else ""
                v_name = chosen_sample["name"] if chosen_sample else "Lead Vocal"
                trk["is_audio"] = True
                trk["live_recording_mode"] = False
                trk["sample_path"] = v_path
                trk["sample_name"] = v_name
                trk["instrument"] = f"Audio Take ({v_name})"
    
                if conn is not None and hasattr(conn, "send_command"):
                    try:
                        if v_path and os.path.exists(v_path):
                            conn.send_command("create_audio_clip", {
                                "track_index": t_idx,
                                "clip_index": 0,
                                "path": v_path
                            })
                            alt_cand = [vs for vs in v_samples if vs.get("path") != v_path]
                            if alt_cand and os.path.exists(alt_cand[0]["path"]):
                                try:
                                    conn.send_command("create_audio_clip", {
                                        "track_index": t_idx,
                                        "clip_index": 1,
                                        "path": alt_cand[0]["path"]
                                    })
                                    trk["alt_sample_path"] = alt_cand[0]["path"]
                                except Exception:
                                    pass
    
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": "query:AudioFx#EQ%20Eight"})
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": "query:AudioFx#Compressor"})
                        conn.send_command("set_track_name", {"track_index": t_idx, "name": f"[{role}] {v_name}"})
                    except Exception as ex_v_load:
                        logger.warning(f"Notice loading vocal audio clip on track {t_idx}: {ex_v_load}")
            else:
                # Option 1 (Default / Recommended): Live Mic Recording Mode & Tracking Setup
                trk["is_audio"] = True
                trk["live_recording_mode"] = True
                trk["sample_path"] = None
                trk["reference_take_path"] = None
                trk["sample_name"] = "Live Vocal Mic (Clean Recording Track)"
                trk["instrument"] = "Live Vocal Mic (Armed & Tracking FX)"
    
                if conn is not None and hasattr(conn, "send_command"):
                    try:
                        # 1. Arm track for physical mic recording
                        conn.send_command("set_track_arm", {"track_index": t_idx, "arm": True})
                        # 2. Configure monitoring state to Auto (1)
                        conn.send_command("execute_code", {"code": f"song.tracks[{t_idx}].current_monitoring_state = 1\nsong.tracks[{t_idx}].arm = True\n"})
                        # 3. Load pristine tracking FX chain only if track has no devices yet
                        t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                        devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
                        if not devs:
                            conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": "query:AudioFx#EQ%20Eight"})
                            conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": "query:AudioFx#Compressor"})
                        # 4. Strictly delete any clips (session or arrangement) so user has a 100% clean canvas for live recording
                        code_clean_vocal = f"""
t = song.tracks[{t_idx}]
for c in list(getattr(t, 'arrangement_clips', [])):
    try:
        t.delete_clip(c)
    except:
        pass
for slot in t.clip_slots:
    if slot.has_clip:
        try:
            slot.delete_clip()
        except:
            pass
"""
                        conn.send_command("execute_code", {"code": code_clean_vocal})
                        conn.send_command("set_track_name", {"track_index": t_idx, "name": f"[{role}] Lead Vocal (Live Mic)"})
                    except Exception as ex_arm:
                        logger.warning(f"Notice setting up live vocal tracking on track {t_idx}: {ex_arm}")
    
            session.data["current_track_ptr"] = ptr + 1
            session._save_state()
    
            if session.data["current_track_ptr"] < len(tracks):
                return session._prompt_current_track_instrument()
            else:
                session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
                session.data["phase_index"] = 4
                session.data["current_param_ptr"] = 0
                session._save_state()
                return session._prompt_current_track_params()
    
        is_chopping = False
        chosen_sample = None
        lookup_role = "GUITAR" if ("guitar" in t_name.lower() or "acustic" in t_name.lower() or "flamenc" in t_name.lower()) else (
            "PERCUSSION" if ("perc" in t_name.lower() or "palma" in t_name.lower() or "clap" in t_name.lower()) else role
        )

        # Check if track is currently in Level 2 Sub-selection for a multi-preset plugin
        pending_plugin = trk.get("pending_plugin_subselection")
        pending_parent_plugin = pending_plugin
        if pending_plugin:
            sub_options = LiveBrowserCatalogEngine.get_plugin_presets_for_role(pending_plugin, role)

            # User wishes to go back to main plugin selection
            if any(w in u_clean for w in ["volver", "atras", "regresar", "cancelar", "cambiar plugin", "otro plugin"]):
                trk.pop("pending_plugin_subselection", None)
                session._save_state()
                return session._prompt_current_track_instrument()

            selected_sub_opt = None
            clean_keywords = ["default", "limpio", "clean", "crudo", "vst base", "plugin limpio", "sin preset"]
            # 1. Clean default plugin selection
            if any(w in u_clean for w in clean_keywords) or (sub_options and (u_clean == str(len(sub_options)) or f"opcion {len(sub_options)}" in u_clean or f"opción {len(sub_options)}" in u_clean)):
                selected_sub_opt = sub_options[-1] if sub_options else None
            else:
                # 2. Number index match
                for idx, s_opt in enumerate(sub_options, 1):
                    if f"opcion {idx}" in u_clean or f"opción {idx}" in u_clean or u_clean == str(idx):
                        selected_sub_opt = s_opt
                        break
                # 3. Name or substring match
                if not selected_sub_opt:
                    for s_opt in sub_options:
                        s_name = _normalize_text(s_opt.name)
                        if s_name in u_clean or u_clean in s_name:
                            selected_sub_opt = s_opt
                            break
                # 4. Token match
                if not selected_sub_opt:
                    for s_opt in sub_options:
                        if any(word in _normalize_text(s_opt.name) for word in u_clean.split() if len(word) > 3):
                            selected_sub_opt = s_opt
                            break
    
            if not selected_sub_opt:
                selected_sub_opt = sub_options[-1] if sub_options else None
    
            trk.pop("pending_plugin_subselection", None)
            target_uri = selected_sub_opt.uri if selected_sub_opt else f"query:Plugins#VST3:{pending_plugin.replace(' ', '%20')}"
            display_name = selected_sub_opt.name if selected_sub_opt else pending_plugin
            if selected_sub_opt and selected_sub_opt.blueprint:
                trk["blueprint"] = selected_sub_opt.blueprint
        else:
            options = LiveBrowserCatalogEngine.get_available_sources_for_role(lookup_role, filter_installed=True)

            selected_opt = None
            u_clean = _normalize_text(user_input)
    
            # Detect Chopping Mode request (Autonomous Synthesis & Transformation)
            is_chopping = False
            chop_idx = (min(7, len(options)) if options else 2) + 1
            if any(w in u_clean for w in ["chopping", "chop", "cortar", "rebanar", "autonomo", "autónomo"]) or u_clean == str(chop_idx) or f"opcion {chop_idx}" in u_clean or f"opción {chop_idx}" in u_clean:
                is_chopping = True

            if is_chopping:
                from engine.audio_genesis import AudioGenesisEngine, GenesisPipelineType
                from engine.audio_genesis.instrument_builder import TargetInstrumentDestination
                genesis = AudioGenesisEngine(conn=conn)
                source_name = t_name or role
                for candidate_t in tracks:
                    if candidate_t.get("role", "").upper() in ["KEYS", "PAD", "LEAD", "SYNTH"]:
                        source_name = candidate_t.get("name", "Keys")
                        break
                gen_path = None
                try:
                    sound_res = genesis.create_provenanced_sound(
                        musical_need=f"chopped_{role.lower()}_loop",
                        target_destination=TargetInstrumentDestination.SIMPLER_SLICED,
                        source_track_name=source_name,
                        genesis_pipeline=GenesisPipelineType.MELODIC_RESAMPLE,
                        session_tracks=tracks
                    )
                    if sound_res and hasattr(sound_res, "mutation") and sound_res.mutation.audio_path:
                        gen_path = str(sound_res.mutation.audio_path)
                except Exception as ex_gen:
                    logger.warning(f"Audio genesis chopping synthesis notice: {ex_gen}")

                target_uri = "query:Synths#Simpler"
                display_name = f"Simpler (Chopping Autónomo: {role})"
                trk["chopping_mode"] = True
                trk["sample_path"] = gen_path
                trk["sample_name"] = f"Genesis_Chop_{role}"
                trk["slice_mode"] = "Slicing"
            else:
                if "nativo" in u_clean or "preset nativo" in u_clean or "seguro" in u_clean or "core library" in u_clean:
                    for opt in options:
                        if "native" in opt.id.lower() or "native" in str(getattr(opt, "category", "")).lower():
                            selected_opt = opt
                            break
                    if not selected_opt:
                        native_fallbacks = {
                            "GUITAR": ("query:Sounds#Guitar%20&%20Plucked:FileId_6432", "Nylon Flamenco Guitar (.adv)"),
                            "PERCUSSION": ("query:Drums#FileId_5437", "Percussion Core Kit (.adg)"),
                            "KEYS": ("query:Sounds#Piano%20&%20Keys:FileId_4847", "Ac Piano Upright (.adg)"),
                            "BASS": ("query:Sounds#Bass:FileId_5176", "808 Drifter (.adg)"),
                            "DRUMS": ("query:Drums#FileId_5422", "808 Core Kit (.adg)"),
                            "LEAD": ("query:Sounds#Synth%20Lead:FileId_6743", "Agenda Lead (.adv)"),
                            "COUNTER_LEAD": ("query:Sounds#Synth%20Lead:FileId_6743", "Agenda Lead (.adv)"),
                            "ARPS": ("query:Sounds#Synth%20Lead:FileId_6743", "Agenda Lead (.adv)"),
                            "PAD": ("query:Sounds#Pad:FileId_4993", "Warm Analog Pad (.adg)"),
                            "STRINGS": ("query:Sounds#Strings:FileId_4765", "Ac Strings Orch (.adg)"),
                            "VOCALS": ("query:Synths#Simpler", "Ableton Simpler"),
                            "FX": ("query:AudioFx#AutoFilter", "Ableton Auto Filter")
                        }
                        fb_uri, fb_name = native_fallbacks.get(lookup_role, native_fallbacks.get(role, ("query:Sounds#Pad:FileId_4993", "Warm Analog Pad (.adg)")))
                        target_uri = fb_uri
                        display_name = fb_name
    
                if not selected_opt and not locals().get("target_uri"):
                    # 1. Direct number/option index match (e.g. "opcion 1", "1", "opcion 2")
                    for i, opt in enumerate(options, 1):
                        if f"opcion {i}" in u_clean or f"opción {i}" in u_clean or u_clean == str(i):
                            selected_opt = opt
                            break
    
                    # 2. Exact or substring match (e.g. "warm analog pad", "808 core kit")
                    if not selected_opt:
                        for opt in options:
                            o_name = opt.name.lower()
                            o_id = opt.id.lower()
                            if o_name == u_clean or o_id == u_clean or u_clean in o_name or o_name in u_clean or o_id in u_clean:
                                selected_opt = opt
                                break
    
                    # 3. Keyword / word match (length > 4)
                    if not selected_opt:
                        for opt in options:
                            if any(word in opt.name.lower() for word in u_clean.split() if len(word) > 4):
                                selected_opt = opt
                                break
                    if not selected_opt:
                        # Check unfiltered raw sources if user specifically requested a VST that was filtered by scan
                        unfiltered = LiveBrowserCatalogEngine.get_available_sources_for_role(role, filter_installed=False)
                        for u_opt in unfiltered:
                            u_o_name = u_opt.name.lower()
                            u_o_id = u_opt.id.lower()
                            if u_o_name == u_clean or u_o_id == u_clean or u_clean in u_o_name or u_o_name in u_clean or u_o_id in u_clean:
                                selected_opt = u_opt
                                break
                    if not selected_opt:
                        native_opts = [o for o in options if "native" in o.id.lower() or "native" in str(getattr(o, "category", "")).lower()]
                        selected_opt = native_opts[0] if native_opts else (options[0] if options else None)
    
                # Check if user selected Analog Lab V, Omnisphere, or Decent Sampler (Multi-preset parent plugin)
                opt_name_low = selected_opt.name.lower() if selected_opt else ""
                is_analog_lab = "analog lab" in opt_name_low or "analog lab" in u_clean
                is_omnisphere = "omnisphere" in opt_name_low or "omnisphere" in u_clean
                is_decent_parent = ("decent sampler" in opt_name_low or "decent sampler" in u_clean or u_clean == "decent") and not ("(" in opt_name_low and ")" in opt_name_low)
                is_surge_parent = ("surge" in opt_name_low or "surge" in u_clean) and "effects" not in opt_name_low and "effects" not in u_clean and not ("(" in opt_name_low and ")" in opt_name_low)
    
                if is_analog_lab or is_omnisphere or is_decent_parent or is_surge_parent:
                    plug_label = "Analog Lab V" if is_analog_lab else ("Omnisphere" if is_omnisphere else ("Decent Sampler" if is_decent_parent else "Surge XT"))
                    clean_keywords = ["default", "limpio", "clean", "crudo", "vst base", "plugin limpio", "sin preset"]
                    if any(w in u_clean for w in clean_keywords):
                        # User explicitly asked for clean default directly in Level 1 prompt
                        sub_opts = LiveBrowserCatalogEngine.get_plugin_presets_for_role(plug_label, role)
                        clean_opt = sub_opts[-1] if sub_opts else None
                        if clean_opt:
                            target_uri = clean_opt.uri
                            display_name = clean_opt.name
                            if clean_opt.blueprint:
                                trk["blueprint"] = clean_opt.blueprint
                        else:
                            target_uri = f"query:Plugins#VST3:{plug_label.replace(' ', '%20')}"
                            display_name = f"{plug_label} (Default)"
                    else:
                        # Switch to Level 2 Sub-selection and re-prompt
                        trk["pending_plugin_subselection"] = plug_label
                        session._save_state()
                        return session._prompt_current_track_instrument()
    
                if not locals().get("target_uri"):
                    target_uri = selected_opt.uri if selected_opt else (
                        "query:Drums#FileId_5422" if role == "DRUMS" else "query:Sounds#Piano%20&%20Keys:FileId_4867"
                    )
                    display_name = selected_opt.name if selected_opt else f"{role} Instrument"
                    if selected_opt and getattr(selected_opt, "blueprint", None):
                        trk["blueprint"] = selected_opt.blueprint
    
        is_verified = False
        load_error = None
    
        if conn is not None and hasattr(conn, "send_command"):
            try:
                try:
                    res = conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": target_uri})
                    if isinstance(res, dict) and (res.get("status") == "error" or "error" in res):
                        logger.warning(f"Initial load notice for {target_uri}: {res}")
                except Exception as ex_init:
                    logger.warning(f"Initial load exception for {target_uri}: {ex_init}")
    
                v_ok, dev_idx, dev_name = RoleTrackOrchestrator.verify_instrument_loaded(
                    conn, t_idx, "Simpler" if is_chopping else display_name
                )
                is_verified = v_ok
    
                # Fallback to clean parent VST if custom user rack failed
                if not is_verified and pending_parent_plugin:
                    clean_vst_uri = f"query:Plugins#VST3:{pending_parent_plugin.replace(' ', '%20')}"
                    if "omnisphere" in pending_parent_plugin.lower():
                        clean_vst_uri = "query:Plugins#VST3:Spectrasonics:Omnisphere"
                    elif "analog lab" in pending_parent_plugin.lower():
                        clean_vst_uri = "query:Plugins#VST3:Arturia:Analog%20Lab%20V"
                    elif "decent" in pending_parent_plugin.lower():
                        clean_vst_uri = "query:Plugins#VST3:Decent%20Samples:Decent%20Sampler"
                    elif "surge" in pending_parent_plugin.lower():
                        clean_vst_uri = "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT"
                    logger.warning(f"Custom rack failed verification on Track {t_idx}, attempting clean parent VST: {clean_vst_uri}")
                    try:
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": clean_vst_uri})
                        vst_ok, vst_idx, vst_name = RoleTrackOrchestrator.verify_instrument_loaded(conn, t_idx, pending_parent_plugin)
                        if vst_ok:
                            is_verified = True
                            display_name = "Spectrasonics Omnisphere" if "omnisphere" in pending_parent_plugin.lower() else pending_parent_plugin
                            target_uri = clean_vst_uri
                            dev_idx = vst_idx
                            logger.info(f"Track {t_idx} recovered with clean parent VST '{pending_parent_plugin}'.")
                    except Exception as vst_ex:
                        logger.warning(f"Clean VST fallback exception: {vst_ex}")

                # Autonomous Native Fallback if third-party VST failed to load in Live
                if not is_verified:
                    logger.warning(f"Instrument '{display_name}' ({target_uri}) failed physical verification on Track {t_idx}. Initiating native fallback...")
                    native_fallbacks = {
                        "GUITAR": ("query:Sounds#Guitar%20&%20Plucked:FileId_6432", "Nylon Flamenco Guitar (.adv)"),
                        "PERCUSSION": ("query:Drums#FileId_5437", "Percussion Core Kit (.adg)"),
                        "KEYS": ("query:Sounds#Piano%20&%20Keys:FileId_4847", "Ac Piano Upright (.adg)"),
                        "BASS": ("query:Sounds#Bass:FileId_5176", "808 Drifter (.adg)"),
                        "DRUMS": ("query:Drums#FileId_5422", "808 Core Kit (.adg)"),
                        "LEAD": ("query:Sounds#Synth%20Lead:FileId_6743", "Agenda Lead (.adv)"),
                        "PAD": ("query:Sounds#Pad:FileId_4993", "Warm Analog Pad (.adg)"),
                        "STRINGS": ("query:Sounds#Strings:FileId_4765", "Ac Strings Orch (.adg)"),
                        "VOCALS": ("query:Synths#Simpler", "Ableton Simpler"),
                        "FX": ("query:AudioFx#AutoFilter", "Ableton Auto Filter")
                    }
                    fb_uri, fb_name = native_fallbacks.get(lookup_role, native_fallbacks.get(role, ("query:Synths#Simpler", "Ableton Simpler")))
                    try:
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": fb_uri})
                        fb_verified, fb_idx, fb_dev = RoleTrackOrchestrator.verify_instrument_loaded(conn, t_idx, fb_name)
                        if fb_verified:
                            is_verified = True
                            display_name = fb_name
                            target_uri = fb_uri
                            dev_idx = fb_idx
                            logger.info(f"Track {t_idx} recovered with native fallback '{fb_name}'.")
                    except Exception as fb_e:
                        logger.error(f"Native recovery attempt error: {fb_e}")
    
                if role == "DRUMS" and is_verified and dev_idx is not None:
                    try:
                        audit = DrumRackGuard.audit_drum_rack(conn, track_index=t_idx, device_index=dev_idx)
                        if not audit.get("is_populated"):
                            rem_res = DrumRackGuard.enforce_populated_drum_kit(conn, track_index=t_idx, device_index=dev_idx)
                            if not rem_res.get("is_populated"):
                                is_verified = False
                                load_error = "Drum Rack fue cargado pero sus pads están vacíos ('Suelte aquí un instrumento o muestra')."
                    except Exception as ex_drum:
                        logger.info(f"Drum guard notice on track {t_idx}: {ex_drum}")
    
                # Configure Simpler for Slicing in Chopping mode & Load Physical Sample File
                if is_chopping and is_verified and dev_idx is not None:
                    try:
                        p_info = conn.send_command("get_device_parameters", {"track_index": t_idx, "device_index": dev_idx})
                        p_list = p_info.get("parameters", []) if isinstance(p_info, dict) else []
                        for p in p_list:
                            p_name = str(p.get("name", "")).lower()
                            if "mode" in p_name:
                                conn.send_command("set_device_parameter", {
                                    "track_index": t_idx,
                                    "device_index": dev_idx,
                                    "parameter_name": p.get("name"),
                                    "value": 2.0  # Slicing mode in Simpler
                                })
                                break
                    except Exception as p_ex:
                        logger.debug(f"Simpler slicing mode notice: {p_ex}")
    
                    gen_sample_path = trk.get("sample_path")
                    if gen_sample_path and os.path.exists(gen_sample_path):
                        try:
                            # Load physical audio sample into Simpler via Live 12 replace_sample LOM API
                            s_path_repr = repr(str(Path(gen_sample_path).resolve()))
                            s_disp_name = trk.get("sample_name", "Autonomous Chop")
                            exec_code = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
sample_path = {s_path_repr}
if hasattr(d, 'replace_sample'):
    d.replace_sample(sample_path)
if hasattr(d, 'playback_mode'):
    d.playback_mode = 2
s = getattr(d, 'sample', None)
if s and hasattr(s, 'reset_slices'):
    s.reset_slices()
slices_count = len(getattr(s, 'slices', [])) if s else 0
"""
                            code_res = conn.send_command("execute_code", {"code": exec_code})
                            res_s_cnt = int(code_res.get("slices_count", 0)) if isinstance(code_res, dict) else 0
                            trk["slices_count"] = res_s_cnt if res_s_cnt > 0 else 16
                            trk["sample_loaded"] = True
                            logger.info(f"Loaded autonomous generated sample '{s_disp_name}' into Simpler on Track {t_idx} ({trk['slices_count']} slices).")
                        except Exception as s_load_err:
                            logger.warning(f"Notice on autonomous sample loading into Simpler: {s_load_err}")
                            trk["slices_count"] = 16

                # Autogenous Foley / Texture Generation if Simpler was loaded for TEXTURE_FOLEY
                if role in ("TEXTURE_FOLEY", "FOLEY") and is_verified and dev_idx is not None:
                    try:
                        from engine.audio_genesis import AudioGenesisEngine, GenesisPipelineType
                        genesis = AudioGenesisEngine(conn=conn)
                        source_name = "Keys"
                        for candidate_t in tracks:
                            if candidate_t.get("role", "").upper() in ["KEYS", "PAD", "SYNTH"]:
                                source_name = candidate_t.get("name", "Keys")
                                break
                        sound_res = genesis.create_provenanced_sound(
                            musical_need="organic_foley_texture",
                            source_track_name=source_name,
                            genesis_pipeline=GenesisPipelineType.FREEZE_PAD,
                            session_tracks=tracks
                        )
                        if sound_res and hasattr(sound_res, "mutation") and sound_res.mutation.audio_path:
                            f_path_repr = repr(str(Path(sound_res.mutation.audio_path).resolve()))
                            exec_foley = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
sample_path = {f_path_repr}
if hasattr(d, 'replace_sample'):
    d.replace_sample(sample_path)
if hasattr(d, 'playback_mode'):
    d.playback_mode = 0
for p in d.parameters:
    if p.name == 'S Loop On':
        p.value = 1.0
    elif p.name == 'S Loop Fade':
        p.value = 0.15
"""
                            conn.send_command("execute_code", {"code": exec_foley})
                            trk["sample_loaded"] = True
                            logger.info(f"Loaded autogenous foley sample into Simpler on Track {t_idx} (source: {source_name}).")
                    except Exception as f_err:
                        logger.warning(f"Notice on autogenous foley generation in Phase 3: {f_err}")

                if is_verified:
                    if is_chopping and chosen_sample:
                        s_short = chosen_sample['name'][:16]
                        conn.send_command("set_track_name", {"track_index": t_idx, "name": f"[{role}] Chop: {s_short}"})
                    else:
                        conn.send_command("set_track_name", {"track_index": t_idx, "name": f"[{role}] {display_name}"})
                else:
                    if not load_error:
                        load_error = f"El dispositivo '{display_name}' no fue detectado en la cadena de la Pista {t_idx}."
            except Exception as e:
                is_verified = False
                load_error = f"Fallo al cargar en Live: {str(e)}"
        else:
            is_verified = True
    
        if not is_verified:
            logger.error(f"Track {t_idx} verification failed: {load_error}")
            return {
                "status": "LOAD_FAILED",
                "current_step": f"PASO 3 DE 7: ERROR DE CARGA EN PISTA {t_idx} ({trk['name']})",
                "action_taken": f"FALLO DE VERIFICACIÓN: {load_error}. La pista no tiene generador sonoro válido.",
                "question": (
                    f"⚠️ **Alerta del Copilot:** No se pudo cargar o verificar '{display_name}' en la Pista {t_idx}.\n\n"
                    f"*Motivo:* {load_error}\n\n"
                    f"1. **Reintentar carga** de {display_name}.\n"
                    f"2. **Cargar preset nativo seguro** de Live Core Library ({role}).\n"
                    f"*Responde indicando cómo deseas proceder.*"
                ),
                "instructions_for_ai": "Elige reintentar o una opción alternativa para no dejar la pista vacía.",
                "retry_required": True,
                "phase": "PHASE_3_INSTRUMENTS"
            }
    
        trk["instrument"] = display_name
        trk["item_uri"] = target_uri
        if "decent sampler" in display_name.lower():
            trk["is_decent_sampler"] = True
            bp = trk.get("blueprint", {})
            if bp and bp.get("library_name"):
                trk["decent_sampler_library"] = bp.get("library_name")
                trk["decent_sampler_preset_path"] = bp.get("preset_path")
            elif "(" in display_name and ")" in display_name:
                lib_name = display_name.split("(", 1)[1].rsplit(")", 1)[0].strip()
                if "default" not in lib_name.lower():
                    trk["decent_sampler_library"] = lib_name
                    from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
                    lib_info = DecentSamplerLibraryManager.get_library_by_name(lib_name)
                    if lib_info and lib_info.preset_path:
                        trk["decent_sampler_preset_path"] = str(lib_info.preset_path)

        if "surge" in display_name.lower() and "effects" not in display_name.lower():
            trk["is_surge_synth"] = True
            try:
                from engine.sound_design.surge_xt_synth.patch_factory import SurgeSynthPatchFactory
                from engine.sound_design.surge_xt_synth.validator import SurgeSynthValidator
                from engine.sound_design.surge_xt_synth.serializer import SurgeSynthSerializer
                from engine.sound_design.surge_xt_synth.sanitizer import SurgeSynthSanitizer

                bpm = float(session.data.get("bpm", 120.0))
                bp = trk.get("blueprint", {})
                applied_p = bp.get("parameters", {})

                if bp and bp.get("patch_model"):
                    surge_patch = bp.get("patch_model")
                else:
                    surge_patch = SurgeSynthPatchFactory.create_role_patch(
                        role=role,
                        bpm=bpm,
                        applied_params=applied_p,
                        track_name=trk.get("name", "SurgeSynth")
                    )

                val_rep = SurgeSynthValidator.validate_patch(surge_patch)
                if not val_rep.is_valid:
                    surge_patch = SurgeSynthSanitizer.sanitize_patch(surge_patch)

                patch_path = SurgeSynthSerializer.save_patch(surge_patch, category=session.data.get("song_name", "Session"))
                trk["surge_synth_patch_path"] = str(patch_path)
                trk["surge_synth_osc_types"] = [osc.osc_type for osc in surge_patch.oscillators]
                trk["surge_synth_category"] = surge_patch.category

                if conn is not None and hasattr(conn, "send_command") and dev_idx is not None:
                    lom_cmds = surge_patch.to_lom_command_list()
                    for p_name, p_val in lom_cmds:
                        try:
                            conn.send_command("set_device_parameter", {
                                "track_index": t_idx,
                                "device_index": dev_idx,
                                "parameter_name": p_name,
                                "value": float(p_val)
                            })
                        except Exception as ex_lom:
                            logger.debug(f"Surge XT parameter dispatch notice: {ex_lom}")
                logger.info(f"Generated and validated Surge XT synth patch '{surge_patch.patch_name}' for track {t_idx} [{role}]: {patch_path}")
            except Exception as ex_surge:
                logger.warning(f"Notice generating Surge XT patch: {ex_surge}")
        session.data["current_track_ptr"] = ptr + 1
        session._save_state()
    
        if session.data["current_track_ptr"] < len(tracks):
            return session._prompt_current_track_instrument()
        else:
            session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
            session.data["phase_index"] = 4
            session.data["current_param_ptr"] = 0
            session._save_state()
            return session._prompt_current_track_params()
    
    # -------------------------------------------------------------------------
    # FASE 4: ESCULPIDO POR CUADRANTES DE SÍNTESIS Y GAIN STAGING
    # -------------------------------------------------------------------------

# engine/production/copilot/phases/phase_5_insert_effects.py
"""
Phase 5: Track-by-track insert effect chains, mandatory EQ gate, and parameter calibration.
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text, parse_autotune_settings
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS, ROLE_FREQUENCY_GUIDE
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.session.transaction_guard import TransactionGuard
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.knowledge.plugins.fabfilter import get_eq_preset, get_compressor_preset
from engine.vocal.vocal_chain_processor import VocalChainProcessor

logger = logging.getLogger("Phase5InsertEffects")

class Phase5InsertEffectsHandler(BasePhaseHandler):
    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_current_fx_device(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_5(session, conn, user_input)

    def find_track_missing_eq(self, session: Any, conn: Any = None) -> Optional[Dict[str, Any]]:
        """
        Verifies if every active track in Live has an equalizer (EQ Eight or Pro-Q).
        Returns the first track lacking an EQ, or None if all tracks are compliant.
        """
        tracks = session.data.get("tracks", [])
        if not tracks:
            return None
    
        for trk in tracks:
            t_idx = session._resolve_live_track_index(conn, trk)
            has_eq = False
            # Check recorded insert_effects
            for eff in trk.get("insert_effects", []):
                if any(q in str(eff.get("name", "")).lower() for q in ["eq", "equalizer", "pro-q"]):
                    if not eff.get("bypass", False):
                        has_eq = True
                        break
            # Check physical devices in Live if connected
            if not has_eq and conn and hasattr(conn, "send_command"):
                try:
                    t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    raw_devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
                    for d in raw_devs:
                        d_name = str(d.get("name", "")).lower()
                        d_class = str(d.get("class_name", "")).lower()
                        if "eq" in d_name or "eq8" in d_class or "pro-q" in d_name:
                            has_eq = True
                            break
                except Exception:
                    pass
    
            if not has_eq:
                return trk
    
        return None
    
    def force_missing_eq_prompt(self, session: Any, conn: Any, missing_trk: Dict[str, Any]) -> Dict[str, Any]:
        """Forces insertion and configuration of EQ Eight on a track that missed it."""
        tracks = session.data.get("tracks", [])
        t_ptr = tracks.index(missing_trk) if missing_trk in tracks else 0
        t_idx = session._resolve_live_track_index(conn, missing_trk)
        role = missing_trk.get("role", "OTHER")
    
        session.data["current_fx_track_ptr"] = t_ptr
        session.data["current_fx_dev_ptr"] = 0
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session._save_state()
    
        guide = ROLE_FREQUENCY_GUIDE.get(role, ROLE_FREQUENCY_GUIDE.get("KEYS", {}))
        return {
            "status": "MISSING_EQ_ENFORCED",
            "current_step": f"PASO 5 DE 7: ECUALIZACIÓN OBLIGATORIA (PISTA {t_ptr + 1}: '{missing_trk.get('name')}')",
            "action_taken": f"Compuerta de ecualización activada: la pista {t_idx} no tiene ecualizador. El motor exige su configuración obligatoria.",
            "question": (
                f"⛔ **COMPUERTA DE ECUALIZACIÓN OBLIGATORIA (PISTA {t_idx}: '{missing_trk.get('name')}', Rol: {role})**\n\n"
                f"El motor no permite avanzar a la Fase 6 si alguna pista carece de ecualizador.\n"
                f"Es obligatorio insertar y calibrar `EQ Eight` para limpiar subgraves, resonancias y transientes.\n\n"
                f"🎯 **Guía Espectral y Dinámica para {role}:**\n"
                f"• **Frecuencias Dominantes:** {guide.get('dominant_zone', 'Información espectral clave')}\n"
                f"• **Puntos de Conflicto Crítico:** {guide.get('conflict_points', 'Enmascaramiento de frecuencias')}\n"
                f"• **Ajuste Quirúrgico Recomendado:** {guide.get('eq_recommendation', 'Corte HPF y limpieza')}\n"
                f"• **Manejo de Transitorios:** {guide.get('transient_handling', 'Control dinámico')}\n\n"
                f"📋 **Formato Esperado de Parámetros:**\n"
                f"• Clave-Valor: `\"Band 1 On: 1.0, 1 Frequency A: 0.28, Band 4 Gain: 0.50\"`\n"
                f"• Preset rápido: `\"Opción 1\"` (Recomendado: aplica el blueprint espectral exacto)\n\n"
                f"*Especifica tus parámetros para EQ Eight o escribe 'Opción 1' para aplicar el blueprint.*"
            ),
            "instructions_for_ai": f"Define los parámetros obligatorios para EQ Eight en la pista {missing_trk.get('name')}.",
            "target_track": t_idx,
            "target_device": "EQ Eight",
            "phase": "PHASE_5_INSERT_EFFECTS"
        }
    
    # -------------------------------------------------------------------------
    # FASE 5: EFECTO POR EFECTO, PARÁMETRO POR PARÁMETRO CON REPORTE DE GANANCIA
    # -------------------------------------------------------------------------
    def _prompt_current_fx_device(self, session: Any) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        t_ptr = session.data.get("current_fx_track_ptr", 0)
    
        if t_ptr >= len(tracks):
            missing_trk = self.find_track_missing_eq(session, None)
            if missing_trk is not None:
                return self.force_missing_eq_prompt(session, None, missing_trk)
    
            session.data["current_phase"] = "PHASE_6_COMPOSITION"
            session.data["phase_index"] = 6
            session._save_state()
            return session._prompt_phase_6()
    
        trk = tracks[t_ptr]
        t_idx = trk.get("index", t_ptr)
        t_name = trk["name"]
        role = trk["role"]
        dev_ptr = session.data.get("current_fx_dev_ptr", 0)
    
        fx_list = ROLE_INSERT_EFFECTS.get(role, ROLE_INSERT_EFFECTS.get("STRINGS", []))
    
        if dev_ptr >= len(fx_list):
            session.data["current_fx_track_ptr"] = t_ptr + 1
            session.data["current_fx_dev_ptr"] = 0
            session._save_state()
            return session._prompt_current_fx_device()
    
        eff = fx_list[dev_ptr]
        eff_name = eff["name"]
        is_eq = any(q in eff_name.lower() for q in ["eq", "equalizer", "pro-q"])
    
        params_info = []
        for p in eff["params"]:
            p_range = p.get("range", "0.0 a 1.0")
            p_behavior = p.get("behavior", p.get("desc", ""))
            params_info.append(f"  • **{p['name']}** (Rango: `{p_range}`): {p_behavior}")
    
        if is_eq:
            guide = ROLE_FREQUENCY_GUIDE.get(role, ROLE_FREQUENCY_GUIDE.get("KEYS", {}))
            eq_guide_block = (
                f"\n🎯 **Guía Espectral y Manejo de Transitorios (Guía Psicoacústica de Frecuencias) OBLIGATORIA ({role}):**\n"
                f"• **Frecuencias Dominantes:** {guide.get('dominant_zone', 'N/A')}\n"
                f"• **Puntos de Conflicto Crítico (Enmascaramiento):** {guide.get('conflict_points', 'N/A')}\n"
                f"• **Ajuste Quirúrgico Recomendado:** {guide.get('eq_recommendation', 'N/A')}\n"
                f"• **Manejo de Transitorios en Estilos Híbridos:** {guide.get('transient_handling', 'N/A')}\n"
                f"⚠️ *Nota del Motor: El ecualizador es 100% obligatorio en esta pista para evitar solapamientos destructivos; no se admite bypass.*"
            )
            params_info.append(eq_guide_block)
    
        # Inyectar directrices de FabFilter y Cadenas Vocales
        eq_tip = get_eq_preset(role.lower())
        comp_tip = get_compressor_preset(role.lower())
        fx_kb = []
        if eq_tip:
            fx_kb.append(f"  💡 **FabFilter Pro-Q ({role}):** {eq_tip.splitlines()[0] if eq_tip else ''}")
        if comp_tip:
            fx_kb.append(f"  💡 **FabFilter Pro-C2 ({role}):** {comp_tip.splitlines()[0] if comp_tip else ''}")
        if role == "VOCALS":
            try:
                sc = InstalledPluginScanner()
                sc.scan()
                at_plugs = [p.name for p in sc.get_plugins_for_role("VOCALS") if "auto" in p.name.lower() or "antares" in p.vendor.lower()]
                s_key = session.data.get("key", "F")
                s_scale = session.data.get("scale", "Minor")
                if at_plugs:
                    fx_kb.append(f"  🎤 **Auto-Tune VST Detectado ({at_plugs[0]}):** Prioridad #1 recomendada. Afinación pre-calibrada en {s_key} {s_scale}. Retune Speed: 0 ms (Trap Hard Snap) o 25 ms (Natural).")
                else:
                    fx_kb.append("  💡 **Cadena Vocal de 10 Slots:** RX De-Click -> Auto-Tune -> Pro-Q3 sustractivo -> 1176 peak -> LA-2A -> Pro-DS -> Pro-Q3 aire -> Saturn 2 -> MicroShift -> Pro-L2.")
                fx_kb.append("  💎 **Suite Vocal Detectada:** FabFilter Pro-Q, Pro-DS, Saturn 2 y ValhallaVintageVerb listos para inserción híbrida.")
            except Exception:
                fx_kb.append("  💡 **Cadena Vocal de 10 Slots:** RX De-Click -> Auto-Tune -> Pro-Q3 sustractivo -> 1176 peak -> LA-2A -> Pro-DS -> Pro-Q3 aire -> Saturn 2 -> MicroShift -> Pro-L2.")
    
        if "auto-tune" in eff_name.lower() or "autotune" in eff_name.lower():
            fx_kb.append("  ⚠️ **OBLIGATORIO — KEY Y SCALE:** Auto-Tune Artist **exige obligatoriamente** definir la **Key** (Tono: C, C#, D, D#, E, F, F#, G, G#, A, A#, B) y la **Scale** (Escala: Minor o Major). No se permite omitir estos valores.")
    
        if fx_kb:
            params_info.append("\n**Directrices Quirúrgicas de Inserción (FabFilter / Plugins):**\n" + "\n".join(fx_kb))
    
        params_text = "\n".join(params_info)
    
        gs = trk.get("gain_staging", {})
        lvl_str = f"{gs.get('target_peak_dbfs', -14.0):.1f} dBFS" if gs else "-14.0 dBFS"
    
        p_examples = ", ".join([f"{p['id']}: X" for p in eff.get("params", [])[:2]]) or "Parameter: Value"
        decision_prompt = (
            f"Analiza la función de este efecto dentro del rol '{role}' y define los valores específicos para cada parámetro considerando la densidad y rango dinámico de la mezcla."
            if is_eq else
            f"Analiza la función de este efecto dentro del rol '{role}' y define los valores específicos para cada parámetro considerando la densidad y rango dinámico de la mezcla, o indica 'Bypass' si determinas que este procesador no es necesario en este canal."
        )
        action_note = f"*Especifica tus valores de configuración (ej: '{p_examples}'). (Nota: Ecualizador 100% obligatorio).*" if is_eq else f"*Especifica tus valores de configuración (ej: '{p_examples}') o indica 'Bypass'.*"
    
        params_format_banner = (
            f"\n\n📋 **Formato Esperado de Parámetros:**\n"
            f"• Clave-Valor: `\"Parámetro: Valor, Parámetro: Valor\"` (ej: `\"{p_examples}\"` o `\"Drive: 35%, Dry/Wet: 50%\"`)\n"
            f"• Con Unidades: `\"Threshold: -16 dB, Attack: 15 ms, Ratio: 4:1\"`\n"
            f"• JSON: `{{\"Drive\": 0.35, \"Dry/Wet\": 0.50}}`\n"
            f"• Opciones rápidas: `\"Opción 1\"` (Valores recomendados) o `\"Bypass\"` (excepto en ecualizadores obligatorios)."
        )
    
        return {
            "current_step": f"PASO 5 DE 7: EFECTO {dev_ptr + 1} DE {len(fx_list)} (PISTA {t_ptr + 1} DE {len(tracks)}: '{t_name}')",
            "action_taken": f"Configurando procesador #{dev_ptr + 1} ({eff_name}) en Pista {t_idx}. Nivel actual: {lvl_str}.",
            "question": (
                f"🔌 **Paso 5 de 7: Cadena de Efectos de Inserción - Esculpido de '{eff_name}' en Pista {t_ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                f"Procesador #{dev_ptr + 1} de {len(fx_list)} en la cadena de inserción. Nivel pre-fader actual: `{lvl_str}`.\n\n"
                f"**Espacio de Parámetros y Rangos Acústicos Disponibles:**\n"
                f"{params_text}\n\n"
                f"🧠 **Decisión Técnica Requerida:**\n"
                f"{decision_prompt}\n\n"
                f"{action_note}"
                f"{params_format_banner}"
            ),
            "instructions_for_ai": f"Define los parámetros para {eff_name} en la pista {t_name}." if is_eq else f"Define los parámetros para {eff_name} en la pista {t_name} o indica Bypass.",
            "target_track": t_idx,
            "target_device": eff_name,
            "device_index_in_chain": dev_ptr + 1,
            "total_devices_in_chain": len(fx_list),
            "phase": "PHASE_5_INSERT_EFFECTS"
        }
    
    def _handle_phase_5(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        t_ptr = session.data.get("current_fx_track_ptr", 0)
    
        if t_ptr >= len(tracks):
            session.data["current_phase"] = "PHASE_6_COMPOSITION"
            session.data["phase_index"] = 6
            session._save_state()
            return session._prompt_phase_6()
    
        trk = tracks[t_ptr]
        t_idx = session._resolve_live_track_index(conn, trk)
        role = trk["role"]
        dev_ptr = session.data.get("current_fx_dev_ptr", 0)
        text = _normalize_text(user_input)
    
        fx_list = ROLE_INSERT_EFFECTS.get(role, ROLE_INSERT_EFFECTS.get("STRINGS", []))
    
        if dev_ptr >= len(fx_list):
            session.data["current_fx_track_ptr"] = t_ptr + 1
            session.data["current_fx_dev_ptr"] = 0
            session._save_state()
            return session._prompt_current_fx_device()
    
        eff = fx_list[dev_ptr]
        eff_name = eff["name"]
        eff_uri = eff["uri"]
    
        # Capture pre-mutation snapshot for deterministic rollback
        track_state = [TransactionGuard.capture_live_track_state(conn, t_idx)]
        TransactionGuard.begin_transaction(session.data, track_state)
    
        applied_params = {}
        is_bypass = ("bypass" in text or "omitir" in text or "opcion 3" in text or "directo" in text)
        is_eq = any(q in eff_name.lower() for q in ["eq", "equalizer", "pro-q"])
    
        if is_bypass and is_eq:
            guide = ROLE_FREQUENCY_GUIDE.get(role, ROLE_FREQUENCY_GUIDE.get("KEYS", {}))
            TransactionGuard.rollback_transaction(conn, session)
            return {
                "status": "VALIDATION_ERROR",
                "current_step": f"PASO 5 DE 7: ECUALIZACIÓN OBLIGATORIA (PISTA {t_ptr + 1}: '{trk.get('name')}')",
                "action_taken": f"El motor prohíbe terminantemente el bypass en el ecualizador ({eff_name}). ¡EL ECUALIZADOR ES 100% OBLIGATORIO!",
                "question": (
                    f"⛔ **EL ECUALIZADOR ES ESTRICTAMENTE OBLIGATORIO EN LA PISTA {t_idx} ('{trk.get('name')}')**\n\n"
                    f"Para garantizar un balance espectral limpio y evitar enmascaramiento y distorsión de transitorios, el motor exige la presencia y configuración del ecualizador.\n\n"
                    f"🎯 **Guía Espectral y Dinámica (Guía Psicoacústica de Frecuencias) para {role}:**\n"
                    f"• **Frecuencias Dominantes:** {guide.get('dominant_zone', 'Información espectral')}\n"
                    f"• **Puntos de Conflicto Crítico:** {guide.get('conflict_points', 'Enmascaramiento')}\n"
                    f"• **Ajuste Quirúrgico Recomendado:** {guide.get('eq_recommendation', 'Corte HPF')}\n"
                    f"• **Manejo de Transitorios:** {guide.get('transient_handling', 'Control dinámico')}\n\n"
                    f"*Por favor define los parámetros del ecualizador para continuar (o escribe 'Opción 1' para aplicar los valores recomendados).*"
                ),
                "instructions_for_ai": f"No puedes omitir el ecualizador {eff_name}. Envía los parámetros de configuración.",
                "target_track": t_idx,
                "target_device": eff_name,
                "device_index_in_chain": dev_ptr + 1,
                "total_devices_in_chain": len(fx_list),
                "phase": "PHASE_5_INSERT_EFFECTS"
            }
    
        if not is_bypass:
            # Validación Estricta para Auto-Tune: Key y Scale son estrictamente obligatorios
            if "auto-tune" in eff_name.lower() or "autotune" in eff_name.lower():
                det_key, det_scale, det_retune = parse_autotune_settings(user_input)
                if not det_key and ("opcion 1" in text or "default" in text or "recomendad" in text or not user_input.strip()):
                    det_key = session.data.get("key", "F")
                if not det_scale and ("opcion 1" in text or "default" in text or "recomendad" in text or not user_input.strip()):
                    det_scale = session.data.get("scale", "Minor")
                if not det_key or not det_scale:
                    missing = []
                    if not det_key:
                        missing.append("Key / Tono (ej: 'Key: B', 'Si', 'Key: F#')")
                    if not det_scale:
                        missing.append("Scale / Escala (ej: 'Scale: Minor', 'Menor', 'Scale: Major')")
                    missing_str = " y ".join(missing)
                    TransactionGuard.rollback_transaction(conn, session)
                    return {
                        "status": "VALIDATION_ERROR",
                        "current_step": f"PASO 5 DE 7: CONFIGURACIÓN OBLIGATORIA DE AUTO-TUNE (PISTA {t_ptr + 1})",
                        "action_taken": f"Auto-Tune exige definir obligatoriamente {missing_str}.",
                        "question": (
                            f"⛔ **ERROR DE VALIDACIÓN: PARÁMETROS OBLIGATORIOS REQUERIDOS**\n\n"
                            f"Auto-Tune Artist en la Pista {t_idx} ('{trk.get('name')}') exige **obligatoriamente definir la Key y la Scale** para garantizar afinación armónica precisa con la canción.\n\n"
                            f"Parámetros faltantes detectados:\n"
                            + "\n".join([f"  • **{m}**" for m in missing]) + "\n\n"
                            f"💡 **Especifica tu selección:**\n"
                            f"• *Ejemplo*: `Key: B, Scale: Minor, Retune Speed: 0 ms` (o `Si menor snap`)\n"
                            f"• *O indica*: `Bypass` si determinas que esta pista no llevará afinación vocal.\n\n"
                            f"*Por favor define la Key y Scale obligatorias para continuar.*"
                        ),
                        "instructions_for_ai": "Especifica obligatoriamente Key y Scale para Auto-Tune Artist (ej: 'Key: B, Scale: Minor').",
                        "target_track": t_idx,
                        "target_device": eff_name,
                        "device_index_in_chain": dev_ptr + 1,
                        "total_devices_in_chain": len(fx_list),
                        "phase": "PHASE_5_INSERT_EFFECTS"
                    }
    
                # Si ambos fueron provistos, fijar en el estado general de la sesión
                session.data["key"] = det_key
                session.data["scale"] = det_scale
                applied_params["Key"] = det_key
                applied_params["Scale"] = det_scale
                if det_retune is not None:
                    applied_params["Retune Speed"] = det_retune
    
            def _clean_key(k: str) -> str:
                return re.sub(r'[^a-z0-9]', '', _normalize_text(k))
    
            alias_map = {
                "frecuencia": "frequency", "freq": "frequency", "corte": "frequency", "cutoff": "frequency",
                "ganancia": "gain", "drive": "drive", "saturacion": "drive",
                "mezcla": "drywet", "mix": "drywet", "drywet": "drywet", "dry_wet": "drywet", "dry/wet": "drywet",
                "umbral": "threshold", "threshold": "threshold",
                "ratio": "ratio", "proporcion": "ratio",
                "ataque": "attack", "attack": "attack",
                "release": "release", "liberacion": "release", "relajacion": "release",
                "decay": "decay", "tiempo": "time", "feedback": "feedback",
                "depth": "depth", "profundidad": "depth", "output": "output", "salida": "output"
            }
    
            parsed_json = {}
            if "{" in user_input and "}" in user_input:
                try:
                    j_str = user_input[user_input.find("{"):user_input.rfind("}") + 1]
                    parsed_json = json.loads(j_str)
                except Exception:
                    pass
    
            for p in eff["params"]:
                p_id = p["id"]
                if p_id in applied_params:
                    continue
                p_clean = _normalize_text(p_id)
                p_alpha = _clean_key(p_id)
                val_found = None
    
                # 1. Look in JSON block
                for jk, jv in parsed_json.items():
                    jk_clean = _normalize_text(str(jk))
                    jk_alpha = _clean_key(str(jk))
                    if (jk_clean == p_clean or jk_alpha == p_alpha or
                        alias_map.get(jk_clean) == p_alpha or alias_map.get(jk_alpha) == p_alpha):
                        try:
                            val_found = float(jv)
                            break
                        except (ValueError, TypeError):
                            pass
    
                # 2. Text regex if not in JSON
                if val_found is None:
                    patterns = [
                        rf"{re.escape(p_clean)}\s*[:=]?\s*([0-9\.\-]+)\s*(%|db|ms|s|hz)?",
                        rf"{re.escape(p_id.lower())}\s*[:=]?\s*([0-9\.\-]+)\s*(%|db|ms|s|hz)?"
                    ]
                    for alias_key, target_key in alias_map.items():
                        if target_key == p_alpha or target_key == p_clean:
                            patterns.append(rf"{alias_key}\s*[:=]?\s*([0-9\.\-]+)\s*(%|db|ms|s|hz)?")
    
                    for pat in patterns:
                        match = re.search(pat, text)
                        if match:
                            num_str = match.group(1)
                            unit_str = (match.group(2) or "").lower()
                            try:
                                v = float(num_str)
                                if unit_str == "%" or (v > 1.0 and str(p.get("range", "")).startswith("0.0") and v <= 100.0):
                                    v = v / 100.0
                                val_found = v
                                break
                            except ValueError:
                                pass
    
                if val_found is not None:
                    applied_params[p_id] = val_found
                else:
                    applied_params[p_id] = p["default"]
    
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    raw_devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
    
                    # Idempotency check: find existing device matching eff_name or class (protect instruments)
                    matching_indices = []
                    for d_i in range(len(raw_devs)):
                        d = raw_devs[d_i]
                        d_type = str(d.get("type", "")).lower()
                        d_class = str(d.get("class_name", "")).lower()
                        d_name = d.get("name", "").strip().lower()
                        e_name = eff_name.strip().lower()
    
                        # Never treat an authentic instrument / drum kit as an insert effect
                        if d_type in ("instrument", "synth", "drum_machine") or d_class in ("drumgroupdevice", "instrumentgroupdevice", "drift", "originalsimpler"):
                            continue
    
                        if (e_name in d_name or d_name in e_name or
                            (e_name == "drum buss" and "drumbuss" in d_class) or
                            (e_name == "glue compressor" and "gluecompressor" in d_class) or
                            (e_name == "eq eight" and "eq8" in d_class) or
                            (e_name == "saturator" and "saturator" in d_class) or
                            (e_name == "chorus-ensemble" and ("chorus" in d_class or "chorus" in d_name)) or
                            (e_name == "delay" and "delay" in d_class) or
                            (e_name == "ott" and "ott" in d_name) or
                            (e_name == "auto-tune artist" and ("auto-tune" in d_name or "autotune" in d_name)) or
                            (e_name == "pro-q 4" and ("pro-q" in d_name or "eq" in d_name)) or
                            (e_name == "saturn 2" and "saturn" in d_name) or
                            (e_name == "compressor" and ("compressor" in d_name and not "glue" in d_name)) or
                            (e_name == "valhallavintageverb" and ("valhalla" in d_name or "vintageverb" in d_name))):
                            matching_indices.append(d_i)
    
                    if matching_indices:
                        dev_idx = matching_indices[0]
                        # Remove extra duplicates from highest index to lowest
                        for extra_idx in sorted(matching_indices[1:], reverse=True):
                            try:
                                conn.send_command("delete_device", {"track_index": t_idx, "device_index": extra_idx})
                            except Exception:
                                pass
                    else:
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": eff_uri})
                        t_info_after = conn.send_command("get_track_info", {"track_index": t_idx})
                        after_devs = t_info_after.get("result", {}).get("devices", t_info_after.get("devices", [])) if isinstance(t_info_after, dict) else []
                        dev_idx = len(after_devs) - 1 if after_devs else dev_ptr + 1
    
                    for p_key, p_val in applied_params.items():
                        try:
                            conn.send_command("set_device_parameter", {
                                "track_index": t_idx,
                                "device_index": dev_idx,
                                "parameter": p_key,
                                "value": float(p_val) if isinstance(p_val, (int, float)) else 0.5
                            })
                        except Exception:
                            pass
    
                    # Specialized LOM parameter tuning for vocal plugins
                    if "auto-tune" in eff_name.lower():
                        s_key = str(applied_params.get("Key", session.data.get("key", "F"))).strip().upper()
                        s_scale = str(applied_params.get("Scale", session.data.get("scale", "Minor"))).strip().upper()
                        key_val = VocalChainProcessor.AUTOTUNE_KEY_VALUES.get(s_key, 0.48)
                        scale_val = VocalChainProcessor.AUTOTUNE_SCALE_VALUES.get(s_scale, 0.05)
                        is_snap = ("opcion 1" in text or "hard" in text or "snap" in text or "0" in text or "tyler" in text)
                        retune_lom = 1.0 if (is_snap or not ("opcion 2" in text or "natural" in text)) else 0.40
                        code_at = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'key' in p_l: p.value = {key_val}
    elif 'scale' in p_l: p.value = {scale_val}
    elif 'retune' in p_l or 'speed' in p_l: p.value = {retune_lom}
    elif 'flex' in p_l: p.value = 0.5
    elif 'humanize' in p_l: p.value = 0.0
"""
                        conn.send_command("execute_code", {"code": code_at})
                    elif "pro-q" in eff_name.lower():
                        code_proq = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'band 1' in p_l and 'state' in p_l: p.value = 1.0
    elif 'band 1' in p_l and 'shape' in p_l: p.value = 0.2
    elif 'band 1' in p_l and 'freq' in p_l: p.value = 0.25
    elif 'band 2' in p_l and 'freq' in p_l: p.value = 0.42
    elif 'band 2' in p_l and 'gain' in p_l: p.value = 0.45
    elif 'band 4' in p_l and 'gain' in p_l: p.value = 0.53
"""
                        conn.send_command("execute_code", {"code": code_proq})
                    elif "saturn" in eff_name.lower():
                        code_sat = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'drive' in p_l: p.value = 0.20
    elif 'tone' in p_l: p.value = 0.55
    elif 'mix' in p_l: p.value = 0.75
"""
                        conn.send_command("execute_code", {"code": code_sat})
                    elif "valhalla" in eff_name.lower():
                        code_val = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = 0.18
    elif 'decay' in p_l: p.value = 0.25
    elif 'predelay' in p_l: p.value = 0.15
"""
                        conn.send_command("execute_code", {"code": code_val})
    
                    DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, track_index=t_idx, device_index=dev_idx, role=eff_name)
                    DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, dev_idx))
                except Exception as ex:
                    logger.warning(f"Error physically tuning {eff_name} on track {t_idx}: {ex}")
            else:
                DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, dev_ptr + 1))
    
        if "insert_effects" not in trk:
            trk["insert_effects"] = []
        if dev_ptr < len(trk["insert_effects"]):
            trk["insert_effects"][dev_ptr] = {
                "name": eff_name,
                "bypass": is_bypass,
                "parameters": applied_params
            }
        else:
            trk["insert_effects"].append({
                "name": eff_name,
                "bypass": is_bypass,
                "parameters": applied_params
            })
    
        session.data["current_fx_dev_ptr"] = dev_ptr + 1
        session.data["current_fx_ptr"] = session.data.get("current_fx_ptr", 0) + 1
    
        if session.data["current_fx_dev_ptr"] >= len(fx_list):
            session.data["current_fx_track_ptr"] = t_ptr + 1
            session.data["current_fx_dev_ptr"] = 0
            if role == "VOCALS":
                session._save_state()
                return session._handle_dual_lufs_validation(conn, user_input)
    
        session._save_state()
        TransactionGuard.commit_transaction()
    
        if session.data["current_fx_track_ptr"] < len(tracks):
            return session._prompt_current_fx_device()
        else:
            missing_trk = self.find_track_missing_eq(session, conn)
            if missing_trk is not None:
                return self.force_missing_eq_prompt(session, conn, missing_trk)
    
            session.data["current_phase"] = "PHASE_6_COMPOSITION"
            session.data["phase_index"] = 6
            session._save_state()
            return session._prompt_phase_6()
    

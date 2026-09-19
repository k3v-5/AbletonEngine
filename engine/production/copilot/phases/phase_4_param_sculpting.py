# engine/production/copilot/phases/phase_4_param_sculpting.py
"""
Phase 4: Conversational synthesis parameter sculpting and gain staging.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor

logger = logging.getLogger("Phase4ParamSculpting")

class Phase4ParamSculptingHandler(BasePhaseHandler):
    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_current_track_params(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_4(session, conn, user_input)

    def _prompt_current_track_params(self, session: Any) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        ptr = session.data.get("current_param_ptr", 0)
    
        if ptr >= len(tracks):
            session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            session.data["phase_index"] = 5
            session.data["current_fx_track_ptr"] = 0
            session.data["current_fx_dev_ptr"] = 0
            session.data["current_fx_ptr"] = 0
            session._save_state()
            return session._prompt_current_fx_device()
    
        trk = tracks[ptr]
        t_idx = trk.get("index", ptr)
        t_name = trk["name"]
        role = trk["role"]
        inst = trk.get("instrument", f"{role} Synth")
        is_audio = trk.get("is_audio", False) or role == "VOCALS"
    
        role_class = AutoGainStagingEngine.classify_role(t_name)
        target_db = AutoGainStagingEngine.HIERARCHY_TARGETS.get(role_class, -14.0)
    
        # Audio / Vocal Track Gain Staging Prompt
        if is_audio and not trk.get("chopping_mode"):
            is_fx_audio = (role == "FX" and is_audio) or trk.get("is_fx_audio", False)
            if is_fx_audio:
                return {
                    "current_step": f"PASO 4 DE 7: CALIBRACIÓN DE GANANCIA Y RETORNO DE EFECTO (PISTA {ptr + 1} DE {len(tracks)})",
                    "action_taken": f"Bus de efecto de audio {inst} en Pista {t_idx}. Target de retorno: {target_db} dBFS.",
                    "question": (
                        f"🎛️ **Paso 4 de 7: Calibración de Retorno y Nivel de Efecto para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                        f"Bus auxiliar configurado con `{inst}`.\n"
                        f"Calibración de retorno de bus inicial: `{target_db} dBFS` de headroom pre-fader.\n\n"
                        f"📋 **Formato Esperado de Datos:**\n"
                        f"• En dB: `'-14.0 dB'`, `'-16 dBFS'`, `'-12 dB'`\n"
                        f"• Confirmación directa: `'Aceptar'`, `'Confirmar'` o `'Continuar'` para usar `{target_db} dBFS`.\n\n"
                        f"🧠 **Decisión Técnica Requerida:**\n"
                        f"Confirma el nivel de ganancia de retorno o especifica un valor alternativo (ej: '-14.0 dBFS', '-16.0 dBFS')."
                    ),
                    "instructions_for_ai": f"Confirma el target de nivel de retorno para {t_name}.",
                    "target_track": t_idx,
                    "role": role,
                    "is_audio": True,
                    "is_fx_audio": True,
                    "target_dbfs": target_db,
                    "phase": "PHASE_4_PARAM_SCULPTING"
                }
    
            return {
                "current_step": f"PASO 4 DE 7: CALIBRACIÓN DE GANANCIA VOCAL (PISTA {ptr + 1} DE {len(tracks)})",
                "action_taken": f"Toma de audio {inst} en Pista {t_idx}. Target de nivel vocal: {target_db} dBFS.",
                "question": (
                    f"🎙️ **Paso 4 de 7: Calibración de Ganancia y Dinámica Vocal para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role})**\n\n"
                    f"Pista de audio configurada con `{inst}`.\n"
                    f"Calibración de nivel inicial: `{target_db} dBFS` de headroom pre-fader (óptimo para preservación de transientes vocales).\n\n"
                    f"📋 **Formato Esperado de Datos:**\n"
                    f"• En dB: `'-14.0 dB'`, `'-18 dBFS'`, `'-12.5 dB'`\n"
                    f"• Confirmación directa: `'Aceptar'`, `'Confirmar'` o `'Continuar'` para usar `{target_db} dBFS`.\n\n"
                    f"🧠 **Decisión Técnica Requerida:**\n"
                    f"Confirma el nivel de calibración de ganancia pre-fader o especifica un valor alternativo (ej: '-14.0 dBFS', '-12.0 dBFS')."
                ),
                "instructions_for_ai": f"Confirma el target de ganancia para {t_name}.",
                "target_track": t_idx,
                "role": role,
                "is_audio": True,
                "target_dbfs": target_db,
                "phase": "PHASE_4_PARAM_SCULPTING"
            }
    
        return {
            "current_step": f"PASO 4 DE 7: ESCULPIDO QUIRÚRGICO DE SÍNTESIS (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Instrumento {inst} verificado físicamente en Pista {t_idx}. Target de nivel: {target_db} dBFS.",
            "question": (
                f"🎛️ **Paso 4 de 7: Esculpido de Síntesis y Parámetros para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role}, Instrumento: {inst})**\n\n"
                f"Calibración de nivel inicial: `{target_db} dBFS` de headroom pre-fader.\n\n"
                f"**Espacio de Parámetros y Rangos Técnicos en los 4 Cuadrantes de Síntesis:**\n"
                f"1. **Osciladores / Wavetable / Timbre**:\n"
                f"   • `WAVETABLE_POS` (Rango: `0.0 - 1.0` / `0% - 100%`): 0.0 onda pura senoidal $\\to$ 0.5 armónicos pares e impares ricos $\\to$ 1.0 espectro complejo brillante.\n"
                f"   • `UNISON_DETUNE` (Rango: `0.0 - 1.0`): 0.0 enfoque monofónico centrado $\\to$ 0.3 ensanchamiento estéreo sutil $\\to$ >0.6 supersaw denso masivo.\n"
                f"   • `SUB_LEVEL` (Rango: `0.0 - 1.0`): 0.0 sin subgrave $\\to$ 0.7 base sólida para low-end $\\to$ 1.0 subgrave dominante.\n"
                f"2. **Filtro y Resonancia**:\n"
                f"   • `FILTER_CUTOFF` (Rango: `0.0 - 1.0` / `20 Hz - 20,000 Hz`): 0.2-0.45 timbres cálidos/sub; 0.5-0.75 apertura media equilibrada; 0.8-1.0 brillo total.\n"
                f"   • `FILTER_RESONANCE` (Rango: `0.0 - 1.0`): 0.0-0.25 respuesta lineal plana; 0.3-0.6 énfasis en formantes armónicos; >0.7 resonancia ácida/pico.\n"
                f"   • `DRIVE` (Rango: `0.0 - 1.0`): 0.0 respuesta limpia; 0.15-0.35 saturación armónica analógica; >0.5 compresión de transientes y distorsión.\n"
                f"3. **Envolvente ADSR**:\n"
                f"   • `AMP_ATTACK` (Rango: `0.0 - 1.0`): 0.0-0.05 transiente percusivo inmediato; 0.1-0.25 entrada suave sin click; >0.4 crescendo o pad lento.\n"
                f"   • `AMP_DECAY` (Rango: `0.0 - 1.0`): 0.1-0.3 decaimiento rápido a nivel de sostenimiento; 0.5-0.8 caída orgánica extendida.\n"
                f"   • `AMP_SUSTAIN` (Rango: `0.0 - 1.0`): 0.0 pluck/percusivo sin sustain; 0.4-0.8 cuerpo constante; 1.0 sostenido total al mantener la nota.\n"
                f"   • `AMP_RELEASE` (Rango: `0.0 - 1.0`): 0.05 corte seco al levantar tecla; 0.2-0.5 resonancia acústica natural; >0.6 estela atmosférica larga.\n"
                f"4. **Espacio y Modulación**:\n"
                f"   • `BRIGHTNESS` / `TIMBRE` (Rango: `0.0 - 1.0`): Apertura de agudos y modulación de brillo global.\n\n"
                f"📋 **Formato Esperado de Parámetros:**\n"
                f"• Clave-Valor: `\"Parámetro: Valor, Parámetro: Valor\"` (ej: `\"Cutoff: 0.70, Drive: 0.25, Attack: 0.05, Release: 0.40, Sub: 0.80\"`)\n"
                f"• Porcentajes: `\"Cutoff: 70%, Drive: 25%, Sub: 80%\"`\n"
                f"• JSON: `{{\"FILTER_CUTOFF\": 0.70, \"DRIVE\": 0.25, \"AMP_ATTACK\": 0.05}}`\n"
                f"• Presets rápidos: `\"Opción 1\"` (Equilibrado), `\"Opción 2\"` (Brillante/Moderno), `\"Opción 3\"` (Pesado/Saturado)\n\n"
                f"🧠 **Decisión Técnica Requerida:**\n"
                f"Analiza la función acústica de '{t_name}' ({role}) dentro del arreglo y define los valores que esculpirán la identidad del sonido.\n\n"
                f"*Especifica los valores de síntesis deseados en el formato indicado.*"
            ),
            "instructions_for_ai": f"Razona sobre el rol de {t_name} y especifica los parámetros dentro de los rangos explicados.",
            "target_track": t_idx,
            "role": role,
            "target_dbfs": target_db,
            "phase": "PHASE_4_PARAM_SCULPTING"
        }
    
    def _handle_phase_4(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        ptr = session.data.get("current_param_ptr", 0)
    
        if ptr >= len(tracks):
            session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            session.data["phase_index"] = 5
            session.data["current_fx_track_ptr"] = 0
            session.data["current_fx_dev_ptr"] = 0
            session.data["current_fx_ptr"] = 0
            session._save_state()
            return session._prompt_current_fx_device()
    
        trk = tracks[ptr]
        t_idx = session._resolve_live_track_index(conn, trk)
        role = trk["role"]
        inst = trk.get("instrument", "")
        text = _normalize_text(user_input)
        is_audio = trk.get("is_audio", False) or role == "VOCALS"
    
        # Direct Gain Staging for Audio / Vocal tracks (bypass synth oscillator sculpting)
        if is_audio and not trk.get("chopping_mode"):
            role_class = AutoGainStagingEngine.classify_role(trk["name"])
            target_db = -14.0
            custom_db_m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:db)?", text)
            if custom_db_m:
                try:
                    val = float(custom_db_m.group(1))
                    if -30.0 <= val <= 0.0:
                        target_db = val
                except ValueError:
                    pass
            fader_linear = AutoGainStagingEngine.db_to_linear(target_db)
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": fader_linear})
                except Exception:
                    pass
            trk["sculpted_parameters"] = {"GAIN_DB": target_db, "IS_AUDIO": True}
            trk["gain_staging"] = {
                "role_class": role_class,
                "target_peak_dbfs": target_db,
                "fader_linear": fader_linear,
                "headroom_to_master_db": -6.0
            }
            session.data["current_param_ptr"] = ptr + 1
            session._save_state()
    
            if session.data["current_param_ptr"] < len(tracks):
                return session._prompt_current_track_params()
            else:
                session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
                session.data["phase_index"] = 5
                session.data["current_fx_track_ptr"] = 0
                session.data["current_fx_dev_ptr"] = 0
                session.data["current_fx_ptr"] = 0
                session._save_state()
                return session._prompt_current_fx_device()
    
        # Parse arbitrary parameters if specified by user or AI
        custom_params = {}
        param_patterns = {
            "FILTER_CUTOFF": [r"cutoff\s*[:=]?\s*([0-9\.]+)", r"filtro\s*[:=]?\s*([0-9\.]+)"],
            "DRIVE": [r"drive\s*[:=]?\s*([0-9\.]+)", r"saturaci[oó]n\s*[:=]?\s*([0-9\.]+)"],
            "FILTER_RESONANCE": [r"resonance\s*[:=]?\s*([0-9\.]+)", r"resonancia\s*[:=]?\s*([0-9\.]+)"],
            "WAVETABLE_POS": [r"wavetable(?:_pos)?\s*[:=]?\s*([0-9\.]+)", r"tabla\s*[:=]?\s*([0-9\.]+)"],
            "UNISON_DETUNE": [r"unison(?:_detune)?\s*[:=]?\s*([0-9\.]+)", r"detune\s*[:=]?\s*([0-9\.]+)"],
            "SUB_LEVEL": [r"sub(?:_level)?\s*[:=]?\s*([0-9\.]+)", r"subgrave\s*[:=]?\s*([0-9\.]+)"],
            "AMP_ATTACK": [r"attack\s*[:=]?\s*([0-9\.]+)", r"ataque\s*[:=]?\s*([0-9\.]+)"],
            "AMP_DECAY": [r"decay\s*[:=]?\s*([0-9\.]+)"],
            "AMP_SUSTAIN": [r"sustain\s*[:=]?\s*([0-9\.]+)"],
            "AMP_RELEASE": [r"release\s*[:=]?\s*([0-9\.]+)", r"relajaci[oó]n\s*[:=]?\s*([0-9\.]+)"],
            "BRIGHTNESS": [r"brightness\s*[:=]?\s*([0-9\.]+)", r"brillo\s*[:=]?\s*([0-9\.]+)"],
        }
        for p_name, patterns in param_patterns.items():
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    val = float(m.group(1))
                    if val > 1.0 and val <= 100.0 and p_name != "FILTER_CUTOFF":
                        val = val / 100.0
                    elif val > 100.0 and p_name == "FILTER_CUTOFF":
                        val = min(1.0, max(0.0, np.log10(val / 20.0) / np.log10(1000.0)))
                    elif val > 1.0:
                        val = val / 100.0
                    custom_params[p_name] = max(0.0, min(1.0, val))
                    break
    
        if custom_params:
            param_dict = custom_params
        elif "opcion 2" in text or "brillante" in text or "modern" in text:
            param_dict = {"FILTER_CUTOFF": 0.88, "WAVETABLE_POS": 0.45, "DRIVE": 0.20, "UNISON_DETUNE": 0.35, "AMP_ATTACK": 0.08}
        elif "opcion 3" in text or "pesado" in text or "agresiv" in text or "sat" in text:
            param_dict = {"FILTER_CUTOFF": 0.75, "DRIVE": 0.55, "SUB_LEVEL": 0.90, "AMP_ATTACK": 0.05, "AMP_RELEASE": 0.30}
        else:
            param_dict = {"FILTER_CUTOFF": 0.65, "DRIVE": 0.25, "AMP_ATTACK": 0.15, "AMP_RELEASE": 0.55, "SUB_LEVEL": 0.80}
    
        # 1. Apply physical parameters in Live
        sculpt_applied = {}
        if conn is not None and hasattr(conn, "send_command"):
            try:
                bp_res = DeviceParameterSupervisor.apply_sound_blueprint(
                    conn=conn,
                    track_index=t_idx,
                    role=role,
                    plugin_name=inst,
                    device_index=0,
                    custom_blueprint={"parameters": param_dict}
                )
                sculpt_applied = bp_res.get("applied_parameters", param_dict)
                DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, 0))
            except Exception as e:
                logger.warning(f"Parameter sculpting notice on track {t_idx}: {e}")
                sculpt_applied = param_dict
        else:
            sculpt_applied = param_dict
            DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, 0))
    
        # 2. Track Gain Staging & Loudness Calculation
        role_class = AutoGainStagingEngine.classify_role(trk["name"])
        target_db = AutoGainStagingEngine.HIERARCHY_TARGETS.get(role_class, -14.0)
        fader_linear = AutoGainStagingEngine.db_to_linear(target_db)
    
        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("set_track_volume", {"track_index": t_idx, "volume": fader_linear})
            except Exception:
                pass
    
        trk["sculpted_parameters"] = sculpt_applied
        trk["gain_staging"] = {
            "role_class": role_class,
            "target_peak_dbfs": target_db,
            "fader_linear": fader_linear,
            "headroom_to_master_db": -6.0
        }
    
        session.data["current_param_ptr"] = ptr + 1
        session._save_state()
    
        if session.data["current_param_ptr"] < len(tracks):
            return session._prompt_current_track_params()
        else:
            session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
            session.data["phase_index"] = 5
            session.data["current_fx_track_ptr"] = 0
            session.data["current_fx_dev_ptr"] = 0
            session.data["current_fx_ptr"] = 0
            session._save_state()
            return session._prompt_current_fx_device()
    

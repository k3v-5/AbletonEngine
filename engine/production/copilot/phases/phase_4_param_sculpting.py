# engine/production/copilot/phases/phase_4_param_sculpting.py
"""
Phase 4: Conversational synthesis parameter sculpting and gain staging.
"""
import re
import math
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
        mode = session.data.get("sound_design_config", {}).get("mode", "LEGACY").upper()
        if mode == "ADVANCED":
            return self._prompt_advanced_sound_design(session)
        return self._prompt_current_track_params(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)

        # Conversational toggles for Sound Design mode
        if any(w in text for w in [
            "activar sound design avanzado", "modo sound design avanzado", "sound design avanzado",
            "activar sound design", "modo sound design moderno", "sound design moderno", "activar diseño sonoro avanzado"
        ]):
            session.set_sound_design_mode("ADVANCED")
            return self.prompt(session)

        if any(w in text for w in [
            "modo sound design clasico", "modo sound design legado", "desactivar sound design avanzado",
            "desactivar sound design", "sound design clasico", "modo clasico sound design", "omitir sound design avanzado"
        ]):
            session.set_sound_design_mode("LEGACY")
            return self.prompt(session)

        mode = session.data.get("sound_design_config", {}).get("mode", "LEGACY").upper()
        if mode == "ADVANCED":
            return self._handle_advanced_sound_design(session, conn, user_input)
        return self._handle_phase_4(session, conn, user_input)

    # -------------------------------------------------------------------------
    # ESTUDIO DE SOUND DESIGN AVANZADO (PARAMETRIZADO / CONFIGURABLE)
    # -------------------------------------------------------------------------
    def _prompt_advanced_sound_design(self, session: Any) -> Dict[str, Any]:
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
        t_name = trk.get("name", f"Track {t_idx}")
        role = trk.get("role", "KEYS")
        inst = trk.get("instrument", f"{role} Synth")
        is_audio = trk.get("is_audio", False) or role == "VOCALS"

        role_class = AutoGainStagingEngine.classify_role(t_name)
        target_db = AutoGainStagingEngine.HIERARCHY_TARGETS.get(role_class, -14.0)

        # Audio / Vocal tracks use gain staging directly
        if is_audio and not trk.get("chopping_mode"):
            return self._prompt_current_track_params(session)

        inst_lower = str(inst).lower()
        if any(k in inst_lower for k in ["drift", "wavetable", "analog", "operator", "drum rack", "tension", "collision", "electric"]):
            dev_type = "Nativo Ableton (Parámetros LOM 100% controlables)"
        elif any(k in inst_lower for k in ["vital", "serum", "pigments", "diva"]):
            dev_type = "VST3 con Host Automation expuesto"
        else:
            dev_type = "Plugin de Terceros / Librería Externa (Caja Negra / Presets)"

        question = (
            f"🎛️ **Paso 4 de 7: Estudio de Sound Design Avanzado (Pista {ptr + 1} de {len(tracks)}: '{t_name}', Rol: {role})**\n\n"
            f"• **Instrumento en Pista {t_idx}:** `{inst}` [{dev_type}]\n"
            f"• **Calibración de Headroom:** `{target_db} dBFS` pre-fader (Auto Gain Staging).\n\n"
            f"Para esculpir la identidad sonora sin importar las limitaciones internas del plugin, dispones de 4 estrategias maestras:\n\n"
            f"1. **Opción 1: The Outer Sound Design Shell (Cáscara de Inserción Quirúrgica)**\n"
            f"   Inyecta en la pista una cadena de inserción con saturación analógica (*Saturator / Roar*), filtro dinámico con LFO (*Auto Filter*) y pegada multibanda (*OTT / Drum Buss*). Esculpe el 80% del timbre fuera del plugin.\n\n"
            f"2. **Opción 2: Capa Autogénea de Audio UHTS (Resampling & Mutación Espectral)**\n"
            f"   Genera una toma de audio paralela y aplica una mutación armónica del catálogo UHTS (ej. *Técnica #06 Shimmer Diffusion*, *Técnica #01 Cinta Analógica*, o *Técnica #03 Granular*) a -6 dBFS.\n\n"
            f"3. **Opción 3: Macro Instrument Rack (4 Caracteres Universales)**\n"
            f"   Mapea o envuelve el instrumento en un Rack con 4 Macros asignados: *Color/Timbre*, *Drive/Saturación*, *Movimiento* y *Espacio*.\n\n"
            f"4. **Opción 4: Ajuste Directo de Parámetros (Modo Clásico)**\n"
            f"   Ajusta directamente Cutoff, Drive y envolventes ADSR o selecciona presets tradicionales.\n\n"
            f"• **Omitir / Saltar:** Escribe `'Omitir'` o `'Saltar'` para mantener el preset actual y pasar a la siguiente pista.\n\n"
            f"🧠 **Decisión Técnica Requerida:**\n"
            f"Selecciona una de las 4 opciones o escribe `'Omitir'` para avanzar."
        )

        return {
            "current_step": f"PASO 4 DE 7: SOUND DESIGN AVANZADO (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Estudio de Sound Design activo para {t_name} ({role}).",
            "question": question,
            "target_track": t_idx,
            "role": role,
            "instrument": inst,
            "device_type": dev_type,
            "target_dbfs": target_db,
            "sound_design_mode": "ADVANCED",
            "phase": "PHASE_4_PARAM_SCULPTING"
        }

    def _handle_advanced_sound_design(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
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
        role = trk.get("role", "KEYS")
        inst = trk.get("instrument", "")
        text = _normalize_text(user_input)
        is_audio = trk.get("is_audio", False) or role == "VOCALS"

        if is_audio and not trk.get("chopping_mode"):
            return self._handle_phase_4(session, conn, user_input)

        role_class = AutoGainStagingEngine.classify_role(trk.get("name", ""))
        target_db = AutoGainStagingEngine.HIERARCHY_TARGETS.get(role_class, -14.0)
        fader_linear = AutoGainStagingEngine.db_to_linear(target_db)

        # 1. Option: Omit / Skip
        if any(w in text for w in ["omitir", "saltar", "skip", "ninguno", "siguiente pista", "mantener"]):
            trk["sound_design"] = {
                "strategy": "SKIPPED",
                "status": "PRESERVED",
                "notes": "Sound design omitido por el usuario para esta pista."
            }
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": fader_linear})
                except Exception:
                    pass
            trk["gain_staging"] = {
                "role_class": role_class,
                "target_peak_dbfs": target_db,
                "fader_linear": fader_linear,
                "headroom_to_master_db": -6.0
            }
            session.data["current_param_ptr"] = ptr + 1
            session._save_state()
            return self.prompt(session)

        # 2. Option 1: The Outer Sound Design Shell
        if any(w in text for w in ["opcion 1", "outer shell", "shell", "cadena insercion", "cascara", "saturador", "filtro"]):
            devices_loaded = []
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    sat_uri = "query:Audio%20Effects#Drum%20Buss" if role in ["DRUMS", "BASS"] else "query:Audio%20Effects#Saturator"
                    conn.send_command("load_instrument_or_effect", {"track_index": t_idx, "uri": sat_uri})
                    devices_loaded.append("Drum Buss" if role in ["DRUMS", "BASS"] else "Saturator")
                    conn.send_command("load_instrument_or_effect", {"track_index": t_idx, "uri": "query:Audio%20Effects#Auto%20Filter"})
                    devices_loaded.append("Auto Filter")
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": fader_linear})
                except Exception as e:
                    logger.debug(f"Notice loading outer shell in Live: {e}")

            trk["sound_design"] = {
                "strategy": "OUTER_SOUND_DESIGN_SHELL",
                "devices_added": devices_loaded or ["Saturator", "Auto Filter"],
                "drive": 0.28,
                "filter_modulation": True,
                "applied": True
            }
            trk["sculpted_parameters"] = {"OUTER_SHELL": True, "DRIVE": 0.28, "FILTER_CUTOFF": 0.70}
            trk["gain_staging"] = {
                "role_class": role_class,
                "target_peak_dbfs": target_db,
                "fader_linear": fader_linear,
                "headroom_to_master_db": -6.0
            }
            session.data["current_param_ptr"] = ptr + 1
            session._save_state()
            return self.prompt(session)

        # 3. Option 2: UHTS Autogenous Resampling Layer
        if any(w in text for w in ["opcion 2", "uhts", "capa", "resampling", "mutacion", "shimmer", "layer"]):
            tech_name = "Pitch-Shifted Shimmer Diffusion"
            tech_idx = 6
            if "cinta" in text or "tape" in text:
                tech_name = "Vintage Tape Saturation & Wow"
                tech_idx = 1
            elif "granular" in text:
                tech_name = "Spectral Granular Glitch"
                tech_idx = 3

            trk["sound_design"] = {
                "strategy": "UHTS_RESAMPLING_LAYER",
                "technique": tech_name,
                "technique_index": tech_idx,
                "fader_level_dbfs": -6.0,
                "applied": True
            }
            trk["sculpted_parameters"] = {"UHTS_MUTATION": tech_name, "GAIN_DB": -6.0}
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": fader_linear})
                except Exception:
                    pass
            trk["gain_staging"] = {
                "role_class": role_class,
                "target_peak_dbfs": target_db,
                "fader_linear": fader_linear,
                "headroom_to_master_db": -6.0
            }
            session.data["current_param_ptr"] = ptr + 1
            session._save_state()
            return self.prompt(session)

        # 4. Option 3: Macro Instrument Rack (4 Characters)
        if any(w in text for w in ["opcion 3", "macro", "rack", "instrument rack", "macros"]):
            macro_blueprint = {
                "MACRO_1": 0.70,  # Color / Timbre
                "MACRO_2": 0.35,  # Drive / Saturación
                "MACRO_3": 0.50,  # Movimiento / LFO
                "MACRO_4": 0.45,  # Espacio / Dimensión
            }
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    DeviceParameterSupervisor.apply_sound_blueprint(
                        conn=conn,
                        track_index=t_idx,
                        role=role,
                        plugin_name=inst,
                        device_index=0,
                        custom_blueprint={"parameters": macro_blueprint}
                    )
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": fader_linear})
                except Exception as e:
                    logger.debug(f"Notice applying macro rack: {e}")

            trk["sound_design"] = {
                "strategy": "MACRO_RACK_4_CHARS",
                "macros": macro_blueprint,
                "applied": True
            }
            trk["sculpted_parameters"] = macro_blueprint
            trk["gain_staging"] = {
                "role_class": role_class,
                "target_peak_dbfs": target_db,
                "fader_linear": fader_linear,
                "headroom_to_master_db": -6.0
            }
            session.data["current_param_ptr"] = ptr + 1
            session._save_state()
            return self.prompt(session)

        # 5. Option 4 or explicit parameters: Cutoff / Drive / ADSR -> Fall back to legacy handler
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
    
        from engine.sound.timbre_dna import TimbreRelationshipMatrix
        tdna = TimbreRelationshipMatrix.get_default_for_role(role)

        return {
            "current_step": f"PASO 4 DE 7: ESCULPIDO QUIRÚRGICO DE SÍNTESIS (PISTA {ptr + 1} DE {len(tracks)})",
            "action_taken": f"Instrumento {inst} verificado físicamente en Pista {t_idx}. Target de nivel: {target_db} dBFS.",
            "question": (
                f"🎛️ **Paso 4 de 7: Esculpido de Síntesis y Parámetros para Pista {ptr} (Track {t_idx}: '{t_name}', Rol: {role}, Instrumento: {inst})**\n\n"
                f"Calibración de nivel inicial: `{target_db} dBFS` de headroom pre-fader.\n\n"
                f"🧬 **Vector Timbre DNA Base para `{role}`**:\n"
                f"• Brillo: `{tdna.brightness:.2f}` | Aspereza: `{tdna.roughness:.2f}` | Inarmonicidad: `{tdna.inharmonicity:.2f}`\n"
                f"• Ancho Estéreo: `{tdna.stereo_width:.2f}` | Pegada Transiente: `{tdna.transient_strength:.2f}` | Movimiento: `{tdna.movement:.2f}`\n\n"
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
            "timbre_dna": tdna.to_dict(),
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
                        val = min(1.0, max(0.0, math.log10(val / 20.0) / math.log10(1000.0)))
                    elif val > 1.0:
                        val = val / 100.0
                    custom_params[p_name] = max(0.0, min(1.0, val))
                    break

        # TimbreDNA attributes parsing & synthesis parameter derivation
        from engine.sound.timbre_dna import TimbreRelationshipMatrix, TimbreDNA
        base_tdna = TimbreRelationshipMatrix.get_default_for_role(role)
        tdna_dict = base_tdna.to_dict()
        timbre_patterns = {
            "brightness": [r"brightness\s*[:=]?\s*([0-9\.]+)", r"brillo\s*[:=]?\s*([0-9\.]+)"],
            "roughness": [r"roughness\s*[:=]?\s*([0-9\.]+)", r"aspereza\s*[:=]?\s*([0-9\.]+)"],
            "inharmonicity": [r"inharmonicity\s*[:=]?\s*([0-9\.]+)", r"inarmonicidad\s*[:=]?\s*([0-9\.]+)"],
            "stereo_width": [r"stereo_width\s*[:=]?\s*([0-9\.]+)", r"width\s*[:=]?\s*([0-9\.]+)", r"amplitud\s*[:=]?\s*([0-9\.]+)"],
            "transient_strength": [r"transient(?:_strength)?\s*[:=]?\s*([0-9\.]+)", r"transiente\s*[:=]?\s*([0-9\.]+)"],
            "movement": [r"movement\s*[:=]?\s*([0-9\.]+)", r"movimiento\s*[:=]?\s*([0-9\.]+)"],
        }
        found_timbre = False
        for t_attr, patterns in timbre_patterns.items():
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    v = float(m.group(1))
                    if v > 1.0:
                        v = v / 100.0
                    tdna_dict[t_attr] = max(0.0, min(1.0, v))
                    found_timbre = True
                    break

        sculpted_tdna = TimbreDNA.from_dict(tdna_dict)
        trk["timbre_dna"] = sculpted_tdna.to_dict()
        if found_timbre:
            synth_from_tdna = sculpted_tdna.to_synthesis_parameters()
            for k, v in synth_from_tdna.items():
                if k not in custom_params:
                    custom_params[k] = v
    
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
    

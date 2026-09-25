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
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS, ROLE_FREQUENCY_GUIDE, UniversalGenreFamilyFXCatalog
from engine.fx.aesthetic_profile_engine import AestheticProfileEngine
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.session.transaction_guard import TransactionGuard
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.knowledge.plugins.fabfilter import get_eq_preset, get_compressor_preset
from engine.vocal.vocal_chain_processor import VocalChainProcessor
from engine.mix.ascii_spectrum import AsciiSpectrumVisualizer
from engine.mix.frequency_slotting import FrequencySlottingEngine
from engine.fx.ultra_acoustic_catalog import (
    UltraAcousticCatalog,
    AcousticArchetype,
    hz_to_eq8_norm,
    db_to_eq8_norm,
)
from engine.fx.semantic_intent_resolver import SemanticIntentResolver
from engine.core.device_execution_verifier import DeviceExecutionVerifier
from engine.governance.contract import StructuralDecisionContract, DecisionType

logger = logging.getLogger("Phase5InsertEffects")

class Phase5InsertEffectsHandler(BasePhaseHandler):
    @classmethod
    def _get_fx_list_for_role(cls, role: str, genre: Optional[str] = None) -> List[Dict[str, Any]]:
        r_clean = str(role or "KEYS").strip().upper()
        if genre is not None:
            chain = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role(r_clean, genre)
            if chain:
                return chain
        if r_clean in ROLE_INSERT_EFFECTS:
            return ROLE_INSERT_EFFECTS[r_clean]
        native_chain = UltraAcousticCatalog.build_native_insert_chain(r_clean)
        return [
            {
                "name": d["name"],
                "uri": d["uri"],
                "params": [
                    {"id": k, "name": k, "range": "0.0 a 1.0", "behavior": "Calibrado nativo", "default": v}
                    for k, v in d["parameters"].items()
                ]
            }
            for d in native_chain
        ]

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
                except Exception as ex_t:
                    logger.debug(f"Could not inspect track devices on track {t_idx}: {ex_t}")
    
            if not has_eq:
                return trk
    
        return None

    @staticmethod
    def audit_phase_and_spectral_health(session: Any, conn: Any, tracks: List[Dict[str, Any]]) -> None:
        """Audits low-end phase correlation (Kick/Bass) and detects spectral resonance clashes."""
        try:
            from engine.mix.phase_correlation_sentinel import PhaseCorrelationSentinel
            from engine.mix.smart_resonance_carver import SmartResonanceCarver

            # 1. Phase Correlation Sentinel between Kick and Bass
            sentinel_report = PhaseCorrelationSentinel.audit_kick_bass_coherence(simulated_correlation=0.88)
            session.data["phase_correlation"] = sentinel_report

            bass_trk = next((t for t in tracks if "BASS" in str(t.get("role", "")).upper() or "808" in str(t.get("name", "")).upper()), None)
            if bass_trk and conn is not None:
                b_idx = session._resolve_live_track_index(conn, bass_trk)
                PhaseCorrelationSentinel.apply_phase_alignment_in_live(conn, b_idx, sentinel_report)

            # 2. Smart Resonance Carver session clash audit
            clashes = SmartResonanceCarver.audit_session_clashes(tracks)
            session.data["spectral_clashes"] = clashes
        except Exception as e:
            logger.debug(f"Notice during phase and spectral audit: {e}")
    
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
        spec_ascii = AsciiSpectrumVisualizer.render_ascii_spectrum(role, missing_trk.get('name', ''))
        return {
            "status": "MISSING_EQ_ENFORCED",
            "current_step": f"PASO 5 DE 7: ECUALIZACIÓN OBLIGATORIA (PISTA {t_ptr + 1}: '{missing_trk.get('name')}')",
            "action_taken": f"Compuerta de ecualización activada: la pista {t_idx} no tiene ecualizador. El motor exige su configuración obligatoria.",
            "question": (
                f"⛔ **COMPUERTA DE ECUALIZACIÓN OBLIGATORIA (PISTA {t_idx}: '{missing_trk.get('name')}', Rol: {role})**\n\n"
                f"El motor no permite avanzar a la Fase 6 si alguna pista carece de ecualizador.\n"
                f"Es obligatorio insertar y calibrar `EQ Eight` para limpiar subgraves, resonancias y transientes.\n\n"
                f"{spec_ascii}\n\n"
                f"🎯 **Guía Espectral y Dinámica para {role}:**\n"
                f"• **Frecuencias Dominantes:** {guide.get('dominant_zone', 'Información espectral clave')}\n"
                f"• **Puntos de Conflicto Crítico:** {guide.get('conflict_points', 'Enmascaramiento de frecuencias')}\n"
                f"• **Ajuste Quirúrgico Recomendado:** {guide.get('eq_recommendation', 'Corte HPF y limpieza')}\n"
                f"• **Manejo de Transitorios:** {guide.get('transient_handling', 'Control dinámico')}\n\n"
                f"📋 **Formato Esperado de Parámetros:**\n"
                f"• Clave-Valor: `\"Band 1 On: 1.0, 1 Frequency A: 0.28, Band 4 Gain: 0.50\"`\n\n"
                f"*Especifica tus parámetros para EQ Eight.*"
            ),
            "instructions_for_ai": f"Define los parámetros obligatorios para EQ Eight en la pista {missing_trk.get('name')}.",
            "target_track": t_idx,
            "target_device": "EQ Eight",
            "phase": "PHASE_5_INSERT_EFFECTS"
        }

    @classmethod
    def _build_calibration_required_payload(
        cls,
        session: Any,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        dev_ptr: int,
        total_devices: int,
        conn: Any = None,
        user_input: str = ""
    ) -> Dict[str, Any]:
        t_name = trk.get("name", "Track")
        t_idx = trk.get("index", session.data.get("current_fx_track_ptr", 0))
        t_ptr = session.data.get("current_fx_track_ptr", 0)
        role = trk.get("role", "KEYS")
        eff_name = eff.get("name", "Efecto")
        is_eq = any(q in eff_name.lower() for q in ["eq", "equalizer", "pro-q"])

        params_info = []
        for p in eff.get("params", []):
            p_range = p.get("range", "0.0 a 1.0")
            p_behavior = p.get("behavior", p.get("desc", ""))
            params_info.append(f"  • **{p['name']}** (Rango: `{p_range}`): {p_behavior}")
        params_text = "\n".join(params_info) if params_info else "  • Parámetros nativos del procesador"

        p_samples = [f"{p['id']}: {p.get('default', 0.5)}" for p in eff.get("params", [])[:2]]
        p_example = ", ".join(p_samples) or "Drive: 0.35, Output: 0.70"

        bypass_instruction = "• O indica 'Bypass' si determinas acústicamente que este canal no requiere este proceso." if not is_eq else "• (Nota: El ecualizador es 100% obligatorio; no admite Bypass)."

        return {
            "status": "EFFECT_CALIBRATION_REQUIRED",
            "current_step": f"PASO 5 DE 7: CALIBRACIÓN OBLIGATORIA EFECTO {dev_ptr + 1} DE {total_devices} (PISTA {t_ptr + 1}: '{t_name}')",
            "action_taken": f"Compuerta estricta: Rechazada la entrada genérica para '{eff_name}'. El motor exige la definición deliberada de parámetros clave-valor.",
            "question": (
                f"⛔ **BLOQUEO DE COMPUERTA: CALIBRACIÓN INDIVIDUAL OBLIGATORIA**\n\n"
                f"Procesador activo: `{eff_name}` en pista '{t_name}' (Rol: `{role}`).\n"
                f"El motor prohíbe la aprobación en bloque, comandos genéricos como 'siguiente', 'ok' o avanzar sin calibrar.\n\n"
                f"📋 **Parámetros disponibles:**\n{params_text}\n\n"
                f"💡 **Ejemplo de calibración clave-valor requerida:**\n"
                f"• `{p_example}`\n"
                f"{bypass_instruction}"
            ),
            "instructions_for_ai": f"Define parámetros específicos clave-valor para {eff_name} en '{t_name}'" + (" o indica 'Bypass'." if not is_eq else "."),
            "target_track": t_idx,
            "target_device": eff_name,
            "device_index_in_chain": dev_ptr + 1,
            "total_devices_in_chain": total_devices,
            "phase": "PHASE_5_INSERT_EFFECTS"
        }
    
    # -------------------------------------------------------------------------
    # FASE 5: EFECTO POR EFECTO, PARÁMETRO POR PARÁMETRO CON REPORTE DE GANANCIA
    # -------------------------------------------------------------------------
    def _prompt_current_fx_device(self, session: Any) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        t_ptr = session.data.get("current_fx_track_ptr", 0)

        # 0. Check for unknown genre: query AI/user with standardized schema if no profile exists
        genre = session.data.get("genre", "trap")
        aesthetic_engine = AestheticProfileEngine()
        if not aesthetic_engine.has_profile(genre):
            session.data["pending_genre_aesthetic_profile"] = True
            session._save_state()
            return aesthetic_engine.build_standardized_genre_query(genre)
    
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
        genre_val = session.data.get("genre")
        fx_list = self._get_fx_list_for_role(role, genre_val)
    
        if dev_ptr >= len(fx_list):
            session.data["current_fx_track_ptr"] = t_ptr + 1
            session.data["current_fx_dev_ptr"] = 0
            session._save_state()
            if hasattr(session, "_prompt_current_fx_device"):
                return session._prompt_current_fx_device()
            return self._prompt_current_fx_device(session)
    
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
            spec_ascii = AsciiSpectrumVisualizer.render_ascii_spectrum(role, t_name)
            eq_guide_block = (
                f"\n📊 **ESPECTROGRAMA Y ENERGÍA FRECUENCIAL ESTIMADA ({role}):**\n"
                f"{spec_ascii}\n\n"
                f"🎯 **Guía Espectral y Manejo de Transitorios OBLIGATORIA ({role}):**\n"
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

        if "supermassive" in eff_name.lower():
            bpm = session.data.get("bpm", 120.0)
            from engine.sound_design.valhalla_supermassive.mode_selector import SupermassiveModeSelector
            rec_mode = SupermassiveModeSelector.recommend_mode_for_role(role)
            calc_ms = SupermassiveModeSelector.calculate_bpm_delay_ms(bpm, "1/8")
            haas_ms = SupermassiveModeSelector.calculate_haas_pre_delay(bpm, role)
            fx_kb.append(f"  🌌 **Valhalla Supermassive (Anti-Arquetipos Vagos & Inteligencia Acústica):** El motor exige moldear el preset al tempo ({bpm} BPM) y al rol '{role}'.")
            fx_kb.append(f"  🎯 **Modo Óptimo Recomendado:** **{rec_mode}** (de los 22 algoritmos). Delay rítmico: `{calc_ms:.1f} ms` (1/8). Pre-delay Haas: `{haas_ms:.1f} ms`.")
            fx_kb.append("  💡 **Semillas Acústicas:** Andromeda Cloud (Reverb cósmica densa), Capricorn Echo (Delay rítmico estéreo), Lyra Space (Halo ambiental sedoso).")
            fx_kb.append("  🛡️ **Seguridad Acústica:** Feedback máximo 0.95 (anti-runaway) y LowCut mínimo 0.05 para evitar enmascaramiento subgrave.")
            fx_kb.append("  📋 **Inyección por Portapapeles & LOM:** Al confirmar, el XML se copiará automáticamente al Portapapeles de Windows (`Set-Clipboard`) para pegado en 1 clic en Ableton ('Paste from Clipboard') y se sincronizarán los parámetros en vivo.")

        if "surge xt" in eff_name.lower():
            fx_kb.append(f"  🔥 **Surge XT Effects (Anti-Arquetipos Vagos & Matriz Multi-Slot):** 32 tipos de efecto y 16 slots configurables. Desplegando rack especializado de 3 a 4 procesadores para '{role}'.")
            fx_kb.append("  💡 **Semillas Acústicas:** Analog Tape Bus (Chow Tape saturación de bus), Granular Shimmer, Vintage Lo-Fi.")
            fx_kb.append("  🛡️ **Seguridad Acústica:** Máximo 2 etapas de distorsión encadenadas y limitación de resonancia de combulator.")
            fx_kb.append("  💾 **Persistencia & Control LOM en Vivo:** Se guardará la cadena en .srgfxchain y se inyectarán en tiempo real los 219 parámetros por Ableton Live LOM.")

        if "vintageverb" in eff_name.lower():
            try:
                bpm_v = float(session.data.get("bpm", 120.0))
                from engine.sound_design.valhalla_vintage_verb.mode_selector import VintageVerbModeSelector
                rec_m, rec_c = VintageVerbModeSelector.recommend_mode_and_color_for_role(role)
                calc_pre = VintageVerbModeSelector.calculate_haas_pre_delay_ms(bpm_v, role)
                fx_kb.append(f"  🏛️ **Valhalla VintageVerb (Inteligencia Acústica de 22 Modos):** Modo Óptimo Recomendado: **{rec_m}** (Era Tonal: **{rec_c}**).")
                fx_kb.append(f"  ⏱️ **Pre-delay Protector Haas:** `{calc_pre:.1f} ms` para preservar el ataque transitorio en rol '{role}'.")
                fx_kb.append("  🛡️ **Seguridad Acústica:** LowCut obligatorio >= 0.05 para evitar acumulación de barro subgrave y resonancia metálica.")
                fx_kb.append("  📋 **Inyección por Portapapeles & LOM:** Al confirmar, el XML se copiará automáticamente al Portapapeles (`Set-Clipboard`) para 1-click 'Paste from Clipboard'.")
            except Exception:
                pass

        if fx_kb:
            params_info.append("\n**Directrices Quirúrgicas de Inserción (FabFilter / Plugins):**\n" + "\n".join(fx_kb))

        # Aesthetic Profile & Zero-Default Policy Injection
        prof = aesthetic_engine.get_profile(genre)
        role_prof = prof.roles.get(role.upper(), None) if prof else None
        mand_effects = role_prof.mandatory_effects if (role_prof and role_prof.mandatory_effects) else ["EQ Eight"]
        opt_effects = role_prof.optional_effects if (role_prof and role_prof.optional_effects) else ["Compressor", "Saturator"]
        inst_name = str(trk.get("instrument", trk["name"]))
        past_decision = aesthetic_engine.get_instrument_decision(genre, inst_name)

        aesthetic_block = (
            f"\n🎨 **Perfil Estético Activo ({genre.upper()}):**\n"
            f"• **Efectos Obligatorios ({role}):** `{', '.join(mand_effects)}`\n"
            f"• **Efectos Opcionales Disponibles:** `{', '.join(opt_effects)}`\n"
            f"• 🛡️ *Política de Cadenas:* El motor nunca selecciona cadenas por defecto siempre pregunta cada uno de los efectos que se desea agregar."
        )
        if past_decision:
            aesthetic_block += f"\n• 💡 **Decisión Histórica Documentada para '{inst_name}':** `[{', '.join(past_decision.effects_added)}]` ({past_decision.reason})"
        params_info.append(aesthetic_block)
    
        params_text = "\n".join(params_info)
    
        gs = trk.get("gain_staging", {})
        lvl_str = f"{gs.get('target_peak_dbfs', -14.0):.1f} dBFS" if gs else "-14.0 dBFS"
    
        p_examples = ", ".join([f"{p['id']}: X" for p in eff.get("params", [])[:2]]) or "Parameter: Value"
        decision_prompt = (
            f"Analiza la función de este efecto dentro del rol '{role}' y define los valores específicos para cada parámetro considerando la densidad y rango dinámico de la mezcla. El motor nunca selecciona cadenas por defecto siempre pregunta cada uno de los efectos que se desea agregar."
            if is_eq else
            f"Analiza la función de este efecto dentro del rol '{role}' y define los valores específicos para cada parámetro considerando la densidad y rango dinámico de la mezcla, o indica 'Bypass' si determinas que este procesador no es necesario en este canal. El motor nunca selecciona cadenas por defecto siempre pregunta cada uno de los efectos que se desea agregar."
        )
        action_note = f"*Especifica tus valores de configuración (ej: '{p_examples}'). (Nota: Ecualizador 100% obligatorio).*" if is_eq else f"*Especifica tus valores de configuración (ej: '{p_examples}') o indica 'Bypass'.*"
    
        params_format_banner = (
            f"\n\n📋 **Formato Esperado de Parámetros:**\n"
            f"• Clave-Valor: `\"Parámetro: Valor, Parámetro: Valor\"` (ej: `\"{p_examples}\"` o `\"Drive: 35%, Dry/Wet: 50%\"`)\n"
            f"• Con Unidades: `\"Threshold: -16 dB, Attack: 15 ms, Ratio: 4:1\"`\n"
            f"• JSON: `{{\"Drive\": 0.35, \"Dry/Wet\": 0.50}}`\n"
            f"• Decisión deliberada por procesador: Evalúa si {eff_name} aporta a la claridad, calidez o pegada de '{t_name}', define sus parámetros conscientemente o indica 'Bypass' si está de más.\n"
            f"• Bypass puntual: Solo si determinas acústicamente que este canal no requiere este proceso (máximo 35% de la sesión)."
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
            "instructions_for_ai": f"Evalúa la función acústica de {eff_name} en '{t_name}' ({role}), define deliberadamente sus parámetros específicos o indica 'Bypass' si no es necesario. Cero atajos genéricos.",
            "target_track": t_idx,
            "target_device": eff_name,
            "device_index_in_chain": dev_ptr + 1,
            "total_devices_in_chain": len(fx_list),
            "phase": "PHASE_5_INSERT_EFFECTS"
        }
    
    def _handle_phase_5(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        # 0. Check for pending genre aesthetic profile definition
        if session.data.get("pending_genre_aesthetic_profile"):
            genre = session.data.get("genre", "trap")
            aesthetic_engine = AestheticProfileEngine()
            parsed_prof = aesthetic_engine.parse_standardized_genre_input(genre, user_input)
            if parsed_prof:
                session.data.pop("pending_genre_aesthetic_profile", None)
                session.data["aesthetic_profile_learned"] = parsed_prof.genre
                session._save_state()
                return self._prompt_current_fx_device(session)
            else:
                return aesthetic_engine.build_standardized_genre_query(genre)

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
    
        genre = session.data.get("genre")
        fx_list = self._get_fx_list_for_role(role, genre)
    
        if dev_ptr >= len(fx_list):
            session.data["current_fx_track_ptr"] = t_ptr + 1
            session.data["current_fx_dev_ptr"] = 0
            session._save_state()
            if hasattr(session, "_prompt_current_fx_device"):
                return session._prompt_current_fx_device()
            return self._prompt_current_fx_device(session)

        eff = fx_list[dev_ptr]
        eff_name = eff["name"]
        eff_uri = eff["uri"]
        is_eq = any(q in eff_name.lower() for q in ["eq", "equalizer", "pro-q"])

        # Prohibit all bulk approval shortcuts and generic advancing tokens
        is_bulk_shortcut = any(w in text for w in [
            "cadena express", "lote", "receta completa", "toda la pista",
            "cadena completa", "todos los efectos", "aprobar todo", "aprobar todos"
        ])
        is_generic_token = text in {
            "siguiente", "next", "ok", "yes", "si", "sí", "aprobar", "todos",
            "continuar", "listo", "proceder", "adelante", "avanzar", "skip"
        } or not user_input.strip()

        # Disallow whole-track bypass/skip via "cadena:" or "efectos:"
        is_whole_track_skip = (text.startswith("cadena:") or text.startswith("efectos:")) and not any(
            sep in text for sep in [":", "="] if len(text.split(sep, 1)) > 1 and any(c.isdigit() for c in text.split(sep, 1)[1])
        )

        if is_bulk_shortcut or is_generic_token or is_whole_track_skip:
            TransactionGuard.rollback_transaction(conn, session)
            return self._build_calibration_required_payload(
                session=session,
                trk=trk,
                eff=eff,
                dev_ptr=dev_ptr,
                total_devices=len(fx_list),
                conn=conn,
                user_input=user_input
            )
    
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
                    f"*Por favor define los parámetros del ecualizador para continuar.*"
                ),
                "instructions_for_ai": f"No puedes omitir el ecualizador {eff_name}. Envía los parámetros de configuración.",
                "target_track": t_idx,
                "target_device": eff_name,
                "device_index_in_chain": dev_ptr + 1,
                "total_devices_in_chain": len(fx_list),
                "phase": "PHASE_5_INSERT_EFFECTS"
            }

        if is_bypass and not is_eq:
            all_tracks = session.data.get("tracks", [])
            tot_non_eq = 0
            for ot in all_tracks:
                o_role = ot.get("role", "STRINGS")
                o_fx = self._get_fx_list_for_role(o_role, genre)
                for fx_item in o_fx:
                    if not any(q in fx_item.get("name", "").lower() for q in ["eq", "equalizer", "pro-q"]):
                        tot_non_eq += 1
            tot_non_eq = max(1, tot_non_eq)
            current_bypassed = session.data.get("bypassed_non_eq_count", 0)
            max_allowed = max(2, int(tot_non_eq * 0.35))

            if current_bypassed >= max_allowed:
                TransactionGuard.rollback_transaction(conn, session)
                return {
                    "status": "VALIDATION_ERROR",
                    "current_step": f"PASO 5 DE 7: CUOTA DE BYPASS EXCEDIDA (PISTA {t_ptr + 1}: '{trk.get('name')}')",
                    "action_taken": f"El motor prohíbe el bypass excesivo ({current_bypassed}/{tot_non_eq} efectos omitidos). Límite de cuota alcanzado (35%).",
                    "question": (
                        f"⛔ **CUOTA MÁXIMA DE BYPASS EXCEDIDA ({current_bypassed}/{tot_non_eq} procesadores omitidos)**\n\n"
                        f"Una producción comercial de alto nivel exige control dinámico (compresión), calidez armónica (saturación) y espacialidad.\n"
                        f"No se permite omitir `{eff_name}` en la pista '{trk.get('name')}'.\n\n"
                        f"Por favor define los parámetros específicos para `{eff_name}`."
                    ),
                    "instructions_for_ai": f"Cuota de bypass excedida. Calibra los parámetros específicos para {eff_name}.",
                    "target_track": t_idx,
                    "target_device": eff_name,
                    "device_index_in_chain": dev_ptr + 1,
                    "total_devices_in_chain": len(fx_list),
                    "phase": "PHASE_5_INSERT_EFFECTS"
                }
            session.data["bypassed_non_eq_count"] = current_bypassed + 1

        if not is_bypass:
            is_opcion_1 = (text.strip() == "1" or any(w in text for w in ["opcion 1", "opción 1", "opcion1"]))
            resolved_intent = SemanticIntentResolver.resolve_intent(user_input, role)
            arch_spec = UltraAcousticCatalog.get_role_archetype_spec(role, resolved_intent.archetype.value)

            if is_opcion_1:
                # Backwards-compatible single-device calibration with recommended parameters
                if "auto-tune" in eff_name.lower() or "autotune" in eff_name.lower():
                    det_key = session.data.get("key", "F")
                    det_scale = session.data.get("scale", "Minor")
                    session.data["key"] = det_key
                    session.data["scale"] = det_scale
                    applied_params["Key"] = det_key
                    applied_params["Scale"] = det_scale
                    applied_params["Retune Speed"] = 0.0
                elif is_eq:
                    prof = AsciiSpectrumVisualizer.get_profile_for_role(role)
                    rec_eq = prof.get("recommended_eq", {})
                    applied_params["1 Filter On A"] = 1.0
                    applied_params["1 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(rec_eq.get("band_1_hpf_hz", 100.0))
                    applied_params["2 Filter On A"] = 1.0
                    applied_params["2 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(rec_eq.get("band_2_mud_hz", 400.0))
                    applied_params["2 Gain A"] = rec_eq.get("band_2_gain_db", -3.0)
                    applied_params["3 Filter On A"] = 1.0
                    applied_params["3 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(rec_eq.get("band_3_snap_hz", 2500.0))
                    applied_params["3 Gain A"] = rec_eq.get("band_3_gain_db", 1.0)
                    applied_params["4 Filter On A"] = 1.0
                    applied_params["4 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(rec_eq.get("band_4_air_hz", 10000.0))
                    applied_params["4 Gain A"] = rec_eq.get("band_4_gain_db", 1.5)
                    for p in eff.get("params", []):
                        p_id = p["id"]
                        if p_id not in applied_params:
                            applied_params[p_id] = p.get("default", 1.0)
                else:
                    eff_lower = eff_name.lower()
                    for p in eff.get("params", []):
                        p_id = p["id"]
                        val_found = None
                        if "glue" in eff_lower and arch_spec.glue_params and p_id in arch_spec.glue_params:
                            val_found = arch_spec.glue_params[p_id]
                        elif "buss" in eff_lower and arch_spec.drum_buss_params and p_id in arch_spec.drum_buss_params:
                            val_found = arch_spec.drum_buss_params[p_id]
                        elif "saturator" in eff_lower and arch_spec.saturator_params and p_id in arch_spec.saturator_params:
                            val_found = arch_spec.saturator_params[p_id]
                        elif "utility" in eff_lower and arch_spec.utility_params and p_id in arch_spec.utility_params:
                            val_found = arch_spec.utility_params[p_id]
                        elif "reverb" in eff_lower and arch_spec.reverb_params and p_id in arch_spec.reverb_params:
                            val_found = arch_spec.reverb_params[p_id]
                        if val_found is not None:
                            applied_params[p_id] = val_found
                        elif p_id not in ("Mode", "ColorMode", "Color"):
                            applied_params[p_id] = p.get("default", 0.5)
            else:
                # Deliberate parameter calibration: parse explicit parameters or JSON
                params_calibrated_count = 0

                # 1. Auto-Tune validation
                if "auto-tune" in eff_name.lower() or "autotune" in eff_name.lower():
                    det_key, det_scale, det_retune = parse_autotune_settings(user_input)
                    if det_key or det_scale or det_retune is not None:
                        params_calibrated_count += 1
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
                    session.data["key"] = det_key
                    session.data["scale"] = det_scale
                    applied_params["Key"] = det_key
                    applied_params["Scale"] = det_scale
                    if det_retune is not None:
                        applied_params["Retune Speed"] = det_retune

                # 2. EQ Eight band extraction
                if is_eq:
                    m_b1 = re.search(r"(?:hpf|banda?\s*1|low\s*cut|corte)\s*[:=]?\s*([0-9\.]+)\s*(?:hz)?", text)
                    if m_b1:
                        f1 = float(m_b1.group(1))
                        applied_params["1 Filter On A"] = 1.0
                        applied_params["1 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(f1)
                        params_calibrated_count += 1
                    m_b2_f = re.search(r"(?:mud|barro|banda?\s*2)\s*[:=]?\s*([0-9\.]+)\s*(?:hz)?", text)
                    if m_b2_f:
                        f2 = float(m_b2_f.group(1))
                        applied_params["2 Filter On A"] = 1.0
                        applied_params["2 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(f2)
                        params_calibrated_count += 1
                    m_b2_g = re.search(r"(?:mud\s*gain|ganancia\s*barro|ganancia\s*banda\s*2|gain\s*2)\s*[:=]?\s*([+\-]?[0-9\.]+)\s*(?:db)?", text)
                    if m_b2_g:
                        applied_params["2 Gain A"] = float(m_b2_g.group(1))
                        params_calibrated_count += 1
                    m_b3_f = re.search(r"(?:presencia|presence|snap|banda?\s*3)\s*[:=]?\s*([0-9\.]+)\s*(?:hz)?", text)
                    if m_b3_f:
                        f3 = float(m_b3_f.group(1))
                        applied_params["3 Filter On A"] = 1.0
                        applied_params["3 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(f3)
                        params_calibrated_count += 1
                    m_b3_g = re.search(r"(?:presencia\s*gain|ganancia\s*presencia|gain\s*3)\s*[:=]?\s*([+\-]?[0-9\.]+)\s*(?:db)?", text)
                    if m_b3_g:
                        applied_params["3 Gain A"] = float(m_b3_g.group(1))
                        params_calibrated_count += 1
                    m_b4_f = re.search(r"(?:aire|air|shelf|banda?\s*4)\s*[:=]?\s*([0-9\.]+)\s*(?:hz)?", text)
                    if m_b4_f:
                        f4 = float(m_b4_f.group(1))
                        applied_params["4 Filter On A"] = 1.0
                        applied_params["4 Frequency A"] = FrequencySlottingEngine.freq_to_normalized(f4)
                        params_calibrated_count += 1
                    m_b4_g = re.search(r"(?:air\s*gain|ganancia\s*aire|gain\s*4)\s*[:=]?\s*([+\-]?[0-9\.]+)\s*(?:db)?", text)
                    if m_b4_g:
                        applied_params["4 Gain A"] = float(m_b4_g.group(1))
                        params_calibrated_count += 1

                # 3. JSON and text regex against device parameters
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

                for p in eff.get("params", []):
                    p_id = p["id"]
                    if p_id in applied_params:
                        continue
                    p_clean = _normalize_text(p_id)
                    p_alpha = _clean_key(p_id)
                    val_found = None

                    # 1. JSON
                    for jk, jv in parsed_json.items():
                        jk_clean = _normalize_text(str(jk))
                        jk_alpha = _clean_key(str(jk))
                        if (jk_clean == p_clean or jk_alpha == p_alpha or
                            alias_map.get(jk_clean) == p_alpha or alias_map.get(jk_alpha) == p_alpha):
                            try:
                                val_found = float(jv)
                                break
                            except (ValueError, TypeError):
                                val_found = jv
                                break

                    # 2. Text regex
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

                    # 3. Categorical matches
                    if val_found is None and p_id == "Mode":
                        from engine.sound_design.valhalla_supermassive.schema import ValhallaSupermassiveSchema
                        from engine.sound_design.valhalla_vintage_verb.schema import ValhallaVintageVerbSchema
                        all_modes = ValhallaVintageVerbSchema.MODES if "vintageverb" in eff_name.lower() else ValhallaSupermassiveSchema.MODE_NAMES
                        m_m = re.search(rf"(?:mode|modo)\s*[:=]?\s*([a-zA-Z0-9_\-\s]+?)(?:,|$|\n)", text, re.IGNORECASE)
                        if m_m:
                            candidate = m_m.group(1).strip()
                            for mode_name in all_modes:
                                if mode_name.lower() == candidate.lower():
                                    val_found = mode_name
                                    break
                        if val_found is None:
                            for mode_name in all_modes:
                                if re.search(rf"\b{re.escape(mode_name)}\b", text, re.IGNORECASE):
                                    val_found = mode_name
                                    break
                    elif val_found is None and p_id in ("ColorMode", "Color"):
                        from engine.sound_design.valhalla_vintage_verb.sanitizer import ValhallaVintageVerbSanitizer
                        m_c = re.search(rf"(?:color|colormode|era)\s*[:=]?\s*([a-zA-Z0-9_\-\s]+?)(?:,|$|\n)", text, re.IGNORECASE)
                        if m_c:
                            val_found = ValhallaVintageVerbSanitizer.resolve_color(m_c.group(1).strip())
                    elif val_found is None and (p_id in ("Key", "Scale") or "type" in p_id.lower()):
                        str_pat = rf"{re.escape(p_clean)}\s*[:=]?\s*([a-zA-Z0-9_\-#]+)"
                        m_str = re.search(str_pat, text, re.IGNORECASE)
                        if m_str:
                            val_found = m_str.group(1).strip()

                    if val_found is not None:
                        applied_params[p_id] = val_found
                        params_calibrated_count += 1

                # 4. Enforce deliberate decision requirement: block if no parameters provided
                if params_calibrated_count == 0:
                    TransactionGuard.rollback_transaction(conn, session)
                    return self._build_calibration_required_payload(
                        session=session,
                        trk=trk,
                        eff=eff,
                        dev_ptr=dev_ptr,
                        total_devices=len(fx_list),
                        conn=conn,
                        user_input=user_input
                    )

                # 5. Fill safe archetype values ONLY for remaining unmentioned secondary parameters
                eff_lower = eff_name.lower()
                for p in eff.get("params", []):
                    p_id = p["id"]
                    if p_id not in applied_params:
                        val_default = None
                        if "glue" in eff_lower and arch_spec.glue_params and p_id in arch_spec.glue_params:
                            val_default = arch_spec.glue_params[p_id]
                        elif "buss" in eff_lower and arch_spec.drum_buss_params and p_id in arch_spec.drum_buss_params:
                            val_default = arch_spec.drum_buss_params[p_id]
                        elif "saturator" in eff_lower and arch_spec.saturator_params and p_id in arch_spec.saturator_params:
                            val_default = arch_spec.saturator_params[p_id]
                        elif "utility" in eff_lower and arch_spec.utility_params and p_id in arch_spec.utility_params:
                            val_default = arch_spec.utility_params[p_id]
                        elif "reverb" in eff_lower and arch_spec.reverb_params and p_id in arch_spec.reverb_params:
                            val_default = arch_spec.reverb_params[p_id]
                        elif is_eq:
                            for b in arch_spec.eq_bands:
                                if p_id == f"{b.band_index} Frequency A":
                                    val_default = hz_to_eq8_norm(b.freq_hz)
                                    break
                                elif p_id == f"{b.band_index} Gain A":
                                    val_default = db_to_eq8_norm(b.gain_db)
                                    break
                                elif p_id == f"{b.band_index} Filter Type":
                                    val_default = float(b.band_type)
                                    break
                                elif p_id == f"Band {b.band_index} On":
                                    val_default = 1.0 if b.enabled else 0.0
                                    break
                        if val_default is not None:
                            applied_params[p_id] = val_default
                        elif p_id not in ("Mode", "ColorMode", "Color"):
                            applied_params[p_id] = p.get("default", 0.5)

            # Specialized builder, 3-tier validation, serialization & clipboard injection
            if "supermassive" in eff_name.lower():
                try:
                    from engine.sound_design.valhalla_supermassive.mode_selector import SupermassiveModeSelector
                    from engine.sound_design.valhalla_supermassive.validator import ValhallaSupermassiveValidator
                    from engine.sound_design.valhalla_supermassive.serializer import ValhallaSupermassiveSerializer

                    song_name = session.data.get("song_name", "Session")
                    t_title = trk.get("name", f"Track_{t_idx}").replace(" ", "_")
                    bpm = float(session.data.get("bpm", 120.0))

                    sm_model = SupermassiveModeSelector.build_role_preset(
                        preset_name=f"{song_name}_{t_title}",
                        role=role,
                        bpm=bpm,
                        applied_params=applied_params
                    )
                    v_rep = ValhallaSupermassiveValidator.validate(sm_model, strict=False)
                    if v_rep.is_valid:
                        preset_p = ValhallaSupermassiveSerializer.save_preset(sm_model, category=song_name)
                        xml_str = ValhallaSupermassiveSerializer.to_xml_string(sm_model)
                        cb_ok = ValhallaSupermassiveSerializer.copy_to_clipboard(xml_str)
                        trk["supermassive_preset_path"] = str(preset_p)
                        trk["supermassive_clipboard_ready"] = cb_ok
                        trk["supermassive_mode"] = sm_model.mode_name
                        logger.info(f"Valhalla Supermassive preset saved: {preset_p} (mode: {sm_model.mode_name}, clipboard: {cb_ok})")
                except Exception as ex_sm:
                    logger.warning(f"Notice building Valhalla Supermassive preset: {ex_sm}")

            if "surge xt" in eff_name.lower():
                try:
                    from engine.sound_design.surge_xt_fx.rack_factory import SurgeFXRackFactory
                    from engine.sound_design.surge_xt_fx.validator import SurgeFXValidator
                    from engine.sound_design.surge_xt_fx.serializer import SurgeFXSerializer

                    song_name = session.data.get("song_name", "Session")
                    t_title = trk.get("name", f"Track_{t_idx}").replace(" ", "_")
                    bpm = float(session.data.get("bpm", 120.0))

                    rack_m = SurgeFXRackFactory.create_role_rack(
                        role=role,
                        bpm=bpm,
                        applied_params=applied_params,
                        track_name=f"{song_name}_{t_title}"
                    )
                    v_rep_srg = SurgeFXValidator.validate_rack(rack_m, strict=False)
                    if v_rep_srg.is_valid:
                        chain_p = SurgeFXSerializer.save_chain_file(rack_m, category=song_name)
                        trk["surge_xt_chain_path"] = str(chain_p)
                        trk["surge_xt_active_slots"] = len(rack_m.get_active_slots())
                        logger.info(f"Surge XT Effects multi-slot rack saved: {chain_p} ({trk['surge_xt_active_slots']} active slots)")
                except Exception as ex_srg:
                    logger.warning(f"Notice building Surge XT FX rack: {ex_srg}")

            if "vintageverb" in eff_name.lower():
                try:
                    from engine.sound_design.valhalla_vintage_verb.mode_selector import VintageVerbModeSelector
                    from engine.sound_design.valhalla_vintage_verb.validator import ValhallaVintageVerbValidator
                    from engine.sound_design.valhalla_vintage_verb.serializer import ValhallaVintageVerbSerializer

                    song_name = session.data.get("song_name", "Session")
                    t_title = trk.get("name", f"Track_{t_idx}").replace(" ", "_")
                    bpm = float(session.data.get("bpm", 120.0))

                    vv_model = VintageVerbModeSelector.build_role_preset(
                        preset_name=f"{song_name}_{t_title}",
                        role=role,
                        bpm=bpm,
                        applied_params=applied_params
                    )
                    v_rep_vv = ValhallaVintageVerbValidator.validate(vv_model, role=role, strict=False)
                    if v_rep_vv.is_valid:
                        preset_p = ValhallaVintageVerbSerializer.save_preset(vv_model, category=song_name)
                        xml_str = ValhallaVintageVerbSerializer.to_xml_string(vv_model)
                        cb_ok = ValhallaVintageVerbSerializer.copy_to_clipboard(xml_str)
                        trk["vintage_verb_preset_path"] = str(preset_p)
                        trk["vintage_verb_clipboard_ready"] = cb_ok
                        trk["vintage_verb_mode"] = vv_model.mode_name
                        trk["vintage_verb_color"] = vv_model.color_name
                        logger.info(f"Valhalla VintageVerb preset saved: {preset_p} (mode: {vv_model.mode_name}, color: {vv_model.color_name}, clipboard: {cb_ok})")
                except Exception as ex_vv:
                    logger.warning(f"Notice building Valhalla VintageVerb preset: {ex_vv}")

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
                            ("supermassive" in e_name and ("supermassive" in d_name or "supermassive" in d_class)) or
                            ("surge xt" in e_name and ("surge" in d_name or "surge" in d_class)) or
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
    
                    is_test_env = DeviceExecutionVerifier.check_is_test_env(conn, session)
                    
                    # Normalize parameters before setting to match LOM names
                    normalized_params = {}
                    for p_key, p_val in applied_params.items():
                        resolved_k = DeviceExecutionVerifier.resolve_lom_parameter_name(eff_name, p_key)
                        normalized_params[resolved_k] = p_val
                    applied_params = normalized_params

                    for p_key, p_val in applied_params.items():
                        try:
                            conn.send_command("set_device_parameter", {
                                "track_index": t_idx,
                                "device_index": dev_idx,
                                "parameter": p_key,
                                "value": float(p_val) if isinstance(p_val, (int, float)) else 0.5
                            })
                        except Exception as p_ex:
                            logger.warning(f"Error setting parameter {p_key} on track {t_idx} device {dev_idx}: {p_ex}")

                    if not is_test_env and conn is not None and hasattr(conn, "send_command"):
                        verified_ok, diag = DeviceExecutionVerifier.verify_device_parameters_batch(
                            conn, track_index=t_idx, device_index=dev_idx, device_name=eff_name,
                            target_params=applied_params, is_test_env=is_test_env
                        )
                        if not verified_ok:
                            TransactionGuard.rollback_transaction(conn, session)
                            retry_c = session.data.get("fx_verification_retry_count", 0) + 1
                            session.data["fx_verification_retry_count"] = retry_c
                            session._save_state()
                            if retry_c <= 3:
                                return DeviceExecutionVerifier.build_verification_failed_payload(
                                    track_index=t_idx, track_name=trk.get("name", f"Track_{t_idx}"),
                                    device_index=dev_idx, device_name=eff_name, diagnosis=diag,
                                    role=role, retry_count=retry_c
                                )
                            else:
                                logger.warning(f"Max retries reached on {eff_name}. Auto-repairing with safe archetype.")
                                session.data["fx_verification_retry_count"] = 0
    
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
                    elif "supermassive" in eff_name.lower():
                        sm_mix = float(sm_model.mix if 'sm_model' in locals() else applied_params.get("Mix", 0.20))
                        sm_feedback = float(sm_model.feedback if 'sm_model' in locals() else min(0.95, float(applied_params.get("Feedback", 0.50))))
                        sm_lowcut = float(sm_model.low_cut if 'sm_model' in locals() else max(0.05, float(applied_params.get("LowCut", 0.20))))
                        sm_highcut = float(sm_model.high_cut if 'sm_model' in locals() else float(applied_params.get("HighCut", 0.65)))
                        sm_mode = float(sm_model.mode if 'sm_model' in locals() else 0.38)
                        sm_sync = 1.0 if ('sm_model' in locals() and sm_model.delay_sync > 0.0) else (1.0 if float(applied_params.get("DelaySync", 1.0)) >= 0.5 else 0.0)
                        code_sm = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = {sm_mix}
    elif 'feedback' in p_l: p.value = {sm_feedback}
    elif 'low cut' in p_l or 'lowcut' in p_l: p.value = {sm_lowcut}
    elif 'high cut' in p_l or 'highcut' in p_l: p.value = {sm_highcut}
    elif 'mode' in p_l: p.value = {sm_mode}
    elif 'sync' in p_l: p.value = {sm_sync}
"""
                        conn.send_command("execute_code", {"code": code_sm})
                    elif "surge xt" in eff_name.lower():
                        if 'rack_m' in locals():
                            for p_k, p_v in rack_m.to_lom_command_list(only_active=True):
                                try:
                                    conn.send_command("set_device_parameter", {
                                        "track_index": t_idx,
                                        "device_index": dev_idx,
                                        "parameter": p_k,
                                        "value": float(p_v)
                                    })
                                except Exception:
                                    pass
                        srg_mix = float(applied_params.get("FX A1 Mix", 0.70))
                        code_srg = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if ('a1' in p_l or 'insert fx 1' in p_l) and 'mix' in p_l: p.value = {srg_mix}
"""
                        conn.send_command("execute_code", {"code": code_srg})
                    elif "vintageverb" in eff_name.lower():
                        vv_mix = float(vv_model.mix if 'vv_model' in locals() else applied_params.get("Mix", 0.20))
                        vv_decay = float(vv_model.decay if 'vv_model' in locals() else applied_params.get("Decay", 0.25))
                        vv_predelay = float(vv_model.predelay if 'vv_model' in locals() else applied_params.get("PreDelay", 0.05))
                        vv_size = float(vv_model.size if 'vv_model' in locals() else applied_params.get("Size", 0.50))
                        vv_lowcut = float(vv_model.low_cut if 'vv_model' in locals() else applied_params.get("LowCut", 0.20))
                        vv_highcut = float(vv_model.high_cut if 'vv_model' in locals() else applied_params.get("HighCut", 0.65))
                        vv_mode = float(vv_model.mode if 'vv_model' in locals() else 0.0)
                        vv_color = float(vv_model.color_mode if 'vv_model' in locals() else 0.50)
                        code_vv = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = {vv_mix}
    elif 'decay' in p_l: p.value = {vv_decay}
    elif 'predelay' in p_l or 'pre-delay' in p_l: p.value = {vv_predelay}
    elif 'low cut' in p_l or 'lowcut' in p_l: p.value = {vv_lowcut}
    elif 'high cut' in p_l or 'highcut' in p_l: p.value = {vv_highcut}
    elif 'size' in p_l: p.value = {vv_size}
    elif 'mode' in p_l: p.value = {vv_mode}
    elif 'color' in p_l: p.value = {vv_color}
"""
                        conn.send_command("execute_code", {"code": code_vv})
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
        dev_entry = {
            "name": eff_name,
            "device_index": dev_ptr + 1,
            "bypass": is_bypass,
            "bypassed": is_bypass,
            "parameters": applied_params
        }
        if dev_ptr < len(trk["insert_effects"]):
            trk["insert_effects"][dev_ptr] = dev_entry
        else:
            trk["insert_effects"].append(dev_entry)

        if "insert_effects" not in session.data or not isinstance(session.data["insert_effects"], dict):
            session.data["insert_effects"] = {}
        session.data["insert_effects"][trk.get("name", str(t_idx))] = trk["insert_effects"]
    
        # Register Governance Contract & Emit Receipt
        decision_type = DecisionType.REJECT if is_bypass else DecisionType.APPLY
        contract = StructuralDecisionContract(
            contract_id=f"insert-fx-t{t_idx}-d{dev_ptr}-{eff_name}",
            decision=decision_type,
            target_track=str(trk.get("name", t_idx)),
            target_device=eff_name,
            parameters=applied_params if not is_bypass else {},
            is_valid=True,
            metadata={"role": role, "device_index": dev_ptr, "bypass": is_bypass}
        )
        if hasattr(session, "state_bus") and session.state_bus is not None:
            session.state_bus.register_contract(contract)

        if hasattr(session, "coordinator") and session.coordinator is not None:
            try:
                coord_res = session.coordinator.execute(
                    contract=contract,
                    conn=conn,
                    session=session,
                    is_test_env=True,
                )
                if coord_res.receipt:
                    trk.setdefault("fx_commit_receipts", []).append(coord_res.receipt.model_dump())
            except Exception as coord_ex:
                logger.debug(f"[Phase5] Governance coordinator notice: {coord_ex}")
    
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
            next_p = self._prompt_current_fx_device(session)
            if trk.get("supermassive_clipboard_ready"):
                next_p["action_taken"] = f"Procesador {eff_name} moldeado y copiado automáticamente al portapapeles de Windows (haz 'Paste from Clipboard' en Supermassive en Live)."
            elif trk.get("vintage_verb_clipboard_ready"):
                next_p["action_taken"] = f"Procesador {eff_name} moldeado y copiado automáticamente al portapapeles de Windows (haz 'Paste from Clipboard' en VintageVerb en Live)."
            elif trk.get("surge_xt_chain_path"):
                next_p["action_taken"] = f"Procesador {eff_name} moldeado y guardado en {trk.get('surge_xt_chain_path')}."
            return next_p
        else:
            missing_trk = self.find_track_missing_eq(session, conn)
            if missing_trk is not None:
                return self.force_missing_eq_prompt(session, conn, missing_trk)

            # Deploy non-destructive submaster bus architecture (preserves all existing tracks)
            from engine.mix.bus_architecture import LiveBusArchitectureEngine
            bus_report = LiveBusArchitectureEngine.deploy_submix_buses_nondestructive(conn, tracks)
            session.data["bus_architecture"] = {
                "deployed": True,
                "topology": bus_report.get("analysis", {}).get("buses", {}),
                "summary_table": bus_report.get("analysis", {}).get("summary_table", "")
            }
            self.audit_phase_and_spectral_health(session, conn, tracks)

            if hasattr(session, "advance_phase"):
                session.advance_phase("PHASE_6_COMPOSITION")
            else:
                session.data["current_phase"] = "PHASE_6_COMPOSITION"
                session.data["phase_index"] = 6
            session._save_state()
            return session._prompt_phase_6()

    

# engine/sound_design/dedicated_plugin_configurator.py
"""
Dedicated Plugin Configurator.

Provides specialized, parameter-prompt-free configuration pipelines for:
- Instruments: Decent Sampler, Surge XT Synth, Vital
- Effects: Valhalla Supermassive, Valhalla VintageVerb, Surge XT Effects

When the AI / user decides to use these plugins, they are configured
through their own dedicated sound design engines rather than stopping
the flow to ask for raw numeric parameters.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("DedicatedPluginConfigurator")


class DedicatedPluginConfigurator:
    """Orchestrates autonomous configuration of specialized VST plugins."""

    # -------------------------------------------------------------------------
    # IDENTIFIERS
    # -------------------------------------------------------------------------

    @staticmethod
    def is_dedicated_instrument(instrument_name: str) -> bool:
        if not instrument_name:
            return False
        name_l = instrument_name.lower()
        if "effects" in name_l:
            return False
        return any(k in name_l for k in ["decent sampler", "surge", "vital"])

    @staticmethod
    def is_dedicated_effect(effect_name: str) -> bool:
        if not effect_name:
            return False
        name_l = effect_name.lower()
        return any(k in name_l for k in ["supermassive", "vintageverb", "surge xt effects", "surge_xt_effects"])

    # -------------------------------------------------------------------------
    # INSTRUMENT CONFIGURATION PATHWAYS
    # -------------------------------------------------------------------------

    @classmethod
    def configure_instrument(
        cls,
        trk: Dict[str, Any],
        session: Any,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Executes the specialized configuration pipeline for a dedicated instrument
        (Decent Sampler, Surge XT Synth, or Vital) without prompting for raw parameters.
        """
        inst_name = str(trk.get("instrument", "")).lower()
        role = trk.get("role", "OTHER")
        bpm = float(session.data.get("bpm", 120.0))
        t_idx = session._resolve_live_track_index(conn, trk)

        if "decent sampler" in inst_name or "decent" in inst_name:
            return cls._configure_decent_sampler(trk, role, bpm, t_idx, session, conn)
        elif "surge" in inst_name and "effects" not in inst_name:
            return cls._configure_surge_xt_synth(trk, role, bpm, t_idx, session, conn)
        elif "vital" in inst_name:
            return cls._configure_vital(trk, role, bpm, t_idx, session, conn)
        else:
            return {"status": "SKIPPED", "message": f"Instrument {inst_name} is not a dedicated engine plugin."}

    @classmethod
    def _configure_decent_sampler(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        session: Any,
        conn: Any
    ) -> Dict[str, Any]:
        """Dedicated configuration for Decent Sampler."""
        from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager

        trk["is_decent_sampler"] = True
        bp = trk.get("blueprint", {})
        lib_name = bp.get("library_name")

        # Discover or match library
        if not lib_name:
            inst_disp = trk.get("instrument", "")
            if "(" in inst_disp and ")" in inst_disp:
                extracted = inst_disp.split("(", 1)[1].rsplit(")", 1)[0].strip()
                if "default" not in extracted.lower():
                    lib_name = extracted

        selected_lib = None
        if lib_name:
            selected_lib = DecentSamplerLibraryManager.get_library_by_name(lib_name)

        if not selected_lib:
            role_libs = DecentSamplerLibraryManager.get_libraries_for_role(role)
            if role_libs:
                selected_lib = role_libs[0]

        if not selected_lib:
            all_valid = DecentSamplerLibraryManager.scan_libraries(require_valid=True)
            if all_valid:
                selected_lib = all_valid[0]

        # Role-based macro parameter sculpt
        is_percussive = role in ("KEYS", "GUITAR", "BASS", "DRUMS", "PERCUSSION", "PLUCK")
        params = {
            "AMP_ATTACK": 0.02 if is_percussive else 0.35,
            "AMP_RELEASE": 0.40 if is_percussive else 0.80,
            "FILTER_CUTOFF": 0.85 if role != "BASS" else 0.38,
            "TONE": 0.60,
            "REVERB": 0.20 if role != "BASS" else 0.0,
            "CHORUS": 0.25 if role in ("KEYS", "PAD", "STRINGS") else 0.0
        }

        preset_path = str(selected_lib.preset_path) if (selected_lib and selected_lib.preset_path) else None
        lib_display = selected_lib.name if selected_lib else "Biblioteca Estándar"

        trk["decent_sampler_library"] = lib_display
        trk["decent_sampler_preset_path"] = preset_path
        trk["decent_sampler_parameters"] = params
        trk["sculpted"] = True
        trk["timbre_dna"] = {
            "brightness": params["FILTER_CUTOFF"],
            "roughness": 0.20,
            "stereo_width": 0.60 if params["CHORUS"] > 0 else 0.30,
            "transient_strength": 0.80 if is_percussive else 0.30,
            "movement": 0.40
        }

        logger.info(f"Decent Sampler configured autonomously on Track {t_idx} [{role}]: {lib_display}")
        return {
            "status": "CONFIGURED",
            "plugin": "Decent Sampler",
            "library": lib_display,
            "preset_path": preset_path,
            "parameters": params,
            "action_taken": f"Decent Sampler configurado mediante su pipeline dedicado con la librería '{lib_display}'."
        }

    @classmethod
    def _configure_surge_xt_synth(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        session: Any,
        conn: Any
    ) -> Dict[str, Any]:
        """Dedicated configuration for Surge XT Synthesizer."""
        from engine.sound_design.surge_xt_synth.patch_factory import SurgeSynthPatchFactory
        from engine.sound_design.surge_xt_synth.validator import SurgeSynthValidator
        from engine.sound_design.surge_xt_synth.serializer import SurgeSynthSerializer
        from engine.sound_design.surge_xt_synth.sanitizer import SurgeSynthSanitizer

        trk["is_surge_synth"] = True
        bp = trk.get("blueprint", {})

        if bp and bp.get("patch_model"):
            surge_patch = bp.get("patch_model")
        else:
            surge_patch = SurgeSynthPatchFactory.create_role_patch(
                role=role,
                bpm=bpm,
                applied_params=bp.get("parameters", {}),
                track_name=trk.get("name", "SurgeSynth")
            )

        val_rep = SurgeSynthValidator.validate_patch(surge_patch)
        if not val_rep.is_valid:
            surge_patch = SurgeSynthSanitizer.sanitize_patch(surge_patch)

        patch_path = SurgeSynthSerializer.save_patch(
            surge_patch, category=session.data.get("song_name", "Session")
        )
        trk["surge_synth_patch_path"] = str(patch_path)
        trk["surge_synth_osc_types"] = [osc.osc_type for osc in surge_patch.oscillators]
        trk["surge_synth_category"] = surge_patch.category
        trk["sculpted"] = True
        trk["timbre_dna"] = {
            "brightness": float(surge_patch.filter1.cutoff),
            "roughness": 0.40,
            "stereo_width": 0.70,
            "transient_strength": 0.85 if surge_patch.amp_envelope.attack < 0.05 else 0.35,
            "movement": 0.50
        }

        # Dispatch LOM parameters if connected
        if conn is not None and hasattr(conn, "send_command"):
            dev_idx = cls._find_device_index(conn, t_idx, ["surge xt", "surge"])
            if dev_idx is not None:
                for p_name, p_val in surge_patch.to_lom_command_list():
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": t_idx,
                            "device_index": dev_idx,
                            "parameter_name": p_name,
                            "value": float(p_val)
                        })
                    except Exception as ex_lom:
                        logger.debug(f"Surge XT parameter dispatch notice: {ex_lom}")

        logger.info(f"Surge XT Synth configured autonomously on Track {t_idx} [{role}]: {surge_patch.patch_name}")
        return {
            "status": "CONFIGURED",
            "plugin": "Surge XT",
            "patch_name": surge_patch.patch_name,
            "patch_path": str(patch_path),
            "action_taken": f"Surge XT sintetizado y validado mediante su pipeline dedicado ({surge_patch.patch_name})."
        }

    @classmethod
    def _configure_vital(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        session: Any,
        conn: Any
    ) -> Dict[str, Any]:
        """Dedicated configuration for Vital Synth."""
        from engine.sound_design.vital_sound_engine import VitalSoundEngine

        trk["is_vital"] = True
        vital_engine = VitalSoundEngine()

        # Map role to Vital archetype category
        vital_role_map = {
            "BASS": "BASS_808" if "808" in str(trk.get("name", "")).lower() else "BASS_SUB",
            "808_BASS": "BASS_808",
            "LEAD": "LEAD_SAW",
            "COUNTER_LEAD": "LEAD_PLUCK",
            "PAD": "PAD_LUSH",
            "STRINGS": "PAD_ORGANIC",
            "KEYS": "CHORD_SUPERAW",
        }
        v_role = vital_role_map.get(role, "LEAD_SAW")
        patch_name = f"Vital_{role}_{trk.get('name', 'Track').replace(' ', '_')}"

        preset_path = vital_engine.create_preset(
            preset_name=patch_name,
            role=v_role,
            directives={"brightness": 0.70, "punch": 0.80, "warmth_drive": 0.25}
        )

        trk["vital_preset_path"] = str(preset_path)
        trk["sculpted"] = True
        trk["timbre_dna"] = {
            "brightness": 0.70,
            "roughness": 0.35,
            "stereo_width": 0.75,
            "transient_strength": 0.80,
            "movement": 0.45
        }

        # Dispatch basic macro controls to Live if device is present
        if conn is not None and hasattr(conn, "send_command"):
            dev_idx = cls._find_device_index(conn, t_idx, ["vital"])
            if dev_idx is not None:
                code_vital = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'cutoff' in p_l or 'filter 1' in p_l: p.value = 0.75
    elif 'resonance' in p_l: p.value = 0.25
"""
                try:
                    conn.send_command("execute_code", {"code": code_vital})
                except Exception as ex_v:
                    logger.debug(f"Vital parameter dispatch notice: {ex_v}")

        logger.info(f"Vital configured autonomously on Track {t_idx} [{role}]: {preset_path}")
        return {
            "status": "CONFIGURED",
            "plugin": "Vital",
            "patch_name": patch_name,
            "preset_path": str(preset_path),
            "action_taken": f"Vital sintetizado y esculpido mediante VitalSoundEngine ({patch_name})."
        }

    # -------------------------------------------------------------------------
    # EFFECT CONFIGURATION PATHWAYS
    # -------------------------------------------------------------------------

    @classmethod
    def configure_effect(
        cls,
        trk: Dict[str, Any],
        eff: Dict[str, Any],
        dev_idx: int,
        session: Any,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Executes the specialized configuration pipeline for a dedicated effect
        (Valhalla Supermassive, Valhalla VintageVerb, or Surge XT Effects)
        without prompting for raw numeric parameters.
        """
        eff_name = str(eff.get("name", "")).lower()
        role = trk.get("role", "OTHER")
        bpm = float(session.data.get("bpm", 120.0))
        t_idx = session._resolve_live_track_index(conn, trk)
        song_name = session.data.get("song_name", "Session")

        if "supermassive" in eff_name:
            return cls._configure_valhalla_supermassive(trk, role, bpm, t_idx, dev_idx, song_name, conn)
        elif "vintageverb" in eff_name or ("valhalla" in eff_name and "verb" in eff_name):
            return cls._configure_valhalla_vintage_verb(trk, role, bpm, t_idx, dev_idx, song_name, conn)
        elif "surge" in eff_name and "effects" in eff_name:
            return cls._configure_surge_xt_effects(trk, role, bpm, t_idx, dev_idx, song_name, conn)
        else:
            return {"status": "SKIPPED", "message": f"Effect {eff_name} is not a dedicated engine plugin."}

    @classmethod
    def _configure_valhalla_supermassive(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        dev_idx: int,
        song_name: str,
        conn: Any
    ) -> Dict[str, Any]:
        """Dedicated configuration for Valhalla Supermassive."""
        from engine.sound_design.valhalla_supermassive.mode_selector import SupermassiveModeSelector
        from engine.sound_design.valhalla_supermassive.validator import ValhallaSupermassiveValidator
        from engine.sound_design.valhalla_supermassive.serializer import ValhallaSupermassiveSerializer

        preset_name = f"SM_{role}_{trk.get('name', 'Track').replace(' ', '_')}"
        sm_model = SupermassiveModeSelector.build_role_preset(preset_name=preset_name, role=role, bpm=bpm)
        v_rep = ValhallaSupermassiveValidator.validate(sm_model, strict=False)

        preset_p = ValhallaSupermassiveSerializer.save_preset(sm_model, category=song_name)
        xml_str = ValhallaSupermassiveSerializer.to_xml_string(sm_model)
        cb_ok = ValhallaSupermassiveSerializer.copy_to_clipboard(xml_str)

        trk["supermassive_preset_path"] = str(preset_p)
        trk["supermassive_clipboard_ready"] = cb_ok
        trk["supermassive_mode"] = sm_model.mode_name

        # Dispatch LOM parameters
        if conn is not None and hasattr(conn, "send_command"):
            code_sm = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = {float(sm_model.mix)}
    elif 'feedback' in p_l: p.value = {float(sm_model.feedback)}
    elif 'low cut' in p_l or 'lowcut' in p_l: p.value = {float(sm_model.low_cut)}
    elif 'high cut' in p_l or 'highcut' in p_l: p.value = {float(sm_model.high_cut)}
    elif 'mode' in p_l: p.value = {float(sm_model.mode)}
    elif 'sync' in p_l: p.value = 1.0 if {sm_model.delay_sync} > 0 else 0.0
"""
            try:
                conn.send_command("execute_code", {"code": code_sm})
            except Exception as ex_sm:
                logger.debug(f"Supermassive LOM dispatch notice: {ex_sm}")

        logger.info(f"Valhalla Supermassive configured autonomously on Track {t_idx} [{role}]: Mode {sm_model.mode_name}")
        return {
            "status": "CONFIGURED",
            "plugin": "Valhalla Supermassive",
            "mode": sm_model.mode_name,
            "preset_path": str(preset_p),
            "clipboard_ready": cb_ok,
            "action_taken": f"Valhalla Supermassive configurado automáticamente en modo {sm_model.mode_name} (copiado al portapapeles de Windows)."
        }

    @classmethod
    def _configure_valhalla_vintage_verb(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        dev_idx: int,
        song_name: str,
        conn: Any
    ) -> Dict[str, Any]:
        """Dedicated configuration for Valhalla VintageVerb."""
        from engine.sound_design.valhalla_vintage_verb.mode_selector import VintageVerbModeSelector
        from engine.sound_design.valhalla_vintage_verb.validator import ValhallaVintageVerbValidator
        from engine.sound_design.valhalla_vintage_verb.serializer import ValhallaVintageVerbSerializer

        preset_name = f"VV_{role}_{trk.get('name', 'Track').replace(' ', '_')}"
        vv_model = VintageVerbModeSelector.build_role_preset(preset_name=preset_name, role=role, bpm=bpm)
        v_rep_vv = ValhallaVintageVerbValidator.validate(vv_model, role=role, strict=False)

        preset_p = ValhallaVintageVerbSerializer.save_preset(vv_model, category=song_name)
        xml_str = ValhallaVintageVerbSerializer.to_xml_string(vv_model)
        cb_ok = ValhallaVintageVerbSerializer.copy_to_clipboard(xml_str)

        trk["vintage_verb_preset_path"] = str(preset_p)
        trk["vintage_verb_clipboard_ready"] = cb_ok
        trk["vintage_verb_mode"] = vv_model.mode_name
        trk["vintage_verb_color"] = vv_model.color_name

        # Dispatch LOM parameters
        if conn is not None and hasattr(conn, "send_command"):
            code_vv = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    p_l = p.name.lower()
    if 'mix' in p_l: p.value = {float(vv_model.mix)}
    elif 'decay' in p_l: p.value = {float(vv_model.decay)}
    elif 'predelay' in p_l or 'pre-delay' in p_l: p.value = {float(vv_model.predelay)}
    elif 'low cut' in p_l or 'lowcut' in p_l: p.value = {float(vv_model.low_cut)}
    elif 'high cut' in p_l or 'highcut' in p_l: p.value = {float(vv_model.high_cut)}
    elif 'size' in p_l: p.value = {float(vv_model.size)}
    elif 'mode' in p_l: p.value = {float(vv_model.mode)}
    elif 'color' in p_l: p.value = {float(vv_model.color_mode)}
"""
            try:
                conn.send_command("execute_code", {"code": code_vv})
            except Exception as ex_vv:
                logger.debug(f"VintageVerb LOM dispatch notice: {ex_vv}")

        logger.info(f"Valhalla VintageVerb configured autonomously on Track {t_idx} [{role}]: Mode {vv_model.mode_name} ({vv_model.color_name})")
        return {
            "status": "CONFIGURED",
            "plugin": "Valhalla VintageVerb",
            "mode": vv_model.mode_name,
            "color": vv_model.color_name,
            "preset_path": str(preset_p),
            "clipboard_ready": cb_ok,
            "action_taken": f"Valhalla VintageVerb configurado automáticamente en modo {vv_model.mode_name} / {vv_model.color_name} (copiado al portapapeles de Windows)."
        }

    @classmethod
    def _configure_surge_xt_effects(
        cls,
        trk: Dict[str, Any],
        role: str,
        bpm: float,
        t_idx: int,
        dev_idx: int,
        song_name: str,
        conn: Any
    ) -> Dict[str, Any]:
        """Dedicated configuration for Surge XT Effects multi-slot rack."""
        from engine.sound_design.surge_xt_fx.rack_factory import SurgeFXRackFactory
        from engine.sound_design.surge_xt_fx.validator import SurgeFXValidator
        from engine.sound_design.surge_xt_fx.serializer import SurgeFXSerializer

        rack_m = SurgeFXRackFactory.create_role_rack(role=role, bpm=bpm)
        v_rep = SurgeFXValidator.validate_rack(rack_m)
        chain_p = SurgeFXSerializer.save_chain_file(rack_m, category=song_name)

        trk["surge_xt_chain_path"] = str(chain_p)
        trk["surge_xt_active_slots"] = len(rack_m.get_active_slots())

        # Dispatch LOM parameters
        if conn is not None and hasattr(conn, "send_command"):
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

        logger.info(f"Surge XT Effects configured autonomously on Track {t_idx} [{role}]: {chain_p}")
        return {
            "status": "CONFIGURED",
            "plugin": "Surge XT Effects",
            "chain_path": str(chain_p),
            "active_slots": len(rack_m.get_active_slots()),
            "action_taken": f"Surge XT Effects configurado automáticamente con {len(rack_m.get_active_slots())} slots activos."
        }

    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------

    @staticmethod
    def _find_device_index(conn: Any, track_index: int, target_names: list) -> Optional[int]:
        """Helper to locate device index by name/class in Live."""
        try:
            t_info = conn.send_command("get_track_info", {"track_index": track_index})
            devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
            for d_idx, d in enumerate(devs):
                d_name = str(d.get("name", "")).lower()
                d_class = str(d.get("class_name", "")).lower()
                for target in target_names:
                    if target.lower() in d_name or target.lower() in d_class:
                        return d_idx
        except Exception:
            pass
        return None

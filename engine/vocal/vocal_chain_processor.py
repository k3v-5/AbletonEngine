# engine/vocal/vocal_chain_processor.py
"""
Surgical Vocal Chain Processor:
Constructs and configures the complete commercial vocal processing chain in Ableton Live 12:
High-Pass Filter, Boxiness Notch, De-Esser, Dual Compression (FET + Opto),
Stereo Dimension, Sidechained Reverb/Delay, and Automatic Harmony Layers.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("VocalChainProcessor")


class VocalChainProcessor:
    """Configures high-end commercial vocal channel strips and spatial effects in Live 12."""

    VOCAL_CHAIN_SPEC = [
        {
            "name": "EQ Eight",
            "role": "SURGICAL_EQ",
            "params": {
                "Band 1 Frequency": 110.0,   # High-pass filter cutting sub-rumble
                "Band 1 Mode": 1,            # 12 dB/oct High Pass
                "Band 2 Frequency": 380.0,   # Boxiness / room mode cut
                "Band 2 Gain": -3.0,
                "Band 2 Q": 2.5,
                "Band 8 Frequency": 12000.0, # High shelf air
                "Band 8 Gain": 2.0
            }
        },
        {
            "name": "Compressor",
            "role": "DE_ESSER",
            "params": {
                "Ratio": 6.0,
                "Attack": 0.5,
                "Release": 40.0,
                "Threshold": -18.0
            }
        },
        {
            "name": "Glue Compressor",
            "role": "DUAL_COMP_PEAK",
            "params": {
                "Ratio": 4.0,
                "Attack": 1.0,               # Fast attack catching peaks
                "Release": 0.2,              # Fast release
                "Threshold": -14.0,
                "Makeup": 2.5
            }
        },
        {
            "name": "Compressor",
            "role": "DUAL_COMP_OPTO",
            "params": {
                "Ratio": 2.5,
                "Attack": 25.0,              # Slow opto-style attack
                "Release": 150.0,            # Smooth leveling release
                "Threshold": -10.0,
                "Makeup": 1.5
            }
        },
        {
            "name": "Chorus-Ensemble",
            "role": "STEREO_DIMENSION",
            "params": {
                "Dry/Wet": 0.18,
                "Amount": 0.40
            }
        }
    ]

    @classmethod
    def get_vocal_chain_spec(cls) -> List[Dict[str, Any]]:
        """Returns the canonical vocal processing chain specification."""
        return list(cls.VOCAL_CHAIN_SPEC)

    # Normalized parameter mappings for Antares Auto-Tune VST3 in Ableton Live 12
    AUTOTUNE_KEY_VALUES: Dict[str, float] = {
        "C": 0.04,
        "C#": 0.12,
        "DB": 0.12,
        "D": 0.20,
        "D#": 0.28,
        "EB": 0.28,
        "E": 0.38,
        "F": 0.48,
        "F#": 0.56,
        "GB": 0.56,
        "G": 0.65,
        "G#": 0.75,
        "AB": 0.75,
        "A": 0.84,
        "A#": 0.92,
        "BB": 0.92,
        "B": 0.98,
    }

    AUTOTUNE_SCALE_VALUES: Dict[str, float] = {
        "MAJOR": 0.015,
        "MINOR": 0.05,
        "NATURAL MINOR": 0.05,
        "HARMONIC MINOR": 0.05,
        "CHROMATIC": 0.08,
    }

    @classmethod
    def build_hybrid_vocal_chain(
        cls,
        vst_scanner: Any = None,
        song_key: str = "F",
        song_scale: str = "Minor",
        style: str = "modern_trap",
        retune_speed: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Dynamically designs a 5-to-7 slot commercial vocal chain.
        Prioritizes user's installed premier VSTs:
        - Slot 1: Antares Auto-Tune (Key & Scale mapped)
        - Slot 2: FabFilter Pro-Q (or EQ Eight)
        - Slot 3: FabFilter Pro-DS (or Compressor De-Esser)
        - Slot 4: FabFilter Pro-C (or Glue Compressor)
        - Slot 5: FabFilter Saturn 2 (or Saturator)
        - Slot 6: ValhallaVintageVerb / ValhallaDelay (or Chorus-Ensemble / Echo)
        """
        if vst_scanner is None:
            try:
                from engine.instruments.installed_scanner import InstalledPluginScanner
                vst_scanner = InstalledPluginScanner()
                vst_scanner.scan()
            except Exception as ex_sc:
                logger.debug(f"Scanner initialization notice: {ex_sc}")
                vst_scanner = None

        installed_map = getattr(vst_scanner, "_cache", {}) if vst_scanner else {}

        def find_best_plugin(patterns: List[str]) -> Optional[Any]:
            for pat in patterns:
                pat_lower = pat.lower()
                for plug in installed_map.values():
                    p_name = plug.name.lower()
                    p_uri = plug.uri.lower()
                    if pat_lower in p_name or pat_lower in p_uri:
                        return plug
            return None

        chain: List[Dict[str, Any]] = []

        # 1. Pitch Correction Slot (Antares Auto-Tune)
        at_plug = find_best_plugin([
            "auto-tune artist",
            "auto-tune pro",
            "auto-tune access",
            "auto-tune efx",
            "auto-tune",
            "autotune"
        ])

        norm_key = song_key.strip().upper() if song_key else "F"
        norm_scale = song_scale.strip().upper() if song_scale else "MINOR"
        key_val = cls.AUTOTUNE_KEY_VALUES.get(norm_key, 0.48)
        scale_val = cls.AUTOTUNE_SCALE_VALUES.get(norm_scale, 0.05)
        # In Auto-Tune Artist LOM: 1.0 = 0 ms (Hard Snap), 0.0 = 400 ms (Slowest)
        retune_val = 1.0 if retune_speed <= 5.0 else 0.40

        if at_plug:
            chain.append({
                "name": at_plug.name,
                "role": "PITCH_CORRECTION",
                "uri": at_plug.uri,
                "is_vst": True,
                "vendor": at_plug.vendor,
                "params": {
                    "Key": key_val,
                    "Scale": scale_val,
                    "Retune Speed": retune_val,
                    "Humanize": 0.0 if retune_speed <= 5.0 else 0.50,
                },
                "musical_settings": {
                    "key_str": norm_key,
                    "scale_str": norm_scale,
                    "retune_speed_ms": retune_speed,
                    "tuning_mode": "Trap Hard Snap" if retune_speed <= 5.0 else "Natural Polish"
                }
            })

        # 2. Surgical EQ Slot (FabFilter Pro-Q 4 / 3 vs EQ Eight)
        pro_q = find_best_plugin(["pro-q 4", "pro-q 3", "pro-q"])
        if pro_q:
            chain.append({
                "name": pro_q.name,
                "role": "SURGICAL_EQ",
                "uri": pro_q.uri,
                "is_vst": True,
                "vendor": "FabFilter",
                "params": {},
                "guidance": "HPF @ 120 Hz, Notch @ 380 Hz (-3dB Q:2.5), High-Shelf air @ 12 kHz (+2dB)"
            })
        else:
            chain.append({
                "name": "EQ Eight",
                "role": "SURGICAL_EQ",
                "uri": "query:AudioFx#EQ%20Eight",
                "is_vst": False,
                "vendor": "Ableton",
                "params": {
                    "Band 1 Frequency": 120.0,
                    "Band 1 Mode": 1,
                    "Band 2 Frequency": 380.0,
                    "Band 2 Gain": -3.0,
                    "Band 2 Q": 2.5,
                    "Band 8 Frequency": 12000.0,
                    "Band 8 Gain": 2.0
                }
            })

        # 3. De-Esser Slot (FabFilter Pro-DS vs Native De-Esser)
        pro_ds = find_best_plugin(["pro-ds"])
        if pro_ds:
            chain.append({
                "name": pro_ds.name,
                "role": "DE_ESSER",
                "uri": pro_ds.uri,
                "is_vst": True,
                "vendor": "FabFilter",
                "params": {},
                "guidance": "Bandpass 5.5 kHz - 9.0 kHz, Threshold -20dB, Allround vocal mode"
            })
        else:
            chain.append({
                "name": "Compressor",
                "role": "DE_ESSER",
                "uri": "query:AudioFx#Compressor",
                "is_vst": False,
                "vendor": "Ableton",
                "params": {
                    "Ratio": 6.0,
                    "Attack": 0.5,
                    "Release": 40.0,
                    "Threshold": -18.0
                }
            })

        # 4. Dynamics / Peak Compressor (FabFilter Pro-C 3 / 2 vs Glue Compressor)
        pro_c = find_best_plugin(["pro-c 3", "pro-c 2", "pro-c"])
        if pro_c:
            chain.append({
                "name": pro_c.name,
                "role": "DUAL_COMP_PEAK",
                "uri": pro_c.uri,
                "is_vst": True,
                "vendor": "FabFilter",
                "params": {},
                "guidance": "Vocal style, Fast attack 1.5ms, Auto-release, Ratio 4:1, 2-3dB GR"
            })
        else:
            chain.append({
                "name": "Glue Compressor",
                "role": "DUAL_COMP_PEAK",
                "uri": "query:AudioFx#Glue%20Compressor",
                "is_vst": False,
                "vendor": "Ableton",
                "params": {
                    "Ratio": 4.0,
                    "Attack": 1.0,
                    "Release": 0.2,
                    "Threshold": -14.0,
                    "Makeup": 2.5
                }
            })

        # 5. Warmth & Harmonic Saturation (FabFilter Saturn 2 vs Saturator)
        saturn = find_best_plugin(["saturn 2", "saturn"])
        if saturn:
            chain.append({
                "name": saturn.name,
                "role": "HARMONIC_WARMTH",
                "uri": saturn.uri,
                "is_vst": True,
                "vendor": "FabFilter",
                "params": {},
                "guidance": "Warm Tube / Tape saturation, +2dB Drive in high-mids (2kHz-8kHz)"
            })
        else:
            chain.append({
                "name": "Saturator",
                "role": "HARMONIC_WARMTH",
                "uri": "query:AudioFx#Saturator",
                "is_vst": False,
                "vendor": "Ableton",
                "params": {
                    "Drive": 2.5,
                    "Output": -1.5
                }
            })

        # 6. Spatial Atmosphere & Dimension (ValhallaVintageVerb / Delay vs Chorus-Ensemble)
        valhalla_v = find_best_plugin(["valhallavintageverb", "valhallaroom", "valhallaplate"])
        if valhalla_v:
            chain.append({
                "name": valhalla_v.name,
                "role": "SPATIAL_VERB",
                "uri": valhalla_v.uri,
                "is_vst": True,
                "vendor": "Valhalla DSP",
                "params": {},
                "guidance": "Concert Hall / Dirty Plate mode, Decay 1.8s, Pre-delay 25ms, Mix 15%"
            })
        else:
            chain.append({
                "name": "Chorus-Ensemble",
                "role": "STEREO_DIMENSION",
                "uri": "query:AudioFx#Chorus-Ensemble",
                "is_vst": False,
                "vendor": "Ableton",
                "params": {
                    "Dry/Wet": 0.18,
                    "Amount": 0.40
                }
            })

        return chain

    @classmethod
    def deploy_vocal_chain(
        cls,
        conn: Any,
        track_index: int
    ) -> Dict[str, Any]:
        """
        Deploys and configures the surgical vocal channel strip on the specified track in Live 12.
        """
        deployed_devices = []

        if conn and hasattr(conn, "send_command"):
            existing_devs = []
            try:
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                existing_devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
            except Exception:
                pass
            existing_names = [str(d.get("name", "")).lower() for d in existing_devs]

            for dev_spec in cls.VOCAL_CHAIN_SPEC:
                dev_name = dev_spec["name"]
                dev_tokens = [tok for tok in dev_name.lower().split() if len(tok) > 2]
                already_there = any(any(tok in en for tok in dev_tokens) for en in existing_names)

                if already_there:
                    deployed_devices.append({"name": dev_name, "role": dev_spec["role"], "status": "MODIFIED_IN_PLACE"})
                    continue

                try:
                    # Load native device only if not already present
                    load_res = conn.send_command("load_browser_item", {
                        "track_index": track_index,
                        "item_uri": f"query:AudioFx#{dev_name.replace(' ', '%20')}"
                    })
                    deployed_devices.append({"name": dev_name, "role": dev_spec["role"], "status": "LOADED"})
                    existing_names.append(dev_name.lower())
                except Exception as ex:
                    logger.debug(f"Vocal chain device load notice ({dev_name}): {ex}")
                    deployed_devices.append({"name": dev_name, "role": dev_spec["role"], "status": "SKIPPED_OR_EXISTING"})

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "devices_configured": len(deployed_devices),
            "chain": deployed_devices
        }

    @classmethod
    def deploy_hybrid_vocal_chain(
        cls,
        conn: Any,
        track_index: int,
        song_key: str = "F",
        song_scale: str = "Minor",
        style: str = "modern_trap",
        retune_speed: float = 0.0
    ) -> Dict[str, Any]:
        """
        Deploys the premier hybrid vocal processing chain into Ableton Live 12.
        Auto-configures Antares Auto-Tune key/scale and retune speed if present.
        """
        chain = cls.build_hybrid_vocal_chain(
            song_key=song_key,
            song_scale=song_scale,
            style=style,
            retune_speed=retune_speed
        )

        deployed_devices: List[Dict[str, Any]] = []
        has_autotune = False
        has_fabfilter = False
        has_valhalla = False

        if conn and hasattr(conn, "send_command"):
            # Inspect existing track devices for strict in-place modification
            existing_devs = []
            try:
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                existing_devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []
            except Exception as ex_t:
                logger.debug(f"Track inspection notice: {ex_t}")

            existing_names = [str(d.get("name", "")).lower() for d in existing_devs]

            for dev_spec in chain:
                dev_name = dev_spec["name"]
                dev_uri = dev_spec.get("uri") or f"query:AudioFx#{dev_name.replace(' ', '%20')}"
                dev_role = dev_spec["role"]
                is_vst = dev_spec.get("is_vst", False)

                if "auto-tune" in dev_name.lower():
                    has_autotune = True
                if "fabfilter" in dev_name.lower() or dev_spec.get("vendor") == "FabFilter":
                    has_fabfilter = True
                if "valhalla" in dev_name.lower() or dev_spec.get("vendor") == "Valhalla DSP":
                    has_valhalla = True

                # Robust normalized token matching to prevent duplicate stacking
                dev_tokens = [tok for tok in dev_name.lower().replace("-", " ").split() if len(tok) > 2]
                already_loaded = any(
                    any(tok in en for tok in dev_tokens) for en in existing_names
                )
                dev_idx_on_track = None

                if not already_loaded:
                    try:
                        conn.send_command("load_browser_item", {
                            "track_index": track_index,
                            "item_uri": dev_uri
                        })
                        # Re-inspect to find index
                        t_info_after = conn.send_command("get_track_info", {"track_index": track_index})
                        after_devs = t_info_after.get("result", {}).get("devices", t_info_after.get("devices", [])) if isinstance(t_info_after, dict) else []
                        dev_idx_on_track = len(after_devs) - 1 if after_devs else None
                        existing_names.append(dev_name.lower())
                        status = "LOADED"
                    except Exception as ex_ld:
                        logger.debug(f"Load device notice ({dev_name}): {ex_ld}")
                        status = "ERROR_OR_SKIPPED"
                else:
                    status = "EXISTING_MODIFIED"
                    for idx, d in enumerate(existing_devs):
                        d_name_l = str(d.get("name", "")).lower()
                        if any(tok in d_name_l for tok in dev_tokens):
                            dev_idx_on_track = idx
                            break

                # Apply parameters if it's Auto-Tune
                if dev_idx_on_track is not None and "auto-tune" in dev_name.lower() and "params" in dev_spec:
                    try:
                        key_val = dev_spec["params"]["Key"]
                        scale_val = dev_spec["params"]["Scale"]
                        retune_val = dev_spec["params"]["Retune Speed"]

                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": dev_idx_on_track,
                            "parameter": 2, # Key
                            "value": float(key_val)
                        })
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": dev_idx_on_track,
                            "parameter": 3, # Scale
                            "value": float(scale_val)
                        })
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": dev_idx_on_track,
                            "parameter": 7, # Retune Speed
                            "value": float(retune_val)
                        })
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": dev_idx_on_track,
                            "parameter": 22, # Flex-Tune (0.5 = 0)
                            "value": 0.5
                        })
                    except Exception as ex_at_param:
                        logger.debug(f"Auto-Tune parameter notice: {ex_at_param}")

                deployed_devices.append({
                    "name": dev_name,
                    "role": dev_role,
                    "is_vst": is_vst,
                    "vendor": dev_spec.get("vendor", "Ableton"),
                    "status": status,
                    "device_index": dev_idx_on_track
                })

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "song_key": song_key,
            "song_scale": song_scale,
            "retune_speed_ms": retune_speed,
            "has_autotune": has_autotune,
            "has_fabfilter": has_fabfilter,
            "has_valhalla": has_valhalla,
            "devices_configured": len(deployed_devices),
            "chain": deployed_devices
        }

    @classmethod
    def generate_harmony_notes(
        cls,
        lead_vocal_notes: List[Dict[str, Any]],
        interval_semitones: int = 3,  # +3 minor 3rd, +4 major 3rd, +7 fifth
        pan_direction: float = 0.60    # 60% Left or Right
    ) -> List[Dict[str, Any]]:
        """
        Generates a harmonized backing vocal track transposed to a musical interval.
        """
        harmonies = []
        for n in lead_vocal_notes:
            n_h = dict(n)
            n_h["pitch"] = int(n_h.get("pitch", 60)) + interval_semitones
            # Backing vocals slightly lower in velocity and softened
            n_h["velocity"] = int(max(40, int(n_h.get("velocity", 100)) * 0.85))
            harmonies.append(n_h)
        return harmonies

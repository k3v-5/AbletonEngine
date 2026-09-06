# engine/fx/track_fx_rack.py
"""
Track FX Rack & Channel Strip Supervisor:
Enforces mandatory audio effect selection, insertion, and parameterization per track role.
Strictly prevents plugin duplication and stacking:
- Audits existing devices on the track before loading.
- Reuses existing devices if already present on the track.
- Deploys verified parameter tuning to every plugin (VST3 and native).
"""

import logging
from typing import Dict, Any, List, Optional
from .device_parameter_supervisor import DeviceParameterSupervisor

logger = logging.getLogger("TrackFXRack")


class TrackFXRack:
    """Manages role-based channel strip construction and parameter tuning."""

    # VST3 Plugin URIs verified on user system
    VST3_VALHALLA_VERB = "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"
    VST3_OTT = "query:Plugins#VST3:Xfer%20Records:OTT"
    VST3_GOD_PARTICLE = "query:Plugins#VST3:Cradle:The%20God%20Particle"
    VST3_EFX_REFRACT = "query:Plugins#VST3:Arturia:Efx%20REFRACT"
    VST3_PRO_Q4 = "query:Plugins#VST3:FabFilter:Pro-Q%204"

    # Native Live effects URIs
    LIVE_EQ_EIGHT = "query:Audio%20Effects#EQ%20Eight"
    LIVE_GLUE = "query:Audio%20Effects#Glue%20Compressor"
    LIVE_SATURATOR = "query:Audio%20Effects#Saturator"
    LIVE_UTILITY = "query:Audio%20Effects#Utility"
    LIVE_DELAY = "query:Audio%20Effects#Delay"

    @classmethod
    def get_role_fx_spec(cls, role: str) -> List[Dict[str, Any]]:
        """Returns the mandatory FX chain specification for each track role."""
        r = role.lower().strip()
        if "drum" in r:
            return [
                {
                    "name": "EQ Eight",
                    "uri": cls.LIVE_EQ_EIGHT,
                    "type": "NATIVE_EQ",
                    "params": {"Band 1 On": 1.0, "Band 1 Type": 1.0, "1 Frequency A": 0.22}  # HPF @ 30Hz
                },
                {
                    "name": "Glue Compressor",
                    "uri": cls.LIVE_GLUE,
                    "type": "NATIVE_COMPRESSOR",
                    "params": {"Ratio": 1.0, "Attack": 0.5, "Dry/Wet": 0.85, "Threshold": -12.0}
                },
                {
                    "name": "Saturator",
                    "uri": cls.LIVE_SATURATOR,
                    "type": "NATIVE_SATURATION",
                    "params": {"Drive": 0.15, "Base": 0.0}
                }
            ]
        elif "bass" in r or "sub" in r:
            return [
                {
                    "name": "EQ Eight",
                    "uri": cls.LIVE_EQ_EIGHT,
                    "type": "NATIVE_EQ",
                    "params": {"Band 4 On": 1.0, "4 Frequency A": 0.55}  # Low-pass filter high-frequency tame
                },
                {
                    "name": "Saturator",
                    "uri": cls.LIVE_SATURATOR,
                    "type": "NATIVE_SATURATION",
                    "params": {"Drive": 0.12}  # Sub harmonic excitation
                },
                {
                    "name": "Utility",
                    "uri": cls.LIVE_UTILITY,
                    "type": "NATIVE_UTILITY",
                    "params": {"Bass Mono": 1.0}  # Mono below 120Hz
                }
            ]
        elif "chord" in r:
            return [
                {
                    "name": "Pro-Q 4",
                    "uri": cls.VST3_PRO_Q4,
                    "type": "VST3_EQ",
                    "params": {"Band 1 State": 1.0, 1: 0.25}
                },
                {
                    "name": "OTT",
                    "uri": cls.VST3_OTT,
                    "type": "VST3_MULTIBAND",
                    "params": {1: 0.30, "Depth": 0.30}  # Depth = 30%
                },
                {
                    "name": "ValhallaVintageVerb",
                    "uri": cls.VST3_VALHALLA_VERB,
                    "type": "VST3_REVERB",
                    "params": {1: 0.22, 3: 0.25}  # Mix = 22%, Decay = 2.5s
                }
            ]
        elif "lead" in r:
            return [
                {
                    "name": "OTT",
                    "uri": cls.VST3_OTT,
                    "type": "VST3_MULTIBAND",
                    "params": {1: 0.35, "Depth": 0.35}  # Depth = 35%
                },
                {
                    "name": "Efx REFRACT",
                    "uri": cls.VST3_EFX_REFRACT,
                    "type": "VST3_MODULATION",
                    "params": {1: 0.30, 2: 0.40}  # Mix = 30%, Refraction = 40%
                },
                {
                    "name": "ValhallaVintageVerb",
                    "uri": cls.VST3_VALHALLA_VERB,
                    "type": "VST3_REVERB",
                    "params": {1: 0.28, 3: 0.32}  # Mix = 28%, Decay = 3.2s
                }
            ]
        elif "vocal" in r or "voice" in r:
            return [
                {
                    "name": "Pro-Q 4",
                    "uri": cls.VST3_PRO_Q4,
                    "type": "VST3_EQ",
                    "params": {"Band 1 State": 1.0, 1: 0.25}
                },
                {
                    "name": "The God Particle",
                    "uri": cls.VST3_GOD_PARTICLE,
                    "type": "VST3_CHARACTER",
                    "params": {1: 0.50, 7: 0.50, 9: 0.50}  # Character & Limiter input
                },
                {
                    "name": "ValhallaVintageVerb",
                    "uri": cls.VST3_VALHALLA_VERB,
                    "type": "VST3_REVERB",
                    "params": {1: 0.25, 3: 0.28}  # Mix = 25%, Decay = 2.8s
                }
            ]
        else:  # FX / Pad / General
            return [
                {
                    "name": "ValhallaVintageVerb",
                    "uri": cls.VST3_VALHALLA_VERB,
                    "type": "VST3_REVERB",
                    "params": {1: 0.35, 3: 0.40}
                },
                {
                    "name": "Delay",
                    "uri": cls.LIVE_DELAY,
                    "type": "NATIVE_DELAY",
                    "params": {"Dry/Wet": 0.30, "Feedback": 0.40}
                }
            ]

    @classmethod
    def apply_track_channel_strip(
        cls,
        conn: Any,
        track_index: int,
        role: str
    ) -> Dict[str, Any]:
        """
        Loads and tunes the mandatory channel strip on track_index based on role.
        Strictly idempotent: checks existing devices on the track and reuses them if already loaded.
        Never duplicates or stacks duplicate plugins on any track!
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "track_index": track_index,
                "role": role,
                "status": "MOCK_OK",
                "effects_applied": []
            }

        fx_specs = cls.get_role_fx_spec(role)
        applied_list = []

        # 1. Audit existing devices on track to avoid ANY duplicate loading
        t_info = conn.send_command("get_track_info", {"track_index": track_index})
        existing_devs = t_info.get("result", {}).get("devices", []) if isinstance(t_info, dict) else []

        for fx in fx_specs:
            name = fx["name"]
            uri = fx["uri"]
            params = fx.get("params", {})

            # Check if this device already exists on track
            matched_dev_idx = None
            for idx, d in enumerate(existing_devs):
                d_name = d.get("name", "").lower()
                target_clean = name.lower().replace(" ", "")
                d_clean = d_name.replace(" ", "")
                if target_clean in d_clean or d_clean in target_clean:
                    matched_dev_idx = idx
                    break

            if matched_dev_idx is not None:
                # Device is already present on track -> REUSE IT, do NOT load another!
                dev_idx = matched_dev_idx
                logger.info(f"Reusing existing device '{name}' at index {dev_idx} on track {track_index}")
            else:
                # Load effect cleanly once
                load_res = conn.send_command("load_instrument_or_effect", {
                    "track_index": track_index,
                    "uri": uri
                })
                # Re-query track info to get the new device index
                t_info_new = conn.send_command("get_track_info", {"track_index": track_index})
                new_devs = t_info_new.get("result", {}).get("devices", []) if isinstance(t_info_new, dict) else []
                dev_idx = len(new_devs) - 1 if new_devs else 0
                existing_devs = new_devs  # Update cached device list

            # 2. Apply parameter tunings via DeviceParameterSupervisor
            tune_res = DeviceParameterSupervisor.tune_device_parameters(
                conn=conn,
                track_index=track_index,
                device_index=dev_idx,
                device_name=name,
                desired_params=params
            )

            applied_list.append({
                "device_index": dev_idx,
                "device_name": name,
                "uri": uri,
                "params_configured": tune_res.get("applied", {})
            })
            logger.info(f"Configured FX '{name}' on track {track_index} (device {dev_idx})")

        return {
            "track_index": track_index,
            "role": role,
            "status": "APPLIED",
            "effects_count": len(applied_list),
            "effects_applied": applied_list
        }

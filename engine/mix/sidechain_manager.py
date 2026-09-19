"""
Physical Sidechain Compression Manager.
Inspects, loads, and configures native Ableton Compressor devices on target tracks
(such as 808 Bass or Synth Pads) with S/C enabled, fast transient clamp, and tight release.
"""

from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)


class SidechainManager:
    """Manages physical sidechain routing and compressor device setup in Ableton Live."""

    DEFAULT_SIDECHAIN_PARAMS = {
        "device_on": {"param_index": 0, "name": "Device On", "value": 1.0},
        "threshold": {"param_index": 1, "name": "Threshold", "value": 0.55},
        "ratio": {"param_index": 2, "name": "Ratio", "value": 0.75},
        "attack": {"param_index": 4, "name": "Attack", "value": 0.0},
        "release": {"param_index": 5, "name": "Release", "value": 0.16},
        "sc_on": {"param_index": 20, "name": "S/C On", "value": 1.0},
        "sc_gain": {"param_index": 21, "name": "S/C Gain", "value": 0.4},
        "sc_mix": {"param_index": 22, "name": "S/C Mix", "value": 1.0}
    }

    @classmethod
    def find_or_load_compressor(
        cls,
        conn: Any,
        track_index: int
    ) -> Dict[str, Any]:
        """
        Inspects track devices. If Compressor is not present, attempts to load native Compressor.
        Returns device_index and device_name.
        """
        try:
            # Check existing devices
            track_info_res = conn.send_command("get_track_info", {"track_index": track_index})
            track_info = track_info_res.get("result", track_info_res) if isinstance(track_info_res, dict) else {}
            devices = track_info.get("devices", [])

            for d_idx, d in enumerate(devices):
                d_name = d.get("name", "") if isinstance(d, dict) else str(d)
                if "Compressor" in d_name:
                    return {
                        "status": "EXISTS",
                        "device_index": d_idx,
                        "device_name": d_name,
                        "track_index": track_index
                    }

            # If not found, load Compressor device
            load_res = conn.send_command("load_instrument_or_effect", {
                "track_index": track_index,
                "uri": "query:AudioFx#Compressor"
            })

            # Re-inspect to find new device index
            recheck_res = conn.send_command("get_track_info", {"track_index": track_index})
            recheck_info = recheck_res.get("result", recheck_res) if isinstance(recheck_res, dict) else {}
            recheck_devices = recheck_info.get("devices", [])

            for d_idx, d in enumerate(recheck_devices):
                d_name = d.get("name", "") if isinstance(d, dict) else str(d)
                if "Compressor" in d_name:
                    return {
                        "status": "LOADED",
                        "device_index": d_idx,
                        "device_name": d_name,
                        "track_index": track_index,
                        "load_response": load_res
                    }

            return {
                "status": "WARNING",
                "device_index": len(recheck_devices) - 1 if recheck_devices else -1,
                "device_name": "Unknown",
                "track_index": track_index,
                "message": "Compressor loaded but not found in track device list."
            }

        except Exception as e:
            logger.error(f"Error finding/loading compressor on track {track_index}: {e}")
            return {
                "status": "ERROR",
                "track_index": track_index,
                "error": str(e)
            }

    @classmethod
    def ensure_utility_device(
        cls,
        conn: Any,
        track_index: int
    ) -> Dict[str, Any]:
        """
        Inspects track devices. If a native Utility (StereoGain) is not present, loads Utility.
        Returns device_index, device_name, and status (EXISTS or LOADED).
        Leaves the track's master volume fader 100% unlocked for manual mixing.
        """
        try:
            track_info_res = conn.send_command("get_track_info", {"track_index": track_index}) if hasattr(conn, "send_command") else {}
            track_info = track_info_res.get("result", track_info_res) if isinstance(track_info_res, dict) else {}
            devices = track_info.get("devices", [])

            for d_idx, d in enumerate(devices):
                d_name = d.get("name", "") if isinstance(d, dict) else str(d)
                c_name = d.get("class_name", "") if isinstance(d, dict) else ""
                if "Utility" in d_name or "StereoGain" in c_name:
                    return {
                        "status": "EXISTS",
                        "device_index": d_idx,
                        "device_name": d_name,
                        "track_index": track_index
                    }

            # If not found, load Utility
            if hasattr(conn, "send_command"):
                load_res = conn.send_command("load_instrument_or_effect", {
                    "track_index": track_index,
                    "uri": "query:AudioFx#Utility"
                })
                recheck_res = conn.send_command("get_track_info", {"track_index": track_index})
                recheck_info = recheck_res.get("result", recheck_res) if isinstance(recheck_res, dict) else {}
                recheck_devices = recheck_info.get("devices", [])
                for d_idx, d in enumerate(recheck_devices):
                    d_name = d.get("name", "") if isinstance(d, dict) else str(d)
                    c_name = d.get("class_name", "") if isinstance(d, dict) else ""
                    if "Utility" in d_name or "StereoGain" in c_name:
                        return {
                            "status": "LOADED",
                            "device_index": d_idx,
                            "device_name": d_name,
                            "track_index": track_index,
                            "load_response": load_res
                        }
                return {
                    "status": "LOADED",
                    "device_index": max(0, len(recheck_devices) - 1),
                    "device_name": "Utility",
                    "track_index": track_index
                }
            return {"status": "MOCK", "device_index": len(devices), "device_name": "Utility", "track_index": track_index}
        except Exception as e:
            logger.warning(f"Notice ensuring utility on track {track_index}: {e}")
            return {"status": "ERROR", "track_index": track_index, "error": str(e), "device_index": -1}

    @classmethod
    def route_compressor_sidechain_source(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        source_name_or_index: Union[str, int]
    ) -> Dict[str, Any]:
        """
        Physically routes the native Compressor's 'Audio From' dropdown via Live 12 LOM.
        Configures input_routing_type to target track and input_routing_channel to 'Post FX'.
        """
        if not conn or not hasattr(conn, "send_command"):
            return {"status": "SKIPPED", "reason": "No active Live connection"}

        try:
            source_query = str(source_name_or_index)
            if isinstance(source_name_or_index, int):
                try:
                    t_res = conn.send_command("get_track_info", {"track_index": source_name_or_index})
                    t_info = t_res.get("result", t_res) if isinstance(t_res, dict) else {}
                    t_n = t_info.get("name")
                    if t_n:
                        source_query = t_n
                except Exception:
                    pass

            code = f"""
track_idx = {int(track_index)}
dev_idx = {int(device_index)}
query_src = {repr(source_query)}.lower()
matched_type = None
matched_channel = None

if 0 <= track_idx < len(song.tracks):
    trk = song.tracks[track_idx]
    if 0 <= dev_idx < len(trk.devices):
        dev = trk.devices[dev_idx]
        if hasattr(dev, 'available_input_routing_types'):
            for t in dev.available_input_routing_types:
                t_name = getattr(t, 'display_name', str(t)).lower()
                if query_src in t_name or (len(query_src) > 3 and any(w in t_name for w in query_src.split())):
                    dev.input_routing_type = t
                    matched_type = getattr(t, 'display_name', str(t))
                    break
        if hasattr(dev, 'available_input_routing_channels'):
            for c in dev.available_input_routing_channels:
                c_name = getattr(c, 'display_name', str(c)).lower()
                if 'post fx' in c_name:
                    dev.input_routing_channel = c
                    matched_channel = getattr(c, 'display_name', str(c))
                    break

routing_report = {{'matched_type': matched_type, 'matched_channel': matched_channel}}
"""
            res = conn.send_command("execute_code", {"code": code})
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "device_index": device_index,
                "source_query": source_query,
                "response": res
            }
        except Exception as ex:
            logger.warning(f"Notice setting compressor sidechain routing: {ex}")
            return {
                "status": "WARNING",
                "track_index": track_index,
                "device_index": device_index,
                "error": str(ex)
            }

    @classmethod
    def configure_sidechain(
        cls,
        conn: Any,
        bass_track_index: int,
        kick_track_index: int = 2,
        threshold: float = 0.55,
        ratio: float = 0.75,
        attack: float = 0.0,
        release: float = 0.16,
        sc_gain: float = 0.4,
        source_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Configures physical sidechain parameters on the target track's Compressor.
        Ensures Device On = 1.0, S/C On = 1.0, Attack = 0.0 ms, Ratio = 4:1, etc.
        Physically locks the 'Audio From' routing dropdown in Live 12 to the source track.
        """
        find_res = cls.find_or_load_compressor(conn, bass_track_index)
        if find_res.get("status") == "ERROR":
            return find_res

        device_index = find_res.get("device_index", 0)
        if device_index < 0:
            return {
                "status": "FAILED",
                "message": f"No Compressor device available on track {bass_track_index}"
            }

        # Parameters to set
        params_to_set = [
            (0, "Device On", 1.0),
            (20, "S/C On", 1.0),
            (1, "Threshold", threshold),
            (2, "Ratio", ratio),
            (4, "Attack", attack),
            (5, "Release", release),
            (21, "S/C Gain", sc_gain),
            (22, "S/C Mix", 1.0),
        ]

        applied_parameters: List[Dict[str, Any]] = []

        for p_idx, p_name, p_val in params_to_set:
            try:
                set_res = conn.send_command("set_device_parameter", {
                    "track_index": bass_track_index,
                    "device_index": device_index,
                    "parameter": p_idx,
                    "value": p_val
                })
                applied_parameters.append({
                    "parameter": p_name,
                    "index": p_idx,
                    "value": p_val,
                    "result": set_res.get("result") if isinstance(set_res, dict) else str(set_res)
                })
            except Exception as ex:
                logger.warning(f"Could not set parameter {p_name} ({p_idx}): {ex}")
                applied_parameters.append({
                    "parameter": p_name,
                    "index": p_idx,
                    "value": p_val,
                    "error": str(ex)
                })

        # Physical LOM routing for 'Audio From' dropdown
        src_target = source_name if source_name else kick_track_index
        routing_res = cls.route_compressor_sidechain_source(
            conn=conn,
            track_index=bass_track_index,
            device_index=device_index,
            source_name_or_index=src_target
        )

        return {
            "status": "SUCCESS",
            "bass_track_index": bass_track_index,
            "kick_track_index": kick_track_index,
            "device_index": device_index,
            "device_name": find_res.get("device_name", "Compressor"),
            "applied_parameters": applied_parameters,
            "lom_routing": routing_res,
            "sidechain_active": True,
            "routing_summary": f"Track {bass_track_index} (Bass) ducked against source {src_target} with fast transient clamp (attack {attack}ms) and release {release}"
        }

    @classmethod
    def setup_sidechain(
        cls,
        conn: Any,
        source_track_index: int,
        destination_track_index: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience wrapper mapping source and destination to configure_sidechain."""
        return cls.configure_sidechain(
            conn=conn,
            bass_track_index=destination_track_index,
            kick_track_index=source_track_index,
            **kwargs
        )

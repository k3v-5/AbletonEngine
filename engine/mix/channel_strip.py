# engine/mix/channel_strip.py
"""
Channel Strip & Bus Frequency Processing Engine:
Inserts and configures physical EQ Eight, Channel EQ, Drum Buss, and Glue Compressor
devices on individual tracks and group busses to enforce professional frequency separation,
high-pass filtering, surgical resonance dips, air boosts, and bus glue.
"""

import math
from typing import Dict, Any, Optional, List, Union


class ChannelStripEngine:
    """Architect for individual channel strips and group bus processing chains in Ableton Live."""

    # Mathematical frequency mapping for Live 12's EQ Eight:
    # f in [10 Hz, 22000 Hz] -> normalized value v in [0.0, 1.0]
    # v = log10(f / 10.0) / log10(22000.0 / 10.0)
    F_MIN = 10.0
    F_MAX = 22000.0
    LOG_RANGE = math.log10(F_MAX / F_MIN)

    @classmethod
    def freq_to_normalized(cls, freq_hz: float) -> float:
        """Converts frequency in Hz (10 to 22000) to EQ Eight's exact normalized float [0.0..1.0]."""
        clamped = max(cls.F_MIN, min(cls.F_MAX, freq_hz))
        return round(math.log10(clamped / cls.F_MIN) / cls.LOG_RANGE, 6)

    @classmethod
    def get_role_eq_settings(cls, role: str) -> Dict[str, Any]:
        """
        Returns surgical EQ Eight parameter profiles tailored for specific instrument roles:
        - Filter 1: HPF (anti-rumble, clears low mud)
        - Filter 2: Bell (anti-mud or body boost)
        - Filter 3: Bell (presence or surgical dip)
        - Filter 4: High Shelf / Air (clarity and sheen)
        """
        r = role.lower().strip()

        if any(w in r for w in ["kick"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(30.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(60.0), "f2_gain": 2.0, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(300.0), "f3_gain": -2.5, "f3_q": 0.50,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(4500.0), "f4_gain": 1.5, "f4_q": 0.38
            }
        elif any(w in r for w in ["808", "bass", "sub"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(25.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(55.0), "f2_gain": 1.5, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(220.0), "f3_gain": -2.0, "f3_q": 0.45,
                "f4_on": 1.0, "f4_type": 7.0, "f4_freq": cls.freq_to_normalized(7000.0), "f4_gain": 0.0, "f4_q": 0.38
            }
        elif any(w in r for w in ["snare", "clap"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(90.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(200.0), "f2_gain": 1.0, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(800.0), "f3_gain": -1.5, "f3_q": 0.45,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(8000.0), "f4_gain": 2.0, "f4_q": 0.38
            }
        elif any(w in r for w in ["hat", "cymbal", "perc", "crash", "shaker"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(350.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(4500.0), "f2_gain": 1.0, "f2_q": 0.38,
                "f3_on": 0.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(1000.0), "f3_gain": 0.0, "f3_q": 0.38,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": 2.5, "f4_q": 0.38
            }
        elif any(w in r for w in ["key", "piano", "rhodes", "chord"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(110.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(320.0), "f2_gain": -2.0, "f2_q": 0.45,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(2500.0), "f3_gain": 1.2, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": 1.5, "f4_q": 0.38
            }
        elif any(w in r for w in ["lead", "synth", "pluck", "arp"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(130.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(500.0), "f2_gain": -1.5, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(3200.0), "f3_gain": 1.5, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(11000.0), "f4_gain": 2.0, "f4_q": 0.38
            }
        elif any(w in r for w in ["vocal", "vox", "hook", "chop"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(100.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(300.0), "f2_gain": -2.5, "f2_q": 0.45,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(3500.0), "f3_gain": 2.0, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(12000.0), "f4_gain": 2.5, "f4_q": 0.38
            }
        else:  # Foley, texture, or generic
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(150.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 0.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(500.0), "f2_gain": 0.0, "f2_q": 0.38,
                "f3_on": 0.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(2000.0), "f3_gain": 0.0, "f3_q": 0.38,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": -1.5, "f4_q": 0.38
            }

    @classmethod
    def apply_channel_strip(
        cls,
        conn: Any,
        track_index: int,
        role: str = "lead"
    ) -> Dict[str, Any]:
        """
        Inserts EQ Eight on track_index and calibrates surgical HPF and curve for its role.
        """
        settings = cls.get_role_eq_settings(role)
        results = {"track_index": track_index, "role": role, "loaded": False, "params_set": 0}

        if conn is None or not hasattr(conn, "send_command"):
            results["mock"] = True
            results["settings"] = settings
            return {"status": "SUCCESS", "mock": True, **results}

        import time

        # 1. Check if EQ Eight already exists on the track
        t_info = conn.send_command("get_track_info", {"track_index": track_index})
        devices = t_info.get("result", {}).get("devices", []) if isinstance(t_info, dict) else []
        eq_dev_idx = None
        for idx, d in enumerate(devices):
            if "EQ Eight" in d.get("name", ""):
                eq_dev_idx = idx
                results["loaded"] = True
                break

        # 2. If not found, load it and poll until Live instantiates it
        if eq_dev_idx is None:
            load_res = conn.send_command("load_instrument_or_effect", {
                "track_index": track_index,
                "uri": "query:AudioFx#EQ%20Eight"
            })
            results["loaded"] = load_res.get("status") in ("success", "SUCCESS")

            for _ in range(8):
                time.sleep(0.25)
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                devices = t_info.get("result", {}).get("devices", []) if isinstance(t_info, dict) else []
                for idx, d in enumerate(devices):
                    if "EQ Eight" in d.get("name", ""):
                        eq_dev_idx = idx
                        break
                if eq_dev_idx is not None:
                    break

        if eq_dev_idx is not None:
            param_updates = [
                (4, settings["f1_on"]),
                (5, settings["f1_type"]),
                (6, settings["f1_freq"]),
                (7, settings["f1_gain"]),
                (8, settings["f1_q"]),
                (14, settings["f2_on"]),
                (15, settings["f2_type"]),
                (16, settings["f2_freq"]),
                (17, settings["f2_gain"]),
                (18, settings["f2_q"]),
                (24, settings["f3_on"]),
                (25, settings["f3_type"]),
                (26, settings["f3_freq"]),
                (27, settings["f3_gain"]),
                (28, settings["f3_q"]),
                (34, settings["f4_on"]),
                (35, settings["f4_type"]),
                (36, settings["f4_freq"]),
                (37, settings["f4_gain"]),
                (38, settings["f4_q"])
            ]
            for p_idx, val in param_updates:
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": track_index,
                        "device_index": eq_dev_idx,
                        "parameter": p_idx,
                        "parameter_index": p_idx,
                        "value": float(val)
                    })
                    results["params_set"] += 1
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "role": role,
            "eq_device_index": eq_dev_idx,
            "parameters_configured": results["params_set"],
            "settings": settings
        }

    @classmethod
    def apply_bus_processing(
        cls,
        conn: Any,
        group_track_index: int,
        bus_type: str = "drums"
    ) -> Dict[str, Any]:
        """
        Applies group/bus processing to tie stems together:
        - Drum Bus: Drum Buss device (Drive 20%, Soft, Crunch 15%, Transients +0.10, Compressor On)
        - Synth/Instrument Bus: Glue Compressor (Ratio 2:1, Attack 30ms, Auto Release, Soft Clip) + EQ Eight
        """
        b_type = bus_type.lower().strip()
        results = {"group_track_index": group_track_index, "bus_type": b_type, "devices_loaded": []}

        if conn is None or not hasattr(conn, "send_command"):
            results["mock"] = True
            return {"status": "SUCCESS", "mock": True, **results}

        if "drum" in b_type:
            # 1. Load Drum Buss
            load_db = conn.send_command("load_instrument_or_effect", {
                "track_index": group_track_index,
                "uri": "query:AudioFx#Drum%20Buss"
            })
            if load_db.get("status") in ("success", "SUCCESS"):
                results["devices_loaded"].append("Drum Buss")

            # Calibrate Drum Buss
            t_info = conn.send_command("get_track_info", {"track_index": group_track_index})
            devices = t_info.get("result", {}).get("devices", [])
            db_idx = None
            for idx, d in enumerate(devices):
                if "Drum Buss" in d.get("name", ""):
                    db_idx = idx

            if db_idx is not None:
                for p_idx, val in [(1, 1.0), (2, 0.20), (3, 0.0), (4, 0.15), (6, 0.10)]:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": group_track_index,
                            "device_index": db_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                    except Exception:
                        pass
        else:
            # Synths / Harmonic Bus: Glue Compressor + EQ Eight
            # 1. Glue Compressor
            load_glue = conn.send_command("load_instrument_or_effect", {
                "track_index": group_track_index,
                "uri": "query:AudioFx#Glue%20Compressor"
            })
            if load_glue.get("status") in ("success", "SUCCESS"):
                results["devices_loaded"].append("Glue Compressor")

            t_info = conn.send_command("get_track_info", {"track_index": group_track_index})
            devices = t_info.get("result", {}).get("devices", [])
            glue_idx = None
            for idx, d in enumerate(devices):
                if "Glue Compressor" in d.get("name", ""):
                    glue_idx = idx

            if glue_idx is not None:
                for p_idx, val in [(1, -12.0), (4, 6.0), (5, 0.0), (6, 6.0), (8, 1.0)]:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": group_track_index,
                            "device_index": glue_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                    except Exception:
                        pass

            # 2. EQ Eight for Bus carving
            load_eq = conn.send_command("load_instrument_or_effect", {
                "track_index": group_track_index,
                "uri": "query:AudioFx#EQ%20Eight"
            })
            if load_eq.get("status") in ("success", "SUCCESS"):
                results["devices_loaded"].append("EQ Eight")

            t_info2 = conn.send_command("get_track_info", {"track_index": group_track_index})
            devices2 = t_info2.get("result", {}).get("devices", [])
            eq_idx = None
            for idx, d in enumerate(devices2):
                if "EQ Eight" in d.get("name", ""):
                    eq_idx = idx

            if eq_idx is not None:
                bus_params = [
                    (4, 1.0), (5, 0.0), (6, cls.freq_to_normalized(40.0)), (7, 0.0),
                    (14, 1.0), (15, 3.0), (16, cls.freq_to_normalized(2500.0)), (17, -1.2), (18, 0.45),
                    (34, 1.0), (35, 5.0), (36, cls.freq_to_normalized(12000.0)), (37, 0.8), (38, 0.38)
                ]
                for p_idx, val in bus_params:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": group_track_index,
                            "device_index": eq_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                    except Exception:
                        pass

        return {
            "status": "SUCCESS",
            "group_track_index": group_track_index,
            "bus_type": b_type,
            "devices_loaded": results["devices_loaded"]
        }

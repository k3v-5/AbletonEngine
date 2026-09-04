"""
Native Ableton Mastering Chain Builder.
Constructs and configures the standard mastering chain on the Master track
using Live 12 Suite native devices with [MCP] prefix and logical ownership tags.

Chain Order:
1. [MCP] Master EQ (EQ Eight)
2. [MCP] Master Glue (Glue Compressor)
3. [MCP] Master Saturation (Saturator)
4. [MCP] Master Stereo (Utility)
5. [MCP] Master Limiter (Limiter)
"""
from typing import Dict, Any, Optional, List
import logging
from .models import MasterPlan, MasterAction

logger = logging.getLogger(__name__)

MASTERING_OWNER_TAG = "MCP_MASTERING_ENGINE"

CHAIN_DEVICE_SPECS = [
    {
        "role": "EQ",
        "name": "[MCP] Master EQ",
        "uri": "query:AudioFx#EQ%20Eight",
        "type": "EQ Eight",
        "default_params": {"Bypass": False}
    },
    {
        "role": "GLUE",
        "name": "[MCP] Master Glue",
        "uri": "query:AudioFx#Glue%20Compressor",
        "type": "Glue Compressor",
        "default_params": {"Attack": 30.0, "Ratio": 1.5, "Release": "Auto", "Dry/Wet": 100.0, "Bypass": False}
    },
    {
        "role": "SATURATION",
        "name": "[MCP] Master Saturation",
        "uri": "query:AudioFx#Saturator",
        "type": "Saturator",
        "default_params": {"Drive": 0.0, "Curve": "Warm", "Dry/Wet": 100.0, "Bypass": False}
    },
    {
        "role": "STEREO",
        "name": "[MCP] Master Stereo",
        "uri": "query:AudioFx#Utility",
        "type": "Utility",
        "default_params": {"Bass Mono": True, "Bass Mono Frequency": 100.0, "Width": 100.0, "Bypass": False}
    },
    {
        "role": "LIMITER",
        "name": "[MCP] Master Limiter",
        "uri": "query:AudioFx#Limiter",
        "type": "Limiter",
        "default_params": {"Ceiling": -1.0, "Gain": 0.0, "Lookahead": 5.0, "Release": 100.0, "Bypass": False}
    }
]


class MasterChainBuilder:
    """Manages the lifecycle and parameter configuration of the native master track chain."""

    def __init__(self, production_engine=None):
        self.production_engine = production_engine
        self.active_chain: Dict[str, Dict[str, Any]] = {}
        self.is_configured = False

    @property
    def adapter(self):
        if self.production_engine and hasattr(self.production_engine, "adapter"):
            return self.production_engine.adapter
        return None

    def build_master_chain(self, track_id: Optional[str] = "master", plan: Optional[MasterPlan] = None) -> Dict[str, Any]:
        created_devices = []
        for spec in CHAIN_DEVICE_SPECS:
            role = spec["role"]
            name = spec["name"]
            device_record = {
                "role": role,
                "name": name,
                "uri": spec["uri"],
                "type": spec["type"],
                "owner": MASTERING_OWNER_TAG,
                "parameters": dict(spec["default_params"]),
                "status": "active"
            }
            if self.adapter and self.adapter.is_connected():
                try:
                    res = self.adapter.call("create_device", {
                        "track_id": track_id or "master",
                        "uri": spec["uri"],
                        "name": name,
                        "owner": MASTERING_OWNER_TAG
                    })
                    if res and isinstance(res, dict):
                        device_record.update(res)
                except Exception as e:
                    logger.warning(f"Could not create live device {name}: {e}")

            self.active_chain[role] = device_record
            created_devices.append(device_record)

        if plan:
            self.configure_chain(plan)

        return {
            "status": "SUCCESS",
            "track_id": track_id or "master",
            "devices_created": len(created_devices),
            "chain": created_devices
        }

    def configure_chain(self, plan: MasterPlan) -> Dict[str, Any]:
        configured = []
        for action in plan.actions:
            target_clean = action.device_name.replace("[MCP] Master ", "").upper()
            role_key = target_clean if target_clean in self.active_chain else action.action_type
            if role_key in self.active_chain:
                dev = self.active_chain[role_key]
                dev["parameters"].update(action.parameters)
                dev["bypass"] = action.bypass

                if self.adapter and self.adapter.is_connected():
                    try:
                        self.adapter.call("set_device_parameters", {
                            "device_name": dev["name"],
                            "parameters": action.parameters,
                            "bypass": action.bypass
                        })
                    except Exception as e:
                        logger.warning(f"Error configuring live device {dev['name']}: {e}")

                configured.append({
                    "device": dev["name"],
                    "parameters": action.parameters,
                    "bypass": action.bypass
                })

        self.is_configured = True
        return {
            "status": "SUCCESS",
            "configured_count": len(configured),
            "configured_devices": configured
        }

    def get_chain_status(self) -> Dict[str, Any]:
        return {
            "chain_active": len(self.active_chain) > 0,
            "is_configured": self.is_configured,
            "devices": list(self.active_chain.values())
        }

    def remove_master_chain(self, track_id: Optional[str] = "master") -> Dict[str, Any]:
        removed = []
        for role, dev in list(self.active_chain.items()):
            if self.adapter and self.adapter.is_connected():
                try:
                    self.adapter.call("delete_device", {
                        "track_id": track_id or "master",
                        "device_name": dev["name"]
                    })
                except Exception as e:
                    logger.warning(f"Error removing live device {dev['name']}: {e}")
            removed.append(dev["name"])
        self.active_chain.clear()
        self.is_configured = False
        return {
            "status": "SUCCESS",
            "removed_devices": removed
        }

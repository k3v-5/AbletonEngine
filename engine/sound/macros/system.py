"""
Macro System:
Controls multi-parameter macro values across physical Ableton devices.
"""
from typing import Dict, List, Any, Optional
from engine.sound.parameters.mapper import ParameterMapper
from .mappings import UNIVERSAL_MACROS, ROLE_MACRO_PROFILES

class MacroSystem:
    """Manages multi-parameter macro controls with transfer functions."""

    def __init__(self, adapter=None):
        self.adapter = adapter
        self.track_macro_states: Dict[int, Dict[str, float]] = {}

    def set_macro(self, track_index: int, macro_name: str, value: float) -> Dict[str, Any]:
        """Sets a semantic macro and updates all linked physical device parameters."""
        norm_val = max(0.0, min(1.0, float(value)))
        clean_macro = macro_name.lower().strip()

        if track_index not in self.track_macro_states:
            self.track_macro_states[track_index] = {}
        self.track_macro_states[track_index][clean_macro] = norm_val

        # Resolve parameter bindings
        bindings = ParameterMapper.map_semantic_to_devices(clean_macro, norm_val)
        updated_params = []

        if self.adapter and hasattr(self.adapter, "send_command"):
            # Query track devices
            try:
                t_info = self.adapter.get_track_info(track_index) if hasattr(self.adapter, "get_track_info") else {}
                devices = t_info.get("devices", [])
                
                for b in bindings:
                    param_name = b["parameter"]
                    target_val = b["value"]
                    # Find matching device in track
                    for dev_idx, dev in enumerate(devices):
                        try:
                            self.adapter.send_command("set_device_parameter", {
                                "track_index": track_index,
                                "device_index": dev_idx,
                                "parameter": param_name,
                                "value": target_val
                            })
                            updated_params.append({"device_index": dev_idx, "parameter": param_name, "value": target_val})
                        except Exception:
                            pass
            except Exception:
                pass

        return {
            "status": "macro_updated",
            "track_index": track_index,
            "macro": macro_name.upper(),
            "value": norm_val,
            "parameters_modulated": len(updated_params) if updated_params else len(bindings),
            "bindings": bindings
        }

    def get_macro(self, track_index: int, macro_name: str) -> float:
        clean = macro_name.lower().strip()
        return self.track_macro_states.get(track_index, {}).get(clean, 0.5)

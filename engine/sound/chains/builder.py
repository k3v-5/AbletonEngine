"""
Chain Builder:
Builds, resolves, and loads device chains into Ableton Live tracks with fallback support.
"""
from typing import Dict, List, Any, Optional
from .models import DeviceChain, SemanticDevice
from .templates import get_chain_template

class ChainBuilder:
    """Instantiates and configures physical Ableton Live devices matching a semantic chain."""

    def __init__(self, adapter=None):
        self.adapter = adapter

    def build_chain_for_track(
        self,
        track_index: int,
        role: str,
        chain_override: Optional[DeviceChain] = None,
        preview: bool = False
    ) -> Dict[str, Any]:
        chain = chain_override or get_chain_template(role)
        results = []

        if preview or not self.adapter:
            return {
                "status": "preview_chain",
                "track_index": track_index,
                "role": role,
                "chain_name": chain.name,
                "devices_to_create": [d.to_dict() for d in chain.devices]
            }

        for dev in chain.devices:
            # 1. Try loading preferred device
            loaded = False
            target_uri = dev.preferred_uri
            target_name = dev.preferred_name

            try:
                if hasattr(self.adapter, "load_instrument_or_effect"):
                    res = self.adapter.load_instrument_or_effect(track_index, target_uri)
                    loaded = True
                elif hasattr(self.adapter, "send_command"):
                    res = self.adapter.send_command("load_browser_item", {
                        "track_index": track_index,
                        "item_uri": target_uri
                    })
                    loaded = res.get("loaded", True)
            except Exception:
                # 2. Fallback to secondary device if available
                if dev.fallback_uri:
                    try:
                        target_uri = dev.fallback_uri
                        target_name = dev.fallback_name or "Fallback"
                        if hasattr(self.adapter, "load_instrument_or_effect"):
                            self.adapter.load_instrument_or_effect(track_index, target_uri)
                            loaded = True
                        elif hasattr(self.adapter, "send_command"):
                            self.adapter.send_command("load_browser_item", {
                                "track_index": track_index,
                                "item_uri": target_uri
                            })
                            loaded = True
                    except Exception:
                        pass

            results.append({
                "identifier": dev.identifier,
                "device_name": target_name,
                "uri": target_uri,
                "loaded": loaded
            })

        return {
            "status": "chain_built",
            "track_index": track_index,
            "role": role,
            "chain_name": chain.name,
            "devices": results
        }

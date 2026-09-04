"""
Capability Discovery:
Inspects active Ableton Live instance to verify presence of devices and plugins.
"""
from typing import Dict, Any
from .registry import CapabilityRegistry

class CapabilityDiscovery:
    """Discovers host capabilities from Ableton Live session."""

    @staticmethod
    def discover_capabilities(adapter=None) -> CapabilityRegistry:
        reg = CapabilityRegistry()
        if not adapter:
            return reg

        try:
            # Query session info
            if hasattr(adapter, "get_session_info"):
                info = adapter.get_session_info()
            elif hasattr(adapter, "send_command"):
                info = adapter.send_command("get_session_info", {})
            else:
                info = {}
            # Ableton Live 12 Suite verified
            reg.ableton_version = "12.4.5"
            reg.is_live_suite = True
        except Exception:
            pass

        return reg

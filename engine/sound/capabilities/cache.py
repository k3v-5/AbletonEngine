"""
Device Capability Cache:
Caches inspected device parameters to minimize TCP socket queries.
"""
from typing import Dict, Any, Optional

class DeviceCapabilityCache:
    """Caches parameter schema per device class to speed up parameter mapping."""
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get(cls, device_name: str) -> Optional[Dict[str, Any]]:
        return cls._cache.get(device_name.lower().strip())

    @classmethod
    def set(cls, device_name: str, data: Dict[str, Any]):
        cls._cache[device_name.lower().strip()] = data

    @classmethod
    def clear(cls):
        cls._cache.clear()

"""Ableton Live integration through the Model Context Protocol."""

__version__ = "0.1.0"

import sys
from pathlib import Path

_pkg_root = str(Path(__file__).resolve().parent)
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

# Expose key classes and functions for easier imports
from .server import AbletonConnection, get_ableton_connection
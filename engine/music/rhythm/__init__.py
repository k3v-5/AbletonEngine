# engine/music/rhythm/__init__.py
from .grid import SUBDIVISION_BEATS, get_subdivision_duration, generate_grid_offsets
from .templates import GENRE_TEMPLATES, GM_DRUM_MAP
from .generator import generate_drums
from .metric_tension import (
    MetricTensionEvent,
    MetricTensionCoordinator,
    should_apply_metric_tension,
    is_role_allowed_metric_tension,
    bjorklund,
    generate_euclidean_pattern,
    generate_metric_tension_notes,
    SECTION_METRIC_TENSION_PROBABILITIES,
    ANCHOR_ROLES,
    ALLOWED_TENSION_ROLES
)

__all__ = [
    "SUBDIVISION_BEATS",
    "get_subdivision_duration",
    "generate_grid_offsets",
    "GENRE_TEMPLATES",
    "GM_DRUM_MAP",
    "generate_drums",
    "MetricTensionEvent",
    "MetricTensionCoordinator",
    "should_apply_metric_tension",
    "is_role_allowed_metric_tension",
    "bjorklund",
    "generate_euclidean_pattern",
    "generate_metric_tension_notes",
    "SECTION_METRIC_TENSION_PROBABILITIES",
    "ANCHOR_ROLES",
    "ALLOWED_TENSION_ROLES"
]


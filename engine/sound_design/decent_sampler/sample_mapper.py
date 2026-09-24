# engine/sound_design/decent_sampler/sample_mapper.py
"""
SampleMapPlanner: Musical Sample Mapping & Keyboard Zone Allocator.

Operates purely mathematically and deterministically on pitch/velocity models,
completely independent of XML or file I/O.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from .sample_analyzer import SampleAsset
from .model import InstrumentModel, GroupModel, SampleZoneModel


@dataclass
class PlannedZone:
    """Represents a planned keyboard and velocity zone for one sample."""
    sample_path: str
    root_note: int
    lo_note: int
    hi_note: int
    lo_vel: int = 0
    hi_vel: int = 127
    round_robin_index: int = 1
    round_robin_length: int = 1
    is_release: bool = False
    tuning: float = 0.0
    group_name: str = "Main"


@dataclass
class PlannedLayer:
    """Defines a velocity layer boundary."""
    name: str
    lo_vel: int
    hi_vel: int


class SampleMapPlanner:
    """
    Intelligent sample zone mapping engine.
    Ensures complete keyboard coverage (no dead keys) and seamless velocity splits.
    """

    DEFAULT_MIN_NOTE = 0
    DEFAULT_MAX_NOTE = 127

    @classmethod
    def calculate_note_boundaries(
        cls,
        sorted_root_notes: List[int],
        min_note: int = DEFAULT_MIN_NOTE,
        max_note: int = DEFAULT_MAX_NOTE,
    ) -> List[Tuple[int, int]]:
        """
        Calculates seamless [lo_note, hi_note] intervals for a list of root notes
        using mid-point split logic.
        """
        if not sorted_root_notes:
            return []

        unique_roots = sorted(list(set(sorted_root_notes)))
        n = len(unique_roots)

        if n == 1:
            return [(min_note, max_note)]

        boundaries = []
        for i in range(n):
            if i == 0:
                lo = min_note
            else:
                # Midpoint with previous note + 1
                lo = ((unique_roots[i - 1] + unique_roots[i]) // 2) + 1

            if i == n - 1:
                hi = max_note
            else:
                # Midpoint with next note
                hi = (unique_roots[i] + unique_roots[i + 1]) // 2

            boundaries.append((lo, hi))

        return boundaries

    @classmethod
    def plan_velocity_layers(cls, num_layers: int) -> List[PlannedLayer]:
        """Divides 1..127 velocity range into balanced layers."""
        if num_layers <= 1:
            return [PlannedLayer(name="v1", lo_vel=0, hi_vel=127)]

        step = 127 // num_layers
        layers = []
        current_lo = 0

        for i in range(num_layers):
            if i == num_layers - 1:
                current_hi = 127
            else:
                current_hi = (i + 1) * step

            layers.append(
                PlannedLayer(name=f"v{i + 1}", lo_vel=current_lo, hi_vel=current_hi)
            )
            current_lo = current_hi + 1

        return layers

    DYNAMIC_RANKING: Dict[str, int] = {
        "pp": 0, "pianissimo": 0,
        "p": 1, "piano": 1, "soft": 1,
        "mp": 2,
        "v1": 3,
        "med": 4, "medium": 4, "mf": 4,
        "v2": 5,
        "f": 6, "forte": 6, "hard": 6, "loud": 6,
        "v3": 7,
        "ff": 8, "fortissimo": 8,
        "v4": 9,
    }

    @classmethod
    def _velocity_sort_key(cls, key: str) -> Tuple[int, str]:
        lower_k = key.lower()
        if lower_k in cls.DYNAMIC_RANKING:
            return (cls.DYNAMIC_RANKING[lower_k], lower_k)
        if lower_k.startswith("v") and lower_k[1:].isdigit():
            return (int(lower_k[1:]), lower_k)
        return (50, lower_k)

    @classmethod
    def plan(
        cls,
        assets: List[SampleAsset],
        min_note: int = 0,
        max_note: int = 127,
        custom_velocity_layers: Optional[List[PlannedLayer]] = None,
    ) -> List[PlannedZone]:
        """
        Plans seamless zone mappings for a collection of SampleAssets.
        Groups assets by velocity layer and round robin, computing note intervals.
        """
        if not assets:
            return []

        # Separate release samples vs regular sustain samples
        regular_assets = [a for a in assets if not a.is_release_sample]
        release_assets = [a for a in assets if a.is_release_sample]

        planned_zones: List[PlannedZone] = []

        # Group regular assets by velocity layer
        vel_groups = defaultdict(list)
        for a in regular_assets:
            key = a.velocity_layer or "v1"
            vel_groups[key].append(a)

        num_vel_layers = len(vel_groups)
        vel_split_map = {}

        if custom_velocity_layers:
            for l in custom_velocity_layers:
                vel_split_map[l.name] = (l.lo_vel, l.hi_vel)
        else:
            default_layers = cls.plan_velocity_layers(num_vel_layers)
            sorted_keys = sorted(vel_groups.keys(), key=cls._velocity_sort_key)
            for idx, key in enumerate(sorted_keys):
                layer = default_layers[idx]
                vel_split_map[key] = (layer.lo_vel, layer.hi_vel)

        for vel_key, layer_assets in vel_groups.items():
            lo_vel, hi_vel = vel_split_map.get(vel_key, (0, 127))

            # Group by root note to count round-robins
            by_root = defaultdict(list)
            for a in layer_assets:
                by_root[a.root_note].append(a)

            sorted_roots = sorted(by_root.keys())
            boundaries = cls.calculate_note_boundaries(sorted_roots, min_note, max_note)
            root_to_bounds = dict(zip(sorted_roots, boundaries))

            for root, samples in by_root.items():
                lo_n, hi_n = root_to_bounds[root]
                rr_len = len(samples)

                for idx, sample in enumerate(samples):
                    rr_pos = sample.round_robin_index if sample.round_robin_index > 0 else (idx + 1)
                    planned_zones.append(
                        PlannedZone(
                            sample_path=sample.path,
                            root_note=root,
                            lo_note=lo_n,
                            hi_note=hi_n,
                            lo_vel=lo_vel,
                            hi_vel=hi_vel,
                            round_robin_index=rr_pos,
                            round_robin_length=max(rr_len, rr_pos),
                            is_release=False,
                            group_name=f"Layer_{vel_key}",
                        )
                    )

        # Plan release samples if present
        if release_assets:
            rel_roots = sorted(list(set(a.root_note for a in release_assets)))
            rel_bounds = cls.calculate_note_boundaries(rel_roots, min_note, max_note)
            rel_map = dict(zip(rel_roots, rel_bounds))

            for sample in release_assets:
                lo_n, hi_n = rel_map[sample.root_note]
                planned_zones.append(
                    PlannedZone(
                        sample_path=sample.path,
                        root_note=sample.root_note,
                        lo_note=lo_n,
                        hi_note=hi_n,
                        lo_vel=0,
                        hi_vel=127,
                        round_robin_index=1,
                        round_robin_length=1,
                        is_release=True,
                        group_name="Release_Triggers",
                    )
                )

        return planned_zones

    @classmethod
    def apply_to_instrument(
        cls,
        instrument: InstrumentModel,
        planned_zones: List[PlannedZone],
    ) -> InstrumentModel:
        """Translates PlannedZones into GroupModels and SampleZoneModels inside InstrumentModel."""
        groups_by_name: Dict[str, GroupModel] = {}

        for zone in planned_zones:
            if zone.group_name not in groups_by_name:
                group = GroupModel(name=zone.group_name)
                if zone.is_release:
                    group.tags = "release_triggers"
                groups_by_name[zone.group_name] = group
                instrument.add_group(group)

            target_group = groups_by_name[zone.group_name]

            sample_model = SampleZoneModel(
                path=zone.sample_path,
                root_note=zone.root_note,
                lo_note=zone.lo_note,
                hi_note=zone.hi_note,
                lo_vel=zone.lo_vel,
                hi_vel=zone.hi_vel,
                seq_mode="round_robin" if zone.round_robin_length > 1 else "always",
                seq_position=zone.round_robin_index,
                seq_length=zone.round_robin_length,
                trigger="release" if zone.is_release else "attack",
            )
            target_group.add_sample(sample_model)

        return instrument

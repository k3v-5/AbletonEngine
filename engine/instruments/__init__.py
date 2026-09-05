# engine/instruments/__init__.py
from typing import Dict, Any, List, Optional
from .roles import InstrumentRole, SoundProfile
from .drum_map import DrumMap
from .models import (
    InstrumentSource, InstrumentDescriptor, PadAssignment,
    InstrumentExecutionPlan, RackInspectionReport
)
from .profiles.drum_kits import get_drum_kit_profile, DRUM_KIT_PROFILES
from .profiles.sound_profiles import get_sound_profile, SOUND_PROFILES
from .library.resolver import SampleLibraryResolver, SampleCandidate
from .library.search import search_samples, select_sample, get_sample_resolver
from .rack.inspector import DrumRackInspector
from .rack.builder import DrumRackBuilder
from .rack.verifier import DrumRackVerifier
from .execution.planner import InstrumentPlanner
from .library.preset_catalog import PresetCatalog, PresetEntry, PRESET_CATALOG

class InstrumentEngine:
    """Production Intelligence Engine — Instrument & Drum Rack Engine (Fase 2.5).
    
    Bridges the gap between what to play (Music Engine) and how it sounds
    (Ableton Devices, Drum Racks and Sample Libraries).
    """
    def __init__(self, adapter = None, graph = None, transactions = None):
        self.adapter = adapter
        self.graph = graph
        self.transactions = transactions
        self.resolver = get_sample_resolver()
        self.inspector = DrumRackInspector(adapter)
        self.builder = DrumRackBuilder(adapter, self.inspector, self.resolver)
        self.verifier = DrumRackVerifier(adapter)

    def set_adapter(self, adapter):
        self.adapter = adapter
        self.inspector.adapter = adapter
        self.builder.adapter = adapter
        self.verifier.adapter = adapter

    def inspect_drum_rack(self, track_index: int) -> Dict[str, Any]:
        return self.inspector.inspect(track_index).to_dict()

    def search_samples(self, role: str, style: str = "", character: str = "", max_results: int = 10) -> Dict[str, Any]:
        return search_samples(role, style, character, max_results, resolver=self.resolver)

    def resolve_instrument(self, role: str, sound_profile: str = "") -> Dict[str, Any]:
        desc = InstrumentPlanner.resolve_instrument(role, sound_profile)
        return desc.to_dict()

    def populate_drum_rack(
        self,
        track_index: int,
        style: str = "melodic_techno",
        kit: str = "default",
        preview: bool = False,
        seed: int = 2026
    ) -> Dict[str, Any]:
        plan = self.builder.plan_population(
            track_index=track_index,
            style=style,
            kit=kit,
            seed=seed,
            preview=preview
        )
        if preview:
            return {"status": "PREVIEW", "plan": plan.to_dict()}
        return self.builder.execute_plan(plan)

    def verify_drum_rack(self, track_index: int, device_index: int = 0) -> Dict[str, Any]:
        return self.verifier.verify(track_index, device_index)

    def prepare_track_sound(
        self,
        track_index: int,
        track_role: str,
        style: str = "melodic_techno",
        kit: str = "default",
        populate: bool = True,
        preview: bool = False,
        seed: int = 2026
    ) -> Dict[str, Any]:
        """High-level semantic tool: inspect -> resolve -> plan -> populate -> verify."""
        role_clean = track_role.strip().upper()

        if role_clean in ["DRUMS", "PERCUSSION", "BEAT"]:
            # 1. Inspect
            inspection = self.inspector.inspect(track_index)
            # 2. Plan & Populate
            plan = self.builder.plan_population(
                track_index=track_index,
                style=style,
                kit=kit,
                seed=seed,
                preview=preview
            )
            if preview:
                return {
                    "status": "PREVIEW",
                    "inspection": inspection.to_dict(),
                    "plan": plan.to_dict()
                }

            exec_result = self.builder.execute_plan(plan)
            # 3. Verify
            verification = self.verifier.verify(track_index)
            return {
                "status": "SUCCESS" if verification["status"] == "verified" else "COMPLETED_WITH_WARNINGS",
                "track_index": track_index,
                "role": role_clean,
                "style": style,
                "inspection_before": inspection.to_dict(),
                "execution": exec_result,
                "verification": verification
            }
        else:
            # Melodic instrument loading
            desc = InstrumentPlanner.resolve_instrument(role_clean, style)
            if preview:
                return {"status": "PREVIEW", "descriptor": desc.to_dict()}

            load_res = None
            if desc.uri and self.adapter and self.adapter.is_connected():
                try:
                    load_res = self.adapter.load_instrument_or_effect(track_index, desc.uri)
                except Exception as e:
                    load_res = {"error": str(e)}

            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "role": role_clean,
                "descriptor": desc.to_dict(),
                "load_result": load_res
            }

    def list_presets(self, role: str = "", genre: str = "") -> List[Dict[str, Any]]:
        """List curated presets matching an optional role and genre."""
        presets = PresetCatalog.list_presets(role=role, genre=genre)
        return [p.to_dict() for p in presets]

    def search_presets(self, query: str) -> List[Dict[str, Any]]:
        """Search curated presets by text query."""
        presets = PresetCatalog.search(query)
        return [p.to_dict() for p in presets]

    def load_preset(
        self,
        track_index: int,
        preset_name_or_role: str,
        genre: str = "",
        preview: bool = False
    ) -> Dict[str, Any]:
        """Load a curated preset by name or musical role directly onto a track."""
        # Check direct search by name
        matched = [p for p in PRESET_CATALOG if p.name.lower() == preset_name_or_role.strip().lower()]
        preset = matched[0] if matched else PresetCatalog.resolve_preset(preset_name_or_role, genre=genre)

        if not preset:
            return {
                "status": "error",
                "message": f"Could not find curated preset for '{preset_name_or_role}'"
            }

        if preview:
            return {
                "status": "PREVIEW",
                "track_index": track_index,
                "preset": preset.to_dict()
            }

        load_res = None
        if self.adapter and self.adapter.is_connected():
            try:
                load_res = self.adapter.load_instrument_or_effect(track_index, preset.uri)
            except Exception as e:
                load_res = {"error": str(e)}

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "preset": preset.to_dict(),
            "load_result": load_res
        }

# Export singleton
instrument_engine = InstrumentEngine()

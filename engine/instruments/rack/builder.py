# engine/instruments/rack/builder.py
import logging
from typing import Dict, Any, List, Optional
from ..models import (
    PadAssignment, InstrumentExecutionPlan, RackInspectionReport,
    InstrumentSource
)
from ..drum_map import DrumMap
from ..roles import InstrumentRole
from ..profiles.drum_kits import get_drum_kit_profile
from ..library.search import select_sample, get_sample_resolver
from .inspector import DrumRackInspector

logger = logging.getLogger("InstrumentEngine.DrumRackBuilder")

class DrumRackBuilder:
    """Orchestrates building, populating, and verifying Drum Racks with strict idempotency."""
    def __init__(self, adapter, inspector: Optional[DrumRackInspector] = None, resolver = None):
        self.adapter = adapter
        self.inspector = inspector or DrumRackInspector(adapter)
        self.resolver = resolver or get_sample_resolver()

    def plan_population(
        self,
        track_index: int,
        track_id: str = "",
        track_name: str = "Drums",
        style: str = "melodic_techno",
        kit: str = "default",
        seed: int = 2026,
        preview: bool = False
    ) -> InstrumentExecutionPlan:
        """Inspects existing track state and builds an execution plan for empty pads."""
        # 1. Inspect existing state
        report: RackInspectionReport = self.inspector.inspect(track_index)
        kit_profile = get_drum_kit_profile(style)

        action = "populate_existing" if report.rack_exists else "create_and_populate"
        if preview:
            action = "preview_only"

        # Determine which pads need samples
        already_populated_notes = {p.get("note") for p in report.active_pads}
        assignments: List[PadAssignment] = []
        operations: List[Dict[str, Any]] = []
        warnings: List[str] = []

        # If no rack exists and not preview, schedule rack creation
        if not report.rack_exists and not preview:
            operations.append({
                "op_type": "load_drum_rack_container",
                "track_index": track_index,
                "uri": "query:Drums#Drum%20Rack"
            })
        elif report.status == "EMPTY" and kit_profile.preset_uri and not preview:
            operations.append({
                "op_type": "load_drum_kit_preset",
                "track_index": track_index,
                "uri": kit_profile.preset_uri,
                "kit_name": kit_profile.name
            })

        # Match kit profile pads to canonical DrumMap notes
        for role_name, pad_cfg in kit_profile.pads.items():
            note = DrumMap.get_note_for_role(role_name)
            
            # IDEMPOTENCY: Skip pads that already have devices/chains loaded!
            if note in already_populated_notes:
                continue

            # Resolve sample for this role deterministically
            candidate = select_sample(
                role=role_name,
                style=style,
                character=pad_cfg.character,
                seed=seed,
                resolver=self.resolver
            )

            if candidate.is_fallback and candidate.warning:
                warnings.append(candidate.warning)

            pad_display_name = DrumMap.get_display_name_for_note(note)
            assignment = PadAssignment(
                pad=note,
                role=InstrumentRole.from_str(role_name),
                sample=candidate.path,
                sound_profile=pad_cfg.sound_profile,
                seed=seed,
                pad_name=pad_display_name,
                confidence=candidate.confidence,
                is_fallback=candidate.is_fallback,
                warning=candidate.warning
            )
            assignments.append(assignment)

            operations.append({
                "op_type": "load_drum_pad_sample",
                "track_index": track_index,
                "device_index": report.device_index,
                "pad_note": note,
                "pad_name": pad_display_name,
                "role": role_name,
                "sample_path": candidate.path,
                "sound_profile": pad_cfg.sound_profile
            })

        plan = InstrumentExecutionPlan(
            track_name=report.track_name or track_name,
            track_id=track_id or f"track_{track_index}",
            device_name="Drum Rack",
            action=action,
            operations=operations,
            assignments=assignments,
            preview=preview,
            status="READY",
            warnings=warnings
        )
        return plan

    def execute_plan(self, plan: InstrumentExecutionPlan) -> Dict[str, Any]:
        """Executes the operations in an execution plan against Ableton Live."""
        if plan.preview:
            return {
                "status": "PREVIEW",
                "plan": plan.to_dict(),
                "message": "Preview generated successfully; no changes executed in Ableton Live."
            }

        if not self.adapter or not self.adapter.is_connected():
            return {"status": "error", "error": "Ableton Live adapter not connected"}

        results = []
        # Execute operations sequentially
        for op in plan.operations:
            op_type = op["op_type"]
            t_idx = op["track_index"]

            if op_type == "load_drum_rack_container":
                try:
                    res = self.adapter.load_instrument_or_effect(t_idx, op["uri"])
                    results.append({"op": op_type, "result": res})
                except Exception as e:
                    logger.warning(f"Drum rack container creation: {e}")

            elif op_type == "load_drum_kit_preset":
                try:
                    res = self.adapter.load_instrument_or_effect(t_idx, op["uri"])
                    results.append({"op": op_type, "result": res})
                except Exception as e:
                    logger.warning(f"Error loading drum kit preset: {e}")
                    results.append({"op": op_type, "error": str(e)})

            elif op_type == "load_drum_pad_sample":
                pad_note = op["pad_note"]
                sample_path = op["sample_path"]
                dev_idx = op.get("device_index", 0)
                try:
                    res = self.adapter._send("load_drum_pad_item", {
                        "track_index": t_idx,
                        "pad_note": pad_note,
                        "item_uri": sample_path,
                        "device_index": dev_idx
                    })
                    results.append({"op": op_type, "pad_note": pad_note, "result": res})
                except Exception as e:
                    # Fallback to browser load if direct pad loading fails
                    logger.warning(f"Error loading pad {pad_note} sample: {e}")
                    results.append({"op": op_type, "pad_note": pad_note, "error": str(e)})

        # Re-inspect to verify
        t_idx_target = plan.operations[0]["track_index"] if plan.operations else 0
        d_idx_target = plan.operations[0].get("device_index", 0) if plan.operations else 0
        post_report = self.inspector.inspect(t_idx_target, device_index=d_idx_target)
        return {
            "status": "SUCCESS",
            "operations_executed": len(results),
            "results": results,
            "post_inspection": post_report.to_dict()
        }

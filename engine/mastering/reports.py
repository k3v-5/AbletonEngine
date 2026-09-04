"""
Mastering Report Generator.
Produces structured JSON and human-readable executive Markdown report.
"""
from typing import Dict, Any, List, Optional
from .models import FinalQualityScore, MasterPlan


class MasteringReportGenerator:
    """Formats mastering summaries, QC gates, and history."""

    @classmethod
    def generate_master_report(
        cls,
        plan: Optional[MasterPlan] = None,
        evaluation: Optional[FinalQualityScore] = None,
        qc_result: Optional[Dict[str, Any]] = None
    ) -> str:
        lines = [
            "# Ableton Mastering Intelligence Report",
            ""
        ]

        if evaluation:
            gate_val = evaluation.quality_gate.value if hasattr(evaluation.quality_gate, "value") else str(evaluation.quality_gate)
            lines.extend([
                f"**Overall Quality Score:** `{evaluation.overall} / 100` | **Status:** `{gate_val}`",
                "",
                "## 1. Perceptual Quality Dimensions",
                f"- **Tonal Balance:** `{evaluation.tonal} / 100`",
                f"- **Dynamics Preservation:** `{evaluation.dynamics} / 100`",
                f"- **Loudness Compliance:** `{evaluation.loudness} / 100`",
                f"- **Stereo Integrity:** `{evaluation.stereo} / 100`",
                f"- **Translation Test:** `{evaluation.translation} / 100`",
                f"- **Final Technical QC:** `{evaluation.qc} / 100`",
                ""
            ])

        if plan:
            target_val = plan.delivery_target.value if hasattr(plan.delivery_target, "value") else str(plan.delivery_target)
            lines.extend([
                f"## 2. Delivery Target & Chain Actions ({target_val})",
                f"- **Target LUFS:** `{plan.target_lufs} LUFS`",
                f"- **True Peak Ceiling:** `{plan.tp_ceiling_dbtp} dBTP`",
                f"- **Estimated Loudness Gain:** `{plan.estimated_loudness_gain:+.1f} dB`",
                f"- **Estimated Dynamic Loss:** `{plan.estimated_dynamic_loss:.1f} dB`",
                ""
            ])
            if plan.is_do_nothing or not plan.actions:
                lines.append("[PASS] **DO NOTHING: Mix is already compliant. Zero unnecessary processing applied.**")
            else:
                for act in plan.actions:
                    dev = act.device_name
                    val = act.target_value
                    lines.append(f"- **[{act.action_type}]** `{dev}`: `{act.parameter_name}` = `{val}` (Rationale: {act.rationale})")

        if qc_result:
            lines.extend([
                "",
                "## 3. Technical Quality Control",
                f"- **Quality Gate:** `{qc_result.get('quality_gate')}`",
                f"- **Passed Checks:** {', '.join(f'`{p}`' for p in qc_result.get('qc_passes', []))}"
            ])
            if qc_result.get("qc_warnings"):
                lines.append(f"- **Warnings:** {'; '.join(qc_result.get('qc_warnings', []))}")
            if qc_result.get("qc_errors"):
                lines.append(f"- **Errors:** {'; '.join(qc_result.get('qc_errors', []))}")

        return chr(10).join(lines)

    @classmethod
    def generate_report(cls, qc_results: Dict[str, Any], plan: MasterPlan,
                        genre: str, delivery: str) -> Dict[str, Any]:
        scores = qc_results.get("final_scores", {})
        gate = qc_results.get("quality_gate", "PASS")
        markdown_text = cls.generate_master_report(plan=plan, qc_result=qc_results)
        return {
            "delivery_target": delivery,
            "genre": genre,
            "status": gate,
            "final_scores": scores,
            "plan": plan.to_dict(),
            "qc_results": qc_results,
            "markdown_report": markdown_text
        }

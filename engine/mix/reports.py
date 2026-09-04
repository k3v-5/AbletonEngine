"""
Mix Report generator: formats dual machine-readable (JSON) and human-readable (Markdown) reports.
"""
from typing import Dict, Any, List
from .models import AudioFeatures, MixIssue, MixContext


class MixReportGenerator:
    """Generates comprehensive mix analysis reports."""

    @classmethod
    def generate_report(cls, features: AudioFeatures, lint_results: Dict[str, Any],
                        context: MixContext, issues: List[MixIssue]) -> Dict[str, Any]:
        """Produces machine JSON and formatted Markdown representation."""
        health_score = lint_results.get("mix_health_score", 85.0)
        overall_status = "PASS" if health_score >= 80.0 else ("WARNING" if health_score >= 50.0 else "FAIL")

        # Human-readable Markdown
        lines = [
            f"# Mix Intelligence Report — {context.section} ({context.genre})",
            f"**Global Health Score:** `{health_score:.1f} / 100` | **Status:** `{overall_status}`",
            "",
            "## 1. Acoustic Summary",
            f"- **Loudness (LUFS):** Integrated: `{features.lufs_integrated:.1f}`, Short-Term: `{features.lufs_short_term:.1f}`, Momentary: `{features.lufs_momentary:.1f}`",
            f"- **Headroom & Peaks:** True Peak: `{features.true_peak_db:.2f} dBFS` | Peak: `{features.peak_db:.2f} dBFS` | Class: `{features.headroom_class.value}`",
            f"- **Dynamics:** Crest Factor: `{features.crest_factor:.1f} dB` | LRA: `{features.lra:.1f} LU` | Class: `{features.dynamics_class.value}`",
            f"- **Stereo Imaging:** Correlation: `{features.stereo.correlation:.2f}` | Width: `{features.stereo.width:.2f}` | Low-end Width: `{features.stereo.low_end_width:.3f}`",
            f"- **Spectral Profile:** `{features.spectral_profile.classification}` (Centroid: `{features.spectral_profile.spectral_centroid:.0f} Hz`, Rolloff: `{features.spectral_profile.spectral_rolloff:.0f} Hz`)",
            "",
            "## 2. Issues & Prioritized Diagnoses"
        ]

        if not issues:
            lines.append("✓ **No critical mix issues detected. All checks passed.**")
        else:
            for idx, iss in enumerate(issues, 1):
                sev_val = iss.severity.value if hasattr(iss.severity, "value") else str(iss.severity)
                icon = "✗" if sev_val in ("CRITICAL", "HIGH") else "⚠"
                lines.append(f"### {idx}. [{sev_val}] {iss.issue_id} — {iss.category}")
                lines.append(f"{icon} **{iss.description}**")
                lines.append(f"- **Confidence:** `{iss.confidence * 100:.0f}%` | **Roles:** `{', '.join(iss.target_roles)}`")
                if iss.evidence:
                    lines.append(f"- **Evidence:** {'; '.join(iss.evidence)}")
                if iss.probable_causes:
                    lines.append(f"- **Probable Causes:** {'; '.join(iss.probable_causes)}")
                if iss.recommended_actions:
                    lines.append(f"- **Recommended Actions:** {'; '.join(iss.recommended_actions)}")
                lines.append("")

        lines.extend([
            "## 3. Production Health Passes",
            ", ".join(f"`{p}`" for p in lint_results.get("passes", [])) if lint_results.get("passes") else "None"
        ])

        markdown_text = chr(10).join(lines)

        return {
            "section": context.section,
            "genre": context.genre,
            "mix_health_score": health_score,
            "status": overall_status,
            "features": features.to_dict(),
            "issues": [iss.to_dict() for iss in issues],
            "passes": lint_results.get("passes", []),
            "markdown_report": markdown_text
        }

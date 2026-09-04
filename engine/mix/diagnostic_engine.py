"""
Diagnostic Engine: evidence-based causal diagnosis and explanation.
Answers: What is wrong, why, with what physical evidence, and what are the best musical fixes.
"""
from typing import List, Dict, Any, Optional
import numpy as np

from .models import MixIssue, MixContext, AudioFeatures, Severity
from .mix_linter import MixLinter


class DiagnosticEngine:
    """Synthesizes physical DSP evidence into actionable causal diagnoses."""

    @classmethod
    def diagnose(cls, features: AudioFeatures, context: MixContext,
                 kick_audio: Optional[np.ndarray] = None,
                 bass_audio: Optional[np.ndarray] = None) -> List[MixIssue]:
        lint_res = MixLinter.lint_mix(features, context, kick_audio, bass_audio)
        all_issues: List[MixIssue] = []
        
        # Re-instantiate MixIssue objects from lint results
        for item in lint_res["errors"] + lint_res["warnings"] + lint_res["info"]:
            all_issues.append(MixIssue(
                issue_id=item["issue_id"],
                category=item["category"],
                severity=Severity(item["severity"]),
                severity_score=item["severity_score"],
                confidence=item["confidence"],
                target_roles=item["target_roles"],
                description=item["description"],
                evidence=item["evidence"],
                probable_causes=item["probable_causes"],
                recommended_actions=item["recommended_actions"]
            ))

        # Sort priority queue: by severity_score * confidence descending
        all_issues.sort(key=lambda x: x.severity_score * x.confidence, reverse=True)
        return all_issues

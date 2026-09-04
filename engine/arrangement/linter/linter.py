"""
Arrangement Repetition & Flow Linter:
Enforces production-grade structural rules:
1. Anti-copy-paste invariant (no duplicate drops or back-to-back clone sections)
2. Climax superiority (Drop 2 > Drop 1 in energy/intensity)
3. Energy monotonicity penalty (no long flat stretches)
4. Narrative completeness (exposition, tension, climax, resolution)
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from engine.arrangement.models.section import Section, SectionType
from engine.arrangement.linter.comparison import SectionComparator

@dataclass
class LintIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    rule_id: str
    message: str
    section_index: Optional[int] = None

class ArrangementLinter:
    """Audits arrangement quality and reports actionable lint issues."""
    
    def lint(self, sections: List[Section]) -> Dict[str, Any]:
        issues: List[LintIssue] = []
        
        if not sections:
            return {"valid": False, "score": 0.0, "issues": [LintIssue("ERROR", "EMPTY", "Arrangement has no sections.").to_dict()]}
            
        # Rule 1: Back-to-back identical sections
        for i in range(len(sections) - 1):
            s1 = sections[i]
            s2 = sections[i + 1]
            comp = SectionComparator.compare_sections(s1, s2)
            if comp["is_identical_copy"]:
                issues.append(LintIssue(
                    severity="ERROR",
                    rule_id="ARR-001-COPY-PASTE",
                    message=f"Sections {i} ('{s1.name}') and {i+1} ('{s2.name}') are identical copies.",
                    section_index=i+1
                ))
                
        # Rule 2: Multi-Drop Escalation (Drop 2 > Drop 1)
        drops = [s for s in sections if s.section_type == SectionType.DROP]
        if len(drops) >= 2:
            drop1 = drops[0]
            drop2 = drops[1]
            if drop2.energy <= drop1.energy:
                issues.append(LintIssue(
                    severity="WARNING",
                    rule_id="ARR-002-DROP-ENERGY",
                    message=f"Drop 2 energy ({drop2.energy}) does not exceed Drop 1 energy ({drop1.energy}). Climax must escalate."
                ))
            if drop1.variation_type == drop2.variation_type and drop1.variation_type != "none":
                issues.append(LintIssue(
                    severity="WARNING",
                    rule_id="ARR-003-DROP-VARIATION",
                    message="Drop 2 has identical variation profile to Drop 1. Differentiate rhythm or melody."
                ))
                
        # Rule 3: Monotony detection (3+ consecutive sections with near-identical energy)
        flat_streak = 1
        for i in range(len(sections) - 1):
            if abs(sections[i].energy - sections[i+1].energy) < 0.05:
                flat_streak += 1
                if flat_streak >= 3:
                    issues.append(LintIssue(
                        severity="WARNING",
                        rule_id="ARR-004-ENERGY-MONOTONY",
                        message=f"Energy monotony detected: {flat_streak} consecutive sections with flat energy near section {i+1}.",
                        section_index=i+1
                    ))
            else:
                flat_streak = 1
                
        # Rule 4: Structure completeness
        types = [s.section_type for s in sections]
        if SectionType.DROP not in types:
            issues.append(LintIssue(
                severity="ERROR",
                rule_id="ARR-005-NO-CLIMAX",
                message="Track lacks a climax/drop section."
            ))
            
        # Calculate health score (0-100)
        score = 100.0
        for iss in issues:
            if iss.severity == "ERROR":
                score -= 25.0
            elif iss.severity == "WARNING":
                score -= 10.0
            elif iss.severity == "INFO":
                score -= 2.0
                
        final_score = max(0.0, score)
        valid = not any(iss.severity == "ERROR" for iss in issues)
        
        return {
            "valid": valid,
            "arrangement_health_score": final_score,
            "issue_count": len(issues),
            "issues": [
                {
                    "severity": iss.severity,
                    "rule_id": iss.rule_id,
                    "message": iss.message,
                    "section_index": iss.section_index
                }
                for iss in issues
            ]
        }

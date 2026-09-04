"""
Arrangement Quality Scorer:
Scores tension dynamics, contrast, pacing, and overall flow.
"""
from typing import Dict, List, Any
from engine.arrangement.models.section import Section

class ArrangementScorer:
    """Evaluates comprehensive musical arrangement quality."""
    
    @staticmethod
    def score_arrangement(sections: List[Section]) -> Dict[str, Any]:
        if not sections:
            return {"overall_score": 0.0}
            
        energies = [s.energy for s in sections]
        dynamic_range = max(energies) - min(energies)
        
        # Energy contrast score (higher difference between adjacent sections = more dynamic)
        deltas = [abs(energies[i+1] - energies[i]) for i in range(len(energies)-1)]
        avg_delta = sum(deltas) / len(deltas) if deltas else 0.0
        contrast_score = min(100.0, avg_delta * 250.0)
        
        # Pacing score (penalize overly short or overly long sections)
        bars = [s.bars for s in sections]
        pacing_score = 90.0
        for b in bars:
            if b < 4 or b > 64:
                pacing_score -= 10.0
                
        overall = round((contrast_score * 0.5) + (pacing_score * 0.3) + (dynamic_range * 100 * 0.2), 1)
        
        return {
            "overall_score": min(100.0, max(0.0, overall)),
            "contrast_score": round(contrast_score, 1),
            "pacing_score": round(pacing_score, 1),
            "dynamic_range": round(dynamic_range, 2),
            "total_bars": sum(bars)
        }

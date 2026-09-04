"""
Motif Evolution Manager:
Interfaces with Fase 2 Motif Memory to apply algebraic transformations.
"""
from typing import List, Dict, Any

class MotifEvolutionManager:
    """Manages transformed variations of musical motifs for arrangement."""
    
    @staticmethod
    def apply_transformation(notes: List[Dict[str, Any]], technique: str) -> List[Dict[str, Any]]:
        """Applies algorithmic transformations to a list of note dicts."""
        if not notes:
            return []
            
        transformed = [dict(n) for n in notes]
        
        if technique == "octave_shift":
            for n in transformed:
                n["pitch"] = min(127, n.get("pitch", 60) + 12)
                
        elif technique == "retrograde":
            # Reverse order of pitches while keeping rhythm timing
            pitches = [n.get("pitch", 60) for n in transformed]
            pitches.reverse()
            for i, p in enumerate(pitches):
                transformed[i]["pitch"] = p
                
        elif technique == "inversion":
            # Invert pitch contour around first pitch
            if transformed:
                pivot = transformed[0].get("pitch", 60)
                for n in transformed:
                    interval = n.get("pitch", 60) - pivot
                    n["pitch"] = max(0, min(127, pivot - interval))
                    
        elif technique == "diminution":
            # Halve durations and times (double speed)
            for n in transformed:
                n["time"] = n.get("time", 0.0) * 0.5
                n["duration"] = max(0.125, n.get("duration", 0.25) * 0.5)
                
        elif technique == "augmentation":
            # Double durations and times (half speed)
            for n in transformed:
                n["time"] = n.get("time", 0.0) * 2.0
                n["duration"] = n.get("duration", 0.25) * 2.0
                
        return transformed

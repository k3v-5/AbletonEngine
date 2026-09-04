# engine/instruments/library/resolver.py
import os
import re
import glob
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from ..roles import InstrumentRole

@dataclass
class SampleCandidate:
    path: str
    filename: str
    role: InstrumentRole
    confidence: float
    style_match: float
    character_match: float
    is_fallback: bool = False
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "filename": self.filename,
            "role": self.role.value if isinstance(self.role, InstrumentRole) else str(self.role),
            "confidence": round(self.confidence, 3),
            "style_match": round(self.style_match, 3),
            "character_match": round(self.character_match, 3),
            "is_fallback": self.is_fallback,
            "warning": self.warning
        }

class SampleLibraryResolver:
    """Intelligent scanner, semantic indexer and sample resolver for local sample libraries."""
    
    ROLE_KEYWORDS: Dict[str, List[str]] = {
        "KICK": ["kick", "bd", "bombo", "bassdrum", "kck", "sub_kick", "deep_kick"],
        "KICK_ALT": ["kick2", "kick_alt", "rumble", "sub_kick"],
        "SNARE": ["snare", "sd", "caja", "snr", "rimshot"],
        "CLAP": ["clap", "cp", "palmas", "handclap", "snap"],
        "CLOSED_HAT": ["closed_hat", "ch", "closed_hihat", "cl_hat", "hat_closed", "hihat_closed", "hat1", "hihat"],
        "OPEN_HAT": ["open_hat", "oh", "open_hihat", "op_hat", "hat_open", "hihat_open", "ride"],
        "PERCUSSION": ["perc", "percussion", "rim", "bongo", "conga", "wood", "click", "stick"],
        "PERC_1": ["perc1", "perc_1", "wood", "rim", "click", "perc"],
        "PERC_2": ["perc2", "perc_2", "metal", "bell", "clang", "synth_perc"],
        "SHAKER": ["shaker", "shk", "maraca", "tambourine"],
        "TOM": ["tom", "floor_tom", "low_tom", "high_tom"],
        "FX": ["fx", "sweep", "laser", "riser", "noise", "downlifter", "uplifter", "glitch"],
        "IMPACT": ["impact", "sub_drop", "boom", "hit", "crash"],
        "VOCAL_CHOP": ["vocal", "vox", "chop", "chant"],
    }

    # Audio file extensions
    AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg")

    def __init__(self, sample_roots: Optional[List[str]] = None):
        self.sample_roots = sample_roots or [
            r"D:\Documentos\Librerias FL Studio",
            r"D:\Documentos\Ableton\User Library\Samples",
            r"D:\Programs\Ableton\Live 12 Suite\Resources\Core Library"
        ]
        self._cache: List[str] = []
        self._is_indexed: bool = False

    def ensure_index(self, max_files: int = 50000):
        """Scans sample roots and indexes available audio files quickly"""
        if self._is_indexed and self._cache:
            return
        
        found = []
        for root in self.sample_roots:
            if not os.path.exists(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for f in filenames:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in self.AUDIO_EXTENSIONS:
                        found.append(os.path.join(dirpath, f))
                        if len(found) >= max_files:
                            break
                if len(found) >= max_files:
                    break
        self._cache = found
        self._is_indexed = True

    def find_samples(
        self,
        role: str,
        style: str = "",
        character: str = "",
        max_results: int = 10
    ) -> List[SampleCandidate]:
        """Search and rank samples for a given role, style and character without loading anything"""
        self.ensure_index()
        role_clean = role.strip().upper()
        keywords = self.ROLE_KEYWORDS.get(role_clean, [role_clean.lower()])
        style_keywords = [s.strip().lower() for s in style.replace("-", "_").split("_") if s]
        char_keywords = [c.strip().lower() for c in character.replace("-", "_").split("_") if c]

        candidates: List[SampleCandidate] = []

        for full_path in self._cache:
            path_lower = full_path.lower()
            fname_lower = os.path.basename(path_lower)
            
            # Role matching score
            role_score = 0.0
            for kw in keywords:
                if kw in fname_lower:
                    role_score = max(role_score, 0.85)
                elif kw in path_lower:
                    role_score = max(role_score, 0.55)

            # Negative filter: avoid confusing open vs closed hat or kick vs snare
            if role_clean == "CLOSED_HAT" and ("open" in fname_lower or " oh" in fname_lower or "_oh" in fname_lower):
                role_score = 0.0
            if role_clean == "OPEN_HAT" and ("closed" in fname_lower or " ch" in fname_lower or "_ch" in fname_lower):
                role_score = 0.0
            if role_clean == "KICK" and ("snare" in fname_lower or "clap" in fname_lower):
                role_score = 0.0

            if role_score <= 0.2:
                continue

            # Style matching score
            style_score = 0.5
            if style_keywords:
                matched_style = sum(1 for sk in style_keywords if sk in path_lower)
                style_score = min(1.0, 0.5 + 0.25 * matched_style)

            # Character matching score
            char_score = 0.5
            if char_keywords:
                matched_char = sum(1 for ck in char_keywords if ck in fname_lower or ck in path_lower)
                char_score = min(1.0, 0.5 + 0.25 * matched_char)

            # Total confidence (weighted harmonic mean)
            confidence = (role_score * 0.55) + (style_score * 0.25) + (char_score * 0.20)

            candidates.append(SampleCandidate(
                path=full_path,
                filename=os.path.basename(full_path),
                role=InstrumentRole.from_str(role_clean),
                confidence=confidence,
                style_match=style_score,
                character_match=char_score
            ))

        # Sort candidates descending by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        if candidates:
            return candidates[:max_results]

        # Fallback handling if no direct match was found
        return self._generate_fallback(role_clean, style, character)

    def _generate_fallback(self, role: str, style: str, character: str) -> List[SampleCandidate]:
        """Provides a safe, explicit fallback sample if preferred match is unavailable"""
        self.ensure_index()
        role_clean = role.strip().upper()
        keywords = self.ROLE_KEYWORDS.get(role_clean, [role_clean.lower()])

        for full_path in self._cache:
            p_lower = full_path.lower()
            if any(kw in p_lower for kw in keywords):
                return [SampleCandidate(
                    path=full_path,
                    filename=os.path.basename(full_path),
                    role=InstrumentRole.from_str(role_clean),
                    confidence=0.50,
                    style_match=0.30,
                    character_match=0.30,
                    is_fallback=True,
                    warning=f"Preferred {role_clean} sample not found; generic fallback applied."
                )]

        # If completely empty library, return a virtual native Ableton Simpler / preset fallback
        return [SampleCandidate(
            path=f"query:Drums#{role_clean}",
            filename=f"Live_BuiltIn_{role_clean}",
            role=InstrumentRole.from_str(role_clean),
            confidence=0.40,
            style_match=0.20,
            character_match=0.20,
            is_fallback=True,
            warning=f"No local sample found for {role_clean}; Ableton native preset fallback provided."
        )]

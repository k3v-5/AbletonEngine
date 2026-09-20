"""
Role Classifier and Semantic Taxonomy Engine:
Centralized single-source-of-truth for track acoustic role detection,
prioritizing kick over sub-bass/808, and providing bidirectional role aliases.
"""

import re
from enum import Enum
from typing import Optional, List, Any, Dict


class CanonicalRole(str, Enum):
    KICK = "KICK"
    SUB = "SUB"
    BASS = "BASS"
    SNARE = "SNARE"
    HI_HATS = "HI_HATS"
    PERCUSSION = "PERCUSSION"
    DRUMS = "DRUMS"
    BREAK = "BREAK"
    KEYS = "KEYS"
    PAD = "PAD"
    LEAD = "LEAD"
    COUNTER_LEAD = "COUNTER_LEAD"
    EAR_CANDY = "EAR_CANDY"
    TEXTURE_FOLEY = "TEXTURE_FOLEY"
    VOCALS = "VOCALS"
    FOLEY = "FOLEY"
    FX = "FX"
    OTHER = "OTHER"


class RoleClassifier:
    """
    Unified deterministic classifier for audio and MIDI tracks.
    Enforces strict priority (e.g. Kick > 808/Bass > Percussion).
    """

    ROLE_ALIASES: Dict[str, str] = {
        "PLUCK": "KEYS",
        "CHORD": "KEYS",
        "CHORDS": "KEYS",
        "PIANO": "KEYS",
        "RHODES": "KEYS",
        "SUB": "BASS",
        "808": "BASS",
        "SYNTH": "LEAD",
        "SOLO": "LEAD",
        "TOPLINE": "LEAD",
        "COUNTER_LEAD": "COUNTER_LEAD",
        "COUNTERLEAD": "COUNTER_LEAD",
        "COUNTER_MELODY": "COUNTER_LEAD",
        "ARP": "COUNTER_LEAD",
        "ARPS": "COUNTER_LEAD",
        "ARPEGGIO": "COUNTER_LEAD",
        "EAR_CANDY": "EAR_CANDY",
        "EARCANDY": "EAR_CANDY",
        "TEXTURE": "TEXTURE_FOLEY",
        "TEXTURE_FOLEY": "TEXTURE_FOLEY",
        "STRINGS": "PAD",
        "STRING": "PAD",
        "ATMOS": "PAD",
        "AMBIENT": "PAD",
        "VOX": "VOCALS",
        "VOZ": "VOCALS",
        "LEAD_VOCAL": "VOCALS",
        "HAT": "HI_HATS",
        "HIHAT": "HI_HATS",
        "CLAP": "SNARE",
        "CAJA": "SNARE",
        "TAROLA": "SNARE",
        "BOMBO": "KICK",
    }

    @classmethod
    def normalize_role(cls, role: Optional[str]) -> str:
        """Normalizes role name against known aliases."""
        if not role:
            return "OTHER"
        cleaned = str(role).strip().upper().replace(" ", "_").replace("-", "_")
        return cls.ROLE_ALIASES.get(cleaned, cleaned)

    @classmethod
    def classify(cls, track_name: str, devices: Optional[List[Any]] = None, fallback_role: str = "") -> CanonicalRole:
        """
        Deterministically classifies a track into a CanonicalRole based on
        track name, device chain strings, and fallback role.
        """
        tn = str(track_name or "").lower().strip()
        dev_str = " ".join([str(d).lower() for d in (devices or [])])
        full = f"{tn} {dev_str}".strip()

        # 1. KICK (Priority 1: Must match before 808/Bass)
        if "kick" in full or "bombo" in full or re.search(r"\bbd\b", full):
            return CanonicalRole.KICK

        # 2. SUB / BASS / 808
        if any(w in full for w in ["808", "bass", "bajo", "sub", "sublab", "trilian", "reese"]):
            if "sub" in full and not any(w in full for w in ["bass", "bajo", "808"]):
                return CanonicalRole.SUB
            return CanonicalRole.BASS

        # 3. SNARE / CLAP
        if any(w in full for w in ["snare", "caja", "clap", "tarola", "rim"]):
            return CanonicalRole.SNARE

        # 4. HI-HATS / CYMBALS
        if any(w in full for w in ["hat", "hihat", "cymbal", "ride", "crash"]) or re.search(r"\bhh\b", full):
            return CanonicalRole.HI_HATS

        # 5. BREAKS / LOOPS
        if "break" in full or "sliced break" in full or "amen" in full:
            return CanonicalRole.BREAK

        # 6. VOCALS
        if any(w in full for w in ["vocal", "vox", "voz", "vocals", "lead vocal", "hook", "chop"]):
            return CanonicalRole.VOCALS

        # 7. DRUMS / PERCUSSION
        if any(w in full for w in ["perc", "shaker", "tom", "bongo", "conga"]):
            return CanonicalRole.PERCUSSION
        if any(w in full for w in ["drum", "kit", "warehouse", "bateria"]):
            return CanonicalRole.DRUMS

        # 8. KEYS / PIANO
        if any(w in full for w in ["piano", "key", "rhodes", "epiano", "teclado", "chord", "chords"]):
            return CanonicalRole.KEYS

        # 9. PAD / STRINGS / ATMOSPHERE
        if any(w in full for w in ["pad", "string", "cuerda", "atmos", "ambient", "colchon"]):
            return CanonicalRole.PAD

        # 10. COUNTER_LEAD / ARPS
        if any(w in full for w in ["counter", "counter lead", "counter_lead", "counter melody", "arp", "arps", "arpeggio"]):
            return CanonicalRole.COUNTER_LEAD

        # 11. LEAD / SYNTH / GUITAR
        if any(w in full for w in ["lead", "pluck", "topline", "guitar", "guitarra", "solo", "synth"]):
            return CanonicalRole.LEAD

        # 12. TEXTURE / FOLEY
        if any(w in full for w in ["texture", "foley", "rain", "vinyl", "murmur", "ruido", "noise", "room"]):
            return CanonicalRole.TEXTURE_FOLEY

        # 13. EAR CANDY / FX
        if any(w in full for w in ["candy", "ear candy", "ear_candy"]):
            return CanonicalRole.EAR_CANDY
        if any(w in full for w in ["fx", "riser", "sweep", "impact", "downlifter", "uplifter"]):
            return CanonicalRole.FX

        # Fallback to metadata role if supplied
        if fallback_role:
            norm_fb = cls.normalize_role(fallback_role)
            try:
                return CanonicalRole(norm_fb)
            except ValueError:
                pass

        return CanonicalRole.OTHER

    @classmethod
    def classify_for_auto_stager(cls, track_name: str, devices: Optional[List[Any]] = None) -> str:
        """
        Adapter method for AutoGainStager HIERARCHY_TARGETS mapping.
        Returns: 'kick', 'bass', 'snare', 'break', 'drums', 'piano', 'pad', 'lead', 'counter_lead', 'ear_candy', 'vocal', 'foley', 'synth', etc.
        """
        role = cls.classify(track_name, devices)
        if role == CanonicalRole.KICK:
            return "kick"
        elif role in (CanonicalRole.BASS, CanonicalRole.SUB):
            return "bass"
        elif role == CanonicalRole.SNARE:
            return "snare"
        elif role == CanonicalRole.BREAK:
            return "break"
        elif role in (CanonicalRole.DRUMS, CanonicalRole.HI_HATS, CanonicalRole.PERCUSSION):
            return "drums"
        elif role == CanonicalRole.KEYS:
            return "piano"
        elif role == CanonicalRole.PAD:
            return "pad"
        elif role == CanonicalRole.COUNTER_LEAD:
            return "counter_lead"
        elif role == CanonicalRole.EAR_CANDY:
            return "ear_candy"
        elif role in (CanonicalRole.FOLEY, CanonicalRole.TEXTURE_FOLEY):
            return "foley"
        elif role == CanonicalRole.VOCALS:
            return "vocal"
        elif role == CanonicalRole.FX:
            return "fx"
        
        tn = str(track_name).lower()
        if "synth" in tn:
            return "synth"
        return "lead"

    @classmethod
    def classify_for_panning(cls, name: str, role: str = "") -> str:
        """
        Adapter method for SpatialPanner pan spread classification.
        """
        canonical = cls.classify(name, fallback_role=role)
        if canonical == CanonicalRole.KICK:
            return "KICK"
        elif canonical == CanonicalRole.SUB:
            return "SUB"
        elif canonical == CanonicalRole.BASS:
            return "BASS"
        elif canonical == CanonicalRole.VOCALS:
            return "VOCALS"
        elif canonical == CanonicalRole.SNARE:
            return "SNARE"
        elif canonical == CanonicalRole.HI_HATS:
            return "HI_HATS"
        elif canonical == CanonicalRole.PERCUSSION:
            return "PERCUSSION"
        elif canonical == CanonicalRole.KEYS:
            return "KEYS"
        elif canonical == CanonicalRole.LEAD:
            return "LEAD"
        elif canonical == CanonicalRole.COUNTER_LEAD:
            return "COUNTER_LEAD"
        elif canonical == CanonicalRole.EAR_CANDY:
            return "EAR_CANDY"
        elif canonical == CanonicalRole.TEXTURE_FOLEY:
            return "TEXTURE_FOLEY"
        elif canonical == CanonicalRole.PAD:
            return "PAD"
        elif canonical == CanonicalRole.DRUMS or canonical == CanonicalRole.BREAK:
            return "DRUMS"
        elif canonical in (CanonicalRole.FX, CanonicalRole.FOLEY):
            return "EAR_CANDY"
        return str(role).upper() if role else "INSTRUMENT"


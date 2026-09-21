# engine/sound_design/signature_sound_generator.py
"""
Signature Sound Generator (Gen 2):
Enforces the artistic law: Every song must possess between 1 and 3 Signature Sounds (never more).
Binds the unique signature material to the song's SonicDNA and tracks its multi-section
evolution across the timeline via SonicMotifMemory.
"""
from __future__ import annotations
import uuid
import hashlib
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("SignatureSoundGenerator")


@dataclass
class SignatureAppearance:
    """A specific narrative occurrence of a signature sound in the timeline."""
    section: str
    bars: Tuple[int, int]
    life_stage: str        # BIRTH, DEVELOPMENT, CLIMAX, DECAY
    form_variation: str    # e.g. "filtered 400Hz HPF", "unfiltered full stereo", "tape relic"
    narrative_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "bars": list(self.bars),
            "life_stage": self.life_stage,
            "form_variation": self.form_variation,
            "narrative_reason": self.narrative_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureAppearance:
        b = data.get("bars", [1, 8])
        return cls(
            section=data.get("section", "Hook 1"),
            bars=(int(b[0]), int(b[1])),
            life_stage=data.get("life_stage", "BIRTH"),
            form_variation=data.get("form_variation", ""),
            narrative_reason=data.get("narrative_reason", ""),
        )


@dataclass
class SignatureSoundRecord:
    """A registered signature sound unique to this song."""
    signature_id: str
    name: str
    song_id: str
    source_stem_desc: str
    mutation_pipeline_desc: str
    role: str  # TRANSITION, BASS_ACCENT, EAR_CANDY, CLIMAX_PAYOFF
    appearances: List[SignatureAppearance] = field(default_factory=list)
    recipe_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature_id": self.signature_id,
            "name": self.name,
            "song_id": self.song_id,
            "source_stem_desc": self.source_stem_desc,
            "mutation_pipeline_desc": self.mutation_pipeline_desc,
            "role": self.role,
            "appearances": [a.to_dict() for a in self.appearances],
            "recipe_hash": self.recipe_hash,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureSoundRecord:
        return cls(
            signature_id=data.get("signature_id", "SIG_1"),
            name=data.get("name", "Signature Sound"),
            song_id=data.get("song_id", "default_song"),
            source_stem_desc=data.get("source_stem_desc", ""),
            mutation_pipeline_desc=data.get("mutation_pipeline_desc", ""),
            role=data.get("role", "TRANSITION"),
            appearances=[SignatureAppearance.from_dict(a) for a in data.get("appearances", [])],
            recipe_hash=data.get("recipe_hash", ""),
            created_at=data.get("created_at", ""),
        )


class SignatureSoundRegistry:
    """
    Manages and guards the signature sounds for a song.
    Enforces the strict quota: minimum 1, maximum 3 signature sounds per song.
    """

    MIN_SIGNATURE_COUNT = 1
    MAX_SIGNATURE_COUNT = 3

    def __init__(self, song_id: str = "default_song"):
        self.song_id = song_id
        self.signatures: Dict[str, SignatureSoundRecord] = {}

    def can_register(self) -> bool:
        return len(self.signatures) < self.MAX_SIGNATURE_COUNT

    def register_signature(
        self,
        name: str,
        source_stem_desc: str,
        mutation_desc: str,
        role: str,
        appearances: List[SignatureAppearance]
    ) -> Tuple[bool, Optional[SignatureSoundRecord], Optional[str]]:
        """
        Attempts to register a new signature sound under the quota rule.
        """
        if not self.can_register():
            return False, None, f"Límite de cuota alcanzado: Máximo de {self.MAX_SIGNATURE_COUNT} Signature Sounds por canción."

        # Compute deterministic recipe hash
        raw_token = f"{self.song_id}_{name}_{source_stem_desc}_{mutation_desc}"
        r_hash = hashlib.sha256(raw_token.encode()).hexdigest()[:12]
        sig_id = f"SIG_{len(self.signatures) + 1}_{r_hash[:6]}"

        record = SignatureSoundRecord(
            signature_id=sig_id,
            name=name,
            song_id=self.song_id,
            source_stem_desc=source_stem_desc,
            mutation_pipeline_desc=mutation_desc,
            role=role,
            appearances=appearances,
            recipe_hash=r_hash,
        )
        self.signatures[sig_id] = record
        return True, record, None

    def validate_quota(self) -> Dict[str, Any]:
        """
        Audits if the song fulfills the 1 to 3 signature sound requirement.
        """
        count = len(self.signatures)
        is_compliant = self.MIN_SIGNATURE_COUNT <= count <= self.MAX_SIGNATURE_COUNT

        return {
            "signature_count": count,
            "min_required": self.MIN_SIGNATURE_COUNT,
            "max_allowed": self.MAX_SIGNATURE_COUNT,
            "is_compliant": is_compliant,
            "verdict": "OPTIMAL_IDENTITY" if is_compliant else ("MISSING_SIGNATURE" if count == 0 else "EXCESSIVE_SIGNATURES"),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "signatures": {k: v.to_dict() for k, v in self.signatures.items()},
            "quota_audit": self.validate_quota(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureSoundRegistry:
        reg = cls(song_id=data.get("song_id", "default_song"))
        sigs = data.get("signatures", {})
        for k, v in sigs.items():
            reg.signatures[k] = SignatureSoundRecord.from_dict(v)
        return reg

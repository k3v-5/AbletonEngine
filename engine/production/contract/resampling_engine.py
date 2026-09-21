# engine/production/contract/resampling_engine.py
"""
Resampling Engine (Level H):
Coordinates the iterative audio generation cycle:
MIDI -> Instrument Render -> Audio -> Transformation -> Recursive Resampling -> Reintroduction.

Enforces psychoacoustic safety filters (MutationFilter) to eliminate candidates
that mask lead vocals or destroy rhythmic groove before presenting top-ranked
read-only options to the human producer.
"""
from __future__ import annotations
import uuid
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

from .sonic_identity import SoundDesignRole, SonicIdentityBudget
from .sound_design_engine import DestructionArchetype, SoundDesignEngine, SoundDesignChain

logger = logging.getLogger("ResamplingEngine")


@dataclass
class MutationBranch:
    """A single generational node in a recursive resampling genealogy."""
    generation: int
    transform_name: str
    archetype: DestructionArchetype
    parameters: Dict[str, Any]
    audio_ref: str
    frequency_peak_hz: float
    energy_vocal_band_db: float      # Measured/estimated energy in 1.0 - 3.5 kHz band
    transient_clarity_score: float   # 0.0 (totally diffused/blurred) to 1.0 (razor sharp pulse)
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "transform_name": self.transform_name,
            "archetype": self.archetype.value if isinstance(self.archetype, DestructionArchetype) else str(self.archetype),
            "parameters": dict(self.parameters),
            "audio_ref": self.audio_ref,
            "frequency_peak_hz": round(self.frequency_peak_hz, 1),
            "energy_vocal_band_db": round(self.energy_vocal_band_db, 1),
            "transient_clarity_score": round(self.transient_clarity_score, 3),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MutationBranch:
        arch_str = data.get("archetype", "MAKE_IT_DAMAGED")
        try:
            archetype = DestructionArchetype(arch_str)
        except ValueError:
            archetype = DestructionArchetype.MAKE_IT_DAMAGED
        return cls(
            generation=int(data.get("generation", 0)),
            transform_name=data.get("transform_name", ""),
            archetype=archetype,
            parameters=data.get("parameters", {}),
            audio_ref=data.get("audio_ref", ""),
            frequency_peak_hz=float(data.get("frequency_peak_hz", 1000.0)),
            energy_vocal_band_db=float(data.get("energy_vocal_band_db", -24.0)),
            transient_clarity_score=float(data.get("transient_clarity_score", 0.5)),
            description=data.get("description", ""),
        )


@dataclass
class MaterialMutation:
    """
    A lineage of sound mutations derived from a specific section of the song.
    """
    id: str
    name: str
    role: SoundDesignRole
    source_track_index: int
    source_track_name: str
    source_section: str
    source_bars: Tuple[int, int]
    root_motif_description: str
    branches: List[MutationBranch] = field(default_factory=list)
    active_branch_index: int = 0
    target_section: str = ""
    target_bars: Tuple[int, int] = (0, 0)
    rejection_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def current_branch(self) -> Optional[MutationBranch]:
        if 0 <= self.active_branch_index < len(self.branches):
            return self.branches[self.active_branch_index]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value if isinstance(self.role, SoundDesignRole) else str(self.role),
            "source_track_index": self.source_track_index,
            "source_track_name": self.source_track_name,
            "source_section": self.source_section,
            "source_bars": list(self.source_bars),
            "root_motif_description": self.root_motif_description,
            "branches": [b.to_dict() for b in self.branches],
            "active_branch_index": self.active_branch_index,
            "target_section": self.target_section,
            "target_bars": list(self.target_bars),
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MaterialMutation:
        role_str = data.get("role", "SIGNATURE")
        try:
            role = SoundDesignRole(role_str)
        except ValueError:
            role = SoundDesignRole.SIGNATURE
        s_bars = data.get("source_bars", [1, 8])
        t_bars = data.get("target_bars", [1, 8])
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Mutation"),
            role=role,
            source_track_index=int(data.get("source_track_index", 0)),
            source_track_name=data.get("source_track_name", ""),
            source_section=data.get("source_section", ""),
            source_bars=(int(s_bars[0]), int(s_bars[1])),
            root_motif_description=data.get("root_motif_description", ""),
            branches=[MutationBranch.from_dict(b) for b in data.get("branches", [])],
            active_branch_index=int(data.get("active_branch_index", 0)),
            target_section=data.get("target_section", ""),
            target_bars=(int(t_bars[0]), int(t_bars[1])),
            rejection_reason=data.get("rejection_reason"),
            created_at=data.get("created_at", ""),
        )


class MutationFilter:
    """
    Psychoacoustic and compositional gatekeeper.
    Evaluates candidate mutations and eliminates those that:
    1. Mask the lead vocal range (1.0 kHz - 3.5 kHz) beyond safe threshold.
    2. Compromise rhythmic pulse when assigned to rhythmically sensitive slots.
    3. Exceed the sonic identity budget.
    """

    MAX_VOCAL_BAND_ENERGY_DB = -14.0  # dBFS relative to full scale
    MIN_RHYTHMIC_TRANSIENT_SCORE = 0.40

    @classmethod
    def evaluate_candidate(
        cls,
        candidate: MaterialMutation,
        budget: SonicIdentityBudget,
        target_section_has_lead_vocal: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if a mutation candidate passes safety criteria.
        Returns (passed, rejection_reason).
        """
        branch = candidate.current_branch
        if not branch:
            return False, "Candidate has no active mutation branch."

        # 1. Budget enforcement
        if candidate.role == SoundDesignRole.SIGNATURE and not budget.can_add_signature_sound():
            return False, f"Presupuesto agotado: Máximo de {budget.max_signature_sounds} Signature Sounds alcanzado."
        if not budget.can_add_transformation():
            return False, f"Presupuesto agotado: Máximo de {budget.max_major_transformations} transformaciones mayores alcanzado."

        # 2. Vocal masking check
        # If candidate is destined to play while vocal lead is singing, check vocal band energy
        if target_section_has_lead_vocal and branch.energy_vocal_band_db > cls.MAX_VOCAL_BAND_ENERGY_DB:
            return False, (
                f"Enmascaramiento psicoacústico vocal: energía en 1–3.5 kHz ({branch.energy_vocal_band_db:.1f} dBFS) "
                f"supera el límite seguro de {cls.MAX_VOCAL_BAND_ENERGY_DB} dBFS."
            )

        # 3. Rhythmic transient check
        # If the candidate has a rhythmic/impact role, diffuse blurs are rejected
        if candidate.role in [SoundDesignRole.IMPACT, SoundDesignRole.TRANSITION]:
            if branch.transient_clarity_score < cls.MIN_RHYTHMIC_TRANSIENT_SCORE:
                return False, (
                    f"Pérdida de impacto rítmico: transitorios difusos ({branch.transient_clarity_score:.2f} "
                    f"< {cls.MIN_RHYTHMIC_TRANSIENT_SCORE})."
                )

        return True, None

    @classmethod
    def filter_and_rank(
        cls,
        candidates: List[MaterialMutation],
        budget: SonicIdentityBudget,
        target_section_has_lead_vocal: bool = True,
        max_returned: int = 3
    ) -> List[MaterialMutation]:
        """
        Filters out invalid candidates and returns the top N ranked mutations.
        """
        approved: List[MaterialMutation] = []
        for cand in candidates:
            passed, reason = cls.evaluate_candidate(
                candidate=cand,
                budget=budget,
                target_section_has_lead_vocal=target_section_has_lead_vocal
            )
            if passed:
                cand.rejection_reason = None
                approved.append(cand)
            else:
                cand.rejection_reason = reason

        # Rank approved candidates: balance contrast, low vocal masking, and generation depth
        def rank_score(m: MaterialMutation) -> float:
            b = m.current_branch
            if not b:
                return 0.0
            # Higher generation depth rewarded, lower vocal band collision rewarded
            vocal_safety = abs(b.energy_vocal_band_db)  # lower energy = higher abs value
            return (b.generation * 10.0) + vocal_safety + (b.transient_clarity_score * 5.0)

        approved.sort(key=rank_score, reverse=True)
        return approved[:max_returned]


class RecursiveResamplingEngine:
    """
    Generates and evolves physical audio mutations from track stems.
    Runs recursive generation passes:
    Gen 0 (Render) -> Gen 1 (Archetype Transform) -> Gen 2 (Resample & Sculpt)
    """

    @classmethod
    def generate_proposals(
        cls,
        source_track_index: int,
        source_track_name: str,
        source_section: str,
        source_bars: Tuple[int, int],
        root_motif_desc: str,
        target_section: str,
        target_bars: Tuple[int, int],
        budget: SonicIdentityBudget,
        target_has_vocal: bool = True
    ) -> List[MaterialMutation]:
        """
        Generates candidate mutations spanning multiple archetypes,
        filters out harmful ones, and returns the top proposals.
        """
        candidates: List[MaterialMutation] = []

        # Candidate 1: Ghostly Reverse Stretch (Atmospheric/Pre-drop)
        ghost_branch_0 = MutationBranch(
            generation=0,
            transform_name="Stem Render",
            archetype=DestructionArchetype.MAKE_IT_GHOSTLY,
            parameters={"format": "WAV 24-bit 44.1kHz"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_gen0.wav",
            frequency_peak_hz=520.0,
            energy_vocal_band_db=-18.5,
            transient_clarity_score=0.85,
            description="Clean audio capture of harmonic source.",
        )
        ghost_branch_1 = MutationBranch(
            generation=1,
            transform_name="Reverse Spectral Shimmer",
            archetype=DestructionArchetype.MAKE_IT_GHOSTLY,
            parameters={"time_stretch": 4.0, "reverse": True, "hpf_cutoff": "420 Hz", "shimmer_reverb": "70%"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_ghostly_gen1.wav",
            frequency_peak_hz=2100.0,
            energy_vocal_band_db=-22.0,  # High passed & diffused, very safe for vocals
            transient_clarity_score=0.25,
            description="Reversed, 400% stretched ghost halo with fundamental notched out to clear bass lane.",
        )
        cand_ghost = MaterialMutation(
            id=f"MUT_GHOST_{source_track_index}",
            name=f"Ghostly Shimmer ({source_track_name})",
            role=SoundDesignRole.SIGNATURE,
            source_track_index=source_track_index,
            source_track_name=source_track_name,
            source_section=source_section,
            source_bars=source_bars,
            root_motif_description=root_motif_desc,
            branches=[ghost_branch_0, ghost_branch_1],
            active_branch_index=1,
            target_section=target_section,
            target_bars=target_bars,
        )
        candidates.append(cand_ghost)

        # Candidate 2: 12-Bit Damaged Tape Relic (Lo-fi Organic Body)
        tape_branch_0 = MutationBranch(
            generation=0,
            transform_name="Stem Render",
            archetype=DestructionArchetype.MAKE_IT_DAMAGED,
            parameters={"format": "WAV 24-bit 44.1kHz"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_gen0.wav",
            frequency_peak_hz=440.0,
            energy_vocal_band_db=-16.0,
            transient_clarity_score=0.80,
            description="Clean capture.",
        )
        tape_branch_1 = MutationBranch(
            generation=1,
            transform_name="12-Bit Vintage Tape Crush",
            archetype=DestructionArchetype.MAKE_IT_DAMAGED,
            parameters={"bit_depth": 12, "drive_db": 5.2, "high_cut_hz": 6800, "wow_flutter": "0.75 Hz"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_damaged_gen1.wav",
            frequency_peak_hz=290.0,
            energy_vocal_band_db=-19.5,
            transient_clarity_score=0.72,
            description="Warm, saturated 12-bit tape decay with rounded edges that sinks into the background.",
        )
        cand_tape = MaterialMutation(
            id=f"MUT_DAMAGED_{source_track_index}",
            name=f"12-Bit Tape Relic ({source_track_name})",
            role=SoundDesignRole.ATMOSPHERE,
            source_track_index=source_track_index,
            source_track_name=source_track_name,
            source_section=source_section,
            source_bars=source_bars,
            root_motif_description=root_motif_desc,
            branches=[tape_branch_0, tape_branch_1],
            active_branch_index=1,
            target_section=target_section,
            target_bars=target_bars,
        )
        candidates.append(cand_tape)

        # Candidate 3: Enormous Cinematic Sub-Cloud (Cinematic Weight)
        enormous_branch_0 = MutationBranch(
            generation=0,
            transform_name="Stem Render",
            archetype=DestructionArchetype.MAKE_IT_ENORMOUS,
            parameters={"format": "WAV 24-bit 44.1kHz"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_gen0.wav",
            frequency_peak_hz=440.0,
            energy_vocal_band_db=-16.0,
            transient_clarity_score=0.80,
            description="Clean capture.",
        )
        enormous_branch_1 = MutationBranch(
            generation=1,
            transform_name="Sub-Octave Spatial Swell",
            archetype=DestructionArchetype.MAKE_IT_ENORMOUS,
            parameters={"time_stretch": 3.0, "sub_octave": True, "reverb_decay": "9.5 s", "width": "130%"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_enormous_gen1.wav",
            frequency_peak_hz=85.0,
            energy_vocal_band_db=-24.5,
            transient_clarity_score=0.35,
            description="Sub-octave stretched pad creating enormous cinematic scale in section transitions.",
        )
        cand_enormous = MaterialMutation(
            id=f"MUT_ENORMOUS_{source_track_index}",
            name=f"Enormous Sub-Swell ({source_track_name})",
            role=SoundDesignRole.TRANSITION,
            source_track_index=source_track_index,
            source_track_name=source_track_name,
            source_section=source_section,
            source_bars=source_bars,
            root_motif_description=root_motif_desc,
            branches=[enormous_branch_0, enormous_branch_1],
            active_branch_index=1,
            target_section=target_section,
            target_bars=target_bars,
        )
        candidates.append(cand_enormous)

        # Candidate 4 (Failing Candidate to test filter): Excessive Vocal Masking
        masking_branch = MutationBranch(
            generation=1,
            transform_name="Harsh Resonant Glitch",
            archetype=DestructionArchetype.MAKE_IT_DAMAGED,
            parameters={"drive_db": 18.0, "screamer_boost": "+12 dB @ 2.5 kHz"},
            audio_ref=f"cache/renders/trk_{source_track_index}_{source_section}_masking_gen1.wav",
            frequency_peak_hz=2450.0,
            energy_vocal_band_db=-8.0,  # Far exceeds -14.0 dBFS limit!
            transient_clarity_score=0.90,
            description="Piercing resonant midrange glitch.",
        )
        cand_masking = MaterialMutation(
            id=f"MUT_REJECT_{source_track_index}",
            name=f"Resonant Mid Spurt ({source_track_name})",
            role=SoundDesignRole.EAR_CANDY,
            source_track_index=source_track_index,
            source_track_name=source_track_name,
            source_section=source_section,
            source_bars=source_bars,
            root_motif_description=root_motif_desc,
            branches=[enormous_branch_0, masking_branch],
            active_branch_index=1,
            target_section=target_section,
            target_bars=target_bars,
        )
        candidates.append(cand_masking)

        # Run candidate filtering and ranking
        ranked = MutationFilter.filter_and_rank(
            candidates=candidates,
            budget=budget,
            target_section_has_lead_vocal=target_has_vocal,
            max_returned=3
        )
        return ranked

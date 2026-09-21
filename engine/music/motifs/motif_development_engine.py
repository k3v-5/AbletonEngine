# engine/music/motifs/motif_development_engine.py
"""
Motif Development Engine (Level K - Motif Development):
Transforms foundational musical motifs across 4 cardinal dimensions:
1. Rhythmic: Augmentation, Diminution, Displacement, Syncopation Infill.
2. Pitch & Modal: Diatonic Inversion, Interpolation, Register Transposition.
3. Structural: Retrograde, Head Fragmentation, Tail Liquidation.
4. Role Transmutation: Melody ➔ Bassline, Melody ➔ Texture/Pad, Melody ➔ Arpeggio.

Binds every variation to the song's CompositoryMemory to guarantee thematic unity.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..models import Motif, NoteEvent, generate_id
from ..theory.scales import snap_to_scale
from .transformations import transform_motif, realize_motif_as_notes
from .compository_memory import CompositoryMemory

logger = logging.getLogger("MotifDevelopmentEngine")


class TransformationDimension(str, Enum):
    RHYTHMIC = "RHYTHMIC"
    PITCH_MODAL = "PITCH_MODAL"
    STRUCTURAL = "STRUCTURAL"
    ROLE_TRANSMUTATION = "ROLE_TRANSMUTATION"


class MotifDevelopmentEngine:
    """
    Executes deep musical motif developments preserving the song's genetic identity.
    """

    @classmethod
    def apply_diatonic_inversion(
        cls,
        motif: Motif,
        pivot_interval: int = 0
    ) -> Motif:
        """
        Mirrors intervals around a melodic pivot (e.g. interval 0 -> 0, +3 -> -3, -2 -> +2).
        """
        inverted_intervals = [2 * pivot_interval - i for i in motif.intervals]
        return Motif(
            id=generate_id("motif_inv"),
            name=f"{motif.name}_inverted",
            length_beats=motif.length_beats,
            intervals=inverted_intervals,
            rhythm=list(motif.rhythm),
            offsets=list(motif.offsets),
            accents=list(motif.accents),
            role=motif.role,
            section=motif.section,
        )

    @classmethod
    def apply_rhythmic_displacement(
        cls,
        motif: Motif,
        shift_beats: float = 0.5
    ) -> Motif:
        """
        Shifts the rhythm forward or backward by a syncopated delta (e.g. 1 16th or 1 8th note).
        """
        new_offsets = [(off + shift_beats) % max(1.0, motif.length_beats) for off in motif.offsets]
        return Motif(
            id=generate_id("motif_disp"),
            name=f"{motif.name}_displaced",
            length_beats=motif.length_beats,
            intervals=list(motif.intervals),
            rhythm=list(motif.rhythm),
            offsets=new_offsets,
            accents=list(motif.accents),
            role=motif.role,
            section=motif.section,
        )

    @classmethod
    def apply_head_fragmentation(
        cls,
        motif: Motif,
        fraction: float = 0.5
    ) -> Motif:
        """
        Extracts the initial motif head to create a focused, punchy rhythmic riff.
        """
        cutoff = motif.length_beats * fraction
        indices = [i for i, off in enumerate(motif.offsets) if off < cutoff]
        if not indices:
            indices = [0]

        return Motif(
            id=generate_id("motif_frag"),
            name=f"{motif.name}_head_frag",
            length_beats=cutoff,
            intervals=[motif.intervals[i] for i in indices],
            rhythm=[motif.rhythm[i] for i in indices],
            offsets=[motif.offsets[i] for i in indices],
            accents=[motif.accents[i] for i in indices],
            role=motif.role,
            section=motif.section,
        )

    @classmethod
    def apply_augmentation(
        cls,
        motif: Motif,
        factor: float = 2.0
    ) -> Motif:
        """
        Dilates the motif in time (e.g. 2x half-time feel for an anthemic climax).
        """
        return Motif(
            id=generate_id("motif_aug"),
            name=f"{motif.name}_aug_{factor}x",
            length_beats=motif.length_beats * factor,
            intervals=list(motif.intervals),
            rhythm=[r * factor for r in motif.rhythm],
            offsets=[off * factor for off in motif.offsets],
            accents=list(motif.accents),
            role=motif.role,
            section=motif.section,
        )

    @classmethod
    def apply_diminution(
        cls,
        motif: Motif,
        factor: float = 0.5
    ) -> Motif:
        """
        Compresses the motif in time (double-time virtuosity).
        """
        return Motif(
            id=generate_id("motif_dim"),
            name=f"{motif.name}_dim_{factor}x",
            length_beats=max(1.0, motif.length_beats * factor),
            intervals=list(motif.intervals),
            rhythm=[max(0.1, r * factor) for r in motif.rhythm],
            offsets=[off * factor for off in motif.offsets],
            accents=list(motif.accents),
            role=motif.role,
            section=motif.section,
        )

    @classmethod
    def transmute_role(
        cls,
        motif: Motif,
        target_role: str = "bass"
    ) -> Motif:
        """
        Cross-stem transmutation: adapts the motif to a new functional role
        (e.g. Lead melody converted into a walking bassline or an atmospheric pad).
        """
        t_role = target_role.lower()
        if "bass" in t_role or "sub" in t_role:
            # Shift accents to emphasize on-beat foundations and lower density
            new_accents = [1.0 if off % 1.0 == 0.0 else 0.5 for off in motif.offsets]
            new_rhythm = [max(0.75, r) for r in motif.rhythm]  # Longer sustains for bass
        elif "texture" in t_role or "pad" in t_role:
            # Stretch into slow harmonic bed
            new_accents = [0.4 for _ in motif.accents]
            new_rhythm = [r * 3.0 for r in motif.rhythm]
        elif "arp" in t_role or "arpeggio" in t_role:
            # Uniform 16th note rhythm
            new_accents = [0.8 if i % 2 == 0 else 0.4 for i in range(len(motif.accents))]
            new_rhythm = [0.25 for _ in motif.rhythm]
        else:
            new_accents = list(motif.accents)
            new_rhythm = list(motif.rhythm)

        return Motif(
            id=generate_id(f"motif_{t_role}"),
            name=f"{motif.name}_as_{t_role}",
            length_beats=motif.length_beats,
            intervals=list(motif.intervals),
            rhythm=new_rhythm,
            offsets=list(motif.offsets),
            accents=new_accents,
            role=target_role,
            section=motif.section,
        )

    @classmethod
    def synthesize_sectional_evolution_cycle(
        cls,
        seed_motif: Motif,
        memory: Optional[CompositoryMemory] = None,
        key: str = "Eb",
        scale: str = "minor"
    ) -> Dict[str, Motif]:
        """
        Builds a coherent 4-stage narrative evolution across the song timeline:
        - Hook 1: Original Seed Statement
        - Verse 2: Rhythmic Displacement + Head Fragment
        - Bridge: Diatonic Inversion transmuted to Bass/Drone
        - Hook 3: Full Augmentation (Climactic Payoff)
        """
        s_id = seed_motif.id
        hook1_seed = seed_motif

        # Stage 2: Verse 2
        v2_disp = cls.apply_rhythmic_displacement(seed_motif, shift_beats=0.5)
        v2_frag = cls.apply_head_fragmentation(v2_disp, fraction=0.75)
        v2_frag.section = "Verse 2"
        v2_frag.role = seed_motif.role

        # Stage 3: Bridge
        bridge_inv = cls.apply_diatonic_inversion(seed_motif, pivot_interval=0)
        bridge_bass = cls.transmute_role(bridge_inv, target_role="bass")
        bridge_bass.section = "Bridge"

        # Stage 4: Hook 3 (Climax)
        h3_aug = cls.apply_augmentation(seed_motif, factor=1.5)
        h3_aug.section = "Hook 3"
        h3_aug.role = seed_motif.role

        evolutions = {
            "Hook 1": hook1_seed,
            "Verse 2": v2_frag,
            "Bridge": bridge_bass,
            "Hook 3": h3_aug,
        }

        # Track in compository memory if provided
        if memory:
            memory.register_seed_motif(
                seed_id=s_id,
                name=seed_motif.name,
                initial_role=seed_motif.role or "melody",
                section_name="Hook 1",
                bar_range=(21, 28),
                intervals=seed_motif.intervals,
                narrative_function="Foundational hook theme statement"
            )
            memory.register_evolution(
                seed_id=s_id,
                derived_motif_id=v2_frag.id,
                section_name="Verse 2",
                bar_range=(37, 44),
                role=v2_frag.role or "melody",
                transformation_name="RHYTHMIC_DISPLACEMENT_AND_FRAGMENTATION",
                intervals=v2_frag.intervals,
                narrative_function="Lighter, syncopated accompaniment preventing verse monotony"
            )
            memory.register_evolution(
                seed_id=s_id,
                derived_motif_id=bridge_bass.id,
                section_name="Bridge",
                bar_range=(53, 60),
                role="bass",
                transformation_name="DIATONIC_INVERSION_TO_BASS",
                intervals=bridge_bass.intervals,
                narrative_function="Dark harmonic inversion providing structural suspense"
            )
            memory.register_evolution(
                seed_id=s_id,
                derived_motif_id=h3_aug.id,
                section_name="Hook 3",
                bar_range=(61, 68),
                role=h3_aug.role or "melody",
                transformation_name="CLIMACTIC_AUGMENTATION",
                intervals=h3_aug.intervals,
                narrative_function="Extended anthemic climax delivering final emotional payoff"
            )

        return evolutions

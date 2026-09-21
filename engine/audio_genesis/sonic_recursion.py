# engine/audio_genesis/sonic_recursion.py
"""
Sonic Recursion & Self-Sampling Rules Engine:
Enforces the 5 fundamental rules of recursive self-sampling and sonic families:

1. Regla 1 (Anti-reciclaje literal): 0.25 <= Distancia Perceptual <= 0.88.
   Veta el plagio interno perezoso (< 0.25) y el caos acústico degenerado (> 0.88).
2. Regla 2 (Prioridad de material significativo): Favorece motivos principales, acordes
   clave, gestos firma y transientes sobre ruido plano.
3. Regla 3 (Mutación dependiente del rol): Un mismo render se especializa en
   BASS, PAD_TEXTURE, PERCUSSION, TRANSITION_RISER o EAR_CANDY.
4. Regla 4 (Profundidad genética limitada): Bloqueo estricto cuando generation_depth >= 3.
5. Regla 5 (Memoria de identidad): Registro formal de Familias Sonoras Autógenas
   (SonicFamilyRegistry) para que la identidad de la obra madure de forma coherente.
"""

from __future__ import annotations
import uuid
import datetime
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

from .provenance import (
    SampleProvenanceRecord,
    SampleOrigin,
    CreativeGovernanceError,
)

logger = logging.getLogger("SonicRecursion")


class RecursiveTargetRole(str, Enum):
    """Target musical role for self-sampling mutations."""
    BASS = "bass"
    PAD_TEXTURE = "pad_texture"
    PERCUSSION = "percussion"
    TRANSITION_RISER = "transition_riser"
    EAR_CANDY = "ear_candy"


class DistanceCategory(str, Enum):
    """Perceptual distance categories for autogenous mutations."""
    SUBTLE_RECOGNIZABLE_VARIATION = "subtle_recognizable_variation"  # Delta < 0.25
    BALANCED_EVOLUTION = "balanced_evolution"                        # 0.25 <= Delta <= 0.88
    RADICAL_DISCOVERY = "radical_discovery"                          # Delta > 0.88


@dataclass
class SonicFamily:
    """
    An autogenous sonic family born from a distinctive mutation.
    Allows related parts of the song to spawn siblings from this lineage.
    """
    family_id: str
    name: str
    dominant_timbre: str
    source_instrument: str
    target_role: RecursiveTargetRole
    transformation_recipe: List[str]
    ancestor_sample_id: str
    recommended_sections: List[str] = field(default_factory=lambda: ["verse", "hook", "bridge"])
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "name": self.name,
            "dominant_timbre": self.dominant_timbre,
            "source_instrument": self.source_instrument,
            "target_role": self.target_role.value if isinstance(self.target_role, RecursiveTargetRole) else str(self.target_role),
            "transformation_recipe": list(self.transformation_recipe),
            "ancestor_sample_id": self.ancestor_sample_id,
            "recommended_sections": list(self.recommended_sections),
            "tags": list(self.tags),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicFamily:
        role_str = data.get("target_role", "pad_texture")
        try:
            role = RecursiveTargetRole(role_str)
        except ValueError:
            role = RecursiveTargetRole.PAD_TEXTURE

        return cls(
            family_id=data.get("family_id", f"family_{str(uuid.uuid4())[:8]}"),
            name=data.get("name", "Autogenous Sonic Family"),
            dominant_timbre=data.get("dominant_timbre", "Harmonic Shimmer"),
            source_instrument=data.get("source_instrument", "Analog Lab V"),
            target_role=role,
            transformation_recipe=list(data.get("transformation_recipe", [])),
            ancestor_sample_id=data.get("ancestor_sample_id", ""),
            recommended_sections=list(data.get("recommended_sections", ["hook", "bridge"])),
            tags=list(data.get("tags", [])),
            created_at=data.get("created_at", ""),
        )


class SonicFamilyRegistry:
    """
    Maintains and catalogues the autogenous sonic families born during production (Regla 5).
    """

    def __init__(self):
        self.families: Dict[str, SonicFamily] = {}

    def register_family(
        self,
        name: str,
        dominant_timbre: str,
        source_instrument: str,
        target_role: RecursiveTargetRole,
        transformation_recipe: List[str],
        ancestor_sample_id: str,
        recommended_sections: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> SonicFamily:
        fam_id = f"fam_{name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:6]}"
        fam = SonicFamily(
            family_id=fam_id,
            name=name,
            dominant_timbre=dominant_timbre,
            source_instrument=source_instrument,
            target_role=target_role,
            transformation_recipe=transformation_recipe,
            ancestor_sample_id=ancestor_sample_id,
            recommended_sections=recommended_sections or ["verse", "hook", "bridge"],
            tags=tags or [target_role.value]
        )
        self.families[fam_id] = fam
        logger.info(f"Registered Sonic Family: '{name}' ({fam_id}) for role {target_role.value}")
        return fam

    def get_family(self, family_id: str) -> Optional[SonicFamily]:
        return self.families.get(family_id)

    def find_families_for_role(self, role: RecursiveTargetRole) -> List[SonicFamily]:
        return [f for f in self.families.values() if f.target_role == role]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_count": len(self.families),
            "families": {k: v.to_dict() for k, v in self.families.items()},
        }


class SeedMusicalSignificance:
    """
    Evaluates tracks and motifs to prioritize musical material over background noise (Regla 2).
    """

    @classmethod
    def rate_significance(
        cls,
        track_name: str,
        role: str = "KEYS",
        is_primary_motif: bool = False,
        has_signature_gesture: bool = False,
        has_chords: bool = False
    ) -> float:
        """
        Returns a score in [0.0, 1.0] indicating musical weight as a genetic seed:
        - Primary Motif / Lead Theme: 1.0
        - Main Chords / Harmonic Bed: 0.90
        - Signature Gesture / Fill: 0.85
        - Drum Transient / Core Groove: 0.80
        - Flat Fillers / Background Foley: 0.40
        """
        if is_primary_motif:
            return 1.0
        if has_signature_gesture:
            return 0.85
        if has_chords:
            return 0.90

        r_low = role.lower()
        t_low = track_name.lower()

        if any(w in r_low or w in t_low for w in ["lead", "vocal", "hook"]):
            return 0.95
        elif any(w in r_low or w in t_low for w in ["keys", "rhodes", "piano", "chords"]):
            return 0.90
        elif any(w in r_low or w in t_low for w in ["bass", "sub", "808"]):
            return 0.82
        elif any(w in r_low or w in t_low for w in ["drum", "kick", "snare"]):
            return 0.80
        elif any(w in r_low or w in t_low for w in ["foley", "noise", "ambient", "dust"]):
            return 0.40
        return 0.65


class PerceptualDistanceAuditor:
    """
    Enforces Regla 1: Anti-literal recycling vs Anti-chaos degradation.
    Audits the perceptual distance (Delta) between parent and offspring:
    - Delta < 0.25: SUBTLE_RECOGNIZABLE_VARIATION (reinforces theme / motif)
    - 0.25 <= Delta <= 0.88: BALANCED_EVOLUTION (sweet spot of audible genetic kinship)
    - Delta > 0.88: RADICAL_DISCOVERY (bold metamorphic timbre)

    In contextual critique mode (strict=False), the distance is treated as a descriptive profile,
    leaving the final verdict to the ContextualSonicCritic in the section mix.
    In isolated gatekeeping mode (strict=True), hard cutoffs (<0.25 or >0.88) trigger rejection.
    """

    MIN_PERCEPTUAL_DISTANCE = 0.25  # Below this, it sounds like an uncreative duplicate in isolated checks
    MAX_PERCEPTUAL_DISTANCE = 0.88  # Above this, it loses direct kinship in isolated checks

    @classmethod
    def classify_distance(cls, distance: float) -> DistanceCategory:
        """Classifies perceptual distance into descriptive artistic categories."""
        if distance < cls.MIN_PERCEPTUAL_DISTANCE:
            return DistanceCategory.SUBTLE_RECOGNIZABLE_VARIATION
        elif distance > cls.MAX_PERCEPTUAL_DISTANCE:
            return DistanceCategory.RADICAL_DISCOVERY
        else:
            return DistanceCategory.BALANCED_EVOLUTION

    @classmethod
    def get_distance_descriptor(cls, distance: float) -> Dict[str, Any]:
        """Returns rich qualitative metadata for the given perceptual distance."""
        category = cls.classify_distance(distance)
        descriptors = {
            DistanceCategory.SUBTLE_RECOGNIZABLE_VARIATION: {
                "label": "Variación Sutil y Reconocible",
                "rationale": "Mantiene el motivo temático inmediatamente reconocible en el arreglo.",
                "typical_use": "Variaciones melódicas, hooks recurrentes, capas de refuerzo armónico.",
                "artistic_risk": "Bajo (alta coherencia, bajo contraste).",
            },
            DistanceCategory.BALANCED_EVOLUTION: {
                "label": "Evolución Balanceada",
                "rationale": "Punto de oro: parentesco genético audible con carácter fresco e independiente.",
                "typical_use": "Nuevos instrumentos acompañantes, pads derivados, líneas de bajo contrastantes.",
                "artistic_risk": "Medio (equilibrio ideal entre familiaridad y sorpresa).",
            },
            DistanceCategory.RADICAL_DISCOVERY: {
                "label": "Descubrimiento Radical",
                "rationale": "Metamorfosis extrema: el timbre original se deforma hasta crear un sonido nuevo e inesperado.",
                "typical_use": "Ear candy, transiciones, drops dramáticos, efectos glitch.",
                "artistic_risk": "Alto (alta sorpresa, requiere validación acústica contextual en la mezcla).",
            },
        }
        info = descriptors[category]
        return {
            "category": category.value,
            "distance": round(distance, 3),
            **info
        }

    @classmethod
    def audit_distance(
        cls,
        parent_record: SampleProvenanceRecord,
        child_record: SampleProvenanceRecord,
        simulated_distance: Optional[float] = None,
        strict: bool = True
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Audits the perceptual difference.
        Returns: (is_approved, distance_score, rejection_reason)
        """
        # Calculate distance based on processing transformations and parameter shifts
        if simulated_distance is not None:
            dist = max(0.0, min(1.0, float(simulated_distance)))
        else:
            dist = cls._calculate_estimated_distance(parent_record, child_record)

        if strict:
            if dist < cls.MIN_PERCEPTUAL_DISTANCE:
                reason = (
                    f"Veto Regla 1 (Reciclaje literal): Distancia perceptual {dist:.2f} < {cls.MIN_PERCEPTUAL_DISTANCE}. "
                    f"El sonido es una copia literal perezosa de '{parent_record.source.track}'. Requiere mayor transformación."
                )
                return False, dist, reason

            if dist > cls.MAX_PERCEPTUAL_DISTANCE:
                reason = (
                    f"Veto Regla 1 (Caos degenerado): Distancia perceptual {dist:.2f} > {cls.MAX_PERCEPTUAL_DISTANCE}. "
                    f"El sonido ha perdido todo parentesco reconocible con la canción y degeneró en ruido inconexo."
                )
                return False, dist, reason

        return True, dist, None

    @classmethod
    def _calculate_estimated_distance(
        cls,
        parent: SampleProvenanceRecord,
        child: SampleProvenanceRecord
    ) -> float:
        """Estimates perceptual distance from the depth and nature of processing steps."""
        diff_steps = len(child.processing) - len(parent.processing)
        base_dist = 0.20 + (diff_steps * 0.12)

        # Inspect step types
        for step in child.processing[len(parent.processing):]:
            s_name = step.name.lower()
            if "stretch" in s_name or "granular" in s_name:
                base_dist += 0.20
            elif "pitch" in s_name or "frequency" in s_name:
                base_dist += 0.15
            elif "reverse" in s_name or "slice" in s_name:
                base_dist += 0.18
            elif "saturation" in s_name or "drive" in s_name:
                base_dist += 0.08

        return round(max(0.10, min(0.95, base_dist)), 3)


class RoleDependentMutator:
    """
    Configures specialized transformation recipes according to target role (Regla 3).
    A single render branches into Bass, Pad, Percussion, Riser, or Ear Candy.
    """

    @classmethod
    def get_role_recipe(
        cls,
        role: RecursiveTargetRole,
        source_track_name: str
    ) -> Dict[str, Any]:
        """Returns specialized DSP chain recipes and pipeline types for each role."""
        if role == RecursiveTargetRole.BASS:
            return {
                "pipeline": "micro_sample",
                "recipe_steps": [
                    "low_pass_filter_110hz",
                    "even_harmonic_saturation",
                    "pitch_shift_-12st",
                    "vca_sidechain_glue"
                ],
                "target_destination": "simpler_melodic",
                "dominant_timbre": f"Sub-Harmonic Foundation ({source_track_name})",
                "params": {"window_ms": 250.0, "root_tune_midi": 36, "punch_db": 4.0}
            }
        elif role == RecursiveTargetRole.PAD_TEXTURE:
            return {
                "pipeline": "freeze_pad",
                "recipe_steps": [
                    "granular_freeze",
                    "time_stretch_600%",
                    "spectral_bandpass_500_4000hz",
                    "diffuse_reverb_shimmer"
                ],
                "target_destination": "audio_clip",
                "dominant_timbre": f"Diffuse Spectral Halo ({source_track_name})",
                "params": {"stretch_factor": 6.0, "hpf_hz": 380.0}
            }
        elif role == RecursiveTargetRole.PERCUSSION:
            return {
                "pipeline": "micro_sample",
                "recipe_steps": [
                    "transient_attack_isolate",
                    "fast_exponential_decay_60ms",
                    "high_pass_filter_1200hz",
                    "harmonic_pluck_tune"
                ],
                "target_destination": "transient_layer",
                "dominant_timbre": f"Acoustic Transient Bite ({source_track_name})",
                "params": {"window_ms": 80.0, "root_tune_midi": 60}
            }
        elif role == RecursiveTargetRole.TRANSITION_RISER:
            return {
                "pipeline": "melodic_resample",
                "recipe_steps": [
                    "reverse_audio_phrase",
                    "exponential_pitch_glide_+24st",
                    "high_pass_filter_sweep_20hz_to_3khz",
                    "stereo_ping_pong_delay"
                ],
                "target_destination": "audio_clip",
                "dominant_timbre": f"Reverse Tension Riser ({source_track_name})",
                "params": {"pitch_shift": 12, "drive_db": 8.0}
            }
        elif role == RecursiveTargetRole.EAR_CANDY:
            return {
                "pipeline": "audio_to_midi_cycle",
                "recipe_steps": [
                    "micro_chopping_32nd_grid",
                    "frequency_shifter_+140hz",
                    "bitcrush_12bit",
                    "auto_pan_lfo"
                ],
                "target_destination": "simpler_sliced",
                "dominant_timbre": f"Micro-Glitch Ear Candy ({source_track_name})",
                "params": {"freq_shift_hz": 140.0, "new_synth": "Wavetable"}
            }
        else:
            raise ValueError(f"Unknown target role: {role}")


class GenerationDepthGuard:
    """
    Enforces Regla 4: Generation Depth Limit (max_depth = 3).
    Prevents degenerate cascading reprocessing.
    """

    MAX_GENERATION_DEPTH = 3

    @classmethod
    def validate_depth(cls, record: SampleProvenanceRecord) -> bool:
        """
        Validates that the source record has not reached or exceeded max depth.
        Raises CreativeGovernanceError if a generation 3+ sample attempts further re-mutation.
        """
        if record.generation_depth >= cls.MAX_GENERATION_DEPTH:
            raise CreativeGovernanceError(
                f"Veto Regla 4 (Límite generacional): El sample '{record.sample_id}' tiene profundidad "
                f"generacional {record.generation_depth} >= {cls.MAX_GENERATION_DEPTH}. Se prohíbe seguir "
                f"degradando indefinidamente este linaje. El motor debe retroalimentarse de las semillas raíz "
                f"(Generación 0 o 1) de la obra."
            )
        return True

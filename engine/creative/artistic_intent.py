# engine/creative/artistic_intent.py
"""
Artistic Intent Manifesto:
Defines what the song seeks to accomplish emotionally, aesthetically, and narratively
before generating a single note, drum pattern, or synthesizer preset.

Every downstream decision (composition, arrangement, sound design, mixing)
must query `serves_intent()`. If a candidate or technique does not serve the intent,
or violates the forbidden tropes, it is ruthlessly eliminated.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("ArtisticIntent")


@dataclass
class EmotionalJourney:
    """Narrative trajectory experienced by the listener across the song."""
    beginning: str = "intimate, fragile, warm"
    middle: str = "hypnotic, escalating tension, focused groove"
    climax: str = "overwhelming, cathartic, expansive"
    ending: str = "unresolved, lingering resonance, evaporating"

    def to_dict(self) -> Dict[str, str]:
        return {
            "beginning": self.beginning,
            "middle": self.middle,
            "climax": self.climax,
            "ending": self.ending,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EmotionalJourney:
        return cls(
            beginning=str(data.get("beginning", "intimate")),
            middle=str(data.get("middle", "hypnotic")),
            climax=str(data.get("climax", "overwhelming")),
            ending=str(data.get("ending", "unresolved")),
        )


@dataclass
class ArtisticIntent:
    """
    Master artistic manifesto governing a musical piece.
    Serves as the supreme standard of truth for the Artistic Critic Engine.
    """
    song_title: str = "Untitled Work"
    genre_anchor: str = "experimental_neo_soul"
    emotional_core: List[str] = field(default_factory=lambda: ["nostalgia", "confidence", "restrained_aggression"])
    listener_experience: EmotionalJourney = field(default_factory=EmotionalJourney)
    identity_aesthetic: Dict[str, str] = field(default_factory=lambda: {
        "primary": "dusty_analog",
        "secondary": "futuristic_granular",
        "signature": "beautiful_imperfection"
    })
    signature_sound_brief: str = "reverse Rhodes ghost note with saturated transient and vinyl crackle tail"
    forbidden_tropes: List[str] = field(default_factory=lambda: [
        "generic_trap_hats",
        "predictable_risers",
        "stock_synth_presets",
        "constant_maximal_density",
        "four_on_the_floor_crash",
        "unextended_major_triads"
    ])
    risk_tolerance: float = 0.65       # 0.0 (conservative) to 1.0 (avant-garde)
    deviation_budget: float = 0.40     # Budget points for unexpected departure before being judged as chaos
    max_competing_hooks: int = 2       # Enforces memorability rule: 1-2 hooks max

    def serves_intent(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determines whether a proposed candidate or musical gesture serves this intent.
        Returns (serves: bool, reason: str).
        """
        # 1. Forbidden tropes check
        tropes = proposal.get("detected_tropes", []) or []
        for trope in tropes:
            if trope in self.forbidden_tropes:
                return False, f"VETO: Violates forbidden trope '{trope}' strictly barred by ArtisticIntent."

        proposal_name = str(proposal.get("name", "")).lower()
        proposal_tags = [str(t).lower() for t in proposal.get("tags", [])]
        for forbidden in self.forbidden_tropes:
            norm_forbidden = forbidden.replace("_", " ")
            if norm_forbidden in proposal_name or any(norm_forbidden in tag for tag in proposal_tags):
                return False, f"VETO: Proposed technique '{forbidden}' matches forbidden artistic trope."

        # 2. Risk check: if proposal exceeds risk tolerance by too much
        prop_risk = float(proposal.get("risk", 0.5))
        if prop_risk > (self.risk_tolerance + 0.35):
            return False, f"VETO: Proposal risk ({prop_risk:.2f}) exceeds risk tolerance ({self.risk_tolerance:.2f}) causing artistic incoherence."

        # 3. Density check: if proposal demands constant maximal density
        density = float(proposal.get("density", 0.5))
        duration_bars = float(proposal.get("duration_bars", 0))
        if density > 0.90 and duration_bars > 16.0:
            if "constant_maximal_density" in self.forbidden_tropes or "dense_polyphony" in self.forbidden_tropes or "crowded_mids" in self.forbidden_tropes:
                return False, "VETO: Sustained maximal density (>0.90 over 16 bars) violates artistic intent of breathing dynamics."

        return True, "Proposal aligns with ArtisticIntent vision."

    def evaluate_alignment(self, candidate_summary: Dict[str, Any]) -> float:
        """
        Calculates holistic alignment score (0.0 to 1.0) with this artistic manifesto.
        """
        score = 1.0
        # Deduction for forbidden trope proximity
        detected_tropes = candidate_summary.get("detected_tropes", [])
        score -= len(detected_tropes) * 0.30

        # Emotional alignment
        cand_emotions = candidate_summary.get("emotions", [])
        shared_emotions = set(self.emotional_core).intersection(set(cand_emotions))
        if self.emotional_core:
            emotional_match = len(shared_emotions) / len(self.emotional_core)
            score = (score * 0.7) + (emotional_match * 0.3)

        # Risk balance: penalize if too timid when high risk is requested, or too wild when low risk is requested
        cand_risk = float(candidate_summary.get("risk", 0.5))
        risk_delta = abs(self.risk_tolerance - cand_risk)
        score -= risk_delta * 0.15

        return round(max(0.0, min(1.0, score)), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_title": self.song_title,
            "genre_anchor": self.genre_anchor,
            "emotional_core": list(self.emotional_core),
            "listener_experience": self.listener_experience.to_dict(),
            "identity_aesthetic": dict(self.identity_aesthetic),
            "signature_sound_brief": self.signature_sound_brief,
            "forbidden_tropes": list(self.forbidden_tropes),
            "risk_tolerance": round(self.risk_tolerance, 2),
            "deviation_budget": round(self.deviation_budget, 2),
            "max_competing_hooks": self.max_competing_hooks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArtisticIntent:
        exp_data = data.get("listener_experience", {})
        listener_exp = EmotionalJourney.from_dict(exp_data) if isinstance(exp_data, dict) else EmotionalJourney()
        return cls(
            song_title=str(data.get("song_title", "Untitled Work")),
            genre_anchor=str(data.get("genre_anchor", "neo_soul")),
            emotional_core=list(data.get("emotional_core", ["nostalgia"])),
            listener_experience=listener_exp,
            identity_aesthetic=dict(data.get("identity_aesthetic", {})),
            signature_sound_brief=str(data.get("signature_sound_brief", "")),
            forbidden_tropes=list(data.get("forbidden_tropes", [])),
            risk_tolerance=float(data.get("risk_tolerance", 0.65)),
            deviation_budget=float(data.get("deviation_budget", 0.40)),
            max_competing_hooks=int(data.get("max_competing_hooks", 2)),
        )

    # -------------------------------------------------------------------------
    # Preset Archetype Builders for Distinct Artistic Visions
    # -------------------------------------------------------------------------
    @classmethod
    def create_minimal_intimate(cls, title: str = "Whisper In Ash") -> ArtisticIntent:
        return cls(
            song_title=title,
            genre_anchor="minimal_neo_soul",
            emotional_core=["fragility", "intimacy", "quiet_longing"],
            listener_experience=EmotionalJourney(
                beginning="bare room, solo voice, dry acoustic noise",
                middle="subtle sub-bass warmth, gentle syncopated shaker",
                climax="dynamic bloom with acoustic piano pedal sustain",
                ending="sudden breath, lone Rhodes decay"
            ),
            identity_aesthetic={"primary": "acoustic_dry", "secondary": "warm_tape", "signature": "intimate_imperfection"},
            signature_sound_brief="felt piano hammer strike + room mic rustle + filtered tape warble",
            forbidden_tropes=["generic_trap_hats", "heavy_distortion", "predictable_risers", "dense_polyphony", "crowded_mids"],
            risk_tolerance=0.55,
            deviation_budget=0.30
        )

    @classmethod
    def create_aggressive_dense(cls, title: str = "Kinetix Overload") -> ArtisticIntent:
        return cls(
            song_title=title,
            genre_anchor="industrial_trap_rage",
            emotional_core=["ferocity", "urgency", "uncompromising_power"],
            listener_experience=EmotionalJourney(
                beginning="industrial siren, clipping 808 drone, stuttering noise",
                middle="relentless syncopated drive, distorted percussive slams",
                climax="cacophony of tearing wavetable leads and sub pressure",
                ending="abrupt silence on beat 4, cold reverb decay"
            ),
            identity_aesthetic={"primary": "distorted_metallic", "secondary": "overdriven_analog", "signature": "visceral_impact"},
            signature_sound_brief="screaming FM lead through bitcrusher + gated 808 transient + anvil strike",
            forbidden_tropes=["sweet_chords", "unextended_major_triads", "smooth_jazz_keys", "polite_mix"],
            risk_tolerance=0.85,
            deviation_budget=0.60
        )

    @classmethod
    def create_psychedelic(cls, title: str = "Liquid Mirages") -> ArtisticIntent:
        return cls(
            song_title=title,
            genre_anchor="psychedelic_downtempo",
            emotional_core=["disorientation", "awe", "transcendence"],
            listener_experience=EmotionalJourney(
                beginning="swirling phaser bed, reversed kalimba, floating pulse",
                middle="binaural pan movement, elastic polyrhythms",
                climax="timbral morphing wall of sound with shimmer delay",
                ending="dissolving into tape flutter and ambient resonant wash"
            ),
            identity_aesthetic={"primary": "liquid_modulation", "secondary": "granular_ambient", "signature": "hallucinatory_depth"},
            signature_sound_brief="binaural flanged flute chop + dynamic reverse granular delays",
            forbidden_tropes=["rigid_grid_quantization", "dry_monophonic_leads", "stock_trap_snare"],
            risk_tolerance=0.75,
            deviation_budget=0.50
        )

    @classmethod
    def create_raw_lofi(cls, title: str = "Tascam Memories") -> ArtisticIntent:
        return cls(
            song_title=title,
            genre_anchor="cassette_lofi_boombap",
            emotional_core=["nostalgia", "melancholic_comfort", "solitude"],
            listener_experience=EmotionalJourney(
                beginning="cassette hum, needle drop, detuned electric piano",
                middle="heavy swinging boom bap pocket, warm round upright bass",
                climax="subtle vinyl loop layer with muted trumpet horn swell",
                ending="tape motor stop deceleration effect"
            ),
            identity_aesthetic={"primary": "cassette_tape_warmth", "secondary": "sp404_vinyl_grit", "signature": "organic_wabi_sabi"},
            signature_sound_brief="SP-404 vinyl sim flutter + detuned Rhodes octave + acoustic vinyl pop",
            forbidden_tropes=["ultra_bright_modern_highs", "pristine_digital_compression", "edm_sweeps"],
            risk_tolerance=0.50,
            deviation_budget=0.35
        )

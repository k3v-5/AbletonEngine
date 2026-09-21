# engine/sound_design/sonic_dna.py
"""
Sonic DNA (Gen 2 - Sound Design & Sonic Identity):
Extracts and maintains the authentic acoustic genome of a specific song.

Ensures that every sound design transformation, resynthesis pass, or hybrid instrument
genetically descends from and harmonizes with the core musical motifs, timbres,
groove, and spatial posture of this specific production.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("SonicDNA")


@dataclass
class HarmonicDNA:
    """The harmonic fingerprint and modal architecture of the piece."""
    key: str = "Eb"
    scale: str = "minor"
    signature_intervals: List[str] = field(default_factory=lambda: ["minor_9th", "flat_7th", "major_13th"])
    characteristic_voicings: List[str] = field(default_factory=lambda: ["Ebm9 (Eb-Gb-Bb-Db-F)", "Ab13 (Ab-C-Gb-F)", "Dbmaj9", "Bmaj7"])
    harmonic_density: str = "extended_modal_jazz"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "scale": self.scale,
            "signature_intervals": list(self.signature_intervals),
            "characteristic_voicings": list(self.characteristic_voicings),
            "harmonic_density": self.harmonic_density,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HarmonicDNA:
        return cls(
            key=data.get("key", "Eb"),
            scale=data.get("scale", "minor"),
            signature_intervals=data.get("signature_intervals", []),
            characteristic_voicings=data.get("characteristic_voicings", []),
            harmonic_density=data.get("harmonic_density", "extended_modal_jazz"),
        )


@dataclass
class RhythmicDNA:
    """The rhythmic pocket, swing percentage, and groove posture."""
    bpm: float = 110.0
    swing_pct: float = 54.0              # 50% = straight grid, 54% = subtle Dilla/Pharrell bounce
    pocket_feel: str = "laid_back_boom_bap"
    syncopation_index: float = 0.68      # 0.0 (rigid 4-on-floor) to 1.0 (highly syncopated)
    kick_snare_relationship: str = "delayed_snare_drag"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bpm": self.bpm,
            "swing_pct": self.swing_pct,
            "pocket_feel": self.pocket_feel,
            "syncopation_index": round(self.syncopation_index, 2),
            "kick_snare_relationship": self.kick_snare_relationship,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RhythmicDNA:
        return cls(
            bpm=float(data.get("bpm", 110.0)),
            swing_pct=float(data.get("swing_pct", 54.0)),
            pocket_feel=data.get("pocket_feel", "laid_back_boom_bap"),
            syncopation_index=float(data.get("syncopation_index", 0.68)),
            kick_snare_relationship=data.get("kick_snare_relationship", "delayed_snare_drag"),
        )


@dataclass
class TimbralDNA:
    """The core timbral hierarchy and spectral weight distribution."""
    primary_timbre: str = "felt_stage_73_rhodes"
    secondary_timbre: str = "analog_lab_jazz_horns"
    sub_anchor: str = "sublab_xl_808_sub"
    dominant_frequency_range: str = "warm_low_mid_250_600hz"
    vocal_lane_cleared: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_timbre": self.primary_timbre,
            "secondary_timbre": self.secondary_timbre,
            "sub_anchor": self.sub_anchor,
            "dominant_frequency_range": self.dominant_frequency_range,
            "vocal_lane_cleared": self.vocal_lane_cleared,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimbralDNA:
        return cls(
            primary_timbre=data.get("primary_timbre", "felt_stage_73_rhodes"),
            secondary_timbre=data.get("secondary_timbre", "analog_lab_jazz_horns"),
            sub_anchor=data.get("sub_anchor", "sublab_xl_808_sub"),
            dominant_frequency_range=data.get("dominant_frequency_range", "warm_low_mid_250_600hz"),
            vocal_lane_cleared=bool(data.get("vocal_lane_cleared", True)),
        )


@dataclass
class TextureDNA:
    """The acoustic floor, noise floor, and organic air of the track."""
    character: str = "dusty_warm_vinyl"
    noise_floor_db: float = -24.0
    foley_elements: List[str] = field(default_factory=lambda: ["vinyl_crackle", "subtle_room_tone"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character": self.character,
            "noise_floor_db": self.noise_floor_db,
            "foley_elements": list(self.foley_elements),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TextureDNA:
        return cls(
            character=data.get("character", "dusty_warm_vinyl"),
            noise_floor_db=float(data.get("noise_floor_db", -24.0)),
            foley_elements=data.get("foley_elements", []),
        )


@dataclass
class SpatialDNA:
    """The natural spatial aperture and lateral dynamics of the work."""
    natural_aperture: str = "center_weighted_with_wide_hook_bursts"
    verse_width_pct: float = 70.0
    hook_width_pct: float = 115.0
    bridge_width_pct: float = 30.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "natural_aperture": self.natural_aperture,
            "verse_width_pct": self.verse_width_pct,
            "hook_width_pct": self.hook_width_pct,
            "bridge_width_pct": self.bridge_width_pct,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatialDNA:
        return cls(
            natural_aperture=data.get("natural_aperture", "center_weighted_with_wide_hook_bursts"),
            verse_width_pct=float(data.get("verse_width_pct", 70.0)),
            hook_width_pct=float(data.get("hook_width_pct", 115.0)),
            bridge_width_pct=float(data.get("bridge_width_pct", 30.0)),
        )


@dataclass
class MotifFingerprint:
    """A recurring musical gesture that forms part of the song's identity."""
    id: str
    track_name: str
    role: str
    bars: Tuple[int, int]
    voicing_or_notes: str
    significance: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "track_name": self.track_name,
            "role": self.role,
            "bars": list(self.bars),
            "voicing_or_notes": self.voicing_or_notes,
            "significance": self.significance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MotifFingerprint:
        bars = data.get("bars", [1, 8])
        return cls(
            id=data.get("id", "MOTIF_1"),
            track_name=data.get("track_name", "Keys"),
            role=data.get("role", "keys"),
            bars=(int(bars[0]), int(bars[1])),
            voicing_or_notes=data.get("voicing_or_notes", ""),
            significance=data.get("significance", ""),
        )


@dataclass
class SonicDNA:
    """
    The master acoustic genome of the song currently in production.
    All downstream sound design mutations must align with and descend from this DNA.
    """
    song_id: str
    harmonic: HarmonicDNA = field(default_factory=HarmonicDNA)
    rhythmic: RhythmicDNA = field(default_factory=RhythmicDNA)
    timbral: TimbralDNA = field(default_factory=TimbralDNA)
    texture: TextureDNA = field(default_factory=TextureDNA)
    spatial: SpatialDNA = field(default_factory=SpatialDNA)
    key_motifs: List[MotifFingerprint] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @classmethod
    def extract_from_session(cls, session_data: Dict[str, Any]) -> SonicDNA:
        """
        Dynamically extracts and constructs the SonicDNA from session state.
        """
        key = session_data.get("key", "Eb")
        scale = session_data.get("scale", "minor")
        bpm = float(session_data.get("bpm", 110.0))
        s_id = f"dna_{key}_{scale}_{int(bpm)}bpm"

        # Determine swing and pocket
        genre = str(session_data.get("genre", "hip-hop")).lower()
        swing = 54.0 if "hop" in genre or "soul" in genre else 50.0

        # Discover track timbres
        tracks = session_data.get("tracks", [])
        primary = "felt_stage_73_rhodes"
        secondary = "analog_lab_jazz_horns"
        sub = "sublab_xl_808_sub"

        for t in tracks:
            t_name = str(t.get("name", "")).lower()
            if "rhodes" in t_name or "stage" in t_name:
                primary = t.get("name", primary)
            elif "horn" in t_name or "brass" in t_name:
                secondary = t.get("name", secondary)
            elif "sub" in t_name or "bass" in t_name:
                sub = t.get("name", sub)

        # Build motifs from known structure
        motifs = [
            MotifFingerprint(
                id="MOTIF_HOOK1_CHORDS",
                track_name="Stage-73 Rhodes",
                role="keys",
                bars=(21, 28),
                voicing_or_notes="Ebm9 - Ab13 - Dbmaj9 - Bmaj7",
                significance="Primary harmonic identity of the hook anthem"
            ),
            MotifFingerprint(
                id="MOTIF_HOOK_HORNS_STAB",
                track_name="Analog Lab Horns",
                role="horns",
                bars=(21, 28),
                voicing_or_notes="Eb5 - F5 syncopated brass punctuation",
                significance="Call-and-response melodic hook accent"
            ),
            MotifFingerprint(
                id="MOTIF_BRIDGE_SUSPENSE",
                track_name="Ac Strings Orch",
                role="strings",
                bars=(53, 60),
                voicing_or_notes="High sustained Eb6 pad swell",
                significance="Tension bridge creating vacuum anticipation for final drop"
            ),
        ]

        return cls(
            song_id=s_id,
            harmonic=HarmonicDNA(key=key, scale=scale),
            rhythmic=RhythmicDNA(bpm=bpm, swing_pct=swing),
            timbral=TimbralDNA(primary_timbre=primary, secondary_timbre=secondary, sub_anchor=sub),
            texture=TextureDNA(),
            spatial=SpatialDNA(),
            key_motifs=motifs,
        )

    def validate_mutation_compatibility(self, mutation_role: str, source_material: str) -> Tuple[bool, Optional[str]]:
        """
        Enforces genetic loyalty: mutations must stem from recognizable session material.
        """
        source_lower = source_material.lower()
        recognized_sources = [
            self.timbral.primary_timbre.lower(),
            self.timbral.secondary_timbre.lower(),
            self.timbral.sub_anchor.lower(),
            "rhodes", "piano", "horns", "brass", "strings", "kick", "snare", "808"
        ]

        if not any(r in source_lower for r in recognized_sources):
            return False, f"Mutación huérfana: el origen '{source_material}' no pertenece al Sonic DNA de la obra."

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "harmonic": self.harmonic.to_dict(),
            "rhythmic": self.rhythmic.to_dict(),
            "timbral": self.timbral.to_dict(),
            "texture": self.texture.to_dict(),
            "spatial": self.spatial.to_dict(),
            "key_motifs": [m.to_dict() for m in self.key_motifs],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicDNA:
        return cls(
            song_id=data.get("song_id", "dna_default"),
            harmonic=HarmonicDNA.from_dict(data.get("harmonic", {})),
            rhythmic=RhythmicDNA.from_dict(data.get("rhythmic", {})),
            timbral=TimbralDNA.from_dict(data.get("timbral", {})),
            texture=TextureDNA.from_dict(data.get("texture", {})),
            spatial=SpatialDNA.from_dict(data.get("spatial", {})),
            key_motifs=[MotifFingerprint.from_dict(m) for m in data.get("key_motifs", [])],
            created_at=data.get("created_at", ""),
        )

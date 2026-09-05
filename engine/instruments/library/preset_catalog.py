# engine/instruments/library/preset_catalog.py
"""Curated Catalog of Verified Native Instrument and Drum Presets for Ableton Live 12 Suite.

Provides instant resolution from high-level musical roles, genres, and timbral intents
to production-ready, authentic .adv and .adg presets without loading empty 'init' patches.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class PresetEntry:
    name: str
    uri: str
    role: str
    category: str
    character: str = ""
    genres: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "uri": self.uri,
            "role": self.role,
            "category": self.category,
            "character": self.character,
            "genres": self.genres,
            "description": self.description,
            "tags": self.tags
        }

# Curated catalog of verified Ableton Live 12 Suite presets
PRESET_CATALOG: List[PresetEntry] = [
    # --- PIANOS & KEYS ---
    PresetEntry(
        name="Grand Piano",
        uri="query:Sounds#Piano%20&%20Keys:FileId_4870",
        role="PIANO",
        category="Piano & Keys",
        character="warm_acoustic",
        genres=["hip_hop", "neo_soul", "pop", "classical", "lofi"],
        description="Full dynamic concert grand piano rack with natural resonance.",
        tags=["acoustic", "keys", "dynamic", "grand"]
    ),
    PresetEntry(
        name="Childhood Home Piano",
        uri="query:Sounds#Piano%20&%20Keys:FileId_4848",
        role="PIANO",
        category="Piano & Keys",
        character="intimate_felt",
        genres=["neo_soul", "lofi", "ambient", "indie"],
        description="Felted, intimate upright piano with tape character. Ideal for Tyler, The Creator and emotional ballads.",
        tags=["felt", "vintage", "emotional", "upright", "lofi"]
    ),
    PresetEntry(
        name="Ac Piano Upright",
        uri="query:Sounds#Piano%20&%20Keys:FileId_4847",
        role="PIANO",
        category="Piano & Keys",
        character="tight_upright",
        genres=["jazz", "hip_hop", "house"],
        description="Crisp acoustic upright piano cutting cleanly through dense mixes.",
        tags=["acoustic", "upright", "punchy"]
    ),
    PresetEntry(
        name="Clav Electric",
        uri="query:Sounds#Piano%20&%20Keys:FileId_6395",
        role="KEYS",
        category="Piano & Keys",
        character="electric_funky",
        genres=["funk", "soul", "hip_hop", "rnb"],
        description="Electric clavinet / stage key with pickup bite and velocity response.",
        tags=["electric", "clavinet", "bite"]
    ),

    # --- 808 & SUB BASS ---
    PresetEntry(
        name="808 BNYX Stopper",
        uri="query:Sounds#Bass:FileId_5175",
        role="SUB_BASS",
        category="Bass",
        character="hard_saturated_808",
        genres=["trap", "rage", "hip_hop", "drill"],
        description="Punchy, distorted modern 808 sub with transient bite for high-energy rap.",
        tags=["808", "sub", "distorted", "hard", "trap"]
    ),
    PresetEntry(
        name="808 Drifter",
        uri="query:Sounds#Bass:FileId_5176",
        role="SUB_BASS",
        category="Bass",
        character="gliding_analog_808",
        genres=["trap", "hip_hop", "lofi"],
        description="Analog 808 sub based on Drift with warm pitch glides and saturation.",
        tags=["808", "drift", "glide", "warm"]
    ),
    PresetEntry(
        name="808 Pure",
        uri="query:Sounds#Bass:FileId_5177",
        role="SUB_BASS",
        category="Bass",
        character="clean_deep_sine",
        genres=["trap", "rnb", "pop", "hip_hop"],
        description="Clean low-end sine 808 sub with smooth decay and tight fundamental.",
        tags=["808", "pure", "deep", "sine"]
    ),
    PresetEntry(
        name="808 Slapping",
        uri="query:Sounds#Bass:FileId_5179",
        role="SUB_BASS",
        category="Bass",
        character="percussive_heavy",
        genres=["trap", "atlanta_bounce", "hip_hop"],
        description="Heavy Atlanta-style punchy 808 with click transient for instant bounce.",
        tags=["808", "punchy", "atlanta", "bounce"]
    ),
    PresetEntry(
        name="Analog Bass",
        uri="query:Sounds#Bass:FileId_5181",
        role="BASS",
        category="Bass",
        character="vintage_moog",
        genres=["synthwave", "funk", "house", "techno"],
        description="Dual-oscillator fat analog bass with warm ladder filter drive.",
        tags=["analog", "moog", "fat", "filter"]
    ),
    PresetEntry(
        name="Basic Sub Sine",
        uri="query:Sounds#Bass:FileId_5196",
        role="SUB_BASS",
        category="Bass",
        character="deep_sub",
        genres=["techno", "dnb", "dubstep", "house"],
        description="Pure mono sub fundamental focused under 80 Hz.",
        tags=["sub", "sine", "fundamental", "clean"]
    ),

    # --- SYNTH LEADS & HOOKS ---
    PresetEntry(
        name="Acceleration Lead",
        uri="query:Sounds#Synth%20Lead:FileId_4589",
        role="LEAD",
        category="Synth Lead",
        character="cutting_saw",
        genres=["trap", "electronic", "synthwave"],
        description="Bright cutting saw lead with portamento and envelope modulation.",
        tags=["saw", "cutting", "lead", "hook"]
    ),
    PresetEntry(
        name="Agenda Lead",
        uri="query:Sounds#Synth%20Lead:FileId_6743",
        role="LEAD",
        category="Synth Lead",
        character="staccato_analog",
        genres=["hip_hop", "trap", "indie"],
        description="Punchy analog hook lead designed for fast melodic runs and ostinatos.",
        tags=["staccato", "punchy", "hook"]
    ),

    # --- PADS & STRINGS ---
    PresetEntry(
        name="Warm Analog Pad",
        uri="query:Sounds#Pad:FileId_4993",
        role="PAD",
        category="Pad",
        character="warm_lush",
        genres=["neo_soul", "ambient", "techno", "hip_hop"],
        description="Spacious analog pad with slow gentle filter sweep and chorus warmth.",
        tags=["warm", "analog", "pad", "lush"]
    ),
    PresetEntry(
        name="VHS Dreams",
        uri="query:Sounds#Pad:FileId_4984",
        role="PAD",
        category="Pad",
        character="lofi_vintage",
        genres=["lofi", "chillhop", "neo_soul"],
        description="Tape flutter pad with retro pitch instability and filtered top-end.",
        tags=["lofi", "vhs", "tape", "retro"]
    ),
    PresetEntry(
        name="Ac Strings Orch",
        uri="query:Sounds#Strings:FileId_4765",
        role="STRINGS",
        category="Strings",
        character="cinematic_ensemble",
        genres=["cinematic", "orchestral", "hip_hop", "pop"],
        description="Full orchestral string section with expressive velocity and legato.",
        tags=["strings", "orchestral", "cinematic", "legato"]
    ),
    PresetEntry(
        name="Ac Strings Pizz Basic",
        uri="query:Sounds#Strings:FileId_4766",
        role="PLUCK",
        category="Strings",
        character="pizzicato_tight",
        genres=["trap", "orchestral", "drill", "cinematic"],
        description="Crisp pizzicato string plucks for tension rhythms and syncopated arps.",
        tags=["pizzicato", "pluck", "tight", "strings"]
    ),

    # --- DRUM KITS (FULL DRUM RACKS) ---
    PresetEntry(
        name="808 Core Kit",
        uri="query:Drums#FileId_5422",
        role="DRUM_KIT",
        category="Drums",
        character="classic_808",
        genres=["trap", "hip_hop", "rnb", "pop"],
        description="Legendary Roland TR-808 kit with deep boom kick, snappy snare, crisp clap, and metallic hats.",
        tags=["808", "drum_rack", "trap", "hip_hop"]
    ),
    PresetEntry(
        name="909 Core Kit",
        uri="query:Drums#FileId_5423",
        role="DRUM_KIT",
        category="Drums",
        character="punchy_909",
        genres=["house", "techno", "dance"],
        description="Classic Roland TR-909 kit with punchy kick, snappy mid snare, and open hi-hat sizzle.",
        tags=["909", "drum_rack", "house", "techno"]
    ),
    PresetEntry(
        name="707 Core Kit",
        uri="query:Drums#FileId_5421",
        role="DRUM_KIT",
        category="Drums",
        character="digital_punch",
        genres=["synthwave", "disco", "electro"],
        description="Roland TR-707 digital PCM drum machine with tight snare and percussive claps.",
        tags=["707", "drum_rack", "digital", "retro"]
    ),
    PresetEntry(
        name="AG Techno Kit",
        uri="query:Drums#FileId_5367",
        role="DRUM_KIT",
        category="Drums",
        character="industrial_techno",
        genres=["techno", "melodic_techno", "industrial"],
        description="Heavy techno drum rack with sub rumble kick, cutting percs, and sharp hats.",
        tags=["techno", "drum_rack", "heavy"]
    )
]

class PresetCatalog:
    """Fast resolver and index for curated native Live 12 presets."""

    @staticmethod
    def resolve_preset(role: str, genre: str = "", mood: str = "") -> Optional[PresetEntry]:
        """Find the best matching preset for a musical role, genre, and timbral character."""
        r_clean = role.strip().upper()
        g_clean = genre.strip().lower()
        m_clean = mood.strip().lower()

        # Exact role matches
        candidates = [p for p in PRESET_CATALOG if p.role == r_clean]
        if not candidates:
            # Flexible role fallback
            for p in PRESET_CATALOG:
                if r_clean in p.role or p.role in r_clean or r_clean in [t.upper() for t in p.tags]:
                    candidates.append(p)

        if not candidates:
            return None

        # Score by genre and character/mood
        def score(p: PresetEntry) -> int:
            s = 0
            if g_clean:
                if g_clean in p.name.lower():
                    s += 20
                if g_clean in p.character or any(g_clean in t.lower() for t in p.tags):
                    s += 12
                if any(g_clean in gn.lower() for gn in p.genres):
                    s += 6
            if m_clean:
                if m_clean in p.name.lower():
                    s += 20
                if m_clean in p.character or any(m_clean in t.lower() for t in p.tags):
                    s += 15
                if any(m_clean in gn.lower() for gn in p.genres):
                    s += 5
            return s

        candidates.sort(key=score, reverse=True)
        return candidates[0]

    @staticmethod
    def list_presets(role: str = "", genre: str = "") -> List[PresetEntry]:
        results = PRESET_CATALOG
        if role:
            r_clean = role.strip().upper()
            results = [p for p in results if p.role == r_clean or r_clean in p.role]
        if genre:
            g_clean = genre.strip().lower()
            results = [p for p in results if g_clean in p.genres]
        return results

    @staticmethod
    def search(query: str) -> List[PresetEntry]:
        q = query.strip().lower()
        return [
            p for p in PRESET_CATALOG
            if q in p.name.lower() or q in p.role.lower() or q in p.character.lower() or any(q in t for t in p.tags)
        ]

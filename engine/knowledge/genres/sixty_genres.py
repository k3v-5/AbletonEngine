# engine/knowledge/genres/sixty_genres.py
"""
60 Most Popular Music Genres: Acoustic Profiles & Production Knowledge Base.
Provides exhaustive sound design, instrumentation, groove pockets, arrangement density,
and mastering LUFS standards for the top 60 commercial genres in modern music production.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class GenreAcousticProfile:
    id: str
    name: str
    family: str
    description: str
    bpm_range: Tuple[float, float, float]  # min_bpm, max_bpm, default_bpm
    time_signature: Tuple[int, int] = (4, 4)
    target_lufs: Tuple[float, float, float] = (-9.5, -8.0, -8.5)  # min_lufs, max_lufs, default_lufs
    recommended_keys_modes: List[str] = field(default_factory=lambda: ["F Minor", "C Minor", "D Minor", "A Minor"])
    channel_density: Tuple[int, int, int] = (6, 12, 18)  # min_channels, recommended_channels, max_channels
    drum_kits: List[str] = field(default_factory=list)
    groove_style: str = "straight_precise"
    groove_swing_pct: float = 0.0
    instruments: List[str] = field(default_factory=list)
    insert_fx: List[str] = field(default_factory=list)
    turnaround_bars: int = 8
    typical_structure: List[str] = field(default_factory=lambda: [
        "Intro (8)", "Verse 1 (16)", "Buildup (8)", "Drop 1 (16)", "Bridge (8)", "Drop 2 (16)", "Outro (8)"
    ])
    sidechain_required: bool = True
    deesser_required: bool = True
    analog_saturation_recommended: bool = True


GENRES_CATALOG: Dict[str, GenreAcousticProfile] = {
    # ── 1. URBAN & HIP-HOP (1-10) ─────────────────────────────────────────────
    "trap": GenreAcousticProfile(
        id="trap",
        name="Trap",
        family="Urban_HipHop",
        description="Atlanta dark trap characterized by rolling hi-hats, pitch-bending 808 sub, and menacing brass/plucks.",
        bpm_range=(130.0, 160.0, 140.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["C Minor", "F Minor", "C# Minor", "D Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["808 Core Kit (.adg)", "808 BNYX Kit", "Trap Tight Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["808 BNYX Stopper (.adg)", "Vital Audio Vital", "Serum 2 Lead", "Analog Lab Dark Keys"],
        insert_fx=["FabFilter Saturn 2", "Xfer Records OTT", "ValhallaVintageVerb", "Glue Compressor"],
        turnaround_bars=8
    ),
    "latin_trap": GenreAcousticProfile(
        id="latin_trap",
        name="Latin Trap",
        family="Urban_HipHop",
        description="Puerto Rican and Argentine trap with heavy sub-bass slides, atmospheric pads, and rhythmic dembow undertones.",
        bpm_range=(115.0, 145.0, 128.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["D Minor", "G Minor", "A Minor", "E Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["808 Core Kit (.adg)", "Latin Trap Drums", "Urban 808 Kit"],
        groove_style="mpc_60",
        groove_swing_pct=52.0,
        instruments=["Intelligent 808 Sub", "Drift Neo-Soul Rhodes", "Vital Dark Flute", "Warm Analog Pad"],
        insert_fx=["FabFilter Saturn 2", "Tape MELLO-FI", "ValhallaVintageVerb", "FabFilter Pro-DS"],
        turnaround_bars=8
    ),
    "drill": GenreAcousticProfile(
        id="drill",
        name="Drill",
        family="Urban_HipHop",
        description="UK and Brooklyn drill with sliding 808 glides, counter-rhythmic offbeat snares, and pitch-descending hi-hat triplets.",
        bpm_range=(140.0, 148.0, 142.0),
        target_lufs=(-8.5, -7.0, -7.5),
        recommended_keys_modes=["C Minor", "F Minor", "Ab Minor", "Eb Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Drill Masters Kit", "808 Core Kit (.adg)", "London Drill Box"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["808 Slide Sub", "Ghost Piano Chops", "Eerie Bells", "Glitch Plucks"],
        insert_fx=["FabFilter Saturn 2", "OTT", "ValhallaDelay", "Dynamic Sidechain"],
        turnaround_bars=8
    ),
    "detroit_trap": GenreAcousticProfile(
        id="detroit_trap",
        name="Detroit Trap",
        family="Urban_HipHop",
        description="Offbeat syncopated trap with fast piano riffs, aggressive clap placements, and bouncy 808 rolls.",
        bpm_range=(170.0, 205.0, 185.0),
        target_lufs=(-8.5, -7.0, -7.5),
        recommended_keys_modes=["Eb Minor", "Bb Minor", "F Minor", "Db Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Detroit Knock Kit", "808 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Aggressive Grand Piano", "808 Sub Punch", "Bell Synth Lead"],
        insert_fx=["FabFilter Saturn 2", "Glue Compressor", "Utility"],
        turnaround_bars=4
    ),
    "hiphop_boombap": GenreAcousticProfile(
        id="hiphop_boombap",
        name="Hip-Hop Boom Bap",
        family="Urban_HipHop",
        description="90s golden era boom-bap with crunchy MPC swing, filtered jazz samples, punchy acoustic kicks and cracked snares.",
        bpm_range=(84.0, 96.0, 90.0),
        target_lufs=(-11.0, -9.0, -10.0),
        recommended_keys_modes=["A Minor", "D Minor", "G Minor", "E Dorian"],
        channel_density=(7, 10, 14),
        drum_kits=["MPC 60 Vinyl Kit", "Vintage Dry Kit", "Acoustic Break Kit"],
        groove_style="mpc_60",
        groove_swing_pct=58.0,
        instruments=["Upright Acoustic Bass", "Rhodes MK1", "Vinyl Horn Chops", "Vinyl Crackle Bed"],
        insert_fx=["Tape J-37", "RC-20 Retro Color", "FabFilter Pro-Q 4", "Glue Compressor"],
        turnaround_bars=8
    ),
    "westcoast_gfunk": GenreAcousticProfile(
        id="westcoast_gfunk",
        name="West Coast G-Funk",
        family="Urban_HipHop",
        description="Laid-back Los Angeles funk with portamento sine leads, bouncy Moog bass, and loose acoustic percussion.",
        bpm_range=(90.0, 104.0, 95.0),
        target_lufs=(-11.0, -9.0, -9.8),
        recommended_keys_modes=["D Minor", "G Minor", "E Minor", "B Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["LinnDrum Classic", "West Coast Funk Kit", "Vintage 70s Kit"],
        groove_style="dilla_drunk",
        groove_swing_pct=54.0,
        instruments=["Portamento Sine Lead (Drift)", "Minimoog Bouncy Bass", "Fender Rhodes", "Funk Rhythm Guitar"],
        insert_fx=["Tape MELLO-FI", "ValhallaVintageVerb", "FabFilter Pro-C 3"],
        turnaround_bars=8
    ),
    "memphis_phonk": GenreAcousticProfile(
        id="memphis_phonk",
        name="Memphis Phonk",
        family="Urban_HipHop",
        description="Lo-fi cassette tape dark phonk with cowbell melodies, distorted 808s, and vintage vocal loop chops.",
        bpm_range=(125.0, 145.0, 134.0),
        target_lufs=(-8.0, -6.5, -7.2),
        recommended_keys_modes=["C Minor", "F# Minor", "D Minor", "A# Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["Roland TR-808 Tape", "Phonk Cowbell Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Distorted 808 Sub", "Memphis 808 Cowbell", "Vintage Soul Chops", "Dark Choir"],
        insert_fx=["FabFilter Saturn 2", "RC-20 Retro Color", "Tape J-37", "Limiter"],
        turnaround_bars=8
    ),
    "plugg": GenreAcousticProfile(
        id="plugg",
        name="Plugg",
        family="Urban_HipHop",
        description="Chill ethereal trap with jazz chords, Roland sound canvas plucks, sparse offbeat 808, and light hi-hat patterns.",
        bpm_range=(130.0, 146.0, 138.0),
        target_lufs=(-10.0, -8.5, -9.0),
        recommended_keys_modes=["Db Major", "Ab Major", "F# Minor", "Eb Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["Plugg Trap Kit", "808 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Roland Jazz Pluck", "808 Sub Sine", "Lush Rhodes", "Celeste Bells"],
        insert_fx=["ValhallaVintageVerb", "FabFilter Saturn 2", "Tape MELLO-FI"],
        turnaround_bars=8
    ),
    "rage": GenreAcousticProfile(
        id="rage",
        name="Rage",
        family="Urban_HipHop",
        description="Hyper-energetic synth-heavy trap inspired by Playboi Carti and Pierre Bourne with blown-out supersaws and fuzzy 808s.",
        bpm_range=(140.0, 160.0, 148.0),
        target_lufs=(-8.0, -6.5, -7.0),
        recommended_keys_modes=["D# Minor", "C Minor", "F Minor", "A Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Rage Overdrive Kit", "808 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Overdriven Supersaw (Vital)", "Fuzz 808 Sub", "Hyper Arp Lead", "Staccato Bell"],
        insert_fx=["Xfer Records OTT", "FabFilter Saturn 2", "Pro-Q 4", "ValhallaVintageVerb"],
        turnaround_bars=8
    ),
    "industrial_hiphop": GenreAcousticProfile(
        id="industrial_hiphop",
        name="Industrial Hip-Hop",
        family="Urban_HipHop",
        description="Abrasive metallic hip-hop inspired by Yeezus and Death Grips with distorted synths, heavy noise sweeps, and mechanical beats.",
        bpm_range=(85.0, 120.0, 105.0),
        target_lufs=(-8.0, -6.5, -7.0),
        recommended_keys_modes=["E Minor", "D Minor", "F# Minor", "C Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["Industrial Metallic Kit", "Distorted Electronic Drum"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Distorted Acid Bass", "Metallic Percussion", "Screaming Modular Lead", "Low Drone Pad"],
        insert_fx=["FabFilter Saturn 2", "OTT", "Tape J-37", "Compressor"],
        turnaround_bars=4
    ),

    # ── 2. LATIN & URBAN (11-18) ──────────────────────────────────────────────
    "reggaeton_clasico": GenreAcousticProfile(
        id="reggaeton_clasico",
        name="Reggaeton Clásico",
        family="Latin_Urban",
        description="Authentic Puerto Rican Dembow rhythm with tight kick and percussive rim-snare countertime, warm sub-bass, and brass stabs.",
        bpm_range=(90.0, 100.0, 94.0),
        target_lufs=(-9.0, -7.5, -8.2),
        recommended_keys_modes=["F Minor", "G Minor", "C Minor", "A# Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Dembow Real Kit", "Classic Dembow Core", "Puerto Rico Percussion"],
        groove_style="reggaeton_dembow",
        groove_swing_pct=48.0,
        instruments=["Deep Sub 808", "Orchestral Brass Stab", "Minor Acoustic Piano", "Timbal Fills"],
        insert_fx=["Glue Compressor", "FabFilter Saturn 2", "ValhallaPlate", "FabFilter Pro-DS"],
        turnaround_bars=8
    ),
    "neoperreo": GenreAcousticProfile(
        id="neoperreo",
        name="Neo-Perreo / Dark Reggaeton",
        family="Latin_Urban",
        description="Underground dark reggaeton fused with rave synthesis, industrial kicks, glitched vocal chops, and deep sub-pressure.",
        bpm_range=(95.0, 110.0, 102.0),
        target_lufs=(-8.5, -7.0, -7.8),
        recommended_keys_modes=["D Minor", "C# Minor", "F Minor", "G Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["Industrial Dembow Kit", "Dark Perreo Drums"],
        groove_style="reggaeton_dembow",
        groove_swing_pct=46.0,
        instruments=["Reese Bass Sub", "Dark Metallic Synth Lead", "Distorted Vocal Chops", "Rave Pluck"],
        insert_fx=["FabFilter Saturn 2", "OTT", "Tape MELLO-FI", "ValhallaVintageVerb"],
        turnaround_bars=8
    ),
    "rkt": GenreAcousticProfile(
        id="rkt",
        name="RKT / Cumbia 420",
        family="Latin_Urban",
        description="Argentine urban sound mixing cumbia villera rhythm with heavy 808 bass, dembow syncopation, and comedic vocal drops.",
        bpm_range=(92.0, 104.0, 98.0),
        target_lufs=(-8.5, -7.0, -7.8),
        recommended_keys_modes=["C Minor", "D Minor", "A Minor", "F Minor"],
        channel_density=(7, 11, 15),
        drum_kits=["RKT Argentina Kit", "Cumbia 420 Drums"],
        groove_style="reggaeton_dembow",
        groove_swing_pct=45.0,
        instruments=["808 Dragged Sub", "Acordeón Villero Synth", "Guiro & Congas", "Siren FX"],
        insert_fx=["FabFilter Saturn 2", "Glue Compressor", "ValhallaRoom"],
        turnaround_bars=8
    ),
    "dancehall": GenreAcousticProfile(
        id="dancehall",
        name="Dancehall Moderno",
        family="Latin_Urban",
        description="Jamaican riddim foundations with rolling percussion, bouncy basslines, and syncopated snare placements.",
        bpm_range=(96.0, 108.0, 102.0),
        target_lufs=(-9.5, -8.0, -8.6),
        recommended_keys_modes=["G Minor", "C Minor", "F Minor", "D Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Kingston Riddim Kit", "Acoustic Percussion Kit"],
        groove_style="reggaeton_dembow",
        groove_swing_pct=50.0,
        instruments=["Sine Sub-Bass", "Riddim Organ Chops", "Steel Pan / Marimba", "Dub Horns"],
        insert_fx=["ValhallaDelay", "Tape J-37", "Glue Compressor"],
        turnaround_bars=8
    ),
    "afrobeat": GenreAcousticProfile(
        id="afrobeat",
        name="Afrobeat",
        family="Latin_Urban",
        description="Polyrhythmic West African groove with syncopated log drums, shakers, warm electric guitar plucks, and brass melodies.",
        bpm_range=(100.0, 114.0, 106.0),
        target_lufs=(-10.5, -8.5, -9.2),
        recommended_keys_modes=["F# Minor", "C# Minor", "A Minor", "E Dorian"],
        channel_density=(10, 16, 22),
        drum_kits=["Afro Percussion Kit", "Lagos Groove Drums", "Organic Shakers"],
        groove_style="mpc_60",
        groove_swing_pct=56.0,
        instruments=["Electric Bass Fingers", "Highlife Rhythm Guitar", "Femi Brass Section", "Warm MKS-20 Piano"],
        insert_fx=["Tape MELLO-FI", "ValhallaRoom", "FabFilter Pro-Q 4", "Glue Compressor"],
        turnaround_bars=8
    ),
    "amapiano": GenreAcousticProfile(
        id="amapiano",
        name="Amapiano",
        family="Latin_Urban",
        description="South African deep house hybrid featuring iconic pitched log drum basslines, jazzy piano chords, and airy shaker grooves.",
        bpm_range=(110.0, 118.0, 113.0),
        target_lufs=(-9.5, -8.0, -8.8),
        recommended_keys_modes=["Eb Minor", "Ab Minor", "Db Major", "Bb Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["Amapiano Log Drum Kit", "Jozi House Percussion"],
        groove_style="ukg_2step",
        groove_swing_pct=54.0,
        instruments=["Pitched Log Drum Bass", "Jazzy Grand Piano", "Warm Rhodes", "Airy Whistle Lead"],
        insert_fx=["FabFilter Pro-MB", "ValhallaVintageVerb", "Tape J-37"],
        turnaround_bars=8
    ),
    "mambo_urbano": GenreAcousticProfile(
        id="mambo_urbano",
        name="Mambo Urbano",
        family="Latin_Urban",
        description="High-velocity Dominican street mambo with aggressive güira, acoustic brass section, and slap/percussive bass.",
        bpm_range=(135.0, 160.0, 148.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["C Minor", "G Minor", "D Minor", "F Major"],
        channel_density=(8, 12, 16),
        drum_kits=["Mambo Dominicano Kit", "Tambora & Guira Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Slap Electric Bass", "Mambo Brass Section", "Acoustic Piano Chops", "Dominican Güira"],
        insert_fx=["Glue Compressor", "FabFilter Saturn 2", "Pro-DS"],
        turnaround_bars=4
    ),
    "latin_pop": GenreAcousticProfile(
        id="latin_pop",
        name="Latin Pop",
        family="Latin_Urban",
        description="Polished commercial radio pop with acoustic guitars, punchy hybrid drums, wide vocal harmonies, and melodic hooks.",
        bpm_range=(98.0, 124.0, 112.0),
        target_lufs=(-10.0, -8.5, -9.0),
        recommended_keys_modes=["G Major", "D Major", "B Minor", "E Minor"],
        channel_density=(10, 16, 24),
        drum_kits=["Pop Acoustic Hybrid Kit", "Modern Radio Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Nylon Acoustic Guitar", "Electric Bass Warm", "Grand Piano", "Lush Synth Pad"],
        insert_fx=["FabFilter Pro-DS", "ValhallaVintageVerb", "FabFilter Pro-C 3", "Tape MELLO-FI"],
        turnaround_bars=8
    ),

    # ── 3. POP & ALTERNATIVE (19-26) ──────────────────────────────────────────
    "dark_asmr_pop": GenreAcousticProfile(
        id="dark_asmr_pop",
        name="Dark ASMR Minimal Pop",
        family="Pop_Alternative",
        description="Finneas / Billie Eilish sonic aesthetic: ultra-dry intimate whispered vocals, sub-sine bass, close acoustic transients, and minimal clutter.",
        bpm_range=(115.0, 140.0, 135.0),
        target_lufs=(-14.0, -11.5, -12.5),
        recommended_keys_modes=["G Minor", "C Minor", "D Minor", "B Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["Acoustic Percussion Core", "Fingersnap & ASMR Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Deep Sine Sub (Clean)", "Felt Piano Upright", "Whispered Pluck Bell", "Ghost Air Texture"],
        insert_fx=["FabFilter Pro-DS", "Tape MELLO-FI", "RC-20 Retro Color", "Utility (Pure Mono Bass)"],
        turnaround_bars=8
    ),
    "bedroom_pop": GenreAcousticProfile(
        id="bedroom_pop",
        name="Bedroom Pop / Indie Lo-Fi",
        family="Pop_Alternative",
        description="Rusowsky / Boy Pablo aesthetic: detuned cassette tape wow/flutter, chorus electric guitars, warm vintage drum boxes, and melancholic chords.",
        bpm_range=(75.0, 95.0, 84.0),
        target_lufs=(-13.0, -11.0, -12.0),
        recommended_keys_modes=["C Major", "F Major", "A Minor", "D Dorian"],
        channel_density=(8, 12, 16),
        drum_kits=["Vintage Dry Drum Machine", "CR-78 Drum Box"],
        groove_style="dilla_drunk",
        groove_swing_pct=56.0,
        instruments=["Detuned Chorus Guitar", "Mellotron Flute", "Wurli V3 Electric Piano", "Warm Tape Bass"],
        insert_fx=["RC-20 Retro Color", "Tape MELLO-FI", "ValhallaVintageVerb", "FabFilter Saturn 2"],
        turnaround_bars=8
    ),
    "hyperpop": GenreAcousticProfile(
        id="hyperpop",
        name="Hyperpop / Glitchcore",
        family="Pop_Alternative",
        description="Pitch-shifted vocals, distorted metallic supersaws, abrasive 808s, maximalist fills, and unpredictable tempo/beat switches.",
        bpm_range=(140.0, 180.0, 158.0),
        target_lufs=(-7.5, -6.0, -6.8),
        recommended_keys_modes=["F# Major", "E Major", "B Major", "C# Minor"],
        channel_density=(10, 18, 26),
        drum_kits=["Hyper Glitch Kit", "Electronic Core Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Vital Wavetable Supersaw", "Distorted Square 808", "Toy Key Pluck", "Laser FX"],
        insert_fx=["Xfer Records OTT", "FabFilter Saturn 2", "ValhallaSpaceModulator", "LittleAlterBoy"],
        turnaround_bars=4
    ),
    "synthwave": GenreAcousticProfile(
        id="synthwave",
        name="Synthwave / Retrowave",
        family="Pop_Alternative",
        description="80s cinematic outrun aesthetic: gated LinnDrum snares, running analog arpeggios, Juno-106 chorus pads, and driving synth basslines.",
        bpm_range=(110.0, 130.0, 120.0),
        target_lufs=(-10.0, -8.5, -9.0),
        recommended_keys_modes=["A Minor", "D Minor", "F Minor", "E Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["LinnDrum Gated Reverb", "Simmons Electronic Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Analog Arp Bass (Drift)", "Juno Lush Pad", "80s Polysynth Brass", "Bright Lead Synth"],
        insert_fx=["ValhallaVintageVerb", "FabFilter Saturn 2", "Glue Compressor", "Tape J-37"],
        turnaround_bars=8
    ),
    "nudisco_dancepop": GenreAcousticProfile(
        id="nudisco_dancepop",
        name="Nu-Disco / Dance-Pop",
        family="Pop_Alternative",
        description="Dua Lipa / Future Nostalgia aesthetic: driving four-on-the-floor kick, slap funk bassline, disco strings, and Nile Rodgers rhythm guitar.",
        bpm_range=(118.0, 126.0, 124.0),
        target_lufs=(-9.0, -7.5, -8.2),
        recommended_keys_modes=["B Minor", "F# Minor", "D Major", "A Minor"],
        channel_density=(10, 16, 22),
        drum_kits=["Disco Machine Kit", "Classic 70s Funk Kit"],
        groove_style="ukg_2step",
        groove_swing_pct=52.0,
        instruments=["Slap Electric Bass (Active)", "Chic Rhythm Guitar", "Disco Strings Section", "Rhodes MK2"],
        insert_fx=["Glue Compressor", "FabFilter Pro-C 3", "ValhallaPlate", "FabFilter Saturn 2"],
        turnaround_bars=8
    ),
    "synthpop_80s": GenreAcousticProfile(
        id="synthpop_80s",
        name="Synth-Pop (80s After Hours)",
        family="Pop_Alternative",
        description="The Weeknd / Max Martin sound: huge gated snare, warm analog Prophet-5 chords, soaring lead vocals with plate reverb, and sidechained bass.",
        bpm_range=(115.0, 132.0, 122.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["F Minor", "Ab Major", "C Minor", "Eb Major"],
        channel_density=(10, 16, 22),
        drum_kits=["DMX Gated 80s Kit", "After Hours Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Prophet Brass Chord", "Analog Bassline (Drift)", "DX7 Electric Piano", "Shimmer Vocal Pad"],
        insert_fx=["ValhallaVintageVerb", "FabFilter Pro-DS", "FabFilter Saturn 2", "OTT"],
        turnaround_bars=8
    ),
    "neosoul_rnb": GenreAcousticProfile(
        id="neosoul_rnb",
        name="Neo-Soul / Contemporary R&B",
        family="Pop_Alternative",
        description="J Dilla / Erykah Badu / Tyler aesthetic: drunken micro-timing, extended jazz chords (9th, 11th, 13th), Rhodes MK1, and warm vocal layers.",
        bpm_range=(76.0, 96.0, 86.0),
        target_lufs=(-12.0, -9.5, -10.5),
        recommended_keys_modes=["Db Major", "Ab Major", "Eb Dorian", "F Minor"],
        channel_density=(8, 14, 20),
        drum_kits=["Dilla Drunk Kit", "MPC 60 Vinyl Drums"],
        groove_style="dilla_drunk",
        groove_swing_pct=62.0,
        instruments=["Rhodes Stage 73", "Warm Fingerstyle Bass", "Muted Jazz Trumpet", "Velvet Vocal Choir"],
        insert_fx=["Tape J-37", "RC-20 Retro Color", "ValhallaVintageVerb", "FabFilter Pro-C 3"],
        turnaround_bars=8
    ),
    "uk_garage": GenreAcousticProfile(
        id="uk_garage",
        name="UK Garage / 2-Step",
        family="Electronic_Club",
        description="Mura Masa / Fred again.. aesthetic: syncopated 2-step skippy rhythm with 58-62% swing, Korg M1 organ bass, and pitched vocal chops.",
        bpm_range=(130.0, 138.0, 134.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["A Minor", "F Minor", "D Minor", "C Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["UKG 2-Step Core Kit", "909 Garage Drums"],
        groove_style="ukg_2step",
        groove_swing_pct=60.0,
        instruments=["Korg M1 Organ Bass", "Pitched Vocal Chops", "Vinyl Rhodes Stabs", "Skippy Shakers"],
        insert_fx=["Glue Compressor", "ValhallaVintageVerb", "FabFilter Saturn 2", "Sidechain Ducking"],
        turnaround_bars=8
    ),

    # ── 4. ELECTRONIC & DANCE (27-36) ─────────────────────────────────────────
    "future_bass": GenreAcousticProfile(
        id="future_bass",
        name="Future Bass",
        family="Electronic_Club",
        description="Lush sidechained supersaw chords with fast LFO pitch/filter modulations, 808 sub, acoustic percussion foley, and vocal chops.",
        bpm_range=(135.0, 160.0, 150.0),
        target_lufs=(-8.0, -6.5, -7.2),
        recommended_keys_modes=["F Major", "C Major", "Ab Major", "Eb Major"],
        channel_density=(10, 18, 24),
        drum_kits=["Future Bass Core Kit", "Electronic Trap Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["LFO Wobble Supersaw (Vital)", "Intelligent 808 Sub", "Bell Pluck Melody", "Foley Percussion Bed"],
        insert_fx=["Xfer Records OTT", "FabFilter Saturn 2", "ValhallaShimmer", "Sidechain Gate"],
        turnaround_bars=8
    ),
    "melodic_dubstep": GenreAcousticProfile(
        id="melodic_dubstep",
        name="Melodic Dubstep",
        family="Electronic_Club",
        description="Seven Lions / Illenium sound: epic cinematic piano intro, massive emotional supersaws, heavy half-time snare, and aggressive sub growls.",
        bpm_range=(138.0, 150.0, 140.0),
        target_lufs=(-7.5, -6.0, -6.8),
        recommended_keys_modes=["F# Minor", "D Minor", "B Minor", "A# Minor"],
        channel_density=(10, 18, 26),
        drum_kits=["Heavy Dubstep Drums", "Punchy Acoustic Hybrid Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Emotional Supersaw Stack", "Cinematic Grand Piano", "Sub Bass 808", "Vocal Atmosphere"],
        insert_fx=["Xfer Records OTT", "ValhallaShimmer", "FabFilter Pro-Q 4", "Glue Compressor"],
        turnaround_bars=8
    ),
    "brostep": GenreAcousticProfile(
        id="brostep",
        name="Heavy Brostep / Tearout",
        family="Electronic_Club",
        description="Skrillex / Zomboy aesthetic: violent wavetable formant growls, aggressive FM screeches, machine-gun bass rhythms, and devastating sub drops.",
        bpm_range=(140.0, 150.0, 140.0),
        target_lufs=(-7.0, -5.5, -6.2),
        recommended_keys_modes=["F Minor", "E Minor", "D# Minor", "C Minor"],
        channel_density=(8, 16, 24),
        drum_kits=["Heavy Brostep Snare Kit", "Punchy EDM Kick Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Vital Formant Growl", "FM Screech Bass", "Sub Bass Clean Sine", "Industrial Riser"],
        insert_fx=["Xfer Records OTT", "FabFilter Saturn 2", "Pro-MB", "Limiter"],
        turnaround_bars=4
    ),
    "drum_and_bass": GenreAcousticProfile(
        id="drum_and_bass",
        name="Drum and Bass / Liquid D&B",
        family="Electronic_Club",
        description="Fast 174 BPM breakbeats with syncopated ghost snares, rolling 808 Reese bass, and atmospheric soul chords.",
        bpm_range=(170.0, 178.0, 174.0),
        target_lufs=(-8.0, -6.5, -7.2),
        recommended_keys_modes=["F Minor", "E Minor", "G Minor", "C Minor"],
        channel_density=(8, 14, 20),
        drum_kits=["Amen Break Sliced Kit", "Modern DnB Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Reese Bass (Polyphonic Glide)", "Liquid Rhodes Chops", "Airy Vocal Pad", "Sub Bass 40Hz"],
        insert_fx=["FabFilter Saturn 2", "OTT", "ValhallaVintageVerb", "Sidechain Ducking"],
        turnaround_bars=16
    ),
    "tech_house": GenreAcousticProfile(
        id="tech_house",
        name="Tech House",
        family="Electronic_Club",
        description="Driving 126-128 BPM club groove with punchy four-on-the-floor kick, rolling sub bassline, crisp claps, and quirky vocal stabs.",
        bpm_range=(124.0, 130.0, 126.0),
        target_lufs=(-8.0, -6.5, -7.2),
        recommended_keys_modes=["G Minor", "A Minor", "D Minor", "F# Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["909 Core Kit (.adg)", "Tech House Drums", "Latin Percussion Box"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["FM Rolling Bass (Drift)", "Quirky Vocal Chop", "Percussive Synth Stab", "White Noise Sweep"],
        insert_fx=["Glue Compressor", "FabFilter Saturn 2", "ValhallaRoom", "Sidechain Ducking"],
        turnaround_bars=16
    ),
    "melodic_techno": GenreAcousticProfile(
        id="melodic_techno",
        name="Melodic Techno / Peak Time",
        family="Electronic_Club",
        description="Tale of Us / Afterlife sound: hypnotic rolling arpeggiated bass, dark evolving synth motifs, cinematic brass swells, and deep sub kick.",
        bpm_range=(122.0, 128.0, 125.0),
        target_lufs=(-8.5, -7.0, -7.8),
        recommended_keys_modes=["C Minor", "D Minor", "G Minor", "Eb Minor"],
        channel_density=(8, 14, 20),
        drum_kits=["Analog Techno Kick Kit", "909 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Moog Rolling Bass Arp", "Dark Saw Pad Swell", "Pluck Lead (Drift)", "Drone Sub"],
        insert_fx=["ValhallaVintageVerb", "FabFilter Saturn 2", "Tape MELLO-FI", "Pro-Q 4"],
        turnaround_bars=16
    ),
    "hard_techno": GenreAcousticProfile(
        id="hard_techno",
        name="Hard Techno / Industrial Techno",
        family="Electronic_Club",
        description="150+ BPM relentless industrial rumble kick, metallic percussions, distorted acid 303 bass, and dark warehouse reverb atmosphere.",
        bpm_range=(145.0, 165.0, 155.0),
        target_lufs=(-7.5, -6.0, -6.5),
        recommended_keys_modes=["F Minor", "D Minor", "E Minor", "B Minor"],
        channel_density=(6, 12, 16),
        drum_kits=["Industrial Rumble Kick Kit", "Distorted 909 Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Rumble Sub Kick", "Acid 303 Bassline", "Metallic Shaker", "Industrial Noise FX"],
        insert_fx=["FabFilter Saturn 2", "OTT", "ValhallaVintageVerb", "Limiter"],
        turnaround_bars=8
    ),
    "deep_house": GenreAcousticProfile(
        id="deep_house",
        name="Deep House",
        family="Electronic_Club",
        description="Warm soulful house with subby sine bass, vintage electric piano chords, smooth muted hi-hats, and vocal whispers.",
        bpm_range=(118.0, 124.0, 122.0),
        target_lufs=(-10.5, -9.0, -9.5),
        recommended_keys_modes=["Eb Minor", "Bb Minor", "Db Major", "F Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Warm Deep House Kit", "Analog 808/909 Hybrid"],
        groove_style="mpc_60",
        groove_swing_pct=54.0,
        instruments=["Sub Sine Bass Warm", "Rhodes MK1 Chords", "Muted Trumpet", "Atmosphere Vinyl"],
        insert_fx=["Tape J-37", "ValhallaRoom", "Glue Compressor"],
        turnaround_bars=8
    ),
    "jersey_club": GenreAcousticProfile(
        id="jersey_club",
        name="Jersey Club",
        family="Electronic_Club",
        description="Bouncy syncopated kick pattern (boom... boom-boom-boom-boom), bed squeak sample, water drops, and vocal chop energy.",
        bpm_range=(130.0, 145.0, 138.0),
        target_lufs=(-8.5, -7.0, -7.5),
        recommended_keys_modes=["C Minor", "F Minor", "G Minor", "A Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["Jersey Club Bouncy Kit", "Urban Percussion Box"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["808 Punch Bass", "Squeak & Water Drop FX", "Vocal Staccato Chops", "Piano Stabs"],
        insert_fx=["FabFilter Saturn 2", "Glue Compressor", "ValhallaRoom"],
        turnaround_bars=4
    ),
    "brazilian_phonk": GenreAcousticProfile(
        id="brazilian_phonk",
        name="Brazilian Phonk / Funk Mandelão",
        family="Electronic_Club",
        description="Montagem aesthetic: distorted metallic funk kick, heavy cowbell melodies, Brazilian vocal drops, and crushed aggressive bass.",
        bpm_range=(125.0, 135.0, 130.0),
        target_lufs=(-7.0, -5.5, -6.2),
        recommended_keys_modes=["C Minor", "D Minor", "F# Minor", "A Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["Funk Mandelo Kit", "Phonk Aggressive Box"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Overdriven Mandelao Bass", "Phonk Cowbell Stabs", "Vocal Shouts", "Laser Sweeps"],
        insert_fx=["FabFilter Saturn 2", "OTT", "Pro-Q 4", "Limiter"],
        turnaround_bars=4
    ),

    # ── 5. ROCK & INDIE (37-44) ───────────────────────────────────────────────
    "indie_rock": GenreAcousticProfile(
        id="indie_rock",
        name="Indie Rock / Alternative Rock",
        family="Rock_Guitars",
        description="Dynamic raw rock with driven rhythm guitars, punchy acoustic kit, melodic bassline, and heartfelt vocal delivery.",
        bpm_range=(110.0, 145.0, 128.0),
        target_lufs=(-11.0, -9.0, -9.8),
        recommended_keys_modes=["A Major", "E Major", "D Major", "F# Minor"],
        channel_density=(8, 14, 20),
        drum_kits=["Vintage Dry Kit", "Acoustic Rock Kit", "Session Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Overdriven Electric Guitar (L/R)", "P-Bass Roundwound", "Telecaster Lead", "Acoustic Tambourine"],
        insert_fx=["FabFilter Saturn 2", "Tape J-37", "ValhallaVintageVerb", "Glue Compressor"],
        turnaround_bars=8
    ),
    "post_punk": GenreAcousticProfile(
        id="post_punk",
        name="Post-Punk / Darkwave",
        family="Rock_Guitars",
        description="Joy Division / The Cure aesthetic: driving chorus bass lead, cold drum machine rhythm, jagged flanged guitars, and hollow reverb vocals.",
        bpm_range=(120.0, 145.0, 132.0),
        target_lufs=(-11.5, -9.5, -10.2),
        recommended_keys_modes=["A Minor", "E Minor", "D Minor", "B Minor"],
        channel_density=(7, 12, 16),
        drum_kits=["LinnDrum Classic", "Acoustic Dry Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Chorus Electric Bass (High Register)", "Flanged Rhythm Guitar", "Analog Synth Drone", "Cold Snare"],
        insert_fx=["ValhallaVintageVerb", "Tape MELLO-FI", "Pro-Q 4", "Compressor"],
        turnaround_bars=8
    ),
    "pop_punk": GenreAcousticProfile(
        id="pop_punk",
        name="Pop Punk Moderno",
        family="Rock_Guitars",
        description="Blink-182 / Travis Barker modern pop punk: blazing fast drums, wall-of-sound distorted guitars, high-energy bass, and anthemic hooks.",
        bpm_range=(150.0, 185.0, 165.0),
        target_lufs=(-8.5, -7.0, -7.6),
        recommended_keys_modes=["E Major", "B Major", "A Major", "C# Minor"],
        channel_density=(10, 16, 24),
        drum_kits=["Acoustic Rock Kit", "Heavy Transient Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Double-Tracked Distorted Guitars", "Punchy Precision Bass", "Lead Guitar Octaves", "Rock Crash Cymbals"],
        insert_fx=["FabFilter Saturn 2", "Glue Compressor", "FabFilter Pro-DS", "Pro-Q 4"],
        turnaround_bars=4
    ),
    "grunge_numetal": GenreAcousticProfile(
        id="grunge_numetal",
        name="Grunge / Nu-Metal",
        family="Rock_Guitars",
        description="Linkin Park / Deftones aesthetic: drop-D detuned high-gain guitars, heavy room drums, aggressive bass growl, and hip-hop turntable textures.",
        bpm_range=(85.0, 120.0, 105.0),
        target_lufs=(-8.5, -7.0, -7.6),
        recommended_keys_modes=["D Minor", "C Minor", "E Minor", "A Minor"],
        channel_density=(10, 16, 22),
        drum_kits=["Acoustic Rock Kit", "Heavy Room Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Drop-D Distorted Rhythm Guitar", "Distorted Bass Guitar", "Atmospheric Synth Pad", "Vinyl Scratch Bed"],
        insert_fx=["FabFilter Saturn 2", "Glue Compressor", "ValhallaRoom", "FabFilter Pro-DS"],
        turnaround_bars=8
    ),
    "math_rock": GenreAcousticProfile(
        id="math_rock",
        name="Math Rock / Progressive Guitar",
        family="Rock_Guitars",
        description="Chon / Covet aesthetic: complex metric shifts, two-hand tapping clean guitars, harmonic polyphonic bass chords, and organic ghost-note drums.",
        bpm_range=(110.0, 140.0, 125.0),
        time_signature=(7, 8),
        target_lufs=(-12.0, -10.0, -11.0),
        recommended_keys_modes=["E Major", "A Major", "F# Dorian", "D Lydian"],
        channel_density=(8, 14, 18),
        drum_kits=["Vintage Dry Kit", "Acoustic Percussion Core"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Tapping Clean Electric Guitar", "Polyphonic Harmonic Bass", "Acoustic Snare Ghost Notes", "Felt Keys"],
        insert_fx=["Tape MELLO-FI", "ValhallaRoom", "FabFilter Pro-C 3"],
        turnaround_bars=7
    ),
    "psychedelic_rock": GenreAcousticProfile(
        id="psychedelic_rock",
        name="Psychedelic Rock / Dream Pop",
        family="Rock_Guitars",
        description="Tame Impala aesthetic: heavy tape flanger on drums, fuzzy bass through guitar pedal, dreamy chorus synths, and saturated falsetto vocals.",
        bpm_range=(105.0, 125.0, 116.0),
        target_lufs=(-11.0, -9.0, -10.0),
        recommended_keys_modes=["A Minor", "D Minor", "F# Minor", "C Major"],
        channel_density=(10, 16, 22),
        drum_kits=["Vintage 70s Dry Kit", "Tape Compressed Drums"],
        groove_style="mpc_60",
        groove_swing_pct=54.0,
        instruments=["Höfner Flatwound Bass", "Fuzz Overdriven Guitar", "Juno Analog Pad", "Phased Drum Bus"],
        insert_fx=["Tape J-37", "RC-20 Retro Color", "ValhallaVintageVerb", "FabFilter Saturn 2"],
        turnaround_bars=8
    ),
    "shoegaze": GenreAcousticProfile(
        id="shoegaze",
        name="Shoegaze / Ambient Rock",
        family="Rock_Guitars",
        description="My Bloody Valentine aesthetic: wall of glide guitar feedback, washed reverse reverb, buried intimate vocals, and loud driving drums.",
        bpm_range=(95.0, 125.0, 112.0),
        target_lufs=(-10.5, -8.5, -9.2),
        recommended_keys_modes=["E Major", "A Major", "D Major", "F# Minor"],
        channel_density=(10, 16, 24),
        drum_kits=["Heavy Room Drums", "Acoustic Rock Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Glide Feedback Guitar Wall", "Warm P-Bass", "Mellotron Strings", "Ambient Vocal Wash"],
        insert_fx=["ValhallaSupermassive", "FabFilter Saturn 2", "ValhallaShimmer", "Pro-C 3"],
        turnaround_bars=8
    ),
    "emo_rap": GenreAcousticProfile(
        id="emo_rap",
        name="Emo Rap / Alternative Trap",
        family="Rock_Guitars",
        description="Juice WRLD / Lil Peep aesthetic: melancholic acoustic/electric guitar arpeggios, heavy 808 bass, and emotionally charged autotune vocals.",
        bpm_range=(120.0, 145.0, 132.0),
        target_lufs=(-9.0, -7.5, -8.2),
        recommended_keys_modes=["C# Minor", "A Minor", "F# Minor", "E Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["808 Core Kit (.adg)", "Emo Trap Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Sad Acoustic Guitar Arp", "Intelligent 808 Sub", "Trap Hi-Hat Rolls", "Ambient Vocal Pad"],
        insert_fx=["FabFilter Saturn 2", "ValhallaVintageVerb", "FabFilter Pro-DS", "Pro-Q 4"],
        turnaround_bars=8
    ),

    # ── 6. LO-FI, AMBIENT & EXPERIMENTAL (45-52) ──────────────────────────────
    "chillhop": GenreAcousticProfile(
        id="chillhop",
        name="Chillhop / Study Beats Lo-Fi",
        family="Lofi_Ambient",
        description="Peaceful study beats with vinyl dust, nostalgic jazz piano chords, unquantized dusty boom bap kick/snare, and warm upright bass.",
        bpm_range=(70.0, 88.0, 80.0),
        target_lufs=(-13.0, -11.0, -12.0),
        recommended_keys_modes=["Eb Major", "Ab Major", "Db Major", "C Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["Dusty Vinyl Drum Box", "MPC 60 Vinyl Kit"],
        groove_style="dilla_drunk",
        groove_swing_pct=60.0,
        instruments=["Rhodes Stage 73", "Upright Bass Acoustic", "Vinyl Crackle Bed", "Muted Trumpet Chops"],
        insert_fx=["RC-20 Retro Color", "Tape MELLO-FI", "Tape J-37"],
        turnaround_bars=8
    ),
    "ambient": GenreAcousticProfile(
        id="ambient",
        name="Ambient / Cinematic Soundscapes",
        family="Lofi_Ambient",
        description="Brian Eno / Hans Zimmer aesthetic: beatless evolving soundscapes, shimmering granular pads, sub-drone textures, and vast spatial reverbs.",
        bpm_range=(50.0, 80.0, 65.0),
        target_lufs=(-16.0, -13.0, -14.5),
        recommended_keys_modes=["D Dorian", "A Aeolian", "F Lydian", "C Major"],
        channel_density=(6, 12, 16),
        drum_kits=[],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Granular Vocal Pad", "Sub Drone 30Hz", "Shimmer Bell Melody", "Foley Wind Bed"],
        insert_fx=["ValhallaSupermassive", "ValhallaShimmer", "FabFilter Pro-Q 4"],
        turnaround_bars=16
    ),
    "triphop": GenreAcousticProfile(
        id="triphop",
        name="Trip-Hop (Bristol Sound)",
        family="Lofi_Ambient",
        description="Massive Attack / Portishead aesthetic: slow heavy breakbeats, dark Rhodes, cinematic strings, vinyl crackle, and haunting female vocals.",
        bpm_range=(75.0, 92.0, 82.0),
        target_lufs=(-12.0, -9.5, -10.5),
        recommended_keys_modes=["D Minor", "G Minor", "C Minor", "A Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["Vintage Breakbeat Drums", "MPC 60 Vinyl Kit"],
        groove_style="mpc_60",
        groove_swing_pct=56.0,
        instruments=["Dark Upright Bass", "Rhodes Electric Piano", "Cinematic String Ensemble", "Vinyl Crackle FX"],
        insert_fx=["Tape J-37", "ValhallaVintageVerb", "FabFilter Pro-C 3"],
        turnaround_bars=8
    ),
    "french_house": GenreAcousticProfile(
        id="french_house",
        name="French House / Filter House",
        family="Electronic_Club",
        description="Daft Punk classic sound: sampled disco loops with dramatic high-pass/low-pass filter sweeps, phasers, and pumping sidechain compression.",
        bpm_range=(118.0, 128.0, 124.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["Ab Major", "Eb Major", "Db Major", "F Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["909 Core Kit (.adg)", "Disco Machine Kit"],
        groove_style="ukg_2step",
        groove_swing_pct=52.0,
        instruments=["Filtered Disco Brass Chops", "Pumping Slap Bass", "Phased Polysynth", "Vocoder Lead"],
        insert_fx=["Glue Compressor", "FabFilter Saturn 2", "Pro-Q 4 (Filter Sweep)"],
        turnaround_bars=8
    ),
    "acid_house": GenreAcousticProfile(
        id="acid_house",
        name="Acid House (303 Acid)",
        family="Electronic_Club",
        description="Chicago classic aesthetic: Roland TB-303 squelching resonant bass, Roland TR-909 punchy rhythm, and hypnotic minimal groove.",
        bpm_range=(120.0, 130.0, 126.0),
        target_lufs=(-9.0, -7.5, -8.2),
        recommended_keys_modes=["A Minor", "D Minor", "C Minor", "E Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["909 Core Kit (.adg)", "808 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Roland TB-303 Acid Bass", "909 Open/Closed Hi-Hats", "Classic House Piano Chord"],
        insert_fx=["FabFilter Saturn 2", "ValhallaVintageVerb", "Glue Compressor"],
        turnaround_bars=8
    ),
    "electro_pop": GenreAcousticProfile(
        id="electro_pop",
        name="Electro Pop",
        family="Pop_Alternative",
        description="Commercial electro pop with punchy four-on-the-floor kicks, analog synth bass, catchy hook vocal chops, and bright lead synths.",
        bpm_range=(118.0, 128.0, 122.0),
        target_lufs=(-9.0, -7.5, -8.0),
        recommended_keys_modes=["C Major", "G Major", "A Minor", "F Major"],
        channel_density=(8, 14, 20),
        drum_kits=["Pop Electronic Hybrid", "909 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Analog Synth Bass (Drift)", "Bright Pluck Hook", "Lush Poly Pad", "Vocal Lead Stabs"],
        insert_fx=["FabFilter Pro-DS", "Xfer Records OTT", "ValhallaPlate"],
        turnaround_bars=8
    ),
    "flamenco_urbano": GenreAcousticProfile(
        id="flamenco_urbano",
        name="Flamenco Urbano / New Flamenco",
        family="Latin_Urban",
        description="Rosalía / Ralphie Choo aesthetic: palmas flamencas, cajón rítmico, nylon guitar falsetas, auto-tune vocal microtonal ornamentation, and 808 sub.",
        bpm_range=(95.0, 130.0, 110.0),
        time_signature=(6, 8),
        target_lufs=(-10.5, -8.5, -9.2),
        recommended_keys_modes=["A Phrygian", "E Phrygian", "D Phrygian", "F# Phrygian"],
        channel_density=(8, 14, 20),
        drum_kits=["Palmas & Cajón Kit", "808 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Nylon Flamenco Guitar", "Palmas Flamencas (Stereo L/R)", "Intelligent 808 Sub", "Cajón Peruano / Flamenco"],
        insert_fx=["FabFilter Pro-DS", "ValhallaRoom", "Tape MELLO-FI", "Glue Compressor"],
        turnaround_bars=12
    ),
    "corrido_tumbado": GenreAcousticProfile(
        id="corrido_tumbado",
        name="Corrido Tumbado / Bélico Urbano",
        family="Latin_Urban",
        description="Peso Pluma / Natanael Cano sound: acoustic requinto and docerola guitars, charcheta and tololoche acoustic bass, paired with trap 808 and brass.",
        bpm_range=(125.0, 145.0, 134.0),
        time_signature=(3, 4),
        target_lufs=(-9.5, -8.0, -8.6),
        recommended_keys_modes=["F# Minor", "C# Minor", "B Minor", "A Major"],
        channel_density=(8, 14, 18),
        drum_kits=["Bélico Trap Kit", "808 Core Kit (.adg)"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Acoustic Requinto Docerola", "Tololoche Acoustic Bass", "Charcheta Brass Horn", "808 Trap Sub"],
        insert_fx=["FabFilter Pro-DS", "Tape J-37", "Glue Compressor", "ValhallaRoom"],
        turnaround_bars=6
    ),

    # ── 7. WORLD, JAZZ & EXPERIMENTAL (53-60) ─────────────────────────────────
    "baile_funk": GenreAcousticProfile(
        id="baile_funk",
        name="Baile Funk / Funk Carioca",
        family="Latin_Urban",
        description="Rio de Janeiro favela sound: syncopated beat box rhythm (tamborzão), heavy sub-bass hits, brass stabs, and raw high-energy vocal shouts.",
        bpm_range=(128.0, 136.0, 130.0),
        target_lufs=(-8.0, -6.5, -7.2),
        recommended_keys_modes=["C Minor", "D Minor", "F# Minor", "A Minor"],
        channel_density=(6, 10, 14),
        drum_kits=["Tamborzao Funk Kit", "Rio Favela Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Sub Bass 808 Punch", "Brass Horn Stabs", "Vocal Energy Shouts", "Percussive Whistle"],
        insert_fx=["FabFilter Saturn 2", "Glue Compressor", "Limiter"],
        turnaround_bars=4
    ),
    "afropop": GenreAcousticProfile(
        id="afropop",
        name="Afropop",
        family="Latin_Urban",
        description="Burna Boy / Wizkid sound: commercial afrobeat fused with modern pop melodies, sweet saxophones, log drums, and clean acoustic guitars.",
        bpm_range=(100.0, 112.0, 104.0),
        target_lufs=(-10.0, -8.5, -9.0),
        recommended_keys_modes=["Db Major", "Gb Major", "Ab Major", "Bb Minor"],
        channel_density=(10, 16, 22),
        drum_kits=["Afropop Core Drums", "Organic Shaker Kit"],
        groove_style="mpc_60",
        groove_swing_pct=54.0,
        instruments=["Warm Electric Bass", "African Guitar Plucks", "Alto Saxophone Solo", "Soft Synth Pad"],
        insert_fx=["Tape MELLO-FI", "ValhallaRoom", "FabFilter Pro-DS"],
        turnaround_bars=8
    ),
    "reggae_dub": GenreAcousticProfile(
        id="reggae_dub",
        name="Reggae Dub",
        family="Latin_Urban",
        description="Heavy one-drop drums, deep round bassline, skank guitar/piano on offbeats, tape delays, and cavernous spring reverbs.",
        bpm_range=(68.0, 84.0, 76.0),
        target_lufs=(-12.0, -9.5, -10.5),
        recommended_keys_modes=["A Minor", "G Minor", "C Minor", "E Minor"],
        channel_density=(8, 12, 16),
        drum_kits=["One-Drop Reggae Kit", "Vintage Dry Kit"],
        groove_style="mpc_60",
        groove_swing_pct=56.0,
        instruments=["Deep Round Bass (Muted)", "Skank Rhythm Guitar", "Bubble Organ Chops", "Dub Horn Section"],
        insert_fx=["Delay TAPE-201", "ValhallaVintageVerb", "Tape J-37"],
        turnaround_bars=8
    ),
    "soul_gospel_chop": GenreAcousticProfile(
        id="soul_gospel_chop",
        name="Soul / Gospel Chop (College Dropout)",
        family="Urban_HipHop",
        description="Classic Kanye West aesthetic: sped-up pitched-up soul vocal samples (+5 semitones), live gospel choirs, acoustic drums, and warm bass.",
        bpm_range=(82.0, 96.0, 88.0),
        target_lufs=(-10.5, -9.0, -9.5),
        recommended_keys_modes=["Eb Major", "Ab Major", "Bb Major", "C Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["Acoustic Break Kit", "MPC 60 Vinyl Kit"],
        groove_style="mpc_60",
        groove_swing_pct=58.0,
        instruments=["Pitched Soul Vocal Sample", "Gospel Hammond B3 Organ", "Warm Electric Bass", "Orchestral Strings"],
        insert_fx=["Tape J-37", "Glue Compressor", "ValhallaRoom", "FabFilter Pro-Q 4"],
        turnaround_bars=8
    ),
    "jazz_fusion": GenreAcousticProfile(
        id="jazz_fusion",
        name="Contemporary Jazz Fusion",
        family="Pop_Alternative",
        description="Snarky Puppy / Thundercat aesthetic: virtuosic 6-string bass solos, intricate chord substitutions, live drum dynamics, and synth leads.",
        bpm_range=(95.0, 135.0, 118.0),
        target_lufs=(-13.0, -11.0, -12.0),
        recommended_keys_modes=["D Dorian", "G Dorian", "F Lydian", "Bb Major 7"],
        channel_density=(10, 16, 24),
        drum_kits=["Acoustic Jazz Dynamic Kit", "Session Drums"],
        groove_style="dilla_drunk",
        groove_swing_pct=56.0,
        instruments=["6-String Bass Melody (Thundercat)", "Rhodes Stage 73", "Moog Voyager Lead", "Brass Section"],
        insert_fx=["Tape MELLO-FI", "ValhallaRoom", "FabFilter Pro-C 3"],
        turnaround_bars=8
    ),
    "bossa_nova_moderna": GenreAcousticProfile(
        id="bossa_nova_moderna",
        name="Bossa Nova Moderna",
        family="Pop_Alternative",
        description="Subtle syncopated nylon guitar pattern, intimate whispered vocals, light rim click and shaker, warm double bass, and subtle Rhodes.",
        bpm_range=(115.0, 135.0, 124.0),
        target_lufs=(-14.0, -12.0, -13.0),
        recommended_keys_modes=["F Major 7", "D Minor 9", "G Minor 7", "C 7(b9)"],
        channel_density=(6, 10, 14),
        drum_kits=["Bossa Nova Percussion Kit", "Acoustic Brushes Kit"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Nylon Acoustic Guitar Fingerstyle", "Acoustic Upright Bass", "Rhodes MK1 Soft", "Flute Melody"],
        insert_fx=["Tape MELLO-FI", "ValhallaRoom", "FabFilter Pro-DS"],
        turnaround_bars=8
    ),
    "eurodance_90s": GenreAcousticProfile(
        id="eurodance_90s",
        name="Eurodance / 90s Dance",
        family="Electronic_Club",
        description="High-energy 90s rave dance: 138-142 BPM four-on-the-floor, Korg M1 house piano chords, fast synth arps, and punchy 909 kicks.",
        bpm_range=(135.0, 145.0, 140.0),
        target_lufs=(-8.5, -7.0, -7.5),
        recommended_keys_modes=["A Minor", "C Minor", "D Minor", "G Minor"],
        channel_density=(8, 14, 18),
        drum_kits=["909 Core Kit (.adg)", "Rave 90s Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Korg M1 House Piano", "Saw Bass Arp", "Rave Lead Synth", "Female Vocal Hook"],
        insert_fx=["Glue Compressor", "FabFilter Saturn 2", "ValhallaVintageVerb"],
        turnaround_bars=8
    ),
    "avantgarde_mutant_pop": GenreAcousticProfile(
        id="avantgarde_mutant_pop",
        name="Avant-Garde Experimental (Mutant Pop)",
        family="Pop_Alternative",
        description="Ca7riel & Paco Amoroso / Arca aesthetic: unpredictable harmonic shifts, sudden tempo changes, mutant guitar solos, industrial breaks, and vocal chaos.",
        bpm_range=(90.0, 175.0, 130.0),
        target_lufs=(-8.5, -7.0, -7.6),
        recommended_keys_modes=["Chromatic / Poly-Modal", "C# Minor", "F# Locrian", "D Dorian"],
        channel_density=(10, 18, 26),
        drum_kits=["Mutant Glitch Kit", "Industrial Rock Drums"],
        groove_style="straight_precise",
        groove_swing_pct=0.0,
        instruments=["Mutant Fuzz Guitar", "Acid Glitch Bass", "Analog Lab Vintage Keys", "Distorted Shouts"],
        insert_fx=["FabFilter Saturn 2", "OTT", "ValhallaSpaceModulator", "LittleAlterBoy"],
        turnaround_bars=4
    )
}


class SixtyGenresKnowledgeBase:
    """Provides querying and documentation for the 60 most popular music genres."""

    @classmethod
    def get_profile(cls, genre_name_or_id: str) -> Optional[GenreAcousticProfile]:
        """Looks up a genre profile by ID, name, or fuzzy substring."""
        if not genre_name_or_id:
            return None
        norm = str(genre_name_or_id).lower().replace(" ", "_").replace("-", "_").strip()
        if norm in GENRES_CATALOG:
            return GENRES_CATALOG[norm]

        # Fuzzy search
        for gid, prof in GENRES_CATALOG.items():
            if norm in gid or gid in norm:
                return prof
            if norm in prof.name.lower() or prof.name.lower() in norm:
                return prof

        return None

    @classmethod
    def find_by_name(cls, query: str) -> Optional[GenreAcousticProfile]:
        """Finds the best matching genre profile from a query string or user message."""
        if not query:
            return None
        prof = cls.get_profile(query)
        if prof:
            return prof

        q_lower = str(query).lower().replace("-", " ")
        best_match = None
        longest_len = 0
        for gid, p in GENRES_CATALOG.items():
            name_clean = p.name.lower().replace("-", " ")
            id_clean = gid.replace("_", " ")
            if name_clean in q_lower or id_clean in q_lower:
                if len(name_clean) > longest_len:
                    best_match = p
                    longest_len = len(name_clean)
        return best_match

    @classmethod
    def list_all_genres(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all 60 catalog genres."""
        return [
            {
                "id": p.id,
                "name": p.name,
                "family": p.family,
                "default_bpm": p.bpm_range[2],
                "bpm_range": f"{p.bpm_range[0]}-{p.bpm_range[1]}",
                "target_lufs": p.target_lufs[2],
                "density_recommended": p.channel_density[1],
                "time_signature": f"{p.time_signature[0]}/{p.time_signature[1]}",
                "description": p.description
            }
            for p in GENRES_CATALOG.values()
        ]

    @classmethod
    def count(cls) -> int:
        return len(GENRES_CATALOG)

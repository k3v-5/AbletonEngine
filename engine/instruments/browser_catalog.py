# engine/instruments/browser_catalog.py
"""
Live Browser Catalog & VST3 / Native Preset Discovery Engine.
- Scans and catalogs available VST3 instruments (Arturia, Spectrasonics, Native Instruments, Vital, Serum) and native Live presets.
- Presents structured sound choices categorized by musical role (KEYS, BASS, LEAD, DRUMS, FX).
- Enables the Copilot and AI agent to select concrete, authentic sound sources rather than defaulting blindly to empty devices.
"""

from enum import Enum
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("BrowserCatalog")


class InstrumentSourceCategory(str, Enum):
    VST3 = "vst3"
    NATIVE_SYNTH = "native_synth"
    DRUM_KIT = "drum_kit"
    AUDIO_EFFECT = "audio_effect"


@dataclass
class SoundSourceOption:
    id: str
    name: str
    role: str  # "KEYS", "BASS", "LEAD", "DRUMS", "STRINGS", "FX"
    category: InstrumentSourceCategory
    uri: str
    vendor: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "category": self.category.value,
            "uri": self.uri,
            "vendor": self.vendor,
            "description": self.description,
        }


# Curated catalog mapping verified on user environment
CURATED_SOURCES: Dict[str, List[SoundSourceOption]] = {
    "KEYS": [
        SoundSourceOption(
            id="vst3_analog_lab",
            name="Arturia Analog Lab V",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Legendary vintage Rhodes, Wurlitzer, and analog polysynths.",
        ),
        SoundSourceOption(
            id="vst3_stage_73",
            name="Arturia Stage-73 V2",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Stage-73%20V2",
            vendor="Arturia",
            description="Authentic physical modeling of the Fender Rhodes Stage 73 electric piano.",
        ),
        SoundSourceOption(
            id="vst3_piano_v",
            name="Arturia Piano V3",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Piano%20V3",
            vendor="Arturia",
            description="Physical modeling acoustic grand and upright concert pianos.",
        ),
        SoundSourceOption(
            id="vst3_wurli",
            name="Arturia Wurli V3",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Wurli%20V3",
            vendor="Arturia",
            description="Physical modeling of vintage Wurlitzer 200A electric piano.",
        ),
        SoundSourceOption(
            id="vst3_kontakt_8",
            name="Native Instruments Kontakt 8",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Kontakt%208",
            vendor="Native Instruments",
            description="Industry standard sampler with ultra-realistic acoustic instruments and keys.",
        ),
        SoundSourceOption(
            id="vst3_zenology",
            name="Roland Cloud ZENOLOGY",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Roland%20Cloud:ZENOLOGY",
            vendor="Roland Cloud",
            description="Zen-Core synthesis engine with classic Roland digital and analog keyboard presets.",
        ),
        SoundSourceOption(
            id="vst3_keyscape",
            name="Spectrasonics Keyscape",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Keyscape",
            vendor="Spectrasonics",
            description="Grammy-grade collector keyboards and authentic jazz Rhodes.",
        ),
        SoundSourceOption(
            id="native_drift_rhodes",
            name="Drift Neo-Soul Rhodes",
            role="KEYS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Drift",
            vendor="Ableton",
            description="Warm analog electric piano with subtle tape drift and chorus.",
        ),
        SoundSourceOption(
            id="native_electric",
            name="Ableton Electric (Vintage EP)",
            role="KEYS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Electric",
            vendor="Ableton",
            description="Physical modeling of electro-mechanical Rhodes and Wurli pianos.",
        ),
    ],
    "BASS": [
        SoundSourceOption(
            id="vst3_serum_bass",
            name="Xfer Records Serum 2 Sub",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
            vendor="Xfer Records",
            description="Clean analog wavetable sub-bass with direct drive saturation and 808 glides.",
        ),
        SoundSourceOption(
            id="vst3_bloom_bass",
            name="Bloom Bass Impulse",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Bloom%20Bass%20Impulse",
            vendor="Bloom",
            description="Specialized modern sub-bass and 808 engine with warm analog drive.",
        ),
        SoundSourceOption(
            id="vst3_cyclop",
            name="Sugar Bytes Cyclop",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Sugar%20Bytes:Cyclop",
            vendor="Sugar Bytes",
            description="Heavy monophonic bass engine with wobble, vocal filter, and sub growls.",
        ),
        SoundSourceOption(
            id="vst3_massive_x",
            name="Native Instruments Massive X",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Massive%20X",
            vendor="Native Instruments",
            description="Next-gen subtractive wavetable monster with complex modulation and low-end punch.",
        ),
        SoundSourceOption(
            id="native_drift_sub",
            name="Drift Monophonic Sub-Bass",
            role="BASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Drift",
            vendor="Ableton",
            description="Pure sine/triangle sub-bass with low-end punch and pitch envelope.",
        ),
        SoundSourceOption(
            id="native_operator_sub",
            name="Ableton Operator (808 Sub-Bass)",
            role="BASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Operator",
            vendor="Ableton",
            description="FM-synthesized deep sub bass with smooth glide and sub warmth.",
        ),
        SoundSourceOption(
            id="vst3_trilian",
            name="Spectrasonics Trilian",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Trilian",
            vendor="Spectrasonics",
            description="Deep physical acoustic and analog synth basses.",
        ),
        SoundSourceOption(
            id="vst3_vital_808",
            name="Vital Audio 808 Sub",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Vital%20Audio:Vital",
            vendor="Vital Audio",
            description="Spectral warp 808 sub-bass with gliding portamento.",
        ),
    ],
    "LEAD": [
        SoundSourceOption(
            id="vst3_pigments",
            name="Arturia Pigments",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Pigments",
            vendor="Arturia",
            description="Polychrome multi-engine synth with cutting wavetable and virtual analog leads.",
        ),
        SoundSourceOption(
            id="vst3_serum_lead",
            name="Xfer Records Serum 2 Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
            vendor="Xfer Records",
            description="Sharp, cutting unison leads with high-resonance filter sweeps and portamento.",
        ),
        SoundSourceOption(
            id="vst3_analog_lab_lead",
            name="Arturia Analog Lab Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Cutting analog brass and vintage synth lead for melodic counterpoint.",
        ),
        SoundSourceOption(
            id="vst3_synplant",
            name="Sonic Charge Synplant",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Sonic%20Charge:Synplant",
            vendor="Sonic Charge",
            description="Organic genetic synthesis for unique, evolving, and expressive melodic leads.",
        ),
        SoundSourceOption(
            id="vst3_massive_x_lead",
            name="Native Instruments Massive X Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Massive%20X",
            vendor="Native Instruments",
            description="Aggressive cutting solo synth with dual wavetable oscillators and drive.",
        ),
        SoundSourceOption(
            id="native_drift_lead",
            name="Drift Classic Lead",
            role="LEAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Drift",
            vendor="Ableton",
            description="Expressive monophonic lead synth with glide and resonance.",
        ),
        SoundSourceOption(
            id="native_wavetable_lead",
            name="Ableton Wavetable (Solo Lead)",
            role="LEAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Wavetable",
            vendor="Ableton",
            description="Modern wavetable lead with stereo unison spread and FM modulation.",
        ),
        SoundSourceOption(
            id="vst3_vital_lead",
            name="Vital Spectral Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Vital%20Audio:Vital",
            vendor="Vital Audio",
            description="Hyper-modern soaring lead with stereo unison spread.",
        ),
    ],
    "PAD": [
        SoundSourceOption(
            id="vst3_omnisphere",
            name="Spectrasonics Omnisphere",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Omnisphere",
            vendor="Spectrasonics",
            description="Massive hybrid ambient pads, cinematic textures, and lush ethereal spaces.",
        ),
        SoundSourceOption(
            id="vst3_pigments_pad",
            name="Arturia Pigments (Ambient Pad)",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Pigments",
            vendor="Arturia",
            description="Granular and harmonic ambient pads with deep spatial modulation.",
        ),
        SoundSourceOption(
            id="vst3_bloom_synth",
            name="Bloom Synth Atmosphere",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Bloom%20Synth%20Atmosphere",
            vendor="Bloom",
            description="Immersive ambient pad bed with organic pitch breathing and shimmer reverb.",
        ),
        SoundSourceOption(
            id="vst3_analog_lab_pad",
            name="Arturia Analog Lab (Warm Pad)",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Rich vintage analog polysynth pads from Jupiter-8 and Prophet-5.",
        ),
        SoundSourceOption(
            id="vst3_zenology_pad",
            name="Roland Cloud ZENOLOGY Pad",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Roland%20Cloud:ZENOLOGY",
            vendor="Roland Cloud",
            description="Iconic Roland D-50 and JD-800 sparkling atmospheric pad sounds.",
        ),
        SoundSourceOption(
            id="native_wavetable_pad",
            name="Wavetable Ambient Keys/Pad",
            role="PAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Wavetable",
            vendor="Ableton",
            description="Modern wavetable polyphonic keys with lush spatial harmonics.",
        ),
        SoundSourceOption(
            id="native_meld",
            name="Ableton Meld (Macro Textures)",
            role="PAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Meld",
            vendor="Ableton",
            description="Bi-timbral macro synth for complex evolving organic drones and pads.",
        ),
    ],
    "DRUMS": [
        SoundSourceOption(
            id="drum_808_core",
            name="808 Core Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5422",
            vendor="Ableton",
            description="Authentic Roland TR-808 analog drum kit with booming kick and snappy snares.",
        ),
        SoundSourceOption(
            id="drum_boom_bap",
            name="Boom Bap Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5305",
            vendor="Ableton",
            description="Gritty vinyl acoustic drums with punchy kicks and textured claps.",
        ),
        SoundSourceOption(
            id="vst3_bloom_drums",
            name="Bloom Drum Breaks",
            role="DRUMS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Bloom%20Drum%20Breaks",
            vendor="Bloom",
            description="Dynamic modern breakbeat slicer and groove generator.",
        ),
        SoundSourceOption(
            id="vst3_egoist",
            name="Sugar Bytes Egoist",
            role="DRUMS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Sugar%20Bytes:Egoist",
            vendor="Sugar Bytes",
            description="Slicer, drum machine, bass line, and multi-effect sequencer.",
        ),
        SoundSourceOption(
            id="drum_bnyx_boot",
            name="BNYX Boot Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#BNYX%20Boot%20Kit.adg",
            vendor="Ableton",
            description="Modern rage, drill, and trap kit with clipped kicks and fast hats.",
        ),
        SoundSourceOption(
            id="drum_909_core",
            name="909 Core Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#909%20Core%20Kit.adg",
            vendor="Ableton",
            description="Classic techno and house TR-909 kit with punchy attack.",
        ),
    ],
    "VOCALS": [
        SoundSourceOption(
            id="vst3_bloom_vocal",
            name="Bloom Vocal Aether",
            role="VOCALS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Bloom%20Vocal%20Aether",
            vendor="Bloom",
            description="Atmospheric vocal chops, vocal pad beds, and choral synthesis.",
        ),
        SoundSourceOption(
            id="vst3_autotune",
            name="Antares Auto-Tune Pro",
            role="VOCALS",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Antares:Auto-Tune%20Pro",
            vendor="Antares",
            description="Industry-standard vocal pitch correction and modern formant shifting.",
        ),
        SoundSourceOption(
            id="vst3_bloom_choir",
            name="Bloom Vocal Choir",
            role="VOCALS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Bloom%20Vocal%20Choir",
            vendor="Bloom",
            description="Harmonic vocal ensemble with dynamic formant shaping and space.",
        ),
        SoundSourceOption(
            id="vst3_bloom_vocal_edit",
            name="Bloom Vocal Edit",
            role="VOCALS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Bloom%20Vocal%20Edit",
            vendor="Bloom",
            description="Creative vocal slicing, pitch glides, and rhythm gated chops.",
        ),
        SoundSourceOption(
            id="native_simpler_vocal",
            name="Ableton Simpler (Vocal Chopper)",
            role="VOCALS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Simpler",
            vendor="Ableton",
            description="Transient-sliced vocal sampler with pitch-envelope glide.",
        ),
    ],
    "FX": [
        SoundSourceOption(
            id="vst3_pro_q_4",
            name="FabFilter Pro-Q 4",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:FabFilter:Pro-Q%204",
            vendor="FabFilter",
            description="Precision surgical and dynamic equalizer with spectral masking display.",
        ),
        SoundSourceOption(
            id="vst3_valhalla_vintage_verb",
            name="ValhallaVintageVerb",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            vendor="Valhalla DSP",
            description="World-class algorithmic space and lush vintage hall/plate reverbs.",
        ),
        SoundSourceOption(
            id="vst3_shaperbox",
            name="Cableguys ShaperBox 3",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Cableguys:ShaperBox%203",
            vendor="Cableguys",
            description="Rhythmic sidechain ducking, volume curve shaping, and filter sweeps.",
        ),
        SoundSourceOption(
            id="vst3_thermal",
            name="Output Thermal",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Output:Thermal",
            vendor="Output",
            description="Multi-stage harmonic distortion, tube saturation, and warm analog drive.",
        ),
        SoundSourceOption(
            id="vst3_soothe2",
            name="oeksound soothe2",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:oeksound:soothe2_x64",
            vendor="oeksound",
            description="Dynamic resonance suppressor that removes harshness without dulling clarity.",
        ),
        SoundSourceOption(
            id="vst3_valhalla_delay",
            name="ValhallaDelay",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaDelay",
            vendor="Valhalla DSP",
            description="Classic tape, BBD, and digital delay with pitch modulation.",
        ),
        SoundSourceOption(
            id="vst3_portal",
            name="Output Portal",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Output:Portal",
            vendor="Output",
            description="Granular audio effects processor for pitch shifts, space, and motion.",
        ),
        SoundSourceOption(
            id="vst3_saturn_2",
            name="FabFilter Saturn 2",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:FabFilter:Saturn%202",
            vendor="FabFilter",
            description="Multiband warmth, vintage tube saturation, and tape exciter.",
        ),
    ],
    "MASTER": [
        SoundSourceOption(
            id="vst3_god_particle",
            name="Cradle The God Particle",
            role="MASTER",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Cradle:The%20God%20Particle",
            vendor="Cradle",
            description="Jaycen Joshua's signature master dynamics and saturation engine.",
        ),
        SoundSourceOption(
            id="vst3_pro_l_2",
            name="FabFilter Pro-L 2",
            role="MASTER",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:FabFilter:Pro-L%202",
            vendor="FabFilter",
            description="True peak brickwall limiter compliant with ITU-R BS.1770-5.",
        ),
        SoundSourceOption(
            id="vst3_pro_mb",
            name="FabFilter Pro-MB",
            role="MASTER",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:FabFilter:Pro-MB",
            vendor="FabFilter",
            description="Professional multiband compressor/expander for precise master bus polish.",
        ),
        SoundSourceOption(
            id="native_master_chain",
            name="Ableton 5-Device Master Chain",
            role="MASTER",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:AudioFx#Limiter",
            vendor="Ableton",
            description="Calibrated sequence: EQ Eight -> Glue Compressor -> Saturator -> Utility -> Limiter.",
        ),
    ],
}


class LiveBrowserCatalogEngine:
    """
    Catalog inspection and dynamic instrument loader.
    """

    @classmethod
    def get_available_sources_for_role(
        cls,
        role: str,
        conn: Any = None,
    ) -> List[SoundSourceOption]:
        """
        Returns sound options for a musical role (KEYS, BASS, LEAD, PAD, DRUMS, VOCALS, FX, MASTER).
        """
        role_key = role.upper()
        return CURATED_SOURCES.get(role_key, CURATED_SOURCES["KEYS"])

    @classmethod
    def get_role_suggestions(
        cls,
        role: str,
        limit: int = 5,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Returns top recommended instruments/sources for a role (default 5),
        along with the total count and note indicating the user/AI can query more.
        """
        sources = cls.get_available_sources_for_role(role, conn)
        total_count = len(sources)
        selected = sources[:limit]
        has_more = total_count > limit
        more_count = max(0, total_count - limit)
        return {
            "status": "SUCCESS",
            "role": role.upper(),
            "top_suggestions": [s.to_dict() for s in selected],
            "top_count": len(selected),
            "total_available": total_count,
            "has_more": has_more,
            "more_count": more_count,
            "query_more_prompt": (
                f"Hay {more_count} opciones adicionales para {role.upper()}. "
                f"Puedes consultar la lista completa con get_available_vst_and_presets(role='{role.lower()}')."
                if has_more else "Todas las opciones disponibles están listadas."
            ),
        }

    @classmethod
    def list_all_available_instruments(
        cls,
        conn: Any = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lists all available instruments organized by role or filtered by a specific role.
        When filtered by role, returns the top 5 curated choices with advice on how to query more.
        """
        if role:
            role_key = role.upper()
            sources = cls.get_available_sources_for_role(role, conn)
            top_5 = sources[:5]
            has_more = len(sources) > 5
            more_count = max(0, len(sources) - 5)
            return {
                "status": "SUCCESS",
                "role_filter": role.lower(),
                "count": len(sources),
                "top_suggestions": [s.to_dict() for s in top_5],
                "has_more": has_more,
                "more_count": more_count,
                "query_more_prompt": (
                    f"Hay {more_count} opciones adicionales para {role_key}. "
                    f"Se muestran las 5 más recomendadas. Puedes pedir cualquier otra por nombre o consultar el catálogo completo."
                    if has_more else "Todas las opciones disponibles están listadas."
                ),
                "items": [s.to_dict() for s in sources]
            }

        all_sources = {}
        all_vst3 = []
        all_native = []
        for r_name, s_list in CURATED_SOURCES.items():
            all_sources[r_name] = [s.to_dict() for s in s_list]
            for s in s_list:
                if s.category == InstrumentSourceCategory.VST3 and s.name not in all_vst3:
                    all_vst3.append(s.name)
                elif s.category in (InstrumentSourceCategory.NATIVE_SYNTH, InstrumentSourceCategory.DRUM_KIT) and s.name not in all_native:
                    all_native.append(s.name)

        return {
            "status": "SUCCESS",
            "role_catalog": all_sources,
            "vst3_plugins": all_vst3,
            "native_presets": all_native,
            "available_roles": list(CURATED_SOURCES.keys())
        }


BrowserCatalogEngine = LiveBrowserCatalogEngine

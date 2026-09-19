# engine/instruments/curated_data.py
"""
Curated instrument sound sources and role definitions catalog.
"""
from typing import Dict, List, Any
from .browser_catalog import InstrumentSourceCategory, SoundSourceOption

INSTRUMENT_ROLE_CATALOG: Dict[str, Dict[str, Any]] = {
    "DRUMS": {
        "description": "Ancla rítmica, cajas, platos, hi-hats y percusión base en el plano estéreo.",
        "frequency_range": "20 Hz - 18 kHz",
        "acoustic_role": "Rhythmic anchor and groove engine"
    },
    "KICK": {
        "description": "Bombo dedicado y aislado para pegada subgrave contundente y disparador de sidechain.",
        "frequency_range": "30 Hz - 120 Hz",
        "acoustic_role": "Sub punch and sidechain trigger"
    },
    "BASS": {
        "description": "Cimiento subgrave monofónico (808 deslizante, sub-bass sintetizado o bajo eléctrico).",
        "frequency_range": "30 Hz - 250 Hz",
        "acoustic_role": "Tonal fundamental and low-end drive"
    },
    "KEYS": {
        "description": "Cuerpo armónico principal (pianos acústicos, Rhodes, Wurlitzer, Clavinet, sintetizadores de teclas).",
        "frequency_range": "200 Hz - 4 kHz",
        "acoustic_role": "Harmonic bed and chord voicing"
    },
    "GUITAR": {
        "description": "Guitarras acústicas de nylon, guitarras eléctricas, rasgueos rítmicos y punteos melódicos.",
        "frequency_range": "100 Hz - 6 kHz",
        "acoustic_role": "Acoustic or electric string timbre and rhythm"
    },
    "BRASS": {
        "description": "Fanfarrias orquestales, trompetas solistas, trompas francesas y brass analógico triunfante.",
        "frequency_range": "120 Hz - 8 kHz",
        "acoustic_role": "Triumphant fanfare, brass stabs, and orchestral power"
    },
    "CHOIR": {
        "description": "Coros góticos, voces sacras líricas, cantos litúrgicos y texturas vocales celestiales MPE.",
        "frequency_range": "150 Hz - 10 kHz",
        "acoustic_role": "Sacred atmosphere, ecclesiastical chords, and human warmth"
    },
    "STRINGS": {
        "description": "Cuerdas orquestales sinfónicas, cellos expresivos, violines solistas y ensambles épicos.",
        "frequency_range": "80 Hz - 12 kHz",
        "acoustic_role": "Orchestral swell, emotional sustain, and cinematic depth"
    },
    "PAD": {
        "description": "Colchón armónico ambiental y apertura espacial tridimensional sin colisionar con el centro.",
        "frequency_range": "300 Hz - 8 kHz",
        "acoustic_role": "Stereo width, ambient shimmer, and spatial glue"
    },
    "LEAD": {
        "description": "Sintetizadores solistas, líneas melódicas principales, ganchos frontales y mordida espectral.",
        "frequency_range": "1 kHz - 12 kHz",
        "acoustic_role": "Topline melodic hook and upfront focus"
    },
    "PERCUSSION": {
        "description": "Percusión secundaria, congas, bongós, shakers, palmas acústicas y tambores étnicos.",
        "frequency_range": "100 Hz - 15 kHz",
        "acoustic_role": "Polyrhythmic texture, transient ear candy, and swing"
    },
    "VOCALS": {
        "description": "Pistas vocales para tomas solistas con micrófono en vivo o chops y armonías procesadas.",
        "frequency_range": "100 Hz - 12 kHz",
        "acoustic_role": "Vocal performance, hooks, and lyrical expression"
    },
    "FX": {
        "description": "Efectos de transición, risers de tensión, downlifters, impactos y barridos espectrales.",
        "frequency_range": "20 Hz - 20 kHz",
        "acoustic_role": "Dynamic tension, section impact, and spatial transitions"
    }
}


# Curated catalog mapping verified on user environment
CURATED_SOURCES: Dict[str, List[SoundSourceOption]] = {
    "GUITAR": [
        SoundSourceOption(
            id="native_flamenco_nylon",
            name="Nylon Flamenco Guitar (.adv)",
            role="GUITAR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Guitar%20&%20Plucked:FileId_6432",
            vendor="Ableton",
            description="Authentic nylon acoustic flamenco guitar with expressive dynamics and woody resonance (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.65, "Resonance": 0.50, "Attack": 0.05, "Release": 0.40},
                "description": "Authentic nylon acoustic flamenco guitar."
            },
        ),
        SoundSourceOption(
            id="native_basic_nylon",
            name="Basic Nylon Concerto Guitar (.adg)",
            role="GUITAR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Guitar%20&%20Plucked:FileId_5060",
            vendor="Ableton",
            description="Concert classical acoustic nylon guitar with warm low end and clear plucking (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Warmth": 0.70, "Brightness": 0.55, "Decay": 0.60},
                "description": "Concert classical acoustic nylon guitar."
            },
        ),
        SoundSourceOption(
            id="native_acoustic_guitar",
            name="Guitar Acoustic (.adg)",
            role="GUITAR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Guitar%20&%20Plucked:FileId_5066",
            vendor="Ableton",
            description="Dynamic steel-string acoustic guitar with realistic finger noise and presence (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Brightness": 0.60, "Dynamic Range": 0.70, "Body": 0.65},
                "description": "Dynamic steel-string acoustic guitar."
            },
        ),
        SoundSourceOption(
            id="native_steel_basic_guitar",
            name="Steel Basic Guitar (.adv)",
            role="GUITAR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Guitar%20&%20Plucked:FileId_6444",
            vendor="Ableton",
            description="Pure acoustic steel string guitar with bright chime (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Brightness": 0.70, "Attack": 0.05},
                "description": "Pure acoustic steel string guitar."
            },
        ),
        SoundSourceOption(
            id="native_strum_o_matic",
            name="Strum-o-Matic (.adg)",
            role="GUITAR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Guitar%20&%20Plucked:FileId_5078",
            vendor="Ableton",
            description="Acoustic and electric rhythmic guitar strumming rack (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.60, "Strum Speed": 0.50},
                "description": "Rhythmic guitar strum engine."
            },
        ),
    ],
    "PERCUSSION": [
        SoundSourceOption(
            id="native_perc_core",
            name="Percussion Core Kit (.adg)",
            role="PERCUSSION",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5437",
            vendor="Ableton",
            description="World percussion, acoustic claps, palmas, shakers, and ethnic hand drums (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Snap": 0.70, "Room Space": 0.40, "Pitch": 0.50},
                "description": "Acoustic claps, palmas, and hand percussion."
            },
        ),
        SoundSourceOption(
            id="native_perc_spirit",
            name="Percussion Spirit Kit (.adg)",
            role="PERCUSSION",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5438",
            vendor="Ableton",
            description="Organic and ethnic hand drums, frame drums, and wooden percussion (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.60, "Decay": 0.50},
                "description": "Organic wooden hand drums."
            },
        ),
        SoundSourceOption(
            id="native_perc_tamuz",
            name="Perc Tamuz Kit (.adg)",
            role="PERCUSSION",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5436",
            vendor="Ableton",
            description="Dynamic acoustic hand percussion and shakers (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Snap": 0.65, "Brightness": 0.60},
                "description": "Acoustic percussion and shakers."
            },
        ),
    ],
    "KEYS": [
        SoundSourceOption(
            id="native_flamenco_nylon",
            name="Nylon Flamenco Guitar (.adv)",
            role="KEYS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Guitar%20&%20Plucked:FileId_6432",
            vendor="Ableton",
            description="Authentic nylon acoustic flamenco guitar with expressive dynamics and woody resonance (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.65, "Resonance": 0.50, "Attack": 0.05, "Release": 0.40},
                "description": "Authentic nylon acoustic flamenco guitar."
            },
        ),
        SoundSourceOption(
            id="vst3_stage_73",
            name="Arturia Stage-73 V2",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Stage-73%20V2",
            vendor="Arturia",
            description="Authentic physical modeling of the Fender Rhodes Stage 73 electric piano.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Drive": 0.30, "Tone": 0.60, "Tremolo": 0.35},
                "description": "Physical modeled vintage Stage 73 Rhodes."
            },
        ),
        SoundSourceOption(
            id="vst3_piano_v",
            name="Arturia Piano V3",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Piano%20V3",
            vendor="Arturia",
            description="Physical modeling acoustic grand and upright concert pianos.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Hardness": 0.50, "Hammer": 0.55, "Resonance": 0.40},
                "description": "Concert grand acoustic piano."
            },
        ),
        SoundSourceOption(
            id="vst3_analog_lab",
            name="Arturia Analog Lab V",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Legendary vintage Rhodes, Wurlitzer, and analog polysynths.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"P1 Brightness": 0.65, "P1 Timbre": 0.55, "P1 Time": 0.45, "P1 Movement": 0.30},
                "description": "Warm vintage Rhodes keys with analog presence and subtle stereo movement."
            },
        ),
        SoundSourceOption(
            id="native_epiano_wurli",
            name="E-Piano Wurli (.adg)",
            role="KEYS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Piano%20&%20Keys:FileId_4867",
            vendor="Ableton",
            description="Vintage Wurli electro-mechanical piano with analog warmth and vibrato (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.65, "Warmth": 0.70, "Decay": 0.50, "Tremolo": 0.35},
                "description": "Vintage warm Wurli with gentle tremolo modulation."
            },
        ),
        SoundSourceOption(
            id="native_ac_piano",
            name="Ac Piano Upright (.adg)",
            role="KEYS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Piano%20&%20Keys:FileId_4847",
            vendor="Ableton",
            description="Acoustic upright piano with intimate felt dampening and room resonance (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Brightness": 0.60, "Dynamic Range": 0.75, "Room Reverb": 0.30},
                "description": "Intimate upright acoustic piano with realistic key noise."
            },
        ),
        SoundSourceOption(
            id="vst3_kontakt_8",
            name="Native Instruments Kontakt 8",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Kontakt%208",
            vendor="Native Instruments",
            description="Industry standard sampler with ultra-realistic acoustic instruments and keys.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Dynamics": 0.70, "Tone": 0.65, "Reverb": 0.35},
                "description": "High-fidelity acoustic keys sampler."
            },
        ),
        SoundSourceOption(
            id="native_drift_rhodes",
            name="Drift Neo-Soul Rhodes",
            role="KEYS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Drift",
            vendor="Ableton",
            description="Warm analog electric piano with subtle tape drift and chorus.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.60, "AMP_ATTACK": 0.02, "AMP_RELEASE": 0.45},
                "description": "Drift analog neo-soul Rhodes."
            },
        ),
        SoundSourceOption(
            id="vst3_keyscape",
            name="Spectrasonics Keyscape",
            role="KEYS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Keyscape",
            vendor="Spectrasonics",
            description="Grammy-grade collector keyboards and authentic jazz Rhodes.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Character": 0.60, "Tone": 0.65, "Reverb": 0.30},
                "description": "Collector keyboard Rhodes."
            },
        ),
    ],
    "BASS": [
        SoundSourceOption(
            id="vst3_sublab_xl",
            name="FutureAudioWorkshop SubLab XL",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:FutureAudioWorkshop:SubLabXL",
            vendor="FutureAudioWorkshop",
            description="Premier 808 sub-bass synthesizer with analog kick layer, X-Sub psychoacoustic engine, and distortion.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SUB_LEVEL": 0.95, "DRIVE": 0.40, "PORTAMENTO_GLIDE": 0.20},
                "description": "Deep 808 sub-bass with analog kick and saturation."
            },
        ),
        SoundSourceOption(
            id="vst3_serum_bass",
            name="Xfer Records Serum 2 Sub",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
            vendor="Xfer Records",
            description="Clean analog wavetable sub-bass with direct drive saturation and 808 glides.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SUB_LEVEL": 0.95, "FILTER_CUTOFF": 0.35, "DRIVE": 0.35, "PORTAMENTO_GLIDE": 0.18},
                "description": "Deep 808 sub-bass with gliding portamento and harmonic drive."
            },
        ),
        SoundSourceOption(
            id="vst3_massive_x_bass",
            name="Native Instruments Massive X",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Massive%20X",
            vendor="Native Instruments",
            description="Next-gen subtractive wavetable monster with analog punch and complex modulation.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.45, "DRIVE": 0.35, "AMP_ATTACK": 0.01},
                "description": "Aggressive wavetable sub-bass and reese."
            },
        ),
        SoundSourceOption(
            id="vst3_massive_bass",
            name="Native Instruments Massive",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Massive",
            vendor="Native Instruments",
            description="Iconic bass synth known for aggressive growls and solid sub tones.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.40, "DRIVE": 0.30},
                "description": "Classic growl and sub-bass."
            },
        ),
        SoundSourceOption(
            id="vst3_cyclop_bass",
            name="Sugar Bytes Cyclop",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Sugar%20Bytes:Cyclop",
            vendor="Sugar Bytes",
            description="Twisted monophonic bass synthesizer for wobble, sub-growls, and heavy modulations.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.45, "DRIVE": 0.40},
                "description": "Twisted monophonic wobble and growl bass."
            },
        ),
        SoundSourceOption(
            id="vst3_analog_lab_bass",
            name="Arturia Analog Lab V",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Legendary vintage analog basses (Minimoog, Prophet, Jupiter) and modern 808s.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"P1 Brightness": 0.50, "P1 Timbre": 0.50, "P1 Time": 0.40, "P1 Movement": 0.30},
                "description": "Vintage analog and modern polysynth basses."
            },
        ),
        SoundSourceOption(
            id="vst3_omnisphere_bass",
            name="Spectrasonics Omnisphere",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Omnisphere",
            vendor="Spectrasonics",
            description="Massive hybrid acoustic/synth basses, sub-booms, and cinematic low end.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.42, "AMP_ATTACK": 0.01},
                "description": "Deep hybrid acoustic and synth bass."
            },
        ),
        SoundSourceOption(
            id="native_808_drifter",
            name="808 Drifter (.adg)",
            role="BASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Bass:FileId_5176",
            vendor="Ableton",
            description="Punchy 808 sub with warm saturation and sub-weight (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.40, "Decay": 0.65, "Drive": 0.35},
                "description": "Punchy 808 sub with warm saturation."
            },
        ),
        SoundSourceOption(
            id="native_808_bnyx",
            name="808 BNYX Stopper (.adg)",
            role="BASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Bass:FileId_5175",
            vendor="Ableton",
            description="Aggressive clipped 808 sub with tight transients (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Punch": 0.85, "Distortion": 0.40, "Decay": 0.55},
                "description": "Aggressive clipped 808 sub."
            },
        ),
        SoundSourceOption(
            id="native_basic_sub_sine",
            name="Basic Sub Sine (.adg)",
            role="BASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Bass:FileId_5196",
            vendor="Ableton",
            description="Pure fundamental sub-bass for low-end reinforcement (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Sub Level": 1.0, "Cutoff": 0.30},
                "description": "Pure fundamental sub-bass."
            },
        ),
        SoundSourceOption(
            id="vst3_bloom_bass",
            name="Bloom Bass Impulse",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Bass%20Impulse",
            vendor="Bloom",
            description="Specialized modern sub-bass and 808 engine with warm analog drive.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SUB_LEVEL": 0.90, "DRIVE": 0.40, "AMP_ATTACK": 0.01},
                "description": "Specialized modern sub-bass."
            },
        ),
        SoundSourceOption(
            id="vst3_vital_808",
            name="Vital Audio 808 Sub",
            role="BASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Vital%20Audio:Vital",
            vendor="Vital Audio",
            description="Spectral warp 808 sub-bass with gliding portamento.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SUB_LEVEL": 0.90, "FILTER_CUTOFF": 0.30, "PORTAMENTO_GLIDE": 0.20},
                "description": "Spectral warp 808 sub-bass with smooth portamento glide."
            },
        ),
        SoundSourceOption(
            id="native_drift_sub",
            name="Drift Monophonic Sub-Bass",
            role="BASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Drift",
            vendor="Ableton",
            description="Pure sine/triangle sub-bass with low-end punch and pitch envelope.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SUB_LEVEL": 0.90, "FILTER_CUTOFF": 0.38, "AMP_ATTACK": 0.01},
                "description": "Pure analog sub-bass with tight attack."
            },
        ),
    ],
    "LEAD": [
        SoundSourceOption(
            id="vst3_massive_x",
            name="Native Instruments Massive X",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Massive%20X",
            vendor="Native Instruments",
            description="Aggressive cutting wavetable syncopated stabs and leads.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.75, "DRIVE": 0.35, "AMP_ATTACK": 0.01, "AMP_RELEASE": 0.25},
                "description": "Aggressive wavetable syncopated stabs."
            },
        ),
        SoundSourceOption(
            id="vst3_pigments",
            name="Arturia Pigments",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Pigments",
            vendor="Arturia",
            description="Polychrome multi-engine synth with cutting wavetable and virtual analog leads.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.70, "FILTER_RESONANCE": 0.25, "AMP_ATTACK": 0.02, "DELAY_MIX": 0.25},
                "description": "Cutting lead synth with synchronized delay and bright filter."
            },
        ),
        SoundSourceOption(
            id="vst3_serum_lead",
            name="Xfer Records Serum 2 Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Xfer%20Records:Serum%202",
            vendor="Xfer Records",
            description="Sharp, cutting unison leads with high-resonance filter sweeps and portamento.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.75, "FILTER_RESONANCE": 0.30, "UNISON_VOICES": 0.40, "PORTAMENTO_GLIDE": 0.12},
                "description": "Unison solo lead with high resonance and glide."
            },
        ),
        SoundSourceOption(
            id="native_agenda_lead",
            name="Agenda Lead (.adv)",
            role="LEAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Synth%20Lead:FileId_6743",
            vendor="Ableton",
            description="Punchy modern synth lead with portamento (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Cutoff": 0.75, "Glide": 0.15, "Drive": 0.30},
                "description": "Punchy solo synth lead with glide."
            },
        ),
        SoundSourceOption(
            id="vst3_analog_lab_lead",
            name="Arturia Analog Lab Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Cutting analog brass and vintage synth lead for melodic counterpoint.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"P1 Brightness": 0.75, "P1 Timbre": 0.65, "P1 Time": 0.40, "P1 Movement": 0.35},
                "description": "Cutting analog brass and vintage solo lead."
            },
        ),
        SoundSourceOption(
            id="native_drift_lead",
            name="Drift Classic Lead",
            role="LEAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Drift",
            vendor="Ableton",
            description="Expressive monophonic lead synth with glide and resonance.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.70, "FILTER_RESONANCE": 0.30, "PORTAMENTO_GLIDE": 0.15},
                "description": "Expressive monophonic drift lead."
            },
        ),
        SoundSourceOption(
            id="vst3_vital_lead",
            name="Vital Spectral Lead",
            role="LEAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Vital%20Audio:Vital",
            vendor="Vital Audio",
            description="Hyper-modern soaring lead with stereo unison spread.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.72, "UNISON_VOICES": 0.50, "PORTAMENTO_GLIDE": 0.14},
                "description": "Hyper-modern soaring lead with stereo spread."
            },
        ),
    ],
    "STRINGS": [
        SoundSourceOption(
            id="vst3_vital_strings",
            name="Vital Audio Celestial Strings",
            role="STRINGS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Vital%20Audio:Vital",
            vendor="Vital Audio",
            description="Lush wavetable synthesizer strings ensemble with slow emotional swell.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.68, "AMP_ATTACK": 0.35, "AMP_RELEASE": 0.65, "CHORUS_MIX": 0.40},
                "description": "Lush spectral wavetable strings ensemble."
            },
        ),
        SoundSourceOption(
            id="native_strings_orch",
            name="Ac Strings Orch (.adg)",
            role="STRINGS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Strings:FileId_4765",
            vendor="Ableton",
            description="Authentic orchestral strings ensemble with dynamic swells (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Attack": 0.35, "Release": 0.60, "Tone": 0.75, "Space": 0.40},
                "description": "Dynamic orchestral ensemble strings with emotional swell and hall reverb."
            },
        ),
        SoundSourceOption(
            id="native_cello_strings",
            name="Cello Strings (.adv)",
            role="STRINGS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Strings:FileId_6384",
            vendor="Ableton",
            description="Solo cello with warm expressive vibrato and woody timbre (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Attack": 0.25, "Vibrato": 0.50, "Release": 0.45},
                "description": "Warm expressive solo cello."
            },
        ),
        SoundSourceOption(
            id="native_ensemble_strings",
            name="Ensemble Strings (.adv)",
            role="STRINGS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Strings:FileId_6385",
            vendor="Ableton",
            description="Full symphonic string section with rich stereo width (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Attack": 0.40, "Release": 0.65, "Brightness": 0.70},
                "description": "Full symphonic string section."
            },
        ),
        SoundSourceOption(
            id="vst3_pigments_strings",
            name="Arturia Pigments (Orchestral Strings)",
            role="STRINGS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Pigments",
            vendor="Arturia",
            description="Hybrid physical modeled and sampled string ensemble with granular space.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.75, "AMP_ATTACK": 0.30, "AMP_RELEASE": 0.60, "REVERB_MIX": 0.35},
                "description": "Lush hybrid orchestral strings with wide stereo space."
            },
        ),
        SoundSourceOption(
            id="vst3_analog_lab_strings",
            name="Arturia Analog Lab (Symphonic Strings)",
            role="STRINGS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Vintage string machines (Solina, Mellotron) and modern symphonic strings.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"P1 Brightness": 0.65, "P1 Timbre": 0.60, "P1 Time": 0.50, "P1 Movement": 0.40},
                "description": "Rich vintage string ensemble with Solina ensemble chorus."
            },
        ),
    ],
    "BRASS": [
        SoundSourceOption(
            id="vst3_analog_lab_brass",
            name="Arturia Analog Lab V (Triumphant Brass & Horns)",
            role="BRASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Epic vintage analog poly-brass, fanfare horns, and cinematic brass sections.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"P1 Brightness": 0.80, "P1 Timbre": 0.70, "P1 Time": 0.35, "P1 Movement": 0.40},
                "description": "Triumphant analog fanfare brass with bright harmonics and fast attack."
            },
        ),
        SoundSourceOption(
            id="vst3_kontakt_brass",
            name="Native Instruments Kontakt 8 (Symphonic Brass)",
            role="BRASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Kontakt%208",
            vendor="Native Instruments",
            description="Ultra-realistic orchestral trumpet fanfares, French horns, and orchestral brass stabs.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Dynamics": 0.85, "Tone": 0.75, "Reverb": 0.30},
                "description": "High-fidelity orchestral brass fanfares."
            },
        ),
        SoundSourceOption(
            id="vst3_omnisphere_brass",
            name="Spectrasonics Omnisphere (Epic Horns & Fanfares)",
            role="BRASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Omnisphere",
            vendor="Spectrasonics",
            description="Massive hybrid cinematic brass, Hans Zimmer style horns, and resonant fanfares.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.78, "AMP_ATTACK": 0.05, "AMP_RELEASE": 0.40},
                "description": "Epic cinematic brass fanfares."
            },
        ),
        SoundSourceOption(
            id="vst3_pigments_brass",
            name="Arturia Pigments (Modern Synth Brass)",
            role="BRASS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Pigments",
            vendor="Arturia",
            description="Punchy modern synth brass stabs with wavetable modulation and sharp transients.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.75, "FILTER_RESONANCE": 0.25, "AMP_ATTACK": 0.04},
                "description": "Punchy wavetable synth brass stabs."
            },
        ),
        SoundSourceOption(
            id="native_some_trumpets",
            name="Some Trumpets (.adg)",
            role="BRASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Brass:FileId_5168",
            vendor="Ableton",
            description="Authentic orchestral and jazz trumpet section with dynamic expression (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Attack": 0.05, "Bright": 0.75, "Space": 0.35},
                "description": "Dynamic trumpet ensemble with bright timbre."
            },
        ),
        SoundSourceOption(
            id="native_flugelhorn",
            name="Ac Flugelhorn (.adg)",
            role="BRASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Brass:FileId_5145",
            vendor="Ableton",
            description="Warm acoustic flugelhorn with mellow tone and realistic vibrato (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tone": 0.65, "Vibrato": 0.40, "Attack": 0.08},
                "description": "Warm acoustic solo flugelhorn."
            },
        ),
        SoundSourceOption(
            id="native_transilvania_brass",
            name="Transilvania Brass (.adg)",
            role="BRASS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Brass:FileId_5170",
            vendor="Ableton",
            description="Dark cinematic brass rack with dramatic low-end weight (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Punch": 0.80, "Decay": 0.60, "Filter": 0.70},
                "description": "Dark cinematic orchestral brass."
            },
        ),
    ],
    "CHOIR": [
        SoundSourceOption(
            id="vst3_bloom_choir",
            name="Bloom Vocal Choir",
            role="CHOIR",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Vocal%20Aether",
            vendor="Bloom",
            description="Harmonic choral vocal ensemble with dynamic formant shaping and celestial reverb.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"REVERB_MIX": 0.40, "VOICE_FORMANT": 0.50},
                "description": "Harmonic choral vocal ensemble."
            },
        ),
        SoundSourceOption(
            id="vst3_omnisphere_choir",
            name="Spectrasonics Omnisphere (Gothic Church Choir)",
            role="CHOIR",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Omnisphere",
            vendor="Spectrasonics",
            description="World-renowned boys choir, Gregorian chants, and massive ecclesiastical cathedral choirs.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.70, "AMP_ATTACK": 0.25, "AMP_RELEASE": 0.65, "REVERB_MIX": 0.45},
                "description": "Gothic ecclesiastical church choir with cathedral reverb."
            },
        ),
        SoundSourceOption(
            id="vst3_kontakt_choir",
            name="Native Instruments Kontakt 8 (Sacred Vocal Choirs)",
            role="CHOIR",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Native%20Instruments:Kontakt%208",
            vendor="Native Instruments",
            description="Ultra-realistic choral libraries with polyphonic legato and sacred vowel shifting.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Dynamics": 0.75, "Tone": 0.65, "Reverb": 0.40},
                "description": "Sacred polyphonic vocal choir sampler."
            },
        ),
        SoundSourceOption(
            id="native_choir_avalon",
            name="Choir Pad Avalon (.adg)",
            role="CHOIR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Pad:FileId_4910",
            vendor="Ableton",
            description="Ethereal vocal choir pad with liturgical atmosphere and slow swell (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Attack": 0.35, "Space": 0.50, "Brightness": 0.60},
                "description": "Ethereal liturgical vocal choir pad."
            },
        ),
        SoundSourceOption(
            id="native_ghost_choir",
            name="MPE Ghost Choir Pad (.adg)",
            role="CHOIR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Pad%20MPE:FileId_5001",
            vendor="Ableton",
            description="Expressive MPE-enabled ghostly choral textures with polyphonic pressure (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Timbre": 0.65, "Reverb": 0.45, "Decay": 0.60},
                "description": "Expressive MPE sacred choir textures."
            },
        ),
        SoundSourceOption(
            id="native_synthetic_choir",
            name="Synthetic Choir Strings (.adg)",
            role="CHOIR",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Strings:FileId_4780",
            vendor="Ableton",
            description="Vintage synthetic choir blended with slow strings for celestial backgrounds (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Attack": 0.30, "Chorus": 0.45, "Space": 0.40},
                "description": "Synthetic choir and strings blend."
            },
        ),
    ],
    "PAD": [
        SoundSourceOption(
            id="vst3_vital_pad",
            name="Vital Audio Poly Shimmer Pad",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Vital%20Audio:Vital",
            vendor="Vital Audio",
            description="Lush spectral warp wavetable pad with ethereal stereo shimmer.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.65, "AMP_ATTACK": 0.35, "AMP_RELEASE": 0.60, "CHORUS_MIX": 0.35},
                "description": "Lush spectral wavetable shimmer pad."
            },
        ),
        SoundSourceOption(
            id="native_warm_analog_pad",
            name="Warm Analog Pad (.adg)",
            role="PAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Pad:FileId_4993",
            vendor="Ableton",
            description="Lush warm analog polysynth pad with slow evolution (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Cutoff": 0.55, "Resonance": 0.20, "Attack": 0.45, "Release": 0.60},
                "description": "Lush warm analog polysynth pad with slow attack."
            },
        ),
        SoundSourceOption(
            id="native_after_glow_pad",
            name="After Glow Pad (.adg)",
            role="PAD",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Sounds#Pad:FileId_4895",
            vendor="Ableton",
            description="Ethereal ambient pad with shimmering reverb tail (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Brightness": 0.50, "Shimmer": 0.40, "Decay": 0.70},
                "description": "Ethereal ambient shimmer pad."
            },
        ),
        SoundSourceOption(
            id="vst3_pigments_pad",
            name="Arturia Pigments (Ambient Pad)",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Pigments",
            vendor="Arturia",
            description="Granular and harmonic ambient pads with deep spatial modulation.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.65, "AMP_ATTACK": 0.45, "AMP_RELEASE": 0.60, "CHORUS_MIX": 0.40},
                "description": "Granular and harmonic ambient pads."
            },
        ),
        SoundSourceOption(
            id="vst3_bloom_synth",
            name="Bloom Synth Atmosphere",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Synth%20Atmosphere",
            vendor="Bloom",
            description="Immersive ambient pad bed with organic pitch breathing and shimmer reverb.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.60, "AMP_ATTACK": 0.50, "REVERB_MIX": 0.50},
                "description": "Immersive ambient pad bed with shimmer."
            },
        ),
        SoundSourceOption(
            id="vst3_omnisphere",
            name="Spectrasonics Omnisphere",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Spectrasonics:Omnisphere",
            vendor="Spectrasonics",
            description="Massive hybrid ambient pads, cinematic textures, and lush ethereal spaces.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"FILTER_CUTOFF": 0.60, "AMP_ATTACK": 0.40, "AMP_RELEASE": 0.65, "REVERB_MIX": 0.45},
                "description": "Massive hybrid ambient pads and ethereal space."
            },
        ),
        SoundSourceOption(
            id="vst3_analog_lab_pad",
            name="Arturia Analog Lab (Warm Pad)",
            role="PAD",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
            vendor="Arturia",
            description="Rich vintage analog polysynth pads from Jupiter-8 and Prophet-5.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"P1 Brightness": 0.60, "P1 Timbre": 0.65, "P1 Time": 0.55, "P1 Movement": 0.45},
                "description": "Rich vintage analog polysynth pads."
            },
        ),
    ],
    "KICK": [
        SoundSourceOption(
            id="kick_808_core",
            name="808 Core Kit (.adg)",
            role="KICK",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5422",
            vendor="Ableton",
            description="Dedicated low-end kick engine with pure sub transient for sidechain routing.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Kick Pitch": 0.50, "Punch": 0.75, "Decay": 0.60},
                "description": "Dedicated Roland TR-808 analog kick."
            },
        ),
        SoundSourceOption(
            id="kick_909_core",
            name="909 Core Kit (.adg)",
            role="KICK",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5445",
            vendor="Ableton",
            description="Punchy house/techno 909 kick transient.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Tune": 0.50, "Attack": 0.80, "Decay": 0.55},
                "description": "Punchy 909 kick."
            },
        )
    ],
    "DRUMS": [
        SoundSourceOption(
            id="native_perc_core",
            name="Percussion Core Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5437",
            vendor="Ableton",
            description="World percussion, acoustic claps, palmas, shakers, and ethnic hand drums (Live 12 verified).",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Snap": 0.70, "Room Space": 0.40, "Pitch": 0.50},
                "description": "Acoustic claps, palmas, and hand percussion."
            },
        ),
        SoundSourceOption(
            id="drum_808_core",
            name="808 Core Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5422",
            vendor="Ableton",
            description="Authentic Roland TR-808 analog drum kit with booming kick and snappy snares.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Kick Pitch": 0.50, "Snare Snap": 0.65, "Hi-Hat Tone": 0.70},
                "description": "Authentic Roland TR-808 analog drum kit."
            },
        ),
        SoundSourceOption(
            id="drum_boom_bap",
            name="Boom Bap Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5305",
            vendor="Ableton",
            description="Gritty vinyl acoustic drums with punchy kicks and textured claps.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Vinyl Grime": 0.45, "Kick Thump": 0.60, "Snare Body": 0.55},
                "description": "Gritty vinyl acoustic drums."
            },
        ),
        SoundSourceOption(
            id="vst3_bloom_drums",
            name="Bloom Drum Breaks",
            role="DRUMS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Drum%20Breaks",
            vendor="Bloom",
            description="Dynamic modern breakbeat slicer and groove generator.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"DRIVE": 0.35, "COMP_DEPTH": 0.60},
                "description": "Dynamic breakbeat slicer."
            },
        ),
        SoundSourceOption(
            id="drum_bnyx_boot",
            name="BNYX Boot Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#BNYX%20Boot%20Kit.adg",
            vendor="Ableton",
            description="Modern rage, drill, and trap kit with clipped kicks and fast hats.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Drive": 0.50, "Clip": 0.40},
                "description": "Modern rage and drill trap kit."
            },
        ),
        SoundSourceOption(
            id="drum_sliced_break",
            name="Sliced Break Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5350",
            vendor="Ableton",
            description="Organic sliced breakbeat drum rack for jungle and breakcore breaks.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Drive": 0.35, "Pitch": 0.50},
                "description": "Sliced breakbeat kit."
            },
        ),
        SoundSourceOption(
            id="drum_909_core",
            name="909 Core Kit (.adg)",
            role="DRUMS",
            category=InstrumentSourceCategory.DRUM_KIT,
            uri="query:Drums#FileId_5423",
            vendor="Ableton",
            description="Classic techno and house TR-909 kit with punchy attack.",
            blueprint={
                "sculpt_type": "macro",
                "parameters": {"Punch": 0.65, "Snap": 0.60},
                "description": "Classic techno and house TR-909 kit."
            },
        ),
    ],
    "VOCALS": [
        SoundSourceOption(
            id="vst3_bloom_vocal",
            name="Bloom Vocal Aether",
            role="VOCALS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Vocal%20Aether",
            vendor="Bloom",
            description="Atmospheric vocal chops, vocal pad beds, and choral synthesis.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SPACE": 0.45, "VOICE_FORMANT": 0.48},
                "description": "Atmospheric vocal chops and space reverb."
            },
        ),
        SoundSourceOption(
            id="vst3_autotune",
            name="Antares Auto-Tune Pro",
            role="VOCALS",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Antares:Auto-Tune%20Pro",
            vendor="Antares",
            description="Industry-standard vocal pitch correction and modern formant shifting.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"REVERB_MIX": 0.20},
                "description": "Pitch correction and formant shifting."
            },
        ),
        SoundSourceOption(
            id="vst3_bloom_choir",
            name="Bloom Vocal Choir",
            role="VOCALS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Vocal%20Choir",
            vendor="Bloom",
            description="Harmonic vocal ensemble with dynamic formant shaping and space.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"REVERB_MIX": 0.40, "VOICE_FORMANT": 0.50},
                "description": "Harmonic vocal ensemble."
            },
        ),
        SoundSourceOption(
            id="vst3_bloom_vocal_edit",
            name="Bloom Vocal Edit",
            role="VOCALS",
            category=InstrumentSourceCategory.VST3,
            uri="query:Plugins#VST3:Excite%20Audio:Bloom%20Vocal%20Edit",
            vendor="Bloom",
            description="Creative vocal slicing, pitch glides, and rhythm gated chops.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"PORTAMENTO_GLIDE": 0.15},
                "description": "Creative vocal slicing and pitch glides."
            },
        ),
        SoundSourceOption(
            id="native_simpler_vocal",
            name="Ableton Simpler (Vocal Chopper)",
            role="VOCALS",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:Synths#Simpler",
            vendor="Ableton",
            description="Transient-sliced vocal sampler with pitch-envelope glide.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"AMP_ATTACK": 0.01, "PORTAMENTO_GLIDE": 0.10},
                "description": "Transient-sliced vocal sampler."
            },
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
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"EQ_HPF_FREQ": 0.18, "EQ_MUD_CUT": 0.46, "EQ_AIR_SHELF": 0.53},
                "description": "Surgical clean EQ with HPF and high air shelf."
            },
        ),
        SoundSourceOption(
            id="vst3_valhalla_vintage_verb",
            name="ValhallaVintageVerb",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            vendor="Valhalla DSP",
            description="World-class algorithmic space and lush vintage hall/plate reverbs.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"REVERB_MIX": 0.30, "REVERB_DECAY": 0.45, "REVERB_PREDELAY": 0.20},
                "description": "Lush 1980s vintage hall reverb."
            },
        ),
        SoundSourceOption(
            id="vst3_shaperbox",
            name="Cableguys ShaperBox 3",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Cableguys:ShaperBox%203",
            vendor="Cableguys",
            description="Rhythmic sidechain ducking, volume curve shaping, and filter sweeps.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"COMP_DEPTH": 0.70, "DRIVE": 0.40},
                "description": "Rhythmic volume sidechain and filter shaping."
            },
        ),
        SoundSourceOption(
            id="vst3_thermal",
            name="Output Thermal",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Output:Thermal",
            vendor="Output",
            description="Multi-stage harmonic distortion, tube saturation, and warm analog drive.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"DRIVE": 0.45, "DRIVE_MIX": 0.65},
                "description": "Multi-stage warm analog distortion."
            },
        ),
        SoundSourceOption(
            id="vst3_soothe2",
            name="oeksound soothe2",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:oeksound:soothe2_x64",
            vendor="oeksound",
            description="Dynamic resonance suppressor that removes harshness without dulling clarity.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"SOOTHE_DEPTH": 0.45, "SOOTHE_SHARPNESS": 0.50},
                "description": "Dynamic resonance suppressor."
            },
        ),
        SoundSourceOption(
            id="vst3_valhalla_delay",
            name="ValhallaDelay",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaDelay",
            vendor="Valhalla DSP",
            description="Classic tape, BBD, and digital delay with pitch modulation.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"DELAY_MIX": 0.25, "DELAY_FEEDBACK": 0.38},
                "description": "Analog tape delay with pitch modulation."
            },
        ),
        SoundSourceOption(
            id="native_saturator",
            name="Ableton Saturator",
            role="FX",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:AudioFx#Saturator",
            vendor="Ableton",
            description="Analog warmth, harmonic drive, and soft clipping.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"DRIVE": 0.40, "DRIVE_MIX": 0.70},
                "description": "Warm analog saturation with soft clipping."
            },
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
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"COMP_DEPTH": 0.60, "LIMITER_GAIN": 0.52},
                "description": "Commercial master dynamics and saturation."
            },
        ),
        SoundSourceOption(
            id="vst3_pro_l_2",
            name="FabFilter Pro-L 2",
            role="MASTER",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:Plugins#VST3:FabFilter:Pro-L%202",
            vendor="FabFilter",
            description="True peak brickwall limiter compliant with ITU-R BS.1770-5.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"LIMITER_GAIN": 0.65, "LIMITER_CEILING": 0.98},
                "description": "True peak brickwall limiter (-0.3 dBTP)."
            },
        ),
        SoundSourceOption(
            id="native_master_chain",
            name="Ableton 5-Device Master Chain",
            role="MASTER",
            category=InstrumentSourceCategory.AUDIO_EFFECT,
            uri="query:AudioFx#Limiter",
            vendor="Ableton",
            description="Calibrated sequence: EQ Eight -> Glue Compressor -> Saturator -> Utility -> Limiter.",
            blueprint={
                "sculpt_type": "semantic",
                "parameters": {"LIMITER_GAIN": 0.60, "LIMITER_CEILING": 0.98},
                "description": "Ableton 5-Device calibrated master chain."
            },
        ),
    ],
}



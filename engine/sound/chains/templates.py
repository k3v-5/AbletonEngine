"""
Production Chain Templates:
Contextual, parameterized signal chains for every musical role.
"""
from typing import Dict, List
from .models import (
    SemanticDevice, DeviceChain,
    DEVICE_PRIMARY_INSTRUMENT, DEVICE_SATURATION, DEVICE_EQ,
    DEVICE_COMPRESSOR, DEVICE_REVERB, DEVICE_DELAY, DEVICE_UTILITY,
    DEVICE_CHORUS, DEVICE_DRUM_BUSS
)

CHAIN_TEMPLATES: Dict[str, DeviceChain] = {
    "SUB_BASS": DeviceChain(
        role="SUB_BASS",
        name="Sub Bass Chain",
        devices=[
            SemanticDevice(
                identifier=DEVICE_PRIMARY_INSTRUMENT,
                preferred_name="Drift",
                preferred_uri="query:Synths#Drift",
                fallback_name="Simpler",
                fallback_uri="query:Synths#Simpler"
            ),
            SemanticDevice(
                identifier=DEVICE_SATURATION,
                preferred_name="Saturator",
                preferred_uri="query:AudioFx#Saturator",
                parameters={"Drive": 2.5, "Soft Clip": 1.0}
            ),
            SemanticDevice(
                identifier=DEVICE_EQ,
                preferred_name="EQ Eight",
                preferred_uri="query:AudioFx#EQ%20Eight",
                fallback_name="Channel EQ",
                fallback_uri="query:AudioFx#Channel%20EQ",
                parameters={"Gain 1": 1.5, "Frequency 1": 50.0}
            ),
            SemanticDevice(
                identifier=DEVICE_COMPRESSOR,
                preferred_name="Compressor",
                preferred_uri="query:AudioFx#Compressor",
                parameters={"Ratio": 3.0, "Attack": 15.0, "Release": 100.0}
            ),
            SemanticDevice(
                identifier=DEVICE_UTILITY,
                preferred_name="Utility",
                preferred_uri="query:AudioFx#Utility",
                parameters={"Bass Mono": 1.0, "Bass Mono Frequency": 120.0, "Width": 0.0}
            )
        ]
    ),
    "BASS": DeviceChain(
        role="BASS",
        name="Melodic Techno Bass Chain",
        devices=[
            SemanticDevice(
                identifier=DEVICE_PRIMARY_INSTRUMENT,
                preferred_name="Wavetable",
                preferred_uri="query:Synths#Wavetable",
                fallback_name="Drift",
                fallback_uri="query:Synths#Drift"
            ),
            SemanticDevice(
                identifier=DEVICE_SATURATION,
                preferred_name="Saturator",
                preferred_uri="query:AudioFx#Saturator",
                parameters={"Drive": 3.5}
            ),
            SemanticDevice(
                identifier=DEVICE_EQ,
                preferred_name="EQ Eight",
                preferred_uri="query:AudioFx#EQ%20Eight",
                parameters={"Frequency 1": 35.0, "Gain 8": -2.0}
            ),
            SemanticDevice(
                identifier=DEVICE_COMPRESSOR,
                preferred_name="Compressor",
                preferred_uri="query:AudioFx#Compressor",
                parameters={"Ratio": 4.0, "Attack": 8.0, "Release": 120.0}
            ),
            SemanticDevice(
                identifier=DEVICE_UTILITY,
                preferred_name="Utility",
                preferred_uri="query:AudioFx#Utility",
                parameters={"Bass Mono": 1.0, "Bass Mono Frequency": 110.0, "Width": 10.0}
            )
        ]
    ),
    "LEAD": DeviceChain(
        role="LEAD",
        name="Hypnotic Lead Chain",
        devices=[
            SemanticDevice(
                identifier=DEVICE_PRIMARY_INSTRUMENT,
                preferred_name="Wavetable",
                preferred_uri="query:Synths#Wavetable",
                fallback_name="Drift",
                fallback_uri="query:Synths#Drift"
            ),
            SemanticDevice(
                identifier=DEVICE_EQ,
                preferred_name="EQ Eight",
                preferred_uri="query:AudioFx#EQ%20Eight",
                parameters={"Frequency 1": 250.0}  # Low cut
            ),
            SemanticDevice(
                identifier=DEVICE_SATURATION,
                preferred_name="Saturator",
                preferred_uri="query:AudioFx#Saturator",
                parameters={"Drive": 4.0}
            ),
            SemanticDevice(
                identifier=DEVICE_DELAY,
                preferred_name="Delay",
                preferred_uri="query:AudioFx#Delay",
                parameters={"Dry/Wet": 25.0, "Feedback": 45.0}
            ),
            SemanticDevice(
                identifier=DEVICE_REVERB,
                preferred_name="Reverb",
                preferred_uri="query:AudioFx#Reverb",
                fallback_name="Hybrid Reverb",
                parameters={"Dry/Wet": 30.0, "Decay Time": 2.8}
            ),
            SemanticDevice(
                identifier=DEVICE_UTILITY,
                preferred_name="Utility",
                preferred_uri="query:AudioFx#Utility",
                parameters={"Width": 125.0}
            )
        ]
    ),
    "PAD": DeviceChain(
        role="PAD",
        name="Lush Atmospheric Pad Chain",
        devices=[
            SemanticDevice(
                identifier=DEVICE_PRIMARY_INSTRUMENT,
                preferred_name="Wavetable",
                preferred_uri="query:Synths#Wavetable",
                fallback_name="Drift",
                fallback_uri="query:Synths#Drift"
            ),
            SemanticDevice(
                identifier=DEVICE_EQ,
                preferred_name="EQ Eight",
                preferred_uri="query:AudioFx#EQ%20Eight",
                parameters={"Frequency 1": 200.0}
            ),
            SemanticDevice(
                identifier=DEVICE_CHORUS,
                preferred_name="Chorus-Ensemble",
                preferred_uri="query:AudioFx#Chorus-Ensemble",
                parameters={"Dry/Wet": 40.0}
            ),
            SemanticDevice(
                identifier=DEVICE_REVERB,
                preferred_name="Reverb",
                preferred_uri="query:AudioFx#Reverb",
                parameters={"Dry/Wet": 55.0, "Decay Time": 4.5}
            ),
            SemanticDevice(
                identifier=DEVICE_UTILITY,
                preferred_name="Utility",
                preferred_uri="query:AudioFx#Utility",
                parameters={"Width": 150.0}
            )
        ]
    ),
    "DRUM_BUS": DeviceChain(
        role="DRUM_BUS",
        name="Techno Drum Processing Chain",
        devices=[
            SemanticDevice(
                identifier=DEVICE_DRUM_BUSS,
                preferred_name="Drum Buss",
                preferred_uri="query:AudioFx#Drum%20Buss",
                parameters={"Drive": 20.0, "Crunch": 10.0, "Boom": 30.0}
            ),
            SemanticDevice(
                identifier=DEVICE_COMPRESSOR,
                preferred_name="Glue Compressor",
                preferred_uri="query:AudioFx#Glue%20Compressor",
                fallback_name="Compressor",
                fallback_uri="query:AudioFx#Compressor",
                parameters={"Threshold": -15.0, "Ratio": 4.0, "Attack": 30.0, "Release": 100.0}
            ),
            SemanticDevice(
                identifier=DEVICE_UTILITY,
                preferred_name="Utility",
                preferred_uri="query:AudioFx#Utility",
                parameters={"Bass Mono": 1.0, "Bass Mono Frequency": 120.0}
            )
        ]
    )
}

def get_chain_template(role: str) -> DeviceChain:
    """Retrieves standard production chain for a role."""
    key = role.upper().strip()
    return CHAIN_TEMPLATES.get(key, CHAIN_TEMPLATES["BASS"])

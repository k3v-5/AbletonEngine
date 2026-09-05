# engine/instruments/execution/planner.py
from typing import Dict, Any, List, Optional
from ..models import InstrumentDescriptor, InstrumentSource, InstrumentExecutionPlan
from ..roles import InstrumentRole
from ..profiles.sound_profiles import get_sound_profile
from ..library.preset_catalog import PresetCatalog

class InstrumentPlanner:
    """Resolves and plans instrumentation for both melodic instruments and drum kits."""
    
    # Native Live 12 instrument mapping for semantic roles
    NATIVE_INSTRUMENT_MAP: Dict[str, Dict[str, Any]] = {
        "SUB_BASS": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Osc 1 Wave": 0.0, "Filter Freq": 150.0} # Sub sine
        },
        "BASS": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Osc 1 Wave": 1.0, "Filter Freq": 800.0} # Sawtooth rolling
        },
        "CHORDS": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Osc 1 Wave": 1.0, "Filter Freq": 2500.0, "Voice Mode": 1.0} # Polyphonic
        },
        "PAD": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Attack": 400.0, "Filter Freq": 2000.0, "Voice Mode": 1.0}
        },
        "LEAD": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Voice Mode": 0.0, "Glide": 50.0, "Filter Freq": 4000.0} # Mono lead
        },
        "PLUCK": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Decay": 180.0, "Sustain": 0.0, "Filter Freq": 3000.0}
        },
        "KEYS": {
            "uri": "query:Synths#Drift",
            "device_name": "Drift",
            "source": InstrumentSource.INSTRUMENT,
            "parameters": {"Voice Mode": 1.0, "Filter Freq": 5000.0}
        }
    }

    @classmethod
    def resolve_instrument(cls, role: str, sound_profile: str = "") -> InstrumentDescriptor:
        role_clean = role.strip().upper()
        profile = get_sound_profile(sound_profile) if sound_profile else None
        target_role = InstrumentRole.from_str(role_clean)

        # 1. Check Curated Native Live 12 Preset Catalog
        preset = PresetCatalog.resolve_preset(role_clean, genre=sound_profile, mood=sound_profile)
        if preset:
            src = InstrumentSource.DRUM_RACK if preset.role == "DRUM_KIT" else InstrumentSource.INSTRUMENT
            return InstrumentDescriptor(
                role=target_role,
                sound_profile=sound_profile or preset.character or role_clean.lower(),
                source=src,
                uri=preset.uri,
                device_name=preset.name,
                parameters={}
            )

        # 2. Check native mapping fallback
        if role_clean in cls.NATIVE_INSTRUMENT_MAP:
            info = cls.NATIVE_INSTRUMENT_MAP[role_clean]
            return InstrumentDescriptor(
                role=target_role,
                sound_profile=sound_profile or role_clean.lower(),
                source=info["source"],
                uri=info["uri"],
                device_name=info["device_name"],
                parameters=info["parameters"]
            )

        # 3. Fallback to Drift
        return InstrumentDescriptor(
            role=target_role,
            sound_profile=sound_profile or "generic",
            source=InstrumentSource.INSTRUMENT,
            uri="query:Synths#Drift",
            device_name="Drift",
            is_fallback=True,
            warning=f"Specific preset for {role_clean} not found; default Drift synth assigned."
        )

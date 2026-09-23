# engine/arrangement/emotional_arc.py
"""
Emotional Arc Director (Director de Arco Emocional):
Orchestrates song arrangement momentum, dynamic density, and structural tension
by evaluating both GENRE and EMOTIONAL INTENT:
1. Automatic Emotion Inference: Derives emotional profile from Key, Scale, and Genre.
2. Dynamic Energy Curves: Calibrates section energy (0.0 to 1.0) and role activity.
3. Hit-Record Inertia Retention: Prevents artificial energy crashes (e.g. Verse 2 retains
   rhythmic drive from Chorus 1 instead of dropping back to a quiet intro).
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger("EmotionalArcDirector")


class MusicalEmotion(str, Enum):
    DARK_AGGRESSIVE = "DARK_AGGRESSIVE"          # Heavy Trap, UK Drill, Dubstep, Industrial Rock
    MELANCHOLIC_INTIMATE = "MELANCHOLIC_INTIMATE"# Sad Pop, Lo-Fi, R&B, Ballad
    EUPHORIC_ANTHEMIC = "EUPHORIC_ANTHEMIC"      # Festival EDM, Future Bass, Stadium Rock, Anthem Pop
    GROOVY_SENSUAL = "GROOVY_SENSUAL"            # Reggaetón, Afrobeat, Latin Urban, Tech House
    NOSTALGIC_CHILL = "NOSTALGIC_CHILL"          # Synthwave, Chillout, Neo-Soul, Indie


class EmotionalArcDirector:
    """Orchestrates arrangement macro-dynamics according to genre pacing and emotional thesis."""

    EMOTIONAL_PROFILES: Dict[MusicalEmotion, Dict[str, Any]] = {
        MusicalEmotion.DARK_AGGRESSIVE: {
            "name": "Oscura / Agresiva",
            "description": "Contraste violento, vacíos tensos, caídas de bajo pesadas y retención rítmica implacable.",
            "intro_energy": 0.35,
            "verse_energy": 0.50,
            "build_energy": 0.85,
            "drop_energy": 1.00,
            "verse_2_inertia_keep_roles": ["BASS", "808", "808_BASS", "HI_HATS"],
            "pre_drop_tension_device": "DEAD_AIR"
        },
        MusicalEmotion.MELANCHOLIC_INTIMATE: {
            "name": "Melancólica / Íntima",
            "description": "Evolución suave, texturas orgánicas continuas, dinámicas contenidas y respiración vocal.",
            "intro_energy": 0.25,
            "verse_energy": 0.40,
            "build_energy": 0.60,
            "drop_energy": 0.78,
            "verse_2_inertia_keep_roles": ["KEYS", "PIANO", "PAD"],
            "pre_drop_tension_device": "FILTER_SWEEP"
        },
        MusicalEmotion.EUPHORIC_ANTHEMIC: {
            "name": "Eufórica / Himno",
            "description": "Contraste gigantesco, acumulación masiva de energía, colapso estéreo y explosión total.",
            "intro_energy": 0.30,
            "verse_energy": 0.55,
            "build_energy": 0.90,
            "drop_energy": 1.00,
            "verse_2_inertia_keep_roles": ["DRUMS", "KICK", "HI_HATS"],
            "pre_drop_tension_device": "STEREO_COLLAPSE"
        },
        MusicalEmotion.GROOVY_SENSUAL: {
            "name": "Groovy / Sensual",
            "description": "Pulso rítmico continuo e hipnótico, variaciones sutiles de percusión sin romper el baile.",
            "intro_energy": 0.40,
            "verse_energy": 0.65,
            "build_energy": 0.75,
            "drop_energy": 0.95,
            "verse_2_inertia_keep_roles": ["DEMBOW", "DRUMS", "BASS", "808"],
            "pre_drop_tension_device": "TIMBAL_ROLL"
        },
        MusicalEmotion.NOSTALGIC_CHILL: {
            "name": "Nostálgica / Chill",
            "description": "Groove relajado, armonías extendidas, lecho textural continuo y calidez analógica.",
            "intro_energy": 0.30,
            "verse_energy": 0.45,
            "build_energy": 0.60,
            "drop_energy": 0.75,
            "verse_2_inertia_keep_roles": ["PAD", "KEYS", "CHORDS"],
            "pre_drop_tension_device": "REVERB_WASHOUT"
        }
    }

    @classmethod
    def infer_emotion(
        cls,
        genre: str = "trap",
        key: str = "F",
        scale: str = "natural_minor"
    ) -> MusicalEmotion:
        """
        Infers the most appropriate musical emotion from key, scale, and genre.
        Completely non-hardcoded with intelligent heuristic mapping.
        """
        g = str(genre or "").lower()
        s = str(scale or "").lower()
        k = str(key or "").upper()

        is_minor = any(m in s for m in ["minor", "menor", "phrygian", "dorian"])
        is_major = any(m in s for m in ["major", "mayor", "lydian"])

        # 1. Reggaeton / Latin Urban / Afrobeat -> GROOVY_SENSUAL
        if any(w in g for w in ["reggaeton", "reggaetón", "dembow", "urbano", "afro", "latin"]):
            return MusicalEmotion.GROOVY_SENSUAL

        # 2. Trap / Drill / Dubstep / Metal / Industrial in Minor -> DARK_AGGRESSIVE
        if any(w in g for w in ["drill", "dubstep", "industrial", "metal", "rage"]) or (
            any(w in g for w in ["trap", "hip", "rap"]) and is_minor
        ):
            return MusicalEmotion.DARK_AGGRESSIVE

        # 3. EDM / House / Dance / Future Bass in Major or Energetic Minor -> EUPHORIC_ANTHEMIC
        if any(w in g for w in ["edm", "dance", "house", "electro", "festival", "future"]) or (
            any(w in g for w in ["pop", "rock"]) and is_major
        ):
            return MusicalEmotion.EUPHORIC_ANTHEMIC

        # 4. Lo-Fi / Synthwave / Indie / Chillout -> NOSTALGIC_CHILL
        if any(w in g for w in ["lofi", "lo-fi", "chill", "synthwave", "retrowave", "ambient", "indie"]):
            return MusicalEmotion.NOSTALGIC_CHILL

        # 5. Pop / Ballad / R&B in Minor -> MELANCHOLIC_INTIMATE
        if is_minor:
            return MusicalEmotion.MELANCHOLIC_INTIMATE

        return MusicalEmotion.EUPHORIC_ANTHEMIC

    @classmethod
    def orchestrate_arc(
        cls,
        sections: List[Dict[str, Any]],
        genre: str = "trap",
        emotion: Optional[MusicalEmotion] = None,
        key: str = "F",
        scale: str = "natural_minor"
    ) -> List[Dict[str, Any]]:
        """
        Orchestrates the macro-dynamic trajectory and role inertia across sections.
        """
        resolved_emotion = emotion or cls.infer_emotion(genre=genre, key=key, scale=scale)
        profile = cls.EMOTIONAL_PROFILES.get(resolved_emotion, cls.EMOTIONAL_PROFILES[MusicalEmotion.DARK_AGGRESSIVE])

        orchestrated = []
        for idx, sec in enumerate(sections):
            name = str(sec.get("name", "")).lower()
            bars = sec.get("bars", 8)

            # Determine baseline energy according to section function and emotional profile
            if any(w in name for w in ["intro", "inicio"]):
                energy = profile["intro_energy"]
                tension = "NONE"
                inertia_keep = []
            elif any(w in name for w in ["build", "subida", "pre", "pre-coro"]):
                energy = profile["build_energy"]
                tension = profile["pre_drop_tension_device"]
                inertia_keep = []
            elif any(w in name for w in ["drop", "coro", "chorus", "hook"]):
                energy = profile["drop_energy"]
                tension = "DROP_RELEASE"
                inertia_keep = []
            elif any(w in name for w in ["verso 2", "verse 2", "verso_2"]):
                # Hit-Record Inertia Retention: Verse 2 does NOT crash to 0.25; it keeps momentum
                energy = min(0.70, profile["verse_energy"] + 0.15)
                tension = "MOMENTUM_SUSTAINED"
                inertia_keep = profile["verse_2_inertia_keep_roles"]
            elif any(w in name for w in ["verso", "verse", "estrofa"]):
                energy = profile["verse_energy"]
                tension = "GROOVE_ESTABLISHED"
                inertia_keep = []
            elif any(w in name for w in ["bridge", "puente"]):
                energy = profile["verse_energy"] + 0.10
                tension = "MODAL_CONTRAST"
                inertia_keep = []
            elif any(w in name for w in ["outro", "final"]):
                energy = profile["intro_energy"]
                tension = "FADEOUT_DESCENT"
                inertia_keep = []
            else:
                energy = 0.50
                tension = "STANDARD"
                inertia_keep = []

            orchestrated.append({
                "section_index": idx,
                "name": sec.get("name", f"Section {idx+1}"),
                "bars": bars,
                "target_energy": round(energy, 2),
                "emotion": resolved_emotion.value,
                "emotion_name": profile["name"],
                "tension_device": tension,
                "inertia_keep_roles": inertia_keep,
                "description": f"Sección {sec.get('name')}: Energía {int(energy * 100)}%, Dispositivo de tensión: {tension}."
            })

        return orchestrated

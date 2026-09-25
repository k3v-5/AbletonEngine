# engine/fx/aesthetic_profile_engine.py
"""
Aesthetic Profile Engine:
Governs genre-specific effect chains, mandatory vs optional device policies,
interactive queries for uncatalogued genres, and persistent documentation of
sound design decisions per instrument.

Core Principles:
1. Zero Default Assumption: The engine never selects chains silently; it queries
   the user/AI track-by-track using a standardized structured query.
2. Genre Learning & Persistence: Unknown genres prompt the AI to define mandatory
   vs optional effects per role, stored permanently in state/learned/aesthetic_profiles.json.
3. Instrument Decision Ledger: Decisions taken on new or atypical instruments are
   formally documented and suggested in future sessions.
"""

import os
import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger("AestheticProfileEngine")

_DEFAULT_STORAGE_PATH = Path(__file__).resolve().parent.parent.parent / "state" / "learned" / "aesthetic_profiles.json"


@dataclass
class RoleFXProfile:
    """Defines mandatory and optional effects for a musical role in an aesthetic profile."""
    mandatory_effects: List[str] = field(default_factory=list)
    optional_effects: List[str] = field(default_factory=list)
    descriptions: Dict[str, str] = field(default_factory=dict)
    default_parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    role_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mandatory_effects": list(self.mandatory_effects),
            "optional_effects": list(self.optional_effects),
            "descriptions": dict(self.descriptions),
            "default_parameters": dict(self.default_parameters),
            "role_notes": self.role_notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoleFXProfile":
        return cls(
            mandatory_effects=list(data.get("mandatory_effects", [])),
            optional_effects=list(data.get("optional_effects", [])),
            descriptions=dict(data.get("descriptions", {})),
            default_parameters=dict(data.get("default_parameters", {})),
            role_notes=str(data.get("role_notes", ""))
        )


@dataclass
class InstrumentDecision:
    """Records a sound design decision taken for an individual instrument."""
    instrument_name: str
    role: str
    effects_added: List[str] = field(default_factory=list)
    configurations: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument_name": self.instrument_name,
            "role": self.role,
            "effects_added": list(self.effects_added),
            "configurations": dict(self.configurations),
            "reason": self.reason,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstrumentDecision":
        return cls(
            instrument_name=str(data.get("instrument_name", "")),
            role=str(data.get("role", "OTHER")),
            effects_added=list(data.get("effects_added", [])),
            configurations=dict(data.get("configurations", {})),
            reason=str(data.get("reason", "")),
            timestamp=str(data.get("timestamp", ""))
        )


@dataclass
class AestheticGenreProfile:
    """Complete aesthetic FX and sound design profile for a musical genre."""
    genre: str
    display_name: str
    roles: Dict[str, RoleFXProfile] = field(default_factory=dict)
    instrument_decisions: Dict[str, InstrumentDecision] = field(default_factory=dict)
    aesthetic_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genre": self.genre,
            "display_name": self.display_name,
            "roles": {r: prof.to_dict() for r, prof in self.roles.items()},
            "instrument_decisions": {k: d.to_dict() for k, d in self.instrument_decisions.items()},
            "aesthetic_notes": self.aesthetic_notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AestheticGenreProfile":
        roles = {}
        for r, r_data in data.get("roles", {}).items():
            roles[str(r).upper()] = RoleFXProfile.from_dict(r_data)
        decisions = {}
        for k, d_data in data.get("instrument_decisions", {}).items():
            decisions[str(k)] = InstrumentDecision.from_dict(d_data)
        return cls(
            genre=str(data.get("genre", "generic")).lower(),
            display_name=str(data.get("display_name", data.get("genre", "Generic"))),
            roles=roles,
            instrument_decisions=decisions,
            aesthetic_notes=str(data.get("aesthetic_notes", ""))
        )


# Baseline seed profiles for established genres
_SEED_PROFILES: Dict[str, Dict[str, Any]] = {
    "trap": {
        "genre": "trap",
        "display_name": "Trap / Modern Urban",
        "aesthetic_notes": "Punchy transient drums, clipped sub-bass, clean stereo separation, dark warm chords.",
        "roles": {
            "DRUMS": {
                "mandatory_effects": ["EQ Eight", "Glue Compressor"],
                "optional_effects": ["Saturator", "Redux", "ValhallaVintageVerb"],
                "descriptions": {
                    "EQ Eight": "Sub-cut at 25 Hz on kick, transient air bump at 8 kHz on snare.",
                    "Glue Compressor": "2:1 to 4:1 ratio for bus glue and transient control.",
                    "Saturator": "Soft Sine drive on 808 snare and claps.",
                    "Redux": "Lo-fi downsampling for dark hi-hat rolls.",
                    "ValhallaVintageVerb": "Plate mode 1980s for airy snare decay."
                }
            },
            "BASS": {
                "mandatory_effects": ["EQ Eight", "Utility"],
                "optional_effects": ["Saturator", "Glue Compressor"],
                "descriptions": {
                    "EQ Eight": "HPF at 25 Hz, notch at 200 Hz to unmask low mids.",
                    "Utility": "Bass Mono engaged below 120 Hz to preserve center phase.",
                    "Saturator": "Warm Drive 2.5 dB to generate 2nd/3rd harmonics for mobile speaker audibility."
                }
            },
            "KEYS": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["Chorus-Ensemble", "ValhallaVintageVerb", "Delay"],
                "descriptions": {
                    "EQ Eight": "Cut below 150 Hz to clear space for 808 bass fundamental.",
                    "Chorus-Ensemble": "Subtle 2-voice stereo width modulation.",
                    "ValhallaVintageVerb": "Chamber or Room mode for realistic studio depth."
                }
            },
            "PAD": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["ValhallaSupermassive", "ValhallaVintageVerb", "Auto Pan"],
                "descriptions": {
                    "EQ Eight": "Gentle band-pass leaving 300 Hz - 7 kHz.",
                    "ValhallaSupermassive": "Andromeda Cloud for massive ambient halo.",
                    "ValhallaVintageVerb": "Cathedral 1970s mode for dark cinematic width."
                }
            },
            "LEAD": {
                "mandatory_effects": ["EQ Eight", "Compressor"],
                "optional_effects": ["Delay", "ValhallaVintageVerb", "Saturator"],
                "descriptions": {
                    "EQ Eight": "Surgical notch at harsh resonance peaks (2.5 kHz - 4 kHz).",
                    "Compressor": "Fast clamp for consistent melodic presence in dense drop.",
                    "Delay": "Dotted 8th note stereo ping-pong bounce."
                }
            },
            "VOCALS": {
                "mandatory_effects": ["EQ Eight", "Compressor"],
                "optional_effects": ["ValhallaVintageVerb", "Delay", "Auto-Tune Artist"],
                "descriptions": {
                    "EQ Eight": "High-pass at 85 Hz, de-mud notch at 350 Hz, high shelf at 12 kHz.",
                    "Compressor": "Opto style or peak limiting 4:1 ratio.",
                    "ValhallaVintageVerb": "Smooth Plate 1980s mode for clean silkiness."
                }
            },
            "FX": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["Auto Pan", "ValhallaSupermassive", "Delay"],
                "descriptions": {
                    "EQ Eight": "Cut low end below 200 Hz on sweep risers.",
                    "ValhallaSupermassive": "Space expansion for cinematic impact."
                }
            }
        }
    },
    "edm": {
        "genre": "edm",
        "display_name": "Electronic Dance Music / Progressive",
        "aesthetic_notes": "High dynamic contrast, heavy sidechain ducking, pristine ultra-bright top end, wide stereo leads.",
        "roles": {
            "DRUMS": {
                "mandatory_effects": ["EQ Eight", "Glue Compressor"],
                "optional_effects": ["Saturator", "Overdrive"],
                "descriptions": {
                    "EQ Eight": "Tight low cut at 30 Hz, surgical snap at 4 kHz.",
                    "Glue Compressor": "Punch mode (Attack 30ms, Release auto) for transient punch."
                }
            },
            "BASS": {
                "mandatory_effects": ["EQ Eight", "Compressor", "Utility"],
                "optional_effects": ["Saturator", "Dynamic EQ"],
                "descriptions": {
                    "EQ Eight": "Sub anchor preservation, notch kick frequency.",
                    "Compressor": "Sidechain ducking triggered by main kick.",
                    "Utility": "Strict Bass Mono <= 130 Hz."
                }
            },
            "LEAD": {
                "mandatory_effects": ["EQ Eight", "Compressor"],
                "optional_effects": ["ValhallaVintageVerb", "Delay", "OTT"],
                "descriptions": {
                    "EQ Eight": "Cut below 250 Hz, presence boost at 5 kHz.",
                    "Compressor": "Heavy pumping sidechain for drop impact.",
                    "ValhallaVintageVerb": "Bright Hall mode for soaring festival leads."
                }
            },
            "PAD": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["ValhallaSupermassive", "Chorus-Ensemble"],
                "descriptions": {
                    "EQ Eight": "Low cut at 180 Hz.",
                    "ValhallaSupermassive": "Lyra Space for lush floating chords."
                }
            },
            "KEYS": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["ValhallaVintageVerb", "Chorus-Ensemble"],
                "descriptions": {
                    "EQ Eight": "Clean body 200 Hz - 8 kHz.",
                    "ValhallaVintageVerb": "Concert Hall for concert piano depth."
                }
            },
            "VOCALS": {
                "mandatory_effects": ["EQ Eight", "Compressor"],
                "optional_effects": ["ValhallaVintageVerb", "Delay"],
                "descriptions": {
                    "EQ Eight": "Bright modern pop curve with air shelf.",
                    "Compressor": "Dual stage peak + leveling."
                }
            },
            "FX": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["Delay", "ValhallaSupermassive"],
                "descriptions": {
                    "EQ Eight": "Band pass filtering for risers and sweeps."
                }
            }
        }
    },
    "techno": {
        "genre": "techno",
        "display_name": "Peak Time / Raw Techno",
        "aesthetic_notes": "Rumbling industrial sub-reverb, dark analog warmth, repetitive hypnotic filtering, distortion harmonics.",
        "roles": {
            "DRUMS": {
                "mandatory_effects": ["EQ Eight", "Saturator"],
                "optional_effects": ["ValhallaVintageVerb", "Overdrive", "Glue Compressor"],
                "descriptions": {
                    "EQ Eight": "Weight at 50 Hz, cut harshness above 10 kHz.",
                    "Saturator": "Hard Curve or Sinoid for aggressive analog punch.",
                    "ValhallaVintageVerb": "Dirty Hall mode for techno kick rumble sub."
                }
            },
            "BASS": {
                "mandatory_effects": ["EQ Eight", "Utility"],
                "optional_effects": ["Saturator", "Compressor"],
                "descriptions": {
                    "EQ Eight": "Tight sub focus, HPF at 28 Hz.",
                    "Utility": "Mono below 140 Hz strictly enforced."
                }
            },
            "LEAD": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["Delay", "ValhallaVintageVerb", "Redux"],
                "descriptions": {
                    "EQ Eight": "Dark filter sweep 400 Hz to 4 kHz.",
                    "Delay": "Hypnotic 16th note ping-pong with high feedback."
                }
            },
            "PAD": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["ValhallaVintageVerb", "Phaser"],
                "descriptions": {
                    "EQ Eight": "High-cut at 6 kHz for dark dystopian textures."
                }
            },
            "FX": {
                "mandatory_effects": ["EQ Eight"],
                "optional_effects": ["Delay", "Redux"],
                "descriptions": {
                    "EQ Eight": "Resonant sweep filtering."
                }
            }
        }
    }
}


class AestheticProfileEngine:
    """
    Manages aesthetic effect profiles per genre and track-by-track decision records.
    Never assumes default effect chains. Persists newly registered genres and
    unregistered instrument decisions.
    """

    def __init__(self, profiles_path: Optional[Path] = None):
        self.profiles_path = profiles_path or _DEFAULT_STORAGE_PATH
        self._profiles: Dict[str, AestheticGenreProfile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Loads profiles from disk, seeding with defaults if absent."""
        # 1. Populate seed profiles
        for g_k, g_data in _SEED_PROFILES.items():
            self._profiles[g_k.lower()] = AestheticGenreProfile.from_dict(g_data)

        # 2. Merge learned profiles from disk
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for g_k, g_val in data.items():
                        if isinstance(g_val, dict):
                            self._profiles[g_k.lower()] = AestheticGenreProfile.from_dict(g_val)
                logger.info(f"Loaded {len(self._profiles)} aesthetic profiles from {self.profiles_path}")
            except Exception as e:
                logger.warning(f"Notice loading aesthetic profiles from {self.profiles_path}: {e}")

    def save_to_disk(self) -> bool:
        """Serializes current profiles to state/learned/aesthetic_profiles.json."""
        try:
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
            export_dict = {k: prof.to_dict() for k, prof in self._profiles.items()}
            with open(self.profiles_path, "w", encoding="utf-8") as f:
                json.dump(export_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(export_dict)} aesthetic profiles to {self.profiles_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save aesthetic profiles: {e}")
            return False

    def has_profile(self, genre: str) -> bool:
        """Checks if an aesthetic profile exists for the given genre."""
        g_norm = str(genre).strip().lower()
        return g_norm in self._profiles

    def get_profile(self, genre: str) -> Optional[AestheticGenreProfile]:
        """Retrieves profile for genre, or None if uncatalogued."""
        g_norm = str(genre).strip().lower()
        return self._profiles.get(g_norm)

    def register_or_update_profile(
        self,
        genre: str,
        profile_data: Union[Dict[str, Any], AestheticGenreProfile]
    ) -> AestheticGenreProfile:
        """
        Registers a new genre aesthetic profile or updates an existing one,
        persisting it permanently to disk.
        """
        g_norm = str(genre).strip().lower()
        if isinstance(profile_data, AestheticGenreProfile):
            prof = profile_data
            prof.genre = g_norm
        else:
            p_dict = dict(profile_data)
            p_dict["genre"] = g_norm
            if "display_name" not in p_dict:
                p_dict["display_name"] = str(genre).capitalize()
            prof = AestheticGenreProfile.from_dict(p_dict)

        self._profiles[g_norm] = prof
        self.save_to_disk()
        return prof

    def document_instrument_decision(
        self,
        genre: str,
        instrument_name: str,
        role: str,
        effects_added: List[str],
        configurations: Optional[Dict[str, Any]] = None,
        reason: str = ""
    ) -> InstrumentDecision:
        """
        Documents and persists a sound design decision taken for an instrument
        (novel or unprofiled) within a genre, so it can be suggested in future sessions.
        """
        import datetime
        g_norm = str(genre).strip().lower()
        prof = self.get_profile(g_norm)
        if not prof:
            prof = self.register_or_update_profile(g_norm, {
                "genre": g_norm,
                "display_name": str(genre).capitalize(),
                "roles": {},
                "instrument_decisions": {}
            })

        timestamp = datetime.datetime.now().isoformat()
        decision = InstrumentDecision(
            instrument_name=instrument_name,
            role=role.upper(),
            effects_added=list(effects_added),
            configurations=dict(configurations or {}),
            reason=reason or f"Efectos elegidos deliberadamente para {instrument_name} en rol {role}.",
            timestamp=timestamp
        )

        # Record by lowercased instrument identifier
        inst_key = instrument_name.strip().lower()
        prof.instrument_decisions[inst_key] = decision

        # Also update role profile optional/mandatory effects if not already present
        r_upper = role.upper()
        if r_upper not in prof.roles:
            prof.roles[r_upper] = RoleFXProfile()
        r_prof = prof.roles[r_upper]
        for eff in effects_added:
            if eff not in r_prof.mandatory_effects and eff not in r_prof.optional_effects:
                r_prof.optional_effects.append(eff)

        self.save_to_disk()
        logger.info(f"Documented decision for instrument '{instrument_name}' in genre '{genre}': {effects_added}")
        return decision

    def get_instrument_decision(self, genre: str, instrument_name: str) -> Optional[InstrumentDecision]:
        """Returns documented past decision for instrument in this genre, if available."""
        prof = self.get_profile(genre)
        if not prof:
            return None
        inst_key = instrument_name.strip().lower()
        return prof.instrument_decisions.get(inst_key)

    # -------------------------------------------------------------------------
    # STANDARDIZED QUERIES (NO ASSUMPTIONS / STRUCTURED INTERFACE)
    # -------------------------------------------------------------------------

    def build_standardized_genre_query(self, genre: str) -> Dict[str, Any]:
        """
        Builds a standardized structured prompt when an unprofiled genre is encountered.
        Asks the AI/user to define mandatory and optional effects per role.
        """
        roles_example = {
            "DRUMS": {"mandatory": ["EQ Eight", "Glue Compressor"], "optional": ["Saturator", "Redux"]},
            "BASS": {"mandatory": ["EQ Eight", "Utility"], "optional": ["Saturator", "Compressor"]},
            "LEAD": {"mandatory": ["EQ Eight", "Compressor"], "optional": ["Delay", "ValhallaVintageVerb"]},
            "KEYS": {"mandatory": ["EQ Eight"], "optional": ["Chorus-Ensemble", "ValhallaVintageVerb"]},
            "PAD": {"mandatory": ["EQ Eight"], "optional": ["ValhallaSupermassive", "Auto Pan"]},
            "VOCALS": {"mandatory": ["EQ Eight", "Compressor"], "optional": ["ValhallaVintageVerb", "Auto-Tune Artist"]},
            "FX": {"mandatory": ["EQ Eight"], "optional": ["ValhallaSupermassive", "Delay"]}
        }
        example_json = json.dumps(roles_example, indent=2)

        return {
            "status": "AESTHETIC_PROFILE_REQUIRED",
            "phase": "PHASE_5_INSERT_EFFECTS",
            "genre": genre,
            "current_step": f"PASO 5: PERFIL ESTÉTICO REQUERIDO (GÉNERO '{genre.upper()}')",
            "action_taken": f"El motor detectó un nuevo género ('{genre}') sin perfil estético registrado. Se prohíbe asumir cadenas por defecto.",
            "question": (
                f"🎨 **NUEVO GÉNERO DETECTADO: '{genre.upper()}' — DEFINICIÓN DE PERFIL ESTÉTICO**\n\n"
                f"El motor nunca asume cadenas de efectos por defecto. Para este nuevo género, la IA/usuario debe definir "
                f"qué efectos deben agregarse la próxima vez de forma **obligatoria** y cuáles de forma **opcional** para cada rol.\n\n"
                f"📐 **Estructura Estandarizada Requerida:**\n"
                f"```json\n"
                f"{example_json}\n"
                f"```\n\n"
                f"✨ **Instrucciones:**\n"
                f"• Puedes responder con un JSON en la estructura anterior o en texto ordenado (ej: 'DRUMS: obligatorio: EQ Eight, Compressor; opcional: Saturator').\n"
                f"• El motor guardará este perfil en `state/learned/aesthetic_profiles.json` para reutilizarlo en futuras sesiones."
            ),
            "instructions_for_ai": "Define la configuración de efectos obligatorios y opcionales para los roles de este nuevo género en formato JSON estructurado.",
            "schema_expected": roles_example
        }

    def parse_standardized_genre_input(
        self,
        genre: str,
        user_input: Union[str, Dict[str, Any]]
    ) -> Optional[AestheticGenreProfile]:
        """
        Parses structured AI/user input (JSON or formatted text) defining a new genre profile.
        Returns the registered AestheticGenreProfile or None if parsing failed.
        """
        parsed_dict: Optional[Dict[str, Any]] = None

        if isinstance(user_input, dict):
            parsed_dict = user_input
        elif isinstance(user_input, str):
            # Attempt JSON parsing
            clean_str = user_input.strip()
            # Extract JSON block if wrapped in markdown code fence
            if "```" in clean_str:
                m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean_str)
                if m:
                    clean_str = m.group(1).strip()
            try:
                js = json.loads(clean_str)
                if isinstance(js, dict):
                    parsed_dict = js
            except Exception:
                pass

        if not parsed_dict and isinstance(user_input, str):
            # Fallback: Line-by-line regex parsing (e.g. "DRUMS: obligatorio: EQ Eight, Compressor; opcional: Saturator")
            roles_found = {}
            lines = user_input.splitlines()
            for line in lines:
                m = re.search(r'\b(DRUMS|BASS|LEAD|KEYS|PAD|VOCALS|FX|STRINGS|SYNTH|PLUCK)\b\s*[:\-]\s*(.*)', line, re.IGNORECASE)
                if m:
                    r_name = m.group(1).upper()
                    body = m.group(2)
                    mand_match = re.search(r'(?:mandatory|obligatorio|obligatorios)\s*[:\-]?\s*([^;]+)', body, re.IGNORECASE)
                    opt_match = re.search(r'(?:optional|opcional|opcionales)\s*[:\-]?\s*([^;]+)', body, re.IGNORECASE)
                    
                    mand_list = [e.strip() for e in mand_match.group(1).split(",") if e.strip()] if mand_match else []
                    opt_list = [e.strip() for e in opt_match.group(1).split(",") if e.strip()] if opt_match else []

                    # If neither keyword was present, treat all listed effects as mandatory
                    if not mand_list and not opt_list:
                        mand_list = [e.strip() for e in body.split(",") if e.strip()]

                    roles_found[r_name] = {
                        "mandatory_effects": mand_list,
                        "optional_effects": opt_list
                    }
            if roles_found:
                parsed_dict = {"roles": roles_found}

        if not parsed_dict:
            return None

        # Build RoleFXProfile objects
        roles_data = parsed_dict.get("roles", parsed_dict)
        roles_obj: Dict[str, RoleFXProfile] = {}
        for r_k, r_v in roles_data.items():
            if isinstance(r_v, dict):
                m_list = r_v.get("mandatory", r_v.get("mandatory_effects", []))
                o_list = r_v.get("optional", r_v.get("optional_effects", []))
                # Ensure EQ is always in mandatory for spectral safety if not present
                if not any("eq" in e.lower() for e in m_list):
                    m_list = ["EQ Eight"] + list(m_list)
                roles_obj[str(r_k).upper()] = RoleFXProfile(
                    mandatory_effects=list(m_list),
                    optional_effects=list(o_list),
                    descriptions=r_v.get("descriptions", {}),
                    default_parameters=r_v.get("parameters", r_v.get("default_parameters", {})),
                    role_notes=str(r_v.get("notes", ""))
                )

        prof = AestheticGenreProfile(
            genre=str(genre).lower(),
            display_name=str(parsed_dict.get("display_name", genre.capitalize())),
            roles=roles_obj,
            aesthetic_notes=str(parsed_dict.get("aesthetic_notes", f"Perfil estético aprendido para {genre}."))
        )
        return self.register_or_update_profile(genre, prof)

    def build_track_fx_selection_query(
        self,
        track: Dict[str, Any],
        genre: str,
        track_index: int,
        total_tracks: int
    ) -> Dict[str, Any]:
        """
        Builds the standardized track-by-track query asking what effects to add.
        Presents mandatory and optional effects from profile, plus any past
        documented decisions for this specific instrument.
        """
        t_name = track.get("name", f"Pista {track_index}")
        t_idx = track.get("index", track_index)
        role = str(track.get("role", "OTHER")).upper()
        inst_name = str(track.get("instrument", "Instrumento no especificado"))

        prof = self.get_profile(genre)
        role_prof = prof.roles.get(role, RoleFXProfile()) if prof else RoleFXProfile()

        # Check for past documented decisions for this instrument
        past_decision = self.get_instrument_decision(genre, inst_name)
        past_note = ""
        if past_decision:
            eff_str = ", ".join(past_decision.effects_added)
            past_note = f"\n💡 **Decisión Histórica Documentada para '{inst_name}':** Se agregaron previamente `[{eff_str}]` ({past_decision.reason})."

        mand_str = ", ".join(role_prof.mandatory_effects) if role_prof.mandatory_effects else "EQ Eight (obligatorio para seguridad espectral)"
        opt_str = ", ".join(role_prof.optional_effects) if role_prof.optional_effects else "Saturator, ValhallaVintageVerb, Compressor"

        return {
            "status": "TRACK_FX_SELECTION_REQUIRED",
            "phase": "PHASE_5_INSERT_EFFECTS",
            "current_step": f"PASO 5: SELECCIÓN DE EFECTOS (PISTA {track_index + 1} DE {total_tracks}: '{t_name}')",
            "action_taken": f"El motor consulta deliberadamente la cadena de efectos para '{t_name}' (Rol: {role}, Instrumento: '{inst_name}').",
            "question": (
                f"🎛️ **SELECCIÓN DELIBERADA DE CADENA DE INSERCIÓN: Pista {track_index + 1}/{total_tracks} ('{t_name}')**\n\n"
                f"• **Rol Musical:** `{role}`\n"
                f"• **Instrumento Generador:** `{inst_name}`\n"
                f"• **Perfil Estético Activo ({genre.upper()}):**\n"
                f"  - 🔴 **Efectos Obligatorios:** `{mand_str}`\n"
                f"  - 🟡 **Efectos Opcionales Disponibles:** `{opt_str}`\n"
                f"{past_note}\n\n"
                f"🧠 **Decisión Técnica Requerida (Cero Cadenas por Defecto):**\n"
                f"El motor prohíbe asumir cadenas ciegas. Indica qué procesadores deseas insertar en esta pista.\n\n"
                f"📌 **Formatos de Respuesta Válidos:**\n"
                f"• `\"Confirmar obligatorios\"` o `\"Opción 1\"`: Inserta la cadena base recomendada por el perfil (`{mand_str}`).\n"
                f"• `\"Cadena: EQ Eight, Saturator, ValhallaVintageVerb\"`: Define tu lista explícita de efectos para este canal.\n"
                f"• Si este instrumento requiere efectos personalizados no contemplados, el motor documentará tu decisión para sugerirla después."
            ),
            "instructions_for_ai": f"Define la lista explícita de efectos a insertar en '{t_name}' (ej: 'EQ Eight, Compressor' o 'Opción 1').",
            "target_track": t_idx,
            "role": role,
            "instrument": inst_name,
            "mandatory_effects": role_prof.mandatory_effects,
            "optional_effects": role_prof.optional_effects
        }

    def parse_track_fx_selection(
        self,
        user_input: str,
        genre: str,
        role: str,
        instrument: str
    ) -> List[str]:
        """
        Parses user/AI response to resolve the exact list of effects to install on the track.
        Documents decision if instrument is novel or has custom choices.
        """
        text = str(user_input).strip()
        role_upper = str(role).upper()
        prof = self.get_profile(genre)
        role_prof = prof.roles.get(role_upper, RoleFXProfile()) if prof else RoleFXProfile()

        # 1. Opción 1 / Confirmar obligatorios
        if any(w in text.lower() for w in ["opcion 1", "opción 1", "confirmar", "obligatorios", "aceptar sugerencia", "por defecto", "standard"]):
            chosen = list(role_prof.mandatory_effects) if role_prof.mandatory_effects else ["EQ Eight"]
            if not any("eq" in e.lower() for e in chosen):
                chosen.insert(0, "EQ Eight")
            return chosen

        # 2. Explicit list of effects (e.g. "Cadena: EQ Eight, Saturator, Delay" or "EQ Eight, Compressor")
        clean_list_str = re.sub(r'(?:cadena|efectos|insertar|agregar|usar)\s*[:\-]?\s*', '', text, flags=re.IGNORECASE)
        candidates = [c.strip() for c in re.split(r'[,;y\n]+', clean_list_str) if c.strip()]

        known_canonical = [
            "EQ Eight", "Glue Compressor", "Compressor", "Saturator", "Utility",
            "Delay", "Reverb", "Chorus-Ensemble", "Phaser-Flanger", "Redux",
            "Overdrive", "Auto Pan", "Drum Buss", "ValhallaVintageVerb",
            "ValhallaSupermassive", "Surge XT Effects", "Auto-Tune Artist"
        ]

        resolved = []
        for cand in candidates:
            match = None
            for kn in known_canonical:
                if kn.lower() == cand.lower() or cand.lower() in kn.lower():
                    match = kn
                    break
            if match:
                if match not in resolved:
                    resolved.append(match)
            elif len(cand) >= 2:
                resolved.append(cand.title())

        # Enforce EQ Eight presence for spectral safety
        if not any("eq" in e.lower() for e in resolved):
            resolved.insert(0, "EQ Eight")

        # Document decision for instrument learning
        if resolved:
            self.document_instrument_decision(
                genre=genre,
                instrument_name=instrument,
                role=role,
                effects_added=resolved,
                reason=f"Configuración personalizada seleccionada: {', '.join(resolved)}"
            )

        return resolved

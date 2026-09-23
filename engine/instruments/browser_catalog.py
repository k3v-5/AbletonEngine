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
    VST2 = "vst2"
    NATIVE_SYNTH = "native_synth"
    DRUM_KIT = "drum_kit"
    AUDIO_EFFECT = "audio_effect"


@dataclass
class SoundSourceOption:
    id: str
    name: str
    role: str  # "KEYS", "BASS", "LEAD", "STRINGS", "PAD", "DRUMS", "VOCALS", "FX", "MASTER"
    category: InstrumentSourceCategory
    uri: str
    vendor: Optional[str] = None
    description: str = ""
    blueprint: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "category": self.category.value,
            "uri": self.uri,
            "vendor": self.vendor,
            "description": self.description,
            "blueprint": self.blueprint,
        }


# Comprehensive 13-type instrument role catalog for intelligent session orchestration
# Re-export curated catalogs from decoupled data module
from .curated_data import INSTRUMENT_ROLE_CATALOG, CURATED_SOURCES

class LiveBrowserCatalogEngine:
    """
    Catalog inspection and dynamic instrument loader with hierarchical acoustic classification.
    """

    ROLE_FAMILY_MAPPING: Dict[str, str] = {
        "COUNTER_LEAD": "LEAD",
        "COUNTERLEAD": "LEAD",
        "COUNTER_MELODY": "LEAD",
        "ARP": "LEAD",
        "ARPS": "LEAD",
        "ARPEGGIO": "LEAD",
        "EAR_CANDY": "LEAD",
        "EARCANDY": "LEAD",
        "TEXTURE_FOLEY": "PAD",
        "TEXTURE": "PAD",
        "FOLEY": "PAD",
        "NOISE": "PAD",
        "SUB_BASS": "BASS",
        "SUB": "BASS",
        "808": "BASS",
        "REESE": "BASS",
        "PLUCK": "KEYS",
        "PLUCKS": "KEYS",
        "CHORDS": "KEYS",
        "PIANO": "KEYS",
        "RHODES": "KEYS",
        "TECLADO": "KEYS",
        "BRASS_STAB": "BRASS",
        "FANFARE": "BRASS",
        "STRINGS_ORCH": "STRINGS",
        "CELLO": "STRINGS",
        "VIOLIN": "STRINGS",
        "PERCUSSION": "PERCUSSION",
        "CLAP": "PERCUSSION",
        "PALMAS": "PERCUSSION",
        "SHAKER": "PERCUSSION",
        "BONGO": "PERCUSSION",
        "VOCAL_CHOP": "VOCALS",
        "VOX": "VOCALS",
        "RHYTHM_GUITAR": "GUITAR",
        "LEAD_GUITAR": "GUITAR",
        "808_BASS": "BASS",
        "ELECTRIC_BASS": "BASS",
        "DEMBOW": "DRUMS",
        "BACKING_VOCALS": "VOCALS",
    }

    @classmethod
    def get_parent_acoustic_role(cls, role: str) -> str:
        """
        Resolves any specialized sub-role or creative alias to its canonical parent acoustic family.
        """
        clean = str(role or "").upper().strip()
        if clean in cls.ROLE_FAMILY_MAPPING:
            return cls.ROLE_FAMILY_MAPPING[clean]
        from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
        norm = RoleTrackOrchestrator.normalize_role(clean)
        if norm in cls.ROLE_FAMILY_MAPPING:
            return cls.ROLE_FAMILY_MAPPING[norm]
        return norm or "KEYS"

    @classmethod
    def scan_user_custom_racks_for_role(cls, role: str) -> List[SoundSourceOption]:
        """
        Dynamically scans the user's User Library for custom Instrument Racks (.adg)
        saved under ANALOG LAB V, Omnisphere, or dedicated role folders.
        """
        import urllib.parse
        import os
        from pathlib import Path
        role_upper = str(role).upper().strip()
        from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
        norm_role = RoleTrackOrchestrator.normalize_role(role_upper)

        candidate_bases = [
            Path(r"D:\Documentos\Ableton\User Library\Presets\Instruments\Instrument Rack"),
            Path.home() / "Documents" / "Ableton" / "User Library" / "Presets" / "Instruments" / "Instrument Rack"
        ]
        base_dir = next((b for b in candidate_bases if b.exists()), None)
        if not base_dir:
            return []

        role_to_subfolders = {
            "BRASS": ["ANALOG LAB V/Brass", "Omnisphere/Brass", "BRASS"],
            "CHOIR": ["Omnisphere/Human Voices", "ANALOG LAB V/Choir", "CHOIR", "VOCALS"],
            "VOCALS": ["Omnisphere/Human Voices", "ANALOG LAB V/Choir", "CHOIR", "VOCALS"],
            "STRINGS": ["ANALOG LAB V/Strings", "Omnisphere/Pads + Strings", "Omnisphere/Bowed Colors", "STRINGS"],
            "BASS": ["ANALOG LAB V/Bass", "Omnisphere/Bass", "BASS"],
            "KEYS": ["ANALOG LAB V/Piano", "ANALOG LAB V/Electric Piano", "ANALOG LAB V/Keys", "Omnisphere/Bells", "Omnisphere/Ethnic World", "KEYS"],
            "LEAD": ["ANALOG LAB V/Lead", "Omnisphere/Lead", "LEAD"],
            "COUNTER_LEAD": ["ANALOG LAB V/Lead", "Omnisphere/Lead", "LEAD"],
            "EAR_CANDY": ["Omnisphere/Bells", "ANALOG LAB V/Keys", "Omnisphere/Plucked", "LEAD"],
            "TEXTURE_FOLEY": ["Omnisphere/Pads + Strings", "ANALOG LAB V/Pad", "PAD"],
            "PAD": ["Omnisphere/Pads + Strings", "ANALOG LAB V/Pad", "PAD"],
            "GUITAR": ["Omnisphere/Guitars", "ANALOG LAB V/Guitar", "GUITAR"],
            "DRUMS": ["DRUMS"],
            "KICK": ["KICK"],
        }

        target_subs = role_to_subfolders.get(norm_role, [norm_role])
        user_options = []
        for sub in target_subs:
            p = base_dir / sub.replace("/", os.sep)
            if not p.exists():
                continue
            for adg_path in sorted(p.glob("*.adg")):
                try:
                    rel_parts = adg_path.relative_to(base_dir).parts
                    encoded_parts = [urllib.parse.quote(part) for part in rel_parts]
                    uri = "query:UserLibrary#Presets:Instruments:Instrument%20Rack:" + ":".join(encoded_parts)
                    plugin_label = rel_parts[0] if len(rel_parts) > 1 else "Custom Rack"
                    clean_name = f"{adg_path.stem} ({plugin_label}) [.adg]"
                    slug_id = f"user_adg_{norm_role.lower()}_{urllib.parse.quote(adg_path.stem.lower()).replace('%', '_')}"
                    user_options.append(SoundSourceOption(
                        id=slug_id,
                        name=clean_name,
                        role=norm_role,
                        category=InstrumentSourceCategory.NATIVE_SYNTH,
                        uri=uri,
                        vendor=f"User / {plugin_label}",
                        description=f"Usuario Instrument Rack ({plugin_label}): {adg_path.stem}",
                        blueprint={
                            "sculpt_type": "macro",
                            "parameters": {},
                            "description": f"Custom {plugin_label} rack verified in User Library."
                        }
                    ))
                except Exception as ex:
                    logger.debug(f"Error parsing custom rack {adg_path}: {ex}")

        return user_options

    @classmethod
    def get_available_sources_for_role(
        cls,
        role: str,
        conn: Any = None,
        filter_installed: bool = True
    ) -> List[SoundSourceOption]:
        """
        Returns sound options for a musical role with 4-tier resilient resolution:
        1. Exact match in CURATED_SOURCES.
        2. Role alias match from RoleTrackOrchestrator.get_role_aliases().
        3. Parent acoustic family match from get_parent_acoustic_role().
        4. Universal guaranteed native fallback.
        Guarantees that the returned list is NEVER empty.
        """
        role_key = str(role or "").upper().strip()
        from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
        norm_role = RoleTrackOrchestrator.normalize_role(role_key)
        
        # Tier 1: Direct match in CURATED_SOURCES
        raw_sources = list(CURATED_SOURCES.get(norm_role, CURATED_SOURCES.get(role_key, [])))
        if not raw_sources:
            for k, v in CURATED_SOURCES.items():
                if k.upper() == norm_role or k.upper() == role_key:
                    raw_sources = list(v)
                    break

        # Tier 2: Role alias match from RoleTrackOrchestrator
        if not raw_sources:
            aliases = RoleTrackOrchestrator.get_role_aliases(norm_role)
            for alias in aliases:
                a_sources = CURATED_SOURCES.get(alias.upper(), [])
                if a_sources:
                    raw_sources = list(a_sources)
                    break

        # Tier 3: Parent acoustic family match
        if not raw_sources:
            parent_role = cls.get_parent_acoustic_role(norm_role)
            raw_sources = list(CURATED_SOURCES.get(parent_role, []))

        # Tier 4: Universal guaranteed fallback
        if not raw_sources:
            raw_sources = list(CURATED_SOURCES.get("KEYS", CURATED_SOURCES.get("LEAD", [])))

        if not filter_installed:
            return raw_sources

        # Cross-reference with InstalledPluginScanner
        try:
            from engine.instruments.installed_scanner import InstalledPluginScanner
            scanner = InstalledPluginScanner()
            scanned = scanner.scan()
            scanned_uris = {p.uri.lower() for p in scanned.values() if p.uri}
            scanned_names = {p.name.lower() for p in scanned.values() if p.name}
            scanned_keys = {k.lower() for k in scanned.keys()}
        except Exception:
            scanned = {}
            scanned_uris, scanned_names, scanned_keys = set(), set(), set()

        verified = []
        for opt in raw_sources:
            # 1. Native Live presets and devices are verified on Live 12 Suite
            if opt.category in (InstrumentSourceCategory.NATIVE_SYNTH, InstrumentSourceCategory.DRUM_KIT, InstrumentSourceCategory.AUDIO_EFFECT):
                if opt.vendor == "Ableton" or opt.uri.startswith("query:Sounds#") or opt.uri.startswith("query:Drums#") or opt.uri.startswith("query:AudioFx#") or opt.uri.startswith("query:Synths#"):
                    verified.append(opt)
                    continue

            # 2. VST3 plugins: must be physically scanned and confirmed on system
            if opt.category == InstrumentSourceCategory.VST3:
                opt_uri = opt.uri.lower()
                opt_name = opt.name.lower()
                opt_id = opt.id.lower()
                is_present = (
                    opt_uri in scanned_uris or
                    any(sn in opt_name or opt_name in sn for sn in scanned_names) or
                    any(sk in opt_id or opt_id in sk for sk in scanned_keys)
                )
                if is_present:
                    verified.append(opt)
                else:
                    logger.debug(f"Filtering out uninstalled VST: {opt.name} ({opt.uri})")
            else:
                verified.append(opt)

        # Fallback safeguard: if all VSTs were filtered out, ensure native instruments are present
        if not verified:
            verified = [opt for opt in raw_sources if opt.category in (InstrumentSourceCategory.NATIVE_SYNTH, InstrumentSourceCategory.DRUM_KIT)]

        # Segregate into third-party VSTs and native plugins (Strict Third-Party Priority)
        third_party = [opt for opt in verified if opt.category in (InstrumentSourceCategory.VST3, InstrumentSourceCategory.VST2)]
        native = [opt for opt in verified if opt not in third_party]

        # In BASS role, ensure SubLab XL is strictly #1
        if norm_role == "BASS":
            sublab_opts = [o for o in third_party if "sublab" in o.id.lower() or "sublab" in o.name.lower()]
            other_third = [o for o in third_party if o not in sublab_opts]
            third_party = sublab_opts + other_third

        verified = third_party + native
        return verified or raw_sources

    @classmethod
    def get_plugin_presets_for_role(
        cls,
        plugin_identifier: str,
        role: str
    ) -> List[SoundSourceOption]:
        """
        Returns custom user racks (.adg) for a parent multi-preset plugin (e.g. Analog Lab V, Omnisphere)
        filtered by role, and appends the clean default VST3 plugin option at the end.
        """
        role_key = role.upper().strip()
        from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
        norm_role = RoleTrackOrchestrator.normalize_role(role_key)
        parent_role = cls.get_parent_acoustic_role(norm_role)
        p_clean = plugin_identifier.lower().strip()

        all_racks = cls.scan_user_custom_racks_for_role(norm_role)
        if not all_racks and parent_role != norm_role:
            all_racks = cls.scan_user_custom_racks_for_role(parent_role)

        matched_racks = []
        is_analog_lab = "analog lab" in p_clean
        is_omnisphere = "omnisphere" in p_clean

        for r in all_racks:
            r_name = r.name.lower()
            r_vendor = r.vendor.lower()
            r_desc = r.description.lower()
            if is_analog_lab and ("analog lab" in r_name or "analog lab" in r_vendor or "analog lab" in r_desc):
                matched_racks.append(r)
            elif is_omnisphere and ("omnisphere" in r_name or "omnisphere" in r_vendor or "omnisphere" in r_desc):
                matched_racks.append(r)

        # Build clean default option
        if is_analog_lab:
            clean_opt = SoundSourceOption(
                id=f"arturia_analog_lab_v_clean_default_{norm_role.lower()}",
                name="Arturia Analog Lab V (Default / Plugin limpio)",
                role=norm_role,
                category=InstrumentSourceCategory.VST3,
                uri="query:Plugins#VST3:Arturia:Analog%20Lab%20V",
                vendor="Arturia",
                description="Carga Analog Lab V en su estado base y el motor preguntará por parámetros y macros para esculpirlo.",
                blueprint={
                    "sculpt_type": "macro",
                    "parameters": {"P1 Brightness": 0.60, "P1 Timbre": 0.55, "P1 Time": 0.45, "P1 Movement": 0.35},
                    "description": "Clean default Analog Lab V."
                }
            )
        elif is_omnisphere:
            clean_opt = SoundSourceOption(
                id=f"spectrasonics_omnisphere_clean_default_{norm_role.lower()}",
                name="Spectrasonics Omnisphere (Default / Plugin limpio)",
                role=norm_role,
                category=InstrumentSourceCategory.VST3,
                uri="query:Plugins#VST3:Spectrasonics:Omnisphere",
                vendor="Spectrasonics",
                description="Carga Omnisphere en su estado base y el motor preguntará por parámetros y macros para esculpirlo.",
                blueprint={
                    "sculpt_type": "semantic",
                    "parameters": {"FILTER_CUTOFF": 0.65, "AMP_ATTACK": 0.05, "AMP_RELEASE": 0.40},
                    "description": "Clean default Omnisphere."
                }
            )
        else:
            clean_opt = SoundSourceOption(
                id=f"{plugin_identifier.replace(' ', '_').lower()}_clean_default_{norm_role.lower()}",
                name=f"{plugin_identifier} (Default / Plugin limpio)",
                role=norm_role,
                category=InstrumentSourceCategory.VST3,
                uri=f"query:Plugins#VST3:{plugin_identifier.replace(' ', '%20')}",
                vendor="ThirdParty",
                description=f"Carga {plugin_identifier} limpio y el motor preguntará por parámetros.",
                blueprint={"sculpt_type": "macro", "parameters": {}, "description": "Clean default plugin."}
            )

        return matched_racks + [clean_opt]

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

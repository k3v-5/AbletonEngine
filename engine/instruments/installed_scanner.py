# engine/instruments/installed_scanner.py
"""
Installed Plugin Scanner & Semantic Role Classifier.
Scans standard Windows VST3 and VST directories, indexes available instruments and effects,
and classifies them into musical roles (KEYS, BASS, LEAD, DRUMS, VOCALS, FX, MASTER)
so the Copilot and AI agent make authentic sound design decisions based on the user's real setup.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class PluginCategory(str, Enum):
    VST3 = "vst3"
    VST2 = "vst2"
    NATIVE = "native"


@dataclass
class ScannedPlugin:
    id: str
    name: str
    vendor: str
    path: str
    category: PluginCategory
    primary_role: str
    supported_roles: List[str]
    description: str
    uri: str
    is_instrument: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "vendor": self.vendor,
            "path": self.path,
            "category": self.category.value,
            "primary_role": self.primary_role,
            "supported_roles": self.supported_roles,
            "description": self.description,
            "uri": self.uri,
            "is_instrument": self.is_instrument,
        }


class InstalledPluginScanner:
    """Scans local disk for installed VST3/VST plugins and classifies them by semantic musical role."""

    DEFAULT_SCAN_PATHS = [
        r"C:\Program Files\Common Files\VST3",
        r"C:\Program Files\Steinberg\VstPlugins",
        r"C:\Program Files\Vstplugins",
        r"C:\Program Files (x86)\Common Files\VST3",
    ]

    # Semantic classification mapping based on plugin names / vendors
    SIGNATURE_MAP = {
        "vital": {
            "vendor": "Vital Audio",
            "primary_role": "BASS",
            "supported_roles": ["BASS", "LEAD", "PLUCK", "VOCALS", "FX"],
            "description": "Spectral warping wavetable synthesizer with modern modulation, glide, and formant modes.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Vital%20Audio:Vital",
        },
        "stage-73": {
            "vendor": "Arturia",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "PIANO", "RHODES"],
            "description": "Authentic physical modeling of the Fender Rhodes Stage 73 electric piano.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Arturia:Stage-73%20V2",
        },
        "wurli": {
            "vendor": "Arturia",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "PIANO"],
            "description": "Physical modeling of the vintage Wurlitzer 200A electric piano.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Arturia:Wurli%20V3",
        },
        "piano v": {
            "vendor": "Arturia",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "PIANO"],
            "description": "Physical modeling grand and upright piano suite.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Arturia:Piano%20V3",
        },
        # Keyboards / Pianos / Rhodes
        "analog lab": {
            "vendor": "Arturia",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "LEAD", "PAD", "BASS"],
            "description": "Legendary vintage keyboards, Rhodes, Wurlitzers, and analog polysynths.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Arturia:Analog%20Lab%20V",
        },
        "omnisphere": {
            "vendor": "Spectrasonics",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "PAD", "LEAD", "TEXTURE", "ACOUSTIC"],
            "description": "Industry powerhouse with massive acoustic/hybrid keys, pads, and cinematic textures.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Spectrasonics:Omnisphere",
        },
        "keyscape": {
            "vendor": "Spectrasonics",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "PIANO", "RHODES"],
            "description": "Collector keyboards with exquisite multisampling of Rhodes, Wurli, and grand pianos.",
            "is_instrument": True,
        },
        "kontakt": {
            "vendor": "Native Instruments",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "SAMPLER", "ORCHESTRAL", "ACOUSTIC", "BASS"],
            "description": "World-standard sampler hosting realistic acoustic instruments, pianos, and libraries.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Native%20Instruments:Kontakt%208",
        },
        "fm8": {
            "vendor": "Native Instruments",
            "primary_role": "KEYS",
            "supported_roles": ["KEYS", "LEAD", "BELLS", "FX"],
            "description": "Dynamic FM synth for crystalline electric pianos, glass bells, and digital leads.",
            "is_instrument": True,
        },
        # Bass & 808 Synthesizers
        "serum": {
            "vendor": "Xfer Records",
            "primary_role": "BASS",
            "supported_roles": ["BASS", "LEAD", "PLUCK", "CHORDS"],
            "description": "Elite wavetable synthesizer for earth-shaking 808s, glide basses, and sharp leads.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Xfer%20Records:Serum%202",
        },
        "massive x": {
            "vendor": "Native Instruments",
            "primary_role": "BASS",
            "supported_roles": ["BASS", "LEAD", "TEXTURE"],
            "description": "Next-gen subtractive wavetable monster with complex modulation and analog punch.",
            "is_instrument": True,
            "live_uri": "query:Plugins#VST3:Native%20Instruments:Massive%20X",
        },
        "massive": {
            "vendor": "Native Instruments",
            "primary_role": "BASS",
            "supported_roles": ["BASS", "LEAD"],
            "description": "Iconic bass and lead synth known for aggressive growls and solid sub tones.",
            "is_instrument": True,
        },
        "trilian": {
            "vendor": "Spectrasonics",
            "primary_role": "BASS",
            "supported_roles": ["BASS", "ACOUSTIC_BASS"],
            "description": "Total bass module featuring acoustic uprights, electric basses, and analog subs.",
            "is_instrument": True,
        },
        "bloom bass": {
            "vendor": "Bloom",
            "primary_role": "BASS",
            "supported_roles": ["BASS", "808"],
            "description": "Specialized sub-bass and bass groove engine with analog saturation.",
            "is_instrument": True,
        },
        # Vocal Engines
        "bloom vocal": {
            "vendor": "Bloom",
            "primary_role": "VOCALS",
            "supported_roles": ["VOCALS", "CHOIR", "HOOKS"],
            "description": "Atmospheric vocal chops, vocal pad beds, and choral synthesis.",
            "is_instrument": True,
        },
        "antares": {
            "vendor": "Antares",
            "primary_role": "VOCALS",
            "supported_roles": ["VOCALS", "PITCH_CORRECTION"],
            "description": "Industry-standard Auto-Tune pitch correction and vocal formatting.",
            "is_instrument": False,
            "live_uri": "query:Plugins#VST3:Antares:Auto-Tune%20Pro",
        },
        # Drums
        "bloom drum": {
            "vendor": "Bloom",
            "primary_role": "DRUMS",
            "supported_roles": ["DRUMS", "PERCUSSION", "BREAKS"],
            "description": "Dynamic drum breaks, groove generators, and modern percussion.",
            "is_instrument": True,
        },
        # Mixing, Dynamics & Space FX
        "fabfilter": {
            "vendor": "FabFilter",
            "primary_role": "FX",
            "supported_roles": ["FX", "EQ", "DYNAMICS", "LIMITING"],
            "description": "Precision surgical mixing suite (Pro-Q 3, Pro-C 2, Pro-L 2).",
            "is_instrument": False,
        },
        "valhalla": {
            "vendor": "Valhalla DSP",
            "primary_role": "FX",
            "supported_roles": ["FX", "REVERB", "DELAY", "SPACE"],
            "description": "World-class algorithmic reverbs and delays (VintageVerb, Delay, Supermassive).",
            "is_instrument": False,
        },
        "shaperbox": {
            "vendor": "Cableguys",
            "primary_role": "FX",
            "supported_roles": ["FX", "SIDECHAIN", "FILTER_SWEEP", "RHYTHM"],
            "description": "Multi-effect envelope shaping for ducking, filtering, and rhythmic stutter.",
            "is_instrument": False,
        },
        "soothe": {
            "vendor": "oeksound",
            "primary_role": "FX",
            "supported_roles": ["FX", "RESONANCE_SUPPRESSION"],
            "description": "Dynamic resonance suppressor that removes harshness without dulling highs.",
            "is_instrument": False,
        },
        "god particle": {
            "vendor": "Cradle",
            "primary_role": "MASTER",
            "supported_roles": ["MASTER", "FX", "GLUE"],
            "description": "Jaycen Joshua's signature master bus saturation, EQ, and dynamics engine.",
            "is_instrument": False,
        },
        "ott": {
            "vendor": "Xfer Records",
            "primary_role": "FX",
            "supported_roles": ["FX", "MULTIBAND_COMPRESSION"],
            "description": "Aggressive upward/downward multiband compressor for hyper-dense presence.",
            "is_instrument": False,
        },
    }

    # High-quality fallback native Ableton Live 12 devices
    NATIVE_FALLBACKS = [
        ScannedPlugin(
            id="native_drift_rhodes",
            name="Ableton Drift (Warm Keys)",
            vendor="Ableton",
            path="Native/Drift",
            category=PluginCategory.NATIVE,
            primary_role="KEYS",
            supported_roles=["KEYS", "BASS", "LEAD"],
            description="Warm analog electric piano with subtle pitch drift and chorus.",
            uri="query:Synths#Drift",
            is_instrument=True,
        ),
        ScannedPlugin(
            id="native_drift_sub",
            name="Ableton Drift (808 Sub)",
            vendor="Ableton",
            path="Native/Drift",
            category=PluginCategory.NATIVE,
            primary_role="BASS",
            supported_roles=["BASS"],
            description="Punchy analog sine/triangle sub-bass with pitch envelope and drive.",
            uri="query:Synths#Drift",
            is_instrument=True,
        ),
        ScannedPlugin(
            id="native_drift_lead",
            name="Ableton Drift (Lead)",
            vendor="Ableton",
            path="Native/Drift",
            category=PluginCategory.NATIVE,
            primary_role="LEAD",
            supported_roles=["LEAD"],
            description="Monophonic expressive lead synth with portamento and resonant filter.",
            uri="query:Synths#Drift",
            is_instrument=True,
        ),
        ScannedPlugin(
            id="native_drum_rack",
            name="Ableton Drum Rack",
            vendor="Ableton",
            path="Native/DrumRack",
            category=PluginCategory.NATIVE,
            primary_role="DRUMS",
            supported_roles=["DRUMS", "PERCUSSION"],
            description="16-pad drum rack supporting individual sample routing and macro controls.",
            uri="query:Drums#Drum%20Rack",
            is_instrument=True,
        ),
    ]

    def __init__(self, scan_paths: Optional[List[str]] = None):
        self.scan_paths = scan_paths or self.DEFAULT_SCAN_PATHS
        self._cache: Dict[str, ScannedPlugin] = {}
        self._scanned = False

    def scan(self, force_rescan: bool = False) -> Dict[str, ScannedPlugin]:
        """Scans the configured plugin directories and builds the index."""
        if self._scanned and not force_rescan and self._cache:
            return self._cache

        self._cache.clear()

        # 1. Add Native Fallbacks
        for native_plug in self.NATIVE_FALLBACKS:
            self._cache[native_plug.id] = native_plug

        # 2. Scan physical directories
        for directory in self.scan_paths:
            if not os.path.exists(directory):
                continue

            try:
                for root, dirs, files in os.walk(directory):
                    for d in dirs:
                        if d.lower().endswith(".vst3"):
                            full_path = os.path.join(root, d)
                            self._process_plugin_file(d, full_path, PluginCategory.VST3)

                    for f in files:
                        lower_f = f.lower()
                        full_path = os.path.join(root, f)
                        if lower_f.endswith(".vst3"):
                            self._process_plugin_file(f, full_path, PluginCategory.VST3)
                        elif lower_f.endswith(".dll") and not lower_f.startswith("api-ms"):
                            self._process_plugin_file(f, full_path, PluginCategory.VST2)
            except Exception:
                pass

        self._scanned = True
        return self._cache

    def _process_plugin_file(self, filename: str, full_path: str, category: PluginCategory):
        clean_name = filename.rsplit(".", 1)[0]
        lower_name = clean_name.lower()

        for sig, meta in self.SIGNATURE_MAP.items():
            if sig in lower_name:
                plug_id = f"{category.value}_{lower_name.replace(' ', '_').replace('.', '_')}"
                if plug_id in self._cache:
                    return

                vendor = meta["vendor"]
                primary_role = meta["primary_role"]
                supported_roles = meta["supported_roles"]
                desc = meta["description"]
                is_inst = meta["is_instrument"]

                uri = meta.get("live_uri") or f"query:Plugins#{category.value.upper()}:{vendor}:{clean_name}"

                plugin = ScannedPlugin(
                    id=plug_id,
                    name=f"{vendor} {clean_name}" if vendor not in clean_name else clean_name,
                    vendor=vendor,
                    path=full_path,
                    category=category,
                    primary_role=primary_role,
                    supported_roles=supported_roles,
                    description=desc,
                    uri=uri,
                    is_instrument=is_inst,
                )
                self._cache[plug_id] = plugin
                return

        if category == PluginCategory.VST3:
            plug_id = f"vst3_generic_{lower_name.replace(' ', '_')}"
            if plug_id not in self._cache:
                self._cache[plug_id] = ScannedPlugin(
                    id=plug_id,
                    name=clean_name,
                    vendor="Unknown",
                    path=full_path,
                    category=category,
                    primary_role="FX",
                    supported_roles=["FX"],
                    description=f"Installed VST3 plugin: {clean_name}",
                    uri=f"query:Plugins#VST3:{clean_name}",
                    is_instrument=False,
                )

    def scan_live_session(self, conn: Any = None) -> Dict[str, ScannedPlugin]:
        """Queries the live connected Ableton instance to discover and register all installed VST3s."""
        self.scan()
        if conn is None:
            return self._cache

        try:
            res = conn.send_command("get_browser_items_at_path", {"path": "plugins/vst3"})
            vendors = res.get("result", {}).get("items", []) if isinstance(res, dict) else []
            for v in vendors:
                v_name = v.get("name")
                if v.get("is_folder") and v_name:
                    v_res = conn.send_command("get_browser_items_at_path", {"path": f"plugins/vst3/{v_name}"})
                    items = v_res.get("result", {}).get("items", []) if isinstance(v_res, dict) else []
                    for it in items:
                        p_name = it.get("name")
                        p_uri = it.get("uri")
                        if not p_name or not p_uri:
                            continue
                        low_name = p_name.lower()
                        role = "FX"
                        is_inst = False
                        if any(w in low_name for w in ["vital", "serum", "bass", "sub", "cyclop"]):
                            role = "BASS"
                            is_inst = True
                        elif any(w in low_name for w in ["lab", "stage", "piano", "wurli", "clav", "organ", "b-3", "rhodes", "kontakt", "omnisphere"]):
                            role = "KEYS"
                            is_inst = True
                        elif any(w in low_name for w in ["lead", "synth", "synplant", "zenology", "pigments", "massive", "fm8", "modular"]):
                            role = "LEAD"
                            is_inst = True
                        elif any(w in low_name for w in ["vocal", "auto-tune", "tune", "vox"]):
                            role = "VOCALS"
                            is_inst = True
                        elif any(w in low_name for w in ["god particle", "limiter", "pro-l"]):
                            role = "MASTER"
                            is_inst = False

                        plug_id = f"live_vst3_{v_name.lower()}_{low_name.replace(' ', '_')}"
                        self._cache[plug_id] = ScannedPlugin(
                            id=plug_id,
                            name=f"{v_name} {p_name}",
                            vendor=v_name,
                            path=f"Live/VST3/{v_name}/{p_name}",
                            category=PluginCategory.VST3,
                            primary_role=role,
                            supported_roles=[role, "FX"],
                            description=f"Host-installed {v_name} {p_name} in Ableton Live.",
                            uri=p_uri,
                            is_instrument=is_inst
                        )
        except Exception:
            pass
        return self._cache

    def get_plugins_for_role(self, role: str) -> List[ScannedPlugin]:
        """Returns all plugins suitable for a specific musical role."""
        self.scan()
        role_upper = role.upper()
        matches = []
        for plug in self._cache.values():
            if role_upper == plug.primary_role or role_upper in plug.supported_roles:
                matches.append(plug)

        matches.sort(key=lambda p: (0 if p.category == PluginCategory.VST3 else 1, p.name))
        return matches

    def get_catalog_summary(self) -> Dict[str, Any]:
        """Returns structured overview of all discovered plugins grouped by role."""
        self.scan()
        roles = ["KEYS", "BASS", "LEAD", "DRUMS", "VOCALS", "FX", "MASTER"]
        catalog = {}
        for r in roles:
            catalog[r] = [p.to_dict() for p in self.get_plugins_for_role(r)]

        total_vst3 = sum(1 for p in self._cache.values() if p.category == PluginCategory.VST3)
        total_vst2 = sum(1 for p in self._cache.values() if p.category == PluginCategory.VST2)
        total_native = sum(1 for p in self._cache.values() if p.category == PluginCategory.NATIVE)

        return {
            "status": "SUCCESS",
            "total_discovered": len(self._cache),
            "vst3_count": total_vst3,
            "vst2_count": total_vst2,
            "native_count": total_native,
            "roles": catalog,
        }

    def recommend_for_role(self, role: str, style: str = "neo_soul_trap") -> ScannedPlugin:
        """Returns the optimal instrument recommendation for a given role and style."""
        candidates = self.get_plugins_for_role(role)
        role_upper = role.upper()

        if role_upper == "KEYS":
            for c in candidates:
                if "stage-73" in c.name.lower() or "analog lab" in c.name.lower() or "keyscape" in c.name.lower() or "kontakt" in c.name.lower():
                    return c
        elif role_upper == "BASS":
            for c in candidates:
                if "vital" in c.name.lower() or "serum" in c.name.lower() or "bloom bass" in c.name.lower():
                    return c
        elif role_upper == "LEAD":
            for c in candidates:
                if "analog lab" in c.name.lower() or "vital" in c.name.lower() or "serum" in c.name.lower():
                    return c
        elif role_upper == "VOCALS":
            for c in candidates:
                if "vital" in c.name.lower() or "bloom vocal" in c.name.lower() or "auto-tune" in c.name.lower():
                    return c
        elif role_upper == "DRUMS":
            for c in candidates:
                if "drum_rack" in c.id or "808" in c.name.lower():
                    return c

        return candidates[0] if candidates else self.NATIVE_FALLBACKS[0]

    @classmethod
    def verify_and_fallback(
        cls,
        conn: Any,
        track_index: int,
        role: str,
        expected_plugin_name: str,
        known_unhealthy: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Verifies that a loaded instrument is active and healthy in Live.
        If the plugin failed to open, threw an error, or is listed in known_unhealthy,
        the motor automatically fails over to the next best working sound source.
        """
        unhealthy_set = set(k.lower() for k in (known_unhealthy or ["stage-73", "stage-73 v2"]))
        
        # Query Live track devices
        devices = []
        if conn and hasattr(conn, "send_command"):
            t_info = conn.send_command("get_track_info", {"track_index": track_index})
            devices = t_info.get("result", {}).get("devices", [])

        is_failed = False
        failure_reason = ""

        # Check if expected plugin is in known unhealthy list
        if any(bad in expected_plugin_name.lower() for bad in unhealthy_set):
            is_failed = True
            failure_reason = f"Plugin '{expected_plugin_name}' is known to require host license activation or failed to open."

        # Check if device is missing or uninstantiated
        if not devices:
            is_failed = True
            failure_reason = f"No devices present on track {track_index}."

        if not is_failed:
            return {
                "status": "HEALTHY",
                "track_index": track_index,
                "plugin_name": expected_plugin_name,
                "verified": True
            }

        # Failure detected: Perform autonomous failover
        scanner = cls()
        candidates = scanner.get_plugins_for_role(role)
        fallback = None
        for c in candidates:
            if not any(bad in c.name.lower() for bad in unhealthy_set) and c.uri:
                fallback = c
                break

        if not fallback:
            fallback = ScannedPlugin(
                id="native_drift",
                name="Drift (Native)",
                vendor="Ableton",
                path="",
                category=PluginCategory.NATIVE,
                primary_role=role.upper(),
                supported_roles=[role.upper()],
                description="Built-in Ableton synthesizer (100% reliable)",
                uri="query:synths#Drift",
                is_instrument=True
            )

        load_res = None
        if conn and hasattr(conn, "send_command") and fallback.uri:
            load_res = conn.send_command("load_browser_item", {
                "track_index": track_index,
                "item_uri": fallback.uri
            })

        return {
            "status": "FAILOVER_EXECUTED",
            "track_index": track_index,
            "failed_plugin": expected_plugin_name,
            "failure_reason": failure_reason,
            "fallback_selected": fallback.name,
            "fallback_uri": fallback.uri,
            "load_result": load_res
        }

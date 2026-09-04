"""
Master Sound Design & Production Engine:
High-level production coordinator uniting Capability Discovery, Sound Profiles,
Chains, Drum Rack Engine, Semantic Macros, Snapshots, and Linter.
"""
from typing import Dict, List, Any, Optional, Union
from .profiles.models import SoundProfile
from .profiles.profiles import get_sound_profile, SOUND_PROFILES
from .intent import SoundIntent, SidechainIntent
from .context import MixContext, AdaptiveAdvisor, FrequencyRoleMap
from .chains.builder import ChainBuilder
from .capabilities.registry import CapabilityRegistry
from .capabilities.discovery import CapabilityDiscovery
from .presets.resolver import PresetResolver
from .drum_rack.engine import DrumRackEngine
from .drum_rack.verifier import DrumRackVerifier
from .macros.system import MacroSystem
from .snapshots.snapshots import SoundSnapshotManager
from .linter import SoundLinter

class SoundEngine:
    """Master Production Intelligence Sound Engine."""

    def __init__(self, parent_engine=None):
        self.engine = parent_engine
        self.adapter = parent_engine.adapter if parent_engine else None
        self.capabilities = CapabilityDiscovery.discover_capabilities(self.adapter)
        self.chain_builder = ChainBuilder(self.adapter)
        self.drum_rack_engine = DrumRackEngine(self.adapter)
        self.macro_system = MacroSystem(self.adapter)
        self.snapshot_manager = SoundSnapshotManager()
        self.advisor = AdaptiveAdvisor()

    def set_adapter(self, adapter):
        self.adapter = adapter
        self.capabilities = CapabilityDiscovery.discover_capabilities(self.adapter)
        self.chain_builder.adapter = adapter
        self.drum_rack_engine.adapter = adapter
        self.macro_system.adapter = adapter

    def build_sound_role(
        self,
        track_index_or_id: Any,
        role: str,
        character: str = "dark_club",
        intent: Optional[SoundIntent] = None,
        mode: str = "update",  # create, reuse, update, replace
        preview: bool = False
    ) -> Dict[str, Any]:
        """
        Builds a complete, production-grade sound chain for a musical role.
        Resolves instrument -> loads preset -> builds effect chain -> configures macros -> verifies.
        """
        track_idx = self._resolve_track_index(track_index_or_id, role)
        clean_role = role.upper().strip()
        
        # 1. Derive SoundIntent & SoundProfile
        sound_intent = intent or SoundIntent(role=clean_role, character=character)
        profile = get_sound_profile(clean_role, character)

        # 2. Preset & Instrument Resolution
        preset_info = PresetResolver.resolve_preset(
            role=clean_role,
            character=character,
            genre=profile.genre,
            brightness=sound_intent.brightness
        )

        # 3. Dry-run preview
        if preview:
            chain_preview = self.chain_builder.build_chain_for_track(track_idx, clean_role, preview=True)
            return {
                "status": "preview",
                "track_index": track_idx,
                "role": clean_role,
                "profile": profile.to_dict(),
                "selected_instrument": preset_info["instrument"],
                "selected_preset": preset_info["preset"],
                "confidence": preset_info["confidence"],
                "chain": chain_preview.get("devices_to_create", []),
                "macros": {
                    "weight": sound_intent.weight,
                    "brightness": sound_intent.brightness,
                    "space": sound_intent.space,
                    "width": sound_intent.width,
                    "punch": sound_intent.punch,
                    "warmth": sound_intent.warmth
                }
            }

        # 4. Snapshot before mutation
        snapshot = self.snapshot_manager.capture(track_idx, self.adapter)

        try:
            # 5. Build Effect Chain
            chain_res = self.chain_builder.build_chain_for_track(track_idx, clean_role, preview=False)

            # 6. Apply Macros (brightness, space, weight, width, punch, warmth)
            self.macro_system.set_macro(track_idx, "brightness", sound_intent.brightness)
            self.macro_system.set_macro(track_idx, "space", sound_intent.space)
            self.macro_system.set_macro(track_idx, "weight", sound_intent.weight)
            self.macro_system.set_macro(track_idx, "width", sound_intent.width)
            self.macro_system.set_macro(track_idx, "punch", sound_intent.punch)
            self.macro_system.set_macro(track_idx, "warmth", sound_intent.warmth)

            # 7. Verify Track Devices
            t_info = self._get_track_info(track_idx)
            lint_res = SoundLinter.lint_track(t_info, role=clean_role)

            return {
                "status": "success",
                "track_index": track_idx,
                "role": clean_role,
                "character": character,
                "instrument": preset_info["instrument"],
                "preset": preset_info["preset"],
                "chain": chain_res.get("devices", []),
                "verification": lint_res,
                "snapshot_id": snapshot.snapshot_id
            }
        except Exception as e:
            self.snapshot_manager.rollback(snapshot.snapshot_id, self.adapter)
            return {
                "status": "partial_failure",
                "track_index": track_idx,
                "role": clean_role,
                "error": str(e),
                "rolled_back": True
            }

    def build_drum_rack(
        self,
        track_index_or_id: Any = None,
        style: str = "melodic_techno",
        preview: bool = False
    ) -> Dict[str, Any]:
        """Builds a complete, verified Drum Rack with all required samples."""
        track_idx = self._resolve_track_index(track_index_or_id, "DRUMS")
        return self.drum_rack_engine.build_drum_rack(
            track_index=track_idx,
            style=style,
            preview=preview
        )

    def create_sound(
        self,
        track_index_or_id: Any,
        role: str,
        character: str = "dark_club",
        brightness: float = 0.5,
        warmth: float = 0.5,
        punch: float = 0.5,
        space: float = 0.2,
        preview: bool = False
    ) -> Dict[str, Any]:
        """Creates an instrument/sound chain based on musical intent parameters."""
        intent = SoundIntent(
            role=role.upper().strip(),
            character=character,
            brightness=brightness,
            warmth=warmth,
            punch=punch,
            space=space
        )
        return self.build_sound_role(
            track_index_or_id=track_index_or_id,
            role=role,
            character=character,
            intent=intent,
            mode="create",
            preview=preview
        )

    def update_sound(
        self,
        track_index_or_id: Any,
        role: str,
        macro_values: Optional[Dict[str, float]] = None,
        character: Optional[str] = None
    ) -> Dict[str, Any]:
        """Updates macro parameters or character on an existing track."""
        track_idx = self._resolve_track_index(track_index_or_id, role)
        results = {}
        if macro_values:
            for m_name, m_val in macro_values.items():
                results[m_name] = self.macro_system.set_macro(track_idx, m_name, m_val)
        if character:
            profile = get_sound_profile(role, character)
            for m_name, m_val in profile.default_macros.items():
                self.macro_system.set_macro(track_idx, m_name, m_val)
            results["character_applied"] = character
        return {
            "status": "updated",
            "track_index": track_idx,
            "role": role,
            "updates": results
        }

    def inspect_track(self, track_index_or_id: Any) -> Dict[str, Any]:
        """Inspects sound chain, devices, macro parameters, and frequency profile for a track."""
        track_idx = self._resolve_track_index(track_index_or_id)
        t_info = self._get_track_info(track_idx)
        role = self._infer_role(track_idx, t_info)
        freq_info = FrequencyRoleMap.ROLE_FREQUENCY_PROFILES.get(role, {})
        return {
            "track_index": track_idx,
            "track_name": t_info.get("name", f"Track {track_idx}"),
            "role": role,
            "devices": t_info.get("devices", []),
            "macros": self.macro_system.track_macro_states.get(track_idx, {}),
            "frequency_profile": freq_info,
            "volume": t_info.get("volume", 0.85),
            "panning": t_info.get("panning", 0.0)
        }

    def verify_track(self, track_index_or_id: Any) -> Dict[str, Any]:
        """Verifies physical sound device state (checks for empty chains, missing plugins)."""
        track_idx = self._resolve_track_index(track_index_or_id)
        t_info = self._get_track_info(track_idx)
        role = self._infer_role(track_idx, t_info)
        lint_res = SoundLinter.lint_track(t_info, role=role)
        
        # Also check Drum Rack if present
        is_drum_rack = any("drum" in d.get("name", "").lower() or d.get("class_name") == "DrumGroupDevice" for d in t_info.get("devices", []))
        drum_verification = None
        if is_drum_rack:
            drum_verification = DrumRackVerifier.verify_drum_rack(self.adapter, track_idx)

        return {
            "track_index": track_idx,
            "role": role,
            "verified": lint_res.get("valid", True) and (drum_verification.get("verified", True) if drum_verification else True),
            "lint": lint_res,
            "drum_rack_verification": drum_verification
        }

    def compare_tracks(self, track_index_or_id_a: Any, track_index_or_id_b: Any) -> Dict[str, Any]:
        """Compares two tracks for frequency clash, stereo balance, and dynamic headroom."""
        idx_a = self._resolve_track_index(track_index_or_id_a)
        idx_b = self._resolve_track_index(track_index_or_id_b)
        info_a = self._get_track_info(idx_a)
        info_b = self._get_track_info(idx_b)
        role_a = self._infer_role(idx_a, info_a)
        role_b = self._infer_role(idx_b, info_b)

        # Detect sub conflict
        is_low_a = role_a in ["SUB_BASS", "SUB", "BASS", "KICK"]
        is_low_b = role_b in ["SUB_BASS", "SUB", "BASS", "KICK"]
        low_end_clash = is_low_a and is_low_b

        # Stereo width comparison
        pan_a = info_a.get("panning", 0.0)
        pan_b = info_b.get("panning", 0.0)

        return {
            "track_a": {"index": idx_a, "name": info_a.get("name"), "role": role_a, "pan": pan_a},
            "track_b": {"index": idx_b, "name": info_b.get("name"), "role": role_b, "pan": pan_b},
            "low_end_clash_risk": low_end_clash,
            "recommended_action": "Apply dynamic sidechain compressor or filter dip if overlapping." if low_end_clash else "Frequency distribution is balanced."
        }

    def apply_profile(self, track_index_or_id: Any, role: str, profile_name: str = "dark_club") -> Dict[str, Any]:
        """Applies a curated sound profile directly to a track."""
        track_idx = self._resolve_track_index(track_index_or_id, role)
        profile = get_sound_profile(role, profile_name)
        for m_name, m_val in profile.default_macros.items():
            self.macro_system.set_macro(track_idx, m_name, m_val)
        return {
            "status": "profile_applied",
            "track_index": track_idx,
            "role": role,
            "profile": profile.to_dict()
        }

    def set_macro(self, track_index_or_id: Any, macro_name: str, value: float) -> Dict[str, Any]:
        track_idx = self._resolve_track_index(track_index_or_id)
        return self.macro_system.set_macro(track_idx, macro_name, value)

    def get_macro(self, track_index_or_id: Any, macro_name: str) -> float:
        track_idx = self._resolve_track_index(track_index_or_id)
        return self.macro_system.get_macro(track_idx, macro_name)

    def get_all_macros(self, track_index_or_id: Any) -> Dict[str, float]:
        track_idx = self._resolve_track_index(track_index_or_id)
        return self.macro_system.track_macro_states.get(track_idx, {})

    def lint_session(self) -> Dict[str, Any]:
        """Audits all tracks in the session for sound design issues."""
        all_issues = []
        track_count = 0
        if self.adapter:
            try:
                s_info = self.adapter.get_session_info() if hasattr(self.adapter, "get_session_info") else {}
                track_count = int(s_info.get("track_count", 0))
            except Exception:
                pass

        if track_count == 0 and self.engine and hasattr(self.engine, "graph"):
            track_count = len(self.engine.graph.tracks)

        for i in range(max(track_count, 1)):
            t_info = self._get_track_info(i)
            role = self._infer_role(i, t_info)
            t_lint = SoundLinter.lint_track(t_info, role=role)
            all_issues.extend(t_lint.get("issues", []))

        total_score = max(0.0, 100.0 - sum(30.0 if x["severity"] == "ERROR" else 10.0 for x in all_issues))
        return {
            "session_valid": not any(x["severity"] == "ERROR" for x in all_issues),
            "sound_health_score": total_score,
            "total_issues": len(all_issues),
            "issues": all_issues
        }

    def _infer_role(self, track_index: int, track_info: Dict[str, Any]) -> str:
        name = track_info.get("name", "").lower()
        if "drum" in name or "perc" in name or "kick" in name:
            return "DRUMS"
        if "sub" in name:
            return "SUB_BASS"
        if "bass" in name:
            return "BASS"
        if "lead" in name:
            return "LEAD"
        if "pad" in name or "string" in name:
            return "PAD"
        if "pluck" in name or "arp" in name:
            return "PLUCK"
        return "LEAD"

    def _resolve_track_index(self, track_index_or_id: Any, role: Optional[str] = None) -> int:
        if isinstance(track_index_or_id, int):
            return track_index_or_id
        if isinstance(track_index_or_id, str) and track_index_or_id.isdigit():
            return int(track_index_or_id)
        
        # Query engine graph or resolver
        if self.engine and hasattr(self.engine, "graph"):
            if role:
                for t in self.engine.graph.tracks.values():
                    if getattr(t, "type", "").lower() == "midi" and (role.lower() in t.name.lower() or t.metadata.role == role.upper()):
                        return getattr(t, "ableton_index", getattr(t, "index", 0))
            for t in self.engine.graph.tracks.values():
                if getattr(t, "type", "").lower() == "midi":
                    return getattr(t, "ableton_index", getattr(t, "index", 0))

        return 2  # default to Track 2 (Drums/Instrument)

    def _get_track_info(self, track_index: int) -> Dict[str, Any]:
        if self.adapter:
            try:
                if hasattr(self.adapter, "get_track_info"):
                    return self.adapter.get_track_info(track_index)
                elif hasattr(self.adapter, "send_command"):
                    return self.adapter.send_command("get_track_info", {"track_index": track_index})
            except Exception:
                pass
        return {"index": track_index, "name": f"Track {track_index}", "is_midi_track": True, "devices": []}

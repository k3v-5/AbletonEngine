# engine/instruments/plugins/normalizer.py
import re
import difflib
from typing import Dict, List, Any, Optional, Union
from .models import PluginProfile, PluginSemanticRole, NormalizedParameterResult
from .registry import PluginRegistry

class VSTParameterNormalizer:
    """
    Intelligent parameter normalizer and semantic mapper for VST3 plugins and native devices.
    Bridges musical intent (e.g. CUTOFF, DRIVE, MACRO_1) to real device parameter names and normalized [0.0, 1.0] ranges.
    """

    CANONICAL_FALLBACK_KEYWORDS = {
        PluginSemanticRole.CUTOFF: ["cutoff", "cut", "filter freq", "filter frequency", "filter 1 freq", "freq", "brightness"],
        PluginSemanticRole.RESONANCE: ["resonance", "res", "filter res", "filter 1 res", "q", "emphasis"],
        PluginSemanticRole.DRIVE: ["drive", "distortion", "dist", "saturation", "overdrive", "warmth", "gain"],
        PluginSemanticRole.DRY_WET: ["dry/wet", "dry wet", "mix", "blend", "amount", "wet"],
        PluginSemanticRole.VOLUME: ["volume", "vol", "master vol", "master volume", "gain", "level", "out"],
        PluginSemanticRole.PANNING: ["pan", "panning", "panorama", "balance"],
        PluginSemanticRole.WIDTH: ["width", "stereo width", "spread", "stereo"],
        PluginSemanticRole.FATNESS: ["fatness", "fat", "body", "punch", "beef"],
        PluginSemanticRole.COLOR: ["color", "colour", "tone", "character", "warmth"],
        PluginSemanticRole.LIMITER_CEILING: ["limiter ceiling", "ceiling", "output ceiling", "out ceil"],
        PluginSemanticRole.THRESHOLD: ["threshold", "thresh"],
        PluginSemanticRole.ATTACK: ["attack", "att", "env attack", "amp attack", "env 1 attack"],
        PluginSemanticRole.DECAY: ["decay", "dec", "env decay", "amp decay", "env 1 decay"],
        PluginSemanticRole.SUSTAIN: ["sustain", "sus", "env sustain", "amp sustain", "env 1 sustain"],
        PluginSemanticRole.RELEASE: ["release", "rel", "env release", "amp release", "env 1 release"],
        PluginSemanticRole.RATE: ["rate", "speed", "lfo rate", "freq rate"],
        PluginSemanticRole.DEPTH: ["depth", "amount", "mod depth"],
        PluginSemanticRole.MORPH: ["morph", "character morph", "refraction"],
        PluginSemanticRole.GLIDE: ["glide", "portamento", "glide time"],
        PluginSemanticRole.MACRO_1: ["macro 1", "macro_1", "m1"],
        PluginSemanticRole.MACRO_2: ["macro 2", "macro_2", "m2"],
        PluginSemanticRole.MACRO_3: ["macro 3", "macro_3", "m3"],
        PluginSemanticRole.MACRO_4: ["macro 4", "macro_4", "m4"],
        PluginSemanticRole.MACRO_5: ["macro 5", "macro_5", "m5"],
        PluginSemanticRole.MACRO_6: ["macro 6", "macro_6", "m6"],
        PluginSemanticRole.MACRO_7: ["macro 7", "macro_7", "m7"],
        PluginSemanticRole.MACRO_8: ["macro 8", "macro_8", "m8"],
        PluginSemanticRole.DYNAMICS: ["dynamics", "modwheel", "cc1"],
        PluginSemanticRole.EXPRESSION: ["expression", "cc11"],
    }

    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or PluginRegistry()

    def resolve_parameter(
        self,
        device_name: str,
        device_parameters: List[Dict[str, Any]],
        role: Union[PluginSemanticRole, str]
    ) -> NormalizedParameterResult:
        """
        Resolves a semantic role to a real device parameter from the given device parameters list.
        """
        if not device_parameters:
            return NormalizedParameterResult(
                found=False,
                error="Device parameters list is empty"
            )

        sem_role = self._parse_role(role)
        profile = self.registry.get_profile(device_name)

        # 1. Profile-guided resolution (Exact mapping)
        if profile and sem_role:
            target_name = profile.parameter_mappings.get(sem_role)
            if target_name:
                param = self._find_param_by_name(device_parameters, target_name)
                if param:
                    return self._build_result(param, sem_role, confidence=1.0, source="profile_exact")

            # 2. Profile semantic aliases
            aliases = profile.semantic_aliases.get(sem_role, [])
            for alias in aliases:
                param = self._find_param_by_name(device_parameters, alias)
                if param:
                    return self._build_result(param, sem_role, confidence=0.9, source="profile_alias", matched_alias=alias)

        # 3. Canonical fallback keywords for the semantic role
        keywords = self.CANONICAL_FALLBACK_KEYWORDS.get(sem_role, [])
        role_str = sem_role.value if sem_role else str(role).lower()
        if not keywords:
            keywords = [role_str]

        # First pass: clean substring matching against parameters
        for kw in keywords:
            kw_clean = self._clean_token(kw)
            for p in device_parameters:
                p_clean = self._clean_token(p.get("name", ""))
                if kw_clean == p_clean:
                    return self._build_result(p, sem_role, confidence=0.85, source="canonical_exact", matched_alias=kw)
                if kw_clean in p_clean or p_clean in kw_clean:
                    return self._build_result(p, sem_role, confidence=0.75, source="canonical_substring", matched_alias=kw)

        # Second pass: difflib fuzzy matching
        param_names = [p.get("name", "") for p in device_parameters]
        best_match = None
        best_score = 0.0
        best_kw = None

        for kw in keywords:
            for p_name in param_names:
                score = difflib.SequenceMatcher(None, self._clean_token(kw), self._clean_token(p_name)).ratio()
                if score > best_score and score >= 0.55:
                    best_score = score
                    best_match = p_name
                    best_kw = kw

        if best_match:
            param = self._find_param_by_name(device_parameters, best_match)
            if param:
                return self._build_result(param, sem_role, confidence=best_score, source="fuzzy_fallback", matched_alias=best_kw)

        return NormalizedParameterResult(
            found=False,
            role=sem_role,
            error=f"Semantic role '{role}' could not be resolved for device '{device_name}'"
        )

    def normalize_value(self, raw_value: float, min_val: float, max_val: float) -> float:
        """Normalizes a raw parameter value to [0.0, 1.0] range"""
        if max_val <= min_val:
            return 0.0
        clamped_raw = max(min_val, min(max_val, float(raw_value)))
        return (clamped_raw - min_val) / (max_val - min_val)

    def denormalize_value(self, normalized_value: float, min_val: float, max_val: float) -> float:
        """Denormalizes a [0.0, 1.0] value into the device's native [min_val, max_val] range"""
        if not (0.0 <= normalized_value <= 1.0):
            raise ValueError(f"Normalized value must be in [0.0, 1.0], got {normalized_value}")
        return min_val + (normalized_value * (max_val - min_val))

    def _parse_role(self, role: Union[PluginSemanticRole, str]) -> Optional[PluginSemanticRole]:
        if isinstance(role, PluginSemanticRole):
            return role
        role_str = str(role).lower().strip().replace(" ", "_").replace("-", "_")
        try:
            return PluginSemanticRole(role_str)
        except ValueError:
            for r in PluginSemanticRole:
                if r.value == role_str or r.name.lower() == role_str:
                    return r
            return None

    def _find_param_by_name(self, parameters: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
        target = self._clean_token(name)
        # Exact match
        for p in parameters:
            if self._clean_token(p.get("name", "")) == target:
                return p
        # Substring match
        for p in parameters:
            p_clean = self._clean_token(p.get("name", ""))
            if target in p_clean or p_clean in target:
                return p
        return None

    @staticmethod
    def _clean_token(s: str) -> str:
        return re.sub(r'[^a-zA-Z0-9]', '', str(s)).lower()

    def _build_result(
        self,
        param: Dict[str, Any],
        role: Optional[PluginSemanticRole],
        confidence: float,
        source: str,
        matched_alias: Optional[str] = None
    ) -> NormalizedParameterResult:
        min_v = float(param.get("min", 0.0))
        max_v = float(param.get("max", 1.0))
        raw_v = float(param.get("value", 0.0))
        norm_v = self.normalize_value(raw_v, min_v, max_v)
        return NormalizedParameterResult(
            found=True,
            parameter_name=param.get("name", ""),
            parameter_index=param.get("index", -1),
            raw_value=raw_v,
            normalized_value=norm_v,
            min_value=min_v,
            max_value=max_v,
            role=role,
            confidence=confidence,
            source=source,
            matched_alias=matched_alias
        )

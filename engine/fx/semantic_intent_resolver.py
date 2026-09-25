"""
Semantic Intent Resolver
========================
Resolutor semántico inequívoco de intenciones acústicas para AbletonEngine.
Traduce texto libre en español o inglés, JSON estructurado o directivas estéticas
a arquetipos calibrados de UltraAcousticCatalog y parámetros físicos nativos.

Arquitectura de 3 capas:
1. Capa Estructurada (JSON y directivas explícitas).
2. Capa Semántica Difusa (Thesaurus multilingüe acústico).
3. Fallback Determinista Garantizado (Nunca falla por incomprensión).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import re
import json

from engine.fx.ultra_acoustic_catalog import (
    AcousticArchetype,
    UltraAcousticCatalog,
    AcousticProfileSpec,
    hz_to_eq8_norm,
    db_to_eq8_norm
)

@dataclass
class ResolvedAcousticIntent:
    role: str
    archetype: AcousticArchetype
    confidence: float
    explanation: str
    native_chain: List[Dict[str, Any]]
    custom_parameters: Dict[str, float] = field(default_factory=dict)
    bypass_requested: bool = False
    is_fallback: bool = False

class SemanticIntentResolver:
    """Motor de resolución semántica acústica de 3 capas."""

    # Thesaurus Semántico Multilingüe (Español / Inglés)
    THESAURUS: Dict[AcousticArchetype, List[str]] = {
        AcousticArchetype.PUNCHY: [
            "punchy", "punch", "pegada", "golpe", "snap", "impacto", "ataque",
            "thump", "transiente", "percusivo", "clic", "batidor", "mordida frontal",
            "chug", "tight snap"
        ],
        AcousticArchetype.OSCURO: [
            "oscuro", "dark", "apagado", "opaco", "filtro bajo", "sin brillo",
            "muffled", "sombre", "warm dark", "corte agudos", "roll-off", "mate",
            "nocturno", "subterraneo"
        ],
        AcousticArchetype.BRILLANTE: [
            "brillante", "bright", "aire", "crisp", "agudo", "cristalino",
            "shimmer", "presencia", "open", "claridad", "definicion alta", "seda"
        ],
        AcousticArchetype.WARM: [
            "warm", "calido", "cálido", "calor", "analogico", "analógico", "cinta",
            "tubo", "valvula", "válvula", "tape warmth", "redondo", "miel", "acogedor"
        ],
        AcousticArchetype.AGGRESSIVE: [
            "agresivo", "aggressive", "distorsion", "distorsionado", "drive", "saturado",
            "dirty", "filoso", "mordiente", "grunge", "duro", "heavy", "crunch",
            "desgarrador", "crudo"
        ],
        AcousticArchetype.TIGHT: [
            "tight", "apretado", "seco", "corto", "controlado", "dry", "sin cola",
            "preciso", "firme", "sin rebote", "decay corto"
        ],
        AcousticArchetype.AIRY: [
            "airy", "etereo", "etéreo", "espacioso", "nube", "abierto", "flotante",
            "reverb amplia", "atmosferico", "atmosférico", "dreamy", "celestial",
            "halo", "inmersivo"
        ],
        AcousticArchetype.WIDE: [
            "wide", "amplio", "ancho", "espacioso", "estereo", "estéreo", "stereo width",
            "envolvente", "abierto a los lados", "alas estereo", "sides"
        ],
        AcousticArchetype.LOFI: [
            "lofi", "lo-fi", "vintage", "retro", "vinilo", "dusty", "organico",
            "orgánico", "ruido", "nostalgico", "nostálgico"
        ],
        AcousticArchetype.DEEP: [
            "deep", "profundo", "subgrave", "pesado", "retumbante", "sub",
            "infragrave", "fondo", "vibrante", "40hz", "50hz"
        ],
        AcousticArchetype.BALANCED: [
            "balanced", "balanceado", "estandar", "estándar", "equilibrado",
            "comercial", "neutro", "normal", "limpio", "radio ready"
        ],
    }

    COMPLACENT_INPUTS = {
        "", "ok", "vale", "bien", "adelante", "continuar", "siguiente", "next",
        "perfecto", "dale", "si", "yes", "default", "por defecto", "standard",
        "estandar", "de acuerdo", "proceder", "{}", "[]", "none", "null"
    }

    @classmethod
    def resolve_intent(
        cls,
        user_input: Any,
        role: str,
        current_genre: Optional[str] = None
    ) -> ResolvedAcousticIntent:
        """
        Punto de entrada principal. Traduce cualquier entrada a ResolvedAcousticIntent.
        Garantiza resolución determinista (nunca lanza excepción).
        """
        r_clean = str(role or "KEYS").strip().upper()
        raw_text = str(user_input or "").strip()
        normalized = raw_text.lower()

        # 1. Comprobación de bypass explícito
        if "bypass" in normalized or "omitir" in normalized or "sin efecto" in normalized:
            spec = UltraAcousticCatalog.get_role_archetype_spec(r_clean, AcousticArchetype.BALANCED)
            return ResolvedAcousticIntent(
                role=r_clean,
                archetype=AcousticArchetype.BALANCED,
                confidence=1.0,
                explanation=f"Bypass explícito solicitado para el rol {r_clean}.",
                native_chain=[],
                bypass_requested=True
            )

        # 2. CAPA 1: Estructurada (JSON o clave-valor directa)
        structured_match = cls._parse_structured_input(user_input)
        if structured_match:
            arch, custom_params = structured_match
            chain = UltraAcousticCatalog.build_native_insert_chain(r_clean, arch.value)
            cls._apply_custom_params_to_chain(chain, custom_params)
            return ResolvedAcousticIntent(
                role=r_clean,
                archetype=arch,
                confidence=0.95,
                explanation=f"Resuelto por directiva estructurada: Arquetipo {arch.value} con {len(custom_params)} ajustes.",
                native_chain=chain,
                custom_parameters=custom_params
            )

        # 3. CAPA 2: Semántica Difusa (Thesaurus y scoring)
        fuzzy_match = cls._match_fuzzy_thesaurus(normalized)
        if fuzzy_match:
            arch, score, matched_keyword = fuzzy_match
            # Extraer posibles ajustes numéricos explícitos (ej: "corte en 120 hz", "gain +3")
            custom_params = cls._extract_numeric_tweaks(normalized)
            chain = UltraAcousticCatalog.build_native_insert_chain(r_clean, arch.value)
            cls._apply_custom_params_to_chain(chain, custom_params)
            return ResolvedAcousticIntent(
                role=r_clean,
                archetype=arch,
                confidence=score,
                explanation=f"Resuelto por afinidad semántica con '{matched_keyword}' -> Arquetipo {arch.value}.",
                native_chain=chain,
                custom_parameters=custom_params
            )

        # 4. CAPA 3: Fallback Garantizado (Arquetipo calibrado del rol)
        default_arch = UltraAcousticCatalog.ROLE_DEFAULT_ARCHETYPE.get(r_clean, AcousticArchetype.BALANCED)
        chain = UltraAcousticCatalog.build_native_insert_chain(r_clean, default_arch.value)

        is_complacent = normalized in cls.COMPLACENT_INPUTS
        expl = (
            f"Entrada vacía o complaciente detectada. Inyectado arquetipo calibrado de estándar comercial: {default_arch.value} para {r_clean}."
            if is_complacent else
            f"Sin coincidencia semántica explícita. Asignado arquetipo predeterminado calibrado: {default_arch.value} para {r_clean}."
        )

        return ResolvedAcousticIntent(
            role=r_clean,
            archetype=default_arch,
            confidence=0.80 if is_complacent else 0.70,
            explanation=expl,
            native_chain=chain,
            is_fallback=True
        )

    @classmethod
    def _parse_structured_input(cls, user_input: Any) -> Optional[Tuple[AcousticArchetype, Dict[str, float]]]:
        """Parsea diccionarios o directivas del tipo 'arquetipo: OSCURO, drive: 0.2'."""
        data_dict = {}
        if isinstance(user_input, dict):
            data_dict = user_input
        elif isinstance(user_input, str) and (user_input.startswith("{") and user_input.endswith("}")):
            try:
                data_dict = json.loads(user_input)
            except Exception:
                pass

        if data_dict:
            arch_raw = data_dict.get("archetype") or data_dict.get("arquetipo")
            custom_p = {}
            for k, v in data_dict.items():
                if k not in ("archetype", "arquetipo") and isinstance(v, (int, float)):
                    custom_p[k] = float(v)

            if arch_raw:
                try:
                    arch_enum = AcousticArchetype(str(arch_raw).strip().upper())
                    return arch_enum, custom_p
                except ValueError:
                    pass

        # Parseo de directiva textual 'arquetipo: NOMBRE'
        if isinstance(user_input, str):
            m = re.search(r'(?:arquetipo|archetype|modo)\s*[:=]\s*([a-zA-Z_]+)', user_input, re.IGNORECASE)
            if m:
                cand = m.group(1).strip().upper()
                try:
                    return AcousticArchetype(cand), {}
                except ValueError:
                    pass

        return None

    @classmethod
    def _match_fuzzy_thesaurus(cls, text: str) -> Optional[Tuple[AcousticArchetype, float, str]]:
        """Busca coincidencias de palabras clave en el thesaurus semántico ponderado."""
        best_arch: Optional[AcousticArchetype] = None
        best_score = 0.0
        best_kw = ""

        for arch, keywords in cls.THESAURUS.items():
            for kw in keywords:
                # Comprobar presencia de la palabra clave en el texto
                if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                    # Mayor puntuación para palabras clave compuestas
                    score = 0.90 if " " in kw else 0.85
                    if score > best_score:
                        best_score = score
                        best_arch = arch
                        best_kw = kw

        if best_arch:
            return best_arch, best_score, best_kw
        return None

    @classmethod
    def _extract_numeric_tweaks(cls, text: str) -> Dict[str, float]:
        """Detecta especificaciones numéricas de usuario en lenguaje natural."""
        tweaks: Dict[str, float] = {}

        # Corte de frecuencias: 'corte en 120 hz' o 'hpf 100'
        hpf_m = re.search(r'(?:corte|hpf|filtro|low cut)\s*(?:en|a)?\s*(\d+(?:\.\d+)?)\s*(?:hz)?', text, re.IGNORECASE)
        if hpf_m:
            try:
                hz = float(hpf_m.group(1))
                tweaks["1 Frequency A"] = hz_to_eq8_norm(hz)
            except ValueError:
                pass

        # Ganancia: 'gain +3' o 'ganancia -2 db'
        gain_m = re.search(r'(?:gain|ganancia)\s*([+-]?\d+(?:\.\d+)?)\s*(?:db)?', text, re.IGNORECASE)
        if gain_m:
            try:
                db = float(gain_m.group(1))
                tweaks["2 Gain A"] = db_to_eq8_norm(db)
            except ValueError:
                pass

        return tweaks

    @classmethod
    def _apply_custom_params_to_chain(cls, chain: List[Dict[str, Any]], custom_params: Dict[str, float]) -> None:
        """Aplica overrides numéricos a los dispositivos de la cadena."""
        if not custom_params:
            return
        for dev in chain:
            for k, v in custom_params.items():
                if k in dev.get("parameters", {}):
                    dev["parameters"][k] = v

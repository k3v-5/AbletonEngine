"""
Tests for Ultra Acoustic Catalog, Semantic Intent Resolver, and Device Execution Verifier.
========================================================================================
Validates:
1. Full 21 acoustic roles coverage with 11 archetypes.
2. Strict frequency and dynamic differentiation across roles (User Directive).
3. Exact mathematical converters for Ableton Live 12 native parameters.
4. 3-Layer Semantic Intent Resolver (Structured, Fuzzy Thesaurus, Guaranteed Fallback).
5. Closed-loop Device Execution Verifier (Tolerances +/- 0.04, Delta >= 1%, Retry Payload).
6. Creative Development Gatekeepers (Section Contrast and Drop 2 Mutation).
"""

import pytest
import math
from typing import Dict, Any, List

from engine.fx.ultra_acoustic_catalog import (
    UltraAcousticCatalog,
    AcousticArchetype,
    AcousticProfileSpec,
    hz_to_eq8_norm,
    db_to_eq8_norm,
    ms_to_glue_attack,
    sec_to_glue_release,
    ULTRA_ACOUSTIC_CATALOG,
)
from engine.fx.semantic_intent_resolver import (
    SemanticIntentResolver,
    ResolvedAcousticIntent,
)
from engine.core.device_execution_verifier import (
    DeviceExecutionVerifier,
    VerificationError,
)
from engine.production.copilot.phases.phase_6.gatekeepers import Phase6Gatekeepers


# --- 1. Catálogo Ultra Amplio y Cobertura de Roles ---

def test_ultra_acoustic_catalog_21_roles_coverage():
    """Verifica que los 21 roles acústicos instrumentales + FX estén definidos."""
    expected_roles = [
        "KICK", "808_BASS", "SUB", "BASS", "ELECTRIC_BASS", "DRUMS", "DEMBOW",
        "PERCUSSION", "KEYS", "GUITAR", "RHYTHM_GUITAR", "LEAD_GUITAR", "LEAD",
        "COUNTER_LEAD", "PAD", "STRINGS", "BRASS", "CHOIR", "VOCALS",
        "BACKING_VOCALS", "EAR_CANDY", "TEXTURE_FOLEY", "FX"
    ]
    for r in expected_roles:
        assert r in ULTRA_ACOUSTIC_CATALOG, f"Rol {r} ausente en ULTRA_ACOUSTIC_CATALOG."
        role_dict = ULTRA_ACOUSTIC_CATALOG[r]
        assert len(role_dict) >= 4, f"Rol {r} tiene menos de 4 arquetipos definidos."
        assert AcousticArchetype.BALANCED in role_dict or AcousticArchetype.PUNCHY in role_dict or AcousticArchetype.OSCURO in role_dict


def test_role_frequency_differentiation_directive():
    """
    Directiva del Usuario:
    'cada arquetipo debe ser diferente para cada tipo de rol acústico ya que no todos manejan las mismas frecuencias'.
    Verifica que el mismo arquetipo sonoro aplique frecuencias y cortes completamente distintos entre roles.
    """
    # 1. Comparar OSCURO en KICK vs SUB vs KEYS vs VOCALS
    kick_dark = UltraAcousticCatalog.get_role_archetype_spec("KICK", AcousticArchetype.OSCURO.value)
    sub_dark = UltraAcousticCatalog.get_role_archetype_spec("SUB", AcousticArchetype.OSCURO.value)
    keys_dark = UltraAcousticCatalog.get_role_archetype_spec("KEYS", AcousticArchetype.OSCURO.value)
    vox_dark = UltraAcousticCatalog.get_role_archetype_spec("VOCALS", AcousticArchetype.OSCURO.value)

    # HPFs deben ser distintos
    hpf_kick = kick_dark.eq_bands[0].freq_hz
    hpf_sub = sub_dark.eq_bands[0].freq_hz
    hpf_keys = keys_dark.eq_bands[0].freq_hz
    hpf_vox = vox_dark.eq_bands[0].freq_hz

    assert hpf_sub < hpf_kick < hpf_vox <= hpf_keys, "Los cortes HPF de OSCURO deben diferir según el rol acústico."

    # Subgrave en SUB debe tener LPF quirúrgico bajo (< 150 Hz), mientras KEYS tiene corte mucho más alto (> 4000 Hz)
    lpf_sub = next(b.freq_hz for b in sub_dark.eq_bands if b.band_type == 6)
    high_keys = next(b.freq_hz for b in keys_dark.eq_bands if b.band_index == 8)
    assert lpf_sub <= 140.0
    assert high_keys >= 4000.0

    # 2. Comparar PUNCHY en KICK vs DEMBOW vs LEAD
    kick_punch = UltraAcousticCatalog.get_role_archetype_spec("KICK", AcousticArchetype.PUNCHY.value)
    dembow_punch = UltraAcousticCatalog.get_role_archetype_spec("DEMBOW", AcousticArchetype.PUNCHY.value)
    lead_punch = UltraAcousticCatalog.get_role_archetype_spec("LEAD", AcousticArchetype.PUNCHY.value)

    # El punch del Kick está en 65 Hz, el snap del Dembow en 2800 Hz, el bite del Lead en 2500 Hz
    kick_boost_f = kick_punch.eq_bands[1].freq_hz
    dembow_snap_f = dembow_punch.eq_bands[3].freq_hz
    lead_bite_f = lead_punch.eq_bands[2].freq_hz

    assert kick_boost_f < 100.0
    assert 2500.0 <= dembow_snap_f <= 3500.0
    assert 2000.0 <= lead_bite_f <= 3000.0


# --- 2. Conversores Matemáticos a Live 12 ---

def test_mathematical_converters_exactness():
    """Valida los conversores analíticos logarítmicos y discretos a Live 12."""
    # EQ Eight Frequencies (20 Hz -> 0.0, 20000 Hz -> 1.0)
    assert hz_to_eq8_norm(20.0) == 0.0
    assert hz_to_eq8_norm(20000.0) == 1.0
    assert abs(hz_to_eq8_norm(200.0) - 0.3333) < 0.001
    assert abs(hz_to_eq8_norm(1000.0) - 0.5663) < 0.001

    # Clamping
    assert hz_to_eq8_norm(5.0) == 0.0
    assert hz_to_eq8_norm(30000.0) == 1.0

    # Gain (-15 dB -> 0.0, 0 dB -> 0.5, +15 dB -> 1.0)
    assert db_to_eq8_norm(-15.0) == 0.0
    assert db_to_eq8_norm(0.0) == 0.5
    assert db_to_eq8_norm(15.0) == 1.0
    assert db_to_eq8_norm(-3.0) == 0.4

    # Glue Compressor discrete steps
    assert ms_to_glue_attack(30.0) == 1.0
    assert ms_to_glue_attack(0.1) == 0.0
    assert ms_to_glue_attack(1.0) == 0.4

    assert sec_to_glue_release(0.0, auto=True) == 0.0
    assert sec_to_glue_release(0.1) == 0.2
    assert sec_to_glue_release(0.2) == 0.4


def test_build_native_insert_chain():
    """Valida la generación de cadenas 100% nativas para Ableton Live 12."""
    chain = UltraAcousticCatalog.build_native_insert_chain("KICK", "PUNCHY")
    assert len(chain) >= 2
    dev_names = [d["name"] for d in chain]
    assert "EQ Eight" in dev_names
    assert all(d["uri"].startswith("query:AudioFx#") for d in chain)

    # Sub debe tener Bass Mono
    sub_chain = UltraAcousticCatalog.build_native_insert_chain("SUB", "OSCURO")
    util_dev = next((d for d in sub_chain if d["name"] == "Utility"), None)
    assert util_dev is not None
    assert util_dev["parameters"].get("Bass Mono") == 1.0
    assert util_dev["parameters"].get("Width") == 0.0


# --- 3. Resolutor Semántico Inequívoco (SemanticIntentResolver) ---

def test_semantic_intent_resolver_layers():
    """Valida las 3 capas del resolutor semántico."""
    # Capa 1: Estructurada
    r1 = SemanticIntentResolver.resolve_intent({"archetype": "OSCURO", "Drive": 0.25}, "BASS")
    assert r1.archetype == AcousticArchetype.OSCURO
    assert r1.custom_parameters.get("Drive") == 0.25
    assert not r1.is_fallback

    # Capa 2: Semántica Difusa en Español
    r2 = SemanticIntentResolver.resolve_intent("quiero un bajo pesado y oscuro pero con medios limpios", "BASS")
    assert r2.archetype in (AcousticArchetype.OSCURO, AcousticArchetype.DEEP)
    assert not r2.is_fallback

    # Capa 2: Semántica Difusa en Inglés con pegada
    r3 = SemanticIntentResolver.resolve_intent("punchy snap with fast transient attack", "KICK")
    assert r3.archetype == AcousticArchetype.PUNCHY

    # Capa 3: Fallback Garantizado ante entrada vacía o complaciente
    r4 = SemanticIntentResolver.resolve_intent("{}", "KICK")
    assert r4.archetype == AcousticArchetype.PUNCHY
    assert r4.is_fallback

    r5 = SemanticIntentResolver.resolve_intent("ok dale", "PAD")
    assert r5.archetype == AcousticArchetype.AIRY
    assert r5.is_fallback

    # Bypass explícito
    r6 = SemanticIntentResolver.resolve_intent("bypass", "KEYS")
    assert r6.bypass_requested is True


# --- 4. Bucle Cerrado de Verificación Física (DeviceExecutionVerifier) ---

class MockLiveSocketConnection:
    """Simulador de socket LOM de Live para pruebas de read-back."""
    def __init__(self, initial_params: Dict[str, float], reject_params: bool = False):
        self.params = dict(initial_params)
        self.reject_params = reject_params
        self.commands_sent = []

    def send_command(self, cmd: str, args: Dict[str, Any]) -> Dict[str, Any]:
        self.commands_sent.append((cmd, args))
        if cmd == "get_device_parameters":
            return {
                "parameters": [
                    {"name": k, "value": v} for k, v in self.params.items()
                ]
            }
        elif cmd == "set_device_parameter":
            p_name = str(args.get("parameter", "")).strip().lower()
            val = float(args.get("value", 0.0))
            if not self.reject_params:
                self.params[p_name] = val
            return {"status": "SUCCESS"}
        elif cmd == "delete_device":
            return {"status": "SUCCESS"}
        return {}


def test_device_execution_verifier_success_and_failure():
    """Verifica el read-back físico dual (tolerancia +/- 0.04 y delta >= 1%)."""
    # 1. Éxito cuando el parámetro cambia y es leído de vuelta dentro de tolerancia
    mock_conn = MockLiveSocketConnection({"1 frequency a": 0.10})
    success, diag = DeviceExecutionVerifier.apply_and_verify_parameter(
        conn=mock_conn,
        track_index=1,
        device_index=0,
        device_name="EQ Eight",
        param_identifier="1 frequency a",
        target_value=0.35,
        is_test_env=False
    )
    assert success is True
    assert diag["status"] == "VERIFIED_PHYSICAL_OK"
    assert abs(mock_conn.params["1 frequency a"] - 0.35) < 0.001

    # 2. Fallo por rechazo físico de Live (valor no cambia / Macro bloqueada)
    mock_conn_rejected = MockLiveSocketConnection({"1 frequency a": 0.10}, reject_params=True)
    success_rej, diag_rej = DeviceExecutionVerifier.apply_and_verify_parameter(
        conn=mock_conn_rejected,
        track_index=1,
        device_index=0,
        device_name="EQ Eight",
        param_identifier="1 frequency a",
        target_value=0.35,
        is_test_env=False
    )
    assert success_rej is False
    assert diag_rej["root_cause"] in ("PARAMETER_VALUE_REJECTED", "STAGNANT_PARAMETER_DELTA_ZERO")

    # 3. Generación del payload de re-pregunta interactiva
    payload = DeviceExecutionVerifier.build_verification_failed_payload(
        track_index=1,
        track_name="Lead Synth",
        device_index=0,
        device_name="EQ Eight",
        diagnosis=diag_rej,
        role="LEAD",
        retry_count=1
    )
    assert payload["status"] == "VERIFICATION_FAILED_RETRY_REQUIRED"
    assert len(payload["actionable_options"]) == 3
    assert payload["retry_count"] == 1
    assert payload["max_retries"] == 3


# --- 5. Compuertas de Desarrollo Creativo en Fase 6 ---

def test_creative_development_gatekeepers():
    """Verifica que loops planos o drops idénticos activen CREATIVE_DEVELOPMENT_BLOCKED."""
    sections = [
        {"name": "Verse 1", "bars": 8},
        {"name": "Chorus 1", "bars": 8},
        {"name": "Verse 2", "bars": 8},
        {"name": "Chorus 2", "bars": 8}
    ]

    # 1. Contraste insuficiente: Verse 1 tiene 10 notas, Chorus 1 tiene 10 notas idénticas
    flat_custom_map = {
        (0, 0): [{"pitch": 60, "start_time": 0.0}] * 10,
        (0, 1): [{"pitch": 60, "start_time": 0.0}] * 10,
    }
    blk_contrast = Phase6Gatekeepers.check_section_contrast(
        session=None,
        sections=sections,
        custom_notes_map=flat_custom_map,
        is_test_env=False
    )
    assert blk_contrast is not None
    assert blk_contrast["status"] == "CREATIVE_DEVELOPMENT_BLOCKED"
    assert "CONTRASTE INSUFICIENTE" in blk_contrast["current_step"]

    # 2. Contraste suficiente: Verse 1 tiene 4 notas, Chorus 1 tiene 24 notas
    dynamic_custom_map = {
        (0, 0): [{"pitch": 60, "start_time": 0.0}] * 4,
        (0, 1): [{"pitch": 60, "start_time": 0.0}] * 24,
    }
    blk_ok = Phase6Gatekeepers.check_section_contrast(
        session=None,
        sections=sections,
        custom_notes_map=dynamic_custom_map,
        is_test_env=False
    )
    assert blk_ok is None

    # 3. Drop 2 idéntico a Drop 1: Secciones 1 (Chorus 1) y 3 (Chorus 2) con notas idénticas
    identical_drops_map = {
        (0, 1): [{"pitch": 60, "start_time": 0.0}, {"pitch": 64, "start_time": 1.0}],
        (0, 3): [{"pitch": 60, "start_time": 0.0}, {"pitch": 64, "start_time": 1.0}],
    }
    blk_drop = Phase6Gatekeepers.check_second_drop_transformation(
        session=None,
        sections=sections,
        custom_notes_map=identical_drops_map,
        is_test_env=False
    )
    assert blk_drop is not None
    assert blk_drop["status"] == "CREATIVE_DEVELOPMENT_BLOCKED"
    assert "DROP 2 IDÉNTICO" in blk_drop["current_step"]

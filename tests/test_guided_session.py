# tests/test_guided_session.py
"""
Unit tests for Copilot Guided Session (State Machine Wizard for Interactive Music Production).
Tests the conversational, step-by-step interactive interview flow across all 7 production phases:
1. PHASE_1_TRACKS (Scaffolding)
2. PHASE_2_SECTIONS (Arrangement cue points)
3. PHASE_3_INSTRUMENTS (Track-by-track verified instrument loading and Drum Pad verification)
4. PHASE_4_PARAM_SCULPTING (Track-by-track synthesis sculpting Delta >= 1)
5. PHASE_5_INSERT_EFFECTS (Track-by-track insert FX chains)
6. PHASE_6_COMPOSITION (Arrangement composition with Drum Octave Guard)
7. PHASE_7_MIX_MASTER (Mixing, Sidechain ducking and LUFS mastering)
8. PHASE_8_COMPLETED (Active listening for ongoing tweaks)
"""

import pytest
from unittest.mock import MagicMock
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor


@pytest.fixture
def clean_session():
    """Provides a fresh CopilotGuidedSession with reset state."""
    session = CopilotGuidedSession()
    session.reset()
    return session


def test_guided_session_initial_prompt(clean_session):
    adapter = MockAbletonAdapter()
    res = clean_session.step(conn=adapter, user_input="")

    assert res["phase"] == "PHASE_1_TRACKS"
    assert "Paso 1 de 7" in res["question"]
    assert "Opción A" in res["question"]
    assert "Opción B" in res["question"]


def test_guided_session_phase_1_scaffolding(clean_session):
    adapter = MockAbletonAdapter()
    res = clean_session.step(conn=adapter, user_input="Opción A")

    assert res["phase"] == "PHASE_2_SECTIONS"
    assert clean_session.data["phase_index"] == 2
    assert len(clean_session.data["tracks"]) == 5
    assert clean_session.data["tracks"][0]["role"] == "DRUMS"
    assert clean_session.data["tracks"][1]["role"] == "KEYS"
    assert clean_session.data["tracks"][2]["role"] == "PAD"
    assert clean_session.data["tracks"][3]["role"] == "BASS"
    assert clean_session.data["tracks"][4]["role"] == "LEAD"

    assert len(adapter.tracks) >= 5
    assert "Paso 2 de 7" in res["question"]


def test_guided_session_phase_2_sections(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    res = clean_session.step(conn=adapter, user_input="Opción B")

    assert res["phase"] == "PHASE_3_INSTRUMENTS"
    assert clean_session.data["phase_index"] == 3
    assert clean_session.data["total_bars"] == 64
    assert len(clean_session.data["sections"]) == 5
    assert clean_session.data["current_track_ptr"] == 0

    assert hasattr(adapter, "cue_points")
    assert len(adapter.cue_points) == 5
    assert "Instrumento / Kit para Pista 0" in res["question"]


def test_guided_session_phase_3_zero_silent_swallow(clean_session):
    """Verifies that an unverified instrument halts progression and flags LOAD_FAILED."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")

    original_send = adapter.send_command
    def fail_load(cmd, params=None):
        if cmd == "load_browser_item":
            raise RuntimeError("Live connection timeout during VST scan")
        return original_send(cmd, params)

    adapter.send_command = fail_load

    res_fail = clean_session.step(conn=adapter, user_input="Opción 1")
    assert res_fail["status"] == "LOAD_FAILED"
    assert res_fail["retry_required"] is True
    assert clean_session.data["current_track_ptr"] == 0
    assert "FALLO DE VERIFICACIÓN" in res_fail["action_taken"]


def test_guided_session_phase_3_track_by_track(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")

    res_t0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 1
    assert "Instrumento / Kit para Pista 1" in res_t0["question"]

    res_t1 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 2
    assert "Instrumento / Kit para Pista 2" in res_t1["question"]

    res_t2 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 3

    res_t3 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_track_ptr"] == 4

    res_t4 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert res_t4["phase"] == "PHASE_4_PARAM_SCULPTING"
    assert clean_session.data["phase_index"] == 4
    assert "Paso 4 de 7" in res_t4["question"]
    assert "Esculpido de Síntesis" in res_t4["question"]


def test_guided_session_phase_4_param_sculpting(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING"

    res_p0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_param_ptr"] == 1

    res_p1 = clean_session.step(conn=adapter, user_input="Opción 2 (Brillante y Moderno)")
    assert clean_session.data["current_param_ptr"] == 2

    clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Opción 3 (Pesado y Agresivo)")
    res_p4 = clean_session.step(conn=adapter, user_input="Opción 2")

    assert res_p4["phase"] == "PHASE_5_INSERT_EFFECTS"
    assert clean_session.data["phase_index"] == 5
    assert "Paso 5 de 7" in res_p4["question"]
    assert "Cadena de Efectos de Inserción" in res_p4["question"]


def _create_compliant_test_wav(filepath, target_lufs=-14.0, profile=None):
    from pathlib import Path
    import soundfile as sf
    import numpy as np
    from engine.mix.lufs_validation_gate import LUFSValidationGate, ProfileRegistry

    p = profile or (ProfileRegistry.CLUB if target_lufs > -11.0 else ProfileRegistry.STREAMING)
    gate = LUFSValidationGate(profile=p)

    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sig = np.sin(2 * np.pi * 1000.0 * t)
    audio = np.vstack([sig, sig])

    cur_res = gate.audit(audio, sr=sr)
    needed_gain = 10 ** ((target_lufs - cur_res.integrated_lufs) / 20.0)
    calibrated = audio * needed_gain

    sf.write(str(filepath), calibrated.T.astype(np.float32), sr)


def test_guided_session_phase_5_insert_effects(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"

    res_fx0 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_fx_ptr"] == 1

    res_fx1 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_fx_ptr"] == 2

    # Step through remaining 7 effects (total 10 effects across 5 tracks)
    for _ in range(7):
        clean_session.step(conn=adapter, user_input="Opción 1")
    res_fx_final = clean_session.step(conn=adapter, user_input="Opción 1")

    assert res_fx_final["phase"] == "PHASE_6_COMPOSITION"
    assert clean_session.data["phase_index"] == 6
    assert "Paso 6 de 7" in res_fx_final["question"]
    assert "tonalidad" in res_fx_final["question"].lower()


def test_guided_session_phase_6_composition(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")

    res = clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    assert res["phase"] == "PHASE_7_AUTOMATION"
    assert clean_session.data["phase_index"] == 7
    assert clean_session.data["key"] == "F"
    assert clean_session.data["scale"] == "natural_minor"
    assert clean_session.data["bpm"] == 120.0

    for trk_info in clean_session.data.get("tracks", []):
        t_idx = trk_info["index"]
        trk = adapter.tracks[t_idx]
        assert trk["clip_slots"][0]["has_clip"] is True
        assert len(trk.get("arrangement_clips", [])) > 0

    assert "Paso 7 de 8" in res["question"]
    assert "automatizaciones" in res["question"].lower()


def test_guided_session_phase_7_automation_and_bypass(clean_session):
    """Validates track automation injection and bypass option in Phase 7."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    assert clean_session.data["current_phase"] == "PHASE_7_AUTOMATION"

    # 1. Test Option 1 (Full Recommended Package)
    res_auto = clean_session.step(conn=adapter, user_input="Opción 1 (Paquete Completo)")
    assert res_auto["phase"] == "PHASE_8_MIX_MASTER"
    assert clean_session.data["phase_index"] == 8
    assert len(clean_session.data["automations"]) >= 3
    assert hasattr(adapter, "automation_envelopes")
    assert len(adapter.automation_envelopes) >= 3

    types = [a["type"] for a in clean_session.data["automations"]]
    assert "FILTER_SWEEP_UP" in types
    assert "REVERB_WASHOUT" in types
    assert any(t in types for t in ["SUB_CLEANUP", "PRE_DROP_VACUUM"])

    # 2. Test Bypass branch
    clean_session.reset()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")

    res_byp = clean_session.step(conn=adapter, user_input="Bypass")
    assert res_byp["phase"] == "PHASE_8_MIX_MASTER"
    assert clean_session.data["phase_index"] == 8
    assert len(clean_session.data["automations"]) == 0


def test_guided_session_phase_8_mix_master_and_phase_9(clean_session):
    from pathlib import Path

    mcp_dir = Path.home() / ".mcp_analysis"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    for old_wav in mcp_dir.glob("*.wav"):
        try:
            old_wav.unlink()
        except Exception:
            pass

    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")
    clean_session.step(conn=adapter, user_input="Opción 1")  # Phase 7 Automation

    # Step 1: Without real audio or stream, gatekeeper MUST block in Phase 8
    res_blocked = clean_session.step(conn=adapter, user_input="Club a -8.5 LUFS")
    assert res_blocked["status"] == "BLOCKED_AWAITING_AUDIO"
    assert res_blocked["retry_required"] is True
    assert clean_session.data["current_phase"] == "PHASE_8_MIX_MASTER"
    assert clean_session.data["is_complete"] is False

    # Step 2: Provide authentic, compliant WAV audio (-8.5 LUFS) in .mcp_analysis and retry
    test_wav = mcp_dir / "phase8_master_fixture.wav"
    _create_compliant_test_wav(test_wav, target_lufs=-8.5)

    try:
        res = clean_session.step(conn=adapter, user_input="Club a -8.5 LUFS")
        assert res["phase"] == "PHASE_9_COMPLETED"
        assert res["status"] == "COMPLIANT_CERTIFIED"
        assert clean_session.data["phase_index"] == 9
        assert clean_session.data["is_complete"] is True
        assert clean_session.data["target_profile"] == "CLUB"
        assert "PRODUCCIÓN FINALIZADA" in res["question"]
        assert "El Copilot permanece activo y escuchando" in res["question"]
        assert "psychoacoustic_report" in res["lufs_audit"]
        assert clean_session.data.get("psychoacoustic_report") is not None

        # Step 3: Test on-demand live tweak and automation in Phase 9
        res_tweak = clean_session.step(conn=adapter, user_input="Cambia el tempo a 128 BPM")
        assert res_tweak["phase"] == "PHASE_9_COMPLETED"
        assert clean_session.data["bpm"] == 128.0
        assert "128.0 BPM" in res_tweak["action_taken"]

        res_auto_live = clean_session.step(conn=adapter, user_input="Automatiza el sweep de filtro en el Lead")
        assert res_auto_live["phase"] == "PHASE_9_COMPLETED"
        assert "Automatización" in res_auto_live["action_taken"]

        # Step 4: Test Stem Export & Forensic Quality Gatekeeper in Phase 9
        res_stems = clean_session.step(conn=adapter, user_input="Exportar paquete de stems")
        assert res_stems["phase"] == "PHASE_9_COMPLETED"
        assert res_stems["current_step"] == "AUDITORÍA Y EXPORTACIÓN DE STEMS COMPLETADA"
        assert res_stems["ready_for_distribution"] is True
        assert "stems_export" in res_stems
        assert res_stems["stems_export"]["stems_count"] >= 5
        assert Path(res_stems["stems_export"]["manifest_path"]).exists()
    finally:
        if test_wav.exists():
            try:
                test_wav.unlink()
            except Exception:
                pass


def test_modular_sections_structural_silences():
    """Validates that section-aware note generation respects structural silences."""
    from engine.production.copilot.guided_session import generate_modular_section_notes

    # 1. Puente / Calma: Drums & Bass MUST be completely silent
    d_bridge = generate_modular_section_notes("DRUMS", 4, "Puente (Calma)", 8)
    b_bridge = generate_modular_section_notes("BASS", 4, "Puente (Calma)", 8)
    k_bridge = generate_modular_section_notes("KEYS", 4, "Puente (Calma)", 8)
    assert len(d_bridge) == 0, "Drums must be totally silent in Puente"
    assert len(b_bridge) == 0, "Bass must be totally silent in Puente"
    assert len(k_bridge) > 0, "Keys should provide harmonic bed in Puente"

    # 2. Buildup: Bass MUST be silent to create drop tension; drums must have roll
    b_build = generate_modular_section_notes("BASS", 2, "Buildup", 8)
    d_build = generate_modular_section_notes("DRUMS", 2, "Buildup", 8)
    assert len(b_build) == 0, "Bass must be silent in Buildup"
    assert len(d_build) >= 32, "Drums must have progressive acceleration in Buildup"

    # 3. Drops: Drums and Bass at maximum impact
    d_drop1 = generate_modular_section_notes("DRUMS", 3, "Drop 1", 16)
    b_drop1 = generate_modular_section_notes("BASS", 3, "Drop 1", 16)
    assert len(d_drop1) >= 200, "Drop 1 must have heavy full drum groove"
    assert len(b_drop1) >= 20, "Drop 1 must have heavy bass notes"
    assert max(n.velocity for n in d_drop1) == 127


def test_insert_effects_sculpting_registry(clean_session):
    """Validates that Phase 5 registers modified internal parameters (Delta >= 1) for insert devices."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    DeviceParameterSupervisor._SCULPTED_REGISTRY.clear()

    # Step through Phase 5 for all 10 insert effects
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")

    # In Phase 5, each track with loaded effects had insert devices added to _SCULPTED_REGISTRY
    assert len(DeviceParameterSupervisor._SCULPTED_REGISTRY) >= 5


def test_real_audio_measurement_policy(clean_session, tmp_path):
    """Validates strict adherence to real audio measurement (zero synthetic estimation policy)."""
    from pathlib import Path

    # Ensure no existing wav files interfere with Test Case 1
    mcp_dir = Path.home() / ".mcp_analysis"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    for old_wav in mcp_dir.glob("*.wav"):
        try:
            old_wav.unlink()
        except Exception:
            pass

    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")
    clean_session.step(conn=adapter, user_input="Bypass")  # Skip automation

    # Test Case 1: When no WAV file or UDP stream exists, reports BLOCKED in Phase 8 without fake estimations
    res_no_audio = clean_session.step(conn=adapter, user_input="Streaming a -14 LUFS")
    assert res_no_audio["status"] == "BLOCKED_AWAITING_AUDIO"
    assert res_no_audio["phase"] == "PHASE_8_MIX_MASTER"
    assert clean_session.data["is_complete"] is False
    audit = clean_session.data.get("lufs_audit", {})
    assert audit.get("status") == "BLOCKED_AWAITING_AUDIO"
    assert audit.get("integrated_lufs") is None, "Must not generate synthetic LUFS when no audio exists"
    assert audit.get("certificate") == "BLOQUEADO_FALTA_AUDIO_REAL"

    # Test Case 2: When an actual compliant WAV file exists in .mcp_analysis, it audits real PCM and passes
    test_wav = mcp_dir / "real_master_test.wav"
    _create_compliant_test_wav(test_wav, target_lufs=-14.0)

    try:
        clean_session.data["current_phase"] = "PHASE_8_MIX_MASTER"
        clean_session.data["phase_index"] = 8
        clean_session._save_state()

        res_real = clean_session.step(conn=adapter, user_input="Streaming a -14 LUFS")
        assert res_real["phase"] == "PHASE_9_COMPLETED"
        assert res_real["status"] == "COMPLIANT_CERTIFIED"
        audit_real = clean_session.data.get("lufs_audit", {})
        assert audit_real.get("integrated_lufs") is not None, "Must produce real LUFS measurement from WAV file"
        assert "WAV" in str(audit_real.get("source")), "Must cite WAV file as source"
        assert "certificate" in audit_real
    finally:
        if test_wav.exists():
            try:
                test_wav.unlink()
            except Exception:
                pass

def test_no_suggested_values_and_ranges_displayed(clean_session):
    """
    Verifies that the engine never outputs pre-cooked suggested values in configurations,
    presents technical parameter ranges, and invites the AI to reason and decide.
    """
    adapter = MockAbletonAdapter()
    
    # 1. Phase 1: Tracks
    p1 = clean_session.step(conn=adapter, user_input="")
    assert "Decisión Técnica Requerida" in p1["question"]
    assert "**DRUMS** (20 Hz - 18 kHz)" in p1["question"]
    assert "**BASS** (30 Hz - 250 Hz)" in p1["question"]
    assert "valor sugerido" not in p1["question"].lower()

    # Move to Phase 2
    p2 = clean_session.step(conn=adapter, user_input="Opción A")
    assert "Decisión Técnica Requerida" in p2["question"]
    assert "Rango de 64 a 128 compases" in p2["question"]
    assert "valor sugerido" not in p2["question"].lower()

    # Move through Phase 3 (Instruments - here curated options are permitted)
    clean_session.step(conn=adapter, user_input="Opción A")
    for _ in range(4):
        clean_session.step(conn=adapter, user_input="Opción 1")
    p4 = clean_session.step(conn=adapter, user_input="Opción 1")

    # 2. Phase 4: Synthesis parameter sculpting
    assert p4["phase"] == "PHASE_4_PARAM_SCULPTING"
    assert "Decisión Técnica Requerida" in p4["question"]
    assert "`WAVETABLE_POS` (Rango: `0.0 - 1.0`" in p4["question"]
    assert "`FILTER_CUTOFF` (Rango: `0.0 - 1.0`" in p4["question"]
    assert "valor sugerido" not in p4["question"].lower()
    assert "opción 1 (cálido y analógico)" not in p4["question"].lower()

    # Provide custom parameters reasoned by AI
    p4_custom = clean_session.step(conn=adapter, user_input="Cutoff: 0.72, Drive: 0.35, Sub: 0.85")
    assert clean_session.data["current_param_ptr"] == 1
    sculpted = clean_session.data["tracks"][0]["sculpted_parameters"]
    assert sculpted.get("FILTER_CUTOFF") == 0.72
    assert sculpted.get("DRIVE") == 0.35
    assert sculpted.get("SUB_LEVEL") == 0.85

    # Fast forward remaining Phase 4 tracks (3 iterations, 4th returns Phase 5 prompt)
    for _ in range(3):
        clean_session.step(conn=adapter, user_input="Cutoff: 0.60, Drive: 0.20")
    p5 = clean_session.step(conn=adapter, user_input="Cutoff: 0.60, Drive: 0.20")

    # 3. Phase 5: Insert Effects
    assert p5["phase"] == "PHASE_5_INSERT_EFFECTS"
    assert "Decisión Técnica Requerida" in p5["question"]
    assert "Rango:" in p5["question"]
    assert "valor sugerido" not in p5["question"].lower()
    assert "aplicar parámetros recomendados" not in p5["question"].lower()

    # Custom parameter input in Phase 5 (Device 0)
    clean_session.step(conn=adapter, user_input="Drive: 0.40, Crunch: 0.25")
    assert clean_session.data["current_fx_ptr"] == 1
    fx_applied = clean_session.data["tracks"][0]["insert_effects"][0]["parameters"]
    assert fx_applied.get("Drive") == 0.40
    assert fx_applied.get("Crunch") == 0.25

    # Fast forward remaining 9 Phase 5 devices (8 calls + 9th returns Phase 6 prompt)
    for _ in range(8):
        clean_session.step(conn=adapter, user_input="Opción 1")
    p6 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert p6["phase"] == "PHASE_6_COMPOSITION"
    assert "Decisión Técnica Requerida" in p6["question"]
    assert "valor sugerido" not in p6["question"].lower()

    # 5. Phase 7: Automation
    p7 = clean_session.step(conn=adapter, user_input="Tonalidad D menor a 124 BPM")
    assert p7["phase"] == "PHASE_7_AUTOMATION"
    assert "Decisión Técnica Requerida" in p7["question"]
    assert "(Recomendada" not in p7["question"]
    assert "valor sugerido" not in p7["question"].lower()

    # 6. Phase 8: Mix and Master
    p8 = clean_session.step(conn=adapter, user_input="Opción A")
    assert p8["phase"] == "PHASE_8_MIX_MASTER"
    assert "Decisión Técnica Requerida" in p8["question"]
    assert "Rango de Sonoridad Integrada" in p8["question"]
    assert "Rango de True Peak" in p8["question"]
    assert "valor sugerido" not in p8["question"].lower()


def test_modular_sections_all_genres_and_progressions():
    """Validates that all 13 drum genres and 11 harmonic progressions synthesize authentic notes."""
    from engine.production.copilot.guided_session import generate_modular_section_notes, resolve_genre_style
    from engine.music.drums.genre_grooves import GenreDrumStyle
    from engine.knowledge.composition.chords import PROGRESSION_DEFINITIONS

    # 1. Test all 13 drum genres in Drop 1 (16 bars)
    for style in GenreDrumStyle:
        d_notes = generate_modular_section_notes(
            role="DRUMS",
            section_index=3,
            section_name="Drop 1",
            section_bars=16,
            key="F",
            scale="natural_minor",
            bpm=120.0,
            genre=style.value
        )
        assert len(d_notes) >= 200, f"Genre {style.value} failed density contract: {len(d_notes)} notes"
        assert max(n.velocity for n in d_notes) == 127, f"Genre {style.value} missing accent 127"

    # 2. Test all harmonic progressions for Keys, Bass and Lead
    all_progressions = list(PROGRESSION_DEFINITIONS.keys()) + ["royal_road", "dorian", "harmonic_minor", "natural_minor"]
    for prog in all_progressions:
        # Keys (Drop-2 voiced and strummed)
        k_notes = generate_modular_section_notes(
            role="KEYS",
            section_index=1,
            section_name="Verse 1",
            section_bars=16,
            key="G",
            scale=prog,
            bpm=125.0
        )
        assert len(k_notes) >= 16, f"Progression {prog} failed keys note generation"
        # Bass (Sub-range MIDI 24-38 with 808 groove)
        b_notes = generate_modular_section_notes(
            role="BASS",
            section_index=3,
            section_name="Drop 1",
            section_bars=16,
            key="G",
            scale=prog,
            bpm=125.0
        )
        assert len(b_notes) >= 20, f"Progression {prog} failed bass density: {len(b_notes)}"
        assert all(23 <= n.pitch <= 50 for n in b_notes), f"Progression {prog} bass pitch out of sub range"

        # Lead (Call-and-response melodic statement)
        l_notes = generate_modular_section_notes(
            role="LEAD",
            section_index=3,
            section_name="Drop 1",
            section_bars=16,
            key="G",
            scale=prog,
            bpm=125.0
        )
        assert len(l_notes) >= 16, f"Progression {prog} failed lead generation"


def test_guided_session_genre_detection_and_composition(clean_session):
    """Validates that user genre and progression inputs are captured and utilized in guided production."""
    adapter = MockAbletonAdapter()

    # Step 1: Detect genre in Phase 1
    res1 = clean_session.step(conn=adapter, user_input="Quiero un tema de Trap a 140 BPM con Drums, Keys, Pad, Bass, Lead")
    assert clean_session.data.get("genre") == "trap"

    # Step 2: Set sections
    clean_session.step(conn=adapter, user_input="Opción B")

    # Steps 3..5: Fast-forward instruments and insert effects
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")

    # Step 6: Compose with specific harmonic progression and genre
    res6 = clean_session.step(conn=adapter, user_input="Trap en F classic_dark a 140 BPM")
    assert clean_session.data["key"] == "F"
    assert clean_session.data["scale"] == "classic_dark"
    assert clean_session.data["genre"] == "trap"
    assert clean_session.data["bpm"] == 140.0
    assert res6["phase"] == "PHASE_7_AUTOMATION"



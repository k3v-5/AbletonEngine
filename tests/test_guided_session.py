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


def _make_composition_input(bpm=120.0, key="F", scale="natural_minor", genre="trap"):
    import json
    payload = {
        "bpm": bpm,
        "key": key,
        "scale": scale,
        "genre": genre,
        "composition": {
            "0": {"all": [{"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 127}, {"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 115}]},
            "DRUMS": {"all": [{"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 100}]},
            "KICK": {"all": [{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 127}]},
            "KEYS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "PAD": {"all": [{"pitch": 65, "start_time": 0.0, "duration": 4.0, "velocity": 80}]},
            "BASS": {"all": [{"pitch": 29, "start_time": 0.0, "duration": 0.5, "velocity": 120}, {"pitch": 41, "start_time": 0.75, "duration": 0.25, "velocity": 110}]},
            "LEAD": {"all": [{"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}]},
            "BRASS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 110}]},
            "CHOIR": {"all": [{"pitch": 65, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "GUITAR": {"all": [{"pitch": 57, "start_time": 0.0, "duration": 1.0, "velocity": 90}]},
            "STRINGS": {"all": [{"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}]},
            "PERCUSSION": {"all": [{"pitch": 42, "start_time": 0.0, "duration": 0.25, "velocity": 90}]},
        }
    }
    return f"```json\n{json.dumps(payload)}\n```"


def test_guided_session_initial_prompt(clean_session):
    adapter = MockAbletonAdapter()
    res = clean_session.step(conn=adapter, user_input="")

    assert res["phase"] == "PHASE_1_TRACKS"
    assert "Paso 1 de 7" in res["question"]
    assert "DRUMS" in res["question"]
    assert "BRASS" in res["question"]
    assert "CHOIR" in res["question"]


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

    # Step through remaining effects across tracks
    res_fx_final = None
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        res_fx_final = clean_session.step(conn=adapter, user_input="Opción 1")

    assert res_fx_final["phase"] == "PHASE_6_COMPOSITION"
    assert clean_session.data["phase_index"] == 6
    assert ("paso 6 de 7" in res_fx_final["question"].lower() or "componiendo pista" in res_fx_final["question"].lower() or "composición" in res_fx_final["question"].lower())


def test_guided_session_phase_5_no_duplicate_insert_effects(clean_session):
    """Verifies that revisiting Phase 5 or processing tracks with existing devices does not duplicate insert effects."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"

    # Step through all effects in Phase 5
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")

    # Verify each track has at least 2 insert effects (including mandatory EQ Eight)
    for t_idx in range(5):
        t_devs = adapter.tracks[t_idx]["devices"]
        fx_devs = [d for d in t_devs if d.get("type") == "audio_effect"]
        assert len(fx_devs) >= 2, f"Track {t_idx} has {len(fx_devs)} insert effects, expected >= 2"
        assert len(clean_session.data["tracks"][t_idx].get("insert_effects", [])) >= 2

    # Deliberately inject a duplicate "Drum Buss" on track 0
    adapter.tracks[0]["devices"].append({
        "index": len(adapter.tracks[0]["devices"]),
        "name": "Drum Buss",
        "class_name": "DrumBuss",
        "type": "audio_effect"
    })
    assert len([d for d in adapter.tracks[0]["devices"] if d.get("name") == "Drum Buss"]) == 2

    # Now simulate re-visiting Phase 5 with pre-existing effects and duplicate
    clean_session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
    clean_session.data["phase_index"] = 5
    clean_session.data["current_fx_ptr"] = 0
    clean_session.data["current_fx_track_ptr"] = 0
    clean_session.data["current_fx_dev_ptr"] = 0
    clean_session._save_state()

    # Step through all effects again
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")

    # Verify duplicate was purged and tracks still have valid insert effects
    drum_busses = [d for d in adapter.tracks[0]["devices"] if d.get("name") == "Drum Buss"]
    assert len(drum_busses) == 1, f"Expected 1 Drum Buss after purge, found {len(drum_busses)}"

    for t_idx in range(5):
        t_devs = adapter.tracks[t_idx]["devices"]
        fx_devs = [d for d in t_devs if d.get("type") == "audio_effect"]
        assert len(fx_devs) >= 2, f"Track {t_idx} has {len(fx_devs)} insert effects after second run, expected >= 2"
        trk_state = clean_session.data["tracks"][t_idx]
        assert len(trk_state.get("insert_effects", [])) >= 2


def test_guided_session_phase_6_composition(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")

    # 1. Without notes, the engine strictly blocks and requires explicit composition
    res_blocked = clean_session.step(conn=adapter, user_input="Tonalidad F menor a 120 BPM")
    assert res_blocked["status"] in ("AWAITING_EXPLICIT_AI_COMPOSITION", "AWAITING_TRACK_NOTES")
    assert res_blocked["phase"] == "PHASE_6_COMPOSITION"

    # 2. Providing explicit AI composition payload advances to Phase 7
    res = clean_session.step(conn=adapter, user_input=_make_composition_input(bpm=120.0, key="F", scale="natural_minor"))

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


def test_guided_session_phase_6_custom_ai_notes(clean_session):
    """
    Validates that when the AI provides direct custom MIDI notes in Phase 6,
    the engine uses the exact AI composition without procedural database overrides.
    """
    import json
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")

    ai_payload = {
        "bpm": 128.0,
        "key": "F",
        "scale": "minor",
        "composition": {
            "0": {
                "0": [
                    {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 127},
                    {"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 115}
                ]
            },
            "BASS": {
                "0": [
                    {"pitch": 29, "start_time": 0.0, "duration": 0.5, "velocity": 120},
                    {"pitch": 41, "start_time": 0.75, "duration": 0.25, "velocity": 110}
                ]
            },
            "KEYS": {
                "0": [
                    {"pitch": 60, "start_time": 0.0, "duration": 2.0, "velocity": 90}
                ]
            },
            "PAD": {
                "0": [
                    {"pitch": 65, "start_time": 0.0, "duration": 4.0, "velocity": 80}
                ]
            },
            "LEAD": {
                "0": [
                    {"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}
                ],
                "Outro": [
                    {"pitch": 53, "start_time": 0.0, "duration": 4.0, "velocity": 127}
                ]
            }
        }
    }
    custom_input = f"Aquí está mi composición directa:\n```json\n{json.dumps(ai_payload)}\n```"
    res = clean_session.step(conn=adapter, user_input=custom_input)

    assert res["phase"] == "PHASE_7_AUTOMATION"
    assert clean_session.data["phase_index"] == 7
    assert clean_session.data["bpm"] == 128.0
    assert clean_session.data["key"] == "F"
    assert clean_session.data["ai_composed"] is True

    # Validate that track 0 clip 0 has the notes composed by the AI
    clip0_notes = adapter.get_clip_notes(0, 0)
    assert len(clip0_notes) >= 2
    assert clip0_notes[0]["pitch"] == 36
    assert clip0_notes[0]["velocity"] == 127
    assert clip0_notes[1]["pitch"] == 38
    assert clip0_notes[1]["velocity"] == 115

    # Validate that BASS track clip 0 has the bass notes composed by the AI
    bass_idx = None
    for trk_info in clean_session.data.get("tracks", []):
        if trk_info["role"] == "BASS":
            bass_idx = trk_info["index"]
            break
    assert bass_idx is not None
    bass_notes = adapter.get_clip_notes(bass_idx, 0)
    assert len(bass_notes) >= 2
    assert bass_notes[0]["pitch"] == 29
    assert bass_notes[1]["pitch"] == 41


def test_guided_session_phase_7_automation_and_bypass(clean_session):
    """Validates track automation injection and bypass option in Phase 7."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())

    assert clean_session.data["current_phase"] == "PHASE_7_AUTOMATION"

    # 1. Test Option 1 (Full Recommended Package)
    res_auto = clean_session.step(conn=adapter, user_input="Opción 1 (Paquete Completo)")
    assert res_auto["phase"] == "PHASE_8_VOCAL_DUCKING"
    assert clean_session.data["phase_index"] == 8
    assert len(clean_session.data["automations"]) >= 3
    assert hasattr(adapter, "automation_envelopes")
    assert len(adapter.automation_envelopes) >= 3

    types = [a["type"] for a in clean_session.data["automations"]]
    assert "FILTER_SWEEP_UP" in types
    assert "REVERB_WASHOUT" in types
    assert any(t in types for t in ["SUB_CLEANUP", "PRE_DROP_VACUUM"])

    # Step into Phase 9 Mix/Master from Phase 8 Vocal Ducking
    res_duck = clean_session.step(conn=adapter, user_input="Opción A")
    assert res_duck["phase"] == "PHASE_9_MIX_MASTER"
    assert clean_session.data["phase_index"] == 9
    assert clean_session.data["vocal_ducking"]["status"] == "CONFIGURED"

    # 2. Test Bypass branch
    clean_session.reset()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())

    res_byp = clean_session.step(conn=adapter, user_input="Bypass")
    assert res_byp["phase"] == "PHASE_8_VOCAL_DUCKING"
    assert clean_session.data["phase_index"] == 8
    assert len(clean_session.data["automations"]) == 0

    res_duck_byp = clean_session.step(conn=adapter, user_input="Bypass")
    assert res_duck_byp["phase"] == "PHASE_9_MIX_MASTER"
    assert clean_session.data["phase_index"] == 9
    assert clean_session.data["vocal_ducking"]["is_bypass"] is True


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
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())
    clean_session.step(conn=adapter, user_input="Opción 1")  # Phase 7 Automation
    clean_session.step(conn=adapter, user_input="Opción A")  # Phase 8 Vocal Ducking

    # Step 1: Without real audio or stream, gatekeeper MUST block in Phase 9 Mix/Master
    res_blocked = clean_session.step(conn=adapter, user_input="Club a -8.5 LUFS")
    assert res_blocked["status"] == "BLOCKED_AWAITING_AUDIO"
    assert res_blocked["retry_required"] is True
    assert clean_session.data["current_phase"] in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER")
    assert clean_session.data["is_complete"] is False

    # Step 2: Provide authentic, compliant WAV audio (-8.5 LUFS) in .mcp_analysis and retry
    test_wav = mcp_dir / "phase8_master_fixture.wav"
    _create_compliant_test_wav(test_wav, target_lufs=-8.5)

    try:
        res = clean_session.step(conn=adapter, user_input="Club a -8.5 LUFS")
        assert res["phase"] in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED")
        assert res["status"] == "COMPLIANT_CERTIFIED"
        assert clean_session.data["phase_index"] in (9, 10)
        assert clean_session.data["is_complete"] is True
        assert clean_session.data["target_profile"] == "CLUB"
        assert "PRODUCCIÓN FINALIZADA" in res["question"]
        assert "El Copilot permanece activo y escuchando" in res["question"]
        assert "psychoacoustic_report" in res["lufs_audit"]
        assert clean_session.data.get("psychoacoustic_report") is not None

        # Step 3: Test on-demand live tweak and automation in completed phase
        res_tweak = clean_session.step(conn=adapter, user_input="Cambia el tempo a 128 BPM")
        assert res_tweak["phase"] in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED")
        assert clean_session.data["bpm"] == 128.0
        assert "128.0 BPM" in res_tweak["action_taken"]

        res_auto_live = clean_session.step(conn=adapter, user_input="Automatiza el sweep de filtro en el Lead")
        assert res_auto_live["phase"] in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED")
        assert "Automatización" in res_auto_live["action_taken"]

        # Step 4: Test Stem Export & Forensic Quality Gatekeeper in completed phase
        res_stems = clean_session.step(conn=adapter, user_input="Exportar paquete de stems")
        assert res_stems["phase"] in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED")
        assert res_stems["current_step"] == "AUDITORÍA Y EXPORTACIÓN DE STEMS COMPLETADA"
        assert res_stems["ready_for_distribution"] is True
        assert "stems_export" in res_stems
        assert res_stems["stems_export"]["stems_count"] >= 4
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

    # Step through Phase 5 for all insert effects
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
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
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())
    clean_session.step(conn=adapter, user_input="Bypass")  # Skip automation
    clean_session.step(conn=adapter, user_input="Bypass")  # Skip vocal ducking

    # Test Case 1: When no WAV file or UDP stream exists, reports BLOCKED in Mix/Master without fake estimations
    res_no_audio = clean_session.step(conn=adapter, user_input="Streaming a -14 LUFS")
    assert res_no_audio["status"] == "BLOCKED_AWAITING_AUDIO"
    assert res_no_audio["phase"] in ("PHASE_8_MIX_MASTER", "PHASE_9_MIX_MASTER")
    assert clean_session.data["is_complete"] is False
    audit = clean_session.data.get("lufs_audit", {})
    assert audit.get("status") == "BLOCKED_AWAITING_AUDIO"
    assert audit.get("integrated_lufs") is None, "Must not generate synthetic LUFS when no audio exists"
    assert audit.get("certificate") == "BLOQUEADO_FALTA_AUDIO_REAL"

    # Test Case 2: When an actual compliant WAV file exists in .mcp_analysis, it audits real PCM and passes
    test_wav = mcp_dir / "real_master_test.wav"
    _create_compliant_test_wav(test_wav, target_lufs=-14.0)

    try:
        clean_session.data["current_phase"] = "PHASE_9_MIX_MASTER"
        clean_session.data["phase_index"] = 9
        clean_session._save_state()

        res_real = clean_session.step(conn=adapter, user_input="Streaming a -14 LUFS")
        assert res_real["phase"] in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED")
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

    # Custom parameter input in Phase 5 (Device 0: EQ Eight)
    clean_session.step(conn=adapter, user_input="1 Frequency A: 0.25, 2 Frequency A: 0.40")
    assert clean_session.data["current_fx_ptr"] == 1
    fx_applied = clean_session.data["tracks"][0]["insert_effects"][0]["parameters"]
    assert fx_applied.get("1 Frequency A") == 0.25
    assert fx_applied.get("2 Frequency A") == 0.40

    # Fast forward remaining Phase 5 devices
    p6 = None
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        p6 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert p6["phase"] == "PHASE_6_COMPOSITION"
    assert ("decisión técnica requerida" in p6["question"].lower() or "componiendo" in p6["question"].lower() or "paso 6" in p6["question"].lower())
    assert "valor sugerido" not in p6["question"].lower()

    # 5. Phase 7: Automation
    p7 = clean_session.step(conn=adapter, user_input=_make_composition_input(bpm=124.0, key="D", scale="natural_minor"))
    assert p7["phase"] == "PHASE_7_AUTOMATION"
    assert "Decisión Técnica Requerida" in p7["question"]
    assert "(Recomendada" not in p7["question"]
    assert "valor sugerido" not in p7["question"].lower()

    # 6. Phase 8: Vocal Ducking
    p8 = clean_session.step(conn=adapter, user_input="Opción A")
    assert p8["phase"] == "PHASE_8_VOCAL_DUCKING"
    assert "Decisión Técnica Requerida" in p8["question"]
    assert "Rango de Atenuación" in p8["question"]
    assert "Rango de Tiempo de Ataque" in p8["question"]
    assert "Rango de Tiempo de Relajación" in p8["question"]
    assert "valor sugerido" not in p8["question"].lower()

    # 7. Phase 9: Mix and Master
    p9 = clean_session.step(conn=adapter, user_input="Opción A")
    assert p9["phase"] == "PHASE_9_MIX_MASTER"
    assert "Decisión Técnica Requerida" in p9["question"]
    assert "Rango de Sonoridad Integrada" in p9["question"]
    assert "Rango de True Peak" in p9["question"]
    assert "valor sugerido" not in p9["question"].lower()


def test_guided_session_vocal_ducking_calibration(clean_session):
    """Validates that Phase 8 Vocal Ducking supports Option A, Option B, Custom dB, and Bypass."""
    adapter = MockAbletonAdapter()

    # Fast forward through Phases 1-7
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())
    clean_session.step(conn=adapter, user_input="Opción 1")  # Finish Phase 7 -> lands in Phase 8

    # Test Option A: Commercial Ducking (-2.5 dB)
    res_a = clean_session.step(conn=adapter, user_input="Opción A")
    assert res_a["phase"] == "PHASE_9_MIX_MASTER"
    assert clean_session.data["vocal_ducking"]["status"] == "CONFIGURED"
    assert clean_session.data["vocal_ducking"]["duck_amount_db"] == -2.5
    assert clean_session.data["vocal_ducking"]["is_bypass"] is False

    # Reset and test Option B: Subtle Ducking (-1.5 dB)
    clean_session.reset()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())
    clean_session.step(conn=adapter, user_input="Opción 1")

    res_b = clean_session.step(conn=adapter, user_input="Opción B")
    assert res_b["phase"] == "PHASE_9_MIX_MASTER"
    assert clean_session.data["vocal_ducking"]["duck_amount_db"] == -1.5

    # Reset and test Custom amount (-3.5 dB)
    clean_session.reset()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")
    clean_session.step(conn=adapter, user_input=_make_composition_input())
    clean_session.step(conn=adapter, user_input="Opción 1")

    res_custom = clean_session.step(conn=adapter, user_input="Atenuar a -3.5 dB")
    assert res_custom["phase"] == "PHASE_9_MIX_MASTER"
    assert clean_session.data["vocal_ducking"]["duck_amount_db"] == -3.5


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
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")

    # Step 6: Compose with specific harmonic progression and genre
    res6 = clean_session.step(conn=adapter, user_input=_make_composition_input(bpm=140.0, key="F", scale="classic_dark", genre="trap"))
    assert clean_session.data["key"] == "F"
    assert clean_session.data["scale"] == "classic_dark"
    assert clean_session.data["genre"] == "trap"
    assert clean_session.data["bpm"] == 140.0
    assert res6["phase"] == "PHASE_7_AUTOMATION"


def test_guided_session_dual_lufs_validation_channel_and_master(clean_session):
    """Validates that user prompt requesting LUFS validation triggers dual-stage audit (channel and master)."""
    adapter = MockAbletonAdapter()

    # Initialize session with vocal track
    clean_session.data["tracks"] = [
        {"index": 12, "name": "[VOCALS] Lead Vocal (Live Mic)", "role": "VOCALS", "insert_effects": []}
    ]
    clean_session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"

    # User explicitly asks to validate LUFS of channel and master
    user_req = "Despues de este punto el motor debe validar si se cumple con los luffs, tanto del canal como de el master en general"
    res = clean_session.step(conn=adapter, user_input=user_req)

    if res["status"] == "LUFS_CALIBRATION_REQUIRED":
        assert res["retry_required"] is True
        assert "COMPUERTA DE SONORIDAD" in res["current_step"]
        assert "| **Canal Individual** |" in res["question"]
        assert "| **Master General** |" in res["question"]
        assert "dual_lufs_audit" in res
        # User triggers mandatory calibration
        res = clean_session.step(conn=adapter, user_input="Calibrar")

    assert res["status"] == "DUAL_LUFS_AUDITED"
    assert "AUDITORÍA LUFS DE DOBLE ETAPA" in res["current_step"]
    assert "| **Canal Individual** |" in res["question"]
    assert "| **Master General** |" in res["question"]
    assert "dual_lufs_audit" in res
    assert res["dual_lufs_audit"]["channel_audit"]["target_lufs"] == -18.0
    assert res["dual_lufs_audit"]["master_audit"]["target_lufs"] in (-14.0, -8.5, -6.0)


def test_guided_session_vocal_take_two_part_choice_prompt(clean_session):
    """Validates that entering vocal take prompts user to choose Option 1, Option 2, or Option 3 (2 Partes)."""
    adapter = MockAbletonAdapter()
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["tracks"] = [
        {"index": 12, "name": "[VOCALS] Lead Vocal (Live Mic)", "role": "VOCALS", "is_audio_track": True, "insert_effects": []}
    ]

    # User says they finished recording vocal take
    res = clean_session.step(conn=adapter, user_input="Ya grabe la voz")

    assert res["status"] == "AWAITING_VOCAL_WORKFLOW_CHOICE"
    assert "SELECCIÓN DE FLUJO" in res["current_step"]
    assert "Opción 1: Solo Cortar Frases" in res["question"]
    assert "Opción 2: Solo Generar Vocal Chops" in res["question"]
    assert "Opción 3: Ambos en 2 Partes" in res["question"]
    assert clean_session.data.get("awaiting_vocal_workflow_choice") is True


def test_guided_session_vocal_take_option_1_and_mandatory_lufs_gate(clean_session):
    """Validates Option 1 (Solo Cortar Frases) and enforcement of the post-audio LUFS calibration gate."""
    adapter = MockAbletonAdapter()
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["tracks"] = [
        {"index": 12, "name": "[VOCALS] Lead Vocal (Live Mic)", "role": "VOCALS", "is_audio_track": True, "insert_effects": []}
    ]

    # Step 1: User requests Option 1
    res1 = clean_session.step(conn=adapter, user_input="Ya grabe la voz, opcion 1 solo cortar frases")

    # Must immediately trigger the LUFS validation gate (never bypass it)
    assert res1["status"] in ("LUFS_CALIBRATION_REQUIRED", "PART_1_LUFS_CERTIFIED", "DUAL_LUFS_AUDITED")
    assert clean_session.data.get("vocal_production_step") == "PART_1_COMPLETED"

    # If off-spec, verify calibration requirement and calibrate
    if res1["status"] == "LUFS_CALIBRATION_REQUIRED":
        assert res1["retry_required"] is True
        assert clean_session.data.get("lufs_gate_active") is True
        assert "CALIBRACIÓN" in res1["current_step"]

        # Step 2: Calibrate to bring into spec
        res2 = clean_session.step(conn=adapter, user_input="Calibrar ganancia")
        assert res2["status"] == "PART_1_LUFS_CERTIFIED"
        assert res2["passed"] is True
        assert clean_session.data.get("lufs_gate_active") is False
        assert clean_session.data.get("lufs_gate_passed") is True
        assert "DECISIÓN PARTE 2" in res2["current_step"]
        assert "Opción A: Sí, generar Vocal Chops en los Drops (Parte 2)" in res2["question"]


def test_guided_session_vocal_take_option_3_both_and_insert_fx(clean_session):
    """Validates Option 3 (Ambos en 2 partes) and transition to Phase 5 after LUFS compliance."""
    adapter = MockAbletonAdapter()
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["tracks"] = [
        {"index": 12, "name": "[VOCALS] Lead Vocal (Live Mic)", "role": "VOCALS", "is_audio_track": True, "insert_effects": []}
    ]

    # User requests Option 3
    res1 = clean_session.step(conn=adapter, user_input="Opcion 3 ambos en 2 partes")

    assert res1["status"] in ("LUFS_CALIBRATION_REQUIRED", "DUAL_LUFS_AUDITED")
    assert clean_session.data.get("vocal_production_step") == "BOTH_COMPLETED"

    if res1["status"] == "LUFS_CALIBRATION_REQUIRED":
        res2 = clean_session.step(conn=adapter, user_input="Calibrar")
        assert res2["status"] == "DUAL_LUFS_AUDITED"
        assert res2["passed"] is True
        assert clean_session.data.get("current_phase") == "PHASE_5_INSERT_EFFECTS"
        assert "Auto-Tune Artist" in res2["question"]


def test_kick_role_insert_effects_and_note_generation():
    from engine.production.copilot.guided_session import ROLE_INSERT_EFFECTS, generate_modular_section_notes
    # Verify KICK has dedicated effects
    assert "KICK" in ROLE_INSERT_EFFECTS
    kick_fx = [fx["name"] for fx in ROLE_INSERT_EFFECTS["KICK"]]
    assert "EQ Eight" in kick_fx
    assert "Glue Compressor" in kick_fx

    # Verify KICK produces pitch 36 notes
    k_notes = generate_modular_section_notes(
        role="KICK",
        section_index=0,
        section_name="Verse 1",
        section_bars=8,
        key="F",
        scale="natural_minor",
        bpm=120.0,
        genre="trap"
    )
    assert len(k_notes) > 0
    assert all(n.pitch == 36 for n in k_notes)


def test_lead_outro_sustained_drone_not_silenced():
    from engine.production.copilot.guided_session import generate_modular_section_notes
    lead_outro = generate_modular_section_notes(
        role="LEAD",
        section_index=6,
        section_name="Outro",
        section_bars=8,
        key="F",
        scale="natural_minor",
        bpm=120.0,
        genre="trap"
    )
    # Lead must NOT be silenced in Outro (needed to feed saturation collapse)
    assert len(lead_outro) > 0
    pitches = [n.pitch for n in lead_outro]
    # Root pitch in octave 4 or 5
    assert any(p in (53, 65, 77) for p in pitches)


def test_phase_6_kick_drums_decoupling_and_pre_drop_vacuum(clean_session):
    adapter = MockAbletonAdapter()
    clean_session.data["current_phase"] = "PHASE_6_COMPOSITION"
    clean_session.data["phase_index"] = 6
    clean_session.data["tracks"] = [
        {"index": 0, "name": "[DRUMS] 808 Core Kit", "role": "DRUMS"},
        {"index": 1, "name": "[KICK] Sub Kick", "role": "KICK"},
        {"index": 2, "name": "[BASS] 808 Sub", "role": "BASS"},
        {"index": 3, "name": "[LEAD] Yeezus Synth", "role": "LEAD"}
    ]
    clean_session.data["sections"] = [
        {"name": "Intro", "bars": 8, "start_bar": 0},
        {"name": "Verse 1", "bars": 8, "start_bar": 8},
        {"name": "Buildup", "bars": 8, "start_bar": 16},
        {"name": "Drop 1", "bars": 8, "start_bar": 24},
        {"name": "Outro", "bars": 8, "start_bar": 32}
    ]
    clean_session._save_state()

    res = clean_session.step(conn=adapter, user_input=_make_composition_input(bpm=120.0, key="F", scale="natural_minor"))
    assert clean_session.data.get("current_phase") == "PHASE_7_AUTOMATION"

    # Verify both tracks have notes recorded
    drums_trk = clean_session.data["tracks"][0]
    kick_trk = clean_session.data["tracks"][1]
    lead_trk = clean_session.data["tracks"][3]
    assert drums_trk["notes_count"] > 0
    assert kick_trk["notes_count"] > 0
    assert lead_trk["notes_count"] > 0


def test_phase_6_gatekeeper_blocks_when_synth_silenced_in_outro(clean_session):
    """Validates that Phase 6 Gatekeeper strictly blocks if synthesizer/lead has zero notes in the Outro."""
    import json
    adapter = MockAbletonAdapter()
    clean_session.data["current_phase"] = "PHASE_6_COMPOSITION"
    clean_session.data["phase_index"] = 6
    clean_session.data["tracks"] = [
        {"index": 0, "name": "[DRUMS] 808 Core Kit", "role": "DRUMS"},
        {"index": 1, "name": "[BASS] 808 Sub", "role": "BASS"},
        {"index": 2, "name": "[LEAD] Yeezus Synth", "role": "LEAD"}
    ]
    clean_session.data["sections"] = [
        {"name": "Intro", "bars": 8, "start_bar": 0},
        {"name": "Verse 1", "bars": 8, "start_bar": 8},
        {"name": "Outro", "bars": 8, "start_bar": 16}
    ]
    clean_session._save_state()

    # 1. Payload where LEAD only has notes in Intro and Verse 1, but NOT in Outro
    bad_payload = {
        "bpm": 120.0,
        "key": "F",
        "scale": "natural_minor",
        "composition": {
            "0": {"all": [{"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 127}]},
            "BASS": {"all": [{"pitch": 29, "start_time": 0.0, "duration": 0.5, "velocity": 120}]},
            "LEAD": {
                "0": [{"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}],
                "Verse 1": [{"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}]
                # Notice: Outro is missing!
            }
        }
    }
    res_blocked = clean_session.step(conn=adapter, user_input=f"```json\n{json.dumps(bad_payload)}\n```")
    assert res_blocked["status"] == "PHASE_6_GATEKEEPER_BLOCKED"
    assert clean_session.data["current_phase"] == "PHASE_6_COMPOSITION"
    assert "Sintetizador no debe silenciarse" in res_blocked["question"]
    assert "[LEAD] Yeezus Synth" in res_blocked["silenced_synth_tracks"]

    # 2. Add Outro drone notes for LEAD and verify gatekeeper unblocks and advances to Phase 7
    good_payload = bad_payload
    good_payload["composition"]["LEAD"]["Outro"] = [
        {"pitch": 53, "start_time": 0.0, "duration": 4.0, "velocity": 127}
    ]
    res_passed = clean_session.step(conn=adapter, user_input=f"```json\n{json.dumps(good_payload)}\n```")
    assert res_passed["phase"] == "PHASE_7_AUTOMATION"
    assert clean_session.data["phase_index"] == 7


def test_phase_5_mandatory_eq_blocks_bypass(clean_session):
    """Verifies that Phase 5 strictly blocks bypass on EQ Eight and enforces psychoacoustic spectral guidance."""
    adapter = MockAbletonAdapter()
    clean_session.reset()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"

    # The first insert effect on Drums is EQ Eight. Attempting to bypass it must be rejected
    res_bypass = clean_session.step(conn=adapter, user_input="Bypass")
    assert res_bypass["status"] == "VALIDATION_ERROR"
    assert clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"
    assert "ECUALIZADOR ES 100% OBLIGATORIO" in res_bypass["action_taken"]
    assert "Guía Psicoacústica de Frecuencias" in res_bypass["question"]
    assert clean_session.data["current_fx_ptr"] == 0

    # Configuring EQ Eight properly succeeds and advances to the next effect
    res_ok = clean_session.step(conn=adapter, user_input="Opción 1")
    assert clean_session.data["current_fx_ptr"] == 1


def test_phase_6_track_by_track_interactive_mode(clean_session):
    """Verifies that Phase 6 track-by-track interactive mode prompts per track and deploys to arrangement."""
    import json
    from engine.memory.user_learning import save_user_preference
    save_user_preference("composition", "mode", "track_by_track")

    adapter = MockAbletonAdapter()
    clean_session.reset()
    clean_session.step(conn=adapter, user_input="Opción A")
    clean_session.step(conn=adapter, user_input="Opción B")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")
    while clean_session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        clean_session.step(conn=adapter, user_input="Opción 1")

    assert clean_session.data["current_phase"] == "PHASE_6_COMPOSITION"
    comp_session = clean_session.data.get("composition_session", {})
    assert comp_session.get("active") is True
    assert comp_session.get("mode") == "BY_TRACK"

    tracks = clean_session.data["tracks"]
    assert len(tracks) == 5

    # 1. Attempting 'siguiente' without notes must be blocked
    res_blank = clean_session.step(conn=adapter, user_input="Siguiente")
    assert res_blank["status"] == "MODULAR_COMPOSITION_BLOCKED"
    assert clean_session.data["current_phase"] == "PHASE_6_COMPOSITION"

    # 2. Step through each track with single-track notes
    for i, trk in enumerate(tracks):
        p = 36 if trk["role"] in ("DRUMS", "BASS") else 60
        payload = {
            "notes": [
                {"pitch": p, "start_time": 0.0, "duration": 1.0, "velocity": 100},
                {"pitch": p, "start_time": 72.0, "duration": 4.0, "velocity": 90}
            ]
        }
        res_step = clean_session.step(conn=adapter, user_input=json.dumps(payload))
        if i < len(tracks) - 1:
            assert res_step["phase"] == "PHASE_6_COMPOSITION"
            assert res_step["status"] == "AWAITING_TRACK_COMPOSITION"
            assert res_step["track_index"] == i + 1
        else:
            # Last track completes Phase 6 and advances to Phase 7
            assert res_step["phase"] == "PHASE_7_AUTOMATION"
            assert clean_session.data["current_phase"] == "PHASE_7_AUTOMATION"
            assert clean_session.data["phase_index"] == 7


def test_phase_10_change_instrument_full_revalidation_flow(clean_session):
    """Verifies that Phase 10 instrument swap executes the complete re-validation lifecycle."""
    adapter = MockAbletonAdapter()
    clean_session.reset()
    clean_session.data["current_phase"] = "PHASE_10_COMPLETED"
    clean_session.data["phase_index"] = 10
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS", "instrument": "Drum Rack 808", "notes_count": 16},
        {"index": 1, "name": "Keys", "role": "KEYS", "instrument": "Grand Piano", "notes_count": 12},
        {"index": 2, "name": "808 Bass", "role": "BASS", "instrument": "Sub 808", "notes_count": 8}
    ]
    clean_session._save_state()

    # Step 1: Initiate swap
    r1 = clean_session.step(conn=adapter, user_input="Cambiar instrumento")
    assert r1["status"] == "INSTRUMENT_SWAP_SELECT_TRACK"
    assert clean_session.data["instrument_swap_state"]["stage"] == "SELECT_TRACK"

    # Step 2: Select Track 1 (Keys)
    r2 = clean_session.step(conn=adapter, user_input="Pista 1")
    assert r2["status"] == "INSTRUMENT_SWAP_SELECT_PRESET"
    assert clean_session.data["instrument_swap_state"]["stage"] == "SELECT_PRESET"
    assert clean_session.data["instrument_swap_state"]["track_index"] == 1

    # Step 3: Select New Instrument / Preset (Stage-73 Rhodes)
    r3 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert r3["status"] == "INSTRUMENT_SWAP_SCULPT_PARAM"
    assert clean_session.data["instrument_swap_state"]["stage"] == "SCULPT_PARAMETER"
    assert clean_session.data["tracks"][1]["instrument"] == "Stage-73 Warm Rhodes"

    # Step 4: Sculpt Parameter with Delta >= 1
    r4 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert r4["status"] == "INSTRUMENT_SWAP_CONFIGURE_EQ"
    assert clean_session.data["instrument_swap_state"]["stage"] == "CONFIGURE_EQ"
    assert "Guía Psicoacústica" in r4["question"] or "Ecualización Quirúrgica" in r4["question"]

    # Step 4b: Attempt to bypass EQ Eight -> Must be rejected
    r_byp = clean_session.step(conn=adapter, user_input="Bypass EQ")
    assert r_byp["status"] == "VALIDATION_ERROR"
    assert clean_session.data["instrument_swap_state"]["stage"] == "CONFIGURE_EQ"

    # Step 5: Configure EQ Eight properly
    r5 = clean_session.step(conn=adapter, user_input="Opción 1")
    assert r5["status"] == "INSTRUMENT_SWAP_NOTES_DECISION"
    assert clean_session.data["instrument_swap_state"]["stage"] == "NOTES_DECISION"

    # Step 6: Notes Decision -> Keep existing notes
    r6 = clean_session.step(conn=adapter, user_input="Conservar notas")
    assert r6["status"] == "COMPLIANT_CERTIFIED"
    assert r6["phase"] == "PHASE_10_COMPLETED"
    assert clean_session.data["current_phase"] == "PHASE_10_COMPLETED"
    assert clean_session.data.get("instrument_swap_state") is None
    assert clean_session.data["tracks"][1]["instrument"] == "Stage-73 Warm Rhodes"


def test_phase_6_governance_auto_heal_retry_succeeds(clean_session):
    """
    Verifies that when create_clip throws INIT_SYNTH_DETECTED, the engine
    does NOT swallow it as a silent warning; instead, it automatically sculpts
    the un-sculpted synth and retries deployment successfully.
    """
    adapter = MockAbletonAdapter()
    clean_session.reset()
    clean_session.data["current_phase"] = "PHASE_6_COMPOSITION"
    clean_session.data["phase_index"] = 6
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Bass", "role": "BASS", "instrument": "Init Saw Bass", "notes_count": 0}
    ]
    clean_session.data["sections"] = [
        {"name": "Intro", "bars": 8, "start_bar": 0}
    ]
    clean_session._save_state()

    # Track create_clip calls: fail first with INIT_SYNTH_DETECTED, succeed on retry
    attempts = {"create_clip": 0, "sculpt_called": False}
    original_send = adapter.send_command

    def mock_send(cmd, params=None):
        if cmd == "create_clip":
            attempts["create_clip"] += 1
            if attempts["create_clip"] == 1:
                raise RuntimeError("[IMMUTABLE GOVERNANCE BLOCKED: INIT_SYNTH_DETECTED] Delta = 0 on Bass")
        return original_send(cmd, params)

    adapter.send_command = mock_send

    notes_input = _make_composition_input()
    res = clean_session.step(conn=adapter, user_input=notes_input)

    # Must have retried create_clip
    assert attempts["create_clip"] >= 2, f"Expected at least 2 create_clip attempts, got {attempts['create_clip']}"
    # Must have succeeded and advanced to Phase 7
    assert res["phase"] == "PHASE_7_AUTOMATION"
    assert clean_session.data["tracks"][0]["notes_count"] > 0
    assert not clean_session.data["tracks"][0].get("deployment_failed", False)


def test_phase_6_governance_failure_prompts_instrument_swap(clean_session):
    """
    Verifies that when create_clip throws INIT_SYNTH_DETECTED and the retry
    fails as well, the engine halts, refuses to advance, sets status to
    PHASE_6_INSTRUMENT_CHANGE_REQUIRED, and allows the user to trigger an instrument swap.
    """
    adapter = MockAbletonAdapter()
    clean_session.reset()
    clean_session.data["current_phase"] = "PHASE_6_COMPOSITION"
    clean_session.data["phase_index"] = 6
    clean_session.data["tracks"] = [
        {"index": 0, "name": "Strings", "role": "STRINGS", "instrument": "Broken Synth", "notes_count": 0}
    ]
    clean_session.data["sections"] = [
        {"name": "Intro", "bars": 8, "start_bar": 0}
    ]
    clean_session._save_state()

    # create_clip permanently throws governance error
    def mock_send(cmd, params=None):
        if cmd == "create_clip":
            raise RuntimeError("[IMMUTABLE GOVERNANCE BLOCKED: INIT_SYNTH_DETECTED] Broken Synth Delta = 0")
        return {"status": "success"}

    adapter.send_command = mock_send

    notes_input = _make_composition_input()
    res = clean_session.step(conn=adapter, user_input=notes_input)

    # Must NOT swallow as warning, must block and ask for instrument change
    assert res["status"] == "PHASE_6_INSTRUMENT_CHANGE_REQUIRED"
    assert res["phase"] == "PHASE_6_COMPOSITION"
    assert "Error Crítico de Gobernanza" in res["question"] or "Error de Gobernanza" in res["question"]
    assert clean_session.data["tracks"][0]["notes_count"] == 0
    assert clean_session.data["tracks"][0]["deployment_failed"] is True

    # User triggers instrument change
    res_swap = clean_session.step(conn=adapter, user_input="Cambiar instrumento")
    assert res_swap["status"] == "INSTRUMENT_SWAP_SELECT_PRESET"
    assert clean_session.data["instrument_swap_state"]["track_index"] == 0










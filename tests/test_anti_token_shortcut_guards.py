# tests/test_anti_token_shortcut_guards.py
"""
Comprehensive tests verifying that all anti-token shortcut guards prevent AI laziness:
1. Phase 4: Role-adaptive synthesis presets guarantee role-specific acoustics even if AI repeats 'Opción 1'.
2. Phase 5: Cadena Express bulk shortcut is strictly rejected with EFFECT_CALIBRATION_REQUIRED to prevent token fatigue and force deliberate per-device sculpting.
3. Phase 5: AntiBypassQuotaGuard blocks excessive bypasses (> 35% of non-EQ insert devices).
4. Phase 8: Vocal ducking clamps bypass to -1.5 dB transparent ducking when active vocals exist.
5. Phase 8: Dual LUFS Gate blocks Option 3 bypass when True Peak > 0.0 dBTP or LUFS deviation > 2.5 dB.
"""
import pytest
from unittest.mock import MagicMock
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.phases.phase_4_param_sculpting import (
    Phase4ParamSculptingHandler,
    get_role_presets,
    ROLE_PRESET_CONFIGS,
)
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler
from engine.production.copilot.phases.phase_8_vocal_ducking import Phase8VocalDuckingHandler
from engine.mix.lufs_validation_gate import DualLoudnessAuditResult, LoudnessAuditResult


class MockAdapter:
    def __init__(self):
        self.tracks = [
            {"index": 0, "name": "Kick", "role": "DRUMS"},
            {"index": 1, "name": "Sub Bass", "role": "BASS"},
            {"index": 2, "name": "Main Lead", "role": "LEAD"},
            {"index": 3, "name": "Vocal Lead", "role": "VOCALS"},
        ]
        self.commands_sent = []

    def send_command(self, cmd, payload=None):
        self.commands_sent.append((cmd, payload))
        if cmd == "get_session_info":
            return {"result": {"track_count": len(self.tracks)}}
        if cmd == "get_track_info":
            t_idx = payload.get("track_index", 0) if payload else 0
            t_name = self.tracks[t_idx]["name"] if t_idx < len(self.tracks) else "Track"
            return {"result": {"name": t_name}}
        if cmd == "get_track_device_count":
            return {"result": {"count": 3}}
        if cmd == "get_device_parameters":
            return {"result": {"parameters": [{"name": "Frequency", "value": 100.0}]}}
        return {"result": {"status": "ok"}}


# -------------------------------------------------------------------------
# 1. PHASE 4: ROLE-ADAPTIVE SYNTHESIS PRESETS
# -------------------------------------------------------------------------
def test_phase_4_role_adaptive_presets_prevent_uniform_acoustics():
    """Verify BASS and LEAD get completely distinct acoustic parameters when selecting Option 1."""
    bass_presets = get_role_presets("BASS")
    lead_presets = get_role_presets("LEAD")
    pad_presets = get_role_presets("PAD")

    # Both have "1", but parameters are tailored
    b1 = bass_presets["1"]
    l1 = lead_presets["1"]
    p1 = pad_presets["1"]

    assert b1["params"]["FILTER_CUTOFF"] < 0.40, "Bass Cutoff must be low for clean sub"
    assert b1["params"]["SUB_LEVEL"] >= 0.90, "Bass Sub level must be high"
    assert b1["timbre"]["stereo_width"] == 0.0, "Sub Bass must be strictly mono"

    assert l1["params"]["FILTER_CUTOFF"] > 0.70, "Lead Cutoff must be wide open for piercing presence"
    assert l1["timbre"]["stereo_width"] >= 0.70, "Lead must have wide stereo width"

    assert p1["params"]["AMP_ATTACK"] >= 0.20, "Pad Attack must be smooth/slow"


def test_phase_4_guided_session_applies_role_presets_and_records_history(tmp_path):
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
    session.data["phase_index"] = 4
    session.data["tracks"] = [
        {"index": 0, "name": "808 Bass", "role": "BASS", "instrument": "Analog Synth"},
        {"index": 1, "name": "Hook Lead", "role": "LEAD", "instrument": "Wavetable Synth"},
    ]
    session.data["current_param_ptr"] = 0
    adapter = MockAdapter()

    # Step 1: BASS selects Opción 1
    res1 = session.step(conn=adapter, user_input="Opción 1")
    assert session.data["current_param_ptr"] == 1
    t0_params = session.data["tracks"][0]["sculpted_parameters"]
    assert t0_params["SUB_LEVEL"] >= 0.90
    assert t0_params["FILTER_CUTOFF"] <= 0.35

    # Step 2: LEAD also selects Opción 1 (same token choice by AI)
    res2 = session.step(conn=adapter, user_input="Opción 1")
    assert session.data["current_param_ptr"] == 2
    t1_params = session.data["tracks"][1]["sculpted_parameters"]
    assert t1_params["FILTER_CUTOFF"] >= 0.80

    # Verify history recorded
    assert "sculpted_presets_history" in session.data
    hist = session.data["sculpted_presets_history"]
    assert len(hist) == 2
    preset_names = [v["preset_name"] for v in hist.values()]
    assert "Opción 1: Sub Grave Monofónico Limpio" in preset_names
    assert "Opción 1: Modern Hyperpop Piercing Lead" in preset_names


# -------------------------------------------------------------------------
# 2. PHASE 5: CADENA EXPRESS REJECTION (STRICT ANTI-SHORTCUT GATE)
# -------------------------------------------------------------------------
def test_phase_5_cadena_express_configures_entire_track_in_one_turn(tmp_path):
    """
    R2: Prohibit bulk approval shortcuts.
    Cadena Express must be rejected with STATUS: EFFECT_CALIBRATION_REQUIRED,
    ensuring AI cannot bypass per-device parameter sculpting in a single turn.
    """
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
    session.data["phase_index"] = 5
    session.data["tracks"] = [
        {
            "index": 0,
            "name": "Sub Bass",
            "role": "BASS",
            "insert_effects": [
                {"name": "EQ Eight", "category": "EQ", "parameters": {}},
                {"name": "Saturator", "category": "DRIVE", "parameters": {}},
                {"name": "Compressor", "category": "DYNAMICS", "parameters": {}},
            ]
        },
        {
            "index": 1,
            "name": "Lead",
            "role": "LEAD",
            "insert_effects": [
                {"name": "EQ Eight", "category": "EQ", "parameters": {}},
            ]
        }
    ]
    session.data["current_fx_track_ptr"] = 0
    session.data["current_fx_dev_ptr"] = 0
    adapter = MockAdapter()

    # AI attempts "Cadena Express" bulk shortcut to configure entire track in one turn
    res = session.step(conn=adapter, user_input="Cadena Express completa")

    # Bulk shortcut MUST be rejected with EFFECT_CALIBRATION_REQUIRED
    assert res["status"] == "EFFECT_CALIBRATION_REQUIRED", (
        f"Cadena Express must be rejected with EFFECT_CALIBRATION_REQUIRED, got: {res.get('status')}"
    )
    assert session.data["current_fx_track_ptr"] == 0, "Track pointer must NOT advance on Cadena Express shortcut"
    assert session.data["current_fx_dev_ptr"] == 0, "Device pointer must NOT advance on Cadena Express shortcut"
    assert "bloqueo" in res["question"].lower() or "calibración" in res["question"].lower() or "prohíbe" in res.get("action_taken", "").lower()


# -------------------------------------------------------------------------
# 3. PHASE 5: ANTI-BYPASS QUOTA GUARD
# -------------------------------------------------------------------------
def test_phase_5_anti_bypass_quota_guard_blocks_excessive_bypasses(tmp_path):
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
    session.data["phase_index"] = 5
    session.data["tracks"] = [
        {
            "index": 0,
            "name": "Synth 1",
            "role": "LEAD",
            "insert_effects": [
                {"name": "EQ Eight", "category": "EQ", "parameters": {"HP_FREQ": 100.0}},
                {"name": "Chorus", "category": "MODULATION", "bypassed": True, "parameters": {}},
                {"name": "Delay", "category": "SPACE", "parameters": {}},
            ]
        },
        {
            "index": 1,
            "name": "Synth 2",
            "role": "KEYS",
            "insert_effects": [
                {"name": "Phaser", "category": "MODULATION", "parameters": {}},
            ]
        }
    ]
    # Set current_bypassed to quota threshold (2) so next bypass is blocked
    session.data["bypassed_non_eq_count"] = 2
    session.data["current_fx_track_ptr"] = 0
    session.data["current_fx_dev_ptr"] = 2  # Targeting Delay
    adapter = MockAdapter()

    res = session.step(conn=adapter, user_input="Bypass")
    assert res["status"] == "VALIDATION_ERROR"
    assert "CUOTA" in res["question"]
    assert session.data["current_fx_dev_ptr"] == 2, "Must remain on same device to force sculpt"


# -------------------------------------------------------------------------
# 4. PHASE 8: VOCAL DUCKING CLAMPING WHEN VOCAL TRACK EXISTS
# -------------------------------------------------------------------------
def test_phase_8_clamps_bypass_when_vocal_track_present(tmp_path):
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
    session.data["phase_index"] = 8
    session.data["tracks"] = [
        {"index": 0, "name": "Main Lead", "role": "LEAD"},
        {"index": 1, "name": "Chords", "role": "KEYS"},
        {"index": 2, "name": "Lead Vocal", "role": "VOCALS"},
    ]
    adapter = MockAdapter()

    # AI tries to bypass ducking to save tokens
    res = session.step(conn=adapter, user_input="Bypass")
    duck_report = session.data["vocal_ducking"]
    assert duck_report["status"] == "CLAMPED_SUBTLE"
    assert duck_report["bypass_clamped"] is True
    assert duck_report["is_bypass"] is False
    assert duck_report["duck_amount_db"] == -1.5


def test_phase_8_allows_bypass_when_no_vocal_track_exists(tmp_path):
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
    session.data["phase_index"] = 8
    session.data["tracks"] = [
        {"index": 0, "name": "Drums", "role": "DRUMS"},
        {"index": 1, "name": "Bass", "role": "BASS"},
        {"index": 2, "name": "Arp", "role": "LEAD"},
    ]
    adapter = MockAdapter()
    adapter.tracks = [
        {"index": 0, "name": "Drums", "role": "DRUMS"},
        {"index": 1, "name": "Bass", "role": "BASS"},
        {"index": 2, "name": "Arp", "role": "LEAD"},
    ]

    res = session.step(conn=adapter, user_input="Bypass")
    duck_report = session.data["vocal_ducking"]
    assert duck_report["status"] == "BYPASS"
    assert duck_report["is_bypass"] is True
    assert duck_report["duck_amount_db"] == 0.0


# -------------------------------------------------------------------------
# 5. PHASE 8: DUAL LUFS GATE BLOCKS LAZY BYPASS ON CLIPPING / SEVERE DEVIATION
# -------------------------------------------------------------------------
def test_phase_8_dual_lufs_gate_blocks_bypass_on_clipping_or_severe_deviation(tmp_path, monkeypatch):
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
    session.data["tracks"] = [
        {"index": 0, "name": "[VOCALS] Lead Vocal", "role": "VOCALS", "insert_effects": []}
    ]
    adapter = MockAdapter()

    # Mock LUFSValidationGate to return failing audit with True Peak clipping (+0.5 dBTP)
    failing_ch = LoudnessAuditResult(
        passed=False,
        integrated_lufs=-12.0,
        short_term_max_lufs=-10.0,
        momentary_max_lufs=-9.0,
        true_peak_dbtp=0.5,  # Clipping!
        target_lufs=-18.0,
        max_true_peak_dbtp=-1.0,
        lufs_deviation_db=6.0,  # Severe!
        headroom_margin_db=-1.5,
        required_trim_db=-6.0
    )
    failing_m = LoudnessAuditResult(
        passed=False,
        integrated_lufs=-8.0,
        short_term_max_lufs=-7.0,
        momentary_max_lufs=-6.0,
        true_peak_dbtp=0.8,  # Clipping!
        target_lufs=-14.0,
        max_true_peak_dbtp=-1.0,
        lufs_deviation_db=6.0,
        headroom_margin_db=-1.8,
        required_trim_db=-6.0
    )
    mock_dual = DualLoudnessAuditResult(
        passed=False,
        channel_audit=failing_ch,
        master_audit=failing_m,
        summary_table="| Channel | Master |",
        certificate="FAILED_CLIPPING"
    )

    from engine.mix.lufs_validation_gate import LUFSValidationGate
    monkeypatch.setattr(LUFSValidationGate, "audit_dual_channel_and_master", lambda **kwargs: mock_dual)

    handler = Phase8VocalDuckingHandler()

    # AI attempts Option 3 (Bypass) to skip calibration
    res = handler.handle_dual_lufs_validation(session, adapter, "Opción 3")
    assert res["status"] == "LUFS_CALIBRATION_REQUIRED"
    assert res["passed"] is False
    assert res["bypass_blocked"] is True
    assert "BLOQUEO DE SEGURIDAD ACÚSTICA" in res["question"]
    assert session.data["lufs_gate_active"] is True
    assert session.data["lufs_gate_passed"] is False

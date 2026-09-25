# tests/test_mastering_and_delivery_features.py
import pytest
import os
import tempfile
import numpy as np
import soundfile as sf

from engine.mastering.live_master_chain import LiveMasterChainEngine
from engine.mix.resonance_detector import ResonanceDetector
from engine.arrangement.top_tail_guard import TopTailGuard
from engine.audio.stem_bouncer import StemBouncer
from engine.audio.stem_audit import StemAuditor
from engine.production.copilot.guided_session import CopilotGuidedSession


class MockLiveConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_session_info":
            return {"track_count": 8, "tempo": 114.0}
        if cmd == "get_track_info":
            t_idx = params.get("track_index", 0)
            return {
                "index": t_idx,
                "name": f"Track_{t_idx}",
                "devices": [
                    {"name": "EQ Eight"},
                    {"name": "Glue Compressor"},
                    {"name": "Limiter"}
                ]
            }
        return {"status": "success"}


def test_master_gain_boost_calibration():
    """Verify master gain boost calculates and applies +3.0 dB cleanly within -1.0 to -1.5 dBTP."""
    specs = LiveMasterChainEngine.get_target_specs("STREAMING")
    assert specs["target_lufs"] == -14.0
    assert specs["ceiling_db"] == -1.0
    assert specs["limiter_gain_boost_db"] == 3.0

    # Test mock boost
    res_mock = LiveMasterChainEngine.apply_master_gain_boost(
        conn=None,
        master_track_index=0,
        gain_boost_db=3.0,
        target_component="limiter"
    )
    assert res_mock["status"] == "MOCK_SUCCESS"
    assert res_mock["gain_boost_db"] == 3.0
    assert -1.5 <= res_mock["projected_true_peak_dbtp"] <= -1.0
    assert -14.0 <= res_mock["projected_lufs"] <= -13.5

    # Test with MockLiveConnection
    conn = MockLiveConnection()
    res_live = LiveMasterChainEngine.apply_master_gain_boost(
        conn=conn,
        master_track_index=7,
        gain_boost_db=3.0,
        target_component="limiter"
    )
    assert res_live["status"] == "SUCCESS"
    assert any(cmd[0] == "set_device_parameter" for cmd in conn.commands)


def test_clean_low_mid_resonances():
    """Verify post-vocal low-mid resonance cleaner applies notch cuts at 441.4 Hz."""
    tracks = [
        {"index": 0, "name": "808 Kit", "role": "DRUMS"},
        {"index": 1, "name": "808 Bass", "role": "BASS"},
        {"index": 2, "name": "Rhodes Piano", "role": "KEYS"},
        {"index": 3, "name": "Warm Pad", "role": "PAD"},
        {"index": 4, "name": "Saxophone", "role": "BRASS"},
        {"index": 5, "name": "Lead Vocal", "role": "VOCALS"}
    ]

    conn = MockLiveConnection()
    clean_res = ResonanceDetector.clean_low_mid_resonances(
        conn=conn,
        tracks=tracks,
        target_center_freq=441.4,
        cut_db=-3.5,
        q=12.0,
        master_track_index=7
    )

    assert clean_res["status"] == "LOW_MID_RESONANCES_CLEANED"
    assert clean_res["center_frequency_hz"] == 441.4
    assert clean_res["gain_cut_db"] == -3.5
    assert clean_res["q_factor"] == 12.0

    processed_roles = [t["role"] for t in clean_res["tracks_processed"]]
    assert "KEYS" in processed_roles
    assert "PAD" in processed_roles
    assert "BRASS" in processed_roles
    # Vocal and drums should not have the harmonic notch filter
    assert "VOCALS" not in processed_roles


def test_top_and_tail_guard():
    """Verify pre-roll gate enforces silence before beat 0 and outro reverb fades to -inf dB."""
    pre_pts = TopTailGuard.generate_pre_roll_gate_points(downbeat_beat=0.0)
    assert pre_pts[0]["value"] == 0.0
    assert pre_pts[-1]["time"] >= 0.0
    assert pre_pts[-1]["value"] > 0.0

    fade_pts = TopTailGuard.generate_outro_reverb_fade_points(start_beat=252.0, end_beat=256.0)
    assert fade_pts[0]["time"] == 252.0
    assert fade_pts[-1]["time"] == 256.0
    assert fade_pts[-1]["value"] == 0.0  # Must be -inf dB

    # Test audio audit on synthesized signal with clean pre-roll and tail
    sr = 44100
    duration_sec = 2.0
    t = np.linspace(0, duration_sec, int(sr * duration_sec))
    # Tone starts at t=0.2 and stops at t=1.8
    envelope = np.zeros_like(t)
    envelope[(t >= 0.2) & (t <= 1.8)] = 1.0
    clean_audio = 0.5 * np.sin(2 * np.pi * 440.0 * t) * envelope

    audit = TopTailGuard.audit_top_and_tail_audio(clean_audio, sr=sr, pre_roll_duration_sec=0.1, tail_duration_sec=0.1)
    assert audit["pre_roll_clean"] is True
    assert audit["tail_faded_clean"] is True
    assert audit["compliant"] is True


def test_commercial_delivery_stems_24bit_44k():
    """Verify partition into DRUMS, BASS, KEYS/BRASS, VOCALS, FX and 24-bit / 44.1 kHz WAV export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bouncer = StemBouncer(export_dir=tmpdir)
        tracks = [
            {"index": 0, "name": "Kick 808", "role": "KICK"},
            {"index": 1, "name": "Trap Drums", "role": "DRUMS"},
            {"index": 2, "name": "Sub Bassline", "role": "BASS"},
            {"index": 3, "name": "Rhodes Piano", "role": "KEYS"},
            {"index": 4, "name": "Sax Lead", "role": "BRASS"},
            {"index": 5, "name": "Warm Strings Pad", "role": "PAD"},
            {"index": 6, "name": "Main Vocal", "role": "VOCALS"},
            {"index": 7, "name": "Riser Sweep FX", "role": "FX"}
        ]

        plan = bouncer.create_commercial_delivery_plan(
            tracks=tracks,
            bpm=114.0,
            start_bar=1.0,
            end_bar=65.0,
            sample_rate=44100,
            bit_depth=24
        )

        assert plan.sample_rate == 44100
        assert plan.bit_depth == 24
        assert plan.total_bars == 64.0

        stem_ids = [s.stem_id for s in plan.stems]
        assert "00_MASTER" in stem_ids
        assert "01_DRUMS" in stem_ids
        assert "02_BASS" in stem_ids
        assert "03_KEYS_BRASS" in stem_ids
        assert "04_VOCALS" in stem_ids
        assert "05_FX" in stem_ids

        # Export package
        export_res = bouncer.export_commercial_delivery_package(plan)
        assert export_res["status"] == "DELIVERY_PACKAGE_EXPORTED"
        assert export_res["sample_rate"] == 44100
        assert export_res["bit_depth"] == 24
        assert os.path.exists(export_res["manifest_path"])

        # Check that written WAV files are strictly 24-bit PCM at 44.1 kHz
        for fpath in export_res["files"]:
            assert os.path.exists(fpath)
            info = sf.info(fpath)
            assert info.samplerate == 44100
            assert info.subtype == "PCM_24"


def test_copilot_guided_session_phase10_listeners():
    """Verify Phase 10 natural language commands for gain boost, low-mid cleaning, top/tail and stems."""
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = "PHASE_10_COMPLETED"
    session.data["phase_index"] = 10
    session.data["total_bars"] = 64
    session.data["tracks"] = [
        {"index": 0, "name": "Kick", "role": "KICK"},
        {"index": 1, "name": "Bass", "role": "BASS"},
        {"index": 2, "name": "Keys", "role": "KEYS"}
    ]

    conn = MockLiveConnection()

    # 1. Gain boost command
    res_boost = session.step(conn=conn, user_input="impulsar ganancia de entrada del limitador +3.0 dB")
    assert "Master input gain" in res_boost["action_taken"]
    assert session.data.get("master_gain_boost", {}).get("gain_boost_db") == 3.0

    # 2. Resonance cleaning command
    res_clean = session.step(conn=conn, user_input="limpieza de resonancias en medios bajos mud box")
    assert "Notch quirúrgico en 441.4 Hz" in res_clean["action_taken"]

    # 3. Top and Tail command
    res_tt = session.step(conn=conn, user_input="verificar ruidos residuales compas 0 y cola de reverb a -inf dB")
    assert "Top & Tail activos" in res_tt["action_taken"]

    # 4. Stems export command
    res_stems = session.step(conn=conn, user_input="exportar stems de entrega")
    assert res_stems["current_step"] == "AUDITORÍA Y EXPORTACIÓN DE STEMS COMPLETADA"
    assert "24-bit / 44.1 kHz" in res_stems["question"]

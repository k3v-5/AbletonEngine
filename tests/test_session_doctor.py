# tests/test_session_doctor.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from engine.production.doctor.session_doctor import CopilotSessionDoctor


class MockLiveConnection:
    def __init__(self, tracks=None, master=None):
        self.tracks = tracks if tracks is not None else []
        self.master = master or {
            "volume": 0.85,
            "panning": 0.0,
            "devices": [
                {"name": "EQ Eight", "type": "audio_effect"},
                {"name": "Glue Compressor", "type": "audio_effect"},
                {"name": "Limiter", "type": "audio_effect"}
            ]
        }
        self.commands = []

    def send_command(self, cmd: str, params: dict = None):
        params = params or {}
        self.commands.append((cmd, params))

        if cmd == "get_session_info":
            return {
                "track_count": len(self.tracks),
                "num_tracks": len(self.tracks),
                "tempo": 120.0,
                "master_track": self.master
            }

        if cmd == "get_track_info":
            t_idx = params.get("track_index", 0)
            if 0 <= t_idx < len(self.tracks):
                return self.tracks[t_idx]
            return {
                "name": f"Track {t_idx}",
                "track_index": t_idx,
                "volume": 0.75,
                "panning": 0.0,
                "is_muted": False,
                "devices": [],
                "clips": []
            }

        if cmd == "set_track_volume":
            t_idx = params.get("track_index", 0)
            vol = params.get("volume", 0.75)
            if 0 <= t_idx < len(self.tracks):
                self.tracks[t_idx]["volume"] = vol
            return {"status": "ok"}

        if cmd == "set_track_panning":
            t_idx = params.get("track_index", 0)
            pan = params.get("panning", 0.0)
            if 0 <= t_idx < len(self.tracks):
                self.tracks[t_idx]["panning"] = pan
            return {"status": "ok"}

        if cmd == "set_track_mute":
            t_idx = params.get("track_index", 0)
            muted = params.get("is_muted", False)
            if 0 <= t_idx < len(self.tracks):
                self.tracks[t_idx]["is_muted"] = muted
            return {"status": "ok"}

        if cmd == "delete_clip":
            t_idx = params.get("track_index", 0)
            c_idx = params.get("clip_index", 0)
            if 0 <= t_idx < len(self.tracks):
                clips = self.tracks[t_idx].get("clips", [])
                if 0 <= c_idx < len(clips):
                    clips.pop(c_idx)
            return {"status": "ok"}

        if cmd == "delete_device":
            t_idx = params.get("track_index", 0)
            d_idx = params.get("device_index", 0)
            if 0 <= t_idx < len(self.tracks):
                devs = self.tracks[t_idx].get("devices", [])
                if 0 <= d_idx < len(devs):
                    devs.pop(d_idx)
            return {"status": "ok"}

        if cmd == "delete_track":
            t_idx = params.get("track_index", 0)
            if 0 <= t_idx < len(self.tracks):
                self.tracks.pop(t_idx)
            return {"status": "ok"}

        if cmd in ("load_browser_item", "load_instrument_or_effect"):
            t_idx = params.get("track_index", 0)
            item = params.get("item_uri") or params.get("uri", "Effect")
            name = item.split("#")[-1].replace("%20", " ")
            if 0 <= t_idx < len(self.tracks):
                self.tracks[t_idx].setdefault("devices", []).append({
                    "name": name,
                    "class_name": name,
                    "type": "audio_effect"
                })
            else:
                self.master.setdefault("devices", []).append({"name": name, "type": "audio_effect"})
            return {"loaded": True, "new_devices": [name]}

        if cmd == "set_device_parameter":
            return {"status": "ok"}

        if cmd == "get_device_parameters":
            return {
                "result": {
                    "parameters": [
                        {"index": 0, "name": "Device On", "value": 1.0},
                        {"index": 1, "name": "Dry/Wet", "value": 0.5},
                        {"index": 2, "name": "Feedback", "value": 0.5},
                        {"index": 3, "name": "Filter Frequency", "value": 0.5},
                        {"index": 4, "name": "Cutoff", "value": 0.5}
                    ]
                }
            }

        if cmd == "create_arrangement_automation_envelope":
            return {"status": "ok", "created": True, "points_count": len(params.get("points", []))}

        return {"status": "ok"}


@pytest.fixture
def clean_doctor(tmp_path):
    state_file = tmp_path / "doctor_test_state.json"
    doctor = CopilotSessionDoctor(state_file=state_file)
    return doctor


def test_doctor_clean_session_certified_optimal(clean_doctor):
    mock_tracks = [
        {
            "name": "Kick",
            "track_index": 0,
            "volume": 0.426,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Kick Beat", "notes_count": 16, "length": 16.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}, {"name": "Drum Bus", "type": "audio_effect"}],
        },
        {
            "name": "Lead Synth",
            "track_index": 1,
            "volume": 0.358,
            "panning": 0.25,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Melody", "notes_count": 32, "length": 16.0}],
            "devices": [{"name": "Serum", "type": "instrument"}, {"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    res = clean_doctor.step(conn, reset=True)

    assert res["status"] == "HEALTH_CERTIFIED_OPTIMAL"
    assert "100%" in res["current_step"]


def test_doctor_detects_structural_issues(clean_doctor):
    mock_tracks = [
        {
            "name": "Hot Lead",
            "track_index": 0,
            "volume": 0.95,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Solo", "notes_count": 24, "length": 8.0}],
            "devices": [{"name": "EQ Eight"}, {"name": "EQ Eight"}],
        },
        {
            "name": "Ghost Track",
            "track_index": 1,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            "clips": [],
            "devices": [],
        },
        {
            "name": "Sub Bassline",
            "track_index": 2,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": True,
            "clips": [{"clip_index": 0, "name": "Bassline", "notes_count": 16, "length": 8.0}],
            "devices": [{"name": "Wavetable"}],
        },
        {
            "name": "Dead Clip Track",
            "track_index": 3,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Empty", "notes_count": 0, "length": 4.0}],
            "devices": [{"name": "Simpler"}],
        },
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    res = clean_doctor.step(conn, reset=True)

    assert res["status"] == "AWAITING_USER_DECISION"
    assert "Detalle 1 de" in res["question"]
    assert clean_doctor.data["status"] == "TRIAGE_IN_PROGRESS"
    queue = clean_doctor.data["issues_queue"]
    categories = [iss["category"] for iss in queue]

    assert "GAIN_STAGING_HEADROOM" in categories
    assert "DUPLICATE_EFFECTS" in categories
    assert "ORPHAN_TRACK" in categories
    assert "MUTED_ACTIVE_TRACK" in categories
    assert "EMPTY_CLIPS" in categories
    assert "MISSING_CHANNEL_EQ" in categories


def test_doctor_detects_unmastered_session(clean_doctor):
    mock_tracks = [
        {
            "name": "Drums",
            "track_index": 0,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Beat", "notes_count": 16, "length": 8.0}],
            "devices": [{"name": "Drum Rack", "type": "instrument"}],
        }
    ]
    # Unmastered Master Track (no devices)
    conn = MockLiveConnection(tracks=mock_tracks, master={"volume": 0.85, "panning": 0.0, "devices": []})
    res = clean_doctor.step(conn, reset=True)

    assert res["status"] == "AWAITING_USER_DECISION"
    queue = clean_doctor.data["issues_queue"]
    cat_list = [i["category"] for i in queue]
    assert "MASTER_CHAIN_AUDIT" in cat_list


def test_doctor_vst_no_false_duplicate(clean_doctor):
    mock_tracks = [
        {
            "name": "Pad Layer",
            "track_index": 0,
            "volume": 0.65,
            "panning": 0.20,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Chords", "notes_count": 16, "length": 8.0}],
            "devices": [
                {"name": "Omnisphere", "class_name": "PluginDevice", "type": 1},
                {"name": "Efx FRAGMENTS", "class_name": "PluginDevice", "type": 2}
            ],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    res = clean_doctor.step(conn, reset=True)

    # Should NOT flag Omnisphere + Efx FRAGMENTS as duplicate
    queue = clean_doctor.data.get("issues_queue", [])
    dup_issues = [i for i in queue if i["category"] == "DUPLICATE_EFFECTS"]
    assert len(dup_issues) == 0


def test_doctor_batch_operations(clean_doctor):
    mock_tracks = [
        {"name": "Orphan 1", "track_index": 0, "volume": 0.75, "panning": 0.0, "is_muted": False, "clips": [], "devices": []},
        {"name": "Orphan 2", "track_index": 1, "volume": 0.75, "panning": 0.0, "is_muted": False, "clips": [], "devices": []},
        {"name": "Orphan 3", "track_index": 2, "volume": 0.75, "panning": 0.0, "is_muted": False, "clips": [], "devices": []},
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    clean_doctor.step(conn, reset=True)

    # User says "Limpiar todas las huérfanas"
    res = clean_doctor.step(conn, user_input="Limpiar todas las huérfanas")
    assert res["status"] == "DOCTOR_COMPLETED"
    assert res["resolved_count"] == 3


def test_doctor_interactive_workflow(clean_doctor):
    mock_tracks = [
        {
            "name": "Hot Vocal",
            "track_index": 0,
            "volume": 0.92,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Vox", "notes_count": 12, "length": 8.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        },
        {
            "name": "Empty Clip Track",
            "track_index": 1,
            "volume": 0.35,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Blank", "notes_count": 0, "length": 4.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)

    # 1. Start session
    res1 = clean_doctor.step(conn, reset=True)
    assert res1["status"] == "AWAITING_USER_DECISION"
    assert "Hot Vocal" in res1["question"]

    # 2. Apply fix on Issue 1 ("Sí")
    res2 = clean_doctor.step(conn, user_input="Sí")
    assert "DOCTOR-001 Corregido" in res2["question"]
    assert conn.tracks[0]["volume"] <= 0.75

    # 3. Skip Issue 2 ("No" / "Omitir")
    res3 = clean_doctor.step(conn, user_input="Omitir")
    assert res3["status"] == "DOCTOR_COMPLETED"
    assert res3["resolved_count"] == 1
    assert res3["skipped_count"] == 1


def test_doctor_custom_value_application(clean_doctor):
    mock_tracks = [
        {
            "name": "Too Loud Synth",
            "track_index": 0,
            "volume": 0.90,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Lead", "notes_count": 8, "length": 4.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    clean_doctor.step(conn, reset=True)

    # User inputs custom volume "-14 dB"
    res = clean_doctor.step(conn, user_input="-14 dBFS")
    assert res["status"] == "DOCTOR_COMPLETED"
    assert conn.tracks[0]["volume"] < 0.75
    assert len(clean_doctor.data["resolved_issues"]) == 1


def test_doctor_rollback_action(clean_doctor):
    mock_tracks = [
        {
            "name": "Guitar",
            "track_index": 0,
            "volume": 0.95,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Riff", "notes_count": 8, "length": 4.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    clean_doctor.step(conn, reset=True)

    # Apply fix
    clean_doctor.step(conn, user_input="Sí")
    assert conn.tracks[0]["volume"] <= 0.75

    # User requests rollback
    res_rb = clean_doctor.step(conn, user_input="Deshacer")
    assert "Acción revertida" in res_rb["question"]
    assert conn.tracks[0]["volume"] == 0.95


def test_doctor_adds_effect_with_mandatory_sculpting(clean_doctor):
    mock_tracks = [
        {
            "name": "Lead Synth",
            "track_index": 0,
            "volume": 0.358,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Lead", "notes_count": 16, "length": 8.0}],
            "devices": [{"name": "Serum", "type": "instrument"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    clean_doctor.step(conn, reset=True)

    # Issue an on-demand command to add Delay with custom parameters
    res = clean_doctor.step(conn, user_input="Agregar Delay a Lead Synth con Feedback 30% y Dry/Wet 20%")
    assert "Acción Creativa Ejecutada" in res["question"]
    assert "Delay" in res["question"]
    assert "Verificado y esculpido por DeviceParameterSupervisor" in res["question"]

    # Verify device was added to mock track
    dev_names = [d["name"] for d in conn.tracks[0]["devices"]]
    assert "Delay" in dev_names

    # Verify device sculpting registration
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    assert (0, len(dev_names) - 1) in DeviceParameterSupervisor._SCULPTED_REGISTRY or (0, 1) in DeviceParameterSupervisor._SCULPTED_REGISTRY


def test_doctor_suggests_and_applies_automation(clean_doctor):
    mock_tracks = [
        {
            "name": "Synth Chords",
            "track_index": 0,
            "volume": 0.358,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Chords", "notes_count": 16, "length": 16.0}],
            "devices": [
                {"name": "Vital", "type": "instrument"},
                {"name": "Auto Filter", "type": "audio_effect"}
            ],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    clean_doctor.step(conn, reset=True)

    # Issue an on-demand automation request
    res = clean_doctor.step(conn, user_input="Agregar automatizacion filter sweep a Synth Chords compas 8")
    assert "Acción Creativa Ejecutada" in res["question"]
    assert "filter_sweep_up" in res["question"]
    assert "puntos Bézier" in res["question"]

    # Verify automation envelope was commanded
    auto_cmds = [c for c in conn.commands if c[0] == "create_arrangement_automation_envelope"]
    assert len(auto_cmds) >= 1
    envelope_points = auto_cmds[0][1]["points"]
    assert len(envelope_points) >= 16


def test_doctor_reverb_washout_and_vacuum(clean_doctor):
    mock_tracks = [
        {
            "name": "Arp",
            "track_index": 0,
            "volume": 0.358,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Arp Line", "notes_count": 32, "length": 16.0}],
            "devices": [{"name": "Reverb", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    clean_doctor.step(conn, reset=True)

    # 1. Reverb Washout
    res_wash = clean_doctor.step(conn, user_input="Crear reverb washout en Arp compas 12")
    assert "reverb_washout" in res_wash["question"]

    # 2. Pre-Drop Vacuum
    res_vac = clean_doctor.step(conn, user_input="Hacer pre-drop vacuum en Arp compas 16")
    assert "pre_drop_vacuum" in res_vac["question"]


def test_doctor_mandatory_channel_eq_detected_and_repaired(clean_doctor):
    mock_tracks = [
        {
            "name": "Bassline",
            "track_index": 0,
            "volume": 0.426,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "808 Bass", "notes_count": 16, "length": 16.0}],
            "devices": [{"name": "SubLabXL", "type": "instrument"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    res = clean_doctor.step(conn, reset=True)

    # 1. Verify MISSING_CHANNEL_EQ is detected as CRITICAL
    assert res["status"] == "AWAITING_USER_DECISION"
    assert clean_doctor.data["status"] == "TRIAGE_IN_PROGRESS"
    queue = clean_doctor.data["issues_queue"]
    assert len(queue) == 1
    assert queue[0]["category"] == "MISSING_CHANNEL_EQ"
    assert queue[0]["severity"] == "CRITICAL"
    assert "Bassline" in queue[0]["description"]
    assert queue[0]["recommended_params"]["action"] == "insert_channel_eq"

    # 2. Apply repair ("Sí")
    res2 = clean_doctor.step(conn, user_input="Sí")
    assert res2["status"] == "DOCTOR_COMPLETED"
    assert len(clean_doctor.data["resolved_issues"]) == 1
    assert "EQ Eight obligatorio insertado" in clean_doctor.data["resolved_issues"][0]["action"]

    # 3. Verify device was loaded onto mock track
    dev_names = [d["name"] for d in conn.tracks[0]["devices"]]
    assert "EQ Eight" in dev_names


def test_doctor_detects_unpopulated_track_and_sidechain_trigger_missing(clean_doctor):
    mock_tracks = [
        {
            "name": "[KICK] 808 Core Kit",
            "track_index": 0,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            "clips": [],  # 0 clips / notes
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        },
        {
            "name": "[BASS] 808 Sub",
            "track_index": 1,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            "clips": [{"clip_index": 0, "name": "Bass Clip", "notes_count": 8, "length": 16.0, "start_time": 0.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        },
        {
            "name": "[LEAD] Synth",
            "track_index": 2,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            # Clip runs from 0.0 to 32.0, overlapping with Drop 1 at beat 32.0 (pre-drop window 30.0-32.0)
            "clips": [{"clip_index": 0, "name": "Lead Spilling", "notes_count": 16, "length": 32.0, "start_time": 0.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    # Add a cue point for Drop 1 at beat 32.0
    def mock_send(cmd, params=None):
        if cmd == "get_cue_points":
            return {"cue_points": [{"name": "Drop 1", "time": 32.0}]}
        return conn.send_command(cmd, params)
    
    mock_conn = MagicMock()
    mock_conn.send_command = mock_send

    res = clean_doctor.step(mock_conn, reset=True)
    assert clean_doctor.data["status"] == "TRIAGE_IN_PROGRESS"
    queue = clean_doctor.data["issues_queue"]
    categories = [iss["category"] for iss in queue]

    assert "UNPOPULATED_TRACK" in categories
    assert "SIDECHAIN_TRIGGER_MISSING" in categories
    assert "PRE_DROP_VACUUM_VIOLATION" in categories


def test_doctor_detects_and_repairs_synth_silenced_in_outro(clean_doctor):
    mock_tracks = [
        {
            "name": "[LEAD] Yeezus Saw",
            "track_index": 0,
            "volume": 0.358,
            "panning": 0.24,
            "is_muted": False,
            # Clip stops at beat 64.0, but Outro starts at 64.0 -> Synth is silenced in Outro!
            "clips": [{"clip_index": 0, "name": "Lead Riff", "notes_count": 16, "length": 64.0, "start_time": 0.0}],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    def mock_send(cmd, params=None):
        if cmd == "get_cue_points":
            return {"cue_points": [{"name": "Verse 1", "time": 0.0}, {"name": "Outro", "time": 64.0}]}
        return conn.send_command(cmd, params)

    mock_conn = MagicMock()
    mock_conn.send_command = mock_send
    mock_conn.tracks = conn.tracks
    mock_conn.master = conn.master

    # 1. Verify SYNTH_SILENCED_IN_OUTRO is detected as CRITICAL
    res1 = clean_doctor.step(mock_conn, reset=True)
    assert clean_doctor.data["status"] == "TRIAGE_IN_PROGRESS"
    queue = clean_doctor.data["issues_queue"]
    cat_list = [iss["category"] for iss in queue]
    assert "SYNTH_SILENCED_IN_OUTRO" in cat_list

    outro_iss = next(iss for iss in queue if iss["category"] == "SYNTH_SILENCED_IN_OUTRO")
    assert outro_iss["severity"] == "CRITICAL"
    assert outro_iss["recommended_params"]["action"] == "populate_synth_outro"
    assert outro_iss["recommended_params"]["outro_time"] == 64.0

    # 2. Apply repair ("Sí")
    res2 = clean_doctor.step(mock_conn, user_input="Sí")
    assert len(clean_doctor.data["resolved_issues"]) >= 1
    assert any("Drone armónico sostenido inyectado en el Outro" in r["action"] for r in clean_doctor.data["resolved_issues"])

    # 3. Verify clip was added to mock track
    lead_clips = conn.tracks[0]["clips"]
    assert any(c.get("name") == "Outro Sustained Drone" and c.get("start_time") == 64.0 for c in lead_clips)


def test_doctor_pre_drop_vacuum_no_false_positive_when_notes_cut(clean_doctor):
    mock_tracks = [
        {
            "name": "[LEAD] Yeezus Saw",
            "track_index": 0,
            "volume": 0.75,
            "panning": 0.0,
            "is_muted": False,
            # Bounding box reaches 32.0, BUT the note ends cleanly at 28.0 (2 beats before 32.0 is 30.0)
            # Silence from 28.0 to 32.0 -> NO spill into [30.0, 32.0)
            "clips": [{
                "clip_index": 0,
                "name": "Clean Pre-Drop Lead",
                "notes_count": 1,
                "length": 32.0,
                "start_time": 0.0,
                "notes": [
                    {"pitch": 60, "start": 0.0, "duration": 28.0}
                ]
            }],
            "devices": [{"name": "EQ Eight", "type": "audio_effect"}],
        }
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    def mock_send(cmd, params=None):
        if cmd == "get_cue_points":
            return {"cue_points": [{"name": "Drop 1", "time": 32.0}]}
        return conn.send_command(cmd, params)

    mock_conn = MagicMock()
    mock_conn.send_command = mock_send
    mock_conn.tracks = conn.tracks
    mock_conn.master = conn.master

    clean_doctor.step(mock_conn, reset=True)
    queue = clean_doctor.data.get("issues_queue", [])
    cat_list = [iss["category"] for iss in queue]
    # PRE_DROP_VACUUM_VIOLATION must NOT be triggered because notes were cut prior to 30.0!
    assert "PRE_DROP_VACUUM_VIOLATION" not in cat_list



